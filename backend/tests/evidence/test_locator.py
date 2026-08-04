from __future__ import annotations

import hashlib
import uuid
from dataclasses import replace

import pytest

from app.evidence.locator import (
    EvidenceLocatorError,
    EvidenceSourceSnapshot,
    validate_candidate,
)
from app.evidence.schemas import CandidateEvidence, EvidenceBoundingBox
from app.models import (
    ConfidenceLevel,
    DocumentParseConfidence,
    DocumentParserType,
    FieldEvidenceStatus,
    LocationVerificationStatus,
    ParserCoverage,
)

pytestmark = pytest.mark.no_database


def _source(*, text: str = "Before exact evidence after") -> EvidenceSourceSnapshot:
    return EvidenceSourceSnapshot(
        project_id=uuid.uuid4(),
        literature_record_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_page_id=uuid.uuid4(),
        page_number=2,
        page_text=text,
        page_width=600,
        page_height=800,
        page_metadata={
            "coordinates": [
                {"page": 2, "x": 10.0, "y": 20.0, "width": 30.0, "height": 10.0}
            ]
        },
        chunk_id=uuid.uuid4(),
        chunk_page_start=2,
        chunk_page_end=2,
        chunk_content=text,
        chunk_section_path=["Results"],
        chunk_metadata=None,
        parser_type=DocumentParserType.GROBID,
        parser_version="0.8.2",
        parse_confidence=DocumentParseConfidence.HIGH,
        parser_coverage=ParserCoverage.FULL_TEXT,
    )


def _candidate(
    source: EvidenceSourceSnapshot, text: str = "exact evidence"
) -> CandidateEvidence:
    return CandidateEvidence(
        candidate_id=uuid.uuid4(),
        project_id=source.project_id,
        literature_record_id=source.literature_record_id,
        document_id=source.document_id,
        chunk_id=source.chunk_id,
        page_number=source.page_number,
        source_text=text,
        source_text_hash=hashlib.sha256(text.encode()).hexdigest(),
    )


def _assert_code(
    candidate: CandidateEvidence, source: EvidenceSourceSnapshot, code: str
) -> None:
    with pytest.raises(EvidenceLocatorError) as exc_info:
        validate_candidate(candidate, source=source, confidence_score=0.9)
    assert exc_info.value.code == code


def test_exact_page_text_hash_offsets_and_coordinates_form_located_evidence() -> None:
    source = _source()
    candidate = _candidate(source).model_copy(
        update={
            "char_start": 7,
            "char_end": 21,
            "bounding_boxes": [
                EvidenceBoundingBox(page=2, x=10, y=20, width=30, height=10)
            ],
        }
    )

    located = validate_candidate(candidate, source=source, confidence_score=0.9)

    assert located.source_text == "exact evidence"
    assert located.source_text_hash == hashlib.sha256(b"exact evidence").hexdigest()
    assert (located.char_start, located.char_end) == (7, 21)
    assert located.evidence_status == FieldEvidenceStatus.LOCATED
    assert located.location_status == LocationVerificationStatus.LOCATED
    assert located.confidence_level == ConfidenceLevel.HIGH
    assert located.bounding_boxes is not None


@pytest.mark.parametrize(
    ("updates", "code"),
    [
        ({"project_id": uuid.uuid4()}, "EVIDENCE_PROJECT_MISMATCH"),
        ({"document_id": uuid.uuid4()}, "EVIDENCE_DOCUMENT_MISMATCH"),
        ({"page_number": 3}, "EVIDENCE_PAGE_MISMATCH"),
        ({"chunk_id": uuid.uuid4()}, "EVIDENCE_CHUNK_MISMATCH"),
        ({"source_text_hash": "0" * 64}, "EVIDENCE_HASH_MISMATCH"),
        ({"char_start": 0, "char_end": 14}, "EVIDENCE_OFFSET_MISMATCH"),
        ({"char_start": 7, "char_end": 999}, "EVIDENCE_OFFSET_OUT_OF_BOUNDS"),
    ],
)
def test_locator_rejects_scope_hash_and_offset_mismatches(
    updates: dict[str, object], code: str
) -> None:
    source = _source()
    _assert_code(_candidate(source).model_copy(update=updates), source, code)


def test_fabricated_text_is_rejected_and_duplicate_text_is_uncertain() -> None:
    source = _source(text="same evidence then same evidence")
    fabricated = _candidate(source, "invented evidence")
    _assert_code(fabricated, source, "EVIDENCE_TEXT_NOT_IN_CHUNK")

    duplicate = _candidate(source, "same evidence")
    located = validate_candidate(duplicate, source=source, confidence_score=0.8)
    assert located.evidence_status == FieldEvidenceStatus.LOCATION_UNCERTAIN
    assert located.location_status == LocationVerificationStatus.LOCATION_UNCERTAIN
    assert located.char_start is None and located.char_end is None
    assert located.limitations


def test_pypdf_never_claims_coordinates_sections_or_high_confidence() -> None:
    source = replace(
        _source(),
        parser_type=DocumentParserType.PYPDF,
        parse_confidence=DocumentParseConfidence.HIGH,
        page_metadata=None,
        chunk_section_path=None,
    )
    located = validate_candidate(
        _candidate(source), source=source, confidence_score=0.99
    )
    assert located.confidence_level == ConfidenceLevel.LOW
    assert located.bounding_boxes is None
    assert any("pypdf" in limitation for limitation in located.limitations)

    with_box = _candidate(source).model_copy(
        update={
            "bounding_boxes": [
                EvidenceBoundingBox(page=2, x=10, y=20, width=30, height=10)
            ]
        }
    )
    _assert_code(with_box, source, "EVIDENCE_COORDINATES_UNAVAILABLE")
