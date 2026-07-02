"""Real LLM client backed by litellm + instructor (structured Pydantic output)."""

from __future__ import annotations

from sprachheft.config import Settings


class LiteLLMClient:
    def __init__(self, settings: Settings):
        self._model = settings.llm_model
        self._api_base = settings.llm_api_base
        self._api_key = settings.llm_api_key
        self._temperature = settings.llm_temperature

    def generate_structured(self, messages: list[dict], response_model, **kwargs):
        import instructor
        import litellm

        client = instructor.from_litellm(litellm.completion)
        extra: dict = {}
        if self._api_base:
            extra["api_base"] = self._api_base
        if self._api_key:
            extra["api_key"] = self._api_key
        return client.chat.completions.create(
            model=self._model,
            messages=messages,
            response_model=response_model,
            temperature=self._temperature,
            max_retries=2,
            **extra,
            **kwargs,
        )
