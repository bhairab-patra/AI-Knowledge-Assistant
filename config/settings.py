"""
Application settings using Pydantic for type-safe configuration management.

Loads configuration from environment variables and .env files.
This module provides a single source of truth for all configuration.
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # -----------------------------
    # Application metadata
    # -----------------------------
    APP_NAME: str = "RAG Pipeline"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # -----------------------------
    # API server
    # -----------------------------
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]
    MAX_UPLOAD_SIZE_MB: int = 100

    # -----------------------------
    # AWS / Bedrock
    # -----------------------------
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SESSION_TOKEN: Optional[str] = None
    AWS_PROFILE: Optional[str] = None

    BEDROCK_LLM_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    BEDROCK_EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v2:0"

    LLM_TEMPERATURE: float = Field(default=0.0, ge=0.0, le=1.0)
    LLM_MAX_TOKENS: int = Field(default=4096, ge=1, le=200000)
    LLM_TOP_P: float = Field(default=0.9, ge=0.0, le=1.0)
    LLM_TOP_K: int = Field(default=250, ge=0)
    # Newer Claude models (Haiku 4.5, Sonnet 4) reject `temperature` AND
    # `top_p` set simultaneously. When False (default), only `temperature`
    # is sent. Set True to use nucleus sampling (`top_p`) instead.
    LLM_USE_TOP_P: bool = False

    # -----------------------------
    # ChromaDB
    # -----------------------------
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "rag_documents"
    CHROMA_DISTANCE_METRIC: Literal["cosine", "l2", "ip"] = "cosine"

    # -----------------------------
    # Document processing
    # -----------------------------
    CHUNK_SIZE: int = Field(default=1000, ge=100, le=8000)
    CHUNK_OVERLAP: int = Field(default=200, ge=0)
    MAX_CHUNKS_PER_DOC: int = Field(default=1000, ge=1)

    # -----------------------------
    # Retrieval
    # -----------------------------
    RETRIEVER_K: int = Field(default=5, ge=1, le=50)
    RETRIEVER_SEARCH_TYPE: Literal["similarity", "mmr", "similarity_score_threshold"] = "mmr"
    RETRIEVER_FETCH_K: int = Field(default=20, ge=1)
    RETRIEVER_LAMBDA_MULT: float = Field(default=0.5, ge=0.0, le=1.0)
    RETRIEVER_SCORE_THRESHOLD: float = Field(default=0.5, ge=0.0, le=1.0)

    # -----------------------------
    # File handling
    # -----------------------------
    ALLOWED_FILE_EXTENSIONS: List[str] = [
        ".pdf", ".txt", ".docx", ".doc", ".md",
        ".csv", ".html", ".pptx", ".xlsx",
    ]
    DATA_RAW_DIR: str = "./data/raw"
    DATA_PROCESSED_DIR: str = "./data/processed"

    # -----------------------------
    # Cache (optional)
    # -----------------------------
    ENABLE_CACHE: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    CACHE_TTL_SECONDS: int = 3600

    # -----------------------------
    # Validators
    # -----------------------------
    @field_validator("CHUNK_OVERLAP")
    @classmethod
    def overlap_must_be_smaller_than_chunk(cls, v, info):
        chunk_size = info.data.get("CHUNK_SIZE", 1000)
        if v >= chunk_size:
            raise ValueError(
                f"CHUNK_OVERLAP ({v}) must be less than CHUNK_SIZE ({chunk_size})"
            )
        return v

    # -----------------------------
    # Convenience properties
    # -----------------------------
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def chroma_persist_path(self) -> Path:
        return Path(self.CHROMA_PERSIST_DIRECTORY).resolve()

    @property
    def data_raw_path(self) -> Path:
        return Path(self.DATA_RAW_DIR).resolve()

    @property
    def data_processed_path(self) -> Path:
        return Path(self.DATA_PROCESSED_DIR).resolve()

    def ensure_dirs(self) -> None:
        """Ensure all data directories exist on disk."""
        for p in (self.chroma_persist_path, self.data_raw_path, self.data_processed_path):
            p.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    settings = Settings()
    settings.ensure_dirs()
    return settings


# Module-level convenience instance
settings = get_settings()
