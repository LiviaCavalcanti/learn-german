"""Grapheme-to-phoneme (IPA) transcription for German words.

Offline and optional: backed by the ``gruut`` library (install the ``phonetics``
extra, e.g. ``uv sync --extra phonetics``). gruut bundles a German lexicon plus a
grapheme-to-phoneme model, so lookups stay fully offline once installed. When the
library is not available the functions degrade gracefully to ``None`` so the rest
of the app (and the offline test suite) keeps working.
"""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _load_sentences():
    """Return gruut's ``sentences`` callable, or ``None`` if gruut is missing."""
    try:
        from gruut import sentences
    except ImportError:
        return None
    return sentences


@lru_cache(maxsize=4096)
def to_ipa(word: str) -> str | None:
    """Return an IPA transcription for a German ``word`` wrapped in ``/…/``.

    Returns ``None`` when the ``phonetics`` extra (gruut) is not installed, the
    input is empty, or no phonemes could be produced. Results are cached.
    """
    word = (word or "").strip()
    if not word:
        return None
    sentences = _load_sentences()
    if sentences is None:
        return None
    try:
        words: list[str] = []
        for sentence in sentences(word, lang="de"):
            for token in sentence:
                if token.phonemes:
                    words.append("".join(token.phonemes))
    except Exception:
        # gruut can raise if the German language data package is unavailable or
        # on unexpected input — treat any failure as "no pronunciation".
        return None
    if not words:
        return None
    # Join phonemes within a word, separate multiple words (e.g. "das Haus").
    return "/" + " ".join(words) + "/"
