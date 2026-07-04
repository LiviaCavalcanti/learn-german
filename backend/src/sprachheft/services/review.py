"""Review queue, grading (FSRS), and dashboard stats."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import and_, func, or_
from sqlmodel import Session, select

from sprachheft.models import Exercise, ReviewLog, SRState, VocabItem, utcnow
from sprachheft.srs import review_card


def _srstate_lang_condition(lang: str):
    """Boolean filter selecting SRState rows whose underlying item is in ``lang``.

    ``SRState`` links polymorphically (``item_type`` + ``item_id``) to either a
    ``VocabItem`` or an ``Exercise``, so scope by matching the item's
    ``target_lang`` for the right table.
    """
    vocab_ids = select(VocabItem.id).where(VocabItem.target_lang == lang)
    exercise_ids = select(Exercise.id).where(Exercise.target_lang == lang)
    return or_(
        and_(SRState.item_type == "vocab", SRState.item_id.in_(vocab_ids)),
        and_(SRState.item_type == "exercise", SRState.item_id.in_(exercise_ids)),
    )


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
            "target_lang": vocab.target_lang,
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
        "target_lang": exercise.target_lang,
        "type": exercise.type,
        "instructions": exercise.instructions,
        "payload": exercise.payload,
        "answer_key": exercise.answer_key,
        "grammar_tags": exercise.grammar_tags,
        "cefr": exercise.cefr,
    }


def get_review_queue(
    session: Session, *, limit: int = 20, lang: str | None = None
) -> list[dict]:
    now = utcnow()
    # Review is vocab-only: exercises are practised on their material page, not here.
    stmt = (
        select(SRState)
        .where(SRState.due <= now, SRState.item_type == "vocab")
        .order_by(SRState.difficulty.desc(), SRState.due)
        .limit(limit if lang is None else max(limit * 10, 200))
    )
    queue: list[dict] = []
    for state in session.exec(stmt).all():
        item = _serialize_item(session, state)
        if not item:
            continue
        if lang and item.get("target_lang") not in (None, lang):
            continue
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
        if len(queue) >= limit:
            break
    return queue


def list_cards(
    session: Session,
    *,
    item_type: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[dict]:
    """List all review cards (not just those due) for the manage view."""
    now = utcnow()
    stmt = select(SRState)
    if item_type in ("vocab", "exercise"):
        stmt = stmt.where(SRState.item_type == item_type)
    stmt = stmt.order_by(SRState.due).offset(offset).limit(limit)

    cards: list[dict] = []
    for state in session.exec(stmt).all():
        item = _serialize_item(session, state)
        if item is None:
            continue
        cards.append(
            {
                "srstate_id": state.id,
                "item_type": state.item_type,
                "item_id": state.item_id,
                "due": state.due,
                "reps": state.reps,
                "lapses": state.lapses,
                "state": state.state,
                "last_review": state.last_review,
                "is_due": state.due <= now,
                "item": item,
            }
        )
    return cards


def remove_cards(session: Session, srstate_ids: list[int]) -> int:
    """Remove cards from review only: delete the SR state (and its review logs),
    but keep the underlying vocab word / exercise in the library."""
    removed = 0
    for srstate_id in dict.fromkeys(srstate_ids):
        state = session.get(SRState, srstate_id)
        if state is None:
            continue
        logs = session.exec(
            select(ReviewLog).where(ReviewLog.srstate_id == srstate_id)
        ).all()
        for log in logs:
            session.delete(log)
        session.delete(state)
        removed += 1
    session.commit()
    return removed


def delete_cards(session: Session, srstate_ids: list[int]) -> int:
    """Delete the underlying items of the given cards entirely (vocab words or
    exercises), which also removes their SR state, review logs, and related rows."""
    vocab_ids: list[int] = []
    exercise_ids: list[int] = []
    for srstate_id in dict.fromkeys(srstate_ids):
        state = session.get(SRState, srstate_id)
        if state is None:
            continue
        if state.item_type == "vocab":
            vocab_ids.append(state.item_id)
        elif state.item_type == "exercise":
            exercise_ids.append(state.item_id)

    from sprachheft.services.exercises import delete_exercise_items
    from sprachheft.services.vocab import delete_vocab_items

    deleted = 0
    if vocab_ids:
        deleted += delete_vocab_items(session, vocab_ids)
    if exercise_ids:
        deleted += delete_exercise_items(session, exercise_ids)
    return deleted


def purge_exercise_review_cards(session: Session) -> int:
    """Drop all exercise cards from spaced review (review is vocab-only).

    Exercises are no longer scheduled for review, so delete any existing exercise
    SR states and their review logs. Idempotent: safe to run on every startup.
    """
    states = session.exec(select(SRState).where(SRState.item_type == "exercise")).all()
    removed = 0
    for state in states:
        logs = session.exec(select(ReviewLog).where(ReviewLog.srstate_id == state.id)).all()
        for log in logs:
            session.delete(log)
        session.delete(state)
        removed += 1
    if removed:
        session.commit()
    return removed


def get_stats(session: Session, *, lang: str | None = None) -> dict:
    now = utcnow()
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # When a language is given, scope every figure to items in that language so the
    # dashboard cards (due now, streak, vocabulary…) are per-language, not global.
    sr_filter = _srstate_lang_condition(lang) if lang else None

    due_stmt = select(func.count(SRState.id)).where(SRState.due <= now)
    if sr_filter is not None:
        due_stmt = due_stmt.where(sr_filter)
    due_now = int(session.exec(due_stmt).one())

    vocab_stmt = select(func.count(VocabItem.id))
    exercise_stmt = select(func.count(Exercise.id))
    if lang:
        vocab_stmt = vocab_stmt.where(VocabItem.target_lang == lang)
        exercise_stmt = exercise_stmt.where(Exercise.target_lang == lang)
    total_vocab = int(session.exec(vocab_stmt).one())
    total_exercises = int(session.exec(exercise_stmt).one())

    reviews_stmt = select(func.count(ReviewLog.id)).where(ReviewLog.reviewed_at >= start_today)
    dates_stmt = select(ReviewLog.reviewed_at)
    if sr_filter is not None:
        reviews_stmt = reviews_stmt.join(
            SRState, ReviewLog.srstate_id == SRState.id
        ).where(sr_filter)
        dates_stmt = dates_stmt.join(SRState, ReviewLog.srstate_id == SRState.id).where(sr_filter)
    reviews_today = int(session.exec(reviews_stmt).one())

    next_due_stmt = select(SRState.due).where(SRState.due > now)
    if sr_filter is not None:
        next_due_stmt = next_due_stmt.where(sr_filter)
    next_due = session.exec(next_due_stmt.order_by(SRState.due).limit(1)).first()

    review_dates = {dt.date() for dt in session.exec(dates_stmt).all()}
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
