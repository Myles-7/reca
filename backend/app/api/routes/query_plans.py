import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError, ContractErrorResponse
from app.core.observability import current_request_id
from app.jobs.dispatcher import dispatcher
from app.jobs.schemas import JobEnvelope
from app.query_plans import generation, service
from app.query_plans.schemas import (
    QueryPlanCreate,
    QueryPlanEnvelope,
    QueryPlanGenerateRequest,
    QueryPlanUpdate,
)

router = APIRouter(tags=["query-plans"])
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ContractErrorResponse},
    403: {"model": ContractErrorResponse},
    404: {"model": ContractErrorResponse},
    409: {"model": ContractErrorResponse},
    422: {"model": ContractErrorResponse},
    503: {"model": ContractErrorResponse},
}


def _meta(*, replayed: bool = False) -> dict[str, Any]:
    return {
        "request_id": current_request_id(),
        "schema_version": "1.0",
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
            message="If-Match is required for QueryPlan updates.",
        )
    normalized = value.strip().strip('"')
    try:
        version = int(normalized)
    except ValueError as exc:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a QueryPlan lock version.",
        ) from exc
    if version < 1:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a positive lock version.",
        )
    return version


@router.post(
    "/projects/{project_id}/query-plans",
    response_model=QueryPlanEnvelope,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def create_query_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    query_plan_in: QueryPlanCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.create_query_plan_command(
        session,
        actor=current_user,
        project_id=project_id,
        payload=query_plan_in,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.data,
            "meta": _meta(replayed=result.idempotency_replayed),
        },
    )


@router.get(
    "/query-plans/{query_plan_id}",
    response_model=QueryPlanEnvelope,
    responses=ERROR_RESPONSES,
)
def get_query_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    query_plan_id: uuid.UUID,
) -> dict[str, Any]:
    return {
        "data": service.get_query_plan(
            session, actor=current_user, query_plan_id=query_plan_id
        ),
        "meta": _meta(),
    }


@router.patch(
    "/query-plans/{query_plan_id}",
    response_model=QueryPlanEnvelope,
    responses=ERROR_RESPONSES,
)
def update_query_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    query_plan_id: uuid.UUID,
    query_plan_in: QueryPlanUpdate,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, Any]:
    return {
        "data": service.update_query_plan(
            session,
            actor=current_user,
            query_plan_id=query_plan_id,
            expected_lock_version=_if_match_version(if_match),
            fields=query_plan_in.fields,
            change_reason=query_plan_in.change_reason,
        ),
        "meta": _meta(),
    }


@router.post(
    "/query-plans/{query_plan_id}/generate",
    response_model=JobEnvelope,
    status_code=202,
    responses=ERROR_RESPONSES,
)
def generate_query_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    query_plan_id: uuid.UUID,
    generate_in: QueryPlanGenerateRequest | None = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    del generate_in
    result = generation.request_generation_job(
        session,
        actor=current_user,
        query_plan_id=query_plan_id,
        idempotency_key=_required_idempotency_key(idempotency_key),
        dispatcher=dispatcher,
    )
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.data,
            "meta": _meta(replayed=result.idempotency_replayed),
        },
    )
