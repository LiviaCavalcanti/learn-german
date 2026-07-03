"""Generation orchestration: run the agent and persist results.

Generation is done in small, incremental sections (vocabulary, then exercises in
batches) so that partial results are saved even when a slow local model times out
on a later step, and the UI can show progress.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlmodel import Session, select

from sprachheft.agents.generator import (
    generate_exercises,
    generate_one,
    generate_vocabulary,
)
from sprachheft.models import Exercise, ExerciseVariant, Material, SRState, VocabItem
from sprachheft.schemas import GenerationResult, GenExercise, GenVocab

# Exercises are generated a few types at a time; each batch is one small LLM call.
EXERCISE_BATCHES: list[list[str]] = [
    ["fill-in-blank", "multiple-choice", "translation"],
    ["conjugation", "reorder"],
    ["reading", "interpretation", "writing"],
]


def _persist_vocab(session: Session, material: Material, vocab: Iterable[GenVocab]) -> int:
    added = 0
    for gv in vocab:
        lemma = (gv.lemma or gv.word).strip()
        if not lemma:
            continue
        existing = session.exec(
            select(VocabItem).where(
                VocabItem.material_id == material.id,
                VocabItem.lemma == lemma,
            )
        ).first()
        if existing:
            continue
        item = VocabItem(
            material_id=material.id,
            target_lang=material.source_lang,
            word=gv.word,
            lemma=lemma,
            pos=gv.pos,
            meaning_en=gv.meaning_en,
            cefr=gv.cefr or material.level,
            example_de=gv.example_de,
            example_en=gv.example_en,
            grammar_tags=gv.grammar_tags,
        )
        session.add(item)
        session.flush()
        session.add(SRState(item_type="vocab", item_id=item.id))
        added += 1
    return added


def _persist_exercises(
    session: Session,
    material: Material,
    exercises: Iterable[GenExercise],
    *,
    source: str = "generated",
) -> int:
    added = 0
    for ge in exercises:
        exercise = Exercise(
            material_id=material.id,
            target_lang=material.source_lang,
            source=source,
            type=ge.type,
            cefr=ge.cefr or material.level,
            grammar_tags=ge.grammar_tags,
            instructions=ge.instructions,
            payload=ge.payload,
            answer_key=ge.answer_key,
        )
        session.add(exercise)
        session.flush()
        added += 1
    return added


def persist_result(
    session: Session,
    material: Material,
    result: GenerationResult,
    *,
    source: str = "generated",
) -> dict:
    vocab_added = _persist_vocab(session, material, result.vocabulary)
    exercises_added = _persist_exercises(session, material, result.exercises, source=source)
    session.commit()
    return {
        "themes": result.themes,
        "vocab_added": vocab_added,
        "exercises_added": exercises_added,
    }


def generate_vocab_section(session: Session, material: Material, stage: int = 2) -> dict:
    """Generate + persist only the vocabulary (fast first step)."""
    vocab = generate_vocabulary(material, stage)
    added = _persist_vocab(session, material, vocab)
    session.commit()
    return {"vocab_added": added, "exercise_batches": len(EXERCISE_BATCHES)}


def generate_exercises_section(
    session: Session, material: Material, stage: int, batch: int
) -> dict:
    """Generate + persist one batch of exercises (a few types)."""
    if not 0 <= batch < len(EXERCISE_BATCHES):
        raise IndexError(f"batch must be 0..{len(EXERCISE_BATCHES) - 1}")
    exercises = generate_exercises(material, stage, EXERCISE_BATCHES[batch])
    added = _persist_exercises(session, material, exercises)
    session.commit()
    return {
        "exercises_added": added,
        "batch": batch,
        "exercise_batches": len(EXERCISE_BATCHES),
    }


def generate_for_material(session: Session, material: Material, *, stage: int = 2) -> dict:
    """Full staged generation; tolerant of per-step failures (partial results persist)."""
    errors: list[str] = []
    vocab_added = 0
    try:
        vocab_added = generate_vocab_section(session, material, stage)["vocab_added"]
    except Exception as exc:  # noqa: BLE001 — one slow step must not lose the rest
        errors.append(f"vocabulary: {exc}")

    exercises_added = 0
    for index in range(len(EXERCISE_BATCHES)):
        try:
            exercises_added += generate_exercises_section(session, material, stage, index)[
                "exercises_added"
            ]
        except Exception as exc:  # noqa: BLE001
            errors.append(f"exercises[{index}]: {exc}")

    return {
        "vocab_added": vocab_added,
        "exercises_added": exercises_added,
        "exercise_batches": len(EXERCISE_BATCHES),
        "errors": errors,
    }


def group_id_for(session: Session, exercise: Exercise) -> int:
    """Group id of an exercise: its variant link's group, else its own id (seed)."""
    link = session.exec(
        select(ExerciseVariant).where(ExerciseVariant.exercise_id == exercise.id)
    ).first()
    return link.group_id if link else exercise.id


def _group_exercises(session: Session, group_id: int) -> list[Exercise]:
    links = session.exec(
        select(ExerciseVariant).where(ExerciseVariant.group_id == group_id)
    ).all()
    ids = {link.exercise_id for link in links}
    ids.add(group_id)  # the seed is always part of its own group
    return list(session.exec(select(Exercise).where(Exercise.id.in_(ids))).all())


def _collect_prompts(exercises: list[Exercise], limit: int = 6) -> list[str]:
    prompts: list[str] = []
    for ex in exercises:
        if ex.instructions:
            prompts.append(ex.instructions)
        payload = ex.payload or {}
        for item in payload.get("items", []) or []:
            if isinstance(item, dict) and item.get("prompt"):
                prompts.append(str(item["prompt"]))
        for key in ("prompt", "task", "theme"):
            if payload.get(key):
                prompts.append(str(payload[key]))
    return prompts[:limit]


def generate_variant(session: Session, exercise: Exercise, *, stage: int = 2) -> Exercise:
    """Generate a fresh alternate of ``exercise`` (same type) and persist it.

    The new exercise coexists with the original; both are linked into the same
    variant group so the UI can paginate between them.
    """
    material = session.get(Material, exercise.material_id) if exercise.material_id else None
    if material is None:
        raise ValueError("Exercise is not linked to a material")

    group_id = group_id_for(session, exercise)
    siblings = _group_exercises(session, group_id)
    avoid = _collect_prompts(siblings)

    gen = generate_one(material, exercise.type, stage, avoid=avoid)
    new_exercise = Exercise(
        material_id=material.id,
        source="generated",
        type=exercise.type,  # keep the slot's type regardless of what the model returns
        cefr=gen.cefr or exercise.cefr or material.level,
        grammar_tags=gen.grammar_tags or exercise.grammar_tags,
        instructions=gen.instructions,
        payload=gen.payload,
        answer_key=gen.answer_key,
    )
    session.add(new_exercise)
    session.flush()

    # Ensure the seed has an explicit position-0 link, then append the new variant.
    seed_link = session.exec(
        select(ExerciseVariant).where(ExerciseVariant.exercise_id == group_id)
    ).first()
    if seed_link is None:
        session.add(ExerciseVariant(group_id=group_id, exercise_id=group_id, position=0))
    positions = [
        link.position
        for link in session.exec(
            select(ExerciseVariant).where(ExerciseVariant.group_id == group_id)
        ).all()
    ]
    next_position = (max(positions) + 1) if positions else 1
    session.add(
        ExerciseVariant(
            group_id=group_id, exercise_id=new_exercise.id, position=next_position
        )
    )

    session.commit()
    session.refresh(new_exercise)
    return new_exercise
