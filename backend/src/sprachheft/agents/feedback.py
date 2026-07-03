"""Feedback agent: review a learner's free-text answer and report German errors.

Used by open-ended exercises (writing, interpretation, reading) where there is no
single correct string to grade against. Instead of revealing a model answer, the
learner's text is sent to the model, which returns structured corrective feedback.
"""

from __future__ import annotations

from sprachheft.llm import get_llm_client
from sprachheft.models import Exercise
from sprachheft.schemas import AnswerFeedback

SYSTEM_PROMPT = """You are an expert German-as-a-foreign-language (DaF) teacher giving \
corrective feedback. The student wrote an answer to an exercise. Check ONLY the student's \
German for correctness: grammar, spelling, capitalisation, word order, case, agreement, verb \
forms, and word choice.

Return structured feedback:
- has_errors: true if there is at least one mistake, otherwise false.
- errors: one entry per mistake. Give the original snippet from the student's text, the \
correction, and a short explanation in English of the underlying rule. Return an empty list \
when there are no mistakes.
- corrected: the student's full answer rewritten in correct German, preserving their meaning. \
If the answer is already correct, repeat it unchanged.
- summary: one or two encouraging sentences (in English) summarising how the student did.

Judge at the exercise's CEFR level; do not demand vocabulary or structures beyond it. If the \
answer is empty or clearly not in German, set has_errors to true and explain in the summary."""


def _context(exercise: Exercise) -> str:
    payload = exercise.payload or {}
    lines = [f"EXERCISE TYPE: {exercise.type}", f"LEVEL: {exercise.cefr or 'A2'}"]
    if exercise.instructions:
        lines.append(f"INSTRUCTIONS: {exercise.instructions}")
    for key in ("prompt", "task", "theme", "text"):
        value = payload.get(key)
        if value:
            lines.append(f"{key.upper()}: {value}")
    guiding = payload.get("guiding_points")
    if isinstance(guiding, list) and guiding:
        lines.append("GUIDING POINTS: " + "; ".join(str(g) for g in guiding))
    return "\n".join(lines)


def build_messages(exercise: Exercise, answer: str) -> list[dict]:
    user = f"{_context(exercise)}\n\nSTUDENT ANSWER:\n{answer.strip()}\n"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def evaluate(exercise: Exercise, answer: str) -> AnswerFeedback:
    client = get_llm_client()
    messages = build_messages(exercise, answer)
    return client.generate_structured(messages, AnswerFeedback)
