"""Project-wide constants used across the pipeline."""
from enum import Enum


class FileType(str, Enum):
    """Enumeration of supported file types for ingestion."""
    PDF = "pdf"
    TEXT = "txt"
    MARKDOWN = "md"
    DOCX = "docx"
    DOC = "doc"
    CSV = "csv"
    HTML = "html"
    PPTX = "pptx"
    XLSX = "xlsx"
    URL = "url"


class SearchType(str, Enum):
    """Retriever search strategies supported by the pipeline."""
    SIMILARITY = "similarity"
    MMR = "mmr"
    SIMILARITY_SCORE_THRESHOLD = "similarity_score_threshold"


class DistanceMetric(str, Enum):
    """Distance metrics supported by ChromaDB."""
    COSINE = "cosine"
    L2 = "l2"
    INNER_PRODUCT = "ip"


# Mapping from file extension (lowercase, with leading dot) to FileType.
EXTENSION_TO_FILETYPE = {
    ".pdf": FileType.PDF,
    ".txt": FileType.TEXT,
    ".md": FileType.MARKDOWN,
    ".markdown": FileType.MARKDOWN,
    ".docx": FileType.DOCX,
    ".doc": FileType.DOC,
    ".csv": FileType.CSV,
    ".html": FileType.HTML,
    ".htm": FileType.HTML,
    ".pptx": FileType.PPTX,
    ".xlsx": FileType.XLSX,
}

# Document metadata keys (kept centralized to avoid magic strings)
META_SOURCE = "source"
META_FILE_NAME = "file_name"
META_FILE_TYPE = "file_type"
META_INGESTED_AT = "ingested_at"
META_CHUNK_INDEX = "chunk_index"
META_TOTAL_CHUNKS = "total_chunks"
META_DOCUMENT_ID = "document_id"
META_PAGE = "page"

# Maximum bytes for a single uploaded file (defaults to 100 MB)
DEFAULT_MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024
