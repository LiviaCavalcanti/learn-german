"""Review API: due queue, grading, and dashboard stats."""

from __future__ import annotations

from fastapi import APIRouter, Query

from sprachheft.api.deps import SessionDep
from sprachheft.schemas import GradeIn
from sprachheft.services.review import get_review_queue, get_stats, grade_item

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/queue")
def review_queue(session: SessionDep, limit: int = Query(20, ge=1, le=100)):
    return get_review_queue(session, limit=limit)


@router.get("/stats")
def review_stats(session: SessionDep):
    return get_stats(session)


@router.post("/grade")
def grade(payload: GradeIn, session: SessionDep):
    state = grade_item(
        session,
        payload.item_type,
        payload.item_id,
        payload.rating,
        session_id=payload.session_id,
    )
    return {
        "srstate_id": state.id,
        "due": state.due,
        "state": state.state,
        "reps": state.reps,
        "lapses": state.lapses,
    }
