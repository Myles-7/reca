from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any

import pytest
from sqlmodel import Session, select

from app.adapters.storage import StorageObjectExists, StorageObjectMissing
from app.agents.service import ModelExecutionMode
from app.evidence import extraction as extraction_service
from app.evidence.extraction import (
    ExtractionProviderIdentity,
    LiteratureExtractionError,
    execute_extraction_job,
    request_extraction_job,
)
from app.jobs import service as job_service
from app.models import (
    Artifact,
    ArtifactStatus,
    ArtifactType,
    AuditLog,
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentParseConfidence,
    DocumentParserType,
    EvidenceSpan,
    FieldEvidenceStatus,
    IdempotencyRecord,
    Job,
    JobStatus,
    LiteratureExtraction,
    LiteratureExtractionField,
    LiteratureExtractionStatus,
    LiteratureFieldCode,
    LiteratureRecord,
    LiteratureSourceType,
    ModelInvocation,
    ModelInvocationStatus,
    ProcessingRun,
    ResearchProject,
    StorageProvider,
    User,
)
from app.projects.schemas import ProjectCreate
from app.projects.service import create_project
from tests.utils.user import create_random_user


class MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_file_once(
        self, *, object_key: str, path: Path, content_sha256: str, size_bytes: int
    ) -> None:
        if object_key in self.objects:
            raise StorageObjectExists(object_key)
        content = path.read_bytes()
        assert hashlib.sha256(content).hexdigest() == content_sha256
        assert len(content) == size_bytes
        self.objects[object_key] = content

    def download_to_path(self, *, object_key: str, path: Path) -> None:
        if object_key not in self.objects:
            raise StorageObjectMissing(object_key)
        path.write_bytes(self.objects[object_key])

    def presign_download(self, *, object_key: str, expires_seconds: int) -> str:
        return f"memory://{object_key}?expires={expires_seconds}"


class FakeDispatcher:
    def __init__(self) -> None:
        self.job_ids: list[uuid.UUID] = []

    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        self.job_ids.append(job_id)


class FailingDispatcher:
    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        raise RuntimeError("dispatcher unavailable")


class FakeProvider:
    def __init__(
        self, identity: ExtractionProviderIdentity, output: dict[str, Any]
    ) -> None:
        self.identity = identity
        self.output = output

    def extract(self, payload: object) -> dict[str, Any]:
        return self.output


class FailingProvider:
    def __init__(self, identity: ExtractionProviderIdentity) -> None:
        self.identity = identity

    def extract(self, payload: object) -> dict[str, Any]:
        raise LiteratureExtractionError(
            "MODEL_PROVIDER_UNAVAILABLE", "provider unavailable", retryable=True
        )


def _identity() -> ExtractionProviderIdentity:
    return ExtractionProviderIdentity(
        provider_id="stage2-fake-provider",
        provider_name="fake",
        model_name="fake-literature-1",
        mode=ModelExecutionMode.MOCK,
        fixture_id="stage2-literature-fixture-v1",
    )


def _graph(
    db: Session,
) -> tuple[
    User, ResearchProject, Document, LiteratureRecord, DocumentPage, DocumentChunk
]:
    actor = create_random_user(db)
    result = create_project(
        db,
        actor=actor,
        payload=ProjectCreate(name="M3 extraction", project_type="RESEARCH"),
        idempotency_key=str(uuid.uuid4()),
    )
    project = db.get(ResearchProject, uuid.UUID(result.data["id"]))
    assert project is not None
    artifact = Artifact(
        project_id=project.id,
        artifact_type=ArtifactType.PDF_DOCUMENT,
        filename="paper.pdf",
        storage_provider=StorageProvider.MINIO,
        storage_key=f"stage2/{uuid.uuid4()}.pdf",
        mime_type="application/pdf",
        size_bytes=1,
        sha256="a" * 64,
        is_original=True,
        is_immutable=True,
        status=ArtifactStatus.AVAILABLE,
        created_by=actor.id,
    )
    db.add(artifact)
    db.flush()
    document = Document(
        project_id=project.id,
        artifact_id=artifact.id,
        parser_type=DocumentParserType.GROBID,
        parser_version="0.8.2",
        parse_status=JobStatus.COMPLETED,
        parse_confidence=DocumentParseConfidence.HIGH,
        page_count=1,
    )
    db.add(document)
    db.flush()
    text = "The study included exactly 312 participants in the final sample."
    literature = LiteratureRecord(
        project_id=project.id,
        document_id=document.id,
        source_type=LiteratureSourceType.USER_UPLOAD,
        title="Stage 2 paper",
        normalized_title="stage 2 paper",
    )
    page = DocumentPage(
        document_id=document.id,
        project_id=project.id,
        page_number=1,
        text_content=text,
    )
    chunk = DocumentChunk(
        project_id=project.id,
        document_id=document.id,
        page_start=1,
        page_end=1,
        section_path=["Methods", "Participants"],
        chunk_index=0,
        content=text,
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
    )
    db.add(literature)
    db.add(page)
    db.add(chunk)
    db.commit()
    return actor, project, document, literature, page, chunk


def _field(field_code: LiteratureFieldCode) -> dict[str, Any]:
    return {
        "field_code": field_code.value,
        "value": {"text": None, "structured": None},
        "evidence_candidates": [],
        "confidence": 0.2,
        "requires_human_review": True,
        "notes": ["No exact source candidate."],
    }


def _output(
    *,
    project: ResearchProject,
    document: Document,
    literature: LiteratureRecord,
    chunk: DocumentChunk,
    source_text: str | None,
) -> dict[str, Any]:
    fields = [_field(code) for code in LiteratureFieldCode]
    sample = next(field for field in fields if field["field_code"] == "SAMPLE_SIZE")
    sample["value"] = {"text": "312", "structured": {"n": 312}}
    sample["confidence"] = 0.95
    if source_text is not None:
        sample["evidence_candidates"] = [
            {
                "candidate_id": str(uuid.uuid4()),
                "project_id": str(project.id),
                "literature_record_id": str(literature.id),
                "document_id": str(document.id),
                "chunk_id": str(chunk.id),
                "page_number": 1,
                "source_text": source_text,
                "source_text_hash": hashlib.sha256(source_text.encode()).hexdigest(),
            }
        ]
    return {
        "literature_record_id": str(literature.id),
        "document_id": str(document.id),
        "fields": fields,
        "document_level_limitations": [],
    }


def _request_and_claim(
    db: Session,
    *,
    actor: User,
    document: Document,
    identity: ExtractionProviderIdentity,
    dispatcher: FakeDispatcher,
) -> tuple[Job, ProcessingRun, LiteratureExtraction]:
    result = request_extraction_job(
        db,
        actor=actor,
        document_id=document.id,
        idempotency_key=str(uuid.uuid4()),
        provider=identity,
        dispatcher=dispatcher,
    )
    job = db.get(Job, uuid.UUID(result.data["id"]))
    assert job is not None
    extraction = db.get(LiteratureExtraction, job.resource_id)
    assert extraction is not None
    claim = job_service.claim_job(
        db,
        job_id=job.id,
        worker_id="stage2-test-worker",
        engine="reca-worker",
        engine_version="test",
    )
    assert claim is not None
    run = db.get(ProcessingRun, claim.run_id)
    assert run is not None
    return job, run, extraction


def test_exact_candidate_creates_span_and_ten_review_fields(db: Session) -> None:
    actor, project, document, literature, _, chunk = _graph(db)
    identity = _identity()
    job, run, extraction = _request_and_claim(
        db,
        actor=actor,
        document=document,
        identity=identity,
        dispatcher=FakeDispatcher(),
    )
    source_text = "exactly 312 participants"
    result = execute_extraction_job(
        db,
        job=job,
        run_id=run.id,
        provider=FakeProvider(
            identity,
            _output(
                project=project,
                document=document,
                literature=literature,
                chunk=chunk,
                source_text=source_text,
            ),
        ),
        storage_backend=MemoryStorage(),
    )
    assert job_service.complete_job(
        db,
        job_id=job.id,
        run_id=run.id,
        worker_id="stage2-test-worker",
        output_object_type="literature_extraction",
        output_object_id=extraction.id,
        log_artifact_id=result.output_artifact.id if result.output_artifact else None,
    )

    db.refresh(extraction)
    db.refresh(job)
    db.refresh(run)
    assert result.extraction.status == LiteratureExtractionStatus.NEEDS_REVIEW
    assert job.status == JobStatus.COMPLETED
    assert run.status == JobStatus.COMPLETED
    assert result.output_artifact is not None and result.output_artifact.is_immutable
    spans = db.exec(
        select(EvidenceSpan).where(EvidenceSpan.project_id == project.id)
    ).all()
    fields = db.exec(
        select(LiteratureExtractionField).where(
            LiteratureExtractionField.extraction_id == extraction.id
        )
    ).all()
    assert len(spans) == 1 and spans[0].source_text == source_text
    assert len(fields) == 10
    sample = next(
        field for field in fields if field.field_code == LiteratureFieldCode.SAMPLE_SIZE
    )
    assert sample.evidence_status == FieldEvidenceStatus.LOCATED
    invocation = db.get(ModelInvocation, extraction.source_model_invocation_id)
    assert (
        invocation is not None and invocation.status == ModelInvocationStatus.SUCCEEDED
    )
    audits = db.exec(select(AuditLog).where(AuditLog.object_id == extraction.id)).all()
    assert any(
        (audit.after_snapshot or {}).get("processing_run_id") == str(run.id)
        for audit in audits
    )


@pytest.mark.parametrize("failure_point", ["invocation", "job", "idempotency"])
def test_request_graph_rolls_back_before_dispatch(
    db: Session, monkeypatch: pytest.MonkeyPatch, failure_point: str
) -> None:
    actor, project, document, _, _, _ = _graph(db)
    key = str(uuid.uuid4())

    if failure_point == "invocation":
        original = extraction_service.model_service.create_model_invocation

        def fail_after_invocation(*args: Any, **kwargs: Any) -> Any:
            original(*args, **kwargs)
            raise RuntimeError("failure after invocation")

        monkeypatch.setattr(
            extraction_service.model_service,
            "create_model_invocation",
            fail_after_invocation,
        )
    elif failure_point == "job":
        original = extraction_service.job_service.create_job

        def fail_after_job(*args: Any, **kwargs: Any) -> Any:
            original(*args, **kwargs)
            raise RuntimeError("failure after job")

        monkeypatch.setattr(
            extraction_service.job_service, "create_job", fail_after_job
        )
    else:
        original = extraction_service.project_service._store_idempotency

        def fail_after_idempotency(*args: Any, **kwargs: Any) -> Any:
            original(*args, **kwargs)
            raise RuntimeError("failure after idempotency")

        monkeypatch.setattr(
            extraction_service.project_service,
            "_store_idempotency",
            fail_after_idempotency,
        )

    with pytest.raises(RuntimeError, match="failure after"):
        request_extraction_job(
            db,
            actor=actor,
            document_id=document.id,
            idempotency_key=key,
            provider=_identity(),
            dispatcher=FakeDispatcher(),
        )
    db.rollback()

    assert not db.exec(
        select(LiteratureExtraction).where(
            LiteratureExtraction.document_id == document.id
        )
    ).all()
    assert not db.exec(
        select(ModelInvocation).where(ModelInvocation.project_id == project.id)
    ).all()
    assert not db.exec(
        select(Job).where(
            Job.project_id == project.id,
            Job.resource_type == "literature_extraction",
        )
    ).all()
    assert not db.exec(
        select(IdempotencyRecord).where(IdempotencyRecord.idempotency_key == key)
    ).all()


def test_dispatch_failure_leaves_terminal_provenance_and_replay(db: Session) -> None:
    actor, _, document, _, _, _ = _graph(db)
    key = str(uuid.uuid4())
    result = request_extraction_job(
        db,
        actor=actor,
        document_id=document.id,
        idempotency_key=key,
        provider=_identity(),
        dispatcher=FailingDispatcher(),
    )
    job = db.get(Job, uuid.UUID(result.data["id"]))
    assert job is not None and job.status == JobStatus.DISPATCH_FAILED
    extraction = db.get(LiteratureExtraction, job.resource_id)
    assert (
        extraction is not None
        and extraction.status == LiteratureExtractionStatus.FAILED
    )
    invocation = db.get(ModelInvocation, extraction.source_model_invocation_id)
    assert invocation is not None and invocation.status == ModelInvocationStatus.FAILED

    replay = request_extraction_job(
        db,
        actor=actor,
        document_id=document.id,
        idempotency_key=key,
        provider=_identity(),
        dispatcher=FakeDispatcher(),
    )
    assert replay.idempotency_replayed is True
    assert replay.data["status"] == JobStatus.DISPATCH_FAILED


def test_fabricated_or_absent_candidates_create_zero_spans(db: Session) -> None:
    actor, project, document, literature, _, chunk = _graph(db)
    identity = _identity()
    job, run, extraction = _request_and_claim(
        db,
        actor=actor,
        document=document,
        identity=identity,
        dispatcher=FakeDispatcher(),
    )
    result = execute_extraction_job(
        db,
        job=job,
        run_id=run.id,
        provider=FakeProvider(
            identity,
            _output(
                project=project,
                document=document,
                literature=literature,
                chunk=chunk,
                source_text="fabricated model quotation",
            ),
        ),
        storage_backend=MemoryStorage(),
    )
    assert job_service.complete_job(
        db,
        job_id=job.id,
        run_id=run.id,
        worker_id="stage2-test-worker",
        output_object_type="literature_extraction",
        output_object_id=extraction.id,
        log_artifact_id=result.output_artifact.id if result.output_artifact else None,
    )

    assert not db.exec(
        select(EvidenceSpan).where(EvidenceSpan.project_id == project.id)
    ).all()
    fields = db.exec(
        select(LiteratureExtractionField).where(
            LiteratureExtractionField.extraction_id == extraction.id
        )
    ).all()
    assert len(fields) == 10
    assert all(
        field.evidence_status == FieldEvidenceStatus.NO_LOCATED_EVIDENCE
        for field in fields
    )
    assert all(field.evidence_limitations for field in fields)


def test_failure_and_retry_reuse_job_with_new_run_and_invocation(db: Session) -> None:
    actor, project, document, literature, _, chunk = _graph(db)
    identity = _identity()
    dispatcher = FakeDispatcher()
    job, first_run, extraction = _request_and_claim(
        db,
        actor=actor,
        document=document,
        identity=identity,
        dispatcher=dispatcher,
    )
    try:
        execute_extraction_job(
            db,
            job=job,
            run_id=first_run.id,
            provider=FailingProvider(identity),
            storage_backend=MemoryStorage(),
        )
    except LiteratureExtractionError as exc:
        assert exc.code == "MODEL_PROVIDER_UNAVAILABLE"
    else:
        raise AssertionError("provider failure must fail the extraction")
    assert job_service.fail_job(
        db,
        job_id=job.id,
        run_id=first_run.id,
        worker_id="stage2-test-worker",
        error_code="MODEL_PROVIDER_UNAVAILABLE",
        error_message="provider unavailable",
        retryable=True,
    )
    first_invocation_id = extraction.source_model_invocation_id
    retry_dispatcher = FakeDispatcher()
    job_service.retry_job(
        db,
        actor=actor,
        job_id=job.id,
        idempotency_key=str(uuid.uuid4()),
        dispatcher=retry_dispatcher,
    )
    claim = job_service.claim_job(
        db,
        job_id=job.id,
        worker_id="stage2-test-worker",
        engine="reca-worker",
        engine_version="test",
    )
    assert claim is not None and claim.run_id != first_run.id
    second_run = db.get(ProcessingRun, claim.run_id)
    assert second_run is not None and second_run.attempt_number == 2
    result = execute_extraction_job(
        db,
        job=job,
        run_id=second_run.id,
        provider=FakeProvider(
            identity,
            _output(
                project=project,
                document=document,
                literature=literature,
                chunk=chunk,
                source_text=None,
            ),
        ),
        storage_backend=MemoryStorage(),
    )
    assert job_service.complete_job(
        db,
        job_id=job.id,
        run_id=second_run.id,
        worker_id="stage2-test-worker",
        output_object_type="literature_extraction",
        output_object_id=extraction.id,
        log_artifact_id=result.output_artifact.id if result.output_artifact else None,
    )
    db.refresh(extraction)
    assert extraction.source_model_invocation_id != first_invocation_id
    first_invocation = db.get(ModelInvocation, first_invocation_id)
    second_invocation = db.get(ModelInvocation, extraction.source_model_invocation_id)
    assert first_invocation is not None
    assert second_invocation is not None
    assert first_invocation.status == ModelInvocationStatus.FAILED
    assert second_invocation.status == ModelInvocationStatus.SUCCEEDED
    runs = db.exec(
        select(ProcessingRun)
        .where(ProcessingRun.job_id == job.id)
        .order_by(ProcessingRun.attempt_number)
    ).all()
    assert [run.attempt_number for run in runs] == [1, 2]
