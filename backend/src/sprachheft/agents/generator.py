"""Generation agent: transcript -> vocabulary + exercises (structured output).

The system prompt mirrors ``prompts/generate-exercises.prompt.md`` so the in-app
agent and the standalone prompt pack stay aligned.
"""

from __future__ import annotations

from sprachheft.llm import get_llm_client
from sprachheft.models import Material
from sprachheft.schemas import GenerationResult

SYSTEM_PROMPT = """You are an expert German-as-a-foreign-language (DaF) teacher and \
assessment item-writer. From a German transcript, a target CEFR level, and a STAGE, produce:

1) 10-15 vocabulary items that actually occur in the transcript (skip trivial function \
words and proper names). For nouns, write the article shorthand r/e/s (= der/die/das). \
Give lemma, part of speech, a concise English meaning, one short example (German + \
English), a CEFR tag, and grammar tags (lowercase kebab codes).
2) Exercises drilling the transcript's grammar and vocabulary, using these types only: \
fill-in-blank, conjugation, translation, multiple-choice, reorder, reading, \
interpretation, writing. Include exactly one interpretation exercise and exactly one \
themed writing exercise.

STAGE controls scaffolding and hints DECREASE as STAGE rises:
- 1 = just introduced: maximum help (word banks, English + German instructions, more \
multiple-choice); put hints in payload.hints.
- 2 = practising: some hints.
- 3 = confident: German instructions, at most a short tip.
- 4 = consolidating: German only, NO hints (payload.hints must be empty), free production.

Keep every item within the CEFR level and solvable from the transcript. Use correct, \
natural German. Fill answer keys for every exercise."""


def build_messages(material: Material, stage: int) -> list[dict]:
    user = (
        f"LEVEL: {material.level}\n"
        f"STAGE: {stage}\n"
        f"TITLE: {material.title}\n"
        f"TRANSCRIPT:\n{material.transcript}\n"
    )
    if material.translation:
        user += f"TRANSLATION:\n{material.translation}\n"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def generate(material: Material, stage: int = 2) -> GenerationResult:
    client = get_llm_client()
    messages = build_messages(material, stage)
    return client.generate_structured(messages, GenerationResult)
