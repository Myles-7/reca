import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query, Request, Response
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError, ContractErrorResponse
from app.artifacts import service
from app.artifacts.schemas import (
    ArtifactDownloadEnvelope,
    ArtifactEnvelope,
    ArtifactListEnvelope,
    ArtifactUploadComplete,
    ArtifactUploadEnvelope,
    ArtifactUploadInitiate,
)
from app.core.observability import current_request_id
from app.models import ArtifactStatus, ArtifactType

router = APIRouter(tags=["artifacts"])
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
        "schema_version": service.SCHEMA_VERSION,
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


@router.get(
    "/projects/{project_id}/artifacts",
    response_model=ArtifactListEnvelope,
    responses=ERROR_RESPONSES,
)
def list_project_artifacts(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    artifact_type: ArtifactType | None = None,
    status: ArtifactStatus | None = None,
    is_original: bool | None = None,
    q: str | None = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    data, pagination = service.list_artifacts(
        session,
        actor=current_user,
        project_id=project_id,
        artifact_type=artifact_type,
        status=status,
        is_original=is_original,
        q=q,
        page=page,
        page_size=page_size,
    )
    return {"data": data, "pagination": pagination, "meta": _meta()}


@router.post(
    "/projects/{project_id}/artifacts/uploads",
    response_model=ArtifactUploadEnvelope,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def initiate_artifact_upload(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    upload_in: ArtifactUploadInitiate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    data, replayed = service.initiate_upload(
        session,
        actor=current_user,
        project_id=project_id,
        payload=upload_in,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return JSONResponse(
        status_code=201,
        content={"data": data, "meta": _meta(replayed=replayed)},
    )


@router.put(
    "/artifact-uploads/{upload_id}/content",
    status_code=204,
    responses=ERROR_RESPONSES,
)
async def transfer_artifact_content(
    *,
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
    upload_id: uuid.UUID,
    content_type: Annotated[str | None, Header(alias="Content-Type")] = None,
) -> Response:
    if (
        content_type is None
        or content_type.split(";", 1)[0].strip().lower() != "application/octet-stream"
    ):
        raise ContractError(
            status_code=415,
            code="FILE_TYPE_UNSUPPORTED",
            message="Artifact content transfer requires application/octet-stream.",
        )
    await service.transfer_content(
        session,
        actor=current_user,
        upload_id=upload_id,
        chunks=request.stream(),
    )
    return Response(status_code=204)


@router.post(
    "/projects/{project_id}/artifacts/uploads/{upload_id}/complete",
    response_model=ArtifactEnvelope,
    responses=ERROR_RESPONSES,
)
def complete_artifact_upload(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    upload_id: uuid.UUID,
    complete_in: ArtifactUploadComplete,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    data, duplicate_id, replayed = service.complete_upload(
        session,
        actor=current_user,
        project_id=project_id,
        upload_id=upload_id,
        payload=complete_in,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return JSONResponse(
        status_code=200,
        content={
            "data": data,
            "meta": _meta(
                replayed=replayed,
                duplicate_of_artifact_id=(
                    str(duplicate_id) if duplicate_id is not None else None
                ),
            ),
        },
    )


@router.get(
    "/artifacts/{artifact_id}",
    response_model=ArtifactEnvelope,
    responses=ERROR_RESPONSES,
)
def get_artifact(
    *, session: SessionDep, current_user: CurrentUser, artifact_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_artifact(
            session, actor=current_user, artifact_id=artifact_id
        ),
        "meta": _meta(),
    }


@router.get(
    "/artifacts/{artifact_id}/download",
    response_model=ArtifactDownloadEnvelope,
    responses=ERROR_RESPONSES,
)
def authorize_artifact_download(
    *, session: SessionDep, current_user: CurrentUser, artifact_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.authorize_download(
            session, actor=current_user, artifact_id=artifact_id
        ),
        "meta": _meta(),
    }
