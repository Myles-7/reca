"""Add the M1 approval infrastructure.

Revision ID: 0006_approval_foundation
Revises: 0005_job_processing_foundation
Create Date: 2026-08-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_approval_foundation"
down_revision = "0005_job_processing_foundation"
branch_labels = None
depends_on = None

approval_type_enum = postgresql.ENUM(
    "RESEARCH_QUESTION_CONFIRMATION",
    "LITERATURE_DECISION_CONFIRMATION",
    "LITERATURE_EXTRACTION_CONFIRMATION",
    "CLEANING_PLAN_APPROVAL",
    "VARIABLE_ROLE_CONFIRMATION",
    "ANALYSIS_PLAN_APPROVAL",
    "FIGURE_CONFIRMATION",
    "MANUSCRIPT_FIX_APPROVAL",
    "CLAIM_CONFIRMATION",
    "EXPORT_CONFIRMATION",
    name="approval_type",
    create_type=False,
)
approval_status_enum = postgresql.ENUM(
    "PENDING",
    "APPROVED",
    "REJECTED",
    "CANCELLED",
    "EXPIRED",
    "SUPERSEDED",
    name="approval_status",
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


def upgrade() -> None:
    bind = op.get_bind()
    approval_type_enum.create(bind, checkfirst=True)
    approval_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "approval_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approval_type", approval_type_enum, nullable=False),
        sa.Column("target_object_type", sa.String(length=100), nullable=False),
        sa.Column("target_object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by_actor_type", audit_actor_type_enum, nullable=False),
        sa.Column("requested_by_actor_id", sa.String(length=255), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", approval_status_enum, nullable=False),
        sa.Column("decision_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("payload_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("impact_summary", postgresql.JSONB(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supersedes_approval_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "payload_hash ~ '^[0-9a-f]{64}$'",
            name="ck_approval_records_payload_hash",
        ),
        sa.ForeignKeyConstraint(
            ["decision_by_user_id"],
            ["user.id"],
            name="fk_approval_records_decision_by_user_id_user",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_approval_records_project_id_research_projects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_approval_id"],
            ["approval_records.id"],
            name="fk_approval_records_supersedes_approval_id_approval_records",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_approval_records"),
    )
    for column in (
        "project_id",
        "target_object_id",
        "decision_by_user_id",
        "payload_hash",
        "supersedes_approval_id",
    ):
        op.create_index(f"ix_approval_records_{column}", "approval_records", [column])
    op.create_index(
        "ix_approval_records_project_status",
        "approval_records",
        ["project_id", "status"],
    )
    op.create_index(
        "ix_approval_records_project_target",
        "approval_records",
        ["project_id", "target_object_type", "target_object_id"],
    )

    op.create_table(
        "approval_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approval_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_type", sa.String(length=100), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision", sa.String(length=100), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["approval_record_id"],
            ["approval_records.id"],
            name="fk_approval_items_approval_record_id_approval_records",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_approval_items"),
        sa.UniqueConstraint(
            "approval_record_id",
            "item_type",
            "item_id",
            name="uq_approval_items_record_item",
        ),
    )
    op.create_index(
        "ix_approval_items_approval_record_id",
        "approval_items",
        ["approval_record_id"],
    )

    op.create_foreign_key(
        "fk_audit_logs_approval_id_approval_records",
        "audit_logs",
        "approval_records",
        ["approval_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.execute(
        """
        CREATE FUNCTION enforce_approval_record_history() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'approval_records are append-only history';
            END IF;
            IF OLD.status <> 'PENDING' THEN
                RAISE EXCEPTION 'terminal approval_records are immutable';
            END IF;
            IF NEW.status = 'PENDING' THEN
                RAISE EXCEPTION 'approval_records may only transition out of PENDING';
            END IF;
            IF NEW.id IS DISTINCT FROM OLD.id
                OR NEW.project_id IS DISTINCT FROM OLD.project_id
                OR NEW.approval_type IS DISTINCT FROM OLD.approval_type
                OR NEW.target_object_type IS DISTINCT FROM OLD.target_object_type
                OR NEW.target_object_id IS DISTINCT FROM OLD.target_object_id
                OR NEW.requested_by_actor_type IS DISTINCT FROM OLD.requested_by_actor_type
                OR NEW.requested_by_actor_id IS DISTINCT FROM OLD.requested_by_actor_id
                OR NEW.requested_at IS DISTINCT FROM OLD.requested_at
                OR NEW.payload_snapshot IS DISTINCT FROM OLD.payload_snapshot
                OR NEW.payload_hash IS DISTINCT FROM OLD.payload_hash
                OR NEW.impact_summary IS DISTINCT FROM OLD.impact_summary
                OR NEW.expires_at IS DISTINCT FROM OLD.expires_at
                OR NEW.supersedes_approval_id IS DISTINCT FROM OLD.supersedes_approval_id
                OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
                RAISE EXCEPTION 'approval identity and payload are immutable';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER approval_records_history_guard
        BEFORE UPDATE OR DELETE ON approval_records
        FOR EACH ROW EXECUTE FUNCTION enforce_approval_record_history();

        CREATE FUNCTION enforce_approval_item_history() RETURNS trigger AS $$
        DECLARE
            approval_state approval_status;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'approval_items are append-only history';
            END IF;
            SELECT status INTO approval_state
            FROM approval_records
            WHERE id = OLD.approval_record_id;
            IF approval_state <> 'PENDING' THEN
                RAISE EXCEPTION 'terminal approval_items are immutable';
            END IF;
            IF NEW.id IS DISTINCT FROM OLD.id
                OR NEW.approval_record_id IS DISTINCT FROM OLD.approval_record_id
                OR NEW.item_type IS DISTINCT FROM OLD.item_type
                OR NEW.item_id IS DISTINCT FROM OLD.item_id THEN
                RAISE EXCEPTION 'approval item identity is immutable';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER approval_items_history_guard
        BEFORE UPDATE OR DELETE ON approval_items
        FOR EACH ROW EXECUTE FUNCTION enforce_approval_item_history();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER approval_items_history_guard ON approval_items")
    op.execute("DROP FUNCTION enforce_approval_item_history()")
    op.execute("DROP TRIGGER approval_records_history_guard ON approval_records")
    op.execute("DROP FUNCTION enforce_approval_record_history()")
    op.drop_constraint(
        "fk_audit_logs_approval_id_approval_records",
        "audit_logs",
        type_="foreignkey",
    )
    op.drop_index("ix_approval_items_approval_record_id", table_name="approval_items")
    op.drop_table("approval_items")
    op.drop_index("ix_approval_records_project_target", table_name="approval_records")
    op.drop_index("ix_approval_records_project_status", table_name="approval_records")
    for column in (
        "supersedes_approval_id",
        "payload_hash",
        "decision_by_user_id",
        "target_object_id",
        "project_id",
    ):
        op.drop_index(f"ix_approval_records_{column}", table_name="approval_records")
    op.drop_table("approval_records")

    bind = op.get_bind()
    approval_status_enum.drop(bind, checkfirst=True)
    approval_type_enum.drop(bind, checkfirst=True)
