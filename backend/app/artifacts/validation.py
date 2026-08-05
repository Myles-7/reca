from __future__ import annotations

import re
import stat
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from defusedxml import ElementTree

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

_DOCX_MAX_ENTRIES = 2_000
_DOCX_MAX_EXPANDED_BYTES = 120_000_000
_DOCX_MAX_MEMBER_RATIO = 100
_DOCX_MAX_PATH_DEPTH = 20
_DOCX_MAX_XML_BYTES = 10_000_000
_NESTED_ARCHIVE_SUFFIXES = {".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz"}
_ACTIVE_RELATIONSHIP_MARKERS = (
    "/attachedtemplate",
    "/oleobject",
    "/package",
    "/control",
    "/vbaProject".lower(),
)
_WORD_MAIN_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
)


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


def _safe_member_name(name: str) -> PurePosixPath:
    if "\\" in name or name.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", name):
        raise ValueError("unsafe archive path")
    member = PurePosixPath(name)
    if (
        member.is_absolute()
        or ".." in member.parts
        or len(member.parts) > _DOCX_MAX_PATH_DEPTH
    ):
        raise ValueError("unsafe archive path")
    return member


def _validate_docx_package(
    archive: zipfile.ZipFile, entries: list[zipfile.ZipInfo]
) -> None:
    names = {entry.filename for entry in entries}
    if "[Content_Types].xml" not in names or "word/document.xml" not in names:
        raise ValueError("required word document structure is missing")
    content_types = ElementTree.fromstring(archive.read("[Content_Types].xml"))
    main_types = {
        item.attrib.get("ContentType", "")
        for item in content_types
        if item.attrib.get("PartName") == "/word/document.xml"
    }
    if main_types != {_WORD_MAIN_CONTENT_TYPE}:
        raise ValueError("macro-enabled or invalid Word main content type")
    for item in content_types:
        content_type = item.attrib.get("ContentType", "").lower()
        part_name = item.attrib.get("PartName", "").lower()
        if (
            "macroenabled" in content_type
            or "vba" in content_type
            or "vbaproject" in part_name
        ):
            raise ValueError("macro-enabled package is not accepted")
    for name in names:
        lowered = name.lower()
        if lowered.endswith("vbaproject.bin"):
            raise ValueError("VBA project is not accepted")
        if Path(lowered).suffix in _NESTED_ARCHIVE_SUFFIXES:
            raise ValueError("nested archive is not accepted")
        if not lowered.endswith(".rels"):
            continue
        root = ElementTree.fromstring(archive.read(name))
        for relationship in root:
            relation_type = relationship.attrib.get("Type", "").lower()
            target_mode = relationship.attrib.get("TargetMode", "").lower()
            if any(
                relation_type.endswith(marker)
                for marker in _ACTIVE_RELATIONSHIP_MARKERS
            ):
                raise ValueError("active package relationship is not accepted")
            if target_mode == "external" and not relation_type.endswith("/hyperlink"):
                raise ValueError("external package relationship is not accepted")


def _validate_zip(path: Path, *, expected_prefix: str) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            is_docx = expected_prefix == "word/"
            max_entries = _DOCX_MAX_ENTRIES if is_docx else 10_000
            max_expanded = (
                _DOCX_MAX_EXPANDED_BYTES if is_docx else settings.MAX_UPLOAD_BYTES * 4
            )
            max_ratio = _DOCX_MAX_MEMBER_RATIO if is_docx else 1_000
            if len(entries) > max_entries:
                raise ValueError("too many archive entries")
            total_uncompressed = 0
            found_expected = False
            seen_names: set[str] = set()
            for entry in entries:
                member = _safe_member_name(entry.filename)
                normalized_name = member.as_posix().casefold()
                if normalized_name in seen_names:
                    raise ValueError("duplicate archive member")
                seen_names.add(normalized_name)
                mode = entry.external_attr >> 16
                file_type = stat.S_IFMT(mode)
                if file_type not in {0, stat.S_IFREG, stat.S_IFDIR}:
                    raise ValueError("non-regular archive member")
                total_uncompressed += entry.file_size
                if total_uncompressed > max_expanded:
                    raise ValueError("archive expansion exceeds limit")
                if (
                    entry.compress_size
                    and entry.file_size / entry.compress_size > max_ratio
                ):
                    raise ValueError("archive compression ratio exceeds limit")
                if is_docx and member.suffix.lower() == ".xml":
                    if entry.file_size > _DOCX_MAX_XML_BYTES:
                        raise ValueError("XML part exceeds limit")
                    ElementTree.fromstring(archive.read(entry))
                if entry.filename.startswith(expected_prefix):
                    found_expected = True
            if "[Content_Types].xml" not in archive.namelist() or not found_expected:
                raise ValueError("required office document structure is missing")
            if is_docx:
                _validate_docx_package(archive, entries)
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
