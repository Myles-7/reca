"""Add the M8 governed agent runtime persistence.

Revision ID: 0019_m8_agent_runtime
Revises: 0018_m7_evidence_export
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019_m8_agent_runtime"
down_revision: str | None = "0018_m7_evidence_export"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def _string(length: int) -> sqlmodel.sql.sqltypes.AutoString:
    return sqlmodel.sql.sqltypes.AutoString(length=length)


def _enum(name: str, *values: str) -> postgresql.ENUM:
    value = postgresql.ENUM(*values, name=name)
    value.create(op.get_bind(), checkfirst=True)
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    op.execute("ALTER TYPE job_task_type ADD VALUE IF NOT EXISTS 'AGENT_ORCHESTRATION'")
    run_status = _enum(
        "agent_run_status",
        "CREATED",
        "PLANNING",
        "WAITING_USER_INPUT",
        "WAITING_APPROVAL",
        "CALLING_TOOL",
        "REVIEWING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
    )
    call_status = _enum(
        "tool_call_status",
        "REQUESTED",
        "WAITING_APPROVAL",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "DENIED",
        "CANCELLED",
    )
    event_type = _enum(
        "agent_event_type",
        "USER_MESSAGE",
        "CONTINUE_INTENT",
        "ASSISTANT_SUMMARY",
        "RUNTIME_CHECKPOINT",
    )
    audit_actor = postgresql.ENUM(
        "USER",
        "AGENT",
        "SYSTEM",
        "WORKER",
        name="audit_actor_type",
        create_type=False,
    )

    op.create_table(
        "agent_runs",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("requested_by_user_id", _uuid(), nullable=False),
        sa.Column("agent_type", _string(100), nullable=False),
        sa.Column("status", run_status, nullable=False),
        sa.Column("request_id", _string(64)),
        sa.Column("correlation_id", _string(64)),
        sa.Column("idempotency_key", _string(255), nullable=False),
        sa.Column("request_payload_hash", _string(64), nullable=False),
        sa.Column("safe_input_summary", postgresql.JSONB(), nullable=False),
        sa.Column("snapshot_schema_version", _string(50), nullable=False),
        sa.Column("snapshot_revision", sa.Integer(), nullable=False),
        sa.Column("snapshot_hash", _string(64), nullable=False),
        sa.Column("source_object_versions", postgresql.JSONB(), nullable=False),
        sa.Column("safe_snapshot_summary", postgresql.JSONB(), nullable=False),
        sa.Column("max_turns", sa.Integer(), nullable=False),
        sa.Column("max_tool_calls", sa.Integer(), nullable=False),
        sa.Column("turn_count", sa.Integer(), nullable=False),
        sa.Column("tool_call_count", sa.Integer(), nullable=False),
        sa.Column("lock_version", sa.Integer(), nullable=False),
        sa.Column("retry_of_agent_run_id", _uuid()),
        sa.Column("job_id", _uuid()),
        sa.Column("failure_code", _string(100)),
        sa.Column("degradation", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_agent_runs"),
        sa.UniqueConstraint("id", "project_id", name="uq_agent_runs_id_project"),
        sa.UniqueConstraint(
            "project_id",
            "requested_by_user_id",
            "idempotency_key",
            name="uq_agent_runs_actor_idempotency",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_agent_runs_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"],
            ["user.id"],
            name="fk_agent_runs_user",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["retry_of_agent_run_id", "project_id"],
            ["agent_runs.id", "agent_runs.project_id"],
            name="fk_agent_runs_retry_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["job_id", "project_id"],
            ["jobs.id", "jobs.project_id"],
            name="fk_agent_runs_job_project",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "agent_type = 'RESEARCH_ORCHESTRATOR'", name="ck_agent_runs_type"
        ),
        sa.CheckConstraint(
            "lock_version >= 1 AND snapshot_revision >= 1",
            name="ck_agent_runs_versions",
        ),
        sa.CheckConstraint(
            "max_turns BETWEEN 1 AND 100 AND max_tool_calls BETWEEN 0 AND 200",
            name="ck_agent_runs_limits",
        ),
        sa.CheckConstraint(
            "turn_count >= 0 AND tool_call_count >= 0", name="ck_agent_runs_progress"
        ),
        sa.CheckConstraint(
            "snapshot_hash ~ '^[0-9a-f]{64}$' AND request_payload_hash ~ '^[0-9a-f]{64}$'",
            name="ck_agent_runs_hashes",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(source_object_versions) = 'object' AND jsonb_typeof(safe_input_summary) = 'object' AND jsonb_typeof(safe_snapshot_summary) = 'object'",
            name="ck_agent_runs_json_objects",
        ),
        sa.CheckConstraint(
            "(status IN ('COMPLETED','FAILED','CANCELLED') AND completed_at IS NOT NULL) OR (status NOT IN ('COMPLETED','FAILED','CANCELLED') AND completed_at IS NULL)",
            name="ck_agent_runs_terminal_completed_at",
        ),
        sa.CheckConstraint(
            "(status = 'FAILED' AND failure_code IS NOT NULL) OR (status <> 'FAILED' AND failure_code IS NULL)",
            name="ck_agent_runs_failure_fields",
        ),
    )
    op.create_index(
        "ix_agent_runs_project_status", "agent_runs", ["project_id", "status"]
    )
    op.create_index(
        "ix_agent_runs_project_created", "agent_runs", ["project_id", "created_at"]
    )
    op.create_index("ix_agent_runs_project_id", "agent_runs", ["project_id"])
    for column in (
        "requested_by_user_id",
        "request_id",
        "correlation_id",
        "retry_of_agent_run_id",
        "job_id",
    ):
        op.create_index(f"ix_agent_runs_{column}", "agent_runs", [column])

    op.create_table(
        "tool_calls",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("agent_run_id", _uuid(), nullable=False),
        sa.Column("requested_by_user_id", _uuid(), nullable=False),
        sa.Column("tool_name", _string(100), nullable=False),
        sa.Column("tool_version", _string(50), nullable=False),
        sa.Column("status", call_status, nullable=False),
        sa.Column("request_id", _string(64)),
        sa.Column("idempotency_key", _string(255), nullable=False),
        sa.Column("input_hash", _string(64), nullable=False),
        sa.Column("safe_input_summary", postgresql.JSONB(), nullable=False),
        sa.Column("output_hash", _string(64)),
        sa.Column("safe_output_summary", postgresql.JSONB()),
        sa.Column("approval_id", _uuid()),
        sa.Column("approval_payload_hash", _string(64)),
        sa.Column("job_id", _uuid()),
        sa.Column("output_object_type", _string(100)),
        sa.Column("output_object_id", _uuid()),
        sa.Column("retry_of_tool_call_id", _uuid()),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("error_code", _string(100)),
        sa.Column("retryable", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_tool_calls"),
        sa.UniqueConstraint("id", "project_id", name="uq_tool_calls_id_project"),
        sa.UniqueConstraint(
            "agent_run_id", "idempotency_key", name="uq_tool_calls_run_idempotency"
        ),
        sa.ForeignKeyConstraint(
            ["agent_run_id", "project_id"],
            ["agent_runs.id", "agent_runs.project_id"],
            name="fk_tool_calls_agent_run_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"],
            ["user.id"],
            name="fk_tool_calls_user",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["retry_of_tool_call_id", "project_id"],
            ["tool_calls.id", "tool_calls.project_id"],
            name="fk_tool_calls_retry_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["approval_id", "project_id"],
            ["approval_records.id", "approval_records.project_id"],
            name="fk_tool_calls_approval_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["job_id", "project_id"],
            ["jobs.id", "jobs.project_id"],
            name="fk_tool_calls_job_project",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "input_hash ~ '^[0-9a-f]{64}$' AND (output_hash IS NULL OR output_hash ~ '^[0-9a-f]{64}$') AND (approval_payload_hash IS NULL OR approval_payload_hash ~ '^[0-9a-f]{64}$')",
            name="ck_tool_calls_hashes",
        ),
        sa.CheckConstraint("attempt_number >= 1", name="ck_tool_calls_attempt_number"),
        sa.CheckConstraint(
            "jsonb_typeof(safe_input_summary) = 'object' AND (safe_output_summary IS NULL OR jsonb_typeof(safe_output_summary) = 'object')",
            name="ck_tool_calls_json_objects",
        ),
        sa.CheckConstraint(
            "(status IN ('COMPLETED','FAILED','DENIED','CANCELLED') AND completed_at IS NOT NULL) OR (status NOT IN ('COMPLETED','FAILED','DENIED','CANCELLED') AND completed_at IS NULL)",
            name="ck_tool_calls_terminal_completed_at",
        ),
        sa.CheckConstraint(
            "(status = 'COMPLETED' AND output_hash IS NOT NULL AND error_code IS NULL) OR (status IN ('FAILED','DENIED') AND error_code IS NOT NULL) OR (status NOT IN ('COMPLETED','FAILED','DENIED') AND output_hash IS NULL AND error_code IS NULL)",
            name="ck_tool_calls_outcome_fields",
        ),
        sa.CheckConstraint(
            "(approval_id IS NULL) = (approval_payload_hash IS NULL)",
            name="ck_tool_calls_approval_pair",
        ),
        sa.CheckConstraint(
            "(output_object_type IS NULL) = (output_object_id IS NULL)",
            name="ck_tool_calls_output_object_pair",
        ),
    )
    op.create_index(
        "ix_tool_calls_project_status", "tool_calls", ["project_id", "status"]
    )
    op.create_index(
        "ix_tool_calls_run_created", "tool_calls", ["agent_run_id", "created_at"]
    )
    op.create_index("ix_tool_calls_agent_run_id", "tool_calls", ["agent_run_id"])
    for column in (
        "project_id",
        "requested_by_user_id",
        "tool_name",
        "request_id",
        "approval_id",
        "job_id",
        "output_object_id",
        "retry_of_tool_call_id",
    ):
        op.create_index(f"ix_tool_calls_{column}", "tool_calls", [column])

    op.create_table(
        "agent_events",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("agent_run_id", _uuid(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("actor_type", audit_actor, nullable=False),
        sa.Column("actor_id", _string(255)),
        sa.Column("safe_summary", postgresql.JSONB(), nullable=False),
        sa.Column("content_hash", _string(64), nullable=False),
        sa.Column("request_id", _string(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_agent_events"),
        sa.UniqueConstraint(
            "agent_run_id", "sequence_number", name="uq_agent_events_run_sequence"
        ),
        sa.ForeignKeyConstraint(
            ["agent_run_id", "project_id"],
            ["agent_runs.id", "agent_runs.project_id"],
            name="fk_agent_events_agent_run_project",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("sequence_number >= 1", name="ck_agent_events_sequence"),
        sa.CheckConstraint(
            "content_hash ~ '^[0-9a-f]{64}$'", name="ck_agent_events_hash"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(safe_summary) = 'object'",
            name="ck_agent_events_summary_object",
        ),
    )
    op.create_index(
        "ix_agent_events_run_created", "agent_events", ["agent_run_id", "created_at"]
    )
    op.create_index("ix_agent_events_agent_run_id", "agent_events", ["agent_run_id"])
    op.create_index("ix_agent_events_project_id", "agent_events", ["project_id"])
    op.create_index("ix_agent_events_request_id", "agent_events", ["request_id"])

    for table in ("model_invocations", "audit_logs"):
        op.add_column(table, sa.Column("agent_run_id", _uuid()))
        op.add_column(table, sa.Column("tool_call_id", _uuid()))
        op.create_index(f"ix_{table}_agent_run_id", table, ["agent_run_id"])
        op.create_index(f"ix_{table}_tool_call_id", table, ["tool_call_id"])
        op.create_foreign_key(
            f"fk_{table}_agent_run_project",
            table,
            "agent_runs",
            ["agent_run_id", "project_id"],
            ["id", "project_id"],
            ondelete="RESTRICT",
        )
        op.create_foreign_key(
            f"fk_{table}_tool_call_project",
            table,
            "tool_calls",
            ["tool_call_id", "project_id"],
            ["id", "project_id"],
            ondelete="RESTRICT",
        )
    op.create_check_constraint(
        "ck_audit_logs_agent_scope",
        "audit_logs",
        "(agent_run_id IS NULL OR project_id IS NOT NULL) AND (tool_call_id IS NULL OR project_id IS NOT NULL)",
    )

    for name in (
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "request_count",
        "latency_ms",
    ):
        op.add_column("model_invocations", sa.Column(name, sa.Integer()))
    op.add_column(
        "model_invocations", sa.Column("redaction_policy_version", _string(50))
    )
    op.create_check_constraint(
        "ck_model_invocations_usage_nonnegative",
        "model_invocations",
        "(input_tokens IS NULL OR input_tokens >= 0) AND (output_tokens IS NULL OR output_tokens >= 0) AND (total_tokens IS NULL OR total_tokens >= 0) AND (request_count IS NULL OR request_count >= 0) AND (latency_ms IS NULL OR latency_ms >= 0)",
    )
    op.create_check_constraint(
        "ck_model_invocations_usage_total",
        "model_invocations",
        "total_tokens IS NULL OR input_tokens IS NULL OR output_tokens IS NULL OR total_tokens = input_tokens + output_tokens",
    )

    op.execute("""
    CREATE OR REPLACE FUNCTION enforce_model_invocation_history() RETURNS trigger AS $$
    BEGIN
        IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'model_invocations are immutable audit facts'; END IF;
        IF OLD.status IN ('SUCCEEDED', 'FAILED') THEN RAISE EXCEPTION 'terminal model_invocations are immutable'; END IF;
        IF OLD.status = 'PENDING' AND NEW.status NOT IN ('RUNNING', 'FAILED') THEN RAISE EXCEPTION 'invalid model_invocation transition'; END IF;
        IF OLD.status = 'RUNNING' AND NEW.status NOT IN ('SUCCEEDED', 'FAILED') THEN RAISE EXCEPTION 'invalid model_invocation transition'; END IF;
        IF NEW.id IS DISTINCT FROM OLD.id OR NEW.project_id IS DISTINCT FROM OLD.project_id
           OR NEW.agent_run_id IS DISTINCT FROM OLD.agent_run_id OR NEW.tool_call_id IS DISTINCT FROM OLD.tool_call_id
           OR NEW.request_id IS DISTINCT FROM OLD.request_id OR NEW.actor_type IS DISTINCT FROM OLD.actor_type
           OR NEW.actor_id IS DISTINCT FROM OLD.actor_id OR NEW.task_type IS DISTINCT FROM OLD.task_type
           OR NEW.prompt_id IS DISTINCT FROM OLD.prompt_id OR NEW.prompt_version IS DISTINCT FROM OLD.prompt_version
           OR NEW.prompt_content_hash IS DISTINCT FROM OLD.prompt_content_hash
           OR NEW.input_schema_name IS DISTINCT FROM OLD.input_schema_name OR NEW.input_schema_version IS DISTINCT FROM OLD.input_schema_version
           OR NEW.output_schema_name IS DISTINCT FROM OLD.output_schema_name OR NEW.output_schema_version IS DISTINCT FROM OLD.output_schema_version
           OR NEW.provider IS DISTINCT FROM OLD.provider OR NEW.model IS DISTINCT FROM OLD.model
           OR NEW.requested_data_access_level IS DISTINCT FROM OLD.requested_data_access_level
           OR NEW.max_allowed_data_access_level IS DISTINCT FROM OLD.max_allowed_data_access_level
           OR NEW.effective_data_access_level IS DISTINCT FROM OLD.effective_data_access_level
           OR NEW.source_ids IS DISTINCT FROM OLD.source_ids OR NEW.input_hash IS DISTINCT FROM OLD.input_hash
           OR NEW.implementation_metadata IS DISTINCT FROM OLD.implementation_metadata
           OR NEW.redaction_policy_version IS DISTINCT FROM OLD.redaction_policy_version
           OR NEW.started_at IS DISTINCT FROM OLD.started_at OR NEW.created_at IS DISTINCT FROM OLD.created_at
        THEN RAISE EXCEPTION 'model_invocation identity and inputs are immutable'; END IF;
        IF NEW.status = 'SUCCEEDED' AND NEW.output_hash IS NULL THEN RAISE EXCEPTION 'successful model_invocation requires output hash'; END IF;
        IF NEW.status = 'FAILED' AND NEW.error_code IS NULL THEN RAISE EXCEPTION 'failed model_invocation requires error code'; END IF;
        RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE FUNCTION enforce_agent_run_history() RETURNS trigger AS $$
    BEGIN
      IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'agent_runs are immutable history'; END IF;
      IF OLD.status IN ('COMPLETED','FAILED','CANCELLED') THEN RAISE EXCEPTION 'terminal agent_runs are immutable'; END IF;
      IF NEW.id IS DISTINCT FROM OLD.id OR NEW.project_id IS DISTINCT FROM OLD.project_id
         OR NEW.requested_by_user_id IS DISTINCT FROM OLD.requested_by_user_id
         OR NEW.agent_type IS DISTINCT FROM OLD.agent_type OR NEW.request_id IS DISTINCT FROM OLD.request_id
         OR NEW.correlation_id IS DISTINCT FROM OLD.correlation_id OR NEW.idempotency_key IS DISTINCT FROM OLD.idempotency_key
         OR NEW.request_payload_hash IS DISTINCT FROM OLD.request_payload_hash
         OR NEW.safe_input_summary IS DISTINCT FROM OLD.safe_input_summary
         OR NEW.max_turns IS DISTINCT FROM OLD.max_turns OR NEW.max_tool_calls IS DISTINCT FROM OLD.max_tool_calls
         OR NEW.retry_of_agent_run_id IS DISTINCT FROM OLD.retry_of_agent_run_id OR NEW.created_at IS DISTINCT FROM OLD.created_at
      THEN RAISE EXCEPTION 'agent_run identity and inputs are immutable'; END IF;
      IF NEW.status IS DISTINCT FROM OLD.status AND NOT (
        (OLD.status='CREATED' AND NEW.status IN ('PLANNING','FAILED','CANCELLED')) OR
        (OLD.status='PLANNING' AND NEW.status IN ('WAITING_USER_INPUT','WAITING_APPROVAL','CALLING_TOOL','REVIEWING','FAILED','CANCELLED')) OR
        (OLD.status='WAITING_USER_INPUT' AND NEW.status IN ('PLANNING','FAILED','CANCELLED')) OR
        (OLD.status='WAITING_APPROVAL' AND NEW.status IN ('PLANNING','CALLING_TOOL','FAILED','CANCELLED')) OR
        (OLD.status='CALLING_TOOL' AND NEW.status IN ('PLANNING','WAITING_APPROVAL','REVIEWING','FAILED','CANCELLED')) OR
        (OLD.status='REVIEWING' AND NEW.status IN ('PLANNING','COMPLETED','FAILED','CANCELLED'))
      ) THEN RAISE EXCEPTION 'invalid agent_run transition'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE TRIGGER agent_runs_history_guard BEFORE UPDATE OR DELETE ON agent_runs FOR EACH ROW EXECUTE FUNCTION enforce_agent_run_history();
    CREATE FUNCTION enforce_tool_call_history() RETURNS trigger AS $$
    BEGIN
      IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'tool_calls are immutable history'; END IF;
      IF OLD.status IN ('COMPLETED','FAILED','DENIED','CANCELLED') THEN RAISE EXCEPTION 'terminal tool_calls are immutable'; END IF;
      IF NEW.id IS DISTINCT FROM OLD.id OR NEW.project_id IS DISTINCT FROM OLD.project_id
         OR NEW.agent_run_id IS DISTINCT FROM OLD.agent_run_id OR NEW.requested_by_user_id IS DISTINCT FROM OLD.requested_by_user_id
         OR NEW.tool_name IS DISTINCT FROM OLD.tool_name OR NEW.tool_version IS DISTINCT FROM OLD.tool_version
         OR NEW.request_id IS DISTINCT FROM OLD.request_id OR NEW.idempotency_key IS DISTINCT FROM OLD.idempotency_key
         OR NEW.input_hash IS DISTINCT FROM OLD.input_hash OR NEW.safe_input_summary IS DISTINCT FROM OLD.safe_input_summary
         OR NEW.retry_of_tool_call_id IS DISTINCT FROM OLD.retry_of_tool_call_id OR NEW.attempt_number IS DISTINCT FROM OLD.attempt_number
         OR NEW.created_at IS DISTINCT FROM OLD.created_at
      THEN RAISE EXCEPTION 'tool_call identity and inputs are immutable'; END IF;
      IF NEW.status IS DISTINCT FROM OLD.status AND NOT (
        (OLD.status='REQUESTED' AND NEW.status IN ('WAITING_APPROVAL','RUNNING','FAILED','DENIED','CANCELLED')) OR
        (OLD.status='WAITING_APPROVAL' AND NEW.status IN ('RUNNING','FAILED','DENIED','CANCELLED')) OR
        (OLD.status='RUNNING' AND NEW.status IN ('COMPLETED','FAILED','CANCELLED'))
      ) THEN RAISE EXCEPTION 'invalid tool_call transition'; END IF;
      RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    CREATE TRIGGER tool_calls_history_guard BEFORE UPDATE OR DELETE ON tool_calls FOR EACH ROW EXECUTE FUNCTION enforce_tool_call_history();
    CREATE FUNCTION enforce_agent_event_history() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'agent_events are append-only'; END; $$ LANGUAGE plpgsql;
    CREATE TRIGGER agent_events_history_guard BEFORE UPDATE OR DELETE ON agent_events FOR EACH ROW EXECUTE FUNCTION enforce_agent_event_history();
    """)


def downgrade() -> None:
    # PostgreSQL enum values are retained as inert compatibility values; removing
    # AGENT_ORCHESTRATION would require rebuilding job_task_type and existing tables.
    op.execute(
        """DO $$ BEGIN IF EXISTS (SELECT 1 FROM agent_runs LIMIT 1) THEN RAISE EXCEPTION 'refusing lossy M8 downgrade while agent history exists'; END IF; END $$;"""
    )
    op.drop_constraint("ck_audit_logs_agent_scope", "audit_logs", type_="check")
    op.execute(
        "DROP TRIGGER agent_events_history_guard ON agent_events; DROP FUNCTION enforce_agent_event_history(); DROP TRIGGER tool_calls_history_guard ON tool_calls; DROP FUNCTION enforce_tool_call_history(); DROP TRIGGER agent_runs_history_guard ON agent_runs; DROP FUNCTION enforce_agent_run_history();"
    )
    op.drop_constraint(
        "ck_model_invocations_usage_total", "model_invocations", type_="check"
    )
    op.drop_constraint(
        "ck_model_invocations_usage_nonnegative", "model_invocations", type_="check"
    )
    for name in (
        "redaction_policy_version",
        "latency_ms",
        "request_count",
        "total_tokens",
        "output_tokens",
        "input_tokens",
    ):
        op.drop_column("model_invocations", name)
    op.execute("""
    CREATE OR REPLACE FUNCTION enforce_model_invocation_history() RETURNS trigger AS $$
    BEGIN
        IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'model_invocations are immutable audit facts'; END IF;
        IF OLD.status IN ('SUCCEEDED', 'FAILED') THEN RAISE EXCEPTION 'terminal model_invocations are immutable'; END IF;
        IF OLD.status = 'PENDING' AND NEW.status NOT IN ('RUNNING', 'FAILED') THEN RAISE EXCEPTION 'invalid model_invocation transition'; END IF;
        IF OLD.status = 'RUNNING' AND NEW.status NOT IN ('SUCCEEDED', 'FAILED') THEN RAISE EXCEPTION 'invalid model_invocation transition'; END IF;
        IF NEW.id IS DISTINCT FROM OLD.id OR NEW.project_id IS DISTINCT FROM OLD.project_id
           OR NEW.request_id IS DISTINCT FROM OLD.request_id OR NEW.actor_type IS DISTINCT FROM OLD.actor_type
           OR NEW.actor_id IS DISTINCT FROM OLD.actor_id OR NEW.task_type IS DISTINCT FROM OLD.task_type
           OR NEW.prompt_id IS DISTINCT FROM OLD.prompt_id OR NEW.prompt_version IS DISTINCT FROM OLD.prompt_version
           OR NEW.prompt_content_hash IS DISTINCT FROM OLD.prompt_content_hash
           OR NEW.input_schema_name IS DISTINCT FROM OLD.input_schema_name OR NEW.input_schema_version IS DISTINCT FROM OLD.input_schema_version
           OR NEW.output_schema_name IS DISTINCT FROM OLD.output_schema_name OR NEW.output_schema_version IS DISTINCT FROM OLD.output_schema_version
           OR NEW.provider IS DISTINCT FROM OLD.provider OR NEW.model IS DISTINCT FROM OLD.model
           OR NEW.requested_data_access_level IS DISTINCT FROM OLD.requested_data_access_level
           OR NEW.max_allowed_data_access_level IS DISTINCT FROM OLD.max_allowed_data_access_level
           OR NEW.effective_data_access_level IS DISTINCT FROM OLD.effective_data_access_level
           OR NEW.source_ids IS DISTINCT FROM OLD.source_ids OR NEW.input_hash IS DISTINCT FROM OLD.input_hash
           OR NEW.implementation_metadata IS DISTINCT FROM OLD.implementation_metadata
           OR NEW.started_at IS DISTINCT FROM OLD.started_at OR NEW.created_at IS DISTINCT FROM OLD.created_at
        THEN RAISE EXCEPTION 'model_invocation identity and inputs are immutable'; END IF;
        IF NEW.status = 'SUCCEEDED' AND NEW.output_hash IS NULL THEN RAISE EXCEPTION 'successful model_invocation requires output hash'; END IF;
        IF NEW.status = 'FAILED' AND NEW.error_code IS NULL THEN RAISE EXCEPTION 'failed model_invocation requires error code'; END IF;
        RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    """)
    for table in ("audit_logs", "model_invocations"):
        op.drop_constraint(f"fk_{table}_tool_call_project", table, type_="foreignkey")
        op.drop_constraint(f"fk_{table}_agent_run_project", table, type_="foreignkey")
        op.drop_index(f"ix_{table}_tool_call_id", table_name=table)
        op.drop_index(f"ix_{table}_agent_run_id", table_name=table)
        op.drop_column(table, "tool_call_id")
        op.drop_column(table, "agent_run_id")
    op.drop_table("agent_events")
    op.drop_table("tool_calls")
    op.drop_table("agent_runs")
    bind = op.get_bind()
    postgresql.ENUM(name="agent_event_type").drop(bind, checkfirst=True)
    postgresql.ENUM(name="tool_call_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="agent_run_status").drop(bind, checkfirst=True)
