import json

import pytest

from app.main import app

pytestmark = pytest.mark.no_database


def test_m8_agent_paths_are_single_typed_contracts() -> None:
    document = app.openapi()
    paths = document["paths"]
    expected = {
        "/api/v1/projects/{project_id}/agent-runs": {"post"},
        "/api/v1/agent-runs/{agent_run_id}": {"get"},
        "/api/v1/agent-runs/{agent_run_id}/messages": {"post"},
        "/api/v1/agent-runs/{agent_run_id}/tool-calls": {"get"},
        "/api/v1/tool-calls/{tool_call_id}": {"get"},
        "/api/v1/agent-runs/{agent_run_id}/cancel": {"post"},
    }
    for path, methods in expected.items():
        assert path in paths
        assert methods <= set(paths[path])
    assert "/api/v1/projects/{project_id}/agents" not in paths


def test_m8_write_headers_and_accepted_semantics_are_explicit() -> None:
    paths = app.openapi()["paths"]
    for path in (
        "/api/v1/projects/{project_id}/agent-runs",
        "/api/v1/agent-runs/{agent_run_id}/messages",
        "/api/v1/agent-runs/{agent_run_id}/cancel",
    ):
        operation = paths[path]["post"]
        header = next(
            parameter
            for parameter in operation["parameters"]
            if parameter["name"] == "Idempotency-Key"
        )
        assert header["required"] is True
        assert "202" in operation["responses"]


def test_m8_public_schemas_are_safe_and_fail_closed() -> None:
    document = app.openapi()
    schemas = document["components"]["schemas"]
    run = schemas["AgentRunPublic"]["properties"]
    tool = schemas["ToolCallLinkPublic"]["properties"]
    assert {"status", "known_status", "allowed_actions", "disabled_reasons"} <= set(run)
    assert {"status", "known_status", "approval", "job", "allowed_actions"} <= set(tool)
    serialized = json.dumps(document).lower()
    for forbidden in (
        "run_state",
        "session_payload",
        "trace_payload",
        "authorization",
        "provider_token",
        "tool_arguments",
        "raw_prompt",
    ):
        assert forbidden not in serialized


def test_m8_input_boundaries_match_safe_persistence() -> None:
    schemas = app.openapi()["components"]["schemas"]
    assert schemas["AgentRunCreateRequest"]["properties"]["goal"]["maxLength"] == 500
    assert schemas["AgentMessageRequest"]["properties"]["message"]["maxLength"] == 500
    assert schemas["AgentRunCreateRequest"]["properties"]["mode"]["const"] == (
        "PLAN_AND_EXPLAIN"
    )
