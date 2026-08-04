from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import (
    ConfidenceLevel,
    EvidenceReviewStatus,
    EvidenceType,
    FieldConfirmationStatus,
    FieldEvidenceStatus,
    JobStatus,
    LiteratureDecisionReason,
    LiteratureDecisionStatus,
    LiteratureExtractionStatus,
    LiteratureFieldCode,
    LocationVerificationStatus,
    ParserCoverage,
    TopicCandidateStatus,
    TopicEvidenceRelation,
    UserDeclaredReadScope,
)
from app.projects.schemas import PaginationMeta, ResponseMeta


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceBoundingBox(StrictModel):
    page: int = Field(ge=1)
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class CandidateEvidence(StrictModel):
    candidate_id: uuid.UUID
    project_id: uuid.UUID
    literature_record_id: uuid.UUID
    document_id: uuid.UUID
    chunk_id: uuid.UUID | None = None
    page_number: int = Field(ge=1)
    source_text: str = Field(min_length=1, max_length=20_000)
    source_text_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    retrieval_run_id: uuid.UUID | None = None
    keyword_score: float | None = Field(default=None, ge=0)
    vector_score: float | None = Field(default=None)
    fused_rank: int | None = Field(default=None, ge=1)
    rerank_score: float | None = None
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=1)
    bounding_boxes: list[EvidenceBoundingBox] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    @field_validator("source_text")
    @classmethod
    def source_text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source_text must contain non-whitespace text")
        return value

    @field_validator("limitations")
    @classmethod
    def normalize_limitations(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("limitations cannot contain blank values")
        if len(normalized) != len(set(normalized)):
            raise ValueError("limitations cannot contain duplicates")
        return normalized

    @model_validator(mode="after")
    def validate_offsets_and_boxes(self) -> CandidateEvidence:
        if (self.char_start is None) != (self.char_end is None):
            raise ValueError("char_start and char_end must be provided together")
        if self.char_start is not None and self.char_end is not None:
            if self.char_end <= self.char_start:
                raise ValueError("char_end must be greater than char_start")
        if any(box.page != self.page_number for box in self.bounding_boxes):
            raise ValueError("bounding box pages must match page_number")
        return self


class EvidenceCandidateDTO(CandidateEvidence):
    evidence_span_id: uuid.UUID | None = None


class LiteratureFieldValue(StrictModel):
    text: str | None = Field(default=None, max_length=20_000)
    structured: dict[str, Any] | list[Any] | None = None

    @model_validator(mode="after")
    def require_a_value(self) -> LiteratureFieldValue:
        if self.text is None and self.structured is None:
            return self
        if self.text is not None and not self.text.strip():
            raise ValueError("value text cannot be blank")
        return self


class LiteratureExtractionCandidateFieldOutput(StrictModel):
    field_code: LiteratureFieldCode
    value: LiteratureFieldValue
    evidence_candidates: list[CandidateEvidence] = Field(
        default_factory=list, max_length=1
    )
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool
    notes: list[str] = Field(default_factory=list)

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("notes cannot contain blank values")
        return normalized


class LiteratureExtractionCandidateOutput(StrictModel):
    literature_record_id: uuid.UUID
    document_id: uuid.UUID
    fields: list[LiteratureExtractionCandidateFieldOutput]
    document_level_limitations: list[str] = Field(default_factory=list)

    @field_validator("document_level_limitations")
    @classmethod
    def normalize_limitations(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("document limitations cannot contain blank values")
        return normalized

    @model_validator(mode="after")
    def require_exactly_ten_fields(self) -> LiteratureExtractionCandidateOutput:
        actual = [field.field_code for field in self.fields]
        expected = list(LiteratureFieldCode)
        if len(actual) != len(expected) or set(actual) != set(expected):
            raise ValueError("fields must contain each frozen field_code exactly once")
        return self


class LiteratureExtractionFieldOutput(StrictModel):
    field_code: LiteratureFieldCode
    value: LiteratureFieldValue
    evidence_span_ids: list[uuid.UUID] = Field(default_factory=list, max_length=1)
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool
    notes: list[str] = Field(default_factory=list)


class LiteratureExtractionOutput(StrictModel):
    literature_record_id: uuid.UUID
    document_id: uuid.UUID
    fields: list[LiteratureExtractionFieldOutput]
    document_level_limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_exactly_ten_fields(self) -> LiteratureExtractionOutput:
        actual = [field.field_code for field in self.fields]
        expected = list(LiteratureFieldCode)
        if len(actual) != len(expected) or set(actual) != set(expected):
            raise ValueError("fields must contain each frozen field_code exactly once")
        return self


class DocumentContextPage(StrictModel):
    page_number: int = Field(ge=1)
    text: str = Field(min_length=1, max_length=20_000)
    chunk_ids: list[uuid.UUID] = Field(default_factory=list)
    section_paths: list[list[str]] = Field(default_factory=list)
    coordinates_available: bool


class LiteratureExtractionInput(StrictModel):
    extraction_id: uuid.UUID
    project_id: uuid.UUID
    literature_record_id: uuid.UUID
    document_id: uuid.UUID
    parser_type: str
    parser_version: str | None
    parse_confidence: str
    pages: list[DocumentContextPage] = Field(min_length=1, max_length=40)
    context_limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_unique_pages(self) -> LiteratureExtractionInput:
        page_numbers = [page.page_number for page in self.pages]
        if len(page_numbers) != len(set(page_numbers)):
            raise ValueError("context pages must be unique")
        if page_numbers != sorted(page_numbers):
            raise ValueError("context pages must be ordered")
        return self


class LiteratureExtractionCreate(StrictModel):
    literature_record_id: uuid.UUID
    field_codes: list[LiteratureFieldCode] = Field(min_length=1, max_length=10)

    @field_validator("field_codes")
    @classmethod
    def require_unique_field_codes(
        cls, values: list[LiteratureFieldCode]
    ) -> list[LiteratureFieldCode]:
        if len(values) != len(set(values)):
            raise ValueError("field_codes cannot contain duplicates")
        return values


class LiteratureExtractionFieldCorrection(StrictModel):
    value_text: str | None = Field(default=None, max_length=20_000)
    value_json: dict[str, Any] | list[Any] | None = None
    evidence_span_id: uuid.UUID | None = None
    correction_reason: str = Field(min_length=1, max_length=4_000)
    confirmation_status: FieldConfirmationStatus

    @field_validator("correction_reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def require_value_or_explicit_rejection(
        self,
    ) -> LiteratureExtractionFieldCorrection:
        if (
            self.value_text is None
            and self.value_json is None
            and self.confirmation_status != FieldConfirmationStatus.REJECTED
        ):
            raise ValueError(
                "a corrected value is required unless the field is rejected"
            )
        if self.value_text is not None and not self.value_text.strip():
            raise ValueError("value_text cannot be blank")
        return self


class ManualEvidenceSpanCreate(StrictModel):
    page_number: int = Field(ge=1)
    source_text: str = Field(min_length=1, max_length=20_000)
    bounding_boxes: list[EvidenceBoundingBox] = Field(default_factory=list)
    evidence_type: EvidenceType
    user_declared_read_scope: UserDeclaredReadScope

    @field_validator("source_text")
    @classmethod
    def normalize_source_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source_text must contain non-whitespace text")
        return value


class EvidenceSpanVerificationCreate(StrictModel):
    location_verification_status: LocationVerificationStatus
    user_declared_read_scope: UserDeclaredReadScope
    reviewed_page_numbers: list[int] = Field(min_length=1)
    note: str | None = Field(default=None, max_length=4_000)

    @field_validator("reviewed_page_numbers")
    @classmethod
    def validate_reviewed_pages(cls, values: list[int]) -> list[int]:
        if any(value < 1 for value in values):
            raise ValueError("reviewed_page_numbers must be positive")
        if len(values) != len(set(values)):
            raise ValueError("reviewed_page_numbers cannot contain duplicates")
        return sorted(values)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class LiteratureDecisionCreate(StrictModel):
    decision: LiteratureDecisionStatus
    reason_code: LiteratureDecisionReason | None = None
    reason_text: str | None = Field(default=None, max_length=4_000)

    @field_validator("reason_text")
    @classmethod
    def normalize_reason_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class LiteratureExtractionFieldPublic(StrictModel):
    id: uuid.UUID | None
    project_id: uuid.UUID
    extraction_id: uuid.UUID
    field_code: LiteratureFieldCode
    model_value_text: str | None
    model_value_json: dict[str, Any] | list[Any] | None
    value_text: str | None
    value_json: dict[str, Any] | list[Any] | None
    confidence_score: float | None
    confidence_level: ConfidenceLevel
    evidence_span_id: uuid.UUID | None
    confirmation_status: FieldConfirmationStatus
    evidence_status: FieldEvidenceStatus
    evidence_limitations: str | None
    lock_version: int
    created_at: datetime | None
    updated_at: datetime | None
    allowed_actions: list[str]


class LiteratureExtractionPublic(StrictModel):
    id: uuid.UUID
    project_id: uuid.UUID
    literature_record_id: uuid.UUID
    document_id: uuid.UUID
    extraction_version: int
    schema_version: str
    status: LiteratureExtractionStatus
    overall_confidence: ConfidenceLevel | None
    source_model_invocation_id: uuid.UUID | None
    processing_run_id: uuid.UUID | None
    document_level_limitations: list[str]
    lock_version: int
    fields: list[LiteratureExtractionFieldPublic]
    allowed_actions: list[str]
    created_at: datetime
    updated_at: datetime


class LiteratureExtractionEnvelope(StrictModel):
    data: LiteratureExtractionPublic
    meta: ResponseMeta


class LiteratureExtractionFieldEnvelope(StrictModel):
    data: LiteratureExtractionFieldPublic
    meta: ResponseMeta


class EvidenceSpanPublic(StrictModel):
    id: uuid.UUID
    project_id: uuid.UUID
    document_id: uuid.UUID
    document_page_id: uuid.UUID | None
    chunk_id: uuid.UUID | None
    page_number: int
    section_path: list[str] | None
    source_text: str
    context_before: str | None
    context_after: str | None
    bounding_boxes: list[dict[str, Any]] | None
    char_start: int | None
    char_end: int | None
    evidence_type: EvidenceType
    confidence_level: ConfidenceLevel | None
    confidence_score: float | None
    parser_type: str | None
    parser_version: str | None
    model_invocation_id: uuid.UUID | None
    source_text_hash: str
    location_verification_status: LocationVerificationStatus
    review_status: EvidenceReviewStatus
    parser_coverage: ParserCoverage
    user_declared_read_scope: UserDeclaredReadScope
    reviewed_by_actor_type: str | None
    reviewed_by_actor_id: str | None
    reviewed_at: datetime | None
    verified_by_actor_id: str | None
    verified_at: datetime | None
    allowed_actions: list[str]
    created_at: datetime


class EvidenceSpanEnvelope(StrictModel):
    data: EvidenceSpanPublic
    meta: ResponseMeta


class EvidenceSpanVerificationPublic(StrictModel):
    id: uuid.UUID
    project_id: uuid.UUID
    evidence_span_id: uuid.UUID
    actor_type: str
    actor_id: str
    location_verification_status: LocationVerificationStatus
    user_declared_read_scope: UserDeclaredReadScope
    reviewed_page_numbers: list[int]
    note: str | None
    source_text_hash: str
    created_at: datetime


class EvidenceSpanVerificationEnvelope(StrictModel):
    data: EvidenceSpanVerificationPublic
    meta: ResponseMeta


class LiteratureDecisionPublic(StrictModel):
    id: uuid.UUID
    project_id: uuid.UUID
    literature_record_id: uuid.UUID
    decision: LiteratureDecisionStatus
    reason_code: LiteratureDecisionReason | None
    reason_text: str | None
    ai_recommendation: LiteratureDecisionStatus | None
    ai_score: float | None
    decided_by_user_id: uuid.UUID
    supersedes_decision_id: uuid.UUID | None
    is_current: bool
    created_at: datetime


class LiteratureDecisionEnvelope(StrictModel):
    data: LiteratureDecisionPublic
    meta: ResponseMeta


class LiteratureDecisionListEnvelope(StrictModel):
    data: list[LiteratureDecisionPublic]
    meta: ResponseMeta


class MatrixSort(StrEnum):
    CREATED_AT = "created_at"
    TITLE = "title"
    YEAR = "year"
    DECISION = "decision"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class LiteratureMatrixField(StrictModel):
    field_code: LiteratureFieldCode
    value_text: str | None
    value_json: dict[str, Any] | list[Any] | None
    confidence_level: ConfidenceLevel
    confidence_score: float | None
    confirmation_status: FieldConfirmationStatus
    evidence_status: FieldEvidenceStatus
    evidence_span_id: uuid.UUID | None
    evidence_limitations: str | None
    lock_version: int | None


class LiteratureMatrixRow(StrictModel):
    literature_record_id: uuid.UUID
    document_id: uuid.UUID | None
    extraction_id: uuid.UUID | None
    extraction_status: LiteratureExtractionStatus | None
    title: str
    authors_text: str | None
    publication_year: int | None
    current_decision: LiteratureDecisionStatus
    fields: list[LiteratureMatrixField]
    allowed_actions: list[str]


class LiteratureMatrixEnvelope(StrictModel):
    data: list[LiteratureMatrixRow]
    allowed_actions: list[str]
    pagination: PaginationMeta
    meta: ResponseMeta


class EvidenceRetrievalMode(StrEnum):
    KEYWORD = "KEYWORD"
    HYBRID = "HYBRID"


class EvidenceSearchRequest(StrictModel):
    query: str = Field(min_length=1, max_length=2_000)
    document_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)
    top_k: int = Field(default=10, ge=1, le=50)
    retrieval_mode: EvidenceRetrievalMode = EvidenceRetrievalMode.KEYWORD
    include_uncertain_literature: bool = False

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("query cannot be blank")
        return normalized

    @field_validator("document_ids")
    @classmethod
    def require_unique_documents(cls, values: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(values) != len(set(values)):
            raise ValueError("document_ids cannot contain duplicates")
        return values


class EvidenceSearchData(StrictModel):
    query: str
    retrieval_run_id: uuid.UUID
    candidates: list[EvidenceCandidateDTO]
    limitations: list[str]


class EvidenceSearchEnvelope(StrictModel):
    data: EvidenceSearchData
    meta: ResponseMeta


class EvidenceSummaryType(StrEnum):
    CONSENSUS = "CONSENSUS"
    CONTROVERSY = "CONTROVERSY"
    EVIDENCE_GAP = "EVIDENCE_GAP"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    METHOD_DIFFERENCE = "METHOD_DIFFERENCE"
    SAMPLE_DIFFERENCE = "SAMPLE_DIFFERENCE"
    MISSING_LITERATURE = "MISSING_LITERATURE"


class EvidenceSetSummaryCreate(StrictModel):
    included_literature_ids: list[uuid.UUID] = Field(min_length=1, max_length=200)
    summary_types: list[EvidenceSummaryType] = Field(min_length=1)
    require_evidence_spans: bool = True

    @field_validator("included_literature_ids", "summary_types")
    @classmethod
    def require_unique_values(cls, values: list[Any]) -> list[Any]:
        if len(values) != len(set(values)):
            raise ValueError("values cannot contain duplicates")
        return values


class EvidenceSummarySourceItem(StrictModel):
    claim_text: str = Field(min_length=1, max_length=10_000)
    supporting_literature_ids: list[uuid.UUID] = Field(default_factory=list)
    contradicting_literature_ids: list[uuid.UUID] = Field(default_factory=list)
    evidence_span_ids: list[uuid.UUID] = Field(default_factory=list)
    strength: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_source(self) -> EvidenceSummarySourceItem:
        source_ids = (
            self.supporting_literature_ids
            + self.contradicting_literature_ids
            + self.evidence_span_ids
        )
        if not source_ids:
            raise ValueError(
                "summary items require a LiteratureRecord or EvidenceSpan source"
            )
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("summary item sources cannot contain duplicates")
        return self


class EvidenceGapItem(EvidenceSummarySourceItem):
    basis: dict[str, int] = Field(default_factory=dict)


class EvidenceSetSummaryOutput(StrictModel):
    included_literature_ids: list[uuid.UUID] = Field(min_length=1)
    scope_statement: str = Field(min_length=1, max_length=4_000)
    consensus_items: list[EvidenceSummarySourceItem] = Field(default_factory=list)
    controversy_items: list[EvidenceSummarySourceItem] = Field(default_factory=list)
    evidence_gap_items: list[EvidenceGapItem] = Field(default_factory=list)
    counterexamples: list[EvidenceSummarySourceItem] = Field(default_factory=list)
    method_difference_items: list[EvidenceSummarySourceItem] = Field(
        default_factory=list
    )
    sample_difference_items: list[EvidenceSummarySourceItem] = Field(
        default_factory=list
    )
    missing_literature: list[EvidenceSummarySourceItem] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    @field_validator("included_literature_ids")
    @classmethod
    def require_unique_literature(cls, values: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(values) != len(set(values)):
            raise ValueError("included_literature_ids cannot contain duplicates")
        return values


class EvidenceContextSpan(StrictModel):
    evidence_span_id: uuid.UUID
    literature_record_id: uuid.UUID
    document_id: uuid.UUID
    page_number: int = Field(ge=1)
    source_text: str = Field(min_length=1, max_length=20_000)
    source_text_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    location_status: LocationVerificationStatus
    limitations: list[str] = Field(default_factory=list)


class EvidenceSetSummaryInput(StrictModel):
    summary_id: uuid.UUID
    project_id: uuid.UUID
    included_literature_ids: list[uuid.UUID] = Field(min_length=1, max_length=200)
    summary_types: list[EvidenceSummaryType]
    require_evidence_spans: bool
    evidence: list[EvidenceContextSpan]
    input_limitations: list[str] = Field(default_factory=list)


class EvidenceSetSummaryPublic(StrictModel):
    id: uuid.UUID
    project_id: uuid.UUID
    included_literature_ids: list[uuid.UUID]
    scope_statement: str
    result: EvidenceSetSummaryOutput | None
    job_id: uuid.UUID | None
    processing_run_id: uuid.UUID | None
    source_model_invocation_id: uuid.UUID | None
    status: JobStatus
    allowed_actions: list[str]
    created_at: datetime


class EvidenceSetSummaryEnvelope(StrictModel):
    data: EvidenceSetSummaryPublic
    meta: ResponseMeta


class TopicGenerationCreate(StrictModel):
    research_question_version_id: uuid.UUID
    evidence_set_summary_id: uuid.UUID
    candidate_count: int = Field(default=3, ge=3, le=3)
    user_constraints: dict[str, Any] = Field(default_factory=dict)


class TopicCandidateSource(StrictModel):
    literature_record_id: uuid.UUID | None = None
    evidence_span_id: uuid.UUID | None = None
    relation_type: TopicEvidenceRelation
    explanation: str | None = Field(default=None, max_length=4_000)

    @model_validator(mode="after")
    def require_exactly_one_source(self) -> TopicCandidateSource:
        if (self.literature_record_id is None) == (self.evidence_span_id is None):
            raise ValueError("topic evidence requires exactly one source")
        return self


class TopicCandidateOutput(StrictModel):
    candidate_order: int = Field(ge=1, le=3)
    question_text: str = Field(min_length=1, max_length=10_000)
    research_object: str = Field(min_length=1, max_length=4_000)
    variables: dict[str, list[str]]
    literature_basis: str = Field(min_length=1, max_length=10_000)
    possible_innovation: str = Field(min_length=1, max_length=10_000)
    data_requirements: dict[str, Any]
    recommended_method: str = Field(min_length=1, max_length=4_000)
    literature_basis_level: ConfidenceLevel
    data_availability: ConfidenceLevel
    method_difficulty: ConfidenceLevel
    time_feasibility: ConfidenceLevel
    ethical_risk: ConfidenceLevel
    major_risks: list[str]
    limitations: list[str]
    supervisor_confirmation_items: list[str] = Field(min_length=1)
    sources: list[TopicCandidateSource] = Field(min_length=1)


class TopicGenerationOutput(StrictModel):
    candidates: list[TopicCandidateOutput] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def require_three_unique_candidates(self) -> TopicGenerationOutput:
        orders = [candidate.candidate_order for candidate in self.candidates]
        questions = [
            " ".join(candidate.question_text.casefold().split())
            for candidate in self.candidates
        ]
        if set(orders) != {1, 2, 3}:
            raise ValueError("candidate_order must contain exactly 1, 2 and 3")
        if len(questions) != len(set(questions)):
            raise ValueError("topic candidate questions must be unique")
        return self


class TopicGenerationInput(StrictModel):
    topic_generation_run_id: uuid.UUID
    project_id: uuid.UUID
    research_question_version_id: uuid.UUID
    research_question: dict[str, Any]
    evidence_set_summary_id: uuid.UUID
    evidence_summary: EvidenceSetSummaryOutput
    candidate_count: int = Field(ge=3, le=3)
    user_constraints: dict[str, Any]


class TopicCandidatePublic(StrictModel):
    id: uuid.UUID
    project_id: uuid.UUID
    topic_generation_run_id: uuid.UUID
    candidate_order: int
    question_text: str
    research_object: str | None
    variables: dict[str, Any] | None
    literature_basis: str | None
    possible_innovation: str | None
    data_requirements: dict[str, Any] | None
    recommended_method: str | None
    literature_basis_level: ConfidenceLevel | None
    data_availability: ConfidenceLevel | None
    method_difficulty: ConfidenceLevel | None
    time_feasibility: ConfidenceLevel | None
    ethical_risk: ConfidenceLevel | None
    major_risks: list[str] | None
    limitations: list[str]
    supervisor_confirmation_items: list[str] | None
    status: TopicCandidateStatus
    sources: list[TopicCandidateSource]
    created_at: datetime


class TopicGenerationRunPublic(StrictModel):
    id: uuid.UUID
    project_id: uuid.UUID
    research_question_version_id: uuid.UUID
    evidence_summary_id: uuid.UUID | None
    user_constraints: dict[str, Any] | None
    job_id: uuid.UUID | None
    processing_run_id: uuid.UUID | None
    source_model_invocation_id: uuid.UUID | None
    status: JobStatus
    candidates: list[TopicCandidatePublic]
    allowed_actions: list[str]
    created_at: datetime


class TopicGenerationRunEnvelope(StrictModel):
    data: TopicGenerationRunPublic
    meta: ResponseMeta
