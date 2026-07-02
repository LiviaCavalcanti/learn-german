"""Import API: paste prompt-pack JSON or raw text to enrich your library."""

from __future__ import annotations

from fastapi import APIRouter

from sprachheft.api.deps import SessionDep
from sprachheft.schemas import ImportJsonIn, ImportTextIn
from sprachheft.services import imports as svc

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/json")
def import_json(payload: ImportJsonIn, session: SessionDep):
    return svc.import_json(session, payload)


@router.post("/text")
def import_text(payload: ImportTextIn, session: SessionDep):
    return svc.import_text(session, payload.raw_text, level=payload.level, title=payload.title)
