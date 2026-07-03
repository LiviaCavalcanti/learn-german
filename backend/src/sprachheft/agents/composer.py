"""Composer agent: a set of learned words -> a practice text + exercises.

Given vocabulary the learner already collected, write a short German text that
uses those words in context and a couple of exercises that drill them. The
result is persisted as a normal Material so it lives in the library, practice,
and review flows.
"""

from __future__ import annotations

from sprachheft.models import VocabItem
from sprachheft.schemas import ComposedText

SYSTEM_PROMPT = """You are an expert German-as-a-foreign-language (DaF) teacher. Given a \
list of German vocabulary words (with English meanings) and a target CEFR level, write a \
short, coherent German text (4-10 short paragraphs or a brief dialogue) that naturally uses \
ALL of the given words. Then create 2-3 exercises that drill those words and the text's \
grammar, using only these types: fill-in-blank, conjugation, translation, multiple-choice, \
reorder, reading, writing. Include at least one exercise that practises the given words and \
one short writing task.

Keep the text and exercises within the CEFR level and in correct, natural German. Fill every \
answer key completely. Return a title, the German text, and the exercises."""


def build_messages(
    items: list[VocabItem], level: str, instructions: str | None
) -> list[dict]:
    words = "\n".join(f"- {v.word} — {v.meaning_en}" for v in items)
    user = f"LEVEL: {level}\nWORDS:\n{words}\n"
    if instructions:
        user += f"INSTRUCTIONS: {instructions}\n"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def compose(
    items: list[VocabItem],
    level: str = "A2",
    instructions: str | None = None,
) -> ComposedText:
    """Compose a text + exercises that practise ``items`` at ``level``."""
    from sprachheft.llm import get_llm_client

    client = get_llm_client()
    messages = build_messages(items, level, instructions)
    return client.generate_structured(messages, ComposedText)
