"""Curriculum (A1–B2 course) loaded from content/<lang>/course.json.

Lessons reference grammar topics from the taxonomy and carry a short seed text;
starting a lesson creates a Material so the generation agent can build content.
Each target language has its own course file under ``content/<lang>/``.
"""

from __future__ import annotations

import json
from functools import lru_cache

from sqlmodel import Session, select

from sprachheft.config import get_settings
from sprachheft.languages import get_language, normalize_native, normalize_target
from sprachheft.models import AnswerAttempt, Exercise, Material

LESSON_NOTE_PREFIX = "Course lesson: "


@lru_cache
def _load(lang: str = "de") -> dict:
    profile = get_language(lang)
    path = get_settings().content_dir / profile.content_dir / "course.json"
    if not path.exists():
        return {"title": f"{profile.name} A1–B2 Course", "levels": []}
    return json.loads(path.read_text(encoding="utf-8"))


def get_course(lang: str = "de") -> dict:
    data = _load(normalize_target(lang))
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


def get_level(level: str, lang: str = "de") -> dict | None:
    for entry in _load(normalize_target(lang)).get("levels", []):
        if entry["level"].lower() == level.lower():
            return entry
    return None


def get_lesson(code: str, lang: str = "de") -> dict | None:
    for level in _load(normalize_target(lang)).get("levels", []):
        for unit in level.get("units", []):
            for lesson in unit.get("lessons", []):
                if lesson["code"] == code:
                    return {
                        **lesson,
                        "level": level["level"],
                        "unit_title": unit.get("title", ""),
                    }
    return None


def start_lesson(
    session: Session, code: str, lang: str = "de", native: str = "en"
) -> Material | None:
    target = normalize_target(lang)
    lesson = get_lesson(code, target)
    if not lesson:
        return None
    note = f"{LESSON_NOTE_PREFIX}{code}"
    # Idempotent: reuse the material already started for this lesson so re-opening a
    # lesson never piles up duplicate copies in the library.
    material = session.exec(
        select(Material).where(Material.notes == note, Material.source_lang == target)
    ).first()
    if material is None:
        material = Material(
            title=lesson["title"],
            media_type="text",
            source_lang=target,
            native_lang=normalize_native(native),
            level=lesson["level"],
            transcript=lesson.get("story") or lesson.get("seed_text", ""),
            notes=note,
        )
        session.add(material)
        session.commit()
        session.refresh(material)
    _ensure_lesson_exercises(session, material, lesson)
    return material


def _ensure_lesson_exercises(session: Session, material: Material, lesson: dict) -> int:
    """Create the lesson's authored grammar exercises as Exercise rows (once).

    These fixed, auto-graded drills ship with the lesson, so a lesson has grammar
    practice immediately without needing the LLM. Idempotent: it skips if the
    lesson's course exercises already exist for this material.
    """
    authored = lesson.get("exercises")
    if not isinstance(authored, list) or not authored:
        return 0
    already = session.exec(
        select(Exercise).where(
            Exercise.material_id == material.id, Exercise.source == "course"
        )
    ).first()
    if already is not None:
        return 0
    added = 0
    for item in authored:
        if not isinstance(item, dict) or not item.get("type"):
            continue
        session.add(
            Exercise(
                material_id=material.id,
                target_lang=material.source_lang,
                source="course",
                type=item["type"],
                cefr=item.get("cefr") or material.level,
                grammar_tags=item.get("grammar_tags") or [],
                instructions=item.get("instructions", ""),
                payload=item.get("payload") or {},
                answer_key=item.get("answer_key") or {},
            )
        )
        added += 1
    if added:
        session.commit()
    return added


def check_answer(
    code: str, index: int, answer: str, lang: str = "de", native: str = "en"
):
    """Evaluate a learner's answer to a lesson comprehension question vs its reference.

    Returns an ``AnswerFeedback`` (verdict + score + language notes), or ``None`` if the
    lesson or question index is unknown. The authored reference answer stays server-side.
    """
    target = normalize_target(lang)
    lesson = get_lesson(code, target)
    if not lesson:
        return None
    questions = lesson.get("questions") or []
    if not isinstance(questions, list) or not 0 <= index < len(questions):
        return None
    question = questions[index] or {}

    from sprachheft.agents.feedback import evaluate_open

    return evaluate_open(
        question=str(question.get("prompt", "")),
        reference=str(question.get("reference", "")),
        answer=answer,
        target_lang=target,
        native_lang=normalize_native(native),
        level=str(lesson.get("level", "A2")),
        exercise_type="reading",
    )


def get_progress(session: Session, lang: str = "de") -> dict:
    """Per-level lesson completion derived from existing data (no schema change).

    A lesson counts as "completed" once at least one of its generated exercises
    has an answer attempt. The only link from a lesson to its material is
    ``Material.notes == f"{LESSON_NOTE_PREFIX}{code}"`` (set by ``start_lesson``).
    """
    target = normalize_target(lang)
    material_to_code: dict[int, str] = {}
    rows = session.exec(
        select(Material.id, Material.notes).where(
            Material.notes.like(f"{LESSON_NOTE_PREFIX}%"),
            Material.source_lang == target,
        )
    ).all()
    for material_id, notes in rows:
        if material_id is not None and notes and notes.startswith(LESSON_NOTE_PREFIX):
            material_to_code[material_id] = notes[len(LESSON_NOTE_PREFIX) :]

    # A course material counts as practiced once one of its exercises has an
    # answer attempt. A single join keeps this to one query and avoids loading
    # every attempted exercise id into memory (and SQLite's bound-parameter cap).
    practiced_material_ids = set(
        session.exec(
            select(Material.id)
            .join(Exercise, Exercise.material_id == Material.id)
            .join(AnswerAttempt, AnswerAttempt.exercise_id == Exercise.id)
            .where(
                Material.notes.like(f"{LESSON_NOTE_PREFIX}%"),
                Material.source_lang == target,
            )
            .distinct()
        ).all()
    )

    completed_codes = {
        code
        for material_id, code in material_to_code.items()
        if material_id in practiced_material_ids
    }

    levels: list[dict] = []
    total_lessons = 0
    completed_lessons = 0
    next_lesson: dict | None = None
    for level in _load(target).get("levels", []):
        codes: list[str] = []
        for unit in level.get("units", []):
            for lesson in unit.get("lessons", []):
                code = lesson["code"]
                codes.append(code)
                if next_lesson is None and code not in completed_codes:
                    next_lesson = {
                        "code": code,
                        "title": lesson.get("title", ""),
                        "level": level["level"],
                        "can_do": lesson.get("can_do", ""),
                    }
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
        "next_lesson": next_lesson,
    }
