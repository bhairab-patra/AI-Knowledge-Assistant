"""Plaintext and Markdown document loader."""
from pathlib import Path
from typing import List

from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader
from langchain_core.documents import Document

from src.core.constants import FileType
from src.core.exceptions import DocumentLoadException
from src.loaders.base_loader import BaseDocumentLoader


class PlainTextLoader(BaseDocumentLoader):
    """Load .txt files as a single LangChain Document."""

    file_type = FileType.TEXT.value

    def _load(self) -> List[Document]:
        path = Path(self.source)
        if not path.exists():
            raise DocumentLoadException(
                f"Text file not found: {self.source}",
                details={"source": self.source},
            )
        try:
            loader = TextLoader(str(path), encoding="utf-8", autodetect_encoding=True)
            return loader.load()
        except Exception as exc:
            raise DocumentLoadException(
                f"Failed to load text file: {self.source}",
                cause=exc,
            ) from exc


class MarkdownLoader(BaseDocumentLoader):
    """Load .md files using Unstructured (preserves headings & structure)."""

    file_type = FileType.MARKDOWN.value

    def _load(self) -> List[Document]:
        path = Path(self.source)
        if not path.exists():
            raise DocumentLoadException(
                f"Markdown file not found: {self.source}",
                details={"source": self.source},
            )
        try:
            loader = UnstructuredMarkdownLoader(str(path))
            return loader.load()
        except Exception as exc:
            raise DocumentLoadException(
                f"Failed to load markdown file: {self.source}",
                cause=exc,
            ) from exc
