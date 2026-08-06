from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.approvals.schemas import ApprovalPublic
from app.artifacts.schemas import ArtifactDownload
from app.jobs.schemas import JobPublic
from app.models import ExportItemIncludeStatus, ExportStatus, ExportType
from app.projects.schemas import PaginationMeta, ResponseMeta


class ReproPackageCreate(BaseModel):
    include_original_literature_files: bool = False
    include_dataset_versions: bool = True
    include_sensitive_data: bool = False
    include_agent_logs: bool = False
    include_model_output_artifacts: bool = False
    acknowledge_license_warnings: bool = False


class ExportReadinessRequest(ReproPackageCreate):
    pass


class ReadinessIssue(BaseModel):
    code: str
    object_type: str
    object_id: uuid.UUID | None = None
    message: str


class ExportCandidate(BaseModel):
    object_type: str
    object_id: uuid.UUID | None
    artifact_id: uuid.UUID | None
    package_path: str
    sha256: str | None
    include_status: ExportItemIncludeStatus
    exclusion_reason: str | None = None
    license_status: str
    sensitive: bool
    redistribution: str
    source_version: dict[str, Any] = Field(default_factory=dict)


class ExportReadiness(BaseModel):
    audit_id: uuid.UUID
    ready: bool
    blocking_issues: list[ReadinessIssue]
    warnings: list[ReadinessIssue]
    requires_confirmation: bool
    candidate_items: list[ExportCandidate]
    limitations: list[str]
    snapshot: dict[str, Any]
    snapshot_hash: str
    rule_set_version: str


class ExportPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    export_type: ExportType
    status: ExportStatus
    scope: dict[str, Any]
    scope_hash: str
    readiness_audit_id: uuid.UUID | None
    approval_record_id: uuid.UUID | None
    job_id: uuid.UUID | None
    lock_version: int
    error_code: str | None
    created_at: datetime
    completed_at: datetime | None
    allowed_actions: list[str]


class ReproPackagePublic(BaseModel):
    id: uuid.UUID
    export_id: uuid.UUID
    project_id: uuid.UUID
    artifact_id: uuid.UUID
    manifest_artifact_id: uuid.UUID
    package_version: int
    schema_version: str
    contains_sensitive_data: bool
    contains_restricted_data: bool
    file_count: int
    total_size_bytes: int
    sha256: str
    manifest_sha256: str
    manifest: dict[str, Any]
    created_at: datetime
    allowed_actions: list[str]


class ReproPackageHistoryItem(BaseModel):
    id: uuid.UUID
    export_id: uuid.UUID
    project_id: uuid.UUID
    artifact_id: uuid.UUID
    manifest_artifact_id: uuid.UUID
    package_version: int
    schema_version: str
    contains_sensitive_data: bool
    contains_restricted_data: bool
    file_count: int
    total_size_bytes: int
    sha256: str
    created_at: datetime
    allowed_actions: list[str]


class ExportReadinessEnvelope(BaseModel):
    data: ExportReadiness
    meta: ResponseMeta


class ExportCreateData(BaseModel):
    export: ExportPublic
    readiness: ExportReadiness
    approval: ApprovalPublic | None = None
    job: JobPublic | None = None


class ExportCreateEnvelope(BaseModel):
    data: ExportCreateData
    meta: ResponseMeta


class ExportEnvelope(BaseModel):
    data: ExportPublic
    meta: ResponseMeta


class ReproPackageEnvelope(BaseModel):
    data: ReproPackagePublic
    meta: ResponseMeta


class ReproPackageHistoryEnvelope(BaseModel):
    data: list[ReproPackageHistoryItem]
    pagination: PaginationMeta
    meta: ResponseMeta


class ReproPackageDownloadData(BaseModel):
    package: ReproPackagePublic
    download: ArtifactDownload


class ReproPackageDownloadEnvelope(BaseModel):
    data: ReproPackageDownloadData
    meta: ResponseMeta
