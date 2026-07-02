"""Manual ingestion: use the pasted transcript/translation as-is."""

from __future__ import annotations

from sprachheft.ingest.base import IngestRequest, IngestResult


class ManualIngestor:
    def can_handle(self, req: IngestRequest) -> bool:
        return bool(req.transcript and req.transcript.strip())

    def ingest(self, req: IngestRequest) -> IngestResult:
        if not req.transcript or not req.transcript.strip():
            raise ValueError("Manual ingestion requires a non-empty transcript.")
        translation = None
        if req.translation and req.translation.strip():
            translation = req.translation.strip()
        return IngestResult(
            transcript=req.transcript.strip(),
            translation=translation,
            source_url=req.source_url,
        )
