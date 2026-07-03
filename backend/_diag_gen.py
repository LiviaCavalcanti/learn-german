"""Temporary diagnostic: exercise the real LLM generation path and report results."""

from __future__ import annotations

import traceback

import httpx

from sprachheft.agents.generator import build_messages, generate
from sprachheft.config import get_settings
from sprachheft.llm import get_llm_client
from sprachheft.models import Material

settings = get_settings()
print("MODEL     :", settings.llm_model)
print("API_BASE  :", settings.llm_api_base)

# 1) Can this process reach Ollama?
base = settings.llm_api_base or "http://localhost:11434"
try:
    tags = httpx.get(f"{base}/api/tags", timeout=5).json()
    print("OLLAMA    : up ->", [m["name"] for m in tags.get("models", [])])
except Exception as exc:  # noqa: BLE001
    print("OLLAMA    : UNREACHABLE ->", exc)

material = Material(
    id=1,
    title="Mein Arbeitstag",
    level="A2",
    transcript=(
        "Heute arbeite ich im Büro. Ich trinke Kaffee und schreibe eine E-Mail "
        "an meine Kollegin. Am Nachmittag habe ich ein Meeting mit dem Team."
    ),
    translation="Today I work in the office...",
)

print("\n--- client:", type(get_llm_client()).__name__)
try:
    result = generate(material, 2)
    print("themes    :", result.themes)
    print("vocab     :", len(result.vocabulary))
    print("exercises :", len(result.exercises))
    if result.exercises:
        print("types     :", [e.type for e in result.exercises])
except Exception:  # noqa: BLE001
    print("GENERATE RAISED:")
    traceback.print_exc()
