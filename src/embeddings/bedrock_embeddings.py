"""
Amazon Bedrock embeddings via langchain_aws.BedrockEmbeddings.

Wraps construction with explicit boto3 client setup and retries so
production failures (throttling, transient network errors) don't crash
the pipeline.
"""
from functools import lru_cache
from typing import List, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from langchain_aws import BedrockEmbeddings
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings
from src.core.exceptions import BedrockClientException, EmbeddingException
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _build_bedrock_runtime_client():
    """Construct a boto3 bedrock-runtime client with retry config."""
    boto_config = Config(
        region_name=settings.AWS_REGION,
        retries={"max_attempts": 5, "mode": "adaptive"},
        connect_timeout=10,
        read_timeout=60,
    )
    try:
        kwargs: dict = {"config": boto_config, "service_name": "bedrock-runtime"}
        if settings.AWS_PROFILE:
            session = boto3.Session(profile_name=settings.AWS_PROFILE)
            return session.client(**kwargs)
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            kwargs.update(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            if settings.AWS_SESSION_TOKEN:
                kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN
        return boto3.client(**kwargs)
    except (BotoCoreError, ClientError) as exc:
        raise BedrockClientException(
            f"Failed to build Bedrock runtime client: {exc}", cause=exc
        ) from exc


class BedrockEmbeddingsService:
    """Wrapper around BedrockEmbeddings exposing safe embed_*/embed_query."""

    def __init__(self, model_id: Optional[str] = None) -> None:
        self.model_id = model_id or settings.BEDROCK_EMBEDDING_MODEL_ID
        self.client = _build_bedrock_runtime_client()
        try:
            self._embeddings = BedrockEmbeddings(
                client=self.client,
                model_id=self.model_id,
                region_name=settings.AWS_REGION,
            )
        except Exception as exc:
            raise BedrockClientException(
                f"Failed to instantiate BedrockEmbeddings: {exc}", cause=exc
            ) from exc
        logger.info("Bedrock embeddings initialized", model_id=self.model_id)

    @property
    def langchain_embeddings(self) -> BedrockEmbeddings:
        """Return underlying LangChain Embeddings instance for vectorstores."""
        return self._embeddings

    @retry(
        reraise=True,
        retry=retry_if_exception_type((ClientError, BotoCoreError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts. Retries transient errors."""
        if not texts:
            return []
        try:
            return self._embeddings.embed_documents(texts)
        except (ClientError, BotoCoreError):
            raise
        except Exception as exc:
            raise EmbeddingException(
                f"Failed to embed documents: {exc}", cause=exc
            ) from exc

    @retry(
        reraise=True,
        retry=retry_if_exception_type((ClientError, BotoCoreError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def embed_query(self, text: str) -> List[float]:
        """Embed a single user query. Retries transient errors."""
        if not text or not text.strip():
            raise EmbeddingException("Cannot embed empty query")
        try:
            return self._embeddings.embed_query(text)
        except (ClientError, BotoCoreError):
            raise
        except Exception as exc:
            raise EmbeddingException(
                f"Failed to embed query: {exc}", cause=exc
            ) from exc


@lru_cache(maxsize=1)
def get_embeddings_service() -> BedrockEmbeddingsService:
    """Cached singleton for the embedding service."""
    return BedrockEmbeddingsService()
