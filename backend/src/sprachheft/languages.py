"""Language registry: per-language configuration for the multi-language app.

German (``de``) is the original target language; other targets (Spanish, French,
Italian, …) reuse the same pipeline. A :class:`LanguageProfile` carries the facts
the backend needs to adapt prompts, dictionaries, phonetics and content to a
target language.

The learner's *native* (explanation) language is a separate axis: it is the
language meanings and feedback are written in, and can be any entry in
:data:`NATIVE_LANGUAGES`. A language can be both a target (something to learn) and
a native language (something you already know) — e.g. a French speaker learning
German, or an English speaker learning French.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_TARGET = "de"
DEFAULT_NATIVE = "en"


@dataclass(frozen=True)
class LanguageProfile:
    """Everything the pipeline needs to know about one target language."""

    code: str  # ISO 639-1, e.g. "de", "es"
    name: str  # English display name, e.g. "German"
    endonym: str  # native name, e.g. "Deutsch", "Español"
    level_framework: str  # proficiency scale label, e.g. "CEFR"
    levels: tuple[str, ...]  # allowed level codes, e.g. ("A1", "A2", "B1", "B2")
    voice: str  # BCP-47 hint for browser text-to-speech, e.g. "de-DE"
    lemmatizer: str  # simplemma language code, or "" if unsupported
    has_conjugation: bool  # whether the verb-conjugation feature applies
    content_dir: str  # sub-directory under content/ holding taxonomy/course JSON
    article_note: str  # a short prompt fragment about noun gender/articles ("" if none)


# Registered target languages. A language becomes *available* to learners only
# once it also has authored content (see :func:`available_targets`).
LANGUAGES: dict[str, LanguageProfile] = {
    "de": LanguageProfile(
        code="de",
        name="German",
        endonym="Deutsch",
        level_framework="CEFR",
        levels=("A1", "A2", "B1", "B2", "C1"),
        voice="de-DE",
        lemmatizer="de",
        has_conjugation=True,
        content_dir="de",
        article_note=(
            "For nouns, include the article shorthand r/e/s (= der/die/das) to mark gender."
        ),
    ),
    "es": LanguageProfile(
        code="es",
        name="Spanish",
        endonym="Español",
        level_framework="CEFR",
        levels=("A1", "A2", "B1", "B2"),
        voice="es-ES",
        lemmatizer="es",
        has_conjugation=True,
        content_dir="es",
        article_note="For nouns, include the definite article el/la to mark gender.",
    ),
    "fr": LanguageProfile(
        code="fr",
        name="French",
        endonym="Français",
        level_framework="CEFR",
        levels=("A1", "A2", "B1", "B2", "C1", "C2"),
        voice="fr-FR",
        lemmatizer="fr",
        has_conjugation=True,
        content_dir="fr",
        article_note="For nouns, include the definite article le/la to mark gender.",
    ),
    "it": LanguageProfile(
        code="it",
        name="Italian",
        endonym="Italiano",
        level_framework="CEFR",
        levels=("A1", "A2", "B1", "B2"),
        voice="it-IT",
        lemmatizer="it",
        has_conjugation=True,
        content_dir="it",
        article_note="For nouns, include the definite article il/lo/la to mark gender.",
    ),
}

# Languages that may be used as the native/explanation language (meanings,
# feedback, translations are written in this language).
NATIVE_LANGUAGES: dict[str, str] = {
    "en": "English",
    "de": "German",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
}


def get_language(code: str | None) -> LanguageProfile:
    """Return the profile for ``code``, falling back to the default target."""
    return LANGUAGES.get((code or DEFAULT_TARGET).lower(), LANGUAGES[DEFAULT_TARGET])


def is_supported_target(code: str | None) -> bool:
    """Whether ``code`` is a registered target language."""
    return (code or "").lower() in LANGUAGES


def normalize_target(code: str | None) -> str:
    """Coerce ``code`` to a known target language code (default if unknown)."""
    lowered = (code or "").lower()
    return lowered if lowered in LANGUAGES else DEFAULT_TARGET


def normalize_native(code: str | None) -> str:
    """Coerce ``code`` to a known native language code (default if unknown)."""
    lowered = (code or "").lower()
    return lowered if lowered in NATIVE_LANGUAGES else DEFAULT_NATIVE


def target_name(code: str | None) -> str:
    """English name of the target language for ``code``."""
    return get_language(code).name


def native_name(code: str | None) -> str:
    """English name of the native/explanation language for ``code``."""
    return NATIVE_LANGUAGES.get(normalize_native(code), "English")


def available_targets(content_dir: Path) -> list[LanguageProfile]:
    """Registered targets that have authored content (a ``course.json``).

    Content lives at ``<content_dir>/<profile.content_dir>/course.json``; a
    language only shows up in the learner-facing picker once that file exists.
    """
    out: list[LanguageProfile] = []
    for profile in LANGUAGES.values():
        if (content_dir / profile.content_dir / "course.json").exists():
            out.append(profile)
    return out
