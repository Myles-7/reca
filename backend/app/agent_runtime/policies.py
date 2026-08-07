from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.models import ApprovalStatus, ModelDataAccessLevel, ProjectStage

from .registry import PROHIBITED_NAMES, Confirmation, ToolDefinition, get_tool
from .schemas import ModelDataDecision


class PolicyDenied(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_ACCESS_RANK = {
    ModelDataAccessLevel.METADATA_ONLY: 0,
    ModelDataAccessLevel.REDACTED_CONTENT: 1,
    ModelDataAccessLevel.VERIFIED_EVIDENCE_ONLY: 2,
    ModelDataAccessLevel.APPROVED_FULL_CONTENT: 3,
}
_PROHIBITED_ARGUMENTS = re.compile(
    r"(^|_)(shell|python|sql|filesystem|path|url|authorization|cookie|token|secret|connection_string)($|_)",
    re.IGNORECASE,
)
CONTENT_BOUNDARY_START = "<untrusted-source-content>"
CONTENT_BOUNDARY_END = "</untrusted-source-content>"


@dataclass(frozen=True)
class ApprovalProjection:
    id: uuid.UUID
    project_id: uuid.UUID
    status: ApprovalStatus
    payload_hash: str
    requested_by_actor_id: str | None
    expired: bool = False
    stale: bool = False


def reject_prohibited_arguments(value: Any, *, path: str = "input") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _PROHIBITED_ARGUMENTS.search(str(key)):
                raise PolicyDenied(
                    "PROHIBITED_ARGUMENT", f"Prohibited argument at {path}."
                )
            reject_prohibited_arguments(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for item in value:
            reject_prohibited_arguments(item, path=path)


def validate_tool_policy(
    *,
    name: str,
    version: str,
    project_stage: ProjectStage,
    permissions: set[str],
    snapshot_current: bool,
    arguments: dict[str, Any],
) -> ToolDefinition:
    if name in PROHIBITED_NAMES:
        raise PolicyDenied("PROHIBITED_TOOL", "The requested capability is prohibited.")
    definition = get_tool(name, version)
    if definition is None:
        raise PolicyDenied("UNKNOWN_TOOL", "The requested Tool is not registered.")
    if not definition.enabled:
        raise PolicyDenied(
            definition.disabled_reason_code or "TOOL_UNAVAILABLE",
            "The requested Tool is unavailable.",
        )
    if not snapshot_current:
        raise PolicyDenied("STALE_PROJECT_CONTEXT", "Project context must be rebuilt.")
    if project_stage not in definition.allowed_stages:
        raise PolicyDenied(
            "TOOL_STAGE_DENIED", "The Tool is unavailable at this stage."
        )
    if definition.required_project_action not in permissions:
        raise PolicyDenied(
            "TOOL_PERMISSION_DENIED", "The Tool is not allowed for this actor."
        )
    reject_prohibited_arguments(arguments)
    try:
        definition.input_schema.model_validate(arguments)
    except ValidationError as exc:
        raise PolicyDenied(
            "TOOL_INPUT_SCHEMA_INVALID",
            "Tool input did not match its registered schema.",
        ) from exc
    return definition


def validate_approval(
    *,
    definition: ToolDefinition,
    projection: ApprovalProjection | None,
    project_id: uuid.UUID,
    actor_id: uuid.UUID,
    expected_payload_hash: str,
) -> None:
    if definition.confirmation != Confirmation.FORMAL_APPROVAL:
        return
    if projection is None:
        raise PolicyDenied("APPROVAL_REQUIRED", "A formal approval is required.")
    if projection.project_id != project_id:
        raise PolicyDenied(
            "APPROVAL_INVALID", "Approval does not belong to this project."
        )
    if (
        projection.status != ApprovalStatus.APPROVED
        or projection.expired
        or projection.stale
    ):
        raise PolicyDenied("APPROVAL_INVALID", "Approval is not currently valid.")
    if projection.payload_hash != expected_payload_hash:
        raise PolicyDenied("APPROVAL_HASH_MISMATCH", "Approval payload does not match.")
    if projection.requested_by_actor_id == str(actor_id):
        raise PolicyDenied(
            "SELF_APPROVAL_PROHIBITED", "An Agent request cannot approve itself."
        )


def decide_model_data_access(
    *,
    requested: ModelDataAccessLevel,
    policy_maximum: ModelDataAccessLevel,
    tool_maximum: ModelDataAccessLevel,
) -> ModelDataDecision:
    effective = min(
        (requested, policy_maximum, tool_maximum),
        key=lambda level: _ACCESS_RANK[level],
    )
    return ModelDataDecision(
        requested=requested, maximum=policy_maximum, effective=effective
    )


def mark_untrusted_content(content: str, *, max_chars: int = 4000) -> str:
    sanitized = content.replace(CONTENT_BOUNDARY_START, "").replace(
        CONTENT_BOUNDARY_END, ""
    )
    return f"{CONTENT_BOUNDARY_START}\n{sanitized[:max_chars]}\n{CONTENT_BOUNDARY_END}"


def validate_output(definition: ToolDefinition, output: dict[str, Any]) -> None:
    try:
        definition.output_schema.model_validate(output)
    except ValidationError as exc:
        raise PolicyDenied(
            "TOOL_OUTPUT_SCHEMA_INVALID",
            "Tool output did not match its registered schema.",
        ) from exc


def redact_trace_payload(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "agent_run_id",
        "tool_call_id",
        "tool_name",
        "tool_version",
        "status",
        "error_code",
        "latency_ms",
        "input_tokens",
        "output_tokens",
        "total_tokens",
    }
    return {key: value for key, value in payload.items() if key in allowed}
