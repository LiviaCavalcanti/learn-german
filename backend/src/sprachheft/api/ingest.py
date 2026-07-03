"""Ingestion API: transcription capability + transcribe-from-link."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from sprachheft.config import get_settings
from sprachheft.ingest.base import IngestRequest
from sprachheft.ingest.link import LinkIngestor
from sprachheft.languages import normalize_target
from sprachheft.schemas import TranscribeIn

router = APIRouter(prefix="/ingest", tags=["ingest"])
_link = LinkIngestor()


@router.get("/status")
def status():
    settings = get_settings()
    return {
        "transcription_available": _link.is_available(),
        "enabled": settings.enable_transcription,
        "model": settings.whisper_model,
    }


@router.post("/transcribe")
def transcribe(payload: TranscribeIn):
    if not _link.is_available():
        raise HTTPException(
            status_code=501,
            detail=(
                "Transcription not available. Install the 'transcribe' extra "
                "(yt-dlp, faster-whisper) and ffmpeg, then restart the backend."
            ),
        )
    try:
        result = _link.ingest(
            IngestRequest(
                media_type="video",
                source_url=payload.source_url,
                source_lang=normalize_target(payload.source_lang),
            )
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Transcription failed: {exc}") from exc
    return {"transcript": result.transcript, "source_url": result.source_url}
