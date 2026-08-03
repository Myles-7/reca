from __future__ import annotations

import hashlib
import json
import math
import tempfile
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc, func, or_
from sqlmodel import Session, col, select

from app.adapters.storage import (
    ObjectStorage,
    S3ObjectStorage,
    StorageError,
    StorageObjectExists,
)
from app.api.errors import ContractError
from app.artifacts.schemas import ArtifactUploadComplete, ArtifactUploadInitiate
from app.artifacts.validation import (
    ArtifactValidationError,
    policy_for,
    verify_file_content,
)
from app.core.config import settings
from app.models import (
    Artifact,
    ArtifactRelation,
    ArtifactRelationType,
    ArtifactStatus,
    ArtifactType,
    IdempotencyRecord,
    ProjectMemberRole,
    StorageProvider,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

UPLOAD_TTL = timedelta(minutes=30)
DOWNLOAD_TTL = timedelta(minutes=5)
SCHEMA_VERSION = "1.0"


def _encoded_dict(value: Any) -> dict[str, Any]:
    return cast(dict[str, Any], jsonable_encoder(value))


storage: ObjectStorage = S3ObjectStorage()


def _storage(override: ObjectStorage | None) -> ObjectStorage:
    return override or storage


def _artifact_key(
    *, project_id: uuid.UUID, artifact_id: uuid.UUID, is_original: bool
) -> str:
    kind = "original" if is_original else "derived"
    return f"projects/{project_id}/artifacts/{artifact_id}/{kind}"


def _metadata(artifact: Artifact) -> dict[str, Any]:
    return dict(artifact.artifact_metadata or {})


def _expires_at(artifact: Artifact) -> datetime:
    value = _metadata(artifact).get("upload_expires_at")
    if not isinstance(value, str):
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Artifact upload session has no valid expiration boundary.",
        )
    return datetime.fromisoformat(value)


def create_generated_json_artifact(
    session: Session,
    *,
    project_id: uuid.UUID,
    payload: Any,
    filename: str,
    artifact_type: ArtifactType,
    metadata: dict[str, Any],
    created_by: uuid.UUID | None = None,
    storage_backend: ObjectStorage | None = None,
) -> Artifact:
    encoded = json.dumps(
        jsonable_encoder(payload),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    artifact = Artifact(
        project_id=project_id,
        artifact_type=artifact_type,
        filename=filename,
        storage_provider=StorageProvider.MINIO,
        storage_key="",
        mime_type="application/json",
        size_bytes=len(encoded),
        sha256=digest,
        is_original=False,
        is_immutable=True,
        status=ArtifactStatus.AVAILABLE,
        artifact_metadata=jsonable_encoder(metadata),
        created_by=created_by,
    )
    artifact.storage_key = _artifact_key(
        project_id=project_id,
        artifact_id=artifact.id,
        is_original=False,
    )
    with tempfile.TemporaryDirectory(prefix="reca-generated-json-") as directory:
        path = Path(directory) / filename
        path.write_bytes(encoded)
        _storage(storage_backend).put_file_once(
            object_key=artifact.storage_key,
            path=path,
            content_sha256=digest,
            size_bytes=len(encoded),
        )
    session.add(artifact)
    session.flush()
    return artifact


def create_generated_bytes_artifact(
    session: Session,
    *,
    project_id: uuid.UUID,
    content: bytes,
    filename: str,
    mime_type: str,
    artifact_type: ArtifactType,
    metadata: dict[str, Any],
    source_artifact_id: uuid.UUID | None = None,
    created_by: uuid.UUID | None = None,
    storage_backend: ObjectStorage | None = None,
) -> Artifact:
    if not content:
        raise ValueError("Generated Artifact content must not be empty.")
    digest = hashlib.sha256(content).hexdigest()
    artifact = Artifact(
        project_id=project_id,
        artifact_type=artifact_type,
        filename=filename,
        storage_provider=StorageProvider.MINIO,
        storage_key="",
        mime_type=mime_type,
        size_bytes=len(content),
        sha256=digest,
        source_artifact_id=source_artifact_id,
        is_original=False,
        is_immutable=True,
        status=ArtifactStatus.AVAILABLE,
        artifact_metadata=jsonable_encoder(metadata),
        created_by=created_by,
    )
    artifact.storage_key = _artifact_key(
        project_id=project_id,
        artifact_id=artifact.id,
        is_original=False,
    )
    with tempfile.TemporaryDirectory(prefix="reca-generated-bytes-") as directory:
        path = Path(directory) / filename
        path.write_bytes(content)
        _storage(storage_backend).put_file_once(
            object_key=artifact.storage_key,
            path=path,
            content_sha256=digest,
            size_bytes=len(content),
        )
    session.add(artifact)
    session.flush()
    if source_artifact_id is not None:
        session.add(
            ArtifactRelation(
                project_id=project_id,
                source_artifact_id=source_artifact_id,
                target_artifact_id=artifact.id,
                relation_type=ArtifactRelationType.DERIVED_FROM,
                relation_metadata={"generated_sha256": digest},
            )
        )
        session.flush()
    return artifact


def download_available_artifact_to_path(
    session: Session,
    *,
    artifact_id: uuid.UUID,
    project_id: uuid.UUID,
    path: Path,
    storage_backend: ObjectStorage | None = None,
) -> Artifact:
    artifact = session.exec(
        select(Artifact).where(
            Artifact.id == artifact_id,
            Artifact.project_id == project_id,
            Artifact.status == ArtifactStatus.AVAILABLE,
            col(Artifact.deleted_at).is_(None),
        )
    ).first()
    if artifact is None:
        raise ContractError(
            status_code=409,
            code="FILE_NOT_AVAILABLE",
            message="The source Artifact is not available for processing.",
        )
    _storage(storage_backend).download_to_path(
        object_key=artifact.storage_key, path=path
    )
    if path.stat().st_size != artifact.size_bytes:
        raise StorageError("Downloaded Artifact size does not match metadata.")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != artifact.sha256:
        raise StorageError("Downloaded Artifact hash does not match metadata.")
    return artifact


def _artifact_allowed_actions(
    *, role: ProjectMemberRole, status: ArtifactStatus
) -> list[str]:
    role_actions = project_service.ROLE_ACTIONS[role]
    actions = ["artifact.read"] if "artifact.read" in role_actions else []
    if status == ArtifactStatus.AVAILABLE and "artifact.download" in role_actions:
        actions.append("artifact.download")
    if status == ArtifactStatus.UPLOADING and "artifact.upload" in role_actions:
        actions.append("artifact.upload")
    return actions


def artifact_data(artifact: Artifact, *, role: ProjectMemberRole) -> dict[str, Any]:
    return _encoded_dict(
        {
            "id": artifact.id,
            "project_id": artifact.project_id,
            "artifact_type": artifact.artifact_type,
            "filename": artifact.filename,
            "original_filename": artifact.original_filename,
            "mime_type": artifact.mime_type,
            "size_bytes": artifact.size_bytes,
            "sha256": artifact.sha256,
            "source_artifact_id": artifact.source_artifact_id,
            "is_original": artifact.is_original,
            "is_immutable": artifact.is_immutable,
            "status": artifact.status,
            "created_by": artifact.created_by,
            "created_at": artifact.created_at,
            "deleted_at": artifact.deleted_at,
            "allowed_actions": _artifact_allowed_actions(
                role=role, status=artifact.status
            ),
        }
    )


def _idempotency_record(
    session: Session,
    *,
    actor_id: uuid.UUID,
    project_id: uuid.UUID,
    method: str,
    path_template: str,
    key: str,
) -> IdempotencyRecord | None:
    return session.exec(
        select(IdempotencyRecord).where(
            IdempotencyRecord.actor_id == actor_id,
            IdempotencyRecord.project_id == project_id,
            IdempotencyRecord.method == method,
            IdempotencyRecord.path_template == path_template,
            IdempotencyRecord.idempotency_key == key,
        )
    ).first()


def _replay(
    session: Session,
    *,
    actor_id: uuid.UUID,
    project_id: uuid.UUID,
    method: str,
    path_template: str,
    key: str,
    request_hash: str,
) -> tuple[dict[str, Any], int] | None:
    record = _idempotency_record(
        session,
        actor_id=actor_id,
        project_id=project_id,
        method=method,
        path_template=path_template,
        key=key,
    )
    if record is None:
        return None
    if record.request_hash != request_hash:
        raise ContractError(
            status_code=409,
            code="IDEMPOTENCY_CONFLICT",
            message="The Idempotency-Key was already used with a different request.",
        )
    body = dict(record.response_body or {})
    error = body.get("_error")
    if isinstance(error, dict):
        raise ContractError(
            status_code=record.response_status,
            code=str(error["code"]),
            message=str(error["message"]),
            details=dict(error.get("details") or {}),
        )
    return body, record.response_status


def _store_result(
    session: Session,
    *,
    actor_id: uuid.UUID,
    project_id: uuid.UUID,
    method: str,
    path_template: str,
    key: str,
    request_hash: str,
    status_code: int,
    body: dict[str, Any],
) -> None:
    session.add(
        IdempotencyRecord(
            actor_id=actor_id,
            project_id=project_id,
            method=method,
            path_template=path_template,
            idempotency_key=key,
            request_hash=request_hash,
            response_status=status_code,
            response_body=body,
            expires_at=datetime.now(UTC) + project_service.IDEMPOTENCY_RETENTION,
        )
    )


def _store_error(
    session: Session,
    *,
    actor_id: uuid.UUID,
    project_id: uuid.UUID,
    method: str,
    path_template: str,
    key: str,
    request_hash: str,
    error: ContractError,
) -> None:
    _store_result(
        session,
        actor_id=actor_id,
        project_id=project_id,
        method=method,
        path_template=path_template,
        key=key,
        request_hash=request_hash,
        status_code=error.status_code,
        body={
            "_error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
            }
        },
    )


def _validation_contract_error(error: ArtifactValidationError) -> ContractError:
    return ContractError(
        status_code=error.status_code,
        code=error.code,
        message=error.message,
    )


def initiate_upload(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    payload: ArtifactUploadInitiate,
    idempotency_key: str,
) -> tuple[dict[str, Any], bool]:
    project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="artifact.upload",
        for_update=True,
    )
    request_digest = project_service.request_hash(payload)
    path_template = "/api/v1/projects/{project_id}/artifacts/uploads"
    replay = _replay(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=path_template,
        key=idempotency_key,
        request_hash=request_digest,
    )
    if replay:
        return replay[0], True

    try:
        filename, policy = policy_for(
            artifact_type=payload.artifact_type,
            filename=payload.filename,
            declared_mime=payload.mime_type,
        )
    except ArtifactValidationError as error:
        raise _validation_contract_error(error)
    if payload.size_bytes > policy.max_bytes:
        raise ContractError(
            status_code=413,
            code="FILE_TOO_LARGE",
            message="File exceeds the configured upload limit.",
        )
    if payload.is_original and payload.source_artifact_id is not None:
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="An original Artifact cannot reference a source Artifact.",
        )
    if payload.source_artifact_id is not None:
        source = session.exec(
            select(Artifact).where(
                Artifact.id == payload.source_artifact_id,
                Artifact.project_id == project_id,
                Artifact.status == ArtifactStatus.AVAILABLE,
                col(Artifact.deleted_at).is_(None),
            )
        ).first()
        if source is None:
            raise ContractError(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="Resource not found.",
            )

    artifact_id = uuid.uuid4()
    expires_at = get_datetime_utc() + UPLOAD_TTL
    artifact = Artifact(
        id=artifact_id,
        project_id=project_id,
        artifact_type=payload.artifact_type,
        filename=filename,
        original_filename=filename,
        storage_key=_artifact_key(
            project_id=project_id,
            artifact_id=artifact_id,
            is_original=payload.is_original,
        ),
        mime_type=policy.mime_type,
        size_bytes=payload.size_bytes,
        sha256=payload.sha256,
        source_artifact_id=payload.source_artifact_id,
        is_original=payload.is_original,
        is_immutable=True,
        status=ArtifactStatus.UPLOADING,
        artifact_metadata={
            "upload_expires_at": expires_at.isoformat(),
            "content_transferred_at": None,
        },
        created_by=actor.id,
    )
    session.add(artifact)
    session.flush()
    project_service._add_audit(
        session,
        project_id=project_id,
        actor=actor,
        action="ARTIFACT_UPLOAD_INITIATED",
        object_type="artifact",
        object_id=artifact.id,
        after={
            "artifact_type": artifact.artifact_type,
            "filename": artifact.filename,
            "size_bytes": artifact.size_bytes,
            "sha256": artifact.sha256,
            "is_original": artifact.is_original,
            "status": artifact.status,
        },
    )
    data = jsonable_encoder(
        {
            "upload_id": artifact.id,
            "artifact_id": artifact.id,
            "status": artifact.status,
            "upload_method": "PUT",
            "upload_url": f"/api/v1/artifact-uploads/{artifact.id}/content",
            "required_headers": {"Content-Type": "application/octet-stream"},
            "expires_at": expires_at,
        }
    )
    _store_result(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=path_template,
        key=idempotency_key,
        request_hash=request_digest,
        status_code=201,
        body=data,
    )
    project_service._commit(session)
    return data, False


def _get_upload_for_actor(
    session: Session, *, actor: User, upload_id: uuid.UUID
) -> Artifact:
    visible = session.get(Artifact, upload_id)
    if visible is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    project_service.authorize_project(
        session,
        project_id=visible.project_id,
        actor=actor,
        action="artifact.upload",
        for_update=True,
    )
    artifact = session.exec(
        select(Artifact)
        .where(Artifact.id == upload_id, Artifact.project_id == visible.project_id)
        .with_for_update()
    ).first()
    if artifact is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    return artifact


def _expire_upload(session: Session, *, artifact: Artifact, actor: User) -> None:
    artifact.status = ArtifactStatus.FAILED
    session.add(artifact)
    project_service._add_audit(
        session,
        project_id=artifact.project_id,
        actor=actor,
        action="ARTIFACT_UPLOAD_FAILED",
        object_type="artifact",
        object_id=artifact.id,
        after={"filename": artifact.filename, "status": artifact.status},
        reason="Upload session expired.",
    )
    project_service._commit(session)


async def transfer_content(
    session: Session,
    *,
    actor: User,
    upload_id: uuid.UUID,
    chunks: AsyncIterator[bytes],
    storage_backend: ObjectStorage | None = None,
) -> None:
    artifact = _get_upload_for_actor(session, actor=actor, upload_id=upload_id)
    if artifact.status != ArtifactStatus.UPLOADING:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Artifact upload does not accept content in its current state.",
        )
    metadata = _metadata(artifact)
    if metadata.get("content_transferred_at") is not None:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Artifact upload content was already transferred.",
        )
    if _expires_at(artifact) <= get_datetime_utc():
        _expire_upload(session, artifact=artifact, actor=actor)
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Artifact upload session has expired.",
        )

    with tempfile.TemporaryDirectory(prefix="reca-artifact-") as directory:
        path = Path(directory) / "content"
        digest = hashlib.sha256()
        size_bytes = 0
        with path.open("wb") as target:
            async for chunk in chunks:
                size_bytes += len(chunk)
                if size_bytes > settings.MAX_UPLOAD_BYTES:
                    raise ContractError(
                        status_code=413,
                        code="FILE_TOO_LARGE",
                        message="Transferred content exceeds the configured limit.",
                    )
                digest.update(chunk)
                target.write(chunk)
        observed_hash = digest.hexdigest()
        backend = _storage(storage_backend)
        try:
            backend.put_file_once(
                object_key=artifact.storage_key,
                path=path,
                content_sha256=observed_hash,
                size_bytes=size_bytes,
            )
        except StorageObjectExists:
            recovery_path = Path(directory) / "existing"
            try:
                backend.download_to_path(
                    object_key=artifact.storage_key, path=recovery_path
                )
            except StorageError as error:
                raise ContractError(
                    status_code=503,
                    code="FILE_UPLOAD_FAILED",
                    message="Object storage could not verify the existing upload.",
                    retryable=True,
                ) from error
            existing = recovery_path.read_bytes()
            if (
                len(existing) != size_bytes
                or hashlib.sha256(existing).hexdigest() != observed_hash
            ):
                artifact.status = ArtifactStatus.FAILED
                session.add(artifact)
                project_service._add_audit(
                    session,
                    project_id=artifact.project_id,
                    actor=actor,
                    action="ARTIFACT_UPLOAD_FAILED",
                    object_type="artifact",
                    object_id=artifact.id,
                    after={"filename": artifact.filename, "status": artifact.status},
                    reason="Storage key collision did not match the transferred content.",
                )
                project_service._commit(session)
                raise ContractError(
                    status_code=503,
                    code="FILE_UPLOAD_FAILED",
                    message="Object storage rejected the upload.",
                )
        except StorageError as error:
            artifact.status = ArtifactStatus.FAILED
            session.add(artifact)
            project_service._add_audit(
                session,
                project_id=artifact.project_id,
                actor=actor,
                action="ARTIFACT_UPLOAD_FAILED",
                object_type="artifact",
                object_id=artifact.id,
                after={"filename": artifact.filename, "status": artifact.status},
                reason="Object storage write failed.",
            )
            project_service._commit(session)
            raise ContractError(
                status_code=503,
                code="FILE_UPLOAD_FAILED",
                message="Object storage rejected the upload.",
                retryable=True,
            ) from error

    metadata["content_transferred_at"] = get_datetime_utc().isoformat()
    metadata["transferred_size_bytes"] = size_bytes
    metadata["transferred_sha256"] = observed_hash
    artifact.artifact_metadata = metadata
    session.add(artifact)
    project_service._commit(session)


def _terminal_complete_error(
    session: Session,
    *,
    artifact: Artifact,
    actor: User,
    idempotency_key: str,
    request_digest: str,
    error: ContractError,
) -> None:
    artifact.status = ArtifactStatus.QUARANTINED
    session.add(artifact)
    project_service._add_audit(
        session,
        project_id=artifact.project_id,
        actor=actor,
        action="ARTIFACT_QUARANTINED",
        object_type="artifact",
        object_id=artifact.id,
        after={
            "filename": artifact.filename,
            "status": artifact.status,
            "error_code": error.code,
        },
        reason=error.message,
    )
    _store_error(
        session,
        actor_id=actor.id,
        project_id=artifact.project_id,
        method="POST",
        path_template=(
            "/api/v1/projects/{project_id}/artifacts/uploads/{upload_id}/complete"
        ),
        key=idempotency_key,
        request_hash=request_digest,
        error=error,
    )
    project_service._commit(session)


def complete_upload(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    upload_id: uuid.UUID,
    payload: ArtifactUploadComplete,
    idempotency_key: str,
    storage_backend: ObjectStorage | None = None,
) -> tuple[dict[str, Any], uuid.UUID | None, bool]:
    access = project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="artifact.upload",
        for_update=True,
    )
    assert access.membership is not None
    request_digest = project_service.request_hash(payload)
    path_template = (
        "/api/v1/projects/{project_id}/artifacts/uploads/{upload_id}/complete"
    )
    replay = _replay(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=path_template,
        key=idempotency_key,
        request_hash=request_digest,
    )
    if replay:
        body = replay[0]
        duplicate_id = body.get("duplicate_of_artifact_id")
        return (
            dict(body["artifact"]),
            uuid.UUID(duplicate_id) if isinstance(duplicate_id, str) else None,
            True,
        )
    artifact = session.exec(
        select(Artifact)
        .where(Artifact.id == upload_id, Artifact.project_id == project_id)
        .with_for_update()
    ).first()
    if artifact is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    if artifact.status != ArtifactStatus.UPLOADING:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Artifact upload cannot be completed in its current state.",
        )
    metadata = _metadata(artifact)
    if metadata.get("content_transferred_at") is None:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Artifact content has not been transferred.",
        )
    if _expires_at(artifact) <= get_datetime_utc():
        _expire_upload(session, artifact=artifact, actor=actor)
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Artifact upload session has expired.",
        )

    backend = _storage(storage_backend)
    with tempfile.TemporaryDirectory(prefix="reca-artifact-verify-") as directory:
        path = Path(directory) / "content"
        try:
            backend.download_to_path(object_key=artifact.storage_key, path=path)
        except StorageError as storage_error:
            error = ContractError(
                status_code=503,
                code="FILE_UPLOAD_FAILED",
                message="Uploaded content could not be read from object storage.",
                retryable=True,
            )
            artifact.status = ArtifactStatus.FAILED
            session.add(artifact)
            project_service._add_audit(
                session,
                project_id=project_id,
                actor=actor,
                action="ARTIFACT_UPLOAD_FAILED",
                object_type="artifact",
                object_id=artifact.id,
                after={"filename": artifact.filename, "status": artifact.status},
                reason=error.message,
            )
            _store_error(
                session,
                actor_id=actor.id,
                project_id=project_id,
                method="POST",
                path_template=path_template,
                key=idempotency_key,
                request_hash=request_digest,
                error=error,
            )
            project_service._commit(session)
            raise error from storage_error

        actual_size = path.stat().st_size
        digest = hashlib.sha256()
        with path.open("rb") as content:
            for chunk in iter(lambda: content.read(1024 * 1024), b""):
                digest.update(chunk)
        actual_hash = digest.hexdigest()
        try:
            _, policy = policy_for(
                artifact_type=artifact.artifact_type,
                filename=artifact.filename,
                declared_mime=artifact.mime_type,
            )
            verified_mime = verify_file_content(path, policy=policy)
        except ArtifactValidationError as validation_error:
            error = _validation_contract_error(validation_error)
            _terminal_complete_error(
                session,
                artifact=artifact,
                actor=actor,
                idempotency_key=idempotency_key,
                request_digest=request_digest,
                error=error,
            )
            raise error

    if (
        actual_hash != artifact.sha256
        or actual_hash != payload.sha256
        or actual_size != artifact.size_bytes
        or actual_size != payload.size_bytes
    ):
        error = ContractError(
            status_code=409,
            code="FILE_HASH_MISMATCH",
            message="Uploaded content hash or size does not match its declarations.",
        )
        _terminal_complete_error(
            session,
            artifact=artifact,
            actor=actor,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            error=error,
        )
        raise error

    duplicate = session.exec(
        select(Artifact).where(
            Artifact.project_id == project_id,
            Artifact.id != artifact.id,
            Artifact.status == ArtifactStatus.AVAILABLE,
            Artifact.sha256 == actual_hash,
            col(Artifact.deleted_at).is_(None),
        )
    ).first()
    artifact.mime_type = verified_mime
    artifact.size_bytes = actual_size
    artifact.sha256 = actual_hash
    artifact.status = ArtifactStatus.AVAILABLE
    metadata["verified_at"] = get_datetime_utc().isoformat()
    artifact.artifact_metadata = metadata
    session.add(artifact)
    if artifact.source_artifact_id is not None:
        session.add(
            ArtifactRelation(
                project_id=project_id,
                source_artifact_id=artifact.source_artifact_id,
                target_artifact_id=artifact.id,
                relation_type=ArtifactRelationType.DERIVED_FROM,
            )
        )
    project_service._add_audit(
        session,
        project_id=project_id,
        actor=actor,
        action="ARTIFACT_AVAILABLE",
        object_type="artifact",
        object_id=artifact.id,
        after={
            "artifact_type": artifact.artifact_type,
            "filename": artifact.filename,
            "mime_type": artifact.mime_type,
            "size_bytes": artifact.size_bytes,
            "sha256": artifact.sha256,
            "is_original": artifact.is_original,
            "status": artifact.status,
        },
    )
    public = artifact_data(artifact, role=access.membership.role)
    stored_body = {
        "artifact": public,
        "duplicate_of_artifact_id": str(duplicate.id) if duplicate else None,
    }
    _store_result(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=path_template,
        key=idempotency_key,
        request_hash=request_digest,
        status_code=200,
        body=stored_body,
    )
    project_service._commit(session)
    return public, duplicate.id if duplicate else None, False


def list_artifacts(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    artifact_type: ArtifactType | None,
    status: ArtifactStatus | None,
    is_original: bool | None,
    q: str | None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    access = project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="artifact.read"
    )
    assert access.membership is not None
    filters: list[Any] = [
        Artifact.project_id == project_id,
        col(Artifact.deleted_at).is_(None),
        Artifact.status != ArtifactStatus.DELETED,
    ]
    if artifact_type is not None:
        filters.append(Artifact.artifact_type == artifact_type)
    if status is not None:
        filters.append(Artifact.status == status)
    if is_original is not None:
        filters.append(Artifact.is_original == is_original)
    if q:
        pattern = f"%{q.strip()}%"
        filters.append(
            or_(
                col(Artifact.filename).ilike(pattern),
                col(Artifact.original_filename).ilike(pattern),
            )
        )
    total = session.exec(
        select(func.count()).select_from(Artifact).where(*filters)
    ).one()
    rows = session.exec(
        select(Artifact)
        .where(*filters)
        .order_by(desc(col(Artifact.created_at)), desc(col(Artifact.id)))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    total_pages = math.ceil(total / page_size) if total else 0
    return (
        [artifact_data(item, role=access.membership.role) for item in rows],
        {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        },
        project_service.allowed_actions(access.membership.role),
    )


def get_artifact(
    session: Session, *, actor: User, artifact_id: uuid.UUID
) -> dict[str, Any]:
    artifact = session.get(Artifact, artifact_id)
    if (
        artifact is None
        or artifact.deleted_at is not None
        or artifact.status == ArtifactStatus.DELETED
    ):
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    access = project_service.authorize_project(
        session,
        project_id=artifact.project_id,
        actor=actor,
        action="artifact.read",
    )
    assert access.membership is not None
    return artifact_data(artifact, role=access.membership.role)


def authorize_download(
    session: Session,
    *,
    actor: User,
    artifact_id: uuid.UUID,
    storage_backend: ObjectStorage | None = None,
) -> dict[str, Any]:
    artifact = session.get(Artifact, artifact_id)
    if (
        artifact is None
        or artifact.deleted_at is not None
        or artifact.status == ArtifactStatus.DELETED
    ):
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    project_service.authorize_project(
        session,
        project_id=artifact.project_id,
        actor=actor,
        action="artifact.download",
    )
    if artifact.status != ArtifactStatus.AVAILABLE:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Artifact is not available for download.",
        )
    try:
        download_url = _storage(storage_backend).presign_download(
            object_key=artifact.storage_key,
            expires_seconds=int(DOWNLOAD_TTL.total_seconds()),
        )
    except StorageError as error:
        raise ContractError(
            status_code=503,
            code="FILE_UPLOAD_FAILED",
            message="Object storage could not authorize the download.",
            retryable=True,
        ) from error
    expires_at = get_datetime_utc() + DOWNLOAD_TTL
    project_service._add_audit(
        session,
        project_id=artifact.project_id,
        actor=actor,
        action="ARTIFACT_DOWNLOAD_AUTHORIZED",
        object_type="artifact",
        object_id=artifact.id,
        after={"filename": artifact.filename, "status": artifact.status},
    )
    project_service._commit(session)
    return _encoded_dict(
        {
            "artifact_id": artifact.id,
            "download_url": download_url,
            "expires_at": expires_at,
            "disposition_filename": artifact.filename,
        }
    )
