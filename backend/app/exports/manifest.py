from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .safety import normalize_package_path

MANIFEST_SCHEMA_VERSION = "reca.repro-manifest.v1"


@dataclass(frozen=True)
class PackageMember:
    path: str
    content: bytes
    member_type: str
    source: dict[str, Any]
    license_status: str = "NOT_APPLICABLE"
    sensitive: bool = False
    redistribution: str = "ALLOWED"

    def __post_init__(self) -> None:
        normalize_package_path(self.path)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def build_manifest(
    members: list[PackageMember], *, implementation: dict[str, Any]
) -> tuple[dict[str, Any], bytes]:
    files = [
        {
            "path": member.path,
            "size": len(member.content),
            "sha256": member.sha256,
            "type": member.member_type,
            "source": member.source,
            "license_status": member.license_status,
            "sensitive": member.sensitive,
            "redistribution": member.redistribution,
        }
        for member in sorted(members, key=lambda item: item.path)
    ]
    manifest = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "manifest_path": "manifest.json",
        "manifest_hash_authority": "ArtifactType.MANIFEST",
        "files": files,
        "runtime_dependencies": implementation["runtime_dependencies"],
        "service_images": implementation["service_images"],
        "upstream_projects": implementation["upstream_projects"],
        "vendored_assets": implementation["vendored_assets"],
        "prompt_versions": implementation["prompt_versions"],
        "ruleset_versions": implementation["ruleset_versions"],
        "statistical_engines": implementation["statistical_engines"],
        "citation_styles": implementation["citation_styles"],
        "configuration_hashes": implementation["configuration_hashes"],
        "source_object_versions": implementation["source_object_versions"],
        "artifact_hashes": implementation["artifact_hashes"],
        "agent_logs": "NOT_AVAILABLE",
        "limitations": implementation["limitations"],
    }
    return manifest, canonical_json(manifest)


def build_readme(
    *,
    members: list[PackageMember],
    limitations: list[str],
    metadata_only_count: int,
    excluded_count: int,
) -> bytes:
    paths = {member.path for member in members}
    has_analysis = any(path.startswith("08_analysis/") for path in paths)
    lines = [
        "# RECA Reproduction Package",
        "",
        "This package records the authorized project snapshot used at export time.",
        "",
        "## Integrity",
        "",
        "Verify every payload member's SHA-256 against `manifest.json` before use.",
        "",
        "## Data and literature",
        "",
        f"Metadata-only items: {metadata_only_count}.",
        f"Excluded items: {excluded_count}.",
    ]
    if metadata_only_count or excluded_count:
        lines.extend(
            [
                "Full offline reproduction is not available for all inputs.",
                "Use the acquisition and license metadata in the package to obtain authorized inputs.",
            ]
        )
    lines.extend(["", "## Analysis", ""])
    if has_analysis:
        lines.append(
            "Reviewed deterministic analysis records are under `08_analysis/`; use only the recorded entrypoint and locked environment metadata."
        )
    else:
        lines.append("No reviewed deterministic analysis entrypoint is included.")
    lines.extend(["", "## Privacy and license", ""])
    lines.append(
        "Do not redistribute metadata-only or excluded sources beyond their recorded rights."
    )
    lines.extend(["", "## Known limitations", ""])
    lines.extend(f"- {item}" for item in limitations)
    lines.append("- Agent logs: NOT_AVAILABLE until M8; no run record was fabricated.")
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")
