from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, func, select

from app.api.errors import ContractError
from app.core.observability import current_request_id
from app.models import (
    AgentEvent,
    AgentEventType,
    AgentRun,
    AgentRunStatus,
    ApprovalRecord,
    ApprovalStatus,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    Job,
    ToolCall,
    ToolCallStatus,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

from .policies import PolicyDenied, validate_tool_policy
from .registry import Confirmation
from .schemas import (
    AgentRunCreate,
    AgentRunView,
    SafeSummary,
    ToolCallRequest,
    ToolCallView,
)
from .snapshot import (
    build_project_context_snapshot,
    canonical_hash,
    snapshot_is_current,
)

RUN_TERMINAL = {
    AgentRunStatus.COMPLETED,
    AgentRunStatus.FAILED,
    AgentRunStatus.CANCELLED,
}
TOOL_TERMINAL = {
    ToolCallStatus.COMPLETED,
    ToolCallStatus.FAILED,
    ToolCallStatus.DENIED,
    ToolCallStatus.CANCELLED,
}
RUN_TRANSITIONS: dict[AgentRunStatus, set[AgentRunStatus]] = {
    AgentRunStatus.CREATED: {
        AgentRunStatus.PLANNING,
        AgentRunStatus.CANCELLED,
        AgentRunStatus.FAILED,
    },
    AgentRunStatus.PLANNING: {
        AgentRunStatus.WAITING_USER_INPUT,
        AgentRunStatus.WAITING_APPROVAL,
        AgentRunStatus.CALLING_TOOL,
        AgentRunStatus.REVIEWING,
        AgentRunStatus.FAILED,
        AgentRunStatus.CANCELLED,
    },
    AgentRunStatus.WAITING_USER_INPUT: {
        AgentRunStatus.PLANNING,
        AgentRunStatus.CANCELLED,
        AgentRunStatus.FAILED,
    },
    AgentRunStatus.WAITING_APPROVAL: {
        AgentRunStatus.PLANNING,
        AgentRunStatus.CALLING_TOOL,
        AgentRunStatus.CANCELLED,
        AgentRunStatus.FAILED,
    },
    AgentRunStatus.CALLING_TOOL: {
        AgentRunStatus.PLANNING,
        AgentRunStatus.WAITING_APPROVAL,
        AgentRunStatus.REVIEWING,
        AgentRunStatus.FAILED,
        AgentRunStatus.CANCELLED,
    },
    AgentRunStatus.REVIEWING: {
        AgentRunStatus.PLANNING,
        AgentRunStatus.COMPLETED,
        AgentRunStatus.FAILED,
        AgentRunStatus.CANCELLED,
    },
}
TOOL_TRANSITIONS: dict[ToolCallStatus, set[ToolCallStatus]] = {
    ToolCallStatus.REQUESTED: {
        ToolCallStatus.WAITING_APPROVAL,
        ToolCallStatus.RUNNING,
        ToolCallStatus.DENIED,
        ToolCallStatus.CANCELLED,
        ToolCallStatus.FAILED,
    },
    ToolCallStatus.WAITING_APPROVAL: {
        ToolCallStatus.RUNNING,
        ToolCallStatus.DENIED,
        ToolCallStatus.CANCELLED,
        ToolCallStatus.FAILED,
    },
    ToolCallStatus.RUNNING: {
        ToolCallStatus.COMPLETED,
        ToolCallStatus.FAILED,
        ToolCallStatus.CANCELLED,
    },
}


def _conflict(code: str, message: str) -> ContractError:
    return ContractError(status_code=409, code=code, message=message)


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise _conflict(
            "AGENT_RUNTIME_CONFLICT", "The operation conflicted with concurrent state."
        ) from exc


def _audit(
    session: Session,
    *,
    project_id: uuid.UUID,
    actor: User,
    action: str,
    object_type: str,
    object_id: uuid.UUID,
    request_id: str | None,
    agent_run_id: uuid.UUID | None = None,
    tool_call_id: uuid.UUID | None = None,
    outcome: AuditOutcome = AuditOutcome.SUCCEEDED,
    summary: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditLog(
            project_id=project_id,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
            action=action,
            object_type=object_type,
            object_id=object_id,
            after_snapshot=summary,
            request_id=request_id,
            agent_run_id=agent_run_id,
            tool_call_id=tool_call_id,
            outcome=outcome,
        )
    )


def _run_actions(run: AgentRun) -> list[str]:
    if run.status in RUN_TERMINAL:
        return []
    actions = ["agent_run.cancel", "agent_run.read"]
    if run.status == AgentRunStatus.WAITING_USER_INPUT:
        actions.append("agent_run.continue")
    return sorted(actions)


def _tool_actions(call: ToolCall) -> list[str]:
    if call.status in TOOL_TERMINAL:
        return []
    return ["tool_call.cancel", "tool_call.read"]


def _run_view(run: AgentRun, *, replayed: bool = False) -> AgentRunView:
    return AgentRunView(
        id=run.id,
        project_id=run.project_id,
        status=run.status,
        lock_version=run.lock_version,
        snapshot_hash=run.snapshot_hash,
        safe_snapshot_summary=run.safe_snapshot_summary,
        allowed_actions=_run_actions(run),
        failure_code=run.failure_code,
        created_at=run.created_at,
        completed_at=run.completed_at,
        idempotency_replayed=replayed,
    )


def _tool_view(call: ToolCall, *, replayed: bool = False) -> ToolCallView:
    return ToolCallView(
        id=call.id,
        project_id=call.project_id,
        agent_run_id=call.agent_run_id,
        tool_name=call.tool_name,
        tool_version=call.tool_version,
        status=call.status,
        allowed_actions=_tool_actions(call),
        error_code=call.error_code,
        retryable=call.retryable,
        idempotency_replayed=replayed,
    )


def create_agent_run(
    session: Session, *, actor: User, command: AgentRunCreate
) -> AgentRunView:
    project_service.authorize_project(
        session, project_id=command.project_id, actor=actor, action="project.read"
    )
    payload_hash = canonical_hash(
        command.model_dump(
            mode="json",
            exclude={"idempotency_key", "request_id", "correlation_id"},
        )
    )
    existing = session.exec(
        select(AgentRun).where(
            AgentRun.project_id == command.project_id,
            AgentRun.requested_by_user_id == actor.id,
            AgentRun.idempotency_key == command.idempotency_key,
        )
    ).first()
    if existing is not None:
        if existing.request_payload_hash != payload_hash:
            raise _conflict(
                "IDEMPOTENCY_CONFLICT",
                "The Idempotency-Key was used with a different payload.",
            )
        return _run_view(existing, replayed=True)
    if command.retry_of_agent_run_id is not None:
        previous = session.exec(
            select(AgentRun).where(
                AgentRun.id == command.retry_of_agent_run_id,
                AgentRun.project_id == command.project_id,
            )
        ).first()
        if previous is None:
            raise ContractError(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="Resource not found.",
            )
        if previous.status not in RUN_TERMINAL:
            raise _conflict(
                "AGENT_RUN_INVALID_STATE", "Retry requires a terminal AgentRun."
            )
    snapshot = build_project_context_snapshot(
        session, actor=actor, project_id=command.project_id
    )
    request_id = command.request_id or current_request_id()
    run = AgentRun(
        project_id=command.project_id,
        requested_by_user_id=actor.id,
        request_id=request_id,
        correlation_id=command.correlation_id,
        idempotency_key=command.idempotency_key,
        request_payload_hash=payload_hash,
        safe_input_summary=command.safe_input_summary.model_dump(mode="json"),
        snapshot_schema_version=snapshot.schema_version,
        snapshot_revision=snapshot.revision,
        snapshot_hash=snapshot.canonical_hash,
        source_object_versions=snapshot.source_object_versions,
        safe_snapshot_summary=snapshot.safe_snapshot_summary,
        max_turns=command.max_turns,
        max_tool_calls=command.max_tool_calls,
        retry_of_agent_run_id=command.retry_of_agent_run_id,
    )
    session.add(run)
    session.flush()
    _audit(
        session,
        project_id=run.project_id,
        actor=actor,
        action="AGENT_RUN_CREATED",
        object_type="agent_run",
        object_id=run.id,
        request_id=request_id,
        agent_run_id=run.id,
        summary={"status": run.status.value, "snapshot_hash": run.snapshot_hash},
    )
    _commit(session)
    session.refresh(run)
    return _run_view(run)


def get_agent_run(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    agent_run_id: uuid.UUID,
    for_update: bool = False,
) -> AgentRun:
    project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="project.read"
    )
    statement = select(AgentRun).where(
        AgentRun.id == agent_run_id, AgentRun.project_id == project_id
    )
    if for_update:
        statement = statement.with_for_update()
    run = session.exec(statement).first()
    if run is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    return run


def list_agent_runs(
    session: Session, *, actor: User, project_id: uuid.UUID, limit: int = 50
) -> list[AgentRunView]:
    project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="project.read"
    )
    runs = session.exec(
        select(AgentRun)
        .where(AgentRun.project_id == project_id)
        .order_by(col(AgentRun.created_at).desc())
        .limit(min(max(limit, 1), 100))
    ).all()
    return [_run_view(run) for run in runs]


def transition_agent_run(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    agent_run_id: uuid.UUID,
    target: AgentRunStatus,
    failure_code: str | None = None,
    commit: bool = True,
) -> AgentRunView:
    run = get_agent_run(
        session,
        actor=actor,
        project_id=project_id,
        agent_run_id=agent_run_id,
        for_update=True,
    )
    if target not in RUN_TRANSITIONS.get(run.status, set()):
        raise _conflict(
            "AGENT_RUN_INVALID_STATE", "The AgentRun state transition is invalid."
        )
    if target == AgentRunStatus.FAILED and not failure_code:
        raise _conflict(
            "AGENT_RUN_FAILURE_CODE_REQUIRED",
            "Failed AgentRuns require a safe error code.",
        )
    run.status = target
    run.failure_code = failure_code if target == AgentRunStatus.FAILED else None
    run.completed_at = get_datetime_utc() if target in RUN_TERMINAL else None
    run.updated_at = get_datetime_utc()
    run.lock_version += 1
    session.add(run)
    _audit(
        session,
        project_id=run.project_id,
        actor=actor,
        action=f"AGENT_RUN_{target.value}",
        object_type="agent_run",
        object_id=run.id,
        request_id=run.request_id,
        agent_run_id=run.id,
        summary={"status": target.value},
    )
    if commit:
        _commit(session)
    else:
        session.flush()
    session.refresh(run)
    return _run_view(run)


def cancel_agent_run(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    agent_run_id: uuid.UUID,
    commit: bool = True,
) -> AgentRunView:
    return transition_agent_run(
        session,
        actor=actor,
        project_id=project_id,
        agent_run_id=agent_run_id,
        target=AgentRunStatus.CANCELLED,
        commit=commit,
    )


def append_agent_event(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    agent_run_id: uuid.UUID,
    event_type: AgentEventType,
    safe_summary: SafeSummary,
    commit: bool = True,
) -> AgentEvent:
    run = get_agent_run(
        session,
        actor=actor,
        project_id=project_id,
        agent_run_id=agent_run_id,
        for_update=True,
    )
    if run.status in RUN_TERMINAL:
        raise _conflict(
            "AGENT_RUN_INVALID_STATE", "Terminal AgentRuns cannot receive events."
        )
    current, rebuilt = snapshot_is_current(
        session, actor=actor, project_id=project_id, expected_hash=run.snapshot_hash
    )
    if not current:
        run.snapshot_revision = rebuilt.revision
        run.snapshot_hash = rebuilt.canonical_hash
        run.source_object_versions = rebuilt.source_object_versions
        run.safe_snapshot_summary = rebuilt.safe_snapshot_summary
        run.updated_at = get_datetime_utc()
        run.lock_version += 1
    sequence = (
        session.exec(
            select(func.count())
            .select_from(AgentEvent)
            .where(AgentEvent.agent_run_id == run.id)
        ).one()
        + 1
    )
    summary = safe_summary.model_dump(mode="json")
    event = AgentEvent(
        project_id=project_id,
        agent_run_id=run.id,
        sequence_number=sequence,
        event_type=event_type,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        safe_summary=summary,
        content_hash=canonical_hash(summary),
        request_id=run.request_id,
    )
    session.add(run)
    session.add(event)
    if commit:
        _commit(session)
    else:
        session.flush()
    session.refresh(event)
    return event


def request_tool_call(
    session: Session, *, actor: User, project_id: uuid.UUID, command: ToolCallRequest
) -> ToolCallView:
    run = get_agent_run(
        session,
        actor=actor,
        project_id=project_id,
        agent_run_id=command.agent_run_id,
        for_update=True,
    )
    if run.status in RUN_TERMINAL:
        raise _conflict(
            "AGENT_RUN_INVALID_STATE", "Terminal AgentRuns cannot request Tools."
        )
    existing = session.exec(
        select(ToolCall).where(
            ToolCall.agent_run_id == run.id,
            ToolCall.idempotency_key == command.idempotency_key,
        )
    ).first()
    input_payload = command.model_dump(mode="json", exclude={"idempotency_key"})
    input_hash = canonical_hash(input_payload)
    if existing is not None:
        if existing.input_hash != input_hash:
            raise _conflict(
                "IDEMPOTENCY_CONFLICT",
                "The Tool Idempotency-Key was used with a different payload.",
            )
        return _tool_view(existing, replayed=True)
    current, snapshot = snapshot_is_current(
        session, actor=actor, project_id=project_id, expected_hash=run.snapshot_hash
    )
    try:
        definition = validate_tool_policy(
            name=command.tool_name,
            version=command.tool_version,
            project_stage=snapshot.project_stage,
            permissions=set(snapshot.permissions),
            snapshot_current=current,
            arguments=command.policy_arguments
            or {
                "source_ids": command.source_ids,
                "options": {},
                "query": command.safe_input_summary.text,
            },
        )
    except PolicyDenied as exc:
        raise ContractError(status_code=409, code=exc.code, message=str(exc)) from exc
    if run.tool_call_count >= run.max_tool_calls:
        raise _conflict(
            "AGENT_TOOL_CALL_LIMIT", "The AgentRun Tool call limit was reached."
        )
    available_ids = {
        resource_id
        for resource_ids in snapshot.available_resources.values()
        for resource_id in resource_ids
    }
    if any(str(source_id) not in available_ids for source_id in command.source_ids):
        raise _conflict(
            "TOOL_SOURCE_INVALID", "A Tool source is missing or not available."
        )
    if any(
        snapshot.source_object_versions.get(name) != value
        for name, value in command.source_hashes.items()
    ):
        raise _conflict(
            "TOOL_SOURCE_HASH_MISMATCH", "A Tool source version or hash is stale."
        )
    if command.retry_of_tool_call_id is not None:
        previous = session.exec(
            select(ToolCall).where(
                ToolCall.id == command.retry_of_tool_call_id,
                ToolCall.project_id == project_id,
                ToolCall.agent_run_id == run.id,
            )
        ).first()
        if previous is None:
            raise ContractError(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="Resource not found.",
            )
        if previous.status not in TOOL_TERMINAL:
            raise _conflict(
                "TOOL_CALL_INVALID_STATE", "Retry requires a terminal ToolCall."
            )
    status = (
        ToolCallStatus.WAITING_APPROVAL
        if definition.confirmation == Confirmation.FORMAL_APPROVAL
        else ToolCallStatus.REQUESTED
    )
    call = ToolCall(
        project_id=project_id,
        agent_run_id=run.id,
        requested_by_user_id=actor.id,
        tool_name=definition.name,
        tool_version=definition.version,
        status=status,
        request_id=command.request_id or current_request_id(),
        idempotency_key=command.idempotency_key,
        input_hash=input_hash,
        safe_input_summary=command.safe_input_summary.model_dump(mode="json"),
        retry_of_tool_call_id=command.retry_of_tool_call_id,
    )
    run.tool_call_count += 1
    run.status = (
        AgentRunStatus.WAITING_APPROVAL
        if status == ToolCallStatus.WAITING_APPROVAL
        else AgentRunStatus.CALLING_TOOL
    )
    run.updated_at = get_datetime_utc()
    run.lock_version += 1
    session.add(run)
    session.add(call)
    session.flush()
    _audit(
        session,
        project_id=project_id,
        actor=actor,
        action="TOOL_CALL_REQUESTED",
        object_type="tool_call",
        object_id=call.id,
        request_id=call.request_id,
        agent_run_id=run.id,
        tool_call_id=call.id,
        summary={
            "tool_name": call.tool_name,
            "tool_version": call.tool_version,
            "status": call.status.value,
            "input_hash": call.input_hash,
        },
    )
    _commit(session)
    session.refresh(call)
    return _tool_view(call)


def transition_tool_call(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    tool_call_id: uuid.UUID,
    target: ToolCallStatus,
    safe_output_summary: SafeSummary | None = None,
    error_code: str | None = None,
    retryable: bool = False,
    approval_id: uuid.UUID | None = None,
    approval_payload_hash: str | None = None,
    job_id: uuid.UUID | None = None,
    output_object_type: str | None = None,
    output_object_id: uuid.UUID | None = None,
    commit: bool = True,
) -> ToolCallView:
    project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="project.read"
    )
    call = session.exec(
        select(ToolCall)
        .where(ToolCall.id == tool_call_id, ToolCall.project_id == project_id)
        .with_for_update()
    ).first()
    if call is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    if target not in TOOL_TRANSITIONS.get(call.status, set()):
        raise _conflict(
            "TOOL_CALL_INVALID_STATE", "The ToolCall state transition is invalid."
        )
    if target in {ToolCallStatus.FAILED, ToolCallStatus.DENIED} and not error_code:
        raise _conflict(
            "TOOL_CALL_ERROR_CODE_REQUIRED",
            "Failed or denied ToolCalls require a safe error code.",
        )
    if target == ToolCallStatus.RUNNING:
        if call.status == ToolCallStatus.WAITING_APPROVAL:
            if approval_id is None or approval_payload_hash is None:
                raise _conflict(
                    "APPROVAL_REQUIRED", "A valid external ApprovalRecord is required."
                )
            approval = session.exec(
                select(ApprovalRecord).where(
                    ApprovalRecord.id == approval_id,
                    ApprovalRecord.project_id == project_id,
                )
            ).first()
            if (
                approval is None
                or approval.status != ApprovalStatus.APPROVED
                or approval.payload_hash != approval_payload_hash
                or approval.decision_by_user_id is None
            ):
                raise _conflict(
                    "APPROVAL_INVALID",
                    "Approval is missing, stale, rejected, foreign, or hash-mismatched.",
                )
        call.started_at = get_datetime_utc()
    if target == ToolCallStatus.COMPLETED and safe_output_summary is None:
        raise _conflict(
            "TOOL_CALL_OUTPUT_REQUIRED",
            "Completed ToolCalls require a safe output summary.",
        )
    call.status = target
    call.approval_id = approval_id or call.approval_id
    call.approval_payload_hash = approval_payload_hash or call.approval_payload_hash
    call.job_id = job_id or call.job_id
    call.error_code = (
        error_code if target in {ToolCallStatus.FAILED, ToolCallStatus.DENIED} else None
    )
    call.retryable = retryable if target == ToolCallStatus.FAILED else False
    call.output_object_type = output_object_type
    call.output_object_id = output_object_id
    if safe_output_summary is not None:
        call.safe_output_summary = safe_output_summary.model_dump(mode="json")
        call.output_hash = canonical_hash(call.safe_output_summary)
    call.completed_at = get_datetime_utc() if target in TOOL_TERMINAL else None
    session.add(call)
    _audit(
        session,
        project_id=project_id,
        actor=actor,
        action=f"TOOL_CALL_{target.value}",
        object_type="tool_call",
        object_id=call.id,
        request_id=call.request_id,
        agent_run_id=call.agent_run_id,
        tool_call_id=call.id,
        outcome=AuditOutcome.DENIED
        if target == ToolCallStatus.DENIED
        else AuditOutcome.SUCCEEDED,
        summary={"status": target.value, "error_code": call.error_code},
    )
    if commit:
        _commit(session)
    else:
        session.flush()
    session.refresh(call)
    return _tool_view(call)


def bind_tool_call_approval(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    tool_call_id: uuid.UUID,
    approval_id: uuid.UUID,
    approval_payload_hash: str,
    target_object_type: str,
    target_object_id: uuid.UUID,
) -> ToolCallView:
    project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="project.read"
    )
    call = session.exec(
        select(ToolCall)
        .where(ToolCall.id == tool_call_id, ToolCall.project_id == project_id)
        .with_for_update()
    ).first()
    if call is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    if call.status != ToolCallStatus.WAITING_APPROVAL:
        raise _conflict(
            "TOOL_CALL_INVALID_STATE", "Only a waiting ToolCall may bind Approval."
        )
    approval = session.exec(
        select(ApprovalRecord).where(
            ApprovalRecord.id == approval_id,
            ApprovalRecord.project_id == project_id,
        )
    ).first()
    if (
        approval is None
        or approval.status not in {ApprovalStatus.PENDING, ApprovalStatus.APPROVED}
        or approval.payload_hash != approval_payload_hash
        or approval.target_object_type != target_object_type
        or approval.target_object_id != target_object_id
        or (
            approval.expires_at is not None
            and approval.expires_at <= get_datetime_utc()
        )
    ):
        raise _conflict(
            "APPROVAL_INVALID",
            "Approval is missing, stale, rejected, foreign, expired, or hash-mismatched.",
        )
    call.approval_id = approval.id
    call.approval_payload_hash = approval.payload_hash
    session.add(call)
    _audit(
        session,
        project_id=project_id,
        actor=actor,
        action="TOOL_CALL_APPROVAL_BOUND",
        object_type="tool_call",
        object_id=call.id,
        request_id=call.request_id,
        agent_run_id=call.agent_run_id,
        tool_call_id=call.id,
        summary={
            "tool_name": call.tool_name,
            "approval_id": str(approval.id),
            "approval_payload_hash": approval.payload_hash,
        },
    )
    _commit(session)
    session.refresh(call)
    return _tool_view(call)


def attach_tool_call_job(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    tool_call_id: uuid.UUID,
    job_id: uuid.UUID,
    output_object_type: str,
    output_object_id: uuid.UUID,
) -> ToolCallView:
    project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="project.read"
    )
    call = session.exec(
        select(ToolCall)
        .where(ToolCall.id == tool_call_id, ToolCall.project_id == project_id)
        .with_for_update()
    ).first()
    job = session.get(Job, job_id)
    if call is None or job is None or job.project_id != project_id:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    if call.status != ToolCallStatus.RUNNING:
        raise _conflict(
            "TOOL_CALL_INVALID_STATE", "Only a running ToolCall may attach a Job."
        )
    if call.job_id is not None:
        if (
            call.job_id == job_id
            and call.output_object_type == output_object_type
            and call.output_object_id == output_object_id
        ):
            return _tool_view(call)
        raise _conflict(
            "TOOL_CALL_JOB_MISMATCH", "The ToolCall already references another Job."
        )
    call.job_id = job.id
    call.output_object_type = output_object_type
    call.output_object_id = output_object_id
    session.add(call)
    _audit(
        session,
        project_id=project_id,
        actor=actor,
        action="TOOL_CALL_JOB_ATTACHED",
        object_type="tool_call",
        object_id=call.id,
        request_id=call.request_id,
        agent_run_id=call.agent_run_id,
        tool_call_id=call.id,
        summary={
            "job_id": str(job.id),
            "output_object_type": output_object_type,
            "output_object_id": str(output_object_id),
        },
    )
    _commit(session)
    session.refresh(call)
    return _tool_view(call)
