from urllib.parse import urlparse

import pytest
from pydantic import AnyHttpUrl

from app.adapters.storage import S3ObjectStorage
from app.core.config import settings

pytestmark = pytest.mark.no_database


def test_presigned_download_uses_browser_reachable_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "MINIO_PUBLIC_ENDPOINT",
        AnyHttpUrl("http://127.0.0.1:19000"),
    )

    url = S3ObjectStorage().presign_download(
        object_key="projects/project-1/artifacts/artifact-1/original",
        expires_seconds=300,
    )

    parsed = urlparse(url)
    assert parsed.scheme == "http"
    assert parsed.netloc == "127.0.0.1:19000"
    assert parsed.path.endswith("/artifacts/artifact-1/original")
    assert "X-Amz-Signature=" in parsed.query
