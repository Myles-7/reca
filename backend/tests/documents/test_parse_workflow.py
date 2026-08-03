from __future__ import annotations

import hashlib
import uuid
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from sqlmodel import Session, select

from app.adapters.documents import DocumentParseError, GrobidResult
from app.adapters.storage import StorageError, StorageObjectExists
from app.api.routes import documents as document_routes
from app.artifacts import service as artifact_service
from app.core.config import settings
from app.documents import service as document_service
from app.jobs import service as job_service
from app.models import (
    Artifact,
    ArtifactRelation,
    ArtifactRelationType,
    ArtifactType,
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentParseConfidence,
    DocumentParserType,
    Job,
    JobStatus,
    ProcessingRun,
    User,
)
from tests.documents.test_parsing import TEI, text_pdf_bytes


class MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_file_once(
        self, *, object_key: str, path: Path, content_sha256: str, size_bytes: int
    ) -> None:
        content = path.read_bytes()
        assert hashlib.sha256(content).hexdigest() == content_sha256
        assert len(content) == size_bytes
        if object_key in self.objects:
            raise StorageObjectExists("exists")
        self.objects[object_key] = content

    def download_to_path(self, *, object_key: str, path: Path) -> None:
        try:
            path.write_bytes(self.objects[object_key])
        except KeyError as exc:
            raise StorageError("missing") from exc

    def presign_download(self, *, object_key: str, expires_seconds: int) -> str:
        return f"https://download.test/{object_key}?expires={expires_seconds}"


class FakeDispatcher:
    def __init__(self) -> None:
        self.job_ids: list[uuid.UUID] = []

    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        self.job_ids.append(job_id)


class RecordedGrobid:
    def __init__(self, result: bytes = TEI) -> None:
        self.result = result
        self.coordinate_requests: list[bool] = []

    def parse(self, pdf_path: Path, *, extract_coordinates: bool) -> GrobidResult:
        assert pdf_path.read_bytes().startswith(b"%PDF")
        self.coordinate_requests.append(extract_coordinates)
        return GrobidResult(tei=self.result, version="0.8.2", revision="recorded")


class UnavailableGrobid:
    def parse(self, pdf_path: Path, *, extract_coordinates: bool) -> GrobidResult:
        raise DocumentParseError("GROBID_UNAVAILABLE", "unavailable", retryable=True)


@pytest.fixture
def memory_storage(monkeypatch: pytest.MonkeyPatch) -> MemoryStorage:
    backend = MemoryStorage()
    monkeypatch.setattr(artifact_service, "storage", backend)
    return backend


def create_project(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/projects",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"name": "Parse workflow", "project_type": "RESEARCH"},
    )
    assert response.status_code == 201, response.text
    return str(response.json()["data"]["id"])


def upload_document(
    client: TestClient,
    headers: dict[str, str],
    project_id: str,
    *,
    content: bytes | None = None,
) -> tuple[uuid.UUID, uuid.UUID]:
    response = client.post(
        f"/api/v1/projects/{project_id}/documents",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        files={
            "file": (
                "paper.pdf",
                content if content is not None else text_pdf_bytes(),
                "application/pdf",
            )
        },
        data={"document_type": "SCHOLARLY_PDF"},
    )
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    return uuid.UUID(data["document"]["id"]), uuid.UUID(data["artifact"]["id"])


def claim(db: Session, job_id: uuid.UUID) -> tuple[Job, ProcessingRun]:
    claimed = job_service.claim_job(
        db,
        job_id=job_id,
        worker_id="document-test-worker",
        engine="reca-worker",
        engine_version="0.1.0",
    )
    assert claimed is not None
    job = db.get(Job, job_id)
    run = db.get(ProcessingRun, claimed.run_id)
    assert job is not None and run is not None
    return job, run


def test_parse_api_is_idempotent_and_preserves_private_parser_choice(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert artifact_service.storage is memory_storage
    dispatcher = FakeDispatcher()
    monkeypatch.setattr(document_routes, "dispatcher", dispatcher)
    project_id = create_project(client, normal_user_token_headers)
    document_id, _ = upload_document(client, normal_user_token_headers, project_id)
    key = str(uuid.uuid4())
    headers = {**normal_user_token_headers, "Idempotency-Key": key}
    payload = {"allow_fallback": False, "extract_coordinates": False}

    first = client.post(
        f"/api/v1/documents/{document_id}/parse", headers=headers, json=payload
    )
    replay = client.post(
        f"/api/v1/documents/{document_id}/parse", headers=headers, json=payload
    )

    assert first.status_code == replay.status_code == 202
    assert replay.json()["meta"]["idempotency_replayed"] is True
    assert first.json()["data"] == replay.json()["data"]
    assert "_document_parse_parameters" not in replay.text
    assert len(dispatcher.job_ids) == 1
    document = db.get(Document, document_id)
    assert document is not None and document.parse_status == JobStatus.QUEUED
    job = db.get(Job, dispatcher.job_ids[0])
    assert job is not None
    assert document_service._job_parameters(db, job) == {
        "allow_fallback": False,
        "extract_coordinates": False,
    }

    conflict = client.post(
        f"/api/v1/documents/{document_id}/parse",
        headers=headers,
        json={"allow_fallback": True, "extract_coordinates": False},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_grobid_parse_creates_immutable_tei_and_stable_pages(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    actor = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).one()
    project_id = create_project(client, normal_user_token_headers)
    document_id, source_artifact_id = upload_document(
        client, normal_user_token_headers, project_id
    )
    dispatcher = FakeDispatcher()
    result = document_service.request_parse(
        db,
        actor=actor,
        document_id=document_id,
        allow_fallback=True,
        extract_coordinates=True,
        idempotency_key=str(uuid.uuid4()),
        dispatcher=dispatcher,
    )
    job_id = uuid.UUID(str(result.data["id"])) if result.data else uuid.uuid4()
    job, run = claim(db, job_id)
    grobid = RecordedGrobid()

    document = document_service.execute_parse_job(
        db,
        job=job,
        run_id=run.id,
        grobid=grobid,
        storage_backend=memory_storage,
    )
    assert job_service.complete_job(
        db,
        job_id=job.id,
        run_id=run.id,
        worker_id="document-test-worker",
        output_object_type="document",
        output_object_id=document.id,
    )

    db.refresh(document)
    assert document.parser_type == DocumentParserType.GROBID
    assert document.parse_confidence == DocumentParseConfidence.HIGH
    assert document.parse_status == JobStatus.COMPLETED
    assert document.page_count == 2
    pages = db.exec(
        select(DocumentPage)
        .where(DocumentPage.document_id == document.id)
        .order_by(DocumentPage.page_number)
    ).all()
    chunks = db.exec(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document.id)
        .order_by(DocumentChunk.chunk_index)
    ).all()
    assert [page.page_number for page in pages] == [1, 2]
    assert "Left column" in (pages[0].text_content or "")
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2, 3]
    assert grobid.coordinate_requests == [True]

    tei = db.exec(
        select(Artifact).where(
            Artifact.project_id == uuid.UUID(project_id),
            Artifact.artifact_type == ArtifactType.OTHER,
            Artifact.mime_type == "application/tei+xml",
        )
    ).one()
    assert tei.is_immutable is True and tei.is_original is False
    assert tei.source_artifact_id == source_artifact_id
    assert memory_storage.objects[tei.storage_key] == TEI
    relation = db.exec(
        select(ArtifactRelation).where(
            ArtifactRelation.source_artifact_id == source_artifact_id,
            ArtifactRelation.target_artifact_id == tei.id,
        )
    ).one()
    assert relation.relation_type == ArtifactRelationType.DERIVED_FROM

    duplicate = job_service.claim_job(
        db,
        job_id=job.id,
        worker_id="duplicate-worker",
        engine="reca-worker",
        engine_version="0.1.0",
    )
    assert duplicate is None
    assert len(memory_storage.objects) == 2

    page_response = client.get(
        f"/api/v1/documents/{document.id}/pages/1",
        headers=normal_user_token_headers,
    )
    assert page_response.status_code == 200
    assert page_response.json()["data"]["page_number"] == 1


def test_pypdf_fallback_is_low_confidence_without_fake_structure(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    actor = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).one()
    project_id = create_project(client, normal_user_token_headers)
    document_id, _ = upload_document(client, normal_user_token_headers, project_id)
    result = document_service.request_parse(
        db,
        actor=actor,
        document_id=document_id,
        allow_fallback=True,
        extract_coordinates=True,
        idempotency_key=str(uuid.uuid4()),
        dispatcher=FakeDispatcher(),
    )
    assert result.data is not None
    job, run = claim(db, uuid.UUID(str(result.data["id"])))

    document = document_service.execute_parse_job(
        db,
        job=job,
        run_id=run.id,
        grobid=UnavailableGrobid(),
        storage_backend=memory_storage,
    )

    assert document.parser_type == DocumentParserType.PYPDF
    assert document.parse_confidence == DocumentParseConfidence.LOW
    page = db.exec(
        select(DocumentPage).where(DocumentPage.document_id == document.id)
    ).one()
    chunk = db.exec(
        select(DocumentChunk).where(DocumentChunk.document_id == document.id)
    ).one()
    assert page.parser_metadata is not None
    assert page.parser_metadata["coordinates_available"] is False
    assert chunk.section_path is None
    assert chunk.chunk_metadata is not None
    assert chunk.chunk_metadata["structure_available"] is False
    stored_run = db.get(ProcessingRun, run.id)
    assert stored_run is not None and stored_run.implementation_metadata is not None
    degradation = stored_run.implementation_metadata["degradation_record"]
    assert degradation["reason_code"] == "GROBID_UNAVAILABLE"
    assert degradation["result_status"] == "DEGRADED"
    assert (
        db.exec(
            select(Artifact).where(
                Artifact.project_id == document.project_id,
                Artifact.mime_type == "application/tei+xml",
            )
        ).all()
        == []
    )


def test_grobid_failure_without_fallback_fails_closed(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    actor = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).one()
    project_id = create_project(client, normal_user_token_headers)
    document_id, _ = upload_document(client, normal_user_token_headers, project_id)
    requested = document_service.request_parse(
        db,
        actor=actor,
        document_id=document_id,
        allow_fallback=False,
        extract_coordinates=True,
        idempotency_key=str(uuid.uuid4()),
        dispatcher=FakeDispatcher(),
    )
    assert requested.data is not None
    job, run = claim(db, uuid.UUID(str(requested.data["id"])))

    with pytest.raises(DocumentParseError) as raised:
        document_service.execute_parse_job(
            db,
            job=job,
            run_id=run.id,
            grobid=UnavailableGrobid(),
            storage_backend=memory_storage,
        )

    assert raised.value.code == "GROBID_UNAVAILABLE"
    document = db.get(Document, document_id)
    stored_run = db.get(ProcessingRun, run.id)
    assert document is not None
    assert document.parse_status == JobStatus.FAILED
    assert document.parser_type == DocumentParserType.NONE
    assert (
        db.exec(
            select(DocumentPage).where(DocumentPage.document_id == document_id)
        ).all()
        == []
    )
    assert stored_run is not None
    assert "degradation_record" not in (stored_run.implementation_metadata or {})


def test_one_document_failure_does_not_block_another_job(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    actor = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).one()
    project_id = create_project(client, normal_user_token_headers)
    blank_writer = PdfWriter()
    blank_writer.add_blank_page(width=200, height=200)
    blank_buffer = BytesIO()
    blank_writer.write(blank_buffer)
    failed_document_id, _ = upload_document(
        client,
        normal_user_token_headers,
        project_id,
        content=blank_buffer.getvalue(),
    )
    successful_document_id, _ = upload_document(
        client, normal_user_token_headers, project_id
    )

    failed_request = document_service.request_parse(
        db,
        actor=actor,
        document_id=failed_document_id,
        allow_fallback=True,
        extract_coordinates=True,
        idempotency_key=str(uuid.uuid4()),
        dispatcher=FakeDispatcher(),
    )
    successful_request = document_service.request_parse(
        db,
        actor=actor,
        document_id=successful_document_id,
        allow_fallback=True,
        extract_coordinates=True,
        idempotency_key=str(uuid.uuid4()),
        dispatcher=FakeDispatcher(),
    )
    assert failed_request.data is not None and successful_request.data is not None
    failed_job, failed_run = claim(db, uuid.UUID(str(failed_request.data["id"])))
    with pytest.raises(DocumentParseError) as raised:
        document_service.execute_parse_job(
            db,
            job=failed_job,
            run_id=failed_run.id,
            grobid=UnavailableGrobid(),
            storage_backend=memory_storage,
        )
    assert raised.value.code == "PDF_SCANNED_NO_TEXT"
    assert job_service.fail_job(
        db,
        job_id=failed_job.id,
        run_id=failed_run.id,
        worker_id="document-test-worker",
        error_code=raised.value.code,
        error_message="Document parsing failed.",
        retryable=raised.value.retryable,
    )

    successful_job, successful_run = claim(
        db, uuid.UUID(str(successful_request.data["id"]))
    )
    successful = document_service.execute_parse_job(
        db,
        job=successful_job,
        run_id=successful_run.id,
        grobid=RecordedGrobid(),
        storage_backend=memory_storage,
    )

    failed = db.get(Document, failed_document_id)
    assert failed is not None and failed.parse_status == JobStatus.FAILED
    assert successful.parse_status == JobStatus.COMPLETED
    assert (
        db.exec(
            select(DocumentPage).where(DocumentPage.document_id == failed_document_id)
        ).all()
        == []
    )
    assert (
        len(
            db.exec(
                select(DocumentPage).where(
                    DocumentPage.document_id == successful_document_id
                )
            ).all()
        )
        == 2
    )


def test_invalid_grobid_tei_is_retained_before_pypdf_fallback(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    actor = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).one()
    project_id = create_project(client, normal_user_token_headers)
    document_id, source_artifact_id = upload_document(
        client, normal_user_token_headers, project_id
    )
    requested = document_service.request_parse(
        db,
        actor=actor,
        document_id=document_id,
        allow_fallback=True,
        extract_coordinates=True,
        idempotency_key=str(uuid.uuid4()),
        dispatcher=FakeDispatcher(),
    )
    assert requested.data is not None
    job, run = claim(db, uuid.UUID(str(requested.data["id"])))

    document = document_service.execute_parse_job(
        db,
        job=job,
        run_id=run.id,
        grobid=RecordedGrobid(b"<invalid-tei>"),
        storage_backend=memory_storage,
    )

    assert document.parser_type == DocumentParserType.PYPDF
    tei_artifact = db.exec(
        select(Artifact).where(
            Artifact.project_id == document.project_id,
            Artifact.mime_type == "application/tei+xml",
        )
    ).one()
    assert tei_artifact.source_artifact_id == source_artifact_id
    assert memory_storage.objects[tei_artifact.storage_key] == b"<invalid-tei>"
    stored_run = db.get(ProcessingRun, run.id)
    assert stored_run is not None and stored_run.implementation_metadata is not None
    assert stored_run.implementation_metadata["tei_artifact_id"] == str(tei_artifact.id)
    assert (
        stored_run.implementation_metadata["degradation_record"]["reason_code"]
        == "GROBID_SCHEMA_INVALID"
    )
