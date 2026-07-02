"""Ingestion seam.

v1 supports manual paste of a transcript (+ optional translation). A future
``LinkIngestor`` (yt-dlp + Whisper) can be registered here without touching
callers.
"""

from __future__ import annotations

from sprachheft.ingest.base import Ingestor, IngestRequest, IngestResult
from sprachheft.ingest.manual import ManualIngestor

_INGESTORS: list[Ingestor] = [ManualIngestor()]


def resolve(req: IngestRequest) -> IngestResult:
    for ingestor in _INGESTORS:
        if ingestor.can_handle(req):
            return ingestor.ingest(req)
    raise ValueError(
        "No ingestor could handle this input. Paste a transcript "
        "(automatic transcription from a link is not available yet)."
    )


__all__ = ["IngestRequest", "IngestResult", "Ingestor", "resolve"]
