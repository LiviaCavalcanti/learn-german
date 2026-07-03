"""Practice answer-checking + auto-grading tests."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from sprachheft.api.app import app
from sprachheft.db import engine
from sprachheft.models import Exercise, Material


def _make_exercise() -> int:
    with Session(engine) as session:
        material = Material(title="Practice", transcript="Ich bin müde.", level="A2")
        session.add(material)
        session.commit()
        session.refresh(material)
        exercise = Exercise(
            material_id=material.id,
            type="fill-in-blank",
            instructions="Setze das richtige Wort ein.",
            payload={"items": [{"prompt": "Ich ___ müde."}], "hints": []},
            answer_key={"items": [{"answer": "bin"}]},
        )
        session.add(exercise)
        session.commit()
        session.refresh(exercise)
        return exercise.id


def test_answer_correct_and_incorrect():
    exercise_id = _make_exercise()
    with TestClient(app) as client:
        resp = client.post(
            "/practice/answer", json={"exercise_id": exercise_id, "responses": ["bin"]}
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["check"]["all_correct"] is True
        assert body["graded"]["rating"] == "good"

        resp = client.post(
            "/practice/answer", json={"exercise_id": exercise_id, "responses": ["ist"]}
        )
        body = resp.json()
        assert body["check"]["all_correct"] is False
        assert body["graded"]["rating"] == "again"


def test_answer_unknown_exercise_404():
    with TestClient(app) as client:
        resp = client.post("/practice/answer", json={"exercise_id": 999999, "responses": []})
        assert resp.status_code == 404


def _make_open_exercise() -> int:
    with Session(engine) as session:
        material = Material(title="Feedback", transcript="Ich arbeite gern.", level="A2")
        session.add(material)
        session.commit()
        session.refresh(material)
        exercise = Exercise(
            material_id=material.id,
            type="writing",
            instructions="Schreibe ein paar Sätze über deinen Tag.",
            payload={"theme": "Alltag", "task": "Beschreibe deinen Arbeitstag."},
            answer_key={"model_answer": "Heute habe ich gearbeitet."},
        )
        session.add(exercise)
        session.commit()
        session.refresh(exercise)
        return exercise.id


def test_answer_feedback_returns_structured_review():
    exercise_id = _make_open_exercise()
    with TestClient(app) as client:
        resp = client.post(
            "/practice/feedback",
            json={"exercise_id": exercise_id, "answer": "Heute habe ich im Büro gearbeitet."},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["has_errors"] is False
        assert isinstance(body["errors"], list)
        assert "summary" in body


def test_answer_feedback_empty_answer_flags_error():
    exercise_id = _make_open_exercise()
    with TestClient(app) as client:
        resp = client.post(
            "/practice/feedback", json={"exercise_id": exercise_id, "answer": ""}
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["has_errors"] is True


def test_answer_feedback_unknown_exercise_404():
    with TestClient(app) as client:
        resp = client.post("/practice/feedback", json={"exercise_id": 999999, "answer": "x"})
        assert resp.status_code == 404


def test_answers_are_saved_and_retrievable():
    exercise_id = _make_exercise()
    with TestClient(app) as client:
        # No attempts yet.
        assert client.get(f"/exercises/{exercise_id}/attempts").json() == []

        client.post("/practice/answer", json={"exercise_id": exercise_id, "responses": ["ist"]})
        client.post("/practice/answer", json={"exercise_id": exercise_id, "responses": ["bin"]})

        attempts = client.get(f"/exercises/{exercise_id}/attempts").json()
        assert len(attempts) == 2
        # Newest first, full result stored so the UI can re-render it.
        assert attempts[0]["responses"] == ["bin"]
        assert attempts[0]["result"]["all_correct"] is True
        assert attempts[1]["responses"] == ["ist"]
        assert attempts[1]["result"]["all_correct"] is False


def test_empty_answer_is_not_saved():
    exercise_id = _make_exercise()
    with TestClient(app) as client:
        client.post("/practice/answer", json={"exercise_id": exercise_id, "responses": ["   "]})
        assert client.get(f"/exercises/{exercise_id}/attempts").json() == []


def test_open_answer_feedback_is_saved():
    exercise_id = _make_open_exercise()
    with TestClient(app) as client:
        client.post(
            "/practice/feedback",
            json={"exercise_id": exercise_id, "answer": "Heute habe ich gearbeitet."},
        )
        attempts = client.get(f"/exercises/{exercise_id}/attempts").json()
        assert len(attempts) == 1
        assert attempts[0]["kind"] == "feedback"
        assert attempts[0]["answer_text"] == "Heute habe ich gearbeitet."
        assert "has_errors" in attempts[0]["result"]
