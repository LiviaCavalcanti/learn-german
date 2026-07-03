"""Rewrite/expand material text (uses the fake LLM -> pads to >= 15 lines)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sprachheft.api.app import app


def test_rewrite_expands_to_min_lines():
    with TestClient(app) as client:
        material = client.post(
            "/materials",
            json={
                "title": "Kurz",
                "media_type": "text",
                "level": "A2",
                "transcript": "Ich fahre zur Arbeit. Ich trinke Kaffee.",
            },
        ).json()

        resp = client.post(
            f"/materials/{material['id']}/rewrite",
            json={"instructions": "länger machen", "target_lines": 15},
        )
        assert resp.status_code == 200, resp.text
        text = resp.json()["transcript"]
        assert text.count("\n") + 1 >= 15
