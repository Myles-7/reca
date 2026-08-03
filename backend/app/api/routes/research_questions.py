import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError, ContractErrorResponse
from app.core.observability import current_request_id
from app.jobs.dispatcher import dispatcher
from app.jobs.schemas import JobEnvelope
from app.research_questions import scoping, service
from app.research_questions.schemas import (
    ApprovalReferenceEnvelope,
    CurrentResearchQuestionEnvelope,
    ResearchQuestionCreate,
    ResearchQuestionEnvelope,
    ResearchQuestionMarkReady,
    ResearchQuestionParseRequest,
    ResearchQuestionVersionContent,
    ResearchQuestionVersionCreate,
    ResearchQuestionVersionEnvelope,
    ResearchQuestionVersionListEnvelope,
    ResearchQuestionVersionUpdate,
)

router = APIRouter(tags=["research-questions"])
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
            message="If-Match is required for ResearchQuestionVersion updates.",
        )
    normalized = value.strip().strip('"')
    try:
        version = int(normalized)
    except ValueError:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a ResearchQuestion version number.",
        )
    if version < 1:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a positive version number.",
        )
    return version


@router.post(
    "/projects/{project_id}/research-questions",
    response_model=ResearchQuestionEnvelope,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def create_research_question(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    question_in: ResearchQuestionCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.create_research_question_command(
        session,
        actor=current_user,
        project_id=project_id,
        content=ResearchQuestionVersionContent(raw_input=question_in.raw_input),
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
    "/projects/{project_id}/research-question",
    response_model=CurrentResearchQuestionEnvelope,
    responses=ERROR_RESPONSES,
)
def get_current_project_research_question(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    return {
        "data": service.get_current_for_project(
            session,
            actor=current_user,
            project_id=project_id,
        ),
        "meta": _meta(),
    }


@router.get(
    "/research-questions/{research_question_id}",
    response_model=ResearchQuestionEnvelope,
    responses=ERROR_RESPONSES,
)
def get_research_question(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    research_question_id: uuid.UUID,
) -> dict[str, Any]:
    return {
        "data": service.get_research_question(
            session,
            actor=current_user,
            research_question_id=research_question_id,
        ),
        "meta": _meta(),
    }


@router.get(
    "/research-questions/{research_question_id}/versions",
    response_model=ResearchQuestionVersionListEnvelope,
    responses=ERROR_RESPONSES,
)
def list_research_question_versions(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    research_question_id: uuid.UUID,
) -> dict[str, Any]:
    return {
        "data": service.list_versions(
            session,
            actor=current_user,
            research_question_id=research_question_id,
        ),
        "meta": _meta(),
    }


@router.get(
    "/research-question-versions/{version_id}",
    response_model=ResearchQuestionVersionEnvelope,
    responses=ERROR_RESPONSES,
)
def get_research_question_version(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
) -> dict[str, Any]:
    return {
        "data": service.get_version(session, actor=current_user, version_id=version_id),
        "meta": _meta(),
    }


@router.post(
    "/research-question-versions/{version_id}/parse",
    response_model=JobEnvelope,
    status_code=202,
    responses=ERROR_RESPONSES,
)
def parse_research_question_version(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    parse_in: ResearchQuestionParseRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = scoping.request_scoping_job(
        session,
        actor=current_user,
        version_id=version_id,
        max_follow_up_questions=parse_in.max_follow_up_questions,
        language=parse_in.language,
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


@router.patch(
    "/research-question-versions/{version_id}",
    response_model=ResearchQuestionVersionEnvelope,
    responses=ERROR_RESPONSES,
)
def update_research_question_version(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    version_in: ResearchQuestionVersionUpdate,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, Any]:
    version = service.update_draft_version(
        session,
        actor=current_user,
        version_id=version_id,
        expected_version_number=_if_match_version(if_match),
        fields=version_in.fields,
        change_reason=version_in.change_reason,
    )
    return {"data": service.version_data(version), "meta": _meta()}


@router.post(
    "/research-questions/{research_question_id}/versions",
    response_model=ResearchQuestionVersionEnvelope,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def create_research_question_version(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    research_question_id: uuid.UUID,
    version_in: ResearchQuestionVersionCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.create_version_command(
        session,
        actor=current_user,
        research_question_id=research_question_id,
        based_on_version_id=version_in.based_on_version_id,
        fields=version_in.fields,
        change_reason=version_in.change_reason,
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
    "/research-question-versions/{version_id}/ready",
    response_model=ResearchQuestionVersionEnvelope,
    responses=ERROR_RESPONSES,
)
def mark_research_question_version_ready(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    ready_in: ResearchQuestionMarkReady,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.mark_version_ready_command(
        session,
        actor=current_user,
        version_id=version_id,
        reason=ready_in.reason,
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
    "/research-question-versions/{version_id}/approval-requests",
    response_model=ApprovalReferenceEnvelope,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def request_research_question_confirmation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.request_confirmation_command(
        session,
        actor=current_user,
        version_id=version_id,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.data,
            "meta": _meta(replayed=result.idempotency_replayed),
        },
    )
