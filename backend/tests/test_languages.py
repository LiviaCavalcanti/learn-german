"""Multi-language plumbing: registry, per-language course/taxonomy, and scoping.

All offline (fake LLM, temp DB). Verifies that a second target language (Spanish)
is available end-to-end and that materials/vocab/taxonomy are language-scoped.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from sprachheft.api.app import app


def test_languages_endpoint_lists_available_targets():
    with TestClient(app) as client:
        body = client.get("/languages").json()
        codes = {t["code"] for t in body["targets"]}
        assert {"de", "es"} <= codes
        assert any(n["code"] == "en" for n in body["natives"])
        es = next(t for t in body["targets"] if t["code"] == "es")
        assert es["level_framework"] == "CEFR"
        assert es["has_conjugation"] is True


def test_spanish_course_loads_with_spanish_codes():
    with TestClient(app) as client:
        course = client.get("/course", params={"lang": "es"}).json()
        assert "A1" in {lvl["level"] for lvl in course["levels"]}
        a1 = client.get("/course/A1", params={"lang": "es"}).json()
        first = a1["units"][0]["lessons"][0]["code"]
        assert first.startswith("es.")


def test_start_spanish_lesson_sets_language_and_scopes_materials():
    with TestClient(app) as client:
        started = client.post(
            "/course/lessons/es.a1.ser-estar/start",
            params={"lang": "es", "native": "en"},
        )
        assert started.status_code == 201, started.text
        material = started.json()
        assert material["source_lang"] == "es"
        assert material["native_lang"] == "en"
        mid = material["id"]

        es_ids = {m["id"] for m in client.get("/materials", params={"lang": "es"}).json()}
        de_ids = {m["id"] for m in client.get("/materials", params={"lang": "de"}).json()}
        assert mid in es_ids
        assert mid not in de_ids


def test_spanish_taxonomy_seeded_and_scoped():
    with TestClient(app) as client:
        topics = client.get("/taxonomy/topics", params={"lang": "es"}).json()
        assert topics, "expected Spanish grammar topics"
        assert all(t["target_lang"] == "es" for t in topics)
        assert any(t["code"].startswith("es.") for t in topics)


def test_vocab_is_language_scoped():
    with TestClient(app) as client:
        client.post(
            "/vocab",
            json={"word": "hola", "meaning_en": "hello", "target_lang": "es"},
        )
        es_words = {v["word"] for v in client.get("/vocab", params={"lang": "es"}).json()}
        de_words = {v["word"] for v in client.get("/vocab", params={"lang": "de"}).json()}
        assert "hola" in es_words
        assert "hola" not in de_words


def test_french_advanced_course_exposes_c1_c2():
    with TestClient(app) as client:
        course = client.get("/course", params={"lang": "fr"}).json()
        levels = {lvl["level"] for lvl in course["levels"]}
        assert {"C1", "C2"} <= levels

        c1 = client.get("/course/C1", params={"lang": "fr"}).json()
        first = c1["units"][0]["lessons"][0]["code"]
        assert first.startswith("fr.c1.")


def test_french_c1_lesson_is_rich_and_strips_answers():
    with TestClient(app) as client:
        lesson = client.get(
            "/course/lessons/fr.c1.subjonctif-present", params={"lang": "fr"}
        ).json()
        # Rich lessons ship an authored story and comprehension questions...
        assert lesson.get("story")
        assert lesson.get("questions")
        # ...but the public endpoint must not leak model answers or graded exercises.
        assert all("reference" not in q for q in lesson["questions"])
        assert not lesson.get("exercises")


def test_start_french_c2_lesson_sets_level_and_language():
    with TestClient(app) as client:
        started = client.post(
            "/course/lessons/fr.c2.discours-politique/start",
            params={"lang": "fr", "native": "en"},
        )
        assert started.status_code == 201, started.text
        material = started.json()
        assert material["source_lang"] == "fr"
        assert material["level"] == "C2"
        assert material["transcript"]


def test_french_taxonomy_seeds_c1_c2_topics():
    with TestClient(app) as client:
        topics = client.get("/taxonomy/topics", params={"lang": "fr"}).json()
        cefr = {t["cefr"] for t in topics}
        assert {"C1", "C2"} <= cefr
        assert all(t["code"].startswith("fr.") for t in topics)
