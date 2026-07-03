"""Feedback agent: review a learner's free-text answer and report errors.

Used by open-ended exercises (writing, interpretation, reading) where there is no
single correct string to grade against. Instead of revealing a model answer, the
learner's text is sent to the model, which returns structured corrective feedback
in the target language, explained in the learner's native language.
"""

from __future__ import annotations

from sprachheft.languages import get_language, native_name
from sprachheft.llm import get_llm_client
from sprachheft.models import Exercise
from sprachheft.schemas import AnswerFeedback


def _system_prompt(target_lang: str, native_lang: str) -> str:
    profile = get_language(target_lang)
    tname = profile.name
    nname = native_name(native_lang)
    return (
        f"You are an expert {tname}-as-a-foreign-language teacher giving corrective feedback. The "
        f"student wrote an answer to an exercise. Check ONLY the student's {tname} for "
        "correctness: grammar, spelling, capitalisation, word order, case, agreement, verb "
        "forms, and word choice.\n\n"
        "Return structured feedback:\n"
        "- has_errors: true if there is at least one mistake, otherwise false.\n"
        "- errors: one entry per mistake. Give the original snippet from the student's text, the "
        f"correction, and a short explanation in {nname} of the underlying rule. Return an empty "
        "list when there are no mistakes.\n"
        f"- corrected: the student's full answer rewritten in correct {tname}, preserving their "
        "meaning. If the answer is already correct, repeat it unchanged.\n"
        f"- summary: one or two encouraging sentences (in {nname}) summarising how the student "
        "did.\n\n"
        "Judge at the exercise's level; do not demand vocabulary or structures beyond it. If the "
        f"answer is empty or clearly not in {tname}, set has_errors to true and explain in the "
        "summary."
    )


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


def build_messages(exercise: Exercise, answer: str, native_lang: str = "en") -> list[dict]:
    user = f"{_context(exercise)}\n\nSTUDENT ANSWER:\n{answer.strip()}\n"
    return [
        {"role": "system", "content": _system_prompt(exercise.target_lang, native_lang)},
        {"role": "user", "content": user},
    ]


def evaluate(exercise: Exercise, answer: str, native_lang: str = "en") -> AnswerFeedback:
    client = get_llm_client()
    messages = build_messages(exercise, answer, native_lang)
    return client.generate_structured(messages, AnswerFeedback)
