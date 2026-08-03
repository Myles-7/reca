from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.jobs.schemas import JobPublic
from app.models import (
    JobStatus,
    LiteratureDecisionStatus,
    LiteratureSourceType,
    LiteratureVerificationStatus,
)
from app.projects.schemas import PaginationMeta, ResponseMeta


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LiteratureSearchCreate(StrictModel):
    page_size: int = Field(default=25, ge=1, le=200)
    use_cache: bool = True


class LiteratureSearchRunPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    query_plan_id: uuid.UUID
    provider: str
    provider_query: dict[str, object]
    result_count: int
    cache_hit: bool
    cache_stale: bool
    cache_source_run_id: uuid.UUID | None
    degraded: bool
    limitations: list[str]
    fetched_at: datetime
    status: JobStatus
    error_code: str | None
    job_id: uuid.UUID | None
    created_at: datetime
    allowed_actions: list[str]


class LiteratureSearchAcceptedData(BaseModel):
    search_run: LiteratureSearchRunPublic
    job: JobPublic


class LiteratureSearchAcceptedEnvelope(BaseModel):
    data: LiteratureSearchAcceptedData
    meta: ResponseMeta


class LiteratureCandidatePublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    search_run_id: uuid.UUID
    result_order: int
    source_identifier: str
    title: str
    abstract: str | None
    publication_year: int | None
    journal_name: str | None
    doi: str | None
    authors_text: str | None
    keywords: list[str]
    work_type: str | None
    open_access_status: str | None
    verification_status: LiteratureVerificationStatus
    fetched_at: datetime
    degraded: bool
    imported_literature_record_id: uuid.UUID | None
    allowed_actions: list[str]


class LiteratureSearchResultsData(BaseModel):
    search_run: LiteratureSearchRunPublic
    results: list[LiteratureCandidatePublic]


class LiteratureSearchResultsEnvelope(BaseModel):
    data: LiteratureSearchResultsData
    pagination: PaginationMeta
    meta: ResponseMeta


class LiteratureImportRequest(StrictModel):
    search_run_id: uuid.UUID
    result_ids: list[uuid.UUID] = Field(min_length=1, max_length=200)


class LiteratureImportResult(BaseModel):
    candidate_id: uuid.UUID
    literature_record_id: uuid.UUID
    matched_existing: bool


class LiteratureImportData(BaseModel):
    imported: list[LiteratureImportResult]


class LiteratureImportEnvelope(BaseModel):
    data: LiteratureImportData
    meta: ResponseMeta


class LiteratureDoiImportRequest(StrictModel):
    doi: str = Field(min_length=1, max_length=500)


class LiteratureRecordPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    document_id: uuid.UUID | None
    source_type: LiteratureSourceType
    source_identifier: str | None
    title: str
    abstract: str | None
    publication_year: int | None
    journal_name: str | None
    doi: str | None
    authors_text: str | None
    keywords: list[str]
    work_type: str | None
    open_access_status: str | None
    verification_status: LiteratureVerificationStatus
    current_decision: LiteratureDecisionStatus
    created_at: datetime
    updated_at: datetime
    allowed_actions: list[str]


class LiteratureRecordEnvelope(BaseModel):
    data: LiteratureRecordPublic
    meta: ResponseMeta


class LiteratureRecordListEnvelope(BaseModel):
    data: list[LiteratureRecordPublic]
    allowed_actions: list[str]
    pagination: PaginationMeta
    meta: ResponseMeta
