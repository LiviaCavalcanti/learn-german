"""Course / curriculum API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from sprachheft.api.deps import SessionDep
from sprachheft.schemas import MaterialRead
from sprachheft.services import course as svc

router = APIRouter(prefix="/course", tags=["course"])


@router.get("")
def get_course(lang: str = Query("de")):
    return svc.get_course(lang)


@router.get("/progress")
def get_progress(session: SessionDep, lang: str = Query("de")):
    return svc.get_progress(session, lang)


@router.get("/lessons/{code}")
def get_lesson(code: str, lang: str = Query("de")):
    lesson = svc.get_lesson(code, lang)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.post("/lessons/{code}/start", response_model=MaterialRead, status_code=201)
def start_lesson(
    code: str,
    session: SessionDep,
    lang: str = Query("de"),
    native: str = Query("en"),
):
    material = svc.start_lesson(session, code, lang, native)
    if not material:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return material


@router.get("/{level}")
def get_level(level: str, lang: str = Query("de")):
    entry = svc.get_level(level, lang)
    if not entry:
        raise HTTPException(status_code=404, detail="Level not found")
    return entry
