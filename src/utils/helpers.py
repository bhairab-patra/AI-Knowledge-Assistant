"""General-purpose helper utilities used throughout the pipeline."""
import hashlib
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def generate_document_id() -> str:
    """Generate a unique UUID4 string for tagging documents."""
    return str(uuid.uuid4())


def utc_now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def compute_file_hash(file_path: str | Path, algorithm: str = "sha256") -> str:
    """Compute hash of a file's contents for deduplication."""
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_file_extension(file_path: str | Path) -> str:
    """Return lowercase file extension including the leading dot."""
    return Path(file_path).suffix.lower()


def get_file_size_bytes(file_path: str | Path) -> int:
    """Return file size in bytes."""
    return os.path.getsize(file_path)


def safe_filename(name: str) -> str:
    """Sanitize a filename so it is safe to write to disk."""
    keep = "-_.() "
    return "".join(c for c in name if c.isalnum() or c in keep).strip() or "file"


def truncate_text(text: str, max_chars: int = 200) -> str:
    """Truncate text and append an ellipsis if it exceeds max_chars."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def is_url(value: Optional[str]) -> bool:
    """Cheap check for whether a string is an HTTP(S) URL."""
    if not value:
        return False
    return value.lower().startswith(("http://", "https://"))
