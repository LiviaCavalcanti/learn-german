"""LLM client factory (selects fake vs. litellm from config)."""

from __future__ import annotations

from functools import lru_cache

from sprachheft.config import get_settings
from sprachheft.llm.base import LLMClient

_FAKE_MODELS = {"fake", "none", "test", ""}


@lru_cache
def get_llm_client() -> LLMClient:
    settings = get_settings()
    if settings.llm_model.strip().lower() in _FAKE_MODELS:
        from sprachheft.llm.fake import FakeLLMClient

        return FakeLLMClient()

    from sprachheft.llm.client import LiteLLMClient

    return LiteLLMClient(settings)


def reset_llm_cache() -> None:
    get_llm_client.cache_clear()
