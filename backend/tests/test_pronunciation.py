"""Pronunciation (text-to-speech) API.

Audio synthesis needs the optional ``phonetics`` extra (espeak-ng), so the
"real audio" assertions are skipped when it is not installed. The API contract —
``/pronunciation/status`` always answers, and ``/pronunciation/audio`` returns
either WAV audio or ``501`` — is verified regardless, and everything stays
offline.
"""

from __future__ import annotations

import os
import pathlib
import tempfile

_TMP_DB = pathlib.Path(tempfile.gettempdir()) / "sprachheft_test.sqlite"
os.environ["SPRACHHEFT_DB_PATH"] = str(_TMP_DB)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from sprachheft.api.app import app  # noqa: E402
from sprachheft.phonetics.tts import synthesize, tts_available  # noqa: E402

client = TestClient(app)

_HAS_TTS = tts_available()


def test_status_reports_availability():
    resp = client.get("/pronunciation/status")
    assert resp.status_code == 200
    assert isinstance(resp.json()["available"], bool)


def test_synthesize_empty_is_none():
    assert synthesize("") is None
    assert synthesize("   ") is None


def test_audio_endpoint_contract():
    resp = client.get("/pronunciation/audio", params={"word": "hola", "lang": "es"})
    if _HAS_TTS:
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"
        # A RIFF/WAVE header plus some samples.
        assert resp.content[:4] == b"RIFF"
        assert len(resp.content) > 44
    else:
        assert resp.status_code == 501


@pytest.mark.skipif(not _HAS_TTS, reason="phonetics extra not installed")
def test_synthesize_returns_wav_for_target_language():
    for lang, word in [("de", "Haus"), ("es", "hola"), ("fr", "bonjour")]:
        wav = synthesize(word, lang)
        assert wav is not None
        assert wav[:4] == b"RIFF"
        assert wav[8:12] == b"WAVE"
        assert len(wav) > 44
