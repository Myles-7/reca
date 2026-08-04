from __future__ import annotations

import uuid
from dataclasses import replace
from typing import Any

import pytest
from sqlmodel import Session, select

from app.agents.service import ModelExecutionMode, canonical_hash
from app.approvals import service as approval_service
from app.evidence.analysis import (
    AnalysisProviderIdentity,
    EvidenceAnalysisError,
    execute_summary_job,
    execute_topic_job,
    request_summary_job,
    request_topic_job,
)
from app.evidence.schemas import EvidenceSetSummaryCreate, TopicGenerationCreate
from app.jobs import service as job_service
from app.models import (
    ApprovalStatus,
    EvidenceSetSummary,
    Job,
    JobStatus,
    LiteratureDecision,
    LiteratureDecisionStatus,
    ModelInvocation,
    ModelInvocationStatus,
    ProcessingRun,
    ResearchQuestionVersion,
    ResearchQuestionVersionStatus,
    TopicCandidate,
    TopicCandidateEvidence,
    TopicGenerationRun,
    User,
)
from app.research_questions import service as research_question_service
from app.research_questions.schemas import ResearchQuestionVersionContent
from tests.evidence.test_extraction_workflow import (
    FakeDispatcher,
    MemoryStorage,
    _graph,
)


class FakeAnalysisProvider:
    def __init__(
        self,
        identity: AnalysisProviderIdentity,
        *,
        summary_output: dict[str, Any] | None = None,
        topic_output: dict[str, Any] | None = None,
    ) -> None:
        self.identity = identity
        self.summary_output = summary_output or {}
        self.topic_output = topic_output or {}

    def summarize(self, payload: object) -> dict[str, Any]:
        return self.summary_output

    def generate_topics(self, payload: object) -> dict[str, Any]:
        return self.topic_output


def _identity() -> AnalysisProviderIdentity:
    return AnalysisProviderIdentity(
        provider_id="stage4-fake-provider",
        provider_name="fake",
        model_name="fake-analysis-1",
        mode=ModelExecutionMode.MOCK,
        fixture_id="stage4-analysis-fixture-v1",
    )


def _recorded_identity(
    raw: dict[str, Any], *, provider_id: str = "stage8-recorded-analysis"
) -> AnalysisProviderIdentity:
    return AnalysisProviderIdentity(
        provider_id=provider_id,
        provider_name="recorded",
        model_name="recorded-analysis-1",
        mode=ModelExecutionMode.RECORDED,
        fixture_id="stage8-analysis-fixture-v1",
        recording_id=f"{provider_id}-v1",
        recording_version="1.0",
        recording_hash=canonical_hash(raw),
        recording_license_status="INTERNAL_FIXTURE",
        recording_redaction_status="REVIEWED_NO_PERSONAL_DATA",
    )


def _include_literature(
    db: Session, *, literature_id: uuid.UUID, actor_id: uuid.UUID, project_id: uuid.UUID
) -> None:
    db.add(
        LiteratureDecision(
            project_id=project_id,
            literature_record_id=literature_id,
            decision=LiteratureDecisionStatus.INCLUDED,
            decided_by_user_id=actor_id,
            reason_text="Included for the current evidence set.",
        )
    )
    db.commit()


def _summary_output(literature_id: uuid.UUID) -> dict[str, Any]:
    sourced = {
        "claim_text": "The current literature set contains one eligible study.",
        "supporting_literature_ids": [str(literature_id)],
        "contradicting_literature_ids": [],
        "evidence_span_ids": [],
        "strength": "LOW",
        "limitations": ["Only the current included literature set was analyzed."],
    }
    return {
        "included_literature_ids": [str(literature_id)],
        "scope_statement": "Based on the current set of one included literature record.",
        "consensus_items": [],
        "controversy_items": [],
        "evidence_gap_items": [],
        "counterexamples": [],
        "method_difference_items": [sourced],
        "sample_difference_items": [],
        "missing_literature": [],
        "missing_information": ["More included literature is needed."],
        "limitations": ["This is not a claim about all academic literature."],
    }


def _topic_output(literature_id: uuid.UUID) -> dict[str, Any]:
    candidates = []
    for order in (1, 2, 3):
        candidates.append(
            {
                "candidate_order": order,
                "question_text": f"Current-set research question {order}",
                "research_object": "Undergraduate students",
                "variables": {
                    "independent": ["AI use"],
                    "dependent": [f"engagement {order}"],
                },
                "literature_basis": "Based on the completed current evidence summary.",
                "possible_innovation": "This relation is less represented in the current set.",
                "data_requirements": {"minimum_fields": ["AI use", "engagement"]},
                "recommended_method": "Correlation analysis",
                "literature_basis_level": "MEDIUM",
                "data_availability": "MEDIUM",
                "method_difficulty": "LOW",
                "time_feasibility": "HIGH",
                "ethical_risk": "LOW",
                "major_risks": [],
                "limitations": ["Cross-sectional evidence cannot establish causality."],
                "supervisor_confirmation_items": ["Confirm the theoretical relation."],
                "sources": [
                    {
                        "literature_record_id": str(literature_id),
                        "evidence_span_id": None,
                        "relation_type": "BASIS",
                        "explanation": "Included literature basis.",
                    }
                ],
            }
        )
    return {"candidates": candidates}


def _claim(db: Session, job: Job) -> ProcessingRun:
    claim = job_service.claim_job(
        db,
        job_id=job.id,
        worker_id="stage4-test-worker",
        engine="reca-worker",
        engine_version="test",
    )
    assert claim is not None
    run = db.get(ProcessingRun, claim.run_id)
    assert run is not None
    return run


def _confirmed_question(
    db: Session, *, project_id: uuid.UUID, actor_id: uuid.UUID
) -> ResearchQuestionVersion:
    actor = db.get(User, actor_id)
    assert actor is not None
    _, version = research_question_service.create_research_question(
        db,
        actor=actor,
        project_id=project_id,
        content=ResearchQuestionVersionContent(
            raw_input="How is AI use related to student engagement?",
            normalized_question="How is AI use related to student engagement?",
            research_object="Undergraduate students",
            independent_variables=["AI use"],
            dependent_variables=["engagement"],
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
        decision_reason="Test fixture confirms the scoped question.",
        item_decisions=[],
        idempotency_key=str(uuid.uuid4()),
    )
    db.refresh(version)
    assert version.status == ResearchQuestionVersionStatus.CONFIRMED
    return version


def test_summary_and_topic_jobs_persist_provenance_and_exactly_three_candidates(
    db: Session,
) -> None:
    actor, project, _, literature, _, _ = _graph(db)
    _include_literature(
        db,
        literature_id=literature.id,
        actor_id=actor.id,
        project_id=project.id,
    )
    identity = _identity()
    summary_key = str(uuid.uuid4())
    summary_payload = EvidenceSetSummaryCreate(
        included_literature_ids=[literature.id],
        summary_types=["CONSENSUS", "EVIDENCE_GAP"],
        require_evidence_spans=False,
    )
    summary_result = request_summary_job(
        db,
        actor=actor,
        project_id=project.id,
        payload=summary_payload,
        idempotency_key=summary_key,
        provider=identity,
        dispatcher=FakeDispatcher(),
    )
    replay = request_summary_job(
        db,
        actor=actor,
        project_id=project.id,
        payload=summary_payload,
        idempotency_key=summary_key,
        provider=identity,
        dispatcher=FakeDispatcher(),
    )
    assert replay.idempotency_replayed is True
    assert replay.data == summary_result.data
    summary_job = db.get(Job, uuid.UUID(summary_result.data["id"]))
    assert summary_job is not None
    summary_run = _claim(db, summary_job)
    summary_execution = execute_summary_job(
        db,
        job=summary_job,
        run_id=summary_run.id,
        provider=FakeAnalysisProvider(
            identity, summary_output=_summary_output(literature.id)
        ),
        storage_backend=MemoryStorage(),
    )
    assert job_service.complete_job(
        db,
        job_id=summary_job.id,
        run_id=summary_run.id,
        worker_id="stage4-test-worker",
        output_object_type=summary_execution.output_object_type,
        output_object_id=summary_execution.output_object_id,
        log_artifact_id=summary_execution.output_artifact.id,
    )
    summary = db.get(EvidenceSetSummary, summary_execution.output_object_id)
    assert summary is not None and summary.status == JobStatus.COMPLETED

    version = _confirmed_question(db, project_id=project.id, actor_id=actor.id)
    topic_result = request_topic_job(
        db,
        actor=actor,
        project_id=project.id,
        payload=TopicGenerationCreate(
            research_question_version_id=version.id,
            evidence_set_summary_id=summary.id,
            candidate_count=3,
            user_constraints={"available_weeks": 8},
        ),
        idempotency_key=str(uuid.uuid4()),
        provider=identity,
        dispatcher=FakeDispatcher(),
    )
    topic_job = db.get(Job, uuid.UUID(topic_result.data["id"]))
    assert topic_job is not None
    topic_processing = _claim(db, topic_job)
    topic_execution = execute_topic_job(
        db,
        job=topic_job,
        run_id=topic_processing.id,
        provider=FakeAnalysisProvider(
            identity, topic_output=_topic_output(literature.id)
        ),
        storage_backend=MemoryStorage(),
    )
    assert job_service.complete_job(
        db,
        job_id=topic_job.id,
        run_id=topic_processing.id,
        worker_id="stage4-test-worker",
        output_object_type=topic_execution.output_object_type,
        output_object_id=topic_execution.output_object_id,
        log_artifact_id=topic_execution.output_artifact.id,
    )
    run = db.get(TopicGenerationRun, topic_execution.output_object_id)
    assert run is not None and run.status == JobStatus.COMPLETED
    candidates = db.exec(
        select(TopicCandidate)
        .where(TopicCandidate.topic_generation_run_id == run.id)
        .order_by(TopicCandidate.candidate_order)
    ).all()
    links = db.exec(
        select(TopicCandidateEvidence).where(
            TopicCandidateEvidence.project_id == project.id
        )
    ).all()
    assert [candidate.candidate_order for candidate in candidates] == [1, 2, 3]
    assert len(links) == 3
    invocations = db.exec(
        select(ModelInvocation).where(ModelInvocation.project_id == project.id)
    ).all()
    assert [invocation.status for invocation in invocations] == [
        ModelInvocationStatus.SUCCEEDED,
        ModelInvocationStatus.SUCCEEDED,
    ]


def test_invalid_summary_output_fails_without_persisting_conclusions(
    db: Session,
) -> None:
    actor, project, _, literature, _, _ = _graph(db)
    _include_literature(
        db,
        literature_id=literature.id,
        actor_id=actor.id,
        project_id=project.id,
    )
    identity = _identity()
    result = request_summary_job(
        db,
        actor=actor,
        project_id=project.id,
        payload=EvidenceSetSummaryCreate(
            included_literature_ids=[literature.id],
            summary_types=["EVIDENCE_GAP"],
            require_evidence_spans=False,
        ),
        idempotency_key=str(uuid.uuid4()),
        provider=identity,
        dispatcher=FakeDispatcher(),
    )
    job = db.get(Job, uuid.UUID(result.data["id"]))
    assert job is not None
    processing = _claim(db, job)
    with pytest.raises(EvidenceAnalysisError) as failure:
        execute_summary_job(
            db,
            job=job,
            run_id=processing.id,
            provider=FakeAnalysisProvider(
                identity,
                summary_output={
                    **_summary_output(literature.id),
                    "scope_statement": "学术界完全没有相关研究。",
                },
            ),
            storage_backend=MemoryStorage(),
        )
    assert failure.value.code == "MODEL_OUTPUT_UNSAFE_CLAIM"
    summary = db.get(EvidenceSetSummary, job.resource_id)
    assert summary is not None and summary.status == JobStatus.FAILED
    assert "consensus_items" not in summary.result_payload


@pytest.mark.parametrize(
    ("failure_kind", "expected_code"),
    [
        ("provider", "MODEL_PROVIDER_MISMATCH"),
        ("recording", "MODEL_RECORDING_HASH_MISMATCH"),
    ],
)
def test_summary_rejects_provenance_mismatch_without_persisting_conclusions(
    db: Session, failure_kind: str, expected_code: str
) -> None:
    actor, project, _, literature, _, _ = _graph(db)
    _include_literature(
        db,
        literature_id=literature.id,
        actor_id=actor.id,
        project_id=project.id,
    )
    recorded_output = _summary_output(literature.id)
    identity = _recorded_identity(recorded_output)
    result = request_summary_job(
        db,
        actor=actor,
        project_id=project.id,
        payload=EvidenceSetSummaryCreate(
            included_literature_ids=[literature.id],
            summary_types=["EVIDENCE_GAP"],
            require_evidence_spans=False,
        ),
        idempotency_key=str(uuid.uuid4()),
        provider=identity,
        dispatcher=FakeDispatcher(),
    )
    job = db.get(Job, uuid.UUID(result.data["id"]))
    assert job is not None
    processing = _claim(db, job)
    provider_identity = (
        replace(identity, provider_id="substituted-provider")
        if failure_kind == "provider"
        else identity
    )
    provider_output = (
        {**recorded_output, "scope_statement": "Changed recorded output."}
        if failure_kind == "recording"
        else recorded_output
    )

    with pytest.raises(EvidenceAnalysisError) as failure:
        execute_summary_job(
            db,
            job=job,
            run_id=processing.id,
            provider=FakeAnalysisProvider(
                provider_identity, summary_output=provider_output
            ),
            storage_backend=MemoryStorage(),
        )

    assert failure.value.code == expected_code
    summary = db.get(EvidenceSetSummary, job.resource_id)
    assert summary is not None and summary.status == JobStatus.FAILED
    assert "consensus_items" not in summary.result_payload
    invocation = db.get(ModelInvocation, summary.source_model_invocation_id)
    assert invocation is not None
    assert invocation.status == ModelInvocationStatus.FAILED


@pytest.mark.parametrize(
    ("failure_kind", "expected_code"),
    [
        ("provider", "MODEL_PROVIDER_MISMATCH"),
        ("recording", "MODEL_RECORDING_HASH_MISMATCH"),
    ],
)
def test_topic_rejects_provenance_mismatch_without_persisting_candidates(
    db: Session, failure_kind: str, expected_code: str
) -> None:
    actor, project, _, literature, _, _ = _graph(db)
    _include_literature(
        db,
        literature_id=literature.id,
        actor_id=actor.id,
        project_id=project.id,
    )
    mock_identity = _identity()
    summary_result = request_summary_job(
        db,
        actor=actor,
        project_id=project.id,
        payload=EvidenceSetSummaryCreate(
            included_literature_ids=[literature.id],
            summary_types=["EVIDENCE_GAP"],
            require_evidence_spans=False,
        ),
        idempotency_key=str(uuid.uuid4()),
        provider=mock_identity,
        dispatcher=FakeDispatcher(),
    )
    summary_job = db.get(Job, uuid.UUID(summary_result.data["id"]))
    assert summary_job is not None
    summary_processing = _claim(db, summary_job)
    summary_execution = execute_summary_job(
        db,
        job=summary_job,
        run_id=summary_processing.id,
        provider=FakeAnalysisProvider(
            mock_identity, summary_output=_summary_output(literature.id)
        ),
        storage_backend=MemoryStorage(),
    )
    summary = db.get(EvidenceSetSummary, summary_execution.output_object_id)
    assert summary is not None and summary.status == JobStatus.COMPLETED

    version = _confirmed_question(db, project_id=project.id, actor_id=actor.id)
    recorded_output = _topic_output(literature.id)
    identity = _recorded_identity(recorded_output, provider_id="stage8-recorded-topic")
    topic_result = request_topic_job(
        db,
        actor=actor,
        project_id=project.id,
        payload=TopicGenerationCreate(
            research_question_version_id=version.id,
            evidence_set_summary_id=summary.id,
            candidate_count=3,
        ),
        idempotency_key=str(uuid.uuid4()),
        provider=identity,
        dispatcher=FakeDispatcher(),
    )
    topic_job = db.get(Job, uuid.UUID(topic_result.data["id"]))
    assert topic_job is not None
    topic_processing = _claim(db, topic_job)
    provider_identity = (
        replace(identity, provider_id="substituted-provider")
        if failure_kind == "provider"
        else identity
    )
    provider_output = (
        {
            "candidates": [
                {
                    **candidate,
                    "question_text": f"Changed {candidate['question_text']}",
                }
                for candidate in recorded_output["candidates"]
            ]
        }
        if failure_kind == "recording"
        else recorded_output
    )

    with pytest.raises(EvidenceAnalysisError) as failure:
        execute_topic_job(
            db,
            job=topic_job,
            run_id=topic_processing.id,
            provider=FakeAnalysisProvider(
                provider_identity, topic_output=provider_output
            ),
            storage_backend=MemoryStorage(),
        )

    assert failure.value.code == expected_code
    run = db.get(TopicGenerationRun, topic_job.resource_id)
    assert run is not None and run.status == JobStatus.FAILED
    candidates = db.exec(
        select(TopicCandidate).where(TopicCandidate.topic_generation_run_id == run.id)
    ).all()
    assert candidates == []
    invocation = db.get(ModelInvocation, run.source_model_invocation_id)
    assert invocation is not None
    assert invocation.status == ModelInvocationStatus.FAILED
