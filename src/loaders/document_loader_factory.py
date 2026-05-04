"""
Factory that returns the right loader for a given source.

Centralizes the routing logic so callers don't need to know which loader
implementation to instantiate for a given file type or URL.
"""
from pathlib import Path
from typing import Type

from src.core.constants import EXTENSION_TO_FILETYPE, FileType
from src.core.exceptions import UnsupportedFileTypeException
from src.loaders.base_loader import BaseDocumentLoader
from src.loaders.csv_loader import (
    CSVDocumentLoader,
    HTMLLoader,
    PPTXLoader,
    XLSXLoader,
)
from src.loaders.docx_loader import DocLoader, DocxLoader
from src.loaders.pdf_loader import PDFLoader
from src.loaders.text_loader import MarkdownLoader, PlainTextLoader
from src.loaders.web_loader import WebLoader
from src.utils.helpers import is_url


# Registry mapping FileType -> Loader class
LOADER_REGISTRY: dict[FileType, Type[BaseDocumentLoader]] = {
    FileType.PDF: PDFLoader,
    FileType.TEXT: PlainTextLoader,
    FileType.MARKDOWN: MarkdownLoader,
    FileType.DOCX: DocxLoader,
    FileType.DOC: DocLoader,
    FileType.CSV: CSVDocumentLoader,
    FileType.HTML: HTMLLoader,
    FileType.PPTX: PPTXLoader,
    FileType.XLSX: XLSXLoader,
    FileType.URL: WebLoader,
}


class DocumentLoaderFactory:
    """Factory class to instantiate the correct loader for a source."""

    @staticmethod
    def get_loader(source: str, **kwargs) -> BaseDocumentLoader:
        """
        Instantiate the appropriate loader for the given source.

        Args:
            source: Either a local filesystem path or an HTTP(S) URL.
            **kwargs: Loader-specific options forwarded to the constructor.

        Returns:
            A concrete BaseDocumentLoader instance ready to call .load() on.

        Raises:
            UnsupportedFileTypeException: If the file extension isn't supported.
        """
        # URL path
        if is_url(source):
            return WebLoader(source, **kwargs)

        # Local file path
        ext = Path(source).suffix.lower()
        file_type = EXTENSION_TO_FILETYPE.get(ext)
        if file_type is None:
            raise UnsupportedFileTypeException(
                f"Unsupported file extension: '{ext}'",
                details={
                    "extension": ext,
                    "supported": sorted(EXTENSION_TO_FILETYPE.keys()),
                },
            )

        loader_cls = LOADER_REGISTRY.get(file_type)
        if loader_cls is None:
            raise UnsupportedFileTypeException(
                f"No loader registered for file type: {file_type}",
                details={"file_type": file_type.value},
            )
        return loader_cls(source, **kwargs)

    @staticmethod
    def supported_extensions() -> list[str]:
        """Return all file extensions handled by the factory."""
        return sorted(EXTENSION_TO_FILETYPE.keys())
