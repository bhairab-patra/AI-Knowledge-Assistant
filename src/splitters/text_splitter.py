"""
Text splitter wrapper around LangChain's RecursiveCharacterTextSplitter.

Splits documents into overlapping chunks suitable for embedding and retrieval.
Adds chunk_index / total_chunks metadata to each chunk for traceability.
"""
from typing import List, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import settings
from src.core.constants import META_CHUNK_INDEX, META_TOTAL_CHUNKS
from src.core.exceptions import ChunkingException
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentTextSplitter:
    """Recursive splitter with metadata enrichment."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None,
    ) -> None:
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.separators = separators or [
            "\n\n",  # paragraph break
            "\n",    # line break
            ". ",    # sentence break
            "? ",
            "! ",
            "; ",
            ", ",
            " ",
            "",
        ]
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
            add_start_index=True,
            keep_separator=True,
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split a list of documents into chunks.

        Each output chunk inherits the source document's metadata and adds
        `chunk_index` and `total_chunks` for traceability.
        """
        if not documents:
            logger.warning("No documents provided to splitter")
            return []

        try:
            chunks = self._splitter.split_documents(documents)
        except Exception as exc:
            raise ChunkingException(
                f"Failed to split documents: {exc}", cause=exc
            ) from exc

        # Enrich chunks with index metadata
        total = len(chunks)
        for idx, chunk in enumerate(chunks):
            chunk.metadata[META_CHUNK_INDEX] = idx
            chunk.metadata[META_TOTAL_CHUNKS] = total

        # Drop empty chunks
        chunks = [c for c in chunks if c.page_content.strip()]
        logger.info(
            "Split documents into chunks",
            input_docs=len(documents),
            output_chunks=len(chunks),
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        return chunks

    def split_text(self, text: str) -> List[str]:
        """Split a raw string into chunks - useful for ad-hoc usage."""
        return self._splitter.split_text(text)
