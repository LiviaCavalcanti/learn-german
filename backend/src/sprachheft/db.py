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
    """Create tables for all registered models."""
    from sprachheft import models  # noqa: F401  (register metadata)

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
