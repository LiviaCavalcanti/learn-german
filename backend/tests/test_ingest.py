"""Ingestion (transcription) API tests — graceful when deps are absent."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sprachheft.api.app import app


def test_ingest_status_and_transcribe_guard():
    with TestClient(app) as client:
        status = client.get("/ingest/status").json()
        assert "transcription_available" in status

        if not status["transcription_available"]:
            resp = client.post(
                "/ingest/transcribe", json={"source_url": "https://example.com/video"}
            )
            assert resp.status_code == 501
