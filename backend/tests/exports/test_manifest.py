from __future__ import annotations

import hashlib
import json

import pytest

from app.exports.collector import redact
from app.exports.manifest import PackageMember, build_manifest, build_readme

pytestmark = pytest.mark.no_database


def _implementation() -> dict[str, object]:
    return {
        "runtime_dependencies": {"python": "3.14"},
        "service_images": [],
        "upstream_projects": [],
        "vendored_assets": [],
        "prompt_versions": [],
        "ruleset_versions": ["m7-export-policy/1.0"],
        "statistical_engines": [],
        "citation_styles": [],
        "configuration_hashes": {},
        "source_object_versions": [],
        "artifact_hashes": [],
        "limitations": ["Restricted source is metadata-only."],
    }


def test_manifest_is_canonical_and_covers_payload_members() -> None:
    members = [
        PackageMember(
            path="02_literature/source.json",
            content=b"{}",
            member_type="literature-metadata",
            source={"object_type": "LITERATURE_RECORD"},
            license_status="UNKNOWN",
            redistribution="METADATA_ONLY",
        ),
        PackageMember(
            path="README_REPRODUCE.md",
            content=b"readme\n",
            member_type="documentation",
            source={"generator": "test"},
        ),
    ]

    manifest, encoded = build_manifest(members, implementation=_implementation())
    assert (
        encoded
        == json.dumps(
            manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    )
    assert [item["path"] for item in manifest["files"]] == [
        "02_literature/source.json",
        "README_REPRODUCE.md",
    ]
    assert all(
        item["sha256"]
        == hashlib.sha256(
            next(member.content for member in members if member.path == item["path"])
        ).hexdigest()
        for item in manifest["files"]
    )
    assert manifest["manifest_hash_authority"] == "ArtifactType.MANIFEST"
    assert manifest["agent_logs"] == "NOT_AVAILABLE"


def test_readme_truthfully_reports_limited_reproduction() -> None:
    readme = build_readme(
        members=[],
        limitations=["Restricted data must be reacquired."],
        metadata_only_count=1,
        excluded_count=2,
    ).decode()
    assert "Full offline reproduction is not available" in readme
    assert "No reviewed deterministic analysis entrypoint is included" in readme
    assert "NOT_AVAILABLE" in readme


def test_redaction_removes_secrets_prompt_content_and_host_paths() -> None:
    value = redact(
        {
            "token": "secret-value",
            "prompt_content": "private prompt",
            "nested": {"password": "pw", "path": "C:\\private\\file"},
            "safe": "kept",
        }
    )
    assert value == {"nested": {"path": "[REDACTED_PATH]"}, "safe": "kept"}
