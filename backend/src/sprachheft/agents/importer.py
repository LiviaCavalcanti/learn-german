"""Importer agent: normalize pasted German material into the exercise schema."""

from __future__ import annotations

from sprachheft.llm import get_llm_client
from sprachheft.schemas import GenerationResult

IMPORT_SYSTEM_PROMPT = """You convert pasted German learning material (grammar \
explanations and/or exercises) into structured study data. Extract useful vocabulary and \
normalize any exercises into these types only: fill-in-blank, conjugation, translation, \
multiple-choice, reorder, reading, interpretation, writing. Preserve the original \
exercises' intent, always provide answer keys, and tag grammar_tags (lowercase kebab \
codes). Keep everything at the given CEFR level and use correct, natural German."""


def normalize(raw_text: str, level: str) -> GenerationResult:
    client = get_llm_client()
    messages = [
        {"role": "system", "content": IMPORT_SYSTEM_PROMPT},
        {"role": "user", "content": f"LEVEL: {level}\nCONTENT:\n{raw_text}\n"},
    ]
    return client.generate_structured(messages, GenerationResult)
