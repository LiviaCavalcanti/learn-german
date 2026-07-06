"""Smoke tests for the backend foundation (isolated temp database)."""

from __future__ import annotations

import os
import pathlib
import tempfile

_TMP_DB = pathlib.Path(tempfile.gettempdir()) / "sprachheft_test.sqlite"
os.environ["SPRACHHEFT_DB_PATH"] = str(_TMP_DB)
if _TMP_DB.exists():
    _TMP_DB.unlink()

from fastapi.testclient import TestClient  # noqa: E402

from sprachheft.api.app import app  # noqa: E402


def test_health():
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


def test_taxonomy_seeded():
    with TestClient(app) as client:
        resp = client.get("/taxonomy/topics")
        assert resp.status_code == 200
        topics = resp.json()
        assert len(topics) >= 40
        assert {"A1", "A2", "B1", "B2"} <= {t["cefr"] for t in topics}


def test_material_crud_and_manual_ingest():
    with TestClient(app) as client:
        payload = {
            "title": "Mein Tag",
            "media_type": "text",
            "level": "A2",
            "transcript": "  Ich stehe früh auf. Dann trinke ich Kaffee.  ",
            "translation": "I get up early. Then I drink coffee.",
        }
        resp = client.post("/materials", json=payload)
        assert resp.status_code == 201, resp.text
        material = resp.json()
        assert material["id"] > 0
        # ManualIngestor trims whitespace
        assert material["transcript"].startswith("Ich stehe früh")
        material_id = material["id"]

        resp = client.get("/materials")
        assert resp.status_code == 200
        assert any(m["id"] == material_id for m in resp.json())

        resp = client.get(f"/materials/{material_id}")
        assert resp.status_code == 200

        resp = client.delete(f"/materials/{material_id}")
        assert resp.status_code == 204

        resp = client.get(f"/materials/{material_id}")
        assert resp.status_code == 404


def test_material_update_patches_only_sent_fields():
    with TestClient(app) as client:
        created = client.post(
            "/materials",
            json={
                "title": "Alt",
                "media_type": "text",
                "level": "A2",
                "transcript": "Ursprünglicher Text.",
                "translation": "Original text.",
            },
        ).json()
        material_id = created["id"]

        resp = client.patch(
            f"/materials/{material_id}",
            json={"title": "Neu", "level": "B1", "transcript": "Bearbeiteter Text."},
        )
        assert resp.status_code == 200, resp.text
        updated = resp.json()
        assert updated["title"] == "Neu"
        assert updated["level"] == "B1"
        assert updated["transcript"] == "Bearbeiteter Text."
        # Fields not sent are left untouched.
        assert updated["translation"] == "Original text."

        assert client.patch("/materials/999999", json={"title": "x"}).status_code == 404


def test_deleting_material_removes_its_vocab_and_exercises():
    with TestClient(app) as client:
        payload = {
            "material": {"title": "Zum Löschen", "level": "A2"},
            "vocabulary": [
                {"word": "r Tisch", "lemma": "Tisch", "meaning_en": "table", "cefr": "A2"}
            ],
            "exercises": [
                {
                    "type": "fill-in-blank",
                    "instructions": "Setze ein.",
                    "payload": {"items": [{"prompt": "Der ___ ist groß."}]},
                    "answer_key": {"items": [{"answer": "Tisch"}]},
                }
            ],
        }
        material_id = client.post("/imports/json", json=payload).json()["material_id"]
        assert client.get("/vocab", params={"material_id": material_id}).json()
        assert client.get("/exercises", params={"material_id": material_id}).json()

        assert client.delete(f"/materials/{material_id}").status_code == 204

        assert client.get(f"/materials/{material_id}").status_code == 404
        assert client.get("/vocab", params={"material_id": material_id}).json() == []
        assert client.get("/exercises", params={"material_id": material_id}).json() == []


def test_manual_ingest_requires_transcript():
    with TestClient(app) as client:
        resp = client.post(
            "/materials",
            json={"title": "Empty", "media_type": "text", "level": "A1", "transcript": "   "},
        )
        assert resp.status_code == 422
