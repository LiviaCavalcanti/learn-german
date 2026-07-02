"""Course/curriculum API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sprachheft.api.app import app


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
