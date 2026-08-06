from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError, ContractErrorResponse
from app.core.observability import current_request_id
from app.exports import service
from app.exports.schemas import (
    ExportCreateEnvelope,
    ExportEnvelope,
    ExportReadinessEnvelope,
    ExportReadinessRequest,
    ReproPackageCreate,
    ReproPackageDownloadEnvelope,
    ReproPackageEnvelope,
    ReproPackageHistoryEnvelope,
)
from app.jobs.dispatcher import dispatcher

router = APIRouter(tags=["exports"])

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ContractErrorResponse, "description": "Malformed request."},
    403: {"model": ContractErrorResponse, "description": "Action not allowed."},
    404: {"model": ContractErrorResponse, "description": "Resource not found."},
    409: {"model": ContractErrorResponse, "description": "State conflict."},
    412: {"model": ContractErrorResponse, "description": "Stale If-Match."},
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


@router.post(
    "/projects/{project_id}/exports/readiness-check",
    response_model=ExportReadinessEnvelope,
    responses=ERROR_RESPONSES,
)
def readiness_check(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    payload: ExportReadinessRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.readiness_check(
        session,
        actor=current_user,
        project_id=project_id,
        request=payload,
        idempotency_key=_required_key(idempotency_key),
    )
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.data,
            "meta": _meta(replayed=result.idempotency_replayed),
        },
    )


@router.post(
    "/projects/{project_id}/exports/repro-package",
    response_model=ExportCreateEnvelope,
    responses=ERROR_RESPONSES,
    status_code=202,
)
def create_repro_package(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    payload: ReproPackageCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.create_repro_package_export(
        session,
        actor=current_user,
        project_id=project_id,
        request=payload,
        idempotency_key=_required_key(idempotency_key),
        dispatcher=dispatcher,
    )
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.data,
            "meta": _meta(replayed=result.idempotency_replayed),
        },
    )


@router.get(
    "/exports/{export_id}", response_model=ExportEnvelope, responses=ERROR_RESPONSES
)
def get_export(
    *, session: SessionDep, current_user: CurrentUser, export_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_export(session, actor=current_user, export_id=export_id),
        "meta": _meta(),
    }


@router.get(
    "/projects/{project_id}/repro-packages",
    response_model=ReproPackageHistoryEnvelope,
    responses=ERROR_RESPONSES,
)
def list_repro_packages(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    data, pagination = service.list_repro_packages(
        session,
        actor=current_user,
        project_id=project_id,
        page=page,
        page_size=page_size,
    )
    return {"data": data, "pagination": pagination, "meta": _meta()}


@router.get(
    "/repro-packages/{package_id}",
    response_model=ReproPackageEnvelope,
    responses=ERROR_RESPONSES,
)
def get_repro_package(
    *, session: SessionDep, current_user: CurrentUser, package_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_repro_package(
            session, actor=current_user, package_id=package_id
        ),
        "meta": _meta(),
    }


@router.get(
    "/repro-packages/{package_id}/download",
    response_model=ReproPackageDownloadEnvelope,
    responses=ERROR_RESPONSES,
)
def download_repro_package(
    *, session: SessionDep, current_user: CurrentUser, package_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.authorize_package_download(
            session, actor=current_user, package_id=package_id
        ),
        "meta": _meta(),
    }
