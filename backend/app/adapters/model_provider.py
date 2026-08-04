from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import BaseModel

from app.agents.prompts import (
    DEFAULT_MANIFEST_PATH,
    get_prompt_contract,
    prompt_asset_path,
)


class ModelProviderError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass
class OpenAICompatibleJsonProvider:
    base_url: str
    api_key: str
    model_name: str
    timeout_seconds: float
    client: httpx.Client | None = None

    def generate(
        self, *, prompt_id: str, prompt_version: str, payload: BaseModel
    ) -> dict[str, Any]:
        contract = get_prompt_contract(prompt_id, prompt_version)
        prompt = prompt_asset_path(contract, DEFAULT_MANIFEST_PATH).read_text(
            encoding="utf-8"
        )
        request = {
            "model": self.model_name,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        payload.model_dump(mode="json"),
                        ensure_ascii=True,
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                },
            ],
        }
        owned_client = self.client is None
        client = self.client or httpx.Client(timeout=self.timeout_seconds)
        try:
            response = client.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=request,
            )
            if response.status_code in {408, 429} or response.status_code >= 500:
                raise ModelProviderError(
                    "MODEL_PROVIDER_UNAVAILABLE",
                    "The configured model provider is temporarily unavailable.",
                    retryable=True,
                )
            if response.status_code >= 400:
                raise ModelProviderError(
                    "MODEL_PROVIDER_REJECTED",
                    "The configured model provider rejected the request.",
                    retryable=False,
                )
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise TypeError("model response must be an object")
            return parsed
        except ModelProviderError:
            raise
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise ModelProviderError(
                "MODEL_PROVIDER_UNAVAILABLE",
                "The configured model provider could not be reached.",
                retryable=True,
            ) from exc
        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise ModelProviderError(
                "MODEL_PROVIDER_RESPONSE_INVALID",
                "The configured model provider returned an invalid JSON response.",
                retryable=False,
            ) from exc
        finally:
            if owned_client:
                client.close()
