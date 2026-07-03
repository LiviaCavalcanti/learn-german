"""Languages API: which target languages are available and native options.

Drives the frontend language picker: only languages that have authored content
(a ``course.json``) appear as targets; ``natives`` are the explanation languages
a learner may already know.
"""

from __future__ import annotations

from fastapi import APIRouter

from sprachheft.config import get_settings
from sprachheft.languages import NATIVE_LANGUAGES, available_targets

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get("")
def list_languages():
    settings = get_settings()
    targets = [
        {
            "code": p.code,
            "name": p.name,
            "endonym": p.endonym,
            "level_framework": p.level_framework,
            "levels": list(p.levels),
            "voice": p.voice,
            "has_conjugation": p.has_conjugation,
        }
        for p in available_targets(settings.content_dir)
    ]
    natives = [{"code": code, "name": name} for code, name in NATIVE_LANGUAGES.items()]
    return {"targets": targets, "natives": natives}
