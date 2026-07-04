"""Pydantic request/response schemas and shared value types for the API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

Level = Literal["A1", "A2", "B1", "B2", "C1"]
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
    source_lang: str = "de"  # target language being learned (ISO 639-1)
    native_lang: str = "en"  # native/explanation language (ISO 639-1)
    level: Level = "A2"
    transcript: str = ""
    translation: str | None = None
    notes: str | None = None


class MaterialUpdate(BaseModel):
    """Partial update of a material (only fields sent in the request are changed)."""

    title: str | None = None
    media_type: MediaType | None = None
    source_url: str | None = None
    level: Level | None = None
    transcript: str | None = None
    translation: str | None = None


class MaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    media_type: str
    source_url: str | None
    source_lang: str
    native_lang: str = "en"
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
    target_lang: str = "de"
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

        return to_ipa(self.word, self.target_lang)


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
    target_lang: str = "de"


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
    target_lang: str = "de"


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
    target_lang: str = "de"
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
    native_lang: str = "en"


class FeedbackError(BaseModel):
    original: str = ""
    correction: str = ""
    explanation: str = ""


class AnswerFeedback(BaseModel):
    has_errors: bool = False
    corrected: str = ""
    errors: list[FeedbackError] = []
    summary: str = ""
    # Correctness assessed against a reference/model answer (open questions and
    # reading comprehension). ``reference`` is set server-side after grading so the
    # UI can reveal it; the LLM only fills verdict/score/errors/corrected/summary.
    verdict: Literal["correct", "partial", "incorrect", "unanswered"] = "unanswered"
    score: float = 0.0
    reference: str = ""


class LessonAnswerIn(BaseModel):
    """A learner's answer to a course-lesson comprehension question (by index)."""

    index: int
    answer: str = ""
    native_lang: str = "en"


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
    source_lang: str = "de"
    native_lang: str = "en"


class ImportTextIn(BaseModel):
    raw_text: str
    level: Level | None = None
    title: str | None = None
    source_lang: str = "de"
    native_lang: str = "en"


# --- Ingestion ---------------------------------------------------------------
class TranscribeIn(BaseModel):
    source_url: str
    source_lang: str = "de"


# --- Rewrite -----------------------------------------------------------------
class RewrittenText(BaseModel):
    text: str


class RewriteIn(BaseModel):
    instructions: str | None = None
    target_lines: int = 15


# --- Conjugation -------------------------------------------------------------
class ConjugationCell(BaseModel):
    """One person/number slot within a tense (language-agnostic)."""

    label: str = Field(description="person/number label, e.g. 'ich', 'yo', 'je', 'I'")
    form: str = Field(default="", description="the conjugated verb form for this slot")


class ConjugationTense(BaseModel):
    """A named tense or mood together with its personal forms."""

    name: str = Field(
        description="tense/mood name in the target language, e.g. 'Präsens', 'Presente'"
    )
    note: str = Field(default="", description="optional short note, e.g. 'compound tense'")
    cells: list[ConjugationCell] = Field(default_factory=list)


class ConjugationTable(BaseModel):
    """A full, language-agnostic conjugation table for a verb.

    Each language decides which tenses/moods and person labels appear (German
    uses ich/du/… with Präsens/Präteritum/…, Spanish uses yo/tú/… with
    Presente/Pretérito/…). Optional fields (``auxiliary``, ``partizip_ii``) are
    populated only where they apply.
    """

    infinitive: str = Field(description="the verb infinitive / citation form")
    language: str = Field(default="de", description="target language code, e.g. 'de', 'es'")
    english: str = Field(default="", description="short meaning in the learner's native language")
    regular: bool = Field(default=True, description="false for irregular/strong verbs")
    notes: str = Field(default="", description="short hint, e.g. stem change or separable prefix")
    auxiliary: str = Field(
        default="", description="compound-tense auxiliary if the language has one (e.g. 'haben')"
    )
    partizip_ii: str = Field(
        default="", description="past participle if the language has one (e.g. 'gearbeitet')"
    )
    tenses: list[ConjugationTense] = Field(
        default_factory=list, description="all tenses/moods, each with its personal forms"
    )


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
