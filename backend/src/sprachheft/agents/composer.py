"""Composer agent: a set of learned words -> a practice text + exercises.

Given vocabulary the learner already collected, write a short text in the target
language that uses those words in context and a couple of exercises that drill
them. The result is persisted as a normal Material so it lives in the library,
practice, and review flows.
"""

from __future__ import annotations

from sprachheft.languages import get_language, native_name
from sprachheft.models import VocabItem
from sprachheft.schemas import ComposedText


def _system_prompt(target_lang: str, native_lang: str) -> str:
    profile = get_language(target_lang)
    tname = profile.name
    nname = native_name(native_lang)
    fw = profile.level_framework
    return (
        f"You are an expert {tname}-as-a-foreign-language teacher. Given a list of {tname} "
        f"vocabulary words (with {nname} meanings) and a target {fw} level, write a short, "
        f"coherent {tname} text (4-10 short paragraphs or a brief dialogue) that naturally uses "
        "ALL of the given words. Then create 2-3 exercises that drill those words and the "
        "text's grammar, "
        "using only these types: fill-in-blank, conjugation, translation, multiple-choice, "
        "reorder, reading, writing. Include at least one exercise that practises the given "
        "words and one short writing task.\n\n"
        f"Keep the text and exercises within the {fw} level and in correct, natural {tname}. "
        f"Fill every answer key completely. Return a title, the {tname} text, and the exercises."
    )


def build_messages(
    items: list[VocabItem],
    level: str,
    instructions: str | None,
    target_lang: str,
    native_lang: str,
) -> list[dict]:
    words = "\n".join(f"- {v.word} — {v.meaning_en}" for v in items)
    user = f"LEVEL: {level}\nWORDS:\n{words}\n"
    if instructions:
        user += f"INSTRUCTIONS: {instructions}\n"
    return [
        {"role": "system", "content": _system_prompt(target_lang, native_lang)},
        {"role": "user", "content": user},
    ]


def compose(
    items: list[VocabItem],
    level: str = "A2",
    instructions: str | None = None,
    target_lang: str = "de",
    native_lang: str = "en",
) -> ComposedText:
    """Compose a text + exercises that practise ``items`` at ``level``."""
    from sprachheft.llm import get_llm_client

    client = get_llm_client()
    messages = build_messages(items, level, instructions, target_lang, native_lang)
    return client.generate_structured(messages, ComposedText)
