from __future__ import annotations

import math
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.adapters.storage import ObjectStorage
from app.api.errors import ContractError
from app.approvals import service as approval_service
from app.artifacts import service as artifact_service
from app.jobs import service as job_service
from app.jobs.dispatcher import dispatcher as default_dispatcher
from app.models import (
    ApprovalRecord,
    ApprovalStatus,
    ApprovalType,
    Artifact,
    ArtifactStatus,
    ArtifactType,
    AuditActorType,
    Export,
    ExportStatus,
    ExportType,
    Job,
    JobTaskType,
    ProjectMemberRole,
    ReproPackage,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

from .collector import enumerate_candidates
from .readiness import run_readiness
from .schemas import (
    ExportPublic,
    ExportReadinessRequest,
    ReproPackageCreate,
    ReproPackageHistoryItem,
    ReproPackagePublic,
)

READINESS_PATH = "/api/v1/projects/{project_id}/exports/readiness-check"
CREATE_PATH = "/api/v1/projects/{project_id}/exports/repro-package"
EXPORT_APPROVAL_TARGET = "export"
APPROVAL_TTL = timedelta(hours=24)


def _not_found() -> ContractError:
    return ContractError(
        status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
    )


def _role(access: project_service.ProjectAccess) -> ProjectMemberRole:
    return access.membership.role if access.membership else ProjectMemberRole.OWNER


def _allowed_actions(role: ProjectMemberRole, export: Export) -> list[str]:
    permissions = project_service.ROLE_ACTIONS[role]
    actions = ["export.read"]
    if (
        export.status == ExportStatus.NEEDS_CONFIRMATION
        and "export.confirm" in permissions
    ):
        actions.append("export.confirm")
    if (
        export.status in {ExportStatus.QUEUED, ExportStatus.PACKAGING}
        and "job.cancel" in permissions
    ):
        actions.append("job.cancel")
    return actions


def export_data(export: Export, role: ProjectMemberRole) -> ExportPublic:
    return ExportPublic(
        id=export.id,
        project_id=export.project_id,
        export_type=export.export_type,
        status=export.status,
        scope=export.scope,
        scope_hash=export.scope_hash,
        readiness_audit_id=export.readiness_audit_id,
        approval_record_id=export.approval_record_id,
        job_id=export.job_id,
        lock_version=export.lock_version,
        error_code=export.error_code,
        created_at=export.created_at,
        completed_at=export.completed_at,
        allowed_actions=_allowed_actions(role, export),
    )


def package_data(
    session: Session, package: ReproPackage, role: ProjectMemberRole
) -> ReproPackagePublic:
    actions = ["export.read"]
    if "export.download" in project_service.ROLE_ACTIONS[role]:
        actions.append("export.download")
    manifest_artifact = session.get(Artifact, package.manifest_artifact_id)
    if (
        manifest_artifact is None
        or manifest_artifact.project_id != package.project_id
        or manifest_artifact.artifact_type != ArtifactType.MANIFEST
        or manifest_artifact.status != ArtifactStatus.AVAILABLE
    ):
        raise ContractError(
            status_code=409,
            code="MANIFEST_NOT_AVAILABLE",
            message="ReproPackage Manifest is unavailable or inconsistent.",
        )
    manifest = (manifest_artifact.artifact_metadata or {}).get("manifest")
    if not isinstance(manifest, dict):
        raise ContractError(
            status_code=409,
            code="MANIFEST_INVALID",
            message="ReproPackage Manifest metadata is invalid.",
        )
    return ReproPackagePublic(
        id=package.id,
        export_id=package.export_id,
        project_id=package.project_id,
        artifact_id=package.artifact_id,
        manifest_artifact_id=package.manifest_artifact_id,
        package_version=package.package_version,
        schema_version=package.schema_version,
        contains_sensitive_data=package.contains_sensitive_data,
        contains_restricted_data=package.contains_restricted_data,
        file_count=package.file_count,
        total_size_bytes=package.total_size_bytes,
        sha256=package.sha256,
        manifest_sha256=manifest_artifact.sha256,
        manifest=manifest,
        created_at=package.created_at,
        allowed_actions=actions,
    )


def package_history_data(
    package: ReproPackage, role: ProjectMemberRole
) -> ReproPackageHistoryItem:
    actions = ["export.read"]
    if "export.download" in project_service.ROLE_ACTIONS[role]:
        actions.append("export.download")
    return ReproPackageHistoryItem(
        id=package.id,
        export_id=package.export_id,
        project_id=package.project_id,
        artifact_id=package.artifact_id,
        manifest_artifact_id=package.manifest_artifact_id,
        package_version=package.package_version,
        schema_version=package.schema_version,
        contains_sensitive_data=package.contains_sensitive_data,
        contains_restricted_data=package.contains_restricted_data,
        file_count=package.file_count,
        total_size_bytes=package.total_size_bytes,
        sha256=package.sha256,
        created_at=package.created_at,
        allowed_actions=actions,
    )


def _audit_key(prefix: str, actor_id: uuid.UUID, key: str) -> str:
    return f"{prefix}:{uuid.uuid5(uuid.NAMESPACE_URL, f'{actor_id}:{key}')}"


def readiness_check(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    request: ExportReadinessRequest,
    idempotency_key: str,
) -> project_service.OperationResult:
    project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="export.readiness"
    )
    digest = project_service.request_hash(request)
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=READINESS_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay:
        return replay
    readiness = run_readiness(
        session,
        project_id=project_id,
        actor=actor,
        request=request,
        idempotency_key=_audit_key("readiness", actor.id, idempotency_key),
    )
    result = project_service.OperationResult(
        data=jsonable_encoder(readiness), status_code=200
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=READINESS_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result


def _approval_payload_from_values(
    *, export: Export, readiness_hash: str, candidate_hash: str
) -> dict[str, Any]:
    request = dict(export.scope.get("request", {}))
    return {
        "schema": "reca.export-confirmation.v1",
        "export_id": str(export.id),
        "project_id": str(export.project_id),
        "export_scope_hash": export.scope_hash,
        "readiness_audit_id": str(export.readiness_audit_id),
        "readiness_snapshot_hash": readiness_hash,
        "candidate_items_hash": candidate_hash,
        "acknowledgements": {
            "include_sensitive_data": bool(request.get("include_sensitive_data")),
            "acknowledge_license_warnings": bool(
                request.get("acknowledge_license_warnings")
            ),
        },
        "policy_version": "m7-export-policy/1.0",
        "schema_version": "reca.repro-manifest.v1",
    }


def resolve_export_approval_payload(
    session: Session, approval: ApprovalRecord
) -> dict[str, Any]:
    export = session.get(Export, approval.target_object_id)
    if (
        export is None
        or export.project_id != approval.project_id
        or export.approval_record_id != approval.id
        or export.readiness_audit_id is None
    ):
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="Export confirmation target is unavailable.",
        )
    request = ReproPackageCreate.model_validate(export.scope.get("request", {}))
    candidates, blocking, warnings, limitations = enumerate_candidates(
        session, project_id=export.project_id, request=request
    )
    if blocking:
        return _approval_payload_from_values(
            export=export,
            readiness_hash="0" * 64,
            candidate_hash=project_service.request_hash(jsonable_encoder(candidates)),
        )
    current_snapshot = {
        "schema": "reca.export-readiness-snapshot.v1",
        "project_id": str(export.project_id),
        "scope": jsonable_encoder(request),
        "candidate_items": jsonable_encoder(candidates),
        "blocking_issues": blocking,
        "warnings": warnings,
        "limitations": limitations,
        "rule_set_version": export.scope.get("rule_set_version"),
    }
    return _approval_payload_from_values(
        export=export,
        readiness_hash=project_service.request_hash(current_snapshot),
        candidate_hash=project_service.request_hash(jsonable_encoder(candidates)),
    )


def _prepare_export_job(
    session: Session,
    *,
    export: Export,
    actor: User,
) -> Job:
    job = job_service.create_job(
        session,
        project_id=export.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.REPRO_PACKAGE_EXPORT,
            resource_type="export",
            resource_id=export.id,
            idempotency_key=f"repro-package:{export.id}",
            requested_by_user_id=actor.id,
            max_retries=2,
            retryable=True,
        ),
    )
    export.status = ExportStatus.QUEUED
    export.job_id = job.id
    export.lock_version += 1
    session.add(export)
    return job


def create_repro_package_export(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    request: ReproPackageCreate,
    idempotency_key: str,
    dispatcher: job_service.JobDispatcher = default_dispatcher,
) -> project_service.OperationResult:
    access = project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="export.create",
        for_update=True,
    )
    digest = project_service.request_hash(request)
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=CREATE_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay:
        return replay
    export = Export(
        project_id=project_id,
        export_type=ExportType.REPRO_PACKAGE,
        status=ExportStatus.VALIDATING,
        requested_by_user_id=actor.id,
        scope={"request": jsonable_encoder(request)},
        scope_hash=project_service.request_hash({"request": request}),
        idempotency_key=idempotency_key,
    )
    session.add(export)
    session.flush()
    readiness = run_readiness(
        session,
        project_id=project_id,
        actor=actor,
        request=ExportReadinessRequest.model_validate(request.model_dump()),
        idempotency_key=f"export-readiness:{export.id}",
    )
    candidate_hash = project_service.request_hash(
        jsonable_encoder(readiness.candidate_items)
    )
    export.readiness_audit_id = readiness.audit_id
    export.scope = {
        "request": jsonable_encoder(request),
        "readiness_snapshot": readiness.snapshot,
        "readiness_snapshot_hash": readiness.snapshot_hash,
        "candidate_items_hash": candidate_hash,
        "rule_set_version": readiness.rule_set_version,
    }
    export.scope_hash = project_service.request_hash(export.scope)
    if not readiness.ready:
        export.status = ExportStatus.FAILED
        export.error_code = "EXPORT_NOT_READY"
        export.lock_version += 1
        session.add(export)
        result = project_service.OperationResult(
            data={
                "export": jsonable_encoder(export_data(export, _role(access))),
                "readiness": jsonable_encoder(readiness),
            },
            status_code=409,
        )
    elif readiness.requires_confirmation:
        export.status = ExportStatus.NEEDS_CONFIRMATION
        export.lock_version += 1
        session.add(export)
        session.flush()
        payload = _approval_payload_from_values(
            export=export,
            readiness_hash=readiness.snapshot_hash,
            candidate_hash=candidate_hash,
        )
        warning_ids = sorted(
            {
                item.object_id
                for item in readiness.warnings
                if item.object_id is not None
            },
            key=str,
        )
        approval = approval_service.create_approval(
            session,
            command=approval_service.ApprovalCreate(
                project_id=project_id,
                approval_type=ApprovalType.EXPORT_CONFIRMATION,
                target_object_type=EXPORT_APPROVAL_TARGET,
                target_object_id=export.id,
                requested_by_actor_type=AuditActorType.USER,
                requested_by_actor_id=str(actor.id),
                payload_snapshot=payload,
                impact_summary={
                    "warning_count": len(readiness.warnings),
                    "contains_sensitive_request": request.include_sensitive_data,
                },
                expires_at=get_datetime_utc() + APPROVAL_TTL,
                items=tuple(
                    approval_service.ApprovalItemCreate(
                        item_type="export_warning", item_id=item_id
                    )
                    for item_id in warning_ids
                ),
            ),
        )
        export.approval_record_id = approval.id
        session.add(export)
        result = project_service.OperationResult(
            data={
                "export": jsonable_encoder(export_data(export, _role(access))),
                "readiness": jsonable_encoder(readiness),
                "approval": approval_service.approval_data(
                    session,
                    approval=approval,
                    actor=actor,
                    role=_role(access),
                    administrative_override=False,
                    include_payload=True,
                ),
            },
            status_code=202,
        )
    else:
        job = _prepare_export_job(session, export=export, actor=actor)
        result = project_service.OperationResult(
            data={
                "export": jsonable_encoder(export_data(export, _role(access))),
                "readiness": jsonable_encoder(readiness),
                "job": job_service.job_data(session, job),
            },
            status_code=202,
        )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=CREATE_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    if export.job_id is not None and export.status == ExportStatus.QUEUED:
        dispatched = job_service.dispatch_job(
            session, job_id=export.job_id, dispatcher=dispatcher
        )
        result = project_service.OperationResult(
            data={
                "export": jsonable_encoder(export_data(export, _role(access))),
                "readiness": jsonable_encoder(readiness),
                "job": job_service.job_data(session, dispatched),
            },
            status_code=202,
        )
        project_service._update_idempotency_result(
            session,
            actor_id=actor.id,
            project_id=project_id,
            method="POST",
            path_template=CREATE_PATH,
            key=idempotency_key,
            result=result,
        )
        project_service._commit(session)
    return result


def apply_export_approval_decision(
    session: Session,
    approval: ApprovalRecord,
    status: ApprovalStatus,
    actor: User,
) -> approval_service.PostCommitAction | None:
    export = session.exec(
        select(Export).where(Export.id == approval.target_object_id).with_for_update()
    ).first()
    if export is None or export.project_id != approval.project_id:
        raise _not_found()
    project_service.authorize_project(
        session,
        project_id=export.project_id,
        actor=actor,
        action="export.confirm",
        for_update=True,
    )
    if export.status != ExportStatus.NEEDS_CONFIRMATION:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Export is not awaiting confirmation.",
        )
    if status == ApprovalStatus.REJECTED:
        export.status = ExportStatus.CANCELLED
        export.completed_at = get_datetime_utc()
        export.lock_version += 1
        session.add(export)
        return None
    if status != ApprovalStatus.APPROVED:
        return None
    job = _prepare_export_job(session, export=export, actor=actor)
    job_id = job.id

    def dispatch_after_commit() -> None:
        job_service.dispatch_job(session, job_id=job_id, dispatcher=default_dispatcher)

    return dispatch_after_commit


def register_approval_handlers() -> None:
    approval_service.register_payload_resolver(
        EXPORT_APPROVAL_TARGET, resolve_export_approval_payload
    )
    approval_service.register_decision_handler(
        EXPORT_APPROVAL_TARGET,
        apply_export_approval_decision,
        permission_action="export.confirm",
    )


def get_export(session: Session, *, actor: User, export_id: uuid.UUID) -> ExportPublic:
    export = session.get(Export, export_id)
    if export is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=export.project_id, actor=actor, action="export.read"
    )
    return export_data(export, _role(access))


def get_repro_package(
    session: Session, *, actor: User, package_id: uuid.UUID
) -> ReproPackagePublic:
    package = session.get(ReproPackage, package_id)
    if package is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=package.project_id, actor=actor, action="export.read"
    )
    return package_data(session, package, _role(access))


def list_repro_packages(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    page: int,
    page_size: int,
) -> tuple[list[ReproPackageHistoryItem], dict[str, Any]]:
    access = project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="export.read"
    )
    total = session.exec(
        select(func.count())
        .select_from(ReproPackage)
        .where(ReproPackage.project_id == project_id)
    ).one()
    packages = session.exec(
        select(ReproPackage)
        .where(ReproPackage.project_id == project_id)
        .order_by(col(ReproPackage.package_version).desc(), col(ReproPackage.id).desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    total_pages = math.ceil(total / page_size) if total else 0
    return [package_history_data(item, _role(access)) for item in packages], {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1 and total_pages > 0,
    }


def authorize_package_download(
    session: Session,
    *,
    actor: User,
    package_id: uuid.UUID,
    storage_backend: ObjectStorage | None = None,
) -> dict[str, Any]:
    package = session.get(ReproPackage, package_id)
    if package is None:
        raise _not_found()
    access = project_service.authorize_project(
        session,
        project_id=package.project_id,
        actor=actor,
        action="export.download",
    )
    artifact = session.get(Artifact, package.artifact_id)
    if (
        artifact is None
        or artifact.project_id != package.project_id
        or artifact.artifact_type != ArtifactType.REPRO_PACKAGE
        or artifact.status != ArtifactStatus.AVAILABLE
        or artifact.sha256 != package.sha256
    ):
        raise ContractError(
            status_code=409,
            code="PACKAGE_NOT_AVAILABLE",
            message="ReproPackage Artifact is unavailable or inconsistent.",
        )
    with tempfile.TemporaryDirectory(
        prefix="reca-package-download-verify-"
    ) as directory:
        path = Path(directory) / artifact.filename
        artifact_service.download_available_artifact_to_path(
            session,
            artifact_id=artifact.id,
            project_id=package.project_id,
            path=path,
            storage_backend=storage_backend,
        )
    download = artifact_service.authorize_download(
        session,
        actor=actor,
        artifact_id=artifact.id,
        storage_backend=storage_backend,
    )
    return {
        "package": jsonable_encoder(package_data(session, package, _role(access))),
        "download": download,
    }


def mark_failed_export_job(session: Session, *, job: Job, error_code: str) -> None:
    export = session.get(Export, job.resource_id)
    if export and export.status != ExportStatus.COMPLETED:
        export.status = ExportStatus.FAILED
        export.error_code = error_code
        export.completed_at = get_datetime_utc()
        export.lock_version += 1
        session.add(export)


def mark_cancelled_export_job(session: Session, *, job: Job) -> None:
    export = session.get(Export, job.resource_id)
    if export and export.status != ExportStatus.COMPLETED:
        export.status = ExportStatus.CANCELLED
        export.completed_at = get_datetime_utc()
        export.lock_version += 1
        session.add(export)
    project_service._commit(session)
