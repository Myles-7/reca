from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.jobs.schemas import JobPublic
from app.models import (
    AnalysisGoal,
    AnalysisMethod,
    AnalysisPlanStatus,
    AnalysisResultType,
    AnalysisRunStatus,
    ArtifactStatus,
    ArtifactType,
    AssumptionCheckCode,
    AssumptionCheckStatus,
    FigureChartType,
    FigureIssueSeverity,
    FigureIssueStatus,
    FigureIssueType,
    FigurePlanStatus,
    FigureRenderRunStatus,
    FigureStatus,
)


class StrictPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")


class M5ResponseMeta(StrictPublic):
    request_id: str | None = None
    schema_version: str = "1.0"
    idempotency_replayed: bool = False


class AnalysisAssumptionPublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    analysis_plan_id: uuid.UUID
    check_code: AssumptionCheckCode
    subject_key: str
    status: AssumptionCheckStatus
    explanation: str
    evidence: dict[str, Any]
    blocks_approval: bool
    checked_at: datetime


class AnalysisPlanPublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    research_question_version_id: uuid.UUID
    dataset_version_id: uuid.UUID
    analysis_goal: AnalysisGoal
    method: AnalysisMethod
    dependent_variable_ids: list[str]
    independent_variable_ids: list[str]
    control_variable_ids: list[str]
    missing_data_policy: dict[str, Any]
    sample_filter: dict[str, Any] | None
    parameters: dict[str, Any]
    status: AnalysisPlanStatus
    validation_hash: str | None
    validation_warnings: list[str]
    approval_record_id: uuid.UUID | None
    payload_hash: str | None
    approval_stale: bool
    lock_version: int
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    invalidated_at: datetime | None
    invalidation_reason: str | None
    checks: list[AnalysisAssumptionPublic]
    allowed_actions: list[str]


class AnalysisPlanEnvelope(StrictPublic):
    data: AnalysisPlanPublic
    meta: M5ResponseMeta


class AnalysisApprovalPublic(StrictPublic):
    approval_id: uuid.UUID
    analysis_plan_id: uuid.UUID
    status: str
    payload_hash: str
    expires_at: datetime | None


class AnalysisApprovalEnvelope(StrictPublic):
    data: AnalysisApprovalPublic
    meta: M5ResponseMeta


class AnalysisRunPublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    analysis_plan_id: uuid.UUID
    dataset_version_id: uuid.UUID
    approval_record_id: uuid.UUID
    processing_run_id: uuid.UUID | None
    run_number: int
    idempotency_key: str
    run_reason: str | None
    status: AnalysisRunStatus
    parameters_hash: str
    input_hash: str
    environment_hash: str | None
    environment_snapshot: dict[str, Any] | None
    effective_n: int | None
    code_artifact_id: uuid.UUID | None
    log_artifact_id: uuid.UUID | None
    requested_by: uuid.UUID | None
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    created_at: datetime
    invalidated_at: datetime | None
    invalidation_reason: str | None
    job_id: uuid.UUID | None
    result_count: int
    allowed_actions: list[str]


class AnalysisRunRequestPublic(StrictPublic):
    analysis_run: AnalysisRunPublic
    job: JobPublic


class AnalysisRunRequestEnvelope(StrictPublic):
    data: AnalysisRunRequestPublic
    meta: M5ResponseMeta


class AnalysisRunEnvelope(StrictPublic):
    data: AnalysisRunPublic
    meta: M5ResponseMeta


class AnalysisResultPublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    analysis_run_id: uuid.UUID
    result_key: str
    result_type: AnalysisResultType
    schema_version: str
    is_primary: bool
    payload: dict[str, Any]
    result_hash: str
    created_at: datetime


class AnalysisResultsPublic(StrictPublic):
    analysis_run_id: uuid.UUID
    dataset_version_id: uuid.UUID
    status: AnalysisRunStatus
    results: list[AnalysisResultPublic]
    code_artifact_id: uuid.UUID | None
    log_artifact_id: uuid.UUID | None
    environment: dict[str, Any] | None


class AnalysisResultsEnvelope(StrictPublic):
    data: AnalysisResultsPublic
    meta: M5ResponseMeta


class FigurePlanPublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    dataset_version_id: uuid.UUID
    analysis_run_id: uuid.UUID | None
    analysis_result_id: uuid.UUID | None
    chart_type: FigureChartType
    parameters: dict[str, Any]
    caption: str
    status: FigurePlanStatus
    plan_hash: str
    lock_version: int
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    invalidated_at: datetime | None
    invalidation_reason: str | None
    allowed_actions: list[str]


class FigurePlanEnvelope(StrictPublic):
    data: FigurePlanPublic
    meta: M5ResponseMeta


class FigureRenderRunPublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    figure_plan_id: uuid.UUID
    dataset_version_id: uuid.UUID
    processing_run_id: uuid.UUID | None
    render_number: int
    idempotency_key: str
    status: FigureRenderRunStatus
    parameters_hash: str
    input_hash: str
    environment_hash: str | None
    environment_snapshot: dict[str, Any] | None
    requested_by: uuid.UUID | None
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    created_at: datetime
    figure_id: uuid.UUID | None
    job_id: uuid.UUID | None
    allowed_actions: list[str]


class FigureRenderRequestPublic(StrictPublic):
    figure_render_run: FigureRenderRunPublic
    job: JobPublic


class FigureRenderRequestEnvelope(StrictPublic):
    data: FigureRenderRequestPublic
    meta: M5ResponseMeta


class FigureRenderRunEnvelope(StrictPublic):
    data: FigureRenderRunPublic
    meta: M5ResponseMeta


class FigureValidationIssuePublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    figure_id: uuid.UUID
    issue_type: FigureIssueType
    severity: FigureIssueSeverity
    status: FigureIssueStatus
    subject_key: str
    message: str
    evidence: dict[str, Any]
    blocks_confirmation: bool
    created_at: datetime


class FigureArtifactPublic(StrictPublic):
    id: uuid.UUID
    format: str
    artifact_type: ArtifactType
    status: ArtifactStatus
    sha256: str
    mime_type: str
    size_bytes: int
    downloadable: bool


class FigurePublic(StrictPublic):
    id: uuid.UUID
    project_id: uuid.UUID
    figure_plan_id: uuid.UUID
    figure_render_run_id: uuid.UUID
    dataset_version_id: uuid.UUID
    analysis_run_id: uuid.UUID | None
    analysis_result_id: uuid.UUID | None
    version_number: int
    chart_type: FigureChartType
    status: FigureStatus
    caption: str
    figure_hash: str
    png_artifact_id: uuid.UUID
    svg_artifact_id: uuid.UUID
    pdf_artifact_id: uuid.UUID
    code_artifact_id: uuid.UUID
    approval_record_id: uuid.UUID | None
    created_at: datetime
    confirmed_at: datetime | None
    invalidated_at: datetime | None
    invalidation_reason: str | None
    validation_issues: list[FigureValidationIssuePublic]
    artifacts: list[FigureArtifactPublic]
    approval_stale: bool
    allowed_actions: list[str]


class FigureEnvelope(StrictPublic):
    data: FigurePublic
    meta: M5ResponseMeta


class FigureIssuesPublic(StrictPublic):
    figure_id: uuid.UUID
    issues: list[FigureValidationIssuePublic]


class FigureIssuesEnvelope(StrictPublic):
    data: FigureIssuesPublic
    meta: M5ResponseMeta


class FigureApprovalPublic(StrictPublic):
    approval_id: uuid.UUID
    figure_id: uuid.UUID
    status: str
    payload_hash: str
    expires_at: datetime | None


class FigureApprovalEnvelope(StrictPublic):
    data: FigureApprovalPublic
    meta: M5ResponseMeta


class FigureRecommendationPublic(StrictPublic):
    status: str
    suggestions: list[dict[str, Any]]
    deterministic: bool
    reason: str | None


class FigureRecommendationEnvelope(StrictPublic):
    data: FigureRecommendationPublic
    meta: M5ResponseMeta
