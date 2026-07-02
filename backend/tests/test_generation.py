"""End-to-end generation test using the offline FakeLLMClient."""

from __future__ import annotations

import os
import pathlib
import tempfile

_TMP_DB = pathlib.Path(tempfile.gettempdir()) / "sprachheft_test.sqlite"
os.environ["SPRACHHEFT_DB_PATH"] = str(_TMP_DB)
os.environ["SPRACHHEFT_LLM_MODEL"] = "fake"

# Ensure config/llm caches pick up the fake model regardless of import order.
from sprachheft.config import get_settings  # noqa: E402
from sprachheft.llm.factory import get_llm_client  # noqa: E402

get_settings.cache_clear()
get_llm_client.cache_clear()

from fastapi.testclient import TestClient  # noqa: E402

from sprachheft.api.app import app  # noqa: E402


def test_generate_creates_vocab_and_exercises():
    with TestClient(app) as client:
        payload = {
            "title": "Mein Arbeitstag",
            "media_type": "text",
            "level": "A2",
            "transcript": (
                "Heute arbeite ich im Büro. Ich trinke Kaffee und schreibe "
                "eine E-Mail an meine Kollegin."
            ),
            "translation": "Today I work in the office. I drink coffee and write an email.",
        }
        resp = client.post("/materials", json=payload)
        assert resp.status_code == 201, resp.text
        material_id = resp.json()["id"]

        resp = client.post(f"/materials/{material_id}/generate", params={"stage": 2})
        assert resp.status_code == 200, resp.text
        summary = resp.json()
        assert summary["vocab_added"] >= 1
        assert summary["exercises_added"] >= 1

        resp = client.get("/exercises", params={"material_id": material_id})
        assert resp.status_code == 200
        exercises = resp.json()
        assert len(exercises) >= 1
        for exercise in exercises:
            assert "payload" in exercise
            assert "answer_key" in exercise
            assert exercise["type"] in {
                "fill-in-blank",
                "conjugation",
                "translation",
                "multiple-choice",
                "reorder",
                "reading",
                "interpretation",
                "writing",
            }

        resp = client.get("/vocab", params={"material_id": material_id})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
