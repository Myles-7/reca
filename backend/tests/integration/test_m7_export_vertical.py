from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from zipfile import ZipFile

from sqlmodel import Session, select

from app.adapters.storage import S3ObjectStorage
from app.exports import service
from app.exports.schemas import ReproPackageCreate
from app.models import Artifact, Export, ExportStatus, Job, JobStatus, ReproPackage
from tests.projects.test_service import create_project


def test_real_worker_minio_repro_package_vertical(db: Session, tmp_path: Path) -> None:
    owner, project = create_project(db)
    created = service.create_repro_package_export(
        db,
        actor=owner,
        project_id=project.id,
        request=ReproPackageCreate(),
        idempotency_key=str(uuid.uuid4()),
    )
    assert created.status_code == 202
    export_id = uuid.UUID(created.data["export"]["id"])
    job_id = uuid.UUID(created.data["job"]["id"])

    deadline = time.monotonic() + 90
    export: Export | None = None
    job: Job | None = None
    while time.monotonic() < deadline:
        db.expire_all()
        export = db.get(Export, export_id)
        job = db.get(Job, job_id)
        if export and export.status in {ExportStatus.COMPLETED, ExportStatus.FAILED}:
            break
        time.sleep(0.5)

    assert export is not None
    assert job is not None
    assert export.status == ExportStatus.COMPLETED, export.error_code
    assert job.status == JobStatus.COMPLETED, job.error_code
    package = db.exec(
        select(ReproPackage).where(ReproPackage.export_id == export.id)
    ).one()
    package_artifact = db.get(Artifact, package.artifact_id)
    manifest_artifact = db.get(Artifact, package.manifest_artifact_id)
    assert package_artifact is not None
    assert manifest_artifact is not None

    storage = S3ObjectStorage()
    package_path = tmp_path / "repro-package.zip"
    try:
        storage.download_to_path(
            object_key=package_artifact.storage_key, path=package_path
        )
        package_bytes = package_path.read_bytes()
        assert hashlib.sha256(package_bytes).hexdigest() == package.sha256
        with ZipFile(package_path) as archive:
            names = archive.namelist()
            assert names == sorted(names)
            assert "manifest.json" in names
            assert "README_REPRODUCE.md" in names
            assert "12_environment/locks/uv.lock" in names
            assert "12_environment/locks/bun.lock" in names
            manifest = json.loads(archive.read("manifest.json"))
            for item in manifest["files"]:
                content = archive.read(item["path"])
                assert len(content) == item["size"]
                assert hashlib.sha256(content).hexdigest() == item["sha256"]
            readme = archive.read("README_REPRODUCE.md").decode("utf-8")
            assert "SHA-256" in readme
            assert "Agent logs: NOT_AVAILABLE" in readme

        download = service.authorize_package_download(
            db, actor=owner, package_id=package.id
        )
        assert download["package"]["id"] == str(package.id)
        assert download["download"]["download_url"].startswith(
            f"{storage.public_endpoint}/"
        )
        print(  # noqa: T201 - emits stage evidence IDs and package hashes
            "M7_VERTICAL_EVIDENCE="
            + json.dumps(
                {
                    "project_id": str(project.id),
                    "export_id": str(export.id),
                    "job_id": str(job.id),
                    "package_id": str(package.id),
                    "artifact_id": str(package.artifact_id),
                    "manifest_artifact_id": str(package.manifest_artifact_id),
                    "zip_sha256": package.sha256,
                    "zip_members": len(names),
                    "manifest_files": len(manifest["files"]),
                },
                sort_keys=True,
            )
        )
    finally:
        storage.delete_object(object_key=package_artifact.storage_key)
        storage.delete_object(object_key=manifest_artifact.storage_key)
