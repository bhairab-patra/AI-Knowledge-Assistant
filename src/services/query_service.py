"""
Query service - thin wrapper around the RAG and conversational chains.

Translates raw inputs to chain inputs, formats source documents into
serializable dicts, and provides a single point of orchestration for
the API layer.
"""
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document

from src.chains.conversational_chain import ConversationalRAGChain
from src.chains.rag_chain import RAGChain
from src.utils.helpers import truncate_text
from src.utils.logger import get_logger
from src.utils.validators import validate_query

logger = get_logger(__name__)


def _serialize_source(doc: Document) -> Dict[str, Any]:
    """Lean serialization - filename + page only."""
    md = doc.metadata or {}
    return {
        "file_name": md.get("file_name") or md.get("source", "unknown"),
        "page": md.get("page"),
        "document_id": md.get("document_id"),
    }


class QueryService:
    """Stateless service that fronts the RAG chains."""

    def __init__(self) -> None:
        # Lazily instantiate chains so a missing collection in tests doesn't
        # block service construction.
        self._rag_chain: Optional[RAGChain] = None
        self._conv_chain: Optional[ConversationalRAGChain] = None

    @property
    def rag_chain(self) -> RAGChain:
        if self._rag_chain is None:
            self._rag_chain = RAGChain()
        return self._rag_chain

    @property
    def conv_chain(self) -> ConversationalRAGChain:
        if self._conv_chain is None:
            self._conv_chain = ConversationalRAGChain()
        return self._conv_chain

    # ------ Single-shot Q&A ------
    def query(
        self,
        question: str,
        k: Optional[int] = None,
        search_type: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Answer a one-shot question with sources."""
        question = validate_query(question)

        # If caller overrides retrieval params, build a fresh chain.
        chain = (
            RAGChain(k=k, search_type=search_type, filter_dict=filter_dict)
            if any(v is not None for v in (k, search_type, filter_dict))
            else self.rag_chain
        )

        result = chain.invoke(question)
        return {
            "question": result["question"],
            "answer": result["answer"],
            "sources": [_serialize_source(d) for d in result.get("sources") or []],
        }

    # ------ Conversational Q&A ------
    def conversational_query(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        k: Optional[int] = None,
        search_type: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Answer a question taking prior turns into account."""
        question = validate_query(question)
        chain = (
            ConversationalRAGChain(k=k, search_type=search_type, filter_dict=filter_dict)
            if any(v is not None for v in (k, search_type, filter_dict))
            else self.conv_chain
        )

        result = chain.invoke(question, chat_history=chat_history)
        return {
            "question": result["question"],
            "standalone_question": result.get("standalone_question"),
            "answer": result["answer"],
            "sources": [_serialize_source(d) for d in result.get("sources") or []],
        }
