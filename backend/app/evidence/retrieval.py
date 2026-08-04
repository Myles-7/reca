from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any

from sqlalchemy import exists
from sqlalchemy.orm import aliased
from sqlmodel import Session, col, select

from app.api.errors import ContractError
from app.evidence.schemas import (
    EvidenceCandidateDTO,
    EvidenceRetrievalMode,
    EvidenceSearchData,
    EvidenceSearchRequest,
)
from app.models import (
    Document,
    DocumentChunk,
    EvidenceSpan,
    LiteratureDecision,
    LiteratureDecisionStatus,
    LiteratureRecord,
    LocationVerificationStatus,
    User,
)
from app.projects import service as project_service

MAX_CANDIDATE_POOL = 500
_TOKEN_PATTERN = re.compile(r"[\w\u3400-\u9fff]+", re.UNICODE)


def _not_found() -> ContractError:
    return ContractError(
        status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
    )


def current_decision_condition(*, include_uncertain: bool = False) -> Any:
    successor = aliased(LiteratureDecision)
    allowed = [LiteratureDecisionStatus.INCLUDED]
    if include_uncertain:
        allowed.append(LiteratureDecisionStatus.UNCERTAIN)
    current_allowed = exists(
        select(LiteratureDecision.id).where(
            LiteratureDecision.project_id == LiteratureRecord.project_id,
            LiteratureDecision.literature_record_id == LiteratureRecord.id,
            col(LiteratureDecision.decision).in_(allowed),
            ~exists(
                select(successor.id).where(
                    successor.project_id == LiteratureDecision.project_id,
                    successor.literature_record_id
                    == LiteratureDecision.literature_record_id,
                    successor.supersedes_decision_id == LiteratureDecision.id,
                )
            ),
        )
    )
    if not include_uncertain:
        return current_allowed
    has_any_decision = exists(
        select(LiteratureDecision.id).where(
            LiteratureDecision.project_id == LiteratureRecord.project_id,
            LiteratureDecision.literature_record_id == LiteratureRecord.id,
        )
    )
    return current_allowed | ~has_any_decision


def current_included_literature(
    session: Session, *, project_id: uuid.UUID
) -> list[LiteratureRecord]:
    return list(
        session.exec(
            select(LiteratureRecord)
            .where(
                LiteratureRecord.project_id == project_id,
                col(LiteratureRecord.deleted_at).is_(None),
                current_decision_condition(),
            )
            .order_by(col(LiteratureRecord.id))
        ).all()
    )


def _tokens(value: str) -> set[str]:
    normalized = value.casefold()
    tokens = {token for token in _TOKEN_PATTERN.findall(normalized) if token}
    if normalized.strip():
        tokens.add(normalized.strip())
    return tokens


def _score(query: str, text: str) -> float:
    query_tokens = _tokens(query)
    if not query_tokens:
        return 0.0
    normalized = text.casefold()
    matched = sum(1 for token in query_tokens if token in normalized)
    return matched / len(query_tokens)


def search_evidence(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    payload: EvidenceSearchRequest,
) -> EvidenceSearchData:
    project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="project.read"
    )
    document_filter = set(payload.document_ids)
    if document_filter:
        visible = set(
            session.exec(
                select(Document.id).where(
                    Document.project_id == project_id,
                    col(Document.id).in_(document_filter),
                )
            ).all()
        )
        if visible != document_filter:
            raise _not_found()

    literature_rows = session.exec(
        select(LiteratureRecord).where(
            LiteratureRecord.project_id == project_id,
            col(LiteratureRecord.deleted_at).is_(None),
            current_decision_condition(
                include_uncertain=payload.include_uncertain_literature
            ),
        )
    ).all()
    literature_by_document = {
        row.document_id: row for row in literature_rows if row.document_id is not None
    }
    allowed_documents = set(literature_by_document)
    if document_filter:
        allowed_documents &= document_filter

    limitations: list[str] = []
    if payload.retrieval_mode == EvidenceRetrievalMode.HYBRID:
        limitations.append(
            "Vector retrieval is not enabled; native project-scoped keyword ranking was used."
        )
    if not allowed_documents:
        limitations.append(
            "No eligible current-literature documents contain searchable evidence."
        )
        return EvidenceSearchData(
            query=payload.query,
            retrieval_run_id=uuid.uuid4(),
            candidates=[],
            limitations=limitations,
        )

    retrieval_run_id = uuid.uuid4()
    ranked: list[tuple[float, str, dict[str, Any]]] = []
    spans = session.exec(
        select(EvidenceSpan).where(
            EvidenceSpan.project_id == project_id,
            col(EvidenceSpan.document_id).in_(allowed_documents),
            col(EvidenceSpan.invalidated_at).is_(None),
        )
    ).all()
    for span in spans:
        if (
            hashlib.sha256(span.source_text.encode("utf-8")).hexdigest()
            != span.source_text_hash
        ):
            limitations.append(
                "An EvidenceSpan with a source hash mismatch was excluded from retrieval."
            )
            continue
        score = _score(payload.query, span.source_text)
        if score <= 0:
            continue
        literature = literature_by_document[span.document_id]
        span_limitations: list[str] = []
        trusted_span_id = None
        if span.location_verification_status == LocationVerificationStatus.VERIFIED:
            trusted_span_id = span.id
        else:
            span_limitations.append(
                f"EvidenceSpan location status is {span.location_verification_status.value}; evidence_span_id is withheld."
            )
        ranked.append(
            (
                score,
                f"span:{span.id}",
                {
                    "project_id": project_id,
                    "literature_record_id": literature.id,
                    "document_id": span.document_id,
                    "chunk_id": span.chunk_id,
                    "page_number": span.page_number,
                    "source_text": span.source_text,
                    "source_text_hash": span.source_text_hash,
                    "evidence_span_id": trusted_span_id,
                    "keyword_score": score,
                    "limitations": span_limitations,
                },
            )
        )

    chunks = session.exec(
        select(DocumentChunk)
        .where(
            DocumentChunk.project_id == project_id,
            col(DocumentChunk.document_id).in_(allowed_documents),
        )
        .order_by(col(DocumentChunk.document_id), col(DocumentChunk.chunk_index))
        .limit(MAX_CANDIDATE_POOL)
    ).all()
    for chunk in chunks:
        source_text = chunk.content[:20_000]
        score = _score(payload.query, source_text)
        if score <= 0:
            continue
        literature = literature_by_document[chunk.document_id]
        chunk_limitations = [
            "Candidate is retrieved from DocumentChunk and has not been promoted to EvidenceSpan."
        ]
        if len(source_text) < len(chunk.content):
            chunk_limitations.append(
                "Chunk text was truncated to the candidate DTO limit."
            )
        ranked.append(
            (
                score,
                f"chunk:{chunk.id}",
                {
                    "project_id": project_id,
                    "literature_record_id": literature.id,
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.id,
                    "page_number": chunk.page_start,
                    "source_text": source_text,
                    "source_text_hash": hashlib.sha256(
                        source_text.encode("utf-8")
                    ).hexdigest(),
                    "evidence_span_id": None,
                    "keyword_score": score,
                    "limitations": chunk_limitations,
                },
            )
        )

    ranked.sort(key=lambda item: (-item[0], item[1]))
    candidates: list[EvidenceCandidateDTO] = []
    seen: set[tuple[uuid.UUID, int, str]] = set()
    for _, source_key, values in ranked:
        dedupe_key = (
            values["document_id"],
            values["page_number"],
            values["source_text_hash"],
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        candidates.append(
            EvidenceCandidateDTO(
                candidate_id=uuid.uuid5(retrieval_run_id, source_key),
                retrieval_run_id=retrieval_run_id,
                fused_rank=len(candidates) + 1,
                **values,
            )
        )
        if len(candidates) >= payload.top_k:
            break
    if not candidates:
        limitations.append(
            "No matching evidence was found in the eligible current literature set."
        )
    return EvidenceSearchData(
        query=payload.query,
        retrieval_run_id=retrieval_run_id,
        candidates=candidates,
        limitations=limitations,
    )
