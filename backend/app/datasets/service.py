from __future__ import annotations

import hashlib
import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.adapters.storage import ObjectStorage, StorageError, StorageObjectExists
from app.api.errors import ContractError
from app.artifacts import service as artifact_service
from app.artifacts.validation import ArtifactValidationError, normalize_filename
from app.core.observability import current_request_id
from app.datasets import limits, parsers
from app.datasets.schemas import (
    DatasetColumnUpdate,
    DatasetUpdate,
    DatasetVersionInvalidation,
    WorksheetSelection,
)
from app.models import (
    Artifact,
    ArtifactStatus,
    ArtifactType,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    Dataset,
    DatasetColumn,
    DatasetColumnConfirmationStatus,
    DatasetFileFormat,
    DatasetLicenseStatus,
    DatasetSourceType,
    DatasetStatus,
    DatasetVersion,
    DatasetVersionStatus,
    DatasetVersionType,
    Figure,
    FigurePlan,
    FigurePlanStatus,
    FigureStatus,
    IdempotencyRecord,
    ProjectMemberRole,
    StorageProvider,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

UPLOAD_PATH = "/api/v1/projects/{project_id}/datasets"
WORKSHEET_SELECTION_PATH = "/api/v1/dataset-versions/{version_id}/worksheet-selection"
VERSION_INVALIDATION_PATH = "/api/v1/dataset-versions/{version_id}/invalidate"
IDEMPOTENCY_RETENTION = timedelta(hours=24)


def _encoded(value: Any) -> dict[str, Any]:
    return cast(dict[str, Any], jsonable_encoder(value))


def _not_found() -> ContractError:
    return ContractError(
        status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
    )


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="The operation conflicted with a concurrent change.",
            retryable=True,
        ) from exc


def _audit(
    session: Session,
    *,
    project_id: uuid.UUID,
    actor: User,
    action: str,
    object_type: str,
    object_id: uuid.UUID,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
) -> None:
    session.add(
        AuditLog(
            project_id=project_id,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
            action=action,
            object_type=object_type,
            object_id=object_id,
            before_snapshot=before,
            after_snapshot=after,
            reason=reason,
            request_id=current_request_id(),
            outcome=AuditOutcome.SUCCEEDED,
        )
    )


def _role(access: project_service.ProjectAccess) -> ProjectMemberRole:
    assert access.membership is not None
    return access.membership.role


def _permissions(role: ProjectMemberRole) -> dict[str, bool]:
    actions = project_service.ROLE_ACTIONS[role]
    return {
        "can_update": "dataset.update" in actions,
        "can_upload": "dataset.upload" in actions,
        "can_confirm_columns": "dataset.column.confirm" in actions,
    }


def _dataset_data(dataset: Dataset, role: ProjectMemberRole) -> dict[str, Any]:
    return _encoded(
        {
            "id": dataset.id,
            "project_id": dataset.project_id,
            "name": dataset.name,
            "description": dataset.description,
            "source_type": dataset.source_type,
            "publisher": dataset.publisher,
            "source_platform": dataset.source_platform,
            "source_identifier": dataset.source_identifier,
            "doi": dataset.doi,
            "acquired_at": dataset.acquired_at,
            "license_name": dataset.license_name,
            "license_status": dataset.license_status,
            "license_warning": "LICENSE_UNKNOWN"
            if dataset.license_status == DatasetLicenseStatus.UNKNOWN
            else None,
            "recommended_citation": dataset.recommended_citation,
            "known_limitations": dataset.known_limitations,
            "current_version_id": dataset.current_version_id,
            "status": dataset.status,
            "lock_version": dataset.lock_version,
            "created_by": dataset.created_by,
            "created_at": dataset.created_at,
            "updated_at": dataset.updated_at,
            "permissions": _permissions(role),
        }
    )


def _version_data(version: DatasetVersion) -> dict[str, Any]:
    return _encoded(
        {
            "id": version.id,
            "project_id": version.project_id,
            "dataset_id": version.dataset_id,
            "version_number": version.version_number,
            "parent_version_id": version.parent_version_id,
            "artifact_id": version.artifact_id,
            "version_type": version.version_type,
            "row_count": version.row_count,
            "column_count": version.column_count,
            "file_format": version.file_format,
            "worksheet_manifest": version.worksheet_manifest,
            "selected_worksheet_name": version.selected_worksheet_name,
            "projection_hash": version.projection_hash,
            "schema_hash": version.schema_hash,
            "data_hash": version.data_hash,
            "transformation_id": version.transformation_id,
            "status": version.status,
            "created_by": version.created_by,
            "created_at": version.created_at,
            "invalidated_at": version.invalidated_at,
            "invalidation_reason": version.invalidation_reason,
        }
    )


def _column_data(column: DatasetColumn) -> dict[str, Any]:
    return _encoded(
        {
            "id": column.id,
            "project_id": column.project_id,
            "dataset_version_id": column.dataset_version_id,
            "source_name": column.source_name,
            "display_name": column.display_name,
            "column_order": column.column_order,
            "inferred_type": column.inferred_type,
            "confirmed_type": column.confirmed_type,
            "semantic_role": column.semantic_role,
            "unit": column.unit,
            "description": column.description,
            "missing_codes": column.missing_codes,
            "category_mapping": column.category_mapping,
            "is_identifier": column.is_identifier,
            "is_sensitive": column.is_sensitive,
            "confirmation_status": column.confirmation_status,
            "unique_count": column.unique_count,
            "missing_ratio": column.missing_ratio,
            "example_values": column.example_values,
            "inherited_from_column_id": column.inherited_from_column_id,
            "lock_version": column.lock_version,
            "created_at": column.created_at,
            "updated_at": column.updated_at,
        }
    )


def _idempotency(
    session: Session,
    *,
    actor_id: uuid.UUID,
    project_id: uuid.UUID,
    path: str,
    key: str,
) -> IdempotencyRecord | None:
    return session.exec(
        select(IdempotencyRecord).where(
            IdempotencyRecord.actor_id == actor_id,
            IdempotencyRecord.project_id == project_id,
            IdempotencyRecord.method == "POST",
            IdempotencyRecord.path_template == path,
            IdempotencyRecord.idempotency_key == key,
        )
    ).first()


def _replay(
    session: Session,
    *,
    actor_id: uuid.UUID,
    project_id: uuid.UUID,
    path: str,
    key: str,
    request_hash: str,
) -> dict[str, Any] | None:
    record = _idempotency(
        session, actor_id=actor_id, project_id=project_id, path=path, key=key
    )
    if record is None:
        return None
    if record.request_hash != request_hash:
        raise ContractError(
            status_code=409,
            code="IDEMPOTENCY_CONFLICT",
            message="The Idempotency-Key was already used with a different request.",
        )
    return dict(record.response_body or {})


def _store_replay(
    session: Session,
    *,
    actor_id: uuid.UUID,
    project_id: uuid.UUID,
    path: str,
    key: str,
    request_hash: str,
    response: dict[str, Any],
    status_code: int = 201,
) -> None:
    session.add(
        IdempotencyRecord(
            actor_id=actor_id,
            project_id=project_id,
            method="POST",
            path_template=path,
            idempotency_key=key,
            request_hash=request_hash,
            response_status=status_code,
            response_body=response,
            expires_at=datetime.now(UTC) + IDEMPOTENCY_RETENTION,
        )
    )


def _manifest_data(items: tuple[parsers.WorksheetInfo, ...]) -> list[dict[str, Any]]:
    return [
        {
            "name": item.name,
            "ordinal": item.ordinal,
            "visibility": item.visibility,
            "estimated_rows": item.estimated_rows,
            "estimated_columns": item.estimated_columns,
            "warnings": list(item.warnings),
        }
        for item in items
    ]


def _publish_profile(
    session: Session,
    *,
    dataset: Dataset,
    version: DatasetVersion,
    profile: parsers.ParsedTable,
) -> None:
    if version.status not in {
        DatasetVersionStatus.CREATING,
        DatasetVersionStatus.VALIDATING,
    }:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="The DatasetVersion cannot be published from its current state.",
        )
    version.status = DatasetVersionStatus.VALIDATING
    session.add(version)
    session.flush()
    for order, column in enumerate(profile.columns, start=1):
        session.add(
            DatasetColumn(
                project_id=version.project_id,
                dataset_version_id=version.id,
                source_name=column.source_name,
                column_order=order,
                inferred_type=column.inferred_type,
                unique_count=column.unique_count,
                missing_ratio=column.missing_ratio,
                example_values=list(column.example_values),
                is_sensitive=column.is_sensitive,
                confirmation_status=DatasetColumnConfirmationStatus.UNCONFIRMED,
            )
        )
    version.row_count = profile.row_count
    version.column_count = len(profile.headers)
    version.projection_hash = profile.projection_hash
    version.schema_hash = profile.schema_hash
    version.status = DatasetVersionStatus.AVAILABLE
    dataset.current_version_id = version.id
    dataset.updated_at = get_datetime_utc()
    session.add(version)
    session.add(dataset)
    session.flush()


def _storage(override: ObjectStorage | None) -> ObjectStorage:
    return override or artifact_service.storage


def _hash_and_prefix(path: Path) -> tuple[str, bytes]:
    digest = hashlib.sha256()
    prefix = b""
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            if len(prefix) < 8:
                prefix += chunk[: 8 - len(prefix)]
            digest.update(chunk)
    return digest.hexdigest(), prefix


def import_dataset(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    path: Path,
    original_filename: str,
    mime_type: str,
    name: str,
    source_type: DatasetSourceType,
    publisher: str | None,
    source_platform: str | None,
    source_identifier: str | None,
    license_name: str | None,
    license_status: DatasetLicenseStatus,
    idempotency_key: str,
    storage_backend: ObjectStorage | None = None,
) -> tuple[dict[str, Any], bool]:
    access = project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="dataset.upload",
        for_update=True,
    )
    if not path.exists() or path.stat().st_size == 0:
        raise ContractError(
            status_code=422, code="EMPTY_FILE", message="The uploaded file is empty."
        )
    if path.stat().st_size > limits.MAX_UPLOAD_BYTES:
        raise ContractError(
            status_code=413,
            code="FILE_TOO_LARGE",
            message="The dataset file exceeds the upload limit.",
        )
    try:
        safe_name = normalize_filename(original_filename)
    except ArtifactValidationError as exc:
        raise ContractError(
            status_code=exc.status_code, code=exc.code, message=exc.message
        ) from exc
    digest, prefix = _hash_and_prefix(path)
    file_format = parsers.detect_format(safe_name, mime_type, prefix)
    if license_status == DatasetLicenseStatus.VERIFIED:
        raise ContractError(
            status_code=422,
            code="LICENSE_VERIFICATION_REQUIRED",
            message="User upload cannot assert a VERIFIED license.",
        )
    request_payload = {
        "sha256": digest,
        "name": name,
        "source_type": source_type,
        "publisher": publisher,
        "source_platform": source_platform,
        "source_identifier": source_identifier,
        "license_name": license_name,
        "license_status": license_status,
    }
    request_hash = project_service.request_hash(request_payload)
    replay = _replay(
        session,
        actor_id=actor.id,
        project_id=project_id,
        path=UPLOAD_PATH,
        key=idempotency_key,
        request_hash=request_hash,
    )
    if replay is not None:
        return replay, True

    artifact = Artifact(
        project_id=project_id,
        artifact_type=ArtifactType.DATASET_FILE,
        filename=safe_name,
        original_filename=safe_name,
        storage_provider=StorageProvider.MINIO,
        storage_key="",
        mime_type="text/csv"
        if file_format == DatasetFileFormat.CSV
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        size_bytes=path.stat().st_size,
        sha256=digest,
        is_original=True,
        is_immutable=True,
        status=ArtifactStatus.UPLOADING,
        artifact_metadata={
            "schema_version": "1.0",
            "dataset_file_format": file_format.value,
        },
        created_by=actor.id,
    )
    artifact.storage_key = artifact_service._artifact_key(
        project_id=project_id, artifact_id=artifact.id, is_original=True
    )
    dataset = Dataset(
        project_id=project_id,
        name=name.strip(),
        source_type=source_type,
        publisher=publisher,
        source_platform=source_platform,
        source_identifier=source_identifier,
        license_name=license_name,
        license_status=license_status if license_name else DatasetLicenseStatus.UNKNOWN,
        created_by=actor.id,
    )
    version = DatasetVersion(
        project_id=project_id,
        dataset_id=dataset.id,
        version_number=1,
        artifact_id=artifact.id,
        version_type=DatasetVersionType.ORIGINAL,
        file_format=file_format,
        data_hash=digest,
        status=DatasetVersionStatus.CREATING,
        created_by=actor.id,
    )
    session.add(artifact)
    session.add(dataset)
    session.add(version)
    session.flush()
    try:
        _storage(storage_backend).put_file_once(
            object_key=artifact.storage_key,
            path=path,
            content_sha256=digest,
            size_bytes=artifact.size_bytes,
        )
    except StorageObjectExists as exc:
        raise ContractError(
            status_code=409,
            code="STORAGE_KEY_CONFLICT",
            message="The immutable object key already exists.",
        ) from exc
    except StorageError as exc:
        raise ContractError(
            status_code=503,
            code="STORAGE_UNAVAILABLE",
            message="Object storage is unavailable.",
            retryable=True,
        ) from exc
    artifact.status = ArtifactStatus.AVAILABLE
    session.add(artifact)
    try:
        if file_format == DatasetFileFormat.CSV:
            version.selected_worksheet_name = None
            _publish_profile(
                session,
                dataset=dataset,
                version=version,
                profile=parsers.parse_csv(path),
            )
        else:
            manifest = parsers.worksheet_manifest(path)
            version.worksheet_manifest = _manifest_data(manifest)
            visible = [item for item in manifest if item.visibility == "VISIBLE"]
            if len(visible) == 1:
                version.selected_worksheet_name = visible[0].name
                _publish_profile(
                    session,
                    dataset=dataset,
                    version=version,
                    profile=parsers.parse_xlsx(path, visible[0].name),
                )
            else:
                session.add(version)
                session.flush()
    except ContractError:
        version.status = DatasetVersionStatus.FAILED
        artifact.status = ArtifactStatus.QUARANTINED
        session.add(version)
        session.add(artifact)
        _audit(
            session,
            project_id=project_id,
            actor=actor,
            action="DATASET_UPLOAD_FAILED",
            object_type="dataset_version",
            object_id=version.id,
        )
        _commit(session)
        raise
    _audit(
        session,
        project_id=project_id,
        actor=actor,
        action="DATASET_UPLOADED",
        object_type="dataset",
        object_id=dataset.id,
        after={
            "version_id": str(version.id),
            "data_hash": digest,
            "status": version.status.value,
        },
    )
    response = {
        "dataset": _dataset_data(dataset, _role(access)),
        "version": _version_data(version),
    }
    _store_replay(
        session,
        actor_id=actor.id,
        project_id=project_id,
        path=UPLOAD_PATH,
        key=idempotency_key,
        request_hash=request_hash,
        response=response,
    )
    _commit(session)
    return response, False


def _dataset_access(
    session: Session,
    *,
    actor: User,
    dataset_id: uuid.UUID,
    action: str,
    for_update: bool = False,
) -> tuple[Dataset, project_service.ProjectAccess]:
    statement = select(Dataset).where(
        Dataset.id == dataset_id,
        Dataset.status != DatasetStatus.DELETED,
        col(Dataset.deleted_at).is_(None),
    )
    if for_update:
        statement = statement.with_for_update()
    dataset = session.exec(statement).first()
    if dataset is None:
        raise _not_found()
    access = project_service.authorize_project(
        session,
        project_id=dataset.project_id,
        actor=actor,
        action=action,
        for_update=for_update,
    )
    return dataset, access


def _version_access(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    action: str,
    for_update: bool = False,
) -> tuple[DatasetVersion, Dataset, project_service.ProjectAccess]:
    statement = select(DatasetVersion).where(
        DatasetVersion.id == version_id, col(DatasetVersion.deleted_at).is_(None)
    )
    if for_update:
        statement = statement.with_for_update()
    version = session.exec(statement).first()
    if version is None:
        raise _not_found()
    dataset, access = _dataset_access(
        session,
        actor=actor,
        dataset_id=version.dataset_id,
        action=action,
        for_update=for_update,
    )
    if dataset.project_id != version.project_id:
        raise _not_found()
    return version, dataset, access


def list_datasets(
    session: Session, *, actor: User, project_id: uuid.UUID
) -> list[dict[str, Any]]:
    access = project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="dataset.read"
    )
    items = session.exec(
        select(Dataset)
        .where(
            Dataset.project_id == project_id,
            Dataset.status != DatasetStatus.DELETED,
            col(Dataset.deleted_at).is_(None),
        )
        .order_by(col(Dataset.created_at).desc())
    ).all()
    return [_dataset_data(item, _role(access)) for item in items]


def get_dataset(
    session: Session, *, actor: User, dataset_id: uuid.UUID
) -> dict[str, Any]:
    dataset, access = _dataset_access(
        session, actor=actor, dataset_id=dataset_id, action="dataset.read"
    )
    data = _dataset_data(dataset, _role(access))
    data["versions"] = [
        _version_data(item)
        for item in session.exec(
            select(DatasetVersion)
            .where(DatasetVersion.dataset_id == dataset.id)
            .order_by(col(DatasetVersion.version_number).desc())
        ).all()
    ]
    return data


def get_version(
    session: Session, *, actor: User, version_id: uuid.UUID
) -> dict[str, Any]:
    version, _, _ = _version_access(
        session, actor=actor, version_id=version_id, action="dataset.read"
    )
    return _version_data(version)


def list_versions(
    session: Session, *, actor: User, dataset_id: uuid.UUID
) -> list[dict[str, Any]]:
    dataset, _ = _dataset_access(
        session, actor=actor, dataset_id=dataset_id, action="dataset.read"
    )
    versions = session.exec(
        select(DatasetVersion)
        .where(
            DatasetVersion.dataset_id == dataset.id,
            DatasetVersion.project_id == dataset.project_id,
            col(DatasetVersion.deleted_at).is_(None),
        )
        .order_by(col(DatasetVersion.version_number).desc())
    ).all()
    return [_version_data(version) for version in versions]


def update_dataset(
    session: Session,
    *,
    actor: User,
    dataset_id: uuid.UUID,
    payload: DatasetUpdate,
    expected_lock_version: int,
) -> dict[str, Any]:
    dataset, access = _dataset_access(
        session,
        actor=actor,
        dataset_id=dataset_id,
        action="dataset.update",
        for_update=True,
    )
    if dataset.lock_version != expected_lock_version:
        raise ContractError(
            status_code=409,
            code="RESOURCE_VERSION_CONFLICT",
            message="The Dataset was modified by another request.",
            details={
                "expected": expected_lock_version,
                "current": dataset.lock_version,
            },
        )
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("license_status") == DatasetLicenseStatus.VERIFIED:
        raise ContractError(
            status_code=422,
            code="LICENSE_VERIFICATION_REQUIRED",
            message="This endpoint cannot assert a VERIFIED license.",
        )
    if updates.get("status") == DatasetStatus.DELETED:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Dataset deletion requires the dedicated lifecycle command.",
        )
    before = _dataset_data(dataset, _role(access))
    for field, value in updates.items():
        setattr(dataset, field, value)
    if not dataset.license_name:
        dataset.license_status = DatasetLicenseStatus.UNKNOWN
    dataset.lock_version += 1
    dataset.updated_at = get_datetime_utc()
    session.add(dataset)
    _audit(
        session,
        project_id=dataset.project_id,
        actor=actor,
        action="DATASET_IDENTITY_UPDATED",
        object_type="dataset",
        object_id=dataset.id,
        before=before,
        after=_dataset_data(dataset, _role(access)),
    )
    _commit(session)
    return _dataset_data(dataset, _role(access))


def list_columns(
    session: Session, *, actor: User, version_id: uuid.UUID
) -> list[dict[str, Any]]:
    version, _, _ = _version_access(
        session, actor=actor, version_id=version_id, action="dataset.read"
    )
    if version.status not in {
        DatasetVersionStatus.AVAILABLE,
        DatasetVersionStatus.INVALIDATED,
    }:
        raise ContractError(
            status_code=409,
            code="DATASET_VERSION_NOT_AVAILABLE",
            message="The DatasetVersion columns are not available.",
        )
    items = session.exec(
        select(DatasetColumn)
        .where(DatasetColumn.dataset_version_id == version.id)
        .order_by(col(DatasetColumn.column_order))
    ).all()
    return [_column_data(item) for item in items]


def update_column(
    session: Session,
    *,
    actor: User,
    column_id: uuid.UUID,
    payload: DatasetColumnUpdate,
    expected_lock_version: int,
) -> dict[str, Any]:
    column = session.exec(
        select(DatasetColumn).where(DatasetColumn.id == column_id).with_for_update()
    ).first()
    if column is None:
        raise _not_found()
    version, _, _ = _version_access(
        session,
        actor=actor,
        version_id=column.dataset_version_id,
        action="dataset.column.confirm",
        for_update=True,
    )
    if version.status != DatasetVersionStatus.AVAILABLE:
        raise ContractError(
            status_code=409,
            code="DATASET_VERSION_NOT_AVAILABLE",
            message="Only an AVAILABLE DatasetVersion can receive field confirmations.",
        )
    if column.lock_version != expected_lock_version:
        raise ContractError(
            status_code=409,
            code="RESOURCE_VERSION_CONFLICT",
            message="The DatasetColumn was modified by another request.",
            details={"expected": expected_lock_version, "current": column.lock_version},
        )
    before = _column_data(column)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(column, field, value)
    if (
        column.confirmation_status == DatasetColumnConfirmationStatus.CONFIRMED
        and column.confirmed_type is None
    ):
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="A confirmed field requires confirmed_type.",
        )
    column.lock_version += 1
    column.updated_at = get_datetime_utc()
    session.add(column)
    _audit(
        session,
        project_id=column.project_id,
        actor=actor,
        action="DATASET_COLUMN_CONFIRMED",
        object_type="dataset_column",
        object_id=column.id,
        before=before,
        after=_column_data(column),
    )
    _commit(session)
    return _column_data(column)


def get_worksheets(
    session: Session, *, actor: User, version_id: uuid.UUID
) -> dict[str, Any]:
    version, _, _ = _version_access(
        session, actor=actor, version_id=version_id, action="dataset.read"
    )
    if version.file_format != DatasetFileFormat.XLSX:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="CSV versions do not have worksheets.",
        )
    return {
        "version_id": str(version.id),
        "status": version.status.value,
        "worksheets": version.worksheet_manifest or [],
        "selected_worksheet_name": version.selected_worksheet_name,
    }


def invalidate_version(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    payload: DatasetVersionInvalidation,
    idempotency_key: str,
) -> tuple[dict[str, Any], bool]:
    version, dataset, _ = _version_access(
        session,
        actor=actor,
        version_id=version_id,
        action="dataset.update",
        for_update=True,
    )
    request_hash = project_service.request_hash(payload)
    replay = _replay(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        path=VERSION_INVALIDATION_PATH,
        key=idempotency_key,
        request_hash=request_hash,
    )
    if replay is not None:
        return replay, True
    if version.status != DatasetVersionStatus.AVAILABLE:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Only an AVAILABLE DatasetVersion can be invalidated.",
        )
    version.status = DatasetVersionStatus.INVALIDATED
    version.invalidated_at = get_datetime_utc()
    version.invalidation_reason = payload.reason.strip()
    from app.evidence_graph.invalidation import propagate_invalidation
    from app.models import EvidenceObjectType

    propagate_invalidation(
        session,
        project_id=version.project_id,
        object_type=EvidenceObjectType.DATASET_VERSION,
        object_id=version.id,
        reason=version.invalidation_reason,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
    )
    for plan in session.exec(
        select(FigurePlan).where(
            FigurePlan.dataset_version_id == version.id,
            FigurePlan.status != FigurePlanStatus.INVALIDATED,
        )
    ):
        plan.status = FigurePlanStatus.INVALIDATED
        plan.invalidated_at = version.invalidated_at
        plan.invalidation_reason = (
            f"Upstream DatasetVersion invalidated: {version.invalidation_reason}"
        )
        session.add(plan)
    for figure in session.exec(
        select(Figure).where(
            Figure.dataset_version_id == version.id,
            Figure.status != FigureStatus.INVALIDATED,
        )
    ):
        figure.status = FigureStatus.INVALIDATED
        figure.invalidated_at = version.invalidated_at
        figure.invalidation_reason = (
            f"Upstream DatasetVersion invalidated: {version.invalidation_reason}"
        )
        session.add(figure)
        propagate_invalidation(
            session,
            project_id=version.project_id,
            object_type=EvidenceObjectType.FIGURE,
            object_id=figure.id,
            reason=figure.invalidation_reason,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
        )
    if dataset.current_version_id == version.id:
        replacement = session.exec(
            select(DatasetVersion)
            .where(
                DatasetVersion.dataset_id == dataset.id,
                DatasetVersion.id != version.id,
                DatasetVersion.status == DatasetVersionStatus.AVAILABLE,
                col(DatasetVersion.deleted_at).is_(None),
            )
            .order_by(col(DatasetVersion.version_number).desc())
            .with_for_update()
        ).first()
        dataset.current_version_id = replacement.id if replacement else None
        dataset.lock_version += 1
        dataset.updated_at = get_datetime_utc()
        session.add(dataset)
    session.add(version)
    _audit(
        session,
        project_id=version.project_id,
        actor=actor,
        action="DATASET_VERSION_INVALIDATED",
        object_type="dataset_version",
        object_id=version.id,
        after={
            "status": version.status.value,
            "reason": version.invalidation_reason,
            "current_version_id": str(dataset.current_version_id)
            if dataset.current_version_id
            else None,
        },
        reason=version.invalidation_reason,
    )
    response = _version_data(version)
    _store_replay(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        path=VERSION_INVALIDATION_PATH,
        key=idempotency_key,
        request_hash=request_hash,
        response=response,
        status_code=200,
    )
    _commit(session)
    return response, False


def select_worksheet(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    payload: WorksheetSelection,
    idempotency_key: str,
    storage_backend: ObjectStorage | None = None,
) -> tuple[dict[str, Any], bool]:
    version, dataset, _ = _version_access(
        session,
        actor=actor,
        version_id=version_id,
        action="dataset.upload",
        for_update=True,
    )
    request_hash = project_service.request_hash(payload)
    replay = _replay(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        path=WORKSHEET_SELECTION_PATH,
        key=idempotency_key,
        request_hash=request_hash,
    )
    if replay is not None:
        return replay, True
    if (
        version.file_format != DatasetFileFormat.XLSX
        or version.status != DatasetVersionStatus.CREATING
        or version.selected_worksheet_name is not None
    ):
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Worksheet selection is no longer available.",
        )
    entry = next(
        (
            item
            for item in version.worksheet_manifest or []
            if item.get("name") == payload.worksheet_name
        ),
        None,
    )
    if entry is None:
        raise ContractError(
            status_code=422,
            code="WORKSHEET_NOT_FOUND",
            message="The selected worksheet does not exist.",
        )
    if entry.get("visibility") != "VISIBLE" and not payload.acknowledge_hidden:
        raise ContractError(
            status_code=422,
            code="HIDDEN_WORKSHEET_ACK_REQUIRED",
            message="Selecting a hidden worksheet requires acknowledgement.",
        )
    with tempfile.TemporaryDirectory(prefix="reca-dataset-select-") as directory:
        local = Path(directory) / "source.xlsx"
        artifact_service.download_available_artifact_to_path(
            session,
            artifact_id=version.artifact_id,
            project_id=version.project_id,
            path=local,
            storage_backend=storage_backend,
        )
        version.selected_worksheet_name = payload.worksheet_name
        try:
            profile = parsers.parse_xlsx(local, payload.worksheet_name)
            _publish_profile(session, dataset=dataset, version=version, profile=profile)
        except ContractError:
            version.status = DatasetVersionStatus.FAILED
            session.add(version)
            _audit(
                session,
                project_id=version.project_id,
                actor=actor,
                action="DATASET_WORKSHEET_SELECTION_FAILED",
                object_type="dataset_version",
                object_id=version.id,
            )
            _commit(session)
            raise
    _audit(
        session,
        project_id=version.project_id,
        actor=actor,
        action="DATASET_WORKSHEET_SELECTED",
        object_type="dataset_version",
        object_id=version.id,
        after={
            "worksheet_name": payload.worksheet_name,
            "acknowledge_hidden": payload.acknowledge_hidden,
        },
    )
    response = _version_data(version)
    _store_replay(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        path=WORKSHEET_SELECTION_PATH,
        key=idempotency_key,
        request_hash=request_hash,
        response=response,
    )
    _commit(session)
    return response, False


def preview(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    offset: int,
    limit: int,
    selected_columns: list[str] | None,
    storage_backend: ObjectStorage | None = None,
) -> dict[str, Any]:
    version, _, _ = _version_access(
        session, actor=actor, version_id=version_id, action="dataset.read"
    )
    if version.status not in {
        DatasetVersionStatus.AVAILABLE,
        DatasetVersionStatus.INVALIDATED,
    }:
        raise ContractError(
            status_code=409,
            code="DATASET_VERSION_NOT_AVAILABLE",
            message="The DatasetVersion preview is not available.",
        )
    columns = session.exec(
        select(DatasetColumn)
        .where(DatasetColumn.dataset_version_id == version.id)
        .order_by(col(DatasetColumn.column_order))
    ).all()
    by_name = {item.source_name: item for item in columns}
    names = selected_columns or list(by_name)
    if not names or any(name not in by_name for name in names):
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Preview columns must belong to the DatasetVersion.",
        )
    with tempfile.TemporaryDirectory(prefix="reca-dataset-preview-") as directory:
        local = Path(directory) / (
            "source.csv"
            if version.file_format == DatasetFileFormat.CSV
            else "source.xlsx"
        )
        artifact_service.download_available_artifact_to_path(
            session,
            artifact_id=version.artifact_id,
            project_id=version.project_id,
            path=local,
            storage_backend=storage_backend,
        )
        profile = (
            parsers.parse_csv(local, preview_offset=offset)
            if version.file_format == DatasetFileFormat.CSV
            else parsers.parse_xlsx(
                local, version.selected_worksheet_name or "", preview_offset=offset
            )
        )
    rows = []
    for row in profile.preview_rows[:limit]:
        output = {}
        for name in names:
            value = row.get(name)
            if by_name[name].is_sensitive and value not in {None, ""}:
                value = "***"
            else:
                value = parsers.redact_risky_value(value)
            if isinstance(value, str) and len(value) > limits.PREVIEW_CELL_CHARS:
                value = value[: limits.PREVIEW_CELL_CHARS]
            output[name] = value
        rows.append(output)
    return {
        "version_id": str(version.id),
        "offset": offset,
        "limit": limit,
        "columns": names,
        "rows": rows,
        "returned": len(rows),
        "total_rows": version.row_count,
        "truncated": offset + len(rows) < (version.row_count or 0),
    }
