"""Download a WikDict pair database and import it into a normalized dict.sqlite.

WikDict data is CC BY-SA 4.0 (from Wiktionary via DBnary). The pair DB
(``de-en.sqlite3``, ~25 MB) holds translations + part of speech; the monolingual
``de.sqlite3`` (~1 GB) adds IPA/inflections and is optional.

Usage:
    uv run python -m sprachheft.dictionary.loader            # download de-en + build
    uv run python -m sprachheft.dictionary.loader --inspect  # show source schema only
    uv run python -m sprachheft.dictionary.loader --source path/to/de-en.sqlite3
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

from sprachheft.config import get_settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS dict_entry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    headword TEXT NOT NULL,
    headword_lower TEXT NOT NULL,
    pos TEXT,
    ipa TEXT,
    translations TEXT NOT NULL DEFAULT '[]',
    senses TEXT NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_dict_headword_lower ON dict_entry(headword_lower);
CREATE TABLE IF NOT EXISTS dict_meta (key TEXT PRIMARY KEY, value TEXT);
"""

_HEADWORD_COLS = ["written_rep", "headword", "lemma", "word"]
_TRANS_COLS = ["trans_list", "translation", "translations", "target", "written_rep_target"]
_POS_COLS = ["part_of_speech", "pos"]
_SENSE_COLS = ["sense", "gloss", "definition"]

_SPLIT_RE = re.compile(r"\s*[|;]\s*")


def _clean(value: str | None) -> str:
    """Trim whitespace and strip WikDict's surrounding double quotes."""
    text = (value or "").strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1].strip()
    return text


def _pick(columns: list[str], preferred: list[str]) -> str | None:
    lowered = {c.lower(): c for c in columns}
    for name in preferred:
        if name in lowered:
            return lowered[name]
    return None


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()]


def _find_translation_table(conn: sqlite3.Connection) -> str | None:
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    ]
    for name in ("translation", "translations"):
        if name in tables:
            return name
    for name in tables:
        cols = _columns(conn, name)
        if _pick(cols, _HEADWORD_COLS) and _pick(cols, _TRANS_COLS):
            return name
    return None


def download(url: str, dest: Path, *, timeout: float = 300.0) -> None:
    import httpx

    print(f"Downloading {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with httpx.stream("GET", url, timeout=timeout, follow_redirects=True) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        done = 0
        with open(tmp, "wb") as fh:
            for chunk in resp.iter_bytes(chunk_size=1 << 20):
                fh.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r  {done / 1e6:6.1f} / {total / 1e6:.1f} MB", end="", flush=True)
        print()
    tmp.replace(dest)


def inspect(source_db: Path) -> None:
    conn = sqlite3.connect(str(source_db))
    try:
        table = _find_translation_table(conn)
        print(f"source: {source_db}")
        print(f"translation table: {table}")
        if table:
            cols = _columns(conn, table)
            print(f"columns: {cols}")
            print(
                "detected -> headword:",
                _pick(cols, _HEADWORD_COLS),
                "| translations:",
                _pick(cols, _TRANS_COLS),
                "| pos:",
                _pick(cols, _POS_COLS),
                "| sense:",
                _pick(cols, _SENSE_COLS),
            )
            for row in conn.execute(f"SELECT * FROM {table} LIMIT 5"):
                print("  sample:", tuple(row))
    finally:
        conn.close()


def build(source_db: Path, dict_db: Path) -> int:
    """Import the source pair DB into the normalized dict.sqlite. Returns entry count."""
    src = sqlite3.connect(str(source_db))
    try:
        table = _find_translation_table(src)
        if not table:
            raise RuntimeError("Could not find a translation table in the source database.")
        cols = _columns(src, table)
        hcol = _pick(cols, _HEADWORD_COLS)
        tcol = _pick(cols, _TRANS_COLS)
        pcol = _pick(cols, _POS_COLS)
        scol = _pick(cols, _SENSE_COLS)
        if not hcol or not tcol:
            raise RuntimeError(f"Missing headword/translation columns in table '{table}' ({cols}).")

        select = (
            f"SELECT {hcol} AS hw, {tcol} AS tr, "
            f"{pcol or 'NULL'} AS pos, {scol or 'NULL'} AS sense FROM {table}"
        )
        aggregated: dict[tuple[str, str], dict] = {}
        for row in src.execute(select):
            headword = _clean(row[0])
            if not headword:
                continue
            translations = [t for t in (_clean(t) for t in _SPLIT_RE.split(row[1] or "")) if t]
            pos = (row[2] or None) or None
            sense = _clean(row[3]) or None
            key = (headword.lower(), pos or "")
            entry = aggregated.setdefault(
                key,
                {"headword": headword, "pos": pos, "translations": [], "senses": []},
            )
            for t in translations:
                if t not in entry["translations"]:
                    entry["translations"].append(t)
            if sense and sense not in entry["senses"]:
                entry["senses"].append(sense)
    finally:
        src.close()

    dict_db.parent.mkdir(parents=True, exist_ok=True)
    dst = sqlite3.connect(str(dict_db))
    try:
        dst.executescript(SCHEMA_SQL)
        dst.execute("DELETE FROM dict_entry")
        dst.executemany(
            "INSERT INTO dict_entry (headword, headword_lower, pos, ipa, translations, senses)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    e["headword"],
                    e["headword"].lower(),
                    e["pos"],
                    None,
                    json.dumps(e["translations"], ensure_ascii=False),
                    json.dumps(e["senses"], ensure_ascii=False),
                )
                for e in aggregated.values()
            ],
        )
        dst.execute(
            "INSERT OR REPLACE INTO dict_meta (key, value) VALUES ('entry_count', ?)",
            (str(len(aggregated)),),
        )
        dst.execute(
            "INSERT OR REPLACE INTO dict_meta (key, value) VALUES ('source', ?)",
            ("WikDict (CC BY-SA 4.0, from Wiktionary via DBnary)",),
        )
        dst.commit()
    finally:
        dst.close()
    return len(aggregated)


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Build the offline dictionary (WikDict).")
    parser.add_argument("--pair", default=settings.dict_pair, help="language pair, e.g. de-en")
    parser.add_argument("--source", type=Path, default=None, help="existing pair sqlite file")
    parser.add_argument("--out", type=Path, default=settings.dict_db_path, help="output dict db")
    parser.add_argument("--inspect", action="store_true", help="print source schema and exit")
    args = parser.parse_args()

    if args.source:
        source_db = args.source
    else:
        source_db = settings.data_dir / f"wikdict-{args.pair}.sqlite3"
        if not source_db.exists():
            url = f"{settings.wikdict_base_url}/{args.pair}.sqlite3"
            download(url, source_db)

    if args.inspect:
        inspect(source_db)
        return

    count = build(source_db, args.out)
    print(f"Imported {count} entries into {args.out}")


if __name__ == "__main__":
    main()
