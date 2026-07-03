"""Importer agent: normalize pasted learning material into the exercise schema."""

from __future__ import annotations

from sprachheft.languages import get_language, native_name
from sprachheft.llm import get_llm_client
from sprachheft.schemas import GenerationResult


def _system_prompt(target_lang: str, native_lang: str) -> str:
    profile = get_language(target_lang)
    tname = profile.name
    nname = native_name(native_lang)
    fw = profile.level_framework
    return (
        f"You convert pasted {tname} learning material (grammar explanations and/or exercises) "
        "into structured study data. Extract useful vocabulary and normalize any exercises into "
        "these types only: fill-in-blank, conjugation, translation, multiple-choice, reorder, "
        "reading, interpretation, writing. Preserve the original exercises' intent, always provide "
        "answer keys, and tag grammar_tags (lowercase kebab codes). Keep everything at the given "
        f"{fw} level and use correct, natural {tname}. Write meanings and explanations in {nname}."
    )


def normalize(
    raw_text: str,
    level: str,
    target_lang: str = "de",
    native_lang: str = "en",
) -> GenerationResult:
    client = get_llm_client()
    messages = [
        {"role": "system", "content": _system_prompt(target_lang, native_lang)},
        {"role": "user", "content": f"LEVEL: {level}\nCONTENT:\n{raw_text}\n"},
    ]
    return client.generate_structured(messages, GenerationResult)
