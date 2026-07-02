"""Thin wrapper over the FSRS scheduler (fsrs v6).

Cards are persisted as plain dicts (``SRState.fsrs_card``) so the scheduler stays
swappable. Datetimes are normalized to naive UTC to match the rest of the models.
"""

from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache

from fsrs import Card, Rating, Scheduler

_RATINGS = {
    "again": Rating.Again,
    "hard": Rating.Hard,
    "good": Rating.Good,
    "easy": Rating.Easy,
}


@lru_cache
def _scheduler() -> Scheduler:
    return Scheduler()


def _naive_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


def review_card(card_dict: dict | None, rating: str) -> dict:
    """Apply a rating to a (serialized) card and return the updated schedule."""
    key = (rating or "").lower()
    if key not in _RATINGS:
        raise ValueError(f"Invalid rating '{rating}'. Use again|hard|good|easy.")
    card = Card.from_dict(card_dict) if card_dict else Card()
    updated, _log = _scheduler().review_card(card, _RATINGS[key])
    state = getattr(updated.state, "name", str(updated.state)).lower()
    return {
        "card": updated.to_dict(),
        "due": _naive_utc(updated.due),
        "stability": float(updated.stability or 0.0),
        "difficulty": float(updated.difficulty or 0.0),
        "state": state,
        "last_review": _naive_utc(updated.last_review),
    }
