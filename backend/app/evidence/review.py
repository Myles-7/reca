from __future__ import annotations

import hashlib
import uuid
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy import asc, desc, exists, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased
from sqlmodel import Session, col, select

from app.api.errors import ContractError
from app.core.observability import current_request_id
from app.evidence.schemas import (
    EvidenceSpanVerificationCreate,
    LiteratureDecisionCreate,
    LiteratureExtractionFieldCorrection,
    ManualEvidenceSpanCreate,
    MatrixSort,
    SortOrder,
)
from app.models import (
    AuditActorType,
    AuditLog,
    AuditOutcome,
    ConfidenceLevel,
    Document,
    DocumentPage,
    DocumentParserType,
    EvidenceReviewStatus,
    EvidenceSpan,
    EvidenceSpanVerificationRecord,
    FieldConfirmationStatus,
    FieldEvidenceStatus,
    LiteratureDecision,
    LiteratureDecisionStatus,
    LiteratureExtraction,
    LiteratureExtractionField,
    LiteratureExtractionFieldRevision,
    LiteratureFieldCode,
    LiteratureRecord,
    LocationVerificationStatus,
    ParserCoverage,
    ProjectMemberRole,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service

_EDIT_ROLES = frozenset({ProjectMemberRole.OWNER, ProjectMemberRole.EDITOR})
_REVIEW_ROLES = frozenset(
    {ProjectMemberRole.OWNER, ProjectMemberRole.EDITOR, ProjectMemberRole.REVIEWER}
)


def _not_found() -> ContractError:
    return ContractError(
        status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
    )


def _permission_denied() -> ContractError:
    return ContractError(
        status_code=403,
        code="PERMISSION_DENIED",
        message="The current user does not have permission for this action.",
    )


def _authorize_roles(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    roles: frozenset[ProjectMemberRole],
    for_update: bool = False,
) -> project_service.ProjectAccess:
    access = project_service.authorize_project(
        session,
        project_id=project_id,
        actor=actor,
        action="project.read",
        for_update=for_update,
    )
    if access.membership is None or access.membership.role not in roles:
        raise _permission_denied()
    return access


def _can_edit(access: project_service.ProjectAccess) -> bool:
    return access.membership is not None and access.membership.role in _EDIT_ROLES


def _can_review(access: project_service.ProjectAccess) -> bool:
    return access.membership is not None and access.membership.role in _REVIEW_ROLES


def _audit(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    action: str,
    object_type: str,
    object_id: uuid.UUID,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
) -> None:
    session.add(
        AuditLog(
            project_id=project_id,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
            action=action,
            object_type=object_type,
            object_id=object_id,
            before_snapshot=jsonable_encoder(before) if before is not None else None,
            after_snapshot=jsonable_encoder(after) if after is not None else None,
            reason=reason,
            request_id=current_request_id(),
            outcome=AuditOutcome.SUCCEEDED,
        )
    )


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="The operation conflicted with a concurrent change.",
            retryable=True,
        ) from exc


def _store_idempotency(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    method: str,
    path: str,
    key: str,
    digest: str,
    result: project_service.OperationResult,
) -> None:
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method=method,
        path_template=path,
        key=key,
        payload_hash=digest,
        result=result,
    )


def _field_actions(*, can_edit: bool) -> list[str]:
    return [
        "literature_extraction_field.read",
        *(["literature_extraction_field.update"] if can_edit else []),
    ]


def field_data(
    field: LiteratureExtractionField,
    *,
    can_edit: bool,
) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "id": field.id,
                "project_id": field.project_id,
                "extraction_id": field.extraction_id,
                "field_code": field.field_code,
                "model_value_text": field.model_value_text,
                "model_value_json": field.model_value_json,
                "value_text": field.value_text,
                "value_json": field.value_json,
                "confidence_score": field.confidence_score,
                "confidence_level": field.confidence_level,
                "evidence_span_id": field.evidence_span_id,
                "confirmation_status": field.confirmation_status,
                "evidence_status": field.evidence_status,
                "evidence_limitations": field.evidence_limitations,
                "lock_version": field.lock_version,
                "created_at": field.created_at,
                "updated_at": field.updated_at,
                "allowed_actions": _field_actions(can_edit=can_edit),
            }
        ),
    )


def _missing_field_data(
    extraction: LiteratureExtraction,
    field_code: LiteratureFieldCode,
) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "id": None,
                "project_id": extraction.project_id,
                "extraction_id": extraction.id,
                "field_code": field_code,
                "model_value_text": None,
                "model_value_json": None,
                "value_text": None,
                "value_json": None,
                "confidence_score": None,
                "confidence_level": ConfidenceLevel.UNKNOWN,
                "evidence_span_id": None,
                "confirmation_status": FieldConfirmationStatus.UNREVIEWED,
                "evidence_status": FieldEvidenceStatus.UNASSESSED,
                "evidence_limitations": None,
                "lock_version": 1,
                "created_at": None,
                "updated_at": None,
                "allowed_actions": [],
            }
        ),
    )


def extraction_data(
    session: Session,
    extraction: LiteratureExtraction,
    *,
    can_edit: bool,
) -> dict[str, Any]:
    rows = session.exec(
        select(LiteratureExtractionField).where(
            LiteratureExtractionField.extraction_id == extraction.id,
            LiteratureExtractionField.project_id == extraction.project_id,
        )
    ).all()
    by_code = {row.field_code: row for row in rows}
    fields = [
        field_data(by_code[code], can_edit=can_edit)
        if code in by_code
        else _missing_field_data(extraction, code)
        for code in LiteratureFieldCode
    ]
    actions = ["literature_extraction.read"]
    if can_edit:
        actions.append("literature_extraction.update_fields")
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "id": extraction.id,
                "project_id": extraction.project_id,
                "literature_record_id": extraction.literature_record_id,
                "document_id": extraction.document_id,
                "extraction_version": extraction.extraction_version,
                "schema_version": extraction.schema_version,
                "status": extraction.status,
                "overall_confidence": extraction.overall_confidence,
                "source_model_invocation_id": extraction.source_model_invocation_id,
                "processing_run_id": extraction.processing_run_id,
                "document_level_limitations": extraction.document_level_limitations
                or [],
                "lock_version": extraction.lock_version,
                "fields": fields,
                "allowed_actions": actions,
                "created_at": extraction.created_at,
                "updated_at": extraction.updated_at,
            }
        ),
    )


def get_extraction(
    session: Session, *, actor: User, extraction_id: uuid.UUID
) -> dict[str, Any]:
    extraction = session.get(LiteratureExtraction, extraction_id)
    if extraction is None:
        raise _not_found()
    access = project_service.authorize_project(
        session,
        project_id=extraction.project_id,
        actor=actor,
        action="project.read",
    )
    return extraction_data(session, extraction, can_edit=_can_edit(access))


def update_field(
    session: Session,
    *,
    actor: User,
    field_id: uuid.UUID,
    payload: LiteratureExtractionFieldCorrection,
    expected_lock_version: int,
    idempotency_key: str,
) -> project_service.OperationResult:
    field = session.get(LiteratureExtractionField, field_id)
    if field is None:
        raise _not_found()
    _authorize_roles(
        session,
        actor=actor,
        project_id=field.project_id,
        roles=_EDIT_ROLES,
        for_update=True,
    )
    path = "/api/v1/literature-extraction-fields/{field_id}"
    digest = project_service.request_hash(
        {"payload": payload, "expected_lock_version": expected_lock_version}
    )
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=field.project_id,
        method="PATCH",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    field = session.exec(
        select(LiteratureExtractionField)
        .where(
            LiteratureExtractionField.id == field_id,
            LiteratureExtractionField.project_id == field.project_id,
        )
        .with_for_update()
    ).one()
    if field.lock_version != expected_lock_version:
        raise ContractError(
            status_code=409,
            code="RESOURCE_VERSION_CONFLICT",
            message="LiteratureExtractionField changed since it was loaded.",
            details={
                "expected_lock_version": expected_lock_version,
                "current_lock_version": field.lock_version,
            },
        )
    extraction = session.exec(
        select(LiteratureExtraction).where(
            LiteratureExtraction.id == field.extraction_id,
            LiteratureExtraction.project_id == field.project_id,
        )
    ).one()
    span = None
    if payload.evidence_span_id is not None:
        span = session.exec(
            select(EvidenceSpan).where(
                EvidenceSpan.id == payload.evidence_span_id,
                EvidenceSpan.project_id == field.project_id,
                EvidenceSpan.document_id == extraction.document_id,
                col(EvidenceSpan.invalidated_at).is_(None),
            )
        ).first()
        if span is None:
            raise _not_found()
    previous = {
        "value_text": field.value_text,
        "value_json": field.value_json,
        "evidence_span_id": field.evidence_span_id,
        "confirmation_status": field.confirmation_status,
        "evidence_status": field.evidence_status,
        "lock_version": field.lock_version,
    }
    revision_number = session.exec(
        select(func.max(LiteratureExtractionFieldRevision.revision_number)).where(
            LiteratureExtractionFieldRevision.field_id == field.id
        )
    ).one()
    evidence_status = FieldEvidenceStatus.NO_LOCATED_EVIDENCE
    evidence_limitations: str | None = (
        f"NO_LOCATED_EVIDENCE: {payload.correction_reason}"
    )
    if span is not None:
        evidence_status = (
            FieldEvidenceStatus.LOCATION_UNCERTAIN
            if span.location_verification_status
            == LocationVerificationStatus.LOCATION_UNCERTAIN
            else FieldEvidenceStatus.LOCATED
        )
        evidence_limitations = (
            "Evidence location remains uncertain."
            if evidence_status == FieldEvidenceStatus.LOCATION_UNCERTAIN
            else None
        )
    revision = LiteratureExtractionFieldRevision(
        project_id=field.project_id,
        field_id=field.id,
        revision_number=(revision_number or 0) + 1,
        old_value_text=field.value_text,
        old_value_json=field.value_json,
        new_value_text=payload.value_text,
        new_value_json=payload.value_json,
        old_evidence_span_id=field.evidence_span_id,
        new_evidence_span_id=payload.evidence_span_id,
        old_confirmation_status=field.confirmation_status,
        new_confirmation_status=payload.confirmation_status,
        old_evidence_status=field.evidence_status,
        new_evidence_status=evidence_status,
        corrected_by_user_id=actor.id,
        correction_reason=payload.correction_reason,
        source_model_invocation_id=extraction.source_model_invocation_id,
        ai_schema_version=extraction.schema_version,
    )
    session.add(revision)
    field.value_text = payload.value_text
    field.value_json = payload.value_json
    field.evidence_span_id = payload.evidence_span_id
    field.confirmation_status = payload.confirmation_status
    field.evidence_status = evidence_status
    field.evidence_limitations = evidence_limitations
    field.corrected_by_user_id = actor.id
    field.correction_reason = payload.correction_reason
    field.lock_version += 1
    field.updated_at = get_datetime_utc()
    session.add(field)
    after = field_data(field, can_edit=True)
    _audit(
        session,
        actor=actor,
        project_id=field.project_id,
        action="LITERATURE_EXTRACTION_FIELD_CORRECTED",
        object_type="literature_extraction_field",
        object_id=field.id,
        before=previous,
        after=after,
        reason=payload.correction_reason,
    )
    result = project_service.OperationResult(data=after, status_code=200)
    _store_idempotency(
        session,
        actor=actor,
        project_id=field.project_id,
        method="PATCH",
        path=path,
        key=idempotency_key,
        digest=digest,
        result=result,
    )
    _commit(session)
    return result


def _document_coverage(session: Session, document: Document) -> ParserCoverage:
    pages = session.exec(
        select(DocumentPage).where(
            DocumentPage.document_id == document.id,
            DocumentPage.project_id == document.project_id,
        )
    ).all()
    if not pages:
        return ParserCoverage.UNKNOWN
    if (
        document.page_count is not None
        and len(pages) == document.page_count
        and all(page.text_content for page in pages)
    ):
        return ParserCoverage.FULL_TEXT
    return ParserCoverage.PARTIAL_TEXT


def _validated_boxes(
    *,
    document: Document,
    page: DocumentPage,
    boxes: list[Any],
) -> list[dict[str, Any]] | None:
    if not boxes:
        return None
    if document.parser_type == DocumentParserType.PYPDF:
        raise ContractError(
            status_code=409,
            code="EVIDENCE_COORDINATES_UNAVAILABLE",
            message="pypdf pages do not provide verified evidence coordinates.",
        )
    stored = (page.parser_metadata or {}).get("coordinates", [])
    if not isinstance(stored, list):
        stored = []
    normalized = [box.model_dump(mode="python") for box in boxes]
    for box in normalized:
        if box["page"] != page.page_number:
            raise ContractError(
                status_code=422,
                code="VALIDATION_ERROR",
                message="Bounding box page must match page_number.",
            )
        if page.width is not None and box["x"] + box["width"] > page.width:
            raise ContractError(
                status_code=422,
                code="VALIDATION_ERROR",
                message="Bounding box exceeds page width.",
            )
        if page.height is not None and box["y"] + box["height"] > page.height:
            raise ContractError(
                status_code=422,
                code="VALIDATION_ERROR",
                message="Bounding box exceeds page height.",
            )
        if box not in stored:
            raise ContractError(
                status_code=409,
                code="EVIDENCE_COORDINATES_UNVERIFIED",
                message="Bounding box is not present in parser provenance.",
            )
    return normalized


def _text_offsets(page_text: str, source_text: str) -> list[int]:
    offsets: list[int] = []
    cursor = 0
    while True:
        position = page_text.find(source_text, cursor)
        if position < 0:
            return offsets
        offsets.append(position)
        cursor = position + 1


def _context(
    page_text: str, char_start: int | None, char_end: int | None
) -> tuple[str | None, str | None]:
    if char_start is None or char_end is None:
        return None, None
    return page_text[max(0, char_start - 160) : char_start] or None, page_text[
        char_end : char_end + 160
    ] or None


def span_data(
    span: EvidenceSpan,
    *,
    can_review: bool,
) -> dict[str, Any]:
    actions = ["evidence_span.read"]
    if can_review:
        actions.append("evidence_span.verify")
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "id": span.id,
                "project_id": span.project_id,
                "document_id": span.document_id,
                "document_page_id": span.document_page_id,
                "chunk_id": span.chunk_id,
                "page_number": span.page_number,
                "section_path": span.section_path,
                "source_text": span.source_text,
                "context_before": span.context_before,
                "context_after": span.context_after,
                "bounding_boxes": span.bounding_boxes,
                "char_start": span.char_start,
                "char_end": span.char_end,
                "evidence_type": span.evidence_type,
                "confidence_level": span.confidence_level,
                "confidence_score": span.confidence_score,
                "parser_type": span.parser_type,
                "parser_version": span.parser_version,
                "model_invocation_id": span.model_invocation_id,
                "source_text_hash": span.source_text_hash,
                "location_verification_status": span.location_verification_status,
                "review_status": span.review_status,
                "parser_coverage": span.parser_coverage,
                "user_declared_read_scope": span.user_declared_read_scope,
                "reviewed_by_actor_type": span.reviewed_by_actor_type,
                "reviewed_by_actor_id": span.reviewed_by_actor_id,
                "reviewed_at": span.reviewed_at,
                "verified_by_actor_id": span.verified_by_actor_id,
                "verified_at": span.verified_at,
                "allowed_actions": actions,
                "created_at": span.created_at,
            }
        ),
    )


def create_manual_span(
    session: Session,
    *,
    actor: User,
    document_id: uuid.UUID,
    payload: ManualEvidenceSpanCreate,
    idempotency_key: str,
) -> project_service.OperationResult:
    document = session.get(Document, document_id)
    if document is None:
        raise _not_found()
    _authorize_roles(
        session,
        actor=actor,
        project_id=document.project_id,
        roles=_REVIEW_ROLES,
    )
    path = "/api/v1/documents/{document_id}/evidence-spans"
    digest = project_service.request_hash(payload)
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=document.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    page = session.exec(
        select(DocumentPage).where(
            DocumentPage.document_id == document.id,
            DocumentPage.project_id == document.project_id,
            DocumentPage.page_number == payload.page_number,
        )
    ).first()
    if page is None or not page.text_content:
        raise ContractError(
            status_code=409,
            code="EVIDENCE_PAGE_TEXT_MISSING",
            message="Parsed page text is required to create EvidenceSpan.",
        )
    offsets = _text_offsets(page.text_content, payload.source_text)
    if not offsets:
        raise ContractError(
            status_code=422,
            code="EVIDENCE_TEXT_NOT_FOUND",
            message="source_text is not present on the selected document page.",
        )
    char_start = offsets[0] if len(offsets) == 1 else None
    char_end = char_start + len(payload.source_text) if char_start is not None else None
    boxes = _validated_boxes(document=document, page=page, boxes=payload.bounding_boxes)
    before, after = _context(page.text_content, char_start, char_end)
    span = EvidenceSpan(
        project_id=document.project_id,
        document_id=document.id,
        document_page_id=page.id,
        page_number=page.page_number,
        source_text=payload.source_text,
        context_before=before,
        context_after=after,
        bounding_boxes=boxes,
        char_start=char_start,
        char_end=char_end,
        evidence_type=payload.evidence_type,
        confidence_level=ConfidenceLevel.UNKNOWN,
        parser_type=document.parser_type,
        parser_version=document.parser_version,
        source_text_hash=hashlib.sha256(
            payload.source_text.encode("utf-8")
        ).hexdigest(),
        location_verification_status=(
            LocationVerificationStatus.LOCATED
            if char_start is not None
            else LocationVerificationStatus.LOCATION_UNCERTAIN
        ),
        parser_coverage=_document_coverage(session, document),
        user_declared_read_scope=payload.user_declared_read_scope,
    )
    session.add(span)
    session.flush()
    data = span_data(span, can_review=True)
    _audit(
        session,
        actor=actor,
        project_id=span.project_id,
        action="EVIDENCE_SPAN_CREATED",
        object_type="evidence_span",
        object_id=span.id,
        after=data,
    )
    result = project_service.OperationResult(data=data, status_code=201)
    _store_idempotency(
        session,
        actor=actor,
        project_id=span.project_id,
        method="POST",
        path=path,
        key=idempotency_key,
        digest=digest,
        result=result,
    )
    _commit(session)
    return result


def get_span(session: Session, *, actor: User, span_id: uuid.UUID) -> dict[str, Any]:
    span = session.get(EvidenceSpan, span_id)
    if span is None or span.invalidated_at is not None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=span.project_id, actor=actor, action="project.read"
    )
    return span_data(span, can_review=_can_review(access))


def _verification_data(record: EvidenceSpanVerificationRecord) -> dict[str, Any]:
    return cast(dict[str, Any], jsonable_encoder(record))


def _validate_verified_location(
    session: Session,
    *,
    span: EvidenceSpan,
    reviewed_page_numbers: list[int],
) -> None:
    page = session.exec(
        select(DocumentPage).where(
            DocumentPage.id == span.document_page_id,
            DocumentPage.document_id == span.document_id,
            DocumentPage.project_id == span.project_id,
            DocumentPage.page_number == span.page_number,
        )
    ).first()
    if (
        page is None
        or not page.text_content
        or span.page_number not in reviewed_page_numbers
    ):
        raise ContractError(
            status_code=409,
            code="EVIDENCE_VERIFICATION_INCOMPLETE",
            message="VERIFIED requires the parsed source page to be reviewed.",
        )
    if (
        hashlib.sha256(span.source_text.encode("utf-8")).hexdigest()
        != span.source_text_hash
    ):
        raise ContractError(
            status_code=409,
            code="EVIDENCE_SOURCE_CHANGED",
            message="EvidenceSpan source hash no longer matches its source text.",
        )
    offset_valid = (
        span.char_start is not None
        and span.char_end is not None
        and page.text_content[span.char_start : span.char_end] == span.source_text
    )
    boxes_valid = False
    if span.bounding_boxes:
        stored = (page.parser_metadata or {}).get("coordinates", [])
        boxes_valid = isinstance(stored, list) and all(
            box in stored for box in span.bounding_boxes
        )
        if not boxes_valid:
            raise ContractError(
                status_code=409,
                code="EVIDENCE_SIDECAR_MISMATCH",
                message="Evidence coordinates cannot be verified against parser provenance.",
            )
    if not offset_valid and not boxes_valid:
        raise ContractError(
            status_code=409,
            code="EVIDENCE_VERIFICATION_INCOMPLETE",
            message="VERIFIED requires a deterministic source location.",
        )


def create_verification_record(
    session: Session,
    *,
    actor: User,
    span_id: uuid.UUID,
    payload: EvidenceSpanVerificationCreate,
    idempotency_key: str,
) -> project_service.OperationResult:
    span = session.get(EvidenceSpan, span_id)
    if span is None or span.invalidated_at is not None:
        raise _not_found()
    _authorize_roles(
        session,
        actor=actor,
        project_id=span.project_id,
        roles=_REVIEW_ROLES,
        for_update=True,
    )
    path = "/api/v1/evidence-spans/{evidence_span_id}/verification-records"
    digest = project_service.request_hash(payload)
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=span.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    span = session.exec(
        select(EvidenceSpan)
        .where(EvidenceSpan.id == span_id, EvidenceSpan.project_id == span.project_id)
        .with_for_update()
    ).one()
    if (
        span.location_verification_status == LocationVerificationStatus.VERIFIED
        and payload.location_verification_status != LocationVerificationStatus.VERIFIED
    ):
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="A VERIFIED EvidenceSpan cannot be downgraded in place.",
        )
    if payload.location_verification_status == LocationVerificationStatus.VERIFIED:
        _validate_verified_location(
            session,
            span=span,
            reviewed_page_numbers=payload.reviewed_page_numbers,
        )
    record = EvidenceSpanVerificationRecord(
        project_id=span.project_id,
        evidence_span_id=span.id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        location_verification_status=payload.location_verification_status,
        user_declared_read_scope=payload.user_declared_read_scope,
        reviewed_page_numbers=payload.reviewed_page_numbers,
        note=payload.note,
        source_text_hash=span.source_text_hash,
    )
    session.add(record)
    session.flush()
    now = get_datetime_utc()
    span.location_verification_status = payload.location_verification_status
    span.user_declared_read_scope = payload.user_declared_read_scope
    span.review_status = (
        EvidenceReviewStatus.CONFIRMED
        if payload.location_verification_status == LocationVerificationStatus.VERIFIED
        else EvidenceReviewStatus.REVIEWED
    )
    span.reviewed_by_actor_type = AuditActorType.USER
    span.reviewed_by_actor_id = str(actor.id)
    span.reviewed_at = now
    if payload.location_verification_status == LocationVerificationStatus.VERIFIED:
        span.verified_by_actor_id = str(actor.id)
        span.verified_at = now
    session.add(span)
    data = _verification_data(record)
    _audit(
        session,
        actor=actor,
        project_id=span.project_id,
        action="EVIDENCE_SPAN_VERIFICATION_RECORDED",
        object_type="evidence_span_verification_record",
        object_id=record.id,
        after=data,
        reason=payload.note,
    )
    result = project_service.OperationResult(data=data, status_code=201)
    _store_idempotency(
        session,
        actor=actor,
        project_id=span.project_id,
        method="POST",
        path=path,
        key=idempotency_key,
        digest=digest,
        result=result,
    )
    _commit(session)
    return result


def _current_decision(
    session: Session, *, project_id: uuid.UUID, literature_id: uuid.UUID
) -> LiteratureDecision | None:
    successor = aliased(LiteratureDecision)
    return session.exec(
        select(LiteratureDecision)
        .where(
            LiteratureDecision.project_id == project_id,
            LiteratureDecision.literature_record_id == literature_id,
            ~exists(
                select(successor.id).where(
                    successor.supersedes_decision_id == LiteratureDecision.id,
                    successor.project_id == project_id,
                    successor.literature_record_id == literature_id,
                )
            ),
        )
        .order_by(
            desc(col(LiteratureDecision.created_at)), desc(col(LiteratureDecision.id))
        )
    ).first()


def decision_data(
    decision: LiteratureDecision, *, current_decision_id: uuid.UUID | None
) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "id": decision.id,
                "project_id": decision.project_id,
                "literature_record_id": decision.literature_record_id,
                "decision": decision.decision,
                "reason_code": decision.reason_code,
                "reason_text": decision.reason_text,
                "ai_recommendation": decision.ai_recommendation,
                "ai_score": decision.ai_score,
                "decided_by_user_id": decision.decided_by_user_id,
                "supersedes_decision_id": decision.supersedes_decision_id,
                "is_current": decision.id == current_decision_id,
                "created_at": decision.created_at,
            }
        ),
    )


def create_decision(
    session: Session,
    *,
    actor: User,
    literature_id: uuid.UUID,
    payload: LiteratureDecisionCreate,
    idempotency_key: str,
) -> project_service.OperationResult:
    literature = session.get(LiteratureRecord, literature_id)
    if literature is None or literature.deleted_at is not None:
        raise _not_found()
    _authorize_roles(
        session,
        actor=actor,
        project_id=literature.project_id,
        roles=_REVIEW_ROLES,
        for_update=True,
    )
    path = "/api/v1/literature/{literature_id}/decisions"
    digest = project_service.request_hash(payload)
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=literature.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    literature = session.exec(
        select(LiteratureRecord)
        .where(
            LiteratureRecord.id == literature.id,
            LiteratureRecord.project_id == literature.project_id,
            col(LiteratureRecord.deleted_at).is_(None),
        )
        .with_for_update()
    ).one()
    previous = _current_decision(
        session, project_id=literature.project_id, literature_id=literature.id
    )
    decision = LiteratureDecision(
        project_id=literature.project_id,
        literature_record_id=literature.id,
        decision=payload.decision,
        reason_code=payload.reason_code,
        reason_text=payload.reason_text,
        decided_by_user_id=actor.id,
        supersedes_decision_id=previous.id if previous is not None else None,
    )
    session.add(decision)
    session.flush()
    before = {
        "current_decision": literature.current_decision,
        "current_decision_id": previous.id if previous is not None else None,
    }
    literature.current_decision = payload.decision
    literature.updated_at = get_datetime_utc()
    session.add(literature)
    data = decision_data(decision, current_decision_id=decision.id)
    _audit(
        session,
        actor=actor,
        project_id=literature.project_id,
        action="LITERATURE_DECISION_CREATED",
        object_type="literature_decision",
        object_id=decision.id,
        before=before,
        after=data,
        reason=payload.reason_text,
    )
    result = project_service.OperationResult(data=data, status_code=201)
    _store_idempotency(
        session,
        actor=actor,
        project_id=literature.project_id,
        method="POST",
        path=path,
        key=idempotency_key,
        digest=digest,
        result=result,
    )
    _commit(session)
    return result


def list_decisions(
    session: Session, *, actor: User, literature_id: uuid.UUID
) -> list[dict[str, Any]]:
    literature = session.get(LiteratureRecord, literature_id)
    if literature is None or literature.deleted_at is not None:
        raise _not_found()
    project_service.authorize_project(
        session,
        project_id=literature.project_id,
        actor=actor,
        action="project.read",
    )
    current = _current_decision(
        session, project_id=literature.project_id, literature_id=literature.id
    )
    rows = session.exec(
        select(LiteratureDecision)
        .where(
            LiteratureDecision.project_id == literature.project_id,
            LiteratureDecision.literature_record_id == literature.id,
        )
        .order_by(
            asc(col(LiteratureDecision.created_at)), asc(col(LiteratureDecision.id))
        )
    ).all()
    return [
        decision_data(
            row, current_decision_id=current.id if current is not None else None
        )
        for row in rows
    ]


def _matrix_field(
    field: LiteratureExtractionField | None, field_code: LiteratureFieldCode
) -> dict[str, Any]:
    if field is None:
        return cast(
            dict[str, Any],
            jsonable_encoder(
                {
                    "field_code": field_code,
                    "value_text": None,
                    "value_json": None,
                    "confidence_level": ConfidenceLevel.UNKNOWN,
                    "confidence_score": None,
                    "confirmation_status": FieldConfirmationStatus.UNREVIEWED,
                    "evidence_status": FieldEvidenceStatus.UNASSESSED,
                    "evidence_span_id": None,
                    "evidence_limitations": None,
                    "lock_version": None,
                }
            ),
        )
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "field_code": field.field_code,
                "value_text": field.value_text,
                "value_json": field.value_json,
                "confidence_level": field.confidence_level,
                "confidence_score": field.confidence_score,
                "confirmation_status": field.confirmation_status,
                "evidence_status": field.evidence_status,
                "evidence_span_id": field.evidence_span_id,
                "evidence_limitations": field.evidence_limitations,
                "lock_version": field.lock_version,
            }
        ),
    )


def list_matrix(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    included_only: bool,
    field_codes: list[LiteratureFieldCode] | None,
    page: int,
    page_size: int,
    sort: MatrixSort,
    order: SortOrder,
) -> tuple[list[dict[str, Any]], int, list[str]]:
    access = project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="project.read"
    )
    selected_codes = field_codes or list(LiteratureFieldCode)
    if len(selected_codes) != len(set(selected_codes)):
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="field_codes cannot contain duplicates.",
        )
    conditions: list[Any] = [
        LiteratureRecord.project_id == project_id,
        col(LiteratureRecord.deleted_at).is_(None),
    ]
    if included_only:
        successor = aliased(LiteratureDecision)
        conditions.append(
            exists(
                select(LiteratureDecision.id).where(
                    LiteratureDecision.project_id == project_id,
                    LiteratureDecision.literature_record_id == LiteratureRecord.id,
                    LiteratureDecision.decision == LiteratureDecisionStatus.INCLUDED,
                    ~exists(
                        select(successor.id).where(
                            successor.supersedes_decision_id == LiteratureDecision.id,
                            successor.project_id == LiteratureDecision.project_id,
                            successor.literature_record_id
                            == LiteratureDecision.literature_record_id,
                        )
                    ),
                )
            )
        )
    total = int(
        session.exec(
            select(func.count()).select_from(LiteratureRecord).where(*conditions)
        ).one()
    )
    sort_column: Any = {
        MatrixSort.CREATED_AT: LiteratureRecord.created_at,
        MatrixSort.TITLE: LiteratureRecord.normalized_title,
        MatrixSort.YEAR: LiteratureRecord.publication_year,
        MatrixSort.DECISION: LiteratureRecord.current_decision,
    }[sort]
    ordering: Any = asc(sort_column) if order == SortOrder.ASC else desc(sort_column)
    records = session.exec(
        select(LiteratureRecord)
        .where(*conditions)
        .order_by(ordering, asc(col(LiteratureRecord.id)))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    can_edit = _can_edit(access)
    can_review = _can_review(access)
    rows: list[dict[str, Any]] = []
    for literature in records:
        current_decision = _current_decision(
            session, project_id=project_id, literature_id=literature.id
        )
        extraction = session.exec(
            select(LiteratureExtraction)
            .where(
                LiteratureExtraction.project_id == project_id,
                LiteratureExtraction.literature_record_id == literature.id,
            )
            .order_by(
                desc(col(LiteratureExtraction.extraction_version)),
                desc(col(LiteratureExtraction.created_at)),
            )
        ).first()
        by_code: dict[LiteratureFieldCode, LiteratureExtractionField] = {}
        if extraction is not None:
            fields = session.exec(
                select(LiteratureExtractionField).where(
                    LiteratureExtractionField.project_id == project_id,
                    LiteratureExtractionField.extraction_id == extraction.id,
                )
            ).all()
            by_code = {field.field_code: field for field in fields}
        actions = ["literature.read"]
        if can_edit:
            actions.extend(["literature.extract", "literature.update_fields"])
        if can_review:
            actions.append("literature.decide")
        rows.append(
            cast(
                dict[str, Any],
                jsonable_encoder(
                    {
                        "literature_record_id": literature.id,
                        "document_id": literature.document_id,
                        "extraction_id": extraction.id
                        if extraction is not None
                        else None,
                        "extraction_status": (
                            extraction.status if extraction is not None else None
                        ),
                        "title": literature.title,
                        "authors_text": literature.authors_text,
                        "publication_year": literature.publication_year,
                        "current_decision": (
                            current_decision.decision
                            if current_decision is not None
                            else LiteratureDecisionStatus.UNCERTAIN
                        ),
                        "fields": [
                            _matrix_field(by_code.get(code), code)
                            for code in selected_codes
                        ],
                        "allowed_actions": actions,
                    }
                ),
            )
        )
    workspace_actions = ["literature_matrix.read"]
    if can_edit:
        workspace_actions.extend(
            [
                "literature.extract",
                "evidence_span.create",
                "evidence.search",
                "evidence_summary.create",
            ]
        )
    if can_review:
        workspace_actions.extend(["evidence_span.verify", "literature.decide"])
    return rows, total, workspace_actions
