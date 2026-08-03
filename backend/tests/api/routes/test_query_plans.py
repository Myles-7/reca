import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.api.routes import query_plans as route_module
from app.models import UserCreate
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


def test_query_plan_api_crud_if_match_and_provider_rejection(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    question = create_question(client, normal_user_token_headers, project_id)
    version_id = question["current_version"]["id"]
    create_path = f"/api/v1/projects/{project_id}/query-plans"
    headers = {
        **normal_user_token_headers,
        "Idempotency-Key": str(uuid.uuid4()),
    }
    rejected = client.post(
        create_path,
        headers=headers,
        json={"research_question_version_id": version_id, "provider": "OpenAlex"},
    )
    assert rejected.status_code == 422

    created = client.post(
        create_path,
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={
            "research_question_version_id": version_id,
            "filters": {
                "from_year": 2020,
                "to_year": 2026,
                "languages": ["zh", "en"],
                "work_types": ["article"],
                "open_access_only": True,
            },
        },
    )
    assert created.status_code == 201, created.text
    plan = created.json()["data"]
    assert plan["status"] == "DRAFT" and plan["lock_version"] == 1
    plan_path = f"/api/v1/query-plans/{plan['id']}"
    fetched = client.get(plan_path, headers=normal_user_token_headers)
    assert fetched.status_code == 200

    updated = client.patch(
        plan_path,
        headers={**normal_user_token_headers, "If-Match": '"1"'},
        json={
            "fields": {
                "chinese_terms": ["学习投入"],
                "english_terms": ["student engagement"],
                "boolean_query": '"student engagement"',
            },
            "change_reason": "Reviewed terms.",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["lock_version"] == 2
    missing_if_match = client.patch(
        plan_path,
        headers=normal_user_token_headers,
        json={
            "fields": {"boolean_query": '"learning engagement"'},
            "change_reason": "Missing version precondition.",
        },
    )
    assert missing_if_match.status_code == 400
    assert missing_if_match.json()["error"]["code"] == "VALIDATION_ERROR"
    malformed_if_match = client.patch(
        plan_path,
        headers={**normal_user_token_headers, "If-Match": '"unknown"'},
        json={
            "fields": {"boolean_query": '"learning engagement"'},
            "change_reason": "Malformed version precondition.",
        },
    )
    assert malformed_if_match.status_code == 400
    assert malformed_if_match.json()["error"]["code"] == "VALIDATION_ERROR"
    stale = client.patch(
        plan_path,
        headers={**normal_user_token_headers, "If-Match": '"1"'},
        json={
            "fields": {"boolean_query": '"learning engagement"'},
            "change_reason": "Stale update.",
        },
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "RESOURCE_VERSION_CONFLICT"


def test_query_plan_api_role_and_no_disclosure_boundaries(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    question = create_question(client, normal_user_token_headers, project_id)
    created = client.post(
        f"/api/v1/projects/{project_id}/query-plans",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"research_question_version_id": question["current_version"]["id"]},
    )
    plan_id = created.json()["data"]["id"]

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
    add_member(client, normal_user_token_headers, project_id, viewer.id, "VIEWER")
    assert (
        client.get(f"/api/v1/query-plans/{plan_id}", headers=viewer_headers).status_code
        == 200
    )
    denied = client.patch(
        f"/api/v1/query-plans/{plan_id}",
        headers={**viewer_headers, "If-Match": '"1"'},
        json={
            "fields": {"chinese_terms": ["越权"]},
            "change_reason": "Should fail.",
        },
    )
    assert denied.status_code == 403

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
    hidden = client.get(f"/api/v1/query-plans/{plan_id}", headers=outsider_headers)
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_query_plan_generate_api_is_idempotent_and_provider_neutral(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispatcher = FakeDispatcher()
    monkeypatch.setattr(route_module, "dispatcher", dispatcher)
    project_id = create_project(client, normal_user_token_headers)
    question = create_question(client, normal_user_token_headers, project_id)
    created = client.post(
        f"/api/v1/projects/{project_id}/query-plans",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"research_question_version_id": question["current_version"]["id"]},
    )
    plan_id = created.json()["data"]["id"]
    path = f"/api/v1/query-plans/{plan_id}/generate"
    key = str(uuid.uuid4())
    headers = {**normal_user_token_headers, "Idempotency-Key": key}
    rejected = client.post(path, headers=headers, json={"provider": "OpenAlex"})
    assert rejected.status_code == 422
    first = client.post(path, headers=headers, json={})
    replay = client.post(path, headers=headers, json={})
    assert first.status_code == replay.status_code == 202
    assert first.json()["data"] == replay.json()["data"]
    assert replay.json()["meta"]["idempotency_replayed"] is True
    assert len(dispatcher.job_ids) == 1
