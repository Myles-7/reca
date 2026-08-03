import math
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError, ContractErrorResponse
from app.core.observability import current_request_id
from app.jobs.dispatcher import dispatcher
from app.literature import service
from app.literature.schemas import (
    LiteratureDoiImportRequest,
    LiteratureImportEnvelope,
    LiteratureImportRequest,
    LiteratureRecordEnvelope,
    LiteratureRecordListEnvelope,
    LiteratureSearchAcceptedEnvelope,
    LiteratureSearchCreate,
    LiteratureSearchResultsEnvelope,
)
from app.models import LiteratureDecisionStatus, LiteratureVerificationStatus

router = APIRouter(tags=["literature"])
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ContractErrorResponse},
    403: {"model": ContractErrorResponse},
    404: {"model": ContractErrorResponse},
    409: {"model": ContractErrorResponse},
    422: {"model": ContractErrorResponse},
    429: {"model": ContractErrorResponse},
    502: {"model": ContractErrorResponse},
    503: {"model": ContractErrorResponse},
}


def _meta(*, replayed: bool = False) -> dict[str, Any]:
    return {
        "request_id": current_request_id(),
        "schema_version": "1.0",
        "idempotency_replayed": replayed,
    }


def _pagination(*, page: int, page_size: int, total: int) -> dict[str, Any]:
    total_pages = math.ceil(total / page_size) if total else 0
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
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
    "/query-plans/{query_plan_id}/search-runs",
    response_model=LiteratureSearchAcceptedEnvelope,
    status_code=202,
    responses=ERROR_RESPONSES,
)
def create_search_run(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    query_plan_id: uuid.UUID,
    search_in: LiteratureSearchCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.request_search_job(
        session,
        actor=current_user,
        query_plan_id=query_plan_id,
        payload=search_in,
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


@router.get(
    "/literature-search-runs/{search_run_id}/results",
    response_model=LiteratureSearchResultsEnvelope,
    responses=ERROR_RESPONSES,
)
def get_search_results(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    search_run_id: uuid.UUID,
    verification_status: LiteratureVerificationStatus | None = None,
    open_access_status: str | None = Query(default=None, max_length=100),
    from_year: int | None = Query(default=None, ge=1000, le=9999),
    to_year: int | None = Query(default=None, ge=1000, le=9999),
    q: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    run, results, total, can_update = service.get_search_results(
        session,
        actor=current_user,
        run_id=search_run_id,
        verification_status=verification_status,
        open_access_status=open_access_status,
        from_year=from_year,
        to_year=to_year,
        q=q,
        page=page,
        page_size=page_size,
    )
    return {
        "data": {
            "search_run": service.search_run_data(run, can_update=can_update),
            "results": results,
        },
        "pagination": _pagination(page=page, page_size=page_size, total=total),
        "meta": _meta(),
    }


@router.post(
    "/projects/{project_id}/literature/import",
    response_model=LiteratureImportEnvelope,
    responses=ERROR_RESPONSES,
)
def import_search_candidates(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    import_in: LiteratureImportRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.import_candidates(
        session,
        actor=current_user,
        project_id=project_id,
        payload=import_in,
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
    "/projects/{project_id}/literature/import-doi",
    response_model=LiteratureRecordEnvelope,
    responses=ERROR_RESPONSES,
)
def import_doi(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    import_in: LiteratureDoiImportRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.import_doi(
        session,
        actor=current_user,
        project_id=project_id,
        payload=import_in,
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
    "/projects/{project_id}/literature",
    response_model=LiteratureRecordListEnvelope,
    responses=ERROR_RESPONSES,
)
def list_literature(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    decision: LiteratureDecisionStatus | None = None,
    verification_status: LiteratureVerificationStatus | None = None,
    has_document: bool | None = None,
    year_from: int | None = Query(default=None, ge=1000, le=9999),
    year_to: int | None = Query(default=None, ge=1000, le=9999),
    q: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    records, total, allowed_actions = service.list_literature(
        session,
        actor=current_user,
        project_id=project_id,
        decision=decision,
        verification_status=verification_status,
        has_document=has_document,
        year_from=year_from,
        year_to=year_to,
        q=q,
        page=page,
        page_size=page_size,
    )
    return {
        "data": records,
        "allowed_actions": allowed_actions,
        "pagination": _pagination(page=page, page_size=page_size, total=total),
        "meta": _meta(),
    }


@router.get(
    "/literature/{literature_id}",
    response_model=LiteratureRecordEnvelope,
    responses=ERROR_RESPONSES,
)
def get_literature(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    literature_id: uuid.UUID,
) -> dict[str, Any]:
    return {
        "data": service.get_literature(
            session, actor=current_user, literature_id=literature_id
        ),
        "meta": _meta(),
    }
