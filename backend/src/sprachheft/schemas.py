"""Pydantic request/response schemas and shared value types for the API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

Level = Literal["A1", "A2", "B1", "B2"]
MediaType = Literal["video", "podcast", "text"]
ExerciseType = Literal[
    "fill-in-blank",
    "conjugation",
    "translation",
    "multiple-choice",
    "reorder",
    "reading",
    "interpretation",
    "writing",
]
Rating = Literal["again", "hard", "good", "easy"]


# --- Materials ---------------------------------------------------------------
class MaterialCreate(BaseModel):
    title: str
    media_type: MediaType = "text"
    source_url: str | None = None
    level: Level = "A2"
    transcript: str = ""
    translation: str | None = None
    notes: str | None = None


class MaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    media_type: str
    source_url: str | None
    source_lang: str
    level: str
    transcript: str
    translation: str | None
    notes: str | None
    created_at: datetime


class MaterialSummary(BaseModel):
    id: int
    title: str
    media_type: str
    level: str
    created_at: datetime
    vocab_count: int = 0
    exercise_count: int = 0


# --- Vocabulary --------------------------------------------------------------
class VocabItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    material_id: int | None
    word: str
    lemma: str
    pos: str | None
    meaning_en: str
    cefr: str | None
    example_de: str | None
    example_en: str | None
    grammar_tags: list[str]
    created_at: datetime

    @computed_field
    @property
    def ipa(self) -> str | None:
        """IPA pronunciation of the word (computed; needs the phonetics extra)."""
        from sprachheft.phonetics import to_ipa

        return to_ipa(self.word)


class VocabItemCreate(BaseModel):
    word: str
    lemma: str | None = None
    pos: str | None = None
    meaning_en: str
    cefr: str | None = None
    example_de: str | None = None
    example_en: str | None = None
    grammar_tags: list[str] = []
    material_id: int | None = None


class VocabItemUpdate(BaseModel):
    """Partial update of a vocabulary item (only provided fields are changed)."""

    word: str | None = None
    lemma: str | None = None
    pos: str | None = None
    meaning_en: str | None = None
    cefr: str | None = None
    example_de: str | None = None
    example_en: str | None = None
    grammar_tags: list[str] | None = None


class VocabComposeIn(BaseModel):
    """Request to compose a practice text + exercises from selected vocabulary."""

    vocab_ids: list[int] = []
    level: Level | None = None
    title: str | None = None
    instructions: str | None = None


class VocabComposeResult(BaseModel):
    material_id: int
    title: str
    vocab_added: int = 0
    exercises_added: int = 0


class VocabDeleteIn(BaseModel):
    ids: list[int] = []


class VocabDeleteResult(BaseModel):
    deleted: int = 0


class VerbVocabIn(BaseModel):
    """Add a looked-up verb to the vocabulary (deduplicated by lemma)."""

    infinitive: str
    english: str = ""
    partizip_ii: str = ""
    auxiliary: str = ""
    cefr: Level | None = None


class VerbVocabResult(BaseModel):
    created: bool
    item: VocabItemRead


# --- Exercises ---------------------------------------------------------------
class ExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    material_id: int | None
    source: str
    type: str
    cefr: str | None
    grammar_tags: list[str]
    instructions: str
    payload: dict
    answer_key: dict
    created_at: datetime
    # Variant grouping (see models.ExerciseVariant). For a standalone exercise
    # group_id defaults to its own id and variant_position to 0.
    group_id: int | None = None
    variant_position: int = 0


class ExerciseUpdate(BaseModel):
    """Partial update of an exercise's instructions and/or answer key."""

    instructions: str | None = None
    answer_key: dict | None = None


class AnswerAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exercise_id: int
    kind: str
    responses: list[str]
    answer_text: str
    result: dict
    correct: int
    total: int
    created_at: datetime


# --- Grammar topics ----------------------------------------------------------
class GrammarTopicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    cefr: str
    description: str | None


# --- Dictionary --------------------------------------------------------------
class DictEntryOut(BaseModel):
    headword: str
    pos: str | None = None
    ipa: str | None = None
    translations: list[str] = []
    senses: list[str] = []


class DictionaryLookupResponse(BaseModel):
    query: str
    lemma: str
    available: bool
    entries: list[DictEntryOut]
    google_translate_url: str


# --- Generation (LLM structured output) --------------------------------------
class GenVocab(BaseModel):
    word: str
    lemma: str | None = None
    pos: str | None = None
    meaning_en: str
    cefr: str | None = None
    example_de: str | None = None
    example_en: str | None = None
    grammar_tags: list[str] = []


class GenExercise(BaseModel):
    type: ExerciseType
    cefr: str | None = None
    grammar_tags: list[str] = []
    instructions: str
    payload: dict = {}
    answer_key: dict = {}


class GenerationResult(BaseModel):
    themes: list[str] = []
    vocabulary: list[GenVocab] = []
    exercises: list[GenExercise] = []


class VocabBatch(BaseModel):
    """Structured output for a vocabulary-only generation call."""

    vocabulary: list[GenVocab] = []


class ExerciseBatch(BaseModel):
    """Structured output for an exercise-batch generation call (a few types)."""

    exercises: list[GenExercise] = []


class ComposedText(BaseModel):
    """A practice text plus exercises composed from a set of learned words."""

    title: str = ""
    text: str = ""
    exercises: list[GenExercise] = []


# --- Practice / Review -------------------------------------------------------
class PracticeSessionCreate(BaseModel):
    kind: str = "practice"
    material_id: int | None = None


class PracticeAnswerIn(BaseModel):
    exercise_id: int
    responses: list[str] = []
    rating: Rating | None = None
    session_id: int | None = None


class AnswerFeedbackIn(BaseModel):
    exercise_id: int
    answer: str = ""


class FeedbackError(BaseModel):
    original: str = ""
    correction: str = ""
    explanation: str = ""


class AnswerFeedback(BaseModel):
    has_errors: bool = False
    corrected: str = ""
    errors: list[FeedbackError] = []
    summary: str = ""


class GradeIn(BaseModel):
    item_type: Literal["vocab", "exercise"]
    item_id: int
    rating: Rating
    session_id: int | None = None


class ReviewCardsIn(BaseModel):
    """Target review cards by their SR-state ids (bulk-capable)."""

    srstate_ids: list[int] = []


# --- Imports -----------------------------------------------------------------
class ImportJsonIn(BaseModel):
    material: dict | None = None
    vocabulary: list[GenVocab] = []
    exercises: list[GenExercise] = []
    title: str | None = None
    level: Level | None = None


class ImportTextIn(BaseModel):
    raw_text: str
    level: Level | None = None
    title: str | None = None


# --- Ingestion ---------------------------------------------------------------
class TranscribeIn(BaseModel):
    source_url: str


# --- Rewrite -----------------------------------------------------------------
class RewrittenText(BaseModel):
    text: str


class RewriteIn(BaseModel):
    instructions: str | None = None
    target_lines: int = 15


# --- Conjugation -------------------------------------------------------------
class ConjugationForms(BaseModel):
    """The six personal forms of a tense."""

    ich: str = ""
    du: str = ""
    er_sie_es: str = Field(default="", description="third person singular: er/sie/es")
    wir: str = ""
    ihr: str = ""
    sie_Sie: str = Field(default="", description="third person plural / formal: sie/Sie")


class ImperativeForms(BaseModel):
    du: str = ""
    ihr: str = ""
    Sie: str = ""


class ConjugationTable(BaseModel):
    """A full conjugation table for a German verb."""

    infinitive: str = Field(description="the verb infinitive, e.g. 'arbeiten'")
    english: str = Field(default="", description="short English meaning of the verb")
    regular: bool = Field(default=True, description="false for strong/irregular verbs")
    auxiliary: str = Field(default="", description="perfect-tense auxiliary: 'haben' or 'sein'")
    partizip_ii: str = Field(default="", description="past participle, e.g. 'gearbeitet'")
    notes: str = Field(default="", description="short hint, e.g. stem change or separable prefix")
    present: ConjugationForms = Field(default_factory=ConjugationForms, description="Präsens")
    praeteritum: ConjugationForms = Field(
        default_factory=ConjugationForms, description="Präteritum"
    )
    perfekt: ConjugationForms = Field(
        default_factory=ConjugationForms, description="Perfekt (auxiliary + past participle)"
    )
    futur1: ConjugationForms = Field(
        default_factory=ConjugationForms, description="Futur I (werden + infinitive)"
    )
    konjunktiv2: ConjugationForms = Field(
        default_factory=ConjugationForms, description="Konjunktiv II"
    )
    imperative: ImperativeForms = Field(default_factory=ImperativeForms, description="Imperativ")


# --- Tutor / teacher chat ----------------------------------------------------
ContextKind = Literal["none", "material", "vocab", "exercise", "text"]


class ChatContext(BaseModel):
    """A learning element from the app attached to the conversation."""

    kind: ContextKind = "none"
    id: int | None = None
    label: str | None = None
    text: str | None = None


class ChatSessionCreate(BaseModel):
    title: str | None = None
    context: ChatContext | None = None


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime


class ChatSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    context: dict
    created_at: datetime
    updated_at: datetime


class ChatSessionDetail(ChatSessionRead):
    messages: list[ChatMessageRead] = []


class ChatSendIn(BaseModel):
    message: str
    context: ChatContext | None = None


class ChatReply(BaseModel):
    """Structured teacher reply plus lightweight signals used to update the profile."""

    reply: str = Field(default="", description="the teacher's chat reply to the student")
    difficulties: list[str] = Field(
        default_factory=list,
        description="concrete things the student struggled with in this message (may be empty)",
    )
    mastered: list[str] = Field(
        default_factory=list,
        description="things the student clearly handled correctly (may be empty)",
    )


class ChatTurnOut(BaseModel):
    user_message: ChatMessageRead
    teacher_message: ChatMessageRead


class LearnerProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    summary: str
    focus: str
    strengths: list[str]
    difficulties: list[str]
    updated_at: datetime


class TeacherCardSuggestion(BaseModel):
    """A spaced-repetition flashcard proposed from a teacher message."""

    front: str = Field(default="", description="short German prompt/cue to recall")
    back: str = Field(default="", description="concise answer/explanation")
    cefr: str = Field(default="A2", description="CEFR level of the card")
    tags: list[str] = Field(default_factory=list, description="0-3 lowercase topic tags")


class CardSuggestIn(BaseModel):
    text: str = ""
    message_id: int | None = None
    context: ChatContext | None = None


class ReviewCardCreate(BaseModel):
    front: str
    back: str
    cefr: Level | None = None
    tags: list[str] = []


class ReviewCardCreated(BaseModel):
    exercise_id: int
    srstate_id: int
