"""Pydantic models for API responses."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str


class IngestResultItem(BaseModel):
    document_id: Optional[str] = None
    source: str
    num_documents: Optional[int] = None
    num_chunks: Optional[int] = None
    error: Optional[Dict[str, Any]] = None


class IngestResponse(BaseModel):
    total: int
    successful: int
    failed: int
    successes: List[IngestResultItem] = []
    failures: List[IngestResultItem] = []


class SourceDocument(BaseModel):
    file_name: str
    page: List[int] = []
    document_id: Optional[str] = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceDocument] = []
    standalone_question: Optional[str] = None
    confidence: Optional[float] = None              # 0.0 - 1.0
    confidence_label: Optional[str] = None  


class StatsResponse(BaseModel):
    collection: str
    persist_directory: str
    vector_count: int


class DeleteResponse(BaseModel):
    status: str
    message: str


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
