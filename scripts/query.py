"""
CLI query script.

Usage examples:
    python -m scripts.query "What is X?"
    python -m scripts.query "What is X?" --k 8 --search-type mmr
    python -m scripts.query --interactive
"""
import argparse
import json
import sys

from config.logging_config import configure_logging
from src.services.query_service import QueryService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query the RAG knowledge base.")
    parser.add_argument("question", nargs="?", help="Question to ask")
    parser.add_argument("--k", type=int, default=None, help="Top-K documents to retrieve")
    parser.add_argument(
        "--search-type",
        choices=["similarity", "mmr", "similarity_score_threshold"],
        default=None,
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Start an interactive REPL"
    )
    return parser


def _print_result(result: dict) -> None:
    print("\n=== Answer ===")
    print(result["answer"])
    print("\n=== Sources ===")
    for i, src in enumerate(result.get("sources", []) or [], start=1):
        meta = src.get("metadata", {})
        print(f"  [{i}] {meta.get('file_name', meta.get('source', 'unknown'))}")
    print()


def main(argv=None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    service = QueryService()

    if args.interactive:
        print("Interactive RAG REPL. Type 'exit' to quit.")
        history = []
        while True:
            try:
                q = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not q:
                continue
            if q.lower() in ("exit", "quit", ":q"):
                break
            result = service.conversational_query(q, chat_history=history)
            _print_result(result)
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": result["answer"]})
        return 0

    if not args.question:
        print("Please provide a question or use --interactive", file=sys.stderr)
        return 2

    result = service.query(args.question, k=args.k, search_type=args.search_type)
    _print_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
