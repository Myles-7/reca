from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    MaxTurnsExceeded,
    Model,
    ModelBehaviorError,
    OutputGuardrailTripwireTriggered,
    RunConfig,
    Runner,
    ToolGuardrailFunctionOutput,
    ToolInputGuardrailTripwireTriggered,
    ToolOutputGuardrailTripwireTriggered,
    ToolTimeoutError,
    function_tool,
    input_guardrail,
    output_guardrail,
    tool_input_guardrail,
    tool_output_guardrail,
)
from pydantic import BaseModel, ConfigDict, Field

from app.agents.prompts import get_prompt_contract, prompt_asset_path

from .policies import PolicyDenied, reject_prohibited_arguments
from .registry import PROHIBITED_NAMES, TOOL_REGISTRY
from .schemas import ToolOutput
from .tool_gateway import ToolGateway

SDK_VERSION = "0.19.1"
PROMPT_ID = "research-orchestrator"
PROMPT_VERSION = "1.0.0"
REGISTRY_VERSION = "m8.1"


class ProviderMode(StrEnum):
    MOCK = "MOCK"
    RECORDED = "RECORDED"
    LIVE = "LIVE"


class OrchestratorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(
        pattern=r"^(COMPLETED|WAITING_USER_INPUT|WAITING_APPROVAL|FAILED)$"
    )
    stage: str
    summary: str = Field(max_length=2000)
    source_ids: list[str] = Field(default_factory=list, max_length=100)
    limitations: list[str] = Field(default_factory=list, max_length=50)


class OrchestrationError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class ResumeBinding:
    sdk_version: str
    registry_version: str
    prompt_id: str
    prompt_version: str
    snapshot_hash: str
    project_id: uuid.UUID
    actor_id: uuid.UUID


@dataclass(frozen=True)
class OrchestrationResult:
    output: OrchestratorOutput | None
    waiting_for_approval: bool
    usage_requests: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    resume_binding: ResumeBinding
    sdk_state: Any | None = field(default=None, repr=False, compare=False)


def validate_resume_binding(
    binding: ResumeBinding,
    *,
    project_id: uuid.UUID,
    actor_id: uuid.UUID,
    snapshot_hash: str,
) -> None:
    expected = ResumeBinding(
        sdk_version=SDK_VERSION,
        registry_version=REGISTRY_VERSION,
        prompt_id=PROMPT_ID,
        prompt_version=PROMPT_VERSION,
        snapshot_hash=snapshot_hash,
        project_id=project_id,
        actor_id=actor_id,
    )
    if binding != expected:
        raise OrchestrationError(
            "RESUME_STATE_INCOMPATIBLE",
            "The paused Agent state is stale or incompatible; start a new run.",
        )


@input_guardrail(run_in_parallel=False)
def reject_instruction_override(
    context: Any, agent: Any, value: Any
) -> GuardrailFunctionOutput:
    del context, agent
    lowered = str(value).casefold()
    patterns = (
        "ignore previous instructions",
        "bypass permission",
        "approve on behalf",
        "execute_shell",
        "execute_python",
        "execute_sql",
        "apply_patch",
        "mcp discovery",
    )
    return GuardrailFunctionOutput(
        output_info={"code": "PROMPT_INJECTION_OR_PROHIBITED_CAPABILITY"},
        tripwire_triggered=any(pattern in lowered for pattern in patterns),
    )


@output_guardrail
def validate_orchestrator_output(
    context: Any, agent: Any, value: Any
) -> GuardrailFunctionOutput:
    del context, agent
    output = OrchestratorOutput.model_validate(value)
    invalid = output.status == "COMPLETED" and not output.source_ids
    return GuardrailFunctionOutput(
        output_info={"code": "ORCHESTRATOR_SOURCE_REQUIRED"},
        tripwire_triggered=invalid,
    )


@tool_input_guardrail
def validate_sdk_tool_input(data: Any) -> ToolGuardrailFunctionOutput:
    try:
        arguments = json.loads(data.context.tool_arguments)
        reject_prohibited_arguments(arguments)
    except (json.JSONDecodeError, PolicyDenied) as exc:
        return ToolGuardrailFunctionOutput.raise_exception(
            {"code": getattr(exc, "code", "TOOL_INPUT_SCHEMA_INVALID")}
        )
    return ToolGuardrailFunctionOutput.allow()


@tool_output_guardrail
def validate_sdk_tool_output(data: Any) -> ToolGuardrailFunctionOutput:
    serialized = json.dumps(data.output, default=str).casefold()
    prohibited = (
        "authorization:",
        "bearer ",
        "connection_string",
        "signed_url",
        "cookie",
        "secret_key",
    )
    if any(value in serialized for value in prohibited):
        return ToolGuardrailFunctionOutput.raise_exception(
            {"code": "SENSITIVE_TOOL_OUTPUT"}
        )
    try:
        ToolOutput.model_validate(data.output)
    except ValueError:
        return ToolGuardrailFunctionOutput.raise_exception(
            {"code": "TOOL_OUTPUT_SCHEMA_INVALID"}
        )
    return ToolGuardrailFunctionOutput.allow()


def _tools(gateway: ToolGateway) -> list[Any]:
    @function_tool(
        name_override="get_project_state",
        description_override="Return the fresh authorized project state projection.",
        timeout=30,
        strict_mode=True,
        tool_input_guardrails=[validate_sdk_tool_input],
        tool_output_guardrails=[validate_sdk_tool_output],
        timeout_behavior="raise_exception",
    )
    async def get_project_state() -> dict[str, Any]:
        return await gateway.execute("get_project_state", {})

    @function_tool(
        name_override="get_pending_approvals",
        description_override="Return pending ApprovalRecord identifiers for this project.",
        timeout=30,
        strict_mode=True,
        tool_input_guardrails=[validate_sdk_tool_input],
        tool_output_guardrails=[validate_sdk_tool_output],
        timeout_behavior="raise_exception",
    )
    async def get_pending_approvals() -> dict[str, Any]:
        return await gateway.execute("get_pending_approvals", {})

    @function_tool(
        name_override="retrieve_evidence",
        description_override="Retrieve current project-scoped evidence candidates.",
        timeout=60,
        strict_mode=True,
        tool_input_guardrails=[validate_sdk_tool_input],
        tool_output_guardrails=[validate_sdk_tool_output],
        timeout_behavior="raise_exception",
    )
    async def retrieve_evidence(
        query: str,
        document_ids: list[str],
        top_k: int,
        retrieval_mode: str,
        include_uncertain_literature: bool,
    ) -> dict[str, Any]:
        return await gateway.execute(
            "retrieve_evidence",
            {
                "query": query,
                "document_ids": document_ids,
                "top_k": top_k,
                "retrieval_mode": retrieval_mode,
                "include_uncertain_literature": include_uncertain_literature,
            },
        )

    @function_tool(
        name_override="profile_dataset",
        description_override="Queue the deterministic quality profile for an authorized DatasetVersion.",
        timeout=120,
        strict_mode=True,
        tool_input_guardrails=[validate_sdk_tool_input],
        tool_output_guardrails=[validate_sdk_tool_output],
        timeout_behavior="raise_exception",
    )
    async def profile_dataset(dataset_version_id: str, rule_set: str) -> dict[str, Any]:
        return await gateway.execute(
            "profile_dataset",
            {"dataset_version_id": dataset_version_id, "rule_set": rule_set},
        )

    @function_tool(
        name_override="apply_approved_transformations",
        description_override="Execute only a current externally approved CleaningPlan through the governed Worker path.",
        timeout=120,
        strict_mode=True,
        tool_input_guardrails=[validate_sdk_tool_input],
        tool_output_guardrails=[validate_sdk_tool_output],
        timeout_behavior="raise_exception",
    )
    async def apply_approved_transformations(
        cleaning_plan_id: str,
    ) -> dict[str, Any]:
        return await gateway.execute(
            "apply_approved_transformations",
            {"cleaning_plan_id": cleaning_plan_id},
        )

    tools = [
        get_project_state,
        get_pending_approvals,
        retrieve_evidence,
        profile_dataset,
        apply_approved_transformations,
    ]
    contract = get_prompt_contract(PROMPT_ID, PROMPT_VERSION)
    if tuple(tool.name for tool in tools) != contract.allowed_tools:
        raise OrchestrationError(
            "PROMPT_TOOL_CONTRACT_MISMATCH",
            "The orchestrator Tool set does not match the PromptContract.",
        )
    return tools


def build_run_config(
    *, correlation_id: str, tracing_enabled: bool = False
) -> RunConfig:
    return RunConfig(
        tracing_disabled=not tracing_enabled,
        trace_include_sensitive_data=False,
        workflow_name="RECA ResearchOrchestrator",
        group_id=correlation_id,
        trace_metadata={
            "component": "research_orchestrator",
            "sdk_version": SDK_VERSION,
        },
        tool_not_found_behavior="raise_error",
    )


class ResearchOrchestratorAdapter:
    def __init__(
        self, *, gateway: ToolGateway, model: Model | str, provider_mode: ProviderMode
    ) -> None:
        if provider_mode == ProviderMode.LIVE and model is None:
            raise OrchestrationError(
                "MODEL_PROVIDER_UNAVAILABLE",
                "Live provider configuration is unavailable.",
            )
        contract = get_prompt_contract(PROMPT_ID, PROMPT_VERSION)
        instructions = prompt_asset_path(
            contract, Path(__file__).parents[1] / "agents/prompts/prompt-manifest.yaml"
        ).read_text(encoding="utf-8")
        self.provider_mode = provider_mode
        self.agent = Agent(
            name="ResearchOrchestrator",
            instructions=instructions,
            model=model,
            tools=_tools(gateway),
            output_type=OrchestratorOutput,
            input_guardrails=[reject_instruction_override],
            output_guardrails=[validate_orchestrator_output],
            mcp_servers=[],
        )
        self._assert_topology()

    def _assert_topology(self) -> None:
        names = {tool.name.casefold() for tool in self.agent.tools}
        if self.agent.handoffs or self.agent.mcp_servers:
            raise OrchestrationError(
                "PROHIBITED_AGENT_TOPOLOGY", "Handoffs and MCP are prohibited."
            )
        if names.intersection(name.casefold() for name in PROHIBITED_NAMES):
            raise OrchestrationError(
                "PROHIBITED_TOOL_REGISTERED", "A prohibited Tool was registered."
            )
        if any(name not in TOOL_REGISTRY for name in names):
            raise OrchestrationError(
                "UNKNOWN_TOOL_REGISTERED", "An unknown Tool was registered."
            )

    async def run(
        self,
        *,
        user_goal: str,
        project_id: uuid.UUID,
        actor_id: uuid.UUID,
        snapshot_hash: str,
        correlation_id: str,
        max_turns: int,
        timeout_seconds: float,
    ) -> OrchestrationResult:
        binding = ResumeBinding(
            sdk_version=SDK_VERSION,
            registry_version=REGISTRY_VERSION,
            prompt_id=PROMPT_ID,
            prompt_version=PROMPT_VERSION,
            snapshot_hash=snapshot_hash,
            project_id=project_id,
            actor_id=actor_id,
        )
        try:
            result = await asyncio.wait_for(
                Runner.run(
                    self.agent,
                    user_goal,
                    max_turns=max_turns,
                    run_config=build_run_config(correlation_id=correlation_id),
                ),
                timeout=timeout_seconds,
            )
        except TimeoutError as exc:
            raise OrchestrationError(
                "AGENT_TIMEOUT", "The Agent run timed out.", retryable=True
            ) from exc
        except asyncio.CancelledError:
            raise
        except MaxTurnsExceeded as exc:
            raise OrchestrationError(
                "AGENT_MAX_TURNS", "The Agent reached its turn limit."
            ) from exc
        except (
            InputGuardrailTripwireTriggered,
            OutputGuardrailTripwireTriggered,
            ToolInputGuardrailTripwireTriggered,
            ToolOutputGuardrailTripwireTriggered,
        ) as exc:
            raise OrchestrationError(
                "AGENT_GUARDRAIL_TRIPPED", "A deterministic guardrail denied the run."
            ) from exc
        except ToolTimeoutError as exc:
            raise OrchestrationError(
                "TOOL_TIMEOUT", "A registered Tool timed out.", retryable=True
            ) from exc
        except ModelBehaviorError as exc:
            raise OrchestrationError(
                "MODEL_OUTPUT_INVALID",
                "The model returned an invalid structured output.",
            ) from exc
        except Exception as exc:
            raise OrchestrationError(
                "MODEL_PROVIDER_FAILED",
                "The configured model provider failed.",
                retryable=True,
            ) from exc
        usage = result.context_wrapper.usage
        output = (
            None
            if result.interruptions
            else OrchestratorOutput.model_validate(result.final_output)
        )
        waiting = bool(result.interruptions) or (
            output is not None and output.status == "WAITING_APPROVAL"
        )
        return OrchestrationResult(
            output=output,
            waiting_for_approval=waiting,
            usage_requests=usage.requests,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            resume_binding=binding,
            sdk_state=result.to_state() if result.interruptions else None,
        )

    async def resume(
        self,
        *,
        paused: OrchestrationResult,
        project_id: uuid.UUID,
        actor_id: uuid.UUID,
        snapshot_hash: str,
        correlation_id: str,
        approval_valid: bool,
        timeout_seconds: float,
    ) -> OrchestrationResult:
        validate_resume_binding(
            paused.resume_binding,
            project_id=project_id,
            actor_id=actor_id,
            snapshot_hash=snapshot_hash,
        )
        if not approval_valid or paused.sdk_state is None:
            raise OrchestrationError(
                "APPROVAL_INVALID", "The external ApprovalRecord is not valid."
            )
        interruptions = paused.sdk_state.get_interruptions()
        if len(interruptions) != 1:
            raise OrchestrationError(
                "RESUME_STATE_INVALID", "Paused state has an invalid interruption set."
            )
        paused.sdk_state.approve(interruptions[0])
        try:
            result = await asyncio.wait_for(
                Runner.run(
                    self.agent,
                    paused.sdk_state,
                    run_config=build_run_config(correlation_id=correlation_id),
                ),
                timeout=timeout_seconds,
            )
        except Exception as exc:
            raise OrchestrationError(
                "AGENT_RESUME_FAILED", "The paused Agent run could not resume."
            ) from exc
        usage = result.context_wrapper.usage
        return OrchestrationResult(
            output=OrchestratorOutput.model_validate(result.final_output),
            waiting_for_approval=bool(result.interruptions),
            usage_requests=usage.requests,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            resume_binding=paused.resume_binding,
            sdk_state=result.to_state() if result.interruptions else None,
        )
