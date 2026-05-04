"""
Retriever construction over the Chroma vector store.

Supports three search strategies via configuration:
  - similarity: classic top-k cosine
  - mmr: Maximal Marginal Relevance for diverse results (default)
  - similarity_score_threshold: only return docs above a score floor
"""
from typing import Any, Dict, Optional

from langchain_core.retrievers import BaseRetriever

from config.settings import settings
from src.core.constants import SearchType
from src.core.exceptions import RetrievalException
from src.utils.logger import get_logger
from src.vectorstore.chroma_store import get_vector_store

logger = get_logger(__name__)


def build_retriever(
    k: Optional[int] = None,
    search_type: Optional[str] = None,
    fetch_k: Optional[int] = None,
    lambda_mult: Optional[float] = None,
    score_threshold: Optional[float] = None,
    filter_dict: Optional[Dict[str, Any]] = None,
) -> BaseRetriever:
    """
    Build a LangChain retriever over the configured vector store.

    Args:
        k: number of documents to return.
        search_type: one of "similarity", "mmr", "similarity_score_threshold".
        fetch_k: docs to fetch before MMR re-ranking.
        lambda_mult: 0=max diversity, 1=max relevance for MMR.
        score_threshold: minimum similarity score to include.
        filter_dict: metadata filter applied during retrieval.

    Returns:
        A configured LangChain retriever.
    """
    store = get_vector_store().langchain_store

    k = k or settings.RETRIEVER_K
    search_type = (search_type or settings.RETRIEVER_SEARCH_TYPE).lower()
    fetch_k = fetch_k or settings.RETRIEVER_FETCH_K
    lambda_mult = lambda_mult if lambda_mult is not None else settings.RETRIEVER_LAMBDA_MULT
    score_threshold = (
        score_threshold if score_threshold is not None else settings.RETRIEVER_SCORE_THRESHOLD
    )

    search_kwargs: Dict[str, Any] = {"k": k}
    if filter_dict:
        search_kwargs["filter"] = filter_dict

    if search_type == SearchType.MMR.value:
        search_kwargs.update({"fetch_k": fetch_k, "lambda_mult": lambda_mult})
    elif search_type == SearchType.SIMILARITY_SCORE_THRESHOLD.value:
        search_kwargs["score_threshold"] = score_threshold
    elif search_type != SearchType.SIMILARITY.value:
        raise RetrievalException(
            f"Unsupported search_type: {search_type}",
            details={
                "search_type": search_type,
                "allowed": [t.value for t in SearchType],
            },
        )

    try:
        retriever = store.as_retriever(
            search_type=search_type, search_kwargs=search_kwargs
        )
    except Exception as exc:
        raise RetrievalException(
            f"Failed to build retriever: {exc}", cause=exc
        ) from exc

    logger.info(
        "Retriever built",
        search_type=search_type,
        k=k,
        fetch_k=fetch_k if search_type == "mmr" else None,
        score_threshold=score_threshold if search_type == "similarity_score_threshold" else None,
    )
    return retriever
