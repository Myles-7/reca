from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any, cast

import pandas as pd  # type: ignore[import-untyped]
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlmodel import Session, col, delete, select

from app.adapters.storage import ObjectStorage, StorageError
from app.analysis import engine
from app.analysis.registry import require_supported
from app.analysis.schemas import (
    AnalysisInvalidate,
    AnalysisPlanCreate,
    AnalysisPlanUpdate,
    AnalysisRunCreate,
    EngineColumn,
    EngineRequest,
)
from app.api.errors import ContractError
from app.approvals import service as approval_service
from app.artifacts import service as artifact_service
from app.core.observability import current_request_id
from app.data_quality.engine import load_dataframe
from app.jobs import service as job_service
from app.models import (
    AnalysisAssumptionCheck,
    AnalysisPlan,
    AnalysisPlanStatus,
    AnalysisResult,
    AnalysisResultType,
    AnalysisRun,
    AnalysisRunStatus,
    ApprovalRecord,
    ApprovalStatus,
    ApprovalType,
    Artifact,
    ArtifactStatus,
    ArtifactType,
    AssumptionCheckCode,
    AssumptionCheckStatus,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    CodeArtifact,
    DataQualityIssue,
    DataQualityIssueStatus,
    DataQualitySeverity,
    DatasetColumn,
    DatasetColumnConfirmationStatus,
    DatasetColumnType,
    DatasetFileFormat,
    DatasetVersion,
    DatasetVersionStatus,
    Figure,
    FigureStatus,
    Job,
    JobTaskType,
    ProjectMemberRole,
    ResearchQuestionVersion,
    ResearchQuestionVersionStatus,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

TARGET_OBJECT_TYPE = "analysis_plan"
RESULT_SCHEMA_VERSION = "analysis-result/1.0"
ENGINE_VERSION = "1.0.0"
CODE_TEMPLATE_VERSION = "reca-analysis-python/1.0.0"
VALIDATE_PATH = "/api/v1/analysis-plans/{plan_id}/validate"
RUN_PATH = "/api/v1/analysis-plans/{plan_id}/runs"


class AnalysisExecutionError(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def _encoded(value: Any) -> dict[str, Any]:
    return cast(dict[str, Any], jsonable_encoder(value))


def _hash(value: Any) -> str:
    encoded = json.dumps(
        jsonable_encoder(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _audit(
    session: Session,
    *,
    project_id: uuid.UUID,
    actor_type: AuditActorType,
    actor_id: str | None,
    action: str,
    object_type: str,
    object_id: uuid.UUID,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
    approval_id: uuid.UUID | None = None,
    job_id: uuid.UUID | None = None,
    outcome: AuditOutcome = AuditOutcome.SUCCEEDED,
) -> None:
    session.add(
        AuditLog(
            project_id=project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            after_snapshot=jsonable_encoder(after) if after is not None else None,
            reason=reason,
            request_id=current_request_id(),
            approval_id=approval_id,
            job_id=job_id,
            outcome=outcome,
        )
    )


def _role(access: project_service.ProjectAccess) -> ProjectMemberRole:
    assert access.membership is not None
    return access.membership.role


def _allowed_actions(role: ProjectMemberRole, plan: AnalysisPlan) -> list[str]:
    permissions = project_service.ROLE_ACTIONS[role]
    result = ["analysis_plan.read"]
    if (
        plan.status
        in {
            AnalysisPlanStatus.DRAFT,
            AnalysisPlanStatus.NEEDS_INPUT,
            AnalysisPlanStatus.READY,
        }
        and "analysis.create" in permissions
    ):
        result.extend(["analysis_plan.update", "analysis_plan.validate"])
    if plan.status == AnalysisPlanStatus.READY and "analysis.approve" in permissions:
        result.append("analysis_plan.request_approval")
    if plan.status == AnalysisPlanStatus.APPROVED and "analysis.run" in permissions:
        result.append("analysis_plan.run")
    if (
        plan.status != AnalysisPlanStatus.INVALIDATED
        and "analysis.invalidate" in permissions
    ):
        result.append("analysis_plan.invalidate")
    return result


def _approval_stale(session: Session, plan: AnalysisPlan) -> bool:
    if plan.approval_record_id is None or plan.payload_hash is None:
        return False
    approval = session.get(ApprovalRecord, plan.approval_record_id)
    if (
        approval is None
        or approval.project_id != plan.project_id
        or approval.target_object_type != TARGET_OBJECT_TYPE
        or approval.target_object_id != plan.id
        or approval.approval_type != ApprovalType.ANALYSIS_PLAN_APPROVAL
    ):
        return True
    return (
        project_service.request_hash(canonical_payload(session, plan))
        != approval.payload_hash
        or approval.payload_hash != plan.payload_hash
    )


def _checks(session: Session, plan_id: uuid.UUID) -> list[AnalysisAssumptionCheck]:
    return list(
        session.exec(
            select(AnalysisAssumptionCheck)
            .where(AnalysisAssumptionCheck.analysis_plan_id == plan_id)
            .order_by(
                col(AnalysisAssumptionCheck.check_code),
                col(AnalysisAssumptionCheck.subject_key),
            )
        )
    )


def _plan_data(
    session: Session, plan: AnalysisPlan, role: ProjectMemberRole
) -> dict[str, Any]:
    return _encoded(
        {
            **plan.model_dump(),
            "checks": _checks(session, plan.id),
            "approval_stale": _approval_stale(session, plan),
            "allowed_actions": _allowed_actions(role, plan),
        }
    )


def _visible_plan(
    session: Session,
    *,
    actor: User,
    plan_id: uuid.UUID,
    action: str,
    for_update: bool = False,
) -> tuple[AnalysisPlan, project_service.ProjectAccess]:
    statement = select(AnalysisPlan).where(AnalysisPlan.id == plan_id)
    if for_update:
        statement = statement.with_for_update()
    plan = session.exec(statement.execution_options(populate_existing=True)).first()
    if plan is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    access = project_service.authorize_project(
        session,
        project_id=plan.project_id,
        actor=actor,
        action=action,
        for_update=for_update,
    )
    return plan, access


def _column_ids(plan: AnalysisPlan) -> list[uuid.UUID]:
    return [
        uuid.UUID(value)
        for value in plan.independent_variable_ids
        + plan.dependent_variable_ids
        + plan.control_variable_ids
    ]


def _columns(session: Session, plan: AnalysisPlan) -> list[DatasetColumn]:
    ids = _column_ids(plan)
    rows = list(
        session.exec(select(DatasetColumn).where(col(DatasetColumn.id).in_(ids)))
    )
    by_id = {row.id: row for row in rows}
    if len(by_id) != len(ids) or any(
        row.project_id != plan.project_id
        or row.dataset_version_id != plan.dataset_version_id
        for row in rows
    ):
        raise ContractError(
            status_code=409,
            code="ANALYSIS_COLUMN_STALE",
            message="A declared column is outside the approved DatasetVersion.",
        )
    return [by_id[column_id] for column_id in ids]


def _assert_columns_confirmed(plan: AnalysisPlan, columns: list[DatasetColumn]) -> None:
    if any(
        column.confirmation_status != DatasetColumnConfirmationStatus.CONFIRMED
        or column.confirmed_type is None
        for column in columns
    ):
        raise ContractError(
            status_code=409,
            code="COLUMN_NOT_CONFIRMED",
            message="Every analysis column must have a confirmed type.",
        )
    acknowledgements = set(plan.parameters.get("sensitive_column_acknowledgements", []))
    if any(
        column.is_sensitive and str(column.id) not in acknowledgements
        for column in columns
    ):
        raise ContractError(
            status_code=409,
            code="SENSITIVE_COLUMN_ACKNOWLEDGEMENT_REQUIRED",
            message="Sensitive analysis columns require explicit acknowledgement.",
        )


def _assert_quality_acknowledged(session: Session, plan: AnalysisPlan) -> None:
    issues = list(
        session.exec(
            select(DataQualityIssue).where(
                DataQualityIssue.dataset_version_id == plan.dataset_version_id,
                DataQualityIssue.severity == DataQualitySeverity.HIGH,
                col(DataQualityIssue.status).in_(
                    [DataQualityIssueStatus.OPEN, DataQualityIssueStatus.ACKNOWLEDGED]
                ),
            )
        )
    )
    acknowledged = set(plan.parameters.get("acknowledged_quality_issue_ids", []))
    missing = [issue for issue in issues if str(issue.id) not in acknowledged]
    if missing:
        raise ContractError(
            status_code=409,
            code="QUALITY_ACKNOWLEDGEMENT_REQUIRED",
            message="Open high-severity quality issues require explicit acknowledgement.",
        )


def _load_frame(
    session: Session,
    *,
    version: DatasetVersion,
    storage_backend: ObjectStorage | None = None,
) -> pd.DataFrame:
    artifact = session.get(Artifact, version.artifact_id)
    if (
        artifact is None
        or artifact.project_id != version.project_id
        or artifact.status != ArtifactStatus.AVAILABLE
        or artifact.sha256 != version.data_hash
    ):
        raise ContractError(
            status_code=409,
            code="DATASET_HASH_MISMATCH",
            message="The Dataset Artifact identity is invalid.",
        )
    suffix = ".csv" if version.file_format == DatasetFileFormat.CSV else ".xlsx"
    with tempfile.TemporaryDirectory(prefix="reca-analysis-source-") as directory:
        path = Path(directory) / f"source{suffix}"
        try:
            artifact_service.download_available_artifact_to_path(
                session,
                artifact_id=artifact.id,
                project_id=version.project_id,
                path=path,
                storage_backend=storage_backend,
            )
        except StorageError as error:
            raise ContractError(
                status_code=409,
                code="DATASET_HASH_MISMATCH",
                message="The Dataset Artifact bytes do not match its immutable hash.",
            ) from error
        return load_dataframe(path, version=version)


def _apply_filter(
    frame: pd.DataFrame, plan: AnalysisPlan, columns: list[DatasetColumn]
) -> pd.DataFrame:
    raw = plan.sample_filter
    if raw is None:
        return frame
    by_id = {str(column.id): column.source_name for column in columns}
    name = by_id.get(str(raw.get("column_id")))
    if name is None:
        raise ContractError(
            status_code=409,
            code="SAMPLE_FILTER_STALE",
            message="The sample filter column is not declared by the plan.",
        )
    operator = raw["operator"]
    series = frame[name]
    if operator == "EQUALS":
        mask = series == raw["value"]
    elif operator == "IN":
        mask = series.isin(raw["values"])
    elif operator == "IS_NULL":
        mask = series.isna()
    elif operator == "IS_NOT_NULL":
        mask = series.notna()
    elif operator == "NUMERIC_RANGE":
        numeric = pd.to_numeric(series, errors="coerce")
        mask = numeric.notna()
        if raw.get("minimum") is not None:
            mask &= (
                numeric.ge(raw["minimum"])
                if raw.get("include_minimum", True)
                else numeric.gt(raw["minimum"])
            )
        if raw.get("maximum") is not None:
            mask &= (
                numeric.le(raw["maximum"])
                if raw.get("include_maximum", True)
                else numeric.lt(raw["maximum"])
            )
    else:
        raise ContractError(
            status_code=409,
            code="SAMPLE_FILTER_STALE",
            message="The persisted sample filter is not whitelisted.",
        )
    return frame.loc[mask].copy()


def _engine_request(plan: AnalysisPlan, columns: list[DatasetColumn]) -> EngineRequest:
    items = [
        EngineColumn(
            column_id=column.id,
            name=column.source_name,
            kind="numeric"
            if column.confirmed_type
            in {DatasetColumnType.INTEGER, DatasetColumnType.NUMERIC}
            else "categorical",
        )
        for column in columns
    ]
    return EngineRequest.model_validate(
        {
            "method": plan.method,
            "columns": items,
            "missing_data_policy": plan.missing_data_policy,
            "parameters": plan.parameters,
        }
    )


def create_plan(
    session: Session, *, actor: User, project_id: uuid.UUID, payload: AnalysisPlanCreate
) -> dict[str, Any]:
    access = project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="analysis.create",
        for_update=True,
    )
    question = session.get(
        ResearchQuestionVersion, payload.research_question_version_id
    )
    version = session.get(DatasetVersion, payload.dataset_version_id)
    if (
        question is None
        or question.project_id != project_id
        or question.status != ResearchQuestionVersionStatus.CONFIRMED
        or version is None
        or version.project_id != project_id
    ):
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    if version.status != DatasetVersionStatus.AVAILABLE:
        raise ContractError(
            status_code=409,
            code="DATASET_VERSION_NOT_AVAILABLE",
            message="Only an AVAILABLE DatasetVersion can be analyzed.",
        )
    require_supported(payload.method)
    plan = AnalysisPlan(
        project_id=project_id,
        research_question_version_id=question.id,
        dataset_version_id=version.id,
        analysis_goal=payload.analysis_goal,
        method=payload.method,
        dependent_variable_ids=[str(value) for value in payload.dependent_variable_ids],
        independent_variable_ids=[
            str(value) for value in payload.independent_variable_ids
        ],
        control_variable_ids=[str(value) for value in payload.control_variable_ids],
        missing_data_policy=payload.missing_data_policy.model_dump(mode="json"),
        sample_filter=payload.sample_filter.model_dump(mode="json")
        if payload.sample_filter
        else None,
        parameters=payload.parameters.model_dump(mode="json"),
        created_by=actor.id,
    )
    session.add(plan)
    session.flush()
    columns = _columns(session, plan)
    _assert_columns_confirmed(plan, columns)
    _audit(
        session,
        project_id=plan.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="ANALYSIS_PLAN_CREATED",
        object_type=TARGET_OBJECT_TYPE,
        object_id=plan.id,
        after={"status": plan.status, "method": plan.method},
    )
    data = _plan_data(session, plan, _role(access))
    project_service._commit(session)
    return data


def get_plan(session: Session, *, actor: User, plan_id: uuid.UUID) -> dict[str, Any]:
    plan, access = _visible_plan(
        session, actor=actor, plan_id=plan_id, action="analysis.read"
    )
    return _plan_data(session, plan, _role(access))


def update_plan(
    session: Session,
    *,
    actor: User,
    plan_id: uuid.UUID,
    payload: AnalysisPlanUpdate,
    expected_lock_version: int,
) -> dict[str, Any]:
    plan, access = _visible_plan(
        session, actor=actor, plan_id=plan_id, action="analysis.create", for_update=True
    )
    if plan.status not in {
        AnalysisPlanStatus.DRAFT,
        AnalysisPlanStatus.NEEDS_INPUT,
        AnalysisPlanStatus.READY,
    }:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="The AnalysisPlan is immutable in its current state.",
        )
    if plan.lock_version != expected_lock_version:
        raise ContractError(
            status_code=412,
            code="PRECONDITION_FAILED",
            message="The AnalysisPlan lock version is stale.",
        )
    changes = payload.model_dump(exclude_unset=True, mode="json")
    for key, value in changes.items():
        setattr(plan, key, value)
    plan.status = AnalysisPlanStatus.DRAFT
    plan.validation_hash = None
    plan.validation_warnings = []
    plan.approval_record_id = None
    plan.payload_hash = None
    plan.lock_version += 1
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    columns = _columns(session, plan)
    _assert_columns_confirmed(plan, columns)
    _audit(
        session,
        project_id=plan.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="ANALYSIS_PLAN_UPDATED",
        object_type=TARGET_OBJECT_TYPE,
        object_id=plan.id,
        after={"status": plan.status, "lock_version": plan.lock_version},
    )
    data = _plan_data(session, plan, _role(access))
    project_service._commit(session)
    return data


def validate_plan(
    session: Session,
    *,
    actor: User,
    plan_id: uuid.UUID,
    idempotency_key: str,
    storage_backend: ObjectStorage | None = None,
) -> project_service.OperationResult:
    plan, access = _visible_plan(
        session, actor=actor, plan_id=plan_id, action="analysis.create", for_update=True
    )
    digest = project_service.request_hash(
        {"plan_id": str(plan.id), "lock_version": plan.lock_version}
    )
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=VALIDATE_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    if plan.status not in {
        AnalysisPlanStatus.DRAFT,
        AnalysisPlanStatus.NEEDS_INPUT,
        AnalysisPlanStatus.READY,
    }:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="The AnalysisPlan cannot be validated in its current state.",
        )
    version = session.get(DatasetVersion, plan.dataset_version_id)
    if version is None or version.status != DatasetVersionStatus.AVAILABLE:
        raise ContractError(
            status_code=409,
            code="DATASET_VERSION_NOT_AVAILABLE",
            message="The DatasetVersion is not available.",
        )
    columns = _columns(session, plan)
    _assert_columns_confirmed(plan, columns)
    _assert_quality_acknowledged(session, plan)
    frame = _apply_filter(
        _load_frame(session, version=version, storage_backend=storage_backend),
        plan,
        columns,
    )
    checks = engine.validate(frame, _engine_request(plan, columns))
    session.exec(
        delete(AnalysisAssumptionCheck).where(
            col(AnalysisAssumptionCheck.analysis_plan_id) == plan.id
        )
    )
    for check in checks:
        session.add(
            AnalysisAssumptionCheck(
                project_id=plan.project_id,
                analysis_plan_id=plan.id,
                check_code=AssumptionCheckCode(check.check_code),
                subject_key=check.subject_key,
                status=AssumptionCheckStatus(check.status),
                explanation=check.explanation,
                evidence=check.evidence,
                blocks_approval=check.blocks_approval,
            )
        )
    blocking = any(
        check.blocks_approval
        and check.status in {"FAILED", "UNKNOWN", "REQUIRES_USER_CONFIRMATION"}
        for check in checks
    )
    plan.status = (
        AnalysisPlanStatus.NEEDS_INPUT if blocking else AnalysisPlanStatus.READY
    )
    plan.validation_warnings = [
        check.explanation
        for check in checks
        if check.status in {"WARNING", "REQUIRES_USER_CONFIRMATION"}
    ]
    plan.validation_hash = _hash(
        {"plan": canonical_payload(session, plan), "checks": checks}
    )
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    _audit(
        session,
        project_id=plan.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="ANALYSIS_PLAN_VALIDATED",
        object_type=TARGET_OBJECT_TYPE,
        object_id=plan.id,
        after={"status": plan.status, "validation_hash": plan.validation_hash},
    )
    session.flush()
    result = project_service.OperationResult(
        data=_plan_data(session, plan, _role(access)), status_code=200
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=VALIDATE_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result


def canonical_payload(session: Session, plan: AnalysisPlan) -> dict[str, Any]:
    version = session.get(DatasetVersion, plan.dataset_version_id)
    if version is None:
        raise ContractError(
            status_code=409,
            code="DATASET_VERSION_STALE",
            message="The DatasetVersion no longer exists.",
        )
    columns = _columns(session, plan)
    return {
        "schema_version": "analysis-plan-approval/1.0",
        "project_id": str(plan.project_id),
        "analysis_plan_id": str(plan.id),
        "plan_lock_version": plan.lock_version,
        "research_question_version_id": str(plan.research_question_version_id),
        "dataset_version_id": str(version.id),
        "data_hash": version.data_hash,
        "schema_hash": version.schema_hash,
        "projection_hash": version.projection_hash,
        "method": plan.method.value,
        "analysis_goal": plan.analysis_goal.value,
        "dependent_variable_ids": plan.dependent_variable_ids,
        "independent_variable_ids": plan.independent_variable_ids,
        "control_variable_ids": plan.control_variable_ids,
        "confirmed_columns": [
            {
                "id": str(column.id),
                "source_name": column.source_name,
                "confirmed_type": column.confirmed_type,
                "is_sensitive": column.is_sensitive,
            }
            for column in columns
        ],
        "missing_data_policy": plan.missing_data_policy,
        "sample_filter": plan.sample_filter,
        "parameters": plan.parameters,
        "validation_hash": plan.validation_hash,
    }


def resolve_approval_payload(
    session: Session, approval: ApprovalRecord
) -> dict[str, Any]:
    plan = session.exec(
        select(AnalysisPlan).where(
            AnalysisPlan.id == approval.target_object_id,
            AnalysisPlan.project_id == approval.project_id,
        )
    ).first()
    if plan is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    return canonical_payload(session, plan)


def apply_approval_decision(
    session: Session, approval: ApprovalRecord, decision: ApprovalStatus, _actor: User
) -> None:
    if approval.approval_type != ApprovalType.ANALYSIS_PLAN_APPROVAL:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Approval type does not match AnalysisPlan approval.",
        )
    plan = session.exec(
        select(AnalysisPlan)
        .where(
            AnalysisPlan.id == approval.target_object_id,
            AnalysisPlan.project_id == approval.project_id,
        )
        .with_for_update()
    ).first()
    if plan is None or plan.approval_record_id != approval.id:
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="The AnalysisPlan no longer references this Approval.",
        )
    if plan.status != AnalysisPlanStatus.NEEDS_APPROVAL:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Only NEEDS_APPROVAL can receive a decision.",
        )
    plan.status = (
        AnalysisPlanStatus.APPROVED
        if decision == ApprovalStatus.APPROVED
        else AnalysisPlanStatus.REJECTED
    )
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    _audit(
        session,
        project_id=plan.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(_actor.id),
        action=(
            "ANALYSIS_PLAN_APPROVED"
            if decision == ApprovalStatus.APPROVED
            else "ANALYSIS_PLAN_REJECTED"
        ),
        object_type=TARGET_OBJECT_TYPE,
        object_id=plan.id,
        approval_id=approval.id,
        after={"status": plan.status},
    )


def register_approval_handlers() -> None:
    approval_service.register_payload_resolver(
        TARGET_OBJECT_TYPE, resolve_approval_payload
    )
    approval_service.register_decision_handler(
        TARGET_OBJECT_TYPE, apply_approval_decision
    )


def request_approval(
    session: Session, *, actor: User, plan_id: uuid.UUID
) -> dict[str, Any]:
    plan, access = _visible_plan(
        session, actor=actor, plan_id=plan_id, action="analysis.create", for_update=True
    )
    if plan.status != AnalysisPlanStatus.READY or not plan.validation_hash:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="A validated READY AnalysisPlan is required.",
        )
    snapshot = canonical_payload(session, plan)
    approval = approval_service.create_approval(
        session,
        command=approval_service.ApprovalCreate(
            project_id=plan.project_id,
            approval_type=ApprovalType.ANALYSIS_PLAN_APPROVAL,
            target_object_type=TARGET_OBJECT_TYPE,
            target_object_id=plan.id,
            requested_by_actor_type=AuditActorType.USER,
            requested_by_actor_id=str(actor.id),
            payload_snapshot=snapshot,
            impact_summary={
                "method": plan.method,
                "dataset_version_id": str(plan.dataset_version_id),
            },
            expires_at=get_datetime_utc() + timedelta(hours=24),
        ),
    )
    plan.status = AnalysisPlanStatus.NEEDS_APPROVAL
    plan.approval_record_id = approval.id
    plan.payload_hash = approval.payload_hash
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    _audit(
        session,
        project_id=plan.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="ANALYSIS_PLAN_APPROVAL_REQUESTED",
        object_type=TARGET_OBJECT_TYPE,
        object_id=plan.id,
        approval_id=approval.id,
        after={"status": plan.status, "payload_hash": approval.payload_hash},
    )
    project_service._commit(session)
    return _encoded(
        {
            "approval_id": approval.id,
            "analysis_plan_id": plan.id,
            "status": approval.status,
            "payload_hash": approval.payload_hash,
            "expires_at": approval.expires_at,
        }
    )


def _fresh_approval(session: Session, plan: AnalysisPlan) -> ApprovalRecord:
    if plan.approval_record_id is None or plan.payload_hash is None:
        raise ContractError(
            status_code=409,
            code="APPROVAL_REQUIRED",
            message="The AnalysisPlan has no formal Approval.",
        )
    approval = session.exec(
        select(ApprovalRecord)
        .where(ApprovalRecord.id == plan.approval_record_id)
        .with_for_update()
    ).first()
    if (
        approval is None
        or approval.project_id != plan.project_id
        or approval.target_object_type != TARGET_OBJECT_TYPE
        or approval.target_object_id != plan.id
        or approval.approval_type != ApprovalType.ANALYSIS_PLAN_APPROVAL
    ):
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="The Approval target does not match the AnalysisPlan.",
        )
    if approval.status != ApprovalStatus.APPROVED:
        raise ContractError(
            status_code=409,
            code="APPROVAL_REQUIRED",
            message="The AnalysisPlan Approval is not APPROVED.",
        )
    if approval.expires_at is not None and approval.expires_at <= get_datetime_utc():
        raise ContractError(
            status_code=409,
            code="APPROVAL_EXPIRED",
            message="The AnalysisPlan Approval has expired.",
        )
    current = canonical_payload(session, plan)
    if (
        project_service.request_hash(current) != approval.payload_hash
        or approval.payload_hash != plan.payload_hash
    ):
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="The AnalysisPlan Approval payload is stale.",
        )
    return approval


def create_run(
    session: Session,
    *,
    actor: User,
    plan_id: uuid.UUID,
    payload: AnalysisRunCreate,
    idempotency_key: str,
    dispatcher: job_service.JobDispatcher,
) -> project_service.OperationResult:
    plan, access = _visible_plan(
        session, actor=actor, plan_id=plan_id, action="analysis.run", for_update=True
    )
    digest = project_service.request_hash({"plan_id": str(plan.id), "payload": payload})
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=RUN_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    if plan.status != AnalysisPlanStatus.APPROVED:
        raise ContractError(
            status_code=409,
            code="APPROVAL_REQUIRED",
            message="Only an APPROVED AnalysisPlan can run.",
        )
    version = session.get(DatasetVersion, plan.dataset_version_id)
    if version is None or version.status != DatasetVersionStatus.AVAILABLE:
        raise ContractError(
            status_code=409,
            code="DATASET_VERSION_NOT_AVAILABLE",
            message="The approved DatasetVersion is not available.",
        )
    approval = _fresh_approval(session, plan)
    columns = _columns(session, plan)
    _assert_columns_confirmed(plan, columns)
    _assert_quality_acknowledged(session, plan)
    require_supported(plan.method)
    artifact = session.get(Artifact, version.artifact_id)
    if (
        artifact is None
        or artifact.status != ArtifactStatus.AVAILABLE
        or artifact.sha256 != version.data_hash
    ):
        raise ContractError(
            status_code=409,
            code="DATASET_HASH_MISMATCH",
            message="The Dataset Artifact identity is invalid.",
        )
    run_number = (
        int(
            session.exec(
                select(func.count())
                .select_from(AnalysisRun)
                .where(AnalysisRun.analysis_plan_id == plan.id)
            ).one()
        )
        + 1
    )
    input_hash = _hash(
        {
            "approval_payload_hash": approval.payload_hash,
            "data_hash": version.data_hash,
            "schema_hash": version.schema_hash,
            "projection_hash": version.projection_hash,
        }
    )
    parameters_hash = _hash(
        {
            "method": plan.method,
            "missing": plan.missing_data_policy,
            "sample_filter": plan.sample_filter,
            "parameters": plan.parameters,
            "engine_version": ENGINE_VERSION,
        }
    )
    run = AnalysisRun(
        project_id=plan.project_id,
        analysis_plan_id=plan.id,
        dataset_version_id=version.id,
        approval_record_id=approval.id,
        run_number=run_number,
        idempotency_key=idempotency_key,
        run_reason=payload.run_reason,
        parameters_hash=parameters_hash,
        input_hash=input_hash,
        requested_by=actor.id,
    )
    session.add(run)
    session.flush()
    job = job_service.create_job(
        session,
        project_id=plan.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.ANALYSIS_RUN,
            resource_type="analysis_run",
            resource_id=run.id,
            idempotency_key=idempotency_key,
            requested_by_user_id=actor.id,
            max_retries=2,
            retryable=True,
        ),
    )
    _audit(
        session,
        project_id=run.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="ANALYSIS_RUN_REQUESTED",
        object_type="analysis_run",
        object_id=run.id,
        approval_id=approval.id,
        job_id=job.id,
        after={"status": run.status, "run_number": run.run_number},
    )
    initial = project_service.OperationResult(
        data={
            "analysis_run": _run_data(session, run, _role(access)),
            "job": job_service.job_data(session, job),
        },
        status_code=202,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=RUN_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=initial,
    )
    project_service._commit(session)
    dispatched = job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)
    data = {
        "analysis_run": _run_data(session, run, _role(access)),
        "job": job_service.job_data(session, dispatched),
    }
    record = session.exec(
        project_service._idempotency_statement(
            actor_id=actor.id,
            project_id=plan.project_id,
            method="POST",
            path_template=RUN_PATH,
            key=idempotency_key,
        ).with_for_update()
    ).one()
    record.response_body = jsonable_encoder(data)
    session.add(record)
    project_service._commit(session)
    return project_service.OperationResult(data=data, status_code=202)


def _run_data(
    session: Session, run: AnalysisRun, role: ProjectMemberRole
) -> dict[str, Any]:
    job = session.exec(
        select(Job).where(
            Job.resource_type == "analysis_run", Job.resource_id == run.id
        )
    ).first()
    return _encoded(
        {
            **run.model_dump(),
            "job_id": job.id if job else None,
            "result_count": session.exec(
                select(func.count())
                .select_from(AnalysisResult)
                .where(AnalysisResult.analysis_run_id == run.id)
            ).one(),
            "allowed_actions": (
                ["analysis_run.invalidate"]
                if run.status == AnalysisRunStatus.COMPLETED
                and "analysis.invalidate" in project_service.ROLE_ACTIONS[role]
                else []
            ),
        }
    )


def get_run(session: Session, *, actor: User, run_id: uuid.UUID) -> dict[str, Any]:
    run = session.get(AnalysisRun, run_id)
    if run is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    access = project_service.authorize_project(
        session, project_id=run.project_id, actor=actor, action="analysis.read"
    )
    return _run_data(session, run, _role(access))


def get_results(session: Session, *, actor: User, run_id: uuid.UUID) -> dict[str, Any]:
    run = session.get(AnalysisRun, run_id)
    if run is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    project_service.authorize_project(
        session, project_id=run.project_id, actor=actor, action="analysis.read"
    )
    rows = list(
        session.exec(
            select(AnalysisResult)
            .where(AnalysisResult.analysis_run_id == run.id)
            .order_by(col(AnalysisResult.result_key))
        )
    )
    return _encoded(
        {
            "analysis_run_id": run.id,
            "dataset_version_id": run.dataset_version_id,
            "status": run.status,
            "results": rows,
            "code_artifact_id": run.code_artifact_id,
            "log_artifact_id": run.log_artifact_id,
            "environment": run.environment_snapshot,
        }
    )


def invalidate_run(
    session: Session, *, actor: User, run_id: uuid.UUID, payload: AnalysisInvalidate
) -> dict[str, Any]:
    run = session.exec(
        select(AnalysisRun).where(AnalysisRun.id == run_id).with_for_update()
    ).first()
    if run is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    access = project_service.authorize_project(
        session,
        project_id=run.project_id,
        actor=actor,
        action="analysis.invalidate",
        for_update=True,
    )
    if run.status != AnalysisRunStatus.COMPLETED:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Only a COMPLETED AnalysisRun can be invalidated.",
        )
    run.status = AnalysisRunStatus.INVALIDATED
    run.invalidated_at = get_datetime_utc()
    run.invalidation_reason = payload.reason.strip()
    session.add(run)
    from app.evidence_graph.invalidation import propagate_invalidation
    from app.models import EvidenceObjectType

    propagate_invalidation(
        session,
        project_id=run.project_id,
        object_type=EvidenceObjectType.ANALYSIS_RUN,
        object_id=run.id,
        reason=run.invalidation_reason,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
    )
    for result in session.exec(
        select(AnalysisResult).where(AnalysisResult.analysis_run_id == run.id)
    ):
        propagate_invalidation(
            session,
            project_id=run.project_id,
            object_type=EvidenceObjectType.ANALYSIS_RESULT,
            object_id=result.id,
            reason=run.invalidation_reason,
            source_hash=result.result_hash,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
        )
    for figure in session.exec(
        select(Figure).where(
            Figure.analysis_run_id == run.id,
            Figure.status != FigureStatus.INVALIDATED,
        )
    ):
        figure.status = FigureStatus.INVALIDATED
        figure.invalidated_at = run.invalidated_at
        figure.invalidation_reason = (
            f"Upstream AnalysisRun invalidated: {run.invalidation_reason}"
        )
        session.add(figure)
        propagate_invalidation(
            session,
            project_id=run.project_id,
            object_type=EvidenceObjectType.FIGURE,
            object_id=figure.id,
            reason=figure.invalidation_reason,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
        )
    _audit(
        session,
        project_id=run.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="ANALYSIS_RUN_INVALIDATED",
        object_type="analysis_run",
        object_id=run.id,
        reason=run.invalidation_reason,
        after={"status": run.status},
    )
    data = _run_data(session, run, _role(access))
    project_service._commit(session)
    return data


def _environment() -> dict[str, str]:
    packages = ("numpy", "pandas", "scipy", "statsmodels")
    return {
        "python": platform.python_version(),
        **{package: importlib.metadata.version(package) for package in packages},
    }


def _fixed_code(plan: AnalysisPlan) -> bytes:
    return (
        "# Generated by RECA. User/model code is never executed.\n"
        f"METHOD = {plan.method.value!r}\n"
        f"TEMPLATE_VERSION = {CODE_TEMPLATE_VERSION!r}\n"
        "# Execution is performed by app.analysis.engine using the approved canonical plan.\n"
    ).encode()


def _cleanup(storage_backend: ObjectStorage | None, keys: list[str]) -> None:
    backend = storage_backend or artifact_service.storage
    for key in keys:
        try:
            backend.delete_object(object_key=key)
        except Exception:
            pass


def execute_analysis_job(
    session: Session,
    *,
    job: Job,
    run_id: uuid.UUID,
    storage_backend: ObjectStorage | None = None,
) -> AnalysisRun:
    run = session.exec(
        select(AnalysisRun).where(AnalysisRun.id == job.resource_id).with_for_update()
    ).first()
    if (
        run is None
        or job.resource_type != "analysis_run"
        or run.project_id != job.project_id
        or run.status != AnalysisRunStatus.QUEUED
    ):
        raise AnalysisExecutionError(
            "ANALYSIS_RUN_STALE", "The AnalysisRun cannot be claimed."
        )
    plan = session.get(AnalysisPlan, run.analysis_plan_id)
    version = session.get(DatasetVersion, run.dataset_version_id)
    actor = session.get(User, run.requested_by) if run.requested_by else None
    if (
        plan is None
        or version is None
        or actor is None
        or plan.project_id != run.project_id
        or version.project_id != run.project_id
    ):
        raise AnalysisExecutionError(
            "ANALYSIS_RUN_STALE", "The persisted execution context is incomplete."
        )
    try:
        project_service.authorize_project(
            session, project_id=run.project_id, actor=actor, action="analysis.run"
        )
        if (
            plan.status != AnalysisPlanStatus.APPROVED
            or version.status != DatasetVersionStatus.AVAILABLE
            or plan.dataset_version_id != version.id
        ):
            raise ContractError(
                status_code=409,
                code="ANALYSIS_RUN_STALE",
                message="The approved plan or DatasetVersion is stale.",
            )
        approval = _fresh_approval(session, plan)
        if approval.id != run.approval_record_id:
            raise ContractError(
                status_code=409,
                code="APPROVAL_STALE",
                message="The Run Approval snapshot is stale.",
            )
        columns = _columns(session, plan)
        _assert_columns_confirmed(plan, columns)
        _assert_quality_acknowledged(session, plan)
        expected_input = _hash(
            {
                "approval_payload_hash": approval.payload_hash,
                "data_hash": version.data_hash,
                "schema_hash": version.schema_hash,
                "projection_hash": version.projection_hash,
            }
        )
        if expected_input != run.input_hash:
            raise ContractError(
                status_code=409,
                code="INPUT_HASH_MISMATCH",
                message="The immutable analysis input hash is stale.",
            )
        frame = _apply_filter(
            _load_frame(session, version=version, storage_backend=storage_backend),
            plan,
            columns,
        )
        environment = _environment()
        job_service.set_run_context(
            session,
            job_id=job.id,
            run_id=run_id,
            input_hash=run.input_hash,
            parameters={
                "analysis_run_id": str(run.id),
                "parameters_hash": run.parameters_hash,
            },
            implementation_metadata={
                "engine": "reca-statistical-engine",
                "engine_version": ENGINE_VERSION,
                "environment": environment,
            },
        )
        run = session.exec(
            select(AnalysisRun).where(AnalysisRun.id == run.id).with_for_update()
        ).one()
        run.status = AnalysisRunStatus.RUNNING
        run.processing_run_id = run_id
        run.started_at = get_datetime_utc()
        session.add(run)
        project_service._commit(session)
        output = engine.execute(frame, _engine_request(plan, columns))
    except ContractError as error:
        run.status = AnalysisRunStatus.FAILED
        run.error_code = error.code
        run.completed_at = get_datetime_utc()
        session.add(run)
        _audit(
            session,
            project_id=run.project_id,
            actor_type=AuditActorType.WORKER,
            actor_id="reca-worker",
            action="ANALYSIS_RUN_FAILED",
            object_type="analysis_run",
            object_id=run.id,
            job_id=job.id,
            after={"status": run.status, "error_code": run.error_code},
            outcome=AuditOutcome.FAILED,
        )
        project_service._commit(session)
        raise AnalysisExecutionError(error.code, error.message, False) from error
    except Exception as error:
        run.status = AnalysisRunStatus.FAILED
        run.error_code = "EXTERNAL_OUTPUT_INVALID"
        run.completed_at = get_datetime_utc()
        session.add(run)
        _audit(
            session,
            project_id=run.project_id,
            actor_type=AuditActorType.WORKER,
            actor_id="reca-worker",
            action="ANALYSIS_RUN_FAILED",
            object_type="analysis_run",
            object_id=run.id,
            job_id=job.id,
            after={"status": run.status, "error_code": run.error_code},
            outcome=AuditOutcome.FAILED,
        )
        project_service._commit(session)
        raise AnalysisExecutionError(
            "EXTERNAL_OUTPUT_INVALID",
            "The deterministic engine returned invalid output.",
            False,
        ) from error

    created_keys: list[str] = []
    try:
        code_bytes = _fixed_code(plan)
        code = artifact_service.create_generated_bytes_artifact(
            session,
            project_id=run.project_id,
            content=code_bytes,
            filename=f"analysis-{run.id}.py",
            mime_type="text/x-python",
            artifact_type=ArtifactType.ANALYSIS_CODE,
            metadata={
                "template_version": CODE_TEMPLATE_VERSION,
                "analysis_run_id": str(run.id),
                "input_hash": run.input_hash,
            },
            created_by=run.requested_by,
            storage_backend=storage_backend,
        )
        created_keys.append(code.storage_key)
        log_payload = {
            "schema_version": "analysis-log/1.0",
            "analysis_run_id": str(run.id),
            "method": plan.method.value,
            "effective_n": output.effective_n,
            "warnings": output.warnings,
            "result_count": len(output.results),
            "input_hash": run.input_hash,
        }
        log = artifact_service.create_generated_json_artifact(
            session,
            project_id=run.project_id,
            payload=log_payload,
            filename=f"analysis-{run.id}-log.json",
            artifact_type=ArtifactType.ANALYSIS_LOG,
            metadata={"analysis_run_id": str(run.id)},
            created_by=run.requested_by,
            storage_backend=storage_backend,
        )
        created_keys.append(log.storage_key)
        code_record = CodeArtifact(
            project_id=run.project_id,
            analysis_run_id=run.id,
            artifact_id=code.id,
            template_version=CODE_TEMPLATE_VERSION,
            language="python",
            entry="app.analysis.engine.execute",
            dependency_snapshot=environment,
            input_hash=run.input_hash,
            output_hash=code.sha256,
        )
        session.add(code_record)
        session.flush()
        for item in output.results:
            payload = item.payload
            session.add(
                AnalysisResult(
                    project_id=run.project_id,
                    analysis_run_id=run.id,
                    result_key=item.result_key,
                    result_type=AnalysisResultType(item.result_type),
                    schema_version=RESULT_SCHEMA_VERSION,
                    is_primary=item.is_primary,
                    payload=payload,
                    result_hash=_hash(payload),
                )
            )
        run.code_artifact_id = code_record.id
        run.log_artifact_id = log.id
        run.environment_snapshot = environment
        run.environment_hash = _hash(environment)
        run.effective_n = output.effective_n
        run.status = AnalysisRunStatus.COMPLETED
        run.completed_at = get_datetime_utc()
        run.error_code = None
        session.add(run)
        _audit(
            session,
            project_id=run.project_id,
            actor_type=AuditActorType.WORKER,
            actor_id="reca-worker",
            action="ANALYSIS_RUN_COMPLETED",
            object_type="analysis_run",
            object_id=run.id,
            job_id=job.id,
            after={
                "status": run.status,
                "effective_n": run.effective_n,
                "environment_hash": run.environment_hash,
            },
        )
        session.commit()
        session.refresh(run)
        return run
    except Exception as error:
        session.rollback()
        _cleanup(storage_backend, created_keys)
        failed = session.get(AnalysisRun, run.id)
        if failed is not None and failed.status != AnalysisRunStatus.COMPLETED:
            failed.status = AnalysisRunStatus.FAILED
            failed.error_code = "ANALYSIS_FINALIZE_FAILED"
            failed.completed_at = get_datetime_utc()
            session.add(failed)
            _audit(
                session,
                project_id=failed.project_id,
                actor_type=AuditActorType.WORKER,
                actor_id="reca-worker",
                action="ANALYSIS_RUN_FAILED",
                object_type="analysis_run",
                object_id=failed.id,
                job_id=job.id,
                after={"status": failed.status, "error_code": failed.error_code},
                outcome=AuditOutcome.FAILED,
            )
            project_service._commit(session)
        raise AnalysisExecutionError(
            "ANALYSIS_FINALIZE_FAILED",
            "Analysis outputs could not be finalized atomically.",
            True,
        ) from error


def mark_cancelled_analysis_job(session: Session, *, job: Job) -> None:
    if job.task_type != JobTaskType.ANALYSIS_RUN or job.resource_type != "analysis_run":
        return
    run = session.exec(
        select(AnalysisRun).where(AnalysisRun.id == job.resource_id).with_for_update()
    ).first()
    if run is None or run.project_id != job.project_id:
        return
    if run.status not in {
        AnalysisRunStatus.QUEUED,
        AnalysisRunStatus.CANCEL_REQUESTED,
    }:
        return
    run.status = AnalysisRunStatus.CANCELLED
    run.completed_at = get_datetime_utc()
    session.add(run)
    _audit(
        session,
        project_id=run.project_id,
        actor_type=AuditActorType.WORKER,
        actor_id="reca-worker",
        action="ANALYSIS_RUN_CANCELLED",
        object_type="analysis_run",
        object_id=run.id,
        job_id=job.id,
        after={"status": run.status},
    )
    project_service._commit(session)


def mark_failed_analysis_job(
    session: Session,
    *,
    job: Job,
    error_code: str,
    worker_id: str,
) -> None:
    if job.task_type != JobTaskType.ANALYSIS_RUN or job.resource_type != "analysis_run":
        return
    run = session.exec(
        select(AnalysisRun).where(AnalysisRun.id == job.resource_id).with_for_update()
    ).first()
    if run is None or run.project_id != job.project_id:
        return
    if run.status not in {
        AnalysisRunStatus.QUEUED,
        AnalysisRunStatus.RUNNING,
        AnalysisRunStatus.CANCEL_REQUESTED,
    }:
        return
    run.status = AnalysisRunStatus.FAILED
    run.error_code = error_code
    run.completed_at = get_datetime_utc()
    session.add(run)
    _audit(
        session,
        project_id=run.project_id,
        actor_type=AuditActorType.WORKER,
        actor_id=worker_id,
        action="ANALYSIS_RUN_FAILED",
        object_type="analysis_run",
        object_id=run.id,
        job_id=job.id,
        after={"status": run.status, "error_code": run.error_code},
        outcome=AuditOutcome.FAILED,
    )
