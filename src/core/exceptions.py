"""
Custom domain exceptions for the RAG pipeline.

All exceptions inherit from RAGPipelineException so callers can catch
the base class to handle any pipeline-specific failure.
"""
from typing import Any, Dict, Optional


class RAGPipelineException(Exception):
    """Root exception for all RAG pipeline errors."""

    status_code: int = 500
    error_code: str = "RAG_PIPELINE_ERROR"

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# ----- Document loading -----
class DocumentLoadException(RAGPipelineException):
    status_code = 422
    error_code = "DOCUMENT_LOAD_ERROR"


class UnsupportedFileTypeException(DocumentLoadException):
    status_code = 415
    error_code = "UNSUPPORTED_FILE_TYPE"


class InvalidURLException(DocumentLoadException):
    status_code = 400
    error_code = "INVALID_URL"


# ----- Chunking / splitting -----
class ChunkingException(RAGPipelineException):
    status_code = 500
    error_code = "CHUNKING_ERROR"


# ----- Embeddings / LLM -----
class EmbeddingException(RAGPipelineException):
    status_code = 502
    error_code = "EMBEDDING_ERROR"


class LLMException(RAGPipelineException):
    status_code = 502
    error_code = "LLM_ERROR"


class BedrockClientException(RAGPipelineException):
    status_code = 502
    error_code = "BEDROCK_CLIENT_ERROR"


# ----- Vector store -----
class VectorStoreException(RAGPipelineException):
    status_code = 500
    error_code = "VECTOR_STORE_ERROR"


class CollectionNotFoundException(VectorStoreException):
    status_code = 404
    error_code = "COLLECTION_NOT_FOUND"


# ----- Retrieval / Chain -----
class RetrievalException(RAGPipelineException):
    status_code = 500
    error_code = "RETRIEVAL_ERROR"


class ChainExecutionException(RAGPipelineException):
    status_code = 500
    error_code = "CHAIN_EXECUTION_ERROR"


# ----- Validation -----
class ValidationException(RAGPipelineException):
    status_code = 400
    error_code = "VALIDATION_ERROR"


class FileSizeExceededException(ValidationException):
    error_code = "FILE_SIZE_EXCEEDED"


# ----- Configuration -----
class ConfigurationException(RAGPipelineException):
    status_code = 500
    error_code = "CONFIGURATION_ERROR"
