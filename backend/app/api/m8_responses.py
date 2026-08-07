from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AgentResponseMeta(StrictPublic):
    request_id: str
    schema_version: Literal["1.0"] = "1.0"
    idempotency_replayed: bool = False


class AgentPagination(StrictPublic):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class AgentRunCreateRequest(StrictPublic):
    goal: str = Field(min_length=1, max_length=500)
    mode: Literal["PLAN_AND_EXPLAIN"] = "PLAN_AND_EXPLAIN"
    allow_tool_calls: bool = True


class AgentMessageRequest(StrictPublic):
    message: str = Field(min_length=1, max_length=500)


class SafeSummaryPublic(StrictPublic):
    kind: str
    text: str | None = None
    attributes: dict[str, str | int | bool | None] = Field(default_factory=dict)


class AgentEventPublic(StrictPublic):
    id: uuid.UUID
    sequence_number: int
    event_type: str
    actor_type: str
    safe_summary: SafeSummaryPublic
    created_at: datetime


class AgentJobLinkPublic(StrictPublic):
    id: uuid.UUID
    status: str
    known_status: bool
    progress_percent: int
    retryable: bool
    error_code: str | None


class AgentApprovalLinkPublic(StrictPublic):
    id: uuid.UUID
    status: str
    known_status: bool
    stale: bool
    expires_at: datetime | None


class ModelInvocationLinkPublic(StrictPublic):
    id: uuid.UUID
    tool_call_id: uuid.UUID | None
    status: str
    known_status: bool
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    request_count: int | None
    latency_ms: int | None
    error_code: str | None
    degraded: bool


class ToolCallLinkPublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    agent_run_id: uuid.UUID
    tool_name: str
    tool_version: str
    status: str
    known_status: bool
    category: str
    confirmation: str
    safe_input_summary: SafeSummaryPublic
    safe_output_summary: SafeSummaryPublic | None
    approval: AgentApprovalLinkPublic | None
    job: AgentJobLinkPublic | None
    output_object_type: str | None
    output_object_id: uuid.UUID | None
    retry_of_tool_call_id: uuid.UUID | None
    error_code: str | None
    retryable: bool
    allowed_actions: list[str]
    disabled_reason_code: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class AgentRunPublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    agent_type: str
    status: str
    known_status: bool
    lock_version: int
    safe_input_summary: SafeSummaryPublic
    safe_snapshot_summary: dict[str, Any]
    snapshot_hash: str
    snapshot_revision: int
    snapshot_current: bool
    source_object_versions: dict[str, str]
    max_turns: int
    max_tool_calls: int
    turn_count: int
    tool_call_count: int
    retry_of_agent_run_id: uuid.UUID | None
    failure_code: str | None
    degradation_code: str | None
    retryable: bool
    allowed_actions: list[str]
    disabled_reasons: dict[str, str]
    job: AgentJobLinkPublic | None
    events: list[AgentEventPublic]
    model_invocations: list[ModelInvocationLinkPublic]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class AgentRunEnvelope(StrictPublic):
    data: AgentRunPublic
    meta: AgentResponseMeta


class ToolCallEnvelope(StrictPublic):
    data: ToolCallLinkPublic
    meta: AgentResponseMeta


class ToolCallListEnvelope(StrictPublic):
    data: list[ToolCallLinkPublic]
    pagination: AgentPagination
    meta: AgentResponseMeta
