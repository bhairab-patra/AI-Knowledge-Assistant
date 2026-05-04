"""Unit tests for the text splitter."""
from langchain_core.documents import Document

from src.splitters.text_splitter import DocumentTextSplitter


def test_splitter_returns_chunks():
    text = "Sentence one. " * 200
    splitter = DocumentTextSplitter(chunk_size=200, chunk_overlap=50)
    docs = [Document(page_content=text, metadata={"source": "memo.txt"})]
    chunks = splitter.split_documents(docs)
    assert len(chunks) > 1
    for i, c in enumerate(chunks):
        assert c.metadata["chunk_index"] == i
        assert c.metadata["total_chunks"] == len(chunks)
        assert c.metadata["source"] == "memo.txt"


def test_splitter_handles_empty_input():
    splitter = DocumentTextSplitter()
    assert splitter.split_documents([]) == []


def test_split_text_returns_strings():
    splitter = DocumentTextSplitter(chunk_size=100, chunk_overlap=20)
    out = splitter.split_text("a" * 1000)
    assert isinstance(out, list)
    assert all(isinstance(s, str) for s in out)
