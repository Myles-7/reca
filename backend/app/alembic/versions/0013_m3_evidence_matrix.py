"""Add M3 evidence matrix domain persistence.

Revision ID: 0013_m3_evidence_matrix
Revises: 0012_document_upload
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from typing import Any

revision = "0013_m3_evidence_matrix"
down_revision = "0012_document_upload"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PREVIOUS_JOB_VALUES = (
    "RESEARCH_QUESTION_SCOPING",
    "QUERY_PLAN_GENERATION",
    "DOCUMENT_PARSE",
    "LITERATURE_SEARCH",
    "LITERATURE_EXTRACT",
    "DOCUMENT_EMBED",
    "LITERATURE_SUMMARIZE",
    "DATASET_PROFILE",
    "DATASET_TRANSFORM",
    "ANALYSIS_RUN",
    "FIGURE_RENDER",
    "MANUSCRIPT_CHECK",
    "EVIDENCE_AUDIT",
    "REPRO_PACKAGE_EXPORT",
)

_ENUMS = {
    "literature_field_code": (
        "TITLE", "AUTHORS", "YEAR", "RESEARCH_OBJECT", "SAMPLE_SIZE",
        "CORE_VARIABLES", "RESEARCH_DESIGN", "ANALYSIS_METHOD",
        "MAIN_CONCLUSION", "LIMITATION",
    ),
    "confidence_level": ("HIGH", "MEDIUM", "LOW", "UNKNOWN"),
    "literature_extraction_status": (
        "DRAFT", "EXTRACTING", "NEEDS_REVIEW", "CONFIRMED",
        "SUPERSEDED", "INVALIDATED", "FAILED",
    ),
    "field_confirmation_status": ("UNREVIEWED", "CONFIRMED", "REJECTED"),
    "field_evidence_status": (
        "UNASSESSED", "LOCATED", "LOCATION_UNCERTAIN", "NO_LOCATED_EVIDENCE",
    ),
    "evidence_type": (
        "FIELD_SUPPORT", "CLAIM_SUPPORT", "CLAIM_CONTRADICTION",
        "METHOD_DESCRIPTION", "SAMPLE_DESCRIPTION", "LIMITATION", "OTHER",
    ),
    "location_verification_status": (
        "EXTRACTED", "LOCATED", "VERIFIED", "LOCATION_UNCERTAIN",
    ),
    "evidence_review_status": ("UNREVIEWED", "REVIEWED", "CONFIRMED", "REJECTED"),
    "parser_coverage": ("UNKNOWN", "PARTIAL_TEXT", "FULL_TEXT"),
    "user_declared_read_scope": (
        "UNKNOWN", "ABSTRACT", "SECTIONS", "FULL_TEXT_DECLARED",
    ),
    "literature_decision_reason": (
        "RELEVANT_OBJECT_AND_METHOD", "OBJECT_MISMATCH", "VARIABLE_MISMATCH",
        "METHOD_MISMATCH", "TYPE_MISMATCH", "YEAR_MISMATCH", "DUPLICATE",
        "FULL_TEXT_UNAVAILABLE", "QUALITY_ISSUE", "OTHER",
    ),
    "topic_candidate_status": (
        "PROPOSED", "SHORTLISTED", "ADOPTED", "REJECTED", "EXPIRED",
    ),
    "topic_evidence_relation": ("BASIS", "SUPPORT", "CONTRADICTION", "LIMITATION"),
}


def _enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(name=name, create_type=False)


def _timestamps(*, updated: bool = False) -> list[sa.Column[Any]]:
    columns: list[sa.Column[Any]] = [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)
    ]
    if updated:
        columns.append(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    return columns


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE job_task_type "
            "ADD VALUE IF NOT EXISTS 'TOPIC_GENERATE' AFTER 'LITERATURE_SUMMARIZE'"
        )

    bind = op.get_bind()
    for name, values in _ENUMS.items():
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)

    op.create_unique_constraint(
        "uq_literature_records_id_project_document",
        "literature_records",
        ["id", "project_id", "document_id"],
    )
    op.create_unique_constraint(
        "uq_document_pages_id_document_project_number",
        "document_pages",
        ["id", "document_id", "project_id", "page_number"],
    )
    op.create_unique_constraint(
        "uq_document_chunks_id_document_project",
        "document_chunks",
        ["id", "document_id", "project_id"],
    )
    op.create_unique_constraint("uq_jobs_id_project", "jobs", ["id", "project_id"])
    op.create_unique_constraint(
        "uq_processing_runs_id_project", "processing_runs", ["id", "project_id"]
    )

    op.create_table(
        "literature_extractions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("literature_record_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("extraction_version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=50), nullable=False),
        sa.Column("status", _enum("literature_extraction_status"), nullable=False),
        sa.Column("overall_confidence", _enum("confidence_level"), nullable=True),
        sa.Column("source_model_invocation_id", sa.Uuid(), nullable=True),
        sa.Column("processing_run_id", sa.Uuid(), nullable=True),
        sa.Column("document_level_limitations", postgresql.JSONB(), nullable=True),
        sa.Column("lock_version", sa.Integer(), nullable=False),
        *_timestamps(updated=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("extraction_version >= 1", name="ck_literature_extractions_version_positive"),
        sa.CheckConstraint("lock_version >= 1", name="ck_literature_extractions_lock"),
        sa.ForeignKeyConstraint(
            ["literature_record_id", "project_id", "document_id"],
            ["literature_records.id", "literature_records.project_id", "literature_records.document_id"],
            name="fk_literature_extractions_record_document_project", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_model_invocation_id", "project_id"],
            ["model_invocations.id", "model_invocations.project_id"],
            name="fk_literature_extractions_model_project", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["processing_run_id", "project_id"],
            ["processing_runs.id", "processing_runs.project_id"],
            name="fk_literature_extractions_run_project", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_literature_extractions"),
        sa.UniqueConstraint("id", "project_id", name="uq_literature_extractions_scope"),
        sa.UniqueConstraint("literature_record_id", "extraction_version", name="uq_literature_extractions_record_version"),
    )
    for column in ("project_id", "literature_record_id", "document_id", "source_model_invocation_id", "processing_run_id"):
        op.create_index(f"ix_literature_extractions_{column}", "literature_extractions", [column])
    op.create_index("ix_literature_extractions_project_status", "literature_extractions", ["project_id", "status"])
    op.create_index("ix_literature_extractions_record_created", "literature_extractions", ["literature_record_id", "created_at"])

    op.create_table(
        "evidence_spans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("document_page_id", sa.Uuid(), nullable=True),
        sa.Column("chunk_id", sa.Uuid(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("section_path", postgresql.JSONB(), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("context_before", sa.Text(), nullable=True),
        sa.Column("context_after", sa.Text(), nullable=True),
        sa.Column("bounding_boxes", postgresql.JSONB(), nullable=True),
        sa.Column("char_start", sa.Integer(), nullable=True),
        sa.Column("char_end", sa.Integer(), nullable=True),
        sa.Column("evidence_type", _enum("evidence_type"), nullable=False),
        sa.Column("confidence_level", _enum("confidence_level"), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("parser_type", _enum("document_parser_type"), nullable=True),
        sa.Column("parser_version", sa.String(length=100), nullable=True),
        sa.Column("model_invocation_id", sa.Uuid(), nullable=True),
        sa.Column("source_text_hash", sa.String(length=64), nullable=False),
        sa.Column("location_verification_status", _enum("location_verification_status"), nullable=False),
        sa.Column("review_status", _enum("evidence_review_status"), nullable=False),
        sa.Column("parser_coverage", _enum("parser_coverage"), nullable=False),
        sa.Column("user_declared_read_scope", _enum("user_declared_read_scope"), nullable=False),
        sa.Column("reviewed_by_actor_type", _enum("audit_actor_type"), nullable=True),
        sa.Column("reviewed_by_actor_id", sa.String(length=255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by_actor_id", sa.String(length=255), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("page_number >= 1", name="ck_evidence_spans_page_positive"),
        sa.CheckConstraint("length(source_text) > 0", name="ck_evidence_spans_source_nonempty"),
        sa.CheckConstraint("source_text_hash ~ '^[0-9a-f]{64}$'", name="ck_evidence_spans_source_hash"),
        sa.CheckConstraint("(char_start IS NULL AND char_end IS NULL) OR (char_start >= 0 AND char_end > char_start)", name="ck_evidence_spans_char_range"),
        sa.CheckConstraint("confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1", name="ck_evidence_spans_confidence"),
        sa.CheckConstraint("bounding_boxes IS NULL OR jsonb_typeof(bounding_boxes) = 'array'", name="ck_evidence_spans_boxes_array"),
        sa.ForeignKeyConstraint(["document_id", "project_id"], ["documents.id", "documents.project_id"], name="fk_evidence_spans_document_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_page_id", "document_id", "project_id", "page_number"], ["document_pages.id", "document_pages.document_id", "document_pages.project_id", "document_pages.page_number"], name="fk_evidence_spans_page_document_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["chunk_id", "document_id", "project_id"], ["document_chunks.id", "document_chunks.document_id", "document_chunks.project_id"], name="fk_evidence_spans_chunk_document_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["model_invocation_id", "project_id"], ["model_invocations.id", "model_invocations.project_id"], name="fk_evidence_spans_model_project", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_evidence_spans"),
        sa.UniqueConstraint("id", "project_id", name="uq_evidence_spans_scope"),
    )
    for column in ("project_id", "document_id", "document_page_id", "chunk_id", "model_invocation_id"):
        op.create_index(f"ix_evidence_spans_{column}", "evidence_spans", [column])
    op.create_index("ix_evidence_spans_project_document", "evidence_spans", ["project_id", "document_id"])
    op.create_index("ix_evidence_spans_document_page", "evidence_spans", ["document_id", "page_number"])

    op.create_table(
        "literature_extraction_fields",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("extraction_id", sa.Uuid(), nullable=False), sa.Column("field_code", _enum("literature_field_code"), nullable=False),
        sa.Column("model_value_text", sa.Text(), nullable=True), sa.Column("model_value_json", postgresql.JSONB(), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True), sa.Column("value_json", postgresql.JSONB(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True), sa.Column("confidence_level", _enum("confidence_level"), nullable=False),
        sa.Column("evidence_span_id", sa.Uuid(), nullable=True), sa.Column("confirmation_status", _enum("field_confirmation_status"), nullable=False),
        sa.Column("evidence_status", _enum("field_evidence_status"), nullable=False), sa.Column("evidence_limitations", sa.Text(), nullable=True),
        sa.Column("corrected_by_user_id", sa.Uuid(), nullable=True), sa.Column("correction_reason", sa.Text(), nullable=True),
        sa.Column("lock_version", sa.Integer(), nullable=False), *_timestamps(updated=True),
        sa.CheckConstraint("lock_version >= 1", name="ck_extraction_fields_lock"),
        sa.CheckConstraint("confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1", name="ck_extraction_fields_confidence"),
        sa.CheckConstraint("(evidence_status IN ('LOCATED', 'LOCATION_UNCERTAIN') AND evidence_span_id IS NOT NULL) OR (evidence_status NOT IN ('LOCATED', 'LOCATION_UNCERTAIN'))", name="ck_extraction_fields_located_span"),
        sa.CheckConstraint("evidence_status <> 'NO_LOCATED_EVIDENCE' OR evidence_span_id IS NULL", name="ck_extraction_fields_no_evidence_span"),
        sa.CheckConstraint("evidence_status NOT IN ('LOCATION_UNCERTAIN', 'NO_LOCATED_EVIDENCE') OR (evidence_limitations IS NOT NULL AND length(evidence_limitations) > 0)", name="ck_extraction_fields_evidence_limitations"),
        sa.ForeignKeyConstraint(["extraction_id", "project_id"], ["literature_extractions.id", "literature_extractions.project_id"], name="fk_extraction_fields_extraction_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evidence_span_id", "project_id"], ["evidence_spans.id", "evidence_spans.project_id"], name="fk_extraction_fields_span_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["corrected_by_user_id"], ["user.id"], name="fk_extraction_fields_corrector", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_literature_extraction_fields"),
        sa.UniqueConstraint("id", "project_id", name="uq_extraction_fields_scope"),
        sa.UniqueConstraint("extraction_id", "field_code", name="uq_extraction_fields_code"),
    )
    for column in ("project_id", "extraction_id", "evidence_span_id", "corrected_by_user_id"):
        op.create_index(f"ix_literature_extraction_fields_{column}", "literature_extraction_fields", [column])
    op.create_index("ix_extraction_fields_project_code", "literature_extraction_fields", ["project_id", "field_code"])

    op.create_table(
        "literature_extraction_field_revisions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("field_id", sa.Uuid(), nullable=False), sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("old_value_text", sa.Text(), nullable=True), sa.Column("old_value_json", postgresql.JSONB(), nullable=True),
        sa.Column("new_value_text", sa.Text(), nullable=True), sa.Column("new_value_json", postgresql.JSONB(), nullable=True),
        sa.Column("old_evidence_span_id", sa.Uuid(), nullable=True), sa.Column("new_evidence_span_id", sa.Uuid(), nullable=True),
        sa.Column("old_confirmation_status", _enum("field_confirmation_status"), nullable=False), sa.Column("new_confirmation_status", _enum("field_confirmation_status"), nullable=False),
        sa.Column("old_evidence_status", _enum("field_evidence_status"), nullable=False), sa.Column("new_evidence_status", _enum("field_evidence_status"), nullable=False),
        sa.Column("corrected_by_user_id", sa.Uuid(), nullable=False), sa.Column("correction_reason", sa.Text(), nullable=False),
        sa.Column("source_model_invocation_id", sa.Uuid(), nullable=True), sa.Column("ai_schema_version", sa.String(length=50), nullable=True), *_timestamps(),
        sa.CheckConstraint("revision_number >= 1", name="ck_field_revisions_number"),
        sa.ForeignKeyConstraint(["field_id", "project_id"], ["literature_extraction_fields.id", "literature_extraction_fields.project_id"], name="fk_field_revisions_field_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["old_evidence_span_id", "project_id"], ["evidence_spans.id", "evidence_spans.project_id"], name="fk_field_revisions_old_span_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["new_evidence_span_id", "project_id"], ["evidence_spans.id", "evidence_spans.project_id"], name="fk_field_revisions_new_span_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_model_invocation_id", "project_id"], ["model_invocations.id", "model_invocations.project_id"], name="fk_field_revisions_model_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["corrected_by_user_id"], ["user.id"], name="fk_field_revisions_corrector", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_literature_extraction_field_revisions"),
        sa.UniqueConstraint("field_id", "revision_number", name="uq_field_revisions_number"),
    )
    for name, column in (
        ("ix_field_revisions_project", "project_id"),
        ("ix_field_revisions_old_span", "old_evidence_span_id"),
        ("ix_field_revisions_new_span", "new_evidence_span_id"),
        ("ix_field_revisions_corrector", "corrected_by_user_id"),
        ("ix_field_revisions_model", "source_model_invocation_id"),
    ):
        op.create_index(name, "literature_extraction_field_revisions", [column])
    op.create_index("ix_field_revisions_field_created", "literature_extraction_field_revisions", ["field_id", "created_at"])

    op.create_table(
        "evidence_span_verification_records",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_span_id", sa.Uuid(), nullable=False), sa.Column("actor_type", _enum("audit_actor_type"), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=False), sa.Column("location_verification_status", _enum("location_verification_status"), nullable=False),
        sa.Column("user_declared_read_scope", _enum("user_declared_read_scope"), nullable=False), sa.Column("reviewed_page_numbers", postgresql.JSONB(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True), sa.Column("source_text_hash", sa.String(length=64), nullable=False), *_timestamps(),
        sa.CheckConstraint("source_text_hash ~ '^[0-9a-f]{64}$'", name="ck_span_verifications_source_hash"),
        sa.CheckConstraint("jsonb_typeof(reviewed_page_numbers) = 'array'", name="ck_span_verifications_pages_array"),
        sa.CheckConstraint("location_verification_status <> 'VERIFIED' OR jsonb_array_length(reviewed_page_numbers) > 0", name="ck_span_verifications_verified_pages"),
        sa.ForeignKeyConstraint(["evidence_span_id", "project_id"], ["evidence_spans.id", "evidence_spans.project_id"], name="fk_span_verifications_span_project", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_evidence_span_verification_records"),
    )
    for column in ("project_id", "evidence_span_id"):
        op.create_index(f"ix_evidence_span_verification_records_{column}", "evidence_span_verification_records", [column])
    op.create_index("ix_span_verifications_span_created", "evidence_span_verification_records", ["evidence_span_id", "created_at"])

    op.create_table(
        "literature_decisions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("literature_record_id", sa.Uuid(), nullable=False), sa.Column("decision", _enum("literature_decision_status"), nullable=False),
        sa.Column("reason_code", _enum("literature_decision_reason"), nullable=True), sa.Column("reason_text", sa.Text(), nullable=True),
        sa.Column("ai_recommendation", _enum("literature_decision_status"), nullable=True), sa.Column("ai_score", sa.Float(), nullable=True),
        sa.Column("decided_by_user_id", sa.Uuid(), nullable=False), sa.Column("supersedes_decision_id", sa.Uuid(), nullable=True), *_timestamps(),
        sa.CheckConstraint("ai_score IS NULL OR ai_score BETWEEN 0 AND 1", name="ck_literature_decisions_ai_score"),
        sa.ForeignKeyConstraint(["literature_record_id", "project_id"], ["literature_records.id", "literature_records.project_id"], name="fk_literature_decisions_record_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["supersedes_decision_id", "project_id", "literature_record_id"], ["literature_decisions.id", "literature_decisions.project_id", "literature_decisions.literature_record_id"], name="fk_literature_decisions_supersedes_scope", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["decided_by_user_id"], ["user.id"], name="fk_literature_decisions_user", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_literature_decisions"),
        sa.UniqueConstraint("id", "project_id", "literature_record_id", name="uq_literature_decisions_scope"),
        sa.UniqueConstraint("supersedes_decision_id", name="uq_literature_decisions_successor"),
    )
    for column in ("project_id", "literature_record_id", "decided_by_user_id", "supersedes_decision_id"):
        op.create_index(f"ix_literature_decisions_{column}", "literature_decisions", [column])
    op.create_index("ix_literature_decisions_record_created", "literature_decisions", ["literature_record_id", "created_at"])
    op.create_index("uq_literature_decisions_initial", "literature_decisions", ["project_id", "literature_record_id"], unique=True, postgresql_where=sa.text("supersedes_decision_id IS NULL"))

    op.create_table(
        "evidence_set_summaries",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("included_literature_ids", postgresql.JSONB(), nullable=False), sa.Column("scope_statement", sa.Text(), nullable=False),
        sa.Column("result_payload", postgresql.JSONB(), nullable=False), sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("processing_run_id", sa.Uuid(), nullable=True), sa.Column("source_model_invocation_id", sa.Uuid(), nullable=True),
        sa.Column("status", _enum("job_status"), nullable=False), *_timestamps(),
        sa.CheckConstraint("jsonb_typeof(included_literature_ids) = 'array'", name="ck_evidence_summaries_literature_array"),
        sa.CheckConstraint("jsonb_typeof(result_payload) = 'object'", name="ck_evidence_summaries_result_object"),
        sa.ForeignKeyConstraint(["job_id", "project_id"], ["jobs.id", "jobs.project_id"], name="fk_evidence_summaries_job_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["processing_run_id", "project_id"], ["processing_runs.id", "processing_runs.project_id"], name="fk_evidence_summaries_run_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_model_invocation_id", "project_id"], ["model_invocations.id", "model_invocations.project_id"], name="fk_evidence_summaries_model_project", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_evidence_set_summaries"),
        sa.UniqueConstraint("id", "project_id", name="uq_evidence_set_summaries_scope"),
    )
    for column in ("project_id", "job_id", "processing_run_id", "source_model_invocation_id"):
        op.create_index(f"ix_evidence_set_summaries_{column}", "evidence_set_summaries", [column])
    op.create_index("ix_evidence_summaries_project_created", "evidence_set_summaries", ["project_id", "created_at"])

    op.create_table(
        "topic_generation_runs",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("research_question_version_id", sa.Uuid(), nullable=False), sa.Column("evidence_summary_id", sa.Uuid(), nullable=True),
        sa.Column("user_constraints", postgresql.JSONB(), nullable=True), sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("processing_run_id", sa.Uuid(), nullable=True), sa.Column("source_model_invocation_id", sa.Uuid(), nullable=True),
        sa.Column("status", _enum("job_status"), nullable=False), *_timestamps(),
        sa.ForeignKeyConstraint(["research_question_version_id", "project_id"], ["research_question_versions.id", "research_question_versions.project_id"], name="fk_topic_runs_rq_version_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evidence_summary_id", "project_id"], ["evidence_set_summaries.id", "evidence_set_summaries.project_id"], name="fk_topic_runs_summary_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["job_id", "project_id"], ["jobs.id", "jobs.project_id"], name="fk_topic_runs_job_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["processing_run_id", "project_id"], ["processing_runs.id", "processing_runs.project_id"], name="fk_topic_runs_processing_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_model_invocation_id", "project_id"], ["model_invocations.id", "model_invocations.project_id"], name="fk_topic_runs_model_project", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_topic_generation_runs"),
        sa.UniqueConstraint("id", "project_id", name="uq_topic_generation_runs_scope"),
    )
    for column in ("project_id", "research_question_version_id", "evidence_summary_id", "job_id", "processing_run_id", "source_model_invocation_id"):
        op.create_index(f"ix_topic_generation_runs_{column}", "topic_generation_runs", [column])
    op.create_index("ix_topic_runs_project_status", "topic_generation_runs", ["project_id", "status"])

    op.create_table(
        "topic_candidates",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("topic_generation_run_id", sa.Uuid(), nullable=False), sa.Column("candidate_order", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False), sa.Column("research_object", sa.Text(), nullable=True),
        sa.Column("variables", postgresql.JSONB(), nullable=True), sa.Column("research_goal", sa.String(length=100), nullable=True),
        sa.Column("literature_basis", sa.Text(), nullable=True), sa.Column("possible_innovation", sa.Text(), nullable=True),
        sa.Column("data_requirements", postgresql.JSONB(), nullable=True), sa.Column("recommended_method", sa.Text(), nullable=True),
        sa.Column("literature_basis_level", _enum("confidence_level"), nullable=True), sa.Column("data_availability", _enum("confidence_level"), nullable=True),
        sa.Column("method_difficulty", _enum("confidence_level"), nullable=True), sa.Column("time_feasibility", _enum("confidence_level"), nullable=True),
        sa.Column("ethical_risk", _enum("confidence_level"), nullable=True), sa.Column("major_risks", postgresql.JSONB(), nullable=True),
        sa.Column("limitations", postgresql.JSONB(), nullable=False),
        sa.Column("supervisor_confirmation_items", postgresql.JSONB(), nullable=True), sa.Column("status", _enum("topic_candidate_status"), nullable=False), *_timestamps(),
        sa.CheckConstraint("candidate_order BETWEEN 1 AND 3", name="ck_topic_candidates_order"),
        sa.CheckConstraint("length(question_text) > 0", name="ck_topic_candidates_question_nonempty"),
        sa.ForeignKeyConstraint(["topic_generation_run_id", "project_id"], ["topic_generation_runs.id", "topic_generation_runs.project_id"], name="fk_topic_candidates_run_project", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_topic_candidates"),
        sa.UniqueConstraint("id", "project_id", name="uq_topic_candidates_scope"),
        sa.UniqueConstraint("topic_generation_run_id", "candidate_order", name="uq_topic_candidates_run_order"),
    )
    for column in ("project_id", "topic_generation_run_id"):
        op.create_index(f"ix_topic_candidates_{column}", "topic_candidates", [column])
    op.create_index("ix_topic_candidates_project_status", "topic_candidates", ["project_id", "status"])

    op.create_table(
        "topic_candidate_evidence",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("topic_candidate_id", sa.Uuid(), nullable=False), sa.Column("literature_record_id", sa.Uuid(), nullable=True),
        sa.Column("evidence_span_id", sa.Uuid(), nullable=True), sa.Column("relation_type", _enum("topic_evidence_relation"), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True), *_timestamps(),
        sa.CheckConstraint("(literature_record_id IS NOT NULL)::integer + (evidence_span_id IS NOT NULL)::integer = 1", name="ck_topic_candidate_evidence_one_source"),
        sa.ForeignKeyConstraint(["topic_candidate_id", "project_id"], ["topic_candidates.id", "topic_candidates.project_id"], name="fk_topic_candidate_evidence_candidate_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["literature_record_id", "project_id"], ["literature_records.id", "literature_records.project_id"], name="fk_topic_candidate_evidence_record_project", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evidence_span_id", "project_id"], ["evidence_spans.id", "evidence_spans.project_id"], name="fk_topic_candidate_evidence_span_project", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_topic_candidate_evidence"),
    )
    for column in ("project_id", "topic_candidate_id", "literature_record_id", "evidence_span_id"):
        op.create_index(f"ix_topic_candidate_evidence_{column}", "topic_candidate_evidence", [column])
    op.create_index("ix_topic_candidate_evidence_candidate", "topic_candidate_evidence", ["topic_candidate_id"])
    op.create_index("uq_topic_candidate_evidence_record", "topic_candidate_evidence", ["topic_candidate_id", "literature_record_id", "relation_type"], unique=True, postgresql_where=sa.text("literature_record_id IS NOT NULL"))
    op.create_index("uq_topic_candidate_evidence_span", "topic_candidate_evidence", ["topic_candidate_id", "evidence_span_id", "relation_type"], unique=True, postgresql_where=sa.text("evidence_span_id IS NOT NULL"))

    op.execute("""
        CREATE FUNCTION m3_append_only_guard() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION '% is append-only', TG_TABLE_NAME;
        END;
        $$ LANGUAGE plpgsql
    """)
    for table in (
        "literature_extraction_field_revisions",
        "evidence_span_verification_records",
        "literature_decisions",
    ):
        op.execute(
            f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION m3_append_only_guard()"
        )

    op.execute("""
        CREATE FUNCTION m3_immutable_evidence_source_guard() RETURNS trigger AS $$
        BEGIN
            IF NEW.project_id IS DISTINCT FROM OLD.project_id
               OR NEW.document_id IS DISTINCT FROM OLD.document_id
               OR NEW.document_page_id IS DISTINCT FROM OLD.document_page_id
               OR NEW.chunk_id IS DISTINCT FROM OLD.chunk_id
               OR NEW.page_number IS DISTINCT FROM OLD.page_number
               OR NEW.source_text IS DISTINCT FROM OLD.source_text
               OR NEW.source_text_hash IS DISTINCT FROM OLD.source_text_hash
               OR NEW.char_start IS DISTINCT FROM OLD.char_start
               OR NEW.char_end IS DISTINCT FROM OLD.char_end
               OR NEW.bounding_boxes IS DISTINCT FROM OLD.bounding_boxes THEN
                RAISE EXCEPTION 'EvidenceSpan source and location are immutable';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER evidence_spans_source_immutable BEFORE UPDATE ON evidence_spans FOR EACH ROW EXECUTE FUNCTION m3_immutable_evidence_source_guard()")

    op.execute("""
        CREATE FUNCTION m3_verification_record_guard() RETURNS trigger AS $$
        DECLARE
            span_hash text;
            span_page integer;
            page_text text;
            quoted_text text;
            boxes jsonb;
            start_offset integer;
            end_offset integer;
        BEGIN
            SELECT span.source_text_hash, span.page_number, page.text_content,
                   span.source_text, span.bounding_boxes, span.char_start, span.char_end
            INTO span_hash, span_page, page_text, quoted_text, boxes,
                 start_offset, end_offset
            FROM evidence_spans span
            LEFT JOIN document_pages page ON page.id = span.document_page_id
            WHERE span.id = NEW.evidence_span_id
              AND span.project_id = NEW.project_id;

            IF FOUND AND NEW.source_text_hash IS DISTINCT FROM span_hash THEN
                RAISE EXCEPTION 'Verification source hash does not match EvidenceSpan';
            END IF;
            IF NEW.location_verification_status = 'VERIFIED' AND FOUND THEN
                IF page_text IS NULL
                   OR position(quoted_text in page_text) = 0
                   OR NOT (NEW.reviewed_page_numbers @> to_jsonb(ARRAY[span_page]))
                   OR ((boxes IS NULL OR jsonb_array_length(boxes) = 0)
                       AND (start_offset IS NULL OR end_offset IS NULL)) THEN
                    RAISE EXCEPTION 'VERIFIED requires matching page text and location';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER span_verification_records_validate BEFORE INSERT ON evidence_span_verification_records FOR EACH ROW EXECUTE FUNCTION m3_verification_record_guard()")

    op.execute("""
        CREATE FUNCTION m3_verified_projection_guard() RETURNS trigger AS $$
        BEGIN
            IF NEW.location_verification_status = 'VERIFIED'
               AND (TG_OP = 'INSERT'
                    OR OLD.location_verification_status IS DISTINCT FROM NEW.location_verification_status)
               AND NOT EXISTS (
                   SELECT 1 FROM evidence_span_verification_records record
                   WHERE record.evidence_span_id = NEW.id
                     AND record.project_id = NEW.project_id
                     AND record.location_verification_status = 'VERIFIED'
                     AND record.source_text_hash = NEW.source_text_hash
               ) THEN
                RAISE EXCEPTION 'VERIFIED EvidenceSpan requires a verification record';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER evidence_spans_verified_projection BEFORE INSERT OR UPDATE OF location_verification_status ON evidence_spans FOR EACH ROW EXECUTE FUNCTION m3_verified_projection_guard()")

    op.execute("""
        CREATE FUNCTION m3_immutable_model_field_guard() RETURNS trigger AS $$
        BEGIN
            IF NEW.project_id IS DISTINCT FROM OLD.project_id
               OR NEW.extraction_id IS DISTINCT FROM OLD.extraction_id
               OR NEW.field_code IS DISTINCT FROM OLD.field_code
               OR NEW.model_value_text IS DISTINCT FROM OLD.model_value_text
               OR NEW.model_value_json IS DISTINCT FROM OLD.model_value_json THEN
                RAISE EXCEPTION 'LiteratureExtractionField model output is immutable';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER extraction_fields_model_immutable BEFORE UPDATE ON literature_extraction_fields FOR EACH ROW EXECUTE FUNCTION m3_immutable_model_field_guard()")

    op.execute("""
        CREATE FUNCTION m3_topic_run_completion_guard() RETURNS trigger AS $$
        DECLARE invalid_count integer;
        BEGIN
            IF NEW.status = 'COMPLETED'
               AND (TG_OP = 'INSERT' OR OLD.status IS DISTINCT FROM NEW.status) THEN
                SELECT count(*) INTO invalid_count
                FROM topic_candidates candidate
                WHERE candidate.topic_generation_run_id = NEW.id
                  AND NOT EXISTS (
                      SELECT 1 FROM topic_candidate_evidence source
                      WHERE source.topic_candidate_id = candidate.id
                  );
                IF (SELECT count(*) FROM topic_candidates WHERE topic_generation_run_id = NEW.id) <> 3
                   OR invalid_count <> 0 THEN
                    RAISE EXCEPTION 'Completed topic run requires exactly three sourced candidates';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER topic_generation_runs_completion_guard BEFORE INSERT OR UPDATE OF status ON topic_generation_runs FOR EACH ROW EXECUTE FUNCTION m3_topic_run_completion_guard()")


def downgrade() -> None:
    bind = op.get_bind()
    topic_job_rows = bind.execute(
        sa.text(
            "SELECT "
            "(SELECT count(*) FROM jobs WHERE task_type::text = 'TOPIC_GENERATE') + "
            "(SELECT count(*) FROM processing_runs "
            "WHERE process_type::text = 'TOPIC_GENERATE')"
        )
    ).scalar_one()
    if topic_job_rows:
        raise RuntimeError(
            "Cannot downgrade 0013 while topic generation job data exists."
        )

    op.execute("DROP TRIGGER topic_generation_runs_completion_guard ON topic_generation_runs")
    op.execute("DROP FUNCTION m3_topic_run_completion_guard()")
    op.execute("DROP TRIGGER extraction_fields_model_immutable ON literature_extraction_fields")
    op.execute("DROP FUNCTION m3_immutable_model_field_guard()")
    op.execute("DROP TRIGGER evidence_spans_verified_projection ON evidence_spans")
    op.execute("DROP FUNCTION m3_verified_projection_guard()")
    op.execute("DROP TRIGGER span_verification_records_validate ON evidence_span_verification_records")
    op.execute("DROP FUNCTION m3_verification_record_guard()")
    op.execute("DROP TRIGGER evidence_spans_source_immutable ON evidence_spans")
    op.execute("DROP FUNCTION m3_immutable_evidence_source_guard()")
    for table in (
        "literature_extraction_field_revisions",
        "evidence_span_verification_records",
        "literature_decisions",
    ):
        op.execute(f"DROP TRIGGER {table}_append_only ON {table}")
    op.execute("DROP FUNCTION m3_append_only_guard()")

    for table in (
        "topic_candidate_evidence", "topic_candidates", "topic_generation_runs",
        "evidence_set_summaries", "literature_decisions",
        "evidence_span_verification_records", "literature_extraction_field_revisions",
        "literature_extraction_fields", "evidence_spans", "literature_extractions",
    ):
        op.drop_table(table)

    op.drop_constraint("uq_processing_runs_id_project", "processing_runs", type_="unique")
    op.drop_constraint("uq_jobs_id_project", "jobs", type_="unique")
    op.drop_constraint("uq_document_chunks_id_document_project", "document_chunks", type_="unique")
    op.drop_constraint("uq_document_pages_id_document_project_number", "document_pages", type_="unique")
    op.drop_constraint("uq_literature_records_id_project_document", "literature_records", type_="unique")
    for name in reversed(tuple(_ENUMS)):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)

    values = ", ".join(f"'{value}'" for value in _PREVIOUS_JOB_VALUES)
    op.execute("ALTER TABLE processing_runs ALTER COLUMN process_type TYPE text")
    op.execute("ALTER TABLE jobs ALTER COLUMN task_type TYPE text")
    op.execute("DROP TYPE job_task_type")
    op.execute(f"CREATE TYPE job_task_type AS ENUM ({values})")
    op.execute("ALTER TABLE jobs ALTER COLUMN task_type TYPE job_task_type USING task_type::job_task_type")
    op.execute("ALTER TABLE processing_runs ALTER COLUMN process_type TYPE job_task_type USING process_type::job_task_type")
