from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    conversation_host: str = Field(default="0.0.0.0", alias="CONVERSATION_SERVICE_HOST")
    conversation_port: int = Field(default=8093, alias="CONVERSATION_SERVICE_PORT")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    conversation_ttl_seconds: int = Field(
        default=300,
        alias="CONVERSATION_TTL_SECONDS",
        description="Segundos sin actividad antes de expirar la sesión",
    )
    conversation_max_turns: int = Field(default=20, alias="CONVERSATION_MAX_TURNS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
