from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Servicio
    ia_core_host: str = Field(default="0.0.0.0", alias="IA_CORE_HOST")
    ia_core_port: int = Field(default=8090, alias="IA_CORE_PORT")

    # LLM
    llm_provider: Literal["openai", "ollama"] = Field(
        default="ollama", alias="LLM_PROVIDER"
    )
    llm_model: str = Field(default="llama3.2", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=1024, alias="LLM_MAX_TOKENS")

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", alias="OPENAI_BASE_URL"
    )

    # Ollama
    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )

    # Prompt
    system_prompt: str = Field(
        default=(
            "Eres NeoBotSeller, un asistente de ventas amable y conciso. "
            "Respondes en el idioma del usuario. Ayudas con productos, stock y CRM."
        ),
        alias="SYSTEM_PROMPT",
    )

    # Conversation service (Redis/) — contexto multi-chat vía HTTP
    conversation_service_url: str = Field(
        default="http://localhost:8093",
        alias="CONVERSATION_SERVICE_URL",
    )
    conversation_service_enabled: bool = Field(
        default=True,
        alias="CONVERSATION_SERVICE_ENABLED",
    )
    conversation_max_turns: int = Field(
        default=20,
        alias="CONVERSATION_MAX_TURNS",
        description="Solo aplica al fallback en memoria local",
    )
    conversation_ttl_seconds: int = Field(
        default=300,
        alias="CONVERSATION_TTL_SECONDS",
        description="Solo aplica al fallback en memoria local",
    )
    max_tool_rounds: int = Field(default=3, alias="MAX_TOOL_ROUNDS")

    # Odoo MCP
    odoo_mcp_enabled: bool = Field(default=True, alias="ODOO_MCP_ENABLED")
    odoo_url: str = Field(default="http://localhost:8069", alias="ODOO_URL")
    odoo_db: str = Field(default="neobotseller", alias="ODOO_DB_NAME")
    odoo_login: str = Field(default="admin", alias="ODOO_LOGIN")
    odoo_password: str = Field(
        default="admin", alias="ODOO_USER_PASSWORD"
    )

    # Actions service (hub MCP unificado — preferido)
    actions_service_url: str = Field(
        default="http://localhost:8092", alias="ACTIONS_SERVICE_URL"
    )

    @field_validator("llm_provider", mode="before")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        return str(value).strip().lower()

    @field_validator("odoo_mcp_enabled", "conversation_service_enabled", mode="before")
    @classmethod
    def parse_bool(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("1", "true", "yes", "on")

    @field_validator("openai_api_key", "llm_model", "system_prompt", mode="before")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        return str(value).strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
