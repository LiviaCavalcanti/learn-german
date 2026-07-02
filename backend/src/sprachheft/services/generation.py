"""Generation orchestration: run the agent and persist results."""

from __future__ import annotations

from sqlmodel import Session, select

from sprachheft.agents.generator import generate
from sprachheft.models import Exercise, Material, SRState, VocabItem
from sprachheft.schemas import GenerationResult


def persist_result(
    session: Session,
    material: Material,
    result: GenerationResult,
    *,
    source: str = "generated",
) -> dict:
    vocab_added = 0
    for gv in result.vocabulary:
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
        vocab_added += 1

    exercises_added = 0
    for ge in result.exercises:
        exercise = Exercise(
            material_id=material.id,
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
        session.add(SRState(item_type="exercise", item_id=exercise.id))
        exercises_added += 1

    session.commit()
    return {
        "themes": result.themes,
        "vocab_added": vocab_added,
        "exercises_added": exercises_added,
    }


def generate_for_material(session: Session, material: Material, *, stage: int = 2) -> dict:
    result = generate(material, stage)
    return persist_result(session, material, result, source="generated")
