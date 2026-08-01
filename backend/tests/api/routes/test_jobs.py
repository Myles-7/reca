from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.api.routes import jobs as job_routes
from app.core.config import settings
from app.jobs import service
from app.models import Job, JobStatus, JobTaskType, ProcessingRun, UserCreate
from tests.utils.user import user_authentication_headers
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
        first_id = int(events[0]["event_id"])
        if last_event_id < first_id - 1 or last_event_id > int(events[-1]["event_id"]):
            return [], True
        return [
            event for event in events if int(event["event_id"]) > last_event_id
        ], False


class FakeDispatcher:
    def __init__(self) -> None:
        self.calls: list[uuid.UUID] = []

    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        assert task_id
        self.calls.append(job_id)


@pytest.fixture
def memory_events(monkeypatch: pytest.MonkeyPatch) -> MemoryEvents:
    events = MemoryEvents()
    monkeypatch.setattr(job_routes, "event_store", events)
    return events


@pytest.fixture
def fake_dispatcher(monkeypatch: pytest.MonkeyPatch) -> FakeDispatcher:
    dispatcher = FakeDispatcher()
    monkeypatch.setattr(job_routes, "dispatcher", dispatcher)
    return dispatcher


def create_project(client: TestClient, headers: dict[str, str]) -> uuid.UUID:
    response = client.post(
        "/api/v1/projects",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"name": "Job project", "project_type": "RESEARCH"},
    )
    assert response.status_code == 201
    return uuid.UUID(response.json()["data"]["id"])


def create_job(
    db: Session,
    *,
    actor_id: uuid.UUID,
    project_id: uuid.UUID,
    status: JobStatus = JobStatus.QUEUED,
    retryable: bool = True,
    retry_count: int = 0,
    max_retries: int = 3,
) -> Job:
    job = service.create_job(
        db,
        project_id=project_id,
        command=service.JobCreate(
            task_type=JobTaskType.DOCUMENT_PARSE,
            resource_type="artifact",
            resource_id=uuid.uuid4(),
            idempotency_key=str(uuid.uuid4()),
            requested_by_user_id=actor_id,
            retryable=retryable,
            max_retries=max_retries,
        ),
    )
    job.status = status
    job.retry_count = retry_count
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_job_list_detail_polling_and_no_generic_create(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    actor = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert actor is not None
    job = create_job(db, actor_id=actor.id, project_id=project_id)

    detail = client.get(f"/api/v1/jobs/{job.id}", headers=normal_user_token_headers)
    listing = client.get(
        f"/api/v1/projects/{project_id}/jobs", headers=normal_user_token_headers
    )
    no_generic_create = client.post(
        "/api/v1/jobs", headers=normal_user_token_headers, json={}
    )
    assert detail.status_code == listing.status_code == 200
    assert detail.json()["data"]["id"] == str(job.id)
    assert listing.json()["pagination"]["total"] == 1
    assert no_generic_create.status_code == 404


def test_retry_reuses_job_and_creates_new_attempt_only_when_worker_claims(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    fake_dispatcher: FakeDispatcher,
    memory_events: MemoryEvents,
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    actor = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert actor is not None
    job = create_job(db, actor_id=actor.id, project_id=project_id)
    first_claim = service.claim_job(
        db,
        job_id=job.id,
        worker_id="worker-1",
        engine="test",
        engine_version="1",
        store=memory_events,
    )
    assert first_claim is not None
    assert service.fail_job(
        db,
        job_id=job.id,
        run_id=first_claim.run_id,
        worker_id="worker-1",
        error_code="TEMPORARY_FAILURE",
        error_message="retry me",
        retryable=True,
        store=memory_events,
    )
    key = str(uuid.uuid4())
    first = client.post(
        f"/api/v1/jobs/{job.id}/retry",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
    )
    replay = client.post(
        f"/api/v1/jobs/{job.id}/retry",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
    )
    assert first.status_code == replay.status_code == 200
    assert first.json()["data"]["id"] == replay.json()["data"]["id"] == str(job.id)
    assert replay.json()["meta"]["idempotency_replayed"] is True
    assert first.json()["data"]["retry_count"] == 1
    assert fake_dispatcher.calls == [job.id]
    assert (
        len(db.exec(select(ProcessingRun).where(ProcessingRun.job_id == job.id)).all())
        == 1
    )

    second_claim = service.claim_job(
        db,
        job_id=job.id,
        worker_id="worker-2",
        engine="test",
        engine_version="1",
        store=memory_events,
    )
    assert second_claim is not None and second_claim.attempt_number == 2
    assert (
        len(db.exec(select(ProcessingRun).where(ProcessingRun.job_id == job.id)).all())
        == 2
    )


def test_cancel_replay_conflict_and_worker_safe_point(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_events: MemoryEvents,
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    actor = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert actor is not None
    job = create_job(db, actor_id=actor.id, project_id=project_id)
    key = str(uuid.uuid4())
    first = client.post(
        f"/api/v1/jobs/{job.id}/cancel",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json={"reason": "No longer needed"},
    )
    replay = client.post(
        f"/api/v1/jobs/{job.id}/cancel",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json={"reason": "No longer needed"},
    )
    conflict = client.post(
        f"/api/v1/jobs/{job.id}/cancel",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json={"reason": "Different reason"},
    )
    assert first.status_code == replay.status_code == 200
    assert replay.json()["meta"]["idempotency_replayed"] is True
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert (
        service.claim_job(
            db,
            job_id=job.id,
            worker_id="worker-1",
            engine="test",
            engine_version="1",
            store=memory_events,
        )
        is None
    )
    db.refresh(job)
    assert job.status == JobStatus.CANCELLED
    assert (
        db.exec(select(ProcessingRun).where(ProcessingRun.job_id == job.id)).all() == []
    )


def test_cross_project_job_and_sse_are_hidden_and_editor_policy_is_enforced(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_events: MemoryEvents,
) -> None:
    assert job_routes.event_store is memory_events
    project_id = create_project(client, normal_user_token_headers)
    actor = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert actor is not None
    job = create_job(
        db, actor_id=actor.id, project_id=project_id, status=JobStatus.COMPLETED
    )
    password = random_lower_string()
    outsider = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com", password=password
        ),
    )
    outsider_headers = user_authentication_headers(
        client=client, email=outsider.email, password=password
    )
    assert (
        client.get(f"/api/v1/jobs/{job.id}", headers=outsider_headers).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/jobs/{job.id}/events", headers=outsider_headers
        ).status_code
        == 404
    )

    add_reviewer = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"user_id": str(outsider.id), "role": "REVIEWER"},
    )
    assert add_reviewer.status_code == 201
    assert (
        client.get(f"/api/v1/jobs/{job.id}", headers=outsider_headers).status_code
        == 200
    )
    denied_cancel = client.post(
        f"/api/v1/jobs/{job.id}/cancel",
        headers={**outsider_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"reason": "reviewer cannot cancel"},
    )
    denied_retry = client.post(
        f"/api/v1/jobs/{job.id}/retry",
        headers={**outsider_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert denied_cancel.status_code == denied_retry.status_code == 403


def test_retry_cancel_guards_and_required_idempotency_key(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    fake_dispatcher: FakeDispatcher,
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    actor = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert actor is not None
    completed = create_job(
        db,
        actor_id=actor.id,
        project_id=project_id,
        status=JobStatus.COMPLETED,
        retryable=False,
    )
    exhausted = create_job(
        db,
        actor_id=actor.id,
        project_id=project_id,
        status=JobStatus.FAILED,
        retry_count=2,
        max_retries=2,
    )
    missing_key = client.post(
        f"/api/v1/jobs/{completed.id}/retry", headers=normal_user_token_headers
    )
    invalid_retry = client.post(
        f"/api/v1/jobs/{completed.id}/retry",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    invalid_cancel = client.post(
        f"/api/v1/jobs/{completed.id}/cancel",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"reason": "too late"},
    )
    exhausted_retry = client.post(
        f"/api/v1/jobs/{exhausted.id}/retry",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert missing_key.status_code == 400
    assert missing_key.json()["error"]["code"] == "MISSING_IDEMPOTENCY_KEY"
    assert invalid_retry.status_code == 409
    assert invalid_retry.json()["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert invalid_cancel.status_code == 409
    assert invalid_cancel.json()["error"]["code"] == "JOB_NOT_CANCELLABLE"
    assert exhausted_retry.status_code == 409
    assert exhausted_retry.json()["error"]["code"] == "JOB_RETRY_EXHAUSTED"
    assert fake_dispatcher.calls == []


def test_sse_reconnect_and_history_miss_return_contract_events(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_events: MemoryEvents,
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    actor = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert actor is not None
    job = create_job(db, actor_id=actor.id, project_id=project_id)
    memory_events.publish(
        job_id=job.id,
        event={
            "schema_version": "1.0",
            "event_type": "job.started",
            "job_id": str(job.id),
            "project_id": str(project_id),
            "status": "RUNNING",
            "progress_percent": 10,
            "current_step": "STARTING",
            "message": "Started",
            "payload": {},
            "occurred_at": "2026-08-01T00:00:00Z",
        },
    )
    job.status = JobStatus.COMPLETED
    db.add(job)
    db.commit()
    memory_events.publish(
        job_id=job.id,
        event={
            "schema_version": "1.0",
            "event_type": "job.completed",
            "job_id": str(job.id),
            "project_id": str(project_id),
            "status": "COMPLETED",
            "progress_percent": 100,
            "current_step": None,
            "message": "Completed",
            "payload": {},
            "occurred_at": "2026-08-01T00:00:01Z",
        },
    )
    resumed = client.get(
        f"/api/v1/jobs/{job.id}/events",
        headers={**normal_user_token_headers, "Last-Event-ID": "1"},
    )
    assert resumed.status_code == 200
    assert "event: job.completed" in resumed.text
    assert "event: job.started" not in resumed.text

    memory_events.events[job.id] = memory_events.events[job.id][1:]
    missed = client.get(
        f"/api/v1/jobs/{job.id}/events",
        headers={**normal_user_token_headers, "Last-Event-ID": "0"},
    )
    assert missed.status_code == 200
    assert "event: job.resync_required" in missed.text
    assert "EVENT_HISTORY_EXPIRED" in missed.text
    assert f"/api/v1/jobs/{job.id}" in missed.text


def test_sse_stops_when_postgres_is_terminal_even_if_terminal_event_is_missing(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = create_project(client, normal_user_token_headers)
    actor = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert actor is not None
    job = create_job(db, actor_id=actor.id, project_id=project_id)

    class TerminalEventMissingStore:
        def __init__(self) -> None:
            self.calls = 0

        def after(
            self, *, job_id: uuid.UUID, last_event_id: int | None
        ) -> tuple[list[dict[str, Any]], bool]:
            del last_event_id
            self.calls += 1
            if self.calls > 1:
                raise AssertionError("SSE did not refresh the PostgreSQL Job state")
            stored = db.get(Job, job_id)
            assert stored is not None
            stored.status = JobStatus.COMPLETED
            stored.progress_percent = 100
            db.add(stored)
            db.commit()
            return [], False

    store = TerminalEventMissingStore()
    monkeypatch.setattr(job_routes, "event_store", store)
    response = client.get(
        f"/api/v1/jobs/{job.id}/events", headers=normal_user_token_headers
    )
    assert response.status_code == 200
    assert response.text == ""
    assert store.calls == 1
