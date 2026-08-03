import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import (
    ResearchGoal,
    ResearchQuestionStatus,
    ResearchQuestionVersionStatus,
    ResearchRelationshipType,
)


class ResearchQuestionVersionContent(BaseModel):
    raw_input: str
    normalized_question: str | None = None
    research_object: str | None = None
    population: str | None = None
    context: str | None = None
    independent_variables: list[str] | None = None
    dependent_variables: list[str] | None = None
    control_variables: list[str] | None = None
    research_goal: ResearchGoal | None = None
    relationship_type: ResearchRelationshipType | None = None
    method_preference: dict[str, Any] | None = None
    time_scope: dict[str, Any] | None = None
    region_scope: dict[str, Any] | None = None
    language_scope: dict[str, Any] | None = None
    resource_constraints: dict[str, Any] | None = None
    ethical_constraints: dict[str, Any] | None = None
    uncertainties: dict[str, Any] | None = None


class ResearchQuestionCreate(BaseModel):
    raw_input: str


class ResearchQuestionVersionFields(BaseModel):
    raw_input: str | None = None
    normalized_question: str | None = None
    research_object: str | None = None
    population: str | None = None
    context: str | None = None
    independent_variables: list[str] | None = None
    dependent_variables: list[str] | None = None
    control_variables: list[str] | None = None
    research_goal: ResearchGoal | None = None
    relationship_type: ResearchRelationshipType | None = None
    method_preference: dict[str, Any] | None = None
    time_scope: dict[str, Any] | None = None
    region_scope: dict[str, Any] | None = None
    language_scope: dict[str, Any] | None = None
    resource_constraints: dict[str, Any] | None = None
    ethical_constraints: dict[str, Any] | None = None
    uncertainties: dict[str, Any] | None = None

    @model_validator(mode="after")
    def require_change(self) -> ResearchQuestionVersionFields:
        if not self.model_fields_set:
            raise ValueError("at least one ResearchQuestion field is required")
        return self


class ResearchQuestionVersionUpdate(BaseModel):
    change_reason: str
    fields: ResearchQuestionVersionFields


class ResearchQuestionVersionCreate(BaseModel):
    based_on_version_id: uuid.UUID
    change_reason: str
    fields: ResearchQuestionVersionFields


class ResearchQuestionMarkReady(BaseModel):
    reason: str | None = None


class ResearchQuestionParseRequest(BaseModel):
    max_follow_up_questions: int = Field(default=3, ge=1, le=3)
    language: str = Field(default="zh-CN", min_length=2, max_length=20)


class ResponseMeta(BaseModel):
    request_id: str
    schema_version: str = "1.0"
    idempotency_replayed: bool = False


class ResearchQuestionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    status: ResearchQuestionStatus
    current_version_id: uuid.UUID | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ResearchQuestionVersionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    research_question_id: uuid.UUID
    project_id: uuid.UUID
    version_number: int
    raw_input: str
    normalized_question: str | None
    research_object: str | None
    population: str | None
    context: str | None
    independent_variables: list[str] | None
    dependent_variables: list[str] | None
    control_variables: list[str] | None
    research_goal: ResearchGoal | None
    relationship_type: ResearchRelationshipType | None
    method_preference: dict[str, Any] | None
    time_scope: dict[str, Any] | None
    region_scope: dict[str, Any] | None
    language_scope: dict[str, Any] | None
    resource_constraints: dict[str, Any] | None
    ethical_constraints: dict[str, Any] | None
    uncertainties: dict[str, Any] | None
    source_model_invocation_id: uuid.UUID | None
    status: ResearchQuestionVersionStatus
    created_by: uuid.UUID
    created_at: datetime
    is_current: bool
    allowed_actions: list[str]
    pending_approval_id: uuid.UUID | None = None
    pending_approval_status: str | None = None


class ResearchQuestionData(ResearchQuestionPublic):
    current_version: ResearchQuestionVersionPublic


class ResearchQuestionEnvelope(BaseModel):
    data: ResearchQuestionData
    meta: ResponseMeta


class CurrentResearchQuestionData(BaseModel):
    question: ResearchQuestionData | None
    allowed_actions: list[str]
    capability_availability: dict[str, str]


class CurrentResearchQuestionEnvelope(BaseModel):
    data: CurrentResearchQuestionData
    meta: ResponseMeta


class ResearchQuestionVersionEnvelope(BaseModel):
    data: ResearchQuestionVersionPublic
    meta: ResponseMeta


class ResearchQuestionVersionListEnvelope(BaseModel):
    data: list[ResearchQuestionVersionPublic]
    meta: ResponseMeta


class ApprovalReference(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    target_object_id: uuid.UUID
    status: str


class ApprovalReferenceEnvelope(BaseModel):
    data: ApprovalReference
    meta: ResponseMeta
