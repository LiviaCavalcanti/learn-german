"""Tests for the new features: vocab-only review, difficulty replace, and
authored lesson content (intro + story + reference-checked questions).

All offline (fake LLM, temp DB) per conftest.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from sprachheft.api.app import app
from sprachheft.db import engine
from sprachheft.models import Exercise, Material, SRState, utcnow
from sprachheft.services.review import purge_exercise_review_cards

_TRANSCRIPT = "Ich arbeite gern im Büro. Der Kaffee ist gut und der Tag ist schön."


def _material(session: Session) -> Material:
    material = Material(title="M", transcript=_TRANSCRIPT, level="A2")
    session.add(material)
    session.commit()
    session.refresh(material)
    return material


# --- Review is vocab-only ----------------------------------------------------
def test_review_queue_excludes_exercises():
    with Session(engine) as session:
        material = _material(session)
        exercise = Exercise(
            material_id=material.id, type="fill-in-blank", answer_key={"items": [{"answer": "x"}]}
        )
        session.add(exercise)
        session.commit()
        session.refresh(exercise)
        # Simulate a legacy exercise review card that must never surface.
        session.add(SRState(item_type="exercise", item_id=exercise.id, due=utcnow()))
        session.commit()
    with TestClient(app) as client:
        queue = client.get("/review/queue").json()
        assert all(item["item_type"] == "vocab" for item in queue)


def test_purge_exercise_review_cards_removes_them():
    with Session(engine) as session:
        material = _material(session)
        exercise = Exercise(material_id=material.id, type="reading")
        session.add(exercise)
        session.commit()
        session.refresh(exercise)
        session.add(SRState(item_type="exercise", item_id=exercise.id, due=utcnow()))
        session.commit()

        assert purge_exercise_review_cards(session) >= 1
        remaining = session.exec(select(SRState).where(SRState.item_type == "exercise")).all()
        assert remaining == []


def test_generated_exercises_are_not_seeded_into_review():
    with TestClient(app) as client:
        material = client.post(
            "/materials", json={"title": "Gen", "level": "A2", "transcript": _TRANSCRIPT}
        ).json()
        client.post(f"/materials/{material['id']}/generate?section=exercises&batch=0&stage=2")
        exercises = client.get(f"/exercises?material_id={material['id']}").json()
        assert exercises
    with Session(engine) as session:
        ids = [e["id"] for e in exercises]
        states = session.exec(
            select(SRState).where(SRState.item_type == "exercise", SRState.item_id.in_(ids))
        ).all()
        assert states == []


# --- Too hard / too easy: replace at difficulty ------------------------------
def test_exercise_replace_keeps_slot_and_type():
    with TestClient(app) as client:
        material = client.post(
            "/materials", json={"title": "R", "level": "A2", "transcript": _TRANSCRIPT}
        ).json()
        client.post(f"/materials/{material['id']}/generate?section=exercises&batch=0&stage=2")
        exercise = client.get(f"/exercises?material_id={material['id']}").json()[0]

        resp = client.post(f"/exercises/{exercise['id']}/replace?direction=easier")
        assert resp.status_code == 200, resp.text
        replaced = resp.json()
        assert replaced["id"] == exercise["id"]  # replaced in place (same slot)
        assert replaced["type"] == exercise["type"]  # same exercise type


def test_vocab_replace_keeps_id_and_needs_material():
    with TestClient(app) as client:
        material = client.post(
            "/materials", json={"title": "V", "level": "A2", "transcript": _TRANSCRIPT}
        ).json()
        client.post(f"/materials/{material['id']}/generate?section=vocab&batch=0&stage=2")
        vocab = client.get(f"/vocab?material_id={material['id']}").json()
        assert vocab
        resp = client.post(f"/vocab/{vocab[0]['id']}/replace?direction=harder")
        assert resp.status_code == 200, resp.text
        assert resp.json()["id"] == vocab[0]["id"]

        # A manually added word has no source material -> cannot regenerate.
        manual = client.post("/vocab", json={"word": "r Baum", "meaning_en": "tree"}).json()
        assert client.post(f"/vocab/{manual['id']}/replace?direction=easier").status_code == 422


# --- Authored lesson content + reference-checked questions --------------------
def test_lesson_exposes_intro_story_questions_without_reference():
    with TestClient(app) as client:
        lesson = client.get("/course/lessons/a1.sein-haben").json()
        assert lesson["intro"]
        assert len(lesson["story"].split()) >= 500
        assert len(lesson["questions"]) == 8
        for question in lesson["questions"]:
            assert question["prompt"] and question["translation"]
            assert "reference" not in question  # never leaked to the client


def test_start_lesson_uses_story_as_transcript():
    with TestClient(app) as client:
        material = client.post("/course/lessons/a1.sein-haben/start").json()
        assert len(material["transcript"].split()) >= 500


def test_start_lesson_is_idempotent_and_ships_grammar_exercises():
    with TestClient(app) as client:
        first = client.post("/course/lessons/a1.questions/start").json()
        second = client.post("/course/lessons/a1.questions/start").json()
        assert first["id"] == second["id"]  # reused — no duplicate library copies

        exercises = client.get(f"/exercises?material_id={first['id']}").json()
        course_ex = [e for e in exercises if e["source"] == "course"]
        # Fixed, auto-graded grammar drills ship with the lesson (no AI needed)...
        assert {"fill-in-blank", "multiple-choice", "reorder"} <= {e["type"] for e in course_ex}
        # ...and re-starting does not duplicate them.
        assert len(course_ex) == 5

        # A shipped fill-in-blank drill grades correctly via the normal path.
        blank = next(e for e in course_ex if e["type"] == "fill-in-blank")
        answer = blank["answer_key"]["items"][0]["answer"]
        checked = client.post(
            "/practice/answer", json={"exercise_id": blank["id"], "responses": [answer]}
        ).json()
        assert checked["check"]["all_correct"] is True


def test_lesson_check_returns_verdict_and_reference():
    with TestClient(app) as client:
        resp = client.post(
            "/course/lessons/a1.sein-haben/check",
            json={"index": 1, "answer": "Ihr Mann heißt Tom und er ist Lehrer."},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["verdict"] in {"correct", "partial", "incorrect", "unanswered"}
        assert body["reference"]  # authored reference revealed after checking

        missing = client.post(
            "/course/lessons/a1.sein-haben/check", json={"index": 99, "answer": "x"}
        )
        assert missing.status_code == 404


def test_practice_feedback_includes_verdict_and_reference():
    with Session(engine) as session:
        material = _material(session)
        exercise = Exercise(
            material_id=material.id,
            type="writing",
            instructions="Schreibe ein paar Sätze.",
            answer_key={"model_answer": "Ich arbeite gern im Büro."},
        )
        session.add(exercise)
        session.commit()
        session.refresh(exercise)
        exercise_id = exercise.id
    with TestClient(app) as client:
        body = client.post(
            "/practice/feedback",
            json={"exercise_id": exercise_id, "answer": "Ich arbeite gern im Büro."},
        ).json()
        assert body["verdict"] in {"correct", "partial", "incorrect", "unanswered"}
        assert body["reference"] == "Ich arbeite gern im Büro."
