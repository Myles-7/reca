import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import ProjectMemberRole, ProjectStage, ProjectStatus, ProjectType


class ResponseMeta(BaseModel):
    request_id: str
    schema_version: str = "1.0"
    idempotency_replayed: bool = False


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ProjectPermissions(BaseModel):
    can_update: bool
    can_delete: bool


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    discipline: str | None = Field(default=None, max_length=100)
    research_direction: str | None = Field(default=None, max_length=200)
    project_type: ProjectType
    current_stage: ProjectStage = ProjectStage.INTENT
    expected_completion_date: date | None = None
    resource_constraints: dict[str, Any] | None = None
    ethical_constraints: dict[str, Any] | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    discipline: str | None = Field(default=None, max_length=100)
    research_direction: str | None = Field(default=None, max_length=200)
    project_type: ProjectType | None = None
    current_stage: ProjectStage | None = None
    expected_completion_date: date | None = None
    resource_constraints: dict[str, Any] | None = None
    ethical_constraints: dict[str, Any] | None = None


class ProjectPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str | None
    discipline: str | None
    research_direction: str | None
    project_type: ProjectType
    current_stage: ProjectStage
    status: ProjectStatus
    expected_completion_date: date | None
    resource_constraints: dict[str, Any] | None
    ethical_constraints: dict[str, Any] | None
    lock_version: int
    created_at: datetime
    updated_at: datetime
    permissions: ProjectPermissions
    allowed_actions: list[str]


class ProjectEnvelope(BaseModel):
    data: ProjectPublic
    meta: ResponseMeta


class ProjectListEnvelope(BaseModel):
    data: list[ProjectPublic]
    pagination: PaginationMeta
    meta: ResponseMeta


class MemberAdd(BaseModel):
    user_id: uuid.UUID
    role: ProjectMemberRole


class MemberUpdate(BaseModel):
    role: ProjectMemberRole
    transfer_ownership: bool = False
    previous_owner_role: ProjectMemberRole | None = None
    reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_transfer(self) -> MemberUpdate:
        if self.transfer_ownership:
            if self.role != ProjectMemberRole.OWNER:
                raise ValueError("ownership transfer requires role OWNER")
            if self.previous_owner_role not in {
                ProjectMemberRole.EDITOR,
                ProjectMemberRole.REVIEWER,
                ProjectMemberRole.VIEWER,
            }:
                raise ValueError("previous_owner_role must be a non-OWNER role")
            if not self.reason or not self.reason.strip():
                raise ValueError("ownership transfer requires reason")
        elif self.previous_owner_role is not None:
            raise ValueError("previous_owner_role is only valid for ownership transfer")
        return self


class MemberUserPublic(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None


class ProjectMemberPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user: MemberUserPublic
    role: ProjectMemberRole
    joined_at: datetime
    removed_at: datetime | None
    allowed_actions: list[str]


class MemberEnvelope(BaseModel):
    data: ProjectMemberPublic
    meta: ResponseMeta


class MemberTransferData(BaseModel):
    member: ProjectMemberPublic
    project_owner_id: uuid.UUID
    previous_owner: dict[str, Any]


class MemberTransferEnvelope(BaseModel):
    data: MemberTransferData
    meta: ResponseMeta


class MemberListEnvelope(BaseModel):
    data: list[ProjectMemberPublic]
    allowed_actions: list[str]
    pagination: PaginationMeta
    meta: ResponseMeta


class AuditActorPublic(BaseModel):
    type: str
    id: str | None
    display_name: str | None


class AuditTargetPublic(BaseModel):
    type: str
    id: uuid.UUID | None
    label: str | None


class AuditLogPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID | None
    actor: AuditActorPublic
    action: str
    target: AuditTargetPublic
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    reason: str | None
    outcome: str
    request_id: str | None
    job_id: uuid.UUID | None
    approval_id: uuid.UUID | None
    created_at: datetime


class AuditListEnvelope(BaseModel):
    data: list[AuditLogPublic]
    pagination: PaginationMeta
    meta: ResponseMeta


class FoundationCounts(BaseModel):
    members: int
    artifacts: int | None = None
    jobs_active: int | None = None
    approvals_pending: int | None = None
    audit_events: int


class CurrentResearchQuestionSummary(BaseModel):
    id: uuid.UUID
    current_version_id: uuid.UUID
    status: str


class ProjectOverviewPublic(BaseModel):
    project_id: uuid.UUID
    current_stage: ProjectStage
    module_availability: dict[str, str]
    current_research_question: CurrentResearchQuestionSummary | None = None
    foundation_counts: FoundationCounts
    counts: dict[str, int | None]
    pending_actions: list[dict[str, Any]]
    evidence_completeness: None = None
    recent_activity: list[AuditLogPublic]


class ProjectOverviewEnvelope(BaseModel):
    data: ProjectOverviewPublic
    meta: ResponseMeta
