from __future__ import annotations

import hashlib
import importlib.metadata
import os
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.api.errors import ContractError
from app.approvals import service as approval_service
from app.artifacts import service as artifact_service
from app.jobs import service as job_service
from app.manuscripts import service as manuscript_service
from app.manuscripts.fixers import (
    FIXER_VERSION,
    apply_fixes,
    canonical_actions,
    preview_fixes,
)
from app.manuscripts.parser import PARSER_VERSION, parse_docx
from app.manuscripts.revision import REVISION_RULE_SET_VERSION, compare_revisions
from app.manuscripts.schemas import (
    ClaimCreate,
    ClaimUpdate,
    FixPlanCreate,
    RevisionAuditCreate,
)
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
    AuditResult,
    AuditResultStatus,
    AuditType,
    Claim,
    ClaimStatus,
    EvidenceSpan,
    Figure,
    FigureStatus,
    Job,
    JobTaskType,
    LocationVerificationStatus,
    Manuscript,
    ManuscriptIssue,
    ManuscriptIssueStatus,
    ManuscriptTransformation,
    ManuscriptTransformationStatus,
    ManuscriptVersion,
    ManuscriptVersionStatus,
    ManuscriptVersionType,
    ProjectMemberRole,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

AUDIT_PATH = "/projects/{project_id}/manuscript-revision-audits"
FIX_PLAN_PATH = "/manuscript-versions/{version_id}/fix-plans"
FIX_APPROVAL_PATH = "/manuscript-fix-plans/{plan_id}/approval-requests"
FIX_EXECUTE_PATH = "/manuscript-fix-plans/{plan_id}/execute"
CLAIM_PATH = "/projects/{project_id}/claims"
CLAIM_APPROVAL_PATH = "/claims/{claim_id}/confirmation-requests"
TRANSFORMATION_TARGET = "manuscript_transformation"
CLAIM_TARGET = "claim"


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _normalized(value: str) -> str:
    return " ".join(value.split())


def _load_version(
    session: Session, version_id: uuid.UUID, project_id: uuid.UUID
) -> tuple[ManuscriptVersion, Artifact]:
    version = session.exec(
        select(ManuscriptVersion).where(
            ManuscriptVersion.id == version_id,
            ManuscriptVersion.project_id == project_id,
        )
    ).first()
    artifact = session.get(Artifact, version.artifact_id) if version else None
    if (
        version is None
        or artifact is None
        or version.status != ManuscriptVersionStatus.AVAILABLE
        or artifact.project_id != project_id
        or artifact.status != ArtifactStatus.AVAILABLE
        or artifact.artifact_type != ArtifactType.MANUSCRIPT_DOCX
        or artifact.sha256 != version.source_hash
    ):
        raise ContractError(
            status_code=409,
            code="VERSION_UNAVAILABLE",
            message="ManuscriptVersion input is unavailable or stale.",
        )
    return version, artifact


def _version_snapshot(
    session: Session, version: ManuscriptVersion, artifact: Artifact
) -> tuple[dict[str, Any], bytes]:
    path = manuscript_service._download_and_verify(session, version, artifact)
    try:
        content = path.read_bytes()
        return parse_docx(path), content
    finally:
        path.unlink(missing_ok=True)


def _role(access: project_service.ProjectAccess) -> ProjectMemberRole:
    return access.membership.role if access.membership else ProjectMemberRole.OWNER


def audit_data(
    session: Session, audit: AuditResult, role: ProjectMemberRole
) -> dict[str, Any]:
    job = session.exec(
        select(Job).where(
            Job.resource_type == "audit_result", Job.resource_id == audit.id
        )
    ).first()
    allowed = (
        ["manuscript_revision_audit.read"]
        if "manuscript.read" in project_service.ROLE_ACTIONS[role]
        else []
    )
    return manuscript_service._encoded(
        {
            **audit.model_dump(),
            "job_id": job.id if job else None,
            "allowed_actions": allowed,
        }
    )


def create_revision_audit(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    payload: RevisionAuditCreate,
    idempotency_key: str,
    dispatcher: job_service.JobDispatcher,
) -> project_service.OperationResult:
    access = project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="manuscript.audit",
        for_update=True,
    )
    digest = project_service.request_hash(payload.model_dump())
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=AUDIT_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    before, before_artifact = _load_version(
        session, payload.baseline_manuscript_version_id, project_id
    )
    after, after_artifact = _load_version(
        session, payload.candidate_manuscript_version_id, project_id
    )
    if before.id == after.id or before.manuscript_id != after.manuscript_id:
        raise ContractError(
            status_code=409,
            code="REVISION_AUDIT_INPUT_INVALID",
            message="Revision audit versions must be distinct versions of the same Manuscript.",
        )
    result_snapshots: list[dict[str, Any]] = []
    for result_id in dict.fromkeys(payload.referenced_result_ids):
        row = session.exec(
            select(AnalysisResult, AnalysisRun)
            .join(
                AnalysisRun, col(AnalysisRun.id) == col(AnalysisResult.analysis_run_id)
            )
            .where(
                AnalysisResult.id == result_id, AnalysisResult.project_id == project_id
            )
        ).first()
        if (
            row is None
            or row[1].status != AnalysisRunStatus.COMPLETED
            or row[1].invalidated_at is not None
        ):
            raise ContractError(
                status_code=409,
                code="REVISION_AUDIT_SOURCE_INVALID",
                message="A referenced AnalysisResult is missing, stale, or unavailable.",
            )
        result_snapshots.append(
            {
                "analysis_result_id": str(row[0].id),
                "analysis_run_id": str(row[1].id),
                "result_hash": row[0].result_hash,
            }
        )
    audit = AuditResult(
        project_id=project_id,
        audit_type=AuditType.REVISION_DRIFT_AUDIT,
        before_version_id=before.id,
        after_version_id=after.id,
        manuscript_id=before.manuscript_id,
        status=AuditResultStatus.QUEUED,
        rule_set_version=REVISION_RULE_SET_VERSION,
        before_source_hash=before_artifact.sha256,
        after_source_hash=after_artifact.sha256,
        idempotency_key=idempotency_key,
        request_snapshot={"referenced_results": result_snapshots},
        requested_by=actor.id,
    )
    session.add(audit)
    session.flush()
    job = job_service.create_job(
        session,
        project_id=project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.MANUSCRIPT_REVISION_AUDIT,
            resource_type="audit_result",
            resource_id=audit.id,
            idempotency_key=idempotency_key,
            requested_by_user_id=actor.id,
            max_retries=2,
            retryable=True,
        ),
    )
    initial = project_service.OperationResult(
        data={
            "audit_result": audit_data(session, audit, _role(access)),
            "job": job_service.job_data(session, job),
        },
        status_code=202,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=AUDIT_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=initial,
    )
    project_service._commit(session)
    dispatched = job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)
    result = project_service.OperationResult(
        data={
            "audit_result": audit_data(session, audit, _role(access)),
            "job": job_service.job_data(session, dispatched),
        },
        status_code=202,
    )
    project_service._update_idempotency_result(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=AUDIT_PATH,
        key=idempotency_key,
        result=result,
    )
    project_service._commit(session)
    return result


def get_revision_audit(
    session: Session, *, actor: User, audit_id: uuid.UUID
) -> dict[str, Any]:
    audit = session.get(AuditResult, audit_id)
    if audit is None:
        raise manuscript_service._not_found()
    access = project_service.authorize_project(
        session, project_id=audit.project_id, actor=actor, action="manuscript.read"
    )
    return audit_data(session, audit, _role(access))


def execute_revision_audit_job(
    session: Session, *, job: Job, run_id: uuid.UUID
) -> AuditResult:
    audit = session.exec(
        select(AuditResult).where(AuditResult.id == job.resource_id).with_for_update()
    ).first()
    if (
        audit is None
        or audit.project_id != job.project_id
        or job.task_type != JobTaskType.MANUSCRIPT_REVISION_AUDIT
        or job.resource_type != "audit_result"
    ):
        raise ContractError(
            status_code=409,
            code="INVALID_JOB_INPUT",
            message="Revision audit Job input is invalid.",
        )
    if audit.status == AuditResultStatus.COMPLETED:
        return audit
    actor = session.get(User, job.requested_by_user_id)
    if actor is None:
        raise ContractError(
            status_code=409,
            code="REVISION_AUDIT_ACTOR_INVALID",
            message="Revision audit actor is unavailable.",
        )
    project_service.authorize_project(
        session,
        project_id=audit.project_id,
        actor=actor,
        action="manuscript.audit",
        for_update=True,
    )
    before, before_artifact = _load_version(
        session, audit.before_version_id, audit.project_id
    )
    after, after_artifact = _load_version(
        session, audit.after_version_id, audit.project_id
    )
    if (
        before.manuscript_id != audit.manuscript_id
        or after.manuscript_id != audit.manuscript_id
        or before_artifact.sha256 != audit.before_source_hash
        or after_artifact.sha256 != audit.after_source_hash
    ):
        raise ContractError(
            status_code=409,
            code="FILE_HASH_MISMATCH",
            message="Revision audit source snapshot is stale.",
        )
    for source in audit.request_snapshot.get("referenced_results", []):
        referenced_result = session.get(
            AnalysisResult, uuid.UUID(str(source["analysis_result_id"]))
        )
        run = (
            session.get(AnalysisRun, referenced_result.analysis_run_id)
            if referenced_result
            else None
        )
        if (
            referenced_result is None
            or run is None
            or referenced_result.project_id != audit.project_id
            or run.status != AnalysisRunStatus.COMPLETED
            or run.invalidated_at is not None
            or referenced_result.result_hash != source.get("result_hash")
        ):
            raise ContractError(
                status_code=409,
                code="REVISION_AUDIT_SOURCE_INVALID",
                message="A referenced scientific result changed before execution.",
            )
    audit.status = AuditResultStatus.RUNNING
    audit.processing_run_id = run_id
    session.add(audit)
    session.flush()
    before_snapshot, _ = _version_snapshot(session, before, before_artifact)
    after_snapshot, _ = _version_snapshot(session, after, after_artifact)
    findings = compare_revisions(before_snapshot, after_snapshot)
    after_paragraphs = {
        int(item["index"]): str(item.get("text", ""))
        for item in after_snapshot.get("paragraphs", [])
    }
    stale_claim_ids: list[str] = []
    claims = session.exec(
        select(Claim).where(
            Claim.project_id == audit.project_id,
            Claim.source_object_type == "manuscript_version",
            Claim.source_object_id == before.id,
            Claim.status != ClaimStatus.INVALIDATED,
        )
    ).all()
    for claim in claims:
        paragraph = claim.source_location.get(
            "paragraph_index", claim.source_location.get("paragraph")
        )
        current = (
            after_paragraphs.get(paragraph) if isinstance(paragraph, int) else None
        )
        if current is None or _hash_bytes(current.encode("utf-8")) != claim.source_hash:
            stale_claim_ids.append(str(claim.id))
            findings.append(
                {
                    "code": "CLAIM_STALE_AFTER_REVISION",
                    "claim_id": str(claim.id),
                    "paragraph": paragraph,
                    "finding_hash": project_service.request_hash(
                        {
                            "code": "CLAIM_STALE_AFTER_REVISION",
                            "claim_id": str(claim.id),
                            "after_version_id": str(after.id),
                        }
                    ),
                }
            )
    audit_payload: dict[str, Any] = {
        "schema": "reca.manuscript.revision-audit.v1",
        "target": {
            "manuscript_id": str(audit.manuscript_id),
            "before_version_id": str(before.id),
            "after_version_id": str(after.id),
        },
        "rule_set_version": REVISION_RULE_SET_VERSION,
        "findings": findings,
        "evidence_ids": [
            item["analysis_result_id"]
            for item in audit.request_snapshot.get("referenced_results", [])
        ]
        + stale_claim_ids,
        "limitations": ["Complex semantic qualifier drift was not model-assisted."],
        "implementation_metadata": {
            "engine": "reca-deterministic-revision-audit",
            "engine_version": REVISION_RULE_SET_VERSION,
            "parser_version": PARSER_VERSION,
        },
        "source_hashes": {
            "before": audit.before_source_hash,
            "after": audit.after_source_hash,
        },
    }
    audit.result = audit_payload
    audit.result_hash = project_service.request_hash(audit_payload)
    audit.status = AuditResultStatus.COMPLETED
    audit.completed_at = get_datetime_utc()
    session.add(audit)
    job_service.set_run_context(
        session,
        job_id=job.id,
        run_id=run_id,
        input_hash=project_service.request_hash(audit_payload["source_hashes"]),
        parameters={"rule_set_version": REVISION_RULE_SET_VERSION},
        implementation_metadata=audit_payload["implementation_metadata"],
    )
    session.flush()
    return audit


def _transformation_payload(transformation: ManuscriptTransformation) -> dict[str, Any]:
    return {
        "transformation_id": str(transformation.id),
        "input_version_id": str(transformation.manuscript_version_id),
        "input_artifact_hash": transformation.input_artifact_hash,
        "issue_ids": transformation.approved_issue_ids,
        "actions": transformation.plan_payload.get("actions", []),
        "fixer_version": FIXER_VERSION,
        "preview_hash": transformation.preview_hash,
        "output_policy": {
            "version_type": "AUTO_FIXED",
            "preserve_source": True,
            "update_current_pointer": True,
        },
    }


def transformation_data(
    session: Session, transformation: ManuscriptTransformation, role: ProjectMemberRole
) -> dict[str, Any]:
    job = session.exec(
        select(Job).where(
            Job.resource_type == "manuscript_transformation",
            Job.resource_id == transformation.id,
        )
    ).first()
    permissions = project_service.ROLE_ACTIONS[role]
    actions = ["manuscript_fix_plan.read"] if "manuscript.read" in permissions else []
    if (
        transformation.status == ManuscriptTransformationStatus.DRAFT
        and "manuscript.fix" in permissions
    ):
        actions.extend(
            ["manuscript_fix_plan.preview", "manuscript_fix_plan.request_approval"]
        )
    if (
        transformation.status == ManuscriptTransformationStatus.APPROVED
        and "manuscript.fix" in permissions
    ):
        actions.append("manuscript_fix_plan.execute")
    return manuscript_service._encoded(
        {
            **transformation.model_dump(),
            "job_id": job.id if job else None,
            "allowed_actions": actions,
        }
    )


def create_fix_plan(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    payload: FixPlanCreate,
    idempotency_key: str,
) -> project_service.OperationResult:
    candidate = session.get(ManuscriptVersion, version_id)
    if candidate is None:
        raise manuscript_service._not_found()
    version, artifact = _load_version(session, version_id, candidate.project_id)
    access = project_service.authorize_project(
        session,
        project_id=version.project_id,
        actor=actor,
        action="manuscript.fix",
        for_update=True,
    )
    digest = project_service.request_hash(payload.model_dump())
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        method="POST",
        path_template=FIX_PLAN_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    issues = list(
        session.exec(
            select(ManuscriptIssue).where(
                col(ManuscriptIssue.id).in_(payload.issue_ids)
            )
        ).all()
    )
    if len(issues) != len(set(payload.issue_ids)) or any(
        item.project_id != version.project_id
        or item.manuscript_version_id != version.id
        or item.status != ManuscriptIssueStatus.ACCEPTED
        or not item.auto_fixable
        or item.invalidated_at is not None
        for item in issues
    ):
        raise ContractError(
            status_code=409,
            code="MANUSCRIPT_FIX_NOT_ALLOWED",
            message="Every Issue must be an ACCEPTED allowlisted auto-fixable Issue from the input version.",
        )
    try:
        actions = canonical_actions(issues)
    except ValueError as error:
        raise ContractError(
            status_code=409, code="MANUSCRIPT_FIX_NOT_ALLOWED", message=str(error)
        ) from error
    plan_payload = {
        "schema": "reca.manuscript.fix-plan.v1",
        "actions": actions,
        "fixer_version": FIXER_VERSION,
    }
    transformation = ManuscriptTransformation(
        project_id=version.project_id,
        manuscript_version_id=version.id,
        approved_issue_ids=[
            str(item.id) for item in sorted(issues, key=lambda item: str(item.id))
        ],
        plan_payload=plan_payload,
        input_artifact_hash=artifact.sha256,
        payload_hash=project_service.request_hash(plan_payload),
        idempotency_key=idempotency_key,
        created_by=actor.id,
    )
    session.add(transformation)
    session.flush()
    result = project_service.OperationResult(
        data=transformation_data(session, transformation, _role(access)),
        status_code=201,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        method="POST",
        path_template=FIX_PLAN_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result


def get_fix_plan(
    session: Session, *, actor: User, plan_id: uuid.UUID
) -> dict[str, Any]:
    plan = session.get(ManuscriptTransformation, plan_id)
    if plan is None:
        raise manuscript_service._not_found()
    access = project_service.authorize_project(
        session, project_id=plan.project_id, actor=actor, action="manuscript.read"
    )
    return transformation_data(session, plan, _role(access))


def preview_fix_plan(
    session: Session, *, actor: User, plan_id: uuid.UUID, if_match: int
) -> dict[str, Any]:
    plan = session.exec(
        select(ManuscriptTransformation)
        .where(ManuscriptTransformation.id == plan_id)
        .with_for_update()
    ).first()
    if plan is None:
        raise manuscript_service._not_found()
    access = project_service.authorize_project(
        session,
        project_id=plan.project_id,
        actor=actor,
        action="manuscript.fix",
        for_update=True,
    )
    if plan.lock_version != if_match:
        raise ContractError(
            status_code=412,
            code="PRECONDITION_FAILED",
            message="The FixPlan has changed.",
        )
    if plan.status != ManuscriptTransformationStatus.DRAFT:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Only a DRAFT FixPlan can be previewed.",
        )
    version, artifact = _load_version(
        session, plan.manuscript_version_id, plan.project_id
    )
    if artifact.sha256 != plan.input_artifact_hash:
        raise ContractError(
            status_code=409,
            code="FILE_HASH_MISMATCH",
            message="FixPlan input Artifact changed.",
        )
    snapshot, content = _version_snapshot(session, version, artifact)
    blocked = list(snapshot["unsupported_features"])
    try:
        preview = preview_fixes(
            content,
            list(plan.plan_payload["actions"]),
            unsupported_features=blocked,
            unknown_parts=list(snapshot.get("unknown_parts", [])),
        )
    except ValueError as error:
        raise ContractError(
            status_code=409, code="MANUSCRIPT_FIX_NOT_ALLOWED", message=str(error)
        ) from error
    plan.preview = preview
    plan.preview_hash = project_service.request_hash(preview)
    plan.lock_version += 1
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    project_service._commit(session)
    return transformation_data(session, plan, _role(access))


def resolve_fix_approval_payload(
    session: Session, approval: ApprovalRecord
) -> dict[str, Any]:
    plan = session.get(ManuscriptTransformation, approval.target_object_id)
    if (
        plan is None
        or plan.project_id != approval.project_id
        or plan.approval_record_id != approval.id
    ):
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="FixPlan Approval target is stale.",
        )
    return _transformation_payload(plan)


def apply_fix_approval_decision(
    session: Session, approval: ApprovalRecord, decision: ApprovalStatus, _actor: User
) -> None:
    plan = session.exec(
        select(ManuscriptTransformation)
        .where(ManuscriptTransformation.id == approval.target_object_id)
        .with_for_update()
    ).one()
    if (
        plan.approval_record_id != approval.id
        or plan.status != ManuscriptTransformationStatus.NEEDS_APPROVAL
    ):
        raise ContractError(
            status_code=409, code="APPROVAL_STALE", message="FixPlan Approval is stale."
        )
    plan.status = (
        ManuscriptTransformationStatus.APPROVED
        if decision == ApprovalStatus.APPROVED
        else ManuscriptTransformationStatus.REJECTED
    )
    plan.lock_version += 1
    plan.updated_at = get_datetime_utc()
    session.add(plan)


def request_fix_approval(
    session: Session, *, actor: User, plan_id: uuid.UUID, idempotency_key: str
) -> project_service.OperationResult:
    plan = session.exec(
        select(ManuscriptTransformation)
        .where(ManuscriptTransformation.id == plan_id)
        .with_for_update()
    ).first()
    if plan is None:
        raise manuscript_service._not_found()
    project_service.authorize_project(
        session,
        project_id=plan.project_id,
        actor=actor,
        action="manuscript.fix",
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
        path_template=FIX_APPROVAL_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    if plan.status != ManuscriptTransformationStatus.DRAFT or plan.preview_hash is None:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="A current preview is required before Approval.",
        )
    snapshot = _transformation_payload(plan)
    approval = approval_service.create_approval(
        session,
        command=approval_service.ApprovalCreate(
            project_id=plan.project_id,
            approval_type=ApprovalType.MANUSCRIPT_FIX_APPROVAL,
            target_object_type=TRANSFORMATION_TARGET,
            target_object_id=plan.id,
            requested_by_actor_type=AuditActorType.USER,
            requested_by_actor_id=str(actor.id),
            payload_snapshot=snapshot,
            impact_summary={
                "issue_count": len(plan.approved_issue_ids),
                "output_policy": snapshot["output_policy"],
            },
            expires_at=get_datetime_utc() + timedelta(hours=24),
            items=tuple(
                approval_service.ApprovalItemCreate(
                    item_type="manuscript_issue", item_id=uuid.UUID(value)
                )
                for value in plan.approved_issue_ids
            ),
        ),
    )
    plan.approval_record_id = approval.id
    plan.payload_hash = approval.payload_hash
    plan.status = ManuscriptTransformationStatus.NEEDS_APPROVAL
    plan.lock_version += 1
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    result = project_service.OperationResult(
        data=manuscript_service._encoded(
            {
                "approval_id": approval.id,
                "plan_id": plan.id,
                "status": approval.status,
                "payload_hash": approval.payload_hash,
                "expires_at": approval.expires_at,
            }
        ),
        status_code=201,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=FIX_APPROVAL_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result


def _fresh_fix_approval(
    session: Session, plan: ManuscriptTransformation
) -> ApprovalRecord:
    approval = (
        session.exec(
            select(ApprovalRecord)
            .where(ApprovalRecord.id == plan.approval_record_id)
            .with_for_update()
        ).first()
        if plan.approval_record_id
        else None
    )
    if (
        approval is None
        or approval.project_id != plan.project_id
        or approval.approval_type != ApprovalType.MANUSCRIPT_FIX_APPROVAL
        or approval.target_object_type != TRANSFORMATION_TARGET
        or approval.target_object_id != plan.id
    ):
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="FixPlan Approval target is stale.",
        )
    if approval.expires_at is not None and approval.expires_at <= get_datetime_utc():
        raise ContractError(
            status_code=409,
            code="APPROVAL_EXPIRED",
            message="FixPlan Approval expired.",
        )
    if approval.status != ApprovalStatus.APPROVED:
        raise ContractError(
            status_code=409,
            code="MANUSCRIPT_FIX_NOT_APPROVED",
            message="FixPlan Approval is not APPROVED.",
        )
    if (
        approval.payload_hash != plan.payload_hash
        or project_service.request_hash(_transformation_payload(plan))
        != approval.payload_hash
    ):
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="FixPlan Approval payload is stale.",
        )
    return approval


def execute_fix_plan(
    session: Session,
    *,
    actor: User,
    plan_id: uuid.UUID,
    idempotency_key: str,
    dispatcher: job_service.JobDispatcher,
) -> project_service.OperationResult:
    plan = session.exec(
        select(ManuscriptTransformation)
        .where(ManuscriptTransformation.id == plan_id)
        .with_for_update()
    ).first()
    if plan is None:
        raise manuscript_service._not_found()
    access = project_service.authorize_project(
        session,
        project_id=plan.project_id,
        actor=actor,
        action="manuscript.fix",
        for_update=True,
    )
    digest = project_service.request_hash({"plan_id": str(plan.id)})
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=FIX_EXECUTE_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    if plan.status != ManuscriptTransformationStatus.APPROVED:
        raise ContractError(
            status_code=409,
            code="MANUSCRIPT_FIX_NOT_APPROVED",
            message="Only an APPROVED FixPlan can execute.",
        )
    _fresh_fix_approval(session, plan)
    job = job_service.create_job(
        session,
        project_id=plan.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.MANUSCRIPT_TRANSFORM,
            resource_type="manuscript_transformation",
            resource_id=plan.id,
            idempotency_key=idempotency_key,
            requested_by_user_id=actor.id,
            max_retries=2,
            retryable=True,
        ),
    )
    plan.status = ManuscriptTransformationStatus.QUEUED
    plan.idempotency_key = idempotency_key
    plan.lock_version += 1
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    initial = project_service.OperationResult(
        data={
            "transformation": transformation_data(session, plan, _role(access)),
            "job": job_service.job_data(session, job),
        },
        status_code=202,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=FIX_EXECUTE_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=initial,
    )
    project_service._commit(session)
    dispatched = job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)
    result = project_service.OperationResult(
        data={
            "transformation": transformation_data(session, plan, _role(access)),
            "job": job_service.job_data(session, dispatched),
        },
        status_code=202,
    )
    project_service._update_idempotency_result(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=FIX_EXECUTE_PATH,
        key=idempotency_key,
        result=result,
    )
    project_service._commit(session)
    return result


def execute_fix_job(
    session: Session, *, job: Job, run_id: uuid.UUID
) -> ManuscriptTransformation:
    plan = session.exec(
        select(ManuscriptTransformation)
        .where(ManuscriptTransformation.id == job.resource_id)
        .with_for_update()
    ).first()
    if (
        plan is None
        or plan.project_id != job.project_id
        or job.task_type != JobTaskType.MANUSCRIPT_TRANSFORM
        or job.resource_type != "manuscript_transformation"
    ):
        raise ContractError(
            status_code=409,
            code="INVALID_JOB_INPUT",
            message="Manuscript transformation Job input is invalid.",
        )
    if plan.status == ManuscriptTransformationStatus.COMPLETED:
        return plan
    actor = session.get(User, job.requested_by_user_id)
    if actor is None:
        raise ContractError(
            status_code=409,
            code="TRANSFORMATION_ACTOR_INVALID",
            message="Requesting actor is unavailable.",
        )
    project_service.authorize_project(
        session,
        project_id=plan.project_id,
        actor=actor,
        action="manuscript.fix",
        for_update=True,
    )
    _fresh_fix_approval(session, plan)
    version, artifact = _load_version(
        session, plan.manuscript_version_id, plan.project_id
    )
    manuscript = session.exec(
        select(Manuscript)
        .where(Manuscript.id == version.manuscript_id)
        .with_for_update()
    ).one()
    if (
        plan.status != ManuscriptTransformationStatus.QUEUED
        or manuscript.current_version_id != version.id
        or artifact.sha256 != plan.input_artifact_hash
    ):
        raise ContractError(
            status_code=409,
            code="MANUSCRIPT_VERSION_STALE",
            message="FixPlan input is no longer the current version.",
        )
    issues = list(
        session.exec(
            select(ManuscriptIssue)
            .where(
                col(ManuscriptIssue.id).in_(
                    [uuid.UUID(value) for value in plan.approved_issue_ids]
                )
            )
            .with_for_update()
        ).all()
    )
    if (
        len(issues) != len(plan.approved_issue_ids)
        or any(
            item.status != ManuscriptIssueStatus.ACCEPTED
            or item.manuscript_version_id != version.id
            or not item.auto_fixable
            for item in issues
        )
        or canonical_actions(issues) != plan.plan_payload.get("actions")
    ):
        raise ContractError(
            status_code=409,
            code="MANUSCRIPT_FIX_INPUT_STALE",
            message="FixPlan Issues are stale.",
        )
    snapshot, content = _version_snapshot(session, version, artifact)
    blocked = list(snapshot["unsupported_features"])
    try:
        output, changes = apply_fixes(
            content,
            list(plan.plan_payload["actions"]),
            unsupported_features=blocked,
            unknown_parts=list(snapshot.get("unknown_parts", [])),
        )
    except ValueError as error:
        raise ContractError(
            status_code=409, code="MANUSCRIPT_FIX_NOT_ALLOWED", message=str(error)
        ) from error
    descriptor, filename = tempfile.mkstemp(prefix="reca-fixed-", suffix=".docx")
    os.close(descriptor)
    output_path = Path(filename)
    output_path.write_bytes(output)
    try:
        output_snapshot = parse_docx(output_path)
    finally:
        output_path.unlink(missing_ok=True)
    output_hash = _hash_bytes(output)
    if plan.preview is None or output_hash != plan.preview.get("output_sha256"):
        raise ContractError(
            status_code=409,
            code="MANUSCRIPT_FIX_OUTPUT_DRIFT",
            message="Fix output no longer matches the approved preview.",
        )
    plan.status = ManuscriptTransformationStatus.RUNNING
    session.add(plan)
    session.flush()
    next_version = session.exec(
        select(func.max(ManuscriptVersion.version_number)).where(
            ManuscriptVersion.manuscript_id == manuscript.id
        )
    ).one()
    output_artifact = artifact_service.create_generated_bytes_artifact(
        session,
        project_id=plan.project_id,
        content=output,
        filename=f"manuscript-v{(next_version or 0) + 1}.docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        artifact_type=ArtifactType.MANUSCRIPT_DOCX,
        metadata={
            "manuscript_transformation_id": str(plan.id),
            "fixer_version": FIXER_VERSION,
            "input_hash": plan.input_artifact_hash,
        },
        source_artifact_id=artifact.id,
        created_by=actor.id,
    )
    target = ManuscriptVersion(
        manuscript_id=manuscript.id,
        project_id=plan.project_id,
        version_number=(next_version or 0) + 1,
        parent_version_id=version.id,
        artifact_id=output_artifact.id,
        version_type=ManuscriptVersionType.AUTO_FIXED,
        source_transformation_id=plan.id,
        status=ManuscriptVersionStatus.AVAILABLE,
        source_hash=output_hash,
        parse_snapshot={
            "schema": output_snapshot["schema"],
            "parser_version": output_snapshot["parser_version"],
            "unsupported_features": output_snapshot["unsupported_features"],
            "unknown_parts": output_snapshot["unknown_parts"],
            "confidence": output_snapshot["confidence"],
            "text_hash": output_snapshot["text_hash"],
        },
        created_by=actor.id,
    )
    session.add(target)
    session.flush()
    for issue in issues:
        issue.status = ManuscriptIssueStatus.RESOLVED
        issue.resolved_at = get_datetime_utc()
        issue.lock_version += 1
        session.add(issue)
    manuscript.current_version_id = target.id
    manuscript.lock_version += 1
    manuscript.updated_at = get_datetime_utc()
    plan.output_manuscript_version_id = target.id
    plan.status = ManuscriptTransformationStatus.COMPLETED
    plan.completed_at = get_datetime_utc()
    plan.updated_at = get_datetime_utc()
    plan.lock_version += 1
    session.add(manuscript)
    session.add(plan)
    job_service.set_run_context(
        session,
        job_id=job.id,
        run_id=run_id,
        input_hash=version.source_hash,
        parameters={
            "payload_hash": plan.payload_hash,
            "preview_hash": plan.preview_hash,
        },
        implementation_metadata={
            "engine": "reca-manuscript-fixer",
            "engine_version": FIXER_VERSION,
            "python_docx": importlib.metadata.version("python-docx"),
            "changes": len(changes),
        },
    )
    session.flush()
    return plan


def _source_snapshot(
    session: Session,
    *,
    project_id: uuid.UUID,
    source_type: str,
    source_id: uuid.UUID,
    location: dict[str, object],
    claim_text: str,
) -> tuple[str, dict[str, object]]:
    if source_type == "manuscript_version":
        version, artifact = _load_version(session, source_id, project_id)
        snapshot, _ = _version_snapshot(session, version, artifact)
        paragraph = location.get("paragraph_index", location.get("paragraph"))
        if not isinstance(paragraph, int):
            raise ContractError(
                status_code=422,
                code="SOURCE_LOCATOR_INVALID",
                message="Manuscript Claim requires paragraph_index.",
            )
        item = next(
            (row for row in snapshot["paragraphs"] if row["index"] == paragraph), None
        )
        if item is None or _normalized(claim_text) not in _normalized(
            str(item["text"])
        ):
            raise ContractError(
                status_code=409,
                code="CLAIM_SOURCE_STALE",
                message="Claim text is not locatable in the ManuscriptVersion.",
            )
        text = str(item["text"])
        return _hash_bytes(text.encode("utf-8")), {
            "schema": "reca.manuscript.locator.v1",
            "paragraph_index": paragraph,
            "text_hash": _hash_bytes(text.encode("utf-8")),
            "version_hash": version.source_hash,
        }
    if source_type == "analysis_result":
        result = session.get(AnalysisResult, source_id)
        run = session.get(AnalysisRun, result.analysis_run_id) if result else None
        if (
            result is None
            or run is None
            or result.project_id != project_id
            or run.status != AnalysisRunStatus.COMPLETED
            or run.invalidated_at is not None
        ):
            raise ContractError(
                status_code=409,
                code="CLAIM_SOURCE_STALE",
                message="AnalysisResult source is unavailable.",
            )
        return result.result_hash, {
            "schema": "reca.analysis-result.locator.v1",
            "result_key": result.result_key,
            **location,
        }
    if source_type == "figure":
        figure = session.get(Figure, source_id)
        if (
            figure is None
            or figure.project_id != project_id
            or figure.status in {FigureStatus.INVALIDATED, FigureStatus.ARCHIVED}
            or figure.invalidated_at is not None
        ):
            raise ContractError(
                status_code=409,
                code="CLAIM_SOURCE_STALE",
                message="Figure source is unavailable.",
            )
        return figure.figure_hash, {
            "schema": "reca.figure.locator.v1",
            "version_number": figure.version_number,
            **location,
        }
    if source_type == "evidence_span":
        span = session.get(EvidenceSpan, source_id)
        if (
            span is None
            or span.project_id != project_id
            or span.location_verification_status
            not in {
                LocationVerificationStatus.LOCATED,
                LocationVerificationStatus.VERIFIED,
            }
        ):
            raise ContractError(
                status_code=409,
                code="CLAIM_SOURCE_STALE",
                message="EvidenceSpan source is not location-verified.",
            )
        return span.source_text_hash, {
            "schema": "reca.evidence-span.locator.v1",
            "page_number": span.page_number,
            "char_start": span.char_start,
            "char_end": span.char_end,
            **location,
        }
    raise ContractError(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Unsupported Claim source type.",
    )


def claim_data(claim: Claim, role: ProjectMemberRole) -> dict[str, Any]:
    permissions = project_service.ROLE_ACTIONS[role]
    actions = ["claim.read"] if "claim.read" in permissions else []
    if (
        claim.status
        not in {ClaimStatus.CONFIRMED, ClaimStatus.REJECTED, ClaimStatus.INVALIDATED}
        and "claim.update" in permissions
    ):
        actions.append("claim.update")
    if (
        claim.status == ClaimStatus.SUPPORTED
        and "claim.request_confirmation" in permissions
    ):
        actions.append("claim.request_confirmation")
    return manuscript_service._encoded(
        {**claim.model_dump(), "allowed_actions": actions}
    )


def create_claim(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    payload: ClaimCreate,
    idempotency_key: str,
) -> project_service.OperationResult:
    access = project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="claim.create",
        for_update=True,
    )
    digest = project_service.request_hash(payload.model_dump())
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=CLAIM_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    if payload.status not in {ClaimStatus.DRAFT, ClaimStatus.NEEDS_EVIDENCE}:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Claims may only be created as DRAFT or NEEDS_EVIDENCE.",
        )
    source_hash, location = _source_snapshot(
        session,
        project_id=project_id,
        source_type=payload.source_object_type,
        source_id=payload.source_object_id,
        location=payload.source_location,
        claim_text=payload.claim_text,
    )
    claim = Claim(
        project_id=project_id,
        claim_type=payload.claim_type,
        claim_text=payload.claim_text,
        normalized_claim=payload.normalized_claim or _normalized(payload.claim_text),
        scope_statement=payload.scope_statement,
        source_object_type=payload.source_object_type,
        source_object_id=payload.source_object_id,
        source_location=location,
        source_hash=source_hash,
        text_hash=_hash_bytes(_normalized(payload.claim_text).encode("utf-8")),
        status=payload.status,
        confidence=payload.confidence,
        created_by_actor_type=AuditActorType.USER,
        created_by_actor_id=str(actor.id),
    )
    session.add(claim)
    session.flush()
    result = project_service.OperationResult(
        data=claim_data(claim, _role(access)), status_code=201
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=CLAIM_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result


def get_claim(session: Session, *, actor: User, claim_id: uuid.UUID) -> dict[str, Any]:
    claim = session.get(Claim, claim_id)
    if claim is None:
        raise manuscript_service._not_found()
    access = project_service.authorize_project(
        session, project_id=claim.project_id, actor=actor, action="claim.read"
    )
    return claim_data(claim, _role(access))


_CLAIM_TRANSITIONS = {
    ClaimStatus.DRAFT: {ClaimStatus.NEEDS_EVIDENCE, ClaimStatus.REJECTED},
    ClaimStatus.NEEDS_EVIDENCE: {
        ClaimStatus.SUPPORTED,
        ClaimStatus.CONFLICTED,
        ClaimStatus.INSUFFICIENT,
        ClaimStatus.REJECTED,
    },
    ClaimStatus.SUPPORTED: {
        ClaimStatus.NEEDS_EVIDENCE,
        ClaimStatus.CONFLICTED,
        ClaimStatus.INSUFFICIENT,
        ClaimStatus.REJECTED,
    },
    ClaimStatus.CONFLICTED: {
        ClaimStatus.NEEDS_EVIDENCE,
        ClaimStatus.SUPPORTED,
        ClaimStatus.INSUFFICIENT,
        ClaimStatus.REJECTED,
    },
    ClaimStatus.INSUFFICIENT: {
        ClaimStatus.NEEDS_EVIDENCE,
        ClaimStatus.SUPPORTED,
        ClaimStatus.CONFLICTED,
        ClaimStatus.REJECTED,
    },
}


def update_claim(
    session: Session,
    *,
    actor: User,
    claim_id: uuid.UUID,
    payload: ClaimUpdate,
    if_match: int,
) -> dict[str, Any]:
    claim = session.exec(
        select(Claim).where(Claim.id == claim_id).with_for_update()
    ).first()
    if claim is None:
        raise manuscript_service._not_found()
    access = project_service.authorize_project(
        session,
        project_id=claim.project_id,
        actor=actor,
        action="claim.update",
        for_update=True,
    )
    if claim.lock_version != if_match:
        raise ContractError(
            status_code=412,
            code="PRECONDITION_FAILED",
            message="The Claim has changed.",
        )
    if claim.status in {
        ClaimStatus.CONFIRMED,
        ClaimStatus.REJECTED,
        ClaimStatus.INVALIDATED,
    }:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Terminal Claim cannot be edited.",
        )
    values = payload.model_dump(exclude_unset=True)
    source_changed = any(
        key in values
        for key in {"source_object_type", "source_object_id", "source_location"}
    )
    content_changed = source_changed or any(
        key in values for key in {"claim_text", "normalized_claim", "scope_statement"}
    )
    source_type = str(values.get("source_object_type", claim.source_object_type))
    source_id = values.get("source_object_id", claim.source_object_id)
    location = values.get("source_location", claim.source_location)
    claim_text = str(values.get("claim_text", claim.claim_text))
    if content_changed:
        if not isinstance(source_id, uuid.UUID) or not isinstance(location, dict):
            raise ContractError(
                status_code=422,
                code="SOURCE_LOCATOR_INVALID",
                message="Claim source update is incomplete.",
            )
        claim.source_hash, claim.source_location = _source_snapshot(
            session,
            project_id=claim.project_id,
            source_type=source_type,
            source_id=source_id,
            location=location,
            claim_text=claim_text,
        )
        if source_changed:
            claim.source_object_type = source_type
            claim.source_object_id = source_id
    if "claim_text" in values:
        claim.claim_text = claim_text
        claim.text_hash = _hash_bytes(_normalized(claim_text).encode("utf-8"))
    if "normalized_claim" in values:
        claim.normalized_claim = values["normalized_claim"]
    elif "claim_text" in values:
        claim.normalized_claim = _normalized(claim_text)
    if "scope_statement" in values:
        claim.scope_statement = values["scope_statement"]
    requested_status = values.get("status")
    if requested_status == ClaimStatus.CONFIRMED:
        raise ContractError(
            status_code=409,
            code="APPROVAL_REQUIRED",
            message="Claim confirmation requires formal Approval.",
        )
    if (
        requested_status is not None
        and requested_status != claim.status
        and requested_status not in _CLAIM_TRANSITIONS.get(claim.status, set())
    ):
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Claim status transition is not allowed.",
        )
    claim.status = (
        ClaimStatus.NEEDS_EVIDENCE
        if content_changed
        else (requested_status or claim.status)
    )
    if "confidence" in values:
        claim.confidence = values["confidence"]
    if content_changed and claim.approval_record_id is not None:
        approval_service.supersede_approval(
            session,
            approval_id=claim.approval_record_id,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
            reason="Claim content or source changed.",
        )
        claim.approval_record_id = None
    claim.lock_version += 1
    claim.updated_at = get_datetime_utc()
    session.add(claim)
    project_service._commit(session)
    return claim_data(claim, _role(access))


def _claim_payload(claim: Claim) -> dict[str, Any]:
    return {
        "claim_id": str(claim.id),
        "claim_type": claim.claim_type,
        "claim_text": claim.claim_text,
        "normalized_claim": claim.normalized_claim,
        "scope_statement": claim.scope_statement,
        "source_object_type": claim.source_object_type,
        "source_object_id": str(claim.source_object_id),
        "source_location": claim.source_location,
        "source_hash": claim.source_hash,
        "text_hash": claim.text_hash,
        "status": claim.status,
        "confidence": claim.confidence,
    }


def resolve_claim_approval_payload(
    session: Session, approval: ApprovalRecord
) -> dict[str, Any]:
    claim = session.get(Claim, approval.target_object_id)
    if (
        claim is None
        or claim.project_id != approval.project_id
        or claim.approval_record_id != approval.id
    ):
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="Claim Approval target is stale.",
        )
    return _claim_payload(claim)


def apply_claim_approval_decision(
    session: Session, approval: ApprovalRecord, decision: ApprovalStatus, _actor: User
) -> None:
    claim = session.exec(
        select(Claim).where(Claim.id == approval.target_object_id).with_for_update()
    ).one()
    if claim.approval_record_id != approval.id or claim.status != ClaimStatus.SUPPORTED:
        raise ContractError(
            status_code=409,
            code="APPROVAL_STALE",
            message="Claim confirmation is stale.",
        )
    _source_snapshot(
        session,
        project_id=claim.project_id,
        source_type=claim.source_object_type,
        source_id=claim.source_object_id,
        location=claim.source_location,
        claim_text=claim.claim_text,
    )
    if decision == ApprovalStatus.APPROVED:
        claim.status = ClaimStatus.CONFIRMED
        claim.confirmed_at = get_datetime_utc()
    else:
        claim.status = ClaimStatus.REJECTED
    claim.lock_version += 1
    claim.updated_at = get_datetime_utc()
    session.add(claim)


def request_claim_confirmation(
    session: Session, *, actor: User, claim_id: uuid.UUID, idempotency_key: str
) -> project_service.OperationResult:
    claim = session.exec(
        select(Claim).where(Claim.id == claim_id).with_for_update()
    ).first()
    if claim is None:
        raise manuscript_service._not_found()
    project_service.authorize_project(
        session,
        project_id=claim.project_id,
        actor=actor,
        action="claim.request_confirmation",
        for_update=True,
    )
    digest = project_service.request_hash(
        {
            "claim_id": str(claim.id),
            "text_hash": claim.text_hash,
            "source_hash": claim.source_hash,
        }
    )
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=claim.project_id,
        method="POST",
        path_template=CLAIM_APPROVAL_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    if claim.status != ClaimStatus.SUPPORTED:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Only a SUPPORTED Claim can request confirmation.",
        )
    source_hash, _ = _source_snapshot(
        session,
        project_id=claim.project_id,
        source_type=claim.source_object_type,
        source_id=claim.source_object_id,
        location=claim.source_location,
        claim_text=claim.claim_text,
    )
    if source_hash != claim.source_hash:
        raise ContractError(
            status_code=409, code="CLAIM_SOURCE_STALE", message="Claim source changed."
        )
    approval = approval_service.create_approval(
        session,
        command=approval_service.ApprovalCreate(
            project_id=claim.project_id,
            approval_type=ApprovalType.CLAIM_CONFIRMATION,
            target_object_type=CLAIM_TARGET,
            target_object_id=claim.id,
            requested_by_actor_type=AuditActorType.USER,
            requested_by_actor_id=str(actor.id),
            payload_snapshot=_claim_payload(claim),
            impact_summary={
                "claim_type": claim.claim_type,
                "source_object_type": claim.source_object_type,
            },
            expires_at=get_datetime_utc() + timedelta(hours=24),
        ),
    )
    claim.approval_record_id = approval.id
    claim.updated_at = get_datetime_utc()
    session.add(claim)
    result = project_service.OperationResult(
        data=manuscript_service._encoded(
            {
                "approval_id": approval.id,
                "claim_id": claim.id,
                "status": approval.status,
                "payload_hash": approval.payload_hash,
                "expires_at": approval.expires_at,
            }
        ),
        status_code=201,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=claim.project_id,
        method="POST",
        path_template=CLAIM_APPROVAL_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result


def register_approval_handlers() -> None:
    approval_service.register_payload_resolver(
        TRANSFORMATION_TARGET, resolve_fix_approval_payload
    )
    approval_service.register_decision_handler(
        TRANSFORMATION_TARGET, apply_fix_approval_decision
    )
    approval_service.register_payload_resolver(
        CLAIM_TARGET, resolve_claim_approval_payload
    )
    approval_service.register_decision_handler(
        CLAIM_TARGET, apply_claim_approval_decision
    )


def mark_failed_stage2_job(session: Session, *, job: Job, error_code: str) -> None:
    if job.task_type == JobTaskType.MANUSCRIPT_REVISION_AUDIT:
        audit = session.get(AuditResult, job.resource_id)
        if audit and audit.status != AuditResultStatus.COMPLETED:
            audit.status = AuditResultStatus.FAILED
            audit.error_code = error_code
            audit.completed_at = get_datetime_utc()
            session.add(audit)
    elif job.task_type == JobTaskType.MANUSCRIPT_TRANSFORM:
        plan = session.get(ManuscriptTransformation, job.resource_id)
        if plan and plan.status != ManuscriptTransformationStatus.COMPLETED:
            plan.status = ManuscriptTransformationStatus.FAILED
            plan.error_code = error_code
            plan.completed_at = get_datetime_utc()
            plan.updated_at = get_datetime_utc()
            session.add(plan)


def mark_cancelled_stage2_job(session: Session, *, job: Job) -> None:
    if job.task_type == JobTaskType.MANUSCRIPT_REVISION_AUDIT:
        audit = session.get(AuditResult, job.resource_id)
        if audit and audit.status != AuditResultStatus.COMPLETED:
            audit.status = AuditResultStatus.CANCELLED
            audit.completed_at = get_datetime_utc()
            session.add(audit)
    elif job.task_type == JobTaskType.MANUSCRIPT_TRANSFORM:
        plan = session.get(ManuscriptTransformation, job.resource_id)
        if plan and plan.status != ManuscriptTransformationStatus.COMPLETED:
            plan.status = ManuscriptTransformationStatus.CANCELLED
            plan.completed_at = get_datetime_utc()
            plan.updated_at = get_datetime_utc()
            session.add(plan)
    project_service._commit(session)
