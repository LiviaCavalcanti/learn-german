"""Tests for vocabulary search and topic summaries."""

from __future__ import annotations

import os
import pathlib
import tempfile

_TMP_DB = pathlib.Path(tempfile.gettempdir()) / "sprachheft_test.sqlite"
os.environ["SPRACHHEFT_DB_PATH"] = str(_TMP_DB)

from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session  # noqa: E402

from sprachheft.api.app import app  # noqa: E402
from sprachheft.db import engine  # noqa: E402
from sprachheft.models import VocabItem  # noqa: E402


def _seed_vocab() -> None:
    with Session(engine) as session:
        session.add(
            VocabItem(
                word="r Bahnhof",
                lemma="Bahnhof",
                pos="noun",
                meaning_en="train station",
                cefr="A2",
                grammar_tags=["a2.dative"],
            )
        )
        session.add(
            VocabItem(
                word="abfragen",
                lemma="abfragen",
                pos="verb",
                meaning_en="to query data or models",
                cefr="B1",
                grammar_tags=["b1.passive"],
            )
        )
        session.commit()


def test_vocab_search_and_topics():
    with TestClient(app) as client:  # lifespan creates tables + seeds taxonomy
        _seed_vocab()

        resp = client.get("/vocab/search", params={"q": "station"})
        assert resp.status_code == 200
        assert any(v["lemma"] == "Bahnhof" for v in resp.json())

        resp = client.get("/vocab/search", params={"q": "query", "tag": "b1.passive"})
        assert resp.status_code == 200
        assert any(v["lemma"] == "abfragen" for v in resp.json())

        resp = client.get("/vocab/topics")
        assert resp.status_code == 200
        topics = {t["topic"]: t for t in resp.json()["topics"]}
        assert "a2.dative" in topics
        assert topics["a2.dative"]["count"] >= 1


def test_semantic_search():
    with TestClient(app) as client:
        _seed_vocab()
        assert client.post("/vocab/reindex").status_code == 200
        results = client.get(
            "/vocab/search", params={"q": "railway station", "semantic": "true"}
        ).json()
        assert isinstance(results, list)
        assert len(results) >= 1


def test_compose_material_from_vocab():
    with TestClient(app) as client:
        _seed_vocab()
        ids = [v["id"] for v in client.get("/vocab").json()][:2]
        assert ids

        resp = client.post("/vocab/compose", json={"vocab_ids": ids, "level": "A2"})
        assert resp.status_code == 201
        body = resp.json()
        assert body["material_id"] > 0
        assert body["title"]
        assert body["vocab_added"] >= 1
        assert body["exercises_added"] >= 1

        material_id = body["material_id"]
        material = client.get(f"/materials/{material_id}").json()
        assert material["transcript"].strip()
        assert material["media_type"] == "text"

        exercises = client.get(f"/exercises?material_id={material_id}").json()
        assert len(exercises) >= 1

        vocab = client.get("/vocab", params={"material_id": material_id}).json()
        assert len(vocab) >= 1


def test_compose_requires_selection():
    with TestClient(app) as client:
        resp = client.post("/vocab/compose", json={"vocab_ids": []})
        assert resp.status_code == 422


def test_delete_vocab_items():
    with TestClient(app) as client:
        _seed_vocab()
        ids = [v["id"] for v in client.get("/vocab").json()]
        assert len(ids) >= 1
        target = ids[0]

        # Give the word SR state + a review log + an embedding to clean up.
        assert client.post("/vocab/reindex").status_code == 200
        client.post(
            "/review/grade", json={"item_type": "vocab", "item_id": target, "rating": "good"}
        )

        resp = client.post("/vocab/delete", json={"ids": [target]})
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 1

        remaining = [v["id"] for v in client.get("/vocab").json()]
        assert target not in remaining

        # Deleting an unknown id is a no-op, not an error.
        resp = client.post("/vocab/delete", json={"ids": [target]})
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 0
