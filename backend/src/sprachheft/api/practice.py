"""Practice API: sessions and answer-checking (with optional SR grading)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from sprachheft.api.deps import SessionDep
from sprachheft.models import Exercise, StudySession
from sprachheft.schemas import (
    AnswerFeedback,
    AnswerFeedbackIn,
    PracticeAnswerIn,
    PracticeSessionCreate,
)
from sprachheft.services.practice import check_exercise, evaluate_answer

router = APIRouter(prefix="/practice", tags=["practice"])


@router.post("/sessions")
def create_session(data: PracticeSessionCreate, session: SessionDep):
    summary = {"material_id": data.material_id} if data.material_id is not None else {}
    study = StudySession(kind=data.kind or "practice", summary=summary)
    session.add(study)
    session.commit()
    session.refresh(study)
    return {"id": study.id, "kind": study.kind, "started_at": study.started_at}


@router.post("/answer")
def submit_answer(payload: PracticeAnswerIn, session: SessionDep):
    exercise = session.get(Exercise, payload.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    check = check_exercise(exercise, payload.responses)
    rating = payload.rating
    if rating is None and check["gradable"]:
        rating = "good" if check["all_correct"] else "again"

    graded = None
    if rating:
        from sprachheft.services.review import grade_item

        state = grade_item(
            session, "exercise", exercise.id, rating, session_id=payload.session_id
        )
        graded = {
            "rating": rating,
            "due": state.due,
            "state": state.state,
            "reps": state.reps,
        }

    if any((r or "").strip() for r in payload.responses):
        from sprachheft.services import attempts as attempts_svc

        attempts_svc.record_attempt(
            session,
            exercise_id=exercise.id,
            kind="check",
            responses=payload.responses,
            result=check,
            correct=int(check.get("correct", 0) or 0),
            total=int(check.get("total", 0) or 0),
        )

    return {"exercise_id": exercise.id, "check": check, "graded": graded}


@router.post("/feedback", response_model=AnswerFeedback)
def answer_feedback(payload: AnswerFeedbackIn, session: SessionDep) -> AnswerFeedback:
    exercise = session.get(Exercise, payload.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    feedback = evaluate_answer(exercise, payload.answer, payload.native_lang)
    if payload.answer.strip():
        from sprachheft.services import attempts as attempts_svc

        attempts_svc.record_attempt(
            session,
            exercise_id=exercise.id,
            kind="feedback",
            answer_text=payload.answer,
            result=feedback.model_dump(),
        )
    return feedback
