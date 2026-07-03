"""Persist and retrieve saved answer attempts."""

from __future__ import annotations

from sqlmodel import Session, select

from sprachheft.models import AnswerAttempt


def record_attempt(
    session: Session,
    *,
    exercise_id: int,
    kind: str,
    responses: list[str] | None = None,
    answer_text: str = "",
    result: dict | None = None,
    correct: int = 0,
    total: int = 0,
) -> AnswerAttempt:
    attempt = AnswerAttempt(
        exercise_id=exercise_id,
        kind=kind,
        responses=responses or [],
        answer_text=answer_text,
        result=result or {},
        correct=correct,
        total=total,
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    return attempt


def list_attempts(session: Session, exercise_id: int, *, limit: int = 20) -> list[AnswerAttempt]:
    stmt = (
        select(AnswerAttempt)
        .where(AnswerAttempt.exercise_id == exercise_id)
        .order_by(AnswerAttempt.created_at.desc())
        .limit(limit)
    )
    return list(session.exec(stmt).all())
