import uuid
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any

from pydantic import EmailStr
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ProjectType(StrEnum):
    THESIS = "THESIS"
    COURSE = "COURSE"
    INNOVATION = "INNOVATION"
    RESEARCH = "RESEARCH"
    DEMO = "DEMO"


class ProjectStage(StrEnum):
    INTENT = "INTENT"
    LITERATURE = "LITERATURE"
    REVIEW = "REVIEW"
    TOPIC = "TOPIC"
    DATA = "DATA"
    ANALYSIS = "ANALYSIS"
    FIGURE = "FIGURE"
    MANUSCRIPT = "MANUSCRIPT"
    EVIDENCE = "EVIDENCE"
    EXPORT = "EXPORT"


class ProjectStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class ProjectMemberRole(StrEnum):
    OWNER = "OWNER"
    EDITOR = "EDITOR"
    REVIEWER = "REVIEWER"
    VIEWER = "VIEWER"


class AuditActorType(StrEnum):
    USER = "USER"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"
    WORKER = "WORKER"


class AuditOutcome(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DENIED = "DENIED"


class ApprovalType(StrEnum):
    RESEARCH_QUESTION_CONFIRMATION = "RESEARCH_QUESTION_CONFIRMATION"
    LITERATURE_DECISION_CONFIRMATION = "LITERATURE_DECISION_CONFIRMATION"
    LITERATURE_EXTRACTION_CONFIRMATION = "LITERATURE_EXTRACTION_CONFIRMATION"
    CLEANING_PLAN_APPROVAL = "CLEANING_PLAN_APPROVAL"
    VARIABLE_ROLE_CONFIRMATION = "VARIABLE_ROLE_CONFIRMATION"
    ANALYSIS_PLAN_APPROVAL = "ANALYSIS_PLAN_APPROVAL"
    FIGURE_CONFIRMATION = "FIGURE_CONFIRMATION"
    MANUSCRIPT_FIX_APPROVAL = "MANUSCRIPT_FIX_APPROVAL"
    CLAIM_CONFIRMATION = "CLAIM_CONFIRMATION"
    EXPORT_CONFIRMATION = "EXPORT_CONFIRMATION"


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"


class ArtifactType(StrEnum):
    PDF_DOCUMENT = "PDF_DOCUMENT"
    DATASET_FILE = "DATASET_FILE"
    MANUSCRIPT_DOCX = "MANUSCRIPT_DOCX"
    FIGURE_PNG = "FIGURE_PNG"
    FIGURE_SVG = "FIGURE_SVG"
    FIGURE_PDF = "FIGURE_PDF"
    ANALYSIS_CODE = "ANALYSIS_CODE"
    ANALYSIS_LOG = "ANALYSIS_LOG"
    JSON_RESULT = "JSON_RESULT"
    CSV_EXPORT = "CSV_EXPORT"
    XLSX_EXPORT = "XLSX_EXPORT"
    REPRO_PACKAGE = "REPRO_PACKAGE"
    MANIFEST = "MANIFEST"
    MODEL_OUTPUT = "MODEL_OUTPUT"
    OTHER = "OTHER"


class StorageProvider(StrEnum):
    MINIO = "MINIO"
    S3 = "S3"
    LOCAL = "LOCAL"


class ArtifactStatus(StrEnum):
    UPLOADING = "UPLOADING"
    AVAILABLE = "AVAILABLE"
    FAILED = "FAILED"
    DELETED = "DELETED"
    QUARANTINED = "QUARANTINED"


class ArtifactRelationType(StrEnum):
    DERIVED_FROM = "DERIVED_FROM"
    GENERATED_FROM = "GENERATED_FROM"
    PACKAGED_IN = "PACKAGED_IN"
    PREVIEW_OF = "PREVIEW_OF"
    REPLACEMENT_OF = "REPLACEMENT_OF"
    CODE_FOR = "CODE_FOR"
    LOG_FOR = "LOG_FOR"


class JobTaskType(StrEnum):
    DOCUMENT_PARSE = "DOCUMENT_PARSE"
    LITERATURE_EXTRACT = "LITERATURE_EXTRACT"
    DOCUMENT_EMBED = "DOCUMENT_EMBED"
    LITERATURE_SUMMARIZE = "LITERATURE_SUMMARIZE"
    DATASET_PROFILE = "DATASET_PROFILE"
    DATASET_TRANSFORM = "DATASET_TRANSFORM"
    ANALYSIS_RUN = "ANALYSIS_RUN"
    FIGURE_RENDER = "FIGURE_RENDER"
    MANUSCRIPT_CHECK = "MANUSCRIPT_CHECK"
    EVIDENCE_AUDIT = "EVIDENCE_AUDIT"
    REPRO_PACKAGE_EXPORT = "REPRO_PACKAGE_EXPORT"


class JobStatus(StrEnum):
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    DISPATCH_FAILED = "DISPATCH_FAILED"


class ModelInvocationStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class ModelDataAccessLevel(StrEnum):
    METADATA_ONLY = "METADATA_ONLY"
    REDACTED_CONTENT = "REDACTED_CONTENT"
    VERIFIED_EVIDENCE_ONLY = "VERIFIED_EVIDENCE_ONLY"
    APPROVED_FULL_CONTENT = "APPROVED_FULL_CONTENT"


class ResearchProject(SQLModel, table=True):
    __tablename__ = "research_projects"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True, ondelete="RESTRICT")
    name: str = Field(max_length=200)
    description: str | None = Field(default=None, sa_column=Column(Text))
    discipline: str | None = Field(default=None, max_length=100)
    research_direction: str | None = Field(default=None, max_length=200)
    project_type: ProjectType = Field(
        sa_column=Column(SAEnum(ProjectType, name="project_type"), nullable=False)
    )
    current_stage: ProjectStage = Field(
        default=ProjectStage.INTENT,
        sa_column=Column(SAEnum(ProjectStage, name="project_stage"), nullable=False),
    )
    status: ProjectStatus = Field(
        default=ProjectStatus.ACTIVE,
        sa_column=Column(SAEnum(ProjectStatus, name="project_status"), nullable=False),
    )
    expected_completion_date: date | None = None
    resource_constraints: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    ethical_constraints: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    current_research_question_version_id: uuid.UUID | None = None
    lock_version: int = Field(default=1, ge=1)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    deleted_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class ProjectMember(SQLModel, table=True):
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "user_id", name="uq_project_members_project_user"
        ),
        Index("ix_project_members_project_role", "project_id", "role"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="research_projects.id", index=True, ondelete="CASCADE"
    )
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True, ondelete="RESTRICT")
    role: ProjectMemberRole = Field(
        sa_column=Column(
            SAEnum(ProjectMemberRole, name="project_member_role"), nullable=False
        )
    )
    permissions: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    invited_by: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL"
    )
    joined_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    removed_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class Artifact(SQLModel, table=True):
    __tablename__ = "artifacts"
    __table_args__ = (
        CheckConstraint("size_bytes >= 0", name="ck_artifacts_size_nonnegative"),
        CheckConstraint(
            "sha256 ~ '^[0-9a-f]{64}$'", name="ck_artifacts_sha256_lower_hex"
        ),
        CheckConstraint(
            "NOT is_original OR is_immutable",
            name="ck_artifacts_original_immutable",
        ),
        Index("ix_artifacts_project_status", "project_id", "status"),
        Index("ix_artifacts_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="research_projects.id", index=True, ondelete="RESTRICT"
    )
    artifact_type: ArtifactType = Field(
        sa_column=Column(SAEnum(ArtifactType, name="artifact_type"), nullable=False)
    )
    filename: str = Field(max_length=255)
    original_filename: str | None = Field(default=None, max_length=255)
    storage_provider: StorageProvider = Field(
        default=StorageProvider.MINIO,
        sa_column=Column(
            SAEnum(StorageProvider, name="storage_provider"), nullable=False
        ),
    )
    storage_key: str = Field(max_length=512, unique=True)
    mime_type: str = Field(max_length=255)
    size_bytes: int = Field(sa_column=Column(BigInteger, nullable=False))
    sha256: str = Field(max_length=64, index=True)
    source_artifact_id: uuid.UUID | None = Field(
        default=None, foreign_key="artifacts.id", index=True, ondelete="RESTRICT"
    )
    is_original: bool
    is_immutable: bool = True
    status: ArtifactStatus = Field(
        default=ArtifactStatus.UPLOADING,
        sa_column=Column(
            SAEnum(ArtifactStatus, name="artifact_status"), nullable=False
        ),
    )
    artifact_metadata: dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSONB, nullable=True)
    )
    created_by: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", index=True, ondelete="SET NULL"
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    deleted_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class ArtifactRelation(SQLModel, table=True):
    __tablename__ = "artifact_relations"
    __table_args__ = (
        UniqueConstraint(
            "source_artifact_id",
            "target_artifact_id",
            "relation_type",
            name="uq_artifact_relations_source_target_type",
        ),
        CheckConstraint(
            "source_artifact_id <> target_artifact_id",
            name="ck_artifact_relations_not_self",
        ),
        Index("ix_artifact_relations_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="research_projects.id", index=True, ondelete="RESTRICT"
    )
    source_artifact_id: uuid.UUID = Field(
        foreign_key="artifacts.id", index=True, ondelete="RESTRICT"
    )
    target_artifact_id: uuid.UUID = Field(
        foreign_key="artifacts.id", index=True, ondelete="RESTRICT"
    )
    relation_type: ArtifactRelationType = Field(
        sa_column=Column(
            SAEnum(ArtifactRelationType, name="artifact_relation_type"),
            nullable=False,
        )
    )
    relation_metadata: dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSONB, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class ApprovalRecord(SQLModel, table=True):
    __tablename__ = "approval_records"
    __table_args__ = (
        CheckConstraint(
            "payload_hash ~ '^[0-9a-f]{64}$'",
            name="ck_approval_records_payload_hash",
        ),
        Index("ix_approval_records_project_status", "project_id", "status"),
        Index(
            "ix_approval_records_project_target",
            "project_id",
            "target_object_type",
            "target_object_id",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="research_projects.id", index=True, ondelete="RESTRICT"
    )
    approval_type: ApprovalType = Field(
        sa_column=Column(SAEnum(ApprovalType, name="approval_type"), nullable=False)
    )
    target_object_type: str = Field(max_length=100)
    target_object_id: uuid.UUID = Field(index=True)
    requested_by_actor_type: AuditActorType = Field(
        sa_column=Column(
            SAEnum(AuditActorType, name="audit_actor_type"), nullable=False
        )
    )
    requested_by_actor_id: str | None = Field(default=None, max_length=255)
    requested_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    status: ApprovalStatus = Field(
        default=ApprovalStatus.PENDING,
        sa_column=Column(
            SAEnum(ApprovalStatus, name="approval_status"), nullable=False
        ),
    )
    decision_by_user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", index=True, ondelete="SET NULL"
    )
    decision_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    decision_reason: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    payload_snapshot: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    payload_hash: str = Field(max_length=64, index=True)
    impact_summary: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    expires_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    supersedes_approval_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="approval_records.id",
        index=True,
        ondelete="RESTRICT",
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class ApprovalItem(SQLModel, table=True):
    __tablename__ = "approval_items"
    __table_args__ = (
        UniqueConstraint(
            "approval_record_id",
            "item_type",
            "item_id",
            name="uq_approval_items_record_item",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    approval_record_id: uuid.UUID = Field(
        foreign_key="approval_records.id", index=True, ondelete="CASCADE"
    )
    item_type: str = Field(max_length=100)
    item_id: uuid.UUID
    decision: str | None = Field(default=None, max_length=100)
    reason: str | None = Field(default=None, sa_column=Column(Text, nullable=True))


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="research_projects.id",
        index=True,
        ondelete="RESTRICT",
    )
    actor_type: AuditActorType = Field(
        sa_column=Column(
            SAEnum(AuditActorType, name="audit_actor_type"), nullable=False
        )
    )
    actor_id: str | None = Field(
        default=None, sa_column=Column(String(length=255), nullable=True)
    )
    action: str = Field(max_length=100, index=True)
    object_type: str = Field(max_length=100)
    object_id: uuid.UUID | None = Field(default=None, index=True)
    before_snapshot: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    after_snapshot: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    reason: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    request_id: str | None = Field(default=None, max_length=64, index=True)
    job_id: uuid.UUID | None = Field(default=None, index=True)
    approval_id: uuid.UUID | None = Field(default=None, index=True)
    outcome: AuditOutcome = Field(
        sa_column=Column(SAEnum(AuditOutcome, name="audit_outcome"), nullable=False)
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class IdempotencyRecord(SQLModel, table=True):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        Index(
            "uq_idempotency_scope_key",
            "actor_id",
            "project_id",
            "method",
            "path_template",
            "idempotency_key",
            unique=True,
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    actor_id: uuid.UUID = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    project_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="research_projects.id",
        index=True,
        ondelete="CASCADE",
    )
    method: str = Field(max_length=10)
    path_template: str = Field(max_length=255)
    idempotency_key: str = Field(max_length=255)
    request_hash: str = Field(max_length=64)
    response_status: int
    response_body: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    expires_at: datetime = Field(sa_type=DateTime(timezone=True))  # type: ignore


class Job(SQLModel, table=True):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(
            "progress_percent BETWEEN 0 AND 100",
            name="ck_jobs_progress_percent",
        ),
        CheckConstraint("retry_count >= 0", name="ck_jobs_retry_count"),
        CheckConstraint("max_retries >= 0", name="ck_jobs_max_retries"),
        CheckConstraint(
            "total_steps IS NULL OR total_steps >= 0",
            name="ck_jobs_total_steps",
        ),
        CheckConstraint(
            "completed_steps IS NULL OR completed_steps >= 0",
            name="ck_jobs_completed_steps",
        ),
        Index("ix_jobs_project_status", "project_id", "status"),
        Index("ix_jobs_project_created", "project_id", "created_at"),
        Index("ix_jobs_status_created", "status", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="research_projects.id", index=True, ondelete="RESTRICT"
    )
    task_type: JobTaskType = Field(
        sa_column=Column(SAEnum(JobTaskType, name="job_task_type"), nullable=False)
    )
    resource_type: str = Field(max_length=100)
    resource_id: uuid.UUID = Field(index=True)
    status: JobStatus = Field(
        default=JobStatus.DRAFT,
        sa_column=Column(SAEnum(JobStatus, name="job_status"), nullable=False),
    )
    idempotency_key: str = Field(max_length=255, index=True)
    progress_percent: int = Field(default=0)
    current_step: str | None = Field(default=None, max_length=255)
    total_steps: int | None = None
    completed_steps: int | None = None
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    celery_task_id: str | None = Field(default=None, max_length=255, index=True)
    requested_by_user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", index=True, ondelete="SET NULL"
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    queued_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    started_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    last_heartbeat_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    error_code: str | None = Field(default=None, max_length=100)
    error_message: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    retryable: bool = False


class ProcessingRun(SQLModel, table=True):
    __tablename__ = "processing_runs"
    __table_args__ = (
        UniqueConstraint(
            "job_id", "attempt_number", name="uq_processing_runs_job_attempt"
        ),
        CheckConstraint(
            "attempt_number >= 1", name="ck_processing_runs_attempt_number"
        ),
        CheckConstraint(
            "parameters_hash ~ '^[0-9a-f]{64}$'",
            name="ck_processing_runs_parameters_hash",
        ),
        CheckConstraint(
            "input_hash IS NULL OR input_hash ~ '^[0-9a-f]{64}$'",
            name="ck_processing_runs_input_hash",
        ),
        Index("ix_processing_runs_project_status", "project_id", "status"),
        Index("ix_processing_runs_job_created", "job_id", "started_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="research_projects.id", index=True, ondelete="RESTRICT"
    )
    job_id: uuid.UUID = Field(foreign_key="jobs.id", index=True, ondelete="RESTRICT")
    process_type: JobTaskType = Field(
        sa_column=Column(SAEnum(JobTaskType, name="job_task_type"), nullable=False)
    )
    input_object_type: str = Field(max_length=100)
    input_object_id: uuid.UUID = Field(index=True)
    input_hash: str | None = Field(default=None, max_length=64)
    parameters: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    parameters_hash: str = Field(max_length=64)
    attempt_number: int
    engine: str = Field(max_length=100)
    engine_version: str | None = Field(default=None, max_length=100)
    implementation_metadata: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    status: JobStatus = Field(
        default=JobStatus.RUNNING,
        sa_column=Column(SAEnum(JobStatus, name="job_status"), nullable=False),
    )
    output_object_type: str | None = Field(default=None, max_length=100)
    output_object_id: uuid.UUID | None = Field(default=None, index=True)
    log_artifact_id: uuid.UUID | None = Field(
        default=None, foreign_key="artifacts.id", index=True, ondelete="RESTRICT"
    )
    started_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class ModelInvocation(SQLModel, table=True):
    __tablename__ = "model_invocations"
    __table_args__ = (
        CheckConstraint(
            "prompt_content_hash ~ '^[0-9a-f]{64}$'",
            name="ck_model_invocations_prompt_hash",
        ),
        CheckConstraint(
            "input_hash ~ '^[0-9a-f]{64}$'",
            name="ck_model_invocations_input_hash",
        ),
        CheckConstraint(
            "output_hash IS NULL OR output_hash ~ '^[0-9a-f]{64}$'",
            name="ck_model_invocations_output_hash",
        ),
        CheckConstraint(
            "(status IN ('PENDING', 'RUNNING') AND output_hash IS NULL "
            "AND error_code IS NULL AND completed_at IS NULL) OR "
            "(status = 'SUCCEEDED' AND output_hash IS NOT NULL "
            "AND error_code IS NULL AND completed_at IS NOT NULL) OR "
            "(status = 'FAILED' AND error_code IS NOT NULL "
            "AND completed_at IS NOT NULL)",
            name="ck_model_invocations_outcome_fields",
        ),
        Index("ix_model_invocations_project_status", "project_id", "status"),
        Index("ix_model_invocations_prompt", "prompt_id", "prompt_version"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="research_projects.id", index=True, ondelete="RESTRICT"
    )
    request_id: str | None = Field(default=None, max_length=64, index=True)
    actor_type: AuditActorType = Field(
        sa_column=Column(
            SAEnum(AuditActorType, name="audit_actor_type"), nullable=False
        )
    )
    actor_id: str | None = Field(default=None, max_length=255)
    task_type: str = Field(max_length=100, index=True)
    prompt_id: str = Field(max_length=100)
    prompt_version: str = Field(max_length=50)
    prompt_content_hash: str = Field(max_length=64)
    input_schema_name: str = Field(max_length=100)
    input_schema_version: str = Field(max_length=50)
    output_schema_name: str = Field(max_length=100)
    output_schema_version: str = Field(max_length=50)
    provider: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    requested_data_access_level: ModelDataAccessLevel = Field(
        sa_column=Column(
            SAEnum(ModelDataAccessLevel, name="model_data_access_level"),
            nullable=False,
        )
    )
    max_allowed_data_access_level: ModelDataAccessLevel = Field(
        sa_column=Column(
            SAEnum(ModelDataAccessLevel, name="model_data_access_level"),
            nullable=False,
        )
    )
    effective_data_access_level: ModelDataAccessLevel = Field(
        sa_column=Column(
            SAEnum(ModelDataAccessLevel, name="model_data_access_level"),
            nullable=False,
        )
    )
    source_ids: list[str] = Field(sa_column=Column(JSONB, nullable=False))
    input_hash: str = Field(max_length=64)
    output_hash: str | None = Field(default=None, max_length=64)
    status: ModelInvocationStatus = Field(
        default=ModelInvocationStatus.PENDING,
        sa_column=Column(
            SAEnum(ModelInvocationStatus, name="model_invocation_status"),
            nullable=False,
        ),
    )
    error_code: str | None = Field(default=None, max_length=100)
    degradation: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    implementation_metadata: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    started_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
