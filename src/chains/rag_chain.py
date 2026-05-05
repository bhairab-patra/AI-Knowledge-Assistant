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
from config.settings import settings
from src.vectorstore.chroma_store import get_vector_store
from src.observability.tracing import get_tracer
from src.observability.langfuse_handler import get_langfuse_handler

tracer = get_tracer()
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
        self.retriever = build_retriever(k=k, search_type=search_type, filter_dict=filter_dict)
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
        answer_step = RunnableParallel(
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

        return retrieve_step | prepare_step | answer_step

    def invoke(self, question: str) -> Dict[str, Any]:
        """Run the chain end-to-end for a single user question, with confidence scoring + tracing."""

        if not question or not question.strip():
            raise ChainExecutionException("Question must not be empty")

        logger.info("RAG chain invoked", question_length=len(question))

        with tracer.start_as_current_span("rag.invoke") as span:
            span.set_attribute("rag.question_length", len(question))

            try:
                # 1. Retrieve docs WITH similarity scores (traced).
                with tracer.start_as_current_span("rag.retrieve"):
                    store = get_vector_store()
                    pairs = store.similarity_search_with_score(question, k=settings.RETRIEVER_K)

                docs = [d for d, _ in pairs]
                # Cosine distance ∈ [0, 2] → similarity ∈ [0, 1]
                similarities = [max(0.0, 1.0 - dist / 2.0) for _, dist in pairs]

                # 2. Aggregate per-chunk similarities into one confidence score.
                confidence = sum(similarities) / len(similarities) if similarities else 0.0
                if confidence >= 0.80:
                    confidence_label = "high"
                elif confidence >= 0.55:
                    confidence_label = "medium"
                else:
                    confidence_label = "low"

                # Surface confidence + retrieval count on the parent span.
                span.set_attribute("rag.confidence", round(confidence, 3))
                span.set_attribute("rag.confidence_label", confidence_label)
                span.set_attribute("rag.num_sources", len(docs))

                # 3. Build context and run the LLM (traced).
                context = _format_docs_as_context(docs)
                with tracer.start_as_current_span("rag.llm_call") as llm_span:
                    llm_span.set_attribute("rag.context_chars", len(context))
                    answer = (RAG_PROMPT | self.llm | StrOutputParser()).invoke(
                        {"context": context, "question": question}
                    )
                    llm_span.set_attribute("rag.answer_chars", len(answer or ""))

                    lf_handler = get_langfuse_handler()

                    config = {"callbacks": [lf_handler]} if lf_handler else {}

                    answer = (RAG_PROMPT | self.llm | StrOutputParser()).invoke(
                        {"context": context, "question": question},
                        config=config,  # ← THIS captures everything
                    )

            except ChainExecutionException:
                raise
            except Exception as exc:
                span.record_exception(exc)
                logger.error("RAG chain failed", error=str(exc))
                raise ChainExecutionException(
                    f"RAG chain execution failed: {exc}", cause=exc
                ) from exc

        logger.info(
            "RAG chain completed",
            num_sources=len(docs),
            answer_length=len(answer or ""),
            confidence=round(confidence, 3),
            confidence_label=confidence_label,
        )

        return {
            "question": question,
            "answer": answer,
            "sources": docs,
            "confidence": round(confidence, 3),
            "confidence_label": confidence_label,
        }

    async def ainvoke(self, question: str) -> Dict[str, Any]:
        """Async version of invoke for use in FastAPI endpoints."""
        if not question or not question.strip():
            raise ChainExecutionException("Question must not be empty")
        try:
            return await self.chain.ainvoke(question)
        except Exception as exc:
            raise ChainExecutionException(f"RAG chain execution failed: {exc}", cause=exc) from exc
