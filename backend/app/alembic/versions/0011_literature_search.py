"""Add M2 literature search, candidate, and record persistence.

Revision ID: 0011_literature_search
Revises: 0010_query_plan_domain
Create Date: 2026-08-01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011_literature_search"
down_revision = "0010_query_plan_domain"
branch_labels = None
depends_on = None

_PREVIOUS_JOB_VALUES = (
    "RESEARCH_QUESTION_SCOPING",
    "QUERY_PLAN_GENERATION",
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

_JOB_STATUS_VALUES = (
    "DRAFT",
    "QUEUED",
    "RUNNING",
    "NEEDS_REVIEW",
    "COMPLETED",
    "FAILED",
    "CANCEL_REQUESTED",
    "CANCELLED",
    "DISPATCH_FAILED",
)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE job_task_type "
            "ADD VALUE IF NOT EXISTS 'LITERATURE_SEARCH' BEFORE 'LITERATURE_EXTRACT'"
        )

    source_type = postgresql.ENUM(
        "OPENALEX",
        "DOI_IMPORT",
        "USER_UPLOAD",
        "MANUAL",
        "CACHE",
        name="literature_source_type",
    )
    verification_status = postgresql.ENUM(
        "VERIFIED",
        "PARTIALLY_VERIFIED",
        "UNVERIFIED",
        "CONFLICTED",
        name="literature_verification_status",
    )
    decision_status = postgresql.ENUM(
        "INCLUDED",
        "EXCLUDED",
        "UNCERTAIN",
        name="literature_decision_status",
    )
    source_type.create(op.get_bind(), checkfirst=True)
    verification_status.create(op.get_bind(), checkfirst=True)
    decision_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "literature_search_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("query_plan_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("provider_query", postgresql.JSONB(), nullable=False),
        sa.Column("query_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False),
        sa.Column("cache_stale", sa.Boolean(), nullable=False),
        sa.Column("cache_source_run_id", sa.Uuid(), nullable=True),
        sa.Column("degraded", sa.Boolean(), nullable=False),
        sa.Column("limitations", postgresql.JSONB(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(*_JOB_STATUS_VALUES, name="job_status", create_type=False),
            nullable=False,
        ),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "result_count >= 0", name="ck_literature_search_runs_result_count"
        ),
        sa.CheckConstraint(
            "query_fingerprint ~ '^[0-9a-f]{64}$'",
            name="ck_literature_search_runs_fingerprint",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_literature_search_runs_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["query_plan_id", "project_id"],
            ["query_plans.id", "query_plans.project_id"],
            name="fk_literature_search_runs_query_plan_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["cache_source_run_id", "project_id"],
            ["literature_search_runs.id", "literature_search_runs.project_id"],
            name="fk_literature_search_runs_cache_source_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name="fk_literature_search_runs_job",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_literature_search_runs"),
        sa.UniqueConstraint("id", "project_id", name="uq_literature_search_runs_scope"),
    )
    op.create_index(
        "ix_literature_search_runs_project_id",
        "literature_search_runs",
        ["project_id"],
    )
    op.create_index(
        "ix_literature_search_runs_query_plan_id",
        "literature_search_runs",
        ["query_plan_id"],
    )
    op.create_index(
        "ix_literature_search_runs_query_fingerprint",
        "literature_search_runs",
        ["query_fingerprint"],
    )
    op.create_index(
        "ix_literature_search_runs_cache_source_run_id",
        "literature_search_runs",
        ["cache_source_run_id"],
    )
    op.create_index(
        "ix_literature_search_runs_job_id", "literature_search_runs", ["job_id"]
    )
    op.create_index(
        "ix_literature_search_runs_cache_lookup",
        "literature_search_runs",
        ["project_id", "query_fingerprint", "status", "fetched_at"],
    )
    op.create_index(
        "ix_literature_search_runs_project_created",
        "literature_search_runs",
        ["project_id", "created_at"],
    )

    op.create_table(
        "literature_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column(
            "source_type",
            postgresql.ENUM(
                "OPENALEX",
                "DOI_IMPORT",
                "USER_UPLOAD",
                "MANUAL",
                "CACHE",
                name="literature_source_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("source_identifier", sa.String(length=500), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("normalized_title", sa.Text(), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("journal_name", sa.String(length=500), nullable=True),
        sa.Column("doi", sa.String(length=500), nullable=True),
        sa.Column("normalized_doi", sa.String(length=500), nullable=True),
        sa.Column("authors_text", sa.Text(), nullable=True),
        sa.Column("keywords", postgresql.JSONB(), nullable=True),
        sa.Column("work_type", sa.String(length=100), nullable=True),
        sa.Column("open_access_status", sa.String(length=100), nullable=True),
        sa.Column(
            "verification_status",
            postgresql.ENUM(
                "VERIFIED",
                "PARTIALLY_VERIFIED",
                "UNVERIFIED",
                "CONFLICTED",
                name="literature_verification_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("raw_source_data", postgresql.JSONB(), nullable=True),
        sa.Column(
            "current_decision",
            postgresql.ENUM(
                "INCLUDED",
                "EXCLUDED",
                "UNCERTAIN",
                name="literature_decision_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "length(normalized_title) > 0",
            name="ck_literature_records_normalized_title",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_literature_records_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_literature_records"),
        sa.UniqueConstraint("id", "project_id", name="uq_literature_records_scope"),
        sa.UniqueConstraint(
            "project_id",
            "normalized_doi",
            name="uq_literature_records_project_doi",
        ),
    )
    for column in (
        "project_id",
        "document_id",
        "source_identifier",
        "normalized_doi",
    ):
        op.create_index(
            f"ix_literature_records_{column}", "literature_records", [column]
        )
    op.create_index(
        "ix_literature_records_project_title",
        "literature_records",
        ["project_id", "normalized_title"],
    )
    op.create_index(
        "ix_literature_records_project_created",
        "literature_records",
        ["project_id", "created_at"],
    )

    op.create_table(
        "literature_search_candidates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("search_run_id", sa.Uuid(), nullable=False),
        sa.Column("result_order", sa.Integer(), nullable=False),
        sa.Column("source_identifier", sa.String(length=500), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("normalized_title", sa.Text(), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("journal_name", sa.String(length=500), nullable=True),
        sa.Column("doi", sa.String(length=500), nullable=True),
        sa.Column("normalized_doi", sa.String(length=500), nullable=True),
        sa.Column("authors_text", sa.Text(), nullable=True),
        sa.Column("keywords", postgresql.JSONB(), nullable=True),
        sa.Column("work_type", sa.String(length=100), nullable=True),
        sa.Column("open_access_status", sa.String(length=100), nullable=True),
        sa.Column(
            "verification_status",
            postgresql.ENUM(
                "VERIFIED",
                "PARTIALLY_VERIFIED",
                "UNVERIFIED",
                "CONFLICTED",
                name="literature_verification_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("raw_source_data", postgresql.JSONB(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("degraded", sa.Boolean(), nullable=False),
        sa.Column("imported_literature_record_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "result_order >= 1", name="ck_literature_candidates_result_order"
        ),
        sa.CheckConstraint(
            "length(normalized_title) > 0",
            name="ck_literature_candidates_normalized_title",
        ),
        sa.ForeignKeyConstraint(
            ["search_run_id", "project_id"],
            ["literature_search_runs.id", "literature_search_runs.project_id"],
            name="fk_literature_candidates_run_project",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["imported_literature_record_id", "project_id"],
            ["literature_records.id", "literature_records.project_id"],
            name="fk_literature_candidates_import_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_literature_search_candidates"),
        sa.UniqueConstraint(
            "search_run_id",
            "source_identifier",
            name="uq_literature_candidates_run_source",
        ),
    )
    for column in (
        "project_id",
        "search_run_id",
        "imported_literature_record_id",
    ):
        op.create_index(
            f"ix_literature_search_candidates_{column}",
            "literature_search_candidates",
            [column],
        )
    op.create_index(
        "ix_literature_candidates_run_order",
        "literature_search_candidates",
        ["search_run_id", "result_order"],
    )
    op.create_index(
        "ix_literature_candidates_project_doi",
        "literature_search_candidates",
        ["project_id", "normalized_doi"],
    )
    op.create_index(
        "ix_literature_candidates_project_title",
        "literature_search_candidates",
        ["project_id", "normalized_title"],
    )


def downgrade() -> None:
    op.drop_table("literature_search_candidates")
    op.drop_table("literature_records")
    op.drop_table("literature_search_runs")
    postgresql.ENUM(name="literature_decision_status").drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="literature_verification_status").drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="literature_source_type").drop(op.get_bind(), checkfirst=True)
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
