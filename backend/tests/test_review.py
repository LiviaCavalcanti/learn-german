"""Review grading (FSRS) + dashboard stats tests."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from sprachheft.api.app import app
from sprachheft.db import engine
from sprachheft.models import Exercise, VocabItem


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


def test_stats_are_scoped_per_language():
    """Dashboard stats (vocab count, reviews today, …) count only the active language."""
    with TestClient(app) as client:
        de_before = client.get("/review/stats?lang=de").json()
        es_before = client.get("/review/stats?lang=es").json()

    with Session(engine) as session:
        de_word = VocabItem(
            word="r Baum", lemma="Baum", meaning_en="tree", cefr="A1", target_lang="de"
        )
        es_word = VocabItem(
            word="el árbol", lemma="árbol", meaning_en="tree", cefr="A1", target_lang="es"
        )
        session.add(de_word)
        session.add(es_word)
        session.commit()
        session.refresh(de_word)
        session.refresh(es_word)
        de_id, es_id = de_word.id, es_word.id

    with TestClient(app) as client:
        client.post(
            "/review/grade", json={"item_type": "vocab", "item_id": de_id, "rating": "good"}
        )
        client.post(
            "/review/grade", json={"item_type": "vocab", "item_id": es_id, "rating": "good"}
        )
        de_after = client.get("/review/stats?lang=de").json()
        es_after = client.get("/review/stats?lang=es").json()

    # Each language sees exactly its own new word + its own review — never the other's.
    assert de_after["total_vocab"] - de_before["total_vocab"] == 1
    assert es_after["total_vocab"] - es_before["total_vocab"] == 1
    assert de_after["reviews_today"] - de_before["reviews_today"] == 1
    assert es_after["reviews_today"] - es_before["reviews_today"] == 1


def test_manage_cards_list_and_remove_from_review():
    with TestClient(app) as client:
        created = client.post(
            "/vocab", json={"word": "r Stuhl", "meaning_en": "chair", "cefr": "A1"}
        )
        assert created.status_code == 201, created.text
        vocab_id = created.json()["id"]

        cards = client.get("/review/cards").json()
        card = next(
            c for c in cards if c["item_type"] == "vocab" and c["item_id"] == vocab_id
        )
        assert "state" in card and "is_due" in card and "last_review" in card
        srstate_id = card["srstate_id"]

        # Remove from review only: the SR card is gone but the word remains.
        resp = client.post("/review/cards/remove", json={"srstate_ids": [srstate_id]})
        assert resp.status_code == 200, resp.text
        assert resp.json()["removed"] == 1
        assert all(c["srstate_id"] != srstate_id for c in client.get("/review/cards").json())
        assert any(v["id"] == vocab_id for v in client.get("/vocab").json())


def test_delete_card_removes_underlying_vocab():
    with TestClient(app) as client:
        vocab_id = client.post("/vocab", json={"word": "e Lampe", "meaning_en": "lamp"}).json()[
            "id"
        ]
        srstate_id = next(
            c["srstate_id"]
            for c in client.get("/review/cards").json()
            if c["item_type"] == "vocab" and c["item_id"] == vocab_id
        )
        resp = client.post("/review/cards/delete", json={"srstate_ids": [srstate_id]})
        assert resp.status_code == 200, resp.text
        assert resp.json()["deleted"] == 1
        assert all(v["id"] != vocab_id for v in client.get("/vocab").json())


def test_update_vocab_endpoint():
    with TestClient(app) as client:
        vocab_id = client.post("/vocab", json={"word": "r Hund", "meaning_en": "dog"}).json()[
            "id"
        ]
        resp = client.patch(f"/vocab/{vocab_id}", json={"meaning_en": "the dog", "cefr": "A1"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["meaning_en"] == "the dog"
        assert body["cefr"] == "A1"
        assert client.patch("/vocab/999999", json={"meaning_en": "x"}).status_code == 404


def test_update_and_delete_exercise():
    with Session(engine) as session:
        exercise = Exercise(
            type="fill-in-blank",
            instructions="Fill it in",
            payload={"items": []},
            answer_key={"items": []},
        )
        session.add(exercise)
        session.commit()
        session.refresh(exercise)
        exercise_id = exercise.id

    with TestClient(app) as client:
        # Seed an SR card for the exercise via grading.
        client.post(
            "/review/grade",
            json={"item_type": "exercise", "item_id": exercise_id, "rating": "good"},
        )

        resp = client.patch(
            f"/exercises/{exercise_id}",
            json={"instructions": "New instructions", "answer_key": {"items": [{"answer": "x"}]}},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["instructions"] == "New instructions"
        assert resp.json()["answer_key"] == {"items": [{"answer": "x"}]}
        assert client.patch("/exercises/999999", json={"instructions": "x"}).status_code == 404

        srstate_id = next(
            c["srstate_id"]
            for c in client.get("/review/cards").json()
            if c["item_type"] == "exercise" and c["item_id"] == exercise_id
        )
        resp = client.post("/review/cards/delete", json={"srstate_ids": [srstate_id]})
        assert resp.json()["deleted"] == 1
        assert all(e["id"] != exercise_id for e in client.get("/exercises").json())
