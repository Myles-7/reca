from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

import pytest

from app.adapters.storage import S3ObjectStorage

pytestmark = pytest.mark.no_database


@pytest.mark.skipif(
    os.getenv("RUN_REAL_MINIO_TESTS") != "1",
    reason="requires an explicitly isolated real MinIO endpoint",
)
def test_stage2_docx_round_trip_against_real_minio(tmp_path: Path) -> None:
    storage = S3ObjectStorage()
    source = tmp_path / "source.docx"
    content = b"stage2-real-minio-docx-boundary"
    source.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    key = f"m6-stage2-tests/{uuid.uuid4()}/derived.docx"
    target = tmp_path / "target.docx"
    try:
        storage.put_file_once(
            object_key=key,
            path=source,
            content_sha256=digest,
            size_bytes=len(content),
        )
        storage.download_to_path(object_key=key, path=target)
        assert target.read_bytes() == content
    finally:
        storage.delete_object(object_key=key)
