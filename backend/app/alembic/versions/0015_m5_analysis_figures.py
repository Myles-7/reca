"""M5 Stage 1 analysis domain.

Revision ID: 0015_m5_analysis
Revises: 0014_m4_data_quality
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015_m5_analysis"
down_revision: str | None = "0014_m4_data_quality"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    analysis_goal = sa.Enum(
        "DESCRIBE", "CORRELATION", "COMPARE_GROUPS", "MODEL", name="analysis_goal"
    )
    analysis_method = sa.Enum(
        "DESCRIPTIVE_STATISTICS",
        "PEARSON_CORRELATION",
        "SPEARMAN_CORRELATION",
        name="analysis_method",
    )
    plan_status = sa.Enum(
        "DRAFT",
        "VALIDATING",
        "NEEDS_INPUT",
        "READY",
        "NEEDS_APPROVAL",
        "APPROVED",
        "REJECTED",
        "INVALIDATED",
        name="analysis_plan_status",
    )
    check_code = sa.Enum(
        "DATA_TYPE",
        "SAMPLE_SIZE",
        "MISSINGNESS",
        "CONSTANT",
        "LINEARITY",
        "OUTLIER_INFLUENCE",
        name="assumption_check_code",
    )
    check_status = sa.Enum(
        "PASSED",
        "FAILED",
        "WARNING",
        "NOT_APPLICABLE",
        "REQUIRES_USER_CONFIRMATION",
        "UNKNOWN",
        name="assumption_check_status",
    )
    run_status = sa.Enum(
        "QUEUED",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "CANCEL_REQUESTED",
        "CANCELLED",
        "INVALIDATED",
        name="analysis_run_status",
    )
    result_type = sa.Enum(
        "DESCRIPTIVE_NUMERIC",
        "DESCRIPTIVE_CATEGORICAL",
        "CORRELATION",
        name="analysis_result_type",
    )

    op.create_table(
        "analysis_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("research_question_version_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_goal", analysis_goal, nullable=False),
        sa.Column("method", analysis_method, nullable=False),
        sa.Column("dependent_variable_ids", postgresql.JSONB(), nullable=False),
        sa.Column("independent_variable_ids", postgresql.JSONB(), nullable=False),
        sa.Column("control_variable_ids", postgresql.JSONB(), nullable=False),
        sa.Column("missing_data_policy", postgresql.JSONB(), nullable=False),
        sa.Column("sample_filter", postgresql.JSONB(), nullable=True),
        sa.Column("parameters", postgresql.JSONB(), nullable=False),
        sa.Column("status", plan_status, nullable=False),
        sa.Column(
            "validation_hash",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=True,
        ),
        sa.Column("validation_warnings", postgresql.JSONB(), nullable=False),
        sa.Column("approval_record_id", sa.Uuid(), nullable=True),
        sa.Column(
            "payload_hash", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True
        ),
        sa.Column("lock_version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        sa.CheckConstraint("lock_version >= 1", name="ck_analysis_plans_lock"),
        sa.CheckConstraint(
            "payload_hash IS NULL OR payload_hash ~ '^[0-9a-f]{64}$'",
            name="ck_analysis_plans_payload_hash",
        ),
        sa.CheckConstraint(
            "validation_hash IS NULL OR validation_hash ~ '^[0-9a-f]{64}$'",
            name="ck_analysis_plans_validation_hash",
        ),
        sa.CheckConstraint(
            "(invalidated_at IS NULL AND invalidation_reason IS NULL) OR (invalidated_at IS NOT NULL AND invalidation_reason IS NOT NULL)",
            name="ck_analysis_plans_invalidation_pair",
        ),
        sa.ForeignKeyConstraint(
            ["research_question_version_id", "project_id"],
            ["research_question_versions.id", "research_question_versions.project_id"],
            name="fk_analysis_plans_question_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_version_id", "project_id"],
            ["dataset_versions.id", "dataset_versions.project_id"],
            name="fk_analysis_plans_dataset_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["approval_record_id", "project_id"],
            ["approval_records.id", "approval_records.project_id"],
            name="fk_analysis_plans_approval_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_analysis_plans_id_project"),
    )
    op.create_index("ix_analysis_plans_project_id", "analysis_plans", ["project_id"])
    op.create_index(
        "ix_analysis_plans_research_question_version_id",
        "analysis_plans",
        ["research_question_version_id"],
    )
    op.create_index(
        "ix_analysis_plans_dataset_version_id", "analysis_plans", ["dataset_version_id"]
    )
    op.create_index(
        "ix_analysis_plans_approval_record_id", "analysis_plans", ["approval_record_id"]
    )
    op.create_index("ix_analysis_plans_created_by", "analysis_plans", ["created_by"])
    op.create_index(
        "ix_analysis_plans_project_status", "analysis_plans", ["project_id", "status"]
    )
    op.create_index(
        "ix_analysis_plans_dataset_created",
        "analysis_plans",
        ["dataset_version_id", "created_at"],
    )

    op.create_table(
        "analysis_assumption_checks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_plan_id", sa.Uuid(), nullable=False),
        sa.Column("check_code", check_code, nullable=False),
        sa.Column(
            "subject_key", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False
        ),
        sa.Column("status", check_status, nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("blocks_approval", sa.Boolean(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_plan_id", "project_id"],
            ["analysis_plans.id", "analysis_plans.project_id"],
            name="fk_analysis_checks_plan_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_analysis_checks_id_project"),
        sa.UniqueConstraint(
            "analysis_plan_id",
            "check_code",
            "subject_key",
            name="uq_analysis_checks_subject",
        ),
    )
    op.create_index(
        "ix_analysis_assumption_checks_project_id",
        "analysis_assumption_checks",
        ["project_id"],
    )
    op.create_index(
        "ix_analysis_assumption_checks_analysis_plan_id",
        "analysis_assumption_checks",
        ["analysis_plan_id"],
    )
    op.create_index(
        "ix_analysis_checks_plan_status",
        "analysis_assumption_checks",
        ["analysis_plan_id", "status"],
    )

    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_plan_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column("approval_record_id", sa.Uuid(), nullable=False),
        sa.Column("processing_run_id", sa.Uuid(), nullable=True),
        sa.Column("run_number", sa.Integer(), nullable=False),
        sa.Column(
            "idempotency_key",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column("run_reason", sa.Text(), nullable=True),
        sa.Column("status", run_status, nullable=False),
        sa.Column(
            "parameters_hash",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=False,
        ),
        sa.Column(
            "input_hash", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False
        ),
        sa.Column(
            "environment_hash",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=True,
        ),
        sa.Column("environment_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("effective_n", sa.Integer(), nullable=True),
        sa.Column("code_artifact_id", sa.Uuid(), nullable=True),
        sa.Column("log_artifact_id", sa.Uuid(), nullable=True),
        sa.Column("requested_by", sa.Uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "error_code", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        sa.CheckConstraint("run_number >= 1", name="ck_analysis_runs_number"),
        sa.CheckConstraint(
            "parameters_hash ~ '^[0-9a-f]{64}$' AND input_hash ~ '^[0-9a-f]{64}$'",
            name="ck_analysis_runs_hashes",
        ),
        sa.CheckConstraint(
            "environment_hash IS NULL OR environment_hash ~ '^[0-9a-f]{64}$'",
            name="ck_analysis_runs_environment_hash",
        ),
        sa.CheckConstraint(
            "effective_n IS NULL OR effective_n >= 0",
            name="ck_analysis_runs_effective_n",
        ),
        sa.CheckConstraint(
            "status <> 'COMPLETED' OR (completed_at IS NOT NULL AND environment_hash IS NOT NULL)",
            name="ck_analysis_runs_completed_snapshot",
        ),
        sa.CheckConstraint(
            "(invalidated_at IS NULL AND invalidation_reason IS NULL) OR (invalidated_at IS NOT NULL AND invalidation_reason IS NOT NULL)",
            name="ck_analysis_runs_invalidation_pair",
        ),
        sa.ForeignKeyConstraint(
            ["analysis_plan_id", "project_id"],
            ["analysis_plans.id", "analysis_plans.project_id"],
            name="fk_analysis_runs_plan_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_version_id", "project_id"],
            ["dataset_versions.id", "dataset_versions.project_id"],
            name="fk_analysis_runs_dataset_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["approval_record_id", "project_id"],
            ["approval_records.id", "approval_records.project_id"],
            name="fk_analysis_runs_approval_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["processing_run_id", "project_id"],
            ["processing_runs.id", "processing_runs.project_id"],
            name="fk_analysis_runs_processing_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["log_artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_analysis_runs_log_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["requested_by"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_analysis_runs_id_project"),
        sa.UniqueConstraint(
            "analysis_plan_id", "run_number", name="uq_analysis_runs_number"
        ),
        sa.UniqueConstraint(
            "analysis_plan_id", "idempotency_key", name="uq_analysis_runs_idempotency"
        ),
    )
    for column in (
        "project_id",
        "analysis_plan_id",
        "dataset_version_id",
        "approval_record_id",
        "processing_run_id",
        "code_artifact_id",
        "log_artifact_id",
        "requested_by",
    ):
        op.create_index(f"ix_analysis_runs_{column}", "analysis_runs", [column])
    op.create_index(
        "ix_analysis_runs_project_status", "analysis_runs", ["project_id", "status"]
    )
    op.create_index(
        "ix_analysis_runs_plan_created",
        "analysis_runs",
        ["analysis_plan_id", "created_at"],
    )

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), nullable=False),
        sa.Column(
            "result_key", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False
        ),
        sa.Column("result_type", result_type, nullable=False),
        sa.Column(
            "schema_version",
            sqlmodel.sql.sqltypes.AutoString(length=50),
            nullable=False,
        ),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "result_hash", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "result_hash ~ '^[0-9a-f]{64}$'", name="ck_analysis_results_hash"
        ),
        sa.ForeignKeyConstraint(
            ["analysis_run_id", "project_id"],
            ["analysis_runs.id", "analysis_runs.project_id"],
            name="fk_analysis_results_run_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_analysis_results_id_project"),
        sa.UniqueConstraint(
            "analysis_run_id", "result_key", name="uq_analysis_results_key"
        ),
    )
    op.create_index(
        "ix_analysis_results_project_id", "analysis_results", ["project_id"]
    )
    op.create_index(
        "ix_analysis_results_analysis_run_id", "analysis_results", ["analysis_run_id"]
    )
    op.create_index(
        "ix_analysis_results_run_type",
        "analysis_results",
        ["analysis_run_id", "result_type"],
    )
    op.create_index(
        "uq_analysis_results_primary",
        "analysis_results",
        ["analysis_run_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )

    op.create_table(
        "code_artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column(
            "template_version",
            sqlmodel.sql.sqltypes.AutoString(length=50),
            nullable=False,
        ),
        sa.Column(
            "language", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False
        ),
        sa.Column(
            "entry", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False
        ),
        sa.Column("dependency_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column(
            "input_hash", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False
        ),
        sa.Column(
            "output_hash", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "input_hash ~ '^[0-9a-f]{64}$' AND output_hash ~ '^[0-9a-f]{64}$'",
            name="ck_code_artifacts_hashes",
        ),
        sa.ForeignKeyConstraint(
            ["analysis_run_id", "project_id"],
            ["analysis_runs.id", "analysis_runs.project_id"],
            name="fk_code_artifacts_run_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_code_artifacts_artifact_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_code_artifacts_id_project"),
        sa.UniqueConstraint("analysis_run_id", name="uq_code_artifacts_run"),
        sa.UniqueConstraint("artifact_id", name="uq_code_artifacts_artifact"),
    )
    op.create_index("ix_code_artifacts_project_id", "code_artifacts", ["project_id"])
    op.create_index(
        "ix_code_artifacts_analysis_run_id", "code_artifacts", ["analysis_run_id"]
    )
    op.create_index("ix_code_artifacts_artifact_id", "code_artifacts", ["artifact_id"])
    op.create_foreign_key(
        "fk_analysis_runs_code_project",
        "analysis_runs",
        "code_artifacts",
        ["code_artifact_id", "project_id"],
        ["id", "project_id"],
        ondelete="RESTRICT",
    )

    op.execute("""
    CREATE FUNCTION reject_analysis_result_mutation() RETURNS trigger AS $$
    BEGIN
      RAISE EXCEPTION 'AnalysisResult rows are immutable';
    END;
    $$ LANGUAGE plpgsql;
    CREATE TRIGGER trg_analysis_results_immutable
    BEFORE UPDATE OR DELETE ON analysis_results
    FOR EACH ROW EXECUTE FUNCTION reject_analysis_result_mutation();
    """)


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_analysis_results_immutable ON analysis_results"
    )
    op.execute("DROP FUNCTION IF EXISTS reject_analysis_result_mutation()")
    op.drop_constraint(
        "fk_analysis_runs_code_project", "analysis_runs", type_="foreignkey"
    )
    for table in (
        "code_artifacts",
        "analysis_results",
        "analysis_runs",
        "analysis_assumption_checks",
        "analysis_plans",
    ):
        op.drop_table(table)
    for name in (
        "analysis_result_type",
        "analysis_run_status",
        "assumption_check_status",
        "assumption_check_code",
        "analysis_plan_status",
        "analysis_method",
        "analysis_goal",
    ):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
