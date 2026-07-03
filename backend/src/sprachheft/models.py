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
    source_lang: str = "de"  # target language being learned (ISO 639-1)
    native_lang: str = "en"  # native/explanation language (ISO 639-1)
    level: str = "A2"  # A1 | A2 | B1 | B2
    transcript: str
    translation: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class VocabItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    material_id: int | None = Field(default=None, foreign_key="material.id", index=True)
    target_lang: str = Field(default="de", index=True)  # language the word belongs to
    word: str
    lemma: str = Field(index=True)
    pos: str | None = None
    meaning_en: str  # meaning in the learner's native language (name kept for compatibility)
    cefr: str | None = None
    example_de: str | None = None  # example sentence in the target language
    example_en: str | None = None  # its translation in the native language
    grammar_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class Exercise(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    material_id: int | None = Field(default=None, foreign_key="material.id", index=True)
    target_lang: str = Field(default="de", index=True)  # language the exercise drills
    source: str = "generated"  # generated | imported | review
    type: str = "fill-in-blank"
    cefr: str | None = None
    grammar_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    instructions: str = ""
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    answer_key: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class AnswerAttempt(SQLModel, table=True):
    """A saved answer attempt for an exercise (gradable check or open feedback).

    Kept in its own table so learners can revisit what they answered. ``result``
    stores the full check/feedback payload so the UI can re-render it verbatim.
    """

    id: int | None = Field(default=None, primary_key=True)
    exercise_id: int = Field(foreign_key="exercise.id", index=True)
    kind: str = "check"  # check | feedback
    responses: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    answer_text: str = ""
    result: dict = Field(default_factory=dict, sa_column=Column(JSON))
    correct: int = 0
    total: int = 0
    created_at: datetime = Field(default_factory=utcnow)


class ExerciseVariant(SQLModel, table=True):
    """Groups exercises that are alternate variants of the same practice slot.

    ``group_id`` is the id of the seed (first) exercise in the group; every
    variant — including the seed — gets a row so ordering is explicit. Kept in a
    separate table so no existing table needs an ``ALTER`` (``init_db`` only
    creates missing tables).
    """

    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(index=True)
    exercise_id: int = Field(foreign_key="exercise.id", index=True)
    position: int = 0
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
    target_lang: str = Field(default="de", index=True)  # language the topic belongs to
    title: str
    cefr: str
    description: str | None = None


class VocabEmbedding(SQLModel, table=True):
    vocab_id: int = Field(foreign_key="vocabitem.id", primary_key=True)
    dim: int = 0
    vector: list[float] = Field(default_factory=list, sa_column=Column(JSON))


class ChatSession(SQLModel, table=True):
    """A conversation thread with the AI teacher."""

    id: int | None = Field(default=None, primary_key=True)
    title: str = "Conversation"
    # Optional attached learning element / context carried through the thread
    # (shape mirrors schemas.ChatContext): {kind, id, label, text}.
    context: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow, index=True)


class ChatMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id", index=True)
    role: str = "user"  # user | teacher
    content: str = ""
    created_at: datetime = Field(default_factory=utcnow, index=True)


class LearnerProfile(SQLModel, table=True):
    """A single, evolving picture of the learner the teacher builds over time.

    Kept as one row (the first/only one). ``strengths`` and ``difficulties`` are
    merged from each chat turn so the teacher "learns" what the student knows and
    where they struggle.
    """

    id: int | None = Field(default=None, primary_key=True)
    summary: str = ""
    focus: str = ""
    strengths: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    difficulties: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=utcnow)
