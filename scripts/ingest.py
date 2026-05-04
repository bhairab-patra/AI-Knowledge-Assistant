"""
CLI ingestion script.

Usage examples:
    python -m scripts.ingest --file data/raw/manual.pdf
    python -m scripts.ingest --directory data/raw
    python -m scripts.ingest --url https://example.com/article
    python -m scripts.ingest --directory data/raw --recursive
"""
import argparse
import json
import sys

from config.logging_config import configure_logging
from src.services.ingestion_service import IngestionService
from src.utils.logger import get_logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest local files, URLs, or directories into the RAG vector store."
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="Path to a single file to ingest")
    src.add_argument("--url", help="HTTP(S) URL to ingest")
    src.add_argument("--directory", help="Directory of files to ingest")
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Recurse into subdirectories (default: true)",
    )
    parser.add_argument(
        "--non-recursive",
        dest="recursive",
        action="store_false",
        help="Disable recursion when ingesting a directory",
    )
    return parser


def main(argv=None) -> int:
    configure_logging()
    log = get_logger("ingest-cli")
    args = build_parser().parse_args(argv)

    service = IngestionService()

    if args.file:
        result = service.ingest_source(args.file)
    elif args.url:
        result = service.ingest_source(args.url)
    else:
        result = service.ingest_directory(args.directory, recursive=args.recursive)

    print(json.dumps(result, indent=2, default=str))
    log.info("Ingestion script complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
