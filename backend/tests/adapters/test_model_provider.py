from __future__ import annotations

import json

import httpx
import pytest
from pydantic import AnyHttpUrl, BaseModel, SecretStr

from app.adapters.model_provider import (
    ModelProviderError,
    OpenAICompatibleJsonProvider,
)
from app.agents.service import ModelExecutionMode
from app.evidence import analysis, extraction
from app.evidence.analysis import AnalysisProviderIdentity
from app.evidence.extraction import ExtractionProviderIdentity

pytestmark = pytest.mark.no_database


class Payload(BaseModel):
    value: str


def _provider(transport: httpx.MockTransport) -> OpenAICompatibleJsonProvider:
    return OpenAICompatibleJsonProvider(
        base_url="https://model.example/v1",
        api_key="test-provider-secret",
        model_name="test-model",
        timeout_seconds=5,
        client=httpx.Client(transport=transport),
    )


def test_openai_compatible_provider_sends_governed_prompt_and_parses_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://model.example/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-provider-secret"
        body = json.loads(request.content)
        assert body["model"] == "test-model"
        assert body["temperature"] == 0
        assert body["response_format"] == {"type": "json_object"}
        assert json.loads(body["messages"][1]["content"]) == {"value": "bounded"}
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"status":"ok"}'}}]},
        )

    result = _provider(httpx.MockTransport(handler)).generate(
        prompt_id="governance-contract-test",
        prompt_version="1.0.0",
        payload=Payload(value="bounded"),
    )
    assert result == {"status": "ok"}


@pytest.mark.parametrize(
    ("response", "code", "retryable"),
    [
        (httpx.Response(503), "MODEL_PROVIDER_UNAVAILABLE", True),
        (httpx.Response(401), "MODEL_PROVIDER_REJECTED", False),
        (
            httpx.Response(200, json={"choices": []}),
            "MODEL_PROVIDER_RESPONSE_INVALID",
            False,
        ),
    ],
)
def test_model_provider_failures_are_explicit(
    response: httpx.Response, code: str, retryable: bool
) -> None:
    provider = _provider(httpx.MockTransport(lambda _request: response))
    with pytest.raises(ModelProviderError) as captured:
        provider.generate(
            prompt_id="governance-contract-test",
            prompt_version="1.0.0",
            payload=Payload(value="bounded"),
        )
    assert captured.value.code == code
    assert captured.value.retryable is retryable


def test_extraction_and_analysis_factories_bind_live_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured = type(
        "ConfiguredSettings",
        (),
        {
            "model_status": "CONFIGURED",
            "MODEL_BASE_URL": AnyHttpUrl("https://model.example/v1"),
            "MODEL_API_KEY": SecretStr("provider-secret"),
            "MODEL_NAME": "reca-structured-model",
            "REQUEST_TIMEOUT_SECONDS": 30.0,
        },
    )()
    monkeypatch.setattr(extraction, "settings", configured)
    monkeypatch.setattr(analysis, "settings", configured)
    extraction_identity = ExtractionProviderIdentity(
        provider_id="openai-compatible",
        provider_name="openai-compatible",
        model_name="reca-structured-model",
        mode=ModelExecutionMode.LIVE,
    )
    analysis_identity = AnalysisProviderIdentity(
        provider_id="openai-compatible",
        provider_name="openai-compatible",
        model_name="reca-structured-model",
        mode=ModelExecutionMode.LIVE,
    )

    extraction_provider = extraction.configured_extraction_provider(extraction_identity)
    analysis_provider = analysis.configured_analysis_provider(analysis_identity)
    assert extraction_provider.identity == extraction_identity
    assert analysis_provider.identity == analysis_identity
