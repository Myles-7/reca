from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, col, select

from app.api.errors import ContractError
from app.core.observability import current_request_id
from app.models import (
    AuditActorType,
    AuditLog,
    AuditOutcome,
    Claim,
    ClaimEvidenceLink,
    ClaimStatus,
    EvidenceLinkStatus,
    EvidenceObjectType,
    get_datetime_utc,
)

from .resolvers import resolve_evidence

RULE_SET_VERSION = "m7-evidence-invalidation/1.0"


@dataclass(frozen=True)
class PropagationResult:
    invalidated_link_ids: tuple[uuid.UUID, ...]
    affected_claim_ids: tuple[uuid.UUID, ...]


def propagate_invalidation(
    session: Session,
    *,
    project_id: uuid.UUID,
    object_type: EvidenceObjectType,
    object_id: uuid.UUID,
    reason: str,
    source_hash: str | None = None,
    actor_type: AuditActorType = AuditActorType.SYSTEM,
    actor_id: str | None = "evidence-invalidation",
) -> PropagationResult:
    now = get_datetime_utc()
    links = session.exec(
        select(ClaimEvidenceLink).where(
            ClaimEvidenceLink.project_id == project_id,
            ClaimEvidenceLink.evidence_object_type == object_type,
            ClaimEvidenceLink.evidence_object_id == object_id,
            col(ClaimEvidenceLink.status).in_(
                [EvidenceLinkStatus.SUGGESTED, EvidenceLinkStatus.ACTIVE]
            ),
        )
    ).all()
    invalidated: list[uuid.UUID] = []
    affected: set[uuid.UUID] = set()
    for link in links:
        before = {
            "status": link.status,
            "lock_version": link.lock_version,
            "source_hash": link.source_hash,
        }
        link.status = EvidenceLinkStatus.INVALIDATED
        link.invalidated_at = now
        link.invalidation_reason = reason
        link.lock_version += 1
        link.updated_at = now
        session.add(link)
        claim = session.get(Claim, link.claim_id)
        if claim is not None and claim.project_id == project_id:
            if claim.status not in {ClaimStatus.INVALIDATED, ClaimStatus.REJECTED}:
                claim.status = ClaimStatus.NEEDS_EVIDENCE
                claim.lock_version += 1
                claim.updated_at = now
                session.add(claim)
            affected.add(claim.id)
        session.add(
            AuditLog(
                project_id=project_id,
                actor_type=actor_type,
                actor_id=actor_id,
                action="CLAIM_EVIDENCE_LINK_INVALIDATED_BY_SOURCE",
                object_type="claim_evidence_link",
                object_id=link.id,
                before_snapshot=jsonable_encoder(before),
                after_snapshot={
                    "status": EvidenceLinkStatus.INVALIDATED,
                    "source_object_type": object_type,
                    "source_object_id": str(object_id),
                    "source_hash": source_hash,
                    "path": [
                        f"{object_type.value}:{object_id}",
                        f"CLAIM_EVIDENCE_LINK:{link.id}",
                        f"CLAIM:{link.claim_id}",
                    ],
                    "rule_set_version": RULE_SET_VERSION,
                    "invalidated_at": now,
                },
                reason=reason,
                request_id=current_request_id(),
                outcome=AuditOutcome.SUCCEEDED,
            )
        )
        invalidated.append(link.id)
    session.flush()
    return PropagationResult(
        invalidated_link_ids=tuple(sorted(invalidated, key=str)),
        affected_claim_ids=tuple(sorted(affected, key=str)),
    )


def reconcile_project(session: Session, *, project_id: uuid.UUID) -> PropagationResult:
    links = session.exec(
        select(ClaimEvidenceLink).where(
            ClaimEvidenceLink.project_id == project_id,
            col(ClaimEvidenceLink.status).in_(
                [EvidenceLinkStatus.SUGGESTED, EvidenceLinkStatus.ACTIVE]
            ),
        )
    ).all()
    invalidated: set[uuid.UUID] = set()
    affected: set[uuid.UUID] = set()
    for link in links:
        reason: str | None = None
        source_hash: str | None = None
        try:
            reference = resolve_evidence(
                session,
                project_id=project_id,
                object_type=link.evidence_object_type,
                object_id=link.evidence_object_id,
            )
            source_hash = reference.source_hash
            if reference.invalidated or reference.stale:
                reason = "Reconciliation detected stale or invalidated evidence."
            elif not reference.known_status:
                reason = "Reconciliation detected an unknown evidence status."
            elif reference.source_hash != link.source_hash:
                reason = "Reconciliation detected an evidence hash mismatch."
        except ContractError:
            reason = "Reconciliation could not resolve evidence in the authoritative project scope."
        if reason is None:
            continue
        result = propagate_invalidation(
            session,
            project_id=project_id,
            object_type=link.evidence_object_type,
            object_id=link.evidence_object_id,
            reason=reason,
            source_hash=source_hash,
            actor_type=AuditActorType.SYSTEM,
            actor_id="evidence-reconciliation",
        )
        invalidated.update(result.invalidated_link_ids)
        affected.update(result.affected_claim_ids)
    return PropagationResult(
        invalidated_link_ids=tuple(sorted(invalidated, key=str)),
        affected_claim_ids=tuple(sorted(affected, key=str)),
    )
