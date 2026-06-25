from __future__ import annotations

import json
from typing import Any

import httpx

from ia_core.config import Settings
from ia_core.llm.base import LLMResponse, ToolCall


class OpenAIProvider:
    provider_name = "openai"

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY es obligatorio cuando LLM_PROVIDER=openai")
        self.settings = settings
        self.model = settings.llm_model
        self._base = settings.openai_base_url.rstrip("/")
        self._api_key = settings.openai_api_key

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.settings.llm_temperature,
            "max_tokens": self.settings.llm_max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self._base}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        message = data["choices"][0]["message"]
        content = (message.get("content") or "").strip()
        tool_calls = [
            ToolCall(
                id=tc["id"],
                name=tc["function"]["name"],
                arguments=tc["function"]["arguments"],
            )
            for tc in message.get("tool_calls", [])
        ]

        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=self.model,
            usage=data.get("usage"),
            tool_calls=tool_calls,
        )
