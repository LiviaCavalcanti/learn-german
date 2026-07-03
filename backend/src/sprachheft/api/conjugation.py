"""Verb conjugation API: full table for a (possibly inflected) German verb."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from sprachheft.schemas import ConjugationTable
from sprachheft.services.conjugation import conjugate_verb

router = APIRouter(prefix="/conjugation", tags=["conjugation"])


@router.get("", response_model=ConjugationTable)
def conjugate(verb: str = Query(..., min_length=1)) -> ConjugationTable:
    cleaned = verb.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="verb is required")
    return conjugate_verb(cleaned)
