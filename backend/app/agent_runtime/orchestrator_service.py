from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlmodel import Session, col, func, select

from app.agent_runtime.providers import build_model
from app.agents.prompts import get_prompt_contract
from app.agents.service import (
    DegradationRecord,
    InvocationCreate,
    ModelExecutionMode,
    ModelUsage,
    complete_model_invocation,
    create_model_invocation,
    fail_model_invocation,
    mark_model_invocation_running,
)
from app.cleaning import service as cleaning_service
from app.core.config import settings
from app.core.db import engine
from app.jobs import service as job_service
from app.jobs.dispatcher import dispatcher as default_dispatcher
from app.models import (
    AgentEvent,
    AgentEventType,
    AgentRun,
    AgentRunStatus,
    ApprovalRecord,
    ApprovalStatus,
    AuditActorType,
    Job,
    JobStatus,
    JobTaskType,
    ModelDataAccessLevel,
    ToolCall,
    ToolCallStatus,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

from . import service as runtime_service
from .schemas import SafeSummary
from .sdk_adapter import (
    PROMPT_ID,
    PROMPT_VERSION,
    REGISTRY_VERSION,
    SDK_VERSION,
    OrchestrationError,
    OrchestrationResult,
    ProviderMode,
    ResearchOrchestratorAdapter,
)
from .snapshot import (
    build_project_context_snapshot,
    canonical_hash,
    snapshot_is_current,
)
from .tool_gateway import DatabaseToolGateway, ToolExecutionContext


@dataclass(frozen=True)
class AgentExecutionResult:
    agent_run_id: uuid.UUID
    model_invocation_id: uuid.UUID | None
    status: AgentRunStatus
    orchestration: OrchestrationResult | None


def queue_agent_run(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    agent_run_id: uuid.UUID,
    dispatcher: job_service.JobDispatcher = default_dispatcher,
) -> Job:
    run = runtime_service.get_agent_run(
        session,
        actor=actor,
        project_id=project_id,
        agent_run_id=agent_run_id,
        for_update=True,
    )
    if run.status != AgentRunStatus.CREATED:
        raise OrchestrationError(
            "AGENT_RUN_INVALID_STATE", "Only a created AgentRun may be queued."
        )
    if run.job_id is not None:
        job = session.get(Job, run.job_id)
        if job is None or job.project_id != project_id:
            raise OrchestrationError(
                "AGENT_JOB_INVALID", "The AgentRun Job reference is invalid."
            )
        return job
    job = job_service.create_job(
        session,
        project_id=project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.AGENT_ORCHESTRATION,
            resource_type="agent_run",
            resource_id=run.id,
            idempotency_key=f"agent-run:{run.id}",
            requested_by_user_id=actor.id,
            max_retries=2,
            retryable=True,
        ),
    )
    run.job_id = job.id
    session.add(run)
    session.commit()
    session.refresh(job)
    return job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)


def _create_followup_agent_job(
    session: Session,
    *,
    run: AgentRun,
    idempotency_key: str,
) -> Job:
    existing = session.exec(
        select(Job).where(
            Job.project_id == run.project_id,
            Job.task_type == JobTaskType.AGENT_ORCHESTRATION,
            Job.resource_type == "agent_run",
            Job.resource_id == run.id,
            Job.idempotency_key == idempotency_key,
        )
    ).first()
    if existing is not None:
        return existing
    job = job_service.create_job(
        session,
        project_id=run.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.AGENT_ORCHESTRATION,
            resource_type="agent_run",
            resource_id=run.id,
            idempotency_key=idempotency_key,
            requested_by_user_id=run.requested_by_user_id,
            max_retries=2,
            retryable=True,
        ),
    )
    run.job_id = job.id
    run.updated_at = get_datetime_utc()
    run.lock_version += 1
    session.add(run)
    project_service._commit(session)
    return job


def approval_resume_post_commit(
    *, approval_id: uuid.UUID, decision: ApprovalStatus
) -> Any:
    def action() -> None:
        with Session(engine) as session:
            calls = session.exec(
                select(ToolCall).where(
                    ToolCall.approval_id == approval_id,
                    ToolCall.status == ToolCallStatus.WAITING_APPROVAL,
                )
            ).all()
            for call in calls:
                run = session.get(AgentRun, call.agent_run_id)
                actor = session.get(User, call.requested_by_user_id)
                approval = session.get(ApprovalRecord, approval_id)
                if (
                    run is None
                    or actor is None
                    or approval is None
                    or run.project_id != call.project_id
                    or approval.project_id != call.project_id
                ):
                    continue
                if decision == ApprovalStatus.REJECTED:
                    runtime_service.transition_tool_call(
                        session,
                        actor=actor,
                        project_id=run.project_id,
                        tool_call_id=call.id,
                        target=ToolCallStatus.DENIED,
                        error_code="APPROVAL_REJECTED",
                    )
                    runtime_service.transition_agent_run(
                        session,
                        actor=actor,
                        project_id=run.project_id,
                        agent_run_id=run.id,
                        target=AgentRunStatus.FAILED,
                        failure_code="APPROVAL_REJECTED",
                    )
                    continue
                if (
                    decision != ApprovalStatus.APPROVED
                    or approval.status != ApprovalStatus.APPROVED
                    or approval.decision_by_user_id is None
                    or approval.payload_hash != call.approval_payload_hash
                    or run.status != AgentRunStatus.WAITING_APPROVAL
                ):
                    continue
                try:
                    _validate_checkpoint(
                        _checkpoint_attributes(session, run=run, call=call),
                        call=call,
                        approval=approval,
                    )
                    runtime_service.append_agent_event(
                        session,
                        actor=actor,
                        project_id=run.project_id,
                        agent_run_id=run.id,
                        event_type=AgentEventType.CONTINUE_INTENT,
                        safe_summary=SafeSummary(
                            kind="external_approval_resume",
                            attributes={
                                "approval_id": str(approval.id),
                                "tool_call_id": str(call.id),
                                "approval_status": approval.status.value,
                            },
                        ),
                        commit=False,
                    )
                    session.refresh(run)
                    job = _create_followup_agent_job(
                        session,
                        run=run,
                        idempotency_key=(
                            f"agent-approval-resume:{run.id}:{approval.id}:"
                            f"{approval.payload_hash}"
                        ),
                    )
                    if job.status in {JobStatus.DRAFT, JobStatus.DISPATCH_FAILED}:
                        job_service.dispatch_job(
                            session, job_id=job.id, dispatcher=default_dispatcher
                        )
                except Exception as exc:
                    session.rollback()
                    latest_run = session.get(AgentRun, run.id)
                    if latest_run is not None and latest_run.status not in {
                        AgentRunStatus.COMPLETED,
                        AgentRunStatus.FAILED,
                        AgentRunStatus.CANCELLED,
                    }:
                        runtime_service.transition_agent_run(
                            session,
                            actor=actor,
                            project_id=run.project_id,
                            agent_run_id=run.id,
                            target=AgentRunStatus.FAILED,
                            failure_code=str(
                                getattr(exc, "code", "AGENT_RESUME_FAILED")
                            )[:100],
                        )

    return action


def notify_agent_tool_job_completed(
    session: Session,
    *,
    job: Job,
    output_object_type: str,
    output_object_id: uuid.UUID,
    dispatcher: job_service.JobDispatcher | None = None,
) -> None:
    call = session.exec(
        select(ToolCall).where(
            ToolCall.project_id == job.project_id,
            ToolCall.job_id == job.id,
            ToolCall.status == ToolCallStatus.RUNNING,
        )
    ).first()
    if call is None:
        return
    run = session.get(AgentRun, call.agent_run_id)
    actor = session.get(User, call.requested_by_user_id)
    if (
        run is None
        or actor is None
        or run.project_id != job.project_id
        or run.status != AgentRunStatus.CALLING_TOOL
    ):
        return
    runtime_service.transition_tool_call(
        session,
        actor=actor,
        project_id=run.project_id,
        tool_call_id=call.id,
        target=ToolCallStatus.COMPLETED,
        safe_output_summary=SafeSummary(
            kind="deterministic_tool_result",
            attributes={
                "status": "COMPLETED",
                "job_id": str(job.id),
                "output_object_type": output_object_type,
                "output_object_id": str(output_object_id),
            },
        ),
        job_id=job.id,
        output_object_type=output_object_type,
        output_object_id=output_object_id,
    )
    runtime_service.append_agent_event(
        session,
        actor=actor,
        project_id=run.project_id,
        agent_run_id=run.id,
        event_type=AgentEventType.RUNTIME_CHECKPOINT,
        safe_summary=SafeSummary(
            kind="deterministic_tool_result",
            attributes={
                "tool_call_id": str(call.id),
                "job_id": str(job.id),
                "output_object_id": str(output_object_id),
            },
        ),
    )
    runtime_service.transition_agent_run(
        session,
        actor=actor,
        project_id=run.project_id,
        agent_run_id=run.id,
        target=AgentRunStatus.REVIEWING,
    )
    session.refresh(run)
    followup = _create_followup_agent_job(
        session,
        run=run,
        idempotency_key=f"agent-tool-summary:{run.id}:{call.id}:{job.id}",
    )
    if followup.status in {JobStatus.DRAFT, JobStatus.DISPATCH_FAILED}:
        job_service.dispatch_job(
            session, job_id=followup.id, dispatcher=dispatcher or default_dispatcher
        )


def notify_agent_tool_job_failed(
    session: Session, *, job: Job, error_code: str
) -> None:
    call = session.exec(
        select(ToolCall).where(
            ToolCall.project_id == job.project_id,
            ToolCall.job_id == job.id,
            ToolCall.status == ToolCallStatus.RUNNING,
        )
    ).first()
    if call is None:
        return
    run = session.get(AgentRun, call.agent_run_id)
    actor = session.get(User, call.requested_by_user_id)
    if run is None or actor is None or run.project_id != job.project_id:
        return
    runtime_service.transition_tool_call(
        session,
        actor=actor,
        project_id=run.project_id,
        tool_call_id=call.id,
        target=ToolCallStatus.FAILED,
        error_code=error_code[:100],
        retryable=job.retryable,
    )
    if run.status not in {
        AgentRunStatus.COMPLETED,
        AgentRunStatus.FAILED,
        AgentRunStatus.CANCELLED,
    }:
        runtime_service.transition_agent_run(
            session,
            actor=actor,
            project_id=run.project_id,
            agent_run_id=run.id,
            target=AgentRunStatus.FAILED,
            failure_code=error_code[:100],
        )


def mark_cancelled_agent_job(session: Session, *, job: Job) -> None:
    agent_run = session.get(AgentRun, job.resource_id)
    if agent_run is None or agent_run.project_id != job.project_id:
        return
    actor = session.get(User, agent_run.requested_by_user_id)
    if actor is None or agent_run.status in {
        AgentRunStatus.COMPLETED,
        AgentRunStatus.FAILED,
        AgentRunStatus.CANCELLED,
    }:
        return
    runtime_service.cancel_agent_run(
        session,
        actor=actor,
        project_id=job.project_id,
        agent_run_id=agent_run.id,
    )


def mark_failed_agent_job(session: Session, *, job: Job, error_code: str) -> None:
    agent_run = session.get(AgentRun, job.resource_id)
    if agent_run is None or agent_run.project_id != job.project_id:
        return
    actor = session.get(User, agent_run.requested_by_user_id)
    if actor is None or agent_run.status in {
        AgentRunStatus.COMPLETED,
        AgentRunStatus.FAILED,
        AgentRunStatus.CANCELLED,
    }:
        return
    runtime_service.transition_agent_run(
        session,
        actor=actor,
        project_id=job.project_id,
        agent_run_id=agent_run.id,
        target=AgentRunStatus.FAILED,
        failure_code=error_code[:100],
    )


def _mode(value: ProviderMode) -> ModelExecutionMode:
    return ModelExecutionMode(value.value)


def _invocation_command(
    *,
    actor: User,
    run: Any,
    provider_mode: ProviderMode,
    provider: str,
    model_name: str,
    expected_output_hash: str | None,
    tool_call_id: uuid.UUID | None = None,
    resume_kind: str | None = None,
) -> InvocationCreate:
    contract = get_prompt_contract("research-orchestrator", "1.0.0")
    kwargs: dict[str, Any] = {}
    if provider_mode == ProviderMode.MOCK:
        kwargs["fixture_id"] = "m8-research-orchestrator-default"
    elif provider_mode == ProviderMode.RECORDED:
        kwargs.update(
            recording_id="m8-research-orchestrator-default",
            recording_version="1.0",
            recording_hash=expected_output_hash,
            recording_license_status="RECA_OWNED",
            recording_redaction_status="REVIEWED",
        )
    return InvocationCreate(
        project_id=run.project_id,
        authorization_actor=actor,
        actor_type=AuditActorType.AGENT,
        actor_id=str(run.id),
        task_type=contract.task_type,
        prompt_id=contract.prompt_id,
        prompt_version=contract.prompt_version,
        prompt_content_hash=contract.content_hash,
        input_schema_name=contract.input_schema.name,
        input_schema_version=contract.input_schema.version,
        output_schema_name=contract.output_schema.name,
        output_schema_version=contract.output_schema.version,
        requested_data_access_level=ModelDataAccessLevel.VERIFIED_EVIDENCE_ONLY,
        max_allowed_data_access_level=ModelDataAccessLevel.VERIFIED_EVIDENCE_ONLY,
        effective_data_access_level=ModelDataAccessLevel.METADATA_ONLY,
        source_ids=(),
        sanitized_input={
            "agent_run_id": str(run.id),
            "snapshot_hash": run.snapshot_hash,
            "safe_input_summary": run.safe_input_summary,
            "resume_kind": resume_kind,
        },
        mode=_mode(provider_mode),
        provider=provider,
        model=model_name,
        request_id=run.request_id,
        agent_run_id=run.id,
        tool_call_id=tool_call_id,
        redaction_policy_version="m8-trace-redaction-1.0",
        execution_metadata={
            "sdk_version": "0.19.1",
            "registry_version": "m8.1",
            "trace_sensitive_data": False,
        },
        **kwargs,
    )


def _latest_waiting_call(session: Session, run: AgentRun) -> ToolCall:
    call = session.exec(
        select(ToolCall)
        .where(
            ToolCall.agent_run_id == run.id,
            ToolCall.project_id == run.project_id,
            ToolCall.status == ToolCallStatus.WAITING_APPROVAL,
        )
        .order_by(col(ToolCall.created_at).desc())
    ).first()
    if call is None:
        raise OrchestrationError(
            "RESUME_CHECKPOINT_INVALID", "No waiting ToolCall is available."
        )
    return call


def _checkpoint_attributes(
    session: Session, *, run: AgentRun, call: ToolCall
) -> dict[str, Any]:
    events = session.exec(
        select(AgentEvent)
        .where(
            AgentEvent.agent_run_id == run.id,
            AgentEvent.project_id == run.project_id,
            AgentEvent.event_type == AgentEventType.RUNTIME_CHECKPOINT,
        )
        .order_by(col(AgentEvent.sequence_number).desc())
    ).all()
    for event in events:
        attributes = dict((event.safe_summary or {}).get("attributes") or {})
        if attributes.get("tool_call_id") == str(call.id):
            return attributes
    raise OrchestrationError(
        "RESUME_CHECKPOINT_INVALID", "The durable resume checkpoint is missing."
    )


def _validate_checkpoint(
    attributes: dict[str, Any],
    *,
    call: ToolCall,
    approval: ApprovalRecord,
) -> None:
    expected = {
        "checkpoint_schema": "1.0",
        "resume_strategy": "DETERMINISTIC_REBUILD",
        "sdk_version": SDK_VERSION,
        "registry_version": REGISTRY_VERSION,
        "prompt_id": PROMPT_ID,
        "prompt_version": PROMPT_VERSION,
        "tool_call_id": str(call.id),
        "tool_name": call.tool_name,
        "tool_version": call.tool_version,
        "tool_input_hash": call.input_hash,
        "approval_id": str(approval.id),
        "approval_payload_hash": approval.payload_hash,
    }
    if any(attributes.get(key) != value for key, value in expected.items()):
        raise OrchestrationError(
            "RESUME_STATE_INCOMPATIBLE",
            "The durable resume checkpoint is stale or incompatible.",
        )
    expires_at = attributes.get("expires_at")
    if expires_at and datetime.fromisoformat(str(expires_at)) <= get_datetime_utc():
        raise OrchestrationError(
            "APPROVAL_EXPIRED", "The durable resume checkpoint has expired."
        )


def _execute_approved_cleaning_tool(
    session: Session,
    *,
    actor: User,
    run: AgentRun,
    dispatcher: job_service.JobDispatcher,
) -> AgentExecutionResult:
    current, _ = snapshot_is_current(
        session,
        actor=actor,
        project_id=run.project_id,
        expected_hash=run.snapshot_hash,
    )
    if not current:
        raise OrchestrationError(
            "STALE_PROJECT_CONTEXT", "The resumed Agent context is stale."
        )
    call = _latest_waiting_call(session, run)
    if call.tool_name != "apply_approved_transformations" or call.approval_id is None:
        raise OrchestrationError(
            "RESUME_CHECKPOINT_INVALID", "The waiting Tool is not resumable."
        )
    approval = session.get(ApprovalRecord, call.approval_id)
    if (
        approval is None
        or approval.project_id != run.project_id
        or approval.status != ApprovalStatus.APPROVED
        or approval.decision_by_user_id is None
        or approval.payload_hash != call.approval_payload_hash
    ):
        raise OrchestrationError(
            "APPROVAL_INVALID", "The external ApprovalRecord is not valid."
        )
    _validate_checkpoint(
        _checkpoint_attributes(session, run=run, call=call),
        call=call,
        approval=approval,
    )
    plan_id_value = (call.safe_input_summary.get("attributes") or {}).get(
        "cleaning_plan_id"
    )
    if plan_id_value is None:
        raise OrchestrationError(
            "RESUME_CHECKPOINT_INVALID", "The CleaningPlan reference is missing."
        )
    plan_id = uuid.UUID(str(plan_id_value))
    runtime_service.transition_tool_call(
        session,
        actor=actor,
        project_id=run.project_id,
        tool_call_id=call.id,
        target=ToolCallStatus.RUNNING,
        approval_id=approval.id,
        approval_payload_hash=approval.payload_hash,
    )
    runtime_service.transition_agent_run(
        session,
        actor=actor,
        project_id=run.project_id,
        agent_run_id=run.id,
        target=AgentRunStatus.CALLING_TOOL,
    )
    try:
        result = cleaning_service.execute_plan(
            session,
            actor=actor,
            plan_id=plan_id,
            idempotency_key=(
                f"agent-cleaning-execute:{approval.id}:{approval.payload_hash}"
            ),
            dispatcher=dispatcher,
        )
        assert result.data is not None
        transformation = result.data["transformation"]
        job = result.data["job"]
        runtime_service.attach_tool_call_job(
            session,
            actor=actor,
            project_id=run.project_id,
            tool_call_id=call.id,
            job_id=uuid.UUID(str(job["id"])),
            output_object_type="data_transformation",
            output_object_id=uuid.UUID(str(transformation["id"])),
        )
    except Exception as exc:
        latest = session.get(ToolCall, call.id)
        if latest is not None and latest.status == ToolCallStatus.RUNNING:
            runtime_service.transition_tool_call(
                session,
                actor=actor,
                project_id=run.project_id,
                tool_call_id=call.id,
                target=ToolCallStatus.FAILED,
                error_code=str(getattr(exc, "code", "TOOL_EXECUTION_FAILED"))[:100],
                retryable=bool(getattr(exc, "retryable", False)),
            )
        raise
    return AgentExecutionResult(
        agent_run_id=run.id,
        model_invocation_id=None,
        status=AgentRunStatus.CALLING_TOOL,
        orchestration=None,
    )


async def _summarize_completed_tool(
    session: Session,
    *,
    actor: User,
    run: AgentRun,
    provider_mode: ProviderMode,
    timeout_seconds: float,
) -> AgentExecutionResult:
    current, snapshot = snapshot_is_current(
        session,
        actor=actor,
        project_id=run.project_id,
        expected_hash=run.snapshot_hash,
    )
    if not current:
        raise OrchestrationError(
            "STALE_PROJECT_CONTEXT", "The Tool result summary context is stale."
        )
    call = session.exec(
        select(ToolCall)
        .where(
            ToolCall.agent_run_id == run.id,
            ToolCall.project_id == run.project_id,
            ToolCall.status == ToolCallStatus.COMPLETED,
        )
        .order_by(col(ToolCall.completed_at).desc())
    ).first()
    if call is None or call.output_object_id is None:
        raise OrchestrationError(
            "TOOL_RESULT_MISSING", "The deterministic Tool result is unavailable."
        )
    source_ids = [str(call.output_object_id), str(run.project_id)]
    final_output = {
        "status": "COMPLETED",
        "stage": snapshot.project_stage.value,
        "summary": "The approved CleaningPlan completed through the deterministic Data Transformation Worker.",
        "source_ids": source_ids,
        "limitations": [
            "This summary reports server-owned Tool, Job and domain output facts."
        ],
    }
    provider = provider_mode.value.lower()
    model_name = "reca-deterministic-orchestrator-1.0"
    if provider_mode == ProviderMode.LIVE:
        provider = "openai-compatible"
        model_name = settings.MODEL_NAME or "unconfigured-live-model"
    invocation = create_model_invocation(
        session,
        command=_invocation_command(
            actor=actor,
            run=run,
            provider_mode=provider_mode,
            provider=provider,
            model_name=model_name,
            expected_output_hash=canonical_hash(final_output),
            tool_call_id=call.id,
            resume_kind="TOOL_RESULT_SUMMARY",
        ),
    )
    mark_model_invocation_running(session, invocation_id=invocation.id)
    try:
        model, _, _ = build_model(
            mode=provider_mode,
            stage=snapshot.project_stage.value,
            source_ids=source_ids,
            resume_summary=final_output,
        )
        adapter = ResearchOrchestratorAdapter(
            gateway=DatabaseToolGateway(
                ToolExecutionContext(
                    project_id=run.project_id,
                    actor_id=actor.id,
                    agent_run_id=run.id,
                    request_id=run.request_id,
                )
            ),
            model=model,
            provider_mode=provider_mode,
        )
        orchestration = await adapter.run(
            user_goal="Summarize the completed registered Tool using server facts only.",
            project_id=run.project_id,
            actor_id=actor.id,
            snapshot_hash=run.snapshot_hash,
            correlation_id=run.correlation_id or str(run.id),
            max_turns=min(run.max_turns, 3),
            timeout_seconds=timeout_seconds,
        )
        if orchestration.output is None or orchestration.waiting_for_approval:
            raise OrchestrationError(
                "MODEL_OUTPUT_INVALID", "The final Tool summary was not completed."
            )
        complete_model_invocation(
            session,
            invocation_id=invocation.id,
            sanitized_output=orchestration.output.model_dump(mode="json"),
            usage=ModelUsage(
                input_tokens=orchestration.input_tokens,
                output_tokens=orchestration.output_tokens,
                request_count=orchestration.usage_requests,
                latency_ms=0,
            ),
        )
        runtime_service.append_agent_event(
            session,
            actor=actor,
            project_id=run.project_id,
            agent_run_id=run.id,
            event_type=AgentEventType.ASSISTANT_SUMMARY,
            safe_summary=SafeSummary(
                kind="assistant_summary",
                text=orchestration.output.summary[:500],
                attributes={
                    "status": "COMPLETED",
                    "tool_call_id": str(call.id),
                    "job_id": str(call.job_id) if call.job_id else None,
                    "output_object_id": str(call.output_object_id),
                },
            ),
        )
        runtime_service.transition_agent_run(
            session,
            actor=actor,
            project_id=run.project_id,
            agent_run_id=run.id,
            target=AgentRunStatus.COMPLETED,
        )
        return AgentExecutionResult(
            agent_run_id=run.id,
            model_invocation_id=invocation.id,
            status=AgentRunStatus.COMPLETED,
            orchestration=orchestration,
        )
    except Exception as exc:
        fail_model_invocation(
            session,
            invocation_id=invocation.id,
            error_code=str(getattr(exc, "code", "AGENT_SUMMARY_FAILED"))[:100],
            degradation=DegradationRecord(
                requested_capability="RESEARCH_ORCHESTRATION",
                primary_provider=provider,
                fallback_provider=None,
                reason_code=str(getattr(exc, "code", "AGENT_SUMMARY_FAILED"))[:100],
                impact="The Tool result remains available in the structured workspace.",
                result_status="FAILED",
                user_visible_message="The Agent summary failed; the deterministic Tool result remains available.",
            ),
        )
        raise


async def execute_agent_run(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    agent_run_id: uuid.UUID,
    provider_mode: ProviderMode,
    timeout_seconds: float = 120,
) -> AgentExecutionResult:
    run = runtime_service.get_agent_run(
        session,
        actor=actor,
        project_id=project_id,
        agent_run_id=agent_run_id,
        for_update=True,
    )
    if run.status == AgentRunStatus.WAITING_APPROVAL:
        return _execute_approved_cleaning_tool(
            session, actor=actor, run=run, dispatcher=default_dispatcher
        )
    if run.status == AgentRunStatus.REVIEWING:
        return await _summarize_completed_tool(
            session,
            actor=actor,
            run=run,
            provider_mode=provider_mode,
            timeout_seconds=timeout_seconds,
        )
    if run.status != AgentRunStatus.CREATED:
        raise OrchestrationError(
            "AGENT_RUN_INVALID_STATE", "Only a newly created AgentRun may be executed."
        )
    current, snapshot = snapshot_is_current(
        session,
        actor=actor,
        project_id=project_id,
        expected_hash=run.snapshot_hash,
    )
    if not current:
        raise OrchestrationError(
            "STALE_PROJECT_CONTEXT", "AgentRun context is stale; start a new run."
        )
    event_count = session.exec(
        select(func.count())
        .select_from(AgentEvent)
        .where(AgentEvent.agent_run_id == run.id)
    ).one()
    if event_count == 0:
        runtime_service.append_agent_event(
            session,
            actor=actor,
            project_id=project_id,
            agent_run_id=run.id,
            event_type=AgentEventType.USER_MESSAGE,
            safe_summary=SafeSummary.model_validate(run.safe_input_summary),
        )
    runtime_service.transition_agent_run(
        session,
        actor=actor,
        project_id=project_id,
        agent_run_id=run.id,
        target=AgentRunStatus.PLANNING,
    )
    source_ids = [
        value
        for values in snapshot.available_resources.values()
        for value in values[:1]
    ][:10] or [str(project_id)]
    if provider_mode in {ProviderMode.MOCK, ProviderMode.RECORDED}:
        provider = provider_mode.value.lower()
        model_name = "reca-deterministic-orchestrator-1.0"
    else:
        provider = "openai-compatible"
        model_name = settings.MODEL_NAME or "unconfigured-live-model"
    expected_output = {
        "status": "COMPLETED",
        "stage": snapshot.project_stage.value,
        "summary": "The authorized project state was reviewed.",
        "source_ids": source_ids,
        "limitations": [
            "Deterministic offline orchestration; no live provider was used."
        ],
    }
    command = _invocation_command(
        actor=actor,
        run=run,
        provider_mode=provider_mode,
        provider=provider,
        model_name=model_name,
        expected_output_hash=canonical_hash(expected_output),
    )
    invocation = create_model_invocation(session, command=command)
    mark_model_invocation_running(session, invocation_id=invocation.id)
    try:
        model, _, _ = build_model(
            mode=provider_mode,
            stage=snapshot.project_stage.value,
            source_ids=source_ids,
            workflow_goal=str(run.safe_input_summary.get("text") or ""),
        )
        gateway = DatabaseToolGateway(
            ToolExecutionContext(
                project_id=project_id,
                actor_id=actor.id,
                agent_run_id=run.id,
                request_id=run.request_id,
            )
        )
        adapter = ResearchOrchestratorAdapter(
            gateway=gateway, model=model, provider_mode=provider_mode
        )
        orchestration = await adapter.run(
            user_goal=str(
                run.safe_input_summary.get("text") or "Review project state."
            ),
            project_id=project_id,
            actor_id=actor.id,
            snapshot_hash=run.snapshot_hash,
            correlation_id=run.correlation_id or str(run.id),
            max_turns=run.max_turns,
            timeout_seconds=timeout_seconds,
        )
        if orchestration.waiting_for_approval:
            waiting_call = session.exec(
                select(ToolCall)
                .where(
                    ToolCall.agent_run_id == run.id,
                    ToolCall.project_id == project_id,
                    ToolCall.status == ToolCallStatus.WAITING_APPROVAL,
                )
                .order_by(col(ToolCall.created_at).desc())
            ).first()
            if waiting_call is None or waiting_call.approval_id is None:
                raise OrchestrationError(
                    "RESUME_CHECKPOINT_INVALID",
                    "The waiting ToolCall has no bound external Approval.",
                )
            approval = session.get(ApprovalRecord, waiting_call.approval_id)
            if approval is None or approval.project_id != project_id:
                raise OrchestrationError(
                    "APPROVAL_INVALID", "The bound Approval is unavailable."
                )
            fresh_snapshot = build_project_context_snapshot(
                session, actor=actor, project_id=project_id
            )
            if orchestration.output is not None:
                complete_model_invocation(
                    session,
                    invocation_id=invocation.id,
                    sanitized_output=orchestration.output.model_dump(mode="json"),
                    usage=ModelUsage(
                        input_tokens=orchestration.input_tokens,
                        output_tokens=orchestration.output_tokens,
                        request_count=orchestration.usage_requests,
                        latency_ms=0,
                    ),
                )
            runtime_service.append_agent_event(
                session,
                actor=actor,
                project_id=project_id,
                agent_run_id=run.id,
                event_type=AgentEventType.RUNTIME_CHECKPOINT,
                safe_summary=SafeSummary(
                    kind="waiting_approval",
                    attributes={
                        "checkpoint_schema": "1.0",
                        "resume_strategy": "DETERMINISTIC_REBUILD",
                        "sdk_version": SDK_VERSION,
                        "registry_version": REGISTRY_VERSION,
                        "prompt_id": PROMPT_ID,
                        "prompt_version": PROMPT_VERSION,
                        "snapshot_hash": fresh_snapshot.canonical_hash,
                        "tool_call_id": str(waiting_call.id),
                        "tool_name": waiting_call.tool_name,
                        "tool_version": waiting_call.tool_version,
                        "tool_input_hash": waiting_call.input_hash,
                        "approval_id": str(approval.id),
                        "approval_payload_hash": approval.payload_hash,
                        "expires_at": approval.expires_at.isoformat()
                        if approval.expires_at
                        else None,
                    },
                ),
            )
            waiting_run = session.get(AgentRun, run.id)
            if (
                waiting_run is None
                or waiting_run.project_id != project_id
                or waiting_run.status != AgentRunStatus.WAITING_APPROVAL
            ):
                raise OrchestrationError(
                    "AGENT_RUN_INVALID_STATE",
                    "The AgentRun did not enter the required approval wait state.",
                )
            return AgentExecutionResult(
                agent_run_id=run.id,
                model_invocation_id=invocation.id,
                status=AgentRunStatus.WAITING_APPROVAL,
                orchestration=orchestration,
            )
        assert orchestration.output is not None
        complete_model_invocation(
            session,
            invocation_id=invocation.id,
            sanitized_output=orchestration.output.model_dump(mode="json"),
            usage=ModelUsage(
                input_tokens=orchestration.input_tokens,
                output_tokens=orchestration.output_tokens,
                request_count=orchestration.usage_requests,
                latency_ms=0,
            ),
        )
        runtime_service.append_agent_event(
            session,
            actor=actor,
            project_id=project_id,
            agent_run_id=run.id,
            event_type=AgentEventType.ASSISTANT_SUMMARY,
            safe_summary=SafeSummary(
                kind="assistant_summary",
                text=orchestration.output.summary[:500],
                attributes={
                    "status": orchestration.output.status,
                    "stage": orchestration.output.stage,
                    "source_count": len(orchestration.output.source_ids),
                },
            ),
        )
        runtime_service.transition_agent_run(
            session,
            actor=actor,
            project_id=project_id,
            agent_run_id=run.id,
            target=AgentRunStatus.REVIEWING,
        )
        runtime_service.transition_agent_run(
            session,
            actor=actor,
            project_id=project_id,
            agent_run_id=run.id,
            target=AgentRunStatus.COMPLETED,
        )
        return AgentExecutionResult(
            agent_run_id=run.id,
            model_invocation_id=invocation.id,
            status=AgentRunStatus.COMPLETED,
            orchestration=orchestration,
        )
    except Exception as exc:
        error_code = str(getattr(exc, "code", "AGENT_EXECUTION_FAILED"))[:100]
        try:
            fail_model_invocation(
                session,
                invocation_id=invocation.id,
                error_code=error_code,
                degradation=DegradationRecord(
                    requested_capability="RESEARCH_ORCHESTRATION",
                    primary_provider=provider,
                    fallback_provider=None,
                    reason_code=error_code,
                    impact="The Agent explanation is unavailable; direct structured workspaces remain available.",
                    result_status="FAILED",
                    user_visible_message="The Agent run failed safely. Use the project workspaces directly.",
                ),
            )
        except Exception:
            session.rollback()
        try:
            latest = runtime_service.get_agent_run(
                session,
                actor=actor,
                project_id=project_id,
                agent_run_id=run.id,
            )
            if latest.status not in {
                AgentRunStatus.COMPLETED,
                AgentRunStatus.FAILED,
                AgentRunStatus.CANCELLED,
            }:
                runtime_service.transition_agent_run(
                    session,
                    actor=actor,
                    project_id=project_id,
                    agent_run_id=run.id,
                    target=AgentRunStatus.FAILED,
                    failure_code=error_code,
                )
        except Exception:
            session.rollback()
        raise
