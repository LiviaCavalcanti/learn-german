"""Teacher chat (tutor) tests — offline via the fake LLM."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sprachheft.api.app import app


def test_chat_session_flow_and_messages_persist():
    with TestClient(app) as client:
        created = client.post("/tutor/sessions", json={"title": "Grammar help"})
        assert created.status_code == 201, created.text
        chat_id = created.json()["id"]

        resp = client.post(
            f"/tutor/sessions/{chat_id}/messages",
            json={"message": "Wie benutze ich den Dativ?"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["user_message"]["role"] == "user"
        assert body["teacher_message"]["role"] == "teacher"
        assert body["teacher_message"]["content"].strip()

        detail = client.get(f"/tutor/sessions/{chat_id}").json()
        assert len(detail["messages"]) == 2
        assert any(s["id"] == chat_id for s in client.get("/tutor/sessions").json())


def test_chat_with_material_context():
    with TestClient(app) as client:
        material = client.post(
            "/materials",
            json={"title": "Mein Tag", "level": "A2", "transcript": "Ich arbeite im Büro."},
        ).json()
        resp = client.post(
            "/tutor/sessions",
            json={"context": {"kind": "material", "id": material["id"], "label": "Mein Tag"}},
        )
        chat_id = resp.json()["id"]
        turn = client.post(
            f"/tutor/sessions/{chat_id}/messages",
            json={"message": "Kannst du mir den Text erklären?"},
        )
        assert turn.status_code == 200, turn.text
        assert turn.json()["teacher_message"]["content"].strip()


def test_suggest_and_add_card_to_review():
    with TestClient(app) as client:
        suggestion = client.post(
            "/tutor/cards/suggest",
            json={"text": "Der Dativ folgt auf 'mit'. Beispiel: Ich fahre mit dem Bus."},
        )
        assert suggestion.status_code == 200, suggestion.text
        card = suggestion.json()
        assert card["front"] and card["back"]

        created = client.post(
            "/tutor/cards",
            json={"front": card["front"], "back": card["back"], "cefr": "A2", "tags": ["dativ"]},
        )
        assert created.status_code == 201, created.text
        exercise_id = created.json()["exercise_id"]

        # The new flashcard shows up as a review card of type 'flashcard'.
        cards = client.get("/review/cards?item_type=exercise").json()
        match = next(c for c in cards if c["item_id"] == exercise_id)
        assert match["item"]["type"] == "flashcard"


def test_profile_updates_endpoint():
    with TestClient(app) as client:
        chat_id = client.post("/tutor/sessions", json={}).json()["id"]
        client.post(
            f"/tutor/sessions/{chat_id}/messages", json={"message": "Ich lernen Deutsch."}
        )
        profile = client.get("/tutor/profile")
        assert profile.status_code == 200, profile.text
        body = profile.json()
        assert "strengths" in body and "difficulties" in body


def test_create_card_requires_front_and_back():
    with TestClient(app) as client:
        resp = client.post("/tutor/cards", json={"front": "", "back": ""})
        assert resp.status_code == 400
