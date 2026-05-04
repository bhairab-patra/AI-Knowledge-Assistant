"""Health and readiness endpoints."""
from fastapi import APIRouter

from config.settings import settings
from src.api.models.response import HealthResponse, StatsResponse
from src.services.ingestion_service import IngestionService

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    """Lightweight liveness check."""
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
async def ready() -> HealthResponse:
    """
    Readiness check that also confirms the vector store is reachable.
    """
    # Touch the store to verify the persistent index is intact
    IngestionService().stats()
    return HealthResponse(
        status="ready",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get("/stats", response_model=StatsResponse, summary="Vector store stats")
async def stats() -> StatsResponse:
    """Return basic stats about the underlying vector collection."""
    s = IngestionService().stats()
    return StatsResponse(**s)
