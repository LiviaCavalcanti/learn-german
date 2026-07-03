"""Conjugation agent: a German verb (in any form) -> full conjugation table.

The input may be inflected (e.g. ``habe``, ``ging``); a lemmatizer provides an
infinitive hint and the model produces the complete table as structured output.
"""

from __future__ import annotations

from sprachheft.dictionary.lemmatize import lemmatize
from sprachheft.llm import get_llm_client
from sprachheft.schemas import ConjugationTable

SYSTEM_PROMPT = """You are an expert German teacher. Given a single German verb — which may \
be given in any conjugated form — identify its infinitive and produce a complete, correct \
conjugation table.

Rules:
- Determine the true infinitive (e.g. 'habe' -> 'haben', 'ging' -> 'gehen', 'gearbeitet' -> \
'arbeiten').
- Fill every person for each tense: ich, du, er/sie/es, wir, ihr, sie/Sie.
- present = Präsens; praeteritum = Präteritum; perfekt = Perfekt (auxiliary + past \
participle, e.g. 'habe gearbeitet'); futur1 = Futur I (e.g. 'werde arbeiten'); \
konjunktiv2 = Konjunktiv II (the simple form for strong/auxiliary verbs such as 'wäre', \
'hätte', 'ginge', otherwise the 'würde' + infinitive form).
- auxiliary is 'haben' or 'sein'. partizip_ii is the past participle.
- imperative: the du, ihr and Sie forms.
- Use correct German, including irregular/strong stem changes and separable prefixes.
- Set regular=false for strong/irregular verbs and put a short hint in notes (e.g. \
'strong verb, stem change e→i' or 'separable: an|rufen'). english is a brief gloss."""


def build_messages(verb: str, infinitive_hint: str) -> list[dict]:
    user = f"VERB: {verb}\n"
    if infinitive_hint and infinitive_hint.lower() != verb.lower():
        user += f"LIKELY INFINITIVE (lemmatizer hint, verify it): {infinitive_hint}\n"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def conjugate(verb: str) -> ConjugationTable:
    client = get_llm_client()
    cleaned = verb.strip()
    messages = build_messages(cleaned, lemmatize(cleaned))
    return client.generate_structured(messages, ConjugationTable)
