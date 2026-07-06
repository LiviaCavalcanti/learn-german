#!/usr/bin/env python
"""Fetch a German news article, add it as a Material, translate it, generate questions.

A standalone daily job (run it from cron / Windows Task Scheduler). It talks to the
running Sprachheft backend over HTTP, so start the backend first::

    cd backend && uv run python main.py

Pipeline
--------
1. List the latest articles from a source: ``nachrichtenleicht`` (easy German, scraped
   off the homepage) or ``dw`` (native-level news, from its RSS feed).
2. Pick the newest article not imported yet (a small JSON state file dedupes runs).
3. Extract the article's full text (trafilatura; falls back to the feed summary).
4. Translate it to the native language with deep-translator (free Google Translate) —
   this automates the "open Google Translate and paste it back" step from the UI.
5. ``POST /materials`` then ``POST /materials/{id}/generate`` so the app produces
   vocabulary + exercises exactly like the manual flow.

Setup (once)::

    cd backend && uv sync --extra daily      # feedparser + deep-translator + trafilatura

Examples::

    uv run python scripts/daily_article.py                    # newest easy-German article
    uv run python scripts/daily_article.py --source dw --level B1
    uv run python scripts/daily_article.py --feed-url <rss-url> --level A2
    uv run python scripts/daily_article.py --dry-run          # fetch + preview, save nothing

Schedule it daily, e.g. cron::

    0 7 * * *  cd /path/to/learning/backend && uv run python scripts/daily_article.py

or Windows Task Scheduler → Program ``powershell`` with arguments::

    -NoProfile -Command "cd C:\\path\\to\\learning\\backend; uv run python scripts/daily_article.py"
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

from sprachheft import news
from sprachheft.news import Article, NewsSource

# .../learning/backend/scripts/daily_article.py -> parents[2] == .../learning
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_FILE = REPO_ROOT / "data" / "daily_article_state.json"
DEFAULT_API_BASE = "http://127.0.0.1:8000"
LEVELS = ["A1", "A2", "B1", "B2", "C1"]


def _warn(message: str) -> None:
    print(f"! {message}", file=sys.stderr)


def _die(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


# --- state (dedupe) ----------------------------------------------------------
def _load_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# --- backend API -------------------------------------------------------------
def _create_material(client: httpx.Client, base: str, payload: dict) -> int:
    resp = client.post(f"{base}/materials", json=payload, timeout=30.0)
    if resp.status_code != 201:
        _die(f"POST /materials returned {resp.status_code}: {resp.text[:300]}")
    return int(resp.json()["id"])


def _generate(client: httpx.Client, base: str, material_id: int, stage: int) -> dict:
    # Generation can be slow with a real local model (several batched LLM calls).
    resp = client.post(
        f"{base}/materials/{material_id}/generate",
        params={"stage": stage},
        timeout=900.0,
    )
    if resp.status_code != 200:
        _die(
            f"POST /materials/{material_id}/generate returned "
            f"{resp.status_code}: {resp.text[:300]}"
        )
    return resp.json()


# --- CLI ---------------------------------------------------------------------
def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a daily German article, add it as a Material, translate it, "
        "and generate questions.",
    )
    parser.add_argument(
        "--source",
        choices=sorted(news.SOURCES),
        default="nachrichtenleicht",
        help="Which built-in feed to read (default: nachrichtenleicht).",
    )
    parser.add_argument("--feed-url", help="Use a custom RSS/Atom feed URL instead of --source.")
    parser.add_argument("--level", choices=LEVELS, help="Override the CEFR level tag.")
    parser.add_argument(
        "--api-base",
        default=DEFAULT_API_BASE,
        help=f"Backend base URL (default: {DEFAULT_API_BASE}).",
    )
    parser.add_argument("--article-lang", default="de", help="Feed language (default: de).")
    parser.add_argument(
        "--native-lang", default="en", help="Translate into this language (default: en)."
    )
    parser.add_argument(
        "--stage", type=int, default=2, choices=[1, 2, 3, 4], help="Generation stage (default: 2)."
    )
    parser.add_argument("--index", type=int, help="Pick the Nth article (0=newest) explicitly.")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=6000,
        help="Cap the article length before translating/generating (default: 6000; 0=no cap).",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Use the short RSS summary instead of fetching the full article page "
        "(RSS sources only).",
    )
    parser.add_argument("--no-translate", action="store_true", help="Skip translation.")
    parser.add_argument(
        "--no-generate", action="store_true", help="Skip vocabulary/exercise generation."
    )
    parser.add_argument("--force", action="store_true", help="Re-import even if already seen.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and preview; save nothing.")
    parser.add_argument(
        "--state-file",
        type=Path,
        default=DEFAULT_STATE_FILE,
        help="JSON file tracking already-imported articles.",
    )
    return parser.parse_args(argv)


def _select_source(args: argparse.Namespace) -> NewsSource:
    if args.feed_url:
        return NewsSource(
            key="custom",
            label=f"Custom feed ({args.feed_url})",
            level=args.level or "A2",
            kind="rss",
            url=args.feed_url,
        )
    return news.SOURCES[args.source]


def _pick(
    articles: list[Article], seen: set[str], index: int | None, force: bool
) -> Article | None:
    if index is not None:
        if not -len(articles) <= index < len(articles):
            _die(f"--index {index} out of range (found {len(articles)} articles)")
        return articles[index]
    for article in articles:
        if force or news.normalize_link(article.url) not in seen:
            return article
    return None


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    if not news.deps_available():
        _die(
            "the 'daily' extra is required (feedparser, trafilatura, deep-translator). "
            "Install it: cd backend && uv sync --extra daily",
            code=2,
        )

    source = _select_source(args)
    level = args.level or source.level

    print(f"Reading: {source.label}")
    try:
        articles = news.latest_from_source(source, limit=30)
    except httpx.HTTPError as exc:
        _die(f"could not fetch {source.url}: {exc}")
    if not articles:
        _die(f"no articles found at {source.url}")

    state = _load_state(args.state_file)
    seen = set(state.get(source.key, {}).get("seen", []))
    article = _pick(articles, seen, args.index, args.force)
    if article is None:
        print("Nothing new to import — the latest articles were already added.")
        return 0

    link = article.url
    fetched_title = ""
    transcript = ""
    if not args.summary_only:
        fetched_title, transcript = news.fetch_article(link)
    if not transcript:
        transcript = article.summary
    transcript = news.truncate(transcript, args.max_chars)
    if not transcript:
        _die("could not extract any article text (try a different --source or --index)")
    # For RSS the feed title is the real headline; for HTML it's a slug placeholder,
    # so let best_title fall back to the article's first line instead.
    explicit = article.title if source.kind == "rss" else ""
    title = news.best_title(explicit, fetched_title, transcript, link)

    print(f"Article: {title}")
    print(f"Link:    {link or '(none)'}")
    print(f"Level:   {level}   Length: {len(transcript)} chars")

    translation: str | None = None
    if not args.no_translate:
        print(f"Translating {args.article_lang} → {args.native_lang} …")
        translation = news.translate_text(transcript, args.article_lang, args.native_lang)
        if translation is None:
            _warn("translation unavailable; saving the article without a translation")

    if args.dry_run:
        print("\n--- transcript (preview) ---")
        print(transcript[:600] + ("…" if len(transcript) > 600 else ""))
        if translation:
            print("\n--- translation (preview) ---")
            print(translation[:600] + ("…" if len(translation) > 600 else ""))
        print("\n(dry run — nothing saved)")
        return 0

    payload = {
        "title": title,
        "media_type": "text",
        "source_url": link or None,
        "source_lang": args.article_lang,
        "native_lang": args.native_lang,
        "level": level,
        "transcript": transcript,
        "translation": translation,
        "notes": f"Daily import from {source.label} on {datetime.now(UTC):%Y-%m-%d}",
    }

    try:
        with httpx.Client() as client:
            material_id = _create_material(client, args.api_base, payload)
            print(f"Created material #{material_id}.")
            if not args.no_generate:
                print(f"Generating vocabulary + exercises (stage {args.stage}) …")
                result = _generate(client, args.api_base, material_id, args.stage)
                print(
                    f"  vocab added: {result.get('vocab_added', 0)}, "
                    f"exercises added: {result.get('exercises_added', 0)}"
                )
                for err in result.get("errors", []) or []:
                    _warn(f"generation: {err}")
    except httpx.ConnectError:
        _die(
            f"could not reach the backend at {args.api_base}. "
            "Start it first: cd backend && uv run python main.py"
        )

    entry_seen = state.setdefault(source.key, {}).setdefault("seen", [])
    entry_seen.append(news.normalize_link(link))
    del entry_seen[:-200]  # keep the list bounded
    state[source.key]["last_run"] = datetime.now(UTC).isoformat()
    _save_state(args.state_file, state)

    print(f"\nDone. Open it at http://localhost:5173/materials/{material_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
