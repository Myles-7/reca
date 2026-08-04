from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.adapters.model_provider import ModelProviderError
from app.adapters.storage import StorageError, StorageObjectExists
from app.artifacts import service as artifact_service
from app.cleaning.schemas import CleaningPlanSuggestionRequest
from app.cleaning.suggestion import suggest_plan
from app.core.config import settings
from app.models import (
    ApprovalRecord,
    Artifact,
    CleaningPlan,
    DataQualityRun,
    Dataset,
    DatasetVersion,
    DatasetVersionStatus,
    DataTransformation,
    Job,
    JobStatus,
    ModelInvocation,
    ModelInvocationStatus,
    User,
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


@pytest.fixture
def cleaning_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[MemoryStorage, RecordingDispatcher]:
    from app.api.routes import cleaning as cleaning_routes

    storage = MemoryStorage()
    dispatcher = RecordingDispatcher()
    monkeypatch.setattr(artifact_service, "storage", storage)
    monkeypatch.setattr(cleaning_routes, "dispatcher", dispatcher)
    return storage, dispatcher


def _project(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.post(
        "/api/v1/projects",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"name": "Cleaning project", "project_type": "RESEARCH"},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json()["data"])


def _upload(
    client: TestClient, headers: dict[str, str], project_id: object, content: bytes
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{project_id}/datasets",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        files={"file": ("cleaning.csv", content, "text/csv")},
        data={
            "name": "Cleaning source",
            "source_type": "USER_UPLOAD",
            "license_status": "UNKNOWN",
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json()["data"])


def test_cleaning_preview_approval_transform_idempotency_and_lineage(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    cleaning_runtime: tuple[MemoryStorage, RecordingDispatcher],
) -> None:
    storage, dispatcher = cleaning_runtime
    project = _project(client, normal_user_token_headers)
    source_bytes = (
        b"id,email,category,score\n"
        b"1,alpha@example.test,a,10\n"
        b"2,beta@example.test,B,bad\n"
        b'3,=HYPERLINK("https://bad.test"),a,30\n'
    )
    uploaded = _upload(client, normal_user_token_headers, project["id"], source_bytes)
    dataset_id = uuid.UUID(uploaded["dataset"]["id"])
    source_id = uuid.UUID(uploaded["version"]["id"])
    source_artifact_id = uuid.UUID(uploaded["version"]["artifact_id"])
    columns_response = client.get(
        f"/api/v1/dataset-versions/{source_id}/columns",
        headers=normal_user_token_headers,
    )
    columns = {item["source_name"]: item for item in columns_response.json()["data"]}
    actions = [
        {
            "action_type": "MAP_CATEGORY",
            "target_columns": [columns["category"]["id"]],
            "row_selector": {"selector_type": "ALL_ROWS"},
            "parameters": {"mapping": {"a": "A"}},
            "reason": "Normalize categories",
        },
        {
            "action_type": "CAST_TYPE",
            "target_columns": [columns["score"]["id"]],
            "row_selector": {"selector_type": "ALL_ROWS"},
            "parameters": {"target_type": "INTEGER", "on_invalid": "MARK_MISSING"},
            "reason": "Normalize score",
        },
        {
            "action_type": "RENAME_COLUMN",
            "target_columns": [columns["category"]["id"]],
            "row_selector": {"selector_type": "ALL_ROWS"},
            "parameters": {"new_name": "group"},
            "reason": "Use field dictionary name",
        },
    ]
    create_key = str(uuid.uuid4())
    created = client.post(
        f"/api/v1/dataset-versions/{source_id}/cleaning-plans",
        headers={**normal_user_token_headers, "Idempotency-Key": create_key},
        json={"title": "Normalize source", "actions": actions},
    )
    replay = client.post(
        f"/api/v1/dataset-versions/{source_id}/cleaning-plans",
        headers={**normal_user_token_headers, "Idempotency-Key": create_key},
        json={"title": "Normalize source", "actions": actions},
    )
    assert created.status_code == replay.status_code == 201, created.text
    assert replay.json()["meta"]["idempotency_replayed"] is True
    plan_id = uuid.UUID(created.json()["data"]["id"])
    source_artifact = db.get(Artifact, source_artifact_id)
    assert source_artifact is not None
    before_hash = source_artifact.sha256
    before_bytes = storage.objects[source_artifact.storage_key]

    preview = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/preview",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert preview.status_code == 200, preview.text
    preview_data = preview.json()["data"]
    assert preview_data["status"] == "READY"
    assert preview_data["preview_summary"]["ready_for_approval"] is True
    assert len(preview_data["preview_summary"]["sample_changes"]) <= 10
    assert storage.objects[source_artifact.storage_key] == before_bytes
    assert source_artifact.sha256 == before_hash
    assert db.exec(
        select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id)
    ).all() == [db.get(DatasetVersion, source_id)]

    approval_request = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/approval-requests",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert approval_request.status_code == 201, approval_request.text
    approval_id = uuid.UUID(approval_request.json()["data"]["approval_id"])
    unapproved = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/execute",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert unapproved.status_code == 409
    assert unapproved.json()["error"]["code"] == "APPROVAL_REQUIRED"
    approved = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"decision_reason": "Preview reviewed", "item_decisions": []},
    )
    assert approved.status_code == 200, approved.text

    execute_key = str(uuid.uuid4())
    accepted = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/execute",
        headers={**normal_user_token_headers, "Idempotency-Key": execute_key},
    )
    execute_replay = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/execute",
        headers={**normal_user_token_headers, "Idempotency-Key": execute_key},
    )
    assert accepted.status_code == execute_replay.status_code == 202, accepted.text
    assert execute_replay.json()["meta"]["idempotency_replayed"] is True
    assert len(dispatcher.calls) == 1
    transformation_id = uuid.UUID(accepted.json()["data"]["transformation"]["id"])
    job_id = uuid.UUID(accepted.json()["data"]["job"]["id"])
    executed = worker_jobs._execute_job(object(), str(job_id))
    assert executed == {"job_id": str(job_id), "claimed": True, "completed": True}

    db.expire_all()
    transformation = db.get(DataTransformation, transformation_id)
    job = db.get(Job, job_id)
    dataset = db.get(Dataset, dataset_id)
    assert transformation is not None and transformation.target_dataset_version_id
    assert transformation.status.value == "COMPLETED"
    assert job is not None and job.status == JobStatus.COMPLETED
    target = db.get(DatasetVersion, transformation.target_dataset_version_id)
    assert target is not None and target.status == DatasetVersionStatus.AVAILABLE
    assert target.parent_version_id == source_id
    assert target.artifact_id != source_artifact_id
    assert dataset is not None and dataset.current_version_id == target.id
    assert storage.objects[source_artifact.storage_key] == before_bytes
    output_artifact = db.get(Artifact, target.artifact_id)
    assert output_artifact is not None
    assert output_artifact.sha256 == target.data_hash
    assert b"'=HYPERLINK" in storage.objects[output_artifact.storage_key]
    assert db.exec(
        select(DataQualityRun).where(DataQualityRun.dataset_version_id == target.id)
    ).one()

    transformation_response = client.get(
        f"/api/v1/data-transformations/{transformation_id}",
        headers=normal_user_token_headers,
    )
    assert transformation_response.status_code == 200
    transformation_data = transformation_response.json()["data"]
    assert transformation_data["cleaning_plan_id"] == str(plan_id)
    assert transformation_data["source_dataset_version_id"] == str(source_id)
    assert transformation_data["target_dataset_version_id"] == str(target.id)
    assert transformation_data["output_artifact_id"] == str(target.artifact_id)
    assert "log_artifact_id" in transformation_data
    assert transformation_data["log_artifact_id"] is None

    history = client.get(
        f"/api/v1/datasets/{dataset_id}/versions",
        headers=normal_user_token_headers,
    )
    assert history.status_code == 200
    assert [item["version_number"] for item in history.json()["data"]] == [2, 1]

    comparison = client.get(
        f"/api/v1/datasets/{dataset_id}/version-comparison",
        headers=normal_user_token_headers,
        params={"base_version_id": source_id, "target_version_id": target.id},
    )
    assert comparison.status_code == 200, comparison.text
    assert comparison.json()["data"]["lineage"]["transformation_id"] == str(
        transformation.id
    )
    assert (
        len(
            db.exec(
                select(DataTransformation).where(
                    DataTransformation.cleaning_plan_id == plan_id
                )
            ).all()
        )
        == 1
    )


def test_worker_revalidates_persisted_parameters_and_leaves_no_available_target(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    cleaning_runtime: tuple[MemoryStorage, RecordingDispatcher],
) -> None:
    _ = cleaning_runtime
    project = _project(client, normal_user_token_headers)
    uploaded = _upload(
        client, normal_user_token_headers, project["id"], b"id,value\n1,a\n2,b\n"
    )
    source_id = uuid.UUID(uploaded["version"]["id"])
    dataset_id = uuid.UUID(uploaded["dataset"]["id"])
    columns = client.get(
        f"/api/v1/dataset-versions/{source_id}/columns",
        headers=normal_user_token_headers,
    ).json()["data"]
    value_id = next(item["id"] for item in columns if item["source_name"] == "value")
    created = client.post(
        f"/api/v1/dataset-versions/{source_id}/cleaning-plans",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "title": "Tamper check",
            "actions": [
                {
                    "action_type": "REPLACE_VALUE",
                    "target_columns": [value_id],
                    "row_selector": {
                        "selector_type": "VALUE_EQUALS",
                        "column_id": value_id,
                        "value": "a",
                    },
                    "parameters": {"replacement": "A"},
                    "reason": "Normalize",
                }
            ],
        },
    )
    plan_id = created.json()["data"]["id"]
    assert (
        client.post(
            f"/api/v1/cleaning-plans/{plan_id}/preview",
            headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        ).status_code
        == 200
    )
    requested = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/approval-requests",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    approval_id = requested.json()["data"]["approval_id"]
    assert (
        client.post(
            f"/api/v1/approvals/{approval_id}/approve",
            headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
            json={"decision_reason": "Reviewed", "item_decisions": []},
        ).status_code
        == 200
    )
    accepted = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/execute",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    transformation_id = uuid.UUID(accepted.json()["data"]["transformation"]["id"])
    job_id = uuid.UUID(accepted.json()["data"]["job"]["id"])
    transformation = db.get(DataTransformation, transformation_id)
    assert transformation is not None
    transformation.parameters_hash = "0" * 64
    db.add(transformation)
    db.commit()

    with pytest.raises(Exception) as execution_error:
        worker_jobs._execute_job(object(), str(job_id))
    assert (
        getattr(execution_error.value, "code", None)
        == "TRANSFORMATION_PARAMETERS_STALE"
    )
    db.expire_all()
    transformation = db.get(DataTransformation, transformation_id)
    dataset = db.get(Dataset, dataset_id)
    job = db.get(Job, job_id)
    assert transformation is not None and transformation.status.value == "FAILED"
    assert transformation.target_dataset_version_id is None
    assert dataset is not None and dataset.current_version_id == source_id
    assert job is not None and job.status == JobStatus.FAILED
    versions = db.exec(
        select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id)
    ).all()
    assert len(versions) == 1 and versions[0].status == DatasetVersionStatus.AVAILABLE


class FailingProvider:
    provider_name = "test-provider"
    model_name = "test-model"

    def generate(self, payload: object) -> dict[str, Any]:
        raise ModelProviderError(
            "MODEL_PROVIDER_UNAVAILABLE", "offline", retryable=True
        )


def test_ai_suggestion_invalid_output_and_provider_failure_are_fail_closed(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    cleaning_runtime: tuple[MemoryStorage, RecordingDispatcher],
) -> None:
    _ = cleaning_runtime
    project = _project(client, normal_user_token_headers)
    uploaded = _upload(
        client,
        normal_user_token_headers,
        project["id"],
        b"id,value\n1,same\n2,same\n3,same\n",
    )
    version_id = uuid.UUID(uploaded["version"]["id"])
    actor = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert actor is not None

    # A formal scan creates the required governed issue source.
    quality = client.post(
        f"/api/v1/dataset-versions/{version_id}/quality-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"rule_set": "RECA_P0_DEFAULT", "include_sensitive_field_detection": True},
    )
    assert quality.status_code == 202, quality.text
    worker_jobs._execute_job(object(), quality.json()["data"]["job"]["id"])

    invalid = client.post(
        f"/api/v1/dataset-versions/{version_id}/cleaning-plan-suggestions",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "mode": "MOCK",
            "fixture_output": {
                "title": "Unsafe",
                "actions": [
                    {
                        "action_type": "CREATE_DERIVED_COLUMN",
                        "target_columns": [str(uuid.uuid4())],
                        "parameters": {},
                        "reason": "expression",
                    }
                ],
            },
        },
    )
    assert invalid.status_code == 422, invalid.text
    assert invalid.json()["error"]["code"] in {
        "ACTION_NOT_AVAILABLE",
        "CLEANING_COLUMN_INVALID",
    }
    failed = db.exec(
        select(ModelInvocation).order_by(ModelInvocation.created_at.desc())
    ).first()
    assert failed is not None and failed.status == ModelInvocationStatus.FAILED
    assert (
        db.exec(
            select(CleaningPlan).where(
                CleaningPlan.source_model_invocation_id == failed.id
            )
        ).first()
        is None
    )

    with pytest.raises(Exception) as provider_error:
        suggest_plan(
            db,
            actor=actor,
            version_id=version_id,
            payload=CleaningPlanSuggestionRequest(mode="LIVE"),
            idempotency_key=str(uuid.uuid4()),
            provider=FailingProvider(),
        )
    assert getattr(provider_error.value, "code", None) == "MODEL_PROVIDER_UNAVAILABLE"
    latest = db.exec(
        select(ModelInvocation).order_by(ModelInvocation.created_at.desc())
    ).first()
    assert latest is not None and latest.status == ModelInvocationStatus.FAILED
    approval_count = len(
        db.exec(
            select(ApprovalRecord).where(
                ApprovalRecord.project_id == uuid.UUID(project["id"])
            )
        ).all()
    )
    assert approval_count == 0
