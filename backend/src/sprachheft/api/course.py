"""Course / curriculum API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from sprachheft.api.deps import SessionDep
from sprachheft.schemas import AnswerFeedback, LessonAnswerIn, MaterialRead
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
    # Strip server-only fields: question reference answers and the authored exercise
    # answer keys (the exercises are delivered separately as gradable Exercise rows).
    public = {k: v for k, v in lesson.items() if k != "exercises"}
    questions = public.get("questions")
    if isinstance(questions, list):
        public["questions"] = [
            {k: v for k, v in q.items() if k != "reference"} if isinstance(q, dict) else q
            for q in questions
        ]
    return public


@router.post("/lessons/{code}/check", response_model=AnswerFeedback)
def check_lesson_answer(code: str, payload: LessonAnswerIn, lang: str = Query("de")):
    feedback = svc.check_answer(code, payload.index, payload.answer, lang, payload.native_lang)
    if feedback is None:
        raise HTTPException(status_code=404, detail="Lesson or question not found")
    return feedback


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
