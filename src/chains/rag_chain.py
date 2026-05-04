"""
Retrieval-Augmented Generation (RAG) chain built with LangChain Expression Language (LCEL).

Pipeline: question -> retriever -> format context -> prompt -> LLM -> string output.
Returns both the answer text and the source documents that were used.
"""
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough

from src.core.exceptions import ChainExecutionException
from src.llm.bedrock_llm import get_llm_service
from src.prompts.templates import RAG_PROMPT
from src.retrievers.retriever import build_retriever
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _format_docs_as_context(docs: List[Document]) -> str:
    """Combine retrieved documents into a single context string with citations."""
    if not docs:
        return "No relevant documents were found."
    blocks = []
    for i, d in enumerate(docs, start=1):
        source = d.metadata.get("file_name") or d.metadata.get("source", "unknown")
        page = d.metadata.get("page")
        loc = f" (page {page})" if page is not None else ""
        blocks.append(f"[Document {i} | source: {source}{loc}]\n{d.page_content}")
    return "\n\n".join(blocks)


class RAGChain:
    """
    Production RAG chain.

    Usage:
        chain = RAGChain()
        result = chain.invoke("What is X?")
        # result == {"answer": "...", "sources": [Document, ...], "question": "..."}
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
        self.chain = self._build_chain()

    def _build_chain(self):
        """Compose the LCEL chain."""
        # Step 1: retrieve docs in parallel with passing the question through
        retrieve_step = RunnableParallel(
            {
                "docs": self.retriever,
                "question": RunnablePassthrough(),
            }
        )

        # Step 2: format docs to a context string while keeping question and docs
        def _prepare(inputs: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "context": _format_docs_as_context(inputs["docs"]),
                "question": inputs["question"],
                "docs": inputs["docs"],
            }

        prepare_step = RunnableLambda(_prepare)

        # Step 3: feed prompt -> LLM -> str, while keeping docs around
        answer_step = (
            RunnableParallel(
                {
                    "answer": (
                        RunnableLambda(lambda x: {"context": x["context"], "question": x["question"]})
                        | RAG_PROMPT
                        | self.llm
                        | StrOutputParser()
                    ),
                    "sources": RunnableLambda(lambda x: x["docs"]),
                    "question": RunnableLambda(lambda x: x["question"]),
                }
            )
        )

        return retrieve_step | prepare_step | answer_step

    def invoke(self, question: str) -> Dict[str, Any]:
        """Run the chain end-to-end for a single user question."""
        if not question or not question.strip():
            raise ChainExecutionException("Question must not be empty")

        logger.info("RAG chain invoked", question_length=len(question))
        try:
            result = self.chain.invoke(question)
        except Exception as exc:
            logger.error("RAG chain failed", error=str(exc))
            raise ChainExecutionException(
                f"RAG chain execution failed: {exc}", cause=exc
            ) from exc

        logger.info(
            "RAG chain completed",
            num_sources=len(result.get("sources") or []),
            answer_length=len(result.get("answer") or ""),
        )
        return result

    async def ainvoke(self, question: str) -> Dict[str, Any]:
        """Async version of invoke for use in FastAPI endpoints."""
        if not question or not question.strip():
            raise ChainExecutionException("Question must not be empty")
        try:
            return await self.chain.ainvoke(question)
        except Exception as exc:
            raise ChainExecutionException(
                f"RAG chain execution failed: {exc}", cause=exc
            ) from exc
