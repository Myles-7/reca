from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from datetime import timedelta
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc, func, or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.adapters.literature import (
    OPENALEX_PROVIDER_NAME,
    LiteratureProvider,
    LiteratureProviderError,
    LiteratureQueryPlanDTO,
    LiteratureRecordDTO,
    ProviderErrorCode,
    PyAlexOpenAlexProvider,
)
from app.api.errors import ContractError
from app.core.config import settings
from app.core.observability import current_request_id
from app.jobs import service as job_service
from app.literature.normalization import (
    normalize_doi,
    normalize_title,
    title_similarity,
)
from app.literature.schemas import (
    LiteratureDoiImportRequest,
    LiteratureImportRequest,
    LiteratureSearchCreate,
)
from app.models import (
    AuditActorType,
    AuditLog,
    AuditOutcome,
    Job,
    JobStatus,
    JobTaskType,
    LiteratureDecisionStatus,
    LiteratureRecord,
    LiteratureSearchCandidate,
    LiteratureSearchRun,
    LiteratureSourceType,
    LiteratureVerificationStatus,
    QueryPlan,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

_SIMILAR_TITLE_THRESHOLD = 0.92


class LiteratureSearchExecutionError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def _not_found() -> ContractError:
    return ContractError(
        status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
    )


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(
        jsonable_encoder(payload),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _audit(
    session: Session,
    *,
    project_id: uuid.UUID,
    actor_type: AuditActorType,
    actor_id: str | None,
    action: str,
    object_type: str,
    object_id: uuid.UUID,
    after: dict[str, Any],
    outcome: AuditOutcome = AuditOutcome.SUCCEEDED,
) -> None:
    session.add(
        AuditLog(
            project_id=project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            after_snapshot=jsonable_encoder(after),
            request_id=current_request_id(),
            outcome=outcome,
        )
    )


def _flush_or_conflict(session: Session) -> None:
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="The operation conflicted with a concurrent change.",
            retryable=True,
        ) from exc


def _can_update(access: project_service.ProjectAccess) -> bool:
    return (
        access.membership is not None
        and "project.update" in project_service.allowed_actions(access.membership.role)
    )


def _workspace_actions(*, can_update: bool) -> list[str]:
    actions = ["literature.read"]
    if can_update:
        actions.extend(
            [
                "literature.search",
                "literature.import",
                "literature.import_doi",
                "document.upload",
            ]
        )
    return actions


def search_run_data(
    run: LiteratureSearchRun, *, can_update: bool = False
) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "id": run.id,
                "project_id": run.project_id,
                "query_plan_id": run.query_plan_id,
                "provider": run.provider,
                "provider_query": run.provider_query,
                "result_count": run.result_count,
                "cache_hit": run.cache_hit,
                "cache_stale": run.cache_stale,
                "cache_source_run_id": run.cache_source_run_id,
                "degraded": run.degraded,
                "limitations": run.limitations or [],
                "fetched_at": run.fetched_at,
                "status": run.status,
                "error_code": run.error_code,
                "job_id": run.job_id,
                "created_at": run.created_at,
                "allowed_actions": [
                    "literature_search.read",
                    *(
                        ["literature_search.import"]
                        if can_update and run.status == JobStatus.COMPLETED
                        else []
                    ),
                ],
            }
        ),
    )


def candidate_data(
    candidate: LiteratureSearchCandidate, *, can_import: bool = False
) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "id": candidate.id,
                "project_id": candidate.project_id,
                "search_run_id": candidate.search_run_id,
                "result_order": candidate.result_order,
                "source_identifier": candidate.source_identifier,
                "title": candidate.title,
                "abstract": candidate.abstract,
                "publication_year": candidate.publication_year,
                "journal_name": candidate.journal_name,
                "doi": candidate.doi,
                "authors_text": candidate.authors_text,
                "keywords": candidate.keywords or [],
                "work_type": candidate.work_type,
                "open_access_status": candidate.open_access_status,
                "verification_status": candidate.verification_status,
                "fetched_at": candidate.fetched_at,
                "degraded": candidate.degraded,
                "imported_literature_record_id": (
                    candidate.imported_literature_record_id
                ),
                "allowed_actions": [
                    "literature_candidate.read",
                    *(
                        ["literature_candidate.import"]
                        if can_import
                        and candidate.imported_literature_record_id is None
                        else []
                    ),
                ],
            }
        ),
    )


def literature_record_data(
    record: LiteratureRecord, *, can_update: bool = False
) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "id": record.id,
                "project_id": record.project_id,
                "document_id": record.document_id,
                "source_type": record.source_type,
                "source_identifier": record.source_identifier,
                "title": record.title,
                "abstract": record.abstract,
                "publication_year": record.publication_year,
                "journal_name": record.journal_name,
                "doi": record.doi,
                "authors_text": record.authors_text,
                "keywords": record.keywords or [],
                "work_type": record.work_type,
                "open_access_status": record.open_access_status,
                "verification_status": record.verification_status,
                "current_decision": record.current_decision,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "allowed_actions": [
                    "literature.read",
                    *(
                        ["document.upload"]
                        if can_update and record.document_id is None
                        else []
                    ),
                ],
            }
        ),
    )


def _plan_for_update(
    session: Session, *, actor: User, query_plan_id: uuid.UUID
) -> QueryPlan:
    plan = session.get(QueryPlan, query_plan_id)
    if plan is None:
        raise _not_found()
    project_service.authorize_project(
        session, project_id=plan.project_id, actor=actor, action="project.update"
    )
    return plan


def request_search_job(
    session: Session,
    *,
    actor: User,
    query_plan_id: uuid.UUID,
    payload: LiteratureSearchCreate,
    idempotency_key: str,
    dispatcher: job_service.JobDispatcher,
) -> project_service.OperationResult:
    plan = _plan_for_update(session, actor=actor, query_plan_id=query_plan_id)
    path = "/api/v1/query-plans/{query_plan_id}/search-runs"
    digest = project_service.request_hash(payload)
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    query_dto = LiteratureQueryPlanDTO.from_query_plan(plan)
    fingerprint = _canonical_hash(
        {
            "query_plan": query_dto.model_dump(mode="json"),
            "page_size": payload.page_size,
        }
    )
    run = LiteratureSearchRun(
        project_id=plan.project_id,
        query_plan_id=plan.id,
        provider=OPENALEX_PROVIDER_NAME,
        provider_query={
            "page_size": payload.page_size,
            "use_cache": payload.use_cache,
            "query_plan_lock_version": plan.lock_version,
        },
        query_fingerprint=fingerprint,
        status=JobStatus.DRAFT,
    )
    session.add(run)
    session.flush()
    job = job_service.create_job(
        session,
        project_id=plan.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.LITERATURE_SEARCH,
            resource_type="literature_search_run",
            resource_id=run.id,
            idempotency_key=idempotency_key,
            requested_by_user_id=actor.id,
            max_retries=2,
            retryable=True,
        ),
    )
    run.job_id = job.id
    session.add(run)
    _audit(
        session,
        project_id=run.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="LITERATURE_SEARCH_REQUESTED",
        object_type="literature_search_run",
        object_id=run.id,
        after={"query_plan_id": plan.id, "job_id": job.id},
    )
    project_service._commit(session)
    dispatched = job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)
    refreshed_run = session.get(LiteratureSearchRun, run.id)
    assert refreshed_run is not None
    refreshed_run.status = dispatched.status
    refreshed_run.error_code = dispatched.error_code
    refreshed_run.updated_at = get_datetime_utc()
    session.add(refreshed_run)
    result = project_service.OperationResult(
        data={
            "search_run": search_run_data(refreshed_run, can_update=True),
            "job": job_service.job_data(session, dispatched),
        },
        status_code=202,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result


def _cache_source(
    session: Session, *, run: LiteratureSearchRun
) -> LiteratureSearchRun | None:
    return session.exec(
        select(LiteratureSearchRun)
        .where(
            LiteratureSearchRun.project_id == run.project_id,
            LiteratureSearchRun.query_fingerprint == run.query_fingerprint,
            LiteratureSearchRun.status == JobStatus.COMPLETED,
            LiteratureSearchRun.id != run.id,
        )
        .order_by(desc(col(LiteratureSearchRun.fetched_at)))
    ).first()


def _copy_candidates(
    session: Session,
    *,
    source: LiteratureSearchRun,
    target: LiteratureSearchRun,
) -> int:
    candidates = session.exec(
        select(LiteratureSearchCandidate)
        .where(LiteratureSearchCandidate.search_run_id == source.id)
        .order_by(col(LiteratureSearchCandidate.result_order))
    ).all()
    for candidate in candidates:
        session.add(
            LiteratureSearchCandidate(
                project_id=target.project_id,
                search_run_id=target.id,
                result_order=candidate.result_order,
                source_identifier=candidate.source_identifier,
                title=candidate.title,
                normalized_title=candidate.normalized_title,
                abstract=candidate.abstract,
                publication_year=candidate.publication_year,
                journal_name=candidate.journal_name,
                doi=candidate.doi,
                normalized_doi=candidate.normalized_doi,
                authors_text=candidate.authors_text,
                keywords=candidate.keywords,
                work_type=candidate.work_type,
                open_access_status=candidate.open_access_status,
                verification_status=candidate.verification_status,
                raw_source_data=candidate.raw_source_data,
                fetched_at=candidate.fetched_at,
                degraded=candidate.degraded,
            )
        )
    return len(candidates)


def _complete_from_cache(
    session: Session,
    *,
    run: LiteratureSearchRun,
    source: LiteratureSearchRun,
    stale: bool,
    provider_error: LiteratureProviderError | None = None,
) -> LiteratureSearchRun:
    count = _copy_candidates(session, source=source, target=run)
    run.provider = source.provider
    run.provider_query = {
        **run.provider_query,
        "cache_source_provider_query": source.provider_query,
    }
    run.result_count = count
    run.cache_hit = True
    run.cache_stale = stale
    run.cache_source_run_id = source.id
    run.degraded = source.degraded or stale
    limitations = list(source.limitations or [])
    limitations.append(
        "Stale cached literature results were used after Provider failure."
        if stale
        else "Cached literature results were used; results are not live."
    )
    run.limitations = list(dict.fromkeys(limitations))
    run.fetched_at = source.fetched_at
    run.status = JobStatus.COMPLETED
    run.error_code = provider_error.code.value if provider_error else None
    run.updated_at = get_datetime_utc()
    session.add(run)
    _audit(
        session,
        project_id=run.project_id,
        actor_type=AuditActorType.WORKER,
        actor_id="literature-search-worker",
        action="LITERATURE_SEARCH_CACHE_USED",
        object_type="literature_search_run",
        object_id=run.id,
        after={
            "cache_source_run_id": source.id,
            "cache_stale": stale,
            "result_count": count,
        },
    )
    project_service._commit(session)
    session.refresh(run)
    return run


def _provider_error_run(
    session: Session,
    *,
    run: LiteratureSearchRun,
    error: LiteratureProviderError,
) -> None:
    run.status = JobStatus.FAILED
    run.error_code = error.code.value
    run.result_count = 0
    run.limitations = [str(error)]
    run.updated_at = get_datetime_utc()
    session.add(run)
    _audit(
        session,
        project_id=run.project_id,
        actor_type=AuditActorType.WORKER,
        actor_id="literature-search-worker",
        action="LITERATURE_SEARCH_FAILED",
        object_type="literature_search_run",
        object_id=run.id,
        after={"error_code": error.code.value, "result_count": 0},
        outcome=AuditOutcome.FAILED,
    )
    project_service._commit(session)


def execute_search_job(
    session: Session,
    *,
    job: Job,
    run_id: uuid.UUID,
    provider: LiteratureProvider | None = None,
) -> LiteratureSearchRun:
    if job.task_type != JobTaskType.LITERATURE_SEARCH:
        raise LiteratureSearchExecutionError(
            "JOB_HANDLER_MISMATCH",
            "Job is not a literature search job.",
            retryable=False,
        )
    run = session.exec(
        select(LiteratureSearchRun)
        .where(LiteratureSearchRun.id == job.resource_id)
        .with_for_update()
    ).first()
    if run is None or run.project_id != job.project_id or run.job_id != job.id:
        raise LiteratureSearchExecutionError(
            "LITERATURE_SEARCH_RUN_INVALID",
            "LiteratureSearchRun is not available for this Job.",
            retryable=False,
        )
    plan = session.get(QueryPlan, run.query_plan_id)
    if plan is None or plan.project_id != run.project_id:
        raise LiteratureSearchExecutionError(
            "LITERATURE_SEARCH_SOURCE_INVALID",
            "QueryPlan is not available for this literature search.",
            retryable=False,
        )
    expected_lock = int(run.provider_query.get("query_plan_lock_version", 0))
    page_size = int(run.provider_query.get("page_size", 25))
    use_cache = bool(run.provider_query.get("use_cache", True))
    query_dto = LiteratureQueryPlanDTO.from_query_plan(plan)
    fingerprint = _canonical_hash(
        {"query_plan": query_dto.model_dump(mode="json"), "page_size": page_size}
    )
    if plan.lock_version != expected_lock or fingerprint != run.query_fingerprint:
        run.status = JobStatus.FAILED
        run.error_code = "RESOURCE_VERSION_CONFLICT"
        run.updated_at = get_datetime_utc()
        session.add(run)
        project_service._commit(session)
        raise LiteratureSearchExecutionError(
            "RESOURCE_VERSION_CONFLICT",
            "QueryPlan changed before literature search execution.",
            retryable=False,
        )
    job_service.set_run_context(
        session,
        job_id=job.id,
        run_id=run_id,
        input_hash=run.query_fingerprint,
        parameters={"page_size": page_size, "use_cache": use_cache},
        implementation_metadata={
            "provider": OPENALEX_PROVIDER_NAME,
            "query_plan_id": str(plan.id),
        },
    )
    run = session.get(LiteratureSearchRun, run.id)
    assert run is not None
    run.status = JobStatus.RUNNING
    run.updated_at = get_datetime_utc()
    session.add(run)
    project_service._commit(session)

    cached = _cache_source(session, run=run) if use_cache else None
    if cached is not None:
        age = get_datetime_utc() - cached.fetched_at
        if age <= timedelta(seconds=settings.OPENALEX_CACHE_TTL_SECONDS):
            return _complete_from_cache(session, run=run, source=cached, stale=False)

    actual_provider = provider or PyAlexOpenAlexProvider()
    try:
        page = asyncio.run(actual_provider.search(query_dto, page_size=page_size))
    except LiteratureProviderError as error:
        if cached is not None and use_cache:
            return _complete_from_cache(
                session,
                run=run,
                source=cached,
                stale=True,
                provider_error=error,
            )
        _provider_error_run(session, run=run, error=error)
        raise LiteratureSearchExecutionError(
            error.code.value, str(error), retryable=error.retryable
        ) from error

    seen_source_ids: set[str] = set()
    result_order = 0
    verification = (
        LiteratureVerificationStatus.UNVERIFIED
        if page.degraded
        else LiteratureVerificationStatus.PARTIALLY_VERIFIED
    )
    for record in page.records:
        if record.source_identifier in seen_source_ids:
            continue
        seen_source_ids.add(record.source_identifier)
        normalized_title = normalize_title(record.title)
        if not normalized_title:
            continue
        result_order += 1
        session.add(
            LiteratureSearchCandidate(
                project_id=run.project_id,
                search_run_id=run.id,
                result_order=result_order,
                source_identifier=record.source_identifier,
                title=record.title,
                normalized_title=normalized_title,
                abstract=record.abstract,
                publication_year=record.publication_year,
                journal_name=record.source_name,
                doi=record.source_doi,
                normalized_doi=record.normalized_doi,
                authors_text="; ".join(author.display_name for author in record.authors)
                or None,
                keywords=list(record.topics) or None,
                work_type=record.work_type,
                open_access_status=record.open_access_status,
                verification_status=verification,
                raw_source_data=record.raw_source_data,
                fetched_at=page.snapshot.retrieved_at,
                degraded=page.degraded,
            )
        )
    run.provider = str(
        page.implementation_metadata.get("provider", page.snapshot.provider)
    )
    run.provider_query = {
        **run.provider_query,
        "provider_request": page.provider_query,
        "snapshot_sha256": page.snapshot.sha256,
        "implementation_metadata": page.implementation_metadata,
    }
    run.result_count = result_order
    run.cache_hit = False
    run.cache_stale = False
    run.degraded = page.degraded
    run.limitations = list(page.limitations) or None
    run.fetched_at = page.snapshot.retrieved_at
    run.status = JobStatus.COMPLETED
    run.error_code = None
    run.updated_at = get_datetime_utc()
    session.add(run)
    _audit(
        session,
        project_id=run.project_id,
        actor_type=AuditActorType.WORKER,
        actor_id="literature-search-worker",
        action="LITERATURE_SEARCH_COMPLETED",
        object_type="literature_search_run",
        object_id=run.id,
        after={
            "result_count": result_order,
            "degraded": run.degraded,
            "cache_hit": False,
        },
    )
    project_service._commit(session)
    session.refresh(run)
    return run


def get_search_results(
    session: Session,
    *,
    actor: User,
    run_id: uuid.UUID,
    verification_status: LiteratureVerificationStatus | None,
    open_access_status: str | None,
    from_year: int | None,
    to_year: int | None,
    q: str | None,
    page: int,
    page_size: int,
) -> tuple[LiteratureSearchRun, list[dict[str, Any]], int, bool]:
    run = session.get(LiteratureSearchRun, run_id)
    if run is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=run.project_id, actor=actor, action="project.read"
    )
    can_update = _can_update(access)
    conditions: list[Any] = [LiteratureSearchCandidate.search_run_id == run.id]
    if verification_status is not None:
        conditions.append(
            LiteratureSearchCandidate.verification_status == verification_status
        )
    if open_access_status:
        conditions.append(
            LiteratureSearchCandidate.open_access_status == open_access_status
        )
    if from_year is not None:
        conditions.append(col(LiteratureSearchCandidate.publication_year) >= from_year)
    if to_year is not None:
        conditions.append(col(LiteratureSearchCandidate.publication_year) <= to_year)
    if q:
        pattern = f"%{q.strip()}%"
        conditions.append(
            or_(
                col(LiteratureSearchCandidate.title).ilike(pattern),
                col(LiteratureSearchCandidate.authors_text).ilike(pattern),
            )
        )
    total = session.exec(
        select(func.count()).select_from(LiteratureSearchCandidate).where(*conditions)
    ).one()
    candidates = session.exec(
        select(LiteratureSearchCandidate)
        .where(*conditions)
        .order_by(col(LiteratureSearchCandidate.result_order))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return (
        run,
        [
            candidate_data(
                candidate,
                can_import=can_update and run.status == JobStatus.COMPLETED,
            )
            for candidate in candidates
        ],
        int(total),
        can_update,
    )


def _authors_match(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False

    def normalize(value: str) -> str:
        return " ".join(value.casefold().split())

    return normalize(left) == normalize(right)


def _title_review_matches(
    session: Session,
    *,
    project_id: uuid.UUID,
    title: str,
    normalized_title: str,
    authors_text: str | None,
    publication_year: int | None,
) -> list[LiteratureRecord]:
    records = session.exec(
        select(LiteratureRecord).where(
            LiteratureRecord.project_id == project_id,
            col(LiteratureRecord.deleted_at).is_(None),
        )
    ).all()
    matches: list[LiteratureRecord] = []
    for record in records:
        if record.normalized_title == normalized_title:
            matches.append(record)
            continue
        if (
            publication_year is not None
            and record.publication_year == publication_year
            and _authors_match(record.authors_text, authors_text)
            and title_similarity(record.title, title) >= _SIMILAR_TITLE_THRESHOLD
        ):
            matches.append(record)
    return matches


def _existing_by_doi(
    session: Session, *, project_id: uuid.UUID, normalized_doi: str | None
) -> LiteratureRecord | None:
    if normalized_doi is None:
        return None
    return session.exec(
        select(LiteratureRecord).where(
            LiteratureRecord.project_id == project_id,
            LiteratureRecord.normalized_doi == normalized_doi,
            col(LiteratureRecord.deleted_at).is_(None),
        )
    ).first()


def _new_record_from_candidate(
    candidate: LiteratureSearchCandidate, *, run: LiteratureSearchRun
) -> LiteratureRecord:
    return LiteratureRecord(
        project_id=candidate.project_id,
        source_type=(
            LiteratureSourceType.CACHE
            if run.cache_hit
            else LiteratureSourceType.OPENALEX
        ),
        source_identifier=candidate.source_identifier,
        title=candidate.title,
        normalized_title=candidate.normalized_title,
        abstract=candidate.abstract,
        publication_year=candidate.publication_year,
        journal_name=candidate.journal_name,
        doi=candidate.doi,
        normalized_doi=candidate.normalized_doi,
        authors_text=candidate.authors_text,
        keywords=candidate.keywords,
        work_type=candidate.work_type,
        open_access_status=candidate.open_access_status,
        verification_status=candidate.verification_status,
        raw_source_data={
            "provider_record": candidate.raw_source_data,
            "search_run_id": str(run.id),
            "candidate_id": str(candidate.id),
            "fetched_at": candidate.fetched_at.isoformat(),
            "cache_hit": run.cache_hit,
            "cache_stale": run.cache_stale,
            "degraded": run.degraded,
        },
        current_decision=LiteratureDecisionStatus.UNCERTAIN,
    )


def import_candidates(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    payload: LiteratureImportRequest,
    idempotency_key: str,
) -> project_service.OperationResult:
    project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="project.update"
    )
    path = "/api/v1/projects/{project_id}/literature/import"
    digest = project_service.request_hash(payload)
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
    run = session.exec(
        select(LiteratureSearchRun).where(
            LiteratureSearchRun.id == payload.search_run_id,
            LiteratureSearchRun.project_id == project_id,
        )
    ).first()
    if run is None or run.status != JobStatus.COMPLETED:
        raise _not_found()
    unique_ids = list(dict.fromkeys(payload.result_ids))
    candidates = session.exec(
        select(LiteratureSearchCandidate).where(
            LiteratureSearchCandidate.project_id == project_id,
            LiteratureSearchCandidate.search_run_id == run.id,
            col(LiteratureSearchCandidate.id).in_(unique_ids),
        )
    ).all()
    if len(candidates) != len(unique_ids):
        raise _not_found()
    by_id = {candidate.id: candidate for candidate in candidates}
    ordered = [by_id[candidate_id] for candidate_id in unique_ids]
    planned: list[tuple[LiteratureSearchCandidate, LiteratureRecord | None]] = []
    review_details: list[dict[str, Any]] = []
    for candidate in ordered:
        if candidate.imported_literature_record_id is not None:
            existing_import = session.get(
                LiteratureRecord, candidate.imported_literature_record_id
            )
            if existing_import is None or existing_import.project_id != project_id:
                raise _not_found()
            planned.append((candidate, existing_import))
            continue
        existing = _existing_by_doi(
            session,
            project_id=project_id,
            normalized_doi=candidate.normalized_doi,
        )
        if existing is not None:
            planned.append((candidate, existing))
            continue
        matches = _title_review_matches(
            session,
            project_id=project_id,
            title=candidate.title,
            normalized_title=candidate.normalized_title,
            authors_text=candidate.authors_text,
            publication_year=candidate.publication_year,
        )
        if matches:
            review_details.append(
                {
                    "candidate_id": str(candidate.id),
                    "possible_literature_record_ids": [
                        str(match.id) for match in matches
                    ],
                }
            )
        planned.append((candidate, None))
    if review_details:
        raise ContractError(
            status_code=409,
            code="LITERATURE_DEDUP_REVIEW_REQUIRED",
            message="Possible duplicate literature requires human review.",
            details={"candidates": review_details},
            suggested_action="Review the possible matches before importing.",
        )
    results: list[dict[str, Any]] = []
    for candidate, existing in planned:
        matched_existing = existing is not None
        record = existing or _new_record_from_candidate(candidate, run=run)
        if existing is None:
            session.add(record)
            _flush_or_conflict(session)
        elif existing.normalized_title != candidate.normalized_title:
            existing.verification_status = LiteratureVerificationStatus.CONFLICTED
            existing.updated_at = get_datetime_utc()
            session.add(existing)
        candidate.imported_literature_record_id = record.id
        session.add(candidate)
        results.append(
            {
                "candidate_id": candidate.id,
                "literature_record_id": record.id,
                "matched_existing": matched_existing,
            }
        )
    _audit(
        session,
        project_id=project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="LITERATURE_CANDIDATES_IMPORTED",
        object_type="literature_search_run",
        object_id=run.id,
        after={"candidate_ids": unique_ids, "import_count": len(results)},
    )
    result = project_service.OperationResult(
        data={"imported": jsonable_encoder(results)}, status_code=200
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
    project_service._commit(session)
    return result


def _provider_contract_error(error: LiteratureProviderError) -> ContractError:
    status_by_code = {
        ProviderErrorCode.INVALID_QUERY: 422,
        ProviderErrorCode.AUTHENTICATION_FAILED: 503,
        ProviderErrorCode.NOT_FOUND: 404,
        ProviderErrorCode.TIMEOUT: 503,
        ProviderErrorCode.RATE_LIMITED: 429,
        ProviderErrorCode.OFFLINE: 503,
        ProviderErrorCode.UPSTREAM_ERROR: 503,
        ProviderErrorCode.SCHEMA_CHANGED: 502,
        ProviderErrorCode.RECORDED_RESPONSE_MISSING: 503,
    }
    return ContractError(
        status_code=status_by_code[error.code],
        code=f"LITERATURE_PROVIDER_{error.code.value}",
        message=str(error),
        retryable=error.retryable,
    )


def _new_record_from_provider(
    *, project_id: uuid.UUID, record: LiteratureRecordDTO
) -> LiteratureRecord:
    title = record.title.strip()
    normalized_title = normalize_title(title)
    if not normalized_title:
        raise ContractError(
            status_code=502,
            code="LITERATURE_PROVIDER_SCHEMA_CHANGED",
            message="Provider returned a literature record without a usable title.",
        )
    return LiteratureRecord(
        project_id=project_id,
        source_type=LiteratureSourceType.DOI_IMPORT,
        source_identifier=record.source_identifier,
        title=title,
        normalized_title=normalized_title,
        abstract=record.abstract,
        publication_year=record.publication_year,
        journal_name=record.source_name,
        doi=record.source_doi,
        normalized_doi=record.normalized_doi,
        authors_text="; ".join(author.display_name for author in record.authors)
        or None,
        keywords=list(record.topics) or None,
        work_type=record.work_type,
        open_access_status=record.open_access_status,
        verification_status=LiteratureVerificationStatus.VERIFIED,
        raw_source_data={
            "provider_record": record.raw_source_data,
            "normalization_version": record.normalization_version,
        },
        current_decision=LiteratureDecisionStatus.UNCERTAIN,
    )


def import_doi(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    payload: LiteratureDoiImportRequest,
    idempotency_key: str,
    provider: LiteratureProvider | None = None,
) -> project_service.OperationResult:
    project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="project.update"
    )
    normalized = normalize_doi(payload.doi)
    if normalized is None:
        raise ContractError(
            status_code=422,
            code="INVALID_DOI",
            message="DOI format is invalid.",
        )
    path = "/api/v1/projects/{project_id}/literature/import-doi"
    digest = project_service.request_hash({"doi": normalized})
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
    existing = _existing_by_doi(
        session, project_id=project_id, normalized_doi=normalized
    )
    if existing is not None:
        result = project_service.OperationResult(
            data=literature_record_data(existing, can_update=True), status_code=200
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
        project_service._commit(session)
        return result
    try:
        provider_record = asyncio.run(
            (provider or PyAlexOpenAlexProvider()).get_by_doi(normalized)
        )
    except LiteratureProviderError as error:
        raise _provider_contract_error(error) from error
    if provider_record is None:
        raise ContractError(
            status_code=404,
            code="DOI_NOT_FOUND",
            message="No literature metadata was found for this DOI.",
        )
    if provider_record.normalized_doi != normalized:
        raise ContractError(
            status_code=409,
            code="LITERATURE_SOURCE_CONFLICT",
            message="Provider DOI does not match the requested DOI.",
        )
    record = _new_record_from_provider(project_id=project_id, record=provider_record)
    matches = _title_review_matches(
        session,
        project_id=project_id,
        title=record.title,
        normalized_title=record.normalized_title,
        authors_text=record.authors_text,
        publication_year=record.publication_year,
    )
    if matches:
        raise ContractError(
            status_code=409,
            code="LITERATURE_DEDUP_REVIEW_REQUIRED",
            message="The DOI metadata may duplicate a record with another DOI.",
            details={
                "possible_literature_record_ids": [str(match.id) for match in matches]
            },
            suggested_action="Review the possible matches before importing.",
        )
    session.add(record)
    _flush_or_conflict(session)
    _audit(
        session,
        project_id=project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="LITERATURE_DOI_IMPORTED",
        object_type="literature_record",
        object_id=record.id,
        after={
            "normalized_doi": normalized,
            "source_identifier": record.source_identifier,
        },
    )
    result = project_service.OperationResult(
        data=literature_record_data(record, can_update=True), status_code=201
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
    project_service._commit(session)
    return result


def list_literature(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    decision: LiteratureDecisionStatus | None,
    verification_status: LiteratureVerificationStatus | None,
    has_document: bool | None,
    year_from: int | None,
    year_to: int | None,
    q: str | None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int, list[str]]:
    access = project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="project.read"
    )
    can_update = _can_update(access)
    conditions: list[Any] = [
        LiteratureRecord.project_id == project_id,
        col(LiteratureRecord.deleted_at).is_(None),
    ]
    if decision is not None:
        conditions.append(LiteratureRecord.current_decision == decision)
    if verification_status is not None:
        conditions.append(LiteratureRecord.verification_status == verification_status)
    if has_document is True:
        conditions.append(col(LiteratureRecord.document_id).is_not(None))
    elif has_document is False:
        conditions.append(col(LiteratureRecord.document_id).is_(None))
    if year_from is not None:
        conditions.append(col(LiteratureRecord.publication_year) >= year_from)
    if year_to is not None:
        conditions.append(col(LiteratureRecord.publication_year) <= year_to)
    if q:
        pattern = f"%{q.strip()}%"
        conditions.append(
            or_(
                col(LiteratureRecord.title).ilike(pattern),
                col(LiteratureRecord.authors_text).ilike(pattern),
                col(LiteratureRecord.doi).ilike(pattern),
            )
        )
    total = session.exec(
        select(func.count()).select_from(LiteratureRecord).where(*conditions)
    ).one()
    records = session.exec(
        select(LiteratureRecord)
        .where(*conditions)
        .order_by(desc(col(LiteratureRecord.created_at)))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return (
        [literature_record_data(record, can_update=can_update) for record in records],
        int(total),
        _workspace_actions(can_update=can_update),
    )


def get_literature(
    session: Session, *, actor: User, literature_id: uuid.UUID
) -> dict[str, Any]:
    record = session.get(LiteratureRecord, literature_id)
    if record is None or record.deleted_at is not None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=record.project_id, actor=actor, action="project.read"
    )
    return literature_record_data(record, can_update=_can_update(access))
