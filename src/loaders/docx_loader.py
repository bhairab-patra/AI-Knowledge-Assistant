"""Word document loader (.docx and .doc)."""
from pathlib import Path
from typing import List

from langchain_community.document_loaders import Docx2txtLoader, UnstructuredWordDocumentLoader
from langchain_core.documents import Document

from src.core.constants import FileType
from src.core.exceptions import DocumentLoadException
from src.loaders.base_loader import BaseDocumentLoader


class DocxLoader(BaseDocumentLoader):
    """Load .docx files using docx2txt (fast, plain text extraction)."""

    file_type = FileType.DOCX.value

    def _load(self) -> List[Document]:
        path = Path(self.source)
        if not path.exists():
            raise DocumentLoadException(
                f"DOCX file not found: {self.source}",
                details={"source": self.source},
            )
        try:
            loader = Docx2txtLoader(str(path))
            return loader.load()
        except Exception as exc:
            raise DocumentLoadException(
                f"Failed to load DOCX: {self.source}",
                cause=exc,
            ) from exc


class DocLoader(BaseDocumentLoader):
    """Load legacy .doc files via Unstructured (requires libreoffice/antiword)."""

    file_type = FileType.DOC.value

    def _load(self) -> List[Document]:
        path = Path(self.source)
        if not path.exists():
            raise DocumentLoadException(
                f".doc file not found: {self.source}",
                details={"source": self.source},
            )
        try:
            loader = UnstructuredWordDocumentLoader(str(path))
            return loader.load()
        except Exception as exc:
            raise DocumentLoadException(
                f"Failed to load .doc: {self.source}. "
                f"Note: legacy .doc requires libreoffice or antiword installed.",
                cause=exc,
            ) from exc
