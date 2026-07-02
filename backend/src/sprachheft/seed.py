"""Seed reference data (grammar taxonomy) from content/taxonomy.json."""

from __future__ import annotations

import json

from sqlmodel import Session, select

from sprachheft.config import get_settings
from sprachheft.db import engine
from sprachheft.models import GrammarTopic


def seed_taxonomy() -> int:
    """Upsert grammar topics from taxonomy.json. Returns count of new rows."""
    settings = get_settings()
    path = settings.content_dir / "taxonomy.json"
    if not path.exists():
        return 0

    data = json.loads(path.read_text(encoding="utf-8"))
    topics = data.get("grammarTopics", [])
    added = 0

    with Session(engine) as session:
        for t in topics:
            code = t.get("code")
            if not code:
                continue
            existing = session.exec(
                select(GrammarTopic).where(GrammarTopic.code == code)
            ).first()
            if existing:
                existing.title = t.get("title", existing.title)
                existing.cefr = t.get("cefr", existing.cefr)
                existing.description = t.get("description")
                session.add(existing)
            else:
                session.add(
                    GrammarTopic(
                        code=code,
                        title=t.get("title", ""),
                        cefr=t.get("cefr", ""),
                        description=t.get("description"),
                    )
                )
                added += 1
        session.commit()

    return added
