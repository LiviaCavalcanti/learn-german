"""Pronunciation (IPA) support.

The g2p transcription itself needs the optional ``phonetics`` extra (espeak-ng
via phonemizer), so those assertions are skipped when it is not installed. The API
contract — that an ``ipa`` field is always present on dictionary and vocab
responses — is verified regardless, and everything here stays offline.
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
from sprachheft.phonetics import to_ipa  # noqa: E402

client = TestClient(app)

_HAS_PHONETICS = to_ipa("Haus") is not None


def test_to_ipa_empty_is_none():
    assert to_ipa("") is None
    assert to_ipa("   ") is None


def test_to_ipa_shape():
    result = to_ipa("sprechen")
    assert result is None or (result.startswith("/") and result.endswith("/"))


def test_vocab_response_includes_ipa_field():
    resp = client.post(
        "/vocab",
        json={"word": "sprechen", "meaning_en": "to speak", "cefr": "A2"},
    )
    assert resp.status_code == 201
    assert "ipa" in resp.json()


def test_dictionary_entries_include_ipa_field():
    resp = client.get("/dictionary/lookup", params={"word": "Haus"})
    assert resp.status_code == 200
    for entry in resp.json()["entries"]:
        assert "ipa" in entry


@pytest.mark.skipif(not _HAS_PHONETICS, reason="phonetics extra not installed")
def test_to_ipa_real_transcription():
    ipa = to_ipa("Haus")
    assert ipa is not None
    assert ipa.startswith("/") and ipa.endswith("/")
    assert len(ipa) > 2


@pytest.mark.skipif(not _HAS_PHONETICS, reason="phonetics extra not installed")
def test_vocab_response_populates_ipa():
    resp = client.post(
        "/vocab",
        json={"word": "Haus", "meaning_en": "house", "cefr": "A1"},
    )
    assert resp.status_code == 201
    assert resp.json()["ipa"]
