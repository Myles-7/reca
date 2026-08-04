from __future__ import annotations

import hashlib
import uuid

import pytest
from sqlmodel import Session

from app.api.errors import ContractError
from app.evidence import review as evidence_review
from app.evidence.retrieval import search_evidence
from app.evidence.schemas import EvidenceSearchRequest, EvidenceSpanVerificationCreate
from app.models import (
    EvidenceSpan,
    EvidenceType,
    LiteratureDecision,
    LiteratureDecisionStatus,
    LocationVerificationStatus,
    UserDeclaredReadScope,
)
from tests.evidence.test_extraction_workflow import _graph


def _decision(
    db: Session,
    *,
    project_id: uuid.UUID,
    literature_id: uuid.UUID,
    actor_id: uuid.UUID,
    decision: LiteratureDecisionStatus,
) -> None:
    db.add(
        LiteratureDecision(
            project_id=project_id,
            literature_record_id=literature_id,
            decision=decision,
            decided_by_user_id=actor_id,
        )
    )
    db.commit()


def test_native_search_is_project_scoped_included_only_and_withholds_unverified_span_id(
    db: Session,
) -> None:
    actor, project, document, literature, page, chunk = _graph(db)
    _decision(
        db,
        project_id=project.id,
        literature_id=literature.id,
        actor_id=actor.id,
        decision=LiteratureDecisionStatus.INCLUDED,
    )
    source_text = "exactly 312 participants"
    char_start = page.text_content.index(source_text)
    span = EvidenceSpan(
        project_id=project.id,
        document_id=document.id,
        document_page_id=page.id,
        chunk_id=chunk.id,
        page_number=1,
        source_text=source_text,
        source_text_hash=hashlib.sha256(source_text.encode()).hexdigest(),
        char_start=char_start,
        char_end=char_start + len(source_text),
        evidence_type=EvidenceType.SAMPLE_DESCRIPTION,
        location_verification_status=LocationVerificationStatus.LOCATED,
    )
    db.add(span)
    db.commit()

    result = search_evidence(
        db,
        actor=actor,
        project_id=project.id,
        payload=EvidenceSearchRequest(query="312 participants", top_k=5),
    )
    assert result.candidates
    span_candidate = next(
        candidate
        for candidate in result.candidates
        if candidate.source_text == source_text
    )
    assert span_candidate.evidence_span_id is None
    assert "withheld" in " ".join(span_candidate.limitations)
    assert all(candidate.project_id == project.id for candidate in result.candidates)

    evidence_review.create_verification_record(
        db,
        actor=actor,
        span_id=span.id,
        payload=EvidenceSpanVerificationCreate(
            location_verification_status=LocationVerificationStatus.VERIFIED,
            user_declared_read_scope=UserDeclaredReadScope.SECTIONS,
            reviewed_page_numbers=[1],
            note="Reviewed the deterministic page offset.",
        ),
        idempotency_key=str(uuid.uuid4()),
    )
    verified = search_evidence(
        db,
        actor=actor,
        project_id=project.id,
        payload=EvidenceSearchRequest(query="312 participants", top_k=5),
    )
    verified_candidate = next(
        candidate
        for candidate in verified.candidates
        if candidate.source_text == source_text
    )
    assert verified_candidate.evidence_span_id == span.id


def test_search_returns_empty_limitations_and_hides_cross_project_document_ids(
    db: Session,
) -> None:
    actor, project, document, literature, _, _ = _graph(db)
    _decision(
        db,
        project_id=project.id,
        literature_id=literature.id,
        actor_id=actor.id,
        decision=LiteratureDecisionStatus.EXCLUDED,
    )
    empty = search_evidence(
        db,
        actor=actor,
        project_id=project.id,
        payload=EvidenceSearchRequest(query="participants", top_k=5),
    )
    assert empty.candidates == []
    assert empty.limitations

    with pytest.raises(ContractError) as hidden:
        search_evidence(
            db,
            actor=actor,
            project_id=project.id,
            payload=EvidenceSearchRequest(
                query="participants", document_ids=[uuid.uuid4()]
            ),
        )
    assert hidden.value.status_code == 404

    hybrid = search_evidence(
        db,
        actor=actor,
        project_id=project.id,
        payload=EvidenceSearchRequest(
            query="participants", document_ids=[document.id], retrieval_mode="HYBRID"
        ),
    )
    assert hybrid.candidates == []
    assert any("Vector retrieval is not enabled" in item for item in hybrid.limitations)
