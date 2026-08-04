from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.evidence.locator import (
    EvidenceLocatorError,
    EvidenceSourceSnapshot,
    validate_candidate,
)
from app.evidence.schemas import (
    CandidateEvidence,
    EvidenceSetSummaryOutput,
    LiteratureExtractionCandidateOutput,
    TopicGenerationOutput,
)
from app.models import (
    ConfidenceLevel,
    DocumentParseConfidence,
    DocumentParserType,
    FieldEvidenceStatus,
    LiteratureFieldCode,
    LocationVerificationStatus,
    ParserCoverage,
)

pytestmark = pytest.mark.no_database

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


def _source(data: dict[str, Any]) -> EvidenceSourceSnapshot:
    ids = data["ids"]
    document = data["document"]
    coordinates = [box for field in data["fields"] for box in field["bounding_boxes"]]
    return EvidenceSourceSnapshot(
        project_id=uuid.UUID(ids["project_id"]),
        literature_record_id=uuid.UUID(ids["included_literature_id"]),
        document_id=uuid.UUID(ids["document_id"]),
        document_page_id=uuid.UUID(ids["document_page_id"]),
        page_number=document["page_number"],
        page_text=document["page_text"],
        page_width=document["page_width"],
        page_height=document["page_height"],
        page_metadata={"coordinates": coordinates},
        chunk_id=uuid.UUID(ids["chunk_id"]),
        chunk_page_start=document["page_number"],
        chunk_page_end=document["page_number"],
        chunk_content=document["page_text"],
        chunk_section_path=document["section_path"],
        chunk_metadata=None,
        parser_type=DocumentParserType.GROBID,
        parser_version=data["parser_expectations"]["GROBID"]["parser_version"],
        parse_confidence=DocumentParseConfidence.HIGH,
        parser_coverage=ParserCoverage.FULL_TEXT,
    )


def _candidate(
    data: dict[str, Any], field: dict[str, Any], *, include_boxes: bool = True
) -> CandidateEvidence:
    ids = data["ids"]
    return CandidateEvidence(
        candidate_id=uuid.uuid5(uuid.NAMESPACE_URL, field["field_code"]),
        project_id=uuid.UUID(ids["project_id"]),
        literature_record_id=uuid.UUID(ids["included_literature_id"]),
        document_id=uuid.UUID(ids["document_id"]),
        chunk_id=uuid.UUID(ids["chunk_id"]),
        page_number=data["document"]["page_number"],
        source_text=field["source_text"],
        source_text_hash=field["source_text_hash"],
        char_start=field["char_start"],
        char_end=field["char_end"],
        bounding_boxes=field["bounding_boxes"] if include_boxes else [],
    )


def test_golden_manifest_is_synthetic_versioned_and_exactly_ten_fields() -> None:
    data = _fixture()

    assert data["golden_set_version"] == "1.0"
    assert data["fixture_kind"] == "RECA_AUTHORED_SYNTHETIC_ACCEPTANCE_DOCUMENT"
    assert data["is_real_publication"] is False
    assert data["annotation"]["model_output_used_as_truth"] is False
    assert (
        hashlib.sha256(data["document"]["page_text"].encode()).hexdigest()
        == data["document"]["page_text_hash"]
    )
    assert [field["field_code"] for field in data["fields"]] == [
        code.value for code in LiteratureFieldCode
    ]
    authors = next(
        field for field in data["fields"] if field["field_code"] == "AUTHORS"
    )
    assert authors["acceptable_missing"] is True
    assert authors["source_text"] is None


def test_golden_extraction_schema_and_all_real_source_locations() -> None:
    data = _fixture()
    source = _source(data)
    output_fields = []

    for field in data["fields"]:
        candidates = []
        if field["source_text"] is not None:
            candidate = _candidate(data, field)
            located = validate_candidate(
                candidate, source=source, confidence_score=field["confidence"]
            )
            assert located.source_text_hash == field["source_text_hash"]
            assert (located.char_start, located.char_end) == (
                field["char_start"],
                field["char_end"],
            )
            assert located.evidence_status == FieldEvidenceStatus.LOCATED
            candidates = [candidate.model_dump(mode="json")]
        output_fields.append(
            {
                "field_code": field["field_code"],
                "value": {
                    "text": field["expected_text"],
                    "structured": field["expected_structured"],
                },
                "evidence_candidates": candidates,
                "confidence": field["confidence"],
                "requires_human_review": field["confidence"] < 0.95,
                "notes": (
                    ["NO_LOCATED_EVIDENCE: acceptable missing author metadata."]
                    if field["source_text"] is None
                    else []
                ),
            }
        )

    validated = LiteratureExtractionCandidateOutput.model_validate(
        {
            "literature_record_id": data["ids"]["included_literature_id"],
            "document_id": data["ids"]["document_id"],
            "fields": output_fields,
            "document_level_limitations": [
                "Synthetic acceptance material is not scientific ground truth."
            ],
        }
    )
    assert len(validated.fields) == 10
    authors = next(
        field
        for field in validated.fields
        if field.field_code == LiteratureFieldCode.AUTHORS
    )
    assert authors.evidence_candidates == []


@pytest.mark.parametrize(
    ("updates", "expected_code"),
    [
        ({"page_number": 2}, "EVIDENCE_PAGE_MISMATCH"),
        (
            {"project_id": uuid.UUID("99999999-9999-4999-8999-999999999999")},
            "EVIDENCE_PROJECT_MISMATCH",
        ),
        ({"source_text_hash": "0" * 64}, "EVIDENCE_HASH_MISMATCH"),
        (
            {
                "source_text": "A fabricated quotation that is absent from the page.",
                "source_text_hash": hashlib.sha256(
                    b"A fabricated quotation that is absent from the page."
                ).hexdigest(),
                "char_start": None,
                "char_end": None,
            },
            "EVIDENCE_TEXT_NOT_IN_CHUNK",
        ),
    ],
)
def test_golden_locator_rejects_wrong_page_scope_hash_and_fabrication(
    updates: dict[str, object], expected_code: str
) -> None:
    data = _fixture()
    field = next(
        field for field in data["fields"] if field["field_code"] == "SAMPLE_SIZE"
    )
    with pytest.raises(EvidenceLocatorError) as failure:
        validate_candidate(
            _candidate(data, field).model_copy(update=updates),
            source=_source(data),
            confidence_score=field["confidence"],
        )
    assert failure.value.code == expected_code


def test_golden_duplicate_and_pypdf_paths_never_invent_trusted_location() -> None:
    data = _fixture()
    field = next(
        field for field in data["fields"] if field["field_code"] == "SAMPLE_SIZE"
    )
    source = _source(data)
    repeated_text = f"{source.page_text}\n{field['source_text']}"
    ambiguous = validate_candidate(
        _candidate(data, field, include_boxes=False).model_copy(
            update={"char_start": None, "char_end": None}
        ),
        source=replace(source, page_text=repeated_text, chunk_content=repeated_text),
        confidence_score=0.98,
    )
    assert ambiguous.evidence_status == FieldEvidenceStatus.LOCATION_UNCERTAIN
    assert ambiguous.location_status == LocationVerificationStatus.LOCATION_UNCERTAIN

    pypdf_source = replace(
        source,
        parser_type=DocumentParserType.PYPDF,
        parser_version=data["parser_expectations"]["PYPDF"]["parser_version"],
        parse_confidence=DocumentParseConfidence.LOW,
        page_metadata=None,
        chunk_section_path=None,
    )
    degraded = validate_candidate(
        _candidate(data, field, include_boxes=False),
        source=pypdf_source,
        confidence_score=0.99,
    )
    assert degraded.confidence_level == ConfidenceLevel.LOW
    assert degraded.bounding_boxes is None
    assert any("pypdf" in limitation for limitation in degraded.limitations)

    with pytest.raises(EvidenceLocatorError) as failure:
        validate_candidate(
            _candidate(data, field), source=pypdf_source, confidence_score=0.99
        )
    assert failure.value.code == "EVIDENCE_COORDINATES_UNAVAILABLE"


def test_golden_history_included_only_summary_and_exactly_three_topics() -> None:
    data = _fixture()
    included = set(data["summary"]["included_literature_ids"])
    excluded = set(data["summary"]["excluded_literature_ids"])
    assert included.isdisjoint(excluded)
    assert data["correction_history"] == [
        {
            "field_code": "SAMPLE_SIZE",
            "model_value_text": "300",
            "old_value_text": "300",
            "new_value_text": "312",
            "reason": "Human review of the exact page text.",
            "preserve_model_value": True,
        }
    ]
    assert [row["decision"] for row in data["decision_history"]] == [
        "UNCERTAIN",
        "INCLUDED",
    ]
    assert all(
        set(item["literature_record_ids"]) <= included
        and set(item["literature_record_ids"]).isdisjoint(excluded)
        for item in data["summary"]["items"]
    )
    assert any(item["kind"] == "COUNTEREXAMPLE" for item in data["summary"]["items"])

    summary = EvidenceSetSummaryOutput.model_validate(
        {
            "included_literature_ids": list(included),
            "scope_statement": data["summary"]["scope_statement"],
            "consensus_items": [
                {
                    "claim_text": data["summary"]["items"][0]["claim"],
                    "supporting_literature_ids": data["summary"]["items"][0][
                        "literature_record_ids"
                    ],
                    "strength": "MEDIUM",
                    "limitations": [],
                }
            ],
            "counterexamples": [
                {
                    "claim_text": data["summary"]["items"][1]["claim"],
                    "supporting_literature_ids": data["summary"]["items"][1][
                        "literature_record_ids"
                    ],
                    "strength": "LOW",
                    "limitations": data["summary"]["limitations"],
                }
            ],
            "limitations": data["summary"]["limitations"],
        }
    )
    assert summary.counterexamples

    candidates = []
    for candidate in data["topic_candidates"]:
        candidates.append(
            {
                "candidate_order": candidate["candidate_order"],
                "question_text": candidate["question_text"],
                "research_object": "Undergraduate students",
                "variables": {"independent": ["AI use"], "dependent": ["engagement"]},
                "literature_basis": "Bound to the current included synthetic record.",
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
                        "literature_record_id": candidate["source_literature_ids"][0],
                        "relation_type": "BASIS",
                    }
                ],
            }
        )
    validated = TopicGenerationOutput.model_validate({"candidates": candidates})
    assert [candidate.candidate_order for candidate in validated.candidates] == [
        1,
        2,
        3,
    ]
    assert all(
        str(candidate.sources[0].literature_record_id) in included
        for candidate in validated.candidates
    )
    with pytest.raises(ValidationError):
        TopicGenerationOutput.model_validate({"candidates": candidates[:2]})
