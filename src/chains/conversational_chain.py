"""
Conversational RAG chain that supports multi-turn chat history.

Uses a question-rewrite step to convert follow-ups like "what about Bob?"
into self-contained queries before retrieval.
"""
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough

from src.chains.rag_chain import _format_docs_as_context
from src.core.exceptions import ChainExecutionException
from src.llm.bedrock_llm import get_llm_service
from src.prompts.templates import CONVERSATIONAL_PROMPT, QUESTION_REWRITE_PROMPT
from src.retrievers.retriever import build_retriever
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _history_to_messages(history: List[Dict[str, str]]) -> List[BaseMessage]:
    """Convert a serializable history list into LangChain message objects."""
    messages: List[BaseMessage] = []
    for turn in history or []:
        role = (turn.get("role") or "").lower()
        content = turn.get("content", "")
        if not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role in ("assistant", "ai"):
            messages.append(AIMessage(content=content))
    return messages


def _history_to_text(history: List[Dict[str, str]]) -> str:
    """Convert history to a flat text representation for the rewrite prompt."""
    if not history:
        return "(no prior conversation)"
    return "\n".join(
        f"{(turn.get('role') or 'user').capitalize()}: {turn.get('content', '')}"
        for turn in history
        if turn.get("content")
    )


class ConversationalRAGChain:
    """
    Multi-turn RAG chain with question rewriting.

    Usage:
        chain = ConversationalRAGChain()
        result = chain.invoke(
            question="What about its pricing?",
            chat_history=[{"role": "user", "content": "Tell me about product X"},
                          {"role": "assistant", "content": "Product X is..."}]
        )
    """

    def __init__(
        self,
        k: Optional[int] = None,
        search_type: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.llm = get_llm_service().langchain_llm
        self.retriever = build_retriever(
            k=k, search_type=search_type, filter_dict=filter_dict
        )

        # Sub-chain that rewrites a follow-up into a standalone question
        self._rewrite_chain = QUESTION_REWRITE_PROMPT | self.llm | StrOutputParser()

        # Final answering chain
        self._answer_chain = CONVERSATIONAL_PROMPT | self.llm | StrOutputParser()

    def _rewrite_if_needed(self, question: str, history_text: str) -> str:
        """Rewrite the question only when there is prior conversation."""
        if history_text == "(no prior conversation)":
            return question
        try:
            return self._rewrite_chain.invoke(
                {"chat_history": history_text, "question": question}
            ).strip() or question
        except Exception as exc:
            logger.warning("Question rewrite failed - using original", error=str(exc))
            return question

    def invoke(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Run the conversational chain end-to-end."""
        if not question or not question.strip():
            raise ChainExecutionException("Question must not be empty")

        history = chat_history or []
        history_text = _history_to_text(history)
        history_messages = _history_to_messages(history)

        logger.info(
            "Conversational RAG invoked",
            question_length=len(question),
            history_turns=len(history),
        )

        try:
            standalone_question = self._rewrite_if_needed(question, history_text)
            docs: List[Document] = self.retriever.invoke(standalone_question)
            context = _format_docs_as_context(docs)
            answer = self._answer_chain.invoke(
                {
                    "context": context,
                    "chat_history": history_messages,
                    "question": question,
                }
            )
        except Exception as exc:
            logger.error("Conversational chain failed", error=str(exc))
            raise ChainExecutionException(
                f"Conversational chain execution failed: {exc}", cause=exc
            ) from exc

        return {
            "answer": answer,
            "sources": docs,
            "question": question,
            "standalone_question": standalone_question,
        }
