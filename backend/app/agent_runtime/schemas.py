from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import (
    AgentRunStatus,
    ModelDataAccessLevel,
    ProjectStage,
    ToolCallStatus,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SafeSummary(StrictModel):
    kind: str = Field(max_length=100)
    text: str | None = Field(default=None, max_length=500)
    attributes: dict[str, str | int | bool | None] = Field(default_factory=dict)


class AgentRunCreate(StrictModel):
    project_id: uuid.UUID
    safe_input_summary: SafeSummary
    idempotency_key: str = Field(min_length=1, max_length=255)
    request_id: str | None = Field(default=None, max_length=64)
    correlation_id: str | None = Field(default=None, max_length=64)
    max_turns: int = Field(default=12, ge=1, le=100)
    max_tool_calls: int = Field(default=24, ge=0, le=200)
    retry_of_agent_run_id: uuid.UUID | None = None


class AgentRunView(StrictModel):
    id: uuid.UUID
    project_id: uuid.UUID
    status: AgentRunStatus
    lock_version: int
    snapshot_hash: str
    safe_snapshot_summary: dict[str, Any]
    allowed_actions: list[str]
    failure_code: str | None
    created_at: datetime
    completed_at: datetime | None
    idempotency_replayed: bool = False


class ToolCallRequest(StrictModel):
    agent_run_id: uuid.UUID
    tool_name: str = Field(min_length=1, max_length=100)
    tool_version: str = Field(default="1.0", max_length=50)
    safe_input_summary: SafeSummary
    source_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)
    source_hashes: dict[str, str] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=1, max_length=255)
    request_id: str | None = Field(default=None, max_length=64)
    retry_of_tool_call_id: uuid.UUID | None = None
    policy_arguments: dict[str, Any] | None = Field(default=None, exclude=True)


class ToolCallView(StrictModel):
    id: uuid.UUID
    project_id: uuid.UUID
    agent_run_id: uuid.UUID
    tool_name: str
    tool_version: str
    status: ToolCallStatus
    allowed_actions: list[str]
    error_code: str | None
    retryable: bool
    idempotency_replayed: bool = False


class ProjectContextSnapshot(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    revision: int = Field(ge=1)
    project_id: uuid.UUID
    project_name: str
    project_stage: ProjectStage
    project_status: str
    source_object_versions: dict[str, str]
    available_resources: dict[str, list[str]]
    pending_approval_ids: list[uuid.UUID]
    blocking_issues: list[str]
    allowed_next_actions: list[str]
    permissions: list[str]
    read_scopes: list[str]
    degraded: bool = False
    degradation_reason: str | None = None
    generated_at: datetime
    canonical_hash: str
    safe_snapshot_summary: dict[str, Any]


class StageResolution(StrictModel):
    project_id: uuid.UUID
    current_stage: ProjectStage | None
    blockers: list[str]
    pending_approval_ids: list[uuid.UUID]
    allowed_next_actions: list[str]
    candidate_tools: list[str]
    reason_codes: list[str]
    source_object_versions: dict[str, str]
    fail_closed: bool


class ToolInput(StrictModel):
    query: str | None = Field(default=None, max_length=500)
    source_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)
    options: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class ProfileDatasetInput(StrictModel):
    dataset_version_id: uuid.UUID
    rule_set: Literal["RECA_P0_DEFAULT"] = "RECA_P0_DEFAULT"


class ApplyApprovedTransformationsInput(StrictModel):
    cleaning_plan_id: uuid.UUID


class ToolOutput(StrictModel):
    tool_name: str
    tool_version: str
    status: Literal["COMPLETED", "FAILED", "DENIED", "WAITING_APPROVAL"]
    result_summary: dict[str, Any] = Field(default_factory=dict)
    output_object_ids: list[uuid.UUID] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    error_code: str | None = None
    tool_call_id: uuid.UUID | None = None
    result_count: int = Field(default=0, ge=0)


class ModelDataDecision(StrictModel):
    requested: ModelDataAccessLevel
    maximum: ModelDataAccessLevel
    effective: ModelDataAccessLevel
