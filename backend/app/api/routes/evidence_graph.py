from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query, Response

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError, ContractErrorResponse
from app.core.observability import current_request_id
from app.evidence_graph import auditors, projector, service
from app.evidence_graph.schemas import (
    ClaimAuditCreate,
    ClaimAuditEnvelope,
    ClaimAuditRequestEnvelope,
    ClaimEvidenceLinkCreate,
    ClaimEvidenceLinkEnvelope,
    ClaimEvidenceLinkListEnvelope,
    ClaimEvidenceLinkTransition,
    EvidenceGraphEnvelope,
)
from app.jobs.dispatcher import dispatcher

router = APIRouter(tags=["evidence-graph"])

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ContractErrorResponse, "description": "Malformed request."},
    403: {"model": ContractErrorResponse, "description": "Action not allowed."},
    404: {"model": ContractErrorResponse, "description": "Resource not found."},
    409: {"model": ContractErrorResponse, "description": "State conflict."},
    412: {"model": ContractErrorResponse, "description": "Stale If-Match."},
    428: {"model": ContractErrorResponse, "description": "If-Match is required."},
    422: {"model": ContractErrorResponse, "description": "Invalid contract input."},
}


def _meta(*, replayed: bool = False) -> dict[str, Any]:
    return {"request_id": current_request_id(), "idempotency_replayed": replayed}


def _required_key(value: str | None) -> str:
    if value is None or not value.strip():
        raise ContractError(
            status_code=400,
            code="IDEMPOTENCY_KEY_REQUIRED",
            message="Idempotency-Key is required for this operation.",
        )
    if len(value) > 255:
        raise ContractError(
            status_code=400,
            code="IDEMPOTENCY_KEY_INVALID",
            message="Idempotency-Key exceeds the maximum length.",
        )
    return value


def _if_match(value: str | None) -> int:
    if value is None or not value.strip():
        raise ContractError(
            status_code=428,
            code="PRECONDITION_REQUIRED",
            message="If-Match is required for evidence link transitions.",
        )
    raw = value.strip().strip("W/").strip('"')
    try:
        parsed = int(raw)
    except ValueError:
        parsed = 0
    if parsed < 1:
        raise ContractError(
            status_code=400,
            code="INVALID_IF_MATCH",
            message="If-Match must contain a positive lock version.",
        )
    return parsed


@router.post(
    "/claims/{claim_id}/evidence-links",
    response_model=ClaimEvidenceLinkEnvelope,
    responses=ERROR_RESPONSES,
    status_code=201,
)
def create_evidence_link(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    claim_id: uuid.UUID,
    payload: ClaimEvidenceLinkCreate,
    response: Response,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = service.create_link(
        session,
        actor=current_user,
        claim_id=claim_id,
        payload=payload,
        idempotency_key=_required_key(idempotency_key),
    )
    response.status_code = result.status_code
    return {"data": result.data, "meta": _meta(replayed=result.idempotency_replayed)}


@router.get(
    "/claims/{claim_id}/evidence-links",
    response_model=ClaimEvidenceLinkListEnvelope,
    responses=ERROR_RESPONSES,
)
def list_evidence_links(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    claim_id: uuid.UUID,
    include_invalidated: bool = False,
) -> dict[str, Any]:
    return {
        "data": service.list_links(
            session,
            actor=current_user,
            claim_id=claim_id,
            include_invalidated=include_invalidated,
        ),
        "meta": _meta(),
    }


@router.patch(
    "/evidence-links/{link_id}",
    response_model=ClaimEvidenceLinkEnvelope,
    responses=ERROR_RESPONSES,
)
def transition_evidence_link(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    link_id: uuid.UUID,
    payload: ClaimEvidenceLinkTransition,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = service.transition_link(
        session,
        actor=current_user,
        link_id=link_id,
        expected_lock_version=_if_match(if_match),
        payload=payload,
        idempotency_key=_required_key(idempotency_key),
    )
    return {"data": result.data, "meta": _meta(replayed=result.idempotency_replayed)}


@router.get(
    "/evidence-links/{link_id}",
    response_model=ClaimEvidenceLinkEnvelope,
    responses=ERROR_RESPONSES,
)
def get_evidence_link(
    *, session: SessionDep, current_user: CurrentUser, link_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_link(session, actor=current_user, link_id=link_id),
        "meta": _meta(),
    }


@router.get(
    "/projects/{project_id}/evidence-graph",
    response_model=EvidenceGraphEnvelope,
    responses=ERROR_RESPONSES,
)
def get_evidence_graph(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    root_claim_id: uuid.UUID | None = None,
    depth: int = 2,
    node_types: Annotated[list[str] | None, Query()] = None,
    risk_only: bool = False,
    include_invalidated: bool = False,
    cursor: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    data = projector.project_graph(
        session,
        actor=current_user,
        project_id=project_id,
        root_claim_id=root_claim_id,
        depth=depth,
        node_types=set(node_types) if node_types else None,
        risk_only=risk_only,
        include_invalidated=include_invalidated,
        cursor=cursor,
        limit=limit,
    )
    return {"data": data, "meta": _meta()}


@router.post(
    "/claims/{claim_id}/audits",
    response_model=ClaimAuditRequestEnvelope,
    responses=ERROR_RESPONSES,
    status_code=202,
)
def create_claim_audit(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    claim_id: uuid.UUID,
    payload: ClaimAuditCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = auditors.request_claim_audit(
        session,
        actor=current_user,
        claim_id=claim_id,
        payload=payload,
        idempotency_key=_required_key(idempotency_key),
        dispatcher=dispatcher,
    )
    return {"data": result.data, "meta": _meta(replayed=result.idempotency_replayed)}


@router.get(
    "/audits/{audit_id}",
    response_model=ClaimAuditEnvelope,
    responses=ERROR_RESPONSES,
)
def get_audit(
    *, session: SessionDep, current_user: CurrentUser, audit_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": auditors.get_audit(session, actor=current_user, audit_id=audit_id),
        "meta": _meta(),
    }
