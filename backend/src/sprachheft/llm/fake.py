"""Deterministic offline LLM client for tests and no-network development.

Derives a few plausible items from the transcript so the end-to-end generation
flow can be exercised without any model. Not a real generator.
"""

from __future__ import annotations

import re

from sprachheft.schemas import GenerationResult, GenExercise, GenVocab

_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß]{4,}")
_STOP = {"heute", "eine", "einen", "meine", "meiner", "diese", "dieser", "haben", "sein"}


def _pick_words(text: str, n: int = 3) -> list[str]:
    picked: list[str] = []
    for match in _WORD_RE.findall(text or ""):
        if match.lower() in _STOP:
            continue
        if match.lower() not in {p.lower() for p in picked}:
            picked.append(match)
        if len(picked) >= n:
            break
    return picked


class FakeLLMClient:
    def generate_structured(self, messages: list[dict], response_model, **kwargs):
        transcript = ""
        for message in messages:
            if message.get("role") == "user":
                transcript = message.get("content", "")

        words = _pick_words(transcript) or ["Alltag", "lernen", "wichtig"]
        vocabulary = [
            GenVocab(
                word=word,
                lemma=word.lower(),
                pos="noun" if word[:1].isupper() else "verb",
                meaning_en=f"(meaning of {word})",
                cefr="A2",
                example_de=f"{word} kommt im Text vor.",
                example_en=f"{word} appears in the text.",
                grammar_tags=[],
            )
            for word in words[:3]
        ]
        first = words[0] if words else "Wort"
        exercises = [
            GenExercise(
                type="fill-in-blank",
                cefr="A2",
                grammar_tags=[],
                instructions="Setze das fehlende Wort ein.",
                payload={"items": [{"prompt": "Das ___ ist wichtig.", "hint": first}], "hints": []},
                answer_key={"items": [{"answer": first}]},
            ),
            GenExercise(
                type="writing",
                cefr="A2",
                grammar_tags=[],
                instructions="Schreibe ein paar Sätze zum Thema.",
                payload={
                    "theme": "Alltag",
                    "task": "Schreibe 3–5 Sätze über deinen Tag.",
                    "target_length": "40–60 Wörter",
                    "useful_phrases": [],
                    "checklist": ["Perfekt benutzen"],
                    "hints": [],
                },
                answer_key={
                    "model_answer": "Heute habe ich gearbeitet.",
                    "rubric": ["Thema getroffen"],
                },
            ),
        ]
        result = GenerationResult(themes=["Alltag"], vocabulary=vocabulary, exercises=exercises)
        if response_model is GenerationResult:
            return result
        return response_model.model_validate(result.model_dump())
