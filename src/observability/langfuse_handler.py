"""Langfuse callback handler - auto-captures every LLM call, prompt, token count, etc."""
import os
from functools import lru_cache
from typing import Optional

from langfuse.callback import CallbackHandler


@lru_cache(maxsize=1)
def get_langfuse_handler() -> Optional[CallbackHandler]:
    """Return a singleton Langfuse handler, or None if not configured."""
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        return None
    return CallbackHandler(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
    )