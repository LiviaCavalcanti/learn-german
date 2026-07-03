"""Review API: due queue, grading, and dashboard stats."""

from __future__ import annotations

from fastapi import APIRouter, Query

from sprachheft.api.deps import SessionDep
from sprachheft.schemas import GradeIn, ReviewCardsIn
from sprachheft.services.review import (
    delete_cards,
    get_review_queue,
    get_stats,
    grade_item,
    list_cards,
    remove_cards,
)

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/queue")
def review_queue(
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
    lang: str | None = Query(None),
):
    return get_review_queue(session, limit=limit, lang=lang)


@router.get("/cards")
def review_cards(
    session: SessionDep,
    item_type: str | None = None,
    limit: int = Query(500, ge=1, le=2000),
):
    """All review cards (not just those due) for the manage view."""
    return list_cards(session, item_type=item_type, limit=limit)


@router.post("/cards/remove")
def remove_review_cards(payload: ReviewCardsIn, session: SessionDep):
    """Stop reviewing the given cards but keep the underlying items."""
    return {"removed": remove_cards(session, payload.srstate_ids)}


@router.post("/cards/delete")
def delete_review_cards(payload: ReviewCardsIn, session: SessionDep):
    """Delete the underlying vocab words / exercises of the given cards."""
    return {"deleted": delete_cards(session, payload.srstate_ids)}


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
