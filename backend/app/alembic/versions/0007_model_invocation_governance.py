"""Add the M1 prompt and model invocation governance persistence.

Revision ID: 0007_model_invocation_governance
Revises: 0006_approval_foundation
Create Date: 2026-08-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_model_invocation_governance"
down_revision = "0006_approval_foundation"
branch_labels = None
depends_on = None

audit_actor_type_enum = postgresql.ENUM(
    "USER",
    "AGENT",
    "SYSTEM",
    "WORKER",
    name="audit_actor_type",
    create_type=False,
)
model_invocation_status_enum = postgresql.ENUM(
    "PENDING",
    "RUNNING",
    "SUCCEEDED",
    "FAILED",
    name="model_invocation_status",
    create_type=False,
)
model_data_access_level_enum = postgresql.ENUM(
    "METADATA_ONLY",
    "REDACTED_CONTENT",
    "VERIFIED_EVIDENCE_ONLY",
    "APPROVED_FULL_CONTENT",
    name="model_data_access_level",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    model_invocation_status_enum.create(bind, checkfirst=True)
    model_data_access_level_enum.create(bind, checkfirst=True)

    op.create_table(
        "model_invocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("actor_type", audit_actor_type_enum, nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("prompt_id", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("prompt_content_hash", sa.String(length=64), nullable=False),
        sa.Column("input_schema_name", sa.String(length=100), nullable=False),
        sa.Column("input_schema_version", sa.String(length=50), nullable=False),
        sa.Column("output_schema_name", sa.String(length=100), nullable=False),
        sa.Column("output_schema_version", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column(
            "requested_data_access_level",
            model_data_access_level_enum,
            nullable=False,
        ),
        sa.Column(
            "max_allowed_data_access_level",
            model_data_access_level_enum,
            nullable=False,
        ),
        sa.Column(
            "effective_data_access_level",
            model_data_access_level_enum,
            nullable=False,
        ),
        sa.Column("source_ids", postgresql.JSONB(), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("output_hash", sa.String(length=64), nullable=True),
        sa.Column("status", model_invocation_status_enum, nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("degradation", postgresql.JSONB(), nullable=True),
        sa.Column("implementation_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "prompt_content_hash ~ '^[0-9a-f]{64}$'",
            name="ck_model_invocations_prompt_hash",
        ),
        sa.CheckConstraint(
            "input_hash ~ '^[0-9a-f]{64}$'",
            name="ck_model_invocations_input_hash",
        ),
        sa.CheckConstraint(
            "output_hash IS NULL OR output_hash ~ '^[0-9a-f]{64}$'",
            name="ck_model_invocations_output_hash",
        ),
        sa.CheckConstraint(
            "(status IN ('PENDING', 'RUNNING') AND output_hash IS NULL "
            "AND error_code IS NULL AND completed_at IS NULL) OR "
            "(status = 'SUCCEEDED' AND output_hash IS NOT NULL "
            "AND error_code IS NULL AND completed_at IS NOT NULL) OR "
            "(status = 'FAILED' AND error_code IS NOT NULL "
            "AND completed_at IS NOT NULL)",
            name="ck_model_invocations_outcome_fields",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(source_ids) = 'array'",
            name="ck_model_invocations_source_ids_array",
        ),
        sa.CheckConstraint(
            "(CASE effective_data_access_level "
            "WHEN 'METADATA_ONLY' THEN 0 WHEN 'REDACTED_CONTENT' THEN 1 "
            "WHEN 'VERIFIED_EVIDENCE_ONLY' THEN 2 ELSE 3 END) <= "
            "(CASE requested_data_access_level "
            "WHEN 'METADATA_ONLY' THEN 0 WHEN 'REDACTED_CONTENT' THEN 1 "
            "WHEN 'VERIFIED_EVIDENCE_ONLY' THEN 2 ELSE 3 END) AND "
            "(CASE effective_data_access_level "
            "WHEN 'METADATA_ONLY' THEN 0 WHEN 'REDACTED_CONTENT' THEN 1 "
            "WHEN 'VERIFIED_EVIDENCE_ONLY' THEN 2 ELSE 3 END) <= "
            "(CASE max_allowed_data_access_level "
            "WHEN 'METADATA_ONLY' THEN 0 WHEN 'REDACTED_CONTENT' THEN 1 "
            "WHEN 'VERIFIED_EVIDENCE_ONLY' THEN 2 ELSE 3 END)",
            name="ck_model_invocations_effective_access",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_model_invocations_project_id_research_projects",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_model_invocations"),
    )
    for column in ("project_id", "request_id", "task_type"):
        op.create_index(
            f"ix_model_invocations_{column}", "model_invocations", [column]
        )
    op.create_index(
        "ix_model_invocations_project_status",
        "model_invocations",
        ["project_id", "status"],
    )
    op.create_index(
        "ix_model_invocations_prompt",
        "model_invocations",
        ["prompt_id", "prompt_version"],
    )

    op.execute(
        """
        CREATE FUNCTION enforce_model_invocation_history() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'model_invocations are immutable audit facts';
            END IF;
            IF OLD.status IN ('SUCCEEDED', 'FAILED') THEN
                RAISE EXCEPTION 'terminal model_invocations are immutable';
            END IF;
            IF OLD.status = 'PENDING' AND NEW.status NOT IN ('RUNNING', 'FAILED') THEN
                RAISE EXCEPTION 'invalid model_invocation transition';
            END IF;
            IF OLD.status = 'RUNNING' AND NEW.status NOT IN ('SUCCEEDED', 'FAILED') THEN
                RAISE EXCEPTION 'invalid model_invocation transition';
            END IF;
            IF NEW.id IS DISTINCT FROM OLD.id
                OR NEW.project_id IS DISTINCT FROM OLD.project_id
                OR NEW.request_id IS DISTINCT FROM OLD.request_id
                OR NEW.actor_type IS DISTINCT FROM OLD.actor_type
                OR NEW.actor_id IS DISTINCT FROM OLD.actor_id
                OR NEW.task_type IS DISTINCT FROM OLD.task_type
                OR NEW.prompt_id IS DISTINCT FROM OLD.prompt_id
                OR NEW.prompt_version IS DISTINCT FROM OLD.prompt_version
                OR NEW.prompt_content_hash IS DISTINCT FROM OLD.prompt_content_hash
                OR NEW.input_schema_name IS DISTINCT FROM OLD.input_schema_name
                OR NEW.input_schema_version IS DISTINCT FROM OLD.input_schema_version
                OR NEW.output_schema_name IS DISTINCT FROM OLD.output_schema_name
                OR NEW.output_schema_version IS DISTINCT FROM OLD.output_schema_version
                OR NEW.provider IS DISTINCT FROM OLD.provider
                OR NEW.model IS DISTINCT FROM OLD.model
                OR NEW.requested_data_access_level IS DISTINCT FROM OLD.requested_data_access_level
                OR NEW.max_allowed_data_access_level IS DISTINCT FROM OLD.max_allowed_data_access_level
                OR NEW.effective_data_access_level IS DISTINCT FROM OLD.effective_data_access_level
                OR NEW.source_ids IS DISTINCT FROM OLD.source_ids
                OR NEW.input_hash IS DISTINCT FROM OLD.input_hash
                OR NEW.implementation_metadata IS DISTINCT FROM OLD.implementation_metadata
                OR NEW.started_at IS DISTINCT FROM OLD.started_at
                OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
                RAISE EXCEPTION 'model_invocation identity and inputs are immutable';
            END IF;
            IF NEW.status = 'SUCCEEDED' AND NEW.output_hash IS NULL THEN
                RAISE EXCEPTION 'successful model_invocation requires output hash';
            END IF;
            IF NEW.status = 'FAILED' AND NEW.error_code IS NULL THEN
                RAISE EXCEPTION 'failed model_invocation requires error code';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER model_invocations_history_guard
        BEFORE UPDATE OR DELETE ON model_invocations
        FOR EACH ROW EXECUTE FUNCTION enforce_model_invocation_history();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER model_invocations_history_guard ON model_invocations")
    op.execute("DROP FUNCTION enforce_model_invocation_history()")
    op.drop_index("ix_model_invocations_prompt", table_name="model_invocations")
    op.drop_index(
        "ix_model_invocations_project_status", table_name="model_invocations"
    )
    for column in ("task_type", "request_id", "project_id"):
        op.drop_index(
            f"ix_model_invocations_{column}", table_name="model_invocations"
        )
    op.drop_table("model_invocations")

    bind = op.get_bind()
    model_data_access_level_enum.drop(bind, checkfirst=True)
    model_invocation_status_enum.drop(bind, checkfirst=True)
