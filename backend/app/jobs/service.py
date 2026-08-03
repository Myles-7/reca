from __future__ import annotations

import hashlib
import json
import math
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc, func
from sqlmodel import Session, col, select

from app.api.errors import ContractError
from app.core.observability import current_request_id
from app.jobs.events import EventStoreError, JobEventStore, event_store
from app.models import (
    AuditActorType,
    AuditLog,
    AuditOutcome,
    Job,
    JobStatus,
    JobTaskType,
    ProcessingRun,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

SCHEMA_VERSION = "1.0"


def _encoded_dict(value: Any) -> dict[str, Any]:
    return cast(dict[str, Any], jsonable_encoder(value))


TERMINAL_STATUSES = frozenset(
    {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
)


class JobDispatcher(Protocol):
    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None: ...


@dataclass(frozen=True)
class JobCreate:
    task_type: JobTaskType
    resource_type: str
    resource_id: uuid.UUID
    idempotency_key: str
    requested_by_user_id: uuid.UUID | None
    max_retries: int = 3
    retryable: bool = True


@dataclass(frozen=True)
class RunClaim:
    run_id: uuid.UUID
    job_id: uuid.UUID
    attempt_number: int


def _canonical_hash(value: Any) -> str:
    encoded = jsonable_encoder(value)
    canonical = json.dumps(
        encoded, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _latest_run(session: Session, job_id: uuid.UUID) -> ProcessingRun | None:
    return session.exec(
        select(ProcessingRun)
        .where(ProcessingRun.job_id == job_id)
        .order_by(desc(col(ProcessingRun.attempt_number)))
    ).first()


def job_data(session: Session, job: Job) -> dict[str, Any]:
    run = _latest_run(session, job.id)
    error = None
    if job.error_code is not None:
        error = {
            "code": job.error_code,
            "message": job.error_message or "Job failed.",
            "retryable": job.retryable,
        }
    result = None
    if run is not None and run.output_object_type and run.output_object_id:
        result = {
            "object_type": run.output_object_type,
            "object_id": run.output_object_id,
            "url": None,
        }
    return _encoded_dict(
        {
            "id": job.id,
            "project_id": job.project_id,
            "task_type": job.task_type,
            "resource_type": job.resource_type,
            "resource_id": job.resource_id,
            "status": job.status,
            "progress_percent": job.progress_percent,
            "current_step": job.current_step,
            "total_steps": job.total_steps,
            "completed_steps": job.completed_steps,
            "retry_count": job.retry_count,
            "max_retries": job.max_retries,
            "retryable": job.retryable,
            "current_processing_run_id": run.id
            if run and run.status == JobStatus.RUNNING
            else None,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "error": error,
            "result": result,
        }
    )


def _audit(
    session: Session,
    *,
    job: Job,
    action: str,
    actor_type: AuditActorType,
    actor_id: str | None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
    outcome: AuditOutcome = AuditOutcome.SUCCEEDED,
    request_id: str | None = None,
) -> None:
    session.add(
        AuditLog(
            project_id=job.project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            object_type="job",
            object_id=job.id,
            before_snapshot=jsonable_encoder(before) if before is not None else None,
            after_snapshot=jsonable_encoder(after) if after is not None else None,
            reason=reason,
            request_id=request_id if request_id is not None else current_request_id(),
            job_id=job.id,
            outcome=outcome,
        )
    )


def _event_payload(
    job: Job,
    *,
    event_type: str,
    message: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _encoded_dict(
        {
            "schema_version": SCHEMA_VERSION,
            "event_type": event_type,
            "job_id": job.id,
            "project_id": job.project_id,
            "status": job.status,
            "progress_percent": job.progress_percent,
            "current_step": job.current_step,
            "message": message,
            "payload": payload or {},
            "occurred_at": get_datetime_utc(),
        }
    )


def _publish(
    job: Job,
    *,
    event_type: str,
    message: str,
    payload: dict[str, Any] | None = None,
    store: JobEventStore | None = None,
) -> None:
    try:
        (store or event_store).publish(
            job_id=job.id,
            event=_event_payload(
                job, event_type=event_type, message=message, payload=payload
            ),
        )
    except EventStoreError:
        # Valkey is an event hint only; the committed PostgreSQL state remains valid.
        return


def create_job(
    session: Session,
    *,
    project_id: uuid.UUID,
    command: JobCreate,
) -> Job:
    job = Job(
        project_id=project_id,
        task_type=command.task_type,
        resource_type=command.resource_type,
        resource_id=command.resource_id,
        idempotency_key=command.idempotency_key,
        requested_by_user_id=command.requested_by_user_id,
        max_retries=command.max_retries,
        retryable=command.retryable,
    )
    session.add(job)
    session.flush()
    _audit(
        session,
        job=job,
        action="JOB_CREATED",
        actor_type=AuditActorType.USER,
        actor_id=str(command.requested_by_user_id)
        if command.requested_by_user_id
        else None,
        after={"status": job.status, "task_type": job.task_type},
    )
    return job


def dispatch_job(
    session: Session,
    *,
    job_id: uuid.UUID,
    dispatcher: JobDispatcher,
    store: JobEventStore | None = None,
) -> Job:
    job = session.exec(
        select(Job)
        .where(Job.id == job_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).first()
    if job is None:
        raise ContractError(
            status_code=404, code="JOB_NOT_FOUND", message="Job not found."
        )
    if job.status not in {JobStatus.DRAFT, JobStatus.QUEUED, JobStatus.DISPATCH_FAILED}:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Job cannot be dispatched in its current state.",
        )
    before = {"status": job.status, "celery_task_id": job.celery_task_id}
    task_id = str(uuid.uuid4())
    job.status = JobStatus.QUEUED
    job.queued_at = get_datetime_utc()
    job.celery_task_id = task_id
    job.error_code = None
    job.error_message = None
    session.add(job)
    _audit(
        session,
        job=job,
        action="JOB_QUEUED",
        actor_type=AuditActorType.SYSTEM,
        actor_id="job-dispatcher",
        before=before,
        after={"status": job.status, "celery_task_id": task_id},
    )
    project_service._commit(session)
    try:
        dispatcher.dispatch(job_id=job.id, task_id=task_id)
    except Exception:
        job = session.exec(select(Job).where(Job.id == job_id).with_for_update()).one()
        job.status = JobStatus.DISPATCH_FAILED
        job.error_code = "JOB_DISPATCH_FAILED"
        job.error_message = "The execution mechanism could not accept the Job."
        session.add(job)
        _audit(
            session,
            job=job,
            action="JOB_DISPATCH_FAILED",
            actor_type=AuditActorType.SYSTEM,
            actor_id="job-dispatcher",
            after={"status": job.status, "error_code": job.error_code},
            outcome=AuditOutcome.FAILED,
        )
        project_service._commit(session)
        _publish(
            job,
            event_type="job.failed",
            message="Job dispatch failed.",
            payload={"error_code": "JOB_DISPATCH_FAILED"},
            store=store,
        )
        return job
    _publish(job, event_type="job.queued", message="Job queued.", store=store)
    return job


def _visible_job(
    session: Session,
    *,
    actor: User,
    job_id: uuid.UUID,
    action: str,
    for_update: bool = False,
) -> Job:
    job = session.exec(
        select(Job).where(Job.id == job_id).execution_options(populate_existing=True)
    ).first()
    if job is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    project_service.authorize_project(
        session,
        project_id=job.project_id,
        actor=actor,
        action=action,
        for_update=for_update,
    )
    if not for_update:
        return job
    locked = session.exec(select(Job).where(Job.id == job_id).with_for_update()).first()
    if locked is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    return locked


def get_job(session: Session, *, actor: User, job_id: uuid.UUID) -> dict[str, Any]:
    return job_data(
        session, _visible_job(session, actor=actor, job_id=job_id, action="job.read")
    )


def list_jobs(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    status: JobStatus | None,
    task_type: JobTaskType | None,
    resource_type: str | None,
    resource_id: uuid.UUID | None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="job.read"
    )
    filters: list[Any] = [Job.project_id == project_id]
    if status is not None:
        filters.append(Job.status == status)
    if task_type is not None:
        filters.append(Job.task_type == task_type)
    if resource_type is not None:
        filters.append(Job.resource_type == resource_type)
    if resource_id is not None:
        filters.append(Job.resource_id == resource_id)
    total = session.exec(select(func.count()).select_from(Job).where(*filters)).one()
    jobs = session.exec(
        select(Job)
        .where(*filters)
        .order_by(desc(col(Job.created_at)), desc(col(Job.id)))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    total_pages = math.ceil(total / page_size) if total else 0
    return [job_data(session, job) for job in jobs], {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


def cancel_job(
    session: Session,
    *,
    actor: User,
    job_id: uuid.UUID,
    reason: str,
    idempotency_key: str,
    store: JobEventStore | None = None,
) -> project_service.OperationResult:
    job = _visible_job(
        session, actor=actor, job_id=job_id, action="job.cancel", for_update=True
    )
    digest = project_service.request_hash({"reason": reason})
    path = "/api/v1/jobs/{job_id}/cancel"
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=job.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay:
        return replay
    if job.status not in {JobStatus.QUEUED, JobStatus.RUNNING}:
        raise ContractError(
            status_code=409,
            code="JOB_NOT_CANCELLABLE",
            message="Job cannot be cancelled in its current state.",
        )
    before = {"status": job.status}
    job.status = JobStatus.CANCEL_REQUESTED
    session.add(job)
    _audit(
        session,
        job=job,
        action="JOB_CANCEL_REQUESTED",
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        before=before,
        after={"status": job.status},
        reason=reason,
    )
    result = project_service.OperationResult(
        data=job_data(session, job), status_code=200
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=job.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    _publish(
        job,
        event_type="job.cancel_requested",
        message="Job cancellation requested.",
        store=store,
    )
    return result


def retry_job(
    session: Session,
    *,
    actor: User,
    job_id: uuid.UUID,
    idempotency_key: str,
    dispatcher: JobDispatcher,
    store: JobEventStore | None = None,
) -> project_service.OperationResult:
    job = _visible_job(
        session, actor=actor, job_id=job_id, action="job.retry", for_update=True
    )
    digest = project_service.request_hash({})
    path = "/api/v1/jobs/{job_id}/retry"
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=job.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay:
        return replay
    if (
        job.status not in {JobStatus.FAILED, JobStatus.DISPATCH_FAILED}
        or not job.retryable
    ):
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Job cannot be retried in its current state.",
        )
    if job.retry_count >= job.max_retries:
        raise ContractError(
            status_code=409,
            code="JOB_RETRY_EXHAUSTED",
            message="Job retry limit has been exhausted.",
        )
    before = {"status": job.status, "retry_count": job.retry_count}
    job.retry_count += 1
    job.status = JobStatus.QUEUED
    job.queued_at = get_datetime_utc()
    job.started_at = None
    job.completed_at = None
    job.last_heartbeat_at = None
    job.progress_percent = 0
    job.current_step = None
    job.completed_steps = 0 if job.total_steps is not None else None
    job.celery_task_id = None
    job.error_code = None
    job.error_message = None
    session.add(job)
    _audit(
        session,
        job=job,
        action="JOB_RETRIED",
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        before=before,
        after={"status": job.status, "retry_count": job.retry_count},
    )
    initial = project_service.OperationResult(
        data=job_data(session, job), status_code=200
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=job.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
        result=initial,
    )
    project_service._commit(session)
    dispatched = dispatch_job(
        session, job_id=job.id, dispatcher=dispatcher, store=store
    )
    data = job_data(session, dispatched)
    record = session.exec(
        project_service._idempotency_statement(
            actor_id=actor.id,
            project_id=job.project_id,
            method="POST",
            path_template=path,
            key=idempotency_key,
        ).with_for_update()
    ).one()
    record.response_body = data
    session.add(record)
    project_service._commit(session)
    return project_service.OperationResult(data=data, status_code=200)


def claim_job(
    session: Session,
    *,
    job_id: uuid.UUID,
    worker_id: str,
    engine: str,
    engine_version: str | None,
    parameters: dict[str, Any] | None = None,
    input_hash: str | None = None,
    implementation_metadata: dict[str, Any] | None = None,
    store: JobEventStore | None = None,
) -> RunClaim | None:
    job = session.exec(
        select(Job)
        .where(Job.id == job_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).first()
    if job is None:
        return None
    if job.status == JobStatus.CANCEL_REQUESTED:
        job.status = JobStatus.CANCELLED
        job.completed_at = get_datetime_utc()
        session.add(job)
        _audit(
            session,
            job=job,
            action="JOB_CANCELLED",
            actor_type=AuditActorType.WORKER,
            actor_id=worker_id,
            after={"status": job.status},
        )
        project_service._commit(session)
        _publish(job, event_type="job.cancelled", message="Job cancelled.", store=store)
        return None
    if job.status != JobStatus.QUEUED:
        return None
    active = session.exec(
        select(ProcessingRun).where(
            ProcessingRun.job_id == job.id,
            ProcessingRun.status == JobStatus.RUNNING,
        )
    ).first()
    if active is not None:
        return None
    latest_attempt = session.exec(
        select(func.max(ProcessingRun.attempt_number)).where(
            ProcessingRun.job_id == job.id
        )
    ).one()
    attempt_number = (latest_attempt or 0) + 1
    now = get_datetime_utc()
    run = ProcessingRun(
        project_id=job.project_id,
        job_id=job.id,
        process_type=job.task_type,
        input_object_type=job.resource_type,
        input_object_id=job.resource_id,
        input_hash=input_hash,
        parameters=parameters,
        parameters_hash=_canonical_hash(parameters or {}),
        attempt_number=attempt_number,
        engine=engine,
        engine_version=engine_version,
        implementation_metadata=implementation_metadata,
        status=JobStatus.RUNNING,
        started_at=now,
    )
    session.add(run)
    session.flush()
    job.status = JobStatus.RUNNING
    job.started_at = now
    job.last_heartbeat_at = now
    session.add(job)
    _audit(
        session,
        job=job,
        action="JOB_STARTED",
        actor_type=AuditActorType.WORKER,
        actor_id=worker_id,
        after={
            "status": job.status,
            "processing_run_id": run.id,
            "attempt_number": attempt_number,
        },
    )
    project_service._commit(session)
    _publish(
        job, event_type="job.started", message="Job execution started.", store=store
    )
    return RunClaim(run_id=run.id, job_id=job.id, attempt_number=attempt_number)


def update_progress(
    session: Session,
    *,
    job_id: uuid.UUID,
    run_id: uuid.UUID,
    worker_id: str,
    progress_percent: int,
    current_step: str | None,
    completed_steps: int | None = None,
    total_steps: int | None = None,
    message: str = "Job progress updated.",
    store: JobEventStore | None = None,
) -> bool:
    if not 0 <= progress_percent <= 100:
        raise ValueError("progress_percent must be between 0 and 100")
    job = session.exec(select(Job).where(Job.id == job_id).with_for_update()).first()
    run = session.get(ProcessingRun, run_id)
    if (
        job is None
        or run is None
        or run.job_id != job_id
        or run.status != JobStatus.RUNNING
    ):
        return False
    if job.status == JobStatus.CANCEL_REQUESTED:
        acknowledge_cancel(
            session, job_id=job_id, run_id=run_id, worker_id=worker_id, store=store
        )
        return False
    if job.status != JobStatus.RUNNING:
        return False
    job.progress_percent = progress_percent
    job.current_step = current_step
    job.completed_steps = completed_steps
    job.total_steps = total_steps
    job.last_heartbeat_at = get_datetime_utc()
    session.add(job)
    project_service._commit(session)
    _publish(job, event_type="job.progress", message=message, store=store)
    return True


def set_run_context(
    session: Session,
    *,
    job_id: uuid.UUID,
    run_id: uuid.UUID,
    input_hash: str,
    parameters: dict[str, Any],
    implementation_metadata: dict[str, Any],
) -> ProcessingRun:
    job = session.get(Job, job_id)
    run = session.exec(
        select(ProcessingRun).where(ProcessingRun.id == run_id).with_for_update()
    ).first()
    if (
        job is None
        or run is None
        or run.job_id != job.id
        or run.project_id != job.project_id
        or job.status != JobStatus.RUNNING
        or run.status != JobStatus.RUNNING
    ):
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="ProcessingRun is not available for execution context.",
        )
    run.input_hash = input_hash
    run.parameters = jsonable_encoder(parameters)
    run.parameters_hash = _canonical_hash(parameters)
    run.implementation_metadata = jsonable_encoder(implementation_metadata)
    session.add(run)
    project_service._commit(session)
    session.refresh(run)
    return run


def complete_job(
    session: Session,
    *,
    job_id: uuid.UUID,
    run_id: uuid.UUID,
    worker_id: str,
    output_object_type: str | None = None,
    output_object_id: uuid.UUID | None = None,
    log_artifact_id: uuid.UUID | None = None,
    store: JobEventStore | None = None,
) -> bool:
    job = session.exec(select(Job).where(Job.id == job_id).with_for_update()).first()
    run = session.get(ProcessingRun, run_id)
    if job is None or run is None or run.job_id != job_id:
        return False
    if job.status != JobStatus.RUNNING or run.status != JobStatus.RUNNING:
        return False
    now = get_datetime_utc()
    run.status = JobStatus.COMPLETED
    run.output_object_type = output_object_type
    run.output_object_id = output_object_id
    run.log_artifact_id = log_artifact_id
    run.completed_at = now
    job.status = JobStatus.COMPLETED
    job.progress_percent = 100
    job.completed_at = now
    job.last_heartbeat_at = now
    job.retryable = False
    session.add(run)
    session.add(job)
    _audit(
        session,
        job=job,
        action="JOB_COMPLETED",
        actor_type=AuditActorType.WORKER,
        actor_id=worker_id,
        after={"status": job.status, "processing_run_id": run.id},
    )
    project_service._commit(session)
    _publish(job, event_type="job.completed", message="Job completed.", store=store)
    return True


def fail_job(
    session: Session,
    *,
    job_id: uuid.UUID,
    run_id: uuid.UUID,
    worker_id: str,
    error_code: str,
    error_message: str,
    retryable: bool,
    store: JobEventStore | None = None,
) -> bool:
    job = session.exec(select(Job).where(Job.id == job_id).with_for_update()).first()
    run = session.get(ProcessingRun, run_id)
    if job is None or run is None or run.job_id != job_id:
        return False
    if job.status != JobStatus.RUNNING or run.status != JobStatus.RUNNING:
        return False
    now = get_datetime_utc()
    run.status = JobStatus.FAILED
    run.completed_at = now
    job.status = JobStatus.FAILED
    job.completed_at = now
    job.last_heartbeat_at = now
    job.error_code = error_code
    job.error_message = error_message
    job.retryable = retryable
    session.add(run)
    session.add(job)
    _audit(
        session,
        job=job,
        action="JOB_FAILED",
        actor_type=AuditActorType.WORKER,
        actor_id=worker_id,
        after={
            "status": job.status,
            "processing_run_id": run.id,
            "error_code": error_code,
        },
        outcome=AuditOutcome.FAILED,
    )
    project_service._commit(session)
    _publish(
        job,
        event_type="job.failed",
        message="Job failed.",
        payload={"error_code": error_code, "retryable": retryable},
        store=store,
    )
    return True


def acknowledge_cancel(
    session: Session,
    *,
    job_id: uuid.UUID,
    run_id: uuid.UUID,
    worker_id: str,
    store: JobEventStore | None = None,
) -> bool:
    job = session.exec(select(Job).where(Job.id == job_id).with_for_update()).first()
    run = session.get(ProcessingRun, run_id)
    if job is None or run is None or run.job_id != job_id:
        return False
    if job.status != JobStatus.CANCEL_REQUESTED or run.status != JobStatus.RUNNING:
        return False
    now = get_datetime_utc()
    run.status = JobStatus.CANCELLED
    run.completed_at = now
    job.status = JobStatus.CANCELLED
    job.completed_at = now
    job.last_heartbeat_at = now
    session.add(run)
    session.add(job)
    _audit(
        session,
        job=job,
        action="JOB_CANCELLED",
        actor_type=AuditActorType.WORKER,
        actor_id=worker_id,
        after={"status": job.status, "processing_run_id": run.id},
    )
    project_service._commit(session)
    _publish(job, event_type="job.cancelled", message="Job cancelled.", store=store)
    return True


def fail_stale_running_jobs(
    session: Session,
    *,
    heartbeat_before: datetime,
    worker_id: str = "job-recovery",
    store: JobEventStore | None = None,
) -> int:
    jobs = session.exec(
        select(Job).where(
            Job.status == JobStatus.RUNNING,
            col(Job.last_heartbeat_at).is_not(None),
            col(Job.last_heartbeat_at) < heartbeat_before,
        )
    ).all()
    failed = 0
    for candidate in jobs:
        locked = session.exec(
            select(Job).where(Job.id == candidate.id).with_for_update()
        ).one()
        heartbeat = locked.last_heartbeat_at
        if (
            locked.status != JobStatus.RUNNING
            or heartbeat is None
            or heartbeat >= heartbeat_before
        ):
            continue
        run = _latest_run(session, locked.id)
        if run is None or run.status != JobStatus.RUNNING:
            continue
        if fail_job(
            session,
            job_id=locked.id,
            run_id=run.id,
            worker_id=worker_id,
            error_code="JOB_TIMEOUT",
            error_message="Worker heartbeat expired before completion.",
            retryable=True,
            store=store,
        ):
            failed += 1
    return failed
