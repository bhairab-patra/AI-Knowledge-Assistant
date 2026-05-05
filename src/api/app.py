"""
FastAPI application factory.

Initializes logging, registers exception handlers and CORS, and mounts
all API routers under the configured prefix.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.logging_config import configure_logging
from config.settings import settings
from src.api.middleware.error_handler import register_exception_handlers
from src.api.routes import health as health_routes
from src.api.routes import ingestion as ingestion_routes
from src.api.routes import query as query_routes
from src.utils.logger import get_logger
from src.observability.tracing import setup_tracing  # ← new import

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup/shutdown logic."""
    configure_logging()
    logger = get_logger(__name__)
    settings.ensure_dirs()
    logger.info(
        "Starting application",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        env=settings.ENVIRONMENT,
    )
    yield
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Application factory used by uvicorn / tests."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-ready RAG pipeline backed by Amazon Bedrock and "
            "ChromaDB. Built with LangChain LCEL."
        ),
        docs_url=f"{settings.API_PREFIX}/docs",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        redoc_url=f"{settings.API_PREFIX}/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Routers
    app.include_router(health_routes.router, prefix=settings.API_PREFIX)
    app.include_router(ingestion_routes.router, prefix=settings.API_PREFIX)
    app.include_router(query_routes.router, prefix=settings.API_PREFIX)

    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": f"{settings.API_PREFIX}/docs",
        }
    setup_tracing(app)   

    return app


app = create_app()
