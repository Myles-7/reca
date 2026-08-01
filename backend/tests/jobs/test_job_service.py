from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from sqlmodel import Session, select

from app.core.config import settings
from app.jobs import service
from app.models import Job, JobStatus, JobTaskType, ProcessingRun, User
from app.projects.schemas import ProjectCreate
from app.projects.service import create_project
from tests.utils.utils import random_lower_string


class MemoryEvents:
    def __init__(self) -> None:
        self.events: dict[uuid.UUID, list[dict[str, Any]]] = {}
        self.sequence: dict[uuid.UUID, int] = {}

    def publish(self, *, job_id: uuid.UUID, event: dict[str, Any]) -> dict[str, Any]:
        event_id = self.sequence.get(job_id, 0) + 1
        self.sequence[job_id] = event_id
        stored = {**event, "event_id": event_id}
        self.events.setdefault(job_id, []).append(stored)
        return stored

    def after(
        self, *, job_id: uuid.UUID, last_event_id: int | None
    ) -> tuple[list[dict[str, Any]], bool]:
        events = self.events.get(job_id, [])
        if last_event_id is None:
            return events, False
        if not events:
            return [], True
        if last_event_id < int(events[0]["event_id"]) - 1:
            return [], True
        return [
            event for event in events if int(event["event_id"]) > last_event_id
        ], False


class FakeDispatcher:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[uuid.UUID, str]] = []

    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        self.calls.append((job_id, task_id))
        if self.fail:
            raise RuntimeError("broker unavailable")


def make_project_and_job(
    db: Session, *, actor: User, retryable: bool = True, max_retries: int = 3
) -> tuple[uuid.UUID, Job]:
    project_result = create_project(
        db,
        actor=actor,
        payload=ProjectCreate(
            name=f"Job project {random_lower_string()}", project_type="RESEARCH"
        ),
        idempotency_key=str(uuid.uuid4()),
    )
    assert project_result.data is not None
    project_id = uuid.UUID(str(project_result.data["id"]))
    job = service.create_job(
        db,
        project_id=project_id,
        command=service.JobCreate(
            task_type=JobTaskType.DOCUMENT_PARSE,
            resource_type="artifact",
            resource_id=uuid.uuid4(),
            idempotency_key=str(uuid.uuid4()),
            requested_by_user_id=actor.id,
            retryable=retryable,
            max_retries=max_retries,
        ),
    )
    db.commit()
    return project_id, job


def test_worker_claim_is_single_attempt_and_completion_is_authoritative(
    db: Session,
) -> None:
    superuser = db.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).one()
    events = MemoryEvents()
    _, job = make_project_and_job(db, actor=superuser)
    dispatched = service.dispatch_job(
        db, job_id=job.id, dispatcher=FakeDispatcher(), store=events
    )
    assert dispatched.status == JobStatus.QUEUED

    first = service.claim_job(
        db,
        job_id=job.id,
        worker_id="worker-1",
        engine="test-engine",
        engine_version="1.0",
        store=events,
    )
    duplicate = service.claim_job(
        db,
        job_id=job.id,
        worker_id="worker-2",
        engine="test-engine",
        engine_version="1.0",
        store=events,
    )
    assert first is not None
    assert duplicate is None
    assert service.update_progress(
        db,
        job_id=job.id,
        run_id=first.run_id,
        worker_id="worker-1",
        progress_percent=50,
        current_step="HALFWAY",
        completed_steps=1,
        total_steps=2,
        store=events,
    )
    output_id = uuid.uuid4()
    assert service.complete_job(
        db,
        job_id=job.id,
        run_id=first.run_id,
        worker_id="worker-1",
        output_object_type="artifact",
        output_object_id=output_id,
        store=events,
    )
    assert not service.complete_job(
        db,
        job_id=job.id,
        run_id=first.run_id,
        worker_id="worker-2",
        store=events,
    )
    stored = db.get(Job, job.id)
    assert stored is not None
    assert stored.status == JobStatus.COMPLETED
    assert stored.progress_percent == 100
    assert (
        len(db.exec(select(ProcessingRun).where(ProcessingRun.job_id == job.id)).all())
        == 1
    )


def test_dispatch_failure_and_stale_worker_recovery_preserve_postgres_truth(
    db: Session,
) -> None:
    superuser = db.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).one()
    events = MemoryEvents()
    _, failed_dispatch_job = make_project_and_job(db, actor=superuser)
    failed_dispatch = service.dispatch_job(
        db,
        job_id=failed_dispatch_job.id,
        dispatcher=FakeDispatcher(fail=True),
        store=events,
    )
    assert failed_dispatch.status == JobStatus.DISPATCH_FAILED
    assert failed_dispatch.error_code == "JOB_DISPATCH_FAILED"
    assert (
        db.exec(
            select(ProcessingRun).where(ProcessingRun.job_id == failed_dispatch.id)
        ).all()
        == []
    )

    _, stale_job = make_project_and_job(db, actor=superuser)
    service.dispatch_job(
        db, job_id=stale_job.id, dispatcher=FakeDispatcher(), store=events
    )
    claim = service.claim_job(
        db,
        job_id=stale_job.id,
        worker_id="worker-crashed",
        engine="test-engine",
        engine_version="1.0",
        store=events,
    )
    assert claim is not None
    stored = db.get(Job, stale_job.id)
    assert stored is not None and stored.last_heartbeat_at is not None
    cutoff = stored.last_heartbeat_at + timedelta(seconds=1)
    assert (
        service.fail_stale_running_jobs(db, heartbeat_before=cutoff, store=events) >= 1
    )
    db.refresh(stored)
    run = db.get(ProcessingRun, claim.run_id)
    assert stored.status == JobStatus.FAILED
    assert stored.error_code == "JOB_TIMEOUT"
    assert run is not None and run.status == JobStatus.FAILED
