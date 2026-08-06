from __future__ import annotations

import hashlib
import io
import json
import posixpath
import zipfile

import pytest


def _canonical_manifest() -> bytes:
    manifest = {
        "schema_version": "m7.manifest.v1",
        "files": [
            {"path": "README_REPRODUCE.md", "type": "documentation"},
            {"path": "manifest.json", "type": "manifest"},
            {"path": "restricted/source.pdf", "include_status": "METADATA_ONLY"},
        ],
    }
    return json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _build_zip() -> bytes:
    entries = {
        "README_REPRODUCE.md": b"Reproduction is limited by restricted source data.\n",
        "manifest.json": _canonical_manifest(),
        "restricted/source.pdf": b"metadata-only",
    }
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(entries):
            assert path == posixpath.normpath(path)
            info = zipfile.ZipInfo(path, date_time=(2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, entries[path], compress_type=zipfile.ZIP_DEFLATED)
    return output.getvalue()


def test_zip_is_stable_and_reopenable() -> None:
    first = _build_zip()
    second = _build_zip()
    assert first == second
    assert hashlib.sha256(first).hexdigest() == hashlib.sha256(second).hexdigest()
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        assert archive.namelist() == [
            "README_REPRODUCE.md",
            "manifest.json",
            "restricted/source.pdf",
        ]
        assert archive.getinfo("restricted/source.pdf").external_attr >> 16 == 0o100644


@pytest.mark.parametrize("path", ["../secret", "/absolute", "a/../../escape", "a\\b"])
def test_zip_slip_paths_are_rejected(path: str) -> None:
    normalized = posixpath.normpath(path.replace("\\", "/"))
    assert (
        normalized.startswith("../")
        or normalized == ".."
        or path.startswith("/")
        or "\\" in path
    )
