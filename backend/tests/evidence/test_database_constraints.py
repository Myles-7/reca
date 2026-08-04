import uuid

import pytest
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlmodel import Session

from app.models import (
    Artifact,
    ArtifactStatus,
    ArtifactType,
    Document,
    DocumentPage,
    EvidenceSpan,
    EvidenceType,
    FieldConfirmationStatus,
    FieldEvidenceStatus,
    LiteratureDecision,
    LiteratureDecisionStatus,
    LiteratureExtraction,
    LiteratureExtractionField,
    LiteratureExtractionFieldRevision,
    LiteratureFieldCode,
    LiteratureRecord,
    LiteratureSourceType,
    LocationVerificationStatus,
    ProjectType,
    ResearchProject,
    StorageProvider,
    User,
)


def _create_document_graph(
    db: Session, *, owner: User, suffix: str
) -> tuple[ResearchProject, Document, LiteratureRecord, DocumentPage]:
    project = ResearchProject(
        owner_id=owner.id,
        name=f"M3 constraints {suffix}",
        project_type=ProjectType.RESEARCH,
    )
    db.add(project)
    db.flush()
    artifact = Artifact(
        project_id=project.id,
        artifact_type=ArtifactType.PDF_DOCUMENT,
        filename=f"{suffix}.pdf",
        storage_provider=StorageProvider.MINIO,
        storage_key=f"m3-constraints/{uuid.uuid4()}.pdf",
        mime_type="application/pdf",
        size_bytes=1,
        sha256="a" * 64,
        is_original=True,
        is_immutable=True,
        status=ArtifactStatus.AVAILABLE,
        created_by=owner.id,
    )
    db.add(artifact)
    db.flush()
    document = Document(project_id=project.id, artifact_id=artifact.id, page_count=1)
    db.add(document)
    db.flush()
    literature = LiteratureRecord(
        project_id=project.id,
        document_id=document.id,
        source_type=LiteratureSourceType.USER_UPLOAD,
        title=f"Paper {suffix}",
        normalized_title=f"paper {suffix}",
    )
    page = DocumentPage(
        document_id=document.id,
        project_id=project.id,
        page_number=1,
        text_content="Verified source text.",
    )
    db.add(literature)
    db.add(page)
    db.flush()
    return project, document, literature, page


def _expect_integrity(db: Session, obj: object) -> None:
    savepoint = db.begin_nested()
    db.add(obj)
    with pytest.raises(IntegrityError):
        db.flush()
    savepoint.rollback()


def _expect_database_rejection(db: Session, obj: object) -> None:
    savepoint = db.begin_nested()
    db.add(obj)
    with pytest.raises(DBAPIError):
        db.flush()
    savepoint.rollback()


def test_m3_database_checks_unique_scope_and_append_only_guards(db: Session) -> None:
    owner = User(
        email=f"m3-constraints-{uuid.uuid4()}@example.com",
        hashed_password="not-used",
    )
    db.add(owner)
    db.flush()
    project, document, literature, page = _create_document_graph(
        db, owner=owner, suffix="one"
    )
    other_project, other_document, _, _ = _create_document_graph(
        db, owner=owner, suffix="two"
    )

    _expect_integrity(
        db,
        LiteratureExtraction(
            project_id=project.id,
            literature_record_id=literature.id,
            document_id=other_document.id,
            extraction_version=1,
            schema_version="1.0.0",
        ),
    )

    _expect_integrity(
        db,
        EvidenceSpan(
            project_id=project.id,
            document_id=document.id,
            document_page_id=page.id,
            page_number=1,
            source_text="Verified source text.",
            source_text_hash="INVALID",
            evidence_type=EvidenceType.FIELD_SUPPORT,
        ),
    )
    _expect_database_rejection(
        db,
        EvidenceSpan(
            project_id=project.id,
            document_id=document.id,
            document_page_id=page.id,
            page_number=1,
            source_text="Verified source text.",
            source_text_hash="b" * 64,
            evidence_type=EvidenceType.FIELD_SUPPORT,
            location_verification_status=LocationVerificationStatus.VERIFIED,
        ),
    )
    _expect_integrity(
        db,
        EvidenceSpan(
            project_id=other_project.id,
            document_id=document.id,
            page_number=1,
            source_text="Verified source text.",
            source_text_hash="b" * 64,
            evidence_type=EvidenceType.FIELD_SUPPORT,
        ),
    )

    extraction = LiteratureExtraction(
        project_id=project.id,
        literature_record_id=literature.id,
        document_id=document.id,
        extraction_version=1,
        schema_version="1.0.0",
    )
    span = EvidenceSpan(
        project_id=project.id,
        document_id=document.id,
        document_page_id=page.id,
        page_number=1,
        source_text="Verified source text.",
        source_text_hash="b" * 64,
        evidence_type=EvidenceType.FIELD_SUPPORT,
    )
    db.add(extraction)
    db.add(span)
    db.flush()

    field = LiteratureExtractionField(
        project_id=project.id,
        extraction_id=extraction.id,
        field_code=LiteratureFieldCode.TITLE,
        model_value_text="Original model title",
        value_text="Original model title",
        evidence_span_id=span.id,
        evidence_status=FieldEvidenceStatus.LOCATED,
    )
    db.add(field)
    db.flush()
    _expect_integrity(
        db,
        LiteratureExtractionField(
            project_id=project.id,
            extraction_id=extraction.id,
            field_code=LiteratureFieldCode.YEAR,
            evidence_status=FieldEvidenceStatus.NO_LOCATED_EVIDENCE,
        ),
    )
    _expect_integrity(
        db,
        LiteratureExtractionField(
            project_id=project.id,
            extraction_id=extraction.id,
            field_code=LiteratureFieldCode.SAMPLE_SIZE,
            evidence_status=FieldEvidenceStatus.LOCATION_UNCERTAIN,
            evidence_limitations="Candidate exists but location is uncertain.",
        ),
    )
    _expect_integrity(
        db,
        LiteratureExtractionField(
            project_id=project.id,
            extraction_id=extraction.id,
            field_code=LiteratureFieldCode.TITLE,
        ),
    )

    revision = LiteratureExtractionFieldRevision(
        project_id=project.id,
        field_id=field.id,
        revision_number=1,
        old_value_text="Original model title",
        new_value_text="Corrected title",
        old_evidence_span_id=span.id,
        new_evidence_span_id=span.id,
        old_confirmation_status=FieldConfirmationStatus.UNREVIEWED,
        new_confirmation_status=FieldConfirmationStatus.CONFIRMED,
        old_evidence_status=FieldEvidenceStatus.LOCATED,
        new_evidence_status=FieldEvidenceStatus.LOCATED,
        corrected_by_user_id=owner.id,
        correction_reason="Checked against the page",
    )
    decision = LiteratureDecision(
        project_id=project.id,
        literature_record_id=literature.id,
        decision=LiteratureDecisionStatus.INCLUDED,
        decided_by_user_id=owner.id,
    )
    db.add(revision)
    db.add(decision)
    db.flush()

    savepoint = db.begin_nested()
    revision.new_value_text = "History rewrite"
    with pytest.raises(DBAPIError, match="append-only"):
        db.flush()
    savepoint.rollback()
    db.refresh(revision)

    savepoint = db.begin_nested()
    decision.decision = LiteratureDecisionStatus.EXCLUDED
    with pytest.raises(DBAPIError, match="append-only"):
        db.flush()
    savepoint.rollback()
