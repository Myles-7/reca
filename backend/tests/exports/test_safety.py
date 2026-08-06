from __future__ import annotations

import io
import stat
import zipfile

import pytest

from app.core.config import settings
from app.exports.safety import (
    FIXED_ZIP_TIMESTAMP,
    PackageSafetyError,
    build_deterministic_zip,
    normalize_package_path,
    validate_member_set,
    verify_zip,
)

pytestmark = pytest.mark.no_database


@pytest.mark.parametrize(
    "path",
    ["", " ", "/absolute", "C:/drive", "../escape", "a/../escape", "a\\b", "a\x00b"],
)
def test_unsafe_package_paths_are_rejected(path: str) -> None:
    with pytest.raises(PackageSafetyError):
        normalize_package_path(path)


def test_duplicate_casefolded_paths_are_rejected() -> None:
    with pytest.raises(PackageSafetyError, match="case-colliding"):
        validate_member_set({"Data/file.csv": b"a", "data/FILE.csv": b"b"})


def test_member_count_size_total_and_depth_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "EXPORT_MAX_MEMBERS", 1)
    with pytest.raises(PackageSafetyError, match="member count"):
        validate_member_set({"a": b"1", "b": b"2"})

    monkeypatch.setattr(settings, "EXPORT_MAX_MEMBERS", 10)
    monkeypatch.setattr(settings, "EXPORT_MAX_ITEM_BYTES", 1)
    with pytest.raises(PackageSafetyError, match="member exceeds"):
        validate_member_set({"a": b"12"})

    monkeypatch.setattr(settings, "EXPORT_MAX_ITEM_BYTES", 10)
    monkeypatch.setattr(settings, "EXPORT_MAX_TOTAL_BYTES", 1)
    with pytest.raises(PackageSafetyError, match="total size"):
        validate_member_set({"a": b"1", "b": b"2"})

    monkeypatch.setattr(settings, "EXPORT_MAX_PATH_DEPTH", 1)
    with pytest.raises(PackageSafetyError, match="depth"):
        normalize_package_path("a/b")


def test_utf8_zip_is_deterministic_sorted_and_reopenable() -> None:
    entries = {
        "metadata/研究.json": b'{"ok":true}',
        "README_REPRODUCE.md": b"reproduce\n",
    }
    first = build_deterministic_zip(entries)
    second = build_deterministic_zip(entries)

    assert first == second
    verify_zip(first, entries)
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        assert archive.namelist() == sorted(entries)
        for info in archive.infolist():
            assert info.date_time == FIXED_ZIP_TIMESTAMP
            assert stat.S_IFMT(info.external_attr >> 16) == stat.S_IFREG


def test_symlink_member_is_rejected() -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        info = zipfile.ZipInfo("link", date_time=FIXED_ZIP_TIMESTAMP)
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, b"target")

    with pytest.raises(PackageSafetyError, match="non-regular"):
        verify_zip(output.getvalue(), {"link": b"target"})


def test_compression_bomb_ratio_is_rejected() -> None:
    content = b"0" * 100_000
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        info = zipfile.ZipInfo("compressed.txt", date_time=FIXED_ZIP_TIMESTAMP)
        info.create_system = 3
        info.external_attr = (stat.S_IFREG | 0o644) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, content)

    with pytest.raises(PackageSafetyError, match="compression ratio"):
        verify_zip(output.getvalue(), {"compressed.txt": content})
