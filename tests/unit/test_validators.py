"""Unit tests for input validators."""
import pytest

from src.core.exceptions import (
    FileSizeExceededException,
    InvalidURLException,
    UnsupportedFileTypeException,
    ValidationException,
)
from src.utils.validators import (
    validate_file_extension,
    validate_file_size,
    validate_query,
    validate_url,
)


def test_validate_file_extension_pass():
    assert validate_file_extension("doc.pdf") == ".pdf"


def test_validate_file_extension_reject():
    with pytest.raises(UnsupportedFileTypeException):
        validate_file_extension("evil.exe")


def test_validate_file_size_pass():
    validate_file_size(100, 1024)  # no exception


def test_validate_file_size_fail():
    with pytest.raises(FileSizeExceededException):
        validate_file_size(2048, 1024)


def test_validate_url_pass():
    assert validate_url("https://example.com/foo") == "https://example.com/foo"


@pytest.mark.parametrize("url", ["", "ftp://x", "not-a-url", "http://"])
def test_validate_url_fail(url):
    with pytest.raises(InvalidURLException):
        validate_url(url)


def test_validate_query_strips():
    assert validate_query("  hello  ") == "hello"


def test_validate_query_empty():
    with pytest.raises(ValidationException):
        validate_query("   ")


def test_validate_query_too_long():
    with pytest.raises(ValidationException):
        validate_query("x" * 5000, max_length=4000)
