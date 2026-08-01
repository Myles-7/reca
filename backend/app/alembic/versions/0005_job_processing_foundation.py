"""Add the M1 Job and ProcessingRun foundation.

Revision ID: 0005_job_processing_foundation
Revises: 0004_artifact_foundation
Create Date: 2026-08-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_job_processing_foundation"
down_revision = "0004_artifact_foundation"
branch_labels = None
depends_on = None

job_task_type_enum = postgresql.ENUM(
    "DOCUMENT_PARSE",
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
    name="job_task_type",
    create_type=False,
)
job_status_enum = postgresql.ENUM(
    "DRAFT",
    "QUEUED",
    "RUNNING",
    "NEEDS_REVIEW",
    "COMPLETED",
    "FAILED",
    "CANCEL_REQUESTED",
    "CANCELLED",
    "DISPATCH_FAILED",
    name="job_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    job_task_type_enum.create(bind, checkfirst=True)
    job_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_type", job_task_type_enum, nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", job_status_enum, nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("current_step", sa.String(length=255), nullable=True),
        sa.Column("total_steps", sa.Integer(), nullable=True),
        sa.Column("completed_steps", sa.Integer(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column(
            "requested_by_user_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retryable", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "completed_steps IS NULL OR completed_steps >= 0",
            name="ck_jobs_completed_steps",
        ),
        sa.CheckConstraint("max_retries >= 0", name="ck_jobs_max_retries"),
        sa.CheckConstraint(
            "progress_percent BETWEEN 0 AND 100",
            name="ck_jobs_progress_percent",
        ),
        sa.CheckConstraint("retry_count >= 0", name="ck_jobs_retry_count"),
        sa.CheckConstraint(
            "total_steps IS NULL OR total_steps >= 0",
            name="ck_jobs_total_steps",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_jobs_project_id_research_projects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"],
            ["user.id"],
            name="fk_jobs_requested_by_user_id_user",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_jobs"),
    )
    op.create_index("ix_jobs_project_id", "jobs", ["project_id"])
    op.create_index("ix_jobs_resource_id", "jobs", ["resource_id"])
    op.create_index("ix_jobs_idempotency_key", "jobs", ["idempotency_key"])
    op.create_index("ix_jobs_celery_task_id", "jobs", ["celery_task_id"])
    op.create_index(
        "ix_jobs_requested_by_user_id", "jobs", ["requested_by_user_id"]
    )
    op.create_index("ix_jobs_project_status", "jobs", ["project_id", "status"])
    op.create_index("ix_jobs_project_created", "jobs", ["project_id", "created_at"])
    op.create_index("ix_jobs_status_created", "jobs", ["status", "created_at"])

    op.create_table(
        "processing_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("process_type", job_task_type_enum, nullable=False),
        sa.Column("input_object_type", sa.String(length=100), nullable=False),
        sa.Column("input_object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=True),
        sa.Column("parameters", postgresql.JSONB(), nullable=True),
        sa.Column("parameters_hash", sa.String(length=64), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("engine", sa.String(length=100), nullable=False),
        sa.Column("engine_version", sa.String(length=100), nullable=True),
        sa.Column("implementation_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("status", job_status_enum, nullable=False),
        sa.Column("output_object_type", sa.String(length=100), nullable=True),
        sa.Column("output_object_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("log_artifact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "attempt_number >= 1", name="ck_processing_runs_attempt_number"
        ),
        sa.CheckConstraint(
            "input_hash IS NULL OR input_hash ~ '^[0-9a-f]{64}$'",
            name="ck_processing_runs_input_hash",
        ),
        sa.CheckConstraint(
            "parameters_hash ~ '^[0-9a-f]{64}$'",
            name="ck_processing_runs_parameters_hash",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name="fk_processing_runs_job_id_jobs",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["log_artifact_id"],
            ["artifacts.id"],
            name="fk_processing_runs_log_artifact_id_artifacts",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_processing_runs_project_id_research_projects",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_processing_runs"),
        sa.UniqueConstraint(
            "job_id", "attempt_number", name="uq_processing_runs_job_attempt"
        ),
    )
    op.create_index(
        "ix_processing_runs_project_id", "processing_runs", ["project_id"]
    )
    op.create_index("ix_processing_runs_job_id", "processing_runs", ["job_id"])
    op.create_index(
        "ix_processing_runs_input_object_id",
        "processing_runs",
        ["input_object_id"],
    )
    op.create_index(
        "ix_processing_runs_output_object_id",
        "processing_runs",
        ["output_object_id"],
    )
    op.create_index(
        "ix_processing_runs_log_artifact_id",
        "processing_runs",
        ["log_artifact_id"],
    )
    op.create_index(
        "ix_processing_runs_project_status",
        "processing_runs",
        ["project_id", "status"],
    )
    op.create_index(
        "ix_processing_runs_job_created",
        "processing_runs",
        ["job_id", "started_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_processing_runs_job_created", table_name="processing_runs"
    )
    op.drop_index(
        "ix_processing_runs_project_status", table_name="processing_runs"
    )
    op.drop_index(
        "ix_processing_runs_log_artifact_id", table_name="processing_runs"
    )
    op.drop_index(
        "ix_processing_runs_output_object_id", table_name="processing_runs"
    )
    op.drop_index(
        "ix_processing_runs_input_object_id", table_name="processing_runs"
    )
    op.drop_index("ix_processing_runs_job_id", table_name="processing_runs")
    op.drop_index("ix_processing_runs_project_id", table_name="processing_runs")
    op.drop_table("processing_runs")

    op.drop_index("ix_jobs_status_created", table_name="jobs")
    op.drop_index("ix_jobs_project_created", table_name="jobs")
    op.drop_index("ix_jobs_project_status", table_name="jobs")
    op.drop_index("ix_jobs_requested_by_user_id", table_name="jobs")
    op.drop_index("ix_jobs_celery_task_id", table_name="jobs")
    op.drop_index("ix_jobs_idempotency_key", table_name="jobs")
    op.drop_index("ix_jobs_resource_id", table_name="jobs")
    op.drop_index("ix_jobs_project_id", table_name="jobs")
    op.drop_table("jobs")

    bind = op.get_bind()
    job_status_enum.drop(bind, checkfirst=True)
    job_task_type_enum.drop(bind, checkfirst=True)
