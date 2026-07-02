"""Importer tests: JSON round-trip (deterministic) and text (fake LLM)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sprachheft.api.app import app


def test_import_json_persists_imported_rows():
    with TestClient(app) as client:
        payload = {
            "material": {"title": "Dativ Übung", "level": "A2", "themes": ["Dativ"]},
            "vocabulary": [
                {"word": "r Tisch", "lemma": "Tisch", "meaning_en": "table", "cefr": "A2"}
            ],
            "exercises": [
                {
                    "type": "fill-in-blank",
                    "instructions": "Setze das richtige Artikelwort ein.",
                    "payload": {"items": [{"prompt": "Ich fahre mit ___ Bus."}]},
                    "answer_key": {"items": [{"answer": "dem"}]},
                }
            ],
        }
        resp = client.post("/imports/json", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["vocab_added"] >= 1
        assert body["exercises_added"] >= 1

        material_id = body["material_id"]
        exercises = client.get("/exercises", params={"material_id": material_id}).json()
        assert any(e["source"] == "imported" for e in exercises)


def test_import_text_uses_fake_llm():
    with TestClient(app) as client:
        resp = client.post(
            "/imports/text",
            json={
                "raw_text": "Der Dativ nach 'mit'. Beispiel: mit dem Bus fahren.",
                "level": "A2",
                "title": "Dativ Notiz",
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["exercises_added"] >= 1
