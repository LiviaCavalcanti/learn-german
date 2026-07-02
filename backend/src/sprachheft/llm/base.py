"""LLM client protocol."""

from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    """Returns a validated instance of ``response_model`` for the given chat messages."""

    def generate_structured(
        self, messages: list[dict], response_model: type[T], **kwargs
    ) -> T: ...
