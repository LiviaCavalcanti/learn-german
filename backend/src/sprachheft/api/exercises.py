"""Exercises API router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from sprachheft.api.deps import SessionDep
from sprachheft.models import Exercise
from sprachheft.schemas import AnswerAttemptRead, ExerciseRead, ExerciseUpdate
from sprachheft.services import attempts as attempts_svc
from sprachheft.services import exercises as svc

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[ExerciseRead])
def list_exercises(
    session: SessionDep,
    material_id: int | None = None,
    type: str | None = None,
    lang: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
):
    return svc.list_exercises_read(
        session, material_id=material_id, type=type, target_lang=lang, limit=limit
    )


@router.get("/{exercise_id}/attempts", response_model=list[AnswerAttemptRead])
def list_attempts(
    exercise_id: int,
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
):
    return attempts_svc.list_attempts(session, exercise_id, limit=limit)


@router.patch("/{exercise_id}", response_model=ExerciseRead)
def update_exercise(exercise_id: int, data: ExerciseUpdate, session: SessionDep):
    exercise = svc.update_exercise(session, exercise_id, data)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return svc.to_read(session, exercise)


@router.post("/{exercise_id}/variant", response_model=ExerciseRead)
def create_variant(
    exercise_id: int,
    session: SessionDep,
    stage: int = Query(2, ge=1, le=4),
):
    """Generate a fresh alternate of an exercise; it coexists with the original."""
    exercise = session.get(Exercise, exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    from sprachheft.services import generation

    new_exercise = generation.generate_variant(session, exercise, stage=stage)
    return svc.to_read(session, new_exercise)
