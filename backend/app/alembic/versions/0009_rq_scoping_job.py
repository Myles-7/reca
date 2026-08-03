"""Add the M2 ResearchQuestion scoping Job type and audit provenance.

Revision ID: 0009_rq_scoping_job
Revises: 0008_research_question_domain
Create Date: 2026-08-01
"""

import sqlalchemy as sa
from alembic import op

revision = "0009_rq_scoping_job"
down_revision = "0008_research_question_domain"
branch_labels = None
depends_on = None

_PREVIOUS_VALUES = (
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
            "ADD VALUE IF NOT EXISTS 'RESEARCH_QUESTION_SCOPING' BEFORE 'DOCUMENT_PARSE'"
        )
    op.add_column(
        "audit_logs",
        sa.Column("model_invocation_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        "ix_audit_logs_model_invocation_id",
        "audit_logs",
        ["model_invocation_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_audit_logs_model_invocation_project",
        "audit_logs",
        "model_invocations",
        ["model_invocation_id", "project_id"],
        ["id", "project_id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    bind = op.get_bind()
    scoping_rows = bind.execute(
        sa.text(
            "SELECT "
            "(SELECT count(*) FROM jobs "
            "WHERE task_type::text = 'RESEARCH_QUESTION_SCOPING') + "
            "(SELECT count(*) FROM processing_runs "
            "WHERE process_type::text = 'RESEARCH_QUESTION_SCOPING')"
        )
    ).scalar_one()
    if scoping_rows:
        raise RuntimeError(
            "Cannot downgrade 0009 while ResearchQuestion scoping job data exists."
        )

    op.drop_constraint(
        "fk_audit_logs_model_invocation_project",
        "audit_logs",
        type_="foreignkey",
    )
    op.drop_index("ix_audit_logs_model_invocation_id", table_name="audit_logs")
    op.drop_column("audit_logs", "model_invocation_id")

    values = ", ".join(f"'{value}'" for value in _PREVIOUS_VALUES)
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
