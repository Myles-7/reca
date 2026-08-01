from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from sqlmodel import Session

from app.core.celery import celery_app
from app.core.db import engine
from app.jobs import service
from app.models import Job, JobTaskType


@dataclass(frozen=True)
class JobExecutionResult:
    output_object_type: str | None = None
    output_object_id: uuid.UUID | None = None
    log_artifact_id: uuid.UUID | None = None


class JobHandler(Protocol):
    def __call__(
        self, *, session: Session, job: Job, run_id: uuid.UUID
    ) -> JobExecutionResult: ...


_handlers: dict[JobTaskType, JobHandler] = {}


def register_job_handler(task_type: JobTaskType, handler: JobHandler) -> None:
    _handlers[task_type] = handler


def _execute_job(self: object, job_id: str) -> dict[str, object]:
    request = getattr(self, "request", None)
    worker_id = str(getattr(request, "hostname", None) or "reca-worker")
    parsed_job_id = uuid.UUID(job_id)
    with Session(engine) as session:
        claim = service.claim_job(
            session,
            job_id=parsed_job_id,
            worker_id=worker_id,
            engine="reca-worker",
            engine_version="0.1.0",
            implementation_metadata={"task_name": "reca.execute_job"},
        )
        if claim is None:
            return {"job_id": job_id, "claimed": False}
        job = session.get(Job, parsed_job_id)
        assert job is not None
        handler = _handlers.get(job.task_type)
        if handler is None:
            service.fail_job(
                session,
                job_id=job.id,
                run_id=claim.run_id,
                worker_id=worker_id,
                error_code="JOB_HANDLER_NOT_REGISTERED",
                error_message="No domain handler is registered for this Job type.",
                retryable=False,
            )
            return {
                "job_id": job_id,
                "claimed": True,
                "completed": False,
                "error_code": "JOB_HANDLER_NOT_REGISTERED",
            }
        try:
            result = handler(session=session, job=job, run_id=claim.run_id)
        except Exception:
            service.fail_job(
                session,
                job_id=job.id,
                run_id=claim.run_id,
                worker_id=worker_id,
                error_code="JOB_EXECUTION_FAILED",
                error_message="The registered domain handler failed.",
                retryable=True,
            )
            raise
        completed = service.complete_job(
            session,
            job_id=job.id,
            run_id=claim.run_id,
            worker_id=worker_id,
            output_object_type=result.output_object_type,
            output_object_id=result.output_object_id,
            log_artifact_id=result.log_artifact_id,
        )
        return {"job_id": job_id, "claimed": True, "completed": completed}


execute_job = celery_app.task(
    bind=True,
    name="reca.execute_job",
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=True,
)(_execute_job)
