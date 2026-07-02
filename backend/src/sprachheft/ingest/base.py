"""Ingestor protocol and data carriers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class IngestRequest:
    media_type: str = "text"
    source_url: str | None = None
    transcript: str | None = None
    translation: str | None = None


@dataclass
class IngestResult:
    transcript: str
    translation: str | None = None
    source_url: str | None = None


@runtime_checkable
class Ingestor(Protocol):
    def can_handle(self, req: IngestRequest) -> bool: ...

    def ingest(self, req: IngestRequest) -> IngestResult: ...
