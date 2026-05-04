"""
ChromaDB vector store wrapper.

Uses langchain_chroma.Chroma which manages a persistent on-disk index.
Exposes high-level methods to add documents, similarity search, delete by
filter, and full reset (useful in tests).
"""
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document

from config.settings import settings
from src.core.exceptions import VectorStoreException
from src.embeddings.bedrock_embeddings import get_embeddings_service
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChromaVectorStore:
    """High-level ChromaDB persistent vector store."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        distance_metric: Optional[str] = None,
    ) -> None:
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.distance_metric = distance_metric or settings.CHROMA_DISTANCE_METRIC

        # Ensure persist dir exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        embeddings = get_embeddings_service().langchain_embeddings

        try:
            self._store = Chroma(
                collection_name=self.collection_name,
                embedding_function=embeddings,
                persist_directory=self.persist_directory,
                collection_metadata={"hnsw:space": self.distance_metric},
            )
        except Exception as exc:
            raise VectorStoreException(
                f"Failed to initialize Chroma store: {exc}", cause=exc
            ) from exc

        logger.info(
            "Chroma vector store initialized",
            persist_directory=self.persist_directory,
            collection=self.collection_name,
            distance=self.distance_metric,
        )

    # ---------- Mutation ----------
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add chunked documents to the store. Returns list of generated IDs."""
        if not documents:
            logger.warning("add_documents called with empty list")
            return []
        try:
            ids = self._store.add_documents(documents)
            logger.info("Added documents to Chroma", count=len(ids))
            return ids
        except Exception as exc:
            raise VectorStoreException(
                f"Failed to add documents to vector store: {exc}", cause=exc
            ) from exc

    def delete_by_metadata(self, filter_dict: Dict[str, Any]) -> None:
        """Delete all entries matching a metadata filter."""
        try:
            # Chroma expects 'where' filters
            self._store.delete(where=filter_dict)
            logger.info("Deleted documents by filter", filter=filter_dict)
        except Exception as exc:
            raise VectorStoreException(
                f"Failed to delete documents: {exc}", cause=exc
            ) from exc

    def delete_collection(self) -> None:
        """Delete the entire collection - use with caution."""
        try:
            self._store.delete_collection()
            logger.warning("Chroma collection deleted", collection=self.collection_name)
        except Exception as exc:
            raise VectorStoreException(
                f"Failed to delete collection: {exc}", cause=exc
            ) from exc

    # ---------- Search ----------
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Top-k similarity search."""
        try:
            return self._store.similarity_search(query, k=k, filter=filter_dict)
        except Exception as exc:
            raise VectorStoreException(
                f"Similarity search failed: {exc}", cause=exc
            ) from exc

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[tuple[Document, float]]:
        """Top-k similarity search returning (doc, distance) pairs."""
        try:
            return self._store.similarity_search_with_score(
                query, k=k, filter=filter_dict
            )
        except Exception as exc:
            raise VectorStoreException(
                f"Similarity search failed: {exc}", cause=exc
            ) from exc

    # ---------- Stats ----------
    def count(self) -> int:
        """Number of vectors currently stored in the collection."""
        try:
            return self._store._collection.count()
        except Exception as exc:
            raise VectorStoreException(
                f"Failed to count documents: {exc}", cause=exc
            ) from exc

    @property
    def langchain_store(self) -> Chroma:
        """Underlying langchain_chroma.Chroma instance for advanced uses."""
        return self._store


@lru_cache(maxsize=1)
def get_vector_store() -> ChromaVectorStore:
    """Cached singleton vector store accessor."""
    return ChromaVectorStore()
