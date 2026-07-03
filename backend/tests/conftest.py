"""Shared test configuration: isolate the DB, force the fake LLM, disable reminders."""

from __future__ import annotations

import os
import pathlib
import tempfile

_TMP_DB = pathlib.Path(tempfile.gettempdir()) / "sprachheft_test.sqlite"
# Start each test session from a clean database. ``init_db()`` only creates
# missing tables (no migrations), so a file left over from an older schema would
# be missing newly added columns. Removing it up front keeps the schema current.
for _suffix in ("", "-wal", "-shm"):
    pathlib.Path(str(_TMP_DB) + _suffix).unlink(missing_ok=True)
os.environ.setdefault("SPRACHHEFT_DB_PATH", str(_TMP_DB))
os.environ.setdefault("SPRACHHEFT_LLM_MODEL", "fake")
os.environ.setdefault("SPRACHHEFT_ENABLE_REMINDERS", "0")
os.environ.setdefault("SPRACHHEFT_EMBEDDING_MODEL", "")
