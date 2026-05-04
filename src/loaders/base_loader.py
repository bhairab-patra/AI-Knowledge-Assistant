"""Abstract base loader defining the contract for all document loaders."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.documents import Document

from src.core.constants import (
    META_DOCUMENT_ID,
    META_FILE_NAME,
    META_FILE_TYPE,
    META_INGESTED_AT,
    META_SOURCE,
)
from src.utils.helpers import generate_document_id, utc_now_iso
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseDocumentLoader(ABC):
    """
    Abstract loader for any document source.

    Concrete loaders must implement `_load()` and return a list of LangChain
    Document objects. The `load()` method handles common metadata enrichment
    so all downstream pipeline stages see a uniform shape.
    """

    file_type: str = "unknown"

    def __init__(self, source: str, **kwargs: Any) -> None:
        self.source = source
        self.kwargs = kwargs
        self.document_id = generate_document_id()

    # ----- Public API -----
    def load(self) -> List[Document]:
        """Load documents and enrich each with standard metadata."""
        logger.info(
            "Loading documents",
            loader=self.__class__.__name__,
            source=self.source,
            document_id=self.document_id,
        )
        try:
            docs = self._load()
        except Exception as exc:  # pragma: no cover - re-raised by caller
            logger.error(
                "Loader failed",
                loader=self.__class__.__name__,
                source=self.source,
                error=str(exc),
            )
            raise

        enriched = [self._enrich_metadata(d) for d in docs]
        logger.info(
            "Loaded documents",
            loader=self.__class__.__name__,
            count=len(enriched),
            source=self.source,
        )
        return enriched

    # ----- Subclass hook -----
    @abstractmethod
    def _load(self) -> List[Document]:
        """Concrete loaders implement this to fetch documents from the source."""
        raise NotImplementedError

    # ----- Helpers -----
    def _build_base_metadata(self) -> Dict[str, Any]:
        return {
            META_SOURCE: self.source,
            META_FILE_NAME: Path(self.source).name,
            META_FILE_TYPE: self.file_type,
            META_DOCUMENT_ID: self.document_id,
            META_INGESTED_AT: utc_now_iso(),
        }

    def _enrich_metadata(self, doc: Document) -> Document:
        base = self._build_base_metadata()
        # Loader-specific metadata wins over the base defaults
        merged = {**base, **(doc.metadata or {})}
        doc.metadata = merged
        return doc
