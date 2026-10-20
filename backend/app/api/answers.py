"""S1-3.2 Answer submission API - owner: Jayme Nguyen

POST /api/sessions/{id}/answers   save the answer, score it, return the next question
An empty answer is a "skip": it is saved with is_blank=true and flagged in feedback.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import load_session, time_is_up, user_id
from app.api.sessions import QuestionOut
from app.evaluation.feedback_rules import feedback_for_answer
from app.evaluation.keyword_evaluator import KeywordEvaluator
from app.repository import AlreadyAnswered, PersistenceError, get_repo
from app.services import question_service as qs

router = APIRouter()
evaluator = KeywordEvaluator()


class AnswerIn(BaseModel):
    question_id: int
    text: str = Field("", max_length=5000)


class AnswerOut(BaseModel):
    saved: bool
    blank: bool
    correct_count: int
    answered: int
    total: int
    completed: bool
    q_index: int
    question: Optional[QuestionOut]


@router.post("/sessions/{session_id}/answers", response_model=AnswerOut)
def submit_answer(session_id: int, body: AnswerIn, uid: str = Depends(user_id), repo=Depends(get_repo)):
    try:
        return _submit(repo, session_id, uid, body)
    except AlreadyAnswered:
        raise HTTPException(status_code=409, detail="This question was already answered.")
    except PersistenceError:
        raise HTTPException(status_code=503, detail="Could not save your answer. Please retry.")


def _submit(repo, session_id: int, uid: str, body: AnswerIn) -> AnswerOut:
    s = load_session(repo, session_id, uid)
    if s["status"] == "completed":
        raise HTTPException(status_code=409, detail="This interview is already finished.")
    if time_is_up(s):
        raise HTTPException(status_code=409, detail="Time is up for this interview.")

    current, _ = qs.current_question(repo, s)
    if not current or current["id"] != body.question_id:
        raise HTTPException(status_code=409, detail="That is not the current question. Please reload the page.")

    text = body.text.strip()
    blank = not text
    result = evaluator.score_answer(text, current["expected_keywords"])
    fb = feedback_for_answer(result, text)
    prior_correct = sum(1 for f in repo.get_feedback(session_id).values() if f["correct"])
    correct_count = prior_correct + (1 if result.correct else 0)
    repo.save_answer(session_id, current["id"], text, blank, {
        "score": result.score, "correct": result.correct, "matched": result.matched,
        "missing": result.missing, "strengths": fb["strengths"], "improvements": fb["improvements"],
    }, correct_count)

    answered = len(repo.get_responses(session_id))
    nxt, idx = None, answered
    if answered < s["total_questions"]:
        try:
            nxt = qs.next_question(session_id, s["difficulty"], repo=repo)
            idx = answered + 1
        except qs.NoQuestionAvailable:
            nxt = None
    return AnswerOut(saved=True, blank=blank, correct_count=correct_count, answered=answered,
                     total=s["total_questions"], completed=nxt is None, q_index=idx,
                     question=QuestionOut(**nxt) if nxt else None)
