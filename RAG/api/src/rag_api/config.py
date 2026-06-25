from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    rag_host: str = Field(default="0.0.0.0", alias="RAG_HOST")
    rag_port: int = Field(default=8091, alias="RAG_PORT")

    ia_core_url: str = Field(default="http://localhost:8090", alias="IA_CORE_URL")

    # Retrieval (embedding-service + Qdrant)
    embedding_service_url: str = Field(
        default="http://localhost:8094",
        alias="EMBEDDING_SERVICE_URL",
    )
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="neobotseller", alias="QDRANT_COLLECTION")
    rag_top_k: int = Field(default=5, alias="RAG_TOP_K")
    rag_enabled: bool = Field(default=True, alias="RAG_RETRIEVAL_ENABLED")

    @field_validator("rag_enabled", mode="before")
    @classmethod
    def parse_bool(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("1", "true", "yes", "on")


@lru_cache
def get_settings() -> Settings:
    return Settings()
