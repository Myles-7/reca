from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Header, Response

from app.analysis import service
from app.analysis.schemas import (
    AnalysisInvalidate,
    AnalysisPlanCreate,
    AnalysisPlanUpdate,
    AnalysisRunCreate,
)
from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError
from app.api.m5_responses import (
    AnalysisApprovalEnvelope,
    AnalysisPlanEnvelope,
    AnalysisResultsEnvelope,
    AnalysisRunEnvelope,
    AnalysisRunRequestEnvelope,
)
from app.core.observability import current_request_id
from app.jobs.dispatcher import dispatcher

router = APIRouter(tags=["analysis"])


def _meta(*, replayed: bool = False) -> dict[str, Any]:
    return {
        "request_id": current_request_id(),
        "schema_version": "1.0",
        "idempotency_replayed": replayed,
    }


def _required_key(value: str | None) -> str:
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


def _if_match(value: str | None) -> int:
    if value is None:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match is required for AnalysisPlan updates.",
        )
    try:
        result = int(value.strip().strip('"'))
    except ValueError as error:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a positive lock version.",
        ) from error
    if result < 1:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a positive lock version.",
        )
    return result


@router.post(
    "/projects/{project_id}/analysis-plans",
    status_code=201,
    response_model=AnalysisPlanEnvelope,
)
def create_analysis_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    payload: AnalysisPlanCreate,
) -> dict[str, Any]:
    return {
        "data": service.create_plan(
            session, actor=current_user, project_id=project_id, payload=payload
        ),
        "meta": _meta(),
    }


@router.get("/analysis-plans/{plan_id}", response_model=AnalysisPlanEnvelope)
def get_analysis_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    response: Response,
) -> dict[str, Any]:
    data = service.get_plan(session, actor=current_user, plan_id=plan_id)
    response.headers["ETag"] = f'"{data["lock_version"]}"'
    return {"data": data, "meta": _meta()}


@router.patch("/analysis-plans/{plan_id}", response_model=AnalysisPlanEnvelope)
def update_analysis_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    payload: AnalysisPlanUpdate,
    response: Response,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, Any]:
    data = service.update_plan(
        session,
        actor=current_user,
        plan_id=plan_id,
        payload=payload,
        expected_lock_version=_if_match(if_match),
    )
    response.headers["ETag"] = f'"{data["lock_version"]}"'
    return {"data": data, "meta": _meta()}


@router.post("/analysis-plans/{plan_id}/validate", response_model=AnalysisPlanEnvelope)
def validate_analysis_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = service.validate_plan(
        session,
        actor=current_user,
        plan_id=plan_id,
        idempotency_key=_required_key(idempotency_key),
    )
    return {"data": result.data, "meta": _meta(replayed=result.idempotency_replayed)}


@router.post(
    "/analysis-plans/{plan_id}/approval-requests",
    status_code=201,
    response_model=AnalysisApprovalEnvelope,
)
def request_analysis_approval(
    *, session: SessionDep, current_user: CurrentUser, plan_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.request_approval(session, actor=current_user, plan_id=plan_id),
        "meta": _meta(),
    }


@router.post(
    "/analysis-plans/{plan_id}/runs",
    status_code=202,
    response_model=AnalysisRunRequestEnvelope,
)
def run_analysis_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    payload: AnalysisRunCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = service.create_run(
        session,
        actor=current_user,
        plan_id=plan_id,
        payload=payload,
        idempotency_key=_required_key(idempotency_key),
        dispatcher=dispatcher,
    )
    return {"data": result.data, "meta": _meta(replayed=result.idempotency_replayed)}


@router.get("/analysis-runs/{run_id}", response_model=AnalysisRunEnvelope)
def get_analysis_run(
    *, session: SessionDep, current_user: CurrentUser, run_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_run(session, actor=current_user, run_id=run_id),
        "meta": _meta(),
    }


@router.get("/analysis-runs/{run_id}/results", response_model=AnalysisResultsEnvelope)
def get_analysis_results(
    *, session: SessionDep, current_user: CurrentUser, run_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_results(session, actor=current_user, run_id=run_id),
        "meta": _meta(),
    }


@router.post("/analysis-runs/{run_id}/invalidate", response_model=AnalysisRunEnvelope)
def invalidate_analysis_run(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    run_id: uuid.UUID,
    payload: AnalysisInvalidate,
) -> dict[str, Any]:
    return {
        "data": service.invalidate_run(
            session, actor=current_user, run_id=run_id, payload=payload
        ),
        "meta": _meta(),
    }
