from __future__ import annotations

import hashlib
import tempfile
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy import delete
from sqlmodel import Session, col, select

from app.adapters.documents import DocumentParseError, GrobidAdapter, GrobidProvider
from app.adapters.storage import ObjectStorage, StorageError
from app.api.errors import ContractError
from app.artifacts import service as artifact_service
from app.artifacts.schemas import ArtifactUploadComplete, ArtifactUploadInitiate
from app.artifacts.validation import (
    ArtifactValidationError,
    policy_for,
    verify_file_content,
)
from app.documents.parsing import ParsedDocument, convert_tei, parse_with_pypdf
from app.jobs import service as job_service
from app.jobs.dispatcher import dispatcher as default_dispatcher
from app.models import (
    Artifact,
    ArtifactStatus,
    ArtifactType,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentParseConfidence,
    DocumentParserType,
    DocumentType,
    IdempotencyRecord,
    Job,
    JobStatus,
    JobTaskType,
    LiteratureRecord,
    ProcessingRun,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

_PATH_TEMPLATE = "/api/v1/projects/{project_id}/documents"
_PARSE_PATH_TEMPLATE = "/api/v1/documents/{document_id}/parse"
_CHUNK_SIZE = 1024 * 1024


def _document_data(
    document: Document,
    *,
    can_update: bool = False,
    literature_record_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    parse_blocked = document.parse_status in {
        JobStatus.QUEUED,
        JobStatus.RUNNING,
        JobStatus.CANCEL_REQUESTED,
    }
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "id": document.id,
                "project_id": document.project_id,
                "artifact_id": document.artifact_id,
                "literature_record_id": literature_record_id,
                "document_type": document.document_type,
                "parser_type": document.parser_type,
                "parser_version": document.parser_version,
                "parse_status": document.parse_status,
                "page_count": document.page_count,
                "language": document.language,
                "is_scanned": document.is_scanned,
                "parse_confidence": document.parse_confidence,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
                "allowed_actions": [
                    "document.read",
                    *(["document.upload"] if can_update else []),
                    *(["document.parse"] if can_update and not parse_blocked else []),
                ],
            }
        ),
    )


def _validation_error(error: ArtifactValidationError) -> ContractError:
    return ContractError(
        status_code=error.status_code,
        code=error.code,
        message=error.message,
    )


def _derived_key(idempotency_key: str, purpose: str) -> str:
    return hashlib.sha256(f"{idempotency_key}:{purpose}".encode()).hexdigest()


def _inspect_pdf(path: Path) -> bool | None:
    try:
        _, policy = policy_for(
            artifact_type=ArtifactType.PDF_DOCUMENT,
            filename="document.pdf",
            declared_mime="application/pdf",
        )
        verify_file_content(path, policy=policy)
    except ArtifactValidationError as error:
        raise _validation_error(error) from error

    with path.open("rb") as source:
        source.seek(0, 2)
        size = source.tell()
        source.seek(max(0, size - 4096))
        tail = source.read()
    if b"%%EOF" not in tail:
        raise ContractError(
            status_code=415,
            code="FILE_TYPE_UNSUPPORTED",
            message="PDF structure is incomplete or damaged.",
            details={"pdf_status": "CORRUPT"},
        )

    encrypted = False
    image_marker = False
    text_marker = False
    overlap = b""
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(_CHUNK_SIZE), b""):
            sample = overlap + chunk
            encrypted = encrypted or b"/Encrypt" in sample
            image_marker = image_marker or b"/Subtype /Image" in sample
            text_marker = text_marker or any(
                marker in sample for marker in (b" BT", b"\nBT", b" Tj", b" TJ")
            )
            overlap = sample[-32:]
    if encrypted:
        raise ContractError(
            status_code=415,
            code="FILE_TYPE_UNSUPPORTED",
            message="Encrypted PDF files must be replaced with a lawful decrypted copy.",
            details={"pdf_status": "ENCRYPTED"},
        )
    if image_marker and not text_marker:
        return True
    if text_marker:
        return False
    return None


async def _stage_upload(
    *,
    filename: str,
    mime_type: str,
    chunks: AsyncIterator[bytes],
    path: Path,
) -> tuple[str, int, str, bool | None]:
    try:
        safe_name, policy = policy_for(
            artifact_type=ArtifactType.PDF_DOCUMENT,
            filename=filename,
            declared_mime=mime_type,
        )
    except ArtifactValidationError as error:
        raise _validation_error(error) from error
    digest = hashlib.sha256()
    size_bytes = 0
    with path.open("wb") as target:
        async for chunk in chunks:
            size_bytes += len(chunk)
            if size_bytes > policy.max_bytes:
                raise ContractError(
                    status_code=413,
                    code="FILE_TOO_LARGE",
                    message="File exceeds the configured PDF upload limit.",
                )
            digest.update(chunk)
            target.write(chunk)
    if size_bytes == 0:
        raise ContractError(
            status_code=415,
            code="FILE_TYPE_UNSUPPORTED",
            message="An empty file is not a valid PDF.",
        )
    return safe_name, size_bytes, digest.hexdigest(), _inspect_pdf(path)


async def _path_chunks(path: Path) -> AsyncIterator[bytes]:
    with path.open("rb") as source:
        while chunk := source.read(_CHUNK_SIZE):
            yield chunk


async def upload_pdf(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    filename: str,
    mime_type: str,
    chunks: AsyncIterator[bytes],
    document_type: DocumentType,
    literature_record_id: uuid.UUID | None,
    idempotency_key: str,
) -> project_service.OperationResult:
    access = project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="artifact.upload",
    )
    assert access.membership is not None
    if document_type != DocumentType.SCHOLARLY_PDF:
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="The PDF upload endpoint only accepts SCHOLARLY_PDF documents.",
        )

    with tempfile.TemporaryDirectory(prefix="reca-document-upload-") as directory:
        path = Path(directory) / "document.pdf"
        safe_name, size_bytes, sha256, is_scanned = await _stage_upload(
            filename=filename,
            mime_type=mime_type,
            chunks=chunks,
            path=path,
        )
        request_digest = project_service.request_hash(
            {
                "filename": safe_name,
                "mime_type": "application/pdf",
                "size_bytes": size_bytes,
                "sha256": sha256,
                "document_type": document_type,
                "literature_record_id": literature_record_id,
            }
        )
        replay = project_service._replay_or_conflict(
            session,
            actor_id=actor.id,
            project_id=project_id,
            method="POST",
            path_template=_PATH_TEMPLATE,
            key=idempotency_key,
            payload_hash=request_digest,
        )
        if replay is not None:
            return replay

        literature: LiteratureRecord | None = None
        if literature_record_id is not None:
            literature = session.exec(
                select(LiteratureRecord).where(
                    LiteratureRecord.id == literature_record_id,
                    LiteratureRecord.project_id == project_id,
                )
            ).first()
            if literature is None or literature.deleted_at is not None:
                raise ContractError(
                    status_code=404,
                    code="RESOURCE_NOT_FOUND",
                    message="Resource not found.",
                )
            if literature.document_id is not None:
                raise ContractError(
                    status_code=409,
                    code="INVALID_STATE_TRANSITION",
                    message="LiteratureRecord is already bound to a Document.",
                )

        upload_data, _ = artifact_service.initiate_upload(
            session,
            actor=actor,
            project_id=project_id,
            payload=ArtifactUploadInitiate(
                artifact_type=ArtifactType.PDF_DOCUMENT,
                filename=safe_name,
                mime_type="application/pdf",
                size_bytes=size_bytes,
                sha256=sha256,
                is_original=True,
            ),
            idempotency_key=_derived_key(idempotency_key, "artifact-init"),
        )
        artifact_id = uuid.UUID(str(upload_data["artifact_id"]))
        artifact = session.get(Artifact, artifact_id)
        assert artifact is not None
        duplicate_id: uuid.UUID | None = None
        if artifact.status == ArtifactStatus.UPLOADING:
            metadata = dict(artifact.artifact_metadata or {})
            if metadata.get("content_transferred_at") is None:
                await artifact_service.transfer_content(
                    session,
                    actor=actor,
                    upload_id=artifact.id,
                    chunks=_path_chunks(path),
                )
            artifact_public, duplicate_id, _ = artifact_service.complete_upload(
                session,
                actor=actor,
                project_id=project_id,
                upload_id=artifact.id,
                payload=ArtifactUploadComplete(
                    sha256=sha256,
                    size_bytes=size_bytes,
                ),
                idempotency_key=_derived_key(idempotency_key, "artifact-complete"),
            )
        elif artifact.status == ArtifactStatus.AVAILABLE:
            artifact_public = artifact_service.get_artifact(
                session, actor=actor, artifact_id=artifact.id
            )
        else:
            raise ContractError(
                status_code=409,
                code="FILE_NOT_AVAILABLE",
                message="The Artifact is not available for Document binding.",
            )

        existing_document = session.exec(
            select(Document).where(Document.artifact_id == artifact.id)
        ).first()
        document = existing_document or Document(
            project_id=project_id,
            artifact_id=artifact.id,
            document_type=document_type,
            parser_type=DocumentParserType.NONE,
            parse_status=JobStatus.DRAFT,
            is_scanned=is_scanned,
            parse_confidence=DocumentParseConfidence.UNKNOWN,
        )
        if existing_document is None:
            session.add(document)
        if literature is not None:
            literature.document_id = document.id
            session.add(literature)
        project_service._add_audit(
            session,
            project_id=project_id,
            actor=actor,
            action="DOCUMENT_UPLOADED",
            object_type="document",
            object_id=document.id,
            after={
                "artifact_id": str(artifact.id),
                "document_type": document.document_type,
                "parse_status": document.parse_status,
                "is_scanned": document.is_scanned,
                "literature_record_id": (
                    str(literature_record_id)
                    if literature_record_id is not None
                    else None
                ),
            },
        )
        result = project_service.OperationResult(
            data={
                "artifact": artifact_public,
                "document": _document_data(
                    document,
                    can_update=True,
                    literature_record_id=literature_record_id,
                ),
                "duplicate_of_artifact_id": (
                    str(duplicate_id) if duplicate_id is not None else None
                ),
            },
            status_code=201,
        )
        project_service._store_idempotency(
            session,
            actor_id=actor.id,
            project_id=project_id,
            method="POST",
            path_template=_PATH_TEMPLATE,
            key=idempotency_key,
            payload_hash=request_digest,
            result=result,
        )
        project_service._commit(session)
        return result


def get_document(
    session: Session, *, actor: User, document_id: uuid.UUID
) -> dict[str, Any]:
    document = session.get(Document, document_id)
    if document is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    access = project_service.authorize_project(
        session,
        project_id=document.project_id,
        actor=actor,
        action="project.read",
    )
    can_update = access.membership is not None and "project.update" in (
        project_service.allowed_actions(access.membership.role)
    )
    literature_record_id = session.exec(
        select(LiteratureRecord.id).where(
            LiteratureRecord.project_id == document.project_id,
            LiteratureRecord.document_id == document.id,
            col(LiteratureRecord.deleted_at).is_(None),
        )
    ).first()
    return _document_data(
        document,
        can_update=can_update,
        literature_record_id=literature_record_id,
    )


def request_parse(
    session: Session,
    *,
    actor: User,
    document_id: uuid.UUID,
    allow_fallback: bool,
    extract_coordinates: bool,
    idempotency_key: str,
    dispatcher: job_service.JobDispatcher = default_dispatcher,
) -> project_service.OperationResult:
    document = session.get(Document, document_id)
    if document is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    project_service.authorize_project(
        session,
        project_id=document.project_id,
        actor=actor,
        action="project.update",
    )
    request_payload = {
        "document_id": document.id,
        "allow_fallback": allow_fallback,
        "extract_coordinates": extract_coordinates,
    }
    digest = project_service.request_hash(request_payload)
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=document.project_id,
        method="POST",
        path_template=_PARSE_PATH_TEMPLATE,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        data = dict(replay.data or {})
        data.pop("_document_parse_parameters", None)
        return project_service.OperationResult(
            data=data,
            status_code=replay.status_code,
            idempotency_replayed=True,
        )
    active = session.exec(
        select(Job).where(
            Job.project_id == document.project_id,
            Job.task_type == JobTaskType.DOCUMENT_PARSE,
            Job.resource_id == document.id,
            col(Job.status).in_([JobStatus.QUEUED, JobStatus.RUNNING]),
        )
    ).first()
    if active is not None:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Document parsing is already in progress.",
        )
    job = job_service.create_job(
        session,
        project_id=document.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.DOCUMENT_PARSE,
            resource_type="document",
            resource_id=document.id,
            idempotency_key=idempotency_key,
            requested_by_user_id=actor.id,
            max_retries=1,
            retryable=True,
        ),
    )
    job.current_step = "QUEUED"
    job.total_steps = 4
    document.parse_status = JobStatus.QUEUED
    document.updated_at = get_datetime_utc()
    session.add(job)
    session.add(document)
    project_service._add_audit(
        session,
        project_id=document.project_id,
        actor=actor,
        action="DOCUMENT_PARSE_REQUESTED",
        object_type="document",
        object_id=document.id,
        after={
            "job_id": str(job.id),
            "allow_fallback": allow_fallback,
            "extract_coordinates": extract_coordinates,
            "parse_status": document.parse_status,
        },
    )
    project_service._commit(session)
    dispatched = job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)
    if dispatched.status == JobStatus.DISPATCH_FAILED:
        document = session.get(Document, document.id)
        assert document is not None
        document.parse_status = JobStatus.DISPATCH_FAILED
        document.updated_at = get_datetime_utc()
        session.add(document)
        project_service._commit(session)
    public_data = job_service.job_data(session, dispatched)
    stored_data = {
        **public_data,
        "_document_parse_parameters": {
            "allow_fallback": allow_fallback,
            "extract_coordinates": extract_coordinates,
        },
    }
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=document.project_id,
        method="POST",
        path_template=_PARSE_PATH_TEMPLATE,
        key=idempotency_key,
        payload_hash=digest,
        result=project_service.OperationResult(data=stored_data, status_code=202),
    )
    project_service._commit(session)
    return project_service.OperationResult(data=public_data, status_code=202)


def _job_parameters(session: Session, job: Job) -> dict[str, bool]:
    if job.requested_by_user_id is None:
        return {"allow_fallback": True, "extract_coordinates": True}
    record = session.exec(
        select(IdempotencyRecord).where(
            IdempotencyRecord.actor_id == job.requested_by_user_id,
            IdempotencyRecord.project_id == job.project_id,
            IdempotencyRecord.method == "POST",
            IdempotencyRecord.path_template == _PARSE_PATH_TEMPLATE,
            IdempotencyRecord.idempotency_key == job.idempotency_key,
        )
    ).first()
    body = dict(record.response_body or {}) if record is not None else {}
    raw = body.get("_document_parse_parameters")
    if not isinstance(raw, dict):
        return {"allow_fallback": True, "extract_coordinates": True}
    return {
        "allow_fallback": raw.get("allow_fallback") is True,
        "extract_coordinates": raw.get("extract_coordinates") is True,
    }


def _system_audit(
    session: Session,
    *,
    document: Document,
    action: str,
    job_id: uuid.UUID,
    run_id: uuid.UUID,
    after: dict[str, Any],
    outcome: AuditOutcome = AuditOutcome.SUCCEEDED,
) -> None:
    session.add(
        AuditLog(
            project_id=document.project_id,
            actor_type=AuditActorType.WORKER,
            actor_id="document-parser",
            action=action,
            object_type="document",
            object_id=document.id,
            after_snapshot={"processing_run_id": str(run_id), **after},
            job_id=job_id,
            outcome=outcome,
        )
    )


def _persist_parsed_document(
    session: Session,
    *,
    document: Document,
    parsed: ParsedDocument,
    parser_type: DocumentParserType,
    parser_version: str,
    confidence: DocumentParseConfidence,
) -> None:
    session.exec(
        delete(DocumentChunk).where(col(DocumentChunk.document_id) == document.id)
    )
    session.exec(
        delete(DocumentPage).where(col(DocumentPage.document_id) == document.id)
    )
    for page in parsed.pages:
        session.add(
            DocumentPage(
                document_id=document.id,
                project_id=document.project_id,
                page_number=page.page_number,
                text_content=page.text or None,
                width=page.width,
                height=page.height,
                parser_metadata=page.metadata,
            )
        )
    for chunk in parsed.chunks:
        session.add(
            DocumentChunk(
                project_id=document.project_id,
                document_id=document.id,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                section_path=chunk.section_path,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                content_hash=chunk.content_hash,
                chunk_metadata=chunk.metadata,
            )
        )
    document.parser_type = parser_type
    document.parser_version = parser_version
    document.parse_status = JobStatus.COMPLETED
    document.page_count = max(page.page_number for page in parsed.pages)
    document.language = parsed.language
    document.parse_confidence = confidence
    document.is_scanned = False
    document.updated_at = get_datetime_utc()
    session.add(document)


def _mark_parse_failed(
    session: Session,
    *,
    job: Job,
    document_id: uuid.UUID,
    run_id: uuid.UUID,
    error_code: str,
) -> None:
    session.rollback()
    document = session.get(Document, document_id)
    assert document is not None
    document.parse_status = JobStatus.FAILED
    document.updated_at = get_datetime_utc()
    session.add(document)
    _system_audit(
        session,
        document=document,
        action="DOCUMENT_PARSE_FAILED",
        job_id=job.id,
        run_id=run_id,
        after={"error_code": error_code},
        outcome=AuditOutcome.FAILED,
    )
    session.commit()


def execute_parse_job(
    session: Session,
    *,
    job: Job,
    run_id: uuid.UUID,
    grobid: GrobidProvider | None = None,
    storage_backend: ObjectStorage | None = None,
) -> Document:
    if job.task_type != JobTaskType.DOCUMENT_PARSE or job.resource_type != "document":
        raise DocumentParseError(
            "DOCUMENT_PARSE_JOB_INVALID",
            "Document parse Job is invalid.",
            retryable=False,
        )
    document = session.exec(
        select(Document).where(
            Document.id == job.resource_id,
            Document.project_id == job.project_id,
        )
    ).first()
    if document is None:
        raise DocumentParseError(
            "DOCUMENT_NOT_FOUND", "Document is not available.", retryable=False
        )
    artifact = session.get(Artifact, document.artifact_id)
    if artifact is None or artifact.project_id != document.project_id:
        raise DocumentParseError(
            "FILE_NOT_AVAILABLE", "Document Artifact is not available.", retryable=False
        )
    parameters = _job_parameters(session, job)
    job_service.set_run_context(
        session,
        job_id=job.id,
        run_id=run_id,
        input_hash=artifact.sha256,
        parameters=parameters,
        implementation_metadata={
            "adapter": "RECA_GROBID_HTTPX",
            "converter": "RECA_TEI_CONVERTER@1.0",
            "fallback": "pypdf",
        },
    )
    document.parse_status = JobStatus.RUNNING
    document.updated_at = get_datetime_utc()
    session.add(document)
    session.commit()
    with tempfile.TemporaryDirectory(prefix="reca-document-parse-") as directory:
        pdf_path = Path(directory) / "document.pdf"
        try:
            artifact_service.download_available_artifact_to_path(
                session,
                artifact_id=artifact.id,
                project_id=document.project_id,
                path=pdf_path,
                storage_backend=storage_backend,
            )
        except StorageError as storage_error:
            _mark_parse_failed(
                session,
                job=job,
                document_id=document.id,
                run_id=run_id,
                error_code="ARTIFACT_STORAGE_FAILED",
            )
            raise DocumentParseError(
                "ARTIFACT_STORAGE_FAILED",
                "Document Artifact storage failed.",
                retryable=True,
            ) from storage_error
        try:
            grobid_result = (grobid or GrobidAdapter()).parse(
                pdf_path,
                extract_coordinates=parameters["extract_coordinates"],
            )
            try:
                tei_artifact = artifact_service.create_generated_bytes_artifact(
                    session,
                    project_id=document.project_id,
                    content=grobid_result.tei,
                    filename=f"document-{document.id}-run-{run_id}.tei.xml",
                    mime_type="application/tei+xml",
                    artifact_type=ArtifactType.OTHER,
                    source_artifact_id=artifact.id,
                    metadata={
                        "processing_run_id": str(run_id),
                        "source_artifact_id": str(artifact.id),
                        "grobid_version": grobid_result.version,
                        "grobid_revision": grobid_result.revision,
                        "grobid_image": "lfoppiano/grobid:0.8.2",
                        "grobid_image_digest": "sha256:cab12863cab26c818479dbcb6a4f09922ed6caeedfbbf59ef957f52d7195a85d",
                        "tei_is_formal_evidence": False,
                    },
                    created_by=job.requested_by_user_id,
                    storage_backend=storage_backend,
                )
                run = session.get(ProcessingRun, run_id)
                assert run is not None
                run_metadata = dict(run.implementation_metadata or {})
                run_metadata["tei_artifact_id"] = str(tei_artifact.id)
                run.implementation_metadata = run_metadata
                session.add(run)
                session.commit()
            except StorageError as storage_error:
                _mark_parse_failed(
                    session,
                    job=job,
                    document_id=document.id,
                    run_id=run_id,
                    error_code="ARTIFACT_STORAGE_FAILED",
                )
                raise DocumentParseError(
                    "ARTIFACT_STORAGE_FAILED",
                    "TEI Artifact storage failed.",
                    retryable=True,
                ) from storage_error
            parsed = convert_tei(grobid_result.tei)
            _persist_parsed_document(
                session,
                document=document,
                parsed=parsed,
                parser_type=DocumentParserType.GROBID,
                parser_version=grobid_result.version or "0.8.2",
                confidence=DocumentParseConfidence.HIGH,
            )
            _system_audit(
                session,
                document=document,
                action="DOCUMENT_PARSED",
                job_id=job.id,
                run_id=run_id,
                after={
                    "parser_type": "GROBID",
                    "tei_artifact_id": str(tei_artifact.id),
                    "page_count": document.page_count,
                },
            )
            session.commit()
            return document
        except DocumentParseError as primary_error:
            code = str(getattr(primary_error, "code", "ARTIFACT_STORAGE_FAILED"))
            retryable = bool(getattr(primary_error, "retryable", True))
            if code == "ARTIFACT_STORAGE_FAILED":
                raise
            if parameters["allow_fallback"] and pdf_path.exists():
                try:
                    parsed = parse_with_pypdf(pdf_path)
                    _persist_parsed_document(
                        session,
                        document=document,
                        parsed=parsed,
                        parser_type=DocumentParserType.PYPDF,
                        parser_version="6.14.2",
                        confidence=DocumentParseConfidence.LOW,
                    )
                    run = session.get(ProcessingRun, run_id)
                    assert run is not None
                    metadata = dict(run.implementation_metadata or {})
                    metadata["degradation_record"] = {
                        "requested_capability": "SCHOLARLY_PDF_STRUCTURED_PARSE",
                        "primary_provider": "GROBID",
                        "fallback_provider": "PYPDF",
                        "reason_code": code,
                        "impact": "Page text only; sections and coordinates unavailable.",
                        "result_status": "DEGRADED",
                        "user_visible_message": "Structured parsing was unavailable; page text was extracted with reduced confidence.",
                    }
                    run.implementation_metadata = metadata
                    session.add(run)
                    _system_audit(
                        session,
                        document=document,
                        action="DOCUMENT_PARSED_DEGRADED",
                        job_id=job.id,
                        run_id=run_id,
                        after={"parser_type": "PYPDF", "reason_code": code},
                    )
                    session.commit()
                    return document
                except DocumentParseError as fallback_error:
                    _mark_parse_failed(
                        session,
                        job=job,
                        document_id=document.id,
                        run_id=run_id,
                        error_code=fallback_error.code,
                    )
                    raise
            _mark_parse_failed(
                session,
                job=job,
                document_id=document.id,
                run_id=run_id,
                error_code=code,
            )
            raise DocumentParseError(
                code, "Document parsing failed.", retryable=retryable
            )


def list_pages(
    session: Session, *, actor: User, document_id: uuid.UUID
) -> list[dict[str, Any]]:
    document = session.get(Document, document_id)
    if document is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    project_service.authorize_project(
        session, project_id=document.project_id, actor=actor, action="project.read"
    )
    pages = session.exec(
        select(DocumentPage)
        .where(DocumentPage.document_id == document.id)
        .order_by(col(DocumentPage.page_number))
    ).all()
    return [cast(dict[str, Any], jsonable_encoder(page)) for page in pages]


def get_page(
    session: Session, *, actor: User, document_id: uuid.UUID, page_number: int
) -> dict[str, Any]:
    page = next(
        (
            item
            for item in list_pages(session, actor=actor, document_id=document_id)
            if item["page_number"] == page_number
        ),
        None,
    )
    if page is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    return page
