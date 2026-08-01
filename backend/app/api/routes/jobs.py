from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError, ContractErrorResponse
from app.jobs import service
from app.jobs.dispatcher import dispatcher
from app.jobs.events import EventStoreError, event_store
from app.jobs.schemas import JobCancel, JobEnvelope, JobListEnvelope
from app.models import JobStatus, JobTaskType, get_datetime_utc

router = APIRouter(tags=["jobs"])
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ContractErrorResponse},
    403: {"model": ContractErrorResponse},
    404: {"model": ContractErrorResponse},
    409: {"model": ContractErrorResponse},
    422: {"model": ContractErrorResponse},
    503: {"model": ContractErrorResponse},
}
HEARTBEAT_SECONDS = 15


def _meta(*, replayed: bool = False) -> dict[str, Any]:
    from app.core.observability import current_request_id

    return {
        "request_id": current_request_id(),
        "schema_version": service.SCHEMA_VERSION,
        "idempotency_replayed": replayed,
    }


def _required_idempotency_key(value: str | None) -> str:
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


@router.get(
    "/projects/{project_id}/jobs",
    response_model=JobListEnvelope,
    responses=ERROR_RESPONSES,
)
def list_project_jobs(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    status: JobStatus | None = None,
    task_type: JobTaskType | None = None,
    resource_type: str | None = Query(default=None, max_length=100),
    resource_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    data, pagination = service.list_jobs(
        session,
        actor=current_user,
        project_id=project_id,
        status=status,
        task_type=task_type,
        resource_type=resource_type,
        resource_id=resource_id,
        page=page,
        page_size=page_size,
    )
    return {"data": data, "pagination": pagination, "meta": _meta()}


@router.get("/jobs/{job_id}", response_model=JobEnvelope, responses=ERROR_RESPONSES)
def get_job(
    *, session: SessionDep, current_user: CurrentUser, job_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_job(session, actor=current_user, job_id=job_id),
        "meta": _meta(),
    }


@router.post(
    "/jobs/{job_id}/cancel", response_model=JobEnvelope, responses=ERROR_RESPONSES
)
def cancel_job(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    job_id: uuid.UUID,
    cancel_in: JobCancel,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.cancel_job(
        session,
        actor=current_user,
        job_id=job_id,
        reason=cancel_in.reason,
        idempotency_key=_required_idempotency_key(idempotency_key),
        store=event_store,
    )
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.data,
            "meta": _meta(replayed=result.idempotency_replayed),
        },
    )


@router.post(
    "/jobs/{job_id}/retry", response_model=JobEnvelope, responses=ERROR_RESPONSES
)
def retry_job(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    job_id: uuid.UUID,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    result = service.retry_job(
        session,
        actor=current_user,
        job_id=job_id,
        idempotency_key=_required_idempotency_key(idempotency_key),
        dispatcher=dispatcher,
        store=event_store,
    )
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.data,
            "meta": _meta(replayed=result.idempotency_replayed),
        },
    )


def _format_event(event: dict[str, Any], *, include_id: bool = True) -> str:
    event_id = f"id: {event['event_id']}\n" if include_id else ""
    return (
        f"event: {event['event_type']}\n"
        f"{event_id}"
        f"data: {json.dumps(event, separators=(',', ':'))}\n\n"
    )


def _resync_event(
    *, job: dict[str, Any], last_event_id: int | None, reason: str
) -> dict[str, Any]:
    return {
        "schema_version": service.SCHEMA_VERSION,
        "event_id": max((last_event_id or 0) + 1, 1),
        "event_type": "job.resync_required",
        "job_id": job["id"],
        "project_id": job["project_id"],
        "status": job["status"],
        "progress_percent": job["progress_percent"],
        "current_step": job["current_step"],
        "message": "Job event history is unavailable; refresh the Job detail.",
        "payload": {
            "reason": reason,
            "status_url": f"/api/v1/jobs/{job['id']}",
        },
        "occurred_at": get_datetime_utc().isoformat(),
    }


@router.get("/jobs/{job_id}/events", responses=ERROR_RESPONSES)
def stream_job_events(
    *,
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
    job_id: uuid.UUID,
    last_event_id: Annotated[int | None, Header(alias="Last-Event-ID", ge=0)] = None,
) -> StreamingResponse:
    job = service.get_job(session, actor=current_user, job_id=job_id)

    async def stream() -> AsyncIterator[str]:
        current_job = job
        cursor = last_event_id
        heartbeat_elapsed = 0
        while True:
            if await request.is_disconnected():
                return
            try:
                events, history_missed = event_store.after(
                    job_id=job_id, last_event_id=cursor
                )
            except EventStoreError:
                yield _format_event(
                    _resync_event(
                        job=current_job,
                        last_event_id=cursor,
                        reason="EVENT_CACHE_UNAVAILABLE",
                    )
                )
                return
            if history_missed:
                yield _format_event(
                    _resync_event(
                        job=current_job,
                        last_event_id=cursor,
                        reason="EVENT_HISTORY_EXPIRED",
                    )
                )
                return
            for event in events:
                cursor = int(event["event_id"])
                yield _format_event(dict(event))
                if event["status"] in {
                    JobStatus.COMPLETED,
                    JobStatus.FAILED,
                    JobStatus.CANCELLED,
                }:
                    return
            current_job = service.get_job(session, actor=current_user, job_id=job_id)
            if current_job["status"] in service.TERMINAL_STATUSES:
                return
            await asyncio.sleep(1)
            heartbeat_elapsed += 1
            if heartbeat_elapsed >= HEARTBEAT_SECONDS:
                heartbeat_elapsed = 0
                heartbeat = {
                    "schema_version": service.SCHEMA_VERSION,
                    "event_id": cursor or 0,
                    "event_type": "job.heartbeat",
                    "job_id": current_job["id"],
                    "project_id": current_job["project_id"],
                    "status": current_job["status"],
                    "progress_percent": current_job["progress_percent"],
                    "current_step": current_job["current_step"],
                    "message": "Job event stream heartbeat.",
                    "payload": {},
                    "occurred_at": get_datetime_utc().isoformat(),
                }
                yield _format_event(heartbeat, include_id=False)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
