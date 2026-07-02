"""Dictionary service tests using a synthetic normalized DB (no network)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from sprachheft.dictionary.loader import SCHEMA_SQL
from sprachheft.dictionary.service import DictEntry, DictionaryService


def _make_dict(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.executescript(SCHEMA_SQL)
    rows = [
        ("gehen", "gehen", "verb", None, json.dumps(["to go", "to walk"]), json.dumps([])),
        ("Haus", "haus", "noun", "haʊ̯s", json.dumps(["house"]), json.dumps(["a building"])),
        ("Bahnhof", "bahnhof", "noun", None, json.dumps(["train station"]), json.dumps([])),
    ]
    conn.executemany(
        "INSERT INTO dict_entry (headword, headword_lower, pos, ipa, translations, senses)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.execute(
        "INSERT OR REPLACE INTO dict_meta (key, value) VALUES ('entry_count', ?)",
        (str(len(rows)),),
    )
    conn.commit()
    conn.close()


def test_lookup_exact_and_lemmatized(tmp_path: Path):
    db = tmp_path / "dict.sqlite"
    _make_dict(db)
    service = DictionaryService(db_path=db)

    assert service.is_available()
    assert service.entry_count() == 3

    # Exact match
    exact = service.lookup("Bahnhof")
    assert any("train station" in e.translations for e in exact)

    # Inflected -> lemma (Häuser -> Haus)
    plural = service.lookup("Häuser")
    assert any(e.headword == "Haus" and "house" in e.translations for e in plural)

    # Inflected verb (gegangen -> gehen)
    verb = service.lookup("gegangen")
    assert any(e.headword == "gehen" and "to go" in e.translations for e in verb)


def test_lookup_unavailable(tmp_path: Path):
    service = DictionaryService(db_path=tmp_path / "missing.sqlite")
    assert service.is_available() is False
    assert service.lookup("Haus") == []
    assert isinstance(DictEntry("x"), DictEntry)
