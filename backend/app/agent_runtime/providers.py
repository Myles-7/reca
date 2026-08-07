from __future__ import annotations

import json
import re
import uuid
from collections.abc import AsyncIterator
from typing import Any

from agents import (
    Model,
    ModelResponse,
    ModelSettings,
    OpenAIChatCompletionsModel,
    Usage,
)
from openai import AsyncOpenAI
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)

from app.core.config import settings

from .sdk_adapter import OrchestrationError, ProviderMode


def _message(value: dict[str, Any]) -> ResponseOutputMessage:
    return ResponseOutputMessage(
        id=f"msg_{uuid.uuid4().hex}",
        type="message",
        role="assistant",
        status="completed",
        content=[
            ResponseOutputText(
                type="output_text", text=json.dumps(value), annotations=[]
            )
        ],
    )


class DeterministicOrchestratorModel(Model):
    """Offline model fixture used only for explicitly labeled Mock/Recorded runs."""

    def __init__(
        self,
        *,
        stage: str,
        source_ids: list[str],
        workflow_goal: str | None = None,
        resume_summary: dict[str, Any] | None = None,
    ) -> None:
        self.stage = stage
        self.source_ids = source_ids
        self.calls = 0
        self.resume_summary = resume_summary
        self.action = self._action(workflow_goal or "")

    @staticmethod
    def _action(goal: str) -> tuple[str, str] | None:
        patterns = (
            ("profile_dataset", r"profile dataset\s+([0-9a-f-]{36})"),
            (
                "apply_approved_transformations",
                r"apply approved cleaning plan\s+([0-9a-f-]{36})",
            ),
        )
        lowered = goal.casefold()
        for name, pattern in patterns:
            matched = re.search(pattern, lowered)
            if matched is not None:
                return name, str(uuid.UUID(matched.group(1)))
        return None

    async def get_response(
        self,
        system_instructions: str | None,
        input: str | list[Any],
        model_settings: ModelSettings,
        tools: list[Any],
        output_schema: Any,
        handoffs: list[Any],
        tracing: Any,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt: Any,
    ) -> ModelResponse:
        del (
            system_instructions,
            input,
            model_settings,
            tools,
            output_schema,
            handoffs,
            tracing,
            previous_response_id,
            conversation_id,
            prompt,
        )
        self.calls += 1
        output: list[Any]
        if self.resume_summary is not None:
            output = [_message(self.resume_summary)]
        elif self.calls == 1:
            output = [
                ResponseFunctionToolCall(
                    type="function_call",
                    name="get_project_state",
                    arguments="{}",
                    call_id="reca-project-state-1",
                )
            ]
        elif self.calls == 2 and self.action is not None:
            name, object_id = self.action
            arguments = (
                {"dataset_version_id": object_id, "rule_set": "RECA_P0_DEFAULT"}
                if name == "profile_dataset"
                else {"cleaning_plan_id": object_id}
            )
            output = [
                ResponseFunctionToolCall(
                    type="function_call",
                    name=name,
                    arguments=json.dumps(arguments),
                    call_id=f"reca-{name}-1",
                )
            ]
        else:
            waiting = (
                self.action is not None
                and self.action[0] == "apply_approved_transformations"
            )
            output = [
                _message(
                    {
                        "status": "WAITING_APPROVAL" if waiting else "COMPLETED",
                        "stage": self.stage,
                        "summary": (
                            "The CleaningPlan is waiting for an external formal Approval decision."
                            if waiting
                            else "The authorized project state and deterministic Tool result were reviewed."
                        ),
                        "source_ids": self.source_ids,
                        "limitations": [
                            "Deterministic offline orchestration; no live provider was used."
                        ],
                    }
                )
            ]
        return ModelResponse(
            output=output,
            usage=Usage(requests=1, input_tokens=10, output_tokens=5, total_tokens=15),
            response_id=f"reca-recorded-{self.calls}",
        )

    def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        del args, kwargs
        raise NotImplementedError


def build_model(
    *,
    mode: ProviderMode,
    stage: str,
    source_ids: list[str],
    workflow_goal: str | None = None,
    resume_summary: dict[str, Any] | None = None,
) -> tuple[Model, str, str]:
    if mode in {ProviderMode.MOCK, ProviderMode.RECORDED}:
        return (
            DeterministicOrchestratorModel(
                stage=stage,
                source_ids=source_ids,
                workflow_goal=workflow_goal,
                resume_summary=resume_summary,
            ),
            mode.value.lower(),
            "reca-deterministic-orchestrator-1.0",
        )
    if settings.model_status != "CONFIGURED":
        raise OrchestrationError(
            "MODEL_PROVIDER_UNAVAILABLE",
            "Live provider credentials are not configured.",
        )
    assert settings.MODEL_API_KEY is not None
    assert settings.MODEL_BASE_URL is not None
    assert settings.MODEL_NAME is not None
    client = AsyncOpenAI(
        api_key=settings.MODEL_API_KEY.get_secret_value(),
        base_url=str(settings.MODEL_BASE_URL),
    )
    return (
        OpenAIChatCompletionsModel(model=settings.MODEL_NAME, openai_client=client),
        "openai-compatible",
        settings.MODEL_NAME,
    )
