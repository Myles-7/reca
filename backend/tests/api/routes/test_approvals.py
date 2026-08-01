from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.approvals import service
from app.core.config import settings
from app.models import (
    ApprovalRecord,
    ApprovalStatus,
    ApprovalType,
    AuditActorType,
    AuditLog,
    UserCreate,
    get_datetime_utc,
)
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_lower_string


def create_project(client: TestClient, headers: dict[str, str]) -> uuid.UUID:
    response = client.post(
        "/api/v1/projects",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"name": "Approval project", "project_type": "RESEARCH"},
    )
    assert response.status_code == 201
    return uuid.UUID(response.json()["data"]["id"])


def create_user_headers(
    client: TestClient, db: Session
) -> tuple[uuid.UUID, dict[str, str]]:
    password = random_lower_string()
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com", password=password
        ),
    )
    return user.id, user_authentication_headers(
        client=client, email=user.email, password=password
    )


def add_member(
    client: TestClient,
    *,
    owner_headers: dict[str, str],
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    role: str,
) -> None:
    response = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={**owner_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"user_id": str(user_id), "role": role},
    )
    assert response.status_code == 201


def create_fixture_approval(
    db: Session,
    *,
    project_id: uuid.UUID,
    requester_id: uuid.UUID,
    payload: dict[str, Any],
    expires_at: Any = None,
    with_item: bool = False,
) -> ApprovalRecord:
    approval = service.create_approval(
        db,
        command=service.ApprovalCreate(
            project_id=project_id,
            approval_type=ApprovalType.ANALYSIS_PLAN_APPROVAL,
            target_object_type="contract-fixture",
            target_object_id=uuid.uuid4(),
            requested_by_actor_type=AuditActorType.USER,
            requested_by_actor_id=str(requester_id),
            payload_snapshot=payload,
            impact_summary={"summary": "Fixture", "api_key": "not-public"},
            expires_at=expires_at,
            items=(
                service.ApprovalItemCreate(
                    item_type="fixture-action", item_id=uuid.uuid4()
                ),
            )
            if with_item
            else (),
        ),
    )
    db.commit()
    db.refresh(approval)
    return approval


@pytest.fixture
def current_payload(monkeypatch: pytest.MonkeyPatch) -> dict[str, dict[str, Any]]:
    state = {"value": {"version": 1, "api_key": "private"}}
    monkeypatch.setitem(
        service.payload_resolvers,
        "contract-fixture",
        lambda _session, _approval: state["value"],
    )
    return state


def test_list_detail_redaction_and_no_generic_create(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    actor = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert actor is not None
    approval = create_fixture_approval(
        db,
        project_id=project_id,
        requester_id=actor.id,
        payload={"version": 1, "api_key": "private"},
    )
    listing = client.get(
        f"/api/v1/projects/{project_id}/approvals",
        headers=normal_user_token_headers,
    )
    detail = client.get(
        f"/api/v1/approvals/{approval.id}", headers=normal_user_token_headers
    )
    no_generic_create = client.post(
        "/api/v1/approvals", headers=normal_user_token_headers, json={}
    )
    assert listing.status_code == detail.status_code == 200
    assert listing.json()["pagination"]["total"] == 1
    assert "payload_snapshot" not in listing.json()["data"][0]
    assert detail.json()["data"]["payload_snapshot"]["api_key"] == "[REDACTED]"
    assert detail.json()["data"]["impact_summary"]["api_key"] == "[REDACTED]"
    assert detail.json()["data"]["allowed_actions"] == [
        "approve",
        "reject",
        "cancel",
    ]
    assert no_generic_create.status_code == 404


def test_approve_replay_conflict_duplicate_and_audit(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    current_payload: dict[str, dict[str, Any]],
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    actor = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert actor is not None
    approval = create_fixture_approval(
        db,
        project_id=project_id,
        requester_id=actor.id,
        payload=current_payload["value"],
    )
    pending_overview = client.get(
        f"/api/v1/projects/{project_id}/overview",
        headers=normal_user_token_headers,
    )
    assert (
        pending_overview.json()["data"]["foundation_counts"]["approvals_pending"] == 1
    )
    key = str(uuid.uuid4())
    body = {"decision_reason": "Reviewed", "item_decisions": []}
    first = client.post(
        f"/api/v1/approvals/{approval.id}/approve",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json=body,
    )
    replay = client.post(
        f"/api/v1/approvals/{approval.id}/approve",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json=body,
    )
    conflict = client.post(
        f"/api/v1/approvals/{approval.id}/approve",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json={"decision_reason": "Different", "item_decisions": []},
    )
    repeated = client.post(
        f"/api/v1/approvals/{approval.id}/approve",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json=body,
    )
    assert first.status_code == replay.status_code == 200
    assert first.json()["data"]["status"] == "APPROVED"
    assert replay.json()["meta"]["idempotency_replayed"] is True
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert repeated.status_code == 409
    assert repeated.json()["error"]["code"] == "INVALID_STATE_TRANSITION"
    decided_overview = client.get(
        f"/api/v1/projects/{project_id}/overview",
        headers=normal_user_token_headers,
    )
    assert (
        decided_overview.json()["data"]["foundation_counts"]["approvals_pending"] == 0
    )
    audit = db.exec(
        select(AuditLog).where(
            AuditLog.approval_id == approval.id,
            AuditLog.action == "APPROVAL_APPROVED",
        )
    ).one()
    assert audit.actor_id == str(actor.id)
    assert audit.project_id == project_id
    assert audit.request_id


def test_role_isolation_stale_expired_and_cancel_rules(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    current_payload: dict[str, dict[str, Any]],
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    owner = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert owner is not None
    editor_id, editor_headers = create_user_headers(client, db)
    viewer_id, viewer_headers = create_user_headers(client, db)
    outsider_id, outsider_headers = create_user_headers(client, db)
    add_member(
        client,
        owner_headers=normal_user_token_headers,
        project_id=project_id,
        user_id=editor_id,
        role="EDITOR",
    )
    add_member(
        client,
        owner_headers=normal_user_token_headers,
        project_id=project_id,
        user_id=viewer_id,
        role="VIEWER",
    )
    stale = create_fixture_approval(
        db,
        project_id=project_id,
        requester_id=owner.id,
        payload=current_payload["value"],
    )
    assert (
        client.get(
            f"/api/v1/approvals/{stale.id}", headers=outsider_headers
        ).status_code
        == 404
    )
    denied = client.post(
        f"/api/v1/approvals/{stale.id}/approve",
        headers={**editor_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"decision_reason": "Editor cannot decide", "item_decisions": []},
    )
    assert denied.status_code == 403
    current_payload["value"] = {"version": 2, "api_key": "private"}
    stale_response = client.post(
        f"/api/v1/approvals/{stale.id}/approve",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"decision_reason": "Old payload", "item_decisions": []},
    )
    assert stale_response.status_code == 409
    assert stale_response.json()["error"]["code"] == "APPROVAL_STALE"
    db.refresh(stale)
    assert stale.status == ApprovalStatus.SUPERSEDED

    current_payload["value"] = {"version": 1, "api_key": "private"}
    expired = create_fixture_approval(
        db,
        project_id=project_id,
        requester_id=owner.id,
        payload=current_payload["value"],
        expires_at=get_datetime_utc() - timedelta(seconds=1),
    )
    expired_response = client.post(
        f"/api/v1/approvals/{expired.id}/reject",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"decision_reason": "Too late", "item_decisions": []},
    )
    assert expired_response.status_code == 409
    assert expired_response.json()["error"]["code"] == "APPROVAL_EXPIRED"

    requester_approval = create_fixture_approval(
        db,
        project_id=project_id,
        requester_id=viewer_id,
        payload=current_payload["value"],
    )
    cancel_key = str(uuid.uuid4())
    cancelled = client.post(
        f"/api/v1/approvals/{requester_approval.id}/cancel",
        headers={**viewer_headers, "Idempotency-Key": cancel_key},
    )
    cancel_replay = client.post(
        f"/api/v1/approvals/{requester_approval.id}/cancel",
        headers={**viewer_headers, "Idempotency-Key": cancel_key},
    )
    assert cancelled.status_code == cancel_replay.status_code == 200
    assert cancelled.json()["data"]["status"] == "CANCELLED"
    assert cancel_replay.json()["meta"]["idempotency_replayed"] is True

    owner_approval = create_fixture_approval(
        db,
        project_id=project_id,
        requester_id=owner.id,
        payload=current_payload["value"],
    )
    forbidden_cancel = client.post(
        f"/api/v1/approvals/{owner_approval.id}/cancel",
        headers={**viewer_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert forbidden_cancel.status_code == 403
    assert outsider_id != viewer_id


def test_reviewer_can_decide_and_item_coverage_is_required(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    current_payload: dict[str, dict[str, Any]],
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    owner = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert owner is not None
    reviewer_id, reviewer_headers = create_user_headers(client, db)
    add_member(
        client,
        owner_headers=normal_user_token_headers,
        project_id=project_id,
        user_id=reviewer_id,
        role="REVIEWER",
    )
    approval = create_fixture_approval(
        db,
        project_id=project_id,
        requester_id=owner.id,
        payload=current_payload["value"],
        with_item=True,
    )
    item = service._approval_items(db, approval.id)[0]
    missing = client.post(
        f"/api/v1/approvals/{approval.id}/approve",
        headers={**reviewer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"decision_reason": "Missing item", "item_decisions": []},
    )
    assert missing.status_code == 422
    accepted = client.post(
        f"/api/v1/approvals/{approval.id}/approve",
        headers={**reviewer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "decision_reason": "Reviewed each item",
            "item_decisions": [
                {
                    "item_type": item.item_type,
                    "item_id": str(item.item_id),
                    "decision": "ACCEPT",
                }
            ],
        },
    )
    assert accepted.status_code == 200
    assert accepted.json()["data"]["items"][0]["decision"] == "ACCEPT"


def test_superuser_decision_is_an_audited_administrative_override(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    current_payload: dict[str, dict[str, Any]],
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    owner = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    superuser = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert owner is not None and superuser is not None
    approval = create_fixture_approval(
        db,
        project_id=project_id,
        requester_id=owner.id,
        payload=current_payload["value"],
    )
    response = client.post(
        f"/api/v1/approvals/{approval.id}/reject",
        headers={**superuser_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"decision_reason": "Administrative review", "item_decisions": []},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "REJECTED"
    actions = db.exec(
        select(AuditLog.action).where(AuditLog.approval_id == approval.id)
    ).all()
    assert "PROJECT_ADMINISTRATIVE_OVERRIDE" in actions
    assert "APPROVAL_REJECTED" in actions
    override = db.exec(
        select(AuditLog).where(
            AuditLog.approval_id == approval.id,
            AuditLog.action == "PROJECT_ADMINISTRATIVE_OVERRIDE",
        )
    ).one()
    assert override.actor_id == str(superuser.id)


def test_superuser_empty_list_override_is_still_audited(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    response = client.get(
        f"/api/v1/projects/{project_id}/approvals",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"] == []
    audit = db.exec(
        select(AuditLog).where(
            AuditLog.project_id == project_id,
            AuditLog.action == "PROJECT_ADMINISTRATIVE_OVERRIDE",
            AuditLog.object_id == project_id,
        )
    ).one()
    assert audit.after_snapshot == {"permission": "approval.read:list"}
