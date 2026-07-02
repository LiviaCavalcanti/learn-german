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
