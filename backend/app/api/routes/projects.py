import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query, Response
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError, ContractErrorResponse
from app.core.observability import current_request_id
from app.models import (
    AuditActorType,
    AuditOutcome,
    ProjectMemberRole,
    ProjectStage,
    ProjectStatus,
    ProjectType,
)
from app.projects import service
from app.projects.schemas import (
    AuditListEnvelope,
    MemberAdd,
    MemberEnvelope,
    MemberListEnvelope,
    MemberTransferEnvelope,
    MemberUpdate,
    ProjectCreate,
    ProjectEnvelope,
    ProjectListEnvelope,
    ProjectOverviewEnvelope,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["projects"])
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


def _if_match_version(value: str | None) -> int:
    if value is None:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match is required for project updates.",
        )
    normalized = value.strip().strip('"')
    try:
        version = int(normalized)
    except ValueError:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a project lock version.",
        )
    if version < 1:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a positive project lock version.",
        )
    return version


@router.post(
    "",
    response_model=ProjectEnvelope,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def create_project(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_in: ProjectCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.create_project(
        session,
        actor=current_user,
        payload=project_in,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.data,
            "meta": _meta(replayed=result.idempotency_replayed),
        },
    )


@router.get("", response_model=ProjectListEnvelope, responses=ERROR_RESPONSES)
def list_projects(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    status: ProjectStatus | None = None,
    current_stage: ProjectStage | None = None,
    project_type: ProjectType | None = None,
    q: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: str = "created_at",
    order: str = "desc",
) -> dict[str, Any]:
    data, pagination = service.list_projects(
        session,
        actor=current_user,
        status=status,
        current_stage=current_stage,
        project_type=project_type,
        q=q,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
    )
    return {"data": data, "pagination": pagination, "meta": _meta()}


@router.get("/{project_id}", response_model=ProjectEnvelope, responses=ERROR_RESPONSES)
def get_project(
    *, session: SessionDep, current_user: CurrentUser, project_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_project(session, actor=current_user, project_id=project_id),
        "meta": _meta(),
    }


@router.patch(
    "/{project_id}", response_model=ProjectEnvelope, responses=ERROR_RESPONSES
)
def update_project(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, Any]:
    data = service.update_project(
        session,
        actor=current_user,
        project_id=project_id,
        payload=project_in,
        expected_lock_version=_if_match_version(if_match),
    )
    return {"data": data, "meta": _meta()}


@router.get(
    "/{project_id}/overview",
    response_model=ProjectOverviewEnvelope,
    responses=ERROR_RESPONSES,
)
def get_project_overview(
    *, session: SessionDep, current_user: CurrentUser, project_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.project_overview(
            session, actor=current_user, project_id=project_id
        ),
        "meta": _meta(),
    }


@router.post(
    "/{project_id}/archive",
    response_model=ProjectEnvelope,
    responses=ERROR_RESPONSES,
)
def archive_project(
    *, session: SessionDep, current_user: CurrentUser, project_id: uuid.UUID
) -> dict[str, Any]:
    data = service.transition_project_status(
        session,
        actor=current_user,
        project_id=project_id,
        target_status=ProjectStatus.ARCHIVED,
    )
    return {"data": data, "meta": _meta()}


@router.post(
    "/{project_id}/restore",
    response_model=ProjectEnvelope,
    responses=ERROR_RESPONSES,
)
def restore_project(
    *, session: SessionDep, current_user: CurrentUser, project_id: uuid.UUID
) -> dict[str, Any]:
    data = service.transition_project_status(
        session,
        actor=current_user,
        project_id=project_id,
        target_status=ProjectStatus.ACTIVE,
    )
    return {"data": data, "meta": _meta()}


@router.get(
    "/{project_id}/members",
    response_model=MemberListEnvelope,
    responses=ERROR_RESPONSES,
)
def list_project_members(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    role: ProjectMemberRole | None = None,
    q: str | None = Query(default=None, max_length=255),
    include_removed: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    data, pagination = service.list_members(
        session,
        actor=current_user,
        project_id=project_id,
        role=role,
        q=q,
        include_removed=include_removed,
        page=page,
        page_size=page_size,
    )
    return {"data": data, "pagination": pagination, "meta": _meta()}


@router.post(
    "/{project_id}/members",
    response_model=MemberEnvelope,
    status_code=201,
    responses={**ERROR_RESPONSES, 200: {"model": MemberEnvelope}},
)
def add_project_member(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    member_in: MemberAdd,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.add_member(
        session,
        actor=current_user,
        project_id=project_id,
        payload=member_in,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.data,
            "meta": _meta(replayed=result.idempotency_replayed),
        },
    )


@router.patch(
    "/{project_id}/members/{member_id}",
    response_model=MemberEnvelope | MemberTransferEnvelope,
    responses=ERROR_RESPONSES,
)
def update_project_member(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    member_id: uuid.UUID,
    member_in: MemberUpdate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.update_member(
        session,
        actor=current_user,
        project_id=project_id,
        member_id=member_id,
        payload=member_in,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.data,
            "meta": _meta(replayed=result.idempotency_replayed),
        },
    )


@router.delete(
    "/{project_id}/members/{member_id}",
    status_code=204,
    responses=ERROR_RESPONSES,
)
def remove_project_member(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    member_id: uuid.UUID,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> Response:
    service.remove_member(
        session,
        actor=current_user,
        project_id=project_id,
        member_id=member_id,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return Response(status_code=204)


@router.get(
    "/{project_id}/audit-logs",
    response_model=AuditListEnvelope,
    responses=ERROR_RESPONSES,
)
def list_project_audit_logs(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    actor_type: AuditActorType | None = None,
    action: str | None = Query(default=None, max_length=100),
    object_type: str | None = Query(default=None, max_length=100),
    object_id: uuid.UUID | None = None,
    outcome: AuditOutcome | None = None,
    request_id: str | None = Query(default=None, max_length=64),
    job_id: uuid.UUID | None = None,
    approval_id: uuid.UUID | None = None,
    from_time: Annotated[datetime | None, Query(alias="from")] = None,
    to_time: Annotated[datetime | None, Query(alias="to")] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    data, pagination = service.list_audit_logs(
        session,
        actor=current_user,
        project_id=project_id,
        actor_type=actor_type,
        action=action,
        object_type=object_type,
        object_id=object_id,
        outcome=outcome,
        request_id=request_id,
        job_id=job_id,
        approval_id=approval_id,
        from_time=from_time,
        to_time=to_time,
        page=page,
        page_size=page_size,
    )
    return {"data": data, "pagination": pagination, "meta": _meta()}
