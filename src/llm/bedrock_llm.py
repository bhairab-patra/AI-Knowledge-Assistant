"""
Amazon Bedrock LLM client via langchain_aws.ChatBedrock.

Uses the Converse API under the hood (works for Claude, Llama, Mistral, etc.).
"""
from functools import lru_cache
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from langchain_aws import ChatBedrock
from langchain_core.language_models import BaseChatModel

from config.settings import settings
from src.core.exceptions import BedrockClientException, LLMException
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _build_bedrock_runtime_client():
    """Construct a boto3 bedrock-runtime client with sensible retry config."""
    boto_config = Config(
        region_name=settings.AWS_REGION,
        retries={"max_attempts": 5, "mode": "adaptive"},
        connect_timeout=10,
        read_timeout=120,
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


class BedrockLLMService:
    """Wrapper around ChatBedrock exposing a configured LangChain LLM."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> None:
        self.model_id = model_id or settings.BEDROCK_LLM_MODEL_ID
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        self.top_p = top_p if top_p is not None else settings.LLM_TOP_P
        self.top_k = top_k if top_k is not None else settings.LLM_TOP_K

        self.client = _build_bedrock_runtime_client()

        # Build model_kwargs forwarded to Bedrock.
        # Newer Claude models (Haiku 4.5 / Sonnet 4+) reject having BOTH
        # `temperature` and `top_p` set, so we pick one based on
        # settings.LLM_USE_TOP_P. Default is temperature-only sampling.
        model_kwargs: dict = {}
        use_top_p = getattr(settings, "LLM_USE_TOP_P", False)
        if use_top_p:
            model_kwargs["top_p"] = self.top_p
        else:
            model_kwargs["temperature"] = self.temperature

        # top_k is Anthropic-specific and is compatible with either sampler.
        if "anthropic" in self.model_id.lower() and self.top_k is not None:
            model_kwargs["top_k"] = self.top_k

        try:
            self._llm = ChatBedrock(
                client=self.client,
                model_id=self.model_id,
                region_name=settings.AWS_REGION,
                model_kwargs=model_kwargs,
                # Use ChatBedrock's max_tokens parameter where supported
            )
            # Some langchain-aws versions expose `max_tokens` as a separate attr
            try:
                self._llm.max_tokens = self.max_tokens  # type: ignore[attr-defined]
            except Exception:
                pass
        except Exception as exc:
            raise BedrockClientException(
                f"Failed to instantiate ChatBedrock: {exc}", cause=exc
            ) from exc

        logger.info(
            "Bedrock LLM initialized",
            model_id=self.model_id,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    @property
    def langchain_llm(self) -> BaseChatModel:
        """Return underlying LangChain chat model for use in chains."""
        return self._llm

    def invoke(self, prompt: str) -> str:
        """Convenience direct invocation - bypasses the chain."""
        try:
            response = self._llm.invoke(prompt)
            return getattr(response, "content", str(response))
        except (ClientError, BotoCoreError) as exc:
            raise LLMException(
                f"Bedrock LLM invocation failed: {exc}", cause=exc
            ) from exc


@lru_cache(maxsize=1)
def get_llm_service() -> BedrockLLMService:
    """Cached singleton accessor for the LLM service."""
    return BedrockLLMService()
