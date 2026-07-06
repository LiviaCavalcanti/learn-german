"""Fetch German news: list latest articles, extract full text, translate.

The heavy dependencies (feedparser for RSS, trafilatura for article text,
deep-translator for translation) are the optional ``daily`` extra;
``deps_available()`` reports whether they are installed so callers (the ``/news``
API and ``scripts/daily_article.py``) can degrade gracefully instead of crashing.

Feeds and article pages are fetched with a browser User-Agent because some servers
reject the default library User-Agents.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser

import httpx

from sprachheft.news.sources import (
    SOURCES,
    Article,
    NewsSource,
    slug_stem,
    title_from_link,
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
TRANSLATE_CHUNK = 4500  # Google Translate accepts ~5000 characters per request
MIN_FULLTEXT_CHARS = 200  # shorter extractions are treated as a miss


def deps_available() -> bool:
    """Whether the optional 'daily' extra (feedparser/trafilatura/deep_translator) is installed."""
    try:
        import deep_translator  # noqa: F401
        import feedparser  # noqa: F401
        import trafilatura  # noqa: F401
    except ImportError:
        return False
    return True


def _http_get(url: str) -> httpx.Response:
    resp = httpx.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=30.0,
        follow_redirects=True,
    )
    resp.raise_for_status()
    return resp


class _TextExtractor(HTMLParser):
    """Collapse an HTML fragment (an RSS summary) to readable plain text."""

    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag in {"script", "style"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip and data.strip():
            self.parts.append(data.strip())


def _html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html or "")
    return " ".join(" ".join(parser.parts).split())


def clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    head = text[:max_chars]
    cut = max(head.rfind(". "), head.rfind(".\n"), head.rfind("\n\n"))
    return (head[: cut + 1] if cut > max_chars // 2 else head).strip()


def best_title(explicit: str, fetched: str, text: str, url: str) -> str:
    """Best available title: an explicit/fetched one, else the first line, else the slug."""
    for candidate in (explicit, fetched):
        if candidate and candidate.strip():
            return clean(candidate)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines and len(lines[0]) <= 120:
        return clean(lines[0])
    return title_from_link(url)


def _summary_text(entry: object) -> str:
    for key in ("summary", "description"):
        value = getattr(entry, key, None)
        if value:
            return _html_to_text(str(value))
    return ""


def latest_from_source(source: NewsSource, limit: int = 12) -> list[Article]:
    """List the newest articles for a source (newest first)."""
    resp = _http_get(source.url)

    if source.kind == "html":
        items: list[Article] = []
        seen: set[str] = set()
        for link in re.findall(source.article_pattern, resp.text):
            if slug_stem(link) in source.exclude or link in seen:
                continue
            seen.add(link)
            items.append(
                Article(
                    source=source.key,
                    title=title_from_link(link),
                    url=link,
                    level=source.level,
                )
            )
            if len(items) >= limit:
                break
        return items

    import feedparser

    feed = feedparser.parse(resp.content)
    articles: list[Article] = []
    for entry in list(getattr(feed, "entries", []))[:limit]:
        link = getattr(entry, "link", "") or ""
        if not link:
            continue
        articles.append(
            Article(
                source=source.key,
                title=clean(getattr(entry, "title", "") or title_from_link(link)),
                url=link,
                level=source.level,
                summary=truncate(clean(_summary_text(entry)), 300),
            )
        )
    return articles


def list_articles(source_key: str, limit: int = 12) -> list[Article]:
    return latest_from_source(SOURCES[source_key], limit)


def fetch_article(url: str) -> tuple[str, str]:
    """Return ``(title, cleaned_main_text)`` for an article page ("" text if unavailable)."""
    if not url:
        return "", ""
    try:
        import trafilatura
    except ImportError:
        return "", ""
    try:
        html = _http_get(url).text
        data = trafilatura.extract(
            html,
            output_format="json",
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )
    except Exception:  # noqa: BLE001 — extraction is best-effort
        return "", ""
    if not data:
        return "", ""
    try:
        obj = json.loads(data)
    except json.JSONDecodeError:
        return "", ""
    title = clean(obj.get("title") or "")
    text = clean(obj.get("text") or "")
    return title, (text if len(text) >= MIN_FULLTEXT_CHARS else "")


def _chunk(text: str, size: int) -> list[str]:
    """Split into <= ``size`` pieces, preferring paragraph then word boundaries."""
    chunks: list[str] = []
    current = ""
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if len(para) > size:
            if current:
                chunks.append(current)
                current = ""
            word = ""
            for token in para.split(" "):
                if len(word) + len(token) + 1 > size:
                    chunks.append(word)
                    word = token
                else:
                    word = f"{word} {token}".strip()
            current = word
        elif len(current) + len(para) + 2 > size:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}".strip()
    if current:
        chunks.append(current)
    return chunks


def translate_text(text: str, source_lang: str = "de", target_lang: str = "en") -> str | None:
    """Translate ``text`` with deep-translator (Google). Returns None on any failure."""
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        return None
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        out = [translator.translate(part) for part in _chunk(text, TRANSLATE_CHUNK)]
    except Exception:  # noqa: BLE001 — translation is best-effort
        return None
    joined = "\n\n".join(piece for piece in out if piece)
    return joined or None
