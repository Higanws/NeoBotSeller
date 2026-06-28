from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    actions_host: str = Field(default="0.0.0.0", alias="ACTIONS_HOST")
    actions_port: int = Field(default=8092, alias="ACTIONS_PORT")

    # Backend Odoo (connectors)
    odoo_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("ODOO_ENABLED", "ODOO_MCP_ENABLED"),
    )
    odoo_url: str = Field(default="http://localhost:8069", alias="ODOO_URL")
    odoo_db: str = Field(default="neobotseller", alias="ODOO_DB_NAME")
    odoo_login: str = Field(default="admin", alias="ODOO_LOGIN")
    odoo_password: str = Field(default="admin", alias="ODOO_USER_PASSWORD")

    rag_enabled: bool = Field(default=True, alias="RAG_ACTIONS_ENABLED")
    rag_api_url: str = Field(default="http://localhost:8091", alias="RAG_API_URL")

    @field_validator("odoo_enabled", "rag_enabled", mode="before")
    @classmethod
    def parse_bool(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("1", "true", "yes", "on")


@lru_cache
def get_settings() -> Settings:
    return Settings()
