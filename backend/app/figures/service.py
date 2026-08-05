from __future__ import annotations

import hashlib
import json
import uuid
from datetime import timedelta
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.adapters.storage import ObjectStorage
from app.analysis import service as analysis_service
from app.api.errors import ContractError
from app.approvals import service as approval_service
from app.artifacts import service as artifact_service
from app.figures import renderer
from app.figures.schemas import (
    BoxplotParameters,
    CorrelationMatrixParameters,
    FigurePlanCreate,
    FigureRenderCreate,
    GroupComparisonParameters,
    HistogramParameters,
    ScatterParameters,
)
from app.jobs import service as job_service
from app.models import (
    AnalysisResult,
    AnalysisRun,
    AnalysisRunStatus,
    ApprovalRecord,
    ApprovalStatus,
    ApprovalType,
    Artifact,
    ArtifactStatus,
    ArtifactType,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    CodeArtifact,
    DatasetColumn,
    DatasetColumnConfirmationStatus,
    DatasetVersion,
    DatasetVersionStatus,
    Figure,
    FigureIssueSeverity,
    FigureIssueStatus,
    FigureIssueType,
    FigurePlan,
    FigurePlanStatus,
    FigureRenderRun,
    FigureRenderRunStatus,
    FigureStatus,
    FigureValidationIssue,
    Job,
    JobTaskType,
    ProjectMemberRole,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

TARGET_OBJECT_TYPE = "figure"
RENDER_PATH = "/api/v1/figure-plans/{plan_id}/render-runs"


class FigureExecutionError(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def _encoded(value: Any) -> dict[str, Any]:
    return cast(dict[str, Any], jsonable_encoder(value))


def _hash(value: Any) -> str:
    raw = json.dumps(
        jsonable_encoder(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(raw).hexdigest()


def _role(access: project_service.ProjectAccess) -> ProjectMemberRole:
    assert access.membership is not None
    return access.membership.role


def _parameter_column_ids(payload: FigurePlanCreate) -> list[uuid.UUID]:
    parameters = payload.parameters
    if isinstance(parameters, ScatterParameters):
        return [parameters.x_column_id, parameters.y_column_id]
    if isinstance(parameters, GroupComparisonParameters):
        return [parameters.group_column_id, parameters.value_column_id]
    if isinstance(parameters, HistogramParameters):
        return [parameters.value_column_id]
    if isinstance(parameters, BoxplotParameters):
        return [
            parameters.value_column_id,
            *([parameters.group_column_id] if parameters.group_column_id else []),
        ]
    assert isinstance(parameters, CorrelationMatrixParameters)
    return parameters.column_ids


def _columns(
    session: Session,
    *,
    project_id: uuid.UUID,
    version_id: uuid.UUID,
    ids: list[uuid.UUID],
) -> list[DatasetColumn]:
    rows = list(
        session.exec(
            select(DatasetColumn).where(
                DatasetColumn.project_id == project_id,
                DatasetColumn.dataset_version_id == version_id,
                col(DatasetColumn.id).in_(ids),
            )
        )
    )
    if len(rows) != len(set(ids)):
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    if any(
        row.confirmation_status != DatasetColumnConfirmationStatus.CONFIRMED
        or row.confirmed_type is None
        for row in rows
    ):
        raise ContractError(
            status_code=409,
            code="COLUMN_CONFIRMATION_REQUIRED",
            message="All Figure columns must be confirmed.",
        )
    return rows


def _assert_upstream(
    session: Session,
    *,
    project_id: uuid.UUID,
    version: DatasetVersion,
    analysis_run_id: uuid.UUID | None,
    analysis_result_id: uuid.UUID | None,
) -> tuple[AnalysisRun | None, AnalysisResult | None]:
    run = session.get(AnalysisRun, analysis_run_id) if analysis_run_id else None
    result = (
        session.get(AnalysisResult, analysis_result_id) if analysis_result_id else None
    )
    if run is not None and (
        run.project_id != project_id
        or run.dataset_version_id != version.id
        or run.status != AnalysisRunStatus.COMPLETED
    ):
        raise ContractError(
            status_code=409,
            code="VERSION_MISMATCH",
            message="AnalysisRun does not match the DatasetVersion.",
        )
    if result is not None and (
        run is None
        or result.project_id != project_id
        or result.analysis_run_id != run.id
    ):
        raise ContractError(
            status_code=409,
            code="RESULT_MISMATCH",
            message="AnalysisResult does not match the AnalysisRun.",
        )
    return run, result


def _assert_result_matches_plan(
    payload: FigurePlanCreate, result: AnalysisResult | None
) -> None:
    if result is None:
        return
    parameters = payload.parameters
    result_payload = result.payload
    if isinstance(parameters, GroupComparisonParameters):
        observed = {
            result_payload.get("group_column_id"),
            result_payload.get("outcome_column_id"),
        }
        expected = {
            str(parameters.group_column_id),
            str(parameters.value_column_id),
        }
        if result.result_type.value != "GROUP_COMPARISON" or observed != expected:
            raise ContractError(
                status_code=409,
                code="RESULT_MISMATCH",
                message="Group comparison Figure does not match the AnalysisResult columns.",
            )
    if isinstance(parameters, ScatterParameters) and result.result_type.value in {
        "CORRELATION",
        "REGRESSION",
    }:
        observed = {
            result_payload.get("x_column_id"),
            result_payload.get("y_column_id"),
        }
        expected = {str(parameters.x_column_id), str(parameters.y_column_id)}
        if observed != expected:
            raise ContractError(
                status_code=409,
                code="RESULT_MISMATCH",
                message="Scatter Figure does not match the AnalysisResult columns.",
            )


def _plan_actions(role: ProjectMemberRole, plan: FigurePlan) -> list[str]:
    permissions = project_service.ROLE_ACTIONS[role]
    actions = ["figure_plan.read"]
    if plan.status == FigurePlanStatus.READY and "figure.render" in permissions:
        actions.append("figure_plan.render")
    if (
        plan.status != FigurePlanStatus.INVALIDATED
        and "figure.invalidate" in permissions
    ):
        actions.append("figure_plan.invalidate")
    return actions


def _figure_actions(role: ProjectMemberRole, figure: Figure) -> list[str]:
    permissions = project_service.ROLE_ACTIONS[role]
    actions = ["figure.read"]
    if (
        figure.status in {FigureStatus.READY, FigureStatus.NEEDS_REVIEW}
        and "figure.request_confirmation" in permissions
    ):
        actions.append("figure.request_confirmation")
    if figure.status != FigureStatus.INVALIDATED and "figure.invalidate" in permissions:
        actions.append("figure.invalidate")
    if figure.status != FigureStatus.INVALIDATED and "artifact.download" in permissions:
        actions.append("figure.download")
    return actions


def create_plan(
    session: Session, *, actor: User, project_id: uuid.UUID, payload: FigurePlanCreate
) -> dict[str, Any]:
    access = project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="figure.create",
        for_update=True,
    )
    version = session.get(DatasetVersion, payload.dataset_version_id)
    if version is None or version.project_id != project_id:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    if version.status != DatasetVersionStatus.AVAILABLE:
        raise ContractError(
            status_code=409,
            code="VERSION_UNAVAILABLE",
            message="DatasetVersion is not AVAILABLE.",
        )
    _, result = _assert_upstream(
        session,
        project_id=project_id,
        version=version,
        analysis_run_id=payload.analysis_run_id,
        analysis_result_id=payload.analysis_result_id,
    )
    _assert_result_matches_plan(payload, result)
    _columns(
        session,
        project_id=project_id,
        version_id=version.id,
        ids=_parameter_column_ids(payload),
    )
    canonical = payload.model_dump(mode="json")
    plan = FigurePlan(
        project_id=project_id,
        dataset_version_id=version.id,
        analysis_run_id=payload.analysis_run_id,
        analysis_result_id=payload.analysis_result_id,
        chart_type=payload.chart_type,
        parameters=payload.parameters.model_dump(mode="json"),
        caption=payload.caption.strip(),
        status=FigurePlanStatus.READY,
        plan_hash=_hash(canonical),
        created_by=actor.id,
    )
    session.add(plan)
    session.flush()
    project_service._commit(session)
    session.refresh(plan)
    return _encoded(
        {**plan.model_dump(), "allowed_actions": _plan_actions(_role(access), plan)}
    )


def get_plan(session: Session, *, actor: User, plan_id: uuid.UUID) -> dict[str, Any]:
    plan = session.get(FigurePlan, plan_id)
    if plan is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    access = project_service.authorize_project(
        session, project_id=plan.project_id, actor=actor, action="figure.read"
    )
    return _encoded(
        {**plan.model_dump(), "allowed_actions": _plan_actions(_role(access), plan)}
    )


def recommendation(*, provider_configured: bool = False) -> dict[str, Any]:
    return {
        "status": "AVAILABLE" if provider_configured else "DEGRADED",
        "suggestions": [],
        "deterministic": False,
        "reason": None if provider_configured else "AI_PROVIDER_NOT_CONFIGURED",
    }


def create_render_run(
    session: Session,
    *,
    actor: User,
    plan_id: uuid.UUID,
    payload: FigureRenderCreate,
    idempotency_key: str,
    dispatcher: job_service.JobDispatcher,
) -> project_service.OperationResult:
    request_reason = payload.reason
    plan = session.get(FigurePlan, plan_id)
    if plan is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    access = project_service.authorize_project(
        session,
        project_id=plan.project_id,
        actor=actor,
        action="figure.render",
        for_update=True,
    )
    existing = session.exec(
        select(FigureRenderRun).where(
            FigureRenderRun.figure_plan_id == plan.id,
            FigureRenderRun.idempotency_key == idempotency_key,
        )
    ).first()
    if existing is not None:
        return project_service.OperationResult(
            data=_render_request_data(session, existing, _role(access)),
            status_code=202,
            idempotency_replayed=True,
        )
    if plan.status != FigurePlanStatus.READY:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="FigurePlan is not READY.",
        )
    version = session.get(DatasetVersion, plan.dataset_version_id)
    if version is None or version.status != DatasetVersionStatus.AVAILABLE:
        raise ContractError(
            status_code=409,
            code="VERSION_UNAVAILABLE",
            message="DatasetVersion is not AVAILABLE.",
        )
    input_hash = _hash(
        {
            "plan_hash": plan.plan_hash,
            "data_hash": version.data_hash,
            "schema_hash": version.schema_hash,
            "projection_hash": version.projection_hash,
        }
    )
    next_number = (
        int(
            session.exec(
                select(func.coalesce(func.max(FigureRenderRun.render_number), 0)).where(
                    FigureRenderRun.figure_plan_id == plan.id
                )
            ).one()
        )
        + 1
    )
    render_run = FigureRenderRun(
        project_id=plan.project_id,
        figure_plan_id=plan.id,
        dataset_version_id=plan.dataset_version_id,
        render_number=next_number,
        idempotency_key=idempotency_key,
        parameters_hash=_hash(plan.parameters),
        input_hash=input_hash,
        requested_by=actor.id,
    )
    session.add(render_run)
    session.flush()
    job = job_service.create_job(
        session,
        project_id=plan.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.FIGURE_RENDER,
            resource_type="figure_render_run",
            resource_id=render_run.id,
            idempotency_key=idempotency_key,
            requested_by_user_id=actor.id,
            max_retries=2,
        ),
    )
    if request_reason:
        job.current_step = "Requested: " + request_reason[:200]
        session.add(job)
    project_service._commit(session)
    dispatched = job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)
    return project_service.OperationResult(
        data={
            "figure_render_run": _render_data(session, render_run, _role(access)),
            "job": job_service.job_data(session, dispatched),
        },
        status_code=202,
    )


def _render_data(
    session: Session, run: FigureRenderRun, role: ProjectMemberRole
) -> dict[str, Any]:
    figure = session.exec(
        select(Figure).where(Figure.figure_render_run_id == run.id)
    ).first()
    job = session.exec(
        select(Job).where(
            Job.resource_type == "figure_render_run", Job.resource_id == run.id
        )
    ).first()
    permissions = project_service.ROLE_ACTIONS[role]
    actions: list[str] = []
    if (
        run.status in {FigureRenderRunStatus.QUEUED, FigureRenderRunStatus.RUNNING}
        and "job.cancel" in permissions
    ):
        actions.append("figure_render_run.cancel")
    if run.status == FigureRenderRunStatus.FAILED and "job.retry" in permissions:
        actions.append("figure_render_run.retry")
    return _encoded(
        {
            **run.model_dump(),
            "figure_id": figure.id if figure else None,
            "job_id": job.id if job else None,
            "allowed_actions": actions,
        }
    )


def _render_request_data(
    session: Session, run: FigureRenderRun, role: ProjectMemberRole
) -> dict[str, Any]:
    job = session.exec(
        select(Job).where(
            Job.resource_type == "figure_render_run", Job.resource_id == run.id
        )
    ).one()
    return {
        "figure_render_run": _render_data(session, run, role),
        "job": job_service.job_data(session, job),
    }


def get_render_run(
    session: Session, *, actor: User, run_id: uuid.UUID
) -> dict[str, Any]:
    run = session.get(FigureRenderRun, run_id)
    if run is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    access = project_service.authorize_project(
        session, project_id=run.project_id, actor=actor, action="figure.read"
    )
    return _render_data(session, run, _role(access))


def _issues(session: Session, figure_id: uuid.UUID) -> list[FigureValidationIssue]:
    return list(
        session.exec(
            select(FigureValidationIssue)
            .where(FigureValidationIssue.figure_id == figure_id)
            .order_by(
                col(FigureValidationIssue.severity),
                col(FigureValidationIssue.issue_type),
            )
        )
    )


def _figure_data(
    session: Session, figure: Figure, role: ProjectMemberRole
) -> dict[str, Any]:
    code_record = session.get(CodeArtifact, figure.code_artifact_id)
    if code_record is None:
        raise ContractError(
            status_code=409,
            code="FIGURE_ARTIFACT_MISMATCH",
            message="Figure Code Artifact relationship is incomplete.",
        )
    artifact_ids = {
        "PNG": figure.png_artifact_id,
        "SVG": figure.svg_artifact_id,
        "PDF": figure.pdf_artifact_id,
        "CODE": code_record.artifact_id,
    }
    permissions = project_service.ROLE_ACTIONS[role]
    artifacts = []
    for format_name, artifact_id in artifact_ids.items():
        artifact = session.get(Artifact, artifact_id)
        if artifact is None or artifact.project_id != figure.project_id:
            raise ContractError(
                status_code=409,
                code="FIGURE_ARTIFACT_MISMATCH",
                message="Figure Artifact relationship is incomplete.",
            )
        artifacts.append(
            {
                "id": artifact.id,
                "format": format_name,
                "artifact_type": artifact.artifact_type,
                "status": artifact.status,
                "sha256": artifact.sha256,
                "mime_type": artifact.mime_type,
                "size_bytes": artifact.size_bytes,
                "downloadable": (
                    figure.status != FigureStatus.INVALIDATED
                    and artifact.status == ArtifactStatus.AVAILABLE
                    and "artifact.download" in permissions
                ),
            }
        )
    return _encoded(
        {
            **figure.model_dump(),
            "validation_issues": _issues(session, figure.id),
            "artifacts": artifacts,
            "approval_stale": _approval_stale(session, figure),
            "allowed_actions": _figure_actions(role, figure),
        }
    )


def get_figure(
    session: Session, *, actor: User, figure_id: uuid.UUID
) -> dict[str, Any]:
    figure = session.get(Figure, figure_id)
    if figure is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    access = project_service.authorize_project(
        session, project_id=figure.project_id, actor=actor, action="figure.read"
    )
    return _figure_data(session, figure, _role(access))


def get_issues(
    session: Session, *, actor: User, figure_id: uuid.UUID
) -> dict[str, Any]:
    figure = session.get(Figure, figure_id)
    if figure is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    project_service.authorize_project(
        session, project_id=figure.project_id, actor=actor, action="figure.read"
    )
    return _encoded({"figure_id": figure.id, "issues": _issues(session, figure.id)})


def canonical_payload(session: Session, figure: Figure) -> dict[str, Any]:
    return _encoded(
        {
            "figure_id": figure.id,
            "figure_hash": figure.figure_hash,
            "figure_plan_id": figure.figure_plan_id,
            "figure_render_run_id": figure.figure_render_run_id,
            "dataset_version_id": figure.dataset_version_id,
            "analysis_run_id": figure.analysis_run_id,
            "analysis_result_id": figure.analysis_result_id,
            "artifact_ids": [
                figure.png_artifact_id,
                figure.svg_artifact_id,
                figure.pdf_artifact_id,
                figure.code_artifact_id,
            ],
            "open_issues": [
                issue.model_dump()
                for issue in _issues(session, figure.id)
                if issue.status == FigureIssueStatus.OPEN
            ],
        }
    )


def _approval_stale(session: Session, figure: Figure) -> bool:
    if figure.approval_record_id is None:
        return False
    approval = session.get(ApprovalRecord, figure.approval_record_id)
    return (
        approval is None
        or approval.project_id != figure.project_id
        or approval.target_object_type != TARGET_OBJECT_TYPE
        or approval.target_object_id != figure.id
        or approval.payload_hash
        != project_service.request_hash(canonical_payload(session, figure))
    )


def resolve_approval_payload(
    session: Session, approval: ApprovalRecord
) -> dict[str, Any]:
    figure = session.get(Figure, approval.target_object_id)
    if figure is None or figure.project_id != approval.project_id:
        raise ContractError(
            status_code=409, code="APPROVAL_STALE", message="Figure no longer exists."
        )
    return canonical_payload(session, figure)


def apply_approval_decision(
    session: Session, approval: ApprovalRecord, decision: ApprovalStatus, _actor: User
) -> None:
    figure = session.exec(
        select(Figure).where(Figure.id == approval.target_object_id).with_for_update()
    ).one()
    if figure.approval_record_id != approval.id or _approval_stale(session, figure):
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="Figure confirmation is stale.",
        )
    figure.status = (
        FigureStatus.CONFIRMED
        if decision == ApprovalStatus.APPROVED
        else FigureStatus.READY
    )
    figure.confirmed_at = (
        get_datetime_utc() if decision == ApprovalStatus.APPROVED else None
    )
    session.add(figure)


def register_approval_handlers() -> None:
    approval_service.register_payload_resolver(
        TARGET_OBJECT_TYPE, resolve_approval_payload
    )
    approval_service.register_decision_handler(
        TARGET_OBJECT_TYPE, apply_approval_decision
    )


def request_confirmation(
    session: Session, *, actor: User, figure_id: uuid.UUID
) -> dict[str, Any]:
    figure = session.exec(
        select(Figure).where(Figure.id == figure_id).with_for_update()
    ).first()
    if figure is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    project_service.authorize_project(
        session,
        project_id=figure.project_id,
        actor=actor,
        action="figure.request_confirmation",
        for_update=True,
    )
    if figure.status not in {FigureStatus.READY, FigureStatus.NEEDS_REVIEW}:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Figure cannot be confirmed.",
        )
    if any(
        issue.blocks_confirmation and issue.status == FigureIssueStatus.OPEN
        for issue in _issues(session, figure.id)
    ):
        raise ContractError(
            status_code=409,
            code="FIGURE_VALIDATION_FAILED",
            message="Blocking Figure issues remain open.",
        )
    approval = approval_service.create_approval(
        session,
        command=approval_service.ApprovalCreate(
            project_id=figure.project_id,
            approval_type=ApprovalType.FIGURE_CONFIRMATION,
            target_object_type=TARGET_OBJECT_TYPE,
            target_object_id=figure.id,
            requested_by_actor_type=AuditActorType.USER,
            requested_by_actor_id=str(actor.id),
            payload_snapshot=canonical_payload(session, figure),
            impact_summary={
                "chart_type": figure.chart_type,
                "figure_hash": figure.figure_hash,
            },
            expires_at=get_datetime_utc() + timedelta(hours=24),
        ),
    )
    figure.approval_record_id = approval.id
    session.add(figure)
    project_service._commit(session)
    return _encoded(
        {
            "approval_id": approval.id,
            "figure_id": figure.id,
            "status": approval.status,
            "payload_hash": approval.payload_hash,
            "expires_at": approval.expires_at,
        }
    )


def authorize_format_download(
    session: Session, *, actor: User, figure_id: uuid.UUID, format_name: str
) -> dict[str, Any]:
    figure = session.get(Figure, figure_id)
    if figure is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    project_service.authorize_project(
        session, project_id=figure.project_id, actor=actor, action="figure.read"
    )
    if figure.status == FigureStatus.INVALIDATED:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Invalidated Figure cannot be downloaded.",
        )
    code_record = session.get(CodeArtifact, figure.code_artifact_id)
    if code_record is None:
        raise ContractError(
            status_code=409,
            code="FIGURE_ARTIFACT_MISMATCH",
            message="Figure Code Artifact relationship is incomplete.",
        )
    artifact_id = {
        "png": figure.png_artifact_id,
        "svg": figure.svg_artifact_id,
        "pdf": figure.pdf_artifact_id,
        "code": code_record.artifact_id,
    }.get(format_name.lower())
    if artifact_id is None:
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Unsupported Figure format.",
        )
    return artifact_service.authorize_download(
        session, actor=actor, artifact_id=artifact_id
    )


def _validation_issues(
    plan: FigurePlan,
) -> list[tuple[FigureIssueType, FigureIssueSeverity, str]]:
    parameters = plan.parameters
    issues: list[tuple[FigureIssueType, FigureIssueSeverity, str]] = []
    if not plan.caption.strip():
        issues.append(
            (
                FigureIssueType.MISSING_CAPTION,
                FigureIssueSeverity.ERROR,
                "Caption is required.",
            )
        )
    if plan.chart_type.value != "CORRELATION_MATRIX":
        missing_labels = [
            axis for axis in ("x", "y") if not parameters.get(f"{axis}_label")
        ]
        if missing_labels:
            issues.append(
                (
                    FigureIssueType.MISSING_AXIS_LABEL,
                    FigureIssueSeverity.WARNING,
                    "Axis labels use confirmed column names: "
                    + ", ".join(missing_labels),
                )
            )
        missing_units = [
            axis for axis in ("x", "y") if not parameters.get(f"{axis}_unit")
        ]
        if missing_units:
            issues.append(
                (
                    FigureIssueType.MISSING_UNIT,
                    FigureIssueSeverity.WARNING,
                    "Units require explicit review: " + ", ".join(missing_units),
                )
            )
    if (
        plan.chart_type.value == "GROUP_COMPARISON"
        and parameters.get("error_bar") == "NONE"
    ):
        issues.append(
            (
                FigureIssueType.UNDEFINED_ERROR_BAR,
                FigureIssueSeverity.WARNING,
                "No uncertainty interval is displayed.",
            )
        )
    if int(parameters.get("dpi", 144)) < 120:
        issues.append(
            (
                FigureIssueType.LOW_RESOLUTION,
                FigureIssueSeverity.WARNING,
                "DPI is below the publication baseline.",
            )
        )
    return issues


def _cleanup(storage_backend: ObjectStorage | None, keys: list[str]) -> None:
    backend = storage_backend or artifact_service.storage
    for key in keys:
        try:
            backend.delete_object(object_key=key)
        except Exception:
            pass


def execute_render_job(
    session: Session,
    *,
    job: Job,
    run_id: uuid.UUID,
    storage_backend: ObjectStorage | None = None,
) -> FigureRenderRun:
    render_run = session.exec(
        select(FigureRenderRun)
        .where(FigureRenderRun.id == job.resource_id)
        .with_for_update()
    ).first()
    if (
        render_run is None
        or job.resource_type != "figure_render_run"
        or render_run.project_id != job.project_id
        or render_run.status != FigureRenderRunStatus.QUEUED
    ):
        raise FigureExecutionError(
            "FIGURE_RENDER_STALE", "FigureRenderRun cannot be claimed."
        )
    plan = session.get(FigurePlan, render_run.figure_plan_id)
    version = session.get(DatasetVersion, render_run.dataset_version_id)
    actor = (
        session.get(User, render_run.requested_by) if render_run.requested_by else None
    )
    if plan is None or version is None or actor is None:
        raise FigureExecutionError(
            "FIGURE_RENDER_STALE", "Persisted render context is incomplete."
        )
    try:
        project_service.authorize_project(
            session,
            project_id=render_run.project_id,
            actor=actor,
            action="figure.render",
        )
        if (
            plan.status != FigurePlanStatus.READY
            or version.status != DatasetVersionStatus.AVAILABLE
            or plan.dataset_version_id != version.id
            or _hash(plan.parameters) != render_run.parameters_hash
        ):
            raise ContractError(
                status_code=409,
                code="FIGURE_RENDER_STALE",
                message="FigurePlan or DatasetVersion is stale.",
            )
        upstream_run, result = _assert_upstream(
            session,
            project_id=plan.project_id,
            version=version,
            analysis_run_id=plan.analysis_run_id,
            analysis_result_id=plan.analysis_result_id,
        )
        expected_input = _hash(
            {
                "plan_hash": plan.plan_hash,
                "data_hash": version.data_hash,
                "schema_hash": version.schema_hash,
                "projection_hash": version.projection_hash,
            }
        )
        if expected_input != render_run.input_hash:
            raise ContractError(
                status_code=409,
                code="INPUT_HASH_MISMATCH",
                message="Figure input hash is stale.",
            )
        create_payload = FigurePlanCreate.model_validate(
            {
                "dataset_version_id": plan.dataset_version_id,
                "analysis_run_id": plan.analysis_run_id,
                "analysis_result_id": plan.analysis_result_id,
                "chart_type": plan.chart_type,
                "parameters": plan.parameters,
                "caption": plan.caption,
            }
        )
        _assert_result_matches_plan(create_payload, result)
        columns = _columns(
            session,
            project_id=plan.project_id,
            version_id=version.id,
            ids=_parameter_column_ids(create_payload),
        )
        frame = analysis_service._load_frame(
            session, version=version, storage_backend=storage_backend
        )
        column_names = {str(column.id): column.source_name for column in columns}
        job_service.set_run_context(
            session,
            job_id=job.id,
            run_id=run_id,
            input_hash=render_run.input_hash,
            parameters={"figure_render_run_id": str(render_run.id)},
            implementation_metadata={"renderer": renderer.TEMPLATE_VERSION},
        )
        render_run.status = FigureRenderRunStatus.RUNNING
        render_run.processing_run_id = run_id
        render_run.started_at = get_datetime_utc()
        session.add(render_run)
        project_service._commit(session)
        output = renderer.render(
            frame=frame,
            parameters=create_payload.parameters,
            column_names=column_names,
            result_payload=result.payload if result else None,
        )
    except Exception as error:
        render_run.status = FigureRenderRunStatus.FAILED
        render_run.error_code = str(getattr(error, "code", "FIGURE_RENDER_FAILED"))
        render_run.completed_at = get_datetime_utc()
        session.add(render_run)
        project_service._commit(session)
        raise FigureExecutionError(
            render_run.error_code, "Deterministic Figure render failed."
        ) from error

    created_keys: list[str] = []
    try:
        specs = (
            ("png", output.png, "image/png", ArtifactType.FIGURE_PNG),
            ("svg", output.svg, "image/svg+xml", ArtifactType.FIGURE_SVG),
            ("pdf", output.pdf, "application/pdf", ArtifactType.FIGURE_PDF),
            ("py", output.code, "text/x-python", ArtifactType.ANALYSIS_CODE),
        )
        artifacts = {}
        for suffix, content, mime_type, artifact_type in specs:
            artifact = artifact_service.create_generated_bytes_artifact(
                session,
                project_id=render_run.project_id,
                content=content,
                filename=f"figure-{render_run.id}.{suffix}",
                mime_type=mime_type,
                artifact_type=artifact_type,
                metadata={
                    "figure_render_run_id": str(render_run.id),
                    "input_hash": render_run.input_hash,
                    "environment": output.environment,
                },
                created_by=render_run.requested_by,
                storage_backend=storage_backend,
            )
            created_keys.append(artifact.storage_key)
            artifacts[suffix] = artifact
        code_record = CodeArtifact(
            project_id=render_run.project_id,
            figure_render_run_id=render_run.id,
            artifact_id=artifacts["py"].id,
            template_version=renderer.TEMPLATE_VERSION,
            language="python",
            entry="app.figures.renderer.render",
            dependency_snapshot=output.environment,
            input_hash=render_run.input_hash,
            output_hash=artifacts["py"].sha256,
        )
        session.add(code_record)
        session.flush()
        version_number = (
            int(
                session.exec(
                    select(func.coalesce(func.max(Figure.version_number), 0)).where(
                        Figure.figure_plan_id == plan.id
                    )
                ).one()
            )
            + 1
        )
        issue_specs = _validation_issues(plan)
        figure_hash = _hash(
            {
                "input_hash": render_run.input_hash,
                "png": artifacts["png"].sha256,
                "svg": artifacts["svg"].sha256,
                "pdf": artifacts["pdf"].sha256,
                "code": artifacts["py"].sha256,
            }
        )
        figure = Figure(
            project_id=render_run.project_id,
            figure_plan_id=plan.id,
            figure_render_run_id=render_run.id,
            dataset_version_id=version.id,
            analysis_run_id=upstream_run.id if upstream_run else None,
            analysis_result_id=result.id if result else None,
            version_number=version_number,
            chart_type=plan.chart_type,
            status=FigureStatus.NEEDS_REVIEW if issue_specs else FigureStatus.READY,
            caption=plan.caption,
            figure_hash=figure_hash,
            png_artifact_id=artifacts["png"].id,
            svg_artifact_id=artifacts["svg"].id,
            pdf_artifact_id=artifacts["pdf"].id,
            code_artifact_id=code_record.id,
        )
        session.add(figure)
        session.flush()
        for issue_type, severity, message in issue_specs:
            session.add(
                FigureValidationIssue(
                    project_id=figure.project_id,
                    figure_id=figure.id,
                    issue_type=issue_type,
                    severity=severity,
                    status=FigureIssueStatus.OPEN,
                    message=message,
                    evidence={"plan_hash": plan.plan_hash},
                    blocks_confirmation=severity == FigureIssueSeverity.ERROR,
                )
            )
        render_run.status = FigureRenderRunStatus.COMPLETED
        render_run.environment_snapshot = output.environment
        render_run.environment_hash = _hash(output.environment)
        render_run.completed_at = get_datetime_utc()
        render_run.error_code = None
        session.add(render_run)
        project_service._commit(session)
        return render_run
    except Exception as error:
        session.rollback()
        _cleanup(storage_backend, created_keys)
        failed = session.get(FigureRenderRun, render_run.id)
        if failed is not None:
            failed.status = FigureRenderRunStatus.FAILED
            failed.error_code = "FIGURE_ARTIFACT_FINALIZE_FAILED"
            failed.completed_at = get_datetime_utc()
            session.add(failed)
            project_service._commit(session)
        raise FigureExecutionError(
            "FIGURE_ARTIFACT_FINALIZE_FAILED",
            "Figure Artifacts could not be finalized.",
        ) from error


def mark_cancelled_figure_job(session: Session, *, job: Job) -> None:
    run = session.get(FigureRenderRun, job.resource_id)
    if run is not None and run.status in {
        FigureRenderRunStatus.QUEUED,
        FigureRenderRunStatus.CANCEL_REQUESTED,
    }:
        run.status = FigureRenderRunStatus.CANCELLED
        run.completed_at = get_datetime_utc()
        session.add(run)
        project_service._commit(session)


def mark_failed_figure_job(
    session: Session,
    *,
    job: Job,
    error_code: str,
    worker_id: str,
) -> None:
    if (
        job.task_type != JobTaskType.FIGURE_RENDER
        or job.resource_type != "figure_render_run"
    ):
        return
    run = session.exec(
        select(FigureRenderRun)
        .where(FigureRenderRun.id == job.resource_id)
        .with_for_update()
    ).first()
    if run is None or run.project_id != job.project_id:
        return
    if run.status not in {
        FigureRenderRunStatus.QUEUED,
        FigureRenderRunStatus.RUNNING,
        FigureRenderRunStatus.CANCEL_REQUESTED,
    }:
        return
    run.status = FigureRenderRunStatus.FAILED
    run.error_code = error_code
    run.completed_at = get_datetime_utc()
    session.add(run)
    session.add(
        AuditLog(
            project_id=run.project_id,
            actor_type=AuditActorType.WORKER,
            actor_id=worker_id,
            action="FIGURE_RENDER_RUN_FAILED",
            object_type="figure_render_run",
            object_id=run.id,
            after_snapshot=jsonable_encoder(
                {"status": run.status, "error_code": run.error_code}
            ),
            job_id=job.id,
            outcome=AuditOutcome.FAILED,
        )
    )
