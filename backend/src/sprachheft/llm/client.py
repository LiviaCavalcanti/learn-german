"""Real LLM client backed by litellm + instructor (structured Pydantic output)."""

from __future__ import annotations

import threading

from sprachheft.config import Settings

# instructor's v2 mode registry loads provider handlers *lazily* and is NOT
# thread-safe: ``ModeRegistry.get_handlers`` pops a mode's loader from the registry
# and only then imports the handler module. That pop-then-import is not atomic, so
# when several generations run at once on FastAPI's threadpool the first time a
# handler is needed, racing threads raise "Mode ... is not registered for provider
# Provider.OPENAI" and the entry can be dropped for the rest of the process.
# Importing the OpenAI handler module once, up front and single-threaded, registers
# every OpenAI mode eagerly so all later lookups are plain dict reads. ``from_litellm``
# always patches the OpenAI provider, so warming that one module is enough.
_registry_lock = threading.Lock()
_registry_ready = False


def _prewarm_instructor_registry() -> None:
    """Eagerly register instructor's OpenAI mode handlers (see note above)."""
    global _registry_ready
    if _registry_ready:
        return
    with _registry_lock:
        if _registry_ready:
            return
        try:
            import instructor.v2.providers.openai.handlers  # noqa: F401
        except Exception:
            # Instructor version without this internal path: fall back to the
            # library's own lazy registration. Mark ready so we don't retry per call.
            pass
        _registry_ready = True


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

        # Register instructor's provider handlers before the first (possibly
        # concurrent) call so the lazy, non-thread-safe registry can't race.
        _prewarm_instructor_registry()

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
