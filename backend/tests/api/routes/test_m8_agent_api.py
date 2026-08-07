import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.agent_runtime import service as runtime_service
from app.api.routes import agent_runs as agent_routes
from app.core.config import settings
from app.models import AgentRun, AgentRunStatus, User


class RecordingDispatcher:
    def __init__(self) -> None:
        self.calls: list[tuple[uuid.UUID, str]] = []

    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        self.calls.append((job_id, task_id))


def _project(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.post(
        "/api/v1/projects",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"name": "M8 Agent API", "project_type": "RESEARCH"},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_m8_agent_api_accepts_reads_messages_cancel_and_replay(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispatcher = RecordingDispatcher()
    monkeypatch.setattr(agent_routes, "dispatcher", dispatcher)
    project = _project(client, normal_user_token_headers)
    key = str(uuid.uuid4())
    payload = {
        "goal": "Review the current project and explain the next safe action.",
        "mode": "PLAN_AND_EXPLAIN",
        "allow_tool_calls": True,
    }
    created = client.post(
        f"/api/v1/projects/{project['id']}/agent-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json=payload,
    )
    replay = client.post(
        f"/api/v1/projects/{project['id']}/agent-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json=payload,
    )
    assert created.status_code == replay.status_code == 202
    assert replay.json()["meta"]["idempotency_replayed"] is True
    assert len(dispatcher.calls) == 1
    run_id = uuid.UUID(created.json()["data"]["id"])
    detail = client.get(
        f"/api/v1/agent-runs/{run_id}", headers=normal_user_token_headers
    )
    tools = client.get(
        f"/api/v1/agent-runs/{run_id}/tool-calls", headers=normal_user_token_headers
    )
    assert detail.status_code == tools.status_code == 200
    assert detail.json()["data"]["known_status"] is True
    assert tools.json()["pagination"]["total"] == 0

    actor = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).one()
    runtime_service.transition_agent_run(
        db,
        actor=actor,
        project_id=uuid.UUID(project["id"]),
        agent_run_id=run_id,
        target=AgentRunStatus.PLANNING,
    )
    runtime_service.transition_agent_run(
        db,
        actor=actor,
        project_id=uuid.UUID(project["id"]),
        agent_run_id=run_id,
        target=AgentRunStatus.WAITING_USER_INPUT,
    )
    message_key = str(uuid.uuid4())
    message = client.post(
        f"/api/v1/agent-runs/{run_id}/messages",
        headers={**normal_user_token_headers, "Idempotency-Key": message_key},
        json={"message": "Use correlation only; do not infer causality."},
    )
    message_replay = client.post(
        f"/api/v1/agent-runs/{run_id}/messages",
        headers={**normal_user_token_headers, "Idempotency-Key": message_key},
        json={"message": "Use correlation only; do not infer causality."},
    )
    assert message.status_code == message_replay.status_code == 202
    assert message_replay.json()["meta"]["idempotency_replayed"] is True
    assert len(message.json()["data"]["events"]) == 1
    assert "agent_run.continue" not in message.json()["data"]["allowed_actions"]
    assert (
        message.json()["data"]["disabled_reasons"]["agent_run.continue"]
        == "AGENT_RESUME_PENDING"
    )

    cancel_key = str(uuid.uuid4())
    cancelled = client.post(
        f"/api/v1/agent-runs/{run_id}/cancel",
        headers={**normal_user_token_headers, "Idempotency-Key": cancel_key},
    )
    cancel_replay = client.post(
        f"/api/v1/agent-runs/{run_id}/cancel",
        headers={**normal_user_token_headers, "Idempotency-Key": cancel_key},
    )
    assert cancelled.status_code == cancel_replay.status_code == 202
    assert cancelled.json()["data"]["status"] == "CANCELLED"
    assert cancel_replay.json()["meta"]["idempotency_replayed"] is True
    persisted = db.get(AgentRun, run_id)
    assert persisted is not None and persisted.status == AgentRunStatus.CANCELLED
