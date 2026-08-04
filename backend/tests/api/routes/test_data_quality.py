from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.adapters.storage import StorageError, StorageObjectExists
from app.api.routes import data_quality as data_quality_routes
from app.artifacts import service as artifact_service
from app.models import (
    Artifact,
    AuditLog,
    DataQualityIssue,
    DataQualityIssueStatus,
    DataQualityRun,
    DataQualityRunStatus,
    DatasetVersion,
    Job,
    JobStatus,
    JobTaskType,
    ProcessingRun,
    ProjectMember,
    ProjectMemberRole,
    User,
    UserCreate,
)
from app.workers import jobs as worker_jobs
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_lower_string


class MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_file_once(
        self,
        *,
        object_key: str,
        path: Path,
        content_sha256: str,
        size_bytes: int,
    ) -> None:
        content = path.read_bytes()
        if object_key in self.objects:
            raise StorageObjectExists("already exists")
        assert len(content) == size_bytes
        assert hashlib.sha256(content).hexdigest() == content_sha256
        self.objects[object_key] = content

    def download_to_path(self, *, object_key: str, path: Path) -> None:
        try:
            path.write_bytes(self.objects[object_key])
        except KeyError as exc:
            raise StorageError("missing") from exc

    def presign_download(self, *, object_key: str, expires_seconds: int) -> str:
        return f"https://example.test/{object_key}?expires={expires_seconds}"


class RecordingDispatcher:
    def __init__(self) -> None:
        self.calls: list[tuple[uuid.UUID, str]] = []

    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        self.calls.append((job_id, task_id))


@pytest.fixture
def quality_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[MemoryStorage, RecordingDispatcher]:
    storage = MemoryStorage()
    dispatcher = RecordingDispatcher()
    monkeypatch.setattr(artifact_service, "storage", storage)
    monkeypatch.setattr(data_quality_routes, "dispatcher", dispatcher)
    return storage, dispatcher


def _project(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.post(
        "/api/v1/projects",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"name": "Quality project", "project_type": "RESEARCH"},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json()["data"])


def _upload(
    client: TestClient,
    headers: dict[str, str],
    project_id: object,
    content: bytes,
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{project_id}/datasets",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        files={"file": ("quality.csv", content, "text/csv")},
        data={
            "name": "Quality fixture",
            "source_type": "USER_UPLOAD",
            "license_status": "UNKNOWN",
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json()["data"])


def _new_user(client: TestClient, db: Session) -> tuple[User, dict[str, str]]:
    password = random_lower_string()
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com",
            password=password,
        ),
    )
    headers = user_authentication_headers(
        client=client, email=user.email, password=password
    )
    return user, headers


def test_quality_job_api_worker_idempotency_review_and_isolation(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    quality_runtime: tuple[MemoryStorage, RecordingDispatcher],
) -> None:
    storage, dispatcher = quality_runtime
    project = _project(client, normal_user_token_headers)
    content = (
        b"id,age,visit_date,group,email\n"
        b"A1,20,2026-01-01,A,alpha@example.test\n"
        b"A1,150,invalid,A,beta@example.test\n"
        b"A3,22,2026-01-03,A,N/A\n"
        b"A4,23,2026-01-04,A,delta@example.test\n"
        b"A5,24,2026-01-05,A,echo@example.test\n"
        b"A6,25,2026-01-06,A,foxtrot@example.test\n"
        b"A7,26,2026-01-07,A,golf@example.test\n"
        b"A8,27,2026-01-08,A,hotel@example.test\n"
        b"A9,28,2026-01-09,A,india@example.test\n"
        b"A10,29,2026-01-10,B,juliet@example.test\n"
    )
    uploaded = _upload(client, normal_user_token_headers, project["id"], content)
    version = uploaded["version"]
    key = str(uuid.uuid4())
    request = {
        "rule_set": "RECA_P0_DEFAULT",
        "include_sensitive_field_detection": True,
    }
    first = client.post(
        f"/api/v1/dataset-versions/{version['id']}/quality-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json=request,
    )
    replay = client.post(
        f"/api/v1/dataset-versions/{version['id']}/quality-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json=request,
    )
    conflict = client.post(
        f"/api/v1/dataset-versions/{version['id']}/quality-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json={**request, "include_sensitive_field_detection": False},
    )

    assert first.status_code == replay.status_code == 202, first.text
    assert replay.json()["meta"]["idempotency_replayed"] is True
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert len(dispatcher.calls) == 1
    run_id = uuid.UUID(first.json()["data"]["run"]["id"])
    job_id = uuid.UUID(first.json()["data"]["job"]["id"])
    assert db.exec(select(DataQualityRun).where(DataQualityRun.id == run_id)).one()
    assert (
        db.exec(
            select(Job).where(
                Job.resource_type == "data_quality_run",
                Job.resource_id == run_id,
            )
        )
        .one()
        .id
        == job_id
    )

    executed = worker_jobs._execute_job(object(), str(job_id))
    assert executed == {"job_id": str(job_id), "claimed": True, "completed": True}
    db.expire_all()
    run = db.get(DataQualityRun, run_id)
    job = db.get(Job, job_id)
    version_model = db.get(DatasetVersion, uuid.UUID(str(version["id"])))
    artifact = db.get(Artifact, uuid.UUID(str(version["artifact_id"])))
    assert run is not None and run.status == DataQualityRunStatus.COMPLETED
    assert job is not None and job.status == JobStatus.COMPLETED
    assert version_model is not None and artifact is not None
    assert (
        version_model.data_hash
        == artifact.sha256
        == hashlib.sha256(content).hexdigest()
    )
    processing = db.exec(
        select(ProcessingRun).where(ProcessingRun.job_id == job_id)
    ).one()
    assert processing.status == JobStatus.COMPLETED
    metadata = processing.implementation_metadata or {}
    assert metadata["ruleset_hash"] == run.ruleset_hash
    assert metadata["input_data_hash"] == version_model.data_hash
    assert metadata["lazy"] is True
    assert metadata["coerce"] is False
    assert metadata["max_affected_rows"] == 100
    assert metadata["max_examples"] == 5

    run_response = client.get(
        f"/api/v1/data-quality-runs/{run_id}",
        headers=normal_user_token_headers,
    )
    issues_response = client.get(
        f"/api/v1/data-quality-runs/{run_id}/issues",
        headers=normal_user_token_headers,
        params={"page_size": 2},
    )
    assert run_response.status_code == issues_response.status_code == 200
    assert run_response.json()["data"]["status"] == "COMPLETED"
    assert issues_response.json()["pagination"]["total"] == run.issue_count
    assert len(issues_response.json()["data"]) == 2
    all_issues = db.exec(
        select(DataQualityIssue).where(DataQualityIssue.data_quality_run_id == run_id)
    ).all()
    assert all_issues
    assert all(len(issue.affected_rows or []) <= 100 for issue in all_issues)
    sensitive = [
        issue
        for issue in all_issues
        if issue.issue_type.value == "POSSIBLE_SENSITIVE_FIELD"
    ]
    assert sensitive
    assert all(
        set((issue.evidence or {}).get("examples", [])) <= {"[MASKED]"}
        for issue in sensitive
    )
    severity_filter = client.get(
        f"/api/v1/data-quality-runs/{run_id}/issues",
        headers=normal_user_token_headers,
        params={"severity": all_issues[0].severity.value},
    )
    assert severity_filter.status_code == 200
    assert all(
        issue["severity"] == all_issues[0].severity.value
        for issue in severity_filter.json()["data"]
    )

    issue_id = all_issues[0].id
    acknowledge_key = str(uuid.uuid4())
    acknowledged = client.post(
        f"/api/v1/data-quality-issues/{issue_id}/acknowledge",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": acknowledge_key,
        },
        json={"reason": "Reviewed against source"},
    )
    acknowledged_replay = client.post(
        f"/api/v1/data-quality-issues/{issue_id}/acknowledge",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": acknowledge_key,
        },
        json={"reason": "Reviewed against source"},
    )
    missing_reason = client.post(
        f"/api/v1/data-quality-issues/{issue_id}/ignore",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"reason": ""},
    )
    ignored = client.post(
        f"/api/v1/data-quality-issues/{issue_id}/ignore",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"reason": "Accepted limitation"},
    )
    assert acknowledged.status_code == acknowledged_replay.status_code == 200
    assert acknowledged_replay.json()["meta"]["idempotency_replayed"] is True
    assert missing_reason.status_code == 422
    assert ignored.status_code == 200
    assert ignored.json()["data"]["status"] == "IGNORED"
    db.expire_all()
    assert db.get(DataQualityIssue, issue_id).status == DataQualityIssueStatus.IGNORED  # type: ignore[union-attr]
    assert db.exec(
        select(AuditLog).where(
            AuditLog.object_id == issue_id,
            AuditLog.action == "DATA_QUALITY_ISSUE_IGNORED",
        )
    ).one()

    owner = db.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == uuid.UUID(str(project["id"])),
            ProjectMember.role == ProjectMemberRole.OWNER,
        )
    ).one()
    reviewer, reviewer_headers = _new_user(client, db)
    db.add(
        ProjectMember(
            project_id=uuid.UUID(str(project["id"])),
            user_id=reviewer.id,
            role=ProjectMemberRole.REVIEWER,
            invited_by=owner.user_id,
        )
    )
    db.commit()
    reviewer_scan = client.post(
        f"/api/v1/dataset-versions/{version['id']}/quality-runs",
        headers={
            **reviewer_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json=request,
    )
    assert reviewer_scan.status_code == 403
    reviewer_read = client.get(
        f"/api/v1/data-quality-runs/{run_id}/issues",
        headers=reviewer_headers,
    )
    reviewer_acknowledge = client.post(
        f"/api/v1/data-quality-issues/{all_issues[1].id}/acknowledge",
        headers={
            **reviewer_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"reason": "Reviewer confirmed the candidate"},
    )
    assert reviewer_read.status_code == 200
    assert reviewer_acknowledge.status_code == 200

    _, outsider_headers = _new_user(client, db)
    hidden = client.get(f"/api/v1/data-quality-runs/{run_id}", headers=outsider_headers)
    assert hidden.status_code == 404


def test_worker_detects_storage_hash_change_and_preserves_failed_facts(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    quality_runtime: tuple[MemoryStorage, RecordingDispatcher],
) -> None:
    storage, _ = quality_runtime
    project = _project(client, normal_user_token_headers)
    uploaded = _upload(
        client,
        normal_user_token_headers,
        project["id"],
        b"record_key,value\na,1\nb,2\n",
    )
    version = uploaded["version"]
    requested = client.post(
        f"/api/v1/dataset-versions/{version['id']}/quality-runs",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"rule_set": "RECA_P0_DEFAULT"},
    )
    assert requested.status_code == 202
    run_id = uuid.UUID(requested.json()["data"]["run"]["id"])
    job_id = uuid.UUID(requested.json()["data"]["job"]["id"])
    artifact = db.get(Artifact, uuid.UUID(str(version["artifact_id"])))
    assert artifact is not None
    storage.objects[artifact.storage_key] = b"record_key,value\na,999\n"

    with pytest.raises(Exception) as error:
        worker_jobs._execute_job(object(), str(job_id))
    assert getattr(error.value, "code", None) == "DATASET_HASH_MISMATCH"
    db.expire_all()
    run = db.get(DataQualityRun, run_id)
    job = db.get(Job, job_id)
    processing = db.exec(
        select(ProcessingRun).where(ProcessingRun.job_id == job_id)
    ).one()
    assert run is not None and run.status == DataQualityRunStatus.FAILED
    assert run.error_code == "DATASET_HASH_MISMATCH"
    assert job is not None and job.status == JobStatus.FAILED
    assert processing.status == JobStatus.FAILED
    assert (
        db.exec(
            select(DataQualityIssue).where(
                DataQualityIssue.data_quality_run_id == run_id
            )
        ).all()
        == []
    )
    assert job.task_type == JobTaskType.DATASET_PROFILE
