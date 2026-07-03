"""Real LLM client backed by litellm + instructor (structured Pydantic output)."""

from __future__ import annotations

from sprachheft.config import Settings


class LiteLLMClient:
    def __init__(self, settings: Settings):
        self._model = settings.llm_model
        self._api_base = settings.llm_api_base
        self._api_key = settings.llm_api_key
        self._temperature = settings.llm_temperature
        self._timeout = settings.llm_timeout

    def generate_structured(self, messages: list[dict], response_model, **kwargs):
        import instructor
        import litellm

        # Local providers (Ollama) don't reliably support OpenAI-style tool calling,
        # so instructor's default TOOLS mode fails with "'NoneType' object is not
        # iterable" (the response has no tool_calls to iterate). JSON mode parses the
        # model's content directly and is the recommended setting for Ollama.
        model = self._model.lower()
        mode = (
            instructor.Mode.JSON
            if model.startswith(("ollama/", "ollama_chat/"))
            else instructor.Mode.TOOLS
        )
        client = instructor.from_litellm(litellm.completion, mode=mode)
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
            timeout=self._timeout,
            **extra,
            **kwargs,
        )
