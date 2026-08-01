from __future__ import annotations

import datetime as dt
import hashlib
import hmac
from pathlib import Path
from typing import Protocol
from urllib.parse import quote, urlencode, urlparse

import httpx

from app.core.config import settings


class StorageError(RuntimeError):
    pass


class StorageObjectExists(StorageError):
    pass


class StorageObjectMissing(StorageError):
    pass


class ObjectStorage(Protocol):
    def put_file_once(
        self, *, object_key: str, path: Path, content_sha256: str, size_bytes: int
    ) -> None: ...

    def download_to_path(self, *, object_key: str, path: Path) -> None: ...

    def presign_download(self, *, object_key: str, expires_seconds: int) -> str: ...


class S3ObjectStorage:
    """Minimal private S3-compatible adapter for the configured MinIO boundary."""

    region = "us-east-1"
    service = "s3"

    @property
    def endpoint(self) -> str:
        return str(settings.MINIO_ENDPOINT).rstrip("/")

    @property
    def public_endpoint(self) -> str:
        endpoint = settings.MINIO_PUBLIC_ENDPOINT or settings.MINIO_ENDPOINT
        return str(endpoint).rstrip("/")

    @property
    def bucket(self) -> str:
        return settings.MINIO_BUCKET

    @property
    def timeout(self) -> httpx.Timeout:
        return httpx.Timeout(
            settings.REQUEST_TIMEOUT_SECONDS,
            connect=settings.CONNECT_TIMEOUT_SECONDS,
        )

    def _canonical_uri(self, object_key: str | None = None) -> str:
        path = f"/{quote(self.bucket, safe='-_.~')}"
        if object_key is not None:
            path += f"/{quote(object_key, safe='/-_.~')}"
        return path

    def _signing_key(self, day: str) -> bytes:
        key = hmac.new(
            ("AWS4" + settings.MINIO_ROOT_PASSWORD.get_secret_value()).encode(),
            day.encode(),
            hashlib.sha256,
        ).digest()
        for component in (self.region, self.service, "aws4_request"):
            key = hmac.new(key, component.encode(), hashlib.sha256).digest()
        return key

    def _signed_headers(
        self,
        *,
        method: str,
        canonical_uri: str,
        payload_hash: str,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, str]:
        now = dt.datetime.now(dt.UTC)
        timestamp = now.strftime("%Y%m%dT%H%M%SZ")
        day = now.strftime("%Y%m%d")
        host = urlparse(self.endpoint).netloc
        headers = {
            "host": host,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": timestamp,
            **(extra_headers or {}),
        }
        normalized = {
            name.lower(): " ".join(value.split()) for name, value in headers.items()
        }
        signed_headers = ";".join(sorted(normalized))
        canonical_headers = "".join(
            f"{name}:{normalized[name]}\n" for name in sorted(normalized)
        )
        canonical_request = (
            f"{method}\n{canonical_uri}\n\n{canonical_headers}\n"
            f"{signed_headers}\n{payload_hash}"
        )
        scope = f"{day}/{self.region}/{self.service}/aws4_request"
        string_to_sign = (
            f"AWS4-HMAC-SHA256\n{timestamp}\n{scope}\n"
            f"{hashlib.sha256(canonical_request.encode()).hexdigest()}"
        )
        signature = hmac.new(
            self._signing_key(day), string_to_sign.encode(), hashlib.sha256
        ).hexdigest()
        normalized["Authorization"] = (
            "AWS4-HMAC-SHA256 "
            f"Credential={settings.MINIO_ROOT_USER}/{scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        return normalized

    def _ensure_bucket(self, client: httpx.Client) -> None:
        uri = self._canonical_uri()
        empty_hash = hashlib.sha256(b"").hexdigest()
        response = client.put(
            self.endpoint + uri,
            headers=self._signed_headers(
                method="PUT", canonical_uri=uri, payload_hash=empty_hash
            ),
            content=b"",
        )
        if response.status_code not in {200, 409}:
            raise StorageError("Object storage bucket is unavailable.")

    def put_file_once(
        self, *, object_key: str, path: Path, content_sha256: str, size_bytes: int
    ) -> None:
        uri = self._canonical_uri(object_key)
        headers = self._signed_headers(
            method="PUT",
            canonical_uri=uri,
            payload_hash=content_sha256,
            extra_headers={"if-none-match": "*"},
        )
        headers["content-length"] = str(size_bytes)
        try:
            with httpx.Client(timeout=self.timeout, trust_env=False) as client:
                self._ensure_bucket(client)
                with path.open("rb") as content:
                    response = client.put(
                        self.endpoint + uri, headers=headers, content=content
                    )
        except (OSError, httpx.HTTPError) as error:
            raise StorageError("Object storage write failed.") from error
        if response.status_code in {409, 412}:
            raise StorageObjectExists("Object storage key already exists.")
        if response.status_code not in {200, 201}:
            raise StorageError("Object storage write failed.")

    def download_to_path(self, *, object_key: str, path: Path) -> None:
        uri = self._canonical_uri(object_key)
        headers = self._signed_headers(
            method="GET", canonical_uri=uri, payload_hash="UNSIGNED-PAYLOAD"
        )
        try:
            with httpx.Client(timeout=self.timeout, trust_env=False) as client:
                with client.stream(
                    "GET", self.endpoint + uri, headers=headers
                ) as response:
                    if response.status_code == 404:
                        raise StorageObjectMissing("Object storage content is missing.")
                    if response.status_code != 200:
                        raise StorageError("Object storage read failed.")
                    with path.open("wb") as target:
                        for chunk in response.iter_bytes():
                            target.write(chunk)
        except StorageError:
            raise
        except (OSError, httpx.HTTPError) as error:
            raise StorageError("Object storage read failed.") from error

    def presign_download(self, *, object_key: str, expires_seconds: int) -> str:
        now = dt.datetime.now(dt.UTC)
        timestamp = now.strftime("%Y%m%dT%H%M%SZ")
        day = now.strftime("%Y%m%d")
        scope = f"{day}/{self.region}/{self.service}/aws4_request"
        uri = self._canonical_uri(object_key)
        query = {
            "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
            "X-Amz-Credential": f"{settings.MINIO_ROOT_USER}/{scope}",
            "X-Amz-Date": timestamp,
            "X-Amz-Expires": str(expires_seconds),
            "X-Amz-SignedHeaders": "host",
        }
        canonical_query = urlencode(sorted(query.items()), quote_via=quote, safe="-_.~")
        host = urlparse(self.public_endpoint).netloc
        canonical_request = (
            f"GET\n{uri}\n{canonical_query}\nhost:{host}\n\nhost\nUNSIGNED-PAYLOAD"
        )
        string_to_sign = (
            f"AWS4-HMAC-SHA256\n{timestamp}\n{scope}\n"
            f"{hashlib.sha256(canonical_request.encode()).hexdigest()}"
        )
        signature = hmac.new(
            self._signing_key(day), string_to_sign.encode(), hashlib.sha256
        ).hexdigest()
        return (
            f"{self.public_endpoint}{uri}?{canonical_query}&X-Amz-Signature={signature}"
        )
