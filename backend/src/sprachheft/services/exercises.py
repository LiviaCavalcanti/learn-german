"""Exercise retrieval."""

from __future__ import annotations

from sqlmodel import Session, select

from sprachheft.models import Exercise, ExerciseVariant
from sprachheft.schemas import ExerciseRead


def list_exercises(
    session: Session,
    *,
    material_id: int | None = None,
    type: str | None = None,
    limit: int = 200,
) -> list[Exercise]:
    stmt = select(Exercise).order_by(Exercise.created_at.desc())
    if material_id is not None:
        stmt = stmt.where(Exercise.material_id == material_id)
    if type:
        stmt = stmt.where(Exercise.type == type)
    return list(session.exec(stmt.limit(limit)).all())


def _variant_map(session: Session, exercise_ids: list[int]) -> dict[int, tuple[int, int]]:
    """Map exercise_id -> (group_id, position) for exercises that belong to a group."""
    if not exercise_ids:
        return {}
    links = session.exec(
        select(ExerciseVariant).where(ExerciseVariant.exercise_id.in_(exercise_ids))
    ).all()
    return {link.exercise_id: (link.group_id, link.position) for link in links}


def to_read(session: Session, exercise: Exercise) -> ExerciseRead:
    """Serialize one exercise, attaching its variant group id and position."""
    group_id, position = _variant_map(session, [exercise.id]).get(
        exercise.id, (exercise.id, 0)
    )
    read = ExerciseRead.model_validate(exercise)
    read.group_id = group_id
    read.variant_position = position
    return read


def list_exercises_read(
    session: Session,
    *,
    material_id: int | None = None,
    type: str | None = None,
    limit: int = 200,
) -> list[ExerciseRead]:
    """List exercises enriched with variant group id and position."""
    exercises = list_exercises(session, material_id=material_id, type=type, limit=limit)
    variant_map = _variant_map(session, [ex.id for ex in exercises])
    reads: list[ExerciseRead] = []
    for exercise in exercises:
        group_id, position = variant_map.get(exercise.id, (exercise.id, 0))
        read = ExerciseRead.model_validate(exercise)
        read.group_id = group_id
        read.variant_position = position
        reads.append(read)
    return reads
