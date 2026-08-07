from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, col, select

from app.models import (
    ApprovalRecord,
    ApprovalStatus,
    Artifact,
    ArtifactStatus,
    CleaningPlan,
    DataQualityRun,
    DatasetVersion,
    ManuscriptIssue,
    ManuscriptIssueStatus,
    User,
)
from app.projects import service as project_service

from .schemas import ProjectContextSnapshot


def canonical_hash(value: Any) -> str:
    canonical = json.dumps(
        jsonable_encoder(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_project_context_snapshot(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
) -> ProjectContextSnapshot:
    access = project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="project.read"
    )
    if access.membership is None:
        raise ValueError("Project membership projection is required")
    project = access.project
    permissions = project_service.allowed_actions(access.membership.role)
    artifacts = session.exec(
        select(Artifact)
        .where(
            Artifact.project_id == project_id,
            Artifact.status == ArtifactStatus.AVAILABLE,
        )
        .order_by(col(Artifact.created_at), col(Artifact.id))
    ).all()
    dataset_versions = session.exec(
        select(DatasetVersion)
        .where(DatasetVersion.project_id == project_id)
        .order_by(col(DatasetVersion.created_at), col(DatasetVersion.id))
    ).all()
    cleaning_plans = session.exec(
        select(CleaningPlan)
        .where(CleaningPlan.project_id == project_id)
        .order_by(col(CleaningPlan.created_at), col(CleaningPlan.id))
    ).all()
    quality_runs = session.exec(
        select(DataQualityRun)
        .where(DataQualityRun.project_id == project_id)
        .order_by(col(DataQualityRun.created_at), col(DataQualityRun.id))
    ).all()
    approvals = session.exec(
        select(ApprovalRecord)
        .where(
            ApprovalRecord.project_id == project_id,
            ApprovalRecord.status == ApprovalStatus.PENDING,
        )
        .order_by(col(ApprovalRecord.created_at), col(ApprovalRecord.id))
    ).all()
    issues = session.exec(
        select(ManuscriptIssue)
        .where(
            ManuscriptIssue.project_id == project_id,
            col(ManuscriptIssue.status).in_(
                [ManuscriptIssueStatus.OPEN, ManuscriptIssueStatus.ACKNOWLEDGED]
            ),
        )
        .order_by(col(ManuscriptIssue.created_at), col(ManuscriptIssue.id))
    ).all()
    artifact_versions = {str(item.id): item.sha256 for item in artifacts}
    approval_versions = {
        str(item.id): f"{item.status.value}:{item.payload_hash}" for item in approvals
    }
    issue_versions = {str(item.id): item.status.value for item in issues}
    dataset_version_versions = {
        str(item.id): canonical_hash(
            {
                "status": item.status.value,
                "data_hash": item.data_hash,
                "schema_hash": item.schema_hash,
                "projection_hash": item.projection_hash,
            }
        )
        for item in dataset_versions
    }
    cleaning_plan_versions = {
        str(item.id): canonical_hash(
            {
                "status": item.status.value,
                "lock_version": item.lock_version,
                "dataset_version_id": item.dataset_version_id,
                "preview_hash": item.preview_hash,
                "payload_hash": item.payload_hash,
                "approval_record_id": item.approval_record_id,
            }
        )
        for item in cleaning_plans
    }
    quality_run_versions = {
        str(item.id): canonical_hash(
            {
                "status": item.status.value,
                "dataset_version_id": item.dataset_version_id,
                "ruleset_hash": item.ruleset_hash,
            }
        )
        for item in quality_runs
    }
    source_versions = {
        "project": f"{project.lock_version}:{project.updated_at.isoformat()}",
        "research_question": str(
            project.current_research_question_version_id or "missing"
        ),
        "artifacts": canonical_hash(artifact_versions),
        "approvals": canonical_hash(approval_versions),
        "blocking_issues": canonical_hash(issue_versions),
        "dataset_versions": canonical_hash(dataset_version_versions),
        "cleaning_plans": canonical_hash(cleaning_plan_versions),
        "data_quality_runs": canonical_hash(quality_run_versions),
    }
    resources: dict[str, list[str]] = {}
    for artifact in artifacts:
        resources.setdefault(artifact.artifact_type.value, []).append(str(artifact.id))
    resources["DatasetVersion"] = [str(item.id) for item in dataset_versions]
    resources["CleaningPlan"] = [str(item.id) for item in cleaning_plans]
    resources["DataQualityRun"] = [str(item.id) for item in quality_runs]
    blocking = [f"MANUSCRIPT_ISSUE:{item.id}" for item in issues]
    safe_summary = {
        "project_stage": project.current_stage.value,
        "artifact_count": len(artifacts),
        "pending_approval_count": len(approvals),
        "blocking_issue_count": len(blocking),
        "permission_count": len(permissions),
        "dataset_version_count": len(dataset_versions),
        "cleaning_plan_count": len(cleaning_plans),
        "data_quality_run_count": len(quality_runs),
    }
    revision = (
        project.lock_version
        + len(artifacts)
        + len(approvals)
        + len(issues)
        + len(dataset_versions)
        + len(cleaning_plans)
        + len(quality_runs)
    )
    hash_payload = {
        "schema_version": "1.0",
        "revision": revision,
        "project_id": project.id,
        "project_name": project.name,
        "project_stage": project.current_stage,
        "project_status": project.status.value,
        "source_object_versions": source_versions,
        "available_resources": resources,
        "pending_approval_ids": [item.id for item in approvals],
        "blocking_issues": blocking,
        "allowed_next_actions": permissions,
        "permissions": permissions,
        "read_scopes": ["PROJECT_METADATA", "AUTHORIZED_RESOURCE_IDS"],
        "degraded": False,
        "degradation_reason": None,
        "safe_snapshot_summary": safe_summary,
    }
    return ProjectContextSnapshot(
        schema_version="1.0",
        revision=revision,
        project_id=project.id,
        project_name=project.name,
        project_stage=project.current_stage,
        project_status=project.status.value,
        source_object_versions=source_versions,
        available_resources=resources,
        pending_approval_ids=[item.id for item in approvals],
        blocking_issues=blocking,
        allowed_next_actions=permissions,
        permissions=permissions,
        read_scopes=["PROJECT_METADATA", "AUTHORIZED_RESOURCE_IDS"],
        degraded=False,
        degradation_reason=None,
        generated_at=datetime.now(UTC),
        canonical_hash=canonical_hash(hash_payload),
        safe_snapshot_summary=safe_summary,
    )


def snapshot_is_current(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    expected_hash: str,
) -> tuple[bool, ProjectContextSnapshot]:
    rebuilt = build_project_context_snapshot(
        session, actor=actor, project_id=project_id
    )
    return rebuilt.canonical_hash == expected_hash, rebuilt
