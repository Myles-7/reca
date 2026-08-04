from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint, UniqueConstraint

from app.models import (
    EvidenceSpan,
    EvidenceSpanVerificationRecord,
    FieldEvidenceStatus,
    LiteratureDecision,
    LiteratureExtraction,
    LiteratureExtractionField,
    LiteratureExtractionFieldRevision,
    LiteratureFieldCode,
    ParserCoverage,
    TopicCandidate,
    TopicCandidateEvidence,
    TopicGenerationRun,
    UserDeclaredReadScope,
)

pytestmark = pytest.mark.no_database


def _constraint_names(model: type[object], kind: type[object]) -> set[str]:
    return {
        constraint.name
        for constraint in model.__table__.constraints  # type: ignore[attr-defined]
        if isinstance(constraint, kind) and constraint.name is not None
    }


def _foreign_key_names(model: type[object]) -> set[str]:
    return {
        constraint.name
        for constraint in model.__table__.foreign_key_constraints  # type: ignore[attr-defined]
        if constraint.name is not None
    }


def test_m3_metadata_registers_frozen_entities_and_enums() -> None:
    assert [value.value for value in LiteratureFieldCode] == [
        "TITLE",
        "AUTHORS",
        "YEAR",
        "RESEARCH_OBJECT",
        "SAMPLE_SIZE",
        "CORE_VARIABLES",
        "RESEARCH_DESIGN",
        "ANALYSIS_METHOD",
        "MAIN_CONCLUSION",
        "LIMITATION",
    ]
    assert FieldEvidenceStatus.NO_LOCATED_EVIDENCE.value == "NO_LOCATED_EVIDENCE"
    assert set(ParserCoverage) == {
        ParserCoverage.UNKNOWN,
        ParserCoverage.PARTIAL_TEXT,
        ParserCoverage.FULL_TEXT,
    }
    assert UserDeclaredReadScope.FULL_TEXT_DECLARED.value == "FULL_TEXT_DECLARED"
    assert ParserCoverage.__name__ != UserDeclaredReadScope.__name__

    assert {
        LiteratureExtraction.__tablename__,
        LiteratureExtractionField.__tablename__,
        EvidenceSpan.__tablename__,
        LiteratureDecision.__tablename__,
        TopicGenerationRun.__tablename__,
        TopicCandidate.__tablename__,
        LiteratureExtractionFieldRevision.__tablename__,
        EvidenceSpanVerificationRecord.__tablename__,
        TopicCandidateEvidence.__tablename__,
    } == {
        "literature_extractions",
        "literature_extraction_fields",
        "evidence_spans",
        "literature_decisions",
        "topic_generation_runs",
        "topic_candidates",
        "literature_extraction_field_revisions",
        "evidence_span_verification_records",
        "topic_candidate_evidence",
    }


def test_m3_metadata_preserves_scope_history_and_evidence_constraints() -> None:
    assert "fk_literature_extractions_record_document_project" in _foreign_key_names(
        LiteratureExtraction
    )
    assert {
        "fk_evidence_spans_document_project",
        "fk_evidence_spans_page_document_project",
        "fk_evidence_spans_chunk_document_project",
    } <= _foreign_key_names(EvidenceSpan)
    assert "fk_extraction_fields_span_project" in _foreign_key_names(
        LiteratureExtractionField
    )
    assert "fk_literature_decisions_supersedes_scope" in _foreign_key_names(
        LiteratureDecision
    )
    assert "fk_topic_candidate_evidence_span_project" in _foreign_key_names(
        TopicCandidateEvidence
    )

    assert "uq_extraction_fields_code" in _constraint_names(
        LiteratureExtractionField, UniqueConstraint
    )
    assert "uq_field_revisions_number" in _constraint_names(
        LiteratureExtractionFieldRevision, UniqueConstraint
    )
    assert "uq_literature_decisions_successor" in _constraint_names(
        LiteratureDecision, UniqueConstraint
    )
    assert "uq_topic_candidates_run_order" in _constraint_names(
        TopicCandidate, UniqueConstraint
    )

    assert {
        "ck_evidence_spans_page_positive",
        "ck_evidence_spans_source_hash",
        "ck_evidence_spans_char_range",
        "ck_evidence_spans_boxes_array",
    } <= _constraint_names(EvidenceSpan, CheckConstraint)
    assert {
        "ck_extraction_fields_located_span",
        "ck_extraction_fields_no_evidence_span",
        "ck_extraction_fields_evidence_limitations",
    } <= _constraint_names(LiteratureExtractionField, CheckConstraint)
    assert "ck_topic_candidate_evidence_one_source" in _constraint_names(
        TopicCandidateEvidence, CheckConstraint
    )


def test_m3_migration_declares_database_guards() -> None:
    root = Path(__file__).resolve().parents[3]
    migration = (
        root / "backend/app/alembic/versions/0013_m3_evidence_matrix.py"
    ).read_text(encoding="utf-8")

    assert 'revision = "0013_m3_evidence_matrix"' in migration
    assert 'down_revision = "0012_document_upload"' in migration
    assert "TOPIC_GENERATE" in migration
    assert "m3_append_only_guard" in migration
    assert "m3_immutable_evidence_source_guard" in migration
    assert "m3_verification_record_guard" in migration
    assert "m3_verified_projection_guard" in migration
    assert "m3_immutable_model_field_guard" in migration
    assert "m3_topic_run_completion_guard" in migration
    assert "exactly three sourced candidates" in migration
    assert "fk_literature_extractions_record_document_project" in migration
    assert "ck_topic_candidate_evidence_one_source" in migration
