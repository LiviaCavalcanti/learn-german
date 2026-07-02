"""Curriculum (A1–B2 course) loaded from content/course.json.

Lessons reference grammar topics from the taxonomy and carry a short seed text;
starting a lesson creates a Material so the generation agent can build content.
"""

from __future__ import annotations

import json
from functools import lru_cache

from sqlmodel import Session

from sprachheft.config import get_settings
from sprachheft.models import Material


@lru_cache
def _load() -> dict:
    path = get_settings().content_dir / "course.json"
    if not path.exists():
        return {"title": "German A1–B2 Course", "levels": []}
    return json.loads(path.read_text(encoding="utf-8"))


def get_course() -> dict:
    data = _load()
    levels = []
    for level in data.get("levels", []):
        units = level.get("units", [])
        levels.append(
            {
                "level": level["level"],
                "title": level.get("title", ""),
                "units": len(units),
                "lessons": sum(len(u.get("lessons", [])) for u in units),
            }
        )
    return {"title": data.get("title", ""), "levels": levels}


def get_level(level: str) -> dict | None:
    for entry in _load().get("levels", []):
        if entry["level"].lower() == level.lower():
            return entry
    return None


def get_lesson(code: str) -> dict | None:
    for level in _load().get("levels", []):
        for unit in level.get("units", []):
            for lesson in unit.get("lessons", []):
                if lesson["code"] == code:
                    return {
                        **lesson,
                        "level": level["level"],
                        "unit_title": unit.get("title", ""),
                    }
    return None


def start_lesson(session: Session, code: str) -> Material | None:
    lesson = get_lesson(code)
    if not lesson:
        return None
    material = Material(
        title=lesson["title"],
        media_type="text",
        level=lesson["level"],
        transcript=lesson.get("seed_text", ""),
        notes=f"Course lesson: {code}",
    )
    session.add(material)
    session.commit()
    session.refresh(material)
    return material
