"""Entry point - run the FastAPI app via uvicorn."""
import uvicorn

from config.settings import settings


def main() -> None:
    uvicorn.run(
        "src.api.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
