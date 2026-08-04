from __future__ import annotations

import math
import uuid
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse

from app.agents.service import ModelExecutionMode
from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError, ContractErrorResponse
from app.core.config import settings
from app.core.observability import current_request_id
from app.evidence import analysis, extraction, retrieval, review
from app.evidence.analysis import AnalysisProviderIdentity
from app.evidence.extraction import ExtractionProviderIdentity
from app.evidence.schemas import (
    EvidenceSearchEnvelope,
    EvidenceSearchRequest,
    EvidenceSetSummaryCreate,
    EvidenceSetSummaryEnvelope,
    EvidenceSpanEnvelope,
    EvidenceSpanVerificationCreate,
    EvidenceSpanVerificationEnvelope,
    LiteratureDecisionCreate,
    LiteratureDecisionEnvelope,
    LiteratureDecisionListEnvelope,
    LiteratureExtractionCreate,
    LiteratureExtractionEnvelope,
    LiteratureExtractionFieldCorrection,
    LiteratureExtractionFieldEnvelope,
    LiteratureMatrixEnvelope,
    ManualEvidenceSpanCreate,
    MatrixSort,
    SortOrder,
    TopicGenerationCreate,
    TopicGenerationRunEnvelope,
)
from app.jobs.dispatcher import dispatcher
from app.jobs.schemas import JobEnvelope
from app.models import LiteratureFieldCode
from app.projects.schemas import ResponseMeta

router = APIRouter(tags=["evidence"])
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ContractErrorResponse},
    403: {"model": ContractErrorResponse},
    404: {"model": ContractErrorResponse},
    409: {"model": ContractErrorResponse},
    422: {"model": ContractErrorResponse},
    503: {"model": ContractErrorResponse},
}


def _meta(*, replayed: bool = False) -> dict[str, Any]:
    return ResponseMeta(
        request_id=current_request_id(), idempotency_replayed=replayed
    ).model_dump(mode="json")


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


def _if_match_version(value: str | None) -> int:
    if value is None:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match is required for LiteratureExtractionField updates.",
        )
    normalized = value.strip().strip('"')
    try:
        version = int(normalized)
    except ValueError as exc:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a field lock version.",
        ) from exc
    if version < 1:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a positive lock version.",
        )
    return version


def _configured_extraction_identity() -> ExtractionProviderIdentity:
    if settings.model_status != "CONFIGURED":
        raise ContractError(
            status_code=503,
            code="MODEL_PROVIDER_UNCONFIGURED",
            message="No production literature extraction provider is configured.",
            retryable=False,
        )
    assert settings.MODEL_NAME is not None
    return ExtractionProviderIdentity(
        provider_id="openai-compatible",
        provider_name="openai-compatible",
        model_name=settings.MODEL_NAME,
        mode=ModelExecutionMode.LIVE,
    )


extraction_identity_provider: Callable[[], ExtractionProviderIdentity] = (
    _configured_extraction_identity
)


def _configured_analysis_identity() -> AnalysisProviderIdentity:
    if settings.model_status != "CONFIGURED":
        raise ContractError(
            status_code=503,
            code="MODEL_PROVIDER_UNCONFIGURED",
            message="No production evidence analysis provider is configured.",
            retryable=False,
        )
    assert settings.MODEL_NAME is not None
    return AnalysisProviderIdentity(
        provider_id="openai-compatible",
        provider_name="openai-compatible",
        model_name=settings.MODEL_NAME,
        mode=ModelExecutionMode.LIVE,
    )


analysis_identity_provider: Callable[[], AnalysisProviderIdentity] = (
    _configured_analysis_identity
)


@router.post(
    "/documents/{document_id}/literature-extractions",
    response_model=JobEnvelope,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def create_literature_extraction(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    document_id: uuid.UUID,
    extraction_in: LiteratureExtractionCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = extraction.request_extraction_job(
        session,
        actor=current_user,
        document_id=document_id,
        literature_record_id=extraction_in.literature_record_id,
        requested_field_codes=tuple(code.value for code in extraction_in.field_codes),
        idempotency_key=_required_idempotency_key(idempotency_key),
        provider=extraction_identity_provider(),
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
    "/literature-extractions/{extraction_id}",
    response_model=LiteratureExtractionEnvelope,
    responses=ERROR_RESPONSES,
)
def get_literature_extraction(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    extraction_id: uuid.UUID,
) -> dict[str, Any]:
    return {
        "data": review.get_extraction(
            session, actor=current_user, extraction_id=extraction_id
        ),
        "meta": _meta(),
    }


@router.patch(
    "/literature-extraction-fields/{field_id}",
    response_model=LiteratureExtractionFieldEnvelope,
    responses=ERROR_RESPONSES,
)
def update_literature_extraction_field(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    field_id: uuid.UUID,
    field_in: LiteratureExtractionFieldCorrection,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = review.update_field(
        session,
        actor=current_user,
        field_id=field_id,
        payload=field_in,
        expected_lock_version=_if_match_version(if_match),
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
    "/documents/{document_id}/evidence-spans",
    response_model=EvidenceSpanEnvelope,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def create_evidence_span(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    document_id: uuid.UUID,
    span_in: ManualEvidenceSpanCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = review.create_manual_span(
        session,
        actor=current_user,
        document_id=document_id,
        payload=span_in,
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
    "/evidence-spans/{evidence_span_id}",
    response_model=EvidenceSpanEnvelope,
    responses=ERROR_RESPONSES,
)
def get_evidence_span(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    evidence_span_id: uuid.UUID,
) -> dict[str, Any]:
    return {
        "data": review.get_span(session, actor=current_user, span_id=evidence_span_id),
        "meta": _meta(),
    }


@router.post(
    "/evidence-spans/{evidence_span_id}/verification-records",
    response_model=EvidenceSpanVerificationEnvelope,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def create_evidence_span_verification(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    evidence_span_id: uuid.UUID,
    verification_in: EvidenceSpanVerificationCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = review.create_verification_record(
        session,
        actor=current_user,
        span_id=evidence_span_id,
        payload=verification_in,
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
    "/literature/{literature_id}/decisions",
    response_model=LiteratureDecisionEnvelope,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def create_literature_decision(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    literature_id: uuid.UUID,
    decision_in: LiteratureDecisionCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = review.create_decision(
        session,
        actor=current_user,
        literature_id=literature_id,
        payload=decision_in,
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
    "/literature/{literature_id}/decisions",
    response_model=LiteratureDecisionListEnvelope,
    responses=ERROR_RESPONSES,
)
def list_literature_decisions(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    literature_id: uuid.UUID,
) -> dict[str, Any]:
    return {
        "data": review.list_decisions(
            session, actor=current_user, literature_id=literature_id
        ),
        "meta": _meta(),
    }


@router.get(
    "/projects/{project_id}/literature-matrix",
    response_model=LiteratureMatrixEnvelope,
    responses=ERROR_RESPONSES,
)
def get_literature_matrix(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    included_only: bool = False,
    field_codes: Annotated[list[LiteratureFieldCode] | None, Query()] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: MatrixSort = MatrixSort.CREATED_AT,
    order: SortOrder = SortOrder.DESC,
) -> dict[str, Any]:
    rows, total, allowed_actions = review.list_matrix(
        session,
        actor=current_user,
        project_id=project_id,
        included_only=included_only,
        field_codes=field_codes,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
    )
    return {
        "data": rows,
        "allowed_actions": allowed_actions,
        "pagination": _pagination(page=page, page_size=page_size, total=total),
        "meta": _meta(),
    }


@router.post(
    "/projects/{project_id}/evidence-search",
    response_model=EvidenceSearchEnvelope,
    responses=ERROR_RESPONSES,
)
def search_project_evidence(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    search_in: EvidenceSearchRequest,
) -> dict[str, Any]:
    data = retrieval.search_evidence(
        session,
        actor=current_user,
        project_id=project_id,
        payload=search_in,
    )
    return {"data": data.model_dump(mode="json"), "meta": _meta()}


@router.post(
    "/projects/{project_id}/evidence-set-summaries",
    response_model=JobEnvelope,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def create_evidence_set_summary(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    summary_in: EvidenceSetSummaryCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = analysis.request_summary_job(
        session,
        actor=current_user,
        project_id=project_id,
        payload=summary_in,
        idempotency_key=_required_idempotency_key(idempotency_key),
        provider=analysis_identity_provider(),
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
    "/evidence-set-summaries/{summary_id}",
    response_model=EvidenceSetSummaryEnvelope,
    responses=ERROR_RESPONSES,
)
def get_evidence_set_summary(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    summary_id: uuid.UUID,
) -> dict[str, Any]:
    return {
        "data": analysis.get_summary(
            session, actor=current_user, summary_id=summary_id
        ),
        "meta": _meta(),
    }


@router.post(
    "/projects/{project_id}/topic-generation-runs",
    response_model=JobEnvelope,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def create_topic_generation_run(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    topic_in: TopicGenerationCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = analysis.request_topic_job(
        session,
        actor=current_user,
        project_id=project_id,
        payload=topic_in,
        idempotency_key=_required_idempotency_key(idempotency_key),
        provider=analysis_identity_provider(),
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
    "/topic-generation-runs/{run_id}",
    response_model=TopicGenerationRunEnvelope,
    responses=ERROR_RESPONSES,
)
def get_topic_generation_run(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    return {
        "data": analysis.get_topic_run(session, actor=current_user, run_id=run_id),
        "meta": _meta(),
    }
