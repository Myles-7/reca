from __future__ import annotations

import hashlib
import importlib.metadata
import math
import os
import platform
import tempfile
import uuid
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc, func
from sqlmodel import Session, col, select

from app.adapters.storage import ObjectStorage, StorageError
from app.api.errors import ContractError
from app.artifacts import service as artifact_service
from app.core.observability import current_request_id
from app.data_quality.engine import ColumnContext, load_dataframe, scan_dataframe
from app.data_quality.registry import (
    RuleSet,
    resolve_persisted_ruleset,
    select_ruleset,
)
from app.data_quality.schemas import (
    QualityIssueAcknowledge,
    QualityIssueIgnore,
    QualityRunCreate,
)
from app.datasets import service as dataset_service
from app.jobs import service as job_service
from app.models import (
    Artifact,
    ArtifactStatus,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    DataQualityIssue,
    DataQualityIssueStatus,
    DataQualityIssueType,
    DataQualityRun,
    DataQualityRunStatus,
    DataQualitySeverity,
    DatasetColumn,
    DatasetVersion,
    DatasetVersionStatus,
    Job,
    JobStatus,
    JobTaskType,
    ProjectMemberRole,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

QUALITY_RUN_PATH = "/api/v1/dataset-versions/{version_id}/quality-runs"
ACKNOWLEDGE_PATH = "/api/v1/data-quality-issues/{issue_id}/acknowledge"
IGNORE_PATH = "/api/v1/data-quality-issues/{issue_id}/ignore"
ENGINE_VERSION = "1.0.0"


class QualityExecutionError(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable

    def __str__(self) -> str:
        return self.message


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


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
    job_id: uuid.UUID | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
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
            job_id=job_id,
            outcome=outcome,
        )
    )


def _role_actions(role: ProjectMemberRole) -> set[str]:
    return set(project_service.ROLE_ACTIONS[role])


def _run_allowed_actions(role: ProjectMemberRole, run: DataQualityRun) -> list[str]:
    actions = _role_actions(role)
    result = ["quality.read"]
    if (
        run.status == DataQualityRunStatus.COMPLETED
        and "dataset.quality.review" in actions
    ):
        result.extend(["quality.issue.acknowledge", "quality.issue.ignore"])
    return result


def _issue_allowed_actions(
    role: ProjectMemberRole, issue: DataQualityIssue
) -> list[str]:
    actions = _role_actions(role)
    if "dataset.quality.review" not in actions:
        return ["quality.read"]
    result = ["quality.read"]
    if issue.status == DataQualityIssueStatus.OPEN:
        result.extend(["quality.issue.acknowledge", "quality.issue.ignore"])
    elif issue.status in {
        DataQualityIssueStatus.ACKNOWLEDGED,
        DataQualityIssueStatus.PLANNED,
    }:
        result.append("quality.issue.ignore")
    return result


def _membership_role(access: project_service.ProjectAccess) -> ProjectMemberRole:
    assert access.membership is not None
    return access.membership.role


def _job_for_run(session: Session, run: DataQualityRun) -> Job | None:
    return session.exec(
        select(Job)
        .where(
            Job.project_id == run.project_id,
            Job.task_type == JobTaskType.DATASET_PROFILE,
            Job.resource_type == "data_quality_run",
            Job.resource_id == run.id,
        )
        .order_by(desc(col(Job.created_at)))
    ).first()


def _run_data(
    session: Session,
    run: DataQualityRun,
    role: ProjectMemberRole,
) -> dict[str, Any]:
    job = _job_for_run(session, run)
    ruleset, include_sensitive = resolve_persisted_ruleset(
        ruleset_id=run.ruleset_id,
        version=run.rule_set_version,
        content_hash=run.ruleset_hash,
    )
    return _encoded(
        {
            "id": run.id,
            "project_id": run.project_id,
            "dataset_version_id": run.dataset_version_id,
            "ruleset_id": run.ruleset_id,
            "ruleset_version": run.rule_set_version,
            "ruleset_hash": run.ruleset_hash,
            "selected_rule_ids": [rule.rule_id for rule in ruleset.rules],
            "include_sensitive_field_detection": include_sensitive,
            "status": run.status,
            "issue_count": run.issue_count,
            "high_issue_count": run.high_issue_count,
            "processing_run_id": run.processing_run_id,
            "job_id": job.id if job else None,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "error_code": run.error_code,
            "created_at": run.created_at,
            "allowed_actions": _run_allowed_actions(role, run),
        }
    )


def _issue_data(issue: DataQualityIssue, role: ProjectMemberRole) -> dict[str, Any]:
    return _encoded(
        {
            "id": issue.id,
            "project_id": issue.project_id,
            "data_quality_run_id": issue.data_quality_run_id,
            "dataset_version_id": issue.dataset_version_id,
            "rule_code": issue.rule_code,
            "issue_type": issue.issue_type,
            "severity": issue.severity,
            "column_id": issue.column_id,
            "affected_row_count": issue.affected_row_count,
            "affected_rows": issue.affected_rows,
            "evidence": issue.evidence,
            "description": issue.description,
            "suggested_actions": issue.suggested_actions,
            "requires_approval": issue.requires_approval,
            "status": issue.status,
            "created_at": issue.created_at,
            "resolved_at": issue.resolved_at,
            "allowed_actions": _issue_allowed_actions(role, issue),
        }
    )


def request_quality_run(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    payload: QualityRunCreate,
    idempotency_key: str,
    dispatcher: job_service.JobDispatcher,
) -> project_service.OperationResult:
    version, _, access = dataset_service._version_access(
        session,
        actor=actor,
        version_id=version_id,
        action="dataset.quality.run",
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
        path_template=QUALITY_RUN_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    if version.status != DatasetVersionStatus.AVAILABLE:
        raise ContractError(
            status_code=409,
            code="DATASET_VERSION_NOT_AVAILABLE",
            message="Only an AVAILABLE DatasetVersion can be scanned.",
        )
    artifact = session.exec(
        select(Artifact).where(
            Artifact.id == version.artifact_id,
            Artifact.project_id == version.project_id,
        )
    ).first()
    if (
        artifact is None
        or artifact.status != ArtifactStatus.AVAILABLE
        or artifact.sha256 != version.data_hash
    ):
        raise ContractError(
            status_code=409,
            code="DATASET_HASH_MISMATCH",
            message="The DatasetVersion Artifact identity is not valid for scanning.",
        )
    ruleset = select_ruleset(
        payload.rule_set,
        include_sensitive_field_detection=payload.include_sensitive_field_detection,
    )
    run = DataQualityRun(
        project_id=version.project_id,
        dataset_version_id=version.id,
        ruleset_id=ruleset.ruleset_id,
        rule_set_version=ruleset.version,
        ruleset_hash=ruleset.content_hash,
        status=DataQualityRunStatus.QUEUED,
    )
    session.add(run)
    session.flush()
    job = job_service.create_job(
        session,
        project_id=version.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.DATASET_PROFILE,
            resource_type="data_quality_run",
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
        action="DATA_QUALITY_RUN_REQUESTED",
        object_type="data_quality_run",
        object_id=run.id,
        job_id=job.id,
        after={
            "dataset_version_id": str(version.id),
            "ruleset_id": ruleset.ruleset_id,
            "ruleset_version": ruleset.version,
            "ruleset_hash": ruleset.content_hash,
        },
    )
    initial = project_service.OperationResult(
        data={
            "run": _run_data(session, run, _membership_role(access)),
            "job": job_service.job_data(session, job),
        },
        status_code=202,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        method="POST",
        path_template=QUALITY_RUN_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=initial,
    )
    project_service._commit(session)
    dispatched = job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)
    if dispatched.status == JobStatus.DISPATCH_FAILED:
        failed = session.exec(
            select(DataQualityRun).where(DataQualityRun.id == run.id).with_for_update()
        ).one()
        failed.status = DataQualityRunStatus.FAILED
        failed.error_code = "JOB_DISPATCH_FAILED"
        failed.completed_at = get_datetime_utc()
        session.add(failed)
        project_service._commit(session)
    session.refresh(run)
    result = project_service.OperationResult(
        data={
            "run": _run_data(session, run, _membership_role(access)),
            "job": job_service.job_data(session, dispatched),
        },
        status_code=202,
    )
    project_service._update_idempotency_result(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        method="POST",
        path_template=QUALITY_RUN_PATH,
        key=idempotency_key,
        result=result,
    )
    project_service._commit(session)
    return result


def _visible_run(
    session: Session,
    *,
    actor: User,
    run_id: uuid.UUID,
) -> tuple[DataQualityRun, project_service.ProjectAccess]:
    run = session.get(DataQualityRun, run_id)
    if run is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    access = project_service.authorize_project(
        session, project_id=run.project_id, actor=actor, action="dataset.read"
    )
    return run, access


def get_run(session: Session, *, actor: User, run_id: uuid.UUID) -> dict[str, Any]:
    run, access = _visible_run(session, actor=actor, run_id=run_id)
    return _run_data(session, run, _membership_role(access))


def list_issues(
    session: Session,
    *,
    actor: User,
    run_id: uuid.UUID,
    severity: DataQualitySeverity | None,
    issue_type: DataQualityIssueType | None,
    status: DataQualityIssueStatus | None,
    column_id: uuid.UUID | None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    run, access = _visible_run(session, actor=actor, run_id=run_id)
    filters: list[Any] = [DataQualityIssue.data_quality_run_id == run.id]
    if severity is not None:
        filters.append(DataQualityIssue.severity == severity)
    if issue_type is not None:
        filters.append(DataQualityIssue.issue_type == issue_type)
    if status is not None:
        filters.append(DataQualityIssue.status == status)
    if column_id is not None:
        filters.append(DataQualityIssue.column_id == column_id)
    total = session.exec(
        select(func.count()).select_from(DataQualityIssue).where(*filters)
    ).one()
    issues = session.exec(
        select(DataQualityIssue)
        .where(*filters)
        .order_by(
            col(DataQualityIssue.created_at),
            col(DataQualityIssue.rule_code),
            col(DataQualityIssue.id),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    total_pages = math.ceil(total / page_size) if total else 0
    role = _membership_role(access)
    return [_issue_data(issue, role) for issue in issues], {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


def _transition_issue(
    session: Session,
    *,
    actor: User,
    issue_id: uuid.UUID,
    target: DataQualityIssueStatus,
    reason: str | None,
    idempotency_key: str,
) -> project_service.OperationResult:
    issue = session.exec(
        select(DataQualityIssue)
        .where(DataQualityIssue.id == issue_id)
        .with_for_update()
    ).first()
    if issue is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    access = project_service.authorize_project(
        session,
        project_id=issue.project_id,
        actor=actor,
        action="dataset.quality.review",
        for_update=True,
    )
    path = (
        ACKNOWLEDGE_PATH
        if target == DataQualityIssueStatus.ACKNOWLEDGED
        else IGNORE_PATH
    )
    digest = project_service.request_hash({"issue_id": str(issue.id), "reason": reason})
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=issue.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    allowed_sources = (
        {DataQualityIssueStatus.OPEN}
        if target == DataQualityIssueStatus.ACKNOWLEDGED
        else {
            DataQualityIssueStatus.OPEN,
            DataQualityIssueStatus.ACKNOWLEDGED,
            DataQualityIssueStatus.PLANNED,
        }
    )
    if issue.status not in allowed_sources:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="The data quality issue cannot enter the requested state.",
        )
    before = {"status": issue.status}
    issue.status = target
    if target == DataQualityIssueStatus.IGNORED:
        issue.resolved_at = get_datetime_utc()
    session.add(issue)
    _audit(
        session,
        project_id=issue.project_id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        action=(
            "DATA_QUALITY_ISSUE_ACKNOWLEDGED"
            if target == DataQualityIssueStatus.ACKNOWLEDGED
            else "DATA_QUALITY_ISSUE_IGNORED"
        ),
        object_type="data_quality_issue",
        object_id=issue.id,
        before=before,
        after={"status": issue.status},
        reason=reason,
    )
    result = project_service.OperationResult(
        data=_issue_data(issue, _membership_role(access)), status_code=200
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=issue.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result


def acknowledge_issue(
    session: Session,
    *,
    actor: User,
    issue_id: uuid.UUID,
    payload: QualityIssueAcknowledge,
    idempotency_key: str,
) -> project_service.OperationResult:
    return _transition_issue(
        session,
        actor=actor,
        issue_id=issue_id,
        target=DataQualityIssueStatus.ACKNOWLEDGED,
        reason=payload.reason,
        idempotency_key=idempotency_key,
    )


def ignore_issue(
    session: Session,
    *,
    actor: User,
    issue_id: uuid.UUID,
    payload: QualityIssueIgnore,
    idempotency_key: str,
) -> project_service.OperationResult:
    return _transition_issue(
        session,
        actor=actor,
        issue_id=issue_id,
        target=DataQualityIssueStatus.IGNORED,
        reason=payload.reason.strip(),
        idempotency_key=idempotency_key,
    )


def _implementation_metadata(
    *,
    ruleset: RuleSet,
    include_sensitive: bool,
    version: DatasetVersion,
) -> dict[str, Any]:
    return {
        "engine": "reca-data-quality",
        "engine_version": ENGINE_VERSION,
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "pandera_version": importlib.metadata.version("pandera"),
        "openpyxl_version": importlib.metadata.version("openpyxl"),
        "ruleset_id": ruleset.ruleset_id,
        "ruleset_version": ruleset.version,
        "ruleset_hash": ruleset.content_hash,
        "selected_rule_ids": [rule.rule_id for rule in ruleset.rules],
        "include_sensitive_field_detection": include_sensitive,
        "code_revision": os.getenv("RECA_CODE_REVISION", "workspace-uncommitted"),
        "input_dataset_version_id": str(version.id),
        "input_data_hash": version.data_hash,
        "lazy": True,
        "coerce": False,
        "normalization_copy_only": True,
        "max_affected_rows": 100,
        "max_examples": 5,
    }


def _fail_run(
    session: Session,
    *,
    run_id: uuid.UUID,
    processing_run_id: uuid.UUID,
    code: str,
) -> None:
    session.rollback()
    run = session.exec(
        select(DataQualityRun).where(DataQualityRun.id == run_id).with_for_update()
    ).first()
    if run is None or run.status == DataQualityRunStatus.COMPLETED:
        return
    run.status = DataQualityRunStatus.FAILED
    run.processing_run_id = processing_run_id
    run.completed_at = get_datetime_utc()
    run.error_code = code
    session.add(run)
    _audit(
        session,
        project_id=run.project_id,
        actor_type=AuditActorType.WORKER,
        actor_id="data-quality-worker",
        action="DATA_QUALITY_RUN_FAILED",
        object_type="data_quality_run",
        object_id=run.id,
        after={"status": run.status, "error_code": code},
        outcome=AuditOutcome.FAILED,
    )
    project_service._commit(session)


def execute_quality_job(
    session: Session,
    *,
    job: Job,
    run_id: uuid.UUID,
    storage_backend: ObjectStorage | None = None,
) -> DataQualityRun:
    quality_run_id = job.resource_id
    try:
        if (
            job.task_type != JobTaskType.DATASET_PROFILE
            or job.resource_type != "data_quality_run"
        ):
            raise QualityExecutionError(
                "JOB_HANDLER_MISMATCH",
                "Job is not a data quality scan.",
                False,
            )
        run = session.exec(
            select(DataQualityRun)
            .where(DataQualityRun.id == quality_run_id)
            .with_for_update()
        ).first()
        if run is None or run.project_id != job.project_id:
            raise QualityExecutionError(
                "DATA_QUALITY_RUN_INVALID",
                "DataQualityRun is not available for this Job.",
                False,
            )
        actor = session.get(User, job.requested_by_user_id)
        if actor is None:
            raise QualityExecutionError(
                "QUALITY_REQUEST_ACTOR_INVALID",
                "The requesting actor is no longer available.",
                False,
            )
        try:
            project_service.authorize_project(
                session,
                project_id=run.project_id,
                actor=actor,
                action="dataset.quality.run",
                for_update=True,
            )
        except ContractError as error:
            raise QualityExecutionError(
                "QUALITY_REQUEST_PERMISSION_STALE",
                "The requesting actor no longer has scan permission.",
                False,
            ) from error
        version = session.exec(
            select(DatasetVersion)
            .where(DatasetVersion.id == run.dataset_version_id)
            .with_for_update()
        ).first()
        if (
            version is None
            or version.project_id != run.project_id
            or version.status != DatasetVersionStatus.AVAILABLE
        ):
            raise QualityExecutionError(
                "DATASET_VERSION_NOT_AVAILABLE",
                "The DatasetVersion is no longer available for scanning.",
                False,
            )
        artifact = session.exec(
            select(Artifact).where(
                Artifact.id == version.artifact_id,
                Artifact.project_id == run.project_id,
            )
        ).first()
        if (
            artifact is None
            or artifact.status != ArtifactStatus.AVAILABLE
            or artifact.sha256 != version.data_hash
        ):
            raise QualityExecutionError(
                "DATASET_HASH_MISMATCH",
                "The immutable Artifact identity changed before scanning.",
                False,
            )
        ruleset, include_sensitive = resolve_persisted_ruleset(
            ruleset_id=run.ruleset_id,
            version=run.rule_set_version,
            content_hash=run.ruleset_hash,
        )
        columns = session.exec(
            select(DatasetColumn)
            .where(
                DatasetColumn.dataset_version_id == version.id,
                DatasetColumn.project_id == version.project_id,
            )
            .order_by(col(DatasetColumn.column_order))
        ).all()
        if not columns:
            raise QualityExecutionError(
                "DATASET_COLUMNS_MISSING",
                "DatasetVersion has no field dictionary.",
                False,
            )
        metadata = _implementation_metadata(
            ruleset=ruleset,
            include_sensitive=include_sensitive,
            version=version,
        )
        job_service.set_run_context(
            session,
            job_id=job.id,
            run_id=run_id,
            input_hash=version.data_hash,
            parameters={
                "ruleset_id": ruleset.ruleset_id,
                "ruleset_version": ruleset.version,
                "ruleset_hash": ruleset.content_hash,
                "include_sensitive_field_detection": include_sensitive,
            },
            implementation_metadata=metadata,
        )
        run = session.get(DataQualityRun, run.id)
        assert run is not None
        run.status = DataQualityRunStatus.RUNNING
        run.processing_run_id = run_id
        run.started_at = get_datetime_utc()
        run.error_code = None
        session.add(run)
        project_service._commit(session)

        suffix = ".csv" if version.file_format.value == "CSV" else ".xlsx"
        with tempfile.TemporaryDirectory(prefix="reca-quality-") as directory:
            local = Path(directory) / f"source{suffix}"
            try:
                artifact_service.download_available_artifact_to_path(
                    session,
                    artifact_id=artifact.id,
                    project_id=run.project_id,
                    path=local,
                    storage_backend=storage_backend,
                )
            except StorageError as error:
                if local.exists() and _sha256_path(local) != version.data_hash:
                    raise QualityExecutionError(
                        "DATASET_HASH_MISMATCH",
                        "Downloaded Artifact hash does not match DatasetVersion.",
                        False,
                    ) from error
                raise QualityExecutionError(
                    "DATASET_ARTIFACT_READ_FAILED",
                    "The immutable dataset Artifact could not be read.",
                    True,
                ) from error
            digest = _sha256_path(local)
            if digest != version.data_hash or digest != artifact.sha256:
                raise QualityExecutionError(
                    "DATASET_HASH_MISMATCH",
                    "Downloaded Artifact hash does not match DatasetVersion.",
                    False,
                )
            frame = load_dataframe(local, version=version)
            before = frame.copy(deep=True)
            facts = scan_dataframe(
                frame,
                columns=tuple(ColumnContext.from_model(column) for column in columns),
                ruleset=ruleset,
                include_sensitive_field_detection=include_sensitive,
            )
            pd.testing.assert_frame_equal(before, frame, check_exact=True)

        locked = session.exec(
            select(DataQualityRun).where(DataQualityRun.id == run.id).with_for_update()
        ).one()
        if locked.status != DataQualityRunStatus.RUNNING:
            raise QualityExecutionError(
                "INVALID_STATE_TRANSITION",
                "DataQualityRun is no longer RUNNING.",
                False,
            )
        existing = session.exec(
            select(func.count())
            .select_from(DataQualityIssue)
            .where(DataQualityIssue.data_quality_run_id == locked.id)
        ).one()
        if existing:
            raise QualityExecutionError(
                "QUALITY_ISSUES_ALREADY_EXIST",
                "DataQualityRun already has persisted issues.",
                False,
            )
        for fact in facts:
            session.add(
                DataQualityIssue(
                    project_id=locked.project_id,
                    data_quality_run_id=locked.id,
                    dataset_version_id=locked.dataset_version_id,
                    rule_code=fact.rule_code,
                    issue_type=fact.issue_type,
                    severity=fact.severity,
                    column_id=fact.column_id,
                    affected_row_count=fact.affected_row_count,
                    affected_rows=list(fact.affected_rows),
                    evidence=fact.evidence,
                    description=fact.description,
                    suggested_actions=None,
                    requires_approval=fact.requires_approval,
                    status=DataQualityIssueStatus.OPEN,
                )
            )
        locked.status = DataQualityRunStatus.COMPLETED
        locked.issue_count = len(facts)
        locked.high_issue_count = sum(
            fact.severity == DataQualitySeverity.HIGH for fact in facts
        )
        locked.processing_run_id = run_id
        locked.completed_at = get_datetime_utc()
        locked.error_code = None
        session.add(locked)
        _audit(
            session,
            project_id=locked.project_id,
            actor_type=AuditActorType.WORKER,
            actor_id="data-quality-worker",
            action="DATA_QUALITY_RUN_COMPLETED",
            object_type="data_quality_run",
            object_id=locked.id,
            job_id=job.id,
            after={
                "issue_count": locked.issue_count,
                "high_issue_count": locked.high_issue_count,
                "ruleset_hash": locked.ruleset_hash,
            },
        )
        project_service._commit(session)
        session.refresh(locked)
        return locked
    except QualityExecutionError as error:
        _fail_run(
            session,
            run_id=quality_run_id,
            processing_run_id=run_id,
            code=error.code,
        )
        raise
    except Exception as error:
        _fail_run(
            session,
            run_id=quality_run_id,
            processing_run_id=run_id,
            code="QUALITY_EXECUTION_FAILED",
        )
        raise QualityExecutionError(
            "QUALITY_EXECUTION_FAILED",
            "The deterministic quality scan failed.",
            True,
        ) from error
