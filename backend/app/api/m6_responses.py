from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.artifacts.schemas import ArtifactDownload
from app.jobs.schemas import JobPublic
from app.models import (
    ApprovalStatus,
    AuditActorType,
    AuditResultStatus,
    AuditType,
    ClaimConfidence,
    ClaimStatus,
    ClaimType,
    ManuscriptCheckRunStatus,
    ManuscriptEvidenceType,
    ManuscriptIssueSeverity,
    ManuscriptIssueStatus,
    ManuscriptIssueType,
    ManuscriptStatus,
    ManuscriptTransformationStatus,
    ManuscriptVersionStatus,
    ManuscriptVersionType,
)


class StrictPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")


class M6ResponseMeta(StrictPublic):
    request_id: str | None = None
    schema_version: str = "1.0"
    idempotency_replayed: bool = False


class ManuscriptPublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str | None
    current_version_id: uuid.UUID | None
    status: ManuscriptStatus
    lock_version: int
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    invalidated_at: datetime | None
    invalidation_reason: str | None
    allowed_actions: list[str]


class ManuscriptVersionPublic(StrictPublic):
    id: uuid.UUID
    manuscript_id: uuid.UUID
    project_id: uuid.UUID
    version_number: int
    parent_version_id: uuid.UUID | None
    artifact_id: uuid.UUID
    version_type: ManuscriptVersionType
    source_transformation_id: uuid.UUID | None
    status: ManuscriptVersionStatus
    source_hash: str
    parse_snapshot: dict[str, Any] | None
    created_by: uuid.UUID | None
    created_at: datetime
    invalidated_at: datetime | None
    invalidation_reason: str | None
    allowed_actions: list[str]


class ManuscriptCreatedPublic(StrictPublic):
    manuscript: ManuscriptPublic
    version: ManuscriptVersionPublic


class ProjectManuscriptDiscoveryPublic(StrictPublic):
    state: Literal["NONE", "ACTIVE", "ARCHIVED", "INVALIDATED"]
    current_manuscript: ManuscriptPublic | None
    current_version: ManuscriptVersionPublic | None
    manuscripts: list[ManuscriptPublic]
    versions: list[ManuscriptVersionPublic]


class ManuscriptCheckRunPublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    manuscript_version_id: uuid.UUID
    rule_set_version: str
    parser_version: str
    source_hash: str
    idempotency_key: str
    requested_checks: list[str]
    status: ManuscriptCheckRunStatus
    issue_count: int
    high_issue_count: int
    processing_run_id: uuid.UUID | None
    source_model_invocation_id: uuid.UUID | None
    degradation: dict[str, Any] | None
    error_code: str | None
    requested_by: uuid.UUID | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    job_id: uuid.UUID | None
    allowed_actions: list[str]


class ManuscriptCheckRequestPublic(StrictPublic):
    manuscript_check_run: ManuscriptCheckRunPublic
    job: JobPublic


class ManuscriptIssueEvidencePublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    manuscript_issue_id: uuid.UUID
    evidence_type: ManuscriptEvidenceType
    evidence_object_type: str
    evidence_object_id: uuid.UUID | None
    evidence_text: str | None
    evidence_hash: str
    evidence_metadata: dict[str, Any] | None
    created_at: datetime


class ManuscriptIssuePublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    manuscript_check_run_id: uuid.UUID
    manuscript_version_id: uuid.UUID
    issue_type: ManuscriptIssueType
    severity: ManuscriptIssueSeverity
    section_name: str | None
    paragraph_index: int | None
    table_index: int | None
    locator: dict[str, Any]
    original_text: str | None
    normalized_reference: str | None
    reason: str
    suggestion: str | None
    finding_hash: str
    confidence: str
    auto_fixable: bool
    status: ManuscriptIssueStatus
    lock_version: int
    decision_reason: str | None
    decided_by: uuid.UUID | None
    source_model_invocation_id: uuid.UUID | None
    created_at: datetime
    resolved_at: datetime | None
    invalidated_at: datetime | None
    allowed_actions: list[str]
    evidence: list[ManuscriptIssueEvidencePublic] = Field(default_factory=list)


class ManuscriptTransformationPublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    manuscript_version_id: uuid.UUID
    approved_issue_ids: list[str]
    plan_payload: dict[str, Any]
    input_artifact_hash: str
    preview: dict[str, Any] | None
    preview_hash: str | None
    approval_record_id: uuid.UUID | None
    output_manuscript_version_id: uuid.UUID | None
    idempotency_key: str | None
    status: ManuscriptTransformationStatus
    payload_hash: str
    lock_version: int
    error_code: str | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    job_id: uuid.UUID | None
    allowed_actions: list[str]


class RevisionAuditPublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    audit_type: AuditType
    before_version_id: uuid.UUID
    after_version_id: uuid.UUID
    manuscript_id: uuid.UUID
    status: AuditResultStatus
    rule_set_version: str
    before_source_hash: str
    after_source_hash: str
    idempotency_key: str
    request_snapshot: dict[str, Any]
    result: dict[str, Any] | None
    result_hash: str | None
    processing_run_id: uuid.UUID | None
    requested_by: uuid.UUID | None
    error_code: str | None
    created_at: datetime
    completed_at: datetime | None
    job_id: uuid.UUID | None
    allowed_actions: list[str]


class RevisionAuditRequestPublic(StrictPublic):
    audit_result: RevisionAuditPublic
    job: JobPublic


class ClaimPublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    claim_type: ClaimType
    claim_text: str
    normalized_claim: str
    scope_statement: str | None
    source_object_type: str
    source_object_id: uuid.UUID
    source_location: dict[str, Any]
    source_hash: str
    text_hash: str
    status: ClaimStatus
    confidence: ClaimConfidence
    created_by_actor_type: AuditActorType
    created_by_actor_id: str | None
    approval_record_id: uuid.UUID | None
    lock_version: int
    created_at: datetime
    updated_at: datetime
    confirmed_at: datetime | None
    invalidated_at: datetime | None
    invalidation_reason: str | None
    allowed_actions: list[str]


class ApprovalRequestPublic(StrictPublic):
    approval_id: uuid.UUID
    status: ApprovalStatus
    payload_hash: str
    expires_at: datetime | None
    plan_id: uuid.UUID | None = None
    claim_id: uuid.UUID | None = None


class TransformationExecutionPublic(StrictPublic):
    transformation: ManuscriptTransformationPublic
    job: JobPublic


class ManuscriptEnvelope(StrictPublic):
    data: ManuscriptPublic
    meta: M6ResponseMeta


class ManuscriptCreatedEnvelope(StrictPublic):
    data: ManuscriptCreatedPublic
    meta: M6ResponseMeta


class ProjectManuscriptDiscoveryEnvelope(StrictPublic):
    data: ProjectManuscriptDiscoveryPublic
    meta: M6ResponseMeta


class ManuscriptVersionEnvelope(StrictPublic):
    data: ManuscriptVersionPublic
    meta: M6ResponseMeta


class ManuscriptVersionListEnvelope(StrictPublic):
    data: list[ManuscriptVersionPublic]
    meta: M6ResponseMeta


class ManuscriptDownloadEnvelope(StrictPublic):
    data: ArtifactDownload
    meta: M6ResponseMeta


class ManuscriptCheckRequestEnvelope(StrictPublic):
    data: ManuscriptCheckRequestPublic
    meta: M6ResponseMeta


class ManuscriptCheckRunEnvelope(StrictPublic):
    data: ManuscriptCheckRunPublic
    meta: M6ResponseMeta


class ManuscriptIssueEnvelope(StrictPublic):
    data: ManuscriptIssuePublic
    meta: M6ResponseMeta


class ManuscriptIssueListEnvelope(StrictPublic):
    data: list[ManuscriptIssuePublic]
    meta: M6ResponseMeta


class ManuscriptTransformationEnvelope(StrictPublic):
    data: ManuscriptTransformationPublic
    meta: M6ResponseMeta


class ApprovalRequestEnvelope(StrictPublic):
    data: ApprovalRequestPublic
    meta: M6ResponseMeta


class TransformationExecutionEnvelope(StrictPublic):
    data: TransformationExecutionPublic
    meta: M6ResponseMeta


class RevisionAuditRequestEnvelope(StrictPublic):
    data: RevisionAuditRequestPublic
    meta: M6ResponseMeta


class RevisionAuditEnvelope(StrictPublic):
    data: RevisionAuditPublic
    meta: M6ResponseMeta


class ClaimEnvelope(StrictPublic):
    data: ClaimPublic
    meta: M6ResponseMeta
