from __future__ import annotations

import hashlib
import uuid

import pytest
from pydantic import ValidationError

from app.evidence.schemas import (
    LiteratureExtractionCandidateOutput,
    LiteratureExtractionOutput,
)
from app.models import LiteratureFieldCode

pytestmark = pytest.mark.no_database


def _field(field_code: LiteratureFieldCode) -> dict[str, object]:
    return {
        "field_code": field_code,
        "value": {"text": None, "structured": None},
        "evidence_candidates": [],
        "confidence": 0.2,
        "requires_human_review": True,
        "notes": ["No exact source candidate."],
    }


def _output() -> dict[str, object]:
    return {
        "literature_record_id": uuid.uuid4(),
        "document_id": uuid.uuid4(),
        "fields": [_field(code) for code in LiteratureFieldCode],
        "document_level_limitations": [],
    }


def test_literature_extraction_requires_each_frozen_field_exactly_once() -> None:
    validated = LiteratureExtractionCandidateOutput.model_validate(_output())

    assert [field.field_code for field in validated.fields] == list(LiteratureFieldCode)

    missing = _output()
    missing["fields"] = missing["fields"][:-1]  # type: ignore[index]
    with pytest.raises(ValidationError, match="each frozen field_code exactly once"):
        LiteratureExtractionCandidateOutput.model_validate(missing)

    duplicate = _output()
    fields = duplicate["fields"]  # type: ignore[assignment]
    fields[-1] = fields[0]
    with pytest.raises(ValidationError, match="each frozen field_code exactly once"):
        LiteratureExtractionCandidateOutput.model_validate(duplicate)


def test_candidate_payload_is_strict_and_hash_shaped() -> None:
    payload = _output()
    field = payload["fields"][0]  # type: ignore[index]
    source_text = "Exact source text"
    field["evidence_candidates"] = [  # type: ignore[index]
        {
            "candidate_id": uuid.uuid4(),
            "project_id": uuid.uuid4(),
            "literature_record_id": payload["literature_record_id"],
            "document_id": payload["document_id"],
            "page_number": 1,
            "source_text": source_text,
            "source_text_hash": hashlib.sha256(source_text.encode()).hexdigest(),
            "unexpected": "rejected",
        }
    ]

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        LiteratureExtractionCandidateOutput.model_validate(payload)

    del field["evidence_candidates"][0]["unexpected"]  # type: ignore[index]
    field["evidence_candidates"][0]["source_text_hash"] = "BAD"  # type: ignore[index]
    with pytest.raises(ValidationError, match="String should match pattern"):
        LiteratureExtractionCandidateOutput.model_validate(payload)


def test_candidate_cannot_supply_trusted_span_id_and_resolved_output_can() -> None:
    payload = _output()
    field = payload["fields"][0]  # type: ignore[index]
    field["evidence_span_ids"] = [str(uuid.uuid4())]  # type: ignore[index]
    with pytest.raises(ValidationError, match="evidence_span_ids"):
        LiteratureExtractionCandidateOutput.model_validate(payload)

    candidate_fields = _output()["fields"]  # type: ignore[assignment]
    resolved = {
        **_output(),
        "fields": [
            {
                "field_code": item["field_code"],
                "value": item["value"],
                "evidence_span_ids": [str(uuid.uuid4())] if index == 0 else [],
                "confidence": item["confidence"],
                "requires_human_review": item["requires_human_review"],
                "notes": item["notes"],
            }
            for index, item in enumerate(candidate_fields)
        ],
    }
    validated = LiteratureExtractionOutput.model_validate(resolved)
    assert len(validated.fields[0].evidence_span_ids) == 1
