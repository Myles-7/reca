from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.jobs.schemas import JobPublic
from app.models import (
    AuditResultOutcome,
    AuditResultStatus,
    AuditType,
    EvidenceLinkStatus,
    EvidenceLinkStrength,
    EvidenceObjectType,
    EvidenceRelationType,
)
from app.projects.schemas import ResponseMeta


class EvidenceRisk(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class CompletenessStatus(StrEnum):
    SATISFIED = "SATISFIED"
    MISSING = "MISSING"
    STALE = "STALE"
    RESTRICTED = "RESTRICTED"
    CONFLICTED = "CONFLICTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class EvidenceReference(BaseModel):
    project_id: uuid.UUID
    object_type: EvidenceObjectType
    object_id: uuid.UUID
    raw_status: str
    known_status: bool
    source_hash: str
    source_version: dict[str, Any]
    label: str
    detail_intent: str
    invalidated: bool = False
    stale: bool = False
    restricted: bool = False
    limitations: list[str] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)


class ClaimEvidenceLinkCreate(BaseModel):
    evidence_object_type: EvidenceObjectType
    evidence_object_id: uuid.UUID
    relation_type: EvidenceRelationType
    strength: EvidenceLinkStrength = EvidenceLinkStrength.UNKNOWN
    explanation: str | None = Field(default=None, max_length=4000)
    suggestion: bool = False


class ClaimEvidenceLinkTransition(BaseModel):
    status: EvidenceLinkStatus
    reason: str | None = Field(default=None, max_length=4000)


class ClaimAuditCreate(BaseModel):
    request_ai_explanation: bool = False


class ClaimEvidenceLinkPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    claim_id: uuid.UUID
    evidence: EvidenceReference
    relation_type: EvidenceRelationType
    strength: EvidenceLinkStrength
    status: EvidenceLinkStatus
    explanation: str | None
    lock_version: int
    confirmed_at: datetime | None
    invalidated_at: datetime | None
    invalidation_reason: str | None
    allowed_actions: list[str]


class GraphNode(BaseModel):
    id: str
    node_type: str
    object_id: uuid.UUID
    label: str
    raw_status: str
    known_status: bool
    risk: EvidenceRisk
    invalidated: bool
    stale: bool
    source_kind: str
    detail_intent: str
    allowed_actions: list[str]
    limitations: list[str]
    lane: str | None = None
    rank: int | None = None


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation_type: str
    strength: EvidenceLinkStrength | None = None
    raw_status: str
    known_status: bool
    risk: EvidenceRisk
    invalidated: bool
    source_kind: str


class CompletenessItem(BaseModel):
    code: str
    status: CompletenessStatus
    source_object_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    missing_actions: list[str] = Field(default_factory=list)


class EvidenceCompleteness(BaseModel):
    rule_set_version: str
    claim_id: uuid.UUID
    scope: dict[str, Any]
    items: list[CompletenessItem]
    limitations: list[str] = Field(default_factory=list)


class EvidenceGraphProjection(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    completeness: dict[str, EvidenceCompleteness]
    partial: bool
    next_cursor: str | None
    limitations: list[str]
    scope: dict[str, Any]


class ClaimAuditPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    audit_type: AuditType
    target_object_type: str | None
    target_object_id: uuid.UUID | None
    job_id: uuid.UUID | None
    execution_status: AuditResultStatus
    outcome: AuditResultOutcome | None
    source_snapshot_hash: str | None
    result_hash: str | None
    findings: list[dict[str, Any]]
    limitations: list[str]
    degraded: bool
    rule_set_version: str
    allowed_actions: list[str]


class ClaimEvidenceLinkEnvelope(BaseModel):
    data: ClaimEvidenceLinkPublic
    meta: ResponseMeta


class ClaimEvidenceLinkListEnvelope(BaseModel):
    data: list[ClaimEvidenceLinkPublic]
    meta: ResponseMeta


class EvidenceGraphEnvelope(BaseModel):
    data: EvidenceGraphProjection
    meta: ResponseMeta


class ClaimAuditRequestData(BaseModel):
    audit_result: ClaimAuditPublic
    job: JobPublic


class ClaimAuditRequestEnvelope(BaseModel):
    data: ClaimAuditRequestData
    meta: ResponseMeta


class ClaimAuditEnvelope(BaseModel):
    data: ClaimAuditPublic
    meta: ResponseMeta
