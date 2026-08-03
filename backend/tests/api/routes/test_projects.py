import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.models import (
    AuditLog,
    ProjectMember,
    ProjectMemberRole,
    ResearchProject,
    UserCreate,
    UserUpdate,
)
from tests.utils.user import (
    create_random_user,
    user_authentication_headers,
)
from tests.utils.utils import random_lower_string


def create_project(
    client: TestClient, headers: dict[str, str], *, name: str = "API project"
) -> dict[str, object]:
    response = client.post(
        "/api/v1/projects",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"name": name, "project_type": "RESEARCH"},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_project_create_requires_idempotency_and_replays(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    payload = {"name": "Idempotent API project", "project_type": "RESEARCH"}
    missing = client.post(
        "/api/v1/projects", headers=normal_user_token_headers, json=payload
    )
    assert missing.status_code == 400
    assert missing.json()["error"]["code"] == "MISSING_IDEMPOTENCY_KEY"

    key = str(uuid.uuid4())
    first = client.post(
        "/api/v1/projects",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json=payload,
    )
    replay = client.post(
        "/api/v1/projects",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json=payload,
    )
    assert first.status_code == replay.status_code == 201
    assert first.json()["data"] == replay.json()["data"]
    assert "project.update" in first.json()["data"]["allowed_actions"]
    assert "project.delete" in first.json()["data"]["allowed_actions"]
    assert replay.json()["meta"]["idempotency_replayed"] is True


def test_project_and_member_envelopes_project_formal_actions(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    project = create_project(client, normal_user_token_headers)
    detail = client.get(
        f"/api/v1/projects/{project['id']}", headers=normal_user_token_headers
    )
    members = client.get(
        f"/api/v1/projects/{project['id']}/members",
        headers=normal_user_token_headers,
    )

    assert detail.status_code == members.status_code == 200
    assert "project.update" in detail.json()["data"]["allowed_actions"]
    assert "project.manage_members" in members.json()["allowed_actions"]
    assert "artifact.upload" in members.json()["allowed_actions"]


def test_project_isolation_returns_no_disclosure_404(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    project = create_project(client, normal_user_token_headers)
    password = random_lower_string()
    outsider = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com", password=password
        ),
    )
    outsider_headers = user_authentication_headers(
        client=client, email=outsider.email, password=password
    )

    response = client.get(f"/api/v1/projects/{project['id']}", headers=outsider_headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_member_mutation_transfer_and_audit_projection(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    project = create_project(client, normal_user_token_headers)
    member = create_random_user(db)
    add = client.post(
        f"/api/v1/projects/{project['id']}/members",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"user_id": str(member.id), "role": "EDITOR"},
    )
    assert add.status_code == 201, add.text
    membership = add.json()["data"]

    transfer = client.patch(
        f"/api/v1/projects/{project['id']}/members/{membership['id']}",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={
            "role": "OWNER",
            "transfer_ownership": True,
            "previous_owner_role": "EDITOR",
            "reason": "Transfer through public API.",
        },
    )
    assert transfer.status_code == 200, transfer.text
    assert transfer.json()["data"]["project_owner_id"] == str(member.id)

    audit = client.get(
        f"/api/v1/projects/{project['id']}/audit-logs",
        headers=normal_user_token_headers,
    )
    assert audit.status_code == 200
    actions = [item["action"] for item in audit.json()["data"]]
    assert "PROJECT_CREATED" in actions
    assert "PROJECT_MEMBER_ADDED" in actions
    assert "PROJECT_OWNERSHIP_TRANSFERRED" in actions
    assert (
        client.post(
            f"/api/v1/projects/{project['id']}/audit-logs",
            headers=normal_user_token_headers,
            json={},
        ).status_code
        == 405
    )


def test_project_update_uses_if_match_and_member_cannot_cross_modify(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    first = create_project(client, normal_user_token_headers, name="First")
    second_owner = create_random_user(db)
    password = random_lower_string()
    crud.update_user(
        session=db, db_user=second_owner, user_in=UserUpdate(password=password)
    )
    second_headers = user_authentication_headers(
        client=client, email=second_owner.email, password=password
    )
    second = create_project(client, second_headers, name="Second")

    updated = client.patch(
        f"/api/v1/projects/{first['id']}",
        headers={**normal_user_token_headers, "If-Match": '"1"'},
        json={"name": "Updated"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["lock_version"] == 2

    stale = client.patch(
        f"/api/v1/projects/{first['id']}",
        headers={**normal_user_token_headers, "If-Match": '"1"'},
        json={"name": "Stale"},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "RESOURCE_VERSION_CONFLICT"

    cross = client.patch(
        f"/api/v1/projects/{second['id']}",
        headers={**normal_user_token_headers, "If-Match": '"1"'},
        json={"name": "Cross-project write"},
    )
    assert cross.status_code == 404
    assert cross.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_owner_remove_is_rejected_and_audit_is_not_client_writable(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    project = create_project(client, normal_user_token_headers)
    owner_member = db.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == uuid.UUID(str(project["id"])),
            ProjectMember.role == ProjectMemberRole.OWNER,
        )
    ).one()
    response = client.delete(
        f"/api/v1/projects/{project['id']}/members/{owner_member.id}",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "LAST_PROJECT_OWNER"
    assert db.get(ResearchProject, uuid.UUID(str(project["id"]))) is not None
    assert db.exec(
        select(AuditLog).where(AuditLog.project_id == uuid.UUID(str(project["id"])))
    ).all()


def test_member_add_idempotency_replay_and_conflict(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    project = create_project(client, normal_user_token_headers)
    first_user = create_random_user(db)
    second_user = create_random_user(db)
    key = str(uuid.uuid4())
    headers = {**normal_user_token_headers, "Idempotency-Key": key}

    first = client.post(
        f"/api/v1/projects/{project['id']}/members",
        headers=headers,
        json={"user_id": str(first_user.id), "role": "VIEWER"},
    )
    replay = client.post(
        f"/api/v1/projects/{project['id']}/members",
        headers=headers,
        json={"user_id": str(first_user.id), "role": "VIEWER"},
    )
    conflict = client.post(
        f"/api/v1/projects/{project['id']}/members",
        headers=headers,
        json={"user_id": str(second_user.id), "role": "VIEWER"},
    )

    assert first.status_code == replay.status_code == 201
    assert first.json()["data"] == replay.json()["data"]
    assert replay.json()["meta"]["idempotency_replayed"] is True
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_non_member_cannot_discover_members_or_audit(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    project = create_project(client, normal_user_token_headers)
    password = random_lower_string()
    outsider = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com", password=password
        ),
    )
    outsider_headers = user_authentication_headers(
        client=client, email=outsider.email, password=password
    )

    for path in (
        f"/api/v1/projects/{project['id']}/members",
        f"/api/v1/projects/{project['id']}/audit-logs",
    ):
        response = client.get(path, headers=outsider_headers)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_only_owner_can_archive_and_restore_project(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    project = create_project(client, normal_user_token_headers)
    password = random_lower_string()
    editor = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com", password=password
        ),
    )
    add = client.post(
        f"/api/v1/projects/{project['id']}/members",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"user_id": str(editor.id), "role": "EDITOR"},
    )
    assert add.status_code == 201, add.text
    editor_headers = user_authentication_headers(
        client=client, email=editor.email, password=password
    )

    forbidden = client.post(
        f"/api/v1/projects/{project['id']}/archive", headers=editor_headers
    )
    archived = client.post(
        f"/api/v1/projects/{project['id']}/archive",
        headers=normal_user_token_headers,
    )
    restored = client.post(
        f"/api/v1/projects/{project['id']}/restore",
        headers=normal_user_token_headers,
    )

    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "PERMISSION_DENIED"
    assert archived.status_code == 200
    assert archived.json()["data"]["status"] == "ARCHIVED"
    assert restored.status_code == 200
    assert restored.json()["data"]["status"] == "ACTIVE"
