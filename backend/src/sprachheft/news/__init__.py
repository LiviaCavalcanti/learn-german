"""German news importer: list sources/articles, fetch, translate, generate.

Shared by the ``/news`` API and ``scripts/daily_article.py``. The optional
``daily`` extra provides the heavy deps — see ``deps_available()``.
"""

from __future__ import annotations

from sprachheft.news.service import (
    best_title,
    clean,
    deps_available,
    fetch_article,
    latest_from_source,
    list_articles,
    translate_text,
    truncate,
)
from sprachheft.news.sources import (
    SOURCES,
    Article,
    NewsSource,
    normalize_link,
    slug_stem,
    title_from_link,
)

__all__ = [
    "SOURCES",
    "Article",
    "NewsSource",
    "best_title",
    "clean",
    "deps_available",
    "fetch_article",
    "latest_from_source",
    "list_articles",
    "normalize_link",
    "slug_stem",
    "title_from_link",
    "translate_text",
    "truncate",
]
