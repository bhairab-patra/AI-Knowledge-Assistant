"""Unit tests for document loaders and the loader factory."""
import pytest

from src.core.exceptions import DocumentLoadException, UnsupportedFileTypeException
from src.loaders.document_loader_factory import DocumentLoaderFactory
from src.loaders.text_loader import PlainTextLoader


def test_plain_text_loader_loads_content(sample_text_file):
    loader = PlainTextLoader(str(sample_text_file))
    docs = loader.load()
    assert len(docs) == 1
    assert "cosmic rays" in docs[0].page_content.lower()
    md = docs[0].metadata
    assert md["file_type"] == "txt"
    assert md["file_name"] == "sample.txt"
    assert "document_id" in md


def test_loader_factory_routes_txt(sample_text_file):
    loader = DocumentLoaderFactory.get_loader(str(sample_text_file))
    assert isinstance(loader, PlainTextLoader)


def test_loader_factory_unsupported_extension(tmp_path):
    bad = tmp_path / "x.xyz"
    bad.write_text("hi")
    with pytest.raises(UnsupportedFileTypeException):
        DocumentLoaderFactory.get_loader(str(bad))


def test_loader_factory_url_routes_to_web():
    from src.loaders.web_loader import WebLoader
    loader = DocumentLoaderFactory.get_loader("https://example.com")
    assert isinstance(loader, WebLoader)


def test_loader_raises_for_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.txt"
    loader = PlainTextLoader(str(missing))
    with pytest.raises(DocumentLoadException):
        loader.load()


def test_supported_extensions_are_sorted():
    exts = DocumentLoaderFactory.supported_extensions()
    assert ".pdf" in exts
    assert ".docx" in exts
    assert ".csv" in exts
    assert exts == sorted(exts)
