from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from sqlalchemy import delete, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlmodel import Session, select

from app.api.errors import ContractError
from app.approvals import service
from app.approvals.schemas import ApprovalItemDecision
from app.core.config import settings
from app.models import (
    ApprovalItem,
    ApprovalRecord,
    ApprovalStatus,
    ApprovalType,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    User,
    get_datetime_utc,
)
from app.projects.schemas import ProjectCreate
from app.projects.service import create_project


def make_project(db: Session, actor: User) -> uuid.UUID:
    result = create_project(
        db,
        actor=actor,
        payload=ProjectCreate(name="Approval project", project_type="RESEARCH"),
        idempotency_key=str(uuid.uuid4()),
    )
    assert result.data is not None
    return uuid.UUID(str(result.data["id"]))


def make_approval(
    db: Session,
    *,
    project_id: uuid.UUID,
    requester_id: uuid.UUID,
    payload: dict[str, object],
    expires_at: object = None,
    supersedes_approval_id: uuid.UUID | None = None,
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
            impact_summary={"summary": "Fixture only", "secret": "hidden"},
            expires_at=expires_at,  # type: ignore[arg-type]
            supersedes_approval_id=supersedes_approval_id,
            items=(
                service.ApprovalItemCreate(
                    item_type="fixture-action", item_id=uuid.uuid4()
                ),
            ),
        ),
    )
    db.commit()
    db.refresh(approval)
    return approval


def test_internal_create_hashes_payload_and_supersedes_pending_history(
    db: Session,
) -> None:
    actor = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).one()
    project_id = make_project(db, actor)
    first = make_approval(
        db,
        project_id=project_id,
        requester_id=actor.id,
        payload={"version": 1},
    )
    replacement = service.create_approval(
        db,
        command=service.ApprovalCreate(
            project_id=project_id,
            approval_type=ApprovalType.ANALYSIS_PLAN_APPROVAL,
            target_object_type=first.target_object_type,
            target_object_id=first.target_object_id,
            requested_by_actor_type=AuditActorType.USER,
            requested_by_actor_id=str(actor.id),
            payload_snapshot={"version": 2},
            supersedes_approval_id=first.id,
        ),
    )
    db.commit()
    db.refresh(first)
    assert first.status == ApprovalStatus.SUPERSEDED
    assert replacement.status == ApprovalStatus.PENDING
    assert replacement.supersedes_approval_id == first.id
    assert replacement.payload_hash == service.project_service.request_hash(
        {"version": 2}
    )
    actions = db.exec(
        select(AuditLog.action).where(
            AuditLog.approval_id.in_([first.id, replacement.id])
        )
    ).all()
    assert "APPROVAL_SUPERSEDED" in actions
    assert "APPROVAL_REQUESTED" in actions


def test_audit_log_rejects_unknown_approval_reference(db: Session) -> None:
    actor = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).one()
    project_id = make_project(db, actor)
    invalid_audit = AuditLog(
        project_id=project_id,
        actor_type=AuditActorType.SYSTEM,
        actor_id="approval-fk-test",
        action="APPROVAL_REFERENCE_TEST",
        object_type="approval",
        object_id=uuid.uuid4(),
        approval_id=uuid.uuid4(),
        outcome=AuditOutcome.FAILED,
    )

    savepoint = db.begin_nested()
    db.add(invalid_audit)
    with pytest.raises(IntegrityError):
        db.flush()
    savepoint.rollback()


@pytest.mark.parametrize("actor_type", [AuditActorType.AGENT, AuditActorType.WORKER])
def test_agent_and_worker_cannot_decide(
    db: Session, actor_type: AuditActorType, monkeypatch: pytest.MonkeyPatch
) -> None:
    actor = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).one()
    project_id = make_project(db, actor)
    payload = {"version": 1}
    approval = make_approval(
        db,
        project_id=project_id,
        requester_id=actor.id,
        payload=payload,
    )
    monkeypatch.setitem(
        service.payload_resolvers,
        "contract-fixture",
        lambda _session, _approval: payload,
    )
    with pytest.raises(ContractError) as error:
        service.decide_approval(
            db,
            actor=actor,
            approval_id=approval.id,
            decision=ApprovalStatus.APPROVED,
            decision_reason="not a user",
            item_decisions=[],
            idempotency_key=str(uuid.uuid4()),
            actor_type=actor_type,
        )
    assert error.value.status_code == 403
    db.refresh(approval)
    assert approval.status == ApprovalStatus.PENDING


def test_stale_and_expired_approvals_transition_without_decision(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    actor = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).one()
    project_id = make_project(db, actor)
    stale = make_approval(
        db,
        project_id=project_id,
        requester_id=actor.id,
        payload={"version": 1},
    )
    monkeypatch.setitem(
        service.payload_resolvers,
        "contract-fixture",
        lambda _session, _approval: {"version": 2},
    )
    with pytest.raises(ContractError) as stale_error:
        service.decide_approval(
            db,
            actor=actor,
            approval_id=stale.id,
            decision=ApprovalStatus.APPROVED,
            decision_reason="stale",
            item_decisions=[],
            idempotency_key=str(uuid.uuid4()),
        )
    assert stale_error.value.code == "APPROVAL_STALE"
    db.refresh(stale)
    assert stale.status == ApprovalStatus.SUPERSEDED
    assert stale.decision_by_user_id is None

    expired = make_approval(
        db,
        project_id=project_id,
        requester_id=actor.id,
        payload={"version": 1},
        expires_at=get_datetime_utc() - timedelta(seconds=1),
    )
    with pytest.raises(ContractError) as expired_error:
        service.decide_approval(
            db,
            actor=actor,
            approval_id=expired.id,
            decision=ApprovalStatus.APPROVED,
            decision_reason="too late",
            item_decisions=[],
            idempotency_key=str(uuid.uuid4()),
        )
    assert expired_error.value.code == "APPROVAL_EXPIRED"
    db.refresh(expired)
    assert expired.status == ApprovalStatus.EXPIRED
    assert expired.decision_by_user_id is None


def test_approved_record_and_items_are_database_immutable(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    actor = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).one()
    project_id = make_project(db, actor)
    payload = {"version": 1}
    approval = make_approval(
        db,
        project_id=project_id,
        requester_id=actor.id,
        payload=payload,
    )
    item = db.exec(
        select(ApprovalItem).where(ApprovalItem.approval_record_id == approval.id)
    ).one()
    monkeypatch.setitem(
        service.payload_resolvers,
        "contract-fixture",
        lambda _session, _approval: payload,
    )
    service.decide_approval(
        db,
        actor=actor,
        approval_id=approval.id,
        decision=ApprovalStatus.APPROVED,
        decision_reason="reviewed",
        item_decisions=[
            ApprovalItemDecision(
                item_type=item.item_type,
                item_id=item.item_id,
                decision="ACCEPT",
            )
        ],
        idempotency_key=str(uuid.uuid4()),
    )
    with pytest.raises(DBAPIError):
        db.execute(
            update(ApprovalRecord)
            .where(ApprovalRecord.id == approval.id)
            .values(decision_reason="tampered")
        )
        db.commit()
    db.rollback()
    with pytest.raises(DBAPIError):
        db.execute(
            update(ApprovalItem)
            .where(ApprovalItem.id == item.id)
            .values(decision="REWRITE")
        )
        db.commit()
    db.rollback()
    with pytest.raises(DBAPIError):
        db.execute(delete(ApprovalRecord).where(ApprovalRecord.id == approval.id))
        db.commit()
    db.rollback()
    stored = db.get(ApprovalRecord, approval.id)
    stored_item = db.get(ApprovalItem, item.id)
    assert stored is not None and stored.decision_reason == "reviewed"
    assert stored_item is not None and stored_item.decision == "ACCEPT"
