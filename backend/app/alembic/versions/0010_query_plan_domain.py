"""Add the M2 QueryPlan domain and generation Job type.

Revision ID: 0010_query_plan_domain
Revises: 0009_rq_scoping_job
Create Date: 2026-08-01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010_query_plan_domain"
down_revision = "0009_rq_scoping_job"
branch_labels = None
depends_on = None

_PREVIOUS_JOB_VALUES = (
    "RESEARCH_QUESTION_SCOPING",
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
)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE job_task_type "
            "ADD VALUE IF NOT EXISTS 'QUERY_PLAN_GENERATION' BEFORE 'DOCUMENT_PARSE'"
        )
    query_plan_status = postgresql.ENUM("DRAFT", name="query_plan_status")
    query_plan_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "query_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("research_question_version_id", sa.Uuid(), nullable=False),
        sa.Column("chinese_terms", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("english_terms", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("synonyms", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("object_terms", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("method_terms", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("boolean_query", sa.Text(), nullable=True),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_model_invocation_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("DRAFT", name="query_plan_status", create_type=False),
            nullable=False,
        ),
        sa.Column("lock_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("lock_version >= 1", name="ck_query_plans_lock_version"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_query_plans_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["research_question_version_id", "project_id"],
            ["research_question_versions.id", "research_question_versions.project_id"],
            name="fk_query_plans_rq_version_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_model_invocation_id", "project_id"],
            ["model_invocations.id", "model_invocations.project_id"],
            name="fk_query_plans_model_invocation_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_query_plans"),
        sa.UniqueConstraint("id", "project_id", name="uq_query_plans_id_project"),
    )
    op.create_index(
        "ix_query_plans_project_id", "query_plans", ["project_id"], unique=False
    )
    op.create_index(
        "ix_query_plans_research_question_version_id",
        "query_plans",
        ["research_question_version_id"],
        unique=False,
    )
    op.create_index(
        "ix_query_plans_source_model_invocation_id",
        "query_plans",
        ["source_model_invocation_id"],
        unique=False,
    )
    op.create_index(
        "ix_query_plans_project_created",
        "query_plans",
        ["project_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_query_plans_rq_version",
        "query_plans",
        ["research_question_version_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("query_plans")
    postgresql.ENUM(name="query_plan_status").drop(op.get_bind(), checkfirst=True)
    values = ", ".join(f"'{value}'" for value in _PREVIOUS_JOB_VALUES)
    op.execute("ALTER TABLE processing_runs ALTER COLUMN process_type TYPE text")
    op.execute("ALTER TABLE jobs ALTER COLUMN task_type TYPE text")
    op.execute("DROP TYPE job_task_type")
    op.execute(f"CREATE TYPE job_task_type AS ENUM ({values})")
    op.execute(
        "ALTER TABLE jobs ALTER COLUMN task_type TYPE job_task_type "
        "USING task_type::job_task_type"
    )
    op.execute(
        "ALTER TABLE processing_runs ALTER COLUMN process_type TYPE job_task_type "
        "USING process_type::job_task_type"
    )
