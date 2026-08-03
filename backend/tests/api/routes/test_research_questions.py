import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.models import AuditLog, User, UserCreate, UserUpdate
from tests.utils.user import create_random_user, user_authentication_headers
from tests.utils.utils import random_lower_string


def create_project(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/projects",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"name": "Research question API", "project_type": "RESEARCH"},
    )
    assert response.status_code == 201, response.text
    return str(response.json()["data"]["id"])


def create_question(
    client: TestClient, headers: dict[str, str], project_id: str
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/projects/{project_id}/research-questions",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"raw_input": "How does generative AI relate to engagement?"},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def add_member(
    client: TestClient,
    headers: dict[str, str],
    project_id: str,
    user_id: uuid.UUID,
    role: str,
) -> None:
    response = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"user_id": str(user_id), "role": role},
    )
    assert response.status_code == 201, response.text


def create_user_headers(client: TestClient, db: Session) -> tuple[User, dict[str, str]]:
    password = random_lower_string()
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com",
            password=password,
        ),
    )
    return user, user_authentication_headers(
        client=client, email=user.email, password=password
    )


def test_research_question_vertical_contract(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    empty = client.get(
        f"/api/v1/projects/{project_id}/research-question",
        headers=normal_user_token_headers,
    )
    assert empty.status_code == 200
    assert empty.json()["data"]["question"] is None
    assert empty.json()["data"]["allowed_actions"] == ["research_question.create"]
    assert empty.json()["data"]["capability_availability"] == {
        "research_question": "AVAILABLE",
        "ai_parse": "NOT_AVAILABLE",
        "query_plan": "NOT_AVAILABLE",
        "literature": "NOT_AVAILABLE",
    }

    question = create_question(client, normal_user_token_headers, project_id)
    question_id = str(question["id"])
    first = question["current_version"]
    first_id = str(first["id"])
    assert first["status"] == "DRAFT"
    assert first["is_current"] is True
    assert first["allowed_actions"] == [
        "research_question.edit",
        "research_question.create_version",
        "research_question.mark_ready",
    ]

    saved = client.post(
        f"/api/v1/research-questions/{question_id}/versions",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={
            "based_on_version_id": first_id,
            "change_reason": "Narrow the population.",
            "fields": {"population": "Teacher education students"},
        },
    )
    assert saved.status_code == 201, saved.text
    second = saved.json()["data"]
    second_id = str(second["id"])
    assert second["version_number"] == 2

    ready = client.post(
        f"/api/v1/research-question-versions/{second_id}/ready",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"reason": "Structured fields reviewed."},
    )
    assert ready.status_code == 200, ready.text
    assert ready.json()["data"]["allowed_actions"] == [
        "research_question.create_version",
        "research_question.request_confirmation",
    ]

    requested = client.post(
        f"/api/v1/research-question-versions/{second_id}/approval-requests",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
    )
    assert requested.status_code == 201, requested.text
    approval_id = requested.json()["data"]["id"]

    current = client.get(
        f"/api/v1/projects/{project_id}/research-question",
        headers=normal_user_token_headers,
    )
    projected = current.json()["data"]["question"]["current_version"]
    assert projected["pending_approval_id"] == approval_id
    assert projected["pending_approval_status"] == "PENDING"
    assert "research_question.request_confirmation" not in projected["allowed_actions"]

    approved = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"decision_reason": "Scope confirmed.", "item_decisions": []},
    )
    assert approved.status_code == 200, approved.text
    confirmed = client.get(
        f"/api/v1/research-question-versions/{second_id}",
        headers=normal_user_token_headers,
    )
    assert confirmed.json()["data"]["status"] == "CONFIRMED"
    actions = set(
        db.exec(
            select(AuditLog.action).where(AuditLog.project_id == uuid.UUID(project_id))
        ).all()
    )
    assert {
        "RESEARCH_QUESTION_CREATED",
        "RESEARCH_QUESTION_VERSION_CREATED",
        "RESEARCH_QUESTION_VERSION_STATUS_CHANGED",
        "RESEARCH_QUESTION_CONFIRMATION_REQUESTED",
        "RESEARCH_QUESTION_CONFIRMED",
    } <= actions


def test_research_question_idempotency_and_if_match(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    payload = {"raw_input": "Idempotent research question"}
    missing = client.post(
        f"/api/v1/projects/{project_id}/research-questions",
        headers=normal_user_token_headers,
        json=payload,
    )
    assert missing.status_code == 400
    assert missing.json()["error"]["code"] == "MISSING_IDEMPOTENCY_KEY"

    create_key = str(uuid.uuid4())
    create_headers = {
        **normal_user_token_headers,
        "Idempotency-Key": create_key,
    }
    first = client.post(
        f"/api/v1/projects/{project_id}/research-questions",
        headers=create_headers,
        json=payload,
    )
    replay = client.post(
        f"/api/v1/projects/{project_id}/research-questions",
        headers=create_headers,
        json=payload,
    )
    conflict = client.post(
        f"/api/v1/projects/{project_id}/research-questions",
        headers=create_headers,
        json={"raw_input": "Different payload"},
    )
    assert first.status_code == replay.status_code == 201
    assert first.json()["data"] == replay.json()["data"]
    assert replay.json()["meta"]["idempotency_replayed"] is True
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"

    question = first.json()["data"]
    question_id = question["id"]
    first_id = question["current_version"]["id"]
    version_body = {
        "based_on_version_id": first_id,
        "change_reason": "Add population.",
        "fields": {"population": "Teacher education students"},
    }
    version_key = str(uuid.uuid4())
    version_headers = {
        **normal_user_token_headers,
        "Idempotency-Key": version_key,
    }
    saved = client.post(
        f"/api/v1/research-questions/{question_id}/versions",
        headers=version_headers,
        json=version_body,
    )
    saved_replay = client.post(
        f"/api/v1/research-questions/{question_id}/versions",
        headers=version_headers,
        json=version_body,
    )
    assert saved.status_code == saved_replay.status_code == 201
    assert saved_replay.json()["meta"]["idempotency_replayed"] is True
    second_id = saved.json()["data"]["id"]

    update_body = {
        "change_reason": "Add context.",
        "fields": {"context": "Higher education"},
    }
    missing_match = client.patch(
        f"/api/v1/research-question-versions/{second_id}",
        headers=normal_user_token_headers,
        json=update_body,
    )
    assert missing_match.status_code == 400
    updated = client.patch(
        f"/api/v1/research-question-versions/{second_id}",
        headers={**normal_user_token_headers, "If-Match": '"2"'},
        json=update_body,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["version_number"] == 3
    stale = client.patch(
        f"/api/v1/research-question-versions/{second_id}",
        headers={**normal_user_token_headers, "If-Match": '"2"'},
        json=update_body,
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "RESOURCE_VERSION_CONFLICT"


def test_research_question_role_matrix_and_confirmed_version_is_immutable(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    question = create_question(client, normal_user_token_headers, project_id)
    question_id = str(question["id"])
    first_id = str(question["current_version"]["id"])
    role_headers: dict[str, dict[str, str]] = {"OWNER": normal_user_token_headers}
    for role in ("EDITOR", "REVIEWER", "VIEWER"):
        user, headers = create_user_headers(client, db)
        add_member(
            client,
            normal_user_token_headers,
            project_id,
            user.id,
            role,
        )
        role_headers[role] = headers

    for headers in role_headers.values():
        assert (
            client.get(
                f"/api/v1/projects/{project_id}/research-question", headers=headers
            ).status_code
            == 200
        )

    editor_save = client.post(
        f"/api/v1/research-questions/{question_id}/versions",
        headers={
            **role_headers["EDITOR"],
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={
            "based_on_version_id": first_id,
            "change_reason": "Editor refinement.",
            "fields": {"context": "Higher education"},
        },
    )
    assert editor_save.status_code == 201
    second_id = editor_save.json()["data"]["id"]
    for role in ("REVIEWER", "VIEWER"):
        denied = client.post(
            f"/api/v1/research-questions/{question_id}/versions",
            headers={
                **role_headers[role],
                "Idempotency-Key": str(uuid.uuid4()),
            },
            json={
                "based_on_version_id": second_id,
                "change_reason": f"{role} attempt.",
                "fields": {"context": role},
            },
        )
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "PERMISSION_DENIED"

    ready = client.post(
        f"/api/v1/research-question-versions/{second_id}/ready",
        headers={
            **role_headers["EDITOR"],
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"reason": "Editor completed review."},
    )
    assert ready.status_code == 200
    requested = client.post(
        f"/api/v1/research-question-versions/{second_id}/approval-requests",
        headers={
            **role_headers["EDITOR"],
            "Idempotency-Key": str(uuid.uuid4()),
        },
    )
    assert requested.status_code == 201
    approval_id = requested.json()["data"]["id"]
    editor_decision = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers={
            **role_headers["EDITOR"],
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"decision_reason": "Editor cannot approve.", "item_decisions": []},
    )
    assert editor_decision.status_code == 403
    approved = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers={
            **role_headers["REVIEWER"],
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"decision_reason": "Reviewer confirms.", "item_decisions": []},
    )
    assert approved.status_code == 200
    immutable = client.patch(
        f"/api/v1/research-question-versions/{second_id}",
        headers={**role_headers["EDITOR"], "If-Match": '"2"'},
        json={
            "change_reason": "Illegal confirmed edit.",
            "fields": {"context": "Changed"},
        },
    )
    assert immutable.status_code == 409
    assert immutable.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


def test_research_question_permissions_and_project_isolation(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    question = create_question(client, normal_user_token_headers, project_id)
    version_id = str(question["current_version"]["id"])

    viewer = create_random_user(db)
    viewer_password = random_lower_string()
    crud.update_user(
        session=db,
        db_user=viewer,
        user_in=UserUpdate(password=viewer_password),
    )
    viewer_headers = user_authentication_headers(
        client=client, email=viewer.email, password=viewer_password
    )
    add_member(
        client,
        normal_user_token_headers,
        project_id,
        viewer.id,
        "VIEWER",
    )
    readable = client.get(
        f"/api/v1/projects/{project_id}/research-question",
        headers=viewer_headers,
    )
    assert readable.status_code == 200
    assert (
        readable.json()["data"]["question"]["current_version"]["allowed_actions"] == []
    )
    denied = client.post(
        f"/api/v1/research-question-versions/{version_id}/ready",
        headers={**viewer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"reason": "Viewer attempt"},
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
    other_project_id = create_project(client, outsider_headers)
    assert other_project_id != project_id
    hidden = client.get(
        f"/api/v1/research-question-versions/{version_id}",
        headers=outsider_headers,
    )
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_research_question_stale_base_and_illegal_transition(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    question = create_question(client, normal_user_token_headers, project_id)
    question_id = str(question["id"])
    first_id = str(question["current_version"]["id"])
    body = {
        "based_on_version_id": first_id,
        "change_reason": "First refinement.",
        "fields": {"context": "Higher education"},
    }
    first_save = client.post(
        f"/api/v1/research-questions/{question_id}/versions",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json=body,
    )
    assert first_save.status_code == 201
    stale = client.post(
        f"/api/v1/research-questions/{question_id}/versions",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={**body, "change_reason": "Stale refinement."},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "RESOURCE_VERSION_CONFLICT"

    second_id = first_save.json()["data"]["id"]
    ready_headers = {
        **normal_user_token_headers,
        "Idempotency-Key": str(uuid.uuid4()),
    }
    assert (
        client.post(
            f"/api/v1/research-question-versions/{second_id}/ready",
            headers=ready_headers,
            json={"reason": None},
        ).status_code
        == 200
    )
    illegal = client.post(
        f"/api/v1/research-question-versions/{second_id}/ready",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"reason": None},
    )
    assert illegal.status_code == 409
    assert illegal.json()["error"]["code"] == "INVALID_STATE_TRANSITION"
