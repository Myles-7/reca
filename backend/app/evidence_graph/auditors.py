from __future__ import annotations

import uuid
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, col, select

from app.api.errors import ContractError
from app.jobs import service as job_service
from app.models import (
    AuditResult,
    AuditResultOutcome,
    AuditResultStatus,
    AuditType,
    Claim,
    ClaimEvidenceLink,
    ClaimStatus,
    EvidenceLinkStatus,
    EvidenceObjectType,
    Job,
    JobTaskType,
    ProjectMemberRole,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

from .resolvers import resolve_evidence
from .schemas import ClaimAuditCreate, ClaimAuditPublic

AUDIT_PATH = "/api/v1/claims/{claim_id}/audits"
RULE_SET_VERSION = "m7-claim-evidence-audit/1.0"


def _not_found() -> ContractError:
    return ContractError(
        status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
    )


def _role(access: project_service.ProjectAccess) -> ProjectMemberRole:
    return access.membership.role if access.membership else ProjectMemberRole.OWNER


def _audit_job_id(session: Session, audit: AuditResult) -> uuid.UUID | None:
    job = session.exec(
        select(Job)
        .where(
            Job.project_id == audit.project_id,
            Job.task_type == JobTaskType.EVIDENCE_AUDIT,
            Job.resource_type == "audit_result",
            Job.resource_id == audit.id,
        )
        .order_by(col(Job.created_at).desc())
    ).first()
    return job.id if job else None


def audit_data(session: Session, audit: AuditResult) -> ClaimAuditPublic:
    return ClaimAuditPublic(
        id=audit.id,
        project_id=audit.project_id,
        audit_type=audit.audit_type,
        target_object_type=audit.target_object_type,
        target_object_id=audit.target_object_id,
        job_id=_audit_job_id(session, audit),
        execution_status=audit.status,
        outcome=audit.outcome,
        source_snapshot_hash=audit.source_snapshot_hash,
        result_hash=audit.result_hash,
        findings=list(audit.findings),
        limitations=list(audit.limitations),
        degraded=audit.degraded,
        rule_set_version=audit.rule_set_version,
        allowed_actions=["audit.read"],
    )


def get_audit(
    session: Session, *, actor: User, audit_id: uuid.UUID
) -> ClaimAuditPublic:
    audit = session.get(AuditResult, audit_id)
    if audit is None:
        raise _not_found()
    project_service.authorize_project(
        session,
        project_id=audit.project_id,
        actor=actor,
        action="audit.read",
    )
    return audit_data(session, audit)


def request_claim_audit(
    session: Session,
    *,
    actor: User,
    claim_id: uuid.UUID,
    payload: ClaimAuditCreate,
    idempotency_key: str,
    dispatcher: job_service.JobDispatcher,
) -> project_service.OperationResult:
    claim = session.exec(
        select(Claim).where(Claim.id == claim_id).with_for_update()
    ).first()
    if claim is None:
        raise _not_found()
    project_service.authorize_project(
        session,
        project_id=claim.project_id,
        actor=actor,
        action="evidence.audit.run",
        for_update=True,
    )
    digest = project_service.request_hash(payload)
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=claim.project_id,
        method="POST",
        path_template=AUDIT_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay:
        return replay
    source_snapshot = {
        "claim_id": str(claim.id),
        "claim_lock_version": claim.lock_version,
        "claim_text_hash": claim.text_hash,
        "claim_source_hash": claim.source_hash,
    }
    audit = AuditResult(
        project_id=claim.project_id,
        audit_type=AuditType.CLAIM_COMPLETENESS_AUDIT,
        target_object_type="CLAIM",
        target_object_id=claim.id,
        status=AuditResultStatus.QUEUED,
        rule_set_version=RULE_SET_VERSION,
        source_snapshot=source_snapshot,
        source_snapshot_hash=project_service.request_hash(source_snapshot),
        idempotency_key=idempotency_key,
        request_snapshot=jsonable_encoder(payload),
        requested_by=actor.id,
    )
    session.add(audit)
    session.flush()
    job = job_service.create_job(
        session,
        project_id=claim.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.EVIDENCE_AUDIT,
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
            "audit_result": jsonable_encoder(audit_data(session, audit)),
            "job": job_service.job_data(session, job),
        },
        status_code=202,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=claim.project_id,
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
            "audit_result": jsonable_encoder(audit_data(session, audit)),
            "job": job_service.job_data(session, dispatched),
        },
        status_code=202,
    )
    project_service._update_idempotency_result(
        session,
        actor_id=actor.id,
        project_id=claim.project_id,
        method="POST",
        path_template=AUDIT_PATH,
        key=idempotency_key,
        result=result,
    )
    project_service._commit(session)
    return result


def _finding(
    code: str, severity: str, message: str, *, object_id: uuid.UUID | None = None
) -> dict[str, Any]:
    value: dict[str, Any] = {"code": code, "severity": severity, "message": message}
    if object_id is not None:
        value["object_id"] = str(object_id)
    return value


def execute_claim_audit_job(
    session: Session, *, job: Job, run_id: uuid.UUID
) -> AuditResult:
    audit = session.exec(
        select(AuditResult).where(AuditResult.id == job.resource_id).with_for_update()
    ).first()
    if (
        audit is None
        or audit.project_id != job.project_id
        or audit.audit_type != AuditType.CLAIM_COMPLETENESS_AUDIT
        or audit.target_object_type != "CLAIM"
        or audit.target_object_id is None
        or job.task_type != JobTaskType.EVIDENCE_AUDIT
        or job.resource_type != "audit_result"
    ):
        raise ContractError(
            status_code=409,
            code="INVALID_JOB_INPUT",
            message="Evidence audit Job input is invalid.",
        )
    if audit.status == AuditResultStatus.COMPLETED:
        return audit
    actor = session.get(User, job.requested_by_user_id)
    claim = session.get(Claim, audit.target_object_id)
    if actor is None or claim is None or claim.project_id != audit.project_id:
        raise ContractError(
            status_code=409,
            code="EVIDENCE_AUDIT_CONTEXT_INVALID",
            message="Evidence audit context is unavailable.",
        )
    project_service.authorize_project(
        session,
        project_id=audit.project_id,
        actor=actor,
        action="evidence.audit.run",
        for_update=True,
    )
    audit.status = AuditResultStatus.RUNNING
    audit.processing_run_id = run_id
    session.add(audit)
    links = session.exec(
        select(ClaimEvidenceLink).where(
            ClaimEvidenceLink.project_id == claim.project_id,
            ClaimEvidenceLink.claim_id == claim.id,
            ClaimEvidenceLink.status == EvidenceLinkStatus.ACTIVE,
        )
    ).all()
    findings: list[dict[str, Any]] = []
    evidence_ids: list[str] = []
    source_rows: list[dict[str, Any]] = []
    if not links:
        findings.append(
            _finding(
                "CLAIM_NO_ACTIVE_EVIDENCE",
                "HIGH",
                "Claim has no active evidence relationship.",
            )
        )
    for link in links:
        try:
            reference = resolve_evidence(
                session,
                project_id=claim.project_id,
                object_type=link.evidence_object_type,
                object_id=link.evidence_object_id,
            )
        except ContractError:
            findings.append(
                _finding(
                    "EVIDENCE_REFERENCE_UNAVAILABLE",
                    "HIGH",
                    "Linked evidence is unavailable in the authorized project scope.",
                    object_id=link.evidence_object_id,
                )
            )
            continue
        evidence_ids.append(str(reference.object_id))
        source_rows.append(
            {
                "type": reference.object_type,
                "id": str(reference.object_id),
                "hash": reference.source_hash,
                "status": reference.raw_status,
            }
        )
        if not reference.known_status:
            findings.append(
                _finding(
                    "EVIDENCE_STATUS_UNKNOWN",
                    "HIGH",
                    "Linked evidence has an unknown status.",
                    object_id=reference.object_id,
                )
            )
        if reference.invalidated or reference.stale:
            findings.append(
                _finding(
                    "INVALIDATED_OR_STALE_SOURCE",
                    "HIGH",
                    "Linked evidence is invalidated or stale.",
                    object_id=reference.object_id,
                )
            )
        if reference.source_hash != link.source_hash:
            findings.append(
                _finding(
                    "EVIDENCE_HASH_MISMATCH",
                    "HIGH",
                    "Linked evidence no longer matches the recorded source hash.",
                    object_id=reference.object_id,
                )
            )
        if reference.restricted:
            findings.append(
                _finding(
                    "EVIDENCE_SCOPE_RESTRICTED",
                    "MEDIUM",
                    "Evidence exists but the current read scope is restricted.",
                    object_id=reference.object_id,
                )
            )
    if claim.claim_type.value == "STATISTICAL_RESULT" and not any(
        link.evidence_object_type == EvidenceObjectType.ANALYSIS_RESULT
        for link in links
    ):
        findings.append(
            _finding(
                "ANALYSIS_RESULT_REQUIRED",
                "HIGH",
                "A statistical Claim requires an active AnalysisResult source.",
            )
        )
    if claim.status == ClaimStatus.CONFIRMED and claim.approval_record_id is None:
        findings.append(
            _finding(
                "CLAIM_CONFIRMATION_INCONSISTENT",
                "HIGH",
                "Confirmed Claim has no Approval snapshot.",
            )
        )
    high_codes = {item["code"] for item in findings if item["severity"] == "HIGH"}
    if "EVIDENCE_HASH_MISMATCH" in high_codes:
        outcome = AuditResultOutcome.DATA_MISMATCH
    elif "INVALIDATED_OR_STALE_SOURCE" in high_codes:
        outcome = AuditResultOutcome.INVALIDATED
    elif high_codes:
        outcome = AuditResultOutcome.INSUFFICIENT_EVIDENCE
    elif findings:
        outcome = AuditResultOutcome.NEEDS_REVIEW
    else:
        outcome = AuditResultOutcome.VERIFIED
    degraded = bool(audit.request_snapshot.get("request_ai_explanation"))
    limitations = (
        ["AI explanation provider was not invoked; deterministic audit completed."]
        if degraded
        else []
    )
    snapshot = {
        "claim_id": str(claim.id),
        "claim_lock_version": claim.lock_version,
        "claim_text_hash": claim.text_hash,
        "claim_source_hash": claim.source_hash,
        "evidence": sorted(
            source_rows, key=lambda item: (str(item["type"]), item["id"])
        ),
    }
    result = {
        "rule_set_version": RULE_SET_VERSION,
        "outcome": outcome,
        "findings": findings,
        "limitations": limitations,
        "degraded": degraded,
    }
    audit.source_snapshot = jsonable_encoder(snapshot)
    audit.source_snapshot_hash = project_service.request_hash(snapshot)
    audit.findings = findings
    audit.evidence_object_ids = sorted(evidence_ids)
    audit.limitations = limitations
    audit.degraded = degraded
    audit.outcome = outcome
    audit.result = jsonable_encoder(result)
    audit.result_hash = project_service.request_hash(result)
    audit.status = AuditResultStatus.COMPLETED
    audit.completed_at = get_datetime_utc()
    session.add(audit)
    job_service.set_run_context(
        session,
        job_id=job.id,
        run_id=run_id,
        input_hash=audit.source_snapshot_hash,
        parameters={"rule_set_version": RULE_SET_VERSION},
        implementation_metadata={
            "engine": "reca-deterministic-evidence-audit",
            "engine_version": RULE_SET_VERSION,
        },
    )
    session.flush()
    return audit


def mark_failed_audit_job(session: Session, *, job: Job, error_code: str) -> None:
    audit = session.get(AuditResult, job.resource_id)
    if audit and audit.status != AuditResultStatus.COMPLETED:
        audit.status = AuditResultStatus.FAILED
        audit.error_code = error_code
        audit.completed_at = get_datetime_utc()
        session.add(audit)


def mark_cancelled_audit_job(session: Session, *, job: Job) -> None:
    audit = session.get(AuditResult, job.resource_id)
    if audit and audit.status != AuditResultStatus.COMPLETED:
        audit.status = AuditResultStatus.CANCELLED
        audit.completed_at = get_datetime_utc()
        session.add(audit)
    project_service._commit(session)
