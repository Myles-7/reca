from __future__ import annotations

import math
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc, func
from sqlmodel import Session, col, select

from app.api.errors import ContractError
from app.approvals.schemas import ApprovalItemDecision
from app.core.observability import current_request_id
from app.models import (
    ApprovalItem,
    ApprovalRecord,
    ApprovalStatus,
    ApprovalType,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    ProjectMemberRole,
    ProjectStatus,
    ResearchProject,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

SCHEMA_VERSION = "1.0"


def _encoded_dict(value: Any) -> dict[str, Any]:
    return cast(dict[str, Any], jsonable_encoder(value))


PayloadResolver = Callable[[Session, ApprovalRecord], dict[str, Any]]
payload_resolvers: dict[str, PayloadResolver] = {}
PostCommitAction = Callable[[], None]
DecisionHandler = Callable[
    [Session, ApprovalRecord, ApprovalStatus, User], PostCommitAction | None
]
decision_handlers: dict[str, DecisionHandler] = {}
decision_permission_actions: dict[str, str] = {}


@dataclass(frozen=True)
class ApprovalItemCreate:
    item_type: str
    item_id: uuid.UUID


@dataclass(frozen=True)
class ApprovalCreate:
    project_id: uuid.UUID
    approval_type: ApprovalType
    target_object_type: str
    target_object_id: uuid.UUID
    requested_by_actor_type: AuditActorType
    requested_by_actor_id: str | None
    payload_snapshot: dict[str, Any]
    impact_summary: dict[str, Any] | None = None
    expires_at: datetime | None = None
    supersedes_approval_id: uuid.UUID | None = None
    items: tuple[ApprovalItemCreate, ...] = ()


def register_payload_resolver(
    target_object_type: str, resolver: PayloadResolver
) -> None:
    payload_resolvers[target_object_type] = resolver


def register_decision_handler(
    target_object_type: str,
    handler: DecisionHandler,
    *,
    permission_action: str | None = None,
) -> None:
    decision_handlers[target_object_type] = handler
    if permission_action is not None:
        decision_permission_actions[target_object_type] = permission_action


def _audit(
    session: Session,
    *,
    approval: ApprovalRecord,
    action: str,
    actor_type: AuditActorType,
    actor_id: str | None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
    outcome: AuditOutcome = AuditOutcome.SUCCEEDED,
) -> None:
    session.add(
        AuditLog(
            project_id=approval.project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            object_type="approval_record",
            object_id=approval.id,
            before_snapshot=jsonable_encoder(before) if before is not None else None,
            after_snapshot=jsonable_encoder(after) if after is not None else None,
            reason=reason,
            request_id=current_request_id(),
            approval_id=approval.id,
            outcome=outcome,
        )
    )


def _audit_override(
    session: Session,
    *,
    project_id: uuid.UUID,
    actor: User,
    permission: str,
    approval_id: uuid.UUID | None = None,
) -> None:
    session.add(
        AuditLog(
            project_id=project_id,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
            action="PROJECT_ADMINISTRATIVE_OVERRIDE",
            object_type="approval_record" if approval_id else "research_project",
            object_id=approval_id or project_id,
            after_snapshot={"permission": permission},
            reason=f"Administrative Approval access: {permission}",
            request_id=current_request_id(),
            approval_id=approval_id,
            outcome=AuditOutcome.SUCCEEDED,
        )
    )


def _approval_items(session: Session, approval_id: uuid.UUID) -> list[ApprovalItem]:
    return list(
        session.exec(
            select(ApprovalItem)
            .where(ApprovalItem.approval_record_id == approval_id)
            .order_by(col(ApprovalItem.item_type), col(ApprovalItem.item_id))
        )
    )


def _redact(value: Any) -> Any:
    sensitive_keys = {
        "api_key",
        "authorization",
        "internal_path",
        "password",
        "raw_content",
        "secret",
        "storage_key",
        "token",
    }
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in sensitive_keys else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _requester_user_id(approval: ApprovalRecord) -> uuid.UUID | None:
    if (
        approval.requested_by_actor_type != AuditActorType.USER
        or approval.requested_by_actor_id is None
    ):
        return None
    try:
        return uuid.UUID(approval.requested_by_actor_id)
    except ValueError:
        return None


def _allowed_actions(
    *,
    approval: ApprovalRecord,
    actor: User,
    role: ProjectMemberRole | None,
    administrative_override: bool,
) -> list[str]:
    if approval.status != ApprovalStatus.PENDING:
        return []
    actions: list[str] = []
    if administrative_override or role in {
        ProjectMemberRole.OWNER,
        ProjectMemberRole.REVIEWER,
    }:
        actions.extend(("approve", "reject"))
    if (
        administrative_override
        or role == ProjectMemberRole.OWNER
        or _requester_user_id(approval) == actor.id
    ):
        actions.append("cancel")
    return actions


def approval_data(
    session: Session,
    *,
    approval: ApprovalRecord,
    actor: User,
    role: ProjectMemberRole | None,
    administrative_override: bool,
    include_payload: bool,
) -> dict[str, Any]:
    decision = None
    if approval.status != ApprovalStatus.PENDING:
        decision = {
            "status": approval.status,
            "user_id": approval.decision_by_user_id,
            "decided_at": approval.decision_at,
            "reason": approval.decision_reason,
        }
    items = _approval_items(session, approval.id)
    data: dict[str, Any] = {
        "id": approval.id,
        "project_id": approval.project_id,
        "approval_type": approval.approval_type,
        "target_object_type": approval.target_object_type,
        "target_object_id": approval.target_object_id,
        "requester": {
            "type": approval.requested_by_actor_type,
            "id": approval.requested_by_actor_id,
        },
        "requested_at": approval.requested_at,
        "status": approval.status,
        "decision": decision,
        "payload_hash": approval.payload_hash,
        "impact_summary": _redact(approval.impact_summary),
        "expires_at": approval.expires_at,
        "supersedes_approval_id": approval.supersedes_approval_id,
        "items": [
            {
                "id": item.id,
                "item_type": item.item_type,
                "item_id": item.item_id,
                "decision": item.decision,
                "reason": item.reason,
            }
            for item in items
        ],
        "allowed_actions": _allowed_actions(
            approval=approval,
            actor=actor,
            role=role,
            administrative_override=administrative_override,
        ),
        "created_at": approval.created_at,
    }
    if include_payload:
        data["payload_snapshot"] = _redact(approval.payload_snapshot)
    return _encoded_dict(data)


def _transition_pending(
    session: Session,
    *,
    approval: ApprovalRecord,
    status: ApprovalStatus,
    actor_type: AuditActorType,
    actor_id: str | None,
    action: str,
    reason: str | None,
    outcome: AuditOutcome = AuditOutcome.SUCCEEDED,
) -> None:
    if approval.status != ApprovalStatus.PENDING:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Approval is not pending.",
        )
    before = {"status": approval.status}
    approval.status = status
    session.add(approval)
    _audit(
        session,
        approval=approval,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        before=before,
        after={"status": status},
        reason=reason,
        outcome=outcome,
    )


def create_approval(session: Session, *, command: ApprovalCreate) -> ApprovalRecord:
    project = session.exec(
        select(ResearchProject).where(
            ResearchProject.id == command.project_id,
            ResearchProject.status != ProjectStatus.DELETED,
            col(ResearchProject.deleted_at).is_(None),
        )
    ).first()
    if project is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    item_keys = [(item.item_type, item.item_id) for item in command.items]
    if len(item_keys) != len(set(item_keys)):
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Approval items must be unique.",
        )
    superseded: ApprovalRecord | None = None
    if command.supersedes_approval_id is not None:
        superseded = session.exec(
            select(ApprovalRecord)
            .where(ApprovalRecord.id == command.supersedes_approval_id)
            .with_for_update()
        ).first()
        if (
            superseded is None
            or superseded.project_id != command.project_id
            or superseded.target_object_type != command.target_object_type
            or superseded.target_object_id != command.target_object_id
        ):
            raise ContractError(
                status_code=409,
                code="INVALID_STATE_TRANSITION",
                message="The superseded Approval does not match the target.",
            )
        if superseded.status == ApprovalStatus.PENDING:
            _transition_pending(
                session,
                approval=superseded,
                status=ApprovalStatus.SUPERSEDED,
                actor_type=command.requested_by_actor_type,
                actor_id=command.requested_by_actor_id,
                action="APPROVAL_SUPERSEDED",
                reason="A replacement Approval was requested.",
            )
    approval = ApprovalRecord(
        project_id=command.project_id,
        approval_type=command.approval_type,
        target_object_type=command.target_object_type,
        target_object_id=command.target_object_id,
        requested_by_actor_type=command.requested_by_actor_type,
        requested_by_actor_id=command.requested_by_actor_id,
        payload_snapshot=jsonable_encoder(command.payload_snapshot),
        payload_hash=project_service.request_hash(command.payload_snapshot),
        impact_summary=jsonable_encoder(command.impact_summary)
        if command.impact_summary is not None
        else None,
        expires_at=command.expires_at,
        supersedes_approval_id=superseded.id if superseded is not None else None,
    )
    session.add(approval)
    session.flush()
    for item in command.items:
        session.add(
            ApprovalItem(
                approval_record_id=approval.id,
                item_type=item.item_type,
                item_id=item.item_id,
            )
        )
    _audit(
        session,
        approval=approval,
        action="APPROVAL_REQUESTED",
        actor_type=command.requested_by_actor_type,
        actor_id=command.requested_by_actor_id,
        after={
            "status": approval.status,
            "approval_type": approval.approval_type,
            "target_object_type": approval.target_object_type,
            "target_object_id": approval.target_object_id,
            "payload_hash": approval.payload_hash,
        },
    )
    return approval


def supersede_approval(
    session: Session,
    *,
    approval_id: uuid.UUID,
    actor_type: AuditActorType,
    actor_id: str | None,
    reason: str,
) -> ApprovalRecord:
    approval = session.exec(
        select(ApprovalRecord).where(ApprovalRecord.id == approval_id).with_for_update()
    ).first()
    if approval is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    _transition_pending(
        session,
        approval=approval,
        status=ApprovalStatus.SUPERSEDED,
        actor_type=actor_type,
        actor_id=actor_id,
        action="APPROVAL_SUPERSEDED",
        reason=reason,
    )
    return approval


def _authorize(
    session: Session,
    *,
    approval: ApprovalRecord,
    actor: User,
    action: str,
    for_update: bool,
) -> project_service.ProjectAccess:
    access = project_service.authorize_project(
        session,
        project_id=approval.project_id,
        actor=actor,
        action=action,
        for_update=for_update,
        allow_superuser_override=True,
        override_reason=f"Administrative Approval access: {action}",
    )
    if access.administrative_override:
        _audit_override(
            session,
            project_id=approval.project_id,
            actor=actor,
            permission=action,
            approval_id=approval.id,
        )
    return access


def _visible_approval(
    session: Session,
    *,
    actor: User,
    approval_id: uuid.UUID,
    action: str,
    for_update: bool,
) -> tuple[ApprovalRecord, project_service.ProjectAccess]:
    statement = select(ApprovalRecord).where(ApprovalRecord.id == approval_id)
    if for_update:
        statement = statement.with_for_update()
    approval = session.exec(statement.execution_options(populate_existing=True)).first()
    if approval is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    access = _authorize(
        session,
        approval=approval,
        actor=actor,
        action=action,
        for_update=for_update,
    )
    return approval, access


def _expire_if_needed(session: Session, approval: ApprovalRecord) -> bool:
    if (
        approval.status == ApprovalStatus.PENDING
        and approval.expires_at is not None
        and approval.expires_at <= get_datetime_utc()
    ):
        _transition_pending(
            session,
            approval=approval,
            status=ApprovalStatus.EXPIRED,
            actor_type=AuditActorType.SYSTEM,
            actor_id="approval-expiration",
            action="APPROVAL_EXPIRED",
            reason="Approval expiration time was reached.",
        )
        return True
    return False


def list_approvals(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    status: ApprovalStatus | None,
    approval_type: ApprovalType | None,
    target_object_type: str | None,
    requested_by_actor_type: AuditActorType | None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    access = project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="approval.read",
        allow_superuser_override=True,
        override_reason="Administrative Approval list access",
    )
    expired = session.exec(
        select(ApprovalRecord)
        .where(
            ApprovalRecord.project_id == project_id,
            ApprovalRecord.status == ApprovalStatus.PENDING,
            col(ApprovalRecord.expires_at).is_not(None),
            col(ApprovalRecord.expires_at) <= get_datetime_utc(),
        )
        .with_for_update()
    ).all()
    for approval in expired:
        _expire_if_needed(session, approval)
    if expired:
        project_service._commit(session)
    filters: list[Any] = [ApprovalRecord.project_id == project_id]
    for column, value in (
        (ApprovalRecord.status, status),
        (ApprovalRecord.approval_type, approval_type),
        (ApprovalRecord.target_object_type, target_object_type),
        (ApprovalRecord.requested_by_actor_type, requested_by_actor_type),
    ):
        if value is not None:
            filters.append(column == value)
    total = session.exec(
        select(func.count()).select_from(ApprovalRecord).where(*filters)
    ).one()
    approvals = session.exec(
        select(ApprovalRecord)
        .where(*filters)
        .order_by(desc(col(ApprovalRecord.created_at)), desc(col(ApprovalRecord.id)))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    role = access.membership.role if access.membership else None
    data = [
        approval_data(
            session,
            approval=approval,
            actor=actor,
            role=role,
            administrative_override=access.administrative_override,
            include_payload=False,
        )
        for approval in approvals
    ]
    if access.administrative_override:
        _audit_override(
            session,
            project_id=project_id,
            actor=actor,
            permission="approval.read:list",
        )
        project_service._commit(session)
    total_pages = math.ceil(total / page_size) if total else 0
    return data, {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


def get_approval(
    session: Session, *, actor: User, approval_id: uuid.UUID
) -> dict[str, Any]:
    approval, access = _visible_approval(
        session,
        actor=actor,
        approval_id=approval_id,
        action="approval.read",
        for_update=True,
    )
    changed = _expire_if_needed(session, approval)
    if changed or access.administrative_override:
        project_service._commit(session)
    return approval_data(
        session,
        approval=approval,
        actor=actor,
        role=access.membership.role if access.membership else None,
        administrative_override=access.administrative_override,
        include_payload=True,
    )


def _validate_item_decisions(
    session: Session,
    *,
    approval: ApprovalRecord,
    decisions: Sequence[ApprovalItemDecision],
) -> list[ApprovalItem]:
    items = _approval_items(session, approval.id)
    expected = {(item.item_type, item.item_id): item for item in items}
    provided = {(item.item_type, item.item_id): item for item in decisions}
    if len(provided) != len(decisions) or set(provided) != set(expected):
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="item_decisions must cover every Approval item exactly once.",
        )
    for key, decision in provided.items():
        item = expected[key]
        item.decision = decision.decision
        item.reason = decision.reason
        session.add(item)
    session.flush()
    return items


def _verify_current_payload(session: Session, approval: ApprovalRecord) -> bool:
    resolver = payload_resolvers.get(approval.target_object_type)
    if resolver is None:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="The owning domain Service has no active Approval payload resolver.",
        )
    return (
        project_service.request_hash(resolver(session, approval))
        == approval.payload_hash
    )


def decide_approval(
    session: Session,
    *,
    actor: User,
    approval_id: uuid.UUID,
    decision: ApprovalStatus,
    decision_reason: str | None,
    item_decisions: Sequence[ApprovalItemDecision],
    idempotency_key: str,
    actor_type: AuditActorType = AuditActorType.USER,
) -> project_service.OperationResult:
    if actor_type != AuditActorType.USER:
        raise ContractError(
            status_code=403,
            code="PERMISSION_DENIED",
            message="Only an authenticated user may decide an Approval.",
        )
    if decision not in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED}:
        raise ValueError("decision must be APPROVED or REJECTED")
    approval = session.exec(
        select(ApprovalRecord)
        .where(ApprovalRecord.id == approval_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).first()
    if approval is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    access = _authorize(
        session,
        approval=approval,
        actor=actor,
        action=decision_permission_actions.get(
            approval.target_object_type, "approval.decide"
        ),
        for_update=True,
    )
    path = (
        "/api/v1/approvals/{approval_id}/approve"
        if decision == ApprovalStatus.APPROVED
        else "/api/v1/approvals/{approval_id}/reject"
    )
    digest = project_service.request_hash(
        {
            "decision_reason": decision_reason,
            "item_decisions": list(item_decisions),
        }
    )
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=approval.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay:
        return replay
    if _expire_if_needed(session, approval):
        project_service._commit(session)
        raise ContractError(
            status_code=409,
            code="APPROVAL_EXPIRED",
            message="Approval has expired.",
        )
    if approval.status != ApprovalStatus.PENDING:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Approval is not pending.",
        )
    if not _verify_current_payload(session, approval):
        _transition_pending(
            session,
            approval=approval,
            status=ApprovalStatus.SUPERSEDED,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
            action="APPROVAL_SUPERSEDED",
            reason="The target payload changed before the decision.",
            outcome=AuditOutcome.FAILED,
        )
        project_service._commit(session)
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="Approval payload no longer matches the target.",
        )
    _validate_item_decisions(session, approval=approval, decisions=item_decisions)
    before = {"status": approval.status}
    now = get_datetime_utc()
    approval.status = decision
    approval.decision_by_user_id = actor.id
    approval.decision_at = now
    approval.decision_reason = decision_reason
    session.add(approval)
    session.flush([approval])
    handler = decision_handlers.get(approval.target_object_type)
    post_commit_action = (
        handler(session, approval, decision, actor) if handler is not None else None
    )
    _audit(
        session,
        approval=approval,
        action="APPROVAL_APPROVED"
        if decision == ApprovalStatus.APPROVED
        else "APPROVAL_REJECTED",
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        before=before,
        after={"status": approval.status, "decision_at": now},
        reason=decision_reason,
    )
    data = approval_data(
        session,
        approval=approval,
        actor=actor,
        role=access.membership.role if access.membership else None,
        administrative_override=access.administrative_override,
        include_payload=True,
    )
    result = project_service.OperationResult(data=data, status_code=200)
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=approval.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    if post_commit_action is not None:
        post_commit_action()
    return result


def cancel_approval(
    session: Session,
    *,
    actor: User,
    approval_id: uuid.UUID,
    idempotency_key: str,
    actor_type: AuditActorType = AuditActorType.USER,
) -> project_service.OperationResult:
    if actor_type != AuditActorType.USER:
        raise ContractError(
            status_code=403,
            code="PERMISSION_DENIED",
            message="Only an authenticated user may cancel an Approval.",
        )
    approval, access = _visible_approval(
        session,
        actor=actor,
        approval_id=approval_id,
        action="approval.cancel",
        for_update=True,
    )
    path = "/api/v1/approvals/{approval_id}/cancel"
    digest = project_service.request_hash({})
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=approval.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay:
        return replay
    if _expire_if_needed(session, approval):
        project_service._commit(session)
        raise ContractError(
            status_code=409,
            code="APPROVAL_EXPIRED",
            message="Approval has expired.",
        )
    if approval.status != ApprovalStatus.PENDING:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Approval is not pending.",
        )
    role = access.membership.role if access.membership else None
    if not (
        access.administrative_override
        or role == ProjectMemberRole.OWNER
        or _requester_user_id(approval) == actor.id
    ):
        raise ContractError(
            status_code=403,
            code="PERMISSION_DENIED",
            message="Only the requester or project OWNER may cancel this Approval.",
        )
    if not _verify_current_payload(session, approval):
        _transition_pending(
            session,
            approval=approval,
            status=ApprovalStatus.SUPERSEDED,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
            action="APPROVAL_SUPERSEDED",
            reason="The target payload changed before cancellation.",
            outcome=AuditOutcome.FAILED,
        )
        project_service._commit(session)
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="Approval payload no longer matches the target.",
        )
    now = get_datetime_utc()
    before = {"status": approval.status}
    approval.status = ApprovalStatus.CANCELLED
    approval.decision_by_user_id = actor.id
    approval.decision_at = now
    session.add(approval)
    _audit(
        session,
        approval=approval,
        action="APPROVAL_CANCELLED",
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        before=before,
        after={"status": approval.status, "decision_at": now},
    )
    data = approval_data(
        session,
        approval=approval,
        actor=actor,
        role=role,
        administrative_override=access.administrative_override,
        include_payload=True,
    )
    result = project_service.OperationResult(data=data, status_code=200)
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=approval.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result
