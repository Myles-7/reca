from __future__ import annotations

import hashlib
import json
import math
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.api.errors import ContractError
from app.core.observability import current_request_id
from app.models import (
    ApprovalRecord,
    ApprovalStatus,
    Artifact,
    ArtifactStatus,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    IdempotencyRecord,
    Job,
    JobStatus,
    ProjectMember,
    ProjectMemberRole,
    ProjectStage,
    ProjectStatus,
    ProjectType,
    ResearchProject,
    User,
    get_datetime_utc,
)
from app.projects.schemas import MemberAdd, MemberUpdate, ProjectCreate, ProjectUpdate

SCHEMA_VERSION = "1.0"


def _encoded_dict(value: Any) -> dict[str, Any]:
    return cast(dict[str, Any], jsonable_encoder(value))


IDEMPOTENCY_RETENTION = timedelta(hours=24)

ROLE_ACTIONS: dict[ProjectMemberRole, frozenset[str]] = {
    ProjectMemberRole.OWNER: frozenset(
        {
            "project.read",
            "project.update",
            "project.delete",
            "project.manage_members",
            "artifact.read",
            "artifact.upload",
            "artifact.download",
            "job.read",
            "job.cancel",
            "job.retry",
            "approval.read",
            "approval.decide",
            "approval.cancel",
            "audit.read",
        }
    ),
    ProjectMemberRole.EDITOR: frozenset(
        {
            "project.read",
            "project.update",
            "artifact.read",
            "artifact.upload",
            "artifact.download",
            "job.read",
            "job.cancel",
            "job.retry",
            "approval.read",
            "approval.cancel",
            "audit.read",
        }
    ),
    ProjectMemberRole.REVIEWER: frozenset(
        {
            "project.read",
            "artifact.read",
            "artifact.download",
            "job.read",
            "approval.read",
            "approval.decide",
            "approval.cancel",
            "audit.read",
        }
    ),
    ProjectMemberRole.VIEWER: frozenset(
        {
            "project.read",
            "artifact.read",
            "artifact.download",
            "job.read",
            "approval.read",
            "approval.cancel",
            "audit.read",
        }
    ),
}


@dataclass(frozen=True)
class OperationResult:
    data: dict[str, Any] | None
    status_code: int
    idempotency_replayed: bool = False


@dataclass(frozen=True)
class ProjectAccess:
    project: ResearchProject
    membership: ProjectMember | None
    administrative_override: bool = False


def _not_found() -> ContractError:
    return ContractError(
        status_code=404,
        code="RESOURCE_NOT_FOUND",
        message="Resource not found.",
    )


def _permission_denied() -> ContractError:
    return ContractError(
        status_code=403,
        code="PERMISSION_DENIED",
        message="The current user does not have permission for this action.",
    )


def _invalid_state(message: str) -> ContractError:
    return ContractError(
        status_code=409,
        code="INVALID_STATE_TRANSITION",
        message=message,
    )


def request_hash(payload: Any) -> str:
    encoded = jsonable_encoder(payload)
    canonical = json.dumps(
        encoded, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def allowed_actions(role: ProjectMemberRole) -> list[str]:
    return sorted(ROLE_ACTIONS[role])


def _project_permissions(role: ProjectMemberRole) -> dict[str, bool]:
    actions = ROLE_ACTIONS[role]
    return {
        "can_update": "project.update" in actions,
        "can_delete": "project.delete" in actions,
    }


def project_data(project: ResearchProject, role: ProjectMemberRole) -> dict[str, Any]:
    return _encoded_dict(
        {
            "id": project.id,
            "owner_id": project.owner_id,
            "name": project.name,
            "description": project.description,
            "discipline": project.discipline,
            "research_direction": project.research_direction,
            "project_type": project.project_type,
            "current_stage": project.current_stage,
            "status": project.status,
            "expected_completion_date": project.expected_completion_date,
            "resource_constraints": project.resource_constraints,
            "ethical_constraints": project.ethical_constraints,
            "lock_version": project.lock_version,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "permissions": _project_permissions(role),
        }
    )


def _project_snapshot(project: ResearchProject) -> dict[str, Any]:
    return _encoded_dict(
        {
            "name": project.name,
            "description": project.description,
            "discipline": project.discipline,
            "research_direction": project.research_direction,
            "project_type": project.project_type,
            "current_stage": project.current_stage,
            "status": project.status,
            "expected_completion_date": project.expected_completion_date,
            "resource_constraints": project.resource_constraints,
            "ethical_constraints": project.ethical_constraints,
            "owner_id": project.owner_id,
            "lock_version": project.lock_version,
        }
    )


def _member_snapshot(member: ProjectMember, user: User) -> dict[str, Any]:
    return _encoded_dict(
        {
            "membership_id": member.id,
            "user_id": member.user_id,
            "user_email": user.email,
            "role": member.role,
            "removed_at": member.removed_at,
        }
    )


def member_data(member: ProjectMember, user: User) -> dict[str, Any]:
    return _encoded_dict(
        {
            "id": member.id,
            "project_id": member.project_id,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
            },
            "role": member.role,
            "joined_at": member.joined_at,
            "removed_at": member.removed_at,
            "allowed_actions": allowed_actions(member.role)
            if member.removed_at is None
            else [],
        }
    )


def _add_audit(
    session: Session,
    *,
    project_id: uuid.UUID,
    actor: User,
    action: str,
    object_type: str,
    object_id: uuid.UUID | None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
    outcome: AuditOutcome = AuditOutcome.SUCCEEDED,
) -> AuditLog:
    audit = AuditLog(
        project_id=project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action=action,
        object_type=object_type,
        object_id=object_id,
        before_snapshot=before,
        after_snapshot=after,
        reason=reason,
        request_id=current_request_id(),
        outcome=outcome,
    )
    session.add(audit)
    return audit


def _idempotency_statement(
    *,
    actor_id: uuid.UUID,
    project_id: uuid.UUID | None,
    method: str,
    path_template: str,
    key: str,
) -> Any:
    statement = select(IdempotencyRecord).where(
        IdempotencyRecord.actor_id == actor_id,
        IdempotencyRecord.method == method,
        IdempotencyRecord.path_template == path_template,
        IdempotencyRecord.idempotency_key == key,
    )
    if project_id is None:
        statement = statement.where(col(IdempotencyRecord.project_id).is_(None))
    else:
        statement = statement.where(IdempotencyRecord.project_id == project_id)
    return statement


def _replay_or_conflict(
    session: Session,
    *,
    actor_id: uuid.UUID,
    project_id: uuid.UUID | None,
    method: str,
    path_template: str,
    key: str,
    payload_hash: str,
) -> OperationResult | None:
    record = session.exec(
        _idempotency_statement(
            actor_id=actor_id,
            project_id=project_id,
            method=method,
            path_template=path_template,
            key=key,
        )
    ).first()
    if record is None:
        return None
    if record.request_hash != payload_hash:
        raise ContractError(
            status_code=409,
            code="IDEMPOTENCY_CONFLICT",
            message="The Idempotency-Key was already used with a different request.",
        )
    return OperationResult(
        data=record.response_body,
        status_code=record.response_status,
        idempotency_replayed=True,
    )


def _store_idempotency(
    session: Session,
    *,
    actor_id: uuid.UUID,
    project_id: uuid.UUID | None,
    method: str,
    path_template: str,
    key: str,
    payload_hash: str,
    result: OperationResult,
) -> None:
    session.add(
        IdempotencyRecord(
            actor_id=actor_id,
            project_id=project_id,
            method=method,
            path_template=path_template,
            idempotency_key=key,
            request_hash=payload_hash,
            response_status=result.status_code,
            response_body=result.data,
            expires_at=datetime.now(UTC) + IDEMPOTENCY_RETENTION,
        )
    )


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="The operation conflicted with a concurrent change.",
            retryable=True,
        )


def authorize_project(
    session: Session,
    *,
    project_id: uuid.UUID,
    actor: User,
    action: str,
    for_update: bool = False,
    allow_superuser_override: bool = False,
    override_reason: str | None = None,
) -> ProjectAccess:
    statement = select(ResearchProject).where(
        ResearchProject.id == project_id,
        ResearchProject.status != ProjectStatus.DELETED,
        col(ResearchProject.deleted_at).is_(None),
    )
    if for_update:
        statement = statement.with_for_update()
    project = session.exec(statement).first()
    if project is None:
        raise _not_found()

    membership_statement = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == actor.id,
        col(ProjectMember.removed_at).is_(None),
    )
    if for_update:
        membership_statement = membership_statement.with_for_update()
    membership = session.exec(membership_statement).first()

    if membership is None:
        if (
            actor.is_superuser
            and allow_superuser_override
            and override_reason
            and override_reason.strip()
        ):
            return ProjectAccess(
                project=project,
                membership=None,
                administrative_override=True,
            )
        raise _not_found()
    if action not in ROLE_ACTIONS[membership.role]:
        raise _permission_denied()
    return ProjectAccess(project=project, membership=membership)


def create_project(
    session: Session,
    *,
    actor: User,
    payload: ProjectCreate,
    idempotency_key: str,
) -> OperationResult:
    payload_digest = request_hash(payload)
    replay = _replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=None,
        method="POST",
        path_template="/api/v1/projects",
        key=idempotency_key,
        payload_hash=payload_digest,
    )
    if replay:
        return replay

    project = ResearchProject(owner_id=actor.id, **payload.model_dump())
    session.add(project)
    session.flush()
    owner = ProjectMember(
        project_id=project.id,
        user_id=actor.id,
        role=ProjectMemberRole.OWNER,
        invited_by=actor.id,
    )
    session.add(owner)
    session.flush()
    _add_audit(
        session,
        project_id=project.id,
        actor=actor,
        action="PROJECT_CREATED",
        object_type="research_project",
        object_id=project.id,
        after=_project_snapshot(project),
    )
    result = OperationResult(
        data=project_data(project, ProjectMemberRole.OWNER), status_code=201
    )
    _store_idempotency(
        session,
        actor_id=actor.id,
        project_id=None,
        method="POST",
        path_template="/api/v1/projects",
        key=idempotency_key,
        payload_hash=payload_digest,
        result=result,
    )
    _commit(session)
    return result


def list_projects(
    session: Session,
    *,
    actor: User,
    status: ProjectStatus | None,
    current_stage: ProjectStage | None,
    project_type: ProjectType | None,
    q: str | None,
    page: int,
    page_size: int,
    sort: str,
    order: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    allowed_sort = {
        "created_at": col(ResearchProject.created_at),
        "updated_at": col(ResearchProject.updated_at),
        "name": col(ResearchProject.name),
    }
    if sort not in allowed_sort or order not in {"asc", "desc"}:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="Unsupported project sort field or order.",
        )

    filters: list[Any] = [
        ProjectMember.user_id == actor.id,
        col(ProjectMember.removed_at).is_(None),
        ResearchProject.status != ProjectStatus.DELETED,
        col(ResearchProject.deleted_at).is_(None),
    ]
    if status is not None:
        filters.append(ResearchProject.status == status)
    if current_stage is not None:
        filters.append(ResearchProject.current_stage == current_stage)
    if project_type is not None:
        filters.append(ResearchProject.project_type == project_type)
    if q:
        pattern = f"%{q.strip()}%"
        filters.append(
            or_(
                col(ResearchProject.name).ilike(pattern),
                col(ResearchProject.description).ilike(pattern),
            )
        )

    count_statement = (
        select(func.count())
        .select_from(ResearchProject)
        .join(ProjectMember, col(ProjectMember.project_id) == col(ResearchProject.id))
        .where(*filters)
    )
    total = session.exec(count_statement).one()
    direction = asc if order == "asc" else desc
    statement = (
        select(ResearchProject, ProjectMember)
        .join(ProjectMember, col(ProjectMember.project_id) == col(ResearchProject.id))
        .where(*filters)
        .order_by(direction(allowed_sort[sort]), direction(col(ResearchProject.id)))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = session.exec(statement).all()
    data = [project_data(project, member.role) for project, member in rows]
    total_pages = math.ceil(total / page_size) if total else 0
    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }
    return data, pagination


def get_project(
    session: Session, *, actor: User, project_id: uuid.UUID
) -> dict[str, Any]:
    access = authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="project.read",
    )
    assert access.membership is not None
    return project_data(access.project, access.membership.role)


def update_project(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    expected_lock_version: int,
) -> dict[str, Any]:
    access = authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="project.update",
        for_update=True,
    )
    project = access.project
    assert access.membership is not None
    if project.status == ProjectStatus.ARCHIVED:
        raise ContractError(
            status_code=409,
            code="RESOURCE_ARCHIVED",
            message="Archived projects are read-only.",
        )
    if project.lock_version != expected_lock_version:
        raise ContractError(
            status_code=409,
            code="RESOURCE_VERSION_CONFLICT",
            message="The project was updated by another operation.",
            details={
                "expected_lock_version": expected_lock_version,
                "current_lock_version": project.lock_version,
            },
            suggested_action="Refresh the project and retry the update.",
        )
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return project_data(project, access.membership.role)
    before = _project_snapshot(project)
    project.sqlmodel_update(changes)
    project.lock_version += 1
    project.updated_at = get_datetime_utc()
    session.add(project)
    after = _project_snapshot(project)
    _add_audit(
        session,
        project_id=project.id,
        actor=actor,
        action="PROJECT_UPDATED",
        object_type="research_project",
        object_id=project.id,
        before=before,
        after=after,
    )
    _commit(session)
    return project_data(project, access.membership.role)


def transition_project_status(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    target_status: ProjectStatus,
) -> dict[str, Any]:
    access = authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="project.delete",
        for_update=True,
    )
    project = access.project
    assert access.membership is not None
    transitions = {
        (ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED): "PROJECT_ARCHIVED",
        (ProjectStatus.ARCHIVED, ProjectStatus.ACTIVE): "PROJECT_RESTORED",
    }
    action = transitions.get((project.status, target_status))
    if action is None:
        raise _invalid_state(
            f"Project cannot transition from {project.status} to {target_status}."
        )
    before = _project_snapshot(project)
    project.status = target_status
    project.lock_version += 1
    project.updated_at = get_datetime_utc()
    session.add(project)
    _add_audit(
        session,
        project_id=project.id,
        actor=actor,
        action=action,
        object_type="research_project",
        object_id=project.id,
        before=before,
        after=_project_snapshot(project),
    )
    _commit(session)
    return project_data(project, access.membership.role)


def list_members(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    role: ProjectMemberRole | None,
    q: str | None,
    include_removed: bool,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    access = authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="project.read",
    )
    assert access.membership is not None
    if include_removed and access.membership.role != ProjectMemberRole.OWNER:
        raise _permission_denied()
    filters: list[Any] = [ProjectMember.project_id == project_id]
    if not include_removed:
        filters.append(col(ProjectMember.removed_at).is_(None))
    if role is not None:
        filters.append(ProjectMember.role == role)
    if q:
        pattern = f"%{q.strip()}%"
        filters.append(
            or_(col(User.email).ilike(pattern), col(User.full_name).ilike(pattern))
        )
    count_statement = (
        select(func.count())
        .select_from(ProjectMember)
        .join(User, col(User.id) == col(ProjectMember.user_id))
        .where(*filters)
    )
    total = session.exec(count_statement).one()
    statement = (
        select(ProjectMember, User)
        .join(User, col(User.id) == col(ProjectMember.user_id))
        .where(*filters)
        .order_by(desc(col(ProjectMember.joined_at)), desc(col(ProjectMember.id)))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = session.exec(statement).all()
    total_pages = math.ceil(total / page_size) if total else 0
    return [member_data(member, user) for member, user in rows], {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


def add_member(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    payload: MemberAdd,
    idempotency_key: str,
) -> OperationResult:
    authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="project.manage_members",
        for_update=True,
    )
    payload_digest = request_hash(payload)
    path_template = "/api/v1/projects/{project_id}/members"
    replay = _replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=path_template,
        key=idempotency_key,
        payload_hash=payload_digest,
    )
    if replay:
        return replay
    if payload.role == ProjectMemberRole.OWNER:
        raise _invalid_state("OWNER can only be assigned through ownership transfer.")
    user = session.get(User, payload.user_id)
    if user is None or not user.is_active:
        raise _not_found()
    member = session.exec(
        select(ProjectMember)
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == payload.user_id,
        )
        .with_for_update()
    ).first()
    now = get_datetime_utc()
    status_code = 201
    action = "PROJECT_MEMBER_ADDED"
    before: dict[str, Any] | None = None
    if member is not None and member.removed_at is None:
        if member.role != payload.role:
            raise ContractError(
                status_code=409,
                code="MEMBER_ALREADY_ACTIVE",
                message="The user is already an active project member.",
            )
        result = OperationResult(data=member_data(member, user), status_code=200)
        _store_idempotency(
            session,
            actor_id=actor.id,
            project_id=project_id,
            method="POST",
            path_template=path_template,
            key=idempotency_key,
            payload_hash=payload_digest,
            result=result,
        )
        _commit(session)
        return result
    if member is None:
        member = ProjectMember(
            project_id=project_id,
            user_id=user.id,
            role=payload.role,
            invited_by=actor.id,
        )
    else:
        before = _member_snapshot(member, user)
        member.role = payload.role
        member.removed_at = None
        member.joined_at = now
        member.invited_by = actor.id
        status_code = 200
        action = "PROJECT_MEMBER_REJOINED"
    session.add(member)
    session.flush()
    after = _member_snapshot(member, user)
    _add_audit(
        session,
        project_id=project_id,
        actor=actor,
        action=action,
        object_type="project_member",
        object_id=member.id,
        before=before,
        after=after,
    )
    result = OperationResult(data=member_data(member, user), status_code=status_code)
    _store_idempotency(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=path_template,
        key=idempotency_key,
        payload_hash=payload_digest,
        result=result,
    )
    _commit(session)
    return result


def update_member(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    member_id: uuid.UUID,
    payload: MemberUpdate,
    idempotency_key: str,
) -> OperationResult:
    access = authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="project.manage_members",
        for_update=True,
        allow_superuser_override=True,
        override_reason=payload.reason,
    )
    payload_digest = request_hash(payload)
    path_template = "/api/v1/projects/{project_id}/members/{member_id}"
    replay = _replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="PATCH",
        path_template=path_template,
        key=idempotency_key,
        payload_hash=payload_digest,
    )
    if replay:
        return replay
    member = session.exec(
        select(ProjectMember)
        .where(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
        )
        .with_for_update()
    ).first()
    if member is None:
        raise _not_found()
    if member.removed_at is not None:
        raise _invalid_state("Removed memberships cannot be updated.")
    user = session.get(User, member.user_id)
    if user is None:
        raise _not_found()

    if payload.transfer_ownership:
        result_data = _transfer_ownership(
            session,
            actor=actor,
            access=access,
            successor=member,
            successor_user=user,
            payload=payload,
        )
    else:
        if payload.role == ProjectMemberRole.OWNER:
            raise _invalid_state(
                "OWNER can only be assigned through ownership transfer."
            )
        if member.role == ProjectMemberRole.OWNER:
            raise ContractError(
                status_code=409,
                code="LAST_PROJECT_OWNER",
                message="Transfer ownership before changing the current OWNER role.",
            )
        before = _member_snapshot(member, user)
        member.role = payload.role
        session.add(member)
        after = _member_snapshot(member, user)
        if before != after:
            _add_audit(
                session,
                project_id=project_id,
                actor=actor,
                action="PROJECT_MEMBER_ROLE_CHANGED",
                object_type="project_member",
                object_id=member.id,
                before=before,
                after=after,
                reason=payload.reason,
            )
        result_data = member_data(member, user)

    result = OperationResult(data=result_data, status_code=200)
    _store_idempotency(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="PATCH",
        path_template=path_template,
        key=idempotency_key,
        payload_hash=payload_digest,
        result=result,
    )
    _commit(session)
    return result


def _transfer_ownership(
    session: Session,
    *,
    actor: User,
    access: ProjectAccess,
    successor: ProjectMember,
    successor_user: User,
    payload: MemberUpdate,
) -> dict[str, Any]:
    project = access.project
    if successor.role == ProjectMemberRole.OWNER:
        raise _invalid_state("The target member is already the project OWNER.")
    owner = session.exec(
        select(ProjectMember)
        .where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == project.owner_id,
            ProjectMember.role == ProjectMemberRole.OWNER,
            col(ProjectMember.removed_at).is_(None),
        )
        .with_for_update()
    ).first()
    if owner is None or owner.id == successor.id:
        raise _invalid_state("The project OWNER invariant is not satisfied.")
    if not access.administrative_override and owner.user_id != actor.id:
        raise _permission_denied()
    owner_user = session.get(User, owner.user_id)
    if owner_user is None or payload.previous_owner_role is None:
        raise _invalid_state("Ownership transfer cannot resolve the current OWNER.")

    before = {
        "owner_id": str(project.owner_id),
        "previous_owner": _member_snapshot(owner, owner_user),
        "successor": _member_snapshot(successor, successor_user),
    }
    owner.role = payload.previous_owner_role
    session.add(owner)
    session.flush([owner])

    successor.role = ProjectMemberRole.OWNER
    project.owner_id = successor.user_id
    project.lock_version += 1
    project.updated_at = get_datetime_utc()
    session.add(successor)
    session.add(project)
    after = {
        "owner_id": str(project.owner_id),
        "previous_owner": _member_snapshot(owner, owner_user),
        "successor": _member_snapshot(successor, successor_user),
        "administrative_override": access.administrative_override,
    }
    _add_audit(
        session,
        project_id=project.id,
        actor=actor,
        action="PROJECT_OWNERSHIP_TRANSFERRED",
        object_type="research_project",
        object_id=project.id,
        before=before,
        after=after,
        reason=payload.reason,
    )
    return _encoded_dict(
        {
            "member": member_data(successor, successor_user),
            "project_owner_id": project.owner_id,
            "previous_owner": {
                "member_id": owner.id,
                "user_id": owner.user_id,
                "role": owner.role,
            },
        }
    )


def remove_member(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    member_id: uuid.UUID,
    idempotency_key: str,
) -> OperationResult:
    access = authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="project.read",
        for_update=True,
    )
    assert access.membership is not None
    payload_digest = request_hash({"member_id": member_id})
    path_template = "/api/v1/projects/{project_id}/members/{member_id}"
    replay = _replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="DELETE",
        path_template=path_template,
        key=idempotency_key,
        payload_hash=payload_digest,
    )
    if replay:
        return replay
    member = session.exec(
        select(ProjectMember)
        .where(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
        )
        .with_for_update()
    ).first()
    if member is None:
        raise _not_found()
    if member.removed_at is not None:
        raise _invalid_state("The membership is already removed.")
    is_self = member.user_id == actor.id
    is_owner = access.membership.role == ProjectMemberRole.OWNER
    if not is_self and not is_owner:
        raise _permission_denied()
    if member.role == ProjectMemberRole.OWNER:
        raise ContractError(
            status_code=409,
            code="LAST_PROJECT_OWNER",
            message="Transfer ownership before removing the current OWNER.",
        )
    user = session.get(User, member.user_id)
    if user is None:
        raise _not_found()
    before = _member_snapshot(member, user)
    member.removed_at = get_datetime_utc()
    session.add(member)
    _add_audit(
        session,
        project_id=project_id,
        actor=actor,
        action="PROJECT_MEMBER_REMOVED",
        object_type="project_member",
        object_id=member.id,
        before=before,
        after=_member_snapshot(member, user),
    )
    result = OperationResult(data=None, status_code=204)
    _store_idempotency(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="DELETE",
        path_template=path_template,
        key=idempotency_key,
        payload_hash=payload_digest,
        result=result,
    )
    _commit(session)
    return result


def list_audit_logs(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    actor_type: AuditActorType | None,
    action: str | None,
    object_type: str | None,
    object_id: uuid.UUID | None,
    outcome: AuditOutcome | None,
    request_id: str | None,
    job_id: uuid.UUID | None,
    approval_id: uuid.UUID | None,
    from_time: datetime | None,
    to_time: datetime | None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="audit.read",
    )
    filters: list[Any] = [AuditLog.project_id == project_id]
    for column, value in (
        (AuditLog.actor_type, actor_type),
        (AuditLog.action, action),
        (AuditLog.object_type, object_type),
        (AuditLog.object_id, object_id),
        (AuditLog.outcome, outcome),
        (AuditLog.request_id, request_id),
        (AuditLog.job_id, job_id),
        (AuditLog.approval_id, approval_id),
    ):
        if value is not None:
            filters.append(column == value)
    if from_time is not None:
        filters.append(AuditLog.created_at >= from_time)
    if to_time is not None:
        filters.append(AuditLog.created_at <= to_time)
    total = session.exec(
        select(func.count()).select_from(AuditLog).where(*filters)
    ).one()
    logs = session.exec(
        select(AuditLog)
        .where(*filters)
        .order_by(desc(col(AuditLog.created_at)), desc(col(AuditLog.id)))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    data = [_audit_data(session, log) for log in logs]
    total_pages = math.ceil(total / page_size) if total else 0
    return data, {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


def _audit_data(session: Session, audit: AuditLog) -> dict[str, Any]:
    actor_user: User | None = None
    if audit.actor_type == AuditActorType.USER and audit.actor_id:
        try:
            actor_user = session.get(User, uuid.UUID(audit.actor_id))
        except ValueError:
            actor_user = None
    label = None
    for snapshot in (audit.after_snapshot, audit.before_snapshot):
        if snapshot:
            label = snapshot.get("user_email") or snapshot.get("name")
            if label:
                break
    return _encoded_dict(
        {
            "id": audit.id,
            "project_id": audit.project_id,
            "actor": {
                "type": audit.actor_type,
                "id": audit.actor_id,
                "display_name": actor_user.full_name if actor_user else None,
            },
            "action": audit.action,
            "target": {
                "type": audit.object_type,
                "id": audit.object_id,
                "label": label,
            },
            "before": audit.before_snapshot,
            "after": audit.after_snapshot,
            "reason": audit.reason,
            "outcome": audit.outcome,
            "request_id": audit.request_id,
            "job_id": audit.job_id,
            "approval_id": audit.approval_id,
            "created_at": audit.created_at,
        }
    )


def project_overview(
    session: Session, *, actor: User, project_id: uuid.UUID
) -> dict[str, Any]:
    access = authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="project.read",
    )
    member_count = session.exec(
        select(func.count())
        .select_from(ProjectMember)
        .where(
            ProjectMember.project_id == project_id,
            col(ProjectMember.removed_at).is_(None),
        )
    ).one()
    audit_count = session.exec(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.project_id == project_id)
    ).one()
    artifact_count = session.exec(
        select(func.count())
        .select_from(Artifact)
        .where(
            Artifact.project_id == project_id,
            Artifact.status != ArtifactStatus.DELETED,
            col(Artifact.deleted_at).is_(None),
        )
    ).one()
    active_job_count = session.exec(
        select(func.count())
        .select_from(Job)
        .where(
            Job.project_id == project_id,
            col(Job.status).in_(
                (
                    JobStatus.DRAFT,
                    JobStatus.QUEUED,
                    JobStatus.RUNNING,
                    JobStatus.NEEDS_REVIEW,
                    JobStatus.CANCEL_REQUESTED,
                    JobStatus.DISPATCH_FAILED,
                )
            ),
        )
    ).one()
    pending_approval_count = session.exec(
        select(func.count())
        .select_from(ApprovalRecord)
        .where(
            ApprovalRecord.project_id == project_id,
            ApprovalRecord.status == ApprovalStatus.PENDING,
            or_(
                col(ApprovalRecord.expires_at).is_(None),
                col(ApprovalRecord.expires_at) > get_datetime_utc(),
            ),
        )
    ).one()
    recent = session.exec(
        select(AuditLog)
        .where(AuditLog.project_id == project_id)
        .order_by(desc(col(AuditLog.created_at)), desc(col(AuditLog.id)))
        .limit(10)
    ).all()
    unavailable = dict.fromkeys(
        (
            "research_question",
            "literature",
            "dataset",
            "analysis",
            "figure",
            "manuscript",
            "evidence",
        ),
        "NOT_AVAILABLE",
    )
    counts = {
        "literature_total": None,
        "literature_included": None,
        "literature_uncertain": None,
        "datasets": None,
        "dataset_versions": None,
        "analysis_runs": None,
        "figures": None,
        "manuscript_issues": None,
        "high_risk_issues": None,
    }
    return _encoded_dict(
        {
            "project_id": project_id,
            "current_stage": access.project.current_stage,
            "module_availability": unavailable,
            "current_research_question": None,
            "foundation_counts": {
                "members": member_count,
                "artifacts": artifact_count,
                "jobs_active": active_job_count,
                "approvals_pending": pending_approval_count,
                "audit_events": audit_count,
            },
            "counts": counts,
            "pending_actions": [],
            "evidence_completeness": None,
            "recent_activity": [_audit_data(session, item) for item in recent],
        }
    )
