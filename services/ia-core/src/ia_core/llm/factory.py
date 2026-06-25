from __future__ import annotations

from ia_core.config import Settings
from ia_core.llm.base import LLMProvider
from ia_core.llm.ollama_provider import OllamaProvider
from ia_core.llm.openai_provider import OpenAIProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "openai":
        return OpenAIProvider(settings)
    if settings.llm_provider == "ollama":
        return OllamaProvider(settings)
    raise ValueError(f"Proveedor LLM no soportado: {settings.llm_provider}")
