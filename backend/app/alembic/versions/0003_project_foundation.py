"""Add the M1 project, membership, audit, and idempotency foundation.

Revision ID: 0003_project_foundation
Revises: 0002_enable_pgvector_extension
Create Date: 2026-08-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_project_foundation"
down_revision = "0002_enable_pgvector_extension"
branch_labels = None
depends_on = None

project_type_enum = postgresql.ENUM(
    "THESIS",
    "COURSE",
    "INNOVATION",
    "RESEARCH",
    "DEMO",
    name="project_type",
    create_type=False,
)
project_stage_enum = postgresql.ENUM(
    "INTENT",
    "LITERATURE",
    "REVIEW",
    "TOPIC",
    "DATA",
    "ANALYSIS",
    "FIGURE",
    "MANUSCRIPT",
    "EVIDENCE",
    "EXPORT",
    name="project_stage",
    create_type=False,
)
project_status_enum = postgresql.ENUM(
    "ACTIVE", "ARCHIVED", "DELETED", name="project_status", create_type=False
)
project_member_role_enum = postgresql.ENUM(
    "OWNER",
    "EDITOR",
    "REVIEWER",
    "VIEWER",
    name="project_member_role",
    create_type=False,
)
audit_actor_type_enum = postgresql.ENUM(
    "USER",
    "AGENT",
    "SYSTEM",
    "WORKER",
    name="audit_actor_type",
    create_type=False,
)
audit_outcome_enum = postgresql.ENUM(
    "SUCCEEDED",
    "FAILED",
    "DENIED",
    name="audit_outcome",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    for enum in (
        project_type_enum,
        project_stage_enum,
        project_status_enum,
        project_member_role_enum,
        audit_actor_type_enum,
        audit_outcome_enum,
    ):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "research_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("discipline", sa.String(length=100), nullable=True),
        sa.Column("research_direction", sa.String(length=200), nullable=True),
        sa.Column("project_type", project_type_enum, nullable=False),
        sa.Column("current_stage", project_stage_enum, nullable=False),
        sa.Column("status", project_status_enum, nullable=False),
        sa.Column("expected_completion_date", sa.Date(), nullable=True),
        sa.Column("resource_constraints", postgresql.JSONB(), nullable=True),
        sa.Column("ethical_constraints", postgresql.JSONB(), nullable=True),
        sa.Column(
            "current_research_question_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("lock_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["user.id"], name="fk_research_projects_owner_id_user", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_research_projects"),
    )
    op.create_index(
        "ix_research_projects_owner_id", "research_projects", ["owner_id"]
    )

    op.create_table(
        "project_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", project_member_role_enum, nullable=False),
        sa.Column("permissions", postgresql.JSONB(), nullable=True),
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["invited_by"], ["user.id"], name="fk_project_members_invited_by_user", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_project_members_project_id_research_projects",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name="fk_project_members_user_id_user", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_project_members"),
        sa.UniqueConstraint(
            "project_id", "user_id", name="uq_project_members_project_user"
        ),
    )
    op.create_index(
        "ix_project_members_project_id", "project_members", ["project_id"]
    )
    op.create_index("ix_project_members_user_id", "project_members", ["user_id"])
    op.create_index(
        "ix_project_members_project_role", "project_members", ["project_id", "role"]
    )
    op.create_index(
        "uq_project_members_active_owner",
        "project_members",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("role = 'OWNER' AND removed_at IS NULL"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_type", audit_actor_type_enum, nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("object_type", sa.String(length=100), nullable=False),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("before_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("after_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approval_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome", audit_outcome_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_audit_logs_project_id_research_projects",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
    )
    for column in (
        "project_id",
        "action",
        "object_id",
        "request_id",
        "job_id",
        "approval_id",
    ):
        op.create_index(f"ix_audit_logs_{column}", "audit_logs", [column])
    op.create_index(
        "ix_audit_logs_project_created",
        "audit_logs",
        ["project_id", "created_at"],
    )
    op.execute(
        """
        CREATE FUNCTION reject_audit_log_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs are append-only';
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER audit_logs_append_only
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION reject_audit_log_mutation();
        """
    )

    op.create_table(
        "idempotency_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("path_template", sa.String(length=255), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["user.id"], name="fk_idempotency_records_actor_id_user", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_idempotency_records_project_id_research_projects",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_idempotency_records"),
    )
    op.create_index(
        "ix_idempotency_records_actor_id", "idempotency_records", ["actor_id"]
    )
    op.create_index(
        "ix_idempotency_records_project_id", "idempotency_records", ["project_id"]
    )
    op.create_index(
        "uq_idempotency_scope_key",
        "idempotency_records",
        ["actor_id", "project_id", "method", "path_template", "idempotency_key"],
        unique=True,
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_index("uq_idempotency_scope_key", table_name="idempotency_records")
    op.drop_index("ix_idempotency_records_project_id", table_name="idempotency_records")
    op.drop_index("ix_idempotency_records_actor_id", table_name="idempotency_records")
    op.drop_table("idempotency_records")

    op.execute("DROP TRIGGER audit_logs_append_only ON audit_logs")
    op.execute("DROP FUNCTION reject_audit_log_mutation()")
    op.drop_index("ix_audit_logs_project_created", table_name="audit_logs")
    for column in (
        "approval_id",
        "job_id",
        "request_id",
        "object_id",
        "action",
        "project_id",
    ):
        op.drop_index(f"ix_audit_logs_{column}", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("uq_project_members_active_owner", table_name="project_members")
    op.drop_index("ix_project_members_project_role", table_name="project_members")
    op.drop_index("ix_project_members_user_id", table_name="project_members")
    op.drop_index("ix_project_members_project_id", table_name="project_members")
    op.drop_table("project_members")

    op.drop_index("ix_research_projects_owner_id", table_name="research_projects")
    op.drop_table("research_projects")

    bind = op.get_bind()
    for enum in (
        audit_outcome_enum,
        audit_actor_type_enum,
        project_member_role_enum,
        project_status_enum,
        project_stage_enum,
        project_type_enum,
    ):
        enum.drop(bind, checkfirst=True)
