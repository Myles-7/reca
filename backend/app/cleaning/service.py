from __future__ import annotations

import hashlib
import importlib.metadata
import io
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any, cast

import pandas as pd  # type: ignore[import-untyped]
from fastapi.encoders import jsonable_encoder
from openpyxl import Workbook  # type: ignore[import-untyped]
from sqlalchemy import func
from sqlmodel import Session, col, delete, select

from app.adapters.storage import ObjectStorage, StorageError
from app.api.errors import ContractError
from app.approvals import service as approval_service
from app.artifacts import service as artifact_service
from app.cleaning.engine import TransformationResult, apply_actions, canonical_hash
from app.cleaning.schemas import (
    CleaningActionInput,
    CleaningPlanCreate,
    CleaningPlanUpdate,
    IssueRowsSelector,
    RenameColumnAction,
    UnavailableAction,
)
from app.core.observability import current_request_id
from app.data_quality.engine import ColumnContext, load_dataframe, scan_dataframe
from app.data_quality.registry import RECA_P0_DEFAULT
from app.datasets import parsers
from app.datasets import service as dataset_service
from app.jobs import service as job_service
from app.models import (
    ApprovalRecord,
    ApprovalStatus,
    ApprovalType,
    Artifact,
    ArtifactStatus,
    ArtifactType,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    CleaningActionType,
    CleaningPlan,
    CleaningPlanAction,
    CleaningPlanStatus,
    CleaningRiskLevel,
    CleaningSelectorType,
    DataQualityIssue,
    DataQualityIssueStatus,
    DataQualityRun,
    DataQualityRunStatus,
    Dataset,
    DatasetColumn,
    DatasetColumnConfirmationStatus,
    DatasetFileFormat,
    DatasetVersion,
    DatasetVersionStatus,
    DatasetVersionType,
    DataTransformation,
    DataTransformationStatus,
    Job,
    JobStatus,
    JobTaskType,
    ProjectMemberRole,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

TARGET_OBJECT_TYPE = "cleaning_plan"
ENGINE_VERSION = "1.0.0"
CREATE_PATH = "/api/v1/dataset-versions/{version_id}/cleaning-plans"
PREVIEW_PATH = "/api/v1/cleaning-plans/{plan_id}/preview"
APPROVAL_PATH = "/api/v1/cleaning-plans/{plan_id}/approval-requests"
EXECUTE_PATH = "/api/v1/cleaning-plans/{plan_id}/execute"


class TransformationExecutionError(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def _encoded(value: Any) -> dict[str, Any]:
    return cast(dict[str, Any], jsonable_encoder(value))


def _audit(
    session: Session,
    *,
    project_id: uuid.UUID,
    actor_type: AuditActorType,
    actor_id: str | None,
    action: str,
    object_type: str,
    object_id: uuid.UUID,
    before: dict[str, Any] | None = None,
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
            before_snapshot=jsonable_encoder(before) if before is not None else None,
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


def _allowed_actions(role: ProjectMemberRole, plan: CleaningPlan) -> list[str]:
    permissions = project_service.ROLE_ACTIONS[role]
    result = ["cleaning_plan.read"]
    if (
        plan.status
        in {
            CleaningPlanStatus.DRAFT,
            CleaningPlanStatus.NEEDS_INPUT,
            CleaningPlanStatus.REJECTED,
        }
        and "dataset.cleaning.plan" in permissions
    ):
        result.extend(["cleaning_plan.update", "cleaning_plan.preview"])
    if (
        plan.status == CleaningPlanStatus.READY
        and "dataset.cleaning.plan" in permissions
    ):
        result.append("cleaning_plan.request_approval")
    if (
        plan.status == CleaningPlanStatus.APPROVED
        and "dataset.cleaning.execute" in permissions
    ):
        result.append("cleaning_plan.execute")
    return result


def _action_rows(session: Session, plan_id: uuid.UUID) -> list[CleaningPlanAction]:
    return list(
        session.exec(
            select(CleaningPlanAction)
            .where(CleaningPlanAction.cleaning_plan_id == plan_id)
            .order_by(col(CleaningPlanAction.action_order))
        )
    )


def _action_payload(row: CleaningPlanAction) -> dict[str, Any]:
    return {
        "action_type": row.action_type.value,
        "target_columns": row.target_columns or [],
        "row_selector": row.row_selector or {"selector_type": row.selector_type.value},
        "parameters": row.parameters,
        "reason": row.reason,
        "source_issue_ids": row.source_issue_ids or [],
    }


def _validated_actions(
    session: Session, plan: CleaningPlan
) -> list[CleaningActionInput]:
    from pydantic import TypeAdapter, ValidationError

    adapter: TypeAdapter[CleaningActionInput] = TypeAdapter(CleaningActionInput)
    result: list[CleaningActionInput] = []
    try:
        for row in _action_rows(session, plan.id):
            result.append(adapter.validate_python(_action_payload(row)))
    except ValidationError as error:
        raise ContractError(
            status_code=409,
            code="CLEANING_PLAN_ACTION_STALE",
            message="The persisted CleaningPlan action no longer matches the whitelist.",
        ) from error
    return result


def _plan_data(
    session: Session, plan: CleaningPlan, role: ProjectMemberRole
) -> dict[str, Any]:
    transformation = session.exec(
        select(DataTransformation).where(DataTransformation.cleaning_plan_id == plan.id)
    ).first()
    job = None
    if transformation is not None:
        job = session.exec(
            select(Job).where(
                Job.resource_type == "data_transformation",
                Job.resource_id == transformation.id,
            )
        ).first()
    return _encoded(
        {
            "id": plan.id,
            "project_id": plan.project_id,
            "dataset_version_id": plan.dataset_version_id,
            "title": plan.title,
            "rationale": plan.rationale,
            "status": plan.status,
            "actions": [_action_payload(row) for row in _action_rows(session, plan.id)],
            "preview_summary": plan.preview_summary,
            "preview_hash": plan.preview_hash,
            "affected_row_count": plan.affected_row_count,
            "affected_column_count": plan.affected_column_count,
            "source_model_invocation_id": plan.source_model_invocation_id,
            "approval_record_id": plan.approval_record_id,
            "payload_hash": plan.payload_hash,
            "lock_version": plan.lock_version,
            "transformation_id": transformation.id if transformation else None,
            "job_id": job.id if job else None,
            "created_by": plan.created_by,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
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
) -> tuple[CleaningPlan, project_service.ProjectAccess]:
    statement = select(CleaningPlan).where(CleaningPlan.id == plan_id)
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


def _assert_action_available(action: CleaningActionInput) -> None:
    if isinstance(action, UnavailableAction):
        raise ContractError(
            status_code=422,
            code="ACTION_NOT_AVAILABLE",
            message=f"{action.action_type} is not available in M4 Competition Core.",
        )


def _validate_action_scope(
    session: Session,
    *,
    version: DatasetVersion,
    actions: list[CleaningActionInput],
) -> None:
    columns = session.exec(
        select(DatasetColumn).where(DatasetColumn.dataset_version_id == version.id)
    ).all()
    by_id = {column.id: column for column in columns}
    for action in actions:
        _assert_action_available(action)
        referenced = set(action.target_columns)
        selector_column = getattr(action.row_selector, "column_id", None)
        if selector_column is not None:
            referenced.add(selector_column)
        if not referenced.issubset(by_id):
            raise ContractError(
                status_code=422,
                code="CLEANING_COLUMN_INVALID",
                message="An action references a column outside the source DatasetVersion.",
            )
        issue_ids = set(action.source_issue_ids)
        if isinstance(action.row_selector, IssueRowsSelector):
            issue_ids.update(action.row_selector.issue_ids)
        if issue_ids:
            issues = session.exec(
                select(DataQualityIssue).where(col(DataQualityIssue.id).in_(issue_ids))
            ).all()
            if len(issues) != len(issue_ids) or any(
                issue.project_id != version.project_id
                or issue.dataset_version_id != version.id
                or issue.status == DataQualityIssueStatus.INVALIDATED
                for issue in issues
            ):
                raise ContractError(
                    status_code=422,
                    code="CLEANING_ISSUE_INVALID",
                    message="An action references an unavailable quality issue.",
                )


def _risk(action: CleaningActionInput) -> CleaningRiskLevel:
    if isinstance(action, RenameColumnAction):
        return CleaningRiskLevel.LOW
    if action.action_type == "CAST_TYPE":
        return CleaningRiskLevel.HIGH
    return CleaningRiskLevel.MEDIUM


def _replace_actions(
    session: Session,
    *,
    plan: CleaningPlan,
    actions: list[CleaningActionInput],
) -> None:
    session.exec(
        delete(CleaningPlanAction).where(
            col(CleaningPlanAction.cleaning_plan_id) == plan.id
        )
    )
    for order, action in enumerate(actions, start=1):
        selector = action.row_selector.model_dump(mode="json")
        session.add(
            CleaningPlanAction(
                project_id=plan.project_id,
                cleaning_plan_id=plan.id,
                action_order=order,
                action_type=CleaningActionType(action.action_type),
                selector_type=CleaningSelectorType(action.row_selector.selector_type),
                target_columns=[str(value) for value in action.target_columns],
                row_selector=selector,
                parameters=action.parameters.model_dump(mode="json"),
                reason=action.reason.strip(),
                source_issue_ids=[str(value) for value in action.source_issue_ids],
                risk_level=_risk(action),
            )
        )
    session.flush()


def create_plan(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    payload: CleaningPlanCreate,
    idempotency_key: str,
) -> project_service.OperationResult:
    version, _, access = dataset_service._version_access(
        session,
        actor=actor,
        version_id=version_id,
        action="dataset.cleaning.plan",
        for_update=True,
    )
    digest = project_service.request_hash(
        {"version_id": str(version.id), "payload": payload}
    )
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        method="POST",
        path_template=CREATE_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    if version.status != DatasetVersionStatus.AVAILABLE:
        raise ContractError(
            status_code=409,
            code="DATASET_VERSION_NOT_AVAILABLE",
            message="Only an AVAILABLE DatasetVersion can receive a CleaningPlan.",
        )
    actions = list(payload.actions)
    _validate_action_scope(session, version=version, actions=actions)
    plan = CleaningPlan(
        project_id=version.project_id,
        dataset_version_id=version.id,
        title=payload.title.strip(),
        rationale=payload.rationale,
        status=CleaningPlanStatus.DRAFT,
        created_by=actor.id,
    )
    session.add(plan)
    session.flush()
    _replace_actions(session, plan=plan, actions=actions)
    _audit(
        session,
        project_id=plan.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="CLEANING_PLAN_CREATED",
        object_type=TARGET_OBJECT_TYPE,
        object_id=plan.id,
        after={"source_version_id": str(version.id), "action_count": len(actions)},
    )
    result = project_service.OperationResult(
        data=_plan_data(session, plan, _role(access)), status_code=201
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=CREATE_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result


def get_plan(session: Session, *, actor: User, plan_id: uuid.UUID) -> dict[str, Any]:
    plan, access = _visible_plan(
        session, actor=actor, plan_id=plan_id, action="dataset.read"
    )
    return _plan_data(session, plan, _role(access))


def update_plan(
    session: Session,
    *,
    actor: User,
    plan_id: uuid.UUID,
    payload: CleaningPlanUpdate,
    expected_lock_version: int,
) -> dict[str, Any]:
    plan, access = _visible_plan(
        session,
        actor=actor,
        plan_id=plan_id,
        action="dataset.cleaning.plan",
        for_update=True,
    )
    if plan.status not in {
        CleaningPlanStatus.DRAFT,
        CleaningPlanStatus.NEEDS_INPUT,
        CleaningPlanStatus.REJECTED,
    }:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="The CleaningPlan is immutable in its current state.",
        )
    if plan.lock_version != expected_lock_version:
        raise ContractError(
            status_code=409,
            code="RESOURCE_VERSION_CONFLICT",
            message="The CleaningPlan was modified by another request.",
            details={"expected": expected_lock_version, "current": plan.lock_version},
        )
    updates = payload.model_dump(exclude_unset=True)
    if payload.actions is not None:
        version = session.get(DatasetVersion, plan.dataset_version_id)
        assert version is not None
        _validate_action_scope(session, version=version, actions=list(payload.actions))
        _replace_actions(session, plan=plan, actions=list(payload.actions))
    if "title" in updates:
        plan.title = cast(str, updates["title"]).strip()
    if "rationale" in updates:
        plan.rationale = cast(str | None, updates["rationale"])
    plan.status = CleaningPlanStatus.DRAFT
    plan.preview_summary = None
    plan.preview_hash = None
    plan.affected_row_count = None
    plan.affected_column_count = None
    plan.approval_record_id = None
    plan.payload_hash = None
    plan.lock_version += 1
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    _audit(
        session,
        project_id=plan.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="CLEANING_PLAN_UPDATED",
        object_type=TARGET_OBJECT_TYPE,
        object_id=plan.id,
        after={"lock_version": plan.lock_version, "status": plan.status},
    )
    project_service._commit(session)
    return _plan_data(session, plan, _role(access))


def _load_source(
    session: Session,
    *,
    version: DatasetVersion,
    storage_backend: ObjectStorage | None,
) -> tuple[pd.DataFrame, Artifact]:
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
            message="The source Artifact identity is not valid.",
        )
    suffix = ".csv" if version.file_format == DatasetFileFormat.CSV else ".xlsx"
    with tempfile.TemporaryDirectory(prefix="reca-cleaning-source-") as directory:
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
                message="The source Artifact bytes do not match the immutable version.",
            ) from error
        frame = load_dataframe(path, version=version)
    return frame, artifact


def _issue_rows(
    session: Session, actions: list[CleaningActionInput]
) -> dict[uuid.UUID, tuple[int, ...]]:
    ids: set[uuid.UUID] = set()
    for action in actions:
        ids.update(action.source_issue_ids)
        if isinstance(action.row_selector, IssueRowsSelector):
            ids.update(action.row_selector.issue_ids)
    if not ids:
        return {}
    issues = session.exec(
        select(DataQualityIssue).where(col(DataQualityIssue.id).in_(ids))
    ).all()
    result = {
        issue.id: tuple(int(value) for value in (issue.affected_rows or []))
        for issue in issues
    }
    if set(result) != ids:
        raise ContractError(
            status_code=409,
            code="CLEANING_ISSUE_STALE",
            message="A referenced quality issue is no longer available.",
        )
    return result


def _masked_samples(
    result: TransformationResult,
    columns: list[DatasetColumn],
    actions: list[CleaningActionInput],
) -> list[dict[str, Any]]:
    sensitive = {column.source_name for column in columns if column.is_sensitive}
    by_id = {column.id: column for column in columns}
    for action in actions:
        if not isinstance(action, RenameColumnAction):
            continue
        for column_id in action.target_columns:
            column = by_id[column_id]
            if column.is_sensitive:
                sensitive.add(action.parameters.new_name)
    output: list[dict[str, Any]] = []
    for sample in result.sample_changes:
        item = dict(sample)
        for side in ("before", "after"):
            item[side] = {
                name: "[MASKED]"
                if name in sensitive
                else parsers.redact_risky_value(value)
                for name, value in sample[side].items()
            }
        output.append(jsonable_encoder(item))
    return output


def preview_plan(
    session: Session,
    *,
    actor: User,
    plan_id: uuid.UUID,
    idempotency_key: str,
    storage_backend: ObjectStorage | None = None,
) -> project_service.OperationResult:
    plan, access = _visible_plan(
        session,
        actor=actor,
        plan_id=plan_id,
        action="dataset.cleaning.plan",
        for_update=True,
    )
    digest = project_service.request_hash(
        {"plan_id": str(plan.id), "lock_version": plan.lock_version}
    )
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=PREVIEW_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    if plan.status not in {
        CleaningPlanStatus.DRAFT,
        CleaningPlanStatus.NEEDS_INPUT,
        CleaningPlanStatus.REJECTED,
        CleaningPlanStatus.READY,
    }:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="The CleaningPlan cannot be previewed in its current state.",
        )
    version = session.get(DatasetVersion, plan.dataset_version_id)
    if version is None or version.status != DatasetVersionStatus.AVAILABLE:
        raise ContractError(
            status_code=409,
            code="DATASET_VERSION_NOT_AVAILABLE",
            message="The source DatasetVersion is not available.",
        )
    actions = _validated_actions(session, plan)
    _validate_action_scope(session, version=version, actions=actions)
    columns = list(
        session.exec(
            select(DatasetColumn)
            .where(DatasetColumn.dataset_version_id == version.id)
            .order_by(col(DatasetColumn.column_order))
        )
    )
    source, _ = _load_source(session, version=version, storage_backend=storage_backend)
    source_snapshot = source.copy(deep=True)
    result = apply_actions(
        source,
        actions=actions,
        columns=columns,
        issue_rows=_issue_rows(session, actions),
    )
    pd.testing.assert_frame_equal(source_snapshot, source, check_exact=True)
    summary = {
        "cleaning_plan_id": str(plan.id),
        "source_dataset_version_id": str(version.id),
        "source_data_hash": version.data_hash,
        "action_hash": canonical_hash(actions),
        "affected_row_count": len(result.affected_rows),
        "affected_column_count": len(result.affected_columns),
        "affected_columns": list(result.affected_columns),
        "row_count_before": len(source),
        "row_count_after": len(result.frame),
        "sample_changes": _masked_samples(result, columns, actions),
        "warnings": list(result.warnings),
        "risk": max(
            (_risk(action) for action in actions),
            key={
                CleaningRiskLevel.LOW: 0,
                CleaningRiskLevel.MEDIUM: 1,
                CleaningRiskLevel.HIGH: 2,
            }.__getitem__,
            default=CleaningRiskLevel.LOW,
        ).value,
        "ready_for_approval": True,
    }
    plan.status = CleaningPlanStatus.READY
    plan.preview_summary = jsonable_encoder(summary)
    plan.preview_hash = canonical_hash(summary)
    plan.affected_row_count = len(result.affected_rows)
    plan.affected_column_count = len(result.affected_columns)
    plan.lock_version += 1
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    _audit(
        session,
        project_id=plan.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="CLEANING_PLAN_PREVIEWED",
        object_type=TARGET_OBJECT_TYPE,
        object_id=plan.id,
        after={"preview_hash": plan.preview_hash, "status": plan.status},
    )
    result_value = project_service.OperationResult(
        data=_plan_data(session, plan, _role(access)), status_code=200
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=PREVIEW_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=result_value,
    )
    project_service._commit(session)
    return result_value


def approval_payload(session: Session, plan: CleaningPlan) -> dict[str, Any]:
    version = session.get(DatasetVersion, plan.dataset_version_id)
    if version is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    actions = _validated_actions(session, plan)
    return {
        "schema_version": "1.0",
        "project_id": str(plan.project_id),
        "cleaning_plan_id": str(plan.id),
        "source_dataset_version_id": str(version.id),
        "source_data_hash": version.data_hash,
        "source_schema_hash": version.schema_hash,
        "source_projection_hash": version.projection_hash,
        "plan_lock_version": plan.lock_version,
        "actions": [action.model_dump(mode="json") for action in actions],
        "action_hash": canonical_hash(actions),
        "preview_hash": plan.preview_hash,
        "risk": (plan.preview_summary or {}).get("risk"),
        "impact_summary": {
            "affected_row_count": plan.affected_row_count,
            "affected_column_count": plan.affected_column_count,
            "row_count_before": (plan.preview_summary or {}).get("row_count_before"),
            "row_count_after": (plan.preview_summary or {}).get("row_count_after"),
        },
    }


def resolve_approval_payload(
    session: Session, approval: ApprovalRecord
) -> dict[str, Any]:
    plan = session.exec(
        select(CleaningPlan).where(
            CleaningPlan.id == approval.target_object_id,
            CleaningPlan.project_id == approval.project_id,
        )
    ).first()
    if plan is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    return approval_payload(session, plan)


def apply_approval_decision(
    session: Session,
    approval: ApprovalRecord,
    decision: ApprovalStatus,
    actor: User,
) -> None:
    if approval.approval_type != ApprovalType.CLEANING_PLAN_APPROVAL:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Approval type does not match CleaningPlan approval.",
        )
    plan = session.exec(
        select(CleaningPlan)
        .where(
            CleaningPlan.id == approval.target_object_id,
            CleaningPlan.project_id == approval.project_id,
        )
        .with_for_update()
    ).first()
    if plan is None or plan.approval_record_id != approval.id:
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="The CleaningPlan no longer references this Approval.",
        )
    if decision == ApprovalStatus.APPROVED:
        if plan.status != CleaningPlanStatus.NEEDS_APPROVAL:
            raise ContractError(
                status_code=409,
                code="INVALID_STATE_TRANSITION",
                message="Only NEEDS_APPROVAL may become APPROVED.",
            )
        plan.status = CleaningPlanStatus.APPROVED
    elif decision == ApprovalStatus.REJECTED:
        if plan.status != CleaningPlanStatus.NEEDS_APPROVAL:
            raise ContractError(
                status_code=409,
                code="INVALID_STATE_TRANSITION",
                message="Only NEEDS_APPROVAL may be rejected.",
            )
        plan.status = CleaningPlanStatus.REJECTED
    else:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Unsupported CleaningPlan Approval decision.",
        )
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    _audit(
        session,
        project_id=plan.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action=(
            "CLEANING_PLAN_APPROVED"
            if decision == ApprovalStatus.APPROVED
            else "CLEANING_PLAN_REJECTED"
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
    session: Session,
    *,
    actor: User,
    plan_id: uuid.UUID,
    idempotency_key: str,
) -> project_service.OperationResult:
    plan, _ = _visible_plan(
        session,
        actor=actor,
        plan_id=plan_id,
        action="dataset.cleaning.plan",
        for_update=True,
    )
    digest = project_service.request_hash(
        {"plan_id": str(plan.id), "preview_hash": plan.preview_hash}
    )
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=APPROVAL_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    if plan.status != CleaningPlanStatus.READY or not plan.preview_hash:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="A complete READY preview is required before Approval.",
        )
    snapshot = approval_payload(session, plan)
    approval = approval_service.create_approval(
        session,
        command=approval_service.ApprovalCreate(
            project_id=plan.project_id,
            approval_type=ApprovalType.CLEANING_PLAN_APPROVAL,
            target_object_type=TARGET_OBJECT_TYPE,
            target_object_id=plan.id,
            requested_by_actor_type=AuditActorType.USER,
            requested_by_actor_id=str(actor.id),
            payload_snapshot=snapshot,
            impact_summary=snapshot["impact_summary"],
            expires_at=get_datetime_utc() + timedelta(hours=24),
        ),
    )
    plan.status = CleaningPlanStatus.NEEDS_APPROVAL
    plan.approval_record_id = approval.id
    plan.payload_hash = approval.payload_hash
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    data = _encoded(
        {
            "approval_id": approval.id,
            "cleaning_plan_id": plan.id,
            "status": approval.status,
            "payload_hash": approval.payload_hash,
            "expires_at": approval.expires_at,
        }
    )
    result = project_service.OperationResult(data=data, status_code=201)
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=APPROVAL_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result


def _fresh_approval(
    session: Session, *, plan: CleaningPlan, source: DatasetVersion
) -> ApprovalRecord:
    if plan.approval_record_id is None or plan.payload_hash is None:
        raise ContractError(
            status_code=409,
            code="APPROVAL_REQUIRED",
            message="The CleaningPlan has no formal Approval.",
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
        or approval.approval_type != ApprovalType.CLEANING_PLAN_APPROVAL
    ):
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="The Approval target does not match the CleaningPlan.",
        )
    if approval.expires_at is not None and approval.expires_at <= get_datetime_utc():
        raise ContractError(
            status_code=409,
            code="APPROVAL_EXPIRED",
            message="The CleaningPlan Approval has expired.",
        )
    if approval.status != ApprovalStatus.APPROVED:
        raise ContractError(
            status_code=409,
            code="APPROVAL_REQUIRED",
            message="The CleaningPlan Approval is not APPROVED.",
        )
    current = approval_payload(session, plan)
    if (
        project_service.request_hash(current) != approval.payload_hash
        or approval.payload_hash != plan.payload_hash
        or current["source_data_hash"] != source.data_hash
    ):
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="The CleaningPlan Approval payload is stale.",
        )
    return approval


def execute_plan(
    session: Session,
    *,
    actor: User,
    plan_id: uuid.UUID,
    idempotency_key: str,
    dispatcher: job_service.JobDispatcher,
) -> project_service.OperationResult:
    plan, _ = _visible_plan(
        session,
        actor=actor,
        plan_id=plan_id,
        action="dataset.cleaning.execute",
        for_update=True,
    )
    digest = project_service.request_hash({"plan_id": str(plan.id)})
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=EXECUTE_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    if plan.status != CleaningPlanStatus.APPROVED:
        raise ContractError(
            status_code=409,
            code="APPROVAL_REQUIRED",
            message="Only an APPROVED CleaningPlan can execute.",
        )
    source = session.get(DatasetVersion, plan.dataset_version_id)
    if source is None:
        raise ContractError(
            status_code=409,
            code="DATASET_VERSION_STALE",
            message="The source DatasetVersion is no longer available.",
        )
    dataset = session.exec(
        select(Dataset).where(Dataset.id == source.dataset_id).with_for_update()
    ).first()
    if (
        dataset is None
        or source.status != DatasetVersionStatus.AVAILABLE
        or dataset.current_version_id != source.id
    ):
        raise ContractError(
            status_code=409,
            code="DATASET_VERSION_STALE",
            message="The source DatasetVersion is no longer the current AVAILABLE version.",
        )
    approval = _fresh_approval(session, plan=plan, source=source)
    actions = _validated_actions(session, plan)
    _validate_action_scope(session, version=source, actions=actions)
    parameters_hash = canonical_hash(
        {
            "approval_payload_hash": approval.payload_hash,
            "action_hash": canonical_hash(actions),
            "engine": "reca-cleaning",
            "engine_version": ENGINE_VERSION,
        }
    )
    transformation = DataTransformation(
        project_id=plan.project_id,
        cleaning_plan_id=plan.id,
        approval_record_id=approval.id,
        source_dataset_version_id=source.id,
        status=DataTransformationStatus.QUEUED,
        action_count=len(actions),
        parameters_hash=parameters_hash,
    )
    session.add(transformation)
    session.flush()
    job = job_service.create_job(
        session,
        project_id=plan.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.DATASET_TRANSFORM,
            resource_type="data_transformation",
            resource_id=transformation.id,
            idempotency_key=idempotency_key,
            requested_by_user_id=actor.id,
            max_retries=2,
            retryable=True,
        ),
    )
    plan.status = CleaningPlanStatus.QUEUED
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    _audit(
        session,
        project_id=plan.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action="DATA_TRANSFORMATION_REQUESTED",
        object_type="data_transformation",
        object_id=transformation.id,
        approval_id=approval.id,
        job_id=job.id,
        after={"status": transformation.status, "parameters_hash": parameters_hash},
    )
    initial = project_service.OperationResult(
        data={
            "transformation": transformation_data(transformation),
            "job": job_service.job_data(session, job),
        },
        status_code=202,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=EXECUTE_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=initial,
    )
    project_service._commit(session)
    dispatched = job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)
    if dispatched.status == JobStatus.DISPATCH_FAILED:
        refreshed_transformation = session.get(DataTransformation, transformation.id)
        refreshed_plan = session.get(CleaningPlan, plan.id)
        assert refreshed_transformation is not None and refreshed_plan is not None
        transformation = refreshed_transformation
        plan = refreshed_plan
        transformation.status = DataTransformationStatus.FAILED
        transformation.error_code = "JOB_DISPATCH_FAILED"
        transformation.completed_at = get_datetime_utc()
        plan.status = CleaningPlanStatus.FAILED
        session.add(transformation)
        session.add(plan)
    result = project_service.OperationResult(
        data={
            "transformation": transformation_data(transformation),
            "job": job_service.job_data(session, dispatched),
        },
        status_code=202,
    )
    project_service._update_idempotency_result(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=EXECUTE_PATH,
        key=idempotency_key,
        result=result,
    )
    project_service._commit(session)
    return result


def transformation_data(transformation: DataTransformation) -> dict[str, Any]:
    return _encoded(
        {
            "id": transformation.id,
            "project_id": transformation.project_id,
            "cleaning_plan_id": transformation.cleaning_plan_id,
            "approval_record_id": transformation.approval_record_id,
            "source_dataset_version_id": transformation.source_dataset_version_id,
            "target_dataset_version_id": transformation.target_dataset_version_id,
            "status": transformation.status,
            "action_count": transformation.action_count,
            "affected_row_count": transformation.affected_row_count,
            "affected_column_count": transformation.affected_column_count,
            "parameters_hash": transformation.parameters_hash,
            "output_artifact_id": transformation.output_artifact_id,
            "log_artifact_id": transformation.log_artifact_id,
            "processing_run_id": transformation.processing_run_id,
            "started_at": transformation.started_at,
            "completed_at": transformation.completed_at,
            "error_code": transformation.error_code,
            "created_at": transformation.created_at,
        }
    )


def get_transformation(
    session: Session, *, actor: User, transformation_id: uuid.UUID
) -> dict[str, Any]:
    transformation = session.exec(
        select(DataTransformation).where(DataTransformation.id == transformation_id)
    ).first()
    if transformation is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    project_service.authorize_project(
        session,
        project_id=transformation.project_id,
        actor=actor,
        action="dataset.read",
    )
    return transformation_data(transformation)


def _safe_export_value(value: Any) -> Any:
    if isinstance(value, str) and value[:1] in {"=", "+", "-", "@"}:
        return f"'{value}"
    return value


def _serialize(frame: pd.DataFrame, file_format: DatasetFileFormat) -> bytes:
    safe = frame.map(_safe_export_value)
    if file_format == DatasetFileFormat.CSV:
        csv_text = safe.to_csv(index=False, lineterminator="\n")
        if not isinstance(csv_text, str):
            raise TransformationExecutionError(
                "CLEANING_SERIALIZATION_INVALID",
                "CSV serialization did not return text.",
            )
        return csv_text.encode("utf-8")
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("CleanedData")
    sheet.append(list(safe.columns))
    for row in safe.itertuples(index=False, name=None):
        sheet.append(list(row))
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _profile_output(
    content: bytes, file_format: DatasetFileFormat
) -> parsers.ParsedTable:
    suffix = ".csv" if file_format == DatasetFileFormat.CSV else ".xlsx"
    with tempfile.TemporaryDirectory(prefix="reca-cleaned-profile-") as directory:
        path = Path(directory) / f"output{suffix}"
        path.write_bytes(content)
        return (
            parsers.parse_csv(path)
            if file_format == DatasetFileFormat.CSV
            else parsers.parse_xlsx(path, "CleanedData")
        )


def _load_persisted_output(
    content: bytes,
    source: DatasetVersion,
) -> pd.DataFrame:
    suffix = ".csv" if source.file_format == DatasetFileFormat.CSV else ".xlsx"
    with tempfile.TemporaryDirectory(prefix="reca-cleaned-readback-") as directory:
        path = Path(directory) / f"output{suffix}"
        path.write_bytes(content)
        projected = source.model_copy(update={"selected_worksheet_name": "CleanedData"})
        return load_dataframe(path, version=projected)


def _fail_transformation(
    session: Session,
    *,
    transformation_id: uuid.UUID,
    processing_run_id: uuid.UUID,
    code: str,
) -> None:
    session.rollback()
    transformation = session.exec(
        select(DataTransformation)
        .where(DataTransformation.id == transformation_id)
        .with_for_update()
    ).first()
    if (
        transformation is None
        or transformation.status == DataTransformationStatus.COMPLETED
    ):
        return
    plan = session.get(CleaningPlan, transformation.cleaning_plan_id)
    target = (
        session.get(DatasetVersion, transformation.target_dataset_version_id)
        if transformation.target_dataset_version_id
        else None
    )
    transformation.status = DataTransformationStatus.FAILED
    transformation.processing_run_id = processing_run_id
    transformation.error_code = code
    transformation.completed_at = get_datetime_utc()
    if plan is not None:
        plan.status = CleaningPlanStatus.FAILED
        plan.updated_at = get_datetime_utc()
        session.add(plan)
    if target is not None and target.status != DatasetVersionStatus.AVAILABLE:
        target.status = DatasetVersionStatus.FAILED
        session.add(target)
    session.add(transformation)
    _audit(
        session,
        project_id=transformation.project_id,
        actor_type=AuditActorType.WORKER,
        actor_id="data-transformation-worker",
        action="DATA_TRANSFORMATION_FAILED",
        object_type="data_transformation",
        object_id=transformation.id,
        after={"status": transformation.status, "error_code": code},
        outcome=AuditOutcome.FAILED,
    )
    project_service._commit(session)


def _cleanup_staging_object(
    storage_backend: ObjectStorage | None, object_key: str | None
) -> None:
    if object_key is None:
        return
    backend = storage_backend or artifact_service.storage
    try:
        backend.delete_object(object_key=object_key)
    except StorageError:
        pass


def execute_transformation_job(
    session: Session,
    *,
    job: Job,
    run_id: uuid.UUID,
    storage_backend: ObjectStorage | None = None,
) -> DataTransformation:
    transformation_id = job.resource_id
    staging_object_key: str | None = None
    try:
        if (
            job.task_type != JobTaskType.DATASET_TRANSFORM
            or job.resource_type != "data_transformation"
        ):
            raise TransformationExecutionError(
                "JOB_HANDLER_MISMATCH", "Job is not a dataset transformation."
            )
        transformation = session.exec(
            select(DataTransformation)
            .where(DataTransformation.id == transformation_id)
            .with_for_update()
        ).first()
        if transformation is None or transformation.project_id != job.project_id:
            raise TransformationExecutionError(
                "DATA_TRANSFORMATION_INVALID", "Transformation is unavailable."
            )
        actor = session.get(User, job.requested_by_user_id)
        if actor is None:
            raise TransformationExecutionError(
                "TRANSFORMATION_ACTOR_INVALID", "Requesting actor is unavailable."
            )
        project_service.authorize_project(
            session,
            project_id=transformation.project_id,
            actor=actor,
            action="dataset.cleaning.execute",
            for_update=True,
        )
        plan = session.exec(
            select(CleaningPlan)
            .where(CleaningPlan.id == transformation.cleaning_plan_id)
            .with_for_update()
        ).one()
        source = session.exec(
            select(DatasetVersion)
            .where(DatasetVersion.id == transformation.source_dataset_version_id)
            .with_for_update()
        ).one()
        dataset = session.exec(
            select(Dataset).where(Dataset.id == source.dataset_id).with_for_update()
        ).one()
        if (
            transformation.status != DataTransformationStatus.QUEUED
            or plan.status != CleaningPlanStatus.QUEUED
            or source.status != DatasetVersionStatus.AVAILABLE
            or dataset.current_version_id != source.id
        ):
            raise TransformationExecutionError(
                "TRANSFORMATION_STATE_STALE", "Transformation state is stale."
            )
        approval = _fresh_approval(session, plan=plan, source=source)
        actions = _validated_actions(session, plan)
        _validate_action_scope(session, version=source, actions=actions)
        expected_parameters = canonical_hash(
            {
                "approval_payload_hash": approval.payload_hash,
                "action_hash": canonical_hash(actions),
                "engine": "reca-cleaning",
                "engine_version": ENGINE_VERSION,
            }
        )
        if expected_parameters != transformation.parameters_hash:
            raise TransformationExecutionError(
                "TRANSFORMATION_PARAMETERS_STALE", "Transformation parameters changed."
            )
        job_service.set_run_context(
            session,
            job_id=job.id,
            run_id=run_id,
            input_hash=source.data_hash,
            parameters={"parameters_hash": transformation.parameters_hash},
            implementation_metadata={
                "engine": "reca-cleaning",
                "engine_version": ENGINE_VERSION,
                "python": __import__("platform").python_version(),
                "pandas": pd.__version__,
                "openpyxl": importlib.metadata.version("openpyxl"),
                "source_version_id": str(source.id),
                "source_data_hash": source.data_hash,
                "approval_payload_hash": approval.payload_hash,
            },
        )
        refreshed_transformation = session.get(DataTransformation, transformation.id)
        refreshed_plan = session.get(CleaningPlan, plan.id)
        assert refreshed_transformation is not None and refreshed_plan is not None
        transformation = refreshed_transformation
        plan = refreshed_plan
        transformation.status = DataTransformationStatus.RUNNING
        transformation.processing_run_id = run_id
        transformation.started_at = get_datetime_utc()
        plan.status = CleaningPlanStatus.RUNNING
        session.add(transformation)
        session.add(plan)
        project_service._commit(session)

        columns = list(
            session.exec(
                select(DatasetColumn)
                .where(DatasetColumn.dataset_version_id == source.id)
                .order_by(col(DatasetColumn.column_order))
            )
        )
        source_frame, source_artifact = _load_source(
            session, version=source, storage_backend=storage_backend
        )
        result = apply_actions(
            source_frame,
            actions=actions,
            columns=columns,
            issue_rows=_issue_rows(session, actions),
        )
        content = _serialize(result.frame, source.file_format)
        profile = _profile_output(content, source.file_format)
        persisted_frame = _load_persisted_output(content, source)
        digest = hashlib.sha256(content).hexdigest()

        transformation = session.exec(
            select(DataTransformation)
            .where(DataTransformation.id == transformation_id)
            .with_for_update()
        ).one()
        plan = session.exec(
            select(CleaningPlan).where(CleaningPlan.id == plan.id).with_for_update()
        ).one()
        dataset = session.exec(
            select(Dataset).where(Dataset.id == dataset.id).with_for_update()
        ).one()
        source = session.exec(
            select(DatasetVersion)
            .where(DatasetVersion.id == source.id)
            .with_for_update()
        ).one()
        _fresh_approval(session, plan=plan, source=source)
        if (
            dataset.current_version_id != source.id
            or source.status != DatasetVersionStatus.AVAILABLE
        ):
            raise TransformationExecutionError(
                "DATASET_VERSION_STALE", "Source version changed before promotion."
            )
        next_version = session.exec(
            select(func.max(DatasetVersion.version_number)).where(
                DatasetVersion.dataset_id == dataset.id
            )
        ).one()
        output_artifact = artifact_service.create_generated_bytes_artifact(
            session,
            project_id=transformation.project_id,
            content=content,
            filename=(
                f"dataset-v{(next_version or 0) + 1}.csv"
                if source.file_format == DatasetFileFormat.CSV
                else f"dataset-v{(next_version or 0) + 1}.xlsx"
            ),
            mime_type=(
                "text/csv"
                if source.file_format == DatasetFileFormat.CSV
                else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            artifact_type=(
                ArtifactType.CSV_EXPORT
                if source.file_format == DatasetFileFormat.CSV
                else ArtifactType.XLSX_EXPORT
            ),
            metadata={
                "data_transformation_id": str(transformation.id),
                "parameters_hash": transformation.parameters_hash,
            },
            source_artifact_id=source_artifact.id,
            created_by=actor.id,
            storage_backend=storage_backend,
        )
        staging_object_key = output_artifact.storage_key
        target = DatasetVersion(
            project_id=source.project_id,
            dataset_id=source.dataset_id,
            version_number=(next_version or 0) + 1,
            parent_version_id=source.id,
            artifact_id=output_artifact.id,
            version_type=DatasetVersionType.CLEANED,
            row_count=profile.row_count,
            column_count=len(profile.headers),
            file_format=source.file_format,
            worksheet_manifest=(
                [
                    {
                        "name": "CleanedData",
                        "ordinal": 1,
                        "visibility": "VISIBLE",
                        "estimated_rows": profile.row_count,
                        "estimated_columns": len(profile.headers),
                        "warnings": [],
                    }
                ]
                if source.file_format == DatasetFileFormat.XLSX
                else None
            ),
            selected_worksheet_name=(
                "CleanedData" if source.file_format == DatasetFileFormat.XLSX else None
            ),
            projection_hash=profile.projection_hash,
            schema_hash=profile.schema_hash,
            data_hash=digest,
            status=DatasetVersionStatus.CREATING,
            created_by=actor.id,
        )
        session.add(target)
        session.flush()
        source_columns_by_id = {column.id: column for column in columns}
        reverse_rename = {
            action.parameters.new_name: source_columns_by_id[
                action.target_columns[0]
            ].source_name
            for action in actions
            if isinstance(action, RenameColumnAction)
        }
        source_by_name = {column.source_name: column for column in columns}
        target_columns: list[DatasetColumn] = []
        for order, column_profile in enumerate(profile.columns, start=1):
            inherited = source_by_name.get(
                reverse_rename.get(
                    column_profile.source_name, column_profile.source_name
                )
            )
            column = DatasetColumn(
                project_id=target.project_id,
                dataset_version_id=target.id,
                source_name=column_profile.source_name,
                display_name=inherited.display_name if inherited else None,
                column_order=order,
                inferred_type=column_profile.inferred_type,
                confirmed_type=inherited.confirmed_type if inherited else None,
                semantic_role=inherited.semantic_role if inherited else None,
                unit=inherited.unit if inherited else None,
                description=inherited.description if inherited else None,
                missing_codes=inherited.missing_codes if inherited else None,
                category_mapping=inherited.category_mapping if inherited else None,
                is_identifier=inherited.is_identifier if inherited else False,
                is_sensitive=(
                    inherited.is_sensitive if inherited else column_profile.is_sensitive
                ),
                confirmation_status=DatasetColumnConfirmationStatus.NEEDS_REVIEW,
                unique_count=column_profile.unique_count,
                missing_ratio=column_profile.missing_ratio,
                example_values=list(column_profile.example_values),
                inherited_from_column_id=inherited.id if inherited else None,
            )
            session.add(column)
            target_columns.append(column)
        session.flush()
        facts = scan_dataframe(
            persisted_frame,
            columns=tuple(
                ColumnContext.from_model(column) for column in target_columns
            ),
            ruleset=RECA_P0_DEFAULT,
            include_sensitive_field_detection=True,
        )
        quality_run = DataQualityRun(
            project_id=target.project_id,
            dataset_version_id=target.id,
            ruleset_id=RECA_P0_DEFAULT.ruleset_id,
            rule_set_version=RECA_P0_DEFAULT.version,
            ruleset_hash=RECA_P0_DEFAULT.content_hash,
            status=DataQualityRunStatus.COMPLETED,
            issue_count=len(facts),
            high_issue_count=sum(fact.severity.value == "HIGH" for fact in facts),
            started_at=get_datetime_utc(),
            completed_at=get_datetime_utc(),
        )
        session.add(quality_run)
        session.flush()
        for fact in facts:
            session.add(
                DataQualityIssue(
                    project_id=target.project_id,
                    data_quality_run_id=quality_run.id,
                    dataset_version_id=target.id,
                    rule_code=fact.rule_code,
                    issue_type=fact.issue_type,
                    severity=fact.severity,
                    column_id=fact.column_id,
                    affected_row_count=fact.affected_row_count,
                    affected_rows=list(fact.affected_rows),
                    evidence=fact.evidence,
                    description=fact.description,
                    requires_approval=fact.requires_approval,
                )
            )
        target.transformation_id = transformation.id
        target.status = DatasetVersionStatus.AVAILABLE
        dataset.current_version_id = target.id
        dataset.updated_at = get_datetime_utc()
        transformation.target_dataset_version_id = target.id
        transformation.output_artifact_id = output_artifact.id
        transformation.affected_row_count = len(result.affected_rows)
        transformation.affected_column_count = len(result.affected_columns)
        transformation.status = DataTransformationStatus.COMPLETED
        transformation.completed_at = get_datetime_utc()
        transformation.error_code = None
        plan.status = CleaningPlanStatus.COMPLETED
        plan.updated_at = get_datetime_utc()
        session.add(target)
        session.add(dataset)
        session.add(transformation)
        session.add(plan)
        _audit(
            session,
            project_id=transformation.project_id,
            actor_type=AuditActorType.WORKER,
            actor_id="data-transformation-worker",
            action="DATA_TRANSFORMATION_COMPLETED",
            object_type="data_transformation",
            object_id=transformation.id,
            approval_id=approval.id,
            job_id=job.id,
            after={
                "target_version_id": str(target.id),
                "output_hash": digest,
                "quality_run_id": str(quality_run.id),
            },
        )
        project_service._commit(session)
        session.refresh(transformation)
        return transformation
    except ContractError as error:
        _cleanup_staging_object(storage_backend, staging_object_key)
        _fail_transformation(
            session,
            transformation_id=transformation_id,
            processing_run_id=run_id,
            code=error.code,
        )
        raise TransformationExecutionError(
            error.code, error.message, error.retryable
        ) from error
    except TransformationExecutionError as error:
        _cleanup_staging_object(storage_backend, staging_object_key)
        _fail_transformation(
            session,
            transformation_id=transformation_id,
            processing_run_id=run_id,
            code=error.code,
        )
        raise
    except Exception as error:
        _cleanup_staging_object(storage_backend, staging_object_key)
        _fail_transformation(
            session,
            transformation_id=transformation_id,
            processing_run_id=run_id,
            code="DATA_TRANSFORMATION_FAILED",
        )
        raise TransformationExecutionError(
            "DATA_TRANSFORMATION_FAILED",
            "The deterministic data transformation failed.",
            True,
        ) from error


def compare_versions(
    session: Session,
    *,
    actor: User,
    dataset_id: uuid.UUID,
    base_version_id: uuid.UUID,
    target_version_id: uuid.UUID,
) -> dict[str, Any]:
    dataset, _ = dataset_service._dataset_access(
        session, actor=actor, dataset_id=dataset_id, action="dataset.read"
    )
    versions = session.exec(
        select(DatasetVersion).where(
            col(DatasetVersion.id).in_({base_version_id, target_version_id}),
            DatasetVersion.dataset_id == dataset.id,
            DatasetVersion.project_id == dataset.project_id,
        )
    ).all()
    by_id = {version.id: version for version in versions}
    if set(by_id) != {base_version_id, target_version_id}:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    base_columns = list(
        session.exec(
            select(DatasetColumn).where(
                DatasetColumn.dataset_version_id == base_version_id
            )
        )
    )
    target_columns = list(
        session.exec(
            select(DatasetColumn).where(
                DatasetColumn.dataset_version_id == target_version_id
            )
        )
    )
    transformation = session.exec(
        select(DataTransformation).where(
            DataTransformation.target_dataset_version_id == target_version_id
        )
    ).first()
    return _encoded(
        {
            "dataset_id": dataset.id,
            "base_version_id": base_version_id,
            "target_version_id": target_version_id,
            "row_count": {
                "before": by_id[base_version_id].row_count,
                "after": by_id[target_version_id].row_count,
                "delta": (by_id[target_version_id].row_count or 0)
                - (by_id[base_version_id].row_count or 0),
            },
            "column_count": {
                "before": by_id[base_version_id].column_count,
                "after": by_id[target_version_id].column_count,
                "delta": (by_id[target_version_id].column_count or 0)
                - (by_id[base_version_id].column_count or 0),
            },
            "missing_cells": {
                "before": sum(
                    round(
                        (column.missing_ratio or 0)
                        * (by_id[base_version_id].row_count or 0)
                    )
                    for column in base_columns
                ),
                "after": sum(
                    round(
                        (column.missing_ratio or 0)
                        * (by_id[target_version_id].row_count or 0)
                    )
                    for column in target_columns
                ),
            },
            "actions": [
                _action_payload(row)
                for row in _action_rows(session, transformation.cleaning_plan_id)
            ]
            if transformation
            else [],
            "affected_row_count": transformation.affected_row_count
            if transformation
            else None,
            "affected_column_count": transformation.affected_column_count
            if transformation
            else None,
            "lineage": {
                "parent_version_id": by_id[target_version_id].parent_version_id,
                "transformation_id": transformation.id if transformation else None,
                "output_artifact_id": transformation.output_artifact_id
                if transformation
                else None,
            },
        }
    )
