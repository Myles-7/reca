from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from app.agents.service import ModelExecutionMode, canonical_hash
from app.approvals import service as approval_service
from app.evidence import review as evidence_review
from app.evidence.analysis import (
    AnalysisProviderIdentity,
    execute_summary_job,
    execute_topic_job,
    request_summary_job,
    request_topic_job,
)
from app.evidence.extraction import (
    ExtractionProviderIdentity,
    execute_extraction_job,
    request_extraction_job,
)
from app.evidence.schemas import (
    EvidenceSetSummaryCreate,
    EvidenceSpanVerificationCreate,
    LiteratureDecisionCreate,
    LiteratureExtractionFieldCorrection,
    MatrixSort,
    SortOrder,
    TopicGenerationCreate,
)
from app.jobs import service as job_service
from app.models import (
    ApprovalStatus,
    Artifact,
    ArtifactStatus,
    ArtifactType,
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentParseConfidence,
    DocumentParserType,
    EvidenceSetSummary,
    EvidenceSpan,
    FieldConfirmationStatus,
    Job,
    JobStatus,
    LiteratureDecision,
    LiteratureDecisionStatus,
    LiteratureExtraction,
    LiteratureExtractionField,
    LiteratureFieldCode,
    LiteratureRecord,
    LiteratureSourceType,
    LocationVerificationStatus,
    ProcessingRun,
    QueryPlan,
    ResearchProject,
    ResearchQuestionVersion,
    ResearchQuestionVersionStatus,
    StorageProvider,
    TopicCandidate,
    TopicCandidateEvidence,
    TopicGenerationRun,
    User,
    UserDeclaredReadScope,
)
from app.projects.schemas import ProjectCreate
from app.projects.service import create_project
from app.research_questions import service as research_question_service
from app.research_questions.schemas import ResearchQuestionVersionContent
from tests.documents.test_parsing import text_pdf_bytes
from tests.evidence.test_analysis_workflow import FakeAnalysisProvider
from tests.evidence.test_extraction_workflow import (
    FakeDispatcher,
    FakeProvider,
    MemoryStorage,
)
from tests.utils.user import create_random_user

FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "golden"
    / "m3_literature_evidence"
    / "v1"
    / "manifest.json"
)


def _fixture() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _key() -> str:
    return str(uuid.uuid4())


def _recorded_extraction_identity(raw: dict[str, Any]) -> ExtractionProviderIdentity:
    return ExtractionProviderIdentity(
        provider_id="m3-stage7-recorded-extraction",
        provider_name="recorded",
        model_name="reca-golden-extraction-v1",
        mode=ModelExecutionMode.RECORDED,
        fixture_id="reca-m3-literature-evidence-synthetic-subset",
        recording_id="m3-stage7-extraction-v1",
        recording_version="1.0",
        recording_hash=canonical_hash(raw),
        recording_license_status="RECA_AUTHORED_SYNTHETIC",
        recording_redaction_status="NO_PRODUCTION_DATA",
    )


def _recorded_analysis_identity(
    *, provider_id: str, raw: dict[str, Any]
) -> AnalysisProviderIdentity:
    return AnalysisProviderIdentity(
        provider_id=provider_id,
        provider_name="recorded",
        model_name="reca-golden-analysis-v1",
        mode=ModelExecutionMode.RECORDED,
        fixture_id="reca-m3-literature-evidence-synthetic-subset",
        recording_id=f"{provider_id}-v1",
        recording_version="1.0",
        recording_hash=canonical_hash(raw),
        recording_license_status="RECA_AUTHORED_SYNTHETIC",
        recording_redaction_status="NO_PRODUCTION_DATA",
    )


def _claim(db: Session, job: Job, *, worker: str) -> ProcessingRun:
    claim = job_service.claim_job(
        db,
        job_id=job.id,
        worker_id=worker,
        engine="reca-worker",
        engine_version="stage7-recorded",
        implementation_metadata={"acceptance_stage": "M3-7"},
    )
    assert claim is not None
    run = db.get(ProcessingRun, claim.run_id)
    assert run is not None
    return run


def _complete(
    db: Session,
    *,
    job: Job,
    run: ProcessingRun,
    worker: str,
    output_type: str,
    output_id: uuid.UUID,
    artifact_id: uuid.UUID | None,
) -> None:
    assert job_service.complete_job(
        db,
        job_id=job.id,
        run_id=run.id,
        worker_id=worker,
        output_object_type=output_type,
        output_object_id=output_id,
        log_artifact_id=artifact_id,
    )


def _base_graph(
    db: Session, data: dict[str, Any]
) -> tuple[
    User,
    ResearchProject,
    ResearchQuestionVersion,
    QueryPlan,
    LiteratureRecord,
    LiteratureRecord,
    Document,
    DocumentChunk,
    Artifact,
    MemoryStorage,
]:
    actor = create_random_user(db)
    project_result = create_project(
        db,
        actor=actor,
        payload=ProjectCreate(name="M3 Stage 7 vertical", project_type="RESEARCH"),
        idempotency_key=_key(),
    )
    project = db.get(ResearchProject, uuid.UUID(project_result.data["id"]))
    assert project is not None

    _, version = research_question_service.create_research_question(
        db,
        actor=actor,
        project_id=project.id,
        content=ResearchQuestionVersionContent(
            raw_input="How is generative AI use associated with learning engagement?",
            normalized_question="How is generative AI use associated with learning engagement?",
            research_object="Undergraduate students",
            independent_variables=["generative AI use"],
            dependent_variables=["learning engagement"],
        ),
    )
    approval = research_question_service.request_confirmation(
        db, actor=actor, version_id=version.id
    )
    approval_service.decide_approval(
        db,
        actor=actor,
        approval_id=approval.id,
        decision=ApprovalStatus.APPROVED,
        decision_reason="Stage 7 fixture confirms the scoped question.",
        item_decisions=[],
        idempotency_key=_key(),
    )
    db.refresh(version)
    assert version.status == ResearchQuestionVersionStatus.CONFIRMED
    plan = QueryPlan(
        project_id=project.id,
        research_question_version_id=version.id,
        english_terms=["generative AI use", "learning engagement"],
        boolean_query='"generative AI use" AND "learning engagement"',
        filters={"from_year": 2020, "to_year": 2026},
    )
    db.add(plan)

    pdf_bytes = text_pdf_bytes("RECA M3 synthetic acceptance document")
    artifact = Artifact(
        project_id=project.id,
        artifact_type=ArtifactType.PDF_DOCUMENT,
        filename=data["document"]["filename"],
        storage_provider=StorageProvider.MINIO,
        storage_key=f"m3-stage7/{uuid.uuid4()}.pdf",
        mime_type="application/pdf",
        size_bytes=len(pdf_bytes),
        sha256=hashlib.sha256(pdf_bytes).hexdigest(),
        is_original=True,
        is_immutable=True,
        status=ArtifactStatus.AVAILABLE,
        created_by=actor.id,
    )
    db.add(artifact)
    db.flush()
    storage = MemoryStorage()
    storage.objects[artifact.storage_key] = pdf_bytes
    document = Document(
        project_id=project.id,
        artifact_id=artifact.id,
        parser_type=DocumentParserType.GROBID,
        parser_version=data["parser_expectations"]["GROBID"]["parser_version"],
        parse_status=JobStatus.COMPLETED,
        parse_confidence=DocumentParseConfidence.HIGH,
        page_count=1,
    )
    db.add(document)
    db.flush()
    coordinates = [box for field in data["fields"] for box in field["bounding_boxes"]]
    page = DocumentPage(
        document_id=document.id,
        project_id=project.id,
        page_number=1,
        text_content=data["document"]["page_text"],
        width=data["document"]["page_width"],
        height=data["document"]["page_height"],
        parser_metadata={"coordinates": coordinates, "mode": "RECORDED"},
    )
    chunk = DocumentChunk(
        project_id=project.id,
        document_id=document.id,
        page_start=1,
        page_end=1,
        section_path=data["document"]["section_path"],
        chunk_index=0,
        content=data["document"]["page_text"],
        content_hash=data["document"]["page_text_hash"],
        chunk_metadata={"coordinates": coordinates, "mode": "RECORDED"},
    )
    included = LiteratureRecord(
        project_id=project.id,
        document_id=document.id,
        source_type=LiteratureSourceType.USER_UPLOAD,
        title="AI Use and Learning Engagement in Undergraduate Students",
        normalized_title="ai use and learning engagement in undergraduate students",
        publication_year=2025,
    )
    excluded = LiteratureRecord(
        project_id=project.id,
        source_type=LiteratureSourceType.USER_UPLOAD,
        title="Excluded synthetic contaminant",
        normalized_title="excluded synthetic contaminant",
    )
    db.add(page)
    db.add(chunk)
    db.add(included)
    db.add(excluded)
    db.commit()
    assert pdf_bytes.startswith(b"%PDF")
    assert (
        hashlib.sha256(storage.objects[artifact.storage_key]).hexdigest()
        == artifact.sha256
    )
    return (
        actor,
        project,
        version,
        plan,
        included,
        excluded,
        document,
        chunk,
        artifact,
        storage,
    )


def _extraction_output(
    data: dict[str, Any],
    *,
    project: ResearchProject,
    literature: LiteratureRecord,
    document: Document,
    chunk: DocumentChunk,
) -> dict[str, Any]:
    fields = []
    for field in data["fields"]:
        expected_text = field["expected_text"]
        expected_structured = field["expected_structured"]
        if field["field_code"] == "SAMPLE_SIZE":
            expected_text = "300"
            expected_structured = {"n": 300}
        candidates = []
        if field["source_text"] is not None:
            candidates.append(
                {
                    "candidate_id": str(
                        uuid.uuid5(uuid.NAMESPACE_URL, field["field_code"])
                    ),
                    "project_id": str(project.id),
                    "literature_record_id": str(literature.id),
                    "document_id": str(document.id),
                    "chunk_id": str(chunk.id),
                    "page_number": 1,
                    "source_text": field["source_text"],
                    "source_text_hash": field["source_text_hash"],
                    "char_start": field["char_start"],
                    "char_end": field["char_end"],
                    "bounding_boxes": field["bounding_boxes"],
                }
            )
        fields.append(
            {
                "field_code": field["field_code"],
                "value": {"text": expected_text, "structured": expected_structured},
                "evidence_candidates": candidates,
                "confidence": field["confidence"],
                "requires_human_review": field["confidence"] < 0.95,
                "notes": [] if candidates else ["No exact source candidate."],
            }
        )
    return {
        "literature_record_id": str(literature.id),
        "document_id": str(document.id),
        "fields": fields,
        "document_level_limitations": [
            "Synthetic acceptance material is not scientific ground truth."
        ],
    }


def _summary_output(
    data: dict[str, Any],
    *,
    literature_id: uuid.UUID,
    span_by_code: dict[str, EvidenceSpan],
) -> dict[str, Any]:
    conclusion = span_by_code["MAIN_CONCLUSION"]
    limitation = span_by_code["LIMITATION"]
    return {
        "included_literature_ids": [str(literature_id)],
        "scope_statement": data["summary"]["scope_statement"],
        "consensus_items": [
            {
                "claim_text": data["summary"]["items"][0]["claim"],
                "supporting_literature_ids": [str(literature_id)],
                "contradicting_literature_ids": [],
                "evidence_span_ids": [str(conclusion.id)],
                "strength": "MEDIUM",
                "limitations": [],
            }
        ],
        "controversy_items": [],
        "evidence_gap_items": [],
        "counterexamples": [
            {
                "claim_text": data["summary"]["items"][1]["claim"],
                "supporting_literature_ids": [str(literature_id)],
                "contradicting_literature_ids": [],
                "evidence_span_ids": [str(limitation.id)],
                "strength": "LOW",
                "limitations": data["summary"]["limitations"],
            }
        ],
        "method_difference_items": [],
        "sample_difference_items": [],
        "missing_literature": [],
        "missing_information": ["A real multi-paper golden set is still required."],
        "limitations": data["summary"]["limitations"],
    }


def _topic_output(
    data: dict[str, Any],
    *,
    literature_id: uuid.UUID,
    span_by_code: dict[str, EvidenceSpan],
) -> dict[str, Any]:
    candidates = []
    for item in data["topic_candidates"]:
        source_code = next(
            code
            for code in item["source_field_codes"]
            if code in {"MAIN_CONCLUSION", "LIMITATION"}
        )
        source_span = span_by_code[source_code]
        candidates.append(
            {
                "candidate_order": item["candidate_order"],
                "question_text": item["question_text"],
                "research_object": "Undergraduate students",
                "variables": {"independent": ["AI use"], "dependent": ["engagement"]},
                "literature_basis": "Bound to the completed current-set summary.",
                "possible_innovation": "Tests a bounded relation in the current set.",
                "data_requirements": {"minimum_fields": ["AI use", "engagement"]},
                "recommended_method": "Regression analysis",
                "literature_basis_level": "MEDIUM",
                "data_availability": "MEDIUM",
                "method_difficulty": "LOW",
                "time_feasibility": "HIGH",
                "ethical_risk": "LOW",
                "major_risks": [],
                "limitations": data["summary"]["limitations"],
                "supervisor_confirmation_items": ["Confirm the bounded question."],
                "sources": [
                    {
                        "literature_record_id": str(literature_id),
                        "evidence_span_id": None,
                        "relation_type": "BASIS",
                        "explanation": "Current included literature source.",
                    },
                    {
                        "literature_record_id": None,
                        "evidence_span_id": str(source_span.id),
                        "relation_type": "SUPPORT",
                        "explanation": "Located source text for the candidate.",
                    },
                ],
            }
        )
    return {"candidates": candidates}


def test_m3_recorded_vertical_database_chain(db: Session) -> None:
    data = _fixture()
    (
        actor,
        project,
        version,
        plan,
        included,
        excluded,
        document,
        chunk,
        artifact,
        storage,
    ) = _base_graph(db, data)
    assert version.status == ResearchQuestionVersionStatus.CONFIRMED
    assert plan.research_question_version_id == version.id
    assert included.document_id == document.id
    assert artifact.is_original and artifact.is_immutable

    extraction_raw = _extraction_output(
        data, project=project, literature=included, document=document, chunk=chunk
    )
    extraction_identity = _recorded_extraction_identity(extraction_raw)
    requested = request_extraction_job(
        db,
        actor=actor,
        document_id=document.id,
        idempotency_key=_key(),
        provider=extraction_identity,
        dispatcher=FakeDispatcher(),
    )
    extraction_job = db.get(Job, uuid.UUID(requested.data["id"]))
    assert extraction_job is not None
    extraction_run = _claim(db, extraction_job, worker="m3-stage7-extraction")
    extraction_result = execute_extraction_job(
        db,
        job=extraction_job,
        run_id=extraction_run.id,
        provider=FakeProvider(extraction_identity, extraction_raw),
        storage_backend=storage,
    )
    _complete(
        db,
        job=extraction_job,
        run=extraction_run,
        worker="m3-stage7-extraction",
        output_type="literature_extraction",
        output_id=extraction_result.extraction.id,
        artifact_id=extraction_result.output_artifact.id,
    )
    extraction = db.get(LiteratureExtraction, extraction_result.extraction.id)
    assert extraction is not None
    fields = db.exec(
        select(LiteratureExtractionField).where(
            LiteratureExtractionField.extraction_id == extraction.id
        )
    ).all()
    assert len(fields) == 10
    spans = db.exec(
        select(EvidenceSpan).where(EvidenceSpan.project_id == project.id)
    ).all()
    assert len(spans) == 9
    span_by_text = {span.source_text: span for span in spans}
    span_by_code = {
        field["field_code"]: span_by_text[field["source_text"]]
        for field in data["fields"]
        if field["source_text"] is not None
    }

    sample_field = next(
        field for field in fields if field.field_code == LiteratureFieldCode.SAMPLE_SIZE
    )
    sample_span = span_by_code["SAMPLE_SIZE"]
    evidence_review.update_field(
        db,
        actor=actor,
        field_id=sample_field.id,
        payload=LiteratureExtractionFieldCorrection(
            value_text="312",
            value_json={"n": 312},
            evidence_span_id=sample_span.id,
            correction_reason="Human review of the exact page text.",
            confirmation_status=FieldConfirmationStatus.CONFIRMED,
        ),
        expected_lock_version=sample_field.lock_version,
        idempotency_key=_key(),
    )
    db.refresh(sample_field)
    assert sample_field.model_value_text == "300"
    assert sample_field.value_text == "312"
    evidence_review.create_verification_record(
        db,
        actor=actor,
        span_id=sample_span.id,
        payload=EvidenceSpanVerificationCreate(
            location_verification_status=LocationVerificationStatus.VERIFIED,
            user_declared_read_scope=UserDeclaredReadScope.SECTIONS,
            reviewed_page_numbers=[1],
            note="Reviewed exact source text and recorded GROBID coordinates.",
        ),
        idempotency_key=_key(),
    )
    db.refresh(sample_span)
    assert (
        sample_span.location_verification_status == LocationVerificationStatus.VERIFIED
    )
    for field_code in ("MAIN_CONCLUSION", "LIMITATION"):
        cited_span = span_by_code[field_code]
        evidence_review.create_verification_record(
            db,
            actor=actor,
            span_id=cited_span.id,
            payload=EvidenceSpanVerificationCreate(
                location_verification_status=LocationVerificationStatus.VERIFIED,
                user_declared_read_scope=UserDeclaredReadScope.SECTIONS,
                reviewed_page_numbers=[cited_span.page_number],
                note=f"Reviewed {field_code.lower()} source text for summary use.",
            ),
            idempotency_key=_key(),
        )

    for decision in (
        LiteratureDecisionStatus.UNCERTAIN,
        LiteratureDecisionStatus.INCLUDED,
    ):
        evidence_review.create_decision(
            db,
            actor=actor,
            literature_id=included.id,
            payload=LiteratureDecisionCreate(
                decision=decision,
                reason_text="Stage 7 deterministic decision history.",
            ),
            idempotency_key=_key(),
        )
    evidence_review.create_decision(
        db,
        actor=actor,
        literature_id=excluded.id,
        payload=LiteratureDecisionCreate(
            decision=LiteratureDecisionStatus.EXCLUDED,
            reason_text="Excluded synthetic contaminant.",
        ),
        idempotency_key=_key(),
    )
    decisions = db.exec(
        select(LiteratureDecision).where(
            LiteratureDecision.literature_record_id == included.id
        )
    ).all()
    assert [row.decision for row in decisions] == [
        LiteratureDecisionStatus.UNCERTAIN,
        LiteratureDecisionStatus.INCLUDED,
    ]
    matrix, total, _ = evidence_review.list_matrix(
        db,
        actor=actor,
        project_id=project.id,
        included_only=True,
        field_codes=None,
        page=1,
        page_size=25,
        sort=MatrixSort.TITLE,
        order=SortOrder.ASC,
    )
    assert total == 1
    assert matrix[0]["literature_record_id"] == str(included.id)

    summary_raw = _summary_output(
        data, literature_id=included.id, span_by_code=span_by_code
    )
    summary_identity = _recorded_analysis_identity(
        provider_id="m3-stage7-recorded-summary", raw=summary_raw
    )
    summary_requested = request_summary_job(
        db,
        actor=actor,
        project_id=project.id,
        payload=EvidenceSetSummaryCreate(
            included_literature_ids=[included.id, excluded.id],
            summary_types=["CONSENSUS", "COUNTEREXAMPLE"],
            require_evidence_spans=True,
        ),
        idempotency_key=_key(),
        provider=summary_identity,
        dispatcher=FakeDispatcher(),
    )
    summary_job = db.get(Job, uuid.UUID(summary_requested.data["id"]))
    assert summary_job is not None
    summary = db.get(EvidenceSetSummary, summary_job.resource_id)
    assert summary is not None
    assert summary.included_literature_ids == [str(included.id)]
    summary_run = _claim(db, summary_job, worker="m3-stage7-summary")
    summary_result = execute_summary_job(
        db,
        job=summary_job,
        run_id=summary_run.id,
        provider=FakeAnalysisProvider(summary_identity, summary_output=summary_raw),
        storage_backend=storage,
    )
    _complete(
        db,
        job=summary_job,
        run=summary_run,
        worker="m3-stage7-summary",
        output_type=summary_result.output_object_type,
        output_id=summary_result.output_object_id,
        artifact_id=summary_result.output_artifact.id,
    )
    db.refresh(summary)
    assert summary.status == JobStatus.COMPLETED
    assert summary.result_payload["counterexamples"]
    assert str(excluded.id) not in json.dumps(summary.result_payload)

    topic_raw = _topic_output(
        data, literature_id=included.id, span_by_code=span_by_code
    )
    topic_identity = _recorded_analysis_identity(
        provider_id="m3-stage7-recorded-topic", raw=topic_raw
    )
    topic_requested = request_topic_job(
        db,
        actor=actor,
        project_id=project.id,
        payload=TopicGenerationCreate(
            research_question_version_id=version.id,
            evidence_set_summary_id=summary.id,
            candidate_count=3,
            user_constraints={"available_weeks": 8},
        ),
        idempotency_key=_key(),
        provider=topic_identity,
        dispatcher=FakeDispatcher(),
    )
    topic_job = db.get(Job, uuid.UUID(topic_requested.data["id"]))
    assert topic_job is not None
    topic_run = _claim(db, topic_job, worker="m3-stage7-topic")
    topic_result = execute_topic_job(
        db,
        job=topic_job,
        run_id=topic_run.id,
        provider=FakeAnalysisProvider(topic_identity, topic_output=topic_raw),
        storage_backend=storage,
    )
    _complete(
        db,
        job=topic_job,
        run=topic_run,
        worker="m3-stage7-topic",
        output_type=topic_result.output_object_type,
        output_id=topic_result.output_object_id,
        artifact_id=topic_result.output_artifact.id,
    )
    persisted_run = db.get(TopicGenerationRun, topic_result.output_object_id)
    assert persisted_run is not None and persisted_run.status == JobStatus.COMPLETED
    candidates = db.exec(
        select(TopicCandidate)
        .where(TopicCandidate.topic_generation_run_id == persisted_run.id)
        .order_by(TopicCandidate.candidate_order)
    ).all()
    links = db.exec(
        select(TopicCandidateEvidence).where(
            TopicCandidateEvidence.project_id == project.id
        )
    ).all()
    assert [candidate.candidate_order for candidate in candidates] == [1, 2, 3]
    assert len(links) == 6
    assert {link.topic_candidate_id for link in links} == {
        candidate.id for candidate in candidates
    }
    assert all(link.project_id == project.id for link in links)
