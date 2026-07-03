"""Course/curriculum API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from sprachheft.api.app import app
from sprachheft.db import engine
from sprachheft.models import AnswerAttempt, Exercise


def test_course_index_and_level():
    with TestClient(app) as client:
        course = client.get("/course").json()
        levels = {level["level"] for level in course["levels"]}
        assert {"A1", "A2", "B1", "B2"} <= levels

        a1 = client.get("/course/A1")
        assert a1.status_code == 200
        assert len(a1.json()["units"]) >= 1


def test_start_lesson_creates_material():
    with TestClient(app) as client:
        resp = client.post("/course/lessons/a2.dative/start")
        assert resp.status_code == 201, resp.text
        material = resp.json()
        assert material["level"] == "A2"
        assert material["transcript"]

        assert client.post("/course/lessons/does.not.exist/start").status_code == 404


def test_course_progress_counts_practiced_lessons():
    with TestClient(app) as client:
        # A started-but-not-practiced lesson does not count as completed.
        started = client.post("/course/lessons/a1.questions/start")
        assert started.status_code == 201, started.text
        progress = client.get("/course/progress").json()
        assert "a1.questions" not in progress["completed_codes"]

        # Practicing a lesson (>=1 answer attempt on its exercise) completes it.
        material = client.post("/course/lessons/a1.alphabet-pronunciation/start").json()
        with Session(engine) as session:
            exercise = Exercise(material_id=material["id"], type="fill-in-blank")
            session.add(exercise)
            session.commit()
            session.refresh(exercise)
            session.add(AnswerAttempt(exercise_id=exercise.id, correct=1, total=1))
            session.commit()

        progress = client.get("/course/progress").json()
        assert "a1.alphabet-pronunciation" in progress["completed_codes"]

        a1 = next(level for level in progress["levels"] if level["level"] == "A1")
        assert a1["lessons_completed"] >= 1
        assert a1["lessons_total"] >= a1["lessons_completed"]
        assert a1["percent"] > 0
        assert progress["total_lessons"] >= progress["completed_lessons"] >= 1
