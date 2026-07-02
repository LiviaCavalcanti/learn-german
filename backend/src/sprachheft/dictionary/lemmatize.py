"""German lemmatization for dictionary lookup (simplemma)."""

from __future__ import annotations

from functools import lru_cache

_DEFAULT_LANG = "de"


@lru_cache(maxsize=8192)
def lemmatize(word: str, lang: str = _DEFAULT_LANG) -> str:
    """Return the lemma for a (possibly inflected) word; falls back to the input."""
    cleaned = (word or "").strip()
    if not cleaned:
        return ""
    try:
        import simplemma

        return simplemma.lemmatize(cleaned, lang=lang)
    except Exception:
        return cleaned


def candidates(word: str, lang: str = _DEFAULT_LANG) -> list[str]:
    """Lowercased, de-duplicated lookup candidates: surface form + lemma."""
    cleaned = (word or "").strip()
    if not cleaned:
        return []
    raw = [
        cleaned,
        cleaned.lower(),
        lemmatize(cleaned, lang),
        lemmatize(cleaned.lower(), lang),
    ]
    out: list[str] = []
    for candidate in raw:
        lowered = candidate.strip().lower()
        if lowered and lowered not in out:
            out.append(lowered)
    return out
