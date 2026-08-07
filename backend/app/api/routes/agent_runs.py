from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlmodel import col, func, select

from app.agent_runtime import service as runtime_service
from app.agent_runtime.orchestrator_service import queue_agent_run
from app.agent_runtime.registry import get_tool
from app.agent_runtime.schemas import AgentRunCreate, SafeSummary
from app.agent_runtime.snapshot import snapshot_is_current
from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError, ContractErrorResponse
from app.api.m8_responses import (
    AgentMessageRequest,
    AgentRunCreateRequest,
    AgentRunEnvelope,
    ToolCallEnvelope,
    ToolCallListEnvelope,
)
from app.core.observability import current_request_id
from app.jobs import service as job_service
from app.jobs.dispatcher import dispatcher
from app.models import (
    AgentEvent,
    AgentEventType,
    AgentRun,
    AgentRunStatus,
    ApprovalRecord,
    Job,
    JobStatus,
    ModelInvocation,
    ToolCall,
    ToolCallStatus,
)
from app.projects import service as project_service

router = APIRouter(tags=["agent-runs"])
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ContractErrorResponse},
    403: {"model": ContractErrorResponse},
    404: {"model": ContractErrorResponse},
    409: {"model": ContractErrorResponse},
    422: {"model": ContractErrorResponse},
}
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


def _meta(*, replayed: bool = False) -> dict[str, Any]:
    return {
        "request_id": current_request_id(),
        "schema_version": "1.0",
        "idempotency_replayed": replayed,
    }


def _required_key(value: str | None) -> str:
    if value is None or not value.strip():
        raise ContractError(
            status_code=400,
            code="MISSING_IDEMPOTENCY_KEY",
            message="Idempotency-Key is required for this operation.",
        )
    if len(value) > 255:
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Idempotency-Key exceeds the maximum length.",
        )
    return value


def _safe_summary(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return SafeSummary.model_validate(value).model_dump(mode="json")


def _job_link(job: Job | None) -> dict[str, Any] | None:
    if job is None:
        return None
    return {
        "id": job.id,
        "status": job.status.value,
        "known_status": True,
        "progress_percent": job.progress_percent,
        "retryable": job.retryable,
        "error_code": job.error_code,
    }


def _approval_link(approval: ApprovalRecord | None) -> dict[str, Any] | None:
    if approval is None:
        return None
    stale = approval.expires_at is not None and approval.expires_at <= datetime.now(UTC)
    return {
        "id": approval.id,
        "status": approval.status.value,
        "known_status": True,
        "stale": stale,
        "expires_at": approval.expires_at,
    }


def _tool_projection(session: SessionDep, call: ToolCall) -> dict[str, Any]:
    definition = get_tool(call.tool_name, call.tool_version)
    if definition is None:
        raise ContractError(
            status_code=409,
            code="TOOL_REGISTRY_MISMATCH",
            message="The Tool contract is no longer available.",
        )
    approval = (
        session.get(ApprovalRecord, call.approval_id) if call.approval_id else None
    )
    job = session.get(Job, call.job_id) if call.job_id else None
    if approval is not None and approval.project_id != call.project_id:
        approval = None
    if job is not None and job.project_id != call.project_id:
        job = None
    actions = [] if call.status in TOOL_TERMINAL else ["tool_call.read"]
    return {
        "id": call.id,
        "project_id": call.project_id,
        "agent_run_id": call.agent_run_id,
        "tool_name": call.tool_name,
        "tool_version": call.tool_version,
        "status": call.status.value,
        "known_status": True,
        "category": definition.category.value,
        "confirmation": definition.confirmation.value,
        "safe_input_summary": _safe_summary(call.safe_input_summary),
        "safe_output_summary": _safe_summary(call.safe_output_summary),
        "approval": _approval_link(approval),
        "job": _job_link(job),
        "output_object_type": call.output_object_type,
        "output_object_id": call.output_object_id,
        "retry_of_tool_call_id": call.retry_of_tool_call_id,
        "error_code": call.error_code,
        "retryable": call.retryable,
        "allowed_actions": actions,
        "disabled_reason_code": definition.disabled_reason_code,
        "created_at": call.created_at,
        "started_at": call.started_at,
        "completed_at": call.completed_at,
    }


def _run_projection(
    session: SessionDep, actor: CurrentUser, run: AgentRun
) -> dict[str, Any]:
    current, _ = snapshot_is_current(
        session, actor=actor, project_id=run.project_id, expected_hash=run.snapshot_hash
    )
    events = session.exec(
        select(AgentEvent)
        .where(
            AgentEvent.agent_run_id == run.id, AgentEvent.project_id == run.project_id
        )
        .order_by(col(AgentEvent.sequence_number))
    ).all()
    invocations = session.exec(
        select(ModelInvocation)
        .where(
            ModelInvocation.agent_run_id == run.id,
            ModelInvocation.project_id == run.project_id,
        )
        .order_by(col(ModelInvocation.created_at))
    ).all()
    job = session.get(Job, run.job_id) if run.job_id else None
    if job is not None and job.project_id != run.project_id:
        job = None
    actions = (
        [] if run.status in RUN_TERMINAL else ["agent_run.read", "agent_run.cancel"]
    )
    disabled: dict[str, str] = {}
    if not current:
        actions = [action for action in actions if action == "agent_run.read"]
        disabled["agent_run.cancel"] = "STALE_PROJECT_CONTEXT"
    pending_continue = bool(
        events and events[-1].event_type == AgentEventType.USER_MESSAGE
    )
    if run.status == AgentRunStatus.WAITING_USER_INPUT and current:
        if pending_continue:
            disabled["agent_run.continue"] = "AGENT_RESUME_PENDING"
        else:
            actions.append("agent_run.continue")
    if run.status == AgentRunStatus.WAITING_APPROVAL:
        disabled["agent_run.continue"] = "EXTERNAL_APPROVAL_REQUIRED"
    degradation_code = None
    if run.degradation:
        degradation_code = str(run.degradation.get("code") or "PROVIDER_DEGRADED")
    return {
        "id": run.id,
        "project_id": run.project_id,
        "agent_type": run.agent_type,
        "status": run.status.value,
        "known_status": True,
        "lock_version": run.lock_version,
        "safe_input_summary": _safe_summary(run.safe_input_summary),
        "safe_snapshot_summary": run.safe_snapshot_summary,
        "snapshot_hash": run.snapshot_hash,
        "snapshot_revision": run.snapshot_revision,
        "snapshot_current": current,
        "source_object_versions": run.source_object_versions,
        "max_turns": run.max_turns,
        "max_tool_calls": run.max_tool_calls,
        "turn_count": run.turn_count,
        "tool_call_count": run.tool_call_count,
        "retry_of_agent_run_id": run.retry_of_agent_run_id,
        "failure_code": run.failure_code,
        "degradation_code": degradation_code,
        "retryable": run.status == AgentRunStatus.FAILED,
        "allowed_actions": sorted(actions),
        "disabled_reasons": disabled,
        "job": _job_link(job),
        "events": [
            {
                "id": event.id,
                "sequence_number": event.sequence_number,
                "event_type": event.event_type.value,
                "actor_type": event.actor_type.value,
                "safe_summary": _safe_summary(event.safe_summary),
                "created_at": event.created_at,
            }
            for event in events
        ],
        "model_invocations": [
            {
                "id": item.id,
                "tool_call_id": item.tool_call_id,
                "status": item.status.value,
                "known_status": True,
                "input_tokens": item.input_tokens,
                "output_tokens": item.output_tokens,
                "total_tokens": item.total_tokens,
                "request_count": item.request_count,
                "latency_ms": item.latency_ms,
                "error_code": item.error_code,
                "degraded": item.degradation is not None,
            }
            for item in invocations
        ],
        "created_at": run.created_at,
        "updated_at": run.updated_at,
        "completed_at": run.completed_at,
    }


def _visible_run(
    session: SessionDep, actor: CurrentUser, run_id: uuid.UUID
) -> AgentRun:
    run = session.get(AgentRun, run_id)
    if run is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    return runtime_service.get_agent_run(
        session,
        actor=actor,
        project_id=run.project_id,
        agent_run_id=run.id,
    )


def _visible_tool(
    session: SessionDep, actor: CurrentUser, call_id: uuid.UUID
) -> ToolCall:
    call = session.get(ToolCall, call_id)
    if call is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    run = runtime_service.get_agent_run(
        session,
        actor=actor,
        project_id=call.project_id,
        agent_run_id=call.agent_run_id,
    )
    if run.project_id != call.project_id:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    return call


@router.post(
    "/projects/{project_id}/agent-runs",
    response_model=AgentRunEnvelope,
    response_model_exclude_none=True,
    status_code=202,
    responses=ERROR_RESPONSES,
)
def create_agent_run(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    body: AgentRunCreateRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", max_length=255)],
    correlation_id: Annotated[str | None, Header(alias="X-Correlation-ID")] = None,
) -> JSONResponse:
    key = _required_key(idempotency_key)
    view = runtime_service.create_agent_run(
        session,
        actor=current_user,
        command=AgentRunCreate(
            project_id=project_id,
            safe_input_summary=SafeSummary(
                kind="USER_GOAL",
                text=body.goal,
                attributes={
                    "provider_mode": "MOCK",
                    "allow_tool_calls": body.allow_tool_calls,
                },
            ),
            idempotency_key=key,
            request_id=current_request_id(),
            correlation_id=correlation_id,
            max_tool_calls=24 if body.allow_tool_calls else 0,
        ),
    )
    run = runtime_service.get_agent_run(
        session, actor=current_user, project_id=project_id, agent_run_id=view.id
    )
    if run.job_id is None:
        queue_agent_run(
            session,
            actor=current_user,
            project_id=project_id,
            agent_run_id=run.id,
            dispatcher=dispatcher,
        )
        session.refresh(run)
    return JSONResponse(
        status_code=202,
        content=jsonable_encoder(
            {
                "data": _run_projection(session, current_user, run),
                "meta": _meta(replayed=view.idempotency_replayed),
            }
        ),
    )


@router.get(
    "/agent-runs/{agent_run_id}",
    response_model=AgentRunEnvelope,
    response_model_exclude_none=True,
    responses=ERROR_RESPONSES,
)
def get_agent_run(
    *, session: SessionDep, current_user: CurrentUser, agent_run_id: uuid.UUID
) -> dict[str, Any]:
    run = _visible_run(session, current_user, agent_run_id)
    return {"data": _run_projection(session, current_user, run), "meta": _meta()}


@router.post(
    "/agent-runs/{agent_run_id}/messages",
    response_model=AgentRunEnvelope,
    response_model_exclude_none=True,
    status_code=202,
    responses=ERROR_RESPONSES,
)
def append_message(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_run_id: uuid.UUID,
    body: AgentMessageRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", max_length=255)],
) -> JSONResponse:
    key = _required_key(idempotency_key)
    run = _visible_run(session, current_user, agent_run_id)
    payload_hash = project_service.request_hash(body.model_dump(mode="json"))
    replay = project_service._replay_or_conflict(
        session,
        actor_id=current_user.id,
        project_id=run.project_id,
        method="POST",
        path_template="/api/v1/agent-runs/{agent_run_id}/messages",
        key=key,
        payload_hash=payload_hash,
    )
    if replay:
        return JSONResponse(
            status_code=replay.status_code,
            content={"data": replay.data, "meta": _meta(replayed=True)},
        )
    if run.status != AgentRunStatus.WAITING_USER_INPUT:
        raise ContractError(
            status_code=409,
            code="AGENT_RUN_NOT_WAITING_FOR_INPUT",
            message="The AgentRun is not waiting for user input.",
        )
    runtime_service.append_agent_event(
        session,
        actor=current_user,
        project_id=run.project_id,
        agent_run_id=run.id,
        event_type=AgentEventType.USER_MESSAGE,
        safe_summary=SafeSummary(kind="USER_MESSAGE", text=body.message),
        commit=False,
    )
    session.refresh(run)
    data = jsonable_encoder(_run_projection(session, current_user, run))
    result = project_service.OperationResult(data=data, status_code=202)
    project_service._store_idempotency(
        session,
        actor_id=current_user.id,
        project_id=run.project_id,
        method="POST",
        path_template="/api/v1/agent-runs/{agent_run_id}/messages",
        key=key,
        payload_hash=payload_hash,
        result=result,
    )
    project_service._commit(session)
    return JSONResponse(status_code=202, content={"data": data, "meta": _meta()})


@router.get(
    "/agent-runs/{agent_run_id}/tool-calls",
    response_model=ToolCallListEnvelope,
    response_model_exclude_none=True,
    responses=ERROR_RESPONSES,
)
def list_tool_calls(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_run_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    run = _visible_run(session, current_user, agent_run_id)
    base = (ToolCall.agent_run_id == run.id) & (ToolCall.project_id == run.project_id)
    total = session.exec(select(func.count()).select_from(ToolCall).where(base)).one()
    calls = session.exec(
        select(ToolCall)
        .where(base)
        .order_by(col(ToolCall.created_at).asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    total_pages = math.ceil(total / page_size) if total else 0
    return {
        "data": [_tool_projection(session, call) for call in calls],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        },
        "meta": _meta(),
    }


@router.get(
    "/tool-calls/{tool_call_id}",
    response_model=ToolCallEnvelope,
    response_model_exclude_none=True,
    responses=ERROR_RESPONSES,
)
def get_tool_call(
    *, session: SessionDep, current_user: CurrentUser, tool_call_id: uuid.UUID
) -> dict[str, Any]:
    call = _visible_tool(session, current_user, tool_call_id)
    return {"data": _tool_projection(session, call), "meta": _meta()}


@router.post(
    "/agent-runs/{agent_run_id}/cancel",
    response_model=AgentRunEnvelope,
    response_model_exclude_none=True,
    status_code=202,
    responses=ERROR_RESPONSES,
)
def cancel_agent_run(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_run_id: uuid.UUID,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", max_length=255)],
) -> JSONResponse:
    key = _required_key(idempotency_key)
    run = _visible_run(session, current_user, agent_run_id)
    payload_hash = project_service.request_hash({})
    replay = project_service._replay_or_conflict(
        session,
        actor_id=current_user.id,
        project_id=run.project_id,
        method="POST",
        path_template="/api/v1/agent-runs/{agent_run_id}/cancel",
        key=key,
        payload_hash=payload_hash,
    )
    if replay:
        return JSONResponse(
            status_code=replay.status_code,
            content={"data": replay.data, "meta": _meta(replayed=True)},
        )
    if run.status in RUN_TERMINAL:
        raise ContractError(
            status_code=409,
            code="AGENT_RUN_NOT_CANCELLABLE",
            message="The AgentRun cannot be cancelled in its current state.",
        )
    if run.job_id:
        job = session.get(Job, run.job_id)
        if job is not None and job.status in {JobStatus.QUEUED, JobStatus.RUNNING}:
            job_service.cancel_job(
                session,
                actor=current_user,
                job_id=job.id,
                reason="AgentRun cancellation requested.",
                idempotency_key=key,
            )
    runtime_service.cancel_agent_run(
        session,
        actor=current_user,
        project_id=run.project_id,
        agent_run_id=run.id,
        commit=False,
    )
    session.refresh(run)
    data = jsonable_encoder(_run_projection(session, current_user, run))
    result = project_service.OperationResult(data=data, status_code=202)
    project_service._store_idempotency(
        session,
        actor_id=current_user.id,
        project_id=run.project_id,
        method="POST",
        path_template="/api/v1/agent-runs/{agent_run_id}/cancel",
        key=key,
        payload_hash=payload_hash,
        result=result,
    )
    project_service._commit(session)
    return JSONResponse(status_code=202, content={"data": data, "meta": _meta()})
