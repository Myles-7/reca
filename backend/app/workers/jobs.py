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
            job = session.get(Job, parsed_job_id)
            if job is not None and job.task_type == JobTaskType.ANALYSIS_RUN:
                from app.analysis.service import mark_cancelled_analysis_job

                mark_cancelled_analysis_job(session, job=job)
            if job is not None and job.task_type == JobTaskType.FIGURE_RENDER:
                from app.figures.service import mark_cancelled_figure_job

                mark_cancelled_figure_job(session, job=job)
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


def _execute_literature_extraction(
    *, session: Session, job: Job, run_id: uuid.UUID
) -> JobExecutionResult:
    from app.evidence.extraction import execute_extraction_job

    result = execute_extraction_job(session, job=job, run_id=run_id)
    return JobExecutionResult(
        output_object_type="literature_extraction",
        output_object_id=result.extraction.id,
        log_artifact_id=(
            result.output_artifact.id if result.output_artifact is not None else None
        ),
    )


def _execute_evidence_set_summary(
    *, session: Session, job: Job, run_id: uuid.UUID
) -> JobExecutionResult:
    from app.evidence.analysis import execute_summary_job

    result = execute_summary_job(session, job=job, run_id=run_id)
    return JobExecutionResult(
        output_object_type=result.output_object_type,
        output_object_id=result.output_object_id,
        log_artifact_id=(
            result.output_artifact.id if result.output_artifact is not None else None
        ),
    )


def _execute_topic_generation(
    *, session: Session, job: Job, run_id: uuid.UUID
) -> JobExecutionResult:
    from app.evidence.analysis import execute_topic_job

    result = execute_topic_job(session, job=job, run_id=run_id)
    return JobExecutionResult(
        output_object_type=result.output_object_type,
        output_object_id=result.output_object_id,
        log_artifact_id=(
            result.output_artifact.id if result.output_artifact is not None else None
        ),
    )


def _execute_dataset_profile(
    *, session: Session, job: Job, run_id: uuid.UUID
) -> JobExecutionResult:
    from app.data_quality.service import execute_quality_job

    quality_run = execute_quality_job(session, job=job, run_id=run_id)
    return JobExecutionResult(
        output_object_type="data_quality_run",
        output_object_id=quality_run.id,
    )


def _execute_dataset_transform(
    *, session: Session, job: Job, run_id: uuid.UUID
) -> JobExecutionResult:
    from app.cleaning.service import execute_transformation_job

    transformation = execute_transformation_job(session, job=job, run_id=run_id)
    return JobExecutionResult(
        output_object_type="data_transformation",
        output_object_id=transformation.id,
        log_artifact_id=transformation.log_artifact_id,
    )


def _execute_analysis_run(
    *, session: Session, job: Job, run_id: uuid.UUID
) -> JobExecutionResult:
    from app.analysis.service import execute_analysis_job

    analysis_run = execute_analysis_job(session, job=job, run_id=run_id)
    return JobExecutionResult(
        output_object_type="analysis_run",
        output_object_id=analysis_run.id,
        log_artifact_id=analysis_run.log_artifact_id,
    )


def _execute_figure_render(
    *, session: Session, job: Job, run_id: uuid.UUID
) -> JobExecutionResult:
    from app.figures.service import execute_render_job

    render_run = execute_render_job(session, job=job, run_id=run_id)
    return JobExecutionResult(
        output_object_type="figure_render_run",
        output_object_id=render_run.id,
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
register_job_handler(JobTaskType.LITERATURE_EXTRACT, _execute_literature_extraction)
register_job_handler(JobTaskType.LITERATURE_SUMMARIZE, _execute_evidence_set_summary)
register_job_handler(JobTaskType.TOPIC_GENERATE, _execute_topic_generation)
register_job_handler(JobTaskType.DATASET_PROFILE, _execute_dataset_profile)
register_job_handler(JobTaskType.DATASET_TRANSFORM, _execute_dataset_transform)
register_job_handler(JobTaskType.ANALYSIS_RUN, _execute_analysis_run)
register_job_handler(JobTaskType.FIGURE_RENDER, _execute_figure_render)
