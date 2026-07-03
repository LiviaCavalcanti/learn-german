"""Review queue, grading (FSRS), and dashboard stats."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func
from sqlmodel import Session, select

from sprachheft.models import Exercise, ReviewLog, SRState, VocabItem, utcnow
from sprachheft.srs import review_card


def grade_item(
    session: Session,
    item_type: str,
    item_id: int,
    rating: str,
    *,
    session_id: int | None = None,
) -> SRState:
    state = session.exec(
        select(SRState).where(SRState.item_type == item_type, SRState.item_id == item_id)
    ).first()
    if state is None:
        state = SRState(item_type=item_type, item_id=item_id)
        session.add(state)
        session.flush()

    result = review_card(state.fsrs_card or None, rating)
    state.fsrs_card = result["card"]
    state.due = result["due"] or utcnow()
    state.stability = result["stability"]
    state.difficulty = result["difficulty"]
    state.state = result["state"]
    state.last_review = utcnow()
    state.reps += 1
    if rating.lower() == "again":
        state.lapses += 1

    session.add(state)
    session.add(ReviewLog(srstate_id=state.id, rating=rating.lower(), session_id=session_id))
    session.commit()
    session.refresh(state)
    return state


def _serialize_item(session: Session, state: SRState) -> dict | None:
    if state.item_type == "vocab":
        vocab = session.get(VocabItem, state.item_id)
        if not vocab:
            return None
        return {
            "kind": "vocab",
            "id": vocab.id,
            "word": vocab.word,
            "lemma": vocab.lemma,
            "meaning_en": vocab.meaning_en,
            "example_de": vocab.example_de,
            "cefr": vocab.cefr,
        }
    exercise = session.get(Exercise, state.item_id)
    if not exercise:
        return None
    return {
        "kind": "exercise",
        "id": exercise.id,
        "type": exercise.type,
        "instructions": exercise.instructions,
        "payload": exercise.payload,
        "answer_key": exercise.answer_key,
        "grammar_tags": exercise.grammar_tags,
        "cefr": exercise.cefr,
    }


def get_review_queue(session: Session, *, limit: int = 20) -> list[dict]:
    now = utcnow()
    stmt = (
        select(SRState)
        .where(SRState.due <= now)
        .order_by(SRState.difficulty.desc(), SRState.due)
        .limit(limit)
    )
    queue: list[dict] = []
    for state in session.exec(stmt).all():
        item = _serialize_item(session, state)
        if item:
            queue.append(
                {
                    "srstate_id": state.id,
                    "item_type": state.item_type,
                    "item_id": state.item_id,
                    "due": state.due,
                    "reps": state.reps,
                    "lapses": state.lapses,
                    "item": item,
                }
            )
    return queue


def get_stats(session: Session) -> dict:
    now = utcnow()
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    due_now = int(session.exec(select(func.count(SRState.id)).where(SRState.due <= now)).one())
    total_vocab = int(session.exec(select(func.count(VocabItem.id))).one())
    total_exercises = int(session.exec(select(func.count(Exercise.id))).one())
    reviews_today = int(
        session.exec(
            select(func.count(ReviewLog.id)).where(ReviewLog.reviewed_at >= start_today)
        ).one()
    )
    next_due = session.exec(
        select(SRState.due).where(SRState.due > now).order_by(SRState.due).limit(1)
    ).first()

    review_dates = {dt.date() for dt in session.exec(select(ReviewLog.reviewed_at)).all()}
    today = now.date()
    streak = 0
    cursor = today if today in review_dates else today - timedelta(days=1)
    while cursor in review_dates:
        streak += 1
        cursor -= timedelta(days=1)

    return {
        "due_now": due_now,
        "total_vocab": total_vocab,
        "total_exercises": total_exercises,
        "reviews_today": reviews_today,
        "streak": streak,
        "next_due": next_due,
    }
