"""Verb conjugation endpoint (offline via the fake LLM regular conjugator)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sprachheft.api.app import app


def test_conjugate_regular_verb():
    with TestClient(app) as client:
        resp = client.get("/conjugation", params={"verb": "arbeiten"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["infinitive"] == "arbeiten"
        assert body["present"]["ich"] == "arbeite"
        assert body["present"]["du"] == "arbeitest"
        assert body["present"]["er_sie_es"] == "arbeitet"
        assert body["praeteritum"]["ich"] == "arbeitete"
        assert body["partizip_ii"] == "gearbeitet"
        assert body["perfekt"]["ich"] == "habe gearbeitet"
        assert body["futur1"]["ich"] == "werde arbeiten"
        assert body["imperative"]["Sie"] == "arbeiten Sie"


def test_conjugate_inflected_form_resolves_infinitive():
    """An inflected form is lemmatised to its infinitive before conjugating."""
    with TestClient(app) as client:
        resp = client.get("/conjugation", params={"verb": "habe"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["infinitive"] == "haben"
        assert body["present"]["er_sie_es"] == "hat"
        assert body["praeteritum"]["ich"] == "hatte"
        assert body["auxiliary"] == "haben"


def test_conjugate_sein_is_irregular():
    with TestClient(app) as client:
        resp = client.get("/conjugation", params={"verb": "sein"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["infinitive"] == "sein"
        assert body["present"]["ich"] == "bin"
        assert body["auxiliary"] == "sein"
        assert body["perfekt"]["ich"] == "bin gewesen"
        assert body["regular"] is False


def test_conjugate_requires_non_blank_verb():
    with TestClient(app) as client:
        assert client.get("/conjugation", params={"verb": "   "}).status_code == 400
        assert client.get("/conjugation", params={"verb": ""}).status_code == 422


def test_add_verb_to_vocab_is_deduplicated():
    with TestClient(app) as client:
        first = client.post(
            "/vocab/verb",
            json={"infinitive": "arbeiten", "english": "to work", "partizip_ii": "gearbeitet"},
        )
        assert first.status_code == 200, first.text
        body = first.json()
        assert body["created"] is True
        assert body["item"]["lemma"] == "arbeiten"
        assert body["item"]["pos"] == "verb"
        assert "verb" in body["item"]["grammar_tags"]

        # Looking the same verb up again does not create a duplicate.
        again = client.post("/vocab/verb", json={"infinitive": "arbeiten", "english": "to work"})
        assert again.status_code == 200, again.text
        assert again.json()["created"] is False
        assert again.json()["item"]["id"] == body["item"]["id"]

        # The verb is now searchable in the vocabulary.
        found = client.get("/vocab/search", params={"q": "arbeiten"}).json()
        assert any(v["lemma"] == "arbeiten" for v in found)


def test_add_verb_requires_infinitive():
    with TestClient(app) as client:
        assert client.post("/vocab/verb", json={"infinitive": "  "}).status_code == 422
