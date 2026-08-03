from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.errors import ContractError
from app.core.observability import current_request_id
from app.models import (
    AuditActorType,
    AuditLog,
    AuditOutcome,
    ProjectMemberRole,
    QueryPlan,
    QueryPlanStatus,
    ResearchQuestionVersion,
    ResearchQuestionVersionStatus,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service
from app.query_plans.schemas import QueryPlanCreate, QueryPlanFields


def _not_found() -> ContractError:
    return ContractError(
        status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
    )


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ContractError(
            status_code=409,
            code="RESOURCE_VERSION_CONFLICT",
            message="The QueryPlan changed concurrently.",
        ) from exc


def _can_update(role: ProjectMemberRole | None) -> bool:
    return role in {ProjectMemberRole.OWNER, ProjectMemberRole.EDITOR}


def _allowed_actions(*, can_update: bool) -> list[str]:
    if not can_update:
        return ["query_plan.read"]
    return ["query_plan.read", "query_plan.update", "query_plan.generate"]


def query_plan_data(plan: QueryPlan, *, can_update: bool) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "id": plan.id,
                "project_id": plan.project_id,
                "research_question_version_id": plan.research_question_version_id,
                "chinese_terms": plan.chinese_terms,
                "english_terms": plan.english_terms,
                "synonyms": plan.synonyms,
                "object_terms": plan.object_terms,
                "method_terms": plan.method_terms,
                "boolean_query": plan.boolean_query,
                "filters": plan.filters,
                "limitations": plan.limitations,
                "source_model_invocation_id": plan.source_model_invocation_id,
                "status": plan.status,
                "lock_version": plan.lock_version,
                "created_at": plan.created_at,
                "updated_at": plan.updated_at,
                "allowed_actions": _allowed_actions(can_update=can_update),
            }
        ),
    )


def _snapshot(plan: QueryPlan) -> dict[str, Any]:
    return {
        "research_question_version_id": str(plan.research_question_version_id),
        "status": plan.status.value,
        "lock_version": plan.lock_version,
        "chinese_term_count": len(plan.chinese_terms or []),
        "english_term_count": len(plan.english_terms or []),
        "has_boolean_query": plan.boolean_query is not None,
        "source_model_invocation_id": (
            str(plan.source_model_invocation_id)
            if plan.source_model_invocation_id is not None
            else None
        ),
    }


def _audit(
    session: Session,
    *,
    plan: QueryPlan,
    actor: User,
    action: str,
    before: dict[str, Any] | None = None,
    reason: str | None = None,
) -> None:
    session.add(
        AuditLog(
            project_id=plan.project_id,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
            action=action,
            object_type="query_plan",
            object_id=plan.id,
            before_snapshot=before,
            after_snapshot=_snapshot(plan),
            reason=reason,
            request_id=current_request_id(),
            outcome=AuditOutcome.SUCCEEDED,
        )
    )


def _version_for_project(
    session: Session, *, project_id: uuid.UUID, version_id: uuid.UUID
) -> ResearchQuestionVersion:
    version = session.exec(
        select(ResearchQuestionVersion).where(
            ResearchQuestionVersion.id == version_id,
            ResearchQuestionVersion.project_id == project_id,
        )
    ).first()
    if version is None:
        raise _not_found()
    if version.status == ResearchQuestionVersionStatus.SUPERSEDED:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="A new QueryPlan cannot target a superseded ResearchQuestionVersion.",
        )
    return version


def _field_values(fields: QueryPlanFields) -> dict[str, Any]:
    values = fields.model_dump(exclude_unset=True, mode="json")
    if "filters" in values and values["filters"] is not None:
        values["filters"] = dict(values["filters"])
    return values


def create_query_plan_command(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    payload: QueryPlanCreate,
    idempotency_key: str,
) -> project_service.OperationResult:
    access = project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="project.update",
        for_update=True,
    )
    _version_for_project(
        session,
        project_id=project_id,
        version_id=payload.research_question_version_id,
    )
    digest = project_service.request_hash(payload)
    path = "/api/v1/projects/{project_id}/query-plans"
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    values = payload.model_dump(exclude={"research_question_version_id"}, mode="json")
    plan = QueryPlan(
        project_id=project_id,
        research_question_version_id=payload.research_question_version_id,
        status=QueryPlanStatus.DRAFT,
        **values,
    )
    session.add(plan)
    session.flush()
    _audit(session, plan=plan, actor=actor, action="QUERY_PLAN_CREATED")
    result = project_service.OperationResult(
        data=query_plan_data(
            plan,
            can_update=_can_update(
                access.membership.role if access.membership else None
            ),
        ),
        status_code=201,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    _commit(session)
    return result


def get_query_plan(
    session: Session, *, actor: User, query_plan_id: uuid.UUID
) -> dict[str, Any]:
    plan = session.get(QueryPlan, query_plan_id)
    if plan is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=plan.project_id, actor=actor, action="project.read"
    )
    return query_plan_data(
        plan,
        can_update=_can_update(access.membership.role if access.membership else None),
    )


def update_query_plan(
    session: Session,
    *,
    actor: User,
    query_plan_id: uuid.UUID,
    expected_lock_version: int,
    fields: QueryPlanFields,
    change_reason: str,
) -> dict[str, Any]:
    plan = session.exec(
        select(QueryPlan).where(QueryPlan.id == query_plan_id).with_for_update()
    ).first()
    if plan is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=plan.project_id, actor=actor, action="project.update"
    )
    if plan.lock_version != expected_lock_version:
        raise ContractError(
            status_code=409,
            code="RESOURCE_VERSION_CONFLICT",
            message="The QueryPlan changed.",
            details={
                "expected_lock_version": expected_lock_version,
                "current_lock_version": plan.lock_version,
            },
        )
    if plan.status != QueryPlanStatus.DRAFT:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Only a DRAFT QueryPlan may be updated.",
        )
    values = _field_values(fields)
    if not values:
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="At least one QueryPlan field must be provided.",
        )
    before = _snapshot(plan)
    for name, value in values.items():
        setattr(plan, name, value)
    plan.lock_version += 1
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    _audit(
        session,
        plan=plan,
        actor=actor,
        action="QUERY_PLAN_UPDATED",
        before=before,
        reason=change_reason,
    )
    _commit(session)
    session.refresh(plan)
    return query_plan_data(
        plan,
        can_update=_can_update(access.membership.role if access.membership else None),
    )
