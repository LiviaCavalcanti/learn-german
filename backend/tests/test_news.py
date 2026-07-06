"""Offline tests for the news importer: source listing + a network-mocked import."""

from __future__ import annotations

import os
import pathlib
import tempfile

_TMP_DB = pathlib.Path(tempfile.gettempdir()) / "sprachheft_test.sqlite"
os.environ.setdefault("SPRACHHEFT_DB_PATH", str(_TMP_DB))
os.environ.setdefault("SPRACHHEFT_LLM_MODEL", "fake")

from fastapi.testclient import TestClient  # noqa: E402

from sprachheft.api.app import app  # noqa: E402


def test_news_sources_lists_known_feeds():
    with TestClient(app) as client:
        resp = client.get("/news/sources")
        assert resp.status_code == 200
        body = resp.json()
        assert "available" in body
        keys = {s["key"] for s in body["sources"]}
        assert {"nachrichtenleicht", "dw"} <= keys


def test_news_import_creates_material(monkeypatch):
    """A mocked fetch/translate must produce a real Material (no network, fake LLM)."""
    import sprachheft.api.news as api_news
    from sprachheft import news

    monkeypatch.setattr(api_news, "deps_available", lambda: True)
    monkeypatch.setattr(
        news,
        "fetch_article",
        lambda url: ("Eine Schlagzeile", "Das ist ein kurzer deutscher Text. Er hat zwei Sätze."),
    )
    monkeypatch.setattr(
        news, "translate_text", lambda text, source="de", target="en": "A short German text."
    )

    with TestClient(app) as client:
        resp = client.post(
            "/news/import",
            json={
                "source": "nachrichtenleicht",
                "url": "https://example.com/eine-schlagzeile-1.html",
                "generate": False,
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["material_id"] > 0
        assert body["title"] == "Eine Schlagzeile"
        assert body["translated"] is True

        mat = client.get(f"/materials/{body['material_id']}").json()
        assert mat["transcript"].startswith("Das ist ein kurzer")
        assert mat["translation"] == "A short German text."
        assert mat["source_url"].endswith("eine-schlagzeile-1.html")
