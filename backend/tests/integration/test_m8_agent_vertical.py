from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.adapters.storage import StorageError, StorageObjectExists
from app.agent_runtime import orchestrator_service, tool_gateway
from app.api.routes import agent_runs as agent_routes
from app.api.routes import cleaning as cleaning_routes
from app.artifacts import service as artifact_service
from app.models import (
    AgentEvent,
    AgentEventType,
    AgentRun,
    AgentRunStatus,
    ApprovalRecord,
    ApprovalStatus,
    Dataset,
    DatasetVersion,
    DatasetVersionStatus,
    DataTransformation,
    Job,
    JobStatus,
    ModelInvocation,
    ToolCall,
    ToolCallStatus,
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


def execute(job_id: uuid.UUID | str) -> dict[str, object]:
    return worker_jobs._execute_job(object(), str(job_id))


def test_m8_recorded_agent_quality_approval_resume_and_transformation(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = MemoryStorage()
    dispatcher = RecordingDispatcher()
    monkeypatch.setattr(artifact_service, "storage", storage)
    monkeypatch.setattr(agent_routes, "dispatcher", dispatcher)
    monkeypatch.setattr(cleaning_routes, "dispatcher", dispatcher)
    monkeypatch.setattr(tool_gateway, "default_dispatcher", dispatcher)
    monkeypatch.setattr(orchestrator_service, "default_dispatcher", dispatcher)

    project_response = client.post(
        "/api/v1/projects",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
        json={"name": "M8 governed vertical", "project_type": "RESEARCH"},
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["data"]["id"]
    content = (
        b"id,age,group\n"
        b"A1,20,A\n"
        b"A2,21,A\n"
        b"A3,22,B\n"
        b"A4,23,B\n"
        b"A5,24,A\n"
        b"A6,25,A\n"
        b"A7,26,B\n"
        b"A8,27,B\n"
        b"A9,28,A\n"
        b"A10,29,B\n"
    )
    upload = client.post(
        f"/api/v1/projects/{project_id}/datasets",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
        files={"file": ("m8-agent.csv", content, "text/csv")},
        data={
            "name": "M8 source",
            "source_type": "USER_UPLOAD",
            "license_status": "UNKNOWN",
        },
    )
    assert upload.status_code == 201, upload.text
    dataset_id = upload.json()["data"]["dataset"]["id"]
    source_version_id = upload.json()["data"]["version"]["id"]
    columns_response = client.get(
        f"/api/v1/dataset-versions/{source_version_id}/columns",
        headers=normal_user_token_headers,
    )
    columns = {item["source_name"]: item for item in columns_response.json()["data"]}

    profile_agent = client.post(
        f"/api/v1/projects/{project_id}/agent-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
        json={
            "goal": f"Profile dataset {source_version_id}",
            "mode": "PLAN_AND_EXPLAIN",
            "allow_tool_calls": True,
        },
    )
    assert profile_agent.status_code == 202, profile_agent.text
    profile_run_id = uuid.UUID(profile_agent.json()["data"]["id"])
    profile_agent_job_id = uuid.UUID(profile_agent.json()["data"]["job"]["id"])
    assert execute(profile_agent_job_id)["completed"] is True
    db.expire_all()
    profile_run = db.get(AgentRun, profile_run_id)
    profile_call = db.exec(
        select(ToolCall).where(
            ToolCall.agent_run_id == profile_run_id,
            ToolCall.tool_name == "profile_dataset",
        )
    ).one()
    assert profile_run is not None and profile_run.status == AgentRunStatus.COMPLETED
    assert profile_call.status == ToolCallStatus.COMPLETED
    assert profile_call.job_id is not None
    assert execute(profile_call.job_id)["completed"] is True

    actions = [
        {
            "action_type": "MAP_CATEGORY",
            "target_columns": [columns["group"]["id"]],
            "row_selector": {"selector_type": "ALL_ROWS"},
            "parameters": {"mapping": {"A": "Group A", "B": "Group B"}},
            "reason": "Use reviewed group labels.",
            "source_issue_ids": [],
        }
    ]
    plan = client.post(
        f"/api/v1/dataset-versions/{source_version_id}/cleaning-plans",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
        json={"title": "Normalize groups", "actions": actions},
    )
    assert plan.status_code == 201, plan.text
    plan_id = plan.json()["data"]["id"]
    preview = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/preview",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
    )
    assert preview.status_code == 200, preview.text
    requested = client.post(
        f"/api/v1/cleaning-plans/{plan_id}/approval-requests",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
    )
    assert requested.status_code == 201, requested.text
    approval_id = uuid.UUID(requested.json()["data"]["approval_id"])

    cleaning_agent = client.post(
        f"/api/v1/projects/{project_id}/agent-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
        json={
            "goal": f"Apply approved cleaning plan {plan_id}",
            "mode": "PLAN_AND_EXPLAIN",
            "allow_tool_calls": True,
        },
    )
    assert cleaning_agent.status_code == 202, cleaning_agent.text
    cleaning_run_id = uuid.UUID(cleaning_agent.json()["data"]["id"])
    initial_job_id = uuid.UUID(cleaning_agent.json()["data"]["job"]["id"])
    assert execute(initial_job_id)["completed"] is True
    db.expire_all()
    cleaning_run = db.get(AgentRun, cleaning_run_id)
    cleaning_call = db.exec(
        select(ToolCall).where(
            ToolCall.agent_run_id == cleaning_run_id,
            ToolCall.tool_name == "apply_approved_transformations",
        )
    ).one()
    cleaning_call_id = cleaning_call.id
    assert cleaning_run is not None
    assert cleaning_run.status == AgentRunStatus.WAITING_APPROVAL
    assert cleaning_call.status == ToolCallStatus.WAITING_APPROVAL
    assert cleaning_call.approval_id == approval_id
    checkpoint = db.exec(
        select(AgentEvent).where(
            AgentEvent.agent_run_id == cleaning_run_id,
            AgentEvent.event_type == AgentEventType.RUNTIME_CHECKPOINT,
        )
    ).one()
    checkpoint_text = str(checkpoint.safe_summary).casefold()
    checkpoint_attributes = checkpoint.safe_summary["attributes"]
    assert "deterministic_rebuild" in checkpoint_text
    assert set(checkpoint_attributes) == {
        "approval_id",
        "approval_payload_hash",
        "checkpoint_schema",
        "expires_at",
        "prompt_id",
        "prompt_version",
        "registry_version",
        "resume_strategy",
        "sdk_version",
        "snapshot_hash",
        "tool_call_id",
        "tool_input_hash",
        "tool_name",
        "tool_version",
    }
    assert not any(
        forbidden in checkpoint_text
        for forbidden in (
            "authorization",
            "instructions",
            "prompt_text",
            "run_state",
            "secret",
            "tool_arguments",
        )
    )

    approved = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
        json={
            "decision_reason": "Reviewed preview and source hashes",
            "item_decisions": [],
        },
    )
    assert approved.status_code == 200, approved.text
    db.expire_all()
    approval = db.get(ApprovalRecord, approval_id)
    cleaning_run = db.get(AgentRun, cleaning_run_id)
    assert approval is not None and approval.decision_by_user_id is not None
    assert cleaning_run is not None and cleaning_run.job_id != initial_job_id
    resume_job_id = cleaning_run.job_id
    assert resume_job_id is not None
    resume_jobs = db.exec(
        select(Job).where(
            Job.project_id == uuid.UUID(project_id),
            Job.resource_type == "agent_run",
            Job.resource_id == cleaning_run_id,
        )
    ).all()
    assert len(resume_jobs) == 2
    orchestrator_service.approval_resume_post_commit(
        approval_id=approval_id, decision=ApprovalStatus.APPROVED
    )()
    duplicate_resume_jobs = db.exec(
        select(Job).where(
            Job.project_id == uuid.UUID(project_id),
            Job.resource_type == "agent_run",
            Job.resource_id == cleaning_run_id,
        )
    ).all()
    assert len(duplicate_resume_jobs) == 2
    assert execute(resume_job_id)["completed"] is True

    db.expire_all()
    cleaning_run = db.get(AgentRun, cleaning_run_id)
    running_cleaning_call = db.get(ToolCall, cleaning_call_id)
    assert (
        cleaning_run is not None and cleaning_run.status == AgentRunStatus.CALLING_TOOL
    )
    assert (
        running_cleaning_call is not None
        and running_cleaning_call.status == ToolCallStatus.RUNNING
    )
    assert running_cleaning_call.job_id is not None
    transformation_job_id = running_cleaning_call.job_id
    transformation_id = running_cleaning_call.output_object_id
    assert transformation_id is not None
    assert execute(transformation_job_id)["completed"] is True

    db.expire_all()
    cleaning_run = db.get(AgentRun, cleaning_run_id)
    completed_cleaning_call = db.get(ToolCall, cleaning_call_id)
    assert cleaning_run is not None and cleaning_run.status == AgentRunStatus.REVIEWING
    assert (
        completed_cleaning_call is not None
        and completed_cleaning_call.status == ToolCallStatus.COMPLETED
    )
    final_agent_job_id = cleaning_run.job_id
    assert final_agent_job_id is not None and final_agent_job_id != resume_job_id
    assert execute(final_agent_job_id)["completed"] is True
    assert execute(transformation_job_id)["claimed"] is False
    assert execute(final_agent_job_id)["claimed"] is False

    db.expire_all()
    cleaning_run = db.get(AgentRun, cleaning_run_id)
    transformation = db.get(DataTransformation, transformation_id)
    dataset = db.get(Dataset, uuid.UUID(dataset_id))
    assert cleaning_run is not None and cleaning_run.status == AgentRunStatus.COMPLETED
    assert transformation is not None and transformation.target_dataset_version_id
    target = db.get(DatasetVersion, transformation.target_dataset_version_id)
    assert target is not None and target.status == DatasetVersionStatus.AVAILABLE
    assert dataset is not None and dataset.current_version_id == target.id
    invocations = sorted(
        db.exec(
            select(ModelInvocation).where(
                ModelInvocation.agent_run_id == cleaning_run_id
            )
        ).all(),
        key=lambda item: item.created_at,
    )
    assert len(invocations) == 2
    assert invocations[0].tool_call_id is None
    assert invocations[1].tool_call_id == cleaning_call_id
    assert all(
        item.redaction_policy_version == "m8-trace-redaction-1.0"
        for item in invocations
    )
    transformation_jobs = db.exec(
        select(Job).where(
            Job.project_id == uuid.UUID(project_id),
            Job.resource_type == "data_transformation",
            Job.resource_id == transformation.id,
        )
    ).all()
    assert len(transformation_jobs) == 1
    assert transformation_jobs[0].status == JobStatus.COMPLETED

    rejected_plan = client.post(
        f"/api/v1/dataset-versions/{source_version_id}/cleaning-plans",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
        json={"title": "Rejected normalization", "actions": actions},
    )
    assert rejected_plan.status_code == 201, rejected_plan.text
    rejected_plan_id = rejected_plan.json()["data"]["id"]
    rejected_preview = client.post(
        f"/api/v1/cleaning-plans/{rejected_plan_id}/preview",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
    )
    assert rejected_preview.status_code == 200, rejected_preview.text
    rejected_request = client.post(
        f"/api/v1/cleaning-plans/{rejected_plan_id}/approval-requests",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
    )
    assert rejected_request.status_code == 201, rejected_request.text
    rejected_approval_id = uuid.UUID(rejected_request.json()["data"]["approval_id"])
    rejected_agent = client.post(
        f"/api/v1/projects/{project_id}/agent-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
        json={
            "goal": f"Apply approved cleaning plan {rejected_plan_id}",
            "mode": "PLAN_AND_EXPLAIN",
            "allow_tool_calls": True,
        },
    )
    assert rejected_agent.status_code == 202, rejected_agent.text
    rejected_run_id = uuid.UUID(rejected_agent.json()["data"]["id"])
    rejected_initial_job_id = uuid.UUID(rejected_agent.json()["data"]["job"]["id"])
    assert execute(rejected_initial_job_id)["completed"] is True
    rejected = client.post(
        f"/api/v1/approvals/{rejected_approval_id}/reject",
        headers={**normal_user_token_headers, "Idempotency-Key": key()},
        json={"decision_reason": "Preview rejected", "item_decisions": []},
    )
    assert rejected.status_code == 200, rejected.text
    db.expire_all()
    rejected_run = db.get(AgentRun, rejected_run_id)
    rejected_call = db.exec(
        select(ToolCall).where(
            ToolCall.agent_run_id == rejected_run_id,
            ToolCall.tool_name == "apply_approved_transformations",
        )
    ).one()
    assert rejected_run is not None and rejected_run.status == AgentRunStatus.FAILED
    assert rejected_run.failure_code == "APPROVAL_REJECTED"
    assert rejected_call.status == ToolCallStatus.DENIED
    assert rejected_call.error_code == "APPROVAL_REJECTED"
    rejected_agent_jobs = db.exec(
        select(Job).where(
            Job.project_id == uuid.UUID(project_id),
            Job.resource_type == "agent_run",
            Job.resource_id == rejected_run_id,
        )
    ).all()
    assert len(rejected_agent_jobs) == 1
    transformations = db.exec(
        select(DataTransformation).where(
            DataTransformation.project_id == uuid.UUID(project_id)
        )
    ).all()
    assert len(transformations) == 1
