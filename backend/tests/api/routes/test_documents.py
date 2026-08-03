import hashlib
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app import crud
from app.adapters.storage import StorageError, StorageObjectExists
from app.artifacts import service as artifact_service
from app.core.config import settings
from app.models import (
    Artifact,
    ArtifactStatus,
    AuditLog,
    Document,
    DocumentPage,
    LiteratureRecord,
    LiteratureSourceType,
    UserCreate,
)
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_lower_string

TEXT_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog >>\nendobj\n"
    b"2 0 obj\n<< /Length 20 >>\nstream\n BT (RECA) Tj ET\nendstream\nendobj\n"
    b"xref\n0 3\n0000000000 65535 f \n"
    b"trailer\n<< /Root 1 0 R /Size 3 >>\nstartxref\n100\n%%EOF\n"
)
SCANNED_PDF = (
    b"%PDF-1.4\n1 0 obj\n<< /Type /XObject /Subtype /Image >>\nendobj\n"
    b"trailer\n<< /Size 2 >>\nstartxref\n60\n%%EOF\n"
)
ENCRYPTED_PDF = (
    b"%PDF-1.4\n1 0 obj\n<< /Encrypt 2 0 R >>\nendobj\n"
    b"trailer\n<< /Size 2 >>\nstartxref\n45\n%%EOF\n"
)


class MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_file_once(
        self, *, object_key: str, path: Path, content_sha256: str, size_bytes: int
    ) -> None:
        content = path.read_bytes()
        assert len(content) == size_bytes
        assert hashlib.sha256(content).hexdigest() == content_sha256
        if object_key in self.objects:
            raise StorageObjectExists("already exists")
        self.objects[object_key] = content

    def download_to_path(self, *, object_key: str, path: Path) -> None:
        try:
            path.write_bytes(self.objects[object_key])
        except KeyError as error:
            raise StorageError("not found") from error

    def presign_download(self, *, object_key: str, expires_seconds: int) -> str:
        if object_key not in self.objects:
            raise StorageError("not found")
        return f"https://download.test/object?expires={expires_seconds}"


@pytest.fixture
def memory_storage(monkeypatch: pytest.MonkeyPatch) -> MemoryStorage:
    backend = MemoryStorage()
    monkeypatch.setattr(artifact_service, "storage", backend)
    return backend


def create_project(client: TestClient, headers: dict[str, str]) -> dict[str, object]:
    response = client.post(
        "/api/v1/projects",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"name": "Document project", "project_type": "RESEARCH"},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def upload(
    client: TestClient,
    headers: dict[str, str],
    project_id: object,
    *,
    content: bytes = TEXT_PDF,
    filename: str = "paper.pdf",
    mime_type: str = "application/pdf",
    key: str | None = None,
    literature_record_id: uuid.UUID | None = None,
) -> object:
    data: dict[str, str] = {"document_type": "SCHOLARLY_PDF"}
    if literature_record_id is not None:
        data["literature_record_id"] = str(literature_record_id)
    return client.post(
        f"/api/v1/projects/{project_id}/documents",
        headers={**headers, "Idempotency-Key": key or str(uuid.uuid4())},
        files={"file": (filename, content, mime_type)},
        data=data,
    )


def test_pdf_upload_creates_immutable_artifact_and_unmatched_document(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    project = create_project(client, normal_user_token_headers)
    response = upload(client, normal_user_token_headers, project["id"])

    assert response.status_code == 201, response.text
    payload = response.json()
    artifact_data = payload["data"]["artifact"]
    document_data = payload["data"]["document"]
    assert artifact_data["status"] == "AVAILABLE"
    assert artifact_data["is_original"] is True
    assert artifact_data["is_immutable"] is True
    assert artifact_data["sha256"] == hashlib.sha256(TEXT_PDF).hexdigest()
    assert document_data["artifact_id"] == artifact_data["id"]
    assert document_data["literature_record_id"] is None
    assert document_data["parse_status"] == "DRAFT"
    assert document_data["parser_type"] == "NONE"
    assert document_data["is_scanned"] is False
    assert document_data["allowed_actions"] == [
        "document.read",
        "document.upload",
        "document.parse",
    ]
    assert "storage_key" not in response.text

    artifact = db.get(Artifact, uuid.UUID(artifact_data["id"]))
    assert artifact is not None and artifact.status == ArtifactStatus.AVAILABLE
    assert memory_storage.objects[artifact.storage_key] == TEXT_PDF
    detail = client.get(
        f"/api/v1/documents/{document_data['id']}",
        headers=normal_user_token_headers,
    )
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == document_data["id"]
    assert detail.json()["data"]["artifact_id"] == artifact_data["id"]
    assert detail.json()["data"]["literature_record_id"] is None
    assert (
        db.exec(
            select(LiteratureRecord).where(
                LiteratureRecord.project_id == uuid.UUID(str(project["id"])),
                LiteratureRecord.document_id == uuid.UUID(document_data["id"]),
            )
        ).first()
        is None
    )
    actions = db.exec(
        select(AuditLog.action).where(
            AuditLog.object_id == uuid.UUID(document_data["id"])
        )
    ).all()
    assert "DOCUMENT_UPLOADED" in actions


def test_optional_literature_binding_and_document_idempotency(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    project = create_project(client, normal_user_token_headers)
    literature = LiteratureRecord(
        project_id=uuid.UUID(str(project["id"])),
        source_type=LiteratureSourceType.MANUAL,
        title="A paper without a PDF",
        normalized_title="a paper without a pdf",
    )
    db.add(literature)
    db.commit()
    db.refresh(literature)
    assert literature.document_id is None

    key = str(uuid.uuid4())
    first = upload(
        client,
        normal_user_token_headers,
        project["id"],
        key=key,
        literature_record_id=literature.id,
    )
    replay = upload(
        client,
        normal_user_token_headers,
        project["id"],
        key=key,
        literature_record_id=literature.id,
    )
    assert first.status_code == replay.status_code == 201
    assert first.json()["data"] == replay.json()["data"]
    assert first.json()["data"]["document"]["literature_record_id"] == str(
        literature.id
    )
    assert replay.json()["meta"]["idempotency_replayed"] is True
    db.refresh(literature)
    assert literature.document_id == uuid.UUID(first.json()["data"]["document"]["id"])
    detail = client.get(
        f"/api/v1/documents/{literature.document_id}",
        headers=normal_user_token_headers,
    )
    assert detail.status_code == 200
    assert detail.json()["data"]["literature_record_id"] == str(literature.id)
    assert len(memory_storage.objects) == 1

    conflict = upload(
        client,
        normal_user_token_headers,
        project["id"],
        content=SCANNED_PDF,
        key=key,
        literature_record_id=literature.id,
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_duplicate_pdf_uses_distinct_original_artifacts(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    project = create_project(client, normal_user_token_headers)
    first = upload(client, normal_user_token_headers, project["id"])
    second = upload(client, normal_user_token_headers, project["id"])
    assert first.status_code == second.status_code == 201
    first_id = uuid.UUID(first.json()["data"]["artifact"]["id"])
    second_id = uuid.UUID(second.json()["data"]["artifact"]["id"])
    assert first_id != second_id
    assert second.json()["meta"]["duplicate_of_artifact_id"] == str(first_id)
    first_artifact = db.get(Artifact, first_id)
    second_artifact = db.get(Artifact, second_id)
    assert first_artifact is not None and second_artifact is not None
    assert first_artifact.storage_key != second_artifact.storage_key
    assert len(memory_storage.objects) == 2


@pytest.mark.parametrize(
    ("content", "filename", "mime_type", "status", "pdf_status"),
    [
        (b"not-a-pdf", "paper.pdf", "application/pdf", 415, None),
        (TEXT_PDF, "paper.txt", "application/pdf", 415, None),
        (TEXT_PDF, "paper.pdf", "text/plain", 415, None),
        (
            TEXT_PDF.removesuffix(b"%%EOF\n"),
            "paper.pdf",
            "application/pdf",
            415,
            "CORRUPT",
        ),
        (ENCRYPTED_PDF, "paper.pdf", "application/pdf", 415, "ENCRYPTED"),
    ],
)
def test_pdf_validation_rejects_unsupported_corrupt_and_encrypted_files(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
    content: bytes,
    filename: str,
    mime_type: str,
    status: int,
    pdf_status: str | None,
) -> None:
    project = create_project(client, normal_user_token_headers)
    response = upload(
        client,
        normal_user_token_headers,
        project["id"],
        content=content,
        filename=filename,
        mime_type=mime_type,
    )
    assert response.status_code == status
    assert response.json()["error"]["code"] == "FILE_TYPE_UNSUPPORTED"
    if pdf_status is not None:
        assert response.json()["error"]["details"]["pdf_status"] == pdf_status
    assert memory_storage.objects == {}


def test_scanned_pdf_is_accepted_without_parsing_or_ocr(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    assert artifact_service.storage is memory_storage
    project = create_project(client, normal_user_token_headers)
    response = upload(
        client,
        normal_user_token_headers,
        project["id"],
        content=SCANNED_PDF,
    )
    assert response.status_code == 201, response.text
    document = response.json()["data"]["document"]
    assert document["is_scanned"] is True
    assert document["page_count"] is None
    assert document["parse_status"] == "DRAFT"


def test_pdf_upload_enforces_configured_size_limit_before_storage(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 64)
    project = create_project(client, normal_user_token_headers)
    response = upload(client, normal_user_token_headers, project["id"])
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"
    assert memory_storage.objects == {}


def test_cross_project_binding_is_hidden_and_reviewer_cannot_upload(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    first = create_project(client, normal_user_token_headers)
    second = create_project(client, normal_user_token_headers)
    literature = LiteratureRecord(
        project_id=uuid.UUID(str(first["id"])),
        source_type=LiteratureSourceType.MANUAL,
        title="Scoped paper",
        normalized_title="scoped paper",
    )
    db.add(literature)
    db.commit()
    cross = upload(
        client,
        normal_user_token_headers,
        second["id"],
        literature_record_id=literature.id,
    )
    assert cross.status_code == 404
    assert cross.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert memory_storage.objects == {}

    password = random_lower_string()
    reviewer = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com", password=password
        ),
    )
    added = client.post(
        f"/api/v1/projects/{first['id']}/members",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"user_id": str(reviewer.id), "role": "REVIEWER"},
    )
    assert added.status_code == 201
    reviewer_headers = user_authentication_headers(
        client=client, email=reviewer.email, password=password
    )
    denied = upload(client, reviewer_headers, first["id"])
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"

    first_document = upload(client, normal_user_token_headers, first["id"])
    reviewer_detail = client.get(
        f"/api/v1/documents/{first_document.json()['data']['document']['id']}",
        headers=reviewer_headers,
    )
    assert reviewer_detail.status_code == 200
    assert reviewer_detail.json()["data"]["allowed_actions"] == ["document.read"]

    second_document = upload(client, normal_user_token_headers, second["id"])
    hidden = client.get(
        f"/api/v1/documents/{second_document.json()['data']['document']['id']}",
        headers=reviewer_headers,
    )
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_document_page_number_is_unique_per_document(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    assert artifact_service.storage is memory_storage
    project = create_project(client, normal_user_token_headers)
    response = upload(client, normal_user_token_headers, project["id"])
    document_id = uuid.UUID(response.json()["data"]["document"]["id"])
    project_id = uuid.UUID(str(project["id"]))
    db.add(DocumentPage(document_id=document_id, project_id=project_id, page_number=1))
    db.commit()
    db.add(DocumentPage(document_id=document_id, project_id=project_id, page_number=1))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    assert (
        db.exec(select(Document).where(Document.id == document_id)).first() is not None
    )
