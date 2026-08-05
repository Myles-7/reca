"""M6 manuscript, check, claim and revision-audit foundation.

Revision ID: 0017_m6_manuscripts
Revises: 0016_m5_figures
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017_m6_manuscripts"
down_revision: str | None = "0016_m5_figures"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name)


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def _string(length: int) -> sqlmodel.sql.sqltypes.AutoString:
    return sqlmodel.sql.sqltypes.AutoString(length=length)


def upgrade() -> None:
    op.execute(
        "ALTER TYPE job_task_type ADD VALUE IF NOT EXISTS 'MANUSCRIPT_REVISION_AUDIT'"
    )
    op.execute(
        "ALTER TYPE job_task_type ADD VALUE IF NOT EXISTS 'MANUSCRIPT_TRANSFORM'"
    )
    manuscript_status = _enum("manuscript_status", "ACTIVE", "ARCHIVED", "INVALIDATED")
    version_type = _enum(
        "manuscript_version_type",
        "ORIGINAL",
        "USER_UPLOAD",
        "AUTO_FIXED",
        "USER_REVISED",
        "DERIVED",
    )
    version_status = _enum(
        "manuscript_version_status", "UPLOADED", "AVAILABLE", "FAILED", "INVALIDATED"
    )
    check_status = _enum(
        "manuscript_check_run_status",
        "UPLOADED",
        "QUEUED",
        "PARSING",
        "CHECKING_RULES",
        "CHECKING_PROJECT_CONSISTENCY",
        "NEEDS_REVIEW",
        "COMPLETED",
        "FAILED",
        "LOW_CONFIDENCE",
        "CANCELLED",
    )
    issue_type = _enum(
        "manuscript_issue_type",
        "IN_TEXT_CITATION_MISSING_REFERENCE",
        "UNUSED_REFERENCE",
        "CITATION_METADATA_MISMATCH",
        "DUPLICATE_REFERENCE",
        "INVALID_DOI_FORMAT",
        "SAMPLE_SIZE_MISMATCH",
        "STATISTIC_MISMATCH",
        "FIGURE_TEXT_MISMATCH",
        "CAUSAL_OVERCLAIM",
        "POPULATION_OVERGENERALIZATION",
        "CONSENSUS_OVERCLAIM",
        "TERMINOLOGY_INCONSISTENCY",
        "UNDEFINED_ABBREVIATION",
        "HEADING_LEVEL_ISSUE",
        "FIGURE_NUMBERING_ISSUE",
        "UNIT_FORMAT_ISSUE",
        "PUNCTUATION_ISSUE",
    )
    issue_severity = _enum("manuscript_issue_severity", "HIGH", "MEDIUM", "LOW", "INFO")
    issue_status = _enum(
        "manuscript_issue_status",
        "OPEN",
        "ACKNOWLEDGED",
        "ACCEPTED",
        "REJECTED",
        "RESOLVED",
        "INVALIDATED",
    )
    evidence_type = _enum(
        "manuscript_evidence_type",
        "LITERATURE_RECORD",
        "EVIDENCE_SPAN",
        "ANALYSIS_RESULT",
        "FIGURE",
        "MANUSCRIPT_LOCATION",
        "RULE",
    )
    transformation_status = _enum(
        "manuscript_transformation_status",
        "DRAFT",
        "NEEDS_APPROVAL",
        "APPROVED",
        "REJECTED",
        "QUEUED",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        "INVALIDATED",
    )
    claim_status = _enum(
        "claim_status",
        "DRAFT",
        "NEEDS_EVIDENCE",
        "SUPPORTED",
        "CONFLICTED",
        "INSUFFICIENT",
        "CONFIRMED",
        "REJECTED",
        "INVALIDATED",
    )
    claim_type = _enum(
        "claim_type",
        "LITERATURE_SUMMARY",
        "CONSENSUS",
        "CONTROVERSY",
        "EVIDENCE_GAP",
        "TOPIC_RATIONALE",
        "DATA_DESCRIPTION",
        "STATISTICAL_RESULT",
        "INTERPRETATION",
        "MANUSCRIPT_STATEMENT",
    )
    claim_confidence = _enum("claim_confidence", "HIGH", "MEDIUM", "LOW", "UNKNOWN")
    audit_type = _enum("audit_type", "REVISION_DRIFT_AUDIT")
    audit_result_status = _enum(
        "audit_result_status", "QUEUED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"
    )

    op.create_table(
        "manuscripts",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("title", _string(500), nullable=True),
        sa.Column("current_version_id", _uuid(), nullable=True),
        sa.Column("status", manuscript_status, nullable=False),
        sa.Column("lock_version", sa.Integer(), nullable=False),
        sa.Column("created_by", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        sa.CheckConstraint("lock_version >= 1", name="ck_manuscripts_lock_version"),
        sa.ForeignKeyConstraint(
            ["project_id"], ["research_projects.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_manuscripts_id_project"),
    )
    op.create_index(
        "ix_manuscripts_project_status", "manuscripts", ["project_id", "status"]
    )
    op.create_index(
        "ix_manuscripts_current_version_id", "manuscripts", ["current_version_id"]
    )
    op.create_index("ix_manuscripts_project_id", "manuscripts", ["project_id"])
    op.create_index("ix_manuscripts_created_by", "manuscripts", ["created_by"])

    op.create_table(
        "manuscript_versions",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("manuscript_id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("parent_version_id", _uuid(), nullable=True),
        sa.Column("artifact_id", _uuid(), nullable=False),
        sa.Column("version_type", version_type, nullable=False),
        sa.Column("source_transformation_id", _uuid(), nullable=True),
        sa.Column("status", version_status, nullable=False),
        sa.Column("source_hash", _string(64), nullable=False),
        sa.Column("parse_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("created_by", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        sa.CheckConstraint("version_number >= 1", name="ck_manuscript_versions_number"),
        sa.CheckConstraint(
            "source_hash ~ '^[0-9a-f]{64}$'", name="ck_manuscript_versions_hash"
        ),
        sa.ForeignKeyConstraint(
            ["manuscript_id", "project_id"],
            ["manuscripts.id", "manuscripts.project_id"],
            name="fk_manuscript_versions_manuscript_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_manuscript_versions_artifact_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["parent_version_id", "project_id"],
            ["manuscript_versions.id", "manuscript_versions.project_id"],
            name="fk_manuscript_versions_parent_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id", "project_id", name="uq_manuscript_versions_id_project"
        ),
        sa.UniqueConstraint(
            "manuscript_id", "version_number", name="uq_manuscript_versions_number"
        ),
        sa.UniqueConstraint("artifact_id", name="uq_manuscript_versions_artifact"),
    )
    for column in (
        "manuscript_id",
        "project_id",
        "parent_version_id",
        "artifact_id",
        "source_transformation_id",
        "created_by",
    ):
        op.create_index(
            f"ix_manuscript_versions_{column}", "manuscript_versions", [column]
        )
    op.create_index(
        "ix_manuscript_versions_manuscript_created",
        "manuscript_versions",
        ["manuscript_id", "created_at"],
    )
    op.create_foreign_key(
        "fk_manuscripts_current_version_scope",
        "manuscripts",
        "manuscript_versions",
        ["current_version_id", "project_id"],
        ["id", "project_id"],
        ondelete="RESTRICT",
    )

    op.create_table(
        "manuscript_check_runs",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("manuscript_version_id", _uuid(), nullable=False),
        sa.Column("rule_set_version", _string(100), nullable=False),
        sa.Column("parser_version", _string(100), nullable=False),
        sa.Column("source_hash", _string(64), nullable=False),
        sa.Column("idempotency_key", _string(255), nullable=False),
        sa.Column("requested_checks", postgresql.JSONB(), nullable=False),
        sa.Column("status", check_status, nullable=False),
        sa.Column("issue_count", sa.Integer(), nullable=False),
        sa.Column("high_issue_count", sa.Integer(), nullable=False),
        sa.Column("processing_run_id", _uuid(), nullable=True),
        sa.Column("source_model_invocation_id", _uuid(), nullable=True),
        sa.Column("degradation", postgresql.JSONB(), nullable=True),
        sa.Column("error_code", _string(100), nullable=True),
        sa.Column("requested_by", _uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "issue_count >= 0 AND high_issue_count >= 0",
            name="ck_manuscript_check_runs_counts",
        ),
        sa.CheckConstraint(
            "source_hash ~ '^[0-9a-f]{64}$'", name="ck_manuscript_check_runs_hash"
        ),
        sa.ForeignKeyConstraint(
            ["manuscript_version_id", "project_id"],
            ["manuscript_versions.id", "manuscript_versions.project_id"],
            name="fk_manuscript_check_runs_version_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["processing_run_id", "project_id"],
            ["processing_runs.id", "processing_runs.project_id"],
            name="fk_manuscript_check_runs_processing_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_model_invocation_id"],
            ["model_invocations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["requested_by"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id", "project_id", name="uq_manuscript_check_runs_id_project"
        ),
        sa.UniqueConstraint(
            "manuscript_version_id",
            "idempotency_key",
            name="uq_manuscript_check_runs_idempotency",
        ),
    )
    op.create_index(
        "ix_manuscript_check_runs_project_status",
        "manuscript_check_runs",
        ["project_id", "status"],
    )
    op.create_index(
        "ix_manuscript_check_runs_project_id", "manuscript_check_runs", ["project_id"]
    )
    for column in (
        "manuscript_version_id",
        "processing_run_id",
        "source_model_invocation_id",
        "requested_by",
    ):
        op.create_index(
            f"ix_manuscript_check_runs_{column}", "manuscript_check_runs", [column]
        )

    op.create_table(
        "manuscript_issues",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("manuscript_check_run_id", _uuid(), nullable=False),
        sa.Column("manuscript_version_id", _uuid(), nullable=False),
        sa.Column("issue_type", issue_type, nullable=False),
        sa.Column("severity", issue_severity, nullable=False),
        sa.Column("section_name", _string(500), nullable=True),
        sa.Column("paragraph_index", sa.Integer(), nullable=True),
        sa.Column("table_index", sa.Integer(), nullable=True),
        sa.Column("locator", postgresql.JSONB(), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=True),
        sa.Column("normalized_reference", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("finding_hash", _string(64), nullable=False),
        sa.Column("confidence", _string(30), nullable=False),
        sa.Column("auto_fixable", sa.Boolean(), nullable=False),
        sa.Column("status", issue_status, nullable=False),
        sa.Column("lock_version", sa.Integer(), nullable=False),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("decided_by", _uuid(), nullable=True),
        sa.Column("source_model_invocation_id", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "finding_hash ~ '^[0-9a-f]{64}$'", name="ck_manuscript_issues_hash"
        ),
        sa.CheckConstraint(
            "NOT auto_fixable OR severity IN ('LOW', 'INFO')",
            name="ck_manuscript_issues_auto_fix_risk",
        ),
        sa.CheckConstraint("lock_version >= 1", name="ck_manuscript_issues_lock"),
        sa.ForeignKeyConstraint(
            ["manuscript_check_run_id", "project_id"],
            ["manuscript_check_runs.id", "manuscript_check_runs.project_id"],
            name="fk_manuscript_issues_run_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["manuscript_version_id", "project_id"],
            ["manuscript_versions.id", "manuscript_versions.project_id"],
            name="fk_manuscript_issues_version_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["decided_by"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["source_model_invocation_id"],
            ["model_invocations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_manuscript_issues_id_project"),
        sa.UniqueConstraint(
            "manuscript_check_run_id",
            "finding_hash",
            name="uq_manuscript_issues_finding",
        ),
    )
    op.create_index(
        "ix_manuscript_issues_run_status",
        "manuscript_issues",
        ["manuscript_check_run_id", "status"],
    )
    op.create_index(
        "ix_manuscript_issues_manuscript_check_run_id",
        "manuscript_issues",
        ["manuscript_check_run_id"],
    )
    for column in (
        "project_id",
        "manuscript_version_id",
        "decided_by",
        "source_model_invocation_id",
    ):
        op.create_index(f"ix_manuscript_issues_{column}", "manuscript_issues", [column])

    op.create_table(
        "manuscript_issue_evidence",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("manuscript_issue_id", _uuid(), nullable=False),
        sa.Column("evidence_type", evidence_type, nullable=False),
        sa.Column("evidence_object_type", _string(100), nullable=False),
        sa.Column("evidence_object_id", _uuid(), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("evidence_hash", _string(64), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["manuscript_issue_id", "project_id"],
            ["manuscript_issues.id", "manuscript_issues.project_id"],
            name="fk_manuscript_issue_evidence_issue_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("project_id", "manuscript_issue_id", "evidence_object_id"):
        op.create_index(
            f"ix_manuscript_issue_evidence_{column}",
            "manuscript_issue_evidence",
            [column],
        )

    op.create_table(
        "manuscript_transformations",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("manuscript_version_id", _uuid(), nullable=False),
        sa.Column("approved_issue_ids", postgresql.JSONB(), nullable=False),
        sa.Column("plan_payload", postgresql.JSONB(), nullable=False),
        sa.Column("input_artifact_hash", _string(64), nullable=False),
        sa.Column("preview", postgresql.JSONB(), nullable=True),
        sa.Column("preview_hash", _string(64), nullable=True),
        sa.Column("approval_record_id", _uuid(), nullable=True),
        sa.Column("output_manuscript_version_id", _uuid(), nullable=True),
        sa.Column("idempotency_key", _string(255), nullable=True),
        sa.Column("status", transformation_status, nullable=False),
        sa.Column("payload_hash", _string(64), nullable=False),
        sa.Column("lock_version", sa.Integer(), nullable=False),
        sa.Column("error_code", _string(100), nullable=True),
        sa.Column("created_by", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "payload_hash ~ '^[0-9a-f]{64}$'",
            name="ck_manuscript_transformations_payload_hash",
        ),
        sa.CheckConstraint(
            "preview_hash IS NULL OR preview_hash ~ '^[0-9a-f]{64}$'",
            name="ck_manuscript_transformations_preview_hash",
        ),
        sa.CheckConstraint(
            "lock_version >= 1", name="ck_manuscript_transformations_lock"
        ),
        sa.ForeignKeyConstraint(
            ["manuscript_version_id", "project_id"],
            ["manuscript_versions.id", "manuscript_versions.project_id"],
            name="fk_manuscript_transformations_input_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["approval_record_id", "project_id"],
            ["approval_records.id", "approval_records.project_id"],
            name="fk_manuscript_transformations_approval_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["output_manuscript_version_id", "project_id"],
            ["manuscript_versions.id", "manuscript_versions.project_id"],
            name="fk_manuscript_transformations_output_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id", "project_id", name="uq_manuscript_transformations_id_project"
        ),
    )
    for column in (
        "project_id",
        "manuscript_version_id",
        "output_manuscript_version_id",
        "approval_record_id",
        "idempotency_key",
        "created_by",
    ):
        op.create_index(
            f"ix_manuscript_transformations_{column}",
            "manuscript_transformations",
            [column],
        )
    op.create_index(
        "ix_manuscript_transformations_project_status",
        "manuscript_transformations",
        ["project_id", "status"],
    )

    op.create_table(
        "claims",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("claim_type", claim_type, nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("normalized_claim", sa.Text(), nullable=True),
        sa.Column("scope_statement", sa.Text(), nullable=True),
        sa.Column("source_object_type", _string(100), nullable=False),
        sa.Column("source_object_id", _uuid(), nullable=False),
        sa.Column("source_location", postgresql.JSONB(), nullable=False),
        sa.Column("source_hash", _string(64), nullable=False),
        sa.Column("text_hash", _string(64), nullable=False),
        sa.Column("status", claim_status, nullable=False),
        sa.Column("confidence", claim_confidence, nullable=False),
        sa.Column(
            "created_by_actor_type",
            postgresql.ENUM(name="audit_actor_type", create_type=False),
            nullable=False,
        ),
        sa.Column("created_by_actor_id", _string(255), nullable=True),
        sa.Column("approval_record_id", _uuid(), nullable=True),
        sa.Column("lock_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        sa.CheckConstraint("text_hash ~ '^[0-9a-f]{64}$'", name="ck_claims_text_hash"),
        sa.CheckConstraint(
            "source_hash ~ '^[0-9a-f]{64}$'", name="ck_claims_source_hash"
        ),
        sa.CheckConstraint("lock_version >= 1", name="ck_claims_lock"),
        sa.ForeignKeyConstraint(
            ["approval_record_id", "project_id"],
            ["approval_records.id", "approval_records.project_id"],
            name="fk_claims_approval_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_claims_id_project"),
    )
    op.create_index("ix_claims_project_id", "claims", ["project_id"])
    op.create_index("ix_claims_source_object_id", "claims", ["source_object_id"])
    op.create_index("ix_claims_approval_record_id", "claims", ["approval_record_id"])
    op.create_index("ix_claims_project_status", "claims", ["project_id", "status"])

    op.create_table(
        "audit_results",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("audit_type", audit_type, nullable=False),
        sa.Column("before_version_id", _uuid(), nullable=False),
        sa.Column("after_version_id", _uuid(), nullable=False),
        sa.Column("manuscript_id", _uuid(), nullable=False),
        sa.Column("status", audit_result_status, nullable=False),
        sa.Column("rule_set_version", _string(100), nullable=False),
        sa.Column("before_source_hash", _string(64), nullable=False),
        sa.Column("after_source_hash", _string(64), nullable=False),
        sa.Column("idempotency_key", _string(255), nullable=False),
        sa.Column("request_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("result_hash", _string(64), nullable=True),
        sa.Column("processing_run_id", _uuid(), nullable=True),
        sa.Column("requested_by", _uuid(), nullable=True),
        sa.Column("error_code", _string(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "result_hash IS NULL OR result_hash ~ '^[0-9a-f]{64}$'",
            name="ck_audit_results_hash",
        ),
        sa.CheckConstraint(
            "before_source_hash ~ '^[0-9a-f]{64}$' AND after_source_hash ~ '^[0-9a-f]{64}$'",
            name="ck_audit_results_source_hashes",
        ),
        sa.ForeignKeyConstraint(
            ["before_version_id", "project_id"],
            ["manuscript_versions.id", "manuscript_versions.project_id"],
            name="fk_audit_results_before_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["processing_run_id", "project_id"],
            ["processing_runs.id", "processing_runs.project_id"],
            name="fk_audit_results_processing_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["requested_by"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["after_version_id", "project_id"],
            ["manuscript_versions.id", "manuscript_versions.project_id"],
            name="fk_audit_results_after_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_audit_results_id_project"),
        sa.UniqueConstraint(
            "project_id", "idempotency_key", name="uq_audit_results_idempotency"
        ),
    )
    op.create_index("ix_audit_results_project_id", "audit_results", ["project_id"])
    op.create_index(
        "ix_audit_results_before_version_id", "audit_results", ["before_version_id"]
    )
    op.create_index(
        "ix_audit_results_after_version_id", "audit_results", ["after_version_id"]
    )
    for column in ("manuscript_id", "processing_run_id", "requested_by"):
        op.create_index(f"ix_audit_results_{column}", "audit_results", [column])
    op.create_index(
        "ix_audit_results_project_status", "audit_results", ["project_id", "status"]
    )

    op.execute("""
    CREATE FUNCTION reject_manuscript_version_mutation() RETURNS trigger AS $$
    BEGIN RAISE EXCEPTION 'ManuscriptVersion rows are immutable'; END;
    $$ LANGUAGE plpgsql;
    CREATE TRIGGER trg_manuscript_versions_immutable
    BEFORE UPDATE OR DELETE ON manuscript_versions
    FOR EACH ROW EXECUTE FUNCTION reject_manuscript_version_mutation();
    """)


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_manuscript_versions_immutable ON manuscript_versions"
    )
    op.execute("DROP FUNCTION IF EXISTS reject_manuscript_version_mutation()")
    op.drop_table("audit_results")
    op.drop_table("claims")
    op.drop_table("manuscript_transformations")
    op.drop_table("manuscript_issue_evidence")
    op.drop_table("manuscript_issues")
    op.drop_table("manuscript_check_runs")
    op.drop_constraint(
        "fk_manuscripts_current_version_scope", "manuscripts", type_="foreignkey"
    )
    op.drop_table("manuscript_versions")
    op.drop_table("manuscripts")
    for name in (
        "audit_result_status",
        "audit_type",
        "claim_confidence",
        "claim_type",
        "claim_status",
        "manuscript_transformation_status",
        "manuscript_evidence_type",
        "manuscript_issue_status",
        "manuscript_issue_severity",
        "manuscript_issue_type",
        "manuscript_check_run_status",
        "manuscript_version_status",
        "manuscript_version_type",
        "manuscript_status",
    ):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
    raise RuntimeError(
        "Cannot downgrade 0017 because PostgreSQL enum job_task_type was extended."
    )
