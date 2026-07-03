"""Seed reference data (grammar taxonomy) from content/<lang>/taxonomy.json."""

from __future__ import annotations

import json

from sqlmodel import Session, select

from sprachheft.config import get_settings
from sprachheft.db import engine
from sprachheft.languages import LANGUAGES
from sprachheft.models import GrammarTopic


def _seed_language(session: Session, lang: str, content_dir) -> int:
    """Upsert grammar topics for one target language. Returns count of new rows."""
    profile = LANGUAGES[lang]
    path = content_dir / profile.content_dir / "taxonomy.json"
    if not path.exists():
        return 0

    data = json.loads(path.read_text(encoding="utf-8"))
    topics = data.get("grammarTopics", [])
    added = 0
    for t in topics:
        code = t.get("code")
        if not code:
            continue
        existing = session.exec(
            select(GrammarTopic).where(GrammarTopic.code == code)
        ).first()
        if existing:
            existing.target_lang = lang
            existing.title = t.get("title", existing.title)
            existing.cefr = t.get("cefr", existing.cefr)
            existing.description = t.get("description")
            session.add(existing)
        else:
            session.add(
                GrammarTopic(
                    code=code,
                    target_lang=lang,
                    title=t.get("title", ""),
                    cefr=t.get("cefr", ""),
                    description=t.get("description"),
                )
            )
            added += 1
    return added


def seed_taxonomy() -> int:
    """Upsert grammar topics for every registered language. Returns new-row count."""
    settings = get_settings()
    added = 0
    with Session(engine) as session:
        for lang in LANGUAGES:
            added += _seed_language(session, lang, settings.content_dir)
        session.commit()
    return added
