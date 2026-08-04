from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.agents.service import ModelExecutionMode
from app.api.routes import evidence as evidence_routes
from app.core.config import settings
from app.evidence.analysis import AnalysisProviderIdentity
from app.evidence.extraction import ExtractionProviderIdentity
from app.main import app
from app.models import (
    Artifact,
    ArtifactStatus,
    ArtifactType,
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentParseConfidence,
    DocumentParserType,
    EvidenceSpan,
    EvidenceSpanVerificationRecord,
    EvidenceType,
    FieldConfirmationStatus,
    FieldEvidenceStatus,
    Job,
    JobStatus,
    LiteratureDecision,
    LiteratureDecisionStatus,
    LiteratureExtraction,
    LiteratureExtractionField,
    LiteratureExtractionFieldRevision,
    LiteratureExtractionStatus,
    LiteratureFieldCode,
    LiteratureRecord,
    LiteratureSourceType,
    ProjectMemberRole,
    ResearchProject,
    StorageProvider,
    User,
    UserCreate,
)
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_lower_string


@dataclass(frozen=True)
class EvidenceGraph:
    project: ResearchProject
    document: Document
    literature: LiteratureRecord
    page: DocumentPage
    chunk: DocumentChunk
    extraction: LiteratureExtraction
    field: LiteratureExtractionField


class FakeDispatcher:
    def __init__(self) -> None:
        self.job_ids: list[uuid.UUID] = []

    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        self.job_ids.append(job_id)


def _create_project(
    client: TestClient, headers: dict[str, str], name: str
) -> uuid.UUID:
    response = client.post(
        "/api/v1/projects",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"name": name, "project_type": "RESEARCH"},
    )
    assert response.status_code == 201, response.text
    return uuid.UUID(response.json()["data"]["id"])


def _create_user_headers(
    client: TestClient, db: Session
) -> tuple[User, dict[str, str]]:
    password = random_lower_string()
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com", password=password
        ),
    )
    return user, user_authentication_headers(
        client=client, email=user.email, password=password
    )


def _add_member(
    client: TestClient,
    owner_headers: dict[str, str],
    project_id: uuid.UUID,
    user: User,
    role: ProjectMemberRole,
) -> None:
    response = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={**owner_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"user_id": str(user.id), "role": role.value},
    )
    assert response.status_code == 201, response.text


def _graph(
    db: Session, *, project_id: uuid.UUID, owner: User, suffix: str
) -> EvidenceGraph:
    project = db.get(ResearchProject, project_id)
    assert project is not None
    artifact = Artifact(
        project_id=project.id,
        artifact_type=ArtifactType.PDF_DOCUMENT,
        filename=f"{suffix}.pdf",
        storage_provider=StorageProvider.MINIO,
        storage_key=f"stage3/{uuid.uuid4()}.pdf",
        mime_type="application/pdf",
        size_bytes=1,
        sha256="a" * 64,
        is_original=True,
        is_immutable=True,
        status=ArtifactStatus.AVAILABLE,
        created_by=owner.id,
    )
    db.add(artifact)
    db.flush()
    document = Document(
        project_id=project.id,
        artifact_id=artifact.id,
        parser_type=DocumentParserType.GROBID,
        parser_version="0.8.2",
        parse_status=JobStatus.COMPLETED,
        page_count=1,
        parse_confidence=DocumentParseConfidence.HIGH,
    )
    db.add(document)
    db.flush()
    text = "The final sample included exactly 312 undergraduate participants."
    page = DocumentPage(
        document_id=document.id,
        project_id=project.id,
        page_number=1,
        text_content=text,
        width=600,
        height=800,
        parser_metadata={
            "coordinates": [
                {"page": 1, "x": 10.0, "y": 20.0, "width": 100.0, "height": 15.0}
            ]
        },
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
    literature = LiteratureRecord(
        project_id=project.id,
        document_id=document.id,
        source_type=LiteratureSourceType.USER_UPLOAD,
        title=f"Evidence paper {suffix}",
        normalized_title=f"evidence paper {suffix}",
        authors_text="A. Researcher",
        publication_year=2025,
    )
    db.add(page)
    db.add(chunk)
    db.add(literature)
    db.flush()
    extraction = LiteratureExtraction(
        project_id=project.id,
        literature_record_id=literature.id,
        document_id=document.id,
        extraction_version=1,
        schema_version="1.0",
        status=LiteratureExtractionStatus.NEEDS_REVIEW,
    )
    db.add(extraction)
    db.flush()
    field = LiteratureExtractionField(
        project_id=project.id,
        extraction_id=extraction.id,
        field_code=LiteratureFieldCode.SAMPLE_SIZE,
        model_value_text="300",
        value_text="300",
        confidence_score=0.7,
        evidence_status=FieldEvidenceStatus.NO_LOCATED_EVIDENCE,
        evidence_limitations="NO_LOCATED_EVIDENCE: model returned no candidate.",
    )
    db.add(field)
    db.commit()
    return EvidenceGraph(project, document, literature, page, chunk, extraction, field)


def _owner(db: Session) -> User:
    return db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).one()


def _span_payload(source_text: str) -> dict[str, object]:
    return {
        "page_number": 1,
        "source_text": source_text,
        "bounding_boxes": [],
        "evidence_type": EvidenceType.SAMPLE_DESCRIPTION.value,
        "user_declared_read_scope": "SECTIONS",
    }


def test_extraction_get_field_history_if_match_and_no_disclosure(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    owner = _owner(db)
    project_id = _create_project(client, normal_user_token_headers, "Stage 3 fields")
    graph = _graph(db, project_id=project_id, owner=owner, suffix="fields")
    outsider, outsider_headers = _create_user_headers(client, db)
    assert outsider.id != owner.id

    visible = client.get(
        f"/api/v1/literature-extractions/{graph.extraction.id}",
        headers=normal_user_token_headers,
    )
    assert visible.status_code == 200, visible.text
    assert len(visible.json()["data"]["fields"]) == 10

    hidden = client.get(
        f"/api/v1/literature-extractions/{graph.extraction.id}",
        headers=outsider_headers,
    )
    assert hidden.status_code == 404

    key = str(uuid.uuid4())
    payload = {
        "value_text": "312",
        "value_json": {"n": 312},
        "evidence_span_id": None,
        "correction_reason": "Corrected from the page text.",
        "confirmation_status": FieldConfirmationStatus.CONFIRMED.value,
    }
    first = client.patch(
        f"/api/v1/literature-extraction-fields/{graph.field.id}",
        headers={
            **normal_user_token_headers,
            "If-Match": '"1"',
            "Idempotency-Key": key,
        },
        json=payload,
    )
    replay = client.patch(
        f"/api/v1/literature-extraction-fields/{graph.field.id}",
        headers={
            **normal_user_token_headers,
            "If-Match": '"1"',
            "Idempotency-Key": key,
        },
        json=payload,
    )
    assert first.status_code == replay.status_code == 200
    assert replay.json()["meta"]["idempotency_replayed"] is True
    db.refresh(graph.field)
    assert graph.field.model_value_text == "300"
    assert graph.field.value_text == "312"
    assert graph.field.lock_version == 2
    revisions = db.exec(
        select(LiteratureExtractionFieldRevision).where(
            LiteratureExtractionFieldRevision.field_id == graph.field.id
        )
    ).all()
    assert len(revisions) == 1
    assert revisions[0].old_value_text == "300"
    assert revisions[0].new_value_text == "312"

    stale = client.patch(
        f"/api/v1/literature-extraction-fields/{graph.field.id}",
        headers={
            **normal_user_token_headers,
            "If-Match": '"1"',
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={**payload, "value_text": "313"},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "RESOURCE_VERSION_CONFLICT"


def test_manual_span_verification_roles_and_project_scope(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    owner = _owner(db)
    project_id = _create_project(client, normal_user_token_headers, "Stage 3 evidence")
    graph = _graph(db, project_id=project_id, owner=owner, suffix="evidence")
    reviewer, reviewer_headers = _create_user_headers(client, db)
    viewer, viewer_headers = _create_user_headers(client, db)
    _add_member(
        client,
        normal_user_token_headers,
        project_id,
        reviewer,
        ProjectMemberRole.REVIEWER,
    )
    _add_member(
        client,
        normal_user_token_headers,
        project_id,
        viewer,
        ProjectMemberRole.VIEWER,
    )

    fabricated = client.post(
        f"/api/v1/documents/{graph.document.id}/evidence-spans",
        headers={**reviewer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json=_span_payload("fabricated quotation"),
    )
    assert fabricated.status_code == 422
    assert fabricated.json()["error"]["code"] == "EVIDENCE_TEXT_NOT_FOUND"

    source_text = "exactly 312 undergraduate participants"
    created = client.post(
        f"/api/v1/documents/{graph.document.id}/evidence-spans",
        headers={**reviewer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json=_span_payload(source_text),
    )
    assert created.status_code == 201, created.text
    span_id = created.json()["data"]["id"]
    assert (
        created.json()["data"]["source_text_hash"]
        == hashlib.sha256(source_text.encode()).hexdigest()
    )

    viewer_denied = client.post(
        f"/api/v1/evidence-spans/{span_id}/verification-records",
        headers={**viewer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "location_verification_status": "VERIFIED",
            "user_declared_read_scope": "FULL_TEXT_DECLARED",
            "reviewed_page_numbers": [1],
            "note": "Viewer cannot verify.",
        },
    )
    assert viewer_denied.status_code == 403

    verified = client.post(
        f"/api/v1/evidence-spans/{span_id}/verification-records",
        headers={**reviewer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "location_verification_status": "VERIFIED",
            "user_declared_read_scope": "SECTIONS",
            "reviewed_page_numbers": [1],
            "note": "Reviewed the exact page text.",
        },
    )
    assert verified.status_code == 201, verified.text
    span = db.get(EvidenceSpan, uuid.UUID(span_id))
    assert span is not None
    assert span.location_verification_status.value == "VERIFIED"
    assert span.user_declared_read_scope.value == "SECTIONS"
    records = db.exec(
        select(EvidenceSpanVerificationRecord).where(
            EvidenceSpanVerificationRecord.evidence_span_id == span.id
        )
    ).all()
    assert len(records) == 1 and records[0].source_text_hash == span.source_text_hash

    other_project_id = _create_project(
        client, normal_user_token_headers, "Stage 3 other evidence"
    )
    other = _graph(db, project_id=other_project_id, owner=owner, suffix="other")
    other_span = EvidenceSpan(
        project_id=other.project.id,
        document_id=other.document.id,
        document_page_id=other.page.id,
        page_number=1,
        source_text=source_text,
        source_text_hash=hashlib.sha256(source_text.encode()).hexdigest(),
        evidence_type=EvidenceType.SAMPLE_DESCRIPTION,
    )
    db.add(other_span)
    db.commit()
    cross_project = client.patch(
        f"/api/v1/literature-extraction-fields/{graph.field.id}",
        headers={
            **normal_user_token_headers,
            "If-Match": '"1"',
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={
            "value_text": "312",
            "evidence_span_id": str(other_span.id),
            "correction_reason": "Cross-project span must be hidden.",
            "confirmation_status": "CONFIRMED",
        },
    )
    assert cross_project.status_code == 404


def test_decision_history_current_projection_and_matrix_filters(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    owner = _owner(db)
    project_id = _create_project(client, normal_user_token_headers, "Stage 3 matrix")
    first = _graph(db, project_id=project_id, owner=owner, suffix="matrix-a")
    second = _graph(db, project_id=project_id, owner=owner, suffix="matrix-b")
    reviewer, reviewer_headers = _create_user_headers(client, db)
    _add_member(
        client,
        normal_user_token_headers,
        project_id,
        reviewer,
        ProjectMemberRole.REVIEWER,
    )

    included = client.post(
        f"/api/v1/literature/{first.literature.id}/decisions",
        headers={**reviewer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "decision": "INCLUDED",
            "reason_code": "RELEVANT_OBJECT_AND_METHOD",
            "reason_text": "Matches the review scope.",
        },
    )
    assert included.status_code == 201
    excluded = client.post(
        f"/api/v1/literature/{first.literature.id}/decisions",
        headers={**reviewer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "decision": "EXCLUDED",
            "reason_code": "METHOD_MISMATCH",
            "reason_text": "Method is outside the final scope.",
        },
    )
    assert excluded.status_code == 201
    history = client.get(
        f"/api/v1/literature/{first.literature.id}/decisions",
        headers=reviewer_headers,
    )
    assert history.status_code == 200
    assert [row["decision"] for row in history.json()["data"]] == [
        "INCLUDED",
        "EXCLUDED",
    ]
    assert [row["is_current"] for row in history.json()["data"]] == [False, True]
    db.refresh(first.literature)
    assert first.literature.current_decision == LiteratureDecisionStatus.EXCLUDED
    assert (
        len(
            db.exec(
                select(LiteratureDecision).where(
                    LiteratureDecision.literature_record_id == first.literature.id
                )
            ).all()
        )
        == 2
    )

    client.post(
        f"/api/v1/literature/{second.literature.id}/decisions",
        headers={**reviewer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "decision": "INCLUDED",
            "reason_code": "RELEVANT_OBJECT_AND_METHOD",
            "reason_text": "Included in current literature set.",
        },
    )
    db.refresh(second.literature)
    second.literature.current_decision = LiteratureDecisionStatus.EXCLUDED
    db.add(second.literature)
    db.commit()
    matrix = client.get(
        f"/api/v1/projects/{project_id}/literature-matrix",
        headers=reviewer_headers,
        params={
            "included_only": "true",
            "field_codes": ["SAMPLE_SIZE", "LIMITATION"],
            "page": 1,
            "page_size": 1,
            "sort": "title",
            "order": "asc",
        },
    )
    assert matrix.status_code == 200, matrix.text
    assert matrix.json()["pagination"]["total"] == 1
    assert matrix.json()["data"][0]["literature_record_id"] == str(second.literature.id)
    assert [field["field_code"] for field in matrix.json()["data"][0]["fields"]] == [
        "SAMPLE_SIZE",
        "LIMITATION",
    ]
    assert "evidence.search" not in matrix.json()["allowed_actions"]
    assert "evidence_summary.create" not in matrix.json()["allowed_actions"]
    owner_matrix = client.get(
        f"/api/v1/projects/{project_id}/literature-matrix",
        headers=normal_user_token_headers,
        params={"page_size": 1},
    )
    assert owner_matrix.status_code == 200
    assert {
        "evidence.search",
        "evidence_summary.create",
    } <= set(owner_matrix.json()["allowed_actions"])
    unknown = client.get(
        f"/api/v1/projects/{project_id}/literature-matrix",
        headers=reviewer_headers,
        params={"sort": "unknown"},
    )
    assert unknown.status_code == 422
    alias = client.post(
        f"/api/v1/literature-records/{first.literature.id}/decisions",
        headers={**reviewer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"decision": "UNCERTAIN"},
    )
    assert alias.status_code == 404


def test_extraction_request_and_openapi_contract(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: object,
) -> None:
    owner = _owner(db)
    project_id = _create_project(
        client, normal_user_token_headers, "Stage 3 extraction"
    )
    graph = _graph(db, project_id=project_id, owner=owner, suffix="extract")
    dispatcher = FakeDispatcher()
    identity = ExtractionProviderIdentity(
        provider_id="stage3-recorded-provider",
        provider_name="recorded",
        model_name="recorded-literature-1",
        mode=ModelExecutionMode.MOCK,
        fixture_id="stage3-literature-fixture-v1",
    )
    monkeypatch.setattr(evidence_routes, "dispatcher", dispatcher)  # type: ignore[attr-defined]
    monkeypatch.setattr(  # type: ignore[attr-defined]
        evidence_routes, "extraction_identity_provider", lambda: identity
    )
    response = client.post(
        f"/api/v1/documents/{graph.document.id}/literature-extractions",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={
            "literature_record_id": str(graph.literature.id),
            "field_codes": [code.value for code in LiteratureFieldCode],
        },
    )
    assert response.status_code == 201, response.text
    assert dispatcher.job_ids == [uuid.UUID(response.json()["data"]["id"])]

    schema = app.openapi()
    paths = schema["paths"]
    assert "/api/v1/documents/{document_id}/literature-extractions" in paths
    assert "/api/v1/literature-extractions/{extraction_id}" in paths
    assert "/api/v1/literature-extraction-fields/{field_id}" in paths
    assert "/api/v1/documents/{document_id}/evidence-spans" in paths
    assert "/api/v1/evidence-spans/{evidence_span_id}" in paths
    assert "/api/v1/evidence-spans/{evidence_span_id}/verification-records" in paths
    assert "/api/v1/literature/{literature_id}/decisions" in paths
    assert "/api/v1/projects/{project_id}/literature-matrix" in paths
    assert not any("literature-records" in path for path in paths)
    assert not any(path.endswith("/confirm") for path in paths if "extraction" in path)


def test_evidence_search_and_summary_request_contract(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: object,
) -> None:
    owner = _owner(db)
    project_id = _create_project(client, normal_user_token_headers, "Stage 4 analysis")
    graph = _graph(db, project_id=project_id, owner=owner, suffix="stage4-analysis")
    decision = client.post(
        f"/api/v1/literature/{graph.literature.id}/decisions",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"decision": "INCLUDED", "reason_text": "Current evidence set."},
    )
    assert decision.status_code == 201

    search = client.post(
        f"/api/v1/projects/{project_id}/evidence-search",
        headers=normal_user_token_headers,
        json={"query": "312 participants", "top_k": 5, "retrieval_mode": "KEYWORD"},
    )
    assert search.status_code == 200, search.text
    assert search.json()["data"]["candidates"]
    assert all(
        candidate["project_id"] == str(project_id)
        for candidate in search.json()["data"]["candidates"]
    )

    dispatcher = FakeDispatcher()
    identity = AnalysisProviderIdentity(
        provider_id="stage4-recorded-provider",
        provider_name="recorded",
        model_name="recorded-analysis-1",
        mode=ModelExecutionMode.MOCK,
        fixture_id="stage4-analysis-fixture-v1",
    )
    monkeypatch.setattr(evidence_routes, "dispatcher", dispatcher)  # type: ignore[attr-defined]
    monkeypatch.setattr(  # type: ignore[attr-defined]
        evidence_routes, "analysis_identity_provider", lambda: identity
    )
    key = str(uuid.uuid4())
    payload = {
        "included_literature_ids": [str(graph.literature.id)],
        "summary_types": ["CONSENSUS", "EVIDENCE_GAP"],
        "require_evidence_spans": False,
    }
    created = client.post(
        f"/api/v1/projects/{project_id}/evidence-set-summaries",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json=payload,
    )
    replay = client.post(
        f"/api/v1/projects/{project_id}/evidence-set-summaries",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json=payload,
    )
    assert created.status_code == replay.status_code == 201
    assert replay.json()["meta"]["idempotency_replayed"] is True
    job = db.get(Job, uuid.UUID(created.json()["data"]["id"]))
    assert job is not None and job.resource_id is not None
    detail = client.get(
        f"/api/v1/evidence-set-summaries/{job.resource_id}",
        headers=normal_user_token_headers,
    )
    assert detail.status_code == 200
    assert detail.json()["data"]["status"] == "QUEUED"

    conflict = client.post(
        f"/api/v1/projects/{project_id}/evidence-set-summaries",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json={**payload, "summary_types": ["CONTROVERSY"]},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
