"""IPA transcription for German words via espeak-ng (through phonemizer).

Offline and optional: install the ``phonetics`` extra (``uv sync --extra
phonetics``), which pulls ``phonemizer`` plus a pip-packaged espeak-ng shared
library (``espeakng-loader``) — so no system package is required. espeak-ng is
fast (sub-millisecond g2p) and includes stress marks, which is helpful for
learners. When the extra is missing the functions degrade gracefully to ``None``
so the rest of the app (and the offline test suite) keeps working.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from functools import lru_cache


@lru_cache(maxsize=1)
def _phonemizer() -> Callable[[str], str] | None:
    """Return a configured ``word -> IPA`` callable, or ``None`` if unavailable."""
    try:
        import espeakng_loader
        from phonemizer.backend import EspeakBackend
        from phonemizer.backend.espeak.wrapper import EspeakWrapper
    except ImportError:
        return None

    quiet = logging.getLogger("sprachheft.phonetics.espeak")
    quiet.addHandler(logging.NullHandler())
    quiet.setLevel(logging.CRITICAL)

    try:
        # espeakng-loader ships the compiled library + data; point espeak at them.
        os.environ.setdefault("ESPEAK_DATA_PATH", espeakng_loader.get_data_path())
        EspeakWrapper.set_library(espeakng_loader.get_library_path())
        backend = EspeakBackend(
            "de",
            with_stress=True,
            preserve_punctuation=False,
            logger=quiet,
        )
    except Exception:
        return None

    def run(word: str) -> str:
        out = backend.phonemize([word], strip=True)
        return out[0] if out else ""

    return run


@lru_cache(maxsize=4096)
def to_ipa(word: str) -> str | None:
    """Return an IPA transcription for a German ``word`` wrapped in ``/…/``.

    Returns ``None`` when the ``phonetics`` extra is not installed, the input is
    empty, or no phonemes could be produced. Results are cached.
    """
    word = (word or "").strip()
    if not word:
        return None
    phonemize = _phonemizer()
    if phonemize is None:
        return None
    try:
        result = phonemize(word).strip()
    except Exception:
        # Treat any espeak failure as "no pronunciation" rather than erroring.
        return None
    if not result:
        return None
    return f"/{result}/"
