"""Query endpoints - one-shot RAG and conversational RAG."""
from fastapi import APIRouter

from src.api.models.request import ConversationalQueryRequest, QueryRequest
from src.api.models.response import QueryResponse
from src.services.query_service import QueryService
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("", response_model=QueryResponse, summary="One-shot RAG query")
async def query(payload: QueryRequest) -> QueryResponse:
    """Answer a single question using the indexed knowledge base."""
    result = QueryService().query(
        question=payload.question,
        k=payload.k,
        search_type=payload.search_type,
        filter_dict=payload.filter,
    )
    return QueryResponse(**result)


@router.post("/chat", response_model=QueryResponse, summary="Conversational RAG query")
async def chat(payload: ConversationalQueryRequest) -> QueryResponse:
    """Answer a question taking prior chat history into account."""
    history = [t.model_dump() for t in (payload.chat_history or [])]
    result = QueryService().conversational_query(
        question=payload.question,
        chat_history=history,
        k=payload.k,
        search_type=payload.search_type,
        filter_dict=payload.filter,
    )
    return QueryResponse(**result)
