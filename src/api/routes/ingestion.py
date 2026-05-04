"""Document ingestion endpoints."""
import shutil
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from config.settings import settings
from src.api.models.request import (
    DeleteByDocumentRequest,
    DeleteBySourceRequest,
    IngestDirectoryRequest,
    IngestURLRequest,
)
from src.api.models.response import DeleteResponse, IngestResponse, IngestResultItem
from src.core.exceptions import RAGPipelineException
from src.services.ingestion_service import IngestionService
from src.utils.helpers import safe_filename
from src.utils.logger import get_logger
from src.utils.validators import validate_file_extension

logger = get_logger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


def _to_response(result: dict) -> IngestResponse:
    """Convert ingestion service result dict into the API response model."""
    return IngestResponse(
        total=result["total"],
        successful=result["successful"],
        failed=result["failed"],
        successes=[IngestResultItem(**s) for s in result.get("successes", [])],
        failures=[IngestResultItem(**f) for f in result.get("failures", [])],
    )


@router.post("/files", response_model=IngestResponse, summary="Upload and ingest files")
async def ingest_files(files: List[UploadFile] = File(...)) -> IngestResponse:
    """
    Upload one or more files. Each file is saved to the raw data directory
    and then ingested into the vector store.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    service = IngestionService()
    saved_paths: List[str] = []

    raw_dir = Path(settings.DATA_RAW_DIR)
    raw_dir.mkdir(parents=True, exist_ok=True)

    try:
        for f in files:
            filename = safe_filename(f.filename or "uploaded")
            try:
                validate_file_extension(filename, settings.ALLOWED_FILE_EXTENSIONS)
            except RAGPipelineException as exc:
                logger.warning("Rejecting unsupported upload", filename=filename, error=exc.message)
                continue

            # Stream upload to disk to avoid loading huge files in memory
            target_path = raw_dir / filename
            with target_path.open("wb") as out:
                shutil.copyfileobj(f.file, out)
            saved_paths.append(str(target_path))

        if not saved_paths:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="None of the uploaded files have a supported extension",
            )

        result = service.ingest_sources(saved_paths)
        return _to_response(result)
    finally:
        for f in files:
            try:
                await f.close()
            except Exception:
                pass


@router.post("/urls", response_model=IngestResponse, summary="Ingest URLs")
async def ingest_urls(payload: IngestURLRequest) -> IngestResponse:
    """Ingest content from a list of HTTP(S) URLs."""
    service = IngestionService()
    result = service.ingest_sources(payload.urls)
    return _to_response(result)


@router.post("/directory", response_model=IngestResponse, summary="Ingest a server directory")
async def ingest_directory(payload: IngestDirectoryRequest) -> IngestResponse:
    """Ingest every supported file in a server-side directory."""
    service = IngestionService()
    result = service.ingest_directory(payload.directory, recursive=payload.recursive)
    return _to_response(result)


@router.delete("/document", response_model=DeleteResponse, summary="Delete by document_id")
async def delete_document(payload: DeleteByDocumentRequest) -> DeleteResponse:
    IngestionService().delete_by_document_id(payload.document_id)
    return DeleteResponse(
        status="ok",
        message=f"Deleted chunks for document_id={payload.document_id}",
    )


@router.delete("/source", response_model=DeleteResponse, summary="Delete by source")
async def delete_source(payload: DeleteBySourceRequest) -> DeleteResponse:
    IngestionService().delete_by_source(payload.source)
    return DeleteResponse(
        status="ok",
        message=f"Deleted chunks for source={payload.source}",
    )
