from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.agents.prompts import PromptContract, PromptManifestError, get_prompt_contract
from app.core.observability import current_request_id
from app.models import (
    AuditActorType,
    AuditLog,
    AuditOutcome,
    ModelDataAccessLevel,
    ModelInvocation,
    ModelInvocationStatus,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service


class ModelExecutionMode(StrEnum):
    MOCK = "MOCK"
    RECORDED = "RECORDED"


class ModelGovernanceError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class DegradationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requested_capability: str
    primary_provider: str | None
    fallback_provider: str | None
    reason_code: str
    impact: str
    result_status: str
    user_visible_message: str


@dataclass(frozen=True)
class SourceReference:
    source_id: uuid.UUID
    project_id: uuid.UUID
    source_type: str


SourceResolver = Callable[[Session, uuid.UUID], SourceReference | None]


@dataclass(frozen=True)
class InvocationCreate:
    project_id: uuid.UUID
    authorization_actor: User
    actor_type: AuditActorType
    actor_id: str | None
    task_type: str
    prompt_id: str
    prompt_version: str
    prompt_content_hash: str
    input_schema_name: str
    input_schema_version: str
    output_schema_name: str
    output_schema_version: str
    requested_data_access_level: ModelDataAccessLevel
    max_allowed_data_access_level: ModelDataAccessLevel
    effective_data_access_level: ModelDataAccessLevel
    source_ids: tuple[uuid.UUID, ...]
    sanitized_input: Any
    mode: ModelExecutionMode
    fixture_id: str | None = None
    recording_id: str | None = None
    recording_version: str | None = None
    recording_hash: str | None = None
    recording_license_status: str | None = None
    recording_redaction_status: str | None = None
    request_id: str | None = None
    retry_of_invocation_id: uuid.UUID | None = None


_ACCESS_RANK = {
    ModelDataAccessLevel.METADATA_ONLY: 0,
    ModelDataAccessLevel.REDACTED_CONTENT: 1,
    ModelDataAccessLevel.VERIFIED_EVIDENCE_ONLY: 2,
    ModelDataAccessLevel.APPROVED_FULL_CONTENT: 3,
}


def canonical_hash(value: Any) -> str:
    encoded = jsonable_encoder(value)
    canonical = json.dumps(
        encoded, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _governance_error(code: str, message: str) -> ModelGovernanceError:
    return ModelGovernanceError(code, message)


def _validate_prompt(command: InvocationCreate) -> PromptContract:
    try:
        contract = get_prompt_contract(command.prompt_id, command.prompt_version)
    except PromptManifestError as exc:
        raise _governance_error("PROMPT_CONTRACT_INVALID", str(exc)) from exc
    expected = (
        (command.task_type, contract.task_type, "task_type"),
        (command.prompt_content_hash, contract.content_hash, "prompt_content_hash"),
        (command.input_schema_name, contract.input_schema.name, "input_schema_name"),
        (
            command.input_schema_version,
            contract.input_schema.version,
            "input_schema_version",
        ),
        (
            command.output_schema_name,
            contract.output_schema.name,
            "output_schema_name",
        ),
        (
            command.output_schema_version,
            contract.output_schema.version,
            "output_schema_version",
        ),
        (
            command.requested_data_access_level.value,
            contract.requested_data_access_level,
            "requested_data_access_level",
        ),
    )
    for actual, required, field in expected:
        if actual != required:
            raise _governance_error(
                "PROMPT_CONTRACT_MISMATCH", f"{field} does not match the manifest"
            )
    try:
        manifest_max = ModelDataAccessLevel(contract.max_allowed_data_access_level)
    except ValueError as exc:
        raise _governance_error(
            "PROMPT_CONTRACT_INVALID", "Manifest data access level is invalid"
        ) from exc
    if _ACCESS_RANK[command.max_allowed_data_access_level] > _ACCESS_RANK[manifest_max]:
        raise _governance_error(
            "MODEL_DATA_ACCESS_DENIED", "Policy maximum exceeds the prompt maximum"
        )
    return contract


def _validate_access(command: InvocationCreate) -> None:
    effective = _ACCESS_RANK[command.effective_data_access_level]
    if effective > _ACCESS_RANK[command.requested_data_access_level]:
        raise _governance_error(
            "MODEL_DATA_ACCESS_DENIED", "Effective access exceeds requested access"
        )
    if effective > _ACCESS_RANK[command.max_allowed_data_access_level]:
        raise _governance_error(
            "MODEL_DATA_ACCESS_DENIED", "Effective access exceeds policy maximum"
        )


def _validate_mode(command: InvocationCreate) -> dict[str, Any]:
    if command.mode == ModelExecutionMode.MOCK:
        if not command.fixture_id:
            raise _governance_error(
                "MODEL_FIXTURE_INVALID", "MOCK mode requires a fixture identity"
            )
        return {"mode": command.mode.value, "fixture_id": command.fixture_id}
    required = (
        command.recording_id,
        command.recording_version,
        command.recording_hash,
        command.recording_license_status,
        command.recording_redaction_status,
    )
    if any(not value for value in required):
        raise _governance_error(
            "MODEL_RECORDING_INVALID",
            "RECORDED mode requires identity, license status, and redaction status",
        )
    assert command.recording_hash is not None
    if len(command.recording_hash) != 64 or any(
        char not in "0123456789abcdef" for char in command.recording_hash
    ):
        raise _governance_error(
            "MODEL_RECORDING_INVALID", "Recording hash must be lowercase SHA-256"
        )
    return {
        "mode": command.mode.value,
        "recording_id": command.recording_id,
        "recording_version": command.recording_version,
        "recording_hash": command.recording_hash,
        "recording_license_status": command.recording_license_status,
        "recording_redaction_status": command.recording_redaction_status,
        "network_access": "DISABLED",
    }


def _validate_sources(
    session: Session,
    *,
    command: InvocationCreate,
    contract: PromptContract,
    source_resolver: SourceResolver | None,
) -> None:
    if not command.source_ids:
        if contract.required_source_types:
            raise _governance_error(
                "MODEL_SOURCE_REQUIRED", "The prompt requires project sources"
            )
        return
    if source_resolver is None:
        raise _governance_error(
            "MODEL_SOURCE_INVALID", "No source resolver is registered for this task"
        )
    allowed = set(contract.required_source_types)
    seen_types: set[str] = set()
    for source_id in command.source_ids:
        source = source_resolver(session, source_id)
        if source is None or source.project_id != command.project_id:
            raise _governance_error(
                "MODEL_SOURCE_INVALID",
                "Source is missing or belongs to another project",
            )
        if source.source_type not in allowed:
            raise _governance_error(
                "MODEL_SOURCE_INVALID", "Source type is not allowed by the prompt"
            )
        seen_types.add(source.source_type)
    if not allowed.issubset(seen_types):
        raise _governance_error(
            "MODEL_SOURCE_REQUIRED", "A required source type is missing"
        )


def _audit(
    session: Session,
    *,
    invocation: ModelInvocation,
    action: str,
    outcome: AuditOutcome,
    summary: dict[str, Any],
) -> None:
    session.add(
        AuditLog(
            project_id=invocation.project_id,
            actor_type=invocation.actor_type,
            actor_id=invocation.actor_id,
            action=action,
            object_type="model_invocation",
            object_id=invocation.id,
            after_snapshot=summary,
            request_id=invocation.request_id,
            outcome=outcome,
        )
    )


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise _governance_error(
            "MODEL_INVOCATION_CONFLICT", "Model invocation persistence conflicted"
        ) from exc


def create_model_invocation(
    session: Session,
    *,
    command: InvocationCreate,
    source_resolver: SourceResolver | None = None,
) -> ModelInvocation:
    project_service.authorize_project(
        session,
        project_id=command.project_id,
        actor=command.authorization_actor,
        action="project.read",
    )
    contract = _validate_prompt(command)
    _validate_access(command)
    metadata = _validate_mode(command)
    _validate_sources(
        session,
        command=command,
        contract=contract,
        source_resolver=source_resolver,
    )
    if command.retry_of_invocation_id is not None:
        previous = session.get(ModelInvocation, command.retry_of_invocation_id)
        if previous is None or previous.project_id != command.project_id:
            raise _governance_error(
                "MODEL_INVOCATION_NOT_FOUND", "Retry source invocation was not found"
            )
        if previous.status not in {
            ModelInvocationStatus.SUCCEEDED,
            ModelInvocationStatus.FAILED,
        }:
            raise _governance_error(
                "MODEL_INVOCATION_INVALID_STATE",
                "Retry source invocation must be terminal",
            )
        metadata["retry_of_invocation_id"] = str(previous.id)

    request_id = command.request_id or current_request_id()
    invocation = ModelInvocation(
        project_id=command.project_id,
        request_id=request_id,
        actor_type=command.actor_type,
        actor_id=command.actor_id,
        task_type=command.task_type,
        prompt_id=command.prompt_id,
        prompt_version=command.prompt_version,
        prompt_content_hash=command.prompt_content_hash,
        input_schema_name=command.input_schema_name,
        input_schema_version=command.input_schema_version,
        output_schema_name=command.output_schema_name,
        output_schema_version=command.output_schema_version,
        provider=None,
        model=None,
        requested_data_access_level=command.requested_data_access_level,
        max_allowed_data_access_level=command.max_allowed_data_access_level,
        effective_data_access_level=command.effective_data_access_level,
        source_ids=[str(source_id) for source_id in command.source_ids],
        input_hash=canonical_hash(command.sanitized_input),
        status=ModelInvocationStatus.PENDING,
        implementation_metadata=metadata,
    )
    session.add(invocation)
    session.flush()
    _audit(
        session,
        invocation=invocation,
        action="MODEL_INVOCATION_CREATED",
        outcome=AuditOutcome.SUCCEEDED,
        summary={
            "task_type": invocation.task_type,
            "prompt_id": invocation.prompt_id,
            "prompt_version": invocation.prompt_version,
            "input_hash": invocation.input_hash,
            "mode": command.mode.value,
            "source_count": len(command.source_ids),
        },
    )
    _commit(session)
    session.refresh(invocation)
    return invocation


def mark_model_invocation_running(
    session: Session, *, invocation_id: uuid.UUID
) -> ModelInvocation:
    invocation = session.exec(
        select(ModelInvocation)
        .where(ModelInvocation.id == invocation_id)
        .with_for_update()
    ).one()
    if invocation.status != ModelInvocationStatus.PENDING:
        raise _governance_error(
            "MODEL_INVOCATION_INVALID_STATE", "Only PENDING may enter RUNNING"
        )
    invocation.status = ModelInvocationStatus.RUNNING
    session.add(invocation)
    _commit(session)
    session.refresh(invocation)
    return invocation


def complete_model_invocation(
    session: Session,
    *,
    invocation_id: uuid.UUID,
    sanitized_output: Any,
) -> ModelInvocation:
    invocation = session.exec(
        select(ModelInvocation)
        .where(ModelInvocation.id == invocation_id)
        .with_for_update()
    ).one()
    if invocation.status != ModelInvocationStatus.RUNNING:
        raise _governance_error(
            "MODEL_INVOCATION_INVALID_STATE", "Only RUNNING may succeed"
        )
    output_hash = canonical_hash(sanitized_output)
    metadata = invocation.implementation_metadata or {}
    if (
        metadata.get("mode") == ModelExecutionMode.RECORDED.value
        and metadata.get("recording_hash") != output_hash
    ):
        raise _governance_error(
            "MODEL_RECORDING_HASH_MISMATCH",
            "Recorded output does not match the reviewed recording hash",
        )
    invocation.status = ModelInvocationStatus.SUCCEEDED
    invocation.output_hash = output_hash
    invocation.completed_at = get_datetime_utc()
    session.add(invocation)
    _audit(
        session,
        invocation=invocation,
        action="MODEL_INVOCATION_SUCCEEDED",
        outcome=AuditOutcome.SUCCEEDED,
        summary={"output_hash": invocation.output_hash},
    )
    _commit(session)
    session.refresh(invocation)
    return invocation


def fail_model_invocation(
    session: Session,
    *,
    invocation_id: uuid.UUID,
    error_code: str,
    degradation: DegradationRecord | dict[str, Any] | None = None,
) -> ModelInvocation:
    invocation = session.exec(
        select(ModelInvocation)
        .where(ModelInvocation.id == invocation_id)
        .with_for_update()
    ).one()
    if invocation.status not in {
        ModelInvocationStatus.PENDING,
        ModelInvocationStatus.RUNNING,
    }:
        raise _governance_error(
            "MODEL_INVOCATION_INVALID_STATE", "Terminal invocation is immutable"
        )
    validated_degradation = (
        DegradationRecord.model_validate(degradation).model_dump(mode="json")
        if degradation is not None
        else None
    )
    invocation.status = ModelInvocationStatus.FAILED
    invocation.error_code = error_code
    invocation.degradation = validated_degradation
    invocation.completed_at = get_datetime_utc()
    session.add(invocation)
    _audit(
        session,
        invocation=invocation,
        action="MODEL_INVOCATION_FAILED",
        outcome=AuditOutcome.FAILED,
        summary={
            "error_code": error_code,
            "degraded": validated_degradation is not None,
        },
    )
    _commit(session)
    session.refresh(invocation)
    return invocation
