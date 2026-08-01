from __future__ import annotations

import re
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from app.core.config import settings
from app.models import ArtifactType


@dataclass(frozen=True)
class FilePolicy:
    extension: str
    mime_type: str
    max_bytes: int


class ArtifactValidationError(ValueError):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


_DANGEROUS_SUFFIXES = {
    ".bat",
    ".cmd",
    ".com",
    ".exe",
    ".html",
    ".js",
    ".php",
    ".ps1",
    ".scr",
    ".sh",
}


def normalize_filename(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).replace("\\", "/")
    normalized = normalized.rsplit("/", 1)[-1]
    normalized = "".join(
        "_" if unicodedata.category(character).startswith("C") else character
        for character in normalized
    )
    normalized = re.sub(r"\s+", " ", normalized).strip(" .")
    if not normalized:
        raise ArtifactValidationError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Filename does not contain a safe display name.",
        )
    return normalized[:255]


def policy_for(
    *, artifact_type: ArtifactType, filename: str, declared_mime: str
) -> tuple[str, FilePolicy]:
    safe_name = normalize_filename(filename)
    extension = Path(safe_name).suffix.lower()
    policies: dict[ArtifactType, dict[str, tuple[str, int]]] = {
        ArtifactType.PDF_DOCUMENT: {
            ".pdf": ("application/pdf", 50_000_000),
        },
        ArtifactType.DATASET_FILE: {
            ".csv": ("text/csv", 100_000_000),
            ".xlsx": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                100_000_000,
            ),
        },
        ArtifactType.MANUSCRIPT_DOCX: {
            ".docx": (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                30_000_000,
            ),
        },
    }
    type_policies = policies.get(artifact_type)
    if type_policies is None or extension not in type_policies:
        raise ArtifactValidationError(
            status_code=415,
            code="FILE_TYPE_UNSUPPORTED",
            message="Artifact type and filename extension are not supported.",
        )
    stem_suffix = Path(safe_name).stem
    if any(stem_suffix.lower().endswith(suffix) for suffix in _DANGEROUS_SUFFIXES):
        raise ArtifactValidationError(
            status_code=415,
            code="FILE_TYPE_UNSUPPORTED",
            message="Dangerous double-extension filename is not accepted.",
        )
    expected_mime, format_limit = type_policies[extension]
    if declared_mime.lower().strip() != expected_mime:
        raise ArtifactValidationError(
            status_code=415,
            code="FILE_TYPE_UNSUPPORTED",
            message="Declared MIME type does not match the file type.",
        )
    return safe_name, FilePolicy(
        extension=extension,
        mime_type=expected_mime,
        max_bytes=min(settings.MAX_UPLOAD_BYTES, format_limit),
    )


def _validate_zip(path: Path, *, expected_prefix: str) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > 10_000:
                raise ValueError("too many archive entries")
            total_uncompressed = 0
            found_expected = False
            for entry in entries:
                member = PurePosixPath(entry.filename.replace("\\", "/"))
                if member.is_absolute() or ".." in member.parts:
                    raise ValueError("unsafe archive path")
                total_uncompressed += entry.file_size
                if total_uncompressed > settings.MAX_UPLOAD_BYTES * 4:
                    raise ValueError("archive expansion exceeds limit")
                if (
                    entry.compress_size
                    and entry.file_size / entry.compress_size > 1_000
                ):
                    raise ValueError("archive compression ratio exceeds limit")
                if entry.filename.startswith(expected_prefix):
                    found_expected = True
            if "[Content_Types].xml" not in archive.namelist() or not found_expected:
                raise ValueError("required office document structure is missing")
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        raise ArtifactValidationError(
            status_code=415,
            code="FILE_TYPE_UNSUPPORTED",
            message="File header or container structure does not match the declared type.",
        ) from error


def verify_file_content(path: Path, *, policy: FilePolicy) -> str:
    if policy.extension == ".pdf":
        with path.open("rb") as content:
            header = content.read(5)
        if header != b"%PDF-":
            raise ArtifactValidationError(
                status_code=415,
                code="FILE_TYPE_UNSUPPORTED",
                message="PDF header is invalid.",
            )
    elif policy.extension == ".docx":
        _validate_zip(path, expected_prefix="word/")
    elif policy.extension == ".xlsx":
        _validate_zip(path, expected_prefix="xl/")
    elif policy.extension == ".csv":
        with path.open("rb") as content:
            sample = content.read(65_536)
        if b"\x00" in sample:
            raise ArtifactValidationError(
                status_code=415,
                code="FILE_TYPE_UNSUPPORTED",
                message="CSV content contains binary data.",
            )
        try:
            sample.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ArtifactValidationError(
                status_code=415,
                code="FILE_TYPE_UNSUPPORTED",
                message="CSV content is not valid UTF-8 text.",
            ) from error
    return policy.mime_type
