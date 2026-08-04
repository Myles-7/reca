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
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import UserDefinedType
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


class ResearchQuestionStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


class ResearchQuestionVersionStatus(StrEnum):
    DRAFT = "DRAFT"
    NEEDS_INPUT = "NEEDS_INPUT"
    READY = "READY"
    CONFIRMED = "CONFIRMED"
    SUPERSEDED = "SUPERSEDED"


class QueryPlanStatus(StrEnum):
    DRAFT = "DRAFT"


class LiteratureSourceType(StrEnum):
    OPENALEX = "OPENALEX"
    DOI_IMPORT = "DOI_IMPORT"
    USER_UPLOAD = "USER_UPLOAD"
    MANUAL = "MANUAL"
    CACHE = "CACHE"


class LiteratureVerificationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONFLICTED = "CONFLICTED"


class LiteratureDecisionStatus(StrEnum):
    INCLUDED = "INCLUDED"
    EXCLUDED = "EXCLUDED"
    UNCERTAIN = "UNCERTAIN"


class LiteratureFieldCode(StrEnum):
    TITLE = "TITLE"
    AUTHORS = "AUTHORS"
    YEAR = "YEAR"
    RESEARCH_OBJECT = "RESEARCH_OBJECT"
    SAMPLE_SIZE = "SAMPLE_SIZE"
    CORE_VARIABLES = "CORE_VARIABLES"
    RESEARCH_DESIGN = "RESEARCH_DESIGN"
    ANALYSIS_METHOD = "ANALYSIS_METHOD"
    MAIN_CONCLUSION = "MAIN_CONCLUSION"
    LIMITATION = "LIMITATION"


class ConfidenceLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class LiteratureExtractionStatus(StrEnum):
    DRAFT = "DRAFT"
    EXTRACTING = "EXTRACTING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFIRMED = "CONFIRMED"
    SUPERSEDED = "SUPERSEDED"
    INVALIDATED = "INVALIDATED"
    FAILED = "FAILED"


class FieldConfirmationStatus(StrEnum):
    UNREVIEWED = "UNREVIEWED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class FieldEvidenceStatus(StrEnum):
    UNASSESSED = "UNASSESSED"
    LOCATED = "LOCATED"
    LOCATION_UNCERTAIN = "LOCATION_UNCERTAIN"
    NO_LOCATED_EVIDENCE = "NO_LOCATED_EVIDENCE"


class EvidenceType(StrEnum):
    FIELD_SUPPORT = "FIELD_SUPPORT"
    CLAIM_SUPPORT = "CLAIM_SUPPORT"
    CLAIM_CONTRADICTION = "CLAIM_CONTRADICTION"
    METHOD_DESCRIPTION = "METHOD_DESCRIPTION"
    SAMPLE_DESCRIPTION = "SAMPLE_DESCRIPTION"
    LIMITATION = "LIMITATION"
    OTHER = "OTHER"


class LocationVerificationStatus(StrEnum):
    EXTRACTED = "EXTRACTED"
    LOCATED = "LOCATED"
    VERIFIED = "VERIFIED"
    LOCATION_UNCERTAIN = "LOCATION_UNCERTAIN"


class EvidenceReviewStatus(StrEnum):
    UNREVIEWED = "UNREVIEWED"
    REVIEWED = "REVIEWED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class ParserCoverage(StrEnum):
    UNKNOWN = "UNKNOWN"
    PARTIAL_TEXT = "PARTIAL_TEXT"
    FULL_TEXT = "FULL_TEXT"


class UserDeclaredReadScope(StrEnum):
    UNKNOWN = "UNKNOWN"
    ABSTRACT = "ABSTRACT"
    SECTIONS = "SECTIONS"
    FULL_TEXT_DECLARED = "FULL_TEXT_DECLARED"


class LiteratureDecisionReason(StrEnum):
    RELEVANT_OBJECT_AND_METHOD = "RELEVANT_OBJECT_AND_METHOD"
    OBJECT_MISMATCH = "OBJECT_MISMATCH"
    VARIABLE_MISMATCH = "VARIABLE_MISMATCH"
    METHOD_MISMATCH = "METHOD_MISMATCH"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    YEAR_MISMATCH = "YEAR_MISMATCH"
    DUPLICATE = "DUPLICATE"
    FULL_TEXT_UNAVAILABLE = "FULL_TEXT_UNAVAILABLE"
    QUALITY_ISSUE = "QUALITY_ISSUE"
    OTHER = "OTHER"


class TopicCandidateStatus(StrEnum):
    PROPOSED = "PROPOSED"
    SHORTLISTED = "SHORTLISTED"
    ADOPTED = "ADOPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TopicEvidenceRelation(StrEnum):
    BASIS = "BASIS"
    SUPPORT = "SUPPORT"
    CONTRADICTION = "CONTRADICTION"
    LIMITATION = "LIMITATION"


class DocumentType(StrEnum):
    SCHOLARLY_PDF = "SCHOLARLY_PDF"
    MANUSCRIPT = "MANUSCRIPT"
    OTHER = "OTHER"


class DocumentParserType(StrEnum):
    GROBID = "GROBID"
    PYPDF = "PYPDF"
    NONE = "NONE"


class DocumentParseConfidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class ResearchGoal(StrEnum):
    DESCRIBE = "DESCRIBE"
    COMPARE = "COMPARE"
    RELATE = "RELATE"
    PREDICT = "PREDICT"


class ResearchRelationshipType(StrEnum):
    ASSOCIATION = "ASSOCIATION"
    COMPARISON = "COMPARISON"
    PREDICTION = "PREDICTION"
    UNSPECIFIED = "UNSPECIFIED"


class VectorType(UserDefinedType[list[float]]):
    cache_ok = True

    def get_col_spec(self, **_kw: Any) -> str:
        return "VECTOR"


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


class DatasetSourceType(StrEnum):
    USER_UPLOAD = "USER_UPLOAD"
    PUBLIC_DATASET = "PUBLIC_DATASET"
    DEMO_DATASET = "DEMO_DATASET"
    MANUAL_ENTRY = "MANUAL_ENTRY"


class DatasetLicenseStatus(StrEnum):
    VERIFIED = "VERIFIED"
    DECLARED_BY_USER = "DECLARED_BY_USER"
    UNKNOWN = "UNKNOWN"
    RESTRICTED = "RESTRICTED"


class DatasetStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class DatasetVersionType(StrEnum):
    ORIGINAL = "ORIGINAL"
    CLEANED = "CLEANED"
    FILTERED = "FILTERED"
    TRANSFORMED = "TRANSFORMED"
    DERIVED = "DERIVED"


class DatasetFileFormat(StrEnum):
    CSV = "CSV"
    XLSX = "XLSX"


class DatasetVersionStatus(StrEnum):
    CREATING = "CREATING"
    VALIDATING = "VALIDATING"
    AVAILABLE = "AVAILABLE"
    FAILED = "FAILED"
    INVALIDATED = "INVALIDATED"
    DELETED = "DELETED"


class DatasetColumnType(StrEnum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    NUMERIC = "NUMERIC"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    DATETIME = "DATETIME"
    CATEGORY = "CATEGORY"
    UNKNOWN = "UNKNOWN"


class DatasetSemanticRole(StrEnum):
    ID = "ID"
    INDEPENDENT_VARIABLE = "INDEPENDENT_VARIABLE"
    DEPENDENT_VARIABLE = "DEPENDENT_VARIABLE"
    CONTROL_VARIABLE = "CONTROL_VARIABLE"
    GROUP_VARIABLE = "GROUP_VARIABLE"
    TIME_VARIABLE = "TIME_VARIABLE"
    WEIGHT = "WEIGHT"
    UNASSIGNED = "UNASSIGNED"


class DatasetColumnConfirmationStatus(StrEnum):
    UNCONFIRMED = "UNCONFIRMED"
    CONFIRMED = "CONFIRMED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class DataQualityRunStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    INVALIDATED = "INVALIDATED"


class DataQualityIssueType(StrEnum):
    MISSING_VALUE = "MISSING_VALUE"
    DUPLICATE_ROW = "DUPLICATE_ROW"
    DUPLICATE_ID = "DUPLICATE_ID"
    CONSTANT_COLUMN = "CONSTANT_COLUMN"
    MIXED_TYPE = "MIXED_TYPE"
    CATEGORY_INCONSISTENCY = "CATEGORY_INCONSISTENCY"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    EXTREME_VALUE = "EXTREME_VALUE"
    GROUP_IMBALANCE = "GROUP_IMBALANCE"
    SUSPICIOUS_UNIT = "SUSPICIOUS_UNIT"
    INVALID_DATE = "INVALID_DATE"
    POSSIBLE_SENSITIVE_FIELD = "POSSIBLE_SENSITIVE_FIELD"


class DataQualitySeverity(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    INFO = "INFO"


class DataQualityIssueStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PLANNED = "PLANNED"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"
    INVALIDATED = "INVALIDATED"


class CleaningPlanStatus(StrEnum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    NEEDS_INPUT = "NEEDS_INPUT"
    READY = "READY"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    INVALIDATED = "INVALIDATED"


class CleaningActionType(StrEnum):
    KEEP_ROWS = "KEEP_ROWS"
    DROP_ROWS = "DROP_ROWS"
    REPLACE_VALUE = "REPLACE_VALUE"
    MAP_CATEGORY = "MAP_CATEGORY"
    CAST_TYPE = "CAST_TYPE"
    MARK_MISSING = "MARK_MISSING"
    IMPUTE_VALUE = "IMPUTE_VALUE"
    CONVERT_UNIT = "CONVERT_UNIT"
    RENAME_COLUMN = "RENAME_COLUMN"
    CREATE_DERIVED_COLUMN = "CREATE_DERIVED_COLUMN"


class CleaningSelectorType(StrEnum):
    ALL_ROWS = "ALL_ROWS"
    ISSUE_ROWS = "ISSUE_ROWS"
    VALUE_EQUALS = "VALUE_EQUALS"
    VALUE_IN = "VALUE_IN"
    IS_NULL = "IS_NULL"
    IS_NOT_NULL = "IS_NOT_NULL"
    NUMERIC_RANGE = "NUMERIC_RANGE"


class CleaningRiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DataTransformationStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ArtifactRelationType(StrEnum):
    DERIVED_FROM = "DERIVED_FROM"
    GENERATED_FROM = "GENERATED_FROM"
    PACKAGED_IN = "PACKAGED_IN"
    PREVIEW_OF = "PREVIEW_OF"
    REPLACEMENT_OF = "REPLACEMENT_OF"
    CODE_FOR = "CODE_FOR"
    LOG_FOR = "LOG_FOR"


class JobTaskType(StrEnum):
    RESEARCH_QUESTION_SCOPING = "RESEARCH_QUESTION_SCOPING"
    QUERY_PLAN_GENERATION = "QUERY_PLAN_GENERATION"
    DOCUMENT_PARSE = "DOCUMENT_PARSE"
    LITERATURE_SEARCH = "LITERATURE_SEARCH"
    LITERATURE_EXTRACT = "LITERATURE_EXTRACT"
    DOCUMENT_EMBED = "DOCUMENT_EMBED"
    LITERATURE_SUMMARIZE = "LITERATURE_SUMMARIZE"
    TOPIC_GENERATE = "TOPIC_GENERATE"
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
    __table_args__ = (
        ForeignKeyConstraint(
            ["current_research_question_version_id", "id"],
            [
                "research_question_versions.id",
                "research_question_versions.project_id",
            ],
            name="fk_research_projects_current_rq_version_project",
            ondelete="RESTRICT",
            use_alter=True,
        ),
    )

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
        Index(
            "uq_project_members_active_owner",
            "project_id",
            unique=True,
            postgresql_where=text("role = 'OWNER' AND removed_at IS NULL"),
        ),
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


class ResearchQuestion(SQLModel, table=True):
    __tablename__ = "research_questions"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_research_questions_id_project"),
        ForeignKeyConstraint(
            ["current_version_id", "id", "project_id"],
            [
                "research_question_versions.id",
                "research_question_versions.research_question_id",
                "research_question_versions.project_id",
            ],
            name="fk_research_questions_current_version_scope",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        Index("ix_research_questions_project_status", "project_id", "status"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="research_projects.id", index=True, ondelete="RESTRICT"
    )
    status: ResearchQuestionStatus = Field(
        default=ResearchQuestionStatus.DRAFT,
        sa_column=Column(
            SAEnum(ResearchQuestionStatus, name="research_question_status"),
            nullable=False,
        ),
    )
    current_version_id: uuid.UUID | None = Field(default=None, index=True)
    created_by: uuid.UUID = Field(
        foreign_key="user.id", index=True, ondelete="RESTRICT"
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class ResearchQuestionVersion(SQLModel, table=True):
    __tablename__ = "research_question_versions"
    __table_args__ = (
        UniqueConstraint(
            "research_question_id",
            "version_number",
            name="uq_research_question_versions_question_number",
        ),
        UniqueConstraint(
            "id",
            "project_id",
            name="uq_research_question_versions_id_project",
        ),
        UniqueConstraint(
            "id",
            "research_question_id",
            "project_id",
            name="uq_research_question_versions_id_question_project",
        ),
        CheckConstraint(
            "version_number >= 1",
            name="ck_research_question_versions_number_positive",
        ),
        ForeignKeyConstraint(
            ["research_question_id", "project_id"],
            ["research_questions.id", "research_questions.project_id"],
            name="fk_research_question_versions_question_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["source_model_invocation_id", "project_id"],
            ["model_invocations.id", "model_invocations.project_id"],
            name="fk_research_question_versions_model_invocation_project",
            ondelete="RESTRICT",
        ),
        Index("ix_research_question_versions_project_status", "project_id", "status"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    research_question_id: uuid.UUID = Field(index=True)
    project_id: uuid.UUID = Field(index=True)
    version_number: int
    raw_input: str = Field(sa_column=Column(Text, nullable=False))
    normalized_question: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    research_object: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    population: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    context: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    independent_variables: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    dependent_variables: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    control_variables: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    research_goal: ResearchGoal | None = Field(
        default=None,
        sa_column=Column(SAEnum(ResearchGoal, name="research_goal"), nullable=True),
    )
    relationship_type: ResearchRelationshipType | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(ResearchRelationshipType, name="research_relationship_type"),
            nullable=True,
        ),
    )
    method_preference: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    time_scope: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    region_scope: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    language_scope: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    resource_constraints: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    ethical_constraints: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    uncertainties: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    source_model_invocation_id: uuid.UUID | None = Field(
        default=None,
        index=True,
    )
    status: ResearchQuestionVersionStatus = Field(
        default=ResearchQuestionVersionStatus.DRAFT,
        sa_column=Column(
            SAEnum(
                ResearchQuestionVersionStatus,
                name="research_question_version_status",
            ),
            nullable=False,
        ),
    )
    created_by: uuid.UUID = Field(
        foreign_key="user.id", index=True, ondelete="RESTRICT"
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class QueryPlan(SQLModel, table=True):
    __tablename__ = "query_plans"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_query_plans_id_project"),
        CheckConstraint("lock_version >= 1", name="ck_query_plans_lock_version"),
        ForeignKeyConstraint(
            ["research_question_version_id", "project_id"],
            ["research_question_versions.id", "research_question_versions.project_id"],
            name="fk_query_plans_rq_version_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["source_model_invocation_id", "project_id"],
            ["model_invocations.id", "model_invocations.project_id"],
            name="fk_query_plans_model_invocation_project",
            ondelete="RESTRICT",
        ),
        Index("ix_query_plans_project_created", "project_id", "created_at"),
        Index(
            "ix_query_plans_rq_version",
            "research_question_version_id",
            "created_at",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="research_projects.id", index=True, ondelete="RESTRICT"
    )
    research_question_version_id: uuid.UUID = Field(index=True)
    chinese_terms: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    english_terms: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    synonyms: dict[str, list[str]] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    object_terms: dict[str, list[str]] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    method_terms: dict[str, list[str]] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    boolean_query: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    filters: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    limitations: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    source_model_invocation_id: uuid.UUID | None = Field(default=None, index=True)
    status: QueryPlanStatus = Field(
        default=QueryPlanStatus.DRAFT,
        sa_column=Column(
            SAEnum(QueryPlanStatus, name="query_plan_status"), nullable=False
        ),
    )
    lock_version: int = Field(default=1, ge=1)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class LiteratureSearchRun(SQLModel, table=True):
    __tablename__ = "literature_search_runs"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_literature_search_runs_scope"),
        CheckConstraint(
            "result_count >= 0", name="ck_literature_search_runs_result_count"
        ),
        CheckConstraint(
            "query_fingerprint ~ '^[0-9a-f]{64}$'",
            name="ck_literature_search_runs_fingerprint",
        ),
        ForeignKeyConstraint(
            ["query_plan_id", "project_id"],
            ["query_plans.id", "query_plans.project_id"],
            name="fk_literature_search_runs_query_plan_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["cache_source_run_id", "project_id"],
            ["literature_search_runs.id", "literature_search_runs.project_id"],
            name="fk_literature_search_runs_cache_source_project",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_literature_search_runs_cache_lookup",
            "project_id",
            "query_fingerprint",
            "status",
            "fetched_at",
        ),
        Index("ix_literature_search_runs_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="research_projects.id", index=True, ondelete="RESTRICT"
    )
    query_plan_id: uuid.UUID = Field(index=True)
    provider: str = Field(max_length=100)
    provider_query: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    query_fingerprint: str = Field(max_length=64, index=True)
    result_count: int = Field(default=0, ge=0)
    cache_hit: bool = False
    cache_stale: bool = False
    cache_source_run_id: uuid.UUID | None = Field(default=None, index=True)
    degraded: bool = False
    limitations: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    fetched_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    status: JobStatus = Field(
        default=JobStatus.DRAFT,
        sa_column=Column(SAEnum(JobStatus, name="job_status"), nullable=False),
    )
    error_code: str | None = Field(default=None, max_length=100)
    job_id: uuid.UUID | None = Field(
        default=None, foreign_key="jobs.id", index=True, ondelete="RESTRICT"
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class LiteratureRecord(SQLModel, table=True):
    __tablename__ = "literature_records"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_literature_records_scope"),
        UniqueConstraint(
            "id",
            "project_id",
            "document_id",
            name="uq_literature_records_id_project_document",
        ),
        UniqueConstraint(
            "project_id",
            "normalized_doi",
            name="uq_literature_records_project_doi",
        ),
        CheckConstraint(
            "length(normalized_title) > 0",
            name="ck_literature_records_normalized_title",
        ),
        ForeignKeyConstraint(
            ["document_id", "project_id"],
            ["documents.id", "documents.project_id"],
            name="fk_literature_records_document_project",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_literature_records_project_title",
            "project_id",
            "normalized_title",
        ),
        Index("ix_literature_records_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="research_projects.id", index=True, ondelete="RESTRICT"
    )
    document_id: uuid.UUID | None = Field(default=None, index=True)
    source_type: LiteratureSourceType = Field(
        sa_column=Column(
            SAEnum(LiteratureSourceType, name="literature_source_type"),
            nullable=False,
        )
    )
    source_identifier: str | None = Field(default=None, max_length=500, index=True)
    title: str = Field(sa_column=Column(Text, nullable=False))
    normalized_title: str = Field(sa_column=Column(Text, nullable=False))
    abstract: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    publication_year: int | None = Field(default=None, ge=1, le=9999)
    journal_name: str | None = Field(default=None, max_length=500)
    doi: str | None = Field(default=None, max_length=500)
    normalized_doi: str | None = Field(default=None, max_length=500, index=True)
    authors_text: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    keywords: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    work_type: str | None = Field(default=None, max_length=100)
    open_access_status: str | None = Field(default=None, max_length=100)
    verification_status: LiteratureVerificationStatus = Field(
        default=LiteratureVerificationStatus.UNVERIFIED,
        sa_column=Column(
            SAEnum(
                LiteratureVerificationStatus,
                name="literature_verification_status",
            ),
            nullable=False,
        ),
    )
    raw_source_data: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    current_decision: LiteratureDecisionStatus = Field(
        default=LiteratureDecisionStatus.UNCERTAIN,
        sa_column=Column(
            SAEnum(LiteratureDecisionStatus, name="literature_decision_status"),
            nullable=False,
        ),
    )
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


class LiteratureSearchCandidate(SQLModel, table=True):
    __tablename__ = "literature_search_candidates"
    __table_args__ = (
        UniqueConstraint(
            "search_run_id",
            "source_identifier",
            name="uq_literature_candidates_run_source",
        ),
        CheckConstraint(
            "result_order >= 1", name="ck_literature_candidates_result_order"
        ),
        CheckConstraint(
            "length(normalized_title) > 0",
            name="ck_literature_candidates_normalized_title",
        ),
        ForeignKeyConstraint(
            ["search_run_id", "project_id"],
            ["literature_search_runs.id", "literature_search_runs.project_id"],
            name="fk_literature_candidates_run_project",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["imported_literature_record_id", "project_id"],
            ["literature_records.id", "literature_records.project_id"],
            name="fk_literature_candidates_import_project",
            ondelete="RESTRICT",
        ),
        Index("ix_literature_candidates_run_order", "search_run_id", "result_order"),
        Index("ix_literature_candidates_project_doi", "project_id", "normalized_doi"),
        Index(
            "ix_literature_candidates_project_title",
            "project_id",
            "normalized_title",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    search_run_id: uuid.UUID = Field(index=True)
    result_order: int = Field(ge=1)
    source_identifier: str = Field(max_length=500)
    title: str = Field(sa_column=Column(Text, nullable=False))
    normalized_title: str = Field(sa_column=Column(Text, nullable=False))
    abstract: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    publication_year: int | None = Field(default=None, ge=1, le=9999)
    journal_name: str | None = Field(default=None, max_length=500)
    doi: str | None = Field(default=None, max_length=500)
    normalized_doi: str | None = Field(default=None, max_length=500)
    authors_text: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    keywords: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    work_type: str | None = Field(default=None, max_length=100)
    open_access_status: str | None = Field(default=None, max_length=100)
    verification_status: LiteratureVerificationStatus = Field(
        default=LiteratureVerificationStatus.UNVERIFIED,
        sa_column=Column(
            SAEnum(
                LiteratureVerificationStatus,
                name="literature_verification_status",
            ),
            nullable=False,
        ),
    )
    raw_source_data: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    fetched_at: datetime = Field(sa_type=DateTime(timezone=True))  # type: ignore
    degraded: bool = False
    imported_literature_record_id: uuid.UUID | None = Field(default=None, index=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class Artifact(SQLModel, table=True):
    __tablename__ = "artifacts"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_artifacts_id_project"),
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


class Document(SQLModel, table=True):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_documents_id_project"),
        UniqueConstraint("artifact_id", name="uq_documents_artifact"),
        CheckConstraint(
            "page_count IS NULL OR page_count >= 1",
            name="ck_documents_page_count_positive",
        ),
        ForeignKeyConstraint(
            ["artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_documents_artifact_project",
            ondelete="RESTRICT",
        ),
        Index("ix_documents_project_status", "project_id", "parse_status"),
        Index("ix_documents_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="research_projects.id", index=True, ondelete="RESTRICT"
    )
    artifact_id: uuid.UUID = Field(index=True)
    document_type: DocumentType = Field(
        default=DocumentType.SCHOLARLY_PDF,
        sa_column=Column(SAEnum(DocumentType, name="document_type"), nullable=False),
    )
    parser_type: DocumentParserType | None = Field(
        default=DocumentParserType.NONE,
        sa_column=Column(
            SAEnum(DocumentParserType, name="document_parser_type"), nullable=True
        ),
    )
    parser_version: str | None = Field(default=None, max_length=100)
    parse_status: JobStatus = Field(
        default=JobStatus.DRAFT,
        sa_column=Column(SAEnum(JobStatus, name="job_status"), nullable=False),
    )
    page_count: int | None = Field(default=None, ge=1)
    language: str | None = Field(default=None, max_length=50)
    is_scanned: bool | None = None
    parse_confidence: DocumentParseConfidence | None = Field(
        default=DocumentParseConfidence.UNKNOWN,
        sa_column=Column(
            SAEnum(DocumentParseConfidence, name="document_parse_confidence"),
            nullable=True,
        ),
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class DocumentPage(SQLModel, table=True):
    __tablename__ = "document_pages"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "page_number", name="uq_document_pages_document_number"
        ),
        UniqueConstraint(
            "id",
            "document_id",
            "project_id",
            "page_number",
            name="uq_document_pages_id_document_project_number",
        ),
        CheckConstraint("page_number >= 1", name="ck_document_pages_number_positive"),
        CheckConstraint(
            "width IS NULL OR width > 0", name="ck_document_pages_width_positive"
        ),
        CheckConstraint(
            "height IS NULL OR height > 0", name="ck_document_pages_height_positive"
        ),
        ForeignKeyConstraint(
            ["document_id", "project_id"],
            ["documents.id", "documents.project_id"],
            name="fk_document_pages_document_project",
            ondelete="CASCADE",
        ),
        Index("ix_document_pages_project_document", "project_id", "document_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(index=True)
    project_id: uuid.UUID = Field(index=True)
    page_number: int = Field(ge=1)
    printed_page_label: str | None = Field(default=None, max_length=100)
    text_content: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    width: float | None = Field(default=None, gt=0)
    height: float | None = Field(default=None, gt=0)
    parser_metadata: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "document_id",
            "project_id",
            name="uq_document_chunks_id_document_project",
        ),
        CheckConstraint("page_start >= 1", name="ck_document_chunks_page_start"),
        CheckConstraint("page_end >= page_start", name="ck_document_chunks_page_range"),
        CheckConstraint("chunk_index >= 0", name="ck_document_chunks_index"),
        CheckConstraint(
            "content_hash ~ '^[0-9a-f]{64}$'",
            name="ck_document_chunks_content_hash",
        ),
        ForeignKeyConstraint(
            ["document_id", "project_id"],
            ["documents.id", "documents.project_id"],
            name="fk_document_chunks_document_project",
            ondelete="CASCADE",
        ),
        Index("ix_document_chunks_project_document", "project_id", "document_id"),
        Index("ix_document_chunks_document_index", "document_id", "chunk_index"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    document_id: uuid.UUID = Field(index=True)
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    section_path: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    chunk_index: int = Field(ge=0)
    content: str = Field(sa_column=Column(Text, nullable=False))
    content_hash: str = Field(max_length=64)
    token_count: int | None = Field(default=None, ge=0)
    embedding: list[float] | None = Field(
        default=None, sa_column=Column(VectorType(), nullable=True)
    )
    embedding_model: str | None = Field(default=None, max_length=200)
    embedding_version: str | None = Field(default=None, max_length=100)
    chunk_metadata: dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSONB, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class LiteratureExtraction(SQLModel, table=True):
    __tablename__ = "literature_extractions"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_literature_extractions_scope"),
        UniqueConstraint(
            "literature_record_id",
            "extraction_version",
            name="uq_literature_extractions_record_version",
        ),
        CheckConstraint(
            "extraction_version >= 1",
            name="ck_literature_extractions_version_positive",
        ),
        CheckConstraint("lock_version >= 1", name="ck_literature_extractions_lock"),
        ForeignKeyConstraint(
            ["literature_record_id", "project_id", "document_id"],
            [
                "literature_records.id",
                "literature_records.project_id",
                "literature_records.document_id",
            ],
            name="fk_literature_extractions_record_document_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["source_model_invocation_id", "project_id"],
            ["model_invocations.id", "model_invocations.project_id"],
            name="fk_literature_extractions_model_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["processing_run_id", "project_id"],
            ["processing_runs.id", "processing_runs.project_id"],
            name="fk_literature_extractions_run_project",
            ondelete="RESTRICT",
        ),
        Index("ix_literature_extractions_project_status", "project_id", "status"),
        Index(
            "ix_literature_extractions_record_created",
            "literature_record_id",
            "created_at",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    literature_record_id: uuid.UUID = Field(index=True)
    document_id: uuid.UUID = Field(index=True)
    extraction_version: int = Field(ge=1)
    schema_version: str = Field(max_length=50)
    status: LiteratureExtractionStatus = Field(
        default=LiteratureExtractionStatus.DRAFT,
        sa_column=Column(
            SAEnum(
                LiteratureExtractionStatus,
                name="literature_extraction_status",
            ),
            nullable=False,
        ),
    )
    overall_confidence: ConfidenceLevel | None = Field(
        default=None,
        sa_column=Column(SAEnum(ConfidenceLevel, name="confidence_level")),
    )
    source_model_invocation_id: uuid.UUID | None = Field(default=None, index=True)
    processing_run_id: uuid.UUID | None = Field(default=None, index=True)
    document_level_limitations: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    lock_version: int = Field(default=1, ge=1)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    confirmed_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class EvidenceSpan(SQLModel, table=True):
    __tablename__ = "evidence_spans"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_evidence_spans_scope"),
        CheckConstraint("page_number >= 1", name="ck_evidence_spans_page_positive"),
        CheckConstraint(
            "length(source_text) > 0", name="ck_evidence_spans_source_nonempty"
        ),
        CheckConstraint(
            "source_text_hash ~ '^[0-9a-f]{64}$'",
            name="ck_evidence_spans_source_hash",
        ),
        CheckConstraint(
            "(char_start IS NULL AND char_end IS NULL) OR "
            "(char_start >= 0 AND char_end > char_start)",
            name="ck_evidence_spans_char_range",
        ),
        CheckConstraint(
            "confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1",
            name="ck_evidence_spans_confidence",
        ),
        CheckConstraint(
            "bounding_boxes IS NULL OR jsonb_typeof(bounding_boxes) = 'array'",
            name="ck_evidence_spans_boxes_array",
        ),
        ForeignKeyConstraint(
            ["document_id", "project_id"],
            ["documents.id", "documents.project_id"],
            name="fk_evidence_spans_document_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["document_page_id", "document_id", "project_id", "page_number"],
            [
                "document_pages.id",
                "document_pages.document_id",
                "document_pages.project_id",
                "document_pages.page_number",
            ],
            name="fk_evidence_spans_page_document_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["chunk_id", "document_id", "project_id"],
            [
                "document_chunks.id",
                "document_chunks.document_id",
                "document_chunks.project_id",
            ],
            name="fk_evidence_spans_chunk_document_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["model_invocation_id", "project_id"],
            ["model_invocations.id", "model_invocations.project_id"],
            name="fk_evidence_spans_model_project",
            ondelete="RESTRICT",
        ),
        Index("ix_evidence_spans_project_document", "project_id", "document_id"),
        Index("ix_evidence_spans_document_page", "document_id", "page_number"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    document_id: uuid.UUID = Field(index=True)
    document_page_id: uuid.UUID | None = Field(default=None, index=True)
    chunk_id: uuid.UUID | None = Field(default=None, index=True)
    page_number: int = Field(ge=1)
    section_path: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    source_text: str = Field(sa_column=Column(Text, nullable=False))
    context_before: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    context_after: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    bounding_boxes: list[dict[str, Any]] | None = Field(
        default=None,
        sa_column=Column(JSONB(none_as_null=True), nullable=True),
    )
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=1)
    evidence_type: EvidenceType = Field(
        sa_column=Column(SAEnum(EvidenceType, name="evidence_type"), nullable=False)
    )
    confidence_level: ConfidenceLevel | None = Field(
        default=None,
        sa_column=Column(SAEnum(ConfidenceLevel, name="confidence_level")),
    )
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    parser_type: DocumentParserType | None = Field(
        default=None,
        sa_column=Column(SAEnum(DocumentParserType, name="document_parser_type")),
    )
    parser_version: str | None = Field(default=None, max_length=100)
    model_invocation_id: uuid.UUID | None = Field(default=None, index=True)
    source_text_hash: str = Field(max_length=64)
    location_verification_status: LocationVerificationStatus = Field(
        default=LocationVerificationStatus.EXTRACTED,
        sa_column=Column(
            SAEnum(
                LocationVerificationStatus,
                name="location_verification_status",
            ),
            nullable=False,
        ),
    )
    review_status: EvidenceReviewStatus = Field(
        default=EvidenceReviewStatus.UNREVIEWED,
        sa_column=Column(
            SAEnum(EvidenceReviewStatus, name="evidence_review_status"),
            nullable=False,
        ),
    )
    parser_coverage: ParserCoverage = Field(
        default=ParserCoverage.UNKNOWN,
        sa_column=Column(
            SAEnum(ParserCoverage, name="parser_coverage"), nullable=False
        ),
    )
    user_declared_read_scope: UserDeclaredReadScope = Field(
        default=UserDeclaredReadScope.UNKNOWN,
        sa_column=Column(
            SAEnum(UserDeclaredReadScope, name="user_declared_read_scope"),
            nullable=False,
        ),
    )
    reviewed_by_actor_type: AuditActorType | None = Field(
        default=None,
        sa_column=Column(SAEnum(AuditActorType, name="audit_actor_type")),
    )
    reviewed_by_actor_id: str | None = Field(default=None, max_length=255)
    reviewed_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    verified_by_actor_id: str | None = Field(default=None, max_length=255)
    verified_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    invalidated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class LiteratureExtractionField(SQLModel, table=True):
    __tablename__ = "literature_extraction_fields"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_extraction_fields_scope"),
        UniqueConstraint(
            "extraction_id", "field_code", name="uq_extraction_fields_code"
        ),
        CheckConstraint("lock_version >= 1", name="ck_extraction_fields_lock"),
        CheckConstraint(
            "confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1",
            name="ck_extraction_fields_confidence",
        ),
        CheckConstraint(
            "(evidence_status IN ('LOCATED', 'LOCATION_UNCERTAIN') "
            "AND evidence_span_id IS NOT NULL) OR "
            "(evidence_status NOT IN ('LOCATED', 'LOCATION_UNCERTAIN'))",
            name="ck_extraction_fields_located_span",
        ),
        CheckConstraint(
            "evidence_status <> 'NO_LOCATED_EVIDENCE' OR evidence_span_id IS NULL",
            name="ck_extraction_fields_no_evidence_span",
        ),
        CheckConstraint(
            "evidence_status NOT IN ('LOCATION_UNCERTAIN', 'NO_LOCATED_EVIDENCE') "
            "OR (evidence_limitations IS NOT NULL AND length(evidence_limitations) > 0)",
            name="ck_extraction_fields_evidence_limitations",
        ),
        ForeignKeyConstraint(
            ["extraction_id", "project_id"],
            ["literature_extractions.id", "literature_extractions.project_id"],
            name="fk_extraction_fields_extraction_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["evidence_span_id", "project_id"],
            ["evidence_spans.id", "evidence_spans.project_id"],
            name="fk_extraction_fields_span_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["corrected_by_user_id"],
            ["user.id"],
            name="fk_extraction_fields_corrector",
            ondelete="RESTRICT",
        ),
        Index("ix_extraction_fields_project_code", "project_id", "field_code"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    extraction_id: uuid.UUID = Field(index=True)
    field_code: LiteratureFieldCode = Field(
        sa_column=Column(
            SAEnum(LiteratureFieldCode, name="literature_field_code"), nullable=False
        )
    )
    model_value_text: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    model_value_json: dict[str, Any] | list[Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    value_text: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    value_json: dict[str, Any] | list[Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    confidence_level: ConfidenceLevel = Field(
        default=ConfidenceLevel.UNKNOWN,
        sa_column=Column(
            SAEnum(ConfidenceLevel, name="confidence_level"), nullable=False
        ),
    )
    evidence_span_id: uuid.UUID | None = Field(default=None, index=True)
    confirmation_status: FieldConfirmationStatus = Field(
        default=FieldConfirmationStatus.UNREVIEWED,
        sa_column=Column(
            SAEnum(FieldConfirmationStatus, name="field_confirmation_status"),
            nullable=False,
        ),
    )
    evidence_status: FieldEvidenceStatus = Field(
        default=FieldEvidenceStatus.UNASSESSED,
        sa_column=Column(
            SAEnum(FieldEvidenceStatus, name="field_evidence_status"), nullable=False
        ),
    )
    evidence_limitations: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    corrected_by_user_id: uuid.UUID | None = Field(default=None, index=True)
    correction_reason: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    lock_version: int = Field(default=1, ge=1)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class LiteratureExtractionFieldRevision(SQLModel, table=True):
    __tablename__ = "literature_extraction_field_revisions"
    __table_args__ = (
        UniqueConstraint(
            "field_id", "revision_number", name="uq_field_revisions_number"
        ),
        CheckConstraint("revision_number >= 1", name="ck_field_revisions_number"),
        ForeignKeyConstraint(
            ["field_id", "project_id"],
            [
                "literature_extraction_fields.id",
                "literature_extraction_fields.project_id",
            ],
            name="fk_field_revisions_field_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["old_evidence_span_id", "project_id"],
            ["evidence_spans.id", "evidence_spans.project_id"],
            name="fk_field_revisions_old_span_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["new_evidence_span_id", "project_id"],
            ["evidence_spans.id", "evidence_spans.project_id"],
            name="fk_field_revisions_new_span_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["source_model_invocation_id", "project_id"],
            ["model_invocations.id", "model_invocations.project_id"],
            name="fk_field_revisions_model_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["corrected_by_user_id"],
            ["user.id"],
            name="fk_field_revisions_corrector",
            ondelete="RESTRICT",
        ),
        Index("ix_field_revisions_project", "project_id"),
        Index("ix_field_revisions_old_span", "old_evidence_span_id"),
        Index("ix_field_revisions_new_span", "new_evidence_span_id"),
        Index("ix_field_revisions_corrector", "corrected_by_user_id"),
        Index("ix_field_revisions_model", "source_model_invocation_id"),
        Index("ix_field_revisions_field_created", "field_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID
    field_id: uuid.UUID
    revision_number: int = Field(ge=1)
    old_value_text: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    old_value_json: dict[str, Any] | list[Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    new_value_text: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    new_value_json: dict[str, Any] | list[Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    old_evidence_span_id: uuid.UUID | None = None
    new_evidence_span_id: uuid.UUID | None = None
    old_confirmation_status: FieldConfirmationStatus = Field(
        sa_column=Column(
            SAEnum(FieldConfirmationStatus, name="field_confirmation_status"),
            nullable=False,
        )
    )
    new_confirmation_status: FieldConfirmationStatus = Field(
        sa_column=Column(
            SAEnum(FieldConfirmationStatus, name="field_confirmation_status"),
            nullable=False,
        )
    )
    old_evidence_status: FieldEvidenceStatus = Field(
        sa_column=Column(
            SAEnum(FieldEvidenceStatus, name="field_evidence_status"), nullable=False
        )
    )
    new_evidence_status: FieldEvidenceStatus = Field(
        sa_column=Column(
            SAEnum(FieldEvidenceStatus, name="field_evidence_status"), nullable=False
        )
    )
    corrected_by_user_id: uuid.UUID
    correction_reason: str = Field(sa_column=Column(Text, nullable=False))
    source_model_invocation_id: uuid.UUID | None = None
    ai_schema_version: str | None = Field(default=None, max_length=50)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class EvidenceSpanVerificationRecord(SQLModel, table=True):
    __tablename__ = "evidence_span_verification_records"
    __table_args__ = (
        CheckConstraint(
            "source_text_hash ~ '^[0-9a-f]{64}$'",
            name="ck_span_verifications_source_hash",
        ),
        CheckConstraint(
            "jsonb_typeof(reviewed_page_numbers) = 'array'",
            name="ck_span_verifications_pages_array",
        ),
        CheckConstraint(
            "location_verification_status <> 'VERIFIED' "
            "OR jsonb_array_length(reviewed_page_numbers) > 0",
            name="ck_span_verifications_verified_pages",
        ),
        ForeignKeyConstraint(
            ["evidence_span_id", "project_id"],
            ["evidence_spans.id", "evidence_spans.project_id"],
            name="fk_span_verifications_span_project",
            ondelete="RESTRICT",
        ),
        Index("ix_span_verifications_span_created", "evidence_span_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    evidence_span_id: uuid.UUID = Field(index=True)
    actor_type: AuditActorType = Field(
        sa_column=Column(
            SAEnum(AuditActorType, name="audit_actor_type"), nullable=False
        )
    )
    actor_id: str = Field(max_length=255)
    location_verification_status: LocationVerificationStatus = Field(
        sa_column=Column(
            SAEnum(
                LocationVerificationStatus,
                name="location_verification_status",
            ),
            nullable=False,
        )
    )
    user_declared_read_scope: UserDeclaredReadScope = Field(
        sa_column=Column(
            SAEnum(UserDeclaredReadScope, name="user_declared_read_scope"),
            nullable=False,
        )
    )
    reviewed_page_numbers: list[int] = Field(sa_column=Column(JSONB, nullable=False))
    note: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    source_text_hash: str = Field(max_length=64)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class LiteratureDecision(SQLModel, table=True):
    __tablename__ = "literature_decisions"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "project_id",
            "literature_record_id",
            name="uq_literature_decisions_scope",
        ),
        UniqueConstraint(
            "supersedes_decision_id", name="uq_literature_decisions_successor"
        ),
        CheckConstraint(
            "ai_score IS NULL OR ai_score BETWEEN 0 AND 1",
            name="ck_literature_decisions_ai_score",
        ),
        ForeignKeyConstraint(
            ["literature_record_id", "project_id"],
            ["literature_records.id", "literature_records.project_id"],
            name="fk_literature_decisions_record_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["supersedes_decision_id", "project_id", "literature_record_id"],
            [
                "literature_decisions.id",
                "literature_decisions.project_id",
                "literature_decisions.literature_record_id",
            ],
            name="fk_literature_decisions_supersedes_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["decided_by_user_id"],
            ["user.id"],
            name="fk_literature_decisions_user",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_literature_decisions_record_created",
            "literature_record_id",
            "created_at",
        ),
        Index(
            "uq_literature_decisions_initial",
            "project_id",
            "literature_record_id",
            unique=True,
            postgresql_where=text("supersedes_decision_id IS NULL"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    literature_record_id: uuid.UUID = Field(index=True)
    decision: LiteratureDecisionStatus = Field(
        sa_column=Column(
            SAEnum(LiteratureDecisionStatus, name="literature_decision_status"),
            nullable=False,
        )
    )
    reason_code: LiteratureDecisionReason | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(LiteratureDecisionReason, name="literature_decision_reason")
        ),
    )
    reason_text: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    ai_recommendation: LiteratureDecisionStatus | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(LiteratureDecisionStatus, name="literature_decision_status")
        ),
    )
    ai_score: float | None = Field(default=None, ge=0, le=1)
    decided_by_user_id: uuid.UUID = Field(index=True)
    supersedes_decision_id: uuid.UUID | None = Field(default=None, index=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class EvidenceSetSummary(SQLModel, table=True):
    __tablename__ = "evidence_set_summaries"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_evidence_set_summaries_scope"),
        CheckConstraint(
            "jsonb_typeof(included_literature_ids) = 'array'",
            name="ck_evidence_summaries_literature_array",
        ),
        CheckConstraint(
            "jsonb_typeof(result_payload) = 'object'",
            name="ck_evidence_summaries_result_object",
        ),
        ForeignKeyConstraint(
            ["job_id", "project_id"],
            ["jobs.id", "jobs.project_id"],
            name="fk_evidence_summaries_job_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["processing_run_id", "project_id"],
            ["processing_runs.id", "processing_runs.project_id"],
            name="fk_evidence_summaries_run_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["source_model_invocation_id", "project_id"],
            ["model_invocations.id", "model_invocations.project_id"],
            name="fk_evidence_summaries_model_project",
            ondelete="RESTRICT",
        ),
        Index("ix_evidence_summaries_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    included_literature_ids: list[str] = Field(sa_column=Column(JSONB, nullable=False))
    scope_statement: str = Field(sa_column=Column(Text, nullable=False))
    result_payload: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    job_id: uuid.UUID | None = Field(default=None, index=True)
    processing_run_id: uuid.UUID | None = Field(default=None, index=True)
    source_model_invocation_id: uuid.UUID | None = Field(default=None, index=True)
    status: JobStatus = Field(
        default=JobStatus.DRAFT,
        sa_column=Column(SAEnum(JobStatus, name="job_status"), nullable=False),
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class TopicGenerationRun(SQLModel, table=True):
    __tablename__ = "topic_generation_runs"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_topic_generation_runs_scope"),
        ForeignKeyConstraint(
            ["research_question_version_id", "project_id"],
            ["research_question_versions.id", "research_question_versions.project_id"],
            name="fk_topic_runs_rq_version_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["evidence_summary_id", "project_id"],
            ["evidence_set_summaries.id", "evidence_set_summaries.project_id"],
            name="fk_topic_runs_summary_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["job_id", "project_id"],
            ["jobs.id", "jobs.project_id"],
            name="fk_topic_runs_job_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["processing_run_id", "project_id"],
            ["processing_runs.id", "processing_runs.project_id"],
            name="fk_topic_runs_processing_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["source_model_invocation_id", "project_id"],
            ["model_invocations.id", "model_invocations.project_id"],
            name="fk_topic_runs_model_project",
            ondelete="RESTRICT",
        ),
        Index("ix_topic_runs_project_status", "project_id", "status"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    research_question_version_id: uuid.UUID = Field(index=True)
    evidence_summary_id: uuid.UUID | None = Field(default=None, index=True)
    user_constraints: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    job_id: uuid.UUID | None = Field(default=None, index=True)
    processing_run_id: uuid.UUID | None = Field(default=None, index=True)
    source_model_invocation_id: uuid.UUID | None = Field(default=None, index=True)
    status: JobStatus = Field(
        default=JobStatus.DRAFT,
        sa_column=Column(SAEnum(JobStatus, name="job_status"), nullable=False),
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class TopicCandidate(SQLModel, table=True):
    __tablename__ = "topic_candidates"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_topic_candidates_scope"),
        UniqueConstraint(
            "topic_generation_run_id",
            "candidate_order",
            name="uq_topic_candidates_run_order",
        ),
        CheckConstraint(
            "candidate_order BETWEEN 1 AND 3", name="ck_topic_candidates_order"
        ),
        CheckConstraint(
            "length(question_text) > 0", name="ck_topic_candidates_question_nonempty"
        ),
        ForeignKeyConstraint(
            ["topic_generation_run_id", "project_id"],
            ["topic_generation_runs.id", "topic_generation_runs.project_id"],
            name="fk_topic_candidates_run_project",
            ondelete="RESTRICT",
        ),
        Index("ix_topic_candidates_project_status", "project_id", "status"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    topic_generation_run_id: uuid.UUID = Field(index=True)
    candidate_order: int = Field(ge=1, le=3)
    question_text: str = Field(sa_column=Column(Text, nullable=False))
    research_object: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    variables: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    research_goal: str | None = Field(default=None, max_length=100)
    literature_basis: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    possible_innovation: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    data_requirements: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    recommended_method: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    literature_basis_level: ConfidenceLevel | None = Field(
        default=None, sa_column=Column(SAEnum(ConfidenceLevel, name="confidence_level"))
    )
    data_availability: ConfidenceLevel | None = Field(
        default=None, sa_column=Column(SAEnum(ConfidenceLevel, name="confidence_level"))
    )
    method_difficulty: ConfidenceLevel | None = Field(
        default=None, sa_column=Column(SAEnum(ConfidenceLevel, name="confidence_level"))
    )
    time_feasibility: ConfidenceLevel | None = Field(
        default=None, sa_column=Column(SAEnum(ConfidenceLevel, name="confidence_level"))
    )
    ethical_risk: ConfidenceLevel | None = Field(
        default=None, sa_column=Column(SAEnum(ConfidenceLevel, name="confidence_level"))
    )
    major_risks: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    limitations: list[str] = Field(
        default_factory=list, sa_column=Column(JSONB, nullable=False)
    )
    supervisor_confirmation_items: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    status: TopicCandidateStatus = Field(
        default=TopicCandidateStatus.PROPOSED,
        sa_column=Column(
            SAEnum(TopicCandidateStatus, name="topic_candidate_status"), nullable=False
        ),
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class TopicCandidateEvidence(SQLModel, table=True):
    __tablename__ = "topic_candidate_evidence"
    __table_args__ = (
        CheckConstraint(
            "(literature_record_id IS NOT NULL)::integer + "
            "(evidence_span_id IS NOT NULL)::integer = 1",
            name="ck_topic_candidate_evidence_one_source",
        ),
        ForeignKeyConstraint(
            ["topic_candidate_id", "project_id"],
            ["topic_candidates.id", "topic_candidates.project_id"],
            name="fk_topic_candidate_evidence_candidate_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["literature_record_id", "project_id"],
            ["literature_records.id", "literature_records.project_id"],
            name="fk_topic_candidate_evidence_record_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["evidence_span_id", "project_id"],
            ["evidence_spans.id", "evidence_spans.project_id"],
            name="fk_topic_candidate_evidence_span_project",
            ondelete="RESTRICT",
        ),
        Index("ix_topic_candidate_evidence_candidate", "topic_candidate_id"),
        Index(
            "uq_topic_candidate_evidence_record",
            "topic_candidate_id",
            "literature_record_id",
            "relation_type",
            unique=True,
            postgresql_where=text("literature_record_id IS NOT NULL"),
        ),
        Index(
            "uq_topic_candidate_evidence_span",
            "topic_candidate_id",
            "evidence_span_id",
            "relation_type",
            unique=True,
            postgresql_where=text("evidence_span_id IS NOT NULL"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    topic_candidate_id: uuid.UUID = Field(index=True)
    literature_record_id: uuid.UUID | None = Field(default=None, index=True)
    evidence_span_id: uuid.UUID | None = Field(default=None, index=True)
    relation_type: TopicEvidenceRelation = Field(
        sa_column=Column(
            SAEnum(TopicEvidenceRelation, name="topic_evidence_relation"),
            nullable=False,
        )
    )
    explanation: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
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
        UniqueConstraint("id", "project_id", name="uq_approval_records_id_project"),
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
        ForeignKeyConstraint(
            ["approval_id"],
            ["approval_records.id"],
            name="fk_audit_logs_approval_id_approval_records",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["model_invocation_id", "project_id"],
            ["model_invocations.id", "model_invocations.project_id"],
            name="fk_audit_logs_model_invocation_project",
            ondelete="RESTRICT",
        ),
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
    model_invocation_id: uuid.UUID | None = Field(default=None, index=True)
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


class Dataset(SQLModel, table=True):
    __tablename__ = "datasets"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_datasets_id_project"),
        UniqueConstraint(
            "project_id", "id", "current_version_id", name="uq_datasets_current_scope"
        ),
        ForeignKeyConstraint(
            ["project_id", "id", "current_version_id"],
            [
                "dataset_versions.project_id",
                "dataset_versions.dataset_id",
                "dataset_versions.id",
            ],
            name="fk_datasets_current_version_scope",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        CheckConstraint("lock_version >= 1", name="ck_datasets_lock_version"),
        Index("ix_datasets_project_status", "project_id", "status"),
        Index("ix_datasets_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="research_projects.id", index=True, ondelete="RESTRICT"
    )
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    source_type: DatasetSourceType = Field(
        sa_column=Column(
            SAEnum(DatasetSourceType, name="dataset_source_type"), nullable=False
        )
    )
    publisher: str | None = Field(default=None, max_length=255)
    source_platform: str | None = Field(default=None, max_length=255)
    source_identifier: str | None = Field(default=None, max_length=500)
    doi: str | None = Field(default=None, max_length=500)
    acquired_at: date | None = None
    license_name: str | None = Field(default=None, max_length=255)
    license_status: DatasetLicenseStatus = Field(
        default=DatasetLicenseStatus.UNKNOWN,
        sa_column=Column(
            SAEnum(DatasetLicenseStatus, name="dataset_license_status"), nullable=False
        ),
    )
    recommended_citation: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    known_limitations: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    current_version_id: uuid.UUID | None = Field(default=None, index=True)
    status: DatasetStatus = Field(
        default=DatasetStatus.ACTIVE,
        sa_column=Column(SAEnum(DatasetStatus, name="dataset_status"), nullable=False),
    )
    lock_version: int = Field(default=1, ge=1)
    created_by: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", index=True, ondelete="SET NULL"
    )
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


class DatasetVersion(SQLModel, table=True):
    __tablename__ = "dataset_versions"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_dataset_versions_id_project"),
        UniqueConstraint(
            "project_id", "dataset_id", "id", name="uq_dataset_versions_scope"
        ),
        UniqueConstraint(
            "dataset_id", "version_number", name="uq_dataset_versions_number"
        ),
        ForeignKeyConstraint(
            ["dataset_id", "project_id"],
            ["datasets.id", "datasets.project_id"],
            name="fk_dataset_versions_dataset_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["parent_version_id", "project_id", "dataset_id"],
            [
                "dataset_versions.id",
                "dataset_versions.project_id",
                "dataset_versions.dataset_id",
            ],
            name="fk_dataset_versions_parent_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_dataset_versions_artifact_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["transformation_id", "project_id"],
            ["data_transformations.id", "data_transformations.project_id"],
            name="fk_dataset_versions_transformation_project",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        CheckConstraint("version_number >= 1", name="ck_dataset_versions_number"),
        CheckConstraint(
            "row_count IS NULL OR row_count >= 0", name="ck_dataset_versions_rows"
        ),
        CheckConstraint(
            "column_count IS NULL OR column_count >= 0",
            name="ck_dataset_versions_columns",
        ),
        CheckConstraint(
            "data_hash ~ '^[0-9a-f]{64}$'", name="ck_dataset_versions_data_hash"
        ),
        CheckConstraint(
            "schema_hash IS NULL OR schema_hash ~ '^[0-9a-f]{64}$'",
            name="ck_dataset_versions_schema_hash",
        ),
        CheckConstraint(
            "projection_hash IS NULL OR projection_hash ~ '^[0-9a-f]{64}$'",
            name="ck_dataset_versions_projection_hash",
        ),
        CheckConstraint(
            "(version_type = 'ORIGINAL' AND parent_version_id IS NULL AND transformation_id IS NULL) "
            "OR (version_type <> 'ORIGINAL' AND parent_version_id IS NOT NULL)",
            name="ck_dataset_versions_lineage",
        ),
        CheckConstraint(
            "(invalidated_at IS NULL AND invalidation_reason IS NULL) OR "
            "(invalidated_at IS NOT NULL AND invalidation_reason IS NOT NULL)",
            name="ck_dataset_versions_invalidation_pair",
        ),
        Index("ix_dataset_versions_project_status", "project_id", "status"),
        Index("ix_dataset_versions_dataset_created", "dataset_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    dataset_id: uuid.UUID = Field(index=True)
    version_number: int = Field(ge=1)
    parent_version_id: uuid.UUID | None = Field(default=None, index=True)
    artifact_id: uuid.UUID = Field(index=True)
    version_type: DatasetVersionType = Field(
        sa_column=Column(
            SAEnum(DatasetVersionType, name="dataset_version_type"), nullable=False
        )
    )
    row_count: int | None = Field(default=None, ge=0)
    column_count: int | None = Field(default=None, ge=0)
    file_format: DatasetFileFormat = Field(
        sa_column=Column(
            SAEnum(DatasetFileFormat, name="dataset_file_format"), nullable=False
        )
    )
    worksheet_manifest: list[dict[str, Any]] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    selected_worksheet_name: str | None = Field(default=None, max_length=255)
    projection_hash: str | None = Field(default=None, max_length=64)
    schema_hash: str | None = Field(default=None, max_length=64)
    data_hash: str = Field(max_length=64, index=True)
    transformation_id: uuid.UUID | None = Field(default=None, index=True)
    status: DatasetVersionStatus = Field(
        default=DatasetVersionStatus.CREATING,
        sa_column=Column(
            SAEnum(DatasetVersionStatus, name="dataset_version_status"), nullable=False
        ),
    )
    created_by: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", index=True, ondelete="SET NULL"
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    invalidated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    invalidation_reason: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    deleted_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class DatasetColumn(SQLModel, table=True):
    __tablename__ = "dataset_columns"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_dataset_columns_id_project"),
        UniqueConstraint(
            "dataset_version_id", "source_name", name="uq_dataset_columns_source"
        ),
        UniqueConstraint(
            "dataset_version_id", "column_order", name="uq_dataset_columns_order"
        ),
        ForeignKeyConstraint(
            ["dataset_version_id", "project_id"],
            ["dataset_versions.id", "dataset_versions.project_id"],
            name="fk_dataset_columns_version_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["inherited_from_column_id", "project_id"],
            ["dataset_columns.id", "dataset_columns.project_id"],
            name="fk_dataset_columns_inherited_project",
            ondelete="RESTRICT",
        ),
        CheckConstraint("column_order >= 1", name="ck_dataset_columns_order"),
        CheckConstraint("lock_version >= 1", name="ck_dataset_columns_lock"),
        CheckConstraint(
            "missing_ratio >= 0 AND missing_ratio <= 1",
            name="ck_dataset_columns_missing_ratio",
        ),
        CheckConstraint("unique_count >= 0", name="ck_dataset_columns_unique_count"),
        Index("ix_dataset_columns_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    dataset_version_id: uuid.UUID = Field(index=True)
    source_name: str = Field(max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    column_order: int = Field(ge=1)
    inferred_type: DatasetColumnType = Field(
        sa_column=Column(
            SAEnum(DatasetColumnType, name="dataset_column_type"), nullable=False
        )
    )
    confirmed_type: DatasetColumnType | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(DatasetColumnType, name="dataset_column_type", create_type=False),
            nullable=True,
        ),
    )
    semantic_role: DatasetSemanticRole | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(DatasetSemanticRole, name="dataset_semantic_role"), nullable=True
        ),
    )
    unit: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    missing_codes: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    category_mapping: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    is_identifier: bool = False
    is_sensitive: bool = False
    confirmation_status: DatasetColumnConfirmationStatus = Field(
        default=DatasetColumnConfirmationStatus.UNCONFIRMED,
        sa_column=Column(
            SAEnum(
                DatasetColumnConfirmationStatus,
                name="dataset_column_confirmation_status",
            ),
            nullable=False,
        ),
    )
    unique_count: int = Field(default=0, ge=0)
    missing_ratio: float = Field(default=0.0, ge=0, le=1)
    example_values: list[Any] = Field(
        default_factory=list, sa_column=Column(JSONB, nullable=False)
    )
    inherited_from_column_id: uuid.UUID | None = Field(default=None, index=True)
    lock_version: int = Field(default=1, ge=1)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class DataQualityRun(SQLModel, table=True):
    __tablename__ = "data_quality_runs"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_data_quality_runs_id_project"),
        ForeignKeyConstraint(
            ["dataset_version_id", "project_id"],
            ["dataset_versions.id", "dataset_versions.project_id"],
            name="fk_data_quality_runs_version_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["processing_run_id", "project_id"],
            ["processing_runs.id", "processing_runs.project_id"],
            name="fk_data_quality_runs_processing_project",
            ondelete="RESTRICT",
        ),
        CheckConstraint("issue_count >= 0", name="ck_data_quality_runs_issue_count"),
        CheckConstraint(
            "high_issue_count >= 0", name="ck_data_quality_runs_high_count"
        ),
        CheckConstraint(
            "ruleset_hash ~ '^[0-9a-f]{64}$'", name="ck_data_quality_runs_ruleset_hash"
        ),
        Index("ix_data_quality_runs_project_status", "project_id", "status"),
        Index("ix_data_quality_runs_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    dataset_version_id: uuid.UUID = Field(index=True)
    ruleset_id: str = Field(max_length=100)
    rule_set_version: str = Field(max_length=50)
    ruleset_hash: str = Field(max_length=64)
    status: DataQualityRunStatus = Field(
        default=DataQualityRunStatus.QUEUED,
        sa_column=Column(
            SAEnum(DataQualityRunStatus, name="data_quality_run_status"), nullable=False
        ),
    )
    issue_count: int = Field(default=0, ge=0)
    high_issue_count: int = Field(default=0, ge=0)
    processing_run_id: uuid.UUID | None = Field(default=None, index=True)
    started_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))  # type: ignore
    completed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))  # type: ignore
    error_code: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)
    )  # type: ignore


class DataQualityIssue(SQLModel, table=True):
    __tablename__ = "data_quality_issues"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_data_quality_issues_id_project"),
        ForeignKeyConstraint(
            ["data_quality_run_id", "project_id"],
            ["data_quality_runs.id", "data_quality_runs.project_id"],
            name="fk_data_quality_issues_run_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["dataset_version_id", "project_id"],
            ["dataset_versions.id", "dataset_versions.project_id"],
            name="fk_data_quality_issues_version_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["column_id", "project_id"],
            ["dataset_columns.id", "dataset_columns.project_id"],
            name="fk_data_quality_issues_column_project",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "affected_row_count IS NULL OR affected_row_count >= 0",
            name="ck_data_quality_issues_affected_rows",
        ),
        Index("ix_data_quality_issues_project_status", "project_id", "status"),
        Index("ix_data_quality_issues_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    data_quality_run_id: uuid.UUID = Field(index=True)
    dataset_version_id: uuid.UUID = Field(index=True)
    rule_code: str = Field(max_length=100)
    issue_type: DataQualityIssueType = Field(
        sa_column=Column(
            SAEnum(DataQualityIssueType, name="data_quality_issue_type"), nullable=False
        )
    )
    severity: DataQualitySeverity = Field(
        sa_column=Column(
            SAEnum(DataQualitySeverity, name="data_quality_severity"), nullable=False
        )
    )
    column_id: uuid.UUID | None = Field(default=None, index=True)
    affected_row_count: int | None = Field(default=None, ge=0)
    affected_rows: list[Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    evidence: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    description: str = Field(sa_column=Column(Text, nullable=False))
    suggested_actions: list[dict[str, Any]] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    requires_approval: bool = False
    status: DataQualityIssueStatus = Field(
        default=DataQualityIssueStatus.OPEN,
        sa_column=Column(
            SAEnum(DataQualityIssueStatus, name="data_quality_issue_status"),
            nullable=False,
        ),
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)
    )  # type: ignore
    resolved_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))  # type: ignore


class CleaningPlan(SQLModel, table=True):
    __tablename__ = "cleaning_plans"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_cleaning_plans_id_project"),
        ForeignKeyConstraint(
            ["dataset_version_id", "project_id"],
            ["dataset_versions.id", "dataset_versions.project_id"],
            name="fk_cleaning_plans_version_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["source_model_invocation_id", "project_id"],
            ["model_invocations.id", "model_invocations.project_id"],
            name="fk_cleaning_plans_model_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["approval_record_id", "project_id"],
            ["approval_records.id", "approval_records.project_id"],
            name="fk_cleaning_plans_approval_project",
            ondelete="RESTRICT",
        ),
        CheckConstraint("lock_version >= 1", name="ck_cleaning_plans_lock"),
        CheckConstraint(
            "preview_hash IS NULL OR preview_hash ~ '^[0-9a-f]{64}$'",
            name="ck_cleaning_plans_preview_hash",
        ),
        CheckConstraint(
            "payload_hash IS NULL OR payload_hash ~ '^[0-9a-f]{64}$'",
            name="ck_cleaning_plans_payload_hash",
        ),
        Index("ix_cleaning_plans_project_status", "project_id", "status"),
        Index("ix_cleaning_plans_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    dataset_version_id: uuid.UUID = Field(index=True)
    title: str = Field(max_length=255)
    rationale: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    status: CleaningPlanStatus = Field(
        default=CleaningPlanStatus.DRAFT,
        sa_column=Column(
            SAEnum(CleaningPlanStatus, name="cleaning_plan_status"), nullable=False
        ),
    )
    preview_summary: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    preview_hash: str | None = Field(default=None, max_length=64)
    affected_row_count: int | None = Field(default=None, ge=0)
    affected_column_count: int | None = Field(default=None, ge=0)
    source_model_invocation_id: uuid.UUID | None = Field(default=None, index=True)
    approval_record_id: uuid.UUID | None = Field(default=None, index=True)
    payload_hash: str | None = Field(default=None, max_length=64)
    lock_version: int = Field(default=1, ge=1)
    created_by: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", index=True, ondelete="SET NULL"
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)
    )  # type: ignore
    updated_at: datetime = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)
    )  # type: ignore


class CleaningPlanAction(SQLModel, table=True):
    __tablename__ = "cleaning_plan_actions"
    __table_args__ = (
        UniqueConstraint(
            "id", "project_id", name="uq_cleaning_plan_actions_id_project"
        ),
        UniqueConstraint(
            "cleaning_plan_id", "action_order", name="uq_cleaning_plan_actions_order"
        ),
        ForeignKeyConstraint(
            ["cleaning_plan_id", "project_id"],
            ["cleaning_plans.id", "cleaning_plans.project_id"],
            name="fk_cleaning_plan_actions_plan_project",
            ondelete="RESTRICT",
        ),
        CheckConstraint("action_order >= 1", name="ck_cleaning_plan_actions_order"),
        Index("ix_cleaning_plan_actions_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    cleaning_plan_id: uuid.UUID = Field(index=True)
    action_order: int = Field(ge=1)
    action_type: CleaningActionType = Field(
        sa_column=Column(
            SAEnum(CleaningActionType, name="cleaning_action_type"), nullable=False
        )
    )
    selector_type: CleaningSelectorType = Field(
        sa_column=Column(
            SAEnum(CleaningSelectorType, name="cleaning_selector_type"), nullable=False
        )
    )
    target_columns: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    row_selector: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    parameters: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    reason: str = Field(sa_column=Column(Text, nullable=False))
    source_issue_ids: list[str] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    preview_before: list[dict[str, Any]] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    preview_after: list[dict[str, Any]] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    risk_level: CleaningRiskLevel = Field(
        sa_column=Column(
            SAEnum(CleaningRiskLevel, name="cleaning_risk_level"), nullable=False
        )
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)
    )  # type: ignore


class DataTransformation(SQLModel, table=True):
    __tablename__ = "data_transformations"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_data_transformations_id_project"),
        UniqueConstraint("cleaning_plan_id", name="uq_data_transformations_plan"),
        ForeignKeyConstraint(
            ["cleaning_plan_id", "project_id"],
            ["cleaning_plans.id", "cleaning_plans.project_id"],
            name="fk_data_transformations_plan_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["source_dataset_version_id", "project_id"],
            ["dataset_versions.id", "dataset_versions.project_id"],
            name="fk_data_transformations_source_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["target_dataset_version_id", "project_id"],
            ["dataset_versions.id", "dataset_versions.project_id"],
            name="fk_data_transformations_target_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["processing_run_id", "project_id"],
            ["processing_runs.id", "processing_runs.project_id"],
            name="fk_data_transformations_processing_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["approval_record_id", "project_id"],
            ["approval_records.id", "approval_records.project_id"],
            name="fk_data_transformations_approval_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["output_artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_data_transformations_output_project",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["log_artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_data_transformations_log_project",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "action_count >= 0", name="ck_data_transformations_action_count"
        ),
        CheckConstraint(
            "parameters_hash ~ '^[0-9a-f]{64}$'",
            name="ck_data_transformations_parameters_hash",
        ),
        CheckConstraint(
            "status <> 'COMPLETED' OR target_dataset_version_id IS NOT NULL",
            name="ck_data_transformations_completed_target",
        ),
        Index("ix_data_transformations_project_status", "project_id", "status"),
        Index("ix_data_transformations_project_created", "project_id", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(index=True)
    cleaning_plan_id: uuid.UUID = Field(index=True)
    approval_record_id: uuid.UUID = Field(index=True)
    source_dataset_version_id: uuid.UUID = Field(index=True)
    target_dataset_version_id: uuid.UUID | None = Field(default=None, index=True)
    status: DataTransformationStatus = Field(
        default=DataTransformationStatus.QUEUED,
        sa_column=Column(
            SAEnum(DataTransformationStatus, name="data_transformation_status"),
            nullable=False,
        ),
    )
    action_count: int = Field(ge=0)
    affected_row_count: int | None = Field(default=None, ge=0)
    affected_column_count: int | None = Field(default=None, ge=0)
    parameters_hash: str = Field(max_length=64)
    output_artifact_id: uuid.UUID | None = Field(default=None, index=True)
    log_artifact_id: uuid.UUID | None = Field(default=None, index=True)
    processing_run_id: uuid.UUID | None = Field(default=None, index=True)
    started_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))  # type: ignore
    completed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))  # type: ignore
    error_code: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)
    )  # type: ignore


class Job(SQLModel, table=True):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_jobs_id_project"),
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
        UniqueConstraint("id", "project_id", name="uq_processing_runs_id_project"),
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
        UniqueConstraint("id", "project_id", name="uq_model_invocations_id_project"),
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
