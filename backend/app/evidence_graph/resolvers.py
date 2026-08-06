from __future__ import annotations

import uuid
from collections.abc import Callable

from sqlmodel import Session

from app.api.errors import ContractError
from app.models import (
    AnalysisPlan,
    AnalysisPlanStatus,
    AnalysisResult,
    AnalysisRun,
    AnalysisRunStatus,
    ApprovalRecord,
    ApprovalStatus,
    Artifact,
    ArtifactStatus,
    AuditResult,
    AuditResultStatus,
    DatasetVersion,
    DatasetVersionStatus,
    DataTransformation,
    DataTransformationStatus,
    EvidenceObjectType,
    EvidenceReviewStatus,
    EvidenceSpan,
    Figure,
    FigureStatus,
    LiteratureRecord,
    LiteratureVerificationStatus,
    LocationVerificationStatus,
    ManuscriptVersion,
    ManuscriptVersionStatus,
    UserDeclaredReadScope,
)
from app.projects import service as project_service

from .schemas import EvidenceReference

Resolver = Callable[[Session, uuid.UUID, uuid.UUID], EvidenceReference]


def _not_found() -> ContractError:
    return ContractError(
        status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
    )


def _hash(snapshot: object) -> str:
    return project_service.request_hash(snapshot)


def _artifact(
    session: Session, *, artifact_id: uuid.UUID, project_id: uuid.UUID
) -> Artifact:
    artifact = session.get(Artifact, artifact_id)
    if (
        artifact is None
        or artifact.project_id != project_id
        or artifact.status != ArtifactStatus.AVAILABLE
        or artifact.deleted_at is not None
    ):
        raise _not_found()
    return artifact


def _literature(
    session: Session, project_id: uuid.UUID, object_id: uuid.UUID
) -> EvidenceReference:
    value = session.get(LiteratureRecord, object_id)
    if value is None or value.project_id != project_id or value.deleted_at is not None:
        raise _not_found()
    known = value.verification_status in {
        LiteratureVerificationStatus.VERIFIED,
        LiteratureVerificationStatus.PARTIALLY_VERIFIED,
        LiteratureVerificationStatus.UNVERIFIED,
    }
    snapshot = {
        "updated_at": value.updated_at.isoformat(),
        "verification_status": value.verification_status,
        "decision": value.current_decision,
        "document_id": value.document_id,
    }
    return EvidenceReference(
        project_id=project_id,
        object_type=EvidenceObjectType.LITERATURE_RECORD,
        object_id=value.id,
        raw_status=value.verification_status,
        known_status=known,
        source_hash=_hash(snapshot),
        source_version=snapshot,
        label=value.title[:240],
        detail_intent="literature-record",
        stale=value.verification_status == LiteratureVerificationStatus.UNVERIFIED,
        limitations=["Literature metadata is not fully verified."]
        if value.verification_status != LiteratureVerificationStatus.VERIFIED
        else [],
        allowed_actions=["evidence.read"],
    )


def _span(
    session: Session, project_id: uuid.UUID, object_id: uuid.UUID
) -> EvidenceReference:
    value = session.get(EvidenceSpan, object_id)
    if value is None or value.project_id != project_id:
        raise _not_found()
    located = value.location_verification_status in {
        LocationVerificationStatus.LOCATED,
        LocationVerificationStatus.VERIFIED,
    }
    restricted = value.user_declared_read_scope == UserDeclaredReadScope.UNKNOWN
    snapshot = {
        "document_id": value.document_id,
        "page_number": value.page_number,
        "source_text_hash": value.source_text_hash,
        "location_status": value.location_verification_status,
        "review_status": value.review_status,
    }
    return EvidenceReference(
        project_id=project_id,
        object_type=EvidenceObjectType.EVIDENCE_SPAN,
        object_id=value.id,
        raw_status=value.location_verification_status,
        known_status=True,
        source_hash=value.source_text_hash,
        source_version=snapshot,
        label=f"EvidenceSpan page {value.page_number}",
        detail_intent="evidence-span",
        stale=not located or value.review_status == EvidenceReviewStatus.REJECTED,
        restricted=restricted,
        limitations=["Read scope is unknown."] if restricted else [],
        allowed_actions=["evidence.read"],
    )


def _dataset_version(
    session: Session, project_id: uuid.UUID, object_id: uuid.UUID
) -> EvidenceReference:
    value = session.get(DatasetVersion, object_id)
    if value is None or value.project_id != project_id or value.deleted_at is not None:
        raise _not_found()
    artifact = _artifact(session, artifact_id=value.artifact_id, project_id=project_id)
    snapshot = {
        "version_number": value.version_number,
        "artifact_id": artifact.id,
        "artifact_hash": artifact.sha256,
        "data_hash": value.data_hash,
    }
    invalidated = (
        value.status == DatasetVersionStatus.INVALIDATED
        or value.invalidated_at is not None
    )
    return EvidenceReference(
        project_id=project_id,
        object_type=EvidenceObjectType.DATASET_VERSION,
        object_id=value.id,
        raw_status=value.status,
        known_status=True,
        source_hash=value.data_hash,
        source_version=snapshot,
        label=f"Dataset version {value.version_number}",
        detail_intent="dataset-version",
        invalidated=invalidated,
        stale=value.status != DatasetVersionStatus.AVAILABLE,
        allowed_actions=["evidence.read"],
    )


def _transformation(
    session: Session, project_id: uuid.UUID, object_id: uuid.UUID
) -> EvidenceReference:
    value = session.get(DataTransformation, object_id)
    if value is None or value.project_id != project_id:
        raise _not_found()
    snapshot = {
        "source_dataset_version_id": value.source_dataset_version_id,
        "target_dataset_version_id": value.target_dataset_version_id,
        "parameters_hash": value.parameters_hash,
    }
    return EvidenceReference(
        project_id=project_id,
        object_type=EvidenceObjectType.DATA_TRANSFORMATION,
        object_id=value.id,
        raw_status=value.status,
        known_status=True,
        source_hash=value.parameters_hash,
        source_version=snapshot,
        label="Data transformation",
        detail_intent="data-transformation",
        stale=value.status != DataTransformationStatus.COMPLETED,
        allowed_actions=["evidence.read"],
    )


def _analysis_plan(
    session: Session, project_id: uuid.UUID, object_id: uuid.UUID
) -> EvidenceReference:
    value = session.get(AnalysisPlan, object_id)
    if value is None or value.project_id != project_id:
        raise _not_found()
    source_hash = (
        value.payload_hash
        or value.validation_hash
        or _hash({"id": value.id, "lock": value.lock_version})
    )
    return EvidenceReference(
        project_id=project_id,
        object_type=EvidenceObjectType.ANALYSIS_PLAN,
        object_id=value.id,
        raw_status=value.status,
        known_status=True,
        source_hash=source_hash,
        source_version={
            "lock_version": value.lock_version,
            "dataset_version_id": value.dataset_version_id,
        },
        label="Analysis plan",
        detail_intent="analysis-plan",
        invalidated=value.invalidated_at is not None,
        stale=value.status
        not in {AnalysisPlanStatus.APPROVED, AnalysisPlanStatus.READY},
        allowed_actions=["evidence.read"],
    )


def _analysis_run(
    session: Session, project_id: uuid.UUID, object_id: uuid.UUID
) -> EvidenceReference:
    value = session.get(AnalysisRun, object_id)
    if value is None or value.project_id != project_id:
        raise _not_found()
    return EvidenceReference(
        project_id=project_id,
        object_type=EvidenceObjectType.ANALYSIS_RUN,
        object_id=value.id,
        raw_status=value.status,
        known_status=True,
        source_hash=value.input_hash,
        source_version={
            "run_number": value.run_number,
            "parameters_hash": value.parameters_hash,
        },
        label=f"Analysis run {value.run_number}",
        detail_intent="analysis-run",
        invalidated=value.invalidated_at is not None,
        stale=value.status != AnalysisRunStatus.COMPLETED,
        allowed_actions=["evidence.read"],
    )


def _analysis_result(
    session: Session, project_id: uuid.UUID, object_id: uuid.UUID
) -> EvidenceReference:
    value = session.get(AnalysisResult, object_id)
    run = session.get(AnalysisRun, value.analysis_run_id) if value else None
    if (
        value is None
        or run is None
        or value.project_id != project_id
        or run.project_id != project_id
    ):
        raise _not_found()
    return EvidenceReference(
        project_id=project_id,
        object_type=EvidenceObjectType.ANALYSIS_RESULT,
        object_id=value.id,
        raw_status=run.status,
        known_status=True,
        source_hash=value.result_hash,
        source_version={
            "analysis_run_id": run.id,
            "result_key": value.result_key,
            "schema_version": value.schema_version,
        },
        label=f"Analysis result {value.result_key}",
        detail_intent="analysis-result",
        invalidated=run.invalidated_at is not None,
        stale=run.status != AnalysisRunStatus.COMPLETED,
        allowed_actions=["evidence.read"],
    )


def _figure(
    session: Session, project_id: uuid.UUID, object_id: uuid.UUID
) -> EvidenceReference:
    value = session.get(Figure, object_id)
    if value is None or value.project_id != project_id:
        raise _not_found()
    _artifact(session, artifact_id=value.png_artifact_id, project_id=project_id)
    invalidated = (
        value.invalidated_at is not None or value.status == FigureStatus.INVALIDATED
    )
    return EvidenceReference(
        project_id=project_id,
        object_type=EvidenceObjectType.FIGURE,
        object_id=value.id,
        raw_status=value.status,
        known_status=True,
        source_hash=value.figure_hash,
        source_version={
            "version_number": value.version_number,
            "analysis_result_id": value.analysis_result_id,
        },
        label=value.caption[:240],
        detail_intent="figure",
        invalidated=invalidated,
        stale=value.status
        in {FigureStatus.DRAFT, FigureStatus.ARCHIVED, FigureStatus.INVALIDATED},
        allowed_actions=["evidence.read"],
    )


def _manuscript_version(
    session: Session, project_id: uuid.UUID, object_id: uuid.UUID
) -> EvidenceReference:
    value = session.get(ManuscriptVersion, object_id)
    if value is None or value.project_id != project_id:
        raise _not_found()
    artifact = _artifact(session, artifact_id=value.artifact_id, project_id=project_id)
    return EvidenceReference(
        project_id=project_id,
        object_type=EvidenceObjectType.MANUSCRIPT_VERSION,
        object_id=value.id,
        raw_status=value.status,
        known_status=True,
        source_hash=artifact.sha256,
        source_version={
            "version_number": value.version_number,
            "artifact_id": artifact.id,
        },
        label=f"Manuscript version {value.version_number}",
        detail_intent="manuscript-version",
        invalidated=value.status == ManuscriptVersionStatus.INVALIDATED,
        stale=value.status != ManuscriptVersionStatus.AVAILABLE,
        allowed_actions=["evidence.read"],
    )


def _approval(
    session: Session, project_id: uuid.UUID, object_id: uuid.UUID
) -> EvidenceReference:
    value = session.get(ApprovalRecord, object_id)
    if value is None or value.project_id != project_id:
        raise _not_found()
    return EvidenceReference(
        project_id=project_id,
        object_type=EvidenceObjectType.APPROVAL,
        object_id=value.id,
        raw_status=value.status,
        known_status=True,
        source_hash=value.payload_hash,
        source_version={
            "approval_type": value.approval_type,
            "target_object_type": value.target_object_type,
            "target_object_id": value.target_object_id,
        },
        label=f"Approval {value.approval_type}",
        detail_intent="approval",
        stale=value.status != ApprovalStatus.APPROVED,
        allowed_actions=["evidence.read"],
    )


def _audit(
    session: Session, project_id: uuid.UUID, object_id: uuid.UUID
) -> EvidenceReference:
    value = session.get(AuditResult, object_id)
    if value is None or value.project_id != project_id:
        raise _not_found()
    source_hash = value.result_hash or value.source_snapshot_hash
    if source_hash is None:
        source_hash = _hash({"id": value.id, "request": value.request_snapshot})
    return EvidenceReference(
        project_id=project_id,
        object_type=EvidenceObjectType.AUDIT_RESULT,
        object_id=value.id,
        raw_status=value.outcome or value.status,
        known_status=True,
        source_hash=source_hash,
        source_version={
            "audit_type": value.audit_type,
            "rule_set_version": value.rule_set_version,
        },
        label=f"Audit {value.audit_type}",
        detail_intent="audit-result",
        invalidated=value.invalidated_at is not None,
        stale=value.status != AuditResultStatus.COMPLETED,
        limitations=list(value.limitations),
        allowed_actions=["evidence.read"],
    )


RESOLVERS: dict[EvidenceObjectType, Resolver] = {
    EvidenceObjectType.LITERATURE_RECORD: _literature,
    EvidenceObjectType.EVIDENCE_SPAN: _span,
    EvidenceObjectType.DATASET_VERSION: _dataset_version,
    EvidenceObjectType.DATA_TRANSFORMATION: _transformation,
    EvidenceObjectType.ANALYSIS_PLAN: _analysis_plan,
    EvidenceObjectType.ANALYSIS_RUN: _analysis_run,
    EvidenceObjectType.ANALYSIS_RESULT: _analysis_result,
    EvidenceObjectType.FIGURE: _figure,
    EvidenceObjectType.MANUSCRIPT_VERSION: _manuscript_version,
    EvidenceObjectType.APPROVAL: _approval,
    EvidenceObjectType.AUDIT_RESULT: _audit,
}


def resolve_evidence(
    session: Session,
    *,
    project_id: uuid.UUID,
    object_type: EvidenceObjectType,
    object_id: uuid.UUID,
) -> EvidenceReference:
    resolver = RESOLVERS.get(object_type)
    if resolver is None:
        raise ContractError(
            status_code=422,
            code="EVIDENCE_TYPE_UNSUPPORTED",
            message="Evidence type is not supported.",
        )
    return resolver(session, project_id, object_id)
