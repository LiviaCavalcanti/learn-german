"""Conjugation agent: a verb (in any form) -> full conjugation table.

The input may be inflected (e.g. ``habe``, ``ging``); a lemmatizer provides an
infinitive hint and the model produces the complete table as structured output.
The prompt adapts to the target language: German keeps its familiar tense set,
other languages get a generic instruction to emit whatever tenses/moods and
person labels that language uses.
"""

from __future__ import annotations

from sprachheft.dictionary.lemmatize import lemmatize
from sprachheft.languages import get_language
from sprachheft.llm import get_llm_client
from sprachheft.schemas import ConjugationTable

GERMAN_SYSTEM_PROMPT = """You are an expert German teacher. Given a single German verb — which \
may be given in any conjugated form — identify its infinitive and produce a complete, correct \
conjugation table.

Rules:
- Determine the true infinitive (e.g. 'habe' -> 'haben', 'ging' -> 'gehen', 'gearbeitet' -> \
'arbeiten').
- Return these tenses/moods as entries in `tenses`, each named in German: Präsens, Präteritum, \
Perfekt (auxiliary + past participle, e.g. 'habe gearbeitet'), Futur I (e.g. 'werde arbeiten'), \
Konjunktiv II (the simple form for strong/auxiliary verbs such as 'wäre', 'hätte', 'ginge', \
otherwise the 'würde' + infinitive form), and Imperativ.
- For each tense give one cell per person, labelled: ich, du, er/sie/es, wir, ihr, sie/Sie. \
For Imperativ give cells labelled du, ihr, Sie.
- auxiliary is 'haben' or 'sein'. partizip_ii is the past participle.
- Use correct German, including irregular/strong stem changes and separable prefixes.
- Set regular=false for strong/irregular verbs and put a short hint in notes (e.g. \
'strong verb, stem change e→i' or 'separable: an|rufen'). english is a brief gloss. \
Set language to 'de'."""


def _generic_system_prompt(lang: str) -> str:
    profile = get_language(lang)
    name = profile.name
    return (
        f"You are an expert {name} teacher. Given a single {name} verb — which may be given in "
        "any conjugated form — identify its infinitive (citation form) and produce a complete, "
        "correct conjugation table.\n\n"
        "Rules:\n"
        "- Determine the true infinitive.\n"
        f"- Return the tenses and moods a {name} learner needs as entries in `tenses` (the main "
        "indicative tenses, plus subjunctive/conditional and imperative where the language has "
        "them). Name each tense/mood in the target language.\n"
        "- For each tense give one cell per person/number the language distinguishes, labelling "
        f"each cell with the natural {name} form (e.g. the subject pronoun).\n"
        "- Fill auxiliary and partizip_ii only if the language uses a compound past with a "
        "participle; otherwise leave them empty.\n"
        "- Set regular=false for irregular verbs and put a short hint in notes. english is a brief "
        f"gloss. Set language to '{lang}'."
    )


def system_prompt(lang: str) -> str:
    return GERMAN_SYSTEM_PROMPT if lang == "de" else _generic_system_prompt(lang)


def build_messages(verb: str, infinitive_hint: str, lang: str) -> list[dict]:
    user = f"LANG: {lang}\nVERB: {verb}\n"
    if infinitive_hint and infinitive_hint.lower() != verb.lower():
        user += f"LIKELY INFINITIVE (lemmatizer hint, verify it): {infinitive_hint}\n"
    return [
        {"role": "system", "content": system_prompt(lang)},
        {"role": "user", "content": user},
    ]


def conjugate(verb: str, lang: str = "de") -> ConjugationTable:
    client = get_llm_client()
    cleaned = verb.strip()
    profile = get_language(lang)
    hint = lemmatize(cleaned, profile.lemmatizer) if profile.lemmatizer else cleaned
    messages = build_messages(cleaned, hint, profile.code)
    table = client.generate_structured(messages, ConjugationTable)
    if not table.language:
        table.language = profile.code
    return table
