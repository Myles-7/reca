from __future__ import annotations

import hashlib
import tempfile
import uuid
from collections.abc import Sequence
from pathlib import Path

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlmodel import Session, select

from app.adapters.storage import ObjectStorage, StorageError
from app.api.errors import ContractError
from app.artifacts import service as artifact_service
from app.jobs import service as job_service
from app.models import (
    ApprovalRecord,
    ApprovalStatus,
    Artifact,
    ArtifactStatus,
    ArtifactType,
    Export,
    ExportItem,
    ExportItemIncludeStatus,
    ExportStatus,
    Job,
    JobTaskType,
    ReproPackage,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

from .collector import (
    collect_metadata_members,
    enumerate_candidates,
    implementation_metadata,
)
from .manifest import (
    MANIFEST_SCHEMA_VERSION,
    PackageMember,
    build_manifest,
    build_readme,
    canonical_json,
)
from .safety import build_deterministic_zip, verify_zip
from .schemas import ReproPackageCreate


def _current_readiness_snapshot(
    *,
    export: Export,
    request: ReproPackageCreate,
    candidates: Sequence[object],
    blocking: list[dict[str, object]],
    warnings: list[dict[str, object]],
    limitations: list[str],
) -> dict[str, object]:
    return {
        "schema": "reca.export-readiness-snapshot.v1",
        "project_id": str(export.project_id),
        "scope": jsonable_encoder(request),
        "candidate_items": jsonable_encoder(candidates),
        "blocking_issues": blocking,
        "warnings": warnings,
        "limitations": limitations,
        "rule_set_version": export.scope.get("rule_set_version"),
    }


def _verify_approval(
    session: Session,
    *,
    export: Export,
) -> ApprovalRecord | None:
    if export.approval_record_id is None:
        return None
    approval = session.get(ApprovalRecord, export.approval_record_id)
    now = get_datetime_utc()
    if (
        approval is None
        or approval.project_id != export.project_id
        or approval.status != ApprovalStatus.APPROVED
        or approval.decision_by_user_id is None
        or (approval.expires_at is not None and approval.expires_at <= now)
    ):
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="Export confirmation is missing, expired, stale, or not approved.",
        )
    approver = session.get(User, approval.decision_by_user_id)
    if approver is None:
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="Export confirmation approver is no longer available.",
        )
    project_service.authorize_project(
        session,
        project_id=export.project_id,
        actor=approver,
        action="export.confirm",
    )
    from .service import resolve_export_approval_payload

    current = resolve_export_approval_payload(session, approval)
    if project_service.request_hash(current) != approval.payload_hash:
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="Export confirmation no longer matches the source snapshot.",
        )
    return approval


def _requirements_lock() -> bytes:
    root = Path(__file__).resolve().parents[3]
    pyproject = root / "backend/pyproject.toml"
    uv_lock = root / "uv.lock"
    parts = [
        "# RECA locked environment references",
        f"backend/pyproject.toml sha256={hashlib.sha256(pyproject.read_bytes()).hexdigest()}",
        f"uv.lock sha256={hashlib.sha256(uv_lock.read_bytes()).hexdigest()}",
    ]
    return ("\n".join(parts) + "\n").encode("utf-8")


def execute_export_job(
    session: Session,
    *,
    job: Job,
    run_id: uuid.UUID,
    storage_backend: ObjectStorage | None = None,
) -> ReproPackage:
    export = session.exec(
        select(Export).where(Export.id == job.resource_id).with_for_update()
    ).first()
    if (
        export is None
        or export.project_id != job.project_id
        or export.job_id != job.id
        or job.task_type != JobTaskType.REPRO_PACKAGE_EXPORT
        or job.resource_type != "export"
    ):
        raise ContractError(
            status_code=409,
            code="INVALID_JOB_INPUT",
            message="ReproPackage Job input is invalid.",
        )
    existing = session.exec(
        select(ReproPackage).where(ReproPackage.export_id == export.id)
    ).first()
    if existing is not None:
        if export.status != ExportStatus.COMPLETED:
            raise ContractError(
                status_code=409,
                code="EXPORT_HISTORY_INCONSISTENT",
                message="ReproPackage history conflicts with Export state.",
            )
        return existing
    if export.status != ExportStatus.QUEUED:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Export is not queued for packaging.",
        )
    actor = session.get(User, job.requested_by_user_id)
    if actor is None:
        raise ContractError(
            status_code=409,
            code="EXPORT_ACTOR_INVALID",
            message="Export requester is unavailable.",
        )
    project_service.authorize_project(
        session,
        project_id=export.project_id,
        actor=actor,
        action="export.create",
        for_update=True,
    )
    request = ReproPackageCreate.model_validate(export.scope.get("request", {}))
    candidates, blocking, warnings, limitations = enumerate_candidates(
        session, project_id=export.project_id, request=request
    )
    if blocking:
        raise ContractError(
            status_code=409,
            code="EXPORT_NOT_READY",
            message="Export sources are no longer ready.",
        )
    current_snapshot = _current_readiness_snapshot(
        export=export,
        request=request,
        candidates=candidates,
        blocking=blocking,
        warnings=warnings,
        limitations=limitations,
    )
    if project_service.request_hash(current_snapshot) != export.scope.get(
        "readiness_snapshot_hash"
    ) or project_service.request_hash(jsonable_encoder(candidates)) != export.scope.get(
        "candidate_items_hash"
    ):
        raise ContractError(
            status_code=409,
            code="EXPORT_SNAPSHOT_STALE",
            message="Export readiness snapshot changed before packaging.",
        )
    approval = _verify_approval(session, export=export)
    if (
        any(
            item.sensitive and item.include_status == ExportItemIncludeStatus.INCLUDED
            for item in candidates
        )
        and approval is None
    ):
        raise ContractError(
            status_code=409,
            code="EXPORT_CONFIRMATION_REQUIRED",
            message="Sensitive export content requires formal Approval.",
        )
    export.status = ExportStatus.PACKAGING
    export.lock_version += 1
    session.add(export)
    session.flush()
    members = collect_metadata_members(session, project_id=export.project_id)
    metadata_payload = {
        "schema": "reca.export-items.v1",
        "items": jsonable_encoder(candidates),
    }
    members.append(
        PackageMember(
            path="12_environment/export-items.json",
            content=canonical_json(metadata_payload),
            member_type="export-policy",
            source={"export_id": str(export.id)},
        )
    )
    root = Path(__file__).resolve().parents[3]
    members.extend(
        [
            PackageMember(
                path="requirements-lock.txt",
                content=_requirements_lock(),
                member_type="environment-lock",
                source={"files": ["backend/pyproject.toml", "uv.lock"]},
            ),
            PackageMember(
                path="12_environment/locks/uv.lock",
                content=(root / "uv.lock").read_bytes(),
                member_type="environment-lock",
                source={"path": "uv.lock"},
            ),
            PackageMember(
                path="12_environment/locks/bun.lock",
                content=(root / "bun.lock").read_bytes(),
                member_type="environment-lock",
                source={"path": "bun.lock"},
            ),
        ]
    )
    with tempfile.TemporaryDirectory(prefix="reca-repro-collect-") as directory:
        work = Path(directory)
        for candidate in candidates:
            if candidate.include_status != ExportItemIncludeStatus.INCLUDED:
                continue
            if candidate.artifact_id is None:
                raise ContractError(
                    status_code=409,
                    code="EXPORT_SOURCE_MISSING",
                    message="Included export item has no Artifact.",
                )
            artifact = session.get(Artifact, candidate.artifact_id)
            if (
                artifact is None
                or artifact.project_id != export.project_id
                or artifact.sha256 != candidate.sha256
            ):
                raise ContractError(
                    status_code=409,
                    code="EXPORT_SOURCE_HASH_MISMATCH",
                    message="Included Artifact changed before packaging.",
                )
            path = work / f"{artifact.id}.content"
            artifact_service.download_available_artifact_to_path(
                session,
                artifact_id=artifact.id,
                project_id=export.project_id,
                path=path,
                storage_backend=storage_backend,
            )
            members.append(
                PackageMember(
                    path=candidate.package_path,
                    content=path.read_bytes(),
                    member_type="artifact",
                    source={
                        "object_type": candidate.object_type,
                        "object_id": str(candidate.object_id),
                        "artifact_id": str(candidate.artifact_id),
                        "source_version": candidate.source_version,
                    },
                    license_status=candidate.license_status,
                    sensitive=candidate.sensitive,
                    redistribution=candidate.redistribution,
                )
            )
    implementation = implementation_metadata(candidates)
    combined_limitations = sorted(set(limitations + implementation["limitations"]))
    metadata_only_count = sum(
        item.include_status == ExportItemIncludeStatus.METADATA_ONLY
        for item in candidates
    )
    excluded_count = sum(
        item.include_status == ExportItemIncludeStatus.EXCLUDED for item in candidates
    )
    readme = build_readme(
        members=members,
        limitations=combined_limitations,
        metadata_only_count=metadata_only_count,
        excluded_count=excluded_count,
    )
    members.append(
        PackageMember(
            path="README_REPRODUCE.md",
            content=readme,
            member_type="documentation",
            source={"generator": "reca-m7-packager"},
        )
    )
    implementation["limitations"] = combined_limitations
    manifest, manifest_bytes = build_manifest(members, implementation=implementation)
    manifest_member = PackageMember(
        path="manifest.json",
        content=manifest_bytes,
        member_type="manifest",
        source={"schema": MANIFEST_SCHEMA_VERSION},
    )
    all_members = members + [manifest_member]
    entries = {member.path: member.content for member in all_members}
    zip_bytes = build_deterministic_zip(entries)
    verify_zip(zip_bytes, entries)
    uploaded: list[Artifact] = []
    backend = storage_backend or artifact_service.storage
    try:
        manifest_artifact = artifact_service.create_generated_bytes_artifact(
            session,
            project_id=export.project_id,
            content=manifest_bytes,
            filename=f"reca-repro-manifest-v{export.id}.json",
            mime_type="application/json",
            artifact_type=ArtifactType.MANIFEST,
            metadata={
                "schema": MANIFEST_SCHEMA_VERSION,
                "export_id": str(export.id),
                "manifest": manifest,
            },
            created_by=actor.id,
            storage_backend=backend,
        )
        uploaded.append(manifest_artifact)
        package_artifact = artifact_service.create_generated_bytes_artifact(
            session,
            project_id=export.project_id,
            content=zip_bytes,
            filename=f"reca-repro-package-{export.id}.zip",
            mime_type="application/zip",
            artifact_type=ArtifactType.REPRO_PACKAGE,
            metadata={
                "schema": MANIFEST_SCHEMA_VERSION,
                "export_id": str(export.id),
                "manifest_artifact_id": str(manifest_artifact.id),
            },
            created_by=actor.id,
            storage_backend=backend,
        )
        uploaded.append(package_artifact)
        with tempfile.TemporaryDirectory(
            prefix="reca-repro-upload-verify-"
        ) as directory:
            verify_root = Path(directory)
            artifact_service.download_available_artifact_to_path(
                session,
                artifact_id=manifest_artifact.id,
                project_id=export.project_id,
                path=verify_root / "manifest.json",
                storage_backend=backend,
            )
            artifact_service.download_available_artifact_to_path(
                session,
                artifact_id=package_artifact.id,
                project_id=export.project_id,
                path=verify_root / "package.zip",
                storage_backend=backend,
            )
    except Exception:
        for artifact in reversed(uploaded):
            try:
                backend.delete_object(object_key=artifact.storage_key)
            except StorageError:
                artifact.status = ArtifactStatus.QUARANTINED
                session.add(artifact)
            else:
                session.delete(artifact)
        export.status = ExportStatus.FAILED
        export.error_code = "EXPORT_PACKAGE_FINALIZE_FAILED"
        export.completed_at = get_datetime_utc()
        export.lock_version += 1
        session.add(export)
        raise
    package_version = (
        int(
            session.exec(
                select(func.coalesce(func.max(ReproPackage.package_version), 0)).where(
                    ReproPackage.project_id == export.project_id
                )
            ).one()
        )
        + 1
    )
    package = ReproPackage(
        export_id=export.id,
        project_id=export.project_id,
        artifact_id=package_artifact.id,
        manifest_artifact_id=manifest_artifact.id,
        package_version=package_version,
        schema_version=MANIFEST_SCHEMA_VERSION,
        contains_sensitive_data=any(
            item.sensitive and item.include_status == ExportItemIncludeStatus.INCLUDED
            for item in candidates
        ),
        contains_restricted_data=any(
            item.include_status == ExportItemIncludeStatus.METADATA_ONLY
            for item in candidates
        ),
        file_count=len(entries),
        total_size_bytes=len(zip_bytes),
        sha256=package_artifact.sha256,
    )
    session.add(package)
    session.flush()
    for candidate in candidates:
        session.add(
            ExportItem(
                export_id=export.id,
                project_id=export.project_id,
                object_type=candidate.object_type,
                object_id=candidate.object_id,
                artifact_id=candidate.artifact_id,
                package_path=candidate.package_path,
                sha256=candidate.sha256,
                include_status=candidate.include_status,
                exclusion_reason=candidate.exclusion_reason,
                source_snapshot=jsonable_encoder(
                    {
                        "license_status": candidate.license_status,
                        "sensitive": candidate.sensitive,
                        "redistribution": candidate.redistribution,
                        "source_version": candidate.source_version,
                    }
                ),
            )
        )
    export.status = ExportStatus.COMPLETED
    export.completed_at = get_datetime_utc()
    export.error_code = None
    export.lock_version += 1
    session.add(export)
    project_service._add_audit(
        session,
        project_id=export.project_id,
        actor=actor,
        action="REPRO_PACKAGE_COMPLETED",
        object_type="repro_package",
        object_id=package.id,
        after={
            "export_id": str(export.id),
            "package_version": package.package_version,
            "sha256": package.sha256,
            "manifest_artifact_id": str(manifest_artifact.id),
        },
    )
    job_service.set_run_context(
        session,
        job_id=job.id,
        run_id=run_id,
        input_hash=str(export.scope.get("readiness_snapshot_hash")),
        parameters={"schema_version": MANIFEST_SCHEMA_VERSION},
        implementation_metadata={
            "engine": "reca-repro-packager",
            "engine_version": MANIFEST_SCHEMA_VERSION,
        },
    )
    session.flush()
    return package
