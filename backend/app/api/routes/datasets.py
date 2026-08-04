from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, Header, Query, Response, UploadFile

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError
from app.api.m4_responses import (
    DatasetColumnEnvelope,
    DatasetColumnListEnvelope,
    DatasetEnvelope,
    DatasetListEnvelope,
    DatasetPreviewEnvelope,
    DatasetUploadEnvelope,
    DatasetVersionEnvelope,
    DatasetVersionListEnvelope,
    WorksheetsEnvelope,
)
from app.datasets import limits, service
from app.datasets.schemas import (
    DatasetColumnUpdate,
    DatasetUpdate,
    DatasetVersionInvalidation,
    WorksheetSelection,
)
from app.models import DatasetLicenseStatus, DatasetSourceType

router = APIRouter(tags=["datasets"])


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


def _if_match(value: str | None, object_name: str) -> int:
    if value is None:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message=f"If-Match is required for {object_name} updates.",
        )
    normalized = value.strip().strip('"')
    try:
        result = int(normalized)
    except ValueError as exc:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a positive lock version.",
        ) from exc
    if result < 1:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a positive lock version.",
        )
    return result


def _meta(*, replayed: bool = False) -> dict[str, Any]:
    return {"schema_version": "1.0", "idempotency_replayed": replayed}


@router.post(
    "/projects/{project_id}/datasets",
    status_code=201,
    response_model=DatasetUploadEnvelope,
)
async def upload_dataset(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    file: Annotated[UploadFile, File()],
    name: Annotated[str, Form(min_length=1, max_length=255)],
    source_type: Annotated[DatasetSourceType, Form()] = DatasetSourceType.USER_UPLOAD,
    publisher: Annotated[str | None, Form(max_length=255)] = None,
    source_platform: Annotated[str | None, Form(max_length=255)] = None,
    source_identifier: Annotated[str | None, Form(max_length=500)] = None,
    license_name: Annotated[str | None, Form(max_length=255)] = None,
    license_status: Annotated[
        DatasetLicenseStatus, Form()
    ] = DatasetLicenseStatus.UNKNOWN,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="reca-dataset-upload-") as directory:
        suffix = Path(file.filename or "").suffix.lower()
        local = (
            Path(directory)
            / f"upload{suffix if suffix in {'.csv', '.xlsx'} else '.bin'}"
        )
        size = 0
        with local.open("wb") as target:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > limits.MAX_UPLOAD_BYTES:
                    raise ContractError(
                        status_code=413,
                        code="FILE_TOO_LARGE",
                        message="The dataset file exceeds the upload limit.",
                    )
                target.write(chunk)
        data, replayed = service.import_dataset(
            session,
            actor=current_user,
            project_id=project_id,
            path=local,
            original_filename=file.filename or "dataset",
            mime_type=file.content_type or "application/octet-stream",
            name=name,
            source_type=source_type,
            publisher=publisher,
            source_platform=source_platform,
            source_identifier=source_identifier,
            license_name=license_name,
            license_status=license_status,
            idempotency_key=_required_idempotency_key(idempotency_key),
        )
    return {"data": data, "meta": _meta(replayed=replayed)}


@router.get("/projects/{project_id}/datasets", response_model=DatasetListEnvelope)
def list_datasets(
    *, session: SessionDep, current_user: CurrentUser, project_id: uuid.UUID
) -> dict[str, Any]:
    data = service.list_datasets(session, actor=current_user, project_id=project_id)
    return {"data": data, "meta": {**_meta(), "count": len(data)}}


@router.get("/datasets/{dataset_id}", response_model=DatasetEnvelope)
def get_dataset(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    dataset_id: uuid.UUID,
    response: Response,
) -> dict[str, Any]:
    data = service.get_dataset(session, actor=current_user, dataset_id=dataset_id)
    response.headers["ETag"] = f'"{data["lock_version"]}"'
    return {"data": data, "meta": _meta()}


@router.patch("/datasets/{dataset_id}", response_model=DatasetEnvelope)
def update_dataset(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    dataset_id: uuid.UUID,
    payload: DatasetUpdate,
    response: Response,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, Any]:
    data = service.update_dataset(
        session,
        actor=current_user,
        dataset_id=dataset_id,
        payload=payload,
        expected_lock_version=_if_match(if_match, "Dataset"),
    )
    response.headers["ETag"] = f'"{data["lock_version"]}"'
    return {"data": data, "meta": _meta()}


@router.get("/dataset-versions/{version_id}", response_model=DatasetVersionEnvelope)
def get_dataset_version(
    *, session: SessionDep, current_user: CurrentUser, version_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_version(session, actor=current_user, version_id=version_id),
        "meta": _meta(),
    }


@router.get(
    "/dataset-versions/{version_id}/worksheets", response_model=WorksheetsEnvelope
)
def get_worksheets(
    *, session: SessionDep, current_user: CurrentUser, version_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_worksheets(
            session, actor=current_user, version_id=version_id
        ),
        "meta": _meta(),
    }


@router.post(
    "/dataset-versions/{version_id}/invalidate",
    response_model=DatasetVersionEnvelope,
)
def invalidate_dataset_version(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    payload: DatasetVersionInvalidation,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    data, replayed = service.invalidate_version(
        session,
        actor=current_user,
        version_id=version_id,
        payload=payload,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return {"data": data, "meta": _meta(replayed=replayed)}


@router.post(
    "/dataset-versions/{version_id}/worksheet-selection",
    status_code=201,
    response_model=DatasetVersionEnvelope,
)
def select_worksheet(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    payload: WorksheetSelection,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    data, replayed = service.select_worksheet(
        session,
        actor=current_user,
        version_id=version_id,
        payload=payload,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return {"data": data, "meta": _meta(replayed=replayed)}


@router.get(
    "/dataset-versions/{version_id}/preview", response_model=DatasetPreviewEnvelope
)
def preview_dataset_version(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[
        int, Query(ge=1, le=limits.PREVIEW_MAX_ROWS)
    ] = limits.PREVIEW_DEFAULT_ROWS,
    columns: Annotated[list[str] | None, Query()] = None,
) -> dict[str, Any]:
    return {
        "data": service.preview(
            session,
            actor=current_user,
            version_id=version_id,
            offset=offset,
            limit=limit,
            selected_columns=columns,
        ),
        "meta": _meta(),
    }


@router.get(
    "/dataset-versions/{version_id}/columns", response_model=DatasetColumnListEnvelope
)
def list_dataset_columns(
    *, session: SessionDep, current_user: CurrentUser, version_id: uuid.UUID
) -> dict[str, Any]:
    data = service.list_columns(session, actor=current_user, version_id=version_id)
    return {"data": data, "meta": {**_meta(), "count": len(data)}}


@router.patch("/dataset-columns/{column_id}", response_model=DatasetColumnEnvelope)
def update_dataset_column(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    column_id: uuid.UUID,
    payload: DatasetColumnUpdate,
    response: Response,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, Any]:
    data = service.update_column(
        session,
        actor=current_user,
        column_id=column_id,
        payload=payload,
        expected_lock_version=_if_match(if_match, "DatasetColumn"),
    )
    response.headers["ETag"] = f'"{data["lock_version"]}"'
    return {"data": data, "meta": _meta()}


@router.get(
    "/datasets/{dataset_id}/versions", response_model=DatasetVersionListEnvelope
)
def list_dataset_versions(
    *, session: SessionDep, current_user: CurrentUser, dataset_id: uuid.UUID
) -> dict[str, Any]:
    data = service.list_versions(session, actor=current_user, dataset_id=dataset_id)
    return {"data": data, "meta": {**_meta(), "count": len(data)}}
