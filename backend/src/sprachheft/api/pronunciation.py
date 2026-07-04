"""Pronunciation (text-to-speech) API: offline audio for a word in the target language.

Uses the bundled espeak-ng library (the ``phonetics`` extra) so a word is spoken
in the language being learned regardless of the voices installed on the learner's
device. Returns ``501`` when the extra is unavailable — mirroring the optional
``/ingest/transcribe`` endpoint — so the frontend can fall back to the browser's
Web Speech API.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response

from sprachheft.languages import normalize_target
from sprachheft.phonetics.tts import synthesize, tts_available

router = APIRouter(prefix="/pronunciation", tags=["pronunciation"])


@router.get("/status")
def status() -> dict:
    """Report whether offline speech synthesis is available."""
    return {"available": tts_available()}


@router.get("/audio")
def audio(
    word: str = Query(..., min_length=1, max_length=200),
    lang: str = Query("de"),
) -> Response:
    """Return WAV audio of ``word`` pronounced in the ``lang`` target language."""
    if not tts_available():
        raise HTTPException(
            status_code=501,
            detail="Pronunciation audio is unavailable (install the 'phonetics' extra).",
        )
    wav = synthesize(word, normalize_target(lang))
    if wav is None:
        raise HTTPException(status_code=422, detail="Could not synthesize audio for that word.")
    return Response(
        content=wav,
        media_type="audio/wav",
        headers={"Cache-Control": "public, max-age=86400"},
    )
