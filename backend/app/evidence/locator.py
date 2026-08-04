from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from typing import Any

from sqlmodel import Session, select

from app.evidence.schemas import CandidateEvidence, EvidenceBoundingBox
from app.models import (
    ConfidenceLevel,
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentParseConfidence,
    DocumentParserType,
    EvidenceType,
    FieldEvidenceStatus,
    LiteratureFieldCode,
    LiteratureRecord,
    LocationVerificationStatus,
    ParserCoverage,
)


class EvidenceLocatorError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class EvidenceSourceSnapshot:
    project_id: uuid.UUID
    literature_record_id: uuid.UUID
    document_id: uuid.UUID
    document_page_id: uuid.UUID
    page_number: int
    page_text: str
    page_width: float | None
    page_height: float | None
    page_metadata: dict[str, Any] | None
    chunk_id: uuid.UUID | None
    chunk_page_start: int | None
    chunk_page_end: int | None
    chunk_content: str | None
    chunk_section_path: list[str] | None
    chunk_metadata: dict[str, Any] | None
    parser_type: DocumentParserType
    parser_version: str | None
    parse_confidence: DocumentParseConfidence
    parser_coverage: ParserCoverage


@dataclass(frozen=True)
class LocatedEvidence:
    source: EvidenceSourceSnapshot
    source_text: str
    source_text_hash: str
    char_start: int | None
    char_end: int | None
    bounding_boxes: list[dict[str, float | int]] | None
    evidence_status: FieldEvidenceStatus
    location_status: LocationVerificationStatus
    confidence_level: ConfidenceLevel
    limitations: tuple[str, ...]


def _fail(code: str, message: str) -> EvidenceLocatorError:
    return EvidenceLocatorError(code, message)


def _confidence_level(score: float, source: EvidenceSourceSnapshot) -> ConfidenceLevel:
    if source.parser_type == DocumentParserType.PYPDF:
        return ConfidenceLevel.LOW
    if source.parse_confidence == DocumentParseConfidence.LOW:
        return ConfidenceLevel.LOW
    if score >= 0.8:
        return ConfidenceLevel.HIGH
    if score >= 0.5:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def _stored_coordinates(source: EvidenceSourceSnapshot) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for metadata in (source.page_metadata, source.chunk_metadata):
        coordinates = (metadata or {}).get("coordinates", [])
        if isinstance(coordinates, list):
            values.extend(item for item in coordinates if isinstance(item, dict))
    return values


def _box_dict(box: EvidenceBoundingBox) -> dict[str, float | int]:
    return box.model_dump(mode="python")


def _validate_boxes(
    boxes: list[EvidenceBoundingBox], source: EvidenceSourceSnapshot
) -> list[dict[str, float | int]] | None:
    if not boxes:
        return None
    if source.parser_type == DocumentParserType.PYPDF:
        raise _fail(
            "EVIDENCE_COORDINATES_UNAVAILABLE",
            "pypdf output cannot provide evidence coordinates.",
        )
    stored = _stored_coordinates(source)
    normalized = [_box_dict(box) for box in boxes]
    for box in normalized:
        if (
            source.page_width is not None
            and float(box["x"]) + float(box["width"]) > source.page_width
        ):
            raise _fail(
                "EVIDENCE_BOX_OUT_OF_BOUNDS", "Bounding box exceeds page width."
            )
        if (
            source.page_height is not None
            and float(box["y"]) + float(box["height"]) > source.page_height
        ):
            raise _fail(
                "EVIDENCE_BOX_OUT_OF_BOUNDS", "Bounding box exceeds page height."
            )
        if box not in stored:
            raise _fail(
                "EVIDENCE_COORDINATES_UNVERIFIED",
                "Bounding box is not present in parser provenance.",
            )
    return normalized


def validate_candidate(
    candidate: CandidateEvidence,
    *,
    source: EvidenceSourceSnapshot,
    confidence_score: float,
) -> LocatedEvidence:
    if candidate.project_id != source.project_id:
        raise _fail(
            "EVIDENCE_PROJECT_MISMATCH", "Candidate belongs to another project."
        )
    if candidate.literature_record_id != source.literature_record_id:
        raise _fail(
            "EVIDENCE_LITERATURE_MISMATCH",
            "Candidate belongs to another LiteratureRecord.",
        )
    if candidate.document_id != source.document_id:
        raise _fail(
            "EVIDENCE_DOCUMENT_MISMATCH", "Candidate belongs to another Document."
        )
    if candidate.page_number != source.page_number:
        raise _fail(
            "EVIDENCE_PAGE_MISMATCH", "Candidate page does not match the source page."
        )
    if candidate.chunk_id != source.chunk_id:
        raise _fail(
            "EVIDENCE_CHUNK_MISMATCH",
            "Candidate chunk does not match the source chunk.",
        )
    if source.chunk_id is not None:
        if (
            source.chunk_page_start is None
            or source.chunk_page_end is None
            or not source.chunk_page_start
            <= source.page_number
            <= source.chunk_page_end
        ):
            raise _fail(
                "EVIDENCE_CHUNK_PAGE_MISMATCH", "Chunk does not cover the page."
            )
        if (
            source.chunk_content is None
            or candidate.source_text not in source.chunk_content
        ):
            raise _fail(
                "EVIDENCE_TEXT_NOT_IN_CHUNK",
                "Candidate text is not present in the chunk.",
            )

    computed_hash = hashlib.sha256(candidate.source_text.encode("utf-8")).hexdigest()
    if candidate.source_text_hash != computed_hash:
        raise _fail("EVIDENCE_HASH_MISMATCH", "Candidate source hash is invalid.")
    offsets: list[int] = []
    cursor = 0
    while True:
        position = source.page_text.find(candidate.source_text, cursor)
        if position < 0:
            break
        offsets.append(position)
        cursor = position + 1
    if not offsets:
        raise _fail(
            "EVIDENCE_TEXT_NOT_FOUND", "Candidate text is not present on the page."
        )

    char_start = candidate.char_start
    char_end = candidate.char_end
    if char_start is not None and char_end is not None:
        if char_end > len(source.page_text):
            raise _fail(
                "EVIDENCE_OFFSET_OUT_OF_BOUNDS", "Candidate offsets exceed the page."
            )
        if source.page_text[char_start:char_end] != candidate.source_text:
            raise _fail(
                "EVIDENCE_OFFSET_MISMATCH",
                "Candidate offsets do not select source_text.",
            )
    elif len(offsets) == 1:
        char_start = offsets[0]
        char_end = char_start + len(candidate.source_text)

    boxes = _validate_boxes(candidate.bounding_boxes, source)
    ambiguous = char_start is None or char_end is None
    limitations = list(candidate.limitations)
    if ambiguous:
        limitations.append(
            "Source text occurs multiple times on the page; location is uncertain."
        )
    if source.parser_type == DocumentParserType.PYPDF:
        limitations.append(
            "pypdf provides page text without verified sections or coordinates."
        )
    limitations = list(dict.fromkeys(limitations))
    return LocatedEvidence(
        source=source,
        source_text=candidate.source_text,
        source_text_hash=computed_hash,
        char_start=char_start,
        char_end=char_end,
        bounding_boxes=boxes,
        evidence_status=(
            FieldEvidenceStatus.LOCATION_UNCERTAIN
            if ambiguous
            else FieldEvidenceStatus.LOCATED
        ),
        location_status=(
            LocationVerificationStatus.LOCATION_UNCERTAIN
            if ambiguous
            else LocationVerificationStatus.LOCATED
        ),
        confidence_level=_confidence_level(confidence_score, source),
        limitations=tuple(limitations),
    )


def _coverage(document: Document, pages: list[DocumentPage]) -> ParserCoverage:
    if not pages:
        return ParserCoverage.UNKNOWN
    if (
        document.page_count is not None
        and len(pages) == document.page_count
        and all(page.text_content for page in pages)
    ):
        return ParserCoverage.FULL_TEXT
    return ParserCoverage.PARTIAL_TEXT


def load_source_snapshot(
    session: Session, candidate: CandidateEvidence
) -> EvidenceSourceSnapshot:
    literature = session.exec(
        select(LiteratureRecord).where(
            LiteratureRecord.id == candidate.literature_record_id,
            LiteratureRecord.project_id == candidate.project_id,
            LiteratureRecord.document_id == candidate.document_id,
        )
    ).first()
    document = session.exec(
        select(Document).where(
            Document.id == candidate.document_id,
            Document.project_id == candidate.project_id,
        )
    ).first()
    if literature is None or document is None:
        raise _fail("EVIDENCE_SOURCE_NOT_FOUND", "Candidate source is unavailable.")
    page = session.exec(
        select(DocumentPage).where(
            DocumentPage.document_id == document.id,
            DocumentPage.project_id == document.project_id,
            DocumentPage.page_number == candidate.page_number,
        )
    ).first()
    if page is None or not page.text_content:
        raise _fail("EVIDENCE_PAGE_TEXT_MISSING", "Parsed page text is unavailable.")
    chunk = None
    if candidate.chunk_id is not None:
        chunk = session.exec(
            select(DocumentChunk).where(
                DocumentChunk.id == candidate.chunk_id,
                DocumentChunk.document_id == document.id,
                DocumentChunk.project_id == document.project_id,
            )
        ).first()
        if chunk is None:
            raise _fail("EVIDENCE_CHUNK_NOT_FOUND", "Candidate chunk is unavailable.")
    pages = session.exec(
        select(DocumentPage).where(
            DocumentPage.document_id == document.id,
            DocumentPage.project_id == document.project_id,
        )
    ).all()
    return EvidenceSourceSnapshot(
        project_id=document.project_id,
        literature_record_id=literature.id,
        document_id=document.id,
        document_page_id=page.id,
        page_number=page.page_number,
        page_text=page.text_content,
        page_width=page.width,
        page_height=page.height,
        page_metadata=page.parser_metadata,
        chunk_id=chunk.id if chunk is not None else None,
        chunk_page_start=chunk.page_start if chunk is not None else None,
        chunk_page_end=chunk.page_end if chunk is not None else None,
        chunk_content=chunk.content if chunk is not None else None,
        chunk_section_path=chunk.section_path if chunk is not None else None,
        chunk_metadata=chunk.chunk_metadata if chunk is not None else None,
        parser_type=document.parser_type or DocumentParserType.NONE,
        parser_version=document.parser_version,
        parse_confidence=document.parse_confidence or DocumentParseConfidence.UNKNOWN,
        parser_coverage=_coverage(document, list(pages)),
    )


def locate_candidate(
    session: Session,
    candidate: CandidateEvidence,
    *,
    confidence_score: float,
) -> LocatedEvidence:
    return validate_candidate(
        candidate,
        source=load_source_snapshot(session, candidate),
        confidence_score=confidence_score,
    )


def evidence_type_for_field(field_code: LiteratureFieldCode) -> EvidenceType:
    if field_code == LiteratureFieldCode.RESEARCH_DESIGN:
        return EvidenceType.METHOD_DESCRIPTION
    if field_code == LiteratureFieldCode.ANALYSIS_METHOD:
        return EvidenceType.METHOD_DESCRIPTION
    if field_code == LiteratureFieldCode.SAMPLE_SIZE:
        return EvidenceType.SAMPLE_DESCRIPTION
    if field_code == LiteratureFieldCode.LIMITATION:
        return EvidenceType.LIMITATION
    return EvidenceType.FIELD_SUPPORT
