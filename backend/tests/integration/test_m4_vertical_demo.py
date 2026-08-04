from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.adapters.storage import StorageError, StorageObjectExists
from app.artifacts import service as artifact_service
from app.models import (
    Artifact,
    DataQualityIssue,
    DataQualityRun,
    Dataset,
    DatasetVersion,
    DatasetVersionStatus,
    DataTransformation,
    Job,
    JobStatus,
)
from app.workers import jobs as worker_jobs


class MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_file_once(
        self, *, object_key: str, path: Path, content_sha256: str, size_bytes: int
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

    def delete_object(self, *, object_key: str) -> None:
        self.objects.pop(object_key, None)

    def presign_download(self, *, object_key: str, expires_seconds: int) -> str:
        return f"https://example.test/{object_key}?expires={expires_seconds}"


class RecordingDispatcher:
    def __init__(self) -> None:
        self.calls: list[tuple[uuid.UUID, str]] = []

    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        self.calls.append((job_id, task_id))


def key() -> str:
    return str(uuid.uuid4())


def test_m4_real_api_csv_quality_cleaning_approval_and_lineage(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.routes import cleaning as cleaning_routes
    from app.api.routes import data_quality as quality_routes

    storage = MemoryStorage()
    dispatcher = RecordingDispatcher()
    monkeypatch.setattr(artifact_service, "storage", storage)
    monkeypatch.setattr(cleaning_routes, "dispatcher", dispatcher)
    monkeypatch.setattr(quality_routes, "dispatcher", dispatcher)

    project_response = client.post(
        "/api/v1/projects",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
        json={"name": "M4 vertical project", "project_type": "RESEARCH"},
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["data"]["id"]
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
    upload = client.post(
        f"/api/v1/projects/{project_id}/datasets",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
        files={"file": ("m4-stage5.csv", content, "text/csv")},
        data={
            "name": "M4 source",
            "source_type": "USER_UPLOAD",
            "license_status": "UNKNOWN",
        },
    )
    assert upload.status_code == 201, upload.text
    uploaded = upload.json()["data"]
    dataset_id = uploaded["dataset"]["id"]
    source_version_id = uploaded["version"]["id"]
    assert uploaded["version"]["status"] == "AVAILABLE"
    assert uploaded["version"]["data_hash"] == hashlib.sha256(content).hexdigest()

    identity = client.patch(
        f"/api/v1/datasets/{dataset_id}",
        headers={**normal_user_token_headers, "If-Match": '"1"'},
        json={
            "description": "Reviewed Stage 5 dataset identity.",
            "publisher": "RECA acceptance",
            "license_name": "Test-only fixture terms",
        },
    )
    assert identity.status_code == 200, identity.text
    assert identity.json()["data"]["lock_version"] == 2

    columns_response = client.get(
        f"/api/v1/dataset-versions/{source_version_id}/columns",
        headers=normal_user_token_headers,
    )
    assert columns_response.status_code == 200, columns_response.text
    columns = {item["source_name"]: item for item in columns_response.json()["data"]}
    confirm = client.patch(
        f"/api/v1/dataset-columns/{columns['age']['id']}",
        headers={**normal_user_token_headers, "If-Match": '"1"'},
        json={
            "display_name": "Participant age",
            "confirmed_type": "INTEGER",
            "confirmation_status": "CONFIRMED",
        },
    )
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["data"]["confirmation_status"] == "CONFIRMED"

    quality_key = key()
    quality = client.post(
        f"/api/v1/dataset-versions/{source_version_id}/quality-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": quality_key},
        json={
            "rule_set": "RECA_P0_DEFAULT",
            "include_sensitive_field_detection": True,
        },
    )
    quality_replay = client.post(
        f"/api/v1/dataset-versions/{source_version_id}/quality-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": quality_key},
        json={
            "rule_set": "RECA_P0_DEFAULT",
            "include_sensitive_field_detection": True,
        },
    )
    assert quality.status_code == quality_replay.status_code == 202
    assert quality_replay.json()["meta"]["idempotency_replayed"] is True
    quality_run_id = quality.json()["data"]["run"]["id"]
    quality_job_id = quality.json()["data"]["job"]["id"]
    assert worker_jobs._execute_job(object(), quality_job_id)["completed"] is True

    issues_response = client.get(
        f"/api/v1/data-quality-runs/{quality_run_id}/issues",
        headers=normal_user_token_headers,
        params={"page_size": 100},
    )
    assert issues_response.status_code == 200, issues_response.text
    issues = issues_response.json()["data"]
    issue_types = {item["issue_type"] for item in issues}
    assert "POSSIBLE_SENSITIVE_FIELD" in issue_types
    assert {"MISSING_VALUE", "DUPLICATE_ID", "EXTREME_VALUE"} & issue_types
    sensitive = [
        item for item in issues if item["issue_type"] == "POSSIBLE_SENSITIVE_FIELD"
    ]
    assert sensitive
    assert all(
        set(item["evidence"].get("examples", [])) <= {"[MASKED]"} for item in sensitive
    )

    actions = [
        {
            "action_type": "MAP_CATEGORY",
            "target_columns": [columns["group"]["id"]],
            "row_selector": {"selector_type": "ALL_ROWS"},
            "parameters": {"mapping": {"A": "Group A", "B": "Group B"}},
            "reason": "Use the reviewed category labels.",
            "source_issue_ids": [],
        }
    ]
    plan = client.post(
        f"/api/v1/dataset-versions/{source_version_id}/cleaning-plans",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
        json={"title": "Normalize group labels", "actions": actions},
    )
    assert plan.status_code == 201, plan.text
    plan_id = plan.json()["data"]["id"]
    preview = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/preview",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["data"]["status"] == "READY"
    assert preview.json()["data"]["preview_summary"]["ready_for_approval"] is True

    requested = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/approval-requests",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
    )
    assert requested.status_code == 201, requested.text
    approval_id = requested.json()["data"]["approval_id"]
    unapproved = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/execute",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
    )
    assert unapproved.status_code == 409
    assert unapproved.json()["error"]["code"] == "APPROVAL_REQUIRED"
    approved = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
        json={
            "decision_reason": "Preview and input hash reviewed",
            "item_decisions": [],
        },
    )
    assert approved.status_code == 200, approved.text

    execute_key = key()
    accepted = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/execute",
        headers={**normal_user_token_headers, "Idempotency-Key": execute_key},
    )
    replayed = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/execute",
        headers={**normal_user_token_headers, "Idempotency-Key": execute_key},
    )
    assert accepted.status_code == replayed.status_code == 202, accepted.text
    assert replayed.json()["meta"]["idempotency_replayed"] is True
    transformation_id = accepted.json()["data"]["transformation"]["id"]
    transformation_job_id = accepted.json()["data"]["job"]["id"]
    assert (
        worker_jobs._execute_job(object(), transformation_job_id)["completed"] is True
    )

    db.expire_all()
    transformation = db.get(DataTransformation, uuid.UUID(transformation_id))
    job = db.get(Job, uuid.UUID(transformation_job_id))
    dataset = db.get(Dataset, uuid.UUID(dataset_id))
    assert transformation is not None and transformation.target_dataset_version_id
    assert transformation.status.value == "COMPLETED"
    assert job is not None and job.status == JobStatus.COMPLETED
    target = db.get(DatasetVersion, transformation.target_dataset_version_id)
    assert target is not None and target.status == DatasetVersionStatus.AVAILABLE
    assert target.parent_version_id == uuid.UUID(source_version_id)
    assert dataset is not None and dataset.current_version_id == target.id
    assert db.exec(
        select(DataQualityRun).where(DataQualityRun.dataset_version_id == target.id)
    ).one()
    assert db.exec(
        select(DataQualityIssue).where(
            DataQualityIssue.data_quality_run_id == uuid.UUID(quality_run_id)
        )
    ).all()

    comparison = client.get(
        f"/api/v1/datasets/{dataset_id}/version-comparison",
        headers=normal_user_token_headers,
        params={
            "base_version_id": source_version_id,
            "target_version_id": str(target.id),
        },
    )
    assert comparison.status_code == 200, comparison.text
    lineage: dict[str, Any] = comparison.json()["data"]["lineage"]
    assert lineage["parent_version_id"] == source_version_id
    assert lineage["transformation_id"] == transformation_id
    source_artifact = db.get(Artifact, uuid.UUID(uploaded["version"]["artifact_id"]))
    assert source_artifact is not None
    assert storage.objects[source_artifact.storage_key] == content
