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
        except Exception as error:
            error_code = str(getattr(error, "code", "JOB_EXECUTION_FAILED"))
            retryable = bool(getattr(error, "retryable", True))
            service.fail_job(
                session,
                job_id=job.id,
                run_id=claim.run_id,
                worker_id=worker_id,
                error_code=error_code,
                error_message="The registered domain handler failed.",
                retryable=retryable,
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


def _execute_research_question_scoping(
    *, session: Session, job: Job, run_id: uuid.UUID
) -> JobExecutionResult:
    from app.research_questions.scoping import execute_scoping_job

    artifact = execute_scoping_job(session, job=job, run_id=run_id)
    return JobExecutionResult(
        output_object_type="artifact",
        output_object_id=artifact.id,
        log_artifact_id=artifact.id,
    )


def _execute_query_plan_generation(
    *, session: Session, job: Job, run_id: uuid.UUID
) -> JobExecutionResult:
    from app.query_plans.generation import execute_generation_job

    artifact = execute_generation_job(session, job=job, run_id=run_id)
    return JobExecutionResult(
        output_object_type="artifact",
        output_object_id=artifact.id,
        log_artifact_id=artifact.id,
    )


def _execute_literature_search(
    *, session: Session, job: Job, run_id: uuid.UUID
) -> JobExecutionResult:
    from app.literature.service import execute_search_job

    search_run = execute_search_job(session, job=job, run_id=run_id)
    return JobExecutionResult(
        output_object_type="literature_search_run",
        output_object_id=search_run.id,
    )


def _execute_document_parse(
    *, session: Session, job: Job, run_id: uuid.UUID
) -> JobExecutionResult:
    from app.documents.service import execute_parse_job

    document = execute_parse_job(session, job=job, run_id=run_id)
    return JobExecutionResult(
        output_object_type="document",
        output_object_id=document.id,
    )


register_job_handler(
    JobTaskType.RESEARCH_QUESTION_SCOPING,
    _execute_research_question_scoping,
)
register_job_handler(
    JobTaskType.QUERY_PLAN_GENERATION,
    _execute_query_plan_generation,
)
register_job_handler(JobTaskType.LITERATURE_SEARCH, _execute_literature_search)
register_job_handler(JobTaskType.DOCUMENT_PARSE, _execute_document_parse)
