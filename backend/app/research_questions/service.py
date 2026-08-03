from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.api.errors import ContractError
from app.approvals import service as approval_service
from app.core.observability import current_request_id
from app.models import (
    ApprovalRecord,
    ApprovalStatus,
    ApprovalType,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    ResearchProject,
    ResearchQuestion,
    ResearchQuestionStatus,
    ResearchQuestionVersion,
    ResearchQuestionVersionStatus,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service
from app.research_questions.schemas import (
    ResearchQuestionVersionContent,
    ResearchQuestionVersionFields,
)

TARGET_OBJECT_TYPE = "research_question_version"


def _not_found() -> ContractError:
    return ContractError(
        status_code=404,
        code="RESOURCE_NOT_FOUND",
        message="Resource not found.",
    )


def _invalid_state(message: str) -> ContractError:
    return ContractError(
        status_code=409,
        code="INVALID_STATE_TRANSITION",
        message=message,
    )


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ContractError(
            status_code=409,
            code="RESOURCE_VERSION_CONFLICT",
            message="The ResearchQuestion changed concurrently.",
        ) from error


def _content_values(content: ResearchQuestionVersionContent) -> dict[str, Any]:
    values = content.model_dump(mode="python")
    if not content.raw_input.strip():
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="raw_input must not be empty.",
        )
    return values


def _audit(
    session: Session,
    *,
    project_id: uuid.UUID,
    actor: User,
    action: str,
    object_type: str,
    object_id: uuid.UUID,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
    approval_id: uuid.UUID | None = None,
) -> None:
    session.add(
        AuditLog(
            project_id=project_id,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
            action=action,
            object_type=object_type,
            object_id=object_id,
            before_snapshot=jsonable_encoder(before) if before is not None else None,
            after_snapshot=jsonable_encoder(after) if after is not None else None,
            reason=reason,
            request_id=current_request_id(),
            approval_id=approval_id,
            outcome=AuditOutcome.SUCCEEDED,
        )
    )


def _system_audit(
    session: Session,
    *,
    project_id: uuid.UUID,
    action: str,
    object_id: uuid.UUID,
    before: dict[str, Any],
    after: dict[str, Any],
) -> None:
    session.add(
        AuditLog(
            project_id=project_id,
            actor_type=AuditActorType.SYSTEM,
            actor_id="research-question-validator",
            action=action,
            object_type=TARGET_OBJECT_TYPE,
            object_id=object_id,
            before_snapshot=jsonable_encoder(before),
            after_snapshot=jsonable_encoder(after),
            request_id=current_request_id(),
            outcome=AuditOutcome.SUCCEEDED,
        )
    )


def _can_update(access: project_service.ProjectAccess) -> bool:
    if access.administrative_override:
        return True
    return bool(
        access.membership
        and "project.update" in project_service.ROLE_ACTIONS[access.membership.role]
    )


def _pending_approval(
    session: Session, version: ResearchQuestionVersion
) -> ApprovalRecord | None:
    return session.exec(
        select(ApprovalRecord).where(
            ApprovalRecord.project_id == version.project_id,
            ApprovalRecord.approval_type == ApprovalType.RESEARCH_QUESTION_CONFIRMATION,
            ApprovalRecord.target_object_type == TARGET_OBJECT_TYPE,
            ApprovalRecord.target_object_id == version.id,
            ApprovalRecord.status == ApprovalStatus.PENDING,
        )
    ).first()


def _allowed_actions(
    version: ResearchQuestionVersion,
    *,
    is_current: bool,
    can_update: bool,
    has_pending_approval: bool,
) -> list[str]:
    if not is_current or not can_update:
        return []
    actions: list[str] = []
    if version.status in {
        ResearchQuestionVersionStatus.DRAFT,
        ResearchQuestionVersionStatus.NEEDS_INPUT,
    }:
        actions.extend(
            [
                "research_question.edit",
                "research_question.create_version",
                "research_question.mark_ready",
            ]
        )
    elif version.status in {
        ResearchQuestionVersionStatus.READY,
        ResearchQuestionVersionStatus.CONFIRMED,
    }:
        actions.append("research_question.create_version")
    if (
        version.status == ResearchQuestionVersionStatus.READY
        and not has_pending_approval
    ):
        actions.append("research_question.request_confirmation")
    return actions


def version_data(
    version: ResearchQuestionVersion,
    *,
    current_version_id: uuid.UUID | None = None,
    can_update: bool = False,
    pending_approval: ApprovalRecord | None = None,
) -> dict[str, Any]:
    is_current = version.id == current_version_id
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "id": version.id,
                "research_question_id": version.research_question_id,
                "project_id": version.project_id,
                "version_number": version.version_number,
                "raw_input": version.raw_input,
                "normalized_question": version.normalized_question,
                "research_object": version.research_object,
                "population": version.population,
                "context": version.context,
                "independent_variables": version.independent_variables,
                "dependent_variables": version.dependent_variables,
                "control_variables": version.control_variables,
                "research_goal": version.research_goal,
                "relationship_type": version.relationship_type,
                "method_preference": version.method_preference,
                "time_scope": version.time_scope,
                "region_scope": version.region_scope,
                "language_scope": version.language_scope,
                "resource_constraints": version.resource_constraints,
                "ethical_constraints": version.ethical_constraints,
                "uncertainties": version.uncertainties,
                "source_model_invocation_id": version.source_model_invocation_id,
                "status": version.status,
                "created_by": version.created_by,
                "created_at": version.created_at,
                "is_current": is_current,
                "allowed_actions": _allowed_actions(
                    version,
                    is_current=is_current,
                    can_update=can_update,
                    has_pending_approval=pending_approval is not None,
                ),
                "pending_approval_id": (
                    pending_approval.id if pending_approval is not None else None
                ),
                "pending_approval_status": (
                    pending_approval.status if pending_approval is not None else None
                ),
            }
        ),
    )


def _question_data(
    session: Session,
    question: ResearchQuestion,
    version: ResearchQuestionVersion,
    *,
    can_update: bool,
) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "id": question.id,
                "project_id": question.project_id,
                "status": question.status,
                "current_version_id": question.current_version_id,
                "created_by": question.created_by,
                "created_at": question.created_at,
                "updated_at": question.updated_at,
                "current_version": version_data(
                    version,
                    current_version_id=question.current_version_id,
                    can_update=can_update,
                    pending_approval=_pending_approval(session, version),
                ),
            }
        ),
    )


def _content_from_version(
    version: ResearchQuestionVersion,
) -> ResearchQuestionVersionContent:
    return ResearchQuestionVersionContent(
        raw_input=version.raw_input,
        normalized_question=version.normalized_question,
        research_object=version.research_object,
        population=version.population,
        context=version.context,
        independent_variables=version.independent_variables,
        dependent_variables=version.dependent_variables,
        control_variables=version.control_variables,
        research_goal=version.research_goal,
        relationship_type=version.relationship_type,
        method_preference=version.method_preference,
        time_scope=version.time_scope,
        region_scope=version.region_scope,
        language_scope=version.language_scope,
        resource_constraints=version.resource_constraints,
        ethical_constraints=version.ethical_constraints,
        uncertainties=version.uncertainties,
    )


def _merge_content(
    version: ResearchQuestionVersion, fields: ResearchQuestionVersionFields
) -> ResearchQuestionVersionContent:
    values = _content_from_version(version).model_dump(mode="python")
    values.update(fields.model_dump(exclude_unset=True, mode="python"))
    return ResearchQuestionVersionContent.model_validate(values)


def _approval_payload(
    session: Session, version: ResearchQuestionVersion
) -> dict[str, Any]:
    question = session.get(ResearchQuestion, version.research_question_id)
    if question is None or question.project_id != version.project_id:
        raise _not_found()
    data = version_data(version)
    data["current_version_id"] = str(question.current_version_id)
    return data


def create_research_question(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    content: ResearchQuestionVersionContent,
    _commit_result: bool = True,
) -> tuple[ResearchQuestion, ResearchQuestionVersion]:
    project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="project.update",
        for_update=True,
    )
    existing = session.exec(
        select(ResearchQuestion).where(
            ResearchQuestion.project_id == project_id,
            ResearchQuestion.status != ResearchQuestionStatus.SUPERSEDED,
        )
    ).first()
    if existing is not None:
        raise _invalid_state(
            "The project already has an active ResearchQuestion. Create a new version instead."
        )
    values = _content_values(content)
    question = ResearchQuestion(project_id=project_id, created_by=actor.id)
    session.add(question)
    session.flush()
    version = ResearchQuestionVersion(
        research_question_id=question.id,
        project_id=project_id,
        version_number=1,
        created_by=actor.id,
        **values,
    )
    session.add(version)
    session.flush()
    question.current_version_id = version.id
    question.status = ResearchQuestionStatus.DRAFT
    question.updated_at = get_datetime_utc()
    session.add(question)
    _audit(
        session,
        project_id=project_id,
        actor=actor,
        action="RESEARCH_QUESTION_CREATED",
        object_type="research_question",
        object_id=question.id,
        after={
            "current_version_id": version.id,
            "version_number": version.version_number,
            "status": version.status,
        },
    )
    if _commit_result:
        _commit(session)
        session.refresh(question)
        session.refresh(version)
    return question, version


def create_research_question_command(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    content: ResearchQuestionVersionContent,
    idempotency_key: str,
) -> project_service.OperationResult:
    project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="project.update",
        for_update=True,
    )
    digest = project_service.request_hash(content)
    path = "/api/v1/projects/{project_id}/research-questions"
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
    question, version = create_research_question(
        session,
        actor=actor,
        project_id=project_id,
        content=content,
        _commit_result=False,
    )
    result = project_service.OperationResult(
        data=_question_data(session, question, version, can_update=True),
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


def save_new_version(
    session: Session,
    *,
    actor: User,
    research_question_id: uuid.UUID,
    based_on_version_id: uuid.UUID,
    content: ResearchQuestionVersionContent,
    change_reason: str,
    _commit_result: bool = True,
) -> ResearchQuestionVersion:
    question = session.exec(
        select(ResearchQuestion)
        .where(ResearchQuestion.id == research_question_id)
        .with_for_update()
    ).first()
    if question is None:
        raise _not_found()
    project_service.authorize_project(
        session,
        project_id=question.project_id,
        actor=actor,
        action="project.update",
    )
    if question.current_version_id != based_on_version_id:
        raise ContractError(
            status_code=409,
            code="RESOURCE_VERSION_CONFLICT",
            message="based_on_version_id is not the current ResearchQuestion version.",
            details={"current_version_id": str(question.current_version_id)},
        )
    based_on = session.exec(
        select(ResearchQuestionVersion).where(
            ResearchQuestionVersion.id == based_on_version_id,
            ResearchQuestionVersion.research_question_id == question.id,
            ResearchQuestionVersion.project_id == question.project_id,
        )
    ).first()
    if based_on is None:
        raise _not_found()
    values = _content_values(content)
    version = ResearchQuestionVersion(
        research_question_id=question.id,
        project_id=question.project_id,
        version_number=based_on.version_number + 1,
        created_by=actor.id,
        **values,
    )
    session.add(version)
    session.flush()
    question.current_version_id = version.id
    question.status = ResearchQuestionStatus.DRAFT
    question.updated_at = get_datetime_utc()
    session.add(question)
    _audit(
        session,
        project_id=question.project_id,
        actor=actor,
        action="RESEARCH_QUESTION_VERSION_CREATED",
        object_type=TARGET_OBJECT_TYPE,
        object_id=version.id,
        before={
            "based_on_version_id": based_on.id,
            "version_number": based_on.version_number,
        },
        after={
            "version_id": version.id,
            "version_number": version.version_number,
            "status": version.status,
        },
        reason=change_reason,
    )
    if _commit_result:
        _commit(session)
        session.refresh(version)
    return version


def create_version_command(
    session: Session,
    *,
    actor: User,
    research_question_id: uuid.UUID,
    based_on_version_id: uuid.UUID,
    fields: ResearchQuestionVersionFields,
    change_reason: str,
    idempotency_key: str,
) -> project_service.OperationResult:
    question = session.get(ResearchQuestion, research_question_id)
    if question is None:
        raise _not_found()
    project_service.authorize_project(
        session,
        project_id=question.project_id,
        actor=actor,
        action="project.update",
        for_update=True,
    )
    base = session.exec(
        select(ResearchQuestionVersion).where(
            ResearchQuestionVersion.id == based_on_version_id,
            ResearchQuestionVersion.research_question_id == question.id,
            ResearchQuestionVersion.project_id == question.project_id,
        )
    ).first()
    if base is None:
        raise _not_found()
    request_payload = {
        "based_on_version_id": based_on_version_id,
        "change_reason": change_reason,
        "fields": fields,
    }
    digest = project_service.request_hash(request_payload)
    path = "/api/v1/research-questions/{research_question_id}/versions"
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=question.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    version = save_new_version(
        session,
        actor=actor,
        research_question_id=question.id,
        based_on_version_id=base.id,
        content=_merge_content(base, fields),
        change_reason=change_reason,
        _commit_result=False,
    )
    result = project_service.OperationResult(
        data=version_data(
            version,
            current_version_id=question.current_version_id,
            can_update=True,
        ),
        status_code=201,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=question.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    _commit(session)
    return result


def update_draft_version(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    expected_version_number: int,
    fields: ResearchQuestionVersionFields,
    change_reason: str,
) -> ResearchQuestionVersion:
    version = session.exec(
        select(ResearchQuestionVersion)
        .where(ResearchQuestionVersion.id == version_id)
        .with_for_update()
    ).first()
    if version is None:
        raise _not_found()
    project_service.authorize_project(
        session,
        project_id=version.project_id,
        actor=actor,
        action="project.update",
    )
    if version.version_number != expected_version_number:
        raise ContractError(
            status_code=409,
            code="RESOURCE_VERSION_CONFLICT",
            message="The ResearchQuestionVersion changed.",
            details={
                "expected_lock_version": expected_version_number,
                "current_lock_version": version.version_number,
            },
        )
    if version.status not in {
        ResearchQuestionVersionStatus.DRAFT,
        ResearchQuestionVersionStatus.NEEDS_INPUT,
    }:
        raise _invalid_state("Only DRAFT or NEEDS_INPUT versions may be updated.")
    return save_new_version(
        session,
        actor=actor,
        research_question_id=version.research_question_id,
        based_on_version_id=version.id,
        content=_merge_content(version, fields),
        change_reason=change_reason,
    )


def get_research_question(
    session: Session, *, actor: User, research_question_id: uuid.UUID
) -> dict[str, Any]:
    question = session.get(ResearchQuestion, research_question_id)
    if question is None:
        raise _not_found()
    access = project_service.authorize_project(
        session,
        project_id=question.project_id,
        actor=actor,
        action="project.read",
    )
    if question.current_version_id is None:
        raise _invalid_state("ResearchQuestion has no current version.")
    version = session.exec(
        select(ResearchQuestionVersion).where(
            ResearchQuestionVersion.id == question.current_version_id,
            ResearchQuestionVersion.research_question_id == question.id,
            ResearchQuestionVersion.project_id == question.project_id,
        )
    ).first()
    if version is None:
        raise _invalid_state("ResearchQuestion current version is unavailable.")
    return _question_data(
        session,
        question,
        version,
        can_update=_can_update(access),
    )


def get_current_for_project(
    session: Session, *, actor: User, project_id: uuid.UUID
) -> dict[str, Any]:
    access = project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="project.read",
    )
    can_update = _can_update(access)
    capability_availability = {
        "research_question": "AVAILABLE",
        "ai_parse": "NOT_AVAILABLE",
        "query_plan": "NOT_AVAILABLE",
        "literature": "NOT_AVAILABLE",
    }
    questions = session.exec(
        select(ResearchQuestion)
        .where(
            ResearchQuestion.project_id == project_id,
            ResearchQuestion.status != ResearchQuestionStatus.SUPERSEDED,
        )
        .order_by(col(ResearchQuestion.updated_at).desc())
        .limit(2)
    ).all()
    if len(questions) > 1:
        raise _invalid_state("The project has more than one active ResearchQuestion.")
    if not questions:
        return {
            "question": None,
            "allowed_actions": (["research_question.create"] if can_update else []),
            "capability_availability": capability_availability,
        }
    question = questions[0]
    if question.current_version_id is None:
        raise _invalid_state("ResearchQuestion has no current version.")
    version = session.exec(
        select(ResearchQuestionVersion).where(
            ResearchQuestionVersion.id == question.current_version_id,
            ResearchQuestionVersion.research_question_id == question.id,
            ResearchQuestionVersion.project_id == project_id,
        )
    ).first()
    if version is None:
        raise _invalid_state("ResearchQuestion current version is unavailable.")
    return {
        "question": _question_data(
            session,
            question,
            version,
            can_update=can_update,
        ),
        "allowed_actions": [],
        "capability_availability": capability_availability,
    }


def get_version(
    session: Session, *, actor: User, version_id: uuid.UUID
) -> dict[str, Any]:
    version = session.get(ResearchQuestionVersion, version_id)
    if version is None:
        raise _not_found()
    access = project_service.authorize_project(
        session,
        project_id=version.project_id,
        actor=actor,
        action="project.read",
    )
    question = session.get(ResearchQuestion, version.research_question_id)
    if question is None or question.project_id != version.project_id:
        raise _not_found()
    return version_data(
        version,
        current_version_id=question.current_version_id,
        can_update=_can_update(access),
        pending_approval=_pending_approval(session, version),
    )


def list_versions(
    session: Session, *, actor: User, research_question_id: uuid.UUID
) -> list[dict[str, Any]]:
    question = session.get(ResearchQuestion, research_question_id)
    if question is None:
        raise _not_found()
    access = project_service.authorize_project(
        session,
        project_id=question.project_id,
        actor=actor,
        action="project.read",
    )
    versions = session.exec(
        select(ResearchQuestionVersion)
        .where(
            ResearchQuestionVersion.research_question_id == question.id,
            ResearchQuestionVersion.project_id == question.project_id,
        )
        .order_by(col(ResearchQuestionVersion.version_number))
    ).all()
    can_update = _can_update(access)
    return [
        version_data(
            version,
            current_version_id=question.current_version_id,
            can_update=can_update,
            pending_approval=_pending_approval(session, version),
        )
        for version in versions
    ]


def transition_version_status(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    target_status: ResearchQuestionVersionStatus,
    reason: str | None = None,
    _commit_result: bool = True,
) -> ResearchQuestionVersion:
    version = session.exec(
        select(ResearchQuestionVersion)
        .where(ResearchQuestionVersion.id == version_id)
        .with_for_update()
    ).first()
    if version is None:
        raise _not_found()
    project_service.authorize_project(
        session,
        project_id=version.project_id,
        actor=actor,
        action="project.update",
    )
    allowed = {
        ResearchQuestionVersionStatus.DRAFT: {
            ResearchQuestionVersionStatus.NEEDS_INPUT,
            ResearchQuestionVersionStatus.READY,
        },
        ResearchQuestionVersionStatus.NEEDS_INPUT: {
            ResearchQuestionVersionStatus.DRAFT,
            ResearchQuestionVersionStatus.READY,
        },
    }
    if target_status not in allowed.get(version.status, set()):
        raise _invalid_state(
            f"ResearchQuestionVersion cannot transition from {version.status} "
            f"to {target_status}."
        )
    before = {"status": version.status}
    version.status = target_status
    session.add(version)
    question = session.get(ResearchQuestion, version.research_question_id)
    if (
        question is None
        or question.project_id != version.project_id
        or question.current_version_id != version.id
    ):
        raise _invalid_state("Only the current ResearchQuestionVersion may transition.")
    question.updated_at = get_datetime_utc()
    session.add(question)
    _audit(
        session,
        project_id=version.project_id,
        actor=actor,
        action="RESEARCH_QUESTION_VERSION_STATUS_CHANGED",
        object_type=TARGET_OBJECT_TYPE,
        object_id=version.id,
        before=before,
        after={"status": target_status},
        reason=reason,
    )
    if _commit_result:
        _commit(session)
        session.refresh(version)
    return version


def mark_version_ready_command(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    reason: str | None,
    idempotency_key: str,
) -> project_service.OperationResult:
    version = session.get(ResearchQuestionVersion, version_id)
    if version is None:
        raise _not_found()
    project_service.authorize_project(
        session,
        project_id=version.project_id,
        actor=actor,
        action="project.update",
        for_update=True,
    )
    digest = project_service.request_hash(
        {"version_id": version_id, "target_status": "READY", "reason": reason}
    )
    path = "/api/v1/research-question-versions/{version_id}/ready"
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    version = transition_version_status(
        session,
        actor=actor,
        version_id=version.id,
        target_status=ResearchQuestionVersionStatus.READY,
        reason=reason,
        _commit_result=False,
    )
    question = session.get(ResearchQuestion, version.research_question_id)
    if question is None or question.project_id != version.project_id:
        raise _not_found()
    result = project_service.OperationResult(
        data=version_data(
            version,
            current_version_id=question.current_version_id,
            can_update=True,
        ),
        status_code=200,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    _commit(session)
    return result


def request_confirmation(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    _commit_result: bool = True,
) -> ApprovalRecord:
    version = session.exec(
        select(ResearchQuestionVersion)
        .where(ResearchQuestionVersion.id == version_id)
        .with_for_update()
    ).first()
    if version is None:
        raise _not_found()
    project_service.authorize_project(
        session,
        project_id=version.project_id,
        actor=actor,
        action="project.update",
    )
    if version.status in {
        ResearchQuestionVersionStatus.DRAFT,
        ResearchQuestionVersionStatus.NEEDS_INPUT,
    }:
        before_status = version.status
        version.status = ResearchQuestionVersionStatus.READY
        session.add(version)
        _system_audit(
            session,
            project_id=version.project_id,
            action="RESEARCH_QUESTION_VERSION_VALIDATED",
            object_id=version.id,
            before={"status": before_status},
            after={"status": version.status},
        )
        session.flush([version])
    elif version.status != ResearchQuestionVersionStatus.READY:
        raise _invalid_state("Only a READY ResearchQuestionVersion may be submitted.")
    pending = session.exec(
        select(ApprovalRecord).where(
            ApprovalRecord.project_id == version.project_id,
            ApprovalRecord.approval_type == ApprovalType.RESEARCH_QUESTION_CONFIRMATION,
            ApprovalRecord.target_object_type == TARGET_OBJECT_TYPE,
            ApprovalRecord.target_object_id == version.id,
            ApprovalRecord.status == ApprovalStatus.PENDING,
        )
    ).first()
    if pending is not None:
        return pending
    approval = approval_service.create_approval(
        session,
        command=approval_service.ApprovalCreate(
            project_id=version.project_id,
            approval_type=ApprovalType.RESEARCH_QUESTION_CONFIRMATION,
            target_object_type=TARGET_OBJECT_TYPE,
            target_object_id=version.id,
            requested_by_actor_type=AuditActorType.USER,
            requested_by_actor_id=str(actor.id),
            payload_snapshot=_approval_payload(session, version),
            impact_summary={
                "research_question_id": str(version.research_question_id),
                "version_number": version.version_number,
            },
        ),
    )
    _audit(
        session,
        project_id=version.project_id,
        actor=actor,
        action="RESEARCH_QUESTION_CONFIRMATION_REQUESTED",
        object_type=TARGET_OBJECT_TYPE,
        object_id=version.id,
        after={"approval_id": approval.id, "status": version.status},
        approval_id=approval.id,
    )
    if _commit_result:
        _commit(session)
        session.refresh(approval)
    return approval


def request_confirmation_command(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    idempotency_key: str,
) -> project_service.OperationResult:
    version = session.get(ResearchQuestionVersion, version_id)
    if version is None:
        raise _not_found()
    project_service.authorize_project(
        session,
        project_id=version.project_id,
        actor=actor,
        action="project.update",
        for_update=True,
    )
    digest = project_service.request_hash({"version_id": version_id})
    path = "/api/v1/research-question-versions/{version_id}/approval-requests"
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    approval = request_confirmation(
        session,
        actor=actor,
        version_id=version.id,
        _commit_result=False,
    )
    data = cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "id": approval.id,
                "project_id": approval.project_id,
                "target_object_id": approval.target_object_id,
                "status": approval.status,
            }
        ),
    )
    result = project_service.OperationResult(data=data, status_code=201)
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    _commit(session)
    return result


def resolve_approval_payload(
    session: Session, approval: ApprovalRecord
) -> dict[str, Any]:
    version = session.exec(
        select(ResearchQuestionVersion).where(
            ResearchQuestionVersion.id == approval.target_object_id,
            ResearchQuestionVersion.project_id == approval.project_id,
        )
    ).first()
    if version is None:
        raise _not_found()
    return _approval_payload(session, version)


def _apply_approval_decision(
    session: Session,
    approval: ApprovalRecord,
    decision: ApprovalStatus,
    actor: User,
) -> None:
    if approval.approval_type != ApprovalType.RESEARCH_QUESTION_CONFIRMATION:
        raise _invalid_state(
            "Approval type does not match ResearchQuestion confirmation."
        )
    version = session.exec(
        select(ResearchQuestionVersion)
        .where(
            ResearchQuestionVersion.id == approval.target_object_id,
            ResearchQuestionVersion.project_id == approval.project_id,
        )
        .with_for_update()
    ).first()
    if version is None:
        raise _not_found()
    question = session.exec(
        select(ResearchQuestion)
        .where(
            ResearchQuestion.id == version.research_question_id,
            ResearchQuestion.project_id == version.project_id,
        )
        .with_for_update()
    ).first()
    project = session.exec(
        select(ResearchProject)
        .where(ResearchProject.id == version.project_id)
        .with_for_update()
    ).first()
    if question is None or project is None or question.current_version_id != version.id:
        raise _invalid_state("The Approval target is no longer the current version.")
    if decision == ApprovalStatus.REJECTED:
        if version.status != ResearchQuestionVersionStatus.READY:
            raise _invalid_state("Only a READY version may be rejected.")
        version.status = ResearchQuestionVersionStatus.DRAFT
        session.add(version)
        _audit(
            session,
            project_id=version.project_id,
            actor=actor,
            action="RESEARCH_QUESTION_CONFIRMATION_REJECTED",
            object_type=TARGET_OBJECT_TYPE,
            object_id=version.id,
            before={"status": ResearchQuestionVersionStatus.READY},
            after={"status": version.status},
            reason=approval.decision_reason,
            approval_id=approval.id,
        )
        return
    if decision != ApprovalStatus.APPROVED:
        raise _invalid_state("Unsupported ResearchQuestion Approval decision.")
    if version.status != ResearchQuestionVersionStatus.READY:
        raise _invalid_state("Only a READY version may be confirmed.")

    previous_version: ResearchQuestionVersion | None = None
    previous_question: ResearchQuestion | None = None
    if project.current_research_question_version_id is not None:
        previous_version = session.exec(
            select(ResearchQuestionVersion)
            .where(
                ResearchQuestionVersion.id
                == project.current_research_question_version_id,
                ResearchQuestionVersion.project_id == project.id,
            )
            .with_for_update()
        ).first()
        if previous_version is not None and previous_version.id != version.id:
            previous_question = session.exec(
                select(ResearchQuestion)
                .where(
                    ResearchQuestion.id == previous_version.research_question_id,
                    ResearchQuestion.project_id == project.id,
                )
                .with_for_update()
            ).first()
            previous_version.status = ResearchQuestionVersionStatus.SUPERSEDED
            session.add(previous_version)
            if previous_question is not None and previous_question.id != question.id:
                previous_question.status = ResearchQuestionStatus.SUPERSEDED
                previous_question.updated_at = get_datetime_utc()
                session.add(previous_question)

    version.status = ResearchQuestionVersionStatus.CONFIRMED
    question.status = ResearchQuestionStatus.CONFIRMED
    question.updated_at = get_datetime_utc()
    project.current_research_question_version_id = version.id
    project.updated_at = get_datetime_utc()
    session.add(version)
    session.add(question)
    session.add(project)
    _audit(
        session,
        project_id=version.project_id,
        actor=actor,
        action="RESEARCH_QUESTION_CONFIRMED",
        object_type=TARGET_OBJECT_TYPE,
        object_id=version.id,
        before={
            "status": ResearchQuestionVersionStatus.READY,
            "previous_confirmed_version_id": previous_version.id
            if previous_version is not None and previous_version.id != version.id
            else None,
        },
        after={"status": version.status},
        reason=approval.decision_reason,
        approval_id=approval.id,
    )


def register_approval_handlers() -> None:
    approval_service.register_payload_resolver(
        TARGET_OBJECT_TYPE, resolve_approval_payload
    )
    approval_service.register_decision_handler(
        TARGET_OBJECT_TYPE, _apply_approval_decision
    )
