from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.artifacts.schemas import ArtifactPublic
from app.models import (
    DocumentParseConfidence,
    DocumentParserType,
    DocumentType,
    JobStatus,
)
from app.projects.schemas import ResponseMeta


class DocumentParseRequest(BaseModel):
    allow_fallback: bool = True
    extract_coordinates: bool = True


class DocumentPagePublic(BaseModel):
    document_id: uuid.UUID
    project_id: uuid.UUID
    page_number: int
    printed_page_label: str | None
    text_content: str | None
    width: float | None
    height: float | None
    parser_metadata: dict[str, Any] | None
    created_at: datetime


class DocumentPageEnvelope(BaseModel):
    data: DocumentPagePublic
    meta: ResponseMeta


class DocumentPageListEnvelope(BaseModel):
    data: list[DocumentPagePublic]
    meta: ResponseMeta


class DocumentPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    artifact_id: uuid.UUID
    literature_record_id: uuid.UUID | None
    document_type: DocumentType
    parser_type: DocumentParserType | None
    parser_version: str | None
    parse_status: JobStatus
    page_count: int | None
    language: str | None
    is_scanned: bool | None
    parse_confidence: DocumentParseConfidence | None
    created_at: datetime
    updated_at: datetime
    allowed_actions: list[str]


class DocumentUploadData(BaseModel):
    artifact: ArtifactPublic
    document: DocumentPublic


class DocumentUploadMeta(ResponseMeta):
    duplicate_of_artifact_id: uuid.UUID | None = None


class DocumentUploadEnvelope(BaseModel):
    data: DocumentUploadData
    meta: DocumentUploadMeta


class DocumentEnvelope(BaseModel):
    data: DocumentPublic
    meta: ResponseMeta
