"""Generation agent: transcript -> vocabulary + exercises (structured output).

Generation is split into small, focused LLM calls (vocabulary, then exercises in
small batches by type). Local models are slow, so keeping each call small makes
generation faster, more reliable, and lets the caller persist results
incrementally. The instructions mirror ``prompts/generate-exercises.prompt.md``.
"""

from __future__ import annotations

from sprachheft.llm import get_llm_client
from sprachheft.models import Material
from sprachheft.schemas import ExerciseBatch, GenExercise, GenVocab, VocabBatch

VOCAB_SYSTEM_PROMPT = """You are an expert German-as-a-foreign-language (DaF) teacher. \
From a German transcript and a target CEFR level, extract 8-12 vocabulary items that \
actually occur in the transcript (skip trivial function words and proper names). For \
nouns, write the article shorthand r/e/s (= der/die/das). For each item give: word, \
lemma, part of speech, a concise English meaning, one short example (German + English), \
a CEFR tag, and grammar tags (lowercase kebab codes). Use correct, natural German. \
Return only the vocabulary list."""

EXERCISE_SYSTEM_PROMPT = """You are an expert German-as-a-foreign-language (DaF) teacher \
and assessment item-writer. From a German transcript, a target CEFR level, a STAGE, and a \
list of requested exercise TYPES, produce exactly ONE exercise for EACH requested type, \
drilling the transcript's grammar and vocabulary.

STAGE controls scaffolding and hints DECREASE as STAGE rises:
- 1 = just introduced: maximum help (word banks, English + German instructions); put \
hints in payload.hints.
- 2 = practising: some hints.
- 3 = confident: German instructions, at most a short tip.
- 4 = consolidating: German only, NO hints (payload.hints must be empty), free production.

Keep every item within the CEFR level and solvable from the transcript. Use correct, \
natural German. Fill answer keys for every exercise. Return only the exercises."""


def _user_context(material: Material) -> str:
    user = f"LEVEL: {material.level}\nTITLE: {material.title}\nTRANSCRIPT:\n{material.transcript}\n"
    if material.translation:
        user += f"TRANSLATION:\n{material.translation}\n"
    return user


def generate_vocabulary(material: Material, stage: int = 2) -> list[GenVocab]:
    """Generate the vocabulary list only (one small, fast call)."""
    client = get_llm_client()
    messages = [
        {"role": "system", "content": VOCAB_SYSTEM_PROMPT},
        {"role": "user", "content": _user_context(material)},
    ]
    return client.generate_structured(messages, VocabBatch).vocabulary


def generate_exercises(
    material: Material, stage: int, types: list[str]
) -> list[GenExercise]:
    """Generate one exercise for each requested type (one small batch call)."""
    client = get_llm_client()
    user = (
        f"LEVEL: {material.level}\n"
        f"STAGE: {stage}\n"
        f"TYPES: {', '.join(types)}\n"
        f"TITLE: {material.title}\n"
        f"TRANSCRIPT:\n{material.transcript}\n"
    )
    if material.translation:
        user += f"TRANSLATION:\n{material.translation}\n"
    messages = [
        {"role": "system", "content": EXERCISE_SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
    return client.generate_structured(messages, ExerciseBatch).exercises


SINGLE_SYSTEM_PROMPT = """You are an expert German-as-a-foreign-language (DaF) teacher and \
assessment item-writer. From a German transcript, a target CEFR level, a STAGE, and a \
required exercise TYPE, produce exactly ONE exercise of that TYPE that drills the \
transcript's grammar and vocabulary.

STAGE controls scaffolding and hints DECREASE as STAGE rises (1 = maximum help with word \
banks and hints in payload.hints; 4 = German only, no hints, free production).

The exercise must be a fresh alternative: do NOT reuse any of the AVOID prompts — change \
the sentences, blanks, options or tokens. Keep it within the CEFR level, solvable from the \
transcript, in correct natural German, and fill the answer key completely. Return only the \
single exercise object."""


def build_single_messages(
    material: Material, ex_type: str, stage: int, avoid: list[str]
) -> list[dict]:
    user = (
        f"LEVEL: {material.level}\n"
        f"STAGE: {stage}\n"
        f"TYPE: {ex_type}\n"
        f"TITLE: {material.title}\n"
        f"TRANSCRIPT:\n{material.transcript}\n"
    )
    if material.translation:
        user += f"TRANSLATION:\n{material.translation}\n"
    if avoid:
        joined = "\n".join(f"- {p}" for p in avoid if p)
        user += f"AVOID (already used, make something different):\n{joined}\n"
    return [
        {"role": "system", "content": SINGLE_SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def generate_one(
    material: Material,
    ex_type: str,
    stage: int = 2,
    avoid: list[str] | None = None,
) -> GenExercise:
    """Generate a single new exercise of ``ex_type`` (a variant)."""
    client = get_llm_client()
    messages = build_single_messages(material, ex_type, stage, avoid or [])
    return client.generate_structured(messages, GenExercise)
