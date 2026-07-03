"""Generation agent: transcript -> vocabulary + exercises (structured output).

Generation is split into small, focused LLM calls (vocabulary, then exercises in
small batches by type). Local models are slow, so keeping each call small makes
generation faster, more reliable, and lets the caller persist results
incrementally. The instructions mirror ``prompts/generate-exercises.prompt.md``.
"""

from __future__ import annotations

from sprachheft.languages import get_language, native_name
from sprachheft.llm import get_llm_client
from sprachheft.models import Material
from sprachheft.schemas import ExerciseBatch, GenExercise, GenVocab, VocabBatch


def _vocab_system_prompt(material: Material) -> str:
    profile = get_language(material.source_lang)
    tname = profile.name
    nname = native_name(material.native_lang)
    fw = profile.level_framework
    return (
        f"You are an expert {tname}-as-a-foreign-language teacher. From a {tname} transcript and a "
        f"target {fw} level, extract 8-12 vocabulary items that actually occur in the transcript "
        f"(skip trivial function words and proper names). {profile.article_note} For each item "
        f"give: word, lemma, part of speech, a concise {nname} meaning, one short example (in "
        f"{tname} plus its {nname} translation), a {fw} tag, and grammar tags (lowercase kebab "
        f"codes). Use correct, natural {tname}. Return only the vocabulary list."
    )


def _exercise_system_prompt(material: Material) -> str:
    profile = get_language(material.source_lang)
    tname = profile.name
    nname = native_name(material.native_lang)
    fw = profile.level_framework
    return (
        f"You are an expert {tname}-as-a-foreign-language teacher and assessment item-writer. From "
        f"a {tname} transcript, a target {fw} level, a STAGE, and a list of requested exercise "
        "TYPES, produce exactly ONE exercise for EACH requested type, drilling the transcript's "
        "grammar and vocabulary.\n\n"
        "STAGE controls scaffolding and hints DECREASE as STAGE rises:\n"
        f"- 1 = just introduced: maximum help (word banks, {nname} + {tname} instructions); put "
        "hints in payload.hints.\n"
        "- 2 = practising: some hints.\n"
        f"- 3 = confident: {tname} instructions, at most a short tip.\n"
        f"- 4 = consolidating: {tname} only, NO hints (payload.hints must be empty), free "
        "production.\n\n"
        f"Keep every item within the {fw} level and solvable from the transcript. Use correct, "
        f"natural {tname}. Fill answer keys for every exercise. For open types the answer key MUST "
        "carry a reference the learner is graded against: reading -> answer_key.items[].answer for "
        "each question; interpretation and writing -> answer_key.model_answer (a full model "
        "answer) plus a short rubric. Return only the exercises."
    )


def _single_system_prompt(material: Material) -> str:
    profile = get_language(material.source_lang)
    tname = profile.name
    fw = profile.level_framework
    return (
        f"You are an expert {tname}-as-a-foreign-language teacher and assessment item-writer. From "
        f"a {tname} transcript, a target {fw} level, a STAGE, and a required exercise TYPE, "
        "produce exactly ONE exercise of that TYPE that drills the transcript's grammar and "
        "vocabulary.\n\n"
        "STAGE controls scaffolding and hints DECREASE as STAGE rises (1 = maximum help with "
        "word banks and hints in payload.hints; 4 = target language only, no hints, free "
        "production).\n\n"
        "The exercise must be a fresh alternative: do NOT reuse any of the AVOID prompts — change "
        f"the sentences, blanks, options or tokens. Keep it within the {fw} level, solvable from "
        f"transcript, in correct natural {tname}, and fill the answer key completely (for open "
        "types include a reference: reading -> answer_key.items[].answer; interpretation and "
        "writing -> answer_key.model_answer). Return only the single exercise object."
    )


def _user_context(material: Material) -> str:
    user = f"LEVEL: {material.level}\nTITLE: {material.title}\nTRANSCRIPT:\n{material.transcript}\n"
    if material.translation:
        user += f"TRANSLATION:\n{material.translation}\n"
    return user


def generate_vocabulary(material: Material, stage: int = 2) -> list[GenVocab]:
    """Generate the vocabulary list only (one small, fast call)."""
    client = get_llm_client()
    messages = [
        {"role": "system", "content": _vocab_system_prompt(material)},
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
        {"role": "system", "content": _exercise_system_prompt(material)},
        {"role": "user", "content": user},
    ]
    return client.generate_structured(messages, ExerciseBatch).exercises


def build_single_messages(
    material: Material,
    ex_type: str,
    stage: int,
    avoid: list[str],
    *,
    difficulty: str | None = None,
    level: str | None = None,
) -> list[dict]:
    user = (
        f"LEVEL: {level or material.level}\n"
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
    if difficulty == "easier":
        user += (
            "DIFFICULTY: Make this noticeably EASIER than the AVOID items — simpler, "
            "higher-frequency vocabulary, shorter sentences, and more support.\n"
        )
    elif difficulty == "harder":
        user += (
            "DIFFICULTY: Make this noticeably HARDER than the AVOID items — richer "
            "vocabulary, longer and more complex sentences, and less support.\n"
        )
    return [
        {"role": "system", "content": _single_system_prompt(material)},
        {"role": "user", "content": user},
    ]


def generate_one(
    material: Material,
    ex_type: str,
    stage: int = 2,
    avoid: list[str] | None = None,
    *,
    difficulty: str | None = None,
    level: str | None = None,
) -> GenExercise:
    """Generate a single new exercise of ``ex_type`` (a variant, optionally easier/harder)."""
    client = get_llm_client()
    messages = build_single_messages(
        material, ex_type, stage, avoid or [], difficulty=difficulty, level=level
    )
    return client.generate_structured(messages, GenExercise)


def _one_vocab_system_prompt(material: Material, difficulty: str | None) -> str:
    profile = get_language(material.source_lang)
    tname = profile.name
    nname = native_name(material.native_lang)
    fw = profile.level_framework
    adj = ""
    if difficulty == "easier":
        adj = f" Choose an EASIER, higher-frequency {tname} word than the ones to AVOID."
    elif difficulty == "harder":
        adj = f" Choose a HARDER, less common {tname} word than the ones to AVOID."
    return (
        f"You are an expert {tname}-as-a-foreign-language teacher. Suggest exactly ONE {tname} "
        f"vocabulary item that fits the transcript and the target {fw} level.{adj} "
        f"{profile.article_note} Give: word, lemma, part of speech, a concise {nname} meaning, one "
        f"short example (in {tname} plus its {nname} translation), a {fw} tag, and grammar tags "
        f"(lowercase kebab codes). Use correct, natural {tname}. Return only the single item."
    )


def generate_one_vocab(
    material: Material,
    avoid: list[str] | None = None,
    *,
    difficulty: str | None = None,
    level: str | None = None,
) -> GenVocab:
    """Generate a single replacement vocabulary item (optionally easier/harder)."""
    client = get_llm_client()
    user = (
        f"LEVEL: {level or material.level}\n"
        f"TITLE: {material.title}\n"
        f"TRANSCRIPT:\n{material.transcript}\n"
    )
    if avoid:
        joined = ", ".join(a for a in avoid if a)
        user += f"AVOID (already known, pick a different word):\n{joined}\n"
    messages = [
        {"role": "system", "content": _one_vocab_system_prompt(material, difficulty)},
        {"role": "user", "content": user},
    ]
    return client.generate_structured(messages, GenVocab)
