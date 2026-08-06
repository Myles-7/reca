from __future__ import annotations

import io
import re
import stat
import zipfile
from collections.abc import Mapping

from app.core.config import settings

FIXED_ZIP_TIMESTAMP = (2020, 1, 1, 0, 0, 0)
REGULAR_FILE_MODE = 0o100644
_DRIVE = re.compile(r"^[A-Za-z]:")


class PackageSafetyError(ValueError):
    pass


def normalize_package_path(value: str) -> str:
    if not value or not value.strip():
        raise PackageSafetyError("Package path must not be empty.")
    if "\x00" in value or "\\" in value:
        raise PackageSafetyError("Package path contains an unsafe character.")
    if value.startswith("/") or _DRIVE.match(value):
        raise PackageSafetyError("Package path must be relative.")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise PackageSafetyError("Package path contains an unsafe segment.")
    if len(parts) > settings.EXPORT_MAX_PATH_DEPTH:
        raise PackageSafetyError("Package path exceeds the depth limit.")
    if len(value.encode("utf-8")) > 1024:
        raise PackageSafetyError("Package path exceeds the byte limit.")
    return "/".join(parts)


def validate_member_set(entries: Mapping[str, bytes]) -> list[str]:
    if not entries:
        raise PackageSafetyError("Package must contain at least one member.")
    if len(entries) > settings.EXPORT_MAX_MEMBERS:
        raise PackageSafetyError("Package member count exceeds the limit.")
    normalized: list[str] = []
    casefolded: set[str] = set()
    total = 0
    for raw_path, content in entries.items():
        path = normalize_package_path(raw_path)
        if path != raw_path:
            raise PackageSafetyError("Package path is not canonical.")
        folded = path.casefold()
        if folded in casefolded:
            raise PackageSafetyError(
                "Package contains duplicate or case-colliding paths."
            )
        casefolded.add(folded)
        if len(content) > settings.EXPORT_MAX_ITEM_BYTES:
            raise PackageSafetyError("Package member exceeds the size limit.")
        total += len(content)
        if total > settings.EXPORT_MAX_TOTAL_BYTES:
            raise PackageSafetyError("Package total size exceeds the limit.")
        normalized.append(path)
    return sorted(normalized)


def build_deterministic_zip(entries: Mapping[str, bytes]) -> bytes:
    paths = validate_member_set(entries)
    output = io.BytesIO()
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in paths:
            info = zipfile.ZipInfo(path, date_time=FIXED_ZIP_TIMESTAMP)
            info.create_system = 3
            info.external_attr = REGULAR_FILE_MODE << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, entries[path])
    value = output.getvalue()
    verify_zip(value, entries)
    return value


def verify_zip(value: bytes, expected: Mapping[str, bytes]) -> None:
    expected_paths = validate_member_set(expected)
    try:
        with zipfile.ZipFile(io.BytesIO(value), "r") as archive:
            if archive.namelist() != expected_paths:
                raise PackageSafetyError("ZIP member order or set is invalid.")
            seen: set[str] = set()
            for info in archive.infolist():
                path = normalize_package_path(info.filename)
                folded = path.casefold()
                if folded in seen:
                    raise PackageSafetyError("ZIP contains duplicate paths.")
                seen.add(folded)
                mode = info.external_attr >> 16
                file_type = stat.S_IFMT(mode)
                if file_type not in {0, stat.S_IFREG}:
                    raise PackageSafetyError("ZIP contains a non-regular member.")
                if info.file_size > settings.EXPORT_MAX_ITEM_BYTES:
                    raise PackageSafetyError("ZIP member exceeds the size limit.")
                if info.file_size and info.compress_size == 0:
                    raise PackageSafetyError(
                        "ZIP member has an invalid compression size."
                    )
                if info.compress_size and (
                    info.file_size / info.compress_size
                    > settings.EXPORT_MAX_COMPRESSION_RATIO
                ):
                    raise PackageSafetyError("ZIP compression ratio exceeds the limit.")
                content = archive.read(info)
                if content != expected[path]:
                    raise PackageSafetyError("ZIP member content verification failed.")
    except zipfile.BadZipFile as error:
        raise PackageSafetyError("ZIP is not readable.") from error
