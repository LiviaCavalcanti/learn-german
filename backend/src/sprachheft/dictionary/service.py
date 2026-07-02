"""Dictionary lookup service over the normalized ``dict.sqlite``."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from sprachheft.config import get_settings
from sprachheft.dictionary.lemmatize import candidates


@dataclass
class DictEntry:
    headword: str
    pos: str | None = None
    ipa: str | None = None
    translations: list[str] = field(default_factory=list)
    senses: list[str] = field(default_factory=list)


class DictionaryService:
    def __init__(self, db_path: str | Path | None = None):
        self._db_path = Path(db_path) if db_path else get_settings().dict_db_path
        self._conn: sqlite3.Connection | None = None
        self._available: bool | None = None

    # -- connection ---------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        if not self._db_path.exists():
            self._available = False
            return False
        try:
            conn = self._connect()
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='dict_entry'"
            ).fetchone()
            self._available = row is not None
        except sqlite3.Error:
            self._available = False
        return self._available

    def entry_count(self) -> int:
        if not self.is_available():
            return 0
        conn = self._connect()
        meta = conn.execute(
            "SELECT value FROM dict_meta WHERE key='entry_count'"
        ).fetchone()
        if meta and str(meta[0]).isdigit():
            return int(meta[0])
        return int(conn.execute("SELECT count(*) FROM dict_entry").fetchone()[0])

    # -- lookup -------------------------------------------------------------
    def lookup(self, word: str, pos: str | None = None) -> list[DictEntry]:
        if not self.is_available():
            return []
        cands = candidates(word)
        if not cands:
            return []
        conn = self._connect()
        placeholders = ",".join("?" for _ in cands)
        sql = (
            "SELECT headword, pos, ipa, translations, senses "
            f"FROM dict_entry WHERE headword_lower IN ({placeholders})"
        )
        params: list[object] = list(cands)
        if pos:
            sql += " AND pos = ?"
            params.append(pos)
        sql += " ORDER BY length(headword) LIMIT 50"

        entries: list[DictEntry] = []
        for row in conn.execute(sql, params).fetchall():
            entries.append(
                DictEntry(
                    headword=row["headword"],
                    pos=row["pos"],
                    ipa=row["ipa"],
                    translations=json.loads(row["translations"]) if row["translations"] else [],
                    senses=json.loads(row["senses"]) if row["senses"] else [],
                )
            )
        return entries


@lru_cache
def get_dictionary_service() -> DictionaryService:
    return DictionaryService()


def reset_dictionary_cache() -> None:
    """Drop the cached service (e.g. after (re)building the dictionary)."""
    get_dictionary_service.cache_clear()
