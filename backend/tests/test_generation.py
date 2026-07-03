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


def test_generate_variant_coexists_and_is_grouped():
    with TestClient(app) as client:
        payload = {
            "title": "Im Büro",
            "media_type": "text",
            "level": "A2",
            "transcript": "Heute arbeite ich im Büro und schreibe eine E-Mail an meine Kollegin.",
        }
        material_id = client.post("/materials", json=payload).json()["id"]
        client.post(f"/materials/{material_id}/generate", params={"stage": 2})

        exercises = client.get("/exercises", params={"material_id": material_id}).json()
        before = len(exercises)
        assert before >= 1
        original = exercises[0]

        resp = client.post(f"/exercises/{original['id']}/variant", params={"stage": 2})
        assert resp.status_code == 200, resp.text
        variant = resp.json()
        # Same slot type, saved alongside, and grouped with the original.
        assert variant["type"] == original["type"]
        assert variant["id"] != original["id"]
        assert variant["group_id"] == original["id"]
        assert variant["variant_position"] >= 1

        after = client.get("/exercises", params={"material_id": material_id}).json()
        assert len(after) == before + 1
        # The original and its variant now share one group id.
        group = [e for e in after if (e.get("group_id") or e["id"]) == original["id"]]
        assert {e["id"] for e in group} == {original["id"], variant["id"]}

        # Variant is persisted: a fresh request still returns both.
        refetched = client.get("/exercises", params={"material_id": material_id}).json()
        assert any(e["id"] == variant["id"] for e in refetched)


def test_variant_missing_exercise_returns_404():
    with TestClient(app) as client:
        resp = client.post("/exercises/999999/variant", params={"stage": 2})
        assert resp.status_code == 404


def test_generate_sections_persist_incrementally():
    with TestClient(app) as client:
        payload = {
            "title": "Staged",
            "media_type": "text",
            "level": "A2",
            "transcript": "Heute arbeite ich im Büro und trinke Kaffee mit der Kollegin.",
        }
        material_id = client.post("/materials", json=payload).json()["id"]

        # Vocabulary section first (fast, saved on its own).
        vocab_resp = client.post(
            f"/materials/{material_id}/generate", params={"section": "vocab", "stage": 2}
        )
        assert vocab_resp.status_code == 200, vocab_resp.text
        vbody = vocab_resp.json()
        assert vbody["vocab_added"] >= 1
        batches = vbody["exercise_batches"]
        assert batches >= 1
        assert len(client.get("/vocab", params={"material_id": material_id}).json()) >= 1
        # No exercises yet — only the vocab step ran.
        assert client.get("/exercises", params={"material_id": material_id}).json() == []

        # Each exercise batch persists on its own.
        total = 0
        for b in range(batches):
            r = client.post(
                f"/materials/{material_id}/generate",
                params={"section": "exercises", "batch": b, "stage": 2},
            )
            assert r.status_code == 200, r.text
            total += r.json()["exercises_added"]
        assert total >= 1
        stored = client.get("/exercises", params={"material_id": material_id}).json()
        assert len(stored) == total


def test_generate_exercises_batch_out_of_range_422():
    with TestClient(app) as client:
        payload = {"title": "Range", "level": "A2", "transcript": "Ich lerne Deutsch."}
        material_id = client.post("/materials", json=payload).json()["id"]
        resp = client.post(
            f"/materials/{material_id}/generate",
            params={"section": "exercises", "batch": 99, "stage": 2},
        )
        assert resp.status_code == 422
