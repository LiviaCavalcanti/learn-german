"""Verb conjugation endpoint (offline via the fake LLM regular conjugator)."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from sprachheft.api.app import app


def _form(body: dict, tense_name: str, label: str) -> str | None:
    """Read one conjugated form from the generic tenses/cells structure."""
    for tense in body.get("tenses", []):
        if tense["name"] == tense_name:
            for cell in tense["cells"]:
                if cell["label"] == label:
                    return cell["form"]
    return None


def test_conjugate_regular_verb():
    with TestClient(app) as client:
        resp = client.get("/conjugation", params={"verb": "arbeiten"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["infinitive"] == "arbeiten"
        assert body["language"] == "de"
        assert _form(body, "Präsens", "ich") == "arbeite"
        assert _form(body, "Präsens", "du") == "arbeitest"
        assert _form(body, "Präsens", "er/sie/es") == "arbeitet"
        assert _form(body, "Präteritum", "ich") == "arbeitete"
        assert body["partizip_ii"] == "gearbeitet"
        assert _form(body, "Perfekt", "ich") == "habe gearbeitet"
        assert _form(body, "Futur I", "ich") == "werde arbeiten"
        assert _form(body, "Imperativ", "Sie") == "arbeiten Sie"


def test_conjugate_inflected_form_resolves_infinitive():
    """An inflected form is lemmatised to its infinitive before conjugating."""
    with TestClient(app) as client:
        resp = client.get("/conjugation", params={"verb": "habe"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["infinitive"] == "haben"
        assert _form(body, "Präsens", "er/sie/es") == "hat"
        assert _form(body, "Präteritum", "ich") == "hatte"
        assert body["auxiliary"] == "haben"


def test_conjugate_sein_is_irregular():
    with TestClient(app) as client:
        resp = client.get("/conjugation", params={"verb": "sein"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["infinitive"] == "sein"
        assert _form(body, "Präsens", "ich") == "bin"
        assert body["auxiliary"] == "sein"
        assert _form(body, "Perfekt", "ich") == "bin gewesen"
        assert body["regular"] is False


def test_conjugate_other_language_uses_stub():
    """A non-German target returns a valid (stub) table offline, tagged by language."""
    with TestClient(app) as client:
        resp = client.get("/conjugation", params={"verb": "hablar", "lang": "es"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["language"] == "es"
        assert body["tenses"], "expected at least one tense"
        assert body["tenses"][0]["cells"], "expected person cells"


def test_conjugate_requires_non_blank_verb():
    with TestClient(app) as client:
        assert client.get("/conjugation", params={"verb": "   "}).status_code == 400
        assert client.get("/conjugation", params={"verb": ""}).status_code == 422


def test_add_verb_to_vocab_is_deduplicated():
    # The test DB persists across runs, so use a verb unique to this run.
    verb = f"testverb{uuid.uuid4().hex[:8]}en"
    with TestClient(app) as client:
        first = client.post(
            "/vocab/verb",
            json={"infinitive": verb, "english": "to test", "partizip_ii": "getestet"},
        )
        assert first.status_code == 200, first.text
        body = first.json()
        assert body["created"] is True
        assert body["item"]["lemma"] == verb.lower()
        assert body["item"]["pos"] == "verb"
        assert "verb" in body["item"]["grammar_tags"]

        # Looking the same verb up again does not create a duplicate.
        again = client.post("/vocab/verb", json={"infinitive": verb, "english": "to test"})
        assert again.status_code == 200, again.text
        assert again.json()["created"] is False
        assert again.json()["item"]["id"] == body["item"]["id"]

        # The verb is now searchable in the vocabulary.
        found = client.get("/vocab/search", params={"q": verb}).json()
        assert any(v["lemma"] == verb.lower() for v in found)


def test_add_verb_requires_infinitive():
    with TestClient(app) as client:
        assert client.post("/vocab/verb", json={"infinitive": "  "}).status_code == 422
