"""Database engine and session management (SQLModel + SQLite)."""

from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from sprachheft.config import get_settings

_settings = get_settings()
_sqlite_url = f"sqlite:///{_settings.db_path}"

engine = create_engine(
    _sqlite_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Create tables for all registered models, then apply lightweight column adds."""
    from sprachheft import models  # noqa: F401  (register metadata)

    SQLModel.metadata.create_all(engine)
    _ensure_columns()


# Columns added to *existing* tables by the multi-language feature. ``init_db`` is
# ``create_all`` only (no migrations), so a database created before these columns
# existed would be missing them. These idempotent, data-preserving ``ALTER``s
# bring an older database up to date. Existing rows are German content, so the
# defaults ('de' target / 'en' native) tag them correctly.
_ADDED_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "material": [("native_lang", "VARCHAR DEFAULT 'en'")],
    "vocabitem": [("target_lang", "VARCHAR DEFAULT 'de'")],
    "exercise": [("target_lang", "VARCHAR DEFAULT 'de'")],
    "grammartopic": [("target_lang", "VARCHAR DEFAULT 'de'")],
}


def _ensure_columns() -> None:
    """Add newly introduced columns to existing tables (idempotent)."""
    with engine.begin() as conn:
        for table, columns in _ADDED_COLUMNS.items():
            info = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
            existing = {row[1] for row in info}
            if not existing:
                continue  # table doesn't exist yet — create_all already made it current
            for name, decl in columns:
                if name not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
