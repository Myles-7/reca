import hashlib
import json
from pathlib import Path

import pytest

from app.agents.prompts import (
    DEFAULT_MANIFEST_PATH,
    PromptManifestError,
    get_prompt_contract,
    load_prompt_manifest,
)

pytestmark = pytest.mark.no_database


def test_git_managed_prompt_manifest_and_content_hash_are_valid() -> None:
    contract = get_prompt_contract("governance-contract-test", "1.0.0")

    assert DEFAULT_MANIFEST_PATH.name == "prompt-manifest.yaml"
    assert contract.task_type == "GOVERNANCE_CONTRACT_TEST"
    assert contract.input_schema.version == "1.0"
    assert contract.output_schema.version == "1.0"
    assert contract.allowed_tools == ()
    assert contract.required_source_types == ()


def _entry(content_hash: str) -> dict[str, object]:
    return {
        "prompt_id": "fixture",
        "prompt_version": "1.0.0",
        "task_type": "GOVERNANCE_CONTRACT_TEST",
        "input_schema": {"name": "Input", "version": "1.0"},
        "output_schema": {"name": "Output", "version": "1.0"},
        "allowed_tools": [],
        "required_source_types": [],
        "max_tool_calls": 0,
        "failure_behavior": "FAIL_CLOSED",
        "requested_data_access_level": "METADATA_ONLY",
        "max_allowed_data_access_level": "METADATA_ONLY",
        "status": "ACTIVE",
        "content_hash": content_hash,
    }


def _write_manifest(tmp_path: Path, prompts: list[dict[str, object]]) -> Path:
    path = tmp_path / "prompt-manifest.yaml"
    path.write_text(
        json.dumps({"manifest_version": "1.0", "prompts": prompts}),
        encoding="utf-8",
    )
    return path


def test_manifest_rejects_duplicate_prompt_identity(tmp_path: Path) -> None:
    content = b"fixture\n"
    (tmp_path / "fixture-1.0.0.txt").write_bytes(content)
    entry = _entry(hashlib.sha256(content).hexdigest())
    path = _write_manifest(tmp_path, [entry, entry])

    with pytest.raises(PromptManifestError, match="Duplicate prompt identity"):
        load_prompt_manifest(path)


def test_manifest_rejects_content_hash_mismatch(tmp_path: Path) -> None:
    (tmp_path / "fixture-1.0.0.txt").write_text("changed\n", encoding="utf-8")
    path = _write_manifest(tmp_path, [_entry("0" * 64)])

    with pytest.raises(PromptManifestError, match="content hash mismatch"):
        load_prompt_manifest(path)


def test_manifest_rejects_unknown_or_escalating_access_level(tmp_path: Path) -> None:
    content = b"fixture\n"
    (tmp_path / "fixture-1.0.0.txt").write_bytes(content)
    entry = _entry(hashlib.sha256(content).hexdigest())
    entry["requested_data_access_level"] = "APPROVED_FULL_CONTENT"
    entry["max_allowed_data_access_level"] = "METADATA_ONLY"
    path = _write_manifest(tmp_path, [entry])

    with pytest.raises(PromptManifestError, match="exceeds"):
        load_prompt_manifest(path)


def test_manifest_rejects_unknown_prompt() -> None:
    with pytest.raises(PromptManifestError, match="Unknown prompt"):
        get_prompt_contract("unknown", "1.0.0")
