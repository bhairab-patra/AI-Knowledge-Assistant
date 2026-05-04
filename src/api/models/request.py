"""Pydantic models for API request bodies."""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class IngestURLRequest(BaseModel):
    """Body for ingesting one or more URLs."""
    urls: List[str] = Field(..., min_length=1, description="URLs to ingest")

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v):
        for url in v:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid URL: {url} (must start with http:// or https://)")
        return v


class IngestDirectoryRequest(BaseModel):
    """Body for ingesting a server-side directory."""
    directory: str = Field(..., description="Absolute path to directory")
    recursive: bool = Field(default=True, description="Recurse into subdirectories")


class QueryRequest(BaseModel):
    """One-shot question request."""
    question: str = Field(..., min_length=1, max_length=4000)
    k: Optional[int] = Field(default=None, ge=1, le=50)
    search_type: Optional[Literal["similarity", "mmr", "similarity_score_threshold"]] = None
    filter: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filter")


class ChatTurn(BaseModel):
    role: Literal["user", "assistant", "ai"]
    content: str = Field(..., min_length=1)


class ConversationalQueryRequest(BaseModel):
    """Multi-turn conversation request."""
    question: str = Field(..., min_length=1, max_length=4000)
    chat_history: Optional[List[ChatTurn]] = Field(default_factory=list)
    k: Optional[int] = Field(default=None, ge=1, le=50)
    search_type: Optional[Literal["similarity", "mmr", "similarity_score_threshold"]] = None
    filter: Optional[Dict[str, Any]] = None


class DeleteByDocumentRequest(BaseModel):
    document_id: str = Field(..., min_length=1)


class DeleteBySourceRequest(BaseModel):
    source: str = Field(..., min_length=1)
