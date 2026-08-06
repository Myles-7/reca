from __future__ import annotations

import uuid

from fastapi.encoders import jsonable_encoder
from sqlmodel import Session

from app.models import (
    AuditResult,
    AuditResultOutcome,
    AuditResultStatus,
    AuditType,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

from .collector import enumerate_candidates
from .schemas import ExportReadiness, ExportReadinessRequest, ReadinessIssue

RULE_SET_VERSION = "m7-export-readiness/1.0"


def run_readiness(
    session: Session,
    *,
    project_id: uuid.UUID,
    actor: User,
    request: ExportReadinessRequest,
    idempotency_key: str,
) -> ExportReadiness:
    project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="export.readiness",
    )
    candidates, blocking, warnings, limitations = enumerate_candidates(
        session, project_id=project_id, request=request
    )
    encoded_candidates = jsonable_encoder(candidates)
    encoded_blocking = jsonable_encoder(blocking)
    encoded_warnings = jsonable_encoder(warnings)
    encoded_limitations = jsonable_encoder(limitations)
    requires_confirmation = any(
        item["code"]
        in {
            "SENSITIVE_DATA_CONFIRMATION_REQUIRED",
            "CLAIM_UNCONFIRMED",
            "AUDIT_DEGRADED",
        }
        for item in warnings
    )
    snapshot = {
        "schema": "reca.export-readiness-snapshot.v1",
        "project_id": str(project_id),
        "scope": jsonable_encoder(request),
        "candidate_items": encoded_candidates,
        "blocking_issues": encoded_blocking,
        "warnings": encoded_warnings,
        "limitations": encoded_limitations,
        "rule_set_version": RULE_SET_VERSION,
    }
    snapshot_hash = project_service.request_hash(snapshot)
    audit = AuditResult(
        project_id=project_id,
        audit_type=AuditType.EXPORT_READINESS_AUDIT,
        target_object_type="RESEARCH_PROJECT",
        target_object_id=project_id,
        status=AuditResultStatus.COMPLETED,
        outcome=(
            AuditResultOutcome.INSUFFICIENT_EVIDENCE
            if blocking
            else (
                AuditResultOutcome.NEEDS_REVIEW
                if requires_confirmation or warnings
                else AuditResultOutcome.VERIFIED
            )
        ),
        rule_set_version=RULE_SET_VERSION,
        source_snapshot=snapshot,
        source_snapshot_hash=snapshot_hash,
        idempotency_key=idempotency_key,
        request_snapshot=jsonable_encoder(request),
        result={
            "ready": not blocking,
            "requires_confirmation": requires_confirmation,
            "blocking_issues": encoded_blocking,
            "warnings": encoded_warnings,
        },
        findings=encoded_blocking + encoded_warnings,
        evidence_object_ids=[
            str(item.object_id) for item in candidates if item.object_id is not None
        ],
        limitations=encoded_limitations,
        degraded=any(item["code"] == "AUDIT_DEGRADED" for item in warnings),
        requested_by=actor.id,
        completed_at=get_datetime_utc(),
    )
    audit.result_hash = project_service.request_hash(audit.result)
    session.add(audit)
    session.flush()
    return ExportReadiness(
        audit_id=audit.id,
        ready=not blocking,
        blocking_issues=[ReadinessIssue.model_validate(item) for item in blocking],
        warnings=[ReadinessIssue.model_validate(item) for item in warnings],
        requires_confirmation=requires_confirmation,
        candidate_items=candidates,
        limitations=limitations,
        snapshot=snapshot,
        snapshot_hash=snapshot_hash,
        rule_set_version=RULE_SET_VERSION,
    )
