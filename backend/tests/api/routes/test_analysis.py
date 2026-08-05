import hashlib
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlmodel import Session, select

from app import crud
from app.adapters.storage import StorageError, StorageObjectExists
from app.analysis.service import AnalysisExecutionError
from app.artifacts import service as artifact_service
from app.jobs import service as job_service
from app.models import (
    AnalysisPlan,
    AnalysisResult,
    AnalysisRun,
    AnalysisRunStatus,
    Artifact,
    CodeArtifact,
    DatasetColumn,
    DatasetColumnConfirmationStatus,
    DatasetColumnType,
    DatasetVersion,
    DatasetVersionStatus,
    Job,
    JobStatus,
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
        except KeyError as error:
            raise StorageError("missing") from error

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
def analysis_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[MemoryStorage, RecordingDispatcher]:
    from app.api.routes import analysis as analysis_routes

    storage = MemoryStorage()
    dispatcher = RecordingDispatcher()
    monkeypatch.setattr(artifact_service, "storage", storage)
    monkeypatch.setattr(analysis_routes, "dispatcher", dispatcher)
    return storage, dispatcher


def _project(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.post(
        "/api/v1/projects",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"name": "Analysis project", "project_type": "RESEARCH"},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json()["data"])


def _user_headers(client: TestClient, db: Session) -> tuple[User, dict[str, str]]:
    password = random_lower_string()
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com", password=password
        ),
    )
    return user, user_authentication_headers(
        client=client, email=user.email, password=password
    )


def _add_member(
    client: TestClient,
    owner_headers: dict[str, str],
    project_id: str,
    user_id: uuid.UUID,
    role: str,
) -> None:
    response = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={**owner_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"user_id": str(user_id), "role": role},
    )
    assert response.status_code == 201, response.text


def _analysis_inputs(
    client: TestClient,
    db: Session,
    headers: dict[str, str],
    project_id: str,
) -> tuple[uuid.UUID, dict[str, Any]]:
    upload = client.post(
        f"/api/v1/projects/{project_id}/datasets",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        files={
            "file": (
                "analysis.csv",
                b"x,y,group\n1,2,A\n2,4,A\n3,6,B\n4,8,B\n5,10,B\n",
                "text/csv",
            )
        },
        data={
            "name": "Analysis source",
            "source_type": "USER_UPLOAD",
            "license_status": "UNKNOWN",
        },
    )
    assert upload.status_code == 201, upload.text
    uploaded = upload.json()["data"]
    version_id = uuid.UUID(uploaded["version"]["id"])
    columns = list(
        db.exec(
            select(DatasetColumn).where(DatasetColumn.dataset_version_id == version_id)
        )
    )
    by_name = {column.source_name: column for column in columns}
    for name in ("x", "y"):
        by_name[name].confirmed_type = DatasetColumnType.NUMERIC
        by_name[name].confirmation_status = DatasetColumnConfirmationStatus.CONFIRMED
        db.add(by_name[name])
    by_name["group"].confirmed_type = DatasetColumnType.CATEGORY
    by_name["group"].confirmation_status = DatasetColumnConfirmationStatus.CONFIRMED
    db.add(by_name["group"])
    db.commit()
    question = client.post(
        f"/api/v1/projects/{project_id}/research-questions",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"raw_input": "Is x associated with y?"},
    )
    assert question.status_code == 201, question.text
    question_version_id = question.json()["data"]["current_version"]["id"]
    ready = client.post(
        f"/api/v1/research-question-versions/{question_version_id}/ready",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"reason": "Analysis scope reviewed."},
    )
    assert ready.status_code == 200, ready.text
    requested = client.post(
        f"/api/v1/research-question-versions/{question_version_id}/approval-requests",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert requested.status_code == 201, requested.text
    approved = client.post(
        f"/api/v1/approvals/{requested.json()['data']['id']}/approve",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "decision_reason": "Research question confirmed.",
            "item_decisions": [],
        },
    )
    assert approved.status_code == 200, approved.text
    return uuid.UUID(question_version_id), {
        name: str(column.id) for name, column in by_name.items()
    }


def test_analysis_approval_worker_results_idempotency_and_invalidation(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    analysis_runtime: tuple[MemoryStorage, RecordingDispatcher],
) -> None:
    storage, dispatcher = analysis_runtime
    project = _project(client, normal_user_token_headers)
    question_version_id, columns = _analysis_inputs(
        client, db, normal_user_token_headers, project["id"]
    )
    dataset = client.get(
        f"/api/v1/projects/{project['id']}/datasets", headers=normal_user_token_headers
    ).json()["data"][0]
    version_id = dataset["current_version_id"]
    create = client.post(
        f"/api/v1/projects/{project['id']}/analysis-plans",
        headers=normal_user_token_headers,
        json={
            "research_question_version_id": str(question_version_id),
            "dataset_version_id": version_id,
            "analysis_goal": "CORRELATION",
            "method": "PEARSON_CORRELATION",
            "dependent_variable_ids": [columns["y"]],
            "independent_variable_ids": [columns["x"]],
            "control_variable_ids": [],
            "missing_data_policy": {"mode": "PAIRWISE_COMPLETE"},
            "parameters": {
                "confidence_level": 0.95,
                "assumption_confirmations": ["LINEARITY"],
            },
        },
    )
    assert create.status_code == 201, create.text
    plan_id = create.json()["data"]["id"]
    outsider, outsider_headers = _user_headers(client, db)
    assert (
        client.get(
            f"/api/v1/analysis-plans/{plan_id}", headers=outsider_headers
        ).status_code
        == 404
    )
    role_headers: dict[str, dict[str, str]] = {"OWNER": normal_user_token_headers}
    for role in ("EDITOR", "REVIEWER", "VIEWER"):
        user, headers = _user_headers(client, db)
        _add_member(client, normal_user_token_headers, project["id"], user.id, role)
        role_headers[role] = headers
    assert outsider.id != uuid.UUID(project["owner_id"])
    for headers in role_headers.values():
        assert (
            client.get(f"/api/v1/analysis-plans/{plan_id}", headers=headers).status_code
            == 200
        )
    validation = client.post(
        f"/api/v1/analysis-plans/{plan_id}/validate",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert validation.status_code == 200, validation.text
    assert validation.json()["data"]["status"] == "READY"
    approval_request = client.post(
        f"/api/v1/analysis-plans/{plan_id}/approval-requests",
        headers=normal_user_token_headers,
    )
    assert approval_request.status_code == 201, approval_request.text
    approval_id = approval_request.json()["data"]["approval_id"]
    unapproved = client.post(
        f"/api/v1/analysis-plans/{plan_id}/runs",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"run_reason": "before approval"},
    )
    assert unapproved.status_code == 409
    assert unapproved.json()["error"]["code"] == "APPROVAL_REQUIRED"
    approved = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"decision_reason": "Reviewed", "item_decisions": []},
    )
    assert approved.status_code == 200, approved.text
    for role in ("REVIEWER", "VIEWER"):
        denied = client.post(
            f"/api/v1/analysis-plans/{plan_id}/runs",
            headers={**role_headers[role], "Idempotency-Key": str(uuid.uuid4())},
            json={"run_reason": f"{role} must not execute"},
        )
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "PERMISSION_DENIED"
    key = str(uuid.uuid4())
    accepted = client.post(
        f"/api/v1/analysis-plans/{plan_id}/runs",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json={"run_reason": "approved correlation"},
    )
    replay = client.post(
        f"/api/v1/analysis-plans/{plan_id}/runs",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json={"run_reason": "approved correlation"},
    )
    assert accepted.status_code == replay.status_code == 202, accepted.text
    assert replay.json()["meta"]["idempotency_replayed"] is True
    assert len(dispatcher.calls) == 1
    run_id = uuid.UUID(accepted.json()["data"]["analysis_run"]["id"])
    job_id = uuid.UUID(accepted.json()["data"]["job"]["id"])
    assert worker_jobs._execute_job(object(), str(job_id))["completed"] is True
    db.expire_all()
    run = db.get(AnalysisRun, run_id)
    job = db.get(Job, job_id)
    assert run is not None and run.status == AnalysisRunStatus.COMPLETED
    assert job is not None and job.status == JobStatus.COMPLETED
    assert run.code_artifact_id is not None and run.log_artifact_id is not None
    assert db.get(CodeArtifact, run.code_artifact_id) is not None
    results = list(
        db.exec(select(AnalysisResult).where(AnalysisResult.analysis_run_id == run_id))
    )
    assert len(results) == 1
    assert results[0].payload["coefficient"] == pytest.approx(1.0)
    result_id = results[0].id
    db.add(
        AnalysisResult(
            project_id=run.project_id,
            analysis_run_id=run.id,
            result_key="second-primary",
            result_type=results[0].result_type,
            is_primary=True,
            payload={"coefficient": 0.5},
            result_hash="0" * 64,
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.expire_all()
    results = list(
        db.exec(select(AnalysisResult).where(AnalysisResult.analysis_run_id == run_id))
    )
    assert all(storage.objects.values())
    response = client.get(
        f"/api/v1/analysis-runs/{run_id}/results", headers=normal_user_token_headers
    )
    assert response.status_code == 200
    assert (
        response.json()["data"]["results"][0]["schema_version"] == "analysis-result/1.0"
    )
    results[0].payload = {"coefficient": 0.0}
    db.add(results[0])
    with pytest.raises(DBAPIError, match="immutable"):
        db.commit()
    db.rollback()

    cancel_request = client.post(
        f"/api/v1/analysis-plans/{plan_id}/runs",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"run_reason": "cancel before execution"},
    )
    assert cancel_request.status_code == 202, cancel_request.text
    cancelled_run_id = uuid.UUID(cancel_request.json()["data"]["analysis_run"]["id"])
    cancelled_job_id = uuid.UUID(cancel_request.json()["data"]["job"]["id"])
    cancel = client.post(
        f"/api/v1/jobs/{cancelled_job_id}/cancel",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"reason": "No longer required."},
    )
    assert cancel.status_code == 200, cancel.text
    assert worker_jobs._execute_job(object(), str(cancelled_job_id))["claimed"] is False
    db.expire_all()
    cancelled_run = db.get(AnalysisRun, cancelled_run_id)
    assert cancelled_run is not None
    assert cancelled_run.status == AnalysisRunStatus.CANCELLED

    stale_request = client.post(
        f"/api/v1/analysis-plans/{plan_id}/runs",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"run_reason": "worker loss reconciliation"},
    )
    assert stale_request.status_code == 202, stale_request.text
    stale_run_id = uuid.UUID(stale_request.json()["data"]["analysis_run"]["id"])
    stale_job_id = uuid.UUID(stale_request.json()["data"]["job"]["id"])
    claim = job_service.claim_job(
        db,
        job_id=stale_job_id,
        worker_id="lost-analysis-worker",
        engine="analysis-engine",
        engine_version="1.0.0",
    )
    assert claim is not None
    claimed_job = db.get(Job, stale_job_id)
    assert claimed_job is not None and claimed_job.last_heartbeat_at is not None
    assert (
        job_service.fail_stale_running_jobs(
            db,
            heartbeat_before=claimed_job.last_heartbeat_at + timedelta(seconds=1),
        )
        == 1
    )
    db.expire_all()
    stale_run = db.get(AnalysisRun, stale_run_id)
    assert stale_run is not None and stale_run.status == AnalysisRunStatus.FAILED
    assert stale_run.error_code == "JOB_TIMEOUT"
    assert not list(
        db.exec(
            select(AnalysisResult).where(AnalysisResult.analysis_run_id == stale_run_id)
        )
    )
    assert (
        db.exec(
            select(CodeArtifact).where(CodeArtifact.analysis_run_id == stale_run_id)
        ).first()
        is None
    )

    plan = db.get(AnalysisPlan, uuid.UUID(plan_id))
    assert plan is not None
    original_parameters = dict(plan.parameters)
    plan.parameters = {**original_parameters, "confidence_level": 0.9}
    db.add(plan)
    db.commit()
    stale = client.post(
        f"/api/v1/analysis-plans/{plan_id}/runs",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"run_reason": "stale approval must fail"},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "APPROVAL_STALE"
    plan.parameters = original_parameters
    db.add(plan)
    db.commit()

    x_column = db.get(DatasetColumn, uuid.UUID(columns["x"]))
    assert x_column is not None
    x_column.confirmation_status = DatasetColumnConfirmationStatus.UNCONFIRMED
    db.add(x_column)
    db.commit()
    unconfirmed = client.post(
        f"/api/v1/analysis-plans/{plan_id}/runs",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"run_reason": "unconfirmed column must fail"},
    )
    assert unconfirmed.status_code == 409
    assert unconfirmed.json()["error"]["code"] == "COLUMN_NOT_CONFIRMED"
    x_column.confirmation_status = DatasetColumnConfirmationStatus.CONFIRMED
    db.add(x_column)
    db.commit()

    version = db.get(DatasetVersion, uuid.UUID(version_id))
    assert version is not None
    version.status = DatasetVersionStatus.INVALIDATED
    db.add(version)
    db.commit()
    unavailable = client.post(
        f"/api/v1/analysis-plans/{plan_id}/runs",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"run_reason": "unavailable version must fail"},
    )
    assert unavailable.status_code == 409
    assert unavailable.json()["error"]["code"] == "DATASET_VERSION_NOT_AVAILABLE"
    version.status = DatasetVersionStatus.AVAILABLE
    db.add(version)
    db.commit()

    failed_request = client.post(
        f"/api/v1/analysis-plans/{plan_id}/runs",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"run_reason": "hash mismatch must fail atomically"},
    )
    assert failed_request.status_code == 202, failed_request.text
    failed_run_id = uuid.UUID(failed_request.json()["data"]["analysis_run"]["id"])
    failed_job_id = uuid.UUID(failed_request.json()["data"]["job"]["id"])
    source_artifact = db.get(Artifact, version.artifact_id)
    assert source_artifact is not None
    original_bytes = storage.objects[source_artifact.storage_key]
    storage.objects[source_artifact.storage_key] = b"corrupted"
    with pytest.raises(AnalysisExecutionError):
        worker_jobs._execute_job(object(), str(failed_job_id))
    storage.objects[source_artifact.storage_key] = original_bytes
    db.expire_all()
    failed_run = db.get(AnalysisRun, failed_run_id)
    assert failed_run is not None and failed_run.status == AnalysisRunStatus.FAILED
    assert not list(
        db.exec(
            select(AnalysisResult).where(
                AnalysisResult.analysis_run_id == failed_run_id
            )
        )
    )
    assert (
        db.exec(
            select(CodeArtifact).where(CodeArtifact.analysis_run_id == failed_run_id)
        ).first()
        is None
    )

    invalidated = client.post(
        f"/api/v1/analysis-runs/{run_id}/invalidate",
        headers=normal_user_token_headers,
        json={"reason": "Upstream coding issue confirmed."},
    )
    assert invalidated.status_code == 200, invalidated.text
    assert invalidated.json()["data"]["status"] == "INVALIDATED"
    assert (
        db.exec(select(AnalysisResult).where(AnalysisResult.analysis_run_id == run_id))
        .one()
        .id
        == result_id
    )
