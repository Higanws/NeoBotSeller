from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_SERVICE_ROOT = Path(__file__).resolve().parents[2]
_RAG_ROOT = _SERVICE_ROOT.parent
_ENV_FILE = _SERVICE_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    embedding_host: str = Field(default="0.0.0.0", alias="EMBEDDING_SERVICE_HOST")
    embedding_port: int = Field(default=8094, alias="EMBEDDING_SERVICE_PORT")

    documents_dir: Path = Field(
        default=_RAG_ROOT / "documents",
        alias="DOCUMENTS_DIR",
    )
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="neobotseller", alias="QDRANT_COLLECTION")

    embedding_provider: Literal["local", "openai"] = Field(
        default="local",
        alias="EMBEDDING_PROVIDER",
    )
    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5",
        alias="EMBEDDING_MODEL",
    )
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="OPENAI_EMBEDDING_MODEL",
    )

    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, alias="CHUNK_OVERLAP")

    embedding_watch: bool = Field(default=False, alias="EMBEDDING_WATCH")
    embedding_watch_interval_seconds: int = Field(
        default=30,
        alias="EMBEDDING_WATCH_INTERVAL_SECONDS",
    )

    @field_validator("documents_dir", mode="before")
    @classmethod
    def resolve_documents_dir(cls, value: Any) -> Path:
        path = Path(str(value))
        if not path.is_absolute():
            path = (_SERVICE_ROOT / path).resolve()
        return path

    @field_validator("embedding_provider", mode="before")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        return str(value).strip().lower()

    @field_validator("embedding_watch", mode="before")
    @classmethod
    def parse_bool(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("1", "true", "yes", "on")


@lru_cache
def get_settings() -> Settings:
    return Settings()
