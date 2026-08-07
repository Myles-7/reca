"""M5 Stage 2 full statistics and Figure domain.

Revision ID: 0016_m5_figures
Revises: 0015_m5_analysis
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016_m5_figures"
down_revision: str | None = "0015_m5_analysis"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _extend_enum(name: str, values: tuple[str, ...]) -> None:
    for value in values:
        op.execute(f"ALTER TYPE {name} ADD VALUE IF NOT EXISTS '{value}'")


def upgrade() -> None:
    _extend_enum(
        "analysis_method",
        (
            "INDEPENDENT_TWO_GROUP",
            "PAIRED_TWO_GROUP",
            "SIMPLE_LINEAR_REGRESSION",
        ),
    )
    _extend_enum(
        "assumption_check_code",
        (
            "NORMALITY",
            "VARIANCE_HOMOGENEITY",
            "PAIRING_VALIDITY",
            "RESIDUAL_DIAGNOSTIC",
        ),
    )
    _extend_enum(
        "analysis_result_type",
        ("GROUP_COMPARISON", "REGRESSION", "DIAGNOSTIC"),
    )

    chart_type = sa.Enum(
        "SCATTER",
        "GROUP_COMPARISON",
        "HISTOGRAM",
        "BOXPLOT",
        "CORRELATION_MATRIX",
        name="figure_chart_type",
    )
    plan_status = sa.Enum(
        "DRAFT", "READY", "INVALIDATED", "ARCHIVED", name="figure_plan_status"
    )
    render_status = sa.Enum(
        "QUEUED",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "CANCEL_REQUESTED",
        "CANCELLED",
        "INVALIDATED",
        name="figure_render_run_status",
    )
    figure_status = sa.Enum(
        "DRAFT",
        "READY",
        "NEEDS_REVIEW",
        "CONFIRMED",
        "INVALIDATED",
        "ARCHIVED",
        name="figure_status",
    )
    issue_type = sa.Enum(
        "MISSING_AXIS_LABEL",
        "MISSING_UNIT",
        "MISSING_LEGEND",
        "MISSING_CAPTION",
        "UNDEFINED_ERROR_BAR",
        "MISLEADING_AXIS_RANGE",
        "LOW_RESOLUTION",
        "VERSION_MISMATCH",
        "RESULT_MISMATCH",
        name="figure_issue_type",
    )
    issue_severity = sa.Enum("ERROR", "WARNING", "INFO", name="figure_issue_severity")
    issue_status = sa.Enum(
        "OPEN", "ACKNOWLEDGED", "RESOLVED", "INVALIDATED", name="figure_issue_status"
    )

    op.create_table(
        "figure_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), nullable=True),
        sa.Column("analysis_result_id", sa.Uuid(), nullable=True),
        sa.Column("chart_type", chart_type, nullable=False),
        sa.Column("parameters", postgresql.JSONB(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("status", plan_status, nullable=False),
        sa.Column(
            "plan_hash", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False
        ),
        sa.Column("lock_version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        sa.CheckConstraint("lock_version >= 1", name="ck_figure_plans_lock"),
        sa.CheckConstraint("plan_hash ~ '^[0-9a-f]{64}$'", name="ck_figure_plans_hash"),
        sa.CheckConstraint(
            "analysis_result_id IS NULL OR analysis_run_id IS NOT NULL",
            name="ck_figure_plans_result_requires_run",
        ),
        sa.CheckConstraint(
            "(invalidated_at IS NULL AND invalidation_reason IS NULL) OR "
            "(invalidated_at IS NOT NULL AND invalidation_reason IS NOT NULL)",
            name="ck_figure_plans_invalidation_pair",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_version_id", "project_id"],
            ["dataset_versions.id", "dataset_versions.project_id"],
            name="fk_figure_plans_dataset_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["analysis_run_id", "project_id"],
            ["analysis_runs.id", "analysis_runs.project_id"],
            name="fk_figure_plans_analysis_run_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["analysis_result_id", "project_id"],
            ["analysis_results.id", "analysis_results.project_id"],
            name="fk_figure_plans_analysis_result_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_figure_plans_id_project"),
    )
    for column in (
        "project_id",
        "dataset_version_id",
        "analysis_run_id",
        "analysis_result_id",
        "created_by",
    ):
        op.create_index(f"ix_figure_plans_{column}", "figure_plans", [column])
    op.create_index(
        "ix_figure_plans_project_status", "figure_plans", ["project_id", "status"]
    )
    op.create_index(
        "ix_figure_plans_dataset_created",
        "figure_plans",
        ["dataset_version_id", "created_at"],
    )

    op.create_table(
        "figure_render_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("figure_plan_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column("processing_run_id", sa.Uuid(), nullable=True),
        sa.Column("render_number", sa.Integer(), nullable=False),
        sa.Column(
            "idempotency_key",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column("status", render_status, nullable=False),
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
        sa.Column("requested_by", sa.Uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "error_code", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("render_number >= 1", name="ck_figure_render_runs_number"),
        sa.CheckConstraint(
            "input_hash ~ '^[0-9a-f]{64}$' AND parameters_hash ~ '^[0-9a-f]{64}$'",
            name="ck_figure_render_runs_hashes",
        ),
        sa.CheckConstraint(
            "environment_hash IS NULL OR environment_hash ~ '^[0-9a-f]{64}$'",
            name="ck_figure_render_runs_environment_hash",
        ),
        sa.CheckConstraint(
            "status <> 'COMPLETED' OR (completed_at IS NOT NULL AND environment_hash IS NOT NULL)",
            name="ck_figure_render_runs_completed_snapshot",
        ),
        sa.ForeignKeyConstraint(
            ["figure_plan_id", "project_id"],
            ["figure_plans.id", "figure_plans.project_id"],
            name="fk_figure_render_runs_plan_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_version_id", "project_id"],
            ["dataset_versions.id", "dataset_versions.project_id"],
            name="fk_figure_render_runs_dataset_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["processing_run_id", "project_id"],
            ["processing_runs.id", "processing_runs.project_id"],
            name="fk_figure_render_runs_processing_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["requested_by"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id", "project_id", name="uq_figure_render_runs_id_project"
        ),
        sa.UniqueConstraint(
            "figure_plan_id", "render_number", name="uq_figure_render_runs_number"
        ),
        sa.UniqueConstraint(
            "figure_plan_id",
            "idempotency_key",
            name="uq_figure_render_runs_idempotency",
        ),
    )
    for column in (
        "project_id",
        "figure_plan_id",
        "dataset_version_id",
        "processing_run_id",
        "requested_by",
    ):
        op.create_index(
            f"ix_figure_render_runs_{column}", "figure_render_runs", [column]
        )
    op.create_index(
        "ix_figure_render_runs_project_status",
        "figure_render_runs",
        ["project_id", "status"],
    )

    op.alter_column(
        "code_artifacts", "analysis_run_id", existing_type=sa.Uuid(), nullable=True
    )
    op.add_column(
        "code_artifacts", sa.Column("figure_render_run_id", sa.Uuid(), nullable=True)
    )
    op.create_index(
        "ix_code_artifacts_figure_render_run_id",
        "code_artifacts",
        ["figure_render_run_id"],
    )
    op.create_unique_constraint(
        "uq_code_artifacts_figure_render_run",
        "code_artifacts",
        ["figure_render_run_id"],
    )
    op.create_foreign_key(
        "fk_code_artifacts_figure_render_project",
        "code_artifacts",
        "figure_render_runs",
        ["figure_render_run_id", "project_id"],
        ["id", "project_id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_code_artifacts_exactly_one_owner",
        "code_artifacts",
        "(analysis_run_id IS NOT NULL)::int + (figure_render_run_id IS NOT NULL)::int = 1",
    )

    op.create_table(
        "figures",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("figure_plan_id", sa.Uuid(), nullable=False),
        sa.Column("figure_render_run_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), nullable=True),
        sa.Column("analysis_result_id", sa.Uuid(), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("chart_type", chart_type, nullable=False),
        sa.Column("status", figure_status, nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column(
            "figure_hash", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False
        ),
        sa.Column("png_artifact_id", sa.Uuid(), nullable=False),
        sa.Column("svg_artifact_id", sa.Uuid(), nullable=False),
        sa.Column("pdf_artifact_id", sa.Uuid(), nullable=False),
        sa.Column("code_artifact_id", sa.Uuid(), nullable=False),
        sa.Column("approval_record_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        sa.CheckConstraint("version_number >= 1", name="ck_figures_version_number"),
        sa.CheckConstraint("figure_hash ~ '^[0-9a-f]{64}$'", name="ck_figures_hash"),
        sa.CheckConstraint(
            "analysis_result_id IS NULL OR analysis_run_id IS NOT NULL",
            name="ck_figures_result_requires_run",
        ),
        sa.CheckConstraint(
            "(invalidated_at IS NULL AND invalidation_reason IS NULL) OR "
            "(invalidated_at IS NOT NULL AND invalidation_reason IS NOT NULL)",
            name="ck_figures_invalidation_pair",
        ),
        sa.ForeignKeyConstraint(
            ["figure_plan_id", "project_id"],
            ["figure_plans.id", "figure_plans.project_id"],
            name="fk_figures_plan_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["figure_render_run_id", "project_id"],
            ["figure_render_runs.id", "figure_render_runs.project_id"],
            name="fk_figures_render_run_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_version_id", "project_id"],
            ["dataset_versions.id", "dataset_versions.project_id"],
            name="fk_figures_dataset_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["analysis_run_id", "project_id"],
            ["analysis_runs.id", "analysis_runs.project_id"],
            name="fk_figures_analysis_run_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["analysis_result_id", "project_id"],
            ["analysis_results.id", "analysis_results.project_id"],
            name="fk_figures_analysis_result_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["png_artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_figures_png_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["svg_artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_figures_svg_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["pdf_artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_figures_pdf_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["code_artifact_id", "project_id"],
            ["code_artifacts.id", "code_artifacts.project_id"],
            name="fk_figures_code_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["approval_record_id", "project_id"],
            ["approval_records.id", "approval_records.project_id"],
            name="fk_figures_approval_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_figures_id_project"),
        sa.UniqueConstraint("figure_render_run_id", name="uq_figures_render_run"),
    )
    for column in (
        "project_id",
        "figure_plan_id",
        "figure_render_run_id",
        "dataset_version_id",
        "analysis_run_id",
        "analysis_result_id",
        "png_artifact_id",
        "svg_artifact_id",
        "pdf_artifact_id",
        "code_artifact_id",
        "approval_record_id",
    ):
        op.create_index(f"ix_figures_{column}", "figures", [column])
    op.create_index("ix_figures_project_status", "figures", ["project_id", "status"])
    op.create_index(
        "ix_figures_plan_version", "figures", ["figure_plan_id", "version_number"]
    )

    op.create_table(
        "figure_validation_issues",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("figure_id", sa.Uuid(), nullable=False),
        sa.Column("issue_type", issue_type, nullable=False),
        sa.Column("severity", issue_severity, nullable=False),
        sa.Column("status", issue_status, nullable=False),
        sa.Column(
            "subject_key", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("blocks_confirmation", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["figure_id", "project_id"],
            ["figures.id", "figures.project_id"],
            name="fk_figure_issues_figure_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_figure_issues_id_project"),
        sa.UniqueConstraint(
            "figure_id", "issue_type", "subject_key", name="uq_figure_issues_subject"
        ),
    )
    op.create_index(
        "ix_figure_validation_issues_project_id",
        "figure_validation_issues",
        ["project_id"],
    )
    op.create_index(
        "ix_figure_validation_issues_figure_id",
        "figure_validation_issues",
        ["figure_id"],
    )
    op.create_index(
        "ix_figure_issues_figure_status",
        "figure_validation_issues",
        ["figure_id", "status"],
    )

    op.execute("""
    CREATE FUNCTION reject_figure_mutation() RETURNS trigger AS $$
    BEGIN
      RAISE EXCEPTION 'Figure rows are immutable except controlled status transitions';
    END;
    $$ LANGUAGE plpgsql;
    CREATE TRIGGER trg_figures_immutable
    BEFORE DELETE ON figures
    FOR EACH ROW EXECUTE FUNCTION reject_figure_mutation();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_figures_immutable ON figures")
    op.execute("DROP FUNCTION IF EXISTS reject_figure_mutation()")
    op.drop_table("figure_validation_issues")
    op.drop_table("figures")
    op.drop_constraint(
        "ck_code_artifacts_exactly_one_owner", "code_artifacts", type_="check"
    )
    op.drop_constraint(
        "fk_code_artifacts_figure_render_project", "code_artifacts", type_="foreignkey"
    )
    op.drop_constraint(
        "uq_code_artifacts_figure_render_run", "code_artifacts", type_="unique"
    )
    op.drop_index("ix_code_artifacts_figure_render_run_id", table_name="code_artifacts")
    op.drop_column("code_artifacts", "figure_render_run_id")
    op.alter_column(
        "code_artifacts", "analysis_run_id", existing_type=sa.Uuid(), nullable=False
    )
    op.drop_table("figure_render_runs")
    op.drop_table("figure_plans")
    for name in (
        "figure_issue_status",
        "figure_issue_severity",
        "figure_issue_type",
        "figure_status",
        "figure_render_run_status",
        "figure_plan_status",
        "figure_chart_type",
    ):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
