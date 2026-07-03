"""Course / curriculum API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from sprachheft.api.deps import SessionDep
from sprachheft.schemas import MaterialRead
from sprachheft.services import course as svc

router = APIRouter(prefix="/course", tags=["course"])


@router.get("")
def get_course():
    return svc.get_course()


@router.get("/progress")
def get_progress(session: SessionDep):
    return svc.get_progress(session)


@router.get("/lessons/{code}")
def get_lesson(code: str):
    lesson = svc.get_lesson(code)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.post("/lessons/{code}/start", response_model=MaterialRead, status_code=201)
def start_lesson(code: str, session: SessionDep):
    material = svc.start_lesson(session, code)
    if not material:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return material


@router.get("/{level}")
def get_level(level: str):
    entry = svc.get_level(level)
    if not entry:
        raise HTTPException(status_code=404, detail="Level not found")
    return entry
