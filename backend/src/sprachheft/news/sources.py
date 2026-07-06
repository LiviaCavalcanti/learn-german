"""German news source registry + small URL helpers.

No daily *text* RSS exists for nachrichtenleicht anymore (its feed redirects to the
HTML homepage), so that source scrapes article links off the homepage; Deutsche
Welle exposes a working RSS feed. Fetching/extraction/translation live in
``service.py``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class NewsSource:
    key: str
    label: str
    level: str  # default CEFR tag (the learner level the source suits)
    kind: str  # "rss" = parse a feed | "html" = scrape article links off an index page
    url: str  # feed URL (rss) or index-page URL (html)
    article_pattern: str = ""  # html: regex capturing article links on the index page
    exclude: tuple[str, ...] = ()  # html: slug stems that are nav/evergreen, not articles


@dataclass(frozen=True)
class Article:
    source: str
    title: str
    url: str
    level: str
    summary: str = ""


SOURCES: dict[str, NewsSource] = {
    "nachrichtenleicht": NewsSource(
        key="nachrichtenleicht",
        label="Nachrichtenleicht — Nachrichten in Einfacher Sprache",
        level="A2",
        kind="html",
        url="https://www.nachrichtenleicht.de/",
        article_pattern=r'href="(https://www\.nachrichtenleicht\.de/[a-z0-9-]+-\d+\.html)"',
        exclude=(
            "benutzung",
            "erklaerung",
            "kontakt",
            "impressum",
            "datenschutz",
            "regionale-angebote",
            "woerterbuch",
            "das-grundgesetz",
            "ueber-uns",
            "barrierefreiheit",
            "sitemap",
        ),
    ),
    "dw": NewsSource(
        key="dw",
        label="Deutsche Welle — Themen des Tages",
        level="B1",
        kind="rss",
        url="https://rss.dw.com/rdf/rss-de-top",
    ),
}


def slug_stem(url: str) -> str:
    """The article slug without its trailing ``-NNN.html`` id (for the exclude list)."""
    name = urlsplit(url).path.rsplit("/", 1)[-1]
    match = re.match(r"(.+?)-\d+\.html?$", name)
    return match.group(1) if match else name


def title_from_link(url: str) -> str:
    return slug_stem(url).replace("-", " ").strip().title() or "Untitled article"


def normalize_link(url: str) -> str:
    """Stable dedupe key: drop query/fragment (e.g. DW's ``?maca=...`` tracker)."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
