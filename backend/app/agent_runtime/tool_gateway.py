from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from fastapi.encoders import jsonable_encoder
from sqlmodel import Session

from app.approvals import service as approval_service
from app.cleaning import service as cleaning_service
from app.core.db import engine
from app.data_quality import service as data_quality_service
from app.data_quality.schemas import QualityRunCreate
from app.evidence.retrieval import search_evidence
from app.evidence.schemas import EvidenceSearchRequest
from app.jobs.dispatcher import dispatcher as default_dispatcher
from app.models import ApprovalStatus, ToolCallStatus, User

from . import service as runtime_service
from .policies import mark_untrusted_content
from .schemas import (
    ApplyApprovedTransformationsInput,
    ProfileDatasetInput,
    SafeSummary,
    ToolCallRequest,
)
from .snapshot import build_project_context_snapshot


class ToolGateway(Protocol):
    async def execute(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ToolExecutionContext:
    project_id: uuid.UUID
    actor_id: uuid.UUID
    agent_run_id: uuid.UUID
    request_id: str | None


def _hash(value: Any) -> str:
    payload = json.dumps(
        jsonable_encoder(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class DatabaseToolGateway:
    """Explicit Service gateway; SDK wrappers never receive a database Session."""

    def __init__(self, context: ToolExecutionContext) -> None:
        self.context = context
        self._call_number = 0
        self._counter_lock = asyncio.Lock()

    async def execute(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        async with self._counter_lock:
            self._call_number += 1
            call_number = self._call_number
        return await asyncio.to_thread(
            self._execute_sync, tool_name, arguments, call_number
        )

    def _actor(self, session: Session) -> User:
        actor = session.get(User, self.context.actor_id)
        if actor is None:
            raise RuntimeError("AGENT_ACTOR_NOT_FOUND")
        return actor

    def _execute_sync(
        self, tool_name: str, arguments: dict[str, Any], call_number: int
    ) -> dict[str, Any]:
        snapshot: Any | None = None
        source_ids: list[uuid.UUID] = []
        safe_attributes: dict[str, str | int | bool | None] = {
            "argument_count": len(arguments)
        }
        if tool_name == "profile_dataset":
            profile_input = ProfileDatasetInput.model_validate(arguments)
            source_ids = [profile_input.dataset_version_id]
            safe_attributes.update(
                dataset_version_id=str(profile_input.dataset_version_id),
                rule_set=profile_input.rule_set,
            )
        elif tool_name == "apply_approved_transformations":
            cleaning_input = ApplyApprovedTransformationsInput.model_validate(arguments)
            source_ids = [cleaning_input.cleaning_plan_id]
            safe_attributes["cleaning_plan_id"] = str(cleaning_input.cleaning_plan_id)
        safe_input = SafeSummary(
            kind="tool_request",
            text=str(arguments.get("query", ""))[:500] or None,
            attributes=safe_attributes,
        )
        idempotency_key = (
            f"agent-tool:{self.context.agent_run_id}:{call_number}:{_hash(arguments)}"
        )
        with Session(engine) as session:
            actor = self._actor(session)
            snapshot = build_project_context_snapshot(
                session, actor=actor, project_id=self.context.project_id
            )
            source_hashes = {
                key: snapshot.source_object_versions[key]
                for key in ("dataset_versions", "cleaning_plans")
                if key in snapshot.source_object_versions
            }
            call = runtime_service.request_tool_call(
                session,
                actor=actor,
                project_id=self.context.project_id,
                command=ToolCallRequest(
                    agent_run_id=self.context.agent_run_id,
                    tool_name=tool_name,
                    safe_input_summary=safe_input,
                    source_ids=source_ids,
                    source_hashes=source_hashes,
                    idempotency_key=idempotency_key,
                    request_id=self.context.request_id,
                    policy_arguments=arguments,
                ),
            )
            if call.status == ToolCallStatus.WAITING_APPROVAL:
                try:
                    cleaning_input = ApplyApprovedTransformationsInput.model_validate(
                        arguments
                    )
                    plan = cleaning_service.get_plan(
                        session, actor=actor, plan_id=cleaning_input.cleaning_plan_id
                    )
                    approval_id = plan.get("approval_record_id")
                    approval_payload_hash = plan.get("payload_hash")
                    if approval_id is None or approval_payload_hash is None:
                        raise RuntimeError("APPROVAL_REQUIRED")
                    runtime_service.bind_tool_call_approval(
                        session,
                        actor=actor,
                        project_id=self.context.project_id,
                        tool_call_id=call.id,
                        approval_id=uuid.UUID(str(approval_id)),
                        approval_payload_hash=str(approval_payload_hash),
                        target_object_type="cleaning_plan",
                        target_object_id=cleaning_input.cleaning_plan_id,
                    )
                except Exception as exc:
                    error_code = str(
                        getattr(exc, "code", str(exc) or "APPROVAL_INVALID")
                    )[:100]
                    runtime_service.transition_tool_call(
                        session,
                        actor=actor,
                        project_id=self.context.project_id,
                        tool_call_id=call.id,
                        target=ToolCallStatus.DENIED,
                        error_code=error_code,
                    )
                    raise RuntimeError(error_code) from exc
                return {
                    "tool_name": tool_name,
                    "tool_version": "1.0",
                    "status": "WAITING_APPROVAL",
                    "result_summary": {},
                    "output_object_ids": [],
                    "warnings": [],
                    "limitations": ["External formal approval is required."],
                    "error_code": None,
                    "tool_call_id": str(call.id),
                }
            if call.status == ToolCallStatus.REQUESTED:
                runtime_service.transition_tool_call(
                    session,
                    actor=actor,
                    project_id=self.context.project_id,
                    tool_call_id=call.id,
                    target=ToolCallStatus.RUNNING,
                )
            try:
                result = self._dispatch(session, actor, tool_name, arguments)
                summary = SafeSummary(
                    kind="tool_result",
                    attributes={
                        "status": "COMPLETED",
                        "result_count": int(result.get("result_count", 1)),
                    },
                )
                runtime_service.transition_tool_call(
                    session,
                    actor=actor,
                    project_id=self.context.project_id,
                    tool_call_id=call.id,
                    target=ToolCallStatus.COMPLETED,
                    safe_output_summary=summary,
                    job_id=uuid.UUID(str(result["job_id"]))
                    if result.get("job_id")
                    else None,
                    output_object_type=str(result["output_object_type"])
                    if result.get("output_object_type")
                    else None,
                    output_object_id=uuid.UUID(str(result["output_object_id"]))
                    if result.get("output_object_id")
                    else None,
                )
                return {
                    "tool_name": result["tool_name"],
                    "tool_version": result["tool_version"],
                    "status": result["status"],
                    "result_summary": result.get("result_summary", {}),
                    "result_count": int(result.get("result_count", 0)),
                    "output_object_ids": result.get("output_object_ids", []),
                    "warnings": result.get("warnings", []),
                    "limitations": result.get("limitations", []),
                    "error_code": result.get("error_code"),
                    "tool_call_id": str(call.id),
                }
            except Exception as exc:
                error_code = str(getattr(exc, "code", "TOOL_EXECUTION_FAILED"))[:100]
                runtime_service.transition_tool_call(
                    session,
                    actor=actor,
                    project_id=self.context.project_id,
                    tool_call_id=call.id,
                    target=ToolCallStatus.FAILED,
                    error_code=error_code,
                    retryable=False,
                )
                raise RuntimeError(error_code) from exc

    def _dispatch(
        self, session: Session, actor: User, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        if tool_name == "get_project_state":
            snapshot = build_project_context_snapshot(
                session, actor=actor, project_id=self.context.project_id
            )
            return {
                "tool_name": tool_name,
                "tool_version": "1.0",
                "status": "COMPLETED",
                "result_summary": {
                    "project_id": str(snapshot.project_id),
                    "stage": snapshot.project_stage.value,
                    "snapshot_hash": snapshot.canonical_hash,
                    "blocking_issues": snapshot.blocking_issues,
                    "pending_approval_ids": [
                        str(value) for value in snapshot.pending_approval_ids
                    ],
                    "allowed_next_actions": snapshot.allowed_next_actions,
                },
                "result_count": 1,
                "output_object_ids": [],
                "warnings": [],
                "limitations": [],
                "error_code": None,
            }
        if tool_name == "get_pending_approvals":
            values, _ = approval_service.list_approvals(
                session,
                actor=actor,
                project_id=self.context.project_id,
                status=ApprovalStatus.PENDING,
                approval_type=None,
                target_object_type=None,
                requested_by_actor_type=None,
                page=1,
                page_size=100,
            )
            ids = [str(value["id"]) for value in values]
            return {
                "tool_name": tool_name,
                "tool_version": "1.0",
                "status": "COMPLETED",
                "result_summary": {"pending_approval_ids": ids},
                "result_count": len(ids),
                "output_object_ids": ids,
                "warnings": [],
                "limitations": [],
                "error_code": None,
            }
        if tool_name == "retrieve_evidence":
            evidence_input = EvidenceSearchRequest.model_validate(arguments)
            evidence_result = search_evidence(
                session,
                actor=actor,
                project_id=self.context.project_id,
                payload=evidence_input,
            )
            candidates = [
                {
                    "evidence_span_id": str(item.evidence_span_id)
                    if item.evidence_span_id
                    else None,
                    "document_id": str(item.document_id),
                    "page_number": item.page_number,
                    "source_text_hash": item.source_text_hash,
                    "source_content": mark_untrusted_content(
                        item.source_text, max_chars=800
                    ),
                    "score": item.rerank_score
                    or item.keyword_score
                    or item.vector_score,
                    "limitations": item.limitations,
                }
                for item in evidence_result.candidates
            ]
            return {
                "tool_name": tool_name,
                "tool_version": "1.0",
                "status": "COMPLETED",
                "result_summary": {
                    "retrieval_run_id": str(evidence_result.retrieval_run_id),
                    "candidates": candidates,
                },
                "result_count": len(candidates),
                "output_object_ids": [
                    item["evidence_span_id"]
                    for item in candidates
                    if item["evidence_span_id"] is not None
                ],
                "warnings": [],
                "limitations": evidence_result.limitations,
                "error_code": None,
            }
        if tool_name == "profile_dataset":
            quality_input = ProfileDatasetInput.model_validate(arguments)
            quality_result = data_quality_service.request_quality_run(
                session,
                actor=actor,
                version_id=quality_input.dataset_version_id,
                payload=QualityRunCreate(rule_set=quality_input.rule_set),
                idempotency_key=(
                    f"agent-profile:{self.context.agent_run_id}:"
                    f"{quality_input.dataset_version_id}:{quality_input.rule_set}"
                ),
                dispatcher=default_dispatcher,
            )
            assert quality_result.data is not None
            run = quality_result.data["run"]
            job = quality_result.data["job"]
            return {
                "tool_name": tool_name,
                "tool_version": "1.0",
                "status": "COMPLETED",
                "result_summary": {
                    "data_quality_run_id": str(run["id"]),
                    "data_quality_run_status": str(run["status"]),
                    "job_id": str(job["id"]),
                    "job_status": str(job["status"]),
                    "dataset_version_id": str(quality_input.dataset_version_id),
                    "ruleset_id": str(run["ruleset_id"]),
                },
                "result_count": 1,
                "output_object_ids": [str(run["id"])],
                "warnings": [],
                "limitations": [
                    "Quality metrics are produced by the deterministic Data Quality Worker."
                ],
                "error_code": None,
                "job_id": str(job["id"]),
                "output_object_type": "data_quality_run",
                "output_object_id": str(run["id"]),
            }
        raise RuntimeError("TOOL_HANDLER_NOT_REGISTERED")
