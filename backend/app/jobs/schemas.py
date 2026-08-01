import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models import JobStatus, JobTaskType
from app.projects.schemas import PaginationMeta, ResponseMeta


class JobErrorPublic(BaseModel):
    code: str
    message: str
    retryable: bool


class JobResultPublic(BaseModel):
    object_type: str
    object_id: uuid.UUID
    url: str | None = None


class JobPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    task_type: JobTaskType
    resource_type: str
    resource_id: uuid.UUID
    status: JobStatus
    progress_percent: int
    current_step: str | None
    total_steps: int | None
    completed_steps: int | None
    retry_count: int
    max_retries: int
    retryable: bool
    current_processing_run_id: uuid.UUID | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error: JobErrorPublic | None
    result: JobResultPublic | None


class JobEnvelope(BaseModel):
    data: JobPublic
    meta: ResponseMeta


class JobListEnvelope(BaseModel):
    data: list[JobPublic]
    pagination: PaginationMeta
    meta: ResponseMeta


class JobCancel(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class JobEventPublic(BaseModel):
    schema_version: str = "1.0"
    event_id: int
    event_type: str
    job_id: uuid.UUID
    project_id: uuid.UUID
    status: JobStatus
    progress_percent: int
    current_step: str | None
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime
