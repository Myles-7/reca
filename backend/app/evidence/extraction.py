from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol, cast

from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.adapters.model_provider import (
    ModelProviderError,
    OpenAICompatibleJsonProvider,
)
from app.adapters.storage import ObjectStorage, StorageError
from app.agents import service as model_service
from app.agents.prompts import get_prompt_contract
from app.api.errors import ContractError
from app.artifacts import service as artifact_service
from app.core.config import settings
from app.evidence.locator import (
    EvidenceLocatorError,
    evidence_type_for_field,
    locate_candidate,
)
from app.evidence.schemas import (
    DocumentContextPage,
    LiteratureExtractionCandidateOutput,
    LiteratureExtractionInput,
)
from app.jobs import service as job_service
from app.jobs.dispatcher import dispatcher as default_dispatcher
from app.models import (
    Artifact,
    ArtifactRelation,
    ArtifactRelationType,
    ArtifactType,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    ConfidenceLevel,
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentParserType,
    EvidenceSpan,
    FieldConfirmationStatus,
    FieldEvidenceStatus,
    Job,
    JobStatus,
    JobTaskType,
    LiteratureExtraction,
    LiteratureExtractionField,
    LiteratureExtractionStatus,
    LiteratureRecord,
    ModelDataAccessLevel,
    ModelInvocation,
    ModelInvocationStatus,
    ProcessingRun,
    User,
    UserDeclaredReadScope,
    get_datetime_utc,
)
from app.projects import service as project_service

PROMPT_ID = "literature-extraction"
PROMPT_VERSION = "1.0.0"
TASK_TYPE = "LITERATURE_FIELD_EXTRACTION"
INPUT_SCHEMA = "LiteratureExtractionInput"
OUTPUT_SCHEMA = "LiteratureExtractionCandidateOutput"
MAX_CONTEXT_PAGES = 40
MAX_PAGE_CHARS = 20_000
MAX_CONTEXT_CHARS = 60_000
_PATH_TEMPLATE = "/api/v1/documents/{document_id}/literature-extractions"


class LiteratureExtractionError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class ExtractionProviderIdentity:
    provider_id: str
    provider_name: str
    model_name: str
    mode: model_service.ModelExecutionMode
    fixture_id: str | None = None
    recording_id: str | None = None
    recording_version: str | None = None
    recording_hash: str | None = None
    recording_license_status: str | None = None
    recording_redaction_status: str | None = None


class ExtractionProvider(Protocol):
    identity: ExtractionProviderIdentity

    def extract(self, payload: LiteratureExtractionInput) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ExtractionExecutionResult:
    extraction: LiteratureExtraction
    output_artifact: Artifact | None


@dataclass
class OpenAICompatibleExtractionProvider:
    identity: ExtractionProviderIdentity
    client: OpenAICompatibleJsonProvider

    def extract(self, payload: LiteratureExtractionInput) -> dict[str, Any]:
        try:
            return self.client.generate(
                prompt_id=PROMPT_ID, prompt_version=PROMPT_VERSION, payload=payload
            )
        except ModelProviderError as exc:
            raise LiteratureExtractionError(
                exc.code, str(exc), retryable=exc.retryable
            ) from exc


_TRANSITIONS = {
    LiteratureExtractionStatus.DRAFT: frozenset(
        {LiteratureExtractionStatus.EXTRACTING, LiteratureExtractionStatus.FAILED}
    ),
    LiteratureExtractionStatus.EXTRACTING: frozenset(
        {LiteratureExtractionStatus.NEEDS_REVIEW, LiteratureExtractionStatus.FAILED}
    ),
    LiteratureExtractionStatus.FAILED: frozenset(
        {LiteratureExtractionStatus.EXTRACTING}
    ),
    LiteratureExtractionStatus.NEEDS_REVIEW: frozenset(
        {
            LiteratureExtractionStatus.CONFIRMED,
            LiteratureExtractionStatus.SUPERSEDED,
            LiteratureExtractionStatus.INVALIDATED,
        }
    ),
    LiteratureExtractionStatus.CONFIRMED: frozenset(
        {LiteratureExtractionStatus.SUPERSEDED, LiteratureExtractionStatus.INVALIDATED}
    ),
    LiteratureExtractionStatus.SUPERSEDED: frozenset(),
    LiteratureExtractionStatus.INVALIDATED: frozenset(),
}


def transition_extraction(
    extraction: LiteratureExtraction, target: LiteratureExtractionStatus
) -> None:
    if target not in _TRANSITIONS[extraction.status]:
        raise LiteratureExtractionError(
            "INVALID_STATE_TRANSITION",
            f"LiteratureExtraction cannot transition from {extraction.status} to {target}.",
        )
    extraction.status = target
    extraction.updated_at = get_datetime_utc()


def _source_resolver(
    session: Session, source_id: uuid.UUID
) -> model_service.SourceReference | None:
    document = session.get(Document, source_id)
    if document is not None:
        return model_service.SourceReference(
            source_id=document.id,
            project_id=document.project_id,
            source_type="Document",
        )
    literature = session.get(LiteratureRecord, source_id)
    if literature is not None:
        return model_service.SourceReference(
            source_id=literature.id,
            project_id=literature.project_id,
            source_type="LiteratureRecord",
        )
    return None


def _document(session: Session, *, document_id: uuid.UUID) -> Document:
    document = session.get(Document, document_id)
    if document is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    return document


def _bound_literature(session: Session, *, document: Document) -> LiteratureRecord:
    literature = session.exec(
        select(LiteratureRecord).where(
            LiteratureRecord.document_id == document.id,
            LiteratureRecord.project_id == document.project_id,
            col(LiteratureRecord.deleted_at).is_(None),
        )
    ).first()
    if literature is None:
        raise ContractError(
            status_code=409,
            code="LITERATURE_DOCUMENT_BINDING_REQUIRED",
            message="Document must be bound to a LiteratureRecord before extraction.",
        )
    return literature


def _document_and_literature(
    session: Session, *, document_id: uuid.UUID
) -> tuple[Document, LiteratureRecord]:
    document = _document(session, document_id=document_id)
    return document, _bound_literature(session, document=document)


def build_extraction_input(
    session: Session,
    *,
    extraction: LiteratureExtraction,
    document: Document,
    literature: LiteratureRecord,
) -> LiteratureExtractionInput:
    if (
        extraction.project_id != document.project_id
        or literature.project_id != document.project_id
        or literature.document_id != document.id
        or extraction.document_id != document.id
        or extraction.literature_record_id != literature.id
    ):
        raise LiteratureExtractionError(
            "EXTRACTION_SOURCE_MISMATCH",
            "Extraction sources do not share project scope.",
        )
    pages = session.exec(
        select(DocumentPage)
        .where(
            DocumentPage.document_id == document.id,
            DocumentPage.project_id == document.project_id,
            col(DocumentPage.text_content).is_not(None),
        )
        .order_by(col(DocumentPage.page_number))
    ).all()
    chunks = session.exec(
        select(DocumentChunk)
        .where(
            DocumentChunk.document_id == document.id,
            DocumentChunk.project_id == document.project_id,
        )
        .order_by(col(DocumentChunk.chunk_index))
    ).all()
    if not pages:
        raise LiteratureExtractionError(
            "DOCUMENT_PAGE_TEXT_MISSING",
            "Document has no parsed page text for extraction.",
        )
    context_pages: list[DocumentContextPage] = []
    limitations: list[str] = []
    consumed = 0
    for page in pages:
        if len(context_pages) >= MAX_CONTEXT_PAGES or consumed >= MAX_CONTEXT_CHARS:
            limitations.append(
                "Model context was bounded before the final document page."
            )
            break
        text = (page.text_content or "").strip()
        if not text:
            continue
        allowance = min(MAX_PAGE_CHARS, MAX_CONTEXT_CHARS - consumed)
        page_text = text[:allowance]
        if len(page_text) < len(text):
            limitations.append(
                f"Page {page.page_number} text was truncated for minimum-necessary model context."
            )
        page_chunks = [
            chunk
            for chunk in chunks
            if chunk.page_start <= page.page_number <= chunk.page_end
        ]
        section_paths = []
        if document.parser_type != DocumentParserType.PYPDF:
            section_paths = [
                chunk.section_path
                for chunk in page_chunks
                if chunk.section_path is not None
            ]
        metadata = page.parser_metadata or {}
        coordinates = metadata.get("coordinates", [])
        context_pages.append(
            DocumentContextPage(
                page_number=page.page_number,
                text=page_text,
                chunk_ids=[chunk.id for chunk in page_chunks],
                section_paths=section_paths,
                coordinates_available=(
                    document.parser_type != DocumentParserType.PYPDF
                    and isinstance(coordinates, list)
                    and bool(coordinates)
                ),
            )
        )
        consumed += len(page_text)
    if document.parser_type == DocumentParserType.PYPDF:
        limitations.append(
            "pypdf context is LOW confidence and has no trusted sections or coordinates."
        )
    return LiteratureExtractionInput(
        extraction_id=extraction.id,
        project_id=document.project_id,
        literature_record_id=literature.id,
        document_id=document.id,
        parser_type=(document.parser_type or DocumentParserType.NONE).value,
        parser_version=document.parser_version,
        parse_confidence=(
            document.parse_confidence.value if document.parse_confidence else "UNKNOWN"
        ),
        pages=context_pages,
        context_limitations=list(dict.fromkeys(limitations)),
    )


def _invocation_command(
    *,
    actor: User,
    extraction_input: LiteratureExtractionInput,
    provider: ExtractionProviderIdentity,
    retry_of_invocation_id: uuid.UUID | None = None,
    attempt_number: int = 1,
) -> model_service.InvocationCreate:
    prompt = get_prompt_contract(PROMPT_ID, PROMPT_VERSION)
    return model_service.InvocationCreate(
        project_id=extraction_input.project_id,
        authorization_actor=actor,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        task_type=TASK_TYPE,
        prompt_id=prompt.prompt_id,
        prompt_version=prompt.prompt_version,
        prompt_content_hash=prompt.content_hash,
        input_schema_name=prompt.input_schema.name,
        input_schema_version=prompt.input_schema.version,
        output_schema_name=prompt.output_schema.name,
        output_schema_version=prompt.output_schema.version,
        requested_data_access_level=ModelDataAccessLevel.REDACTED_CONTENT,
        max_allowed_data_access_level=ModelDataAccessLevel.REDACTED_CONTENT,
        effective_data_access_level=ModelDataAccessLevel.REDACTED_CONTENT,
        source_ids=(
            extraction_input.document_id,
            extraction_input.literature_record_id,
        ),
        sanitized_input=extraction_input.model_dump(mode="json"),
        mode=provider.mode,
        provider=provider.provider_name,
        model=provider.model_name,
        fixture_id=provider.fixture_id,
        recording_id=provider.recording_id,
        recording_version=provider.recording_version,
        recording_hash=provider.recording_hash,
        recording_license_status=provider.recording_license_status,
        recording_redaction_status=provider.recording_redaction_status,
        retry_of_invocation_id=retry_of_invocation_id,
        execution_metadata={
            "extraction_id": str(extraction_input.extraction_id),
            "document_id": str(extraction_input.document_id),
            "literature_record_id": str(extraction_input.literature_record_id),
            "provider_id": provider.provider_id,
            "attempt_number": attempt_number,
            "context_page_count": len(extraction_input.pages),
            "context_limitations": extraction_input.context_limitations,
        },
    )


def _audit(
    session: Session,
    *,
    extraction: LiteratureExtraction,
    action: str,
    actor_type: AuditActorType,
    actor_id: str | None,
    job_id: uuid.UUID | None,
    invocation_id: uuid.UUID | None,
    processing_run_id: uuid.UUID | None = None,
    after: dict[str, Any] | None = None,
    outcome: AuditOutcome = AuditOutcome.SUCCEEDED,
) -> None:
    snapshot = dict(after or {})
    if processing_run_id is not None:
        snapshot["processing_run_id"] = str(processing_run_id)
    session.add(
        AuditLog(
            project_id=extraction.project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            object_type="literature_extraction",
            object_id=extraction.id,
            after_snapshot=jsonable_encoder(snapshot) if snapshot else None,
            job_id=job_id,
            model_invocation_id=invocation_id,
            outcome=outcome,
        )
    )


def request_extraction_job(
    session: Session,
    *,
    actor: User,
    document_id: uuid.UUID,
    idempotency_key: str,
    provider: ExtractionProviderIdentity,
    literature_record_id: uuid.UUID | None = None,
    requested_field_codes: tuple[str, ...] | None = None,
    dispatcher: job_service.JobDispatcher = default_dispatcher,
) -> project_service.OperationResult:
    document = _document(session, document_id=document_id)
    project_service.authorize_project(
        session, project_id=document.project_id, actor=actor, action="project.update"
    )
    literature = _bound_literature(session, document=document)
    if literature_record_id is not None and literature.id != literature_record_id:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    if document.parse_status != JobStatus.COMPLETED:
        raise ContractError(
            status_code=409,
            code="DOCUMENT_NOT_PARSED",
            message="Document parsing must complete before literature extraction.",
        )
    digest = project_service.request_hash(
        {
            "document_id": document.id,
            "literature_record_id": literature.id,
            "provider_id": provider.provider_id,
            "prompt_version": PROMPT_VERSION,
            "field_codes": list(requested_field_codes or ()),
        }
    )
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=document.project_id,
        method="POST",
        path_template=_PATH_TEMPLATE,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    active = session.exec(
        select(LiteratureExtraction).where(
            LiteratureExtraction.project_id == document.project_id,
            LiteratureExtraction.document_id == document.id,
            col(LiteratureExtraction.status).in_(
                [
                    LiteratureExtractionStatus.DRAFT,
                    LiteratureExtractionStatus.EXTRACTING,
                ]
            ),
        )
    ).first()
    if active is not None:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Literature extraction is already active for this Document.",
        )
    latest_version = session.exec(
        select(func.max(LiteratureExtraction.extraction_version)).where(
            LiteratureExtraction.literature_record_id == literature.id
        )
    ).one()
    extraction = LiteratureExtraction(
        project_id=document.project_id,
        literature_record_id=literature.id,
        document_id=document.id,
        extraction_version=(latest_version or 0) + 1,
        schema_version="1.0",
        status=LiteratureExtractionStatus.DRAFT,
    )
    session.add(extraction)
    session.flush()
    extraction_input = build_extraction_input(
        session,
        extraction=extraction,
        document=document,
        literature=literature,
    )
    invocation = model_service.create_model_invocation(
        session,
        command=_invocation_command(
            actor=actor, extraction_input=extraction_input, provider=provider
        ),
        source_resolver=_source_resolver,
        commit=False,
    )
    extraction.source_model_invocation_id = invocation.id
    session.add(extraction)
    job = job_service.create_job(
        session,
        project_id=document.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.LITERATURE_EXTRACT,
            resource_type="literature_extraction",
            resource_id=extraction.id,
            idempotency_key=idempotency_key,
            requested_by_user_id=actor.id,
            max_retries=2,
            retryable=True,
        ),
    )
    job.total_steps = 4
    job.current_step = "QUEUED"
    session.add(job)
    _audit(
        session,
        extraction=extraction,
        action="LITERATURE_EXTRACTION_REQUESTED",
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        job_id=job.id,
        invocation_id=invocation.id,
        after={
            "status": extraction.status,
            "document_id": str(document.id),
            "literature_record_id": str(literature.id),
            "provider_id": provider.provider_id,
            "requested_field_codes": list(requested_field_codes or ()),
        },
    )
    initial = project_service.OperationResult(
        data=job_service.job_data(session, job), status_code=201
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=document.project_id,
        method="POST",
        path_template=_PATH_TEMPLATE,
        key=idempotency_key,
        payload_hash=digest,
        result=initial,
    )
    project_service._commit(session)
    dispatched = job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)
    if dispatched.status == JobStatus.DISPATCH_FAILED:
        model_service.fail_model_invocation(
            session,
            invocation_id=invocation.id,
            error_code="JOB_DISPATCH_FAILED",
            degradation=model_service.DegradationRecord(
                requested_capability=TASK_TYPE,
                primary_provider=invocation.provider,
                fallback_provider=None,
                reason_code="JOB_DISPATCH_FAILED",
                impact="No extraction worker accepted the request.",
                result_status="FAILED",
                user_visible_message="Literature extraction could not be queued.",
            ),
        )
        failed_extraction = session.get(LiteratureExtraction, extraction.id)
        assert failed_extraction is not None
        transition_extraction(failed_extraction, LiteratureExtractionStatus.FAILED)
        session.add(failed_extraction)
        _audit(
            session,
            extraction=failed_extraction,
            action="LITERATURE_EXTRACTION_FAILED",
            actor_type=AuditActorType.SYSTEM,
            actor_id="job-dispatcher",
            job_id=job.id,
            invocation_id=invocation.id,
            after={"error_code": "JOB_DISPATCH_FAILED"},
            outcome=AuditOutcome.FAILED,
        )
        project_service._commit(session)
    result = project_service.OperationResult(
        data=job_service.job_data(session, dispatched), status_code=201
    )
    project_service._update_idempotency_result(
        session,
        actor_id=actor.id,
        project_id=document.project_id,
        method="POST",
        path_template=_PATH_TEMPLATE,
        key=idempotency_key,
        result=result,
    )
    project_service._commit(session)
    return result


def _provider_identity_from_invocation(
    invocation: ModelInvocation,
) -> ExtractionProviderIdentity:
    metadata = invocation.implementation_metadata or {}
    execution = metadata.get("execution", {})
    try:
        mode = model_service.ModelExecutionMode(str(metadata["mode"]))
        provider_id = str(execution["provider_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LiteratureExtractionError(
            "MODEL_INPUT_INVALID", "Model execution provenance is invalid."
        ) from exc
    return ExtractionProviderIdentity(
        provider_id=provider_id,
        provider_name=invocation.provider or "unconfigured",
        model_name=invocation.model or "unconfigured",
        mode=mode,
        fixture_id=cast(str | None, metadata.get("fixture_id")),
        recording_id=cast(str | None, metadata.get("recording_id")),
        recording_version=cast(str | None, metadata.get("recording_version")),
        recording_hash=cast(str | None, metadata.get("recording_hash")),
        recording_license_status=cast(
            str | None, metadata.get("recording_license_status")
        ),
        recording_redaction_status=cast(
            str | None, metadata.get("recording_redaction_status")
        ),
    )


def configured_extraction_provider(
    identity: ExtractionProviderIdentity,
) -> ExtractionProvider:
    if settings.model_status != "CONFIGURED":
        raise LiteratureExtractionError(
            "MODEL_PROVIDER_UNCONFIGURED",
            "No production LiteratureExtraction provider is configured.",
            retryable=False,
        )
    assert settings.MODEL_BASE_URL is not None
    assert settings.MODEL_API_KEY is not None
    assert settings.MODEL_NAME is not None
    expected = ExtractionProviderIdentity(
        provider_id="openai-compatible",
        provider_name="openai-compatible",
        model_name=settings.MODEL_NAME,
        mode=model_service.ModelExecutionMode.LIVE,
    )
    if identity != expected:
        raise LiteratureExtractionError(
            "MODEL_PROVIDER_MISMATCH",
            "Configured provider does not match invocation provenance.",
            retryable=False,
        )
    return OpenAICompatibleExtractionProvider(
        identity=identity,
        client=OpenAICompatibleJsonProvider(
            base_url=str(settings.MODEL_BASE_URL),
            api_key=settings.MODEL_API_KEY.get_secret_value(),
            model_name=settings.MODEL_NAME,
            timeout_seconds=settings.REQUEST_TIMEOUT_SECONDS,
        ),
    )


def _retry_invocation(
    session: Session,
    *,
    job: Job,
    extraction: LiteratureExtraction,
    previous: ModelInvocation,
    extraction_input: LiteratureExtractionInput,
    attempt_number: int,
) -> ModelInvocation:
    if job.requested_by_user_id is None:
        raise LiteratureExtractionError(
            "MODEL_AUTHORIZATION_ACTOR_MISSING",
            "Retry cannot recreate ModelInvocation without its requesting user.",
        )
    actor = session.get(User, job.requested_by_user_id)
    if actor is None:
        raise LiteratureExtractionError(
            "MODEL_AUTHORIZATION_ACTOR_MISSING",
            "Retry requesting user is unavailable.",
        )
    invocation = model_service.create_model_invocation(
        session,
        command=_invocation_command(
            actor=actor,
            extraction_input=extraction_input,
            provider=_provider_identity_from_invocation(previous),
            retry_of_invocation_id=previous.id,
            attempt_number=attempt_number,
        ),
        source_resolver=_source_resolver,
        commit=False,
    )
    extraction.source_model_invocation_id = invocation.id
    session.add(extraction)
    project_service._commit(session)
    return invocation


def _mark_failed(
    session: Session,
    *,
    extraction_id: uuid.UUID,
    invocation_id: uuid.UUID,
    job: Job,
    run_id: uuid.UUID,
    code: str,
    retryable: bool,
) -> None:
    session.rollback()
    invocation = session.get(ModelInvocation, invocation_id)
    if invocation is not None and invocation.status in {
        ModelInvocationStatus.PENDING,
        ModelInvocationStatus.RUNNING,
    }:
        model_service.fail_model_invocation(
            session,
            invocation_id=invocation.id,
            error_code=code,
            degradation=model_service.DegradationRecord(
                requested_capability=TASK_TYPE,
                primary_provider=invocation.provider,
                fallback_provider=None,
                reason_code=code,
                impact="Literature fields require review and no unvalidated EvidenceSpan was created.",
                result_status="UNAVAILABLE",
                user_visible_message="Literature extraction failed without creating unvalidated evidence.",
            ),
        )
    extraction = session.get(LiteratureExtraction, extraction_id)
    if extraction is None:
        return
    if extraction.status != LiteratureExtractionStatus.FAILED:
        transition_extraction(extraction, LiteratureExtractionStatus.FAILED)
    session.add(extraction)
    _audit(
        session,
        extraction=extraction,
        action="LITERATURE_EXTRACTION_FAILED",
        actor_type=AuditActorType.WORKER,
        actor_id="literature-extraction-worker",
        job_id=job.id,
        invocation_id=invocation_id,
        processing_run_id=run_id,
        after={"error_code": code, "retryable": retryable},
        outcome=AuditOutcome.FAILED,
    )
    project_service._commit(session)


def _context(
    page_text: str, char_start: int | None, char_end: int | None
) -> tuple[str | None, str | None]:
    if char_start is None or char_end is None:
        return None, None
    return page_text[max(0, char_start - 160) : char_start] or None, page_text[
        char_end : char_end + 160
    ] or None


def _persist_output(
    session: Session,
    *,
    extraction: LiteratureExtraction,
    document: Document,
    invocation: ModelInvocation,
    run_id: uuid.UUID,
    output: LiteratureExtractionCandidateOutput,
) -> tuple[int, int]:
    span_count = 0
    rejected_count = 0
    confidence_levels: list[ConfidenceLevel] = []
    for field_output in output.fields:
        evidence_span_id = None
        evidence_status = FieldEvidenceStatus.NO_LOCATED_EVIDENCE
        evidence_limitations: list[str] = []
        confidence_level = (
            ConfidenceLevel.HIGH
            if field_output.confidence >= 0.8
            else ConfidenceLevel.MEDIUM
            if field_output.confidence >= 0.5
            else ConfidenceLevel.LOW
        )
        if document.parser_type == DocumentParserType.PYPDF:
            confidence_level = ConfidenceLevel.LOW
        if field_output.evidence_candidates:
            candidate = field_output.evidence_candidates[0]
            try:
                located = locate_candidate(
                    session, candidate, confidence_score=field_output.confidence
                )
                before, after = _context(
                    located.source.page_text, located.char_start, located.char_end
                )
                span = EvidenceSpan(
                    project_id=extraction.project_id,
                    document_id=extraction.document_id,
                    document_page_id=located.source.document_page_id,
                    chunk_id=located.source.chunk_id,
                    page_number=located.source.page_number,
                    section_path=(
                        located.source.chunk_section_path
                        if located.source.parser_type != DocumentParserType.PYPDF
                        else None
                    ),
                    source_text=located.source_text,
                    context_before=before,
                    context_after=after,
                    bounding_boxes=located.bounding_boxes,
                    char_start=located.char_start,
                    char_end=located.char_end,
                    evidence_type=evidence_type_for_field(field_output.field_code),
                    confidence_level=located.confidence_level,
                    confidence_score=field_output.confidence,
                    parser_type=located.source.parser_type,
                    parser_version=located.source.parser_version,
                    model_invocation_id=invocation.id,
                    source_text_hash=located.source_text_hash,
                    location_verification_status=located.location_status,
                    parser_coverage=located.source.parser_coverage,
                    user_declared_read_scope=UserDeclaredReadScope.UNKNOWN,
                )
                session.add(span)
                session.flush()
                evidence_span_id = span.id
                evidence_status = located.evidence_status
                confidence_level = located.confidence_level
                evidence_limitations.extend(located.limitations)
                span_count += 1
            except EvidenceLocatorError as exc:
                evidence_limitations.append(f"{exc.code}: {exc}")
                rejected_count += 1
        else:
            evidence_limitations.append(
                "NO_LOCATED_EVIDENCE: model returned no source candidate."
            )
        evidence_limitations.extend(field_output.notes)
        field = LiteratureExtractionField(
            project_id=extraction.project_id,
            extraction_id=extraction.id,
            field_code=field_output.field_code,
            model_value_text=field_output.value.text,
            model_value_json=field_output.value.structured,
            value_text=field_output.value.text,
            value_json=field_output.value.structured,
            confidence_score=field_output.confidence,
            confidence_level=confidence_level,
            evidence_span_id=evidence_span_id,
            confirmation_status=FieldConfirmationStatus.UNREVIEWED,
            evidence_status=evidence_status,
            evidence_limitations=(
                " ".join(dict.fromkeys(evidence_limitations))
                if evidence_limitations
                else None
            ),
        )
        session.add(field)
        confidence_levels.append(confidence_level)
    extraction.overall_confidence = (
        ConfidenceLevel.LOW
        if ConfidenceLevel.LOW in confidence_levels
        else ConfidenceLevel.MEDIUM
        if ConfidenceLevel.MEDIUM in confidence_levels
        else ConfidenceLevel.HIGH
    )
    extraction.document_level_limitations = list(
        dict.fromkeys(
            [
                *output.document_level_limitations,
                *(
                    ["pypdf extraction is LOW confidence without trusted coordinates."]
                    if document.parser_type == DocumentParserType.PYPDF
                    else []
                ),
            ]
        )
    )
    extraction.processing_run_id = run_id
    extraction.source_model_invocation_id = invocation.id
    transition_extraction(extraction, LiteratureExtractionStatus.NEEDS_REVIEW)
    session.add(extraction)
    return span_count, rejected_count


def execute_extraction_job(
    session: Session,
    *,
    job: Job,
    run_id: uuid.UUID,
    provider: ExtractionProvider | None = None,
    storage_backend: ObjectStorage | None = None,
) -> ExtractionExecutionResult:
    if (
        job.task_type != JobTaskType.LITERATURE_EXTRACT
        or job.resource_type != "literature_extraction"
    ):
        raise LiteratureExtractionError(
            "JOB_HANDLER_MISMATCH", "Job is not a LiteratureExtraction job."
        )
    extraction = session.exec(
        select(LiteratureExtraction).where(
            LiteratureExtraction.id == job.resource_id,
            LiteratureExtraction.project_id == job.project_id,
        )
    ).first()
    if extraction is None:
        raise LiteratureExtractionError(
            "LITERATURE_EXTRACTION_NOT_FOUND", "LiteratureExtraction is unavailable."
        )
    previous = (
        session.get(ModelInvocation, extraction.source_model_invocation_id)
        if extraction.source_model_invocation_id is not None
        else None
    )
    if (
        extraction.status == LiteratureExtractionStatus.NEEDS_REVIEW
        and previous is not None
        and previous.status == ModelInvocationStatus.SUCCEEDED
    ):
        return ExtractionExecutionResult(extraction=extraction, output_artifact=None)
    document, literature = _document_and_literature(
        session, document_id=extraction.document_id
    )
    if (
        document.project_id != job.project_id
        or literature.id != extraction.literature_record_id
    ):
        raise LiteratureExtractionError(
            "EXTRACTION_SOURCE_MISMATCH", "Job sources do not match the extraction."
        )
    extraction_input = build_extraction_input(
        session,
        extraction=extraction,
        document=document,
        literature=literature,
    )
    run = session.get(ProcessingRun, run_id)
    if run is None or run.job_id != job.id or run.project_id != job.project_id:
        raise LiteratureExtractionError(
            "PROCESSING_RUN_INVALID",
            "ProcessingRun does not belong to the extraction Job.",
        )
    if previous is None:
        raise LiteratureExtractionError(
            "MODEL_INVOCATION_NOT_FOUND", "Extraction ModelInvocation is unavailable."
        )
    invocation = previous
    if previous.status == ModelInvocationStatus.FAILED:
        invocation = _retry_invocation(
            session,
            job=job,
            extraction=extraction,
            previous=previous,
            extraction_input=extraction_input,
            attempt_number=run.attempt_number,
        )
    if invocation.status != ModelInvocationStatus.PENDING:
        raise LiteratureExtractionError(
            "MODEL_INVOCATION_INVALID_STATE",
            "ModelInvocation is not available for extraction.",
        )
    if (
        model_service.canonical_hash(extraction_input.model_dump(mode="json"))
        != invocation.input_hash
    ):
        _mark_failed(
            session,
            extraction_id=extraction.id,
            invocation_id=invocation.id,
            job=job,
            run_id=run_id,
            code="RESOURCE_VERSION_CONFLICT",
            retryable=False,
        )
        raise LiteratureExtractionError(
            "RESOURCE_VERSION_CONFLICT", "Document context changed before extraction."
        )
    identity = _provider_identity_from_invocation(invocation)
    try:
        selected_provider = provider or configured_extraction_provider(identity)
        if selected_provider.identity != identity:
            raise LiteratureExtractionError(
                "MODEL_PROVIDER_MISMATCH",
                "Injected provider does not match invocation provenance.",
            )
    except LiteratureExtractionError as exc:
        _mark_failed(
            session,
            extraction_id=extraction.id,
            invocation_id=invocation.id,
            job=job,
            run_id=run_id,
            code=exc.code,
            retryable=exc.retryable,
        )
        raise
    job_service.set_run_context(
        session,
        job_id=job.id,
        run_id=run_id,
        input_hash=invocation.input_hash,
        parameters={
            "prompt_version": PROMPT_VERSION,
            "context_page_count": len(extraction_input.pages),
        },
        implementation_metadata={
            "model_invocation_id": str(invocation.id),
            "provider_id": identity.provider_id,
            "provider": identity.provider_name,
            "model": identity.model_name,
            "mode": identity.mode.value,
            "locator": "RECA_EXACT_PAGE_LOCATOR@1.0",
        },
    )
    transition_extraction(extraction, LiteratureExtractionStatus.EXTRACTING)
    session.add(extraction)
    _audit(
        session,
        extraction=extraction,
        action="LITERATURE_EXTRACTION_STARTED",
        actor_type=AuditActorType.WORKER,
        actor_id="literature-extraction-worker",
        job_id=job.id,
        invocation_id=invocation.id,
        processing_run_id=run_id,
        after={"status": extraction.status, "attempt_number": run.attempt_number},
    )
    project_service._commit(session)
    model_service.mark_model_invocation_running(session, invocation_id=invocation.id)
    try:
        raw = selected_provider.extract(extraction_input)
        output = LiteratureExtractionCandidateOutput.model_validate(raw)
    except LiteratureExtractionError as exc:
        _mark_failed(
            session,
            extraction_id=extraction.id,
            invocation_id=invocation.id,
            job=job,
            run_id=run_id,
            code=exc.code,
            retryable=exc.retryable,
        )
        raise
    except (ValidationError, TypeError, ValueError) as exc:
        _mark_failed(
            session,
            extraction_id=extraction.id,
            invocation_id=invocation.id,
            job=job,
            run_id=run_id,
            code="MODEL_OUTPUT_SCHEMA_INVALID",
            retryable=False,
        )
        raise LiteratureExtractionError(
            "MODEL_OUTPUT_SCHEMA_INVALID", "LiteratureExtraction output is invalid."
        ) from exc
    if (
        output.document_id != document.id
        or output.literature_record_id != literature.id
    ):
        _mark_failed(
            session,
            extraction_id=extraction.id,
            invocation_id=invocation.id,
            job=job,
            run_id=run_id,
            code="MODEL_OUTPUT_SOURCE_MISSING",
            retryable=False,
        )
        raise LiteratureExtractionError(
            "MODEL_OUTPUT_SOURCE_MISSING", "Model output source IDs are invalid."
        )
    if (
        identity.mode == model_service.ModelExecutionMode.RECORDED
        and identity.recording_hash != model_service.canonical_hash(raw)
    ):
        _mark_failed(
            session,
            extraction_id=extraction.id,
            invocation_id=invocation.id,
            job=job,
            run_id=run_id,
            code="MODEL_RECORDING_HASH_MISMATCH",
            retryable=False,
        )
        raise LiteratureExtractionError(
            "MODEL_RECORDING_HASH_MISMATCH",
            "Recorded output does not match the reviewed recording hash.",
        )
    try:
        output_artifact = artifact_service.create_generated_json_artifact(
            session,
            project_id=extraction.project_id,
            payload=output.model_dump(mode="json"),
            filename=f"literature-extraction-{invocation.id}.json",
            artifact_type=ArtifactType.MODEL_OUTPUT,
            metadata={
                "schema_name": OUTPUT_SCHEMA,
                "schema_version": "1.0",
                "extraction_id": str(extraction.id),
                "document_id": str(document.id),
                "literature_record_id": str(literature.id),
                "model_invocation_id": str(invocation.id),
                "processing_run_id": str(run_id),
                "provider_id": identity.provider_id,
                "mode": identity.mode.value,
                "evidence_spans_require_locator": True,
            },
            created_by=job.requested_by_user_id,
            storage_backend=storage_backend,
        )
        session.add(
            ArtifactRelation(
                project_id=extraction.project_id,
                source_artifact_id=document.artifact_id,
                target_artifact_id=output_artifact.id,
                relation_type=ArtifactRelationType.DERIVED_FROM,
                relation_metadata={
                    "processing_run_id": str(run_id),
                    "model_invocation_id": str(invocation.id),
                },
            )
        )
        span_count, rejected_count = _persist_output(
            session,
            extraction=extraction,
            document=document,
            invocation=invocation,
            run_id=run_id,
            output=output,
        )
    except StorageError as exc:
        _mark_failed(
            session,
            extraction_id=extraction.id,
            invocation_id=invocation.id,
            job=job,
            run_id=run_id,
            code="MODEL_OUTPUT_PERSISTENCE_FAILED",
            retryable=True,
        )
        raise LiteratureExtractionError(
            "MODEL_OUTPUT_PERSISTENCE_FAILED",
            "Validated extraction output could not be stored.",
            retryable=True,
        ) from exc
    _audit(
        session,
        extraction=extraction,
        action="LITERATURE_EXTRACTION_NEEDS_REVIEW",
        actor_type=AuditActorType.WORKER,
        actor_id="literature-extraction-worker",
        job_id=job.id,
        invocation_id=invocation.id,
        processing_run_id=run_id,
        after={
            "status": extraction.status,
            "field_count": len(output.fields),
            "evidence_span_count": span_count,
            "rejected_candidate_count": rejected_count,
            "artifact_id": str(output_artifact.id),
        },
    )
    model_service.complete_model_invocation(
        session,
        invocation_id=invocation.id,
        sanitized_output=raw,
    )
    session.refresh(extraction)
    return ExtractionExecutionResult(
        extraction=extraction, output_artifact=output_artifact
    )
