"""
Ingestion service - the orchestrator that ties loaders, splitter, and vector
store together. Public methods accept either local files, URLs, or directories.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document

from config.settings import settings
from src.core.constants import (
    META_DOCUMENT_ID,
    META_FILE_NAME,
    META_SOURCE,
)
from src.core.exceptions import (
    DocumentLoadException,
    RAGPipelineException,
    UnsupportedFileTypeException,
)
from src.loaders.document_loader_factory import DocumentLoaderFactory
from src.splitters.text_splitter import DocumentTextSplitter
from src.utils.helpers import get_file_size_bytes, is_url
from src.utils.logger import get_logger
from src.utils.validators import validate_file_extension, validate_file_size, validate_url
from src.vectorstore.chroma_store import get_vector_store

logger = get_logger(__name__)


class IngestionService:
    """Coordinates loading, splitting, and vector-store insertion."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> None:
        self.splitter = DocumentTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        self.store = get_vector_store()

    # -----------------------------
    # Single-source ingestion
    # -----------------------------
    def ingest_source(self, source: str, **loader_kwargs) -> Dict[str, Any]:
        """
        Ingest a single source (file path or URL).

        Returns a summary dict with document_id, num_chunks, and source.
        """
        logger.info("Ingestion started", source=source)

        # Pre-flight validation
        if is_url(source):
            validate_url(source)
        else:
            path = Path(source)
            if not path.exists() or not path.is_file():
                raise DocumentLoadException(
                    f"File does not exist: {source}", details={"source": source}
                )
            validate_file_extension(source, settings.ALLOWED_FILE_EXTENSIONS)
            validate_file_size(
                get_file_size_bytes(path), settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
            )

        loader = DocumentLoaderFactory.get_loader(source, **loader_kwargs)
        documents: List[Document] = loader.load()
        if not documents:
            raise DocumentLoadException(
                f"No content extracted from source: {source}",
                details={"source": source},
            )

        chunks = self.splitter.split_documents(documents)
        if not chunks:
            raise DocumentLoadException(
                f"Document produced no chunks: {source}",
                details={"source": source},
            )

        ids = self.store.add_documents(chunks)
        result = {
            "document_id": loader.document_id,
            "source": source,
            "num_documents": len(documents),
            "num_chunks": len(chunks),
            "vector_ids": ids,
        }
        logger.info("Ingestion completed", **{k: v for k, v in result.items() if k != "vector_ids"})
        return result

    # -----------------------------
    # Batch ingestion
    # -----------------------------
    def ingest_sources(self, sources: List[str], **loader_kwargs) -> Dict[str, Any]:
        """Ingest a list of sources, capturing per-source success/failure."""
        successes: List[Dict[str, Any]] = []
        failures: List[Dict[str, Any]] = []
        for source in sources:
            try:
                successes.append(self.ingest_source(source, **loader_kwargs))
            except RAGPipelineException as exc:
                failures.append({"source": source, "error": exc.to_dict()})
                logger.error("Ingest failed", source=source, error=exc.message)
            except Exception as exc:  # pragma: no cover - safety net
                failures.append({"source": source, "error": {"message": str(exc)}})
                logger.exception("Unexpected ingest failure", source=source)
        return {
            "total": len(sources),
            "successful": len(successes),
            "failed": len(failures),
            "successes": successes,
            "failures": failures,
        }

    # -----------------------------
    # Directory ingestion
    # -----------------------------
    def ingest_directory(
        self, directory: str, recursive: bool = True
    ) -> Dict[str, Any]:
        """Ingest every supported file in a directory."""
        path = Path(directory)
        if not path.exists() or not path.is_dir():
            raise DocumentLoadException(
                f"Directory not found: {directory}", details={"directory": directory}
            )

        supported = set(DocumentLoaderFactory.supported_extensions())
        iterator = path.rglob("*") if recursive else path.glob("*")
        files = [str(f) for f in iterator if f.is_file() and f.suffix.lower() in supported]

        logger.info("Ingesting directory", directory=directory, count=len(files))
        if not files:
            return {"total": 0, "successful": 0, "failed": 0, "successes": [], "failures": []}
        return self.ingest_sources(files)

    # -----------------------------
    # Document management
    # -----------------------------
    def delete_by_document_id(self, document_id: str) -> None:
        """Delete all chunks belonging to a previously ingested document."""
        self.store.delete_by_metadata({META_DOCUMENT_ID: document_id})

    def delete_by_source(self, source: str) -> None:
        """Delete all chunks belonging to a given source path/URL."""
        self.store.delete_by_metadata({META_SOURCE: source})

    def stats(self) -> Dict[str, Any]:
        """Return basic stats about the vector store."""
        return {
            "collection": self.store.collection_name,
            "persist_directory": self.store.persist_directory,
            "vector_count": self.store.count(),
        }
