"""Shared pytest fixtures."""
import os
import shutil
import sys
from pathlib import Path

import pytest

# Ensure project root is on PYTHONPATH so `import src...` works in tests
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def tmp_test_dir(tmp_path_factory) -> Path:
    """Temporary directory used for the test session."""
    p = tmp_path_factory.mktemp("rag_test")
    yield p
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)


@pytest.fixture
def sample_text_file(tmp_path: Path) -> Path:
    f = tmp_path / "sample.txt"
    f.write_text(
        "Cosmic rays are high-energy particles. "
        "They constantly bombard Earth's atmosphere from outer space.",
        encoding="utf-8",
    )
    return f


@pytest.fixture
def sample_md_file(tmp_path: Path) -> Path:
    f = tmp_path / "sample.md"
    f.write_text("# Title\n\nThis is markdown content.\n", encoding="utf-8")
    return f


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path):
    """Point ChromaDB and data dirs at a per-test tmp folder so tests are hermetic."""
    monkeypatch.setenv("CHROMA_PERSIST_DIRECTORY", str(tmp_path / "chroma"))
    monkeypatch.setenv("DATA_RAW_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("DATA_PROCESSED_DIR", str(tmp_path / "processed"))
    # Don't talk to real AWS in unit tests
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
