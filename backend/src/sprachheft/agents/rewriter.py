"""Rewrite/expand a material's German text via the LLM."""

from __future__ import annotations

from sprachheft.llm import get_llm_client
from sprachheft.models import Material
from sprachheft.schemas import RewrittenText

SYSTEM_PROMPT = """You are a German-as-a-foreign-language (DaF) writing assistant. You \
rewrite or expand a German text for a learner.

Rules:
- Write natural, correct German at the given CEFR level.
- Follow the user's instructions for how to change or expand the text.
- Produce a coherent, self-contained text of AT LEAST {min_lines} lines (one sentence \
per line is fine). Add related details, examples, or a short dialogue to reach the length.
- Keep the topic recognizable unless the instructions say otherwise.
Return only the rewritten German text."""


def rewrite_text(material: Material, instructions: str | None, target_lines: int = 15) -> str:
    client = get_llm_client()
    system = SYSTEM_PROMPT.format(min_lines=target_lines)
    default = "Expand and enrich the text; keep the topic and level."
    user = (
        f"LEVEL: {material.level}\n"
        f"TARGET_LINES: {target_lines}\n"
        f"INSTRUCTIONS: {instructions or default}\n"
        f"CURRENT_TEXT:\n{material.transcript}\n"
    )
    result = client.generate_structured(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        RewrittenText,
    )
    text = (result.text or "").strip()
    return text or material.transcript
