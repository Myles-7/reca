import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, Header, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError, ContractErrorResponse
from app.core.observability import current_request_id
from app.documents import service
from app.documents.schemas import (
    DocumentEnvelope,
    DocumentPageEnvelope,
    DocumentPageListEnvelope,
    DocumentParseRequest,
    DocumentUploadEnvelope,
)
from app.jobs.dispatcher import dispatcher
from app.jobs.schemas import JobEnvelope
from app.models import DocumentType

router = APIRouter(tags=["documents"])
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ContractErrorResponse},
    403: {"model": ContractErrorResponse},
    404: {"model": ContractErrorResponse},
    409: {"model": ContractErrorResponse},
    413: {"model": ContractErrorResponse},
    415: {"model": ContractErrorResponse},
    422: {"model": ContractErrorResponse},
    503: {"model": ContractErrorResponse},
}


def _meta(*, replayed: bool = False, **extra: Any) -> dict[str, Any]:
    return {
        "request_id": current_request_id(),
        "schema_version": "1.0",
        "idempotency_replayed": replayed,
        **extra,
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


async def _upload_chunks(upload: UploadFile) -> AsyncIterator[bytes]:
    while chunk := await upload.read(1024 * 1024):
        yield chunk


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentUploadEnvelope,
    status_code=201,
    responses=ERROR_RESPONSES,
)
async def upload_document(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    file: Annotated[UploadFile, File()],
    document_type: Annotated[DocumentType, Form()] = DocumentType.SCHOLARLY_PDF,
    literature_record_id: Annotated[uuid.UUID | None, Form()] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    try:
        result = await service.upload_pdf(
            session,
            actor=current_user,
            project_id=project_id,
            filename=file.filename or "",
            mime_type=file.content_type or "",
            chunks=_upload_chunks(file),
            document_type=document_type,
            literature_record_id=literature_record_id,
            idempotency_key=_required_idempotency_key(idempotency_key),
        )
    finally:
        await file.close()
    data = dict(result.data or {})
    duplicate_id = data.pop("duplicate_of_artifact_id", None)
    return JSONResponse(
        status_code=result.status_code,
        content=jsonable_encoder(
            {
                "data": data,
                "meta": _meta(
                    replayed=result.idempotency_replayed,
                    duplicate_of_artifact_id=duplicate_id,
                ),
            }
        ),
    )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentEnvelope,
    responses=ERROR_RESPONSES,
)
def get_document(
    *, session: SessionDep, current_user: CurrentUser, document_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_document(
            session, actor=current_user, document_id=document_id
        ),
        "meta": _meta(),
    }


@router.post(
    "/documents/{document_id}/parse",
    response_model=JobEnvelope,
    status_code=202,
    responses=ERROR_RESPONSES,
)
def parse_document(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    document_id: uuid.UUID,
    payload: DocumentParseRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.request_parse(
        session,
        actor=current_user,
        document_id=document_id,
        allow_fallback=payload.allow_fallback,
        extract_coordinates=payload.extract_coordinates,
        idempotency_key=_required_idempotency_key(idempotency_key),
        dispatcher=dispatcher,
    )
    return JSONResponse(
        status_code=result.status_code,
        content=jsonable_encoder(
            {
                "data": result.data,
                "meta": _meta(replayed=result.idempotency_replayed),
            }
        ),
    )


@router.get(
    "/documents/{document_id}/pages",
    response_model=DocumentPageListEnvelope,
    responses=ERROR_RESPONSES,
)
def list_document_pages(
    *, session: SessionDep, current_user: CurrentUser, document_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.list_pages(
            session, actor=current_user, document_id=document_id
        ),
        "meta": _meta(),
    }


@router.get(
    "/documents/{document_id}/pages/{page_number}",
    response_model=DocumentPageEnvelope,
    responses=ERROR_RESPONSES,
)
def get_document_page(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    document_id: uuid.UUID,
    page_number: int,
) -> dict[str, Any]:
    return {
        "data": service.get_page(
            session,
            actor=current_user,
            document_id=document_id,
            page_number=page_number,
        ),
        "meta": _meta(),
    }
