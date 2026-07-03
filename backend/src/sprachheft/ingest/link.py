"""Link ingestion: transcribe audio/video from a URL (yt-dlp + faster-whisper).

Optional: requires the ``transcribe`` extra (yt-dlp, faster-whisper) and ffmpeg on
PATH. If unavailable, ``is_available()`` returns False and callers degrade
gracefully (the app keeps working with manual transcript paste).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from sprachheft.config import get_settings
from sprachheft.ingest.base import IngestRequest, IngestResult


def _deps_available() -> bool:
    try:
        import faster_whisper  # noqa: F401
        import yt_dlp  # noqa: F401

        return True
    except Exception:
        return False


class LinkIngestor:
    def is_available(self) -> bool:
        return get_settings().enable_transcription and _deps_available()

    def can_handle(self, req: IngestRequest) -> bool:
        has_transcript = bool(req.transcript and req.transcript.strip())
        return bool(req.source_url) and not has_transcript and self.is_available()

    def ingest(self, req: IngestRequest) -> IngestResult:
        if not req.source_url:
            raise ValueError("A source URL is required for transcription.")
        if not self.is_available():
            raise RuntimeError(
                "Transcription is not available. Install the 'transcribe' extra "
                "(yt-dlp, faster-whisper) and ensure ffmpeg is on PATH."
            )
        transcript = self._transcribe(req.source_url, req.source_lang)
        return IngestResult(
            transcript=transcript,
            translation=req.translation,
            source_url=req.source_url,
        )

    def _transcribe(self, url: str, lang: str = "de") -> str:
        import yt_dlp
        from faster_whisper import WhisperModel

        settings = get_settings()
        with tempfile.TemporaryDirectory() as tmp:
            template = str(Path(tmp) / "audio.%(ext)s")
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": template,
                "quiet": True,
                "noprogress": True,
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}
                ],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            audio_files = sorted(Path(tmp).glob("audio.*"))
            if not audio_files:
                raise RuntimeError("Could not download audio from the URL.")
            model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
            segments, _info = model.transcribe(str(audio_files[0]), language=lang)
            return " ".join(segment.text.strip() for segment in segments).strip()
