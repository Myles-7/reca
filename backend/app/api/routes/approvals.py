import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError, ContractErrorResponse
from app.approvals import service
from app.approvals.schemas import (
    ApprovalDecisionRequest,
    ApprovalEnvelope,
    ApprovalListEnvelope,
    ApprovalRejectRequest,
)
from app.core.observability import current_request_id
from app.models import ApprovalStatus, ApprovalType, AuditActorType

router = APIRouter(tags=["approvals"])
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ContractErrorResponse},
    403: {"model": ContractErrorResponse},
    404: {"model": ContractErrorResponse},
    409: {"model": ContractErrorResponse},
    422: {"model": ContractErrorResponse},
}


def _meta(*, replayed: bool = False) -> dict[str, Any]:
    return {
        "request_id": current_request_id(),
        "schema_version": service.SCHEMA_VERSION,
        "idempotency_replayed": replayed,
    }


def _required_idempotency_key(value: str | None) -> str:
    if value is None or not value.strip():
        raise ContractError(
            status_code=400,
            code="MISSING_IDEMPOTENCY_KEY",
            message="Idempotency-Key is required for this operation.",
        )
    if len(value) > 255:
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Idempotency-Key exceeds the maximum length.",
        )
    return value


@router.get(
    "/projects/{project_id}/approvals",
    response_model=ApprovalListEnvelope,
    response_model_exclude_none=True,
    responses=ERROR_RESPONSES,
)
def list_project_approvals(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    status: ApprovalStatus | None = None,
    approval_type: ApprovalType | None = None,
    target_object_type: str | None = Query(default=None, max_length=100),
    requested_by_actor_type: AuditActorType | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    data, pagination = service.list_approvals(
        session,
        actor=current_user,
        project_id=project_id,
        status=status,
        approval_type=approval_type,
        target_object_type=target_object_type,
        requested_by_actor_type=requested_by_actor_type,
        page=page,
        page_size=page_size,
    )
    return {"data": data, "pagination": pagination, "meta": _meta()}


@router.get(
    "/approvals/{approval_id}",
    response_model=ApprovalEnvelope,
    response_model_exclude_none=True,
    responses=ERROR_RESPONSES,
)
def get_approval(
    *, session: SessionDep, current_user: CurrentUser, approval_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_approval(
            session, actor=current_user, approval_id=approval_id
        ),
        "meta": _meta(),
    }


@router.post(
    "/approvals/{approval_id}/approve",
    response_model=ApprovalEnvelope,
    response_model_exclude_none=True,
    responses=ERROR_RESPONSES,
)
def approve(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    approval_id: uuid.UUID,
    decision_in: ApprovalDecisionRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.decide_approval(
        session,
        actor=current_user,
        approval_id=approval_id,
        decision=ApprovalStatus.APPROVED,
        decision_reason=decision_in.decision_reason,
        item_decisions=decision_in.item_decisions,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.data,
            "meta": _meta(replayed=result.idempotency_replayed),
        },
    )


@router.post(
    "/approvals/{approval_id}/reject",
    response_model=ApprovalEnvelope,
    response_model_exclude_none=True,
    responses=ERROR_RESPONSES,
)
def reject(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    approval_id: uuid.UUID,
    decision_in: ApprovalRejectRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.decide_approval(
        session,
        actor=current_user,
        approval_id=approval_id,
        decision=ApprovalStatus.REJECTED,
        decision_reason=decision_in.decision_reason,
        item_decisions=decision_in.item_decisions,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.data,
            "meta": _meta(replayed=result.idempotency_replayed),
        },
    )


@router.post(
    "/approvals/{approval_id}/cancel",
    response_model=ApprovalEnvelope,
    response_model_exclude_none=True,
    responses=ERROR_RESPONSES,
)
def cancel(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    approval_id: uuid.UUID,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.cancel_approval(
        session,
        actor=current_user,
        approval_id=approval_id,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.data,
            "meta": _meta(replayed=result.idempotency_replayed),
        },
    )
