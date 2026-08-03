import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models import ArtifactStatus, ArtifactType
from app.projects.schemas import PaginationMeta, ResponseMeta


class ArtifactUploadInitiate(BaseModel):
    artifact_type: ArtifactType
    filename: str = Field(min_length=1, max_length=1024)
    mime_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    is_original: bool
    source_artifact_id: uuid.UUID | None = None


class ArtifactUploadComplete(BaseModel):
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class ArtifactUploadSession(BaseModel):
    upload_id: uuid.UUID
    artifact_id: uuid.UUID
    status: ArtifactStatus
    upload_method: str
    upload_url: str
    required_headers: dict[str, str]
    expires_at: datetime


class ArtifactUploadEnvelope(BaseModel):
    data: ArtifactUploadSession
    meta: ResponseMeta


class ArtifactPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    artifact_type: ArtifactType
    filename: str
    original_filename: str | None
    mime_type: str
    size_bytes: int
    sha256: str
    source_artifact_id: uuid.UUID | None
    is_original: bool
    is_immutable: bool
    status: ArtifactStatus
    created_by: uuid.UUID | None
    created_at: datetime
    deleted_at: datetime | None
    allowed_actions: list[str]


class ArtifactResponseMeta(ResponseMeta):
    duplicate_of_artifact_id: uuid.UUID | None = None


class ArtifactEnvelope(BaseModel):
    data: ArtifactPublic
    meta: ArtifactResponseMeta


class ArtifactListEnvelope(BaseModel):
    data: list[ArtifactPublic]
    allowed_actions: list[str]
    pagination: PaginationMeta
    meta: ResponseMeta


class ArtifactDownload(BaseModel):
    artifact_id: uuid.UUID
    download_url: str
    expires_at: datetime
    disposition_filename: str


class ArtifactDownloadEnvelope(BaseModel):
    data: ArtifactDownload
    meta: ResponseMeta


class ArtifactFilters(BaseModel):
    artifact_type: ArtifactType | None = None
    status: ArtifactStatus | None = None
    is_original: bool | None = None
    q: str | None = None
    page: int = 1
    page_size: int = 20


ArtifactData = dict[str, Any]
