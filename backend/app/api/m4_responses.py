from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.cleaning.schemas import CleaningActionInput, CleaningPlanSuggestion
from app.jobs.schemas import JobPublic
from app.models import (
    CleaningPlanStatus,
    DataQualityIssueStatus,
    DataQualityIssueType,
    DataQualityRunStatus,
    DataQualitySeverity,
    DatasetColumnConfirmationStatus,
    DatasetColumnType,
    DatasetFileFormat,
    DatasetLicenseStatus,
    DatasetSemanticRole,
    DatasetSourceType,
    DatasetStatus,
    DatasetVersionStatus,
    DatasetVersionType,
    DataTransformationStatus,
)


class M4ResponseMeta(BaseModel):
    request_id: str | None = None
    schema_version: str = "1.0"
    idempotency_replayed: bool = False
    count: int | None = None


class M4Envelope[T](BaseModel):
    data: T
    meta: M4ResponseMeta


class DatasetPermissionsPublic(BaseModel):
    can_update: bool
    can_upload: bool
    can_confirm_columns: bool


class WorksheetPublic(BaseModel):
    name: str
    ordinal: int
    visibility: str
    estimated_rows: int
    estimated_columns: int
    warnings: list[str] = Field(default_factory=list)


class DatasetVersionPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    dataset_id: uuid.UUID
    version_number: int
    parent_version_id: uuid.UUID | None
    artifact_id: uuid.UUID
    version_type: DatasetVersionType
    row_count: int | None
    column_count: int | None
    file_format: DatasetFileFormat
    worksheet_manifest: list[WorksheetPublic] | None
    selected_worksheet_name: str | None
    projection_hash: str | None
    schema_hash: str | None
    data_hash: str
    transformation_id: uuid.UUID | None
    status: DatasetVersionStatus
    created_by: uuid.UUID | None
    created_at: datetime
    invalidated_at: datetime | None
    invalidation_reason: str | None


class DatasetPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    source_type: DatasetSourceType
    publisher: str | None
    source_platform: str | None
    source_identifier: str | None
    doi: str | None
    acquired_at: date | None
    license_name: str | None
    license_status: DatasetLicenseStatus
    license_warning: str | None
    recommended_citation: str | None
    known_limitations: list[str] | None
    current_version_id: uuid.UUID | None
    status: DatasetStatus
    lock_version: int
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    permissions: DatasetPermissionsPublic
    versions: list[DatasetVersionPublic] | None = None


class DatasetUploadPublic(BaseModel):
    dataset: DatasetPublic
    version: DatasetVersionPublic


class WorksheetsPublic(BaseModel):
    version_id: uuid.UUID
    status: DatasetVersionStatus
    worksheets: list[WorksheetPublic]
    selected_worksheet_name: str | None


class DatasetColumnPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    dataset_version_id: uuid.UUID
    source_name: str
    display_name: str | None
    column_order: int
    inferred_type: DatasetColumnType
    confirmed_type: DatasetColumnType | None
    semantic_role: DatasetSemanticRole | None
    unit: str | None
    description: str | None
    missing_codes: list[str] | None
    category_mapping: dict[str, Any] | None
    is_identifier: bool
    is_sensitive: bool
    confirmation_status: DatasetColumnConfirmationStatus
    unique_count: int
    missing_ratio: float
    example_values: list[Any]
    inherited_from_column_id: uuid.UUID | None
    lock_version: int
    created_at: datetime
    updated_at: datetime


class DatasetPreviewPublic(BaseModel):
    version_id: uuid.UUID
    offset: int
    limit: int
    columns: list[str]
    rows: list[dict[str, Any]]
    returned: int
    total_rows: int | None
    truncated: bool


class DataQualityRunPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    dataset_version_id: uuid.UUID
    ruleset_id: str
    ruleset_version: str
    ruleset_hash: str
    selected_rule_ids: list[str]
    include_sensitive_field_detection: bool
    status: DataQualityRunStatus
    issue_count: int
    high_issue_count: int
    processing_run_id: uuid.UUID | None
    job_id: uuid.UUID | None
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    created_at: datetime
    allowed_actions: list[str]


class QualityRunRequestPublic(BaseModel):
    run: DataQualityRunPublic
    job: JobPublic


class DataQualityIssuePublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    data_quality_run_id: uuid.UUID
    dataset_version_id: uuid.UUID
    rule_code: str
    issue_type: DataQualityIssueType
    severity: DataQualitySeverity
    column_id: uuid.UUID | None
    affected_row_count: int | None
    affected_rows: list[Any] | None
    evidence: dict[str, Any]
    description: str
    suggested_actions: list[dict[str, Any]] | None
    requires_approval: bool
    status: DataQualityIssueStatus
    created_at: datetime
    resolved_at: datetime | None
    allowed_actions: list[str]


class PaginationPublic(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class QualityIssuesEnvelope(BaseModel):
    data: list[DataQualityIssuePublic]
    pagination: PaginationPublic
    meta: M4ResponseMeta


class CleaningPlanPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    dataset_version_id: uuid.UUID
    title: str
    rationale: str | None
    status: CleaningPlanStatus
    actions: list[CleaningActionInput]
    preview_summary: dict[str, Any] | None
    preview_hash: str | None
    affected_row_count: int | None
    affected_column_count: int | None
    source_model_invocation_id: uuid.UUID | None
    approval_record_id: uuid.UUID | None
    payload_hash: str | None
    lock_version: int
    transformation_id: uuid.UUID | None
    job_id: uuid.UUID | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    allowed_actions: list[str]


class ApprovalRequestPublic(BaseModel):
    approval_id: uuid.UUID
    cleaning_plan_id: uuid.UUID
    status: str
    payload_hash: str
    expires_at: datetime | None


class DataTransformationPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    cleaning_plan_id: uuid.UUID
    approval_record_id: uuid.UUID
    source_dataset_version_id: uuid.UUID
    target_dataset_version_id: uuid.UUID | None
    status: DataTransformationStatus
    action_count: int
    affected_row_count: int | None
    affected_column_count: int | None
    parameters_hash: str
    output_artifact_id: uuid.UUID | None
    log_artifact_id: uuid.UUID | None
    processing_run_id: uuid.UUID | None
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    created_at: datetime


class TransformationExecutionPublic(BaseModel):
    transformation: DataTransformationPublic
    job: JobPublic


class CountDeltaPublic(BaseModel):
    before: int | None
    after: int | None
    delta: int


class MissingCellsPublic(BaseModel):
    before: int
    after: int


class VersionLineagePublic(BaseModel):
    parent_version_id: uuid.UUID | None
    transformation_id: uuid.UUID | None
    output_artifact_id: uuid.UUID | None


class VersionComparisonPublic(BaseModel):
    dataset_id: uuid.UUID
    base_version_id: uuid.UUID
    target_version_id: uuid.UUID
    row_count: CountDeltaPublic
    column_count: CountDeltaPublic
    missing_cells: MissingCellsPublic
    actions: list[CleaningActionInput]
    affected_row_count: int | None
    affected_column_count: int | None
    lineage: VersionLineagePublic


class CleaningPlanSuggestionPublic(BaseModel):
    model_invocation_id: uuid.UUID
    status: Literal["CANDIDATE"]
    suggestion: CleaningPlanSuggestion
    allowed_actions: list[str]


DatasetEnvelope = M4Envelope[DatasetPublic]
DatasetListEnvelope = M4Envelope[list[DatasetPublic]]
DatasetUploadEnvelope = M4Envelope[DatasetUploadPublic]
DatasetVersionEnvelope = M4Envelope[DatasetVersionPublic]
DatasetVersionListEnvelope = M4Envelope[list[DatasetVersionPublic]]
WorksheetsEnvelope = M4Envelope[WorksheetsPublic]
DatasetColumnEnvelope = M4Envelope[DatasetColumnPublic]
DatasetColumnListEnvelope = M4Envelope[list[DatasetColumnPublic]]
DatasetPreviewEnvelope = M4Envelope[DatasetPreviewPublic]
DataQualityRunEnvelope = M4Envelope[DataQualityRunPublic]
QualityRunRequestEnvelope = M4Envelope[QualityRunRequestPublic]
DataQualityIssueEnvelope = M4Envelope[DataQualityIssuePublic]
CleaningPlanEnvelope = M4Envelope[CleaningPlanPublic]
ApprovalRequestEnvelope = M4Envelope[ApprovalRequestPublic]
TransformationExecutionEnvelope = M4Envelope[TransformationExecutionPublic]
DataTransformationEnvelope = M4Envelope[DataTransformationPublic]
VersionComparisonEnvelope = M4Envelope[VersionComparisonPublic]
CleaningPlanSuggestionEnvelope = M4Envelope[CleaningPlanSuggestionPublic]
