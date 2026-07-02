"""Shared test configuration: isolate the DB, force the fake LLM, disable reminders."""

from __future__ import annotations

import os
import pathlib
import tempfile

_TMP_DB = pathlib.Path(tempfile.gettempdir()) / "sprachheft_test.sqlite"
os.environ.setdefault("SPRACHHEFT_DB_PATH", str(_TMP_DB))
os.environ.setdefault("SPRACHHEFT_LLM_MODEL", "fake")
os.environ.setdefault("SPRACHHEFT_ENABLE_REMINDERS", "0")
os.environ.setdefault("SPRACHHEFT_EMBEDDING_MODEL", "")
