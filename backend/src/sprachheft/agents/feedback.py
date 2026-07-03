"""Feedback agent: assess a learner's free-text answer against a reference.

Used by open-ended exercises (writing, interpretation, reading) and course
comprehension questions, where there is no single string to match. The model
compares the answer to a reference/model answer for correctness (verdict + score)
and checks the learner's target language for mistakes, explained in their native
language.
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
        f"You are an expert {tname}-as-a-foreign-language teacher marking a student's answer. You "
        "are given the QUESTION or TASK, a REFERENCE ANSWER (the expected answer; it may be "
        "empty), and the STUDENT ANSWER.\n\n"
        "Do two things:\n"
        "1. Correctness \u2014 compare the MEANING of the student's answer with the reference (not "
        "word for word). Set:\n"
        "   - verdict: 'correct' (matches the reference and fully answers the question), 'partial' "
        "(partly right or incomplete), 'incorrect' (wrong or off-topic), or 'unanswered' (empty).\n"
        "   - score: a number from 0.0 to 1.0 for how well it matches the reference.\n"
        "   If the reference is empty, judge correctness from the question alone.\n"
        f"2. Language \u2014 check the student's {tname} for grammar, spelling, capitalisation, word "
        "order, case, agreement, verb forms and word choice. Set has_errors, list each mistake in "
        f"errors (original snippet, correction, short {nname} explanation), and set corrected to "
        f"the answer rewritten in correct {tname} (repeat it unchanged if already correct).\n\n"
        f"summary: one or two encouraging sentences (in {nname}) that say whether the content is "
        "right and give the main language tip. Judge at the exercise's level; do not demand "
        f"structures beyond it. If the answer is empty or clearly not in {tname}, set the verdict "
        "accordingly and has_errors true, and explain in the summary."
    )


def _reference_for(exercise: Exercise) -> str:
    """Best available reference/model answer for an exercise, from its answer key."""
    ak = exercise.answer_key or {}
    if ak.get("model_answer"):
        return str(ak["model_answer"])
    if ak.get("reference"):
        return str(ak["reference"])
    items = ak.get("items")
    if isinstance(items, list):
        answers = [
            str(it.get("answer"))
            for it in items
            if isinstance(it, dict) and it.get("answer") is not None
        ]
        if answers:
            return " / ".join(answers)
    return ""


def _question_for(exercise: Exercise) -> str:
    payload = exercise.payload or {}
    parts: list[str] = []
    if exercise.instructions:
        parts.append(exercise.instructions)
    for key in ("prompt", "task", "theme", "text"):
        value = payload.get(key)
        if value:
            parts.append(f"{key}: {value}")
    guiding = payload.get("guiding_points")
    if isinstance(guiding, list) and guiding:
        parts.append("guiding points: " + "; ".join(str(g) for g in guiding))
    return "\n".join(parts)


def _user_message(question: str, reference: str, answer: str, level: str, etype: str) -> str:
    return (
        f"EXERCISE TYPE: {etype}\n"
        f"LEVEL: {level}\n"
        f"QUESTION:\n{question.strip()}\n\n"
        f"REFERENCE ANSWER:\n{reference.strip()}\n\n"
        f"STUDENT ANSWER:\n{answer.strip()}\n"
    )


def evaluate_open(
    *,
    question: str,
    reference: str,
    answer: str,
    target_lang: str = "de",
    native_lang: str = "en",
    level: str = "A2",
    exercise_type: str = "reading",
) -> AnswerFeedback:
    """Assess a free-text answer against a reference (question / reference / answer)."""
    client = get_llm_client()
    messages = [
        {"role": "system", "content": _system_prompt(target_lang, native_lang)},
        {
            "role": "user",
            "content": _user_message(question, reference, answer, level, exercise_type),
        },
    ]
    feedback = client.generate_structured(messages, AnswerFeedback)
    feedback.reference = reference  # authoritative reference, revealed after checking
    return feedback


def evaluate(exercise: Exercise, answer: str, native_lang: str = "en") -> AnswerFeedback:
    return evaluate_open(
        question=_question_for(exercise),
        reference=_reference_for(exercise),
        answer=answer,
        target_lang=exercise.target_lang,
        native_lang=native_lang,
        level=exercise.cefr or "A2",
        exercise_type=exercise.type,
    )
