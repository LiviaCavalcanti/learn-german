"""Curriculum (A1–B2 course) loaded from content/course.json.

Lessons reference grammar topics from the taxonomy and carry a short seed text;
starting a lesson creates a Material so the generation agent can build content.
"""

from __future__ import annotations

import json
from functools import lru_cache

from sqlmodel import Session, select

from sprachheft.config import get_settings
from sprachheft.models import AnswerAttempt, Exercise, Material

LESSON_NOTE_PREFIX = "Course lesson: "


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
        notes=f"{LESSON_NOTE_PREFIX}{code}",
    )
    session.add(material)
    session.commit()
    session.refresh(material)
    return material


def get_progress(session: Session) -> dict:
    """Per-level lesson completion derived from existing data (no schema change).

    A lesson counts as "completed" once at least one of its generated exercises
    has an answer attempt. The only link from a lesson to its material is
    ``Material.notes == f"{LESSON_NOTE_PREFIX}{code}"`` (set by ``start_lesson``).
    """
    material_to_code: dict[int, str] = {}
    rows = session.exec(
        select(Material.id, Material.notes).where(Material.notes.like(f"{LESSON_NOTE_PREFIX}%"))
    ).all()
    for material_id, notes in rows:
        if material_id is not None and notes and notes.startswith(LESSON_NOTE_PREFIX):
            material_to_code[material_id] = notes[len(LESSON_NOTE_PREFIX) :]

    attempted_exercise_ids = set(session.exec(select(AnswerAttempt.exercise_id)).all())
    practiced_material_ids: set[int] = set()
    if attempted_exercise_ids:
        practiced_material_ids = {
            material_id
            for material_id in session.exec(
                select(Exercise.material_id).where(Exercise.id.in_(attempted_exercise_ids))
            ).all()
            if material_id is not None
        }

    completed_codes = {
        code
        for material_id, code in material_to_code.items()
        if material_id in practiced_material_ids
    }

    levels: list[dict] = []
    total_lessons = 0
    completed_lessons = 0
    for level in _load().get("levels", []):
        codes = [
            lesson["code"] for unit in level.get("units", []) for lesson in unit.get("lessons", [])
        ]
        done = sum(1 for code in codes if code in completed_codes)
        total_lessons += len(codes)
        completed_lessons += done
        levels.append(
            {
                "level": level["level"],
                "title": level.get("title", ""),
                "lessons_total": len(codes),
                "lessons_completed": done,
                "percent": round(done / len(codes) * 100) if codes else 0,
            }
        )

    return {
        "levels": levels,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "percent": round(completed_lessons / total_lessons * 100) if total_lessons else 0,
        "completed_codes": sorted(completed_codes),
    }
