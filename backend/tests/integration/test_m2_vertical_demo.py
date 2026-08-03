from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.adapters.documents import GrobidResult
from app.adapters.literature import PyAlexOpenAlexProvider, RecordedOpenAlexTransport
from app.artifacts import service as artifact_service
from app.core.config import settings
from app.documents import service as document_service
from app.jobs import service as job_service
from app.literature import service as literature_service
from app.models import (
    Artifact,
    Document,
    DocumentPage,
    DocumentParseConfidence,
    DocumentParserType,
    Job,
    JobStatus,
    JobTaskType,
    LiteratureRecord,
    LiteratureSearchRun,
    ResearchQuestionVersion,
    ResearchQuestionVersionStatus,
    User,
    UserCreate,
)
from app.research_questions.scoping import (
    DEFAULT_RECORDED_FIXTURE,
    load_fixture_contract,
)
from app.workers import jobs as worker_jobs
from tests.documents.test_parse_workflow import MemoryStorage
from tests.documents.test_parsing import TEI, text_pdf_bytes
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_lower_string

OPENALEX_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "openalex"
    / "works_recorded.json"
)


class CapturingDispatcher:
    def __init__(self) -> None:
        self.job_ids: list[uuid.UUID] = []

    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        assert task_id
        self.job_ids.append(job_id)


class RecordedGrobid:
    def parse(self, pdf_path: Path, *, extract_coordinates: bool) -> GrobidResult:
        assert extract_coordinates is True
        assert pdf_path.read_bytes().startswith(b"%PDF")
        return GrobidResult(tei=TEI, version="0.8.2", revision="recorded-m2-10")


def _key() -> str:
    return str(uuid.uuid4())


def _run_worker_job(
    db: Session, job_id: uuid.UUID
) -> tuple[Job, worker_jobs.JobExecutionResult]:
    claim = job_service.claim_job(
        db,
        job_id=job_id,
        worker_id="m2-vertical-worker",
        engine="reca-worker",
        engine_version="0.1.0",
        implementation_metadata={"acceptance_stage": "M2-10"},
    )
    assert claim is not None
    job = db.get(Job, job_id)
    assert job is not None
    handler = worker_jobs._handlers[job.task_type]
    result = handler(session=db, job=job, run_id=claim.run_id)
    assert job_service.complete_job(
        db,
        job_id=job.id,
        run_id=claim.run_id,
        worker_id="m2-vertical-worker",
        output_object_type=result.output_object_type,
        output_object_id=result.output_object_id,
        log_artifact_id=result.log_artifact_id,
    )
    db.refresh(job)
    assert job.status == JobStatus.COMPLETED
    return job, result


def _create_outsider(client: TestClient, db: Session) -> tuple[User, dict[str, str]]:
    password = random_lower_string()
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com",
            password=password,
        ),
    )
    return user, user_authentication_headers(
        client=client, email=user.email, password=password
    )


def test_m2_recorded_vertical_demo_and_cross_project_security(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.routes import documents as document_routes
    from app.api.routes import literature as literature_routes
    from app.api.routes import research_questions as research_question_routes

    storage = MemoryStorage()
    monkeypatch.setattr(artifact_service, "storage", storage)

    scoping_dispatcher = CapturingDispatcher()
    monkeypatch.setattr(research_question_routes, "dispatcher", scoping_dispatcher)
    search_dispatcher = CapturingDispatcher()
    monkeypatch.setattr(literature_routes, "dispatcher", search_dispatcher)
    parse_dispatcher = CapturingDispatcher()
    monkeypatch.setattr(document_routes, "dispatcher", parse_dispatcher)

    recorded = json.loads(OPENALEX_FIXTURE.read_text(encoding="utf-8"))
    provider = PyAlexOpenAlexProvider(
        transport=RecordedOpenAlexTransport(recorded["recordings"])
    )
    monkeypatch.setattr(literature_service, "PyAlexOpenAlexProvider", lambda: provider)
    monkeypatch.setattr(document_service, "GrobidAdapter", RecordedGrobid)

    project_response = client.post(
        "/api/v1/projects",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
        json={"name": "M2 recorded vertical demo", "project_type": "RESEARCH"},
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["data"]["id"]

    fixture = load_fixture_contract(DEFAULT_RECORDED_FIXTURE)
    assert fixture.input_match is not None
    idea = str(fixture.input_match["topic"])
    question_response = client.post(
        f"/api/v1/projects/{project_id}/research-questions",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
        json={"raw_input": idea},
    )
    assert question_response.status_code == 201, question_response.text
    question = question_response.json()["data"]
    first_version_id = question["current_version"]["id"]

    scoped = client.post(
        f"/api/v1/research-question-versions/{first_version_id}/parse",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
        json={"max_follow_up_questions": 3, "language": "zh-CN"},
    )
    assert scoped.status_code == 202, scoped.text
    scoping_job_id = uuid.UUID(scoped.json()["data"]["id"])
    assert scoping_dispatcher.job_ids == [scoping_job_id]
    scoping_job, scoping_result = _run_worker_job(db, scoping_job_id)
    assert scoping_job.task_type == JobTaskType.RESEARCH_QUESTION_SCOPING
    scoping_artifact = db.get(Artifact, scoping_result.output_object_id)
    assert scoping_artifact is not None
    candidate_envelope = json.loads(
        storage.objects[scoping_artifact.storage_key].decode("utf-8")
    )
    assert candidate_envelope["result"]["status"] == "CANDIDATES_READY"
    assert len(candidate_envelope["result"]["candidates"]) == 1
    assert scoping_artifact.artifact_metadata["mode"] == "RECORDED"

    candidate = candidate_envelope["result"]["candidates"][0]
    edited = client.post(
        f"/api/v1/research-questions/{question['id']}/versions",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
        json={
            "based_on_version_id": first_version_id,
            "change_reason": "User reviewed the recorded scoping candidate.",
            "fields": {
                "normalized_question": candidate["spec"]["normalized_question"],
                "research_object": candidate["spec"]["research_object"],
                "context": candidate["spec"]["context"],
                "research_goal": candidate["spec"]["research_goal"],
                "relationship_type": candidate["spec"]["relationship_type"],
            },
        },
    )
    assert edited.status_code == 201, edited.text
    confirmed_version_id = edited.json()["data"]["id"]
    ready = client.post(
        f"/api/v1/research-question-versions/{confirmed_version_id}/ready",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
        json={"reason": "User reviewed the candidate fields."},
    )
    assert ready.status_code == 200, ready.text
    approval = client.post(
        f"/api/v1/research-question-versions/{confirmed_version_id}/approval-requests",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
    )
    assert approval.status_code == 201, approval.text
    approved = client.post(
        f"/api/v1/approvals/{approval.json()['data']['id']}/approve",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
        json={"decision_reason": "Scope confirmed.", "item_decisions": []},
    )
    assert approved.status_code == 200, approved.text
    version = db.get(ResearchQuestionVersion, uuid.UUID(confirmed_version_id))
    assert version is not None
    assert version.status == ResearchQuestionVersionStatus.CONFIRMED

    plan_response = client.post(
        f"/api/v1/projects/{project_id}/query-plans",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
        json={
            "research_question_version_id": confirmed_version_id,
            "chinese_terms": ["生成式人工智能", "学习投入"],
            "english_terms": ["generative AI", "learning engagement"],
            "boolean_query": '("generative AI" OR GenAI) AND "learning engagement"',
            "filters": {
                "from_year": 2020,
                "to_year": 2026,
                "languages": ["zh", "en"],
                "work_types": ["article"],
                "open_access_only": False,
            },
        },
    )
    assert plan_response.status_code == 201, plan_response.text
    plan = plan_response.json()["data"]

    search_response = client.post(
        f"/api/v1/query-plans/{plan['id']}/search-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
        json={"page_size": 25, "use_cache": True},
    )
    assert search_response.status_code == 202, search_response.text
    search_job_id = uuid.UUID(search_response.json()["data"]["job"]["id"])
    assert search_dispatcher.job_ids == [search_job_id]
    search_job, search_result = _run_worker_job(db, search_job_id)
    assert search_job.task_type == JobTaskType.LITERATURE_SEARCH
    search_run = db.get(LiteratureSearchRun, search_result.output_object_id)
    assert search_run is not None
    assert search_run.provider == "OPENALEX_PYALEX"
    assert search_run.degraded is True
    assert search_run.result_count == 1

    results_response = client.get(
        f"/api/v1/literature-search-runs/{search_run.id}/results",
        headers=normal_user_token_headers,
    )
    assert results_response.status_code == 200, results_response.text
    results = results_response.json()["data"]["results"]
    assert len(results) == 1
    assert results[0]["degraded"] is True

    cached_response = client.post(
        f"/api/v1/query-plans/{plan['id']}/search-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
        json={"page_size": 25, "use_cache": True},
    )
    assert cached_response.status_code == 202, cached_response.text
    cached_job_id = uuid.UUID(cached_response.json()["data"]["job"]["id"])
    assert search_dispatcher.job_ids == [search_job_id, cached_job_id]
    _, cached_result = _run_worker_job(db, cached_job_id)
    cached_run = db.get(LiteratureSearchRun, cached_result.output_object_id)
    assert cached_run is not None
    assert cached_run.cache_hit is True
    assert cached_run.cache_source_run_id == search_run.id
    assert cached_run.degraded is True
    assert cached_run.result_count == search_run.result_count

    imported = client.post(
        f"/api/v1/projects/{project_id}/literature/import",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
        json={
            "search_run_id": str(search_run.id),
            "result_ids": [results[0]["id"]],
        },
    )
    assert imported.status_code == 200, imported.text
    literature_id = imported.json()["data"]["imported"][0]["literature_record_id"]
    doi_import = client.post(
        f"/api/v1/projects/{project_id}/literature/import-doi",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
        json={"doi": results[0]["doi"]},
    )
    assert doi_import.status_code == 200, doi_import.text
    assert doi_import.json()["data"]["id"] == literature_id
    assert db.get(LiteratureRecord, uuid.UUID(literature_id)) is not None

    upload = client.post(
        f"/api/v1/projects/{project_id}/documents",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
        files={
            "file": (
                "recorded-paper.pdf",
                text_pdf_bytes("M2 vertical page text"),
                "application/pdf",
            )
        },
        data={
            "document_type": "SCHOLARLY_PDF",
            "literature_record_id": literature_id,
        },
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["data"]["document"]["id"]
    document = db.get(Document, uuid.UUID(document_id))
    assert document is not None
    source_artifact = db.get(Artifact, document.artifact_id)
    assert source_artifact is not None and source_artifact.is_original is True

    parse = client.post(
        f"/api/v1/documents/{document_id}/parse",
        headers={**normal_user_token_headers, "Idempotency-Key": _key()},
        json={"allow_fallback": True, "extract_coordinates": True},
    )
    assert parse.status_code == 202, parse.text
    parse_job_id = uuid.UUID(parse.json()["data"]["id"])
    assert parse_dispatcher.job_ids == [parse_job_id]
    parse_job, parse_result = _run_worker_job(db, parse_job_id)
    assert parse_job.task_type == JobTaskType.DOCUMENT_PARSE
    assert parse_result.output_object_id == document.id
    db.refresh(document)
    assert document.parser_type == DocumentParserType.GROBID
    assert document.parse_confidence == DocumentParseConfidence.HIGH
    assert document.parse_status == JobStatus.COMPLETED

    pages_response = client.get(
        f"/api/v1/documents/{document_id}/pages",
        headers=normal_user_token_headers,
    )
    assert pages_response.status_code == 200, pages_response.text
    pages = pages_response.json()["data"]
    assert [page["page_number"] for page in pages] == [1, 2]
    assert "Left column" in pages[0]["text_content"]
    assert (
        len(
            db.exec(
                select(DocumentPage).where(
                    DocumentPage.document_id == uuid.UUID(document_id)
                )
            ).all()
        )
        == 2
    )

    _, outsider_headers = _create_outsider(client, db)
    hidden_paths = [
        f"/api/v1/research-question-versions/{confirmed_version_id}",
        f"/api/v1/query-plans/{plan['id']}",
        f"/api/v1/literature-search-runs/{search_run.id}/results",
        f"/api/v1/literature/{literature_id}",
        f"/api/v1/documents/{document_id}",
        f"/api/v1/documents/{document_id}/pages/1",
    ]
    for path in hidden_paths:
        hidden = client.get(path, headers=outsider_headers)
        assert hidden.status_code == 404, (path, hidden.text)
        assert hidden.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    linked_record = db.get(LiteratureRecord, uuid.UUID(literature_id))
    assert linked_record is not None and linked_record.document_id == document.id
    assert (
        crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER) is not None
    )
