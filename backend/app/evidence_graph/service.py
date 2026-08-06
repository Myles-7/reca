from __future__ import annotations

import uuid
from typing import Any

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
    EvidenceRelationType,
    ProjectMemberRole,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

from .resolvers import resolve_evidence
from .schemas import (
    ClaimEvidenceLinkCreate,
    ClaimEvidenceLinkPublic,
    ClaimEvidenceLinkTransition,
    EvidenceReference,
)

CREATE_PATH = "/api/v1/claims/{claim_id}/evidence-links"
TRANSITION_PATH = "/api/v1/evidence-links/{link_id}"

RELATION_MATRIX: dict[EvidenceRelationType, frozenset[EvidenceObjectType]] = {
    EvidenceRelationType.SUPPORTED_BY: frozenset(
        {
            EvidenceObjectType.LITERATURE_RECORD,
            EvidenceObjectType.EVIDENCE_SPAN,
            EvidenceObjectType.ANALYSIS_RESULT,
            EvidenceObjectType.FIGURE,
        }
    ),
    EvidenceRelationType.CONTRADICTED_BY: frozenset(
        {
            EvidenceObjectType.LITERATURE_RECORD,
            EvidenceObjectType.EVIDENCE_SPAN,
            EvidenceObjectType.ANALYSIS_RESULT,
        }
    ),
    EvidenceRelationType.DERIVED_FROM: frozenset(
        {
            EvidenceObjectType.MANUSCRIPT_VERSION,
            EvidenceObjectType.DATASET_VERSION,
            EvidenceObjectType.ANALYSIS_RESULT,
        }
    ),
    EvidenceRelationType.TRANSFORMED_FROM: frozenset(
        {EvidenceObjectType.DATASET_VERSION, EvidenceObjectType.DATA_TRANSFORMATION}
    ),
    EvidenceRelationType.ANALYZED_BY: frozenset(
        {
            EvidenceObjectType.ANALYSIS_PLAN,
            EvidenceObjectType.ANALYSIS_RUN,
            EvidenceObjectType.ANALYSIS_RESULT,
        }
    ),
    EvidenceRelationType.PRODUCED_BY: frozenset(
        {EvidenceObjectType.ANALYSIS_RUN, EvidenceObjectType.DATA_TRANSFORMATION}
    ),
    EvidenceRelationType.VISUALIZED_AS: frozenset({EvidenceObjectType.FIGURE}),
    EvidenceRelationType.CONFIRMED_BY: frozenset({EvidenceObjectType.APPROVAL}),
    EvidenceRelationType.AUDITED_BY: frozenset({EvidenceObjectType.AUDIT_RESULT}),
    EvidenceRelationType.INVALIDATED_BY: frozenset({EvidenceObjectType.AUDIT_RESULT}),
}


def _not_found() -> ContractError:
    return ContractError(
        status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
    )


def _role(access: project_service.ProjectAccess) -> ProjectMemberRole:
    return access.membership.role if access.membership else ProjectMemberRole.OWNER


def _audit(
    session: Session,
    *,
    project_id: uuid.UUID,
    actor_type: AuditActorType,
    actor_id: str | None,
    action: str,
    link: ClaimEvidenceLink,
    before: dict[str, Any] | None = None,
    reason: str | None = None,
) -> None:
    session.add(
        AuditLog(
            project_id=project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            object_type="claim_evidence_link",
            object_id=link.id,
            before_snapshot=jsonable_encoder(before) if before else None,
            after_snapshot=jsonable_encoder(
                {
                    "claim_id": link.claim_id,
                    "evidence_object_type": link.evidence_object_type,
                    "evidence_object_id": link.evidence_object_id,
                    "relation_type": link.relation_type,
                    "status": link.status,
                    "lock_version": link.lock_version,
                }
            ),
            reason=reason,
            request_id=current_request_id(),
            outcome=AuditOutcome.SUCCEEDED,
        )
    )


def _allowed_actions(role: ProjectMemberRole, link: ClaimEvidenceLink) -> list[str]:
    actions = project_service.ROLE_ACTIONS[role]
    result = ["evidence.read"]
    if (
        link.status == EvidenceLinkStatus.SUGGESTED
        and "evidence.link.confirm" in actions
    ):
        result.extend(["evidence.link.confirm", "evidence.link.reject"])
    if (
        link.status == EvidenceLinkStatus.ACTIVE
        and "evidence.link.invalidate" in actions
    ):
        result.append("evidence.link.invalidate")
    return result


def link_data(
    session: Session, link: ClaimEvidenceLink, role: ProjectMemberRole
) -> ClaimEvidenceLinkPublic:
    evidence = resolve_evidence(
        session,
        project_id=link.project_id,
        object_type=link.evidence_object_type,
        object_id=link.evidence_object_id,
    )
    return ClaimEvidenceLinkPublic(
        id=link.id,
        project_id=link.project_id,
        claim_id=link.claim_id,
        evidence=evidence,
        relation_type=link.relation_type,
        strength=link.strength,
        status=link.status,
        explanation=link.explanation,
        lock_version=link.lock_version,
        confirmed_at=link.confirmed_at,
        invalidated_at=link.invalidated_at,
        invalidation_reason=link.invalidation_reason,
        allowed_actions=_allowed_actions(role, link),
    )


def _claim(session: Session, *, claim_id: uuid.UUID, for_update: bool = False) -> Claim:
    statement = select(Claim).where(Claim.id == claim_id)
    if for_update:
        statement = statement.with_for_update()
    claim = session.exec(statement).first()
    if claim is None:
        raise _not_found()
    return claim


def _validate_reference(reference: EvidenceReference, *, active: bool) -> None:
    if not reference.known_status:
        raise ContractError(
            status_code=409,
            code="EVIDENCE_STATUS_UNKNOWN",
            message="Evidence status is unknown.",
        )
    if reference.invalidated or reference.stale:
        raise ContractError(
            status_code=409,
            code="EVIDENCE_SOURCE_INVALID",
            message="Evidence source is stale or invalidated.",
        )
    if active and reference.restricted:
        raise ContractError(
            status_code=409,
            code="EVIDENCE_SCOPE_RESTRICTED",
            message="Restricted evidence cannot be activated without a valid read scope.",
        )


def create_link(
    session: Session,
    *,
    actor: User,
    claim_id: uuid.UUID,
    payload: ClaimEvidenceLinkCreate,
    idempotency_key: str,
) -> project_service.OperationResult:
    claim = _claim(session, claim_id=claim_id, for_update=True)
    access = project_service.authorize_project(
        session,
        project_id=claim.project_id,
        actor=actor,
        action="evidence.link.create",
        for_update=True,
    )
    role = _role(access)
    if claim.status in {ClaimStatus.INVALIDATED, ClaimStatus.REJECTED}:
        raise ContractError(
            status_code=409,
            code="CLAIM_SOURCE_INVALID",
            message="Claim cannot receive evidence in its current state.",
        )
    if payload.evidence_object_type not in RELATION_MATRIX[payload.relation_type]:
        raise ContractError(
            status_code=422,
            code="EVIDENCE_RELATION_NOT_ALLOWED",
            message="Evidence type is not allowed for this relation.",
        )
    digest = project_service.request_hash(payload)
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=claim.project_id,
        method="POST",
        path_template=CREATE_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay:
        return replay
    status = (
        EvidenceLinkStatus.SUGGESTED
        if payload.suggestion or role == ProjectMemberRole.REVIEWER
        else EvidenceLinkStatus.ACTIVE
    )
    reference = resolve_evidence(
        session,
        project_id=claim.project_id,
        object_type=payload.evidence_object_type,
        object_id=payload.evidence_object_id,
    )
    _validate_reference(reference, active=status == EvidenceLinkStatus.ACTIVE)
    duplicate = session.exec(
        select(ClaimEvidenceLink).where(
            ClaimEvidenceLink.project_id == claim.project_id,
            ClaimEvidenceLink.claim_id == claim.id,
            ClaimEvidenceLink.evidence_object_type == payload.evidence_object_type,
            ClaimEvidenceLink.evidence_object_id == payload.evidence_object_id,
            ClaimEvidenceLink.relation_type == payload.relation_type,
            col(ClaimEvidenceLink.status).in_(
                [EvidenceLinkStatus.SUGGESTED, EvidenceLinkStatus.ACTIVE]
            ),
        )
    ).first()
    if duplicate is not None:
        result = project_service.OperationResult(
            data=jsonable_encoder(link_data(session, duplicate, role)), status_code=200
        )
        project_service._store_idempotency(
            session,
            actor_id=actor.id,
            project_id=claim.project_id,
            method="POST",
            path_template=CREATE_PATH,
            key=idempotency_key,
            payload_hash=digest,
            result=result,
        )
        project_service._commit(session)
        return result
    now = get_datetime_utc()
    link = ClaimEvidenceLink(
        project_id=claim.project_id,
        claim_id=claim.id,
        evidence_object_type=payload.evidence_object_type,
        evidence_object_id=payload.evidence_object_id,
        relation_type=payload.relation_type,
        strength=payload.strength,
        status=status,
        source_hash=reference.source_hash,
        source_version=jsonable_encoder(reference.source_version),
        explanation=payload.explanation,
        created_by_actor_type=AuditActorType.USER,
        created_by_actor_id=str(actor.id),
        idempotency_key=idempotency_key,
        confirmed_by_user_id=actor.id if status == EvidenceLinkStatus.ACTIVE else None,
        confirmed_at=now if status == EvidenceLinkStatus.ACTIVE else None,
    )
    session.add(link)
    session.flush()
    if claim.status in {
        ClaimStatus.DRAFT,
        ClaimStatus.NEEDS_EVIDENCE,
        ClaimStatus.INSUFFICIENT,
    }:
        claim.status = (
            ClaimStatus.SUPPORTED
            if status == EvidenceLinkStatus.ACTIVE
            else ClaimStatus.NEEDS_EVIDENCE
        )
        claim.lock_version += 1
        claim.updated_at = now
        session.add(claim)
    _audit(
        session,
        project_id=claim.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="CLAIM_EVIDENCE_LINK_CREATED",
        link=link,
    )
    result = project_service.OperationResult(
        data=jsonable_encoder(link_data(session, link, role)), status_code=201
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=claim.project_id,
        method="POST",
        path_template=CREATE_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result


def list_links(
    session: Session,
    *,
    actor: User,
    claim_id: uuid.UUID,
    include_invalidated: bool = False,
) -> list[ClaimEvidenceLinkPublic]:
    claim = _claim(session, claim_id=claim_id)
    access = project_service.authorize_project(
        session, project_id=claim.project_id, actor=actor, action="evidence.read"
    )
    statement = select(ClaimEvidenceLink).where(
        ClaimEvidenceLink.project_id == claim.project_id,
        ClaimEvidenceLink.claim_id == claim.id,
    )
    if not include_invalidated:
        statement = statement.where(
            ClaimEvidenceLink.status != EvidenceLinkStatus.INVALIDATED
        )
    links = session.exec(
        statement.order_by(col(ClaimEvidenceLink.created_at), col(ClaimEvidenceLink.id))
    ).all()
    visible: list[ClaimEvidenceLinkPublic] = []
    for link in links:
        try:
            visible.append(link_data(session, link, _role(access)))
        except ContractError as error:
            if error.status_code != 404:
                raise
    return visible


def get_link(
    session: Session, *, actor: User, link_id: uuid.UUID
) -> ClaimEvidenceLinkPublic:
    link = session.get(ClaimEvidenceLink, link_id)
    if link is None:
        raise _not_found()
    access = project_service.authorize_project(
        session,
        project_id=link.project_id,
        actor=actor,
        action="evidence.read",
    )
    return link_data(session, link, _role(access))


def transition_link(
    session: Session,
    *,
    actor: User,
    link_id: uuid.UUID,
    expected_lock_version: int,
    payload: ClaimEvidenceLinkTransition,
    idempotency_key: str,
) -> project_service.OperationResult:
    link = session.exec(
        select(ClaimEvidenceLink)
        .where(ClaimEvidenceLink.id == link_id)
        .with_for_update()
    ).first()
    if link is None:
        raise _not_found()
    action = {
        EvidenceLinkStatus.ACTIVE: "evidence.link.confirm",
        EvidenceLinkStatus.REJECTED: "evidence.link.reject",
        EvidenceLinkStatus.INVALIDATED: "evidence.link.invalidate",
    }.get(payload.status)
    if action is None:
        raise ContractError(
            status_code=422,
            code="INVALID_LINK_TRANSITION",
            message="Link transition is not supported.",
        )
    access = project_service.authorize_project(
        session, project_id=link.project_id, actor=actor, action=action, for_update=True
    )
    if link.lock_version != expected_lock_version:
        raise ContractError(
            status_code=412,
            code="PRECONDITION_FAILED",
            message="Evidence link version is stale.",
        )
    digest = project_service.request_hash(payload)
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=link.project_id,
        method="PATCH",
        path_template=TRANSITION_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay:
        return replay
    allowed = {
        EvidenceLinkStatus.SUGGESTED: {
            EvidenceLinkStatus.ACTIVE,
            EvidenceLinkStatus.REJECTED,
            EvidenceLinkStatus.INVALIDATED,
        },
        EvidenceLinkStatus.ACTIVE: {EvidenceLinkStatus.INVALIDATED},
    }
    if payload.status not in allowed.get(link.status, set()):
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Evidence link cannot transition from its current state.",
        )
    before = {"status": link.status, "lock_version": link.lock_version}
    now = get_datetime_utc()
    if payload.status == EvidenceLinkStatus.ACTIVE:
        reference = resolve_evidence(
            session,
            project_id=link.project_id,
            object_type=link.evidence_object_type,
            object_id=link.evidence_object_id,
        )
        _validate_reference(reference, active=True)
        if reference.source_hash != link.source_hash:
            raise ContractError(
                status_code=409,
                code="EVIDENCE_HASH_MISMATCH",
                message="Evidence source changed after link creation.",
            )
        link.confirmed_by_user_id = actor.id
        link.confirmed_at = now
    if payload.status == EvidenceLinkStatus.INVALIDATED:
        if not payload.reason:
            raise ContractError(
                status_code=422,
                code="INVALIDATION_REASON_REQUIRED",
                message="Invalidation reason is required.",
            )
        link.invalidated_at = now
        link.invalidation_reason = payload.reason
    link.status = payload.status
    link.lock_version += 1
    link.updated_at = now
    session.add(link)
    _audit(
        session,
        project_id=link.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action=f"CLAIM_EVIDENCE_LINK_{payload.status}",
        link=link,
        before=before,
        reason=payload.reason,
    )
    result = project_service.OperationResult(
        data=jsonable_encoder(link_data(session, link, _role(access))), status_code=200
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=link.project_id,
        method="PATCH",
        path_template=TRANSITION_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result
