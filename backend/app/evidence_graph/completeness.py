from __future__ import annotations

from sqlmodel import Session, col, select

from app.api.errors import ContractError
from app.models import (
    Claim,
    ClaimEvidenceLink,
    ClaimStatus,
    EvidenceLinkStatus,
    EvidenceObjectType,
)

from .resolvers import resolve_evidence
from .schemas import (
    CompletenessItem,
    CompletenessStatus,
    EvidenceCompleteness,
)

RULE_SET_VERSION = "m7-evidence-completeness/1.0"


def _item(
    code: str,
    status: CompletenessStatus,
    *,
    ids: list[str] | None = None,
    limitations: list[str] | None = None,
    actions: list[str] | None = None,
) -> CompletenessItem:
    return CompletenessItem(
        code=code,
        status=status,
        source_object_ids=ids or [],
        limitations=limitations or [],
        missing_actions=actions or [],
    )


def evaluate_claim(session: Session, *, claim: Claim) -> EvidenceCompleteness:
    links = session.exec(
        select(ClaimEvidenceLink).where(
            ClaimEvidenceLink.project_id == claim.project_id,
            ClaimEvidenceLink.claim_id == claim.id,
            col(ClaimEvidenceLink.status).in_(
                [EvidenceLinkStatus.ACTIVE, EvidenceLinkStatus.SUGGESTED]
            ),
        )
    ).all()
    references = []
    unknown_ids: list[str] = []
    for link in links:
        try:
            references.append(
                (
                    link,
                    resolve_evidence(
                        session,
                        project_id=claim.project_id,
                        object_type=link.evidence_object_type,
                        object_id=link.evidence_object_id,
                    ),
                )
            )
        except ContractError:
            unknown_ids.append(str(link.evidence_object_id))

    active = [
        (link, ref)
        for link, ref in references
        if link.status == EvidenceLinkStatus.ACTIVE
    ]
    types = {link.evidence_object_type for link, _ in active}
    restricted = [str(ref.object_id) for _, ref in active if ref.restricted]
    stale = [str(ref.object_id) for _, ref in active if ref.stale or ref.invalidated]
    items: list[CompletenessItem] = []
    items.append(
        _item(
            "CLAIM_SOURCE",
            CompletenessStatus.STALE
            if claim.status == ClaimStatus.INVALIDATED
            else CompletenessStatus.SATISFIED,
            ids=[str(claim.source_object_id)],
        )
    )
    if unknown_ids:
        items.append(
            _item(
                "EVIDENCE_STATUS",
                CompletenessStatus.UNKNOWN,
                ids=unknown_ids,
                limitations=["One or more evidence references could not be resolved."],
                actions=["refresh-evidence"],
            )
        )
    elif stale:
        items.append(
            _item(
                "EVIDENCE_STATUS",
                CompletenessStatus.STALE,
                ids=stale,
                actions=["replace-stale-evidence"],
            )
        )
    elif restricted:
        items.append(
            _item(
                "EVIDENCE_STATUS",
                CompletenessStatus.RESTRICTED,
                ids=restricted,
                limitations=["Evidence exists but current read scope is insufficient."],
            )
        )
    elif active:
        items.append(
            _item(
                "EVIDENCE_STATUS",
                CompletenessStatus.SATISFIED,
                ids=[str(ref.object_id) for _, ref in active],
            )
        )
    else:
        items.append(
            _item(
                "EVIDENCE_STATUS",
                CompletenessStatus.MISSING,
                actions=["create-evidence-link"],
            )
        )

    located_types = {
        EvidenceObjectType.EVIDENCE_SPAN,
        EvidenceObjectType.LITERATURE_RECORD,
    }
    items.append(
        _item(
            "LOCATED_ORIGINAL_EVIDENCE",
            CompletenessStatus.SATISFIED
            if types & located_types
            else CompletenessStatus.MISSING,
            ids=[
                str(ref.object_id)
                for link, ref in active
                if link.evidence_object_type in located_types
            ],
            actions=[] if types & located_types else ["link-evidence-span"],
        )
    )
    analysis_types = {
        EvidenceObjectType.ANALYSIS_RESULT,
        EvidenceObjectType.ANALYSIS_RUN,
    }
    analysis_applicable = claim.claim_type.value in {
        "STATISTICAL_RESULT",
        "DATA_DESCRIPTION",
        "INTERPRETATION",
        "MANUSCRIPT_STATEMENT",
    }
    items.append(
        _item(
            "ANALYSIS_RESULT",
            (
                CompletenessStatus.SATISFIED
                if types & analysis_types
                else CompletenessStatus.MISSING
            )
            if analysis_applicable
            else CompletenessStatus.NOT_APPLICABLE,
            ids=[
                str(ref.object_id)
                for link, ref in active
                if link.evidence_object_type in analysis_types
            ],
            actions=["link-analysis-result"]
            if analysis_applicable and not types & analysis_types
            else [],
        )
    )
    items.append(
        _item(
            "CLAIM_CONFIRMATION",
            CompletenessStatus.SATISFIED
            if claim.status == ClaimStatus.CONFIRMED
            else CompletenessStatus.MISSING,
            ids=[str(claim.approval_record_id)] if claim.approval_record_id else [],
            actions=[]
            if claim.status == ClaimStatus.CONFIRMED
            else ["request-claim-confirmation"],
        )
    )
    audit_ids = [
        str(ref.object_id)
        for link, ref in active
        if link.evidence_object_type == EvidenceObjectType.AUDIT_RESULT
    ]
    items.append(
        _item(
            "CURRENT_AUDIT",
            CompletenessStatus.SATISFIED if audit_ids else CompletenessStatus.MISSING,
            ids=audit_ids,
            actions=[] if audit_ids else ["run-claim-audit"],
        )
    )
    return EvidenceCompleteness(
        rule_set_version=RULE_SET_VERSION,
        claim_id=claim.id,
        scope={"project_id": str(claim.project_id), "active_link_count": len(active)},
        items=items,
        limitations=[
            "Completeness is a rule checklist, not a scientific quality score."
        ],
    )
