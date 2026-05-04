"""CSV, HTML, PowerPoint and Excel document loaders."""
from pathlib import Path
from typing import List

from langchain_community.document_loaders import (
    BSHTMLLoader,
    CSVLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
)
from langchain_core.documents import Document

from src.core.constants import FileType
from src.core.exceptions import DocumentLoadException
from src.loaders.base_loader import BaseDocumentLoader


def _ensure_exists(path: Path, source: str) -> None:
    if not path.exists():
        raise DocumentLoadException(
            f"File not found: {source}", details={"source": source}
        )


class CSVDocumentLoader(BaseDocumentLoader):
    """Load CSV files - one Document per row."""

    file_type = FileType.CSV.value

    def _load(self) -> List[Document]:
        path = Path(self.source)
        _ensure_exists(path, self.source)
        try:
            loader = CSVLoader(file_path=str(path), encoding="utf-8")
            return loader.load()
        except Exception as exc:
            raise DocumentLoadException(
                f"Failed to load CSV: {self.source}", cause=exc
            ) from exc


class HTMLLoader(BaseDocumentLoader):
    """Load local HTML files using BeautifulSoup."""

    file_type = FileType.HTML.value

    def _load(self) -> List[Document]:
        path = Path(self.source)
        _ensure_exists(path, self.source)
        try:
            loader = BSHTMLLoader(file_path=str(path), open_encoding="utf-8")
            return loader.load()
        except Exception as exc:
            raise DocumentLoadException(
                f"Failed to load HTML: {self.source}", cause=exc
            ) from exc


class PPTXLoader(BaseDocumentLoader):
    """Load PowerPoint .pptx files via Unstructured."""

    file_type = FileType.PPTX.value

    def _load(self) -> List[Document]:
        path = Path(self.source)
        _ensure_exists(path, self.source)
        try:
            loader = UnstructuredPowerPointLoader(str(path))
            return loader.load()
        except Exception as exc:
            raise DocumentLoadException(
                f"Failed to load PPTX: {self.source}", cause=exc
            ) from exc


class XLSXLoader(BaseDocumentLoader):
    """Load Excel .xlsx files via Unstructured."""

    file_type = FileType.XLSX.value

    def _load(self) -> List[Document]:
        path = Path(self.source)
        _ensure_exists(path, self.source)
        try:
            loader = UnstructuredExcelLoader(str(path), mode="elements")
            return loader.load()
        except Exception as exc:
            raise DocumentLoadException(
                f"Failed to load XLSX: {self.source}", cause=exc
            ) from exc
