from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class PromptManifestError(ValueError):
    """Raised when the Git-managed prompt registry is invalid."""


class PromptStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


@dataclass(frozen=True)
class SchemaIdentity:
    name: str
    version: str


@dataclass(frozen=True)
class PromptContract:
    prompt_id: str
    prompt_version: str
    task_type: str
    input_schema: SchemaIdentity
    output_schema: SchemaIdentity
    allowed_tools: tuple[str, ...]
    required_source_types: tuple[str, ...]
    max_tool_calls: int
    failure_behavior: str
    requested_data_access_level: str
    max_allowed_data_access_level: str
    status: PromptStatus
    content_hash: str


PROMPT_DIRECTORY = Path(__file__).with_name("prompts")
DEFAULT_MANIFEST_PATH = PROMPT_DIRECTORY / "prompt-manifest.yaml"
DATA_ACCESS_LEVELS = (
    "METADATA_ONLY",
    "REDACTED_CONTENT",
    "VERIFIED_EVIDENCE_ONLY",
    "APPROVED_FULL_CONTENT",
)


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PromptManifestError(f"{field} must be a non-empty string")
    return value


def _string_tuple(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise PromptManifestError(f"{field} must be a list of strings")
    if len(value) != len(set(value)):
        raise PromptManifestError(f"{field} contains duplicate values")
    return tuple(value)


def _schema_identity(value: Any, field: str) -> SchemaIdentity:
    if not isinstance(value, dict):
        raise PromptManifestError(f"{field} must be an object")
    return SchemaIdentity(
        name=_required_string(value.get("name"), f"{field}.name"),
        version=_required_string(value.get("version"), f"{field}.version"),
    )


def prompt_asset_path(contract: PromptContract, manifest_path: Path) -> Path:
    return manifest_path.parent / (
        f"{contract.prompt_id}-{contract.prompt_version}.txt"
    )


def prompt_content_hash(path: Path) -> str:
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def load_prompt_manifest(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> dict[tuple[str, str], PromptContract]:
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PromptManifestError(f"Unable to load prompt manifest: {exc}") from exc

    if not isinstance(raw, dict) or raw.get("manifest_version") != "1.0":
        raise PromptManifestError("Unsupported or missing manifest_version")
    prompts = raw.get("prompts")
    if not isinstance(prompts, list):
        raise PromptManifestError("prompts must be a list")

    registry: dict[tuple[str, str], PromptContract] = {}
    for entry in prompts:
        if not isinstance(entry, dict):
            raise PromptManifestError("Each prompt entry must be an object")
        try:
            status = PromptStatus(_required_string(entry.get("status"), "status"))
        except ValueError as exc:
            raise PromptManifestError("Prompt status is invalid") from exc
        max_tool_calls = entry.get("max_tool_calls")
        if not isinstance(max_tool_calls, int) or max_tool_calls < 0:
            raise PromptManifestError("max_tool_calls must be a non-negative integer")
        contract = PromptContract(
            prompt_id=_required_string(entry.get("prompt_id"), "prompt_id"),
            prompt_version=_required_string(
                entry.get("prompt_version"), "prompt_version"
            ),
            task_type=_required_string(entry.get("task_type"), "task_type"),
            input_schema=_schema_identity(entry.get("input_schema"), "input_schema"),
            output_schema=_schema_identity(entry.get("output_schema"), "output_schema"),
            allowed_tools=_string_tuple(entry.get("allowed_tools"), "allowed_tools"),
            required_source_types=_string_tuple(
                entry.get("required_source_types"), "required_source_types"
            ),
            max_tool_calls=max_tool_calls,
            failure_behavior=_required_string(
                entry.get("failure_behavior"), "failure_behavior"
            ),
            requested_data_access_level=_required_string(
                entry.get("requested_data_access_level"),
                "requested_data_access_level",
            ),
            max_allowed_data_access_level=_required_string(
                entry.get("max_allowed_data_access_level"),
                "max_allowed_data_access_level",
            ),
            status=status,
            content_hash=_required_string(entry.get("content_hash"), "content_hash"),
        )
        key = (contract.prompt_id, contract.prompt_version)
        if key in registry:
            raise PromptManifestError(f"Duplicate prompt identity: {key[0]}@{key[1]}")
        if len(contract.content_hash) != 64 or any(
            char not in "0123456789abcdef" for char in contract.content_hash
        ):
            raise PromptManifestError("content_hash must be lowercase SHA-256")
        try:
            requested_rank = DATA_ACCESS_LEVELS.index(
                contract.requested_data_access_level
            )
            maximum_rank = DATA_ACCESS_LEVELS.index(
                contract.max_allowed_data_access_level
            )
        except ValueError as exc:
            raise PromptManifestError("Prompt data access level is invalid") from exc
        if requested_rank > maximum_rank:
            raise PromptManifestError(
                "requested_data_access_level exceeds max_allowed_data_access_level"
            )
        asset = prompt_asset_path(contract, manifest_path)
        if not asset.is_file() or prompt_content_hash(asset) != contract.content_hash:
            raise PromptManifestError(
                f"Prompt content hash mismatch: {contract.prompt_id}@{contract.prompt_version}"
            )
        registry[key] = contract
    return registry


def get_prompt_contract(
    prompt_id: str,
    prompt_version: str,
    *,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> PromptContract:
    registry = load_prompt_manifest(manifest_path)
    try:
        return registry[(prompt_id, prompt_version)]
    except KeyError as exc:
        raise PromptManifestError(
            f"Unknown prompt: {prompt_id}@{prompt_version}"
        ) from exc
