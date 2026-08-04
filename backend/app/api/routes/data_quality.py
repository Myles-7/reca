from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError
from app.api.m4_responses import (
    DataQualityIssueEnvelope,
    DataQualityRunEnvelope,
    QualityIssuesEnvelope,
    QualityRunRequestEnvelope,
)
from app.core.observability import current_request_id
from app.data_quality import service
from app.data_quality.schemas import (
    QualityIssueAcknowledge,
    QualityIssueIgnore,
    QualityRunCreate,
)
from app.jobs.dispatcher import dispatcher
from app.models import (
    DataQualityIssueStatus,
    DataQualityIssueType,
    DataQualitySeverity,
)

router = APIRouter(tags=["data-quality"])


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


@router.post(
    "/dataset-versions/{version_id}/quality-runs",
    status_code=202,
    response_model=QualityRunRequestEnvelope,
)
def request_quality_run(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    payload: QualityRunCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = service.request_quality_run(
        session,
        actor=current_user,
        version_id=version_id,
        payload=payload,
        idempotency_key=_required_idempotency_key(idempotency_key),
        dispatcher=dispatcher,
    )
    return {
        "data": result.data,
        "meta": _meta(replayed=result.idempotency_replayed),
    }


@router.get("/data-quality-runs/{run_id}", response_model=DataQualityRunEnvelope)
def get_quality_run(
    *, session: SessionDep, current_user: CurrentUser, run_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_run(session, actor=current_user, run_id=run_id),
        "meta": _meta(),
    }


@router.get("/data-quality-runs/{run_id}/issues", response_model=QualityIssuesEnvelope)
def list_quality_issues(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    run_id: uuid.UUID,
    severity: DataQualitySeverity | None = None,
    issue_type: DataQualityIssueType | None = None,
    status: DataQualityIssueStatus | None = None,
    column_id: uuid.UUID | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict[str, Any]:
    data, pagination = service.list_issues(
        session,
        actor=current_user,
        run_id=run_id,
        severity=severity,
        issue_type=issue_type,
        status=status,
        column_id=column_id,
        page=page,
        page_size=page_size,
    )
    return {"data": data, "pagination": pagination, "meta": _meta()}


@router.post(
    "/data-quality-issues/{issue_id}/acknowledge",
    response_model=DataQualityIssueEnvelope,
)
def acknowledge_quality_issue(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    issue_id: uuid.UUID,
    payload: QualityIssueAcknowledge,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = service.acknowledge_issue(
        session,
        actor=current_user,
        issue_id=issue_id,
        payload=payload,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return {
        "data": result.data,
        "meta": _meta(replayed=result.idempotency_replayed),
    }


@router.post(
    "/data-quality-issues/{issue_id}/ignore",
    response_model=DataQualityIssueEnvelope,
)
def ignore_quality_issue(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    issue_id: uuid.UUID,
    payload: QualityIssueIgnore,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = service.ignore_issue(
        session,
        actor=current_user,
        issue_id=issue_id,
        payload=payload,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return {
        "data": result.data,
        "meta": _meta(replayed=result.idempotency_replayed),
    }
