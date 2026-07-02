"""Exercises API router."""

from __future__ import annotations

from fastapi import APIRouter, Query

from sprachheft.api.deps import SessionDep
from sprachheft.schemas import ExerciseRead
from sprachheft.services import exercises as svc

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[ExerciseRead])
def list_exercises(
    session: SessionDep,
    material_id: int | None = None,
    type: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
):
    return svc.list_exercises(session, material_id=material_id, type=type, limit=limit)
