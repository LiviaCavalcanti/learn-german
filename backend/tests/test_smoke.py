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


def test_manual_ingest_requires_transcript():
    with TestClient(app) as client:
        resp = client.post(
            "/materials",
            json={"title": "Empty", "media_type": "text", "level": "A1", "transcript": "   "},
        )
        assert resp.status_code == 422
