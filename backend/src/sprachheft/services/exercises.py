"""Exercise retrieval."""

from __future__ import annotations

from sqlmodel import Session, select

from sprachheft.models import Exercise


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
