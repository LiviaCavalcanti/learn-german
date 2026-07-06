"""Orchestration for the news importer: list sources, fetch, translate, persist.

Delegates fetching/extraction/translation to ``sprachheft.news`` and reuses the
normal material-creation + generation services so imported news behaves exactly
like any other material.
"""

from __future__ import annotations

from sqlmodel import Session

from sprachheft import news
from sprachheft.languages import normalize_native, normalize_target
from sprachheft.schemas import (
    MaterialCreate,
    NewsArticleOut,
    NewsImportIn,
    NewsImportOut,
    NewsSourceOut,
    NewsSourcesOut,
)
from sprachheft.services import generation, materials


def list_sources() -> NewsSourcesOut:
    return NewsSourcesOut(
        available=news.deps_available(),
        sources=[
            NewsSourceOut(key=s.key, label=s.label, level=s.level, kind=s.kind)
            for s in news.SOURCES.values()
        ],
    )


def latest(source_key: str, limit: int = 12) -> list[NewsArticleOut]:
    return [
        NewsArticleOut(
            source=a.source, title=a.title, url=a.url, level=a.level, summary=a.summary
        )
        for a in news.list_articles(source_key, limit)
    ]


def import_article(session: Session, data: NewsImportIn) -> NewsImportOut:
    source = news.SOURCES.get(data.source)
    label = source.label if source else data.source
    level = data.level or (source.level if source else "A2")
    target = normalize_target(data.article_lang)
    native = normalize_native(data.native_lang)

    fetched_title, text = news.fetch_article(data.url)
    text = news.truncate(text, data.max_chars)
    if not text:
        raise ValueError("Could not extract the article text from that page.")
    # HTML sources list slug placeholders as titles; prefer the article's real first
    # line there. RSS feed titles are the real headline, so keep them.
    explicit = "" if (source and source.kind == "html") else (data.title or "")
    title = news.best_title(explicit, fetched_title, text, data.url)

    translation = news.translate_text(text, target, native) if data.translate else None

    material = materials.create_material(
        session,
        MaterialCreate(
            title=title,
            media_type="text",
            source_url=data.url,
            source_lang=target,
            native_lang=native,
            level=level,
            transcript=text,
            translation=translation,
            notes=f"News import — {label}",
        ),
    )

    counts: dict = {}
    if data.generate:
        counts = generation.generate_for_material(session, material, stage=data.stage)

    return NewsImportOut(
        material_id=int(material.id or 0),
        title=title,
        level=level,
        translated=translation is not None,
        vocab_added=int(counts.get("vocab_added", 0)),
        exercises_added=int(counts.get("exercises_added", 0)),
    )
