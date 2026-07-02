"""Review grading (FSRS) + dashboard stats tests."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from sprachheft.api.app import app
from sprachheft.db import engine
from sprachheft.models import VocabItem


def _make_vocab() -> int:
    with Session(engine) as session:
        vocab = VocabItem(word="r Tisch", lemma="Tisch", meaning_en="table", cefr="A2")
        session.add(vocab)
        session.commit()
        session.refresh(vocab)
        return vocab.id


def test_grade_updates_state_and_stats():
    vocab_id = _make_vocab()
    with TestClient(app) as client:
        resp = client.post(
            "/review/grade",
            json={"item_type": "vocab", "item_id": vocab_id, "rating": "good"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["reps"] == 1
        assert body["due"] is not None

        # Grading again advances reps and (for 'again') lapses.
        resp = client.post(
            "/review/grade",
            json={"item_type": "vocab", "item_id": vocab_id, "rating": "again"},
        )
        body = resp.json()
        assert body["reps"] == 2
        assert body["lapses"] == 1

        stats = client.get("/review/stats").json()
        assert stats["reviews_today"] >= 2
        assert stats["total_vocab"] >= 1

        assert client.get("/review/queue").status_code == 200
