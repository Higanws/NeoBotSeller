from __future__ import annotations

from typing import Any

import httpx

from ia_core.config import Settings
from ia_core.llm.base import LLMResponse, ToolCall


class OllamaProvider:
    provider_name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model = settings.llm_model
        self._base = settings.ollama_base_url.rstrip("/")

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.settings.llm_temperature,
                "num_predict": self.settings.llm_max_tokens,
            },
        }
        if tools:
            payload["tools"] = tools

        with httpx.Client(timeout=180.0) as client:
            response = client.post(f"{self._base}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        message = data.get("message", {})
        content = (message.get("content") or "").strip()
        tool_calls = [
            ToolCall(
                id=tc.get("id") or f"call_{i}",
                name=tc["function"]["name"],
                arguments=tc["function"]["arguments"],
            )
            for i, tc in enumerate(message.get("tool_calls", []))
        ]

        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=self.model,
            usage={
                "prompt_eval_count": data.get("prompt_eval_count"),
                "eval_count": data.get("eval_count"),
            },
            tool_calls=tool_calls,
        )
