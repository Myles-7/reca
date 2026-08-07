from pathlib import Path

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.models import AgentEvent, AgentRun, AuditLog, ModelInvocation, ToolCall

pytestmark = pytest.mark.no_database


def test_runtime_models_compile_with_same_project_foreign_keys() -> None:
    dialect = postgresql.dialect()
    ddl = "\n".join(
        str(CreateTable(model.__table__).compile(dialect=dialect))
        for model in (AgentRun, ToolCall, AgentEvent, ModelInvocation, AuditLog)
    )
    assert "fk_tool_calls_agent_run_project" in ddl
    assert "fk_tool_calls_approval_project" in ddl
    assert "fk_tool_calls_job_project" in ddl
    assert "fk_agent_runs_job_project" in ddl
    assert "fk_model_invocations_agent_run_project" in ddl
    assert "fk_audit_logs_tool_call_project" in ddl
    assert "safe_input_summary JSONB NOT NULL" in ddl
    assert "agent_run_id UUID" in ddl


def test_0019_is_additive_guarded_and_honest_about_downgrade() -> None:
    migration = (
        Path(__file__).resolve().parents[2]
        / "app/alembic/versions/0019_m8_agent_runtime.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0018_m7_evidence_export"' in migration
    assert '"agent_runs"' in migration
    assert '"tool_calls"' in migration
    assert '"agent_events"' in migration
    assert 'op.add_column("model_invocations"' in migration
    assert 'op.drop_table("model_invocations")' not in migration
    assert "refusing lossy M8 downgrade while agent history exists" in migration
    assert "terminal agent_runs are immutable" in migration
    assert "terminal tool_calls are immutable" in migration
    assert "agent_events are append-only" in migration
    assert "AGENT_ORCHESTRATION" in migration
    assert "retained as inert compatibility values" in migration
