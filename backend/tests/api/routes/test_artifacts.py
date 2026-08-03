import hashlib
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.exc import DBAPIError
from sqlmodel import Session, select

from app import crud
from app.adapters.storage import StorageError, StorageObjectExists
from app.artifacts import service as artifact_service
from app.models import (
    Artifact,
    ArtifactStatus,
    AuditLog,
    UserCreate,
)
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_lower_string

PDF = b"%PDF-1.7\nRECA artifact fixture\n"


class MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.fail_put = False
        self.fail_get = False

    def put_file_once(
        self, *, object_key: str, path: Path, content_sha256: str, size_bytes: int
    ) -> None:
        if self.fail_put:
            raise StorageError("write failed")
        content = path.read_bytes()
        assert len(content) == size_bytes
        assert hashlib.sha256(content).hexdigest() == content_sha256
        if object_key in self.objects:
            raise StorageObjectExists("already exists")
        self.objects[object_key] = content

    def download_to_path(self, *, object_key: str, path: Path) -> None:
        if self.fail_get or object_key not in self.objects:
            raise StorageError("read failed")
        path.write_bytes(self.objects[object_key])

    def presign_download(self, *, object_key: str, expires_seconds: int) -> str:
        if self.fail_get:
            raise StorageError("presign failed")
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
        json={"name": "Artifact project", "project_type": "RESEARCH"},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def initiate(
    client: TestClient,
    headers: dict[str, str],
    project_id: object,
    *,
    content: bytes = PDF,
    sha256: str | None = None,
    filename: str = "paper.pdf",
    key: str | None = None,
) -> tuple[dict[str, object], str]:
    idempotency_key = key or str(uuid.uuid4())
    response = client.post(
        f"/api/v1/projects/{project_id}/artifacts/uploads",
        headers={**headers, "Idempotency-Key": idempotency_key},
        json={
            "artifact_type": "PDF_DOCUMENT",
            "filename": filename,
            "mime_type": "application/pdf",
            "size_bytes": len(content),
            "sha256": sha256 or hashlib.sha256(content).hexdigest(),
            "is_original": True,
            "source_artifact_id": None,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["data"], idempotency_key


def transfer(
    client: TestClient, headers: dict[str, str], upload_id: object, content: bytes = PDF
) -> object:
    return client.put(
        f"/api/v1/artifact-uploads/{upload_id}/content",
        headers={**headers, "Content-Type": "application/octet-stream"},
        content=content,
    )


def complete(
    client: TestClient,
    headers: dict[str, str],
    project_id: object,
    upload_id: object,
    *,
    content: bytes = PDF,
    sha256: str | None = None,
    key: str | None = None,
) -> object:
    return client.post(
        f"/api/v1/projects/{project_id}/artifacts/uploads/{upload_id}/complete",
        headers={**headers, "Idempotency-Key": key or str(uuid.uuid4())},
        json={
            "sha256": sha256 or hashlib.sha256(content).hexdigest(),
            "size_bytes": len(content),
        },
    )


def test_artifact_lifecycle_isolated_download_and_immutability(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    assert artifact_service.storage is memory_storage
    project = create_project(client, normal_user_token_headers)
    upload, _ = initiate(
        client,
        normal_user_token_headers,
        project["id"],
        filename="../../paper.pdf",
    )
    artifact_id = uuid.UUID(str(upload["artifact_id"]))
    artifact = db.get(Artifact, artifact_id)
    assert artifact is not None
    assert artifact.filename == "paper.pdf"
    assert artifact.storage_key == (
        f"projects/{project['id']}/artifacts/{artifact_id}/original"
    )

    first_transfer = transfer(client, normal_user_token_headers, artifact_id)
    second_transfer = transfer(client, normal_user_token_headers, artifact_id)
    assert first_transfer.status_code == 204
    assert second_transfer.status_code == 409
    assert second_transfer.json()["error"]["code"] == "INVALID_STATE_TRANSITION"

    completed = complete(client, normal_user_token_headers, project["id"], artifact_id)
    assert completed.status_code == 200, completed.text
    assert completed.json()["data"]["status"] == "AVAILABLE"
    assert "storage_key" not in completed.text

    detail = client.get(
        f"/api/v1/artifacts/{artifact_id}", headers=normal_user_token_headers
    )
    listing = client.get(
        f"/api/v1/projects/{project['id']}/artifacts",
        headers=normal_user_token_headers,
    )
    download = client.get(
        f"/api/v1/artifacts/{artifact_id}/download",
        headers=normal_user_token_headers,
    )
    assert detail.status_code == listing.status_code == download.status_code == 200
    assert listing.json()["pagination"]["total"] == 1
    assert "artifact.upload" in listing.json()["allowed_actions"]
    assert download.json()["data"]["disposition_filename"] == "paper.pdf"
    assert "storage_key" not in download.text

    password = random_lower_string()
    outsider = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com", password=password
        ),
    )
    outsider_headers = user_authentication_headers(
        client=client, email=outsider.email, password=password
    )
    for path in (
        f"/api/v1/artifacts/{artifact_id}",
        f"/api/v1/artifacts/{artifact_id}/download",
    ):
        denied = client.get(path, headers=outsider_headers)
        assert denied.status_code == 404
        assert denied.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    with pytest.raises(DBAPIError):
        db.execute(
            update(Artifact).where(Artifact.id == artifact_id).values(sha256="0" * 64)
        )
        db.commit()
    db.rollback()
    assert memory_storage.objects[artifact.storage_key] == PDF
    actions = db.exec(
        select(AuditLog.action).where(AuditLog.project_id == artifact.project_id)
    ).all()
    assert "ARTIFACT_UPLOAD_INITIATED" in actions
    assert "ARTIFACT_AVAILABLE" in actions
    assert "ARTIFACT_DOWNLOAD_AUTHORIZED" in actions


def test_upload_initiate_idempotency_replays_without_allocating_another_key(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    assert artifact_service.storage is memory_storage
    project = create_project(client, normal_user_token_headers)
    key = str(uuid.uuid4())
    first, _ = initiate(client, normal_user_token_headers, project["id"], key=key)
    replay, _ = initiate(client, normal_user_token_headers, project["id"], key=key)
    assert first == replay

    conflict = client.post(
        f"/api/v1/projects/{project['id']}/artifacts/uploads",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json={
            "artifact_type": "PDF_DOCUMENT",
            "filename": "different.pdf",
            "mime_type": "application/pdf",
            "size_bytes": len(PDF),
            "sha256": hashlib.sha256(PDF).hexdigest(),
            "is_original": True,
            "source_artifact_id": None,
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_hash_mismatch_is_quarantined_and_idempotently_replayed(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    assert artifact_service.storage is memory_storage
    project = create_project(client, normal_user_token_headers)
    declared_hash = "0" * 64
    upload, _ = initiate(
        client,
        normal_user_token_headers,
        project["id"],
        sha256=declared_hash,
    )
    artifact_id = uuid.UUID(str(upload["artifact_id"]))
    assert transfer(client, normal_user_token_headers, artifact_id).status_code == 204
    complete_key = str(uuid.uuid4())

    first = complete(
        client,
        normal_user_token_headers,
        project["id"],
        artifact_id,
        sha256=declared_hash,
        key=complete_key,
    )
    replay = complete(
        client,
        normal_user_token_headers,
        project["id"],
        artifact_id,
        sha256=declared_hash,
        key=complete_key,
    )
    assert first.status_code == replay.status_code == 409
    assert first.json()["error"]["code"] == "FILE_HASH_MISMATCH"
    assert replay.json()["error"]["code"] == "FILE_HASH_MISMATCH"
    artifact = db.get(Artifact, artifact_id)
    assert artifact is not None and artifact.status == ArtifactStatus.QUARANTINED
    download = client.get(
        f"/api/v1/artifacts/{artifact_id}/download",
        headers=normal_user_token_headers,
    )
    assert download.status_code == 409


def test_executable_masquerading_as_pdf_is_quarantined(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    assert artifact_service.storage is memory_storage
    content = b"MZ\x90\x00not really a PDF"
    project = create_project(client, normal_user_token_headers)
    upload, _ = initiate(
        client,
        normal_user_token_headers,
        project["id"],
        content=content,
    )
    artifact_id = uuid.UUID(str(upload["artifact_id"]))
    assert (
        transfer(client, normal_user_token_headers, artifact_id, content).status_code
        == 204
    )

    response = complete(
        client,
        normal_user_token_headers,
        project["id"],
        artifact_id,
        content=content,
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "FILE_TYPE_UNSUPPORTED"
    artifact = db.get(Artifact, artifact_id)
    assert artifact is not None
    assert artifact.status == ArtifactStatus.QUARANTINED


def test_duplicate_content_has_distinct_artifacts_and_storage_keys(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    project = create_project(client, normal_user_token_headers)
    artifact_ids: list[uuid.UUID] = []
    responses = []
    for _ in range(2):
        upload, _ = initiate(client, normal_user_token_headers, project["id"])
        artifact_id = uuid.UUID(str(upload["artifact_id"]))
        artifact_ids.append(artifact_id)
        assert (
            transfer(client, normal_user_token_headers, artifact_id).status_code == 204
        )
        responses.append(
            complete(client, normal_user_token_headers, project["id"], artifact_id)
        )

    assert all(response.status_code == 200 for response in responses)
    assert artifact_ids[0] != artifact_ids[1]
    assert responses[1].json()["meta"]["duplicate_of_artifact_id"] == str(
        artifact_ids[0]
    )
    artifacts = [db.get(Artifact, artifact_id) for artifact_id in artifact_ids]
    assert all(artifact is not None for artifact in artifacts)
    assert artifacts[0] is not None and artifacts[1] is not None
    assert artifacts[0].storage_key != artifacts[1].storage_key
    assert len(memory_storage.objects) == 2


def test_storage_failure_and_partial_write_recovery_do_not_overwrite(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    project = create_project(client, normal_user_token_headers)
    failed_upload, _ = initiate(client, normal_user_token_headers, project["id"])
    failed_id = uuid.UUID(str(failed_upload["artifact_id"]))
    memory_storage.fail_put = True
    failed = transfer(client, normal_user_token_headers, failed_id)
    assert failed.status_code == 503
    failed_artifact = db.get(Artifact, failed_id)
    assert failed_artifact is not None
    assert failed_artifact.status == ArtifactStatus.FAILED

    memory_storage.fail_put = False
    recovery_upload, _ = initiate(client, normal_user_token_headers, project["id"])
    recovery_id = uuid.UUID(str(recovery_upload["artifact_id"]))
    recovery_artifact = db.get(Artifact, recovery_id)
    assert recovery_artifact is not None
    memory_storage.objects[recovery_artifact.storage_key] = PDF
    recovered = transfer(client, normal_user_token_headers, recovery_id)
    assert recovered.status_code == 204
    completed = complete(client, normal_user_token_headers, project["id"], recovery_id)
    assert completed.status_code == 200
    assert memory_storage.objects[recovery_artifact.storage_key] == PDF


def test_reviewer_cannot_upload_and_cross_project_complete_is_hidden(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    memory_storage: MemoryStorage,
) -> None:
    assert artifact_service.storage is memory_storage
    first = create_project(client, normal_user_token_headers)
    password = random_lower_string()
    reviewer = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com", password=password
        ),
    )
    add = client.post(
        f"/api/v1/projects/{first['id']}/members",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"user_id": str(reviewer.id), "role": "REVIEWER"},
    )
    assert add.status_code == 201
    reviewer_headers = user_authentication_headers(
        client=client, email=reviewer.email, password=password
    )
    denied = client.post(
        f"/api/v1/projects/{first['id']}/artifacts/uploads",
        headers={**reviewer_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "artifact_type": "PDF_DOCUMENT",
            "filename": "paper.pdf",
            "mime_type": "application/pdf",
            "size_bytes": len(PDF),
            "sha256": hashlib.sha256(PDF).hexdigest(),
            "is_original": True,
            "source_artifact_id": None,
        },
    )
    assert denied.status_code == 403

    upload, _ = initiate(client, normal_user_token_headers, first["id"])
    artifact_id = uuid.UUID(str(upload["artifact_id"]))
    assert transfer(client, normal_user_token_headers, artifact_id).status_code == 204
    second = create_project(client, normal_user_token_headers)
    cross = complete(client, normal_user_token_headers, second["id"], artifact_id)
    assert cross.status_code == 404
