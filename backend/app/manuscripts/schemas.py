from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import ClaimConfidence, ClaimStatus, ClaimType


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ManuscriptCreate(StrictModel):
    artifact_id: uuid.UUID
    title: str | None = Field(default=None, max_length=500)


class CheckRunCreate(StrictModel):
    checks: list[
        Literal[
            "CITATION",
            "NUMERIC_CONSISTENCY",
            "CAUSALITY",
            "TERMINOLOGY",
            "BASIC_FORMAT",
        ]
    ] = Field(min_length=1)
    use_project_literature: bool = True
    use_project_analysis_results: bool = True
    use_project_figures: bool = True


class IssueDecision(StrictModel):
    reason: str | None = Field(default=None, max_length=2000)


class RevisionAuditCreate(StrictModel):
    baseline_manuscript_version_id: uuid.UUID
    candidate_manuscript_version_id: uuid.UUID
    referenced_result_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)


class FixPlanCreate(StrictModel):
    issue_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)


class ClaimCreate(StrictModel):
    claim_type: ClaimType
    source_object_type: Literal[
        "manuscript_version", "analysis_result", "figure", "evidence_span"
    ]
    source_object_id: uuid.UUID
    source_location: dict[str, object]
    claim_text: str = Field(min_length=1, max_length=20_000)
    normalized_claim: str | None = Field(default=None, max_length=20_000)
    scope_statement: str | None = Field(default=None, max_length=10_000)
    status: ClaimStatus = ClaimStatus.NEEDS_EVIDENCE
    confidence: ClaimConfidence = ClaimConfidence.UNKNOWN


class ClaimUpdate(StrictModel):
    claim_text: str | None = Field(default=None, min_length=1, max_length=20_000)
    normalized_claim: str | None = Field(default=None, max_length=20_000)
    scope_statement: str | None = Field(default=None, max_length=10_000)
    source_object_type: (
        Literal["manuscript_version", "analysis_result", "figure", "evidence_span"]
        | None
    ) = None
    source_object_id: uuid.UUID | None = None
    source_location: dict[str, object] | None = None
    status: ClaimStatus | None = None
    confidence: ClaimConfidence | None = None
