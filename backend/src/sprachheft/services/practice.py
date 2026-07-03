"""Practice: auto-check answers for objective exercises; reveal for open ones."""

from __future__ import annotations

from sprachheft.models import Exercise

_GRADABLE = {"fill-in-blank", "conjugation", "translation", "multiple-choice", "reorder"}


def _norm(value: object) -> str:
    return " ".join(str(value or "").strip().casefold().split()).rstrip(".!?,;:")


def _expected(exercise: Exercise) -> list[list[str]]:
    answer_key = exercise.answer_key or {}
    items = answer_key.get("items")
    # Fallback: some models attach the answers to the payload items instead of the
    # answer key. Without this the grader finds nothing and always scores 0.
    if not isinstance(items, list) or not items:
        payload_items = (exercise.payload or {}).get("items")
        if isinstance(payload_items, list):
            items = [
                it
                for it in payload_items
                if isinstance(it, dict) and it.get("answer") is not None
            ]
    expected: list[list[str]] = []
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                expected.append([str(item)])
                continue
            answer = item.get("answer")
            accept = item.get("accept") or []
            variants = [str(v) for v in [answer, *accept] if v is not None]
            expected.append(variants)
    return expected


def check_exercise(exercise: Exercise, responses: list[str]) -> dict:
    etype = exercise.type
    if etype not in _GRADABLE:
        return {"gradable": False, "type": etype, "answer_key": exercise.answer_key or {}}

    expected = _expected(exercise)
    items: list[dict] = []
    correct = 0
    for index, variants in enumerate(expected):
        given = responses[index] if index < len(responses) else ""
        ok = any(_norm(variant) == _norm(given) for variant in variants)
        if ok:
            correct += 1
        items.append(
            {"given": given, "expected": variants[0] if variants else "", "correct": ok}
        )
    total = len(expected)
    return {
        "gradable": True,
        "type": etype,
        "items": items,
        "correct": correct,
        "total": total,
        "all_correct": total > 0 and correct == total,
    }


def evaluate_answer(exercise: Exercise, answer: str, native_lang: str = "en"):
    """Ask the LLM to assess a free-text answer against its reference and flag errors."""
    from sprachheft.agents.feedback import evaluate

    return evaluate(exercise, answer, native_lang)
