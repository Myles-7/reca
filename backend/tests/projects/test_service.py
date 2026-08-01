import uuid

import pytest
from sqlalchemy import update
from sqlalchemy.exc import DBAPIError
from sqlmodel import Session, func, select

from app import crud
from app.api.errors import ContractError
from app.models import (
    AuditLog,
    ProjectMember,
    ProjectMemberRole,
    ResearchProject,
    User,
    UserCreate,
)
from app.projects import service
from app.projects.schemas import MemberAdd, MemberUpdate, ProjectCreate, ProjectUpdate
from tests.utils.user import create_random_user
from tests.utils.utils import random_email, random_lower_string


def project_input(name: str = "M1 project") -> ProjectCreate:
    return ProjectCreate(name=name, project_type="RESEARCH")


def create_project(
    db: Session, owner_email: str | None = None
) -> tuple[User, ResearchProject]:
    owner = (
        crud.create_user(
            session=db,
            user_create=UserCreate(
                email=owner_email or random_email(), password=random_lower_string()
            ),
        )
        if owner_email
        else create_random_user(db)
    )
    result = service.create_project(
        db,
        actor=owner,
        payload=project_input(),
        idempotency_key=str(uuid.uuid4()),
    )
    assert result.data is not None
    project = db.get(ResearchProject, uuid.UUID(result.data["id"]))
    assert project is not None
    return owner, project


def test_create_project_is_atomic_and_idempotent(db: Session) -> None:
    owner = create_random_user(db)
    payload = project_input("Atomic project")
    key = str(uuid.uuid4())

    first = service.create_project(
        db, actor=owner, payload=payload, idempotency_key=key
    )
    replay = service.create_project(
        db, actor=owner, payload=payload, idempotency_key=key
    )

    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.idempotency_replayed is True
    assert replay.data == first.data
    project_id = uuid.UUID(first.data["id"]) if first.data else None
    members = db.exec(
        select(ProjectMember).where(ProjectMember.project_id == project_id)
    ).all()
    audits = db.exec(select(AuditLog).where(AuditLog.project_id == project_id)).all()
    assert [(member.user_id, member.role) for member in members] == [
        (owner.id, ProjectMemberRole.OWNER)
    ]
    assert [audit.action for audit in audits] == ["PROJECT_CREATED"]

    with pytest.raises(ContractError, match="different request") as exc_info:
        service.create_project(
            db,
            actor=owner,
            payload=project_input("Different payload"),
            idempotency_key=key,
        )
    assert exc_info.value.code == "IDEMPOTENCY_CONFLICT"


def test_cross_project_read_is_not_disclosed(db: Session) -> None:
    _owner, project = create_project(db)
    outsider = create_random_user(db)

    with pytest.raises(ContractError) as exc_info:
        service.get_project(db, actor=outsider, project_id=project.id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "RESOURCE_NOT_FOUND"


def test_editor_can_update_project_but_cannot_manage_members(db: Session) -> None:
    owner, project = create_project(db)
    editor = create_random_user(db)
    service.add_member(
        db,
        actor=owner,
        project_id=project.id,
        payload=MemberAdd(user_id=editor.id, role=ProjectMemberRole.EDITOR),
        idempotency_key=str(uuid.uuid4()),
    )

    updated = service.update_project(
        db,
        actor=editor,
        project_id=project.id,
        payload=ProjectUpdate(name="Editor update"),
        expected_lock_version=1,
    )
    assert updated["name"] == "Editor update"
    assert updated["lock_version"] == 2

    with pytest.raises(ContractError) as exc_info:
        service.add_member(
            db,
            actor=editor,
            project_id=project.id,
            payload=MemberAdd(
                user_id=create_random_user(db).id, role=ProjectMemberRole.VIEWER
            ),
            idempotency_key=str(uuid.uuid4()),
        )
    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "PERMISSION_DENIED"


def test_optimistic_lock_conflict_has_current_version(db: Session) -> None:
    owner, project = create_project(db)
    service.update_project(
        db,
        actor=owner,
        project_id=project.id,
        payload=ProjectUpdate(name="First update"),
        expected_lock_version=1,
    )

    with pytest.raises(ContractError) as exc_info:
        service.update_project(
            db,
            actor=owner,
            project_id=project.id,
            payload=ProjectUpdate(name="Stale update"),
            expected_lock_version=1,
        )

    assert exc_info.value.code == "RESOURCE_VERSION_CONFLICT"
    assert exc_info.value.details == {
        "expected_lock_version": 1,
        "current_lock_version": 2,
    }


def test_ownership_transfer_is_explicit_and_preserves_single_owner(db: Session) -> None:
    owner, project = create_project(db)
    successor = create_random_user(db)
    added = service.add_member(
        db,
        actor=owner,
        project_id=project.id,
        payload=MemberAdd(user_id=successor.id, role=ProjectMemberRole.EDITOR),
        idempotency_key=str(uuid.uuid4()),
    )
    assert added.data is not None
    member_id = uuid.UUID(added.data["id"])

    result = service.update_member(
        db,
        actor=owner,
        project_id=project.id,
        member_id=member_id,
        payload=MemberUpdate(
            role=ProjectMemberRole.OWNER,
            transfer_ownership=True,
            previous_owner_role=ProjectMemberRole.REVIEWER,
            reason="Transfer project responsibility.",
        ),
        idempotency_key=str(uuid.uuid4()),
    )

    db.refresh(project)
    active_owners = db.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.role == ProjectMemberRole.OWNER,
            ProjectMember.removed_at.is_(None),
        )
    ).all()
    assert project.owner_id == successor.id
    assert [member.user_id for member in active_owners] == [successor.id]
    assert result.data is not None
    assert result.data["previous_owner"]["role"] == "REVIEWER"
    transfer_audits = db.exec(
        select(AuditLog).where(
            AuditLog.project_id == project.id,
            AuditLog.action == "PROJECT_OWNERSHIP_TRANSFERRED",
        )
    ).all()
    assert len(transfer_audits) == 1


def test_owner_cannot_be_removed_and_non_owner_can_remove_self(db: Session) -> None:
    owner, project = create_project(db)
    owner_member = db.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == owner.id,
        )
    ).one()

    with pytest.raises(ContractError) as exc_info:
        service.remove_member(
            db,
            actor=owner,
            project_id=project.id,
            member_id=owner_member.id,
            idempotency_key=str(uuid.uuid4()),
        )
    assert exc_info.value.code == "LAST_PROJECT_OWNER"

    viewer = create_random_user(db)
    added = service.add_member(
        db,
        actor=owner,
        project_id=project.id,
        payload=MemberAdd(user_id=viewer.id, role=ProjectMemberRole.VIEWER),
        idempotency_key=str(uuid.uuid4()),
    )
    assert added.data is not None
    service.remove_member(
        db,
        actor=viewer,
        project_id=project.id,
        member_id=uuid.UUID(added.data["id"]),
        idempotency_key=str(uuid.uuid4()),
    )
    member = db.get(ProjectMember, uuid.UUID(added.data["id"]))
    assert member is not None
    assert member.removed_at is not None


def test_audit_log_rejects_update_at_database_boundary(db: Session) -> None:
    _owner, project = create_project(db)
    audit = db.exec(select(AuditLog).where(AuditLog.project_id == project.id)).one()

    with pytest.raises(DBAPIError):
        db.execute(
            update(AuditLog).where(AuditLog.id == audit.id).values(action="TAMPERED")
        )
        db.commit()
    db.rollback()
    count = db.exec(
        select(func.count()).select_from(AuditLog).where(AuditLog.id == audit.id)
    ).one()
    assert count == 1
