"""Verb conjugation service (delegates to the LLM conjugation agent)."""

from __future__ import annotations

from sprachheft.schemas import ConjugationTable


def conjugate_verb(verb: str) -> ConjugationTable:
    """Return the full conjugation table for a (possibly inflected) German verb."""
    from sprachheft.agents.conjugation import conjugate

    return conjugate(verb)
