"""Input validation helpers used by the API and CLI layers."""
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from src.core.constants import EXTENSION_TO_FILETYPE
from src.core.exceptions import (
    FileSizeExceededException,
    InvalidURLException,
    UnsupportedFileTypeException,
    ValidationException,
)


def validate_file_extension(
    file_path: str | Path,
    allowed_extensions: Iterable[str] | None = None,
) -> str:
    """Validate file extension is supported. Returns the extension."""
    ext = Path(file_path).suffix.lower()
    if not ext:
        raise UnsupportedFileTypeException(
            f"File '{file_path}' has no extension",
            details={"file_path": str(file_path)},
        )

    allowed = set(allowed_extensions or EXTENSION_TO_FILETYPE.keys())
    if ext not in allowed:
        raise UnsupportedFileTypeException(
            f"File extension '{ext}' is not supported",
            details={"extension": ext, "allowed": sorted(allowed)},
        )
    return ext


def validate_file_size(file_size_bytes: int, max_size_bytes: int) -> None:
    """Raise FileSizeExceededException if file exceeds max allowed size."""
    if file_size_bytes > max_size_bytes:
        raise FileSizeExceededException(
            f"File size {file_size_bytes} bytes exceeds limit {max_size_bytes} bytes",
            details={"size": file_size_bytes, "max": max_size_bytes},
        )


def validate_url(url: str) -> str:
    """Validate that a string is a usable HTTP(S) URL."""
    if not url or not isinstance(url, str):
        raise InvalidURLException("URL must be a non-empty string")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise InvalidURLException(
            f"URL must use http or https, got '{parsed.scheme}'",
            details={"url": url},
        )
    if not parsed.netloc:
        raise InvalidURLException(f"URL has no host: {url}", details={"url": url})
    return url


def validate_query(query: str, max_length: int = 4000) -> str:
    """Validate user query string."""
    if not query or not query.strip():
        raise ValidationException("Query cannot be empty")
    query = query.strip()
    if len(query) > max_length:
        raise ValidationException(
            f"Query length {len(query)} exceeds max {max_length}",
            details={"length": len(query), "max_length": max_length},
        )
    return query
