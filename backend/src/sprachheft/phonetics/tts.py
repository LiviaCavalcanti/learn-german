"""Offline text-to-speech via the bundled espeak-ng shared library.

Synthesizes a word or short phrase to WAV audio in the *target* language, using
the same espeak-ng library that powers IPA transcription (the ``phonetics``
extra). This is deliberately OS-independent: it does not rely on the speech
voices installed on the learner's device, so a learner always hears the language
they are studying pronounced in that language — not whatever default voice the
browser happens to fall back to.

Degrades gracefully to ``None`` when the ``phonetics`` extra is not installed,
mirroring :func:`sprachheft.phonetics.to_ipa`. espeak access is serialized with a
lock because the library keeps a single global synthesis callback and voice.
"""

from __future__ import annotations

import ctypes
import io
import os
import threading
import wave
from functools import lru_cache

# espeak_AUDIO_OUTPUT: run the synth callback synchronously (no audio device).
_AUDIO_OUTPUT_SYNCHRONOUS = 0x02
# espeak_Synth flag: the text is UTF-8.
_CHARS_UTF8 = 0x01

# espeak-ng voice names for the app's target languages. Unknown codes fall back
# to their two-letter form, which espeak understands for most languages.
_VOICE_BY_LANG: dict[str, str] = {
    "de": "de",
    "es": "es",
    "fr": "fr-fr",
    "it": "it",
    "en": "en",
}

_lock = threading.Lock()
_engine: _Engine | None = None
_load_failed = False


class _Engine:
    """A loaded, initialized espeak-ng library with a capture callback."""

    def __init__(self, lib: ctypes.CDLL, sample_rate: int) -> None:
        self.lib = lib
        self.sample_rate = sample_rate
        self._buf = bytearray()

        lib.espeak_SetVoiceByName.argtypes = [ctypes.c_char_p]
        lib.espeak_SetVoiceByName.restype = ctypes.c_int
        lib.espeak_Synth.argtypes = [
            ctypes.c_char_p,
            ctypes.c_size_t,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.c_uint,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        lib.espeak_Synth.restype = ctypes.c_int
        lib.espeak_Synchronize.restype = ctypes.c_int

        # Keep a reference to the callback so it is not garbage-collected while
        # espeak holds the pointer.
        cb_type = ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p
        )
        self._callback = cb_type(self._on_samples)
        lib.espeak_SetSynthCallback(self._callback)

    def _on_samples(self, wav, numsamples, _events) -> int:  # noqa: ANN001
        # espeak delivers signed 16-bit PCM in chunks; numsamples == 0 marks the
        # end of synthesis. Returning 0 tells espeak to continue.
        if numsamples > 0 and wav:
            self._buf += ctypes.string_at(wav, numsamples * 2)
        return 0

    def synth(self, text: str, voice: str) -> bytes:
        """Synthesize ``text`` with ``voice`` and return raw 16-bit PCM (mono)."""
        self.lib.espeak_SetVoiceByName(voice.encode("utf-8"))
        self._buf = bytearray()
        data = text.encode("utf-8")
        self.lib.espeak_Synth(data, len(data) + 1, 0, 0, 0, _CHARS_UTF8, None, None)
        self.lib.espeak_Synchronize()
        return bytes(self._buf)


def _load_engine() -> _Engine | None:
    """Load and initialize espeak-ng once (or return the cached engine)."""
    global _engine, _load_failed
    if _engine is not None or _load_failed:
        return _engine
    try:
        import espeakng_loader
    except ImportError:
        _load_failed = True
        return None
    try:
        lib = ctypes.CDLL(espeakng_loader.get_library_path())
        lib.espeak_Initialize.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        lib.espeak_Initialize.restype = ctypes.c_int
        # espeak_Initialize wants the directory that *contains* espeak-ng-data.
        data_root = os.path.dirname(espeakng_loader.get_data_path())
        rate = lib.espeak_Initialize(
            _AUDIO_OUTPUT_SYNCHRONOUS, 0, data_root.encode("utf-8"), 0
        )
        if rate <= 0:
            _load_failed = True
            return None
        _engine = _Engine(lib, rate)
    except Exception:
        _load_failed = True
        return None
    return _engine


def _to_wav(pcm: bytes, sample_rate: int) -> bytes:
    """Wrap raw mono 16-bit PCM in a WAV container."""
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm)
    return out.getvalue()


@lru_cache(maxsize=2048)
def synthesize(word: str, lang: str = "de") -> bytes | None:
    """Return WAV audio for ``word`` spoken in ``lang``, or ``None``.

    Returns ``None`` when the ``phonetics`` extra is not installed, the input is
    empty, or synthesis produced no audio. Results are cached.
    """
    word = (word or "").strip()
    if not word:
        return None
    base = (lang or "de").lower()[:2]
    voice = _VOICE_BY_LANG.get(base, base)
    with _lock:
        engine = _load_engine()
        if engine is None:
            return None
        try:
            pcm = engine.synth(word, voice)
        except Exception:
            return None
        sample_rate = engine.sample_rate
    if not pcm:
        return None
    return _to_wav(pcm, sample_rate)


def tts_available() -> bool:
    """Whether offline speech synthesis is usable (phonetics extra installed)."""
    with _lock:
        return _load_engine() is not None
