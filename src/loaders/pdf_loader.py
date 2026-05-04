"""PDF document loader using pypdf via LangChain's PyPDFLoader."""
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from src.core.constants import FileType
from src.core.exceptions import DocumentLoadException
from src.loaders.base_loader import BaseDocumentLoader
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PDFLoader(BaseDocumentLoader):
    """Load a PDF file and produce one Document per page."""

    file_type = FileType.PDF.value

    def _load(self) -> List[Document]:
        path = Path(self.source)
        if not path.exists():
            raise DocumentLoadException(
                f"PDF file not found: {self.source}",
                details={"source": self.source},
            )
        try:
            loader = PyPDFLoader(str(path))
            documents = loader.load()
        except Exception as exc:
            raise DocumentLoadException(
                f"Failed to load PDF: {self.source}",
                details={"source": self.source},
                cause=exc,
            ) from exc

        # Filter out blank pages
        documents = [d for d in documents if d.page_content and d.page_content.strip()]
        logger.debug("PDF loaded", source=self.source, pages=len(documents))
        return documents
