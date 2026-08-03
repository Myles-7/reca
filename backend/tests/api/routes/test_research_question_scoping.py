import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.api.routes import research_questions as route_module
from app.models import Job, ModelInvocation, ProcessingRun, UserCreate
from tests.api.routes.test_research_questions import (
    add_member,
    create_project,
    create_question,
)
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_lower_string


class FakeDispatcher:
    def __init__(self) -> None:
        self.job_ids: list[uuid.UUID] = []

    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        assert task_id
        self.job_ids.append(job_id)


def test_parse_api_creates_idempotent_governed_job(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispatcher = FakeDispatcher()
    monkeypatch.setattr(route_module, "dispatcher", dispatcher)
    project_id = create_project(client, normal_user_token_headers)
    question = create_question(client, normal_user_token_headers, project_id)
    version_id = str(question["current_version"]["id"])
    path = f"/api/v1/research-question-versions/{version_id}/parse"

    missing = client.post(
        path,
        headers=normal_user_token_headers,
        json={"max_follow_up_questions": 3, "language": "zh-CN"},
    )
    assert missing.status_code == 400
    assert missing.json()["error"]["code"] == "MISSING_IDEMPOTENCY_KEY"

    key = str(uuid.uuid4())
    headers = {**normal_user_token_headers, "Idempotency-Key": key}
    payload = {"max_follow_up_questions": 3, "language": "zh-CN"}
    created = client.post(path, headers=headers, json=payload)
    replay = client.post(path, headers=headers, json=payload)
    conflict = client.post(
        path,
        headers=headers,
        json={"max_follow_up_questions": 2, "language": "zh-CN"},
    )
    assert created.status_code == replay.status_code == 202
    assert created.json()["data"] == replay.json()["data"]
    assert replay.json()["meta"]["idempotency_replayed"] is True
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"

    job_id = uuid.UUID(created.json()["data"]["id"])
    job = db.get(Job, job_id)
    assert job is not None
    invocation = db.get(ModelInvocation, job.resource_id)
    assert invocation is not None
    assert invocation.source_ids == [version_id]
    assert db.get(ProcessingRun, job.id) is None
    assert dispatcher.job_ids == [job.id]


def test_parse_api_preserves_role_and_no_disclosure_boundaries(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(route_module, "dispatcher", FakeDispatcher())
    project_id = create_project(client, normal_user_token_headers)
    question = create_question(client, normal_user_token_headers, project_id)
    version_id = str(question["current_version"]["id"])
    path = f"/api/v1/research-question-versions/{version_id}/parse"

    password = random_lower_string()
    viewer = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com", password=password
        ),
    )
    viewer_headers = user_authentication_headers(
        client=client, email=viewer.email, password=password
    )
    add_member(
        client,
        normal_user_token_headers,
        project_id,
        viewer.id,
        "VIEWER",
    )
    denied = client.post(
        path,
        headers={**viewer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={},
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"

    outsider_password = random_lower_string()
    outsider = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com",
            password=outsider_password,
        ),
    )
    outsider_headers = user_authentication_headers(
        client=client, email=outsider.email, password=outsider_password
    )
    hidden = client.post(
        path,
        headers={**outsider_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={},
    )
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
