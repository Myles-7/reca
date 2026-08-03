from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

import httpx

from app.core.config import settings

GROBID_COORDINATE_ELEMENTS = (
    "p",
    "s",
    "head",
    "figure",
    "table",
    "ref",
    "biblStruct",
)


class DocumentParseError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class GrobidResult:
    tei: bytes
    version: str | None
    revision: str | None


class GrobidProvider(Protocol):
    def parse(self, pdf_path: Path, *, extract_coordinates: bool) -> GrobidResult: ...


class GrobidAdapter:
    _semaphore = threading.BoundedSemaphore(settings.GROBID_MAX_CONCURRENCY)

    def __init__(self, *, transport: httpx.BaseTransport | None = None) -> None:
        self.base_url = str(settings.GROBID_URL).rstrip("/")
        self.transport = transport

    def _version(self, client: httpx.Client) -> tuple[str | None, str | None]:
        try:
            response = client.get("/api/version")
            if response.status_code != 200:
                return None, None
            payload = response.json()
            return str(payload.get("version") or "") or None, str(
                payload.get("revision") or ""
            ) or None
        except httpx.HTTPError, ValueError:
            return None, None

    def parse(self, pdf_path: Path, *, extract_coordinates: bool) -> GrobidResult:
        timeout = httpx.Timeout(
            settings.GROBID_PARSE_TIMEOUT_SECONDS,
            connect=settings.CONNECT_TIMEOUT_SECONDS,
        )
        fields: list[tuple[str, tuple[str | None, Any, str | None]]] = [
            ("consolidateHeader", (None, "0", None))
        ]
        if extract_coordinates:
            fields.extend(
                ("teiCoordinates", (None, element, None))
                for element in GROBID_COORDINATE_ELEMENTS
            )
        try:
            with self._semaphore:
                with httpx.Client(
                    base_url=self.base_url,
                    timeout=timeout,
                    trust_env=False,
                    transport=self.transport,
                ) as client:
                    with pdf_path.open("rb") as source:
                        files = [
                            *fields,
                            (
                                "input",
                                ("document.pdf", source, "application/pdf"),
                            ),
                        ]
                        with client.stream(
                            "POST",
                            "/api/processFulltextDocument",
                            files=cast(Any, files),
                        ) as response:
                            status_code = response.status_code
                            chunks: list[bytes] = []
                            total_bytes = 0
                            if status_code == 200:
                                for chunk in response.iter_bytes():
                                    total_bytes += len(chunk)
                                    if total_bytes > settings.GROBID_MAX_RESPONSE_BYTES:
                                        raise DocumentParseError(
                                            "GROBID_OUTPUT_TOO_LARGE",
                                            "GROBID output exceeded the configured limit.",
                                            retryable=False,
                                        )
                                    chunks.append(chunk)
                            content = b"".join(chunks)
                    version, revision = self._version(client)
        except httpx.TimeoutException as exc:
            raise DocumentParseError(
                "GROBID_TIMEOUT", "GROBID parsing timed out.", retryable=True
            ) from exc
        except (OSError, httpx.ConnectError, httpx.NetworkError) as exc:
            raise DocumentParseError(
                "GROBID_UNAVAILABLE", "GROBID is unavailable.", retryable=True
            ) from exc
        if status_code in {502, 503, 504}:
            raise DocumentParseError(
                "GROBID_UNAVAILABLE", "GROBID is unavailable.", retryable=True
            )
        if status_code == 204:
            raise DocumentParseError(
                "GROBID_EMPTY_OUTPUT", "GROBID returned no TEI.", retryable=False
            )
        if status_code in {400, 409, 413, 415, 422}:
            raise DocumentParseError(
                "GROBID_INPUT_REJECTED",
                "GROBID rejected the PDF input.",
                retryable=False,
            )
        if status_code != 200:
            raise DocumentParseError(
                "GROBID_PROCESSING_FAILED",
                "GROBID parsing failed.",
                retryable=False,
            )
        if not content.strip():
            raise DocumentParseError(
                "GROBID_EMPTY_OUTPUT", "GROBID returned no TEI.", retryable=False
            )
        return GrobidResult(tei=content, version=version, revision=revision)
