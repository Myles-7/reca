from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Header

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError
from app.api.m5_responses import (
    FigureApprovalEnvelope,
    FigureEnvelope,
    FigureIssuesEnvelope,
    FigurePlanEnvelope,
    FigureRecommendationEnvelope,
    FigureRenderRequestEnvelope,
    FigureRenderRunEnvelope,
)
from app.artifacts.schemas import ArtifactDownloadEnvelope
from app.core.observability import current_request_id
from app.figures import service
from app.figures.schemas import (
    FigurePlanCreate,
    FigureRecommendationRequest,
    FigureRenderCreate,
)
from app.jobs.dispatcher import dispatcher

router = APIRouter(tags=["figures"])


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


@router.post(
    "/projects/{project_id}/figure-plans",
    status_code=201,
    response_model=FigurePlanEnvelope,
)
def create_figure_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    payload: FigurePlanCreate,
) -> dict[str, Any]:
    return {
        "data": service.create_plan(
            session, actor=current_user, project_id=project_id, payload=payload
        ),
        "meta": _meta(),
    }


@router.get("/figure-plans/{plan_id}", response_model=FigurePlanEnvelope)
def get_figure_plan(
    *, session: SessionDep, current_user: CurrentUser, plan_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_plan(session, actor=current_user, plan_id=plan_id),
        "meta": _meta(),
    }


@router.post(
    "/projects/{project_id}/figure-recommendations",
    response_model=FigureRecommendationEnvelope,
)
def get_figure_recommendations(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    payload: FigureRecommendationRequest,
) -> dict[str, Any]:
    del payload
    from app.projects import service as project_service

    project_service.authorize_project(
        session, project_id=project_id, actor=current_user, action="figure.read"
    )
    return {"data": service.recommendation(), "meta": _meta()}


@router.post(
    "/figure-plans/{plan_id}/render-runs",
    status_code=202,
    response_model=FigureRenderRequestEnvelope,
)
def render_figure_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    payload: FigureRenderCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = service.create_render_run(
        session,
        actor=current_user,
        plan_id=plan_id,
        payload=payload,
        idempotency_key=_required_key(idempotency_key),
        dispatcher=dispatcher,
    )
    return {
        "data": result.data,
        "meta": _meta(replayed=result.idempotency_replayed),
    }


@router.get("/figure-render-runs/{run_id}", response_model=FigureRenderRunEnvelope)
def get_figure_render_run(
    *, session: SessionDep, current_user: CurrentUser, run_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_render_run(session, actor=current_user, run_id=run_id),
        "meta": _meta(),
    }


@router.get("/figures/{figure_id}", response_model=FigureEnvelope)
def get_figure(
    *, session: SessionDep, current_user: CurrentUser, figure_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_figure(session, actor=current_user, figure_id=figure_id),
        "meta": _meta(),
    }


@router.get(
    "/figures/{figure_id}/validation-issues", response_model=FigureIssuesEnvelope
)
def get_figure_validation_issues(
    *, session: SessionDep, current_user: CurrentUser, figure_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_issues(session, actor=current_user, figure_id=figure_id),
        "meta": _meta(),
    }


@router.post(
    "/figures/{figure_id}/approval-requests",
    status_code=201,
    response_model=FigureApprovalEnvelope,
)
def request_figure_confirmation(
    *, session: SessionDep, current_user: CurrentUser, figure_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.request_confirmation(
            session, actor=current_user, figure_id=figure_id
        ),
        "meta": _meta(),
    }


@router.get(
    "/figures/{figure_id}/downloads/{format_name}",
    response_model=ArtifactDownloadEnvelope,
)
def download_figure_format(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    figure_id: uuid.UUID,
    format_name: str,
) -> dict[str, Any]:
    return {
        "data": service.authorize_format_download(
            session,
            actor=current_user,
            figure_id=figure_id,
            format_name=format_name,
        ),
        "meta": _meta(),
    }
