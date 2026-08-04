from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.agents.prompts import get_prompt_contract
from app.evidence.analysis import EvidenceAnalysisError, _validate_summary_sources
from app.evidence.schemas import (
    EvidenceSetSummaryInput,
    EvidenceSetSummaryOutput,
    TopicGenerationOutput,
)

pytestmark = pytest.mark.no_database


def _summary_ids() -> tuple[uuid.UUID, uuid.UUID]:
    return uuid.uuid4(), uuid.uuid4()


def _summary_output(
    literature_id: uuid.UUID, *, contradicting: bool = False
) -> EvidenceSetSummaryOutput:
    item = {
        "claim_text": "The current literature set contains differing findings.",
        "supporting_literature_ids": [] if contradicting else [str(literature_id)],
        "contradicting_literature_ids": ([str(literature_id)] if contradicting else []),
        "evidence_span_ids": [],
        "strength": "LOW",
        "limitations": ["This statement is limited to the current literature set."],
    }
    return EvidenceSetSummaryOutput.model_validate(
        {
            "included_literature_ids": [str(literature_id)],
            "scope_statement": "Based on the current set of one included record.",
            "consensus_items": [],
            "controversy_items": [item] if contradicting else [],
            "evidence_gap_items": [],
            "counterexamples": [],
            "method_difference_items": [] if contradicting else [item],
            "sample_difference_items": [],
            "missing_literature": [],
            "missing_information": [],
            "limitations": [],
        }
    )


def _topic_candidate(
    order: int, question: str, literature_id: uuid.UUID
) -> dict[str, object]:
    return {
        "candidate_order": order,
        "question_text": question,
        "research_object": "Undergraduate students",
        "variables": {"independent": ["AI use"], "dependent": ["engagement"]},
        "literature_basis": "Based on the current included literature set.",
        "possible_innovation": "The moderator is less represented in the current set.",
        "data_requirements": {"minimum_fields": ["AI use", "engagement"]},
        "recommended_method": "Correlation analysis",
        "literature_basis_level": "MEDIUM",
        "data_availability": "MEDIUM",
        "method_difficulty": "LOW",
        "time_feasibility": "HIGH",
        "ethical_risk": "LOW",
        "major_risks": [],
        "limitations": ["Cross-sectional data cannot establish causality."],
        "supervisor_confirmation_items": ["Confirm the theoretical model."],
        "sources": [
            {
                "literature_record_id": str(literature_id),
                "evidence_span_id": None,
                "relation_type": "BASIS",
                "explanation": "Current-set literature basis.",
            }
        ],
    }


def test_summary_requires_sources_and_preserves_counterexamples() -> None:
    literature_id, summary_id = _summary_ids()
    summary_input = EvidenceSetSummaryInput.model_validate(
        {
            "summary_id": str(summary_id),
            "project_id": str(uuid.uuid4()),
            "included_literature_ids": [str(literature_id)],
            "summary_types": ["CONTROVERSY"],
            "require_evidence_spans": False,
            "evidence": [],
            "input_limitations": [],
        }
    )
    with pytest.raises(EvidenceAnalysisError) as hidden:
        _validate_summary_sources(
            summary_input=summary_input,
            output=_summary_output(literature_id, contradicting=True),
        )
    assert hidden.value.code == "MODEL_OUTPUT_COUNTEREXAMPLE_HIDDEN"

    with pytest.raises(ValidationError):
        EvidenceSetSummaryOutput.model_validate(
            {
                "included_literature_ids": [str(literature_id)],
                "scope_statement": "Current set only.",
                "consensus_items": [{"claim_text": "Unsupported claim"}],
            }
        )


def test_summary_rejects_universal_gap_language() -> None:
    literature_id, summary_id = _summary_ids()
    summary_input = EvidenceSetSummaryInput.model_validate(
        {
            "summary_id": str(summary_id),
            "project_id": str(uuid.uuid4()),
            "included_literature_ids": [str(literature_id)],
            "summary_types": ["EVIDENCE_GAP"],
            "require_evidence_spans": False,
            "evidence": [],
        }
    )
    output = _summary_output(literature_id)
    output.scope_statement = "学术界完全没有相关研究。"
    with pytest.raises(EvidenceAnalysisError) as unsafe:
        _validate_summary_sources(summary_input=summary_input, output=output)
    assert unsafe.value.code == "MODEL_OUTPUT_UNSAFE_CLAIM"


def test_topic_output_requires_exactly_three_unique_sourced_candidates() -> None:
    literature_id = uuid.uuid4()
    valid = [
        _topic_candidate(order, f"Question {order}", literature_id)
        for order in (1, 2, 3)
    ]
    output = TopicGenerationOutput.model_validate({"candidates": valid})
    assert [candidate.candidate_order for candidate in output.candidates] == [1, 2, 3]

    with pytest.raises(ValidationError):
        TopicGenerationOutput.model_validate({"candidates": valid[:2]})
    with pytest.raises(ValidationError):
        TopicGenerationOutput.model_validate({"candidates": valid + [valid[0]]})

    duplicate = [dict(item) for item in valid]
    duplicate[1]["question_text"] = duplicate[0]["question_text"]
    with pytest.raises(ValidationError):
        TopicGenerationOutput.model_validate({"candidates": duplicate})

    unsourced = [dict(item) for item in valid]
    unsourced[0]["sources"] = []
    with pytest.raises(ValidationError):
        TopicGenerationOutput.model_validate({"candidates": unsourced})


def test_stage4_prompt_contracts_are_registered_and_fail_closed() -> None:
    summary = get_prompt_contract("evidence-set-summary", "1.0.0")
    topic = get_prompt_contract("topic-candidate-generation", "1.0.0")

    assert summary.output_schema.name == "EvidenceSetSummaryOutput"
    assert summary.failure_behavior == "FAIL_CLOSED"
    assert topic.output_schema.name == "TopicGenerationOutput"
    assert topic.failure_behavior == "FAIL_CLOSED"
