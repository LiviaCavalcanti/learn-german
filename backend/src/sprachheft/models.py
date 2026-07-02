"""SQLModel table definitions.

Enum-like fields are stored as plain strings for predictable persistence; the
allowed values are validated at the API boundary (see ``schemas.py``).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    """Timezone-naive UTC timestamp (keeps SQLite comparisons consistent)."""
    return datetime.now(UTC).replace(tzinfo=None)


class Material(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    media_type: str = "text"  # video | podcast | text
    source_url: str | None = None
    source_lang: str = "de"
    level: str = "A2"  # A1 | A2 | B1 | B2
    transcript: str
    translation: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class VocabItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    material_id: int | None = Field(default=None, foreign_key="material.id", index=True)
    word: str
    lemma: str = Field(index=True)
    pos: str | None = None
    meaning_en: str
    cefr: str | None = None
    example_de: str | None = None
    example_en: str | None = None
    grammar_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class Exercise(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    material_id: int | None = Field(default=None, foreign_key="material.id", index=True)
    source: str = "generated"  # generated | imported | review
    type: str = "fill-in-blank"
    cefr: str | None = None
    grammar_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    instructions: str = ""
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    answer_key: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class SRState(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    item_type: str = "vocab"  # vocab | exercise
    item_id: int = Field(index=True)
    due: datetime = Field(default_factory=utcnow, index=True)
    stability: float = 0.0
    difficulty: float = 0.0
    reps: int = 0
    lapses: int = 0
    last_review: datetime | None = None
    state: str = "new"  # new | learning | review | relearning
    fsrs_card: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class ReviewLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    srstate_id: int = Field(foreign_key="srstate.id", index=True)
    rating: str  # again | hard | good | easy
    reviewed_at: datetime = Field(default_factory=utcnow)
    session_id: int | None = Field(default=None, foreign_key="studysession.id")


class StudySession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    kind: str = "practice"  # practice | review
    started_at: datetime = Field(default_factory=utcnow)
    ended_at: datetime | None = None
    summary: dict = Field(default_factory=dict, sa_column=Column(JSON))


class ImportSource(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str | None = None
    raw_text: str
    parsed_summary: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class GrammarTopic(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    title: str
    cefr: str
    description: str | None = None


class VocabEmbedding(SQLModel, table=True):
    vocab_id: int = Field(foreign_key="vocabitem.id", primary_key=True)
    dim: int = 0
    vector: list[float] = Field(default_factory=list, sa_column=Column(JSON))
