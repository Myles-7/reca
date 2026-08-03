from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import ResearchGoal, ResearchRelationshipType


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConfidenceLabel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ResearchQuestionScopingStatus(StrEnum):
    NEEDS_USER_INPUT = "NEEDS_USER_INPUT"
    CANDIDATES_READY = "CANDIDATES_READY"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class PopulationSpec(StrictModel):
    education_level: str | None = None
    major_scope: str | None = None
    other_constraints: list[str] = Field(default_factory=list)


class VariableSpec(StrictModel):
    name: str = Field(min_length=1)
    definition: str | None = None
    measurement_hint: str | None = None


class UncertaintySpec(StrictModel):
    field: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class ResearchQuestionSpec(StrictModel):
    normalized_question: str = Field(min_length=1)
    research_object: str | None = None
    population: PopulationSpec | None = None
    context: str | None = None
    independent_variables: list[VariableSpec] = Field(default_factory=list)
    dependent_variables: list[VariableSpec] = Field(default_factory=list)
    control_variables: list[VariableSpec] = Field(default_factory=list)
    research_goal: ResearchGoal | None = None
    relationship_type: ResearchRelationshipType | None = None
    method_preference: list[str] = Field(default_factory=list)
    time_scope: str | None = None
    region_scope: str | None = None
    language_scope: list[str] = Field(default_factory=list)
    resource_constraints: list[str] = Field(default_factory=list)
    ethical_constraints: list[str] = Field(default_factory=list)
    uncertainties: list[UncertaintySpec] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list, max_length=3)


class SocraticQuestion(StrictModel):
    question_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    required: bool


class ScopingAnswer(StrictModel):
    question_id: str = Field(min_length=1)
    answer: str = Field(min_length=1)


class ProjectContextSnapshot(StrictModel):
    project_id: uuid.UUID
    project_stage: str
    discipline: str | None = None
    research_direction: str | None = None


class ResearchQuestionScopingInput(StrictModel):
    topic: str = Field(min_length=1)
    answers: list[ScopingAnswer] = Field(default_factory=list)
    project_context: ProjectContextSnapshot
    allowed_evidence_ids: list[uuid.UUID] = Field(default_factory=list)
    round_number: int = Field(ge=1, le=2)
    max_follow_up_questions: int = Field(default=3, ge=1, le=3)
    language: str = Field(default="zh-CN", min_length=2, max_length=20)


class ResearchQuestionCandidate(StrictModel):
    candidate_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    spec: ResearchQuestionSpec
    supporting_source_ids: list[uuid.UUID] = Field(default_factory=list)
    available_data: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    feasibility_risks: list[str] = Field(default_factory=list)


class ResearchQuestionScopingOutput(StrictModel):
    status: ResearchQuestionScopingStatus
    socratic_questions: list[SocraticQuestion] = Field(
        default_factory=list, max_length=3
    )
    candidates: list[ResearchQuestionCandidate] = Field(
        default_factory=list, max_length=3
    )
    evidence_gaps: list[str] = Field(default_factory=list)
    source_ids: list[uuid.UUID] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status_payload(self) -> ResearchQuestionScopingOutput:
        if self.status == ResearchQuestionScopingStatus.NEEDS_USER_INPUT:
            if not self.socratic_questions or self.candidates:
                raise ValueError(
                    "NEEDS_USER_INPUT requires questions and forbids candidates"
                )
        elif self.status == ResearchQuestionScopingStatus.CANDIDATES_READY:
            if not self.candidates or self.socratic_questions:
                raise ValueError(
                    "CANDIDATES_READY requires candidates and forbids questions"
                )
        elif self.candidates:
            raise ValueError("non-ready scoping states cannot contain candidates")
        return self


class AIModelMetadata(StrictModel):
    model_invocation_id: uuid.UUID
    provider: str
    model: str
    prompt_version: str


class AIOutputEnvelope[ResultT: BaseModel](StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    task_type: str
    result: ResultT
    source_ids: list[uuid.UUID]
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_label: ConfidenceLabel
    limitations: list[str]
    warnings: list[str]
    requires_human_review: bool
    review_reasons: list[str]
    generated_at: datetime
    model_metadata: AIModelMetadata

    @model_validator(mode="after")
    def validate_confidence_label(self) -> AIOutputEnvelope[ResultT]:
        expected = (
            ConfidenceLabel.LOW
            if self.confidence < 0.5
            else ConfidenceLabel.MEDIUM
            if self.confidence < 0.8
            else ConfidenceLabel.HIGH
        )
        if self.confidence_label != expected:
            raise ValueError("confidence_label does not match confidence")
        return self


class ResearchQuestionParseEnvelope(AIOutputEnvelope[ResearchQuestionSpec]):
    task_type: Literal["RESEARCH_QUESTION_PARSE"]


class ResearchQuestionScopingEnvelope(AIOutputEnvelope[ResearchQuestionScopingOutput]):
    task_type: Literal["RESEARCH_QUESTION_SCOPING"]
