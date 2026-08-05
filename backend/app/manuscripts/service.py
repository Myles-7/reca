from __future__ import annotations

import hashlib
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, col, select

from app.api.errors import ContractError
from app.artifacts import service as artifact_service
from app.artifacts.validation import policy_for, verify_file_content
from app.jobs import service as job_service
from app.manuscripts.parser import PARSER_VERSION, parse_docx
from app.manuscripts.rules import RULE_SET_VERSION, Finding, run_rules
from app.manuscripts.schemas import CheckRunCreate, ManuscriptCreate
from app.models import (
    AnalysisResult,
    AnalysisRun,
    AnalysisRunStatus,
    Artifact,
    ArtifactStatus,
    ArtifactType,
    Job,
    JobTaskType,
    Manuscript,
    ManuscriptCheckRun,
    ManuscriptCheckRunStatus,
    ManuscriptEvidenceType,
    ManuscriptIssue,
    ManuscriptIssueEvidence,
    ManuscriptIssueSeverity,
    ManuscriptIssueStatus,
    ManuscriptIssueType,
    ManuscriptStatus,
    ManuscriptVersion,
    ManuscriptVersionStatus,
    ManuscriptVersionType,
    ProjectMemberRole,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service


def _encoded(value: Any) -> dict[str, Any]:
    return cast(dict[str, Any], jsonable_encoder(value))


def _role(access: project_service.ProjectAccess) -> ProjectMemberRole:
    return access.membership.role if access.membership else ProjectMemberRole.OWNER


_STATISTIC_RE = re.compile(
    r"\b(?P<label>p|r|beta|β)\s*(?:=|:|is)\s*(?P<value>-?(?:\d+(?:\.\d+)?|\.\d+))",
    re.IGNORECASE,
)


def _formal_numeric_metrics(payload: dict[str, Any]) -> dict[str, float | None]:
    """Read explicit M5 result fields without recalculating scientific facts."""
    metrics: dict[str, float | None] = {}
    aliases = {
        "p": ("p_value", "p"),
        "r": ("coefficient", "r", "correlation"),
        "beta": ("beta", "standardized_beta", "effect_size"),
        "n": ("n", "effective_n", "sample_size"),
    }

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for metric, keys in aliases.items():
                for key in keys:
                    candidate = value.get(key)
                    if isinstance(candidate, (int, float)) and not isinstance(
                        candidate, bool
                    ):
                        metrics.setdefault(metric, float(candidate))
                    elif candidate is None and key in value:
                        metrics.setdefault(metric, None)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return metrics


def _metric_matches(observed: float, expected: float | None) -> bool | None:
    if expected is None:
        return None
    return abs(observed - expected) <= max(1e-6, abs(expected) * 1e-3)


def _not_found() -> ContractError:
    return ContractError(
        status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
    )


def _download_and_verify(
    session: Session, version: ManuscriptVersion, artifact: Artifact
) -> Path:
    descriptor, filename = tempfile.mkstemp(prefix="reca-manuscript-", suffix=".docx")
    os.close(descriptor)
    path = Path(filename)
    artifact_service.download_available_artifact_to_path(
        session, artifact_id=artifact.id, project_id=version.project_id, path=path
    )
    _, policy = policy_for(
        artifact_type=artifact.artifact_type,
        filename=artifact.filename,
        declared_mime=artifact.mime_type,
    )
    verify_file_content(path, policy=policy)
    if hashlib.sha256(path.read_bytes()).hexdigest() != version.source_hash:
        raise ContractError(
            status_code=409,
            code="FILE_HASH_MISMATCH",
            message="ManuscriptVersion source hash no longer matches its Artifact.",
        )
    return path


def create_manuscript(
    session: Session, *, actor: User, project_id: uuid.UUID, payload: ManuscriptCreate
) -> dict[str, Any]:
    access = project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="manuscript.upload",
        for_update=True,
    )
    artifact = session.exec(
        select(Artifact)
        .where(Artifact.id == payload.artifact_id, Artifact.project_id == project_id)
        .with_for_update()
    ).first()
    if artifact is None:
        raise _not_found()
    if (
        artifact.artifact_type != ArtifactType.MANUSCRIPT_DOCX
        or artifact.status != ArtifactStatus.AVAILABLE
        or not artifact.is_original
        or not artifact.is_immutable
    ):
        raise ContractError(
            status_code=409,
            code="VERSION_UNAVAILABLE",
            message="A finalized immutable original MANUSCRIPT_DOCX Artifact is required.",
        )
    existing = session.exec(
        select(ManuscriptVersion).where(ManuscriptVersion.artifact_id == artifact.id)
    ).first()
    if existing is not None:
        raise ContractError(
            status_code=409,
            code="RESOURCE_CONFLICT",
            message="Artifact is already attached to a ManuscriptVersion.",
        )
    probe_version = ManuscriptVersion(
        manuscript_id=uuid.uuid4(),
        project_id=project_id,
        version_number=1,
        artifact_id=artifact.id,
        version_type=ManuscriptVersionType.ORIGINAL,
        source_hash=artifact.sha256,
    )
    path = _download_and_verify(session, probe_version, artifact)
    try:
        snapshot = parse_docx(path)
    finally:
        path.unlink(missing_ok=True)
    manuscript = Manuscript(
        project_id=project_id,
        title=payload.title or artifact.filename,
        created_by=actor.id,
    )
    session.add(manuscript)
    session.flush()
    version = ManuscriptVersion(
        manuscript_id=manuscript.id,
        project_id=project_id,
        version_number=1,
        artifact_id=artifact.id,
        version_type=ManuscriptVersionType.ORIGINAL,
        status=ManuscriptVersionStatus.AVAILABLE,
        source_hash=artifact.sha256,
        parse_snapshot={
            "schema": snapshot["schema"],
            "parser_version": snapshot["parser_version"],
            "unsupported_features": snapshot["unsupported_features"],
            "unknown_parts": snapshot["unknown_parts"],
            "confidence": snapshot["confidence"],
            "text_hash": snapshot["text_hash"],
        },
        created_by=actor.id,
    )
    session.add(version)
    session.flush()
    manuscript.current_version_id = version.id
    manuscript.updated_at = get_datetime_utc()
    session.add(manuscript)
    project_service._add_audit(
        session,
        project_id=project_id,
        actor=actor,
        action="MANUSCRIPT_CREATED",
        object_type="manuscript",
        object_id=manuscript.id,
        after=_encoded(
            {
                "version_id": version.id,
                "artifact_id": artifact.id,
                "source_hash": artifact.sha256,
            }
        ),
    )
    project_service._commit(session)
    return {
        "manuscript": manuscript_data(manuscript, _role(access)),
        "version": version_data(version, _role(access)),
    }


def manuscript_data(value: Manuscript, role: ProjectMemberRole) -> dict[str, Any]:
    actions = project_service.ROLE_ACTIONS[role]
    return _encoded(
        {
            "id": value.id,
            "project_id": value.project_id,
            "title": value.title,
            "current_version_id": value.current_version_id,
            "status": value.status,
            "lock_version": value.lock_version,
            "created_by": value.created_by,
            "created_at": value.created_at,
            "updated_at": value.updated_at,
            "invalidated_at": value.invalidated_at,
            "invalidation_reason": value.invalidation_reason,
            "allowed_actions": sorted(
                action
                for action in ("manuscript.read", "manuscript.upload")
                if action in actions
            ),
        }
    )


def version_data(value: ManuscriptVersion, role: ProjectMemberRole) -> dict[str, Any]:
    actions = project_service.ROLE_ACTIONS[role]
    allowed = []
    if "manuscript.read" in actions:
        allowed.append("manuscript_version.read")
    if (
        value.status == ManuscriptVersionStatus.AVAILABLE
        and "manuscript.check" in actions
    ):
        allowed.append("manuscript_version.check")
    if (
        value.status == ManuscriptVersionStatus.AVAILABLE
        and "artifact.download" in actions
    ):
        allowed.append("manuscript_version.download")
    return _encoded(
        {
            "id": value.id,
            "manuscript_id": value.manuscript_id,
            "project_id": value.project_id,
            "version_number": value.version_number,
            "parent_version_id": value.parent_version_id,
            "artifact_id": value.artifact_id,
            "version_type": value.version_type,
            "source_transformation_id": value.source_transformation_id,
            "status": value.status,
            "source_hash": value.source_hash,
            "parse_snapshot": value.parse_snapshot,
            "created_by": value.created_by,
            "created_at": value.created_at,
            "invalidated_at": value.invalidated_at,
            "invalidation_reason": value.invalidation_reason,
            "allowed_actions": allowed,
        }
    )


def get_manuscript(
    session: Session, *, actor: User, manuscript_id: uuid.UUID
) -> dict[str, Any]:
    manuscript = session.get(Manuscript, manuscript_id)
    if manuscript is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=manuscript.project_id, actor=actor, action="manuscript.read"
    )
    return manuscript_data(manuscript, _role(access))


def discover_project_manuscripts(
    session: Session, *, actor: User, project_id: uuid.UUID
) -> dict[str, Any]:
    access = project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="manuscript.read"
    )
    role = _role(access)
    manuscripts = session.exec(
        select(Manuscript)
        .where(Manuscript.project_id == project_id)
        .order_by(col(Manuscript.updated_at).desc(), col(Manuscript.created_at).desc())
    ).all()
    versions = session.exec(
        select(ManuscriptVersion)
        .where(ManuscriptVersion.project_id == project_id)
        .order_by(
            col(ManuscriptVersion.manuscript_id),
            col(ManuscriptVersion.version_number),
        )
    ).all()
    current_manuscript = next(
        (item for item in manuscripts if item.status == ManuscriptStatus.ACTIVE), None
    )
    current_version = None
    if (
        current_manuscript is not None
        and current_manuscript.current_version_id is not None
    ):
        current_version = next(
            (
                item
                for item in versions
                if item.id == current_manuscript.current_version_id
                and item.manuscript_id == current_manuscript.id
            ),
            None,
        )
        if current_version is None:
            raise ContractError(
                status_code=409,
                code="VERSION_UNAVAILABLE",
                message="The current ManuscriptVersion is unavailable.",
            )
    state = (
        ManuscriptStatus.ACTIVE.value
        if current_manuscript is not None
        else manuscripts[0].status.value
        if manuscripts
        else "NONE"
    )
    return {
        "state": state,
        "current_manuscript": (
            manuscript_data(current_manuscript, role)
            if current_manuscript is not None
            else None
        ),
        "current_version": (
            version_data(current_version, role) if current_version is not None else None
        ),
        "manuscripts": [manuscript_data(item, role) for item in manuscripts],
        "versions": [version_data(item, role) for item in versions],
    }


def list_versions(
    session: Session, *, actor: User, manuscript_id: uuid.UUID
) -> list[dict[str, Any]]:
    manuscript = session.get(Manuscript, manuscript_id)
    if manuscript is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=manuscript.project_id, actor=actor, action="manuscript.read"
    )
    versions = session.exec(
        select(ManuscriptVersion)
        .where(ManuscriptVersion.manuscript_id == manuscript.id)
        .order_by(col(ManuscriptVersion.version_number))
    ).all()
    return [version_data(item, _role(access)) for item in versions]


def get_version(
    session: Session, *, actor: User, version_id: uuid.UUID
) -> dict[str, Any]:
    version = session.get(ManuscriptVersion, version_id)
    if version is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=version.project_id, actor=actor, action="manuscript.read"
    )
    return version_data(version, _role(access))


def authorize_download(
    session: Session, *, actor: User, version_id: uuid.UUID
) -> dict[str, Any]:
    version = session.get(ManuscriptVersion, version_id)
    if version is None:
        raise _not_found()
    project_service.authorize_project(
        session, project_id=version.project_id, actor=actor, action="artifact.download"
    )
    if version.status != ManuscriptVersionStatus.AVAILABLE:
        raise ContractError(
            status_code=409,
            code="VERSION_UNAVAILABLE",
            message="ManuscriptVersion is not AVAILABLE.",
        )
    return artifact_service.authorize_download(
        session, actor=actor, artifact_id=version.artifact_id
    )


def create_check_run(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    payload: CheckRunCreate,
    idempotency_key: str,
    dispatcher: job_service.JobDispatcher,
) -> project_service.OperationResult:
    version = session.get(ManuscriptVersion, version_id)
    if version is None:
        raise _not_found()
    access = project_service.authorize_project(
        session,
        project_id=version.project_id,
        actor=actor,
        action="manuscript.check",
        for_update=True,
    )
    existing = session.exec(
        select(ManuscriptCheckRun).where(
            ManuscriptCheckRun.manuscript_version_id == version.id,
            ManuscriptCheckRun.idempotency_key == idempotency_key,
        )
    ).first()
    if existing is not None:
        return project_service.OperationResult(
            data=check_request_data(session, existing, _role(access)),
            status_code=202,
            idempotency_replayed=True,
        )
    artifact = session.get(Artifact, version.artifact_id)
    if (
        version.status != ManuscriptVersionStatus.AVAILABLE
        or artifact is None
        or artifact.project_id != version.project_id
        or artifact.status != ArtifactStatus.AVAILABLE
        or artifact.sha256 != version.source_hash
    ):
        raise ContractError(
            status_code=409,
            code="VERSION_UNAVAILABLE",
            message="ManuscriptVersion input is not valid for checking.",
        )
    run = ManuscriptCheckRun(
        project_id=version.project_id,
        manuscript_version_id=version.id,
        rule_set_version=RULE_SET_VERSION,
        parser_version=PARSER_VERSION,
        source_hash=version.source_hash,
        idempotency_key=idempotency_key,
        requested_checks=list(dict.fromkeys(payload.checks)),
        requested_by=actor.id,
    )
    session.add(run)
    session.flush()
    job = job_service.create_job(
        session,
        project_id=version.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.MANUSCRIPT_CHECK,
            resource_type="manuscript_check_run",
            resource_id=run.id,
            idempotency_key=idempotency_key,
            requested_by_user_id=actor.id,
            max_retries=2,
            retryable=True,
        ),
    )
    project_service._commit(session)
    dispatched = job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)
    return project_service.OperationResult(
        data={
            "manuscript_check_run": check_run_data(session, run, _role(access)),
            "job": job_service.job_data(session, dispatched),
        },
        status_code=202,
    )


def check_run_data(
    session: Session, run: ManuscriptCheckRun, role: ProjectMemberRole
) -> dict[str, Any]:
    job = session.exec(
        select(Job).where(
            Job.resource_type == "manuscript_check_run", Job.resource_id == run.id
        )
    ).first()
    actions = project_service.ROLE_ACTIONS[role]
    return _encoded(
        {
            **run.model_dump(),
            "job_id": job.id if job else None,
            "allowed_actions": ["manuscript_check_run.read"]
            if "manuscript.read" in actions
            else [],
        }
    )


def check_request_data(
    session: Session, run: ManuscriptCheckRun, role: ProjectMemberRole
) -> dict[str, Any]:
    job = session.exec(
        select(Job).where(
            Job.resource_type == "manuscript_check_run", Job.resource_id == run.id
        )
    ).one()
    return {
        "manuscript_check_run": check_run_data(session, run, role),
        "job": job_service.job_data(session, job),
    }


def get_check_run(
    session: Session, *, actor: User, run_id: uuid.UUID
) -> dict[str, Any]:
    run = session.get(ManuscriptCheckRun, run_id)
    if run is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=run.project_id, actor=actor, action="manuscript.read"
    )
    return check_run_data(session, run, _role(access))


def execute_check_job(
    session: Session, *, job: Job, run_id: uuid.UUID
) -> ManuscriptCheckRun:
    run = session.exec(
        select(ManuscriptCheckRun)
        .where(
            ManuscriptCheckRun.id == job.resource_id,
            ManuscriptCheckRun.project_id == job.project_id,
        )
        .with_for_update()
    ).first()
    if (
        run is None
        or job.task_type != JobTaskType.MANUSCRIPT_CHECK
        or job.resource_type != "manuscript_check_run"
    ):
        raise ContractError(
            status_code=409,
            code="INVALID_JOB_INPUT",
            message="Manuscript Check Job input is invalid.",
        )
    version = session.exec(
        select(ManuscriptVersion).where(
            ManuscriptVersion.id == run.manuscript_version_id,
            ManuscriptVersion.project_id == run.project_id,
        )
    ).first()
    artifact = session.get(Artifact, version.artifact_id) if version else None
    if (
        version is None
        or artifact is None
        or version.status != ManuscriptVersionStatus.AVAILABLE
        or artifact.status != ArtifactStatus.AVAILABLE
        or artifact.artifact_type != ArtifactType.MANUSCRIPT_DOCX
        or artifact.project_id != run.project_id
        or artifact.sha256 != version.source_hash
        or run.source_hash != version.source_hash
    ):
        raise ContractError(
            status_code=409,
            code="FILE_HASH_MISMATCH",
            message="Worker revalidation rejected the ManuscriptVersion input.",
        )
    run.status = ManuscriptCheckRunStatus.PARSING
    run.processing_run_id = run_id
    run.started_at = get_datetime_utc()
    session.add(run)
    session.flush()
    path = _download_and_verify(session, version, artifact)
    try:
        snapshot = parse_docx(path)
    finally:
        path.unlink(missing_ok=True)
    run.status = ManuscriptCheckRunStatus.CHECKING_RULES
    findings = run_rules(snapshot, set(run.requested_checks))
    formal_evidence: dict[str, AnalysisResult] = {}
    project_consistency = "NOT_REQUESTED"
    if "NUMERIC_CONSISTENCY" in run.requested_checks:
        completed_results = session.exec(
            select(AnalysisResult, AnalysisRun)
            .join(
                AnalysisRun,
                col(AnalysisRun.id) == col(AnalysisResult.analysis_run_id),
            )
            .where(
                AnalysisResult.project_id == run.project_id,
                AnalysisRun.project_id == run.project_id,
                AnalysisRun.status == AnalysisRunStatus.COMPLETED,
                col(AnalysisRun.invalidated_at).is_(None),
                col(AnalysisRun.effective_n).is_not(None),
            )
        ).all()
        candidate_metrics = [
            (result, _formal_numeric_metrics(result.payload), analysis_run.effective_n)
            for result, analysis_run in completed_results
        ]
        effective_values = {
            effective_n
            for _, _, effective_n in candidate_metrics
            if effective_n is not None
        }
        if len(effective_values) == 1:
            expected_n = float(next(iter(effective_values)))
            for paragraph in snapshot["paragraphs"]:
                text = str(paragraph["text"])
                for match in re.finditer(r"\bN\s*=\s*(\d+)\b", text):
                    observed_n = float(match.group(1))
                    if observed_n == expected_n:
                        continue
                    finding = Finding(
                        ManuscriptIssueType.SAMPLE_SIZE_MISMATCH,
                        ManuscriptIssueSeverity.HIGH,
                        dict(paragraph["locator"]),
                        text[:240],
                        f"N={int(observed_n)}",
                        "Manuscript sample size does not match the completed project AnalysisRun.",
                        "Review the formal AnalysisResult and its DatasetVersion before changing the manuscript.",
                    )
                    findings.append(finding)
                    formal_evidence[finding.finding_hash] = candidate_metrics[0][0]
        elif completed_results:
            project_consistency = "AMBIGUOUS"
        else:
            project_consistency = "SOURCE_UNAVAILABLE"

        # Compare only explicit statistics. Missing/null values remain unknown and
        # never become a fabricated mismatch or success.
        for paragraph in snapshot["paragraphs"]:
            text = str(paragraph["text"])
            for match in _STATISTIC_RE.finditer(text):
                label = match.group("label").lower().replace("β", "beta")
                observed = float(match.group("value"))
                comparisons = [
                    (result, metrics.get(label))
                    for result, metrics, _ in candidate_metrics
                    if label in metrics
                ]
                if len(comparisons) != 1:
                    project_consistency = (
                        "AMBIGUOUS" if comparisons else "SOURCE_UNAVAILABLE"
                    )
                    continue
                result, expected = comparisons[0]
                matched = _metric_matches(observed, expected)
                if matched is False:
                    finding = Finding(
                        ManuscriptIssueType.STATISTIC_MISMATCH,
                        ManuscriptIssueSeverity.HIGH,
                        dict(paragraph["locator"]),
                        text[:240],
                        f"{label}={observed:g}",
                        f"Manuscript {label} does not match the completed project AnalysisResult within tolerance.",
                        "Review the formal AnalysisResult and version/hash before changing the manuscript.",
                    )
                    findings.append(finding)
                    formal_evidence[finding.finding_hash] = result
                elif matched is None:
                    project_consistency = "SOURCE_UNAVAILABLE"
        if completed_results and project_consistency == "NOT_REQUESTED":
            project_consistency = (
                "EXACT_MATCH" if not formal_evidence else "EXACT_MISMATCH"
            )
    for finding in findings:
        issue = ManuscriptIssue(
            project_id=run.project_id,
            manuscript_check_run_id=run.id,
            manuscript_version_id=version.id,
            issue_type=finding.issue_type,
            severity=finding.severity,
            locator=finding.locator,
            paragraph_index=finding.locator.get("paragraph"),
            table_index=finding.locator.get("table"),
            original_text=finding.original_text,
            normalized_reference=finding.normalized_reference,
            reason=finding.reason,
            suggestion=finding.suggestion,
            finding_hash=finding.finding_hash,
            confidence=finding.confidence,
            auto_fixable=finding.auto_fixable,
        )
        session.add(issue)
        session.flush()
        evidence_payload = {
            "rule_set_version": RULE_SET_VERSION,
            "finding_code": finding.issue_type.value,
            "locator": finding.locator,
        }
        session.add(
            ManuscriptIssueEvidence(
                project_id=run.project_id,
                manuscript_issue_id=issue.id,
                evidence_type=ManuscriptEvidenceType.RULE,
                evidence_object_type="deterministic_rule",
                evidence_hash=hashlib.sha256(
                    jsonable_encoder(evidence_payload).__repr__().encode()
                ).hexdigest(),
                evidence_metadata=evidence_payload,
            )
        )
        linked_evidence = formal_evidence.get(finding.finding_hash)
        if linked_evidence is not None:
            result_payload = {
                "result_hash": linked_evidence.result_hash,
                "analysis_run_id": str(linked_evidence.analysis_run_id),
                "match": "EXACT_MISMATCH",
            }
            session.add(
                ManuscriptIssueEvidence(
                    project_id=run.project_id,
                    manuscript_issue_id=issue.id,
                    evidence_type=ManuscriptEvidenceType.ANALYSIS_RESULT,
                    evidence_object_type="analysis_result",
                    evidence_object_id=linked_evidence.id,
                    evidence_hash=hashlib.sha256(
                        jsonable_encoder(result_payload).__repr__().encode()
                    ).hexdigest(),
                    evidence_metadata=result_payload,
                )
            )
    run.issue_count = len(findings)
    run.high_issue_count = sum(
        item.severity == ManuscriptIssueSeverity.HIGH for item in findings
    )
    run.degradation = {
        "unsupported_features": snapshot["unsupported_features"],
        "unknown_parts": snapshot["unknown_parts"],
        "confidence": snapshot["confidence"],
        "project_consistency": project_consistency,
    }
    run.status = (
        ManuscriptCheckRunStatus.LOW_CONFIDENCE
        if snapshot["confidence"] == "LOW"
        else (
            ManuscriptCheckRunStatus.NEEDS_REVIEW
            if findings
            else ManuscriptCheckRunStatus.COMPLETED
        )
    )
    run.completed_at = get_datetime_utc()
    session.add(run)
    session.flush()
    return run


def list_issues(
    session: Session, *, actor: User, run_id: uuid.UUID
) -> list[dict[str, Any]]:
    run = session.get(ManuscriptCheckRun, run_id)
    if run is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=run.project_id, actor=actor, action="manuscript.read"
    )
    return [
        issue_data(item, _role(access))
        for item in session.exec(
            select(ManuscriptIssue)
            .where(ManuscriptIssue.manuscript_check_run_id == run.id)
            .order_by(col(ManuscriptIssue.created_at))
        ).all()
    ]


def issue_data(issue: ManuscriptIssue, role: ProjectMemberRole) -> dict[str, Any]:
    permissions = project_service.ROLE_ACTIONS[role]
    actions = ["manuscript_issue.read"] if "manuscript.read" in permissions else []
    if (
        issue.status in {ManuscriptIssueStatus.OPEN, ManuscriptIssueStatus.ACKNOWLEDGED}
        and "manuscript.review" in permissions
    ):
        actions.extend(["manuscript_issue.accept", "manuscript_issue.reject"])
    return _encoded({**issue.model_dump(), "allowed_actions": actions})


def get_issue(session: Session, *, actor: User, issue_id: uuid.UUID) -> dict[str, Any]:
    issue = session.get(ManuscriptIssue, issue_id)
    if issue is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=issue.project_id, actor=actor, action="manuscript.read"
    )
    data = issue_data(issue, _role(access))
    data["evidence"] = [
        _encoded(item)
        for item in session.exec(
            select(ManuscriptIssueEvidence).where(
                ManuscriptIssueEvidence.manuscript_issue_id == issue.id
            )
        ).all()
    ]
    return data


def decide_issue(
    session: Session,
    *,
    actor: User,
    issue_id: uuid.UUID,
    accept: bool,
    reason: str | None,
    if_match: int,
) -> dict[str, Any]:
    issue = session.exec(
        select(ManuscriptIssue).where(ManuscriptIssue.id == issue_id).with_for_update()
    ).first()
    if issue is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=issue.project_id, actor=actor, action="manuscript.review"
    )
    if issue.lock_version != if_match:
        raise ContractError(
            status_code=412,
            code="PRECONDITION_FAILED",
            message="The ManuscriptIssue has changed.",
        )
    if (
        issue.status
        not in {ManuscriptIssueStatus.OPEN, ManuscriptIssueStatus.ACKNOWLEDGED}
        or issue.invalidated_at is not None
    ):
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Issue cannot be decided in its current state.",
        )
    before = issue.status
    issue.status = (
        ManuscriptIssueStatus.ACCEPTED if accept else ManuscriptIssueStatus.REJECTED
    )
    issue.decision_reason = reason
    issue.decided_by = actor.id
    issue.lock_version += 1
    session.add(issue)
    project_service._add_audit(
        session,
        project_id=issue.project_id,
        actor=actor,
        action="MANUSCRIPT_ISSUE_ACCEPTED" if accept else "MANUSCRIPT_ISSUE_REJECTED",
        object_type="manuscript_issue",
        object_id=issue.id,
        before=_encoded({"status": before, "lock_version": if_match}),
        after=_encoded({"status": issue.status, "lock_version": issue.lock_version}),
        reason=reason,
    )
    project_service._commit(session)
    return issue_data(issue, _role(access))


def mark_failed_check_job(session: Session, *, job: Job, error_code: str) -> None:
    run = session.get(ManuscriptCheckRun, job.resource_id)
    if (
        run
        and run.project_id == job.project_id
        and run.status
        not in {
            ManuscriptCheckRunStatus.COMPLETED,
            ManuscriptCheckRunStatus.NEEDS_REVIEW,
            ManuscriptCheckRunStatus.LOW_CONFIDENCE,
        }
    ):
        run.status = ManuscriptCheckRunStatus.FAILED
        run.error_code = error_code
        run.completed_at = get_datetime_utc()
        session.add(run)


def mark_cancelled_check_job(session: Session, *, job: Job) -> None:
    run = session.get(ManuscriptCheckRun, job.resource_id)
    if run and run.project_id == job.project_id:
        run.status = ManuscriptCheckRunStatus.CANCELLED
        run.completed_at = get_datetime_utc()
        session.add(run)
        project_service._commit(session)
