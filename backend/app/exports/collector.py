from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, col, select

from app.core.config import settings
from app.models import (
    AnalysisPlan,
    AnalysisResult,
    AnalysisRun,
    AnalysisRunStatus,
    ApprovalRecord,
    Artifact,
    ArtifactStatus,
    ArtifactType,
    AuditResult,
    Claim,
    ClaimEvidenceLink,
    Dataset,
    DatasetLicenseStatus,
    DatasetVersion,
    DatasetVersionStatus,
    DataTransformation,
    EvidenceSpan,
    ExportItemIncludeStatus,
    Figure,
    FigureStatus,
    LiteratureDecision,
    LiteratureRecord,
    ManuscriptCheckRun,
    ManuscriptVersion,
    ManuscriptVersionStatus,
    QueryPlan,
    ResearchQuestionVersion,
)

from .manifest import PackageMember, canonical_json
from .schemas import ExportCandidate, ReproPackageCreate

_ROOT = Path(__file__).resolve().parents[3]
_SENSITIVE_KEY = re.compile(
    r"(secret|token|password|api.?key|connection|dsn|credential|prompt.?content)",
    re.IGNORECASE,
)


def _enum(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): redact(item)
            for key, item in value.items()
            if not _SENSITIVE_KEY.search(str(key))
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    if isinstance(value, str):
        if re.match(r"^[A-Za-z]:[\\/]", value) or value.startswith("/tmp/"):
            return "[REDACTED_PATH]"
        return value
    return jsonable_encoder(value)


def _artifact_path(artifact: Artifact) -> str:
    suffix = Path(artifact.filename).suffix.lower()
    prefixes = {
        ArtifactType.PDF_DOCUMENT: "02_literature/files",
        ArtifactType.DATASET_FILE: "06_data_versions/files",
        ArtifactType.ANALYSIS_CODE: "08_analysis/code",
        ArtifactType.ANALYSIS_LOG: "08_analysis/logs",
        ArtifactType.JSON_RESULT: "08_analysis/results",
        ArtifactType.FIGURE_PNG: "09_figures",
        ArtifactType.FIGURE_SVG: "09_figures",
        ArtifactType.FIGURE_PDF: "09_figures",
        ArtifactType.MANUSCRIPT_DOCX: "10_manuscript",
        ArtifactType.MODEL_OUTPUT: "13_agent_and_approval_logs/model-output",
    }
    prefix = prefixes.get(artifact.artifact_type, "12_environment/artifacts")
    return f"{prefix}/{artifact.id}{suffix}"


def enumerate_candidates(
    session: Session, *, project_id: uuid.UUID, request: ReproPackageCreate
) -> tuple[
    list[ExportCandidate], list[dict[str, Any]], list[dict[str, Any]], list[str]
]:
    artifacts = session.exec(
        select(Artifact)
        .where(Artifact.project_id == project_id, col(Artifact.deleted_at).is_(None))
        .order_by(col(Artifact.id))
    ).all()
    dataset_versions = session.exec(
        select(DatasetVersion).where(DatasetVersion.project_id == project_id)
    ).all()
    datasets = {
        value.id: value
        for value in session.exec(
            select(Dataset).where(Dataset.project_id == project_id)
        ).all()
    }
    dataset_by_artifact = {
        value.artifact_id: (value, datasets.get(value.dataset_id))
        for value in dataset_versions
    }
    manuscript_by_artifact = {
        value.artifact_id: value
        for value in session.exec(
            select(ManuscriptVersion).where(ManuscriptVersion.project_id == project_id)
        ).all()
    }
    figure_by_artifact: dict[uuid.UUID, Figure] = {}
    for stored_figure in session.exec(
        select(Figure).where(Figure.project_id == project_id)
    ).all():
        for artifact_id in (
            stored_figure.png_artifact_id,
            stored_figure.svg_artifact_id,
            stored_figure.pdf_artifact_id,
        ):
            if artifact_id:
                figure_by_artifact[artifact_id] = stored_figure
    candidates: list[ExportCandidate] = []
    blocking: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    limitations = [
        "Original literature files are metadata-only unless redistribution rights are explicit.",
        "M8 Agent logs are NOT_AVAILABLE and are not synthesized.",
    ]
    for artifact in artifacts:
        metadata = dict(artifact.artifact_metadata or {})
        sensitive = bool(
            metadata.get("sensitive") or metadata.get("contains_sensitive_data")
        )
        include_status = ExportItemIncludeStatus.INCLUDED
        reason: str | None = None
        license_status = "NOT_APPLICABLE"
        redistribution = "ALLOWED"
        owner_version: dict[str, Any] = {
            "artifact_status": artifact.status,
            "artifact_type": artifact.artifact_type,
        }
        if artifact.status != ArtifactStatus.AVAILABLE:
            include_status = ExportItemIncludeStatus.MISSING
            reason = "Artifact is not AVAILABLE."
            blocking.append(
                {
                    "code": "ARTIFACT_NOT_AVAILABLE",
                    "object_type": "ARTIFACT",
                    "object_id": artifact.id,
                    "message": "A candidate Artifact is not available.",
                }
            )
        elif artifact.artifact_type == ArtifactType.PDF_DOCUMENT:
            license_status = "UNKNOWN"
            redistribution = "METADATA_ONLY"
            include_status = ExportItemIncludeStatus.METADATA_ONLY
            reason = "Literature redistribution rights are not explicitly recorded."
            if request.include_original_literature_files:
                warnings.append(
                    {
                        "code": "LITERATURE_LICENSE_UNKNOWN",
                        "object_type": "ARTIFACT",
                        "object_id": artifact.id,
                        "message": "The literature file was downgraded to metadata-only.",
                    }
                )
        elif artifact.artifact_type == ArtifactType.DATASET_FILE:
            owner = dataset_by_artifact.get(artifact.id)
            dataset_version, dataset = owner if owner else (None, None)
            if dataset_version is not None:
                owner_version.update(
                    {
                        "dataset_version_id": dataset_version.id,
                        "version_number": dataset_version.version_number,
                        "data_hash": dataset_version.data_hash,
                        "status": dataset_version.status,
                    }
                )
            if dataset is None:
                include_status = ExportItemIncludeStatus.BLOCKED
                reason = "Dataset authority is missing."
                blocking.append(
                    {
                        "code": "DATASET_AUTHORITY_MISSING",
                        "object_type": "ARTIFACT",
                        "object_id": artifact.id,
                        "message": "Dataset Artifact has no same-project Dataset authority.",
                    }
                )
            else:
                license_status = dataset.license_status.value
                owner_version["dataset_id"] = dataset.id
                owner_version["license_name"] = dataset.license_name
                if (
                    dataset_version
                    and dataset_version.status != DatasetVersionStatus.AVAILABLE
                ):
                    include_status = ExportItemIncludeStatus.BLOCKED
                    reason = "DatasetVersion is invalidated or unavailable."
                    blocking.append(
                        {
                            "code": "DATASET_VERSION_INVALID",
                            "object_type": "DATASET_VERSION",
                            "object_id": dataset_version.id,
                            "message": "DatasetVersion is not available for export.",
                        }
                    )
                elif not request.include_dataset_versions:
                    include_status = ExportItemIncludeStatus.EXCLUDED
                    reason = "Dataset versions were excluded by export scope."
                elif dataset.license_status in {
                    DatasetLicenseStatus.UNKNOWN,
                    DatasetLicenseStatus.RESTRICTED,
                }:
                    redistribution = "METADATA_ONLY"
                    include_status = ExportItemIncludeStatus.METADATA_ONLY
                    reason = "Dataset license does not authorize redistribution."
                    warnings.append(
                        {
                            "code": "DATASET_LICENSE_UNKNOWN"
                            if dataset.license_status == DatasetLicenseStatus.UNKNOWN
                            else "DATASET_LICENSE_RESTRICTED",
                            "object_type": "DATASET",
                            "object_id": dataset.id,
                            "message": "Dataset content was downgraded to metadata-only.",
                        }
                    )
        elif artifact.artifact_type == ArtifactType.MODEL_OUTPUT:
            if not request.include_model_output_artifacts:
                include_status = ExportItemIncludeStatus.EXCLUDED
                reason = "Model output Artifacts were excluded by export scope."
            elif not metadata.get("redaction_verified"):
                include_status = ExportItemIncludeStatus.METADATA_ONLY
                redistribution = "METADATA_ONLY"
                reason = (
                    "Model output lacks an authoritative redaction verification record."
                )
                warnings.append(
                    {
                        "code": "MODEL_OUTPUT_REDACTION_UNVERIFIED",
                        "object_type": "ARTIFACT",
                        "object_id": artifact.id,
                        "message": "Model output was downgraded to metadata-only.",
                    }
                )
        elif artifact.artifact_type == ArtifactType.ANALYSIS_LOG:
            include_status = ExportItemIncludeStatus.METADATA_ONLY
            redistribution = "METADATA_ONLY"
            reason = (
                "Raw logs are excluded to prevent secret and internal-path disclosure."
            )
        elif artifact.artifact_type == ArtifactType.MANUSCRIPT_DOCX:
            manuscript_version = manuscript_by_artifact.get(artifact.id)
            if (
                manuscript_version
                and manuscript_version.status != ManuscriptVersionStatus.AVAILABLE
            ):
                include_status = ExportItemIncludeStatus.BLOCKED
                reason = "ManuscriptVersion is invalidated or unavailable."
                blocking.append(
                    {
                        "code": "MANUSCRIPT_VERSION_INVALID",
                        "object_type": "MANUSCRIPT_VERSION",
                        "object_id": manuscript_version.id,
                        "message": "ManuscriptVersion is not available for export.",
                    }
                )
            else:
                include_status = ExportItemIncludeStatus.METADATA_ONLY
                redistribution = "METADATA_ONLY"
                reason = "Manuscript source is represented by metadata and hash only."
        artifact_figure = figure_by_artifact.get(artifact.id)
        if artifact_figure is not None:
            owner_version.update(
                {
                    "figure_id": artifact_figure.id,
                    "figure_hash": artifact_figure.figure_hash,
                }
            )
            if (
                artifact_figure.status == FigureStatus.INVALIDATED
                or artifact_figure.invalidated_at
            ):
                include_status = ExportItemIncludeStatus.BLOCKED
                reason = "Figure is invalidated."
                blocking.append(
                    {
                        "code": "FIGURE_INVALIDATED",
                        "object_type": "FIGURE",
                        "object_id": artifact_figure.id,
                        "message": "An invalidated Figure cannot be packaged.",
                    }
                )
        if sensitive:
            if not request.include_sensitive_data:
                include_status = ExportItemIncludeStatus.EXCLUDED
                reason = "Sensitive Artifact excluded by default."
            elif include_status == ExportItemIncludeStatus.INCLUDED:
                warnings.append(
                    {
                        "code": "SENSITIVE_DATA_CONFIRMATION_REQUIRED",
                        "object_type": "ARTIFACT",
                        "object_id": artifact.id,
                        "message": "Sensitive content requires formal Export confirmation.",
                    }
                )
        candidates.append(
            ExportCandidate(
                object_type="ARTIFACT",
                object_id=artifact.id,
                artifact_id=artifact.id,
                package_path=_artifact_path(artifact),
                sha256=artifact.sha256,
                include_status=include_status,
                exclusion_reason=reason,
                license_status=license_status,
                sensitive=sensitive,
                redistribution=redistribution,
                source_version=redact(owner_version),
            )
        )
    for run in session.exec(
        select(AnalysisRun).where(AnalysisRun.project_id == project_id)
    ).all():
        if run.status not in {AnalysisRunStatus.COMPLETED} or run.invalidated_at:
            warnings.append(
                {
                    "code": "ANALYSIS_RUN_NOT_CURRENT",
                    "object_type": "ANALYSIS_RUN",
                    "object_id": run.id,
                    "message": "An analysis run is incomplete or invalidated and is not evidence for reproducibility.",
                }
            )
    for claim in session.exec(
        select(Claim).where(Claim.project_id == project_id)
    ).all():
        if claim.status.value not in {"CONFIRMED", "REJECTED", "INVALIDATED"}:
            warnings.append(
                {
                    "code": "CLAIM_UNCONFIRMED",
                    "object_type": "CLAIM",
                    "object_id": claim.id,
                    "message": "A Claim remains unconfirmed.",
                }
            )
    for audit in session.exec(
        select(AuditResult).where(AuditResult.project_id == project_id)
    ).all():
        if audit.degraded:
            warnings.append(
                {
                    "code": "AUDIT_DEGRADED",
                    "object_type": "AUDIT_RESULT",
                    "object_id": audit.id,
                    "message": "An AuditResult records provider degradation.",
                }
            )
    candidates.sort(key=lambda item: (item.package_path, str(item.object_id or "")))
    blocking.sort(key=lambda item: (item["code"], str(item.get("object_id") or "")))
    warnings.sort(key=lambda item: (item["code"], str(item.get("object_id") or "")))
    return candidates, blocking, warnings, limitations


def _rows(
    session: Session,
    model: type[Any],
    project_id: uuid.UUID,
    fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    values = session.exec(
        select(model).where(model.project_id == project_id).order_by(col(model.id))
    ).all()
    return [
        redact({field: _enum(getattr(value, field, None)) for field in fields})
        for value in values
    ]


def collect_metadata_members(
    session: Session, *, project_id: uuid.UUID
) -> list[PackageMember]:
    specs: list[tuple[str, type[Any], tuple[str, ...]]] = [
        (
            "01_research_question/research-question-versions.json",
            ResearchQuestionVersion,
            ("id", "version_number", "normalized_question", "status", "created_at"),
        ),
        (
            "01_research_question/query-plans.json",
            QueryPlan,
            (
                "id",
                "research_question_version_id",
                "status",
                "lock_version",
                "created_at",
            ),
        ),
        (
            "02_literature/literature-metadata.json",
            LiteratureRecord,
            (
                "id",
                "title",
                "publication_year",
                "journal_name",
                "doi",
                "verification_status",
                "current_decision",
            ),
        ),
        (
            "03_evidence_matrix/evidence-spans.json",
            EvidenceSpan,
            (
                "id",
                "literature_record_id",
                "document_id",
                "page_number",
                "source_text_hash",
                "review_status",
                "location_verification_status",
                "invalidated_at",
            ),
        ),
        (
            "03_evidence_matrix/literature-decisions.json",
            LiteratureDecision,
            (
                "id",
                "literature_record_id",
                "decision",
                "reason_code",
                "reason_text",
                "created_at",
            ),
        ),
        (
            "05_data_identity/datasets.json",
            Dataset,
            (
                "id",
                "name",
                "source_type",
                "publisher",
                "source_identifier",
                "doi",
                "license_name",
                "license_status",
                "known_limitations",
                "status",
            ),
        ),
        (
            "07_cleaning/transformations.json",
            DataTransformation,
            (
                "id",
                "source_dataset_version_id",
                "target_dataset_version_id",
                "status",
                "input_hash",
                "output_hash",
                "rule_set_version",
            ),
        ),
        (
            "08_analysis/plans.json",
            AnalysisPlan,
            (
                "id",
                "research_question_version_id",
                "dataset_version_id",
                "analysis_goal",
                "method",
                "status",
                "payload_hash",
                "validation_hash",
                "approval_record_id",
            ),
        ),
        (
            "08_analysis/results.json",
            AnalysisResult,
            (
                "id",
                "analysis_run_id",
                "result_key",
                "result_type",
                "schema_version",
                "is_primary",
                "payload",
                "result_hash",
            ),
        ),
        (
            "09_figures/figures.json",
            Figure,
            (
                "id",
                "dataset_version_id",
                "analysis_run_id",
                "analysis_result_id",
                "version_number",
                "chart_type",
                "status",
                "figure_hash",
                "invalidated_at",
            ),
        ),
        (
            "10_manuscript/check-runs.json",
            ManuscriptCheckRun,
            (
                "id",
                "manuscript_version_id",
                "rule_set_version",
                "parser_version",
                "source_hash",
                "status",
                "issue_count",
                "high_issue_count",
                "degradation",
            ),
        ),
        (
            "11_evidence_graph/claim-links.json",
            ClaimEvidenceLink,
            (
                "id",
                "claim_id",
                "evidence_object_type",
                "evidence_object_id",
                "relation_type",
                "strength",
                "status",
                "source_hash",
                "source_version",
                "invalidated_at",
            ),
        ),
        (
            "11_evidence_graph/audits.json",
            AuditResult,
            (
                "id",
                "audit_type",
                "target_object_type",
                "target_object_id",
                "status",
                "outcome",
                "rule_set_version",
                "result_hash",
                "findings",
                "limitations",
                "degraded",
            ),
        ),
        (
            "13_agent_and_approval_logs/approvals.json",
            ApprovalRecord,
            (
                "id",
                "approval_type",
                "target_object_type",
                "target_object_id",
                "status",
                "payload_hash",
                "expires_at",
                "supersedes_approval_id",
                "created_at",
            ),
        ),
    ]
    members: list[PackageMember] = []
    for path, model, fields in specs:
        payload = {
            "schema": "reca.export-metadata.v1",
            "items": _rows(session, model, project_id, fields),
        }
        members.append(
            PackageMember(
                path=path,
                content=canonical_json(payload),
                member_type="metadata",
                source={"object_type": model.__name__, "project_scope": "CURRENT"},
            )
        )
    members.append(
        PackageMember(
            path="13_agent_and_approval_logs/agent-logs.json",
            content=canonical_json({"status": "NOT_AVAILABLE", "records": []}),
            member_type="availability",
            source={"object_type": "AGENT_RUN", "implemented_stage": "M8"},
        )
    )
    return members


def implementation_metadata(candidates: list[ExportCandidate]) -> dict[str, Any]:
    packages = (
        "fastapi",
        "sqlmodel",
        "alembic",
        "celery",
        "pandas",
        "numpy",
        "scipy",
        "statsmodels",
        "matplotlib",
    )
    runtime = []
    for package in packages:
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            version = "NOT_AVAILABLE"
        runtime.append({"name": package, "version": version, "source": "backend lock"})
    frontend_package = _ROOT / "frontend/package.json"
    if frontend_package.exists():
        value = json.loads(frontend_package.read_text(encoding="utf-8"))
        xyflow = value.get("dependencies", {}).get("@xyflow/react")
        if xyflow:
            runtime.append(
                {
                    "name": "@xyflow/react",
                    "version": xyflow,
                    "source": "frontend/package.json",
                }
            )
    prompt_manifest = _ROOT / "backend/app/agents/prompts/prompt-manifest.yaml"
    prompt_versions = []
    if prompt_manifest.exists():
        content = prompt_manifest.read_bytes()
        prompt_versions.append(
            {
                "path": "backend/app/agents/prompts/prompt-manifest.yaml",
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    config = {
        "export_max_members": settings.EXPORT_MAX_MEMBERS,
        "export_max_item_bytes": settings.EXPORT_MAX_ITEM_BYTES,
        "export_max_total_bytes": settings.EXPORT_MAX_TOTAL_BYTES,
        "export_max_path_depth": settings.EXPORT_MAX_PATH_DEPTH,
        "export_max_compression_ratio": settings.EXPORT_MAX_COMPRESSION_RATIO,
    }
    source_versions = [
        {
            "object_type": item.object_type,
            "object_id": str(item.object_id) if item.object_id else None,
            "source_version": item.source_version,
        }
        for item in candidates
    ]
    return {
        "runtime_dependencies": runtime,
        "service_images": [
            {
                "service": "reca-backend-worker",
                "digest": os.getenv("RECA_SERVICE_IMAGE_DIGEST", "NOT_AVAILABLE"),
            }
        ],
        "upstream_projects": [],
        "vendored_assets": [],
        "prompt_versions": prompt_versions,
        "ruleset_versions": [
            "m7-export-readiness/1.0",
            "m7-evidence-completeness/1.0",
            "m7-claim-evidence-audit/1.0",
        ],
        "statistical_engines": [
            {"name": name, "version": version}
            for name, version in (
                (item["name"], item["version"])
                for item in runtime
                if item["name"] in {"numpy", "scipy", "statsmodels", "pandas"}
            )
        ],
        "citation_styles": [
            {
                "status": "NOT_AVAILABLE",
                "reason": "No adopted CSL artifact is stored in this snapshot.",
            }
        ],
        "configuration_hashes": {
            "export_policy": hashlib.sha256(canonical_json(config)).hexdigest()
        },
        "source_object_versions": source_versions,
        "artifact_hashes": [
            {"artifact_id": str(item.artifact_id), "sha256": item.sha256}
            for item in candidates
            if item.artifact_id and item.sha256
        ],
        "limitations": [
            "Service image digest is NOT_AVAILABLE when the deployment does not provide RECA_SERVICE_IMAGE_DIGEST.",
            "Manifest files cover every payload member; manifest.json integrity is authoritative through its separate immutable Artifact.",
        ],
    }
