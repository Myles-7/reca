import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models import ApprovalStatus, ApprovalType, AuditActorType
from app.projects.schemas import PaginationMeta, ResponseMeta


class ApprovalRequesterPublic(BaseModel):
    type: AuditActorType
    id: str | None


class ApprovalDecisionPublic(BaseModel):
    status: ApprovalStatus
    user_id: uuid.UUID | None
    decided_at: datetime | None
    reason: str | None


class ApprovalItemPublic(BaseModel):
    id: uuid.UUID
    item_type: str
    item_id: uuid.UUID
    decision: str | None
    reason: str | None


class ApprovalPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    approval_type: ApprovalType
    target_object_type: str
    target_object_id: uuid.UUID
    requester: ApprovalRequesterPublic
    requested_at: datetime
    status: ApprovalStatus
    decision: ApprovalDecisionPublic | None
    payload_hash: str
    payload_snapshot: dict[str, Any] | None = None
    impact_summary: dict[str, Any] | None
    expires_at: datetime | None
    supersedes_approval_id: uuid.UUID | None
    items: list[ApprovalItemPublic]
    allowed_actions: list[str]
    created_at: datetime


class ApprovalEnvelope(BaseModel):
    data: ApprovalPublic
    meta: ResponseMeta


class ApprovalListEnvelope(BaseModel):
    data: list[ApprovalPublic]
    pagination: PaginationMeta
    meta: ResponseMeta


class ApprovalItemDecision(BaseModel):
    item_type: str = Field(min_length=1, max_length=100)
    item_id: uuid.UUID
    decision: str = Field(min_length=1, max_length=100)
    reason: str | None = Field(default=None, max_length=2000)


class ApprovalDecisionRequest(BaseModel):
    decision_reason: str | None = Field(default=None, max_length=2000)
    item_decisions: list[ApprovalItemDecision] = Field(default_factory=list)


class ApprovalRejectRequest(BaseModel):
    decision_reason: str = Field(min_length=1, max_length=2000)
    item_decisions: list[ApprovalItemDecision] = Field(default_factory=list)
