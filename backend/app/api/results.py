"""S1-5.3 Results endpoints - owner: Shegofa Ahmadi

POST /api/sessions/{id}/complete   mark the session done, return its results
GET  /api/sessions/{id}/results    return the results (Results in frontend/lib/types.ts)

Scores come from the feedback rows saved when each answer was submitted (S1-3.2);
asked questions with no saved answer count as unanswered. The overall score averages
over all of the interview's questions, so questions never reached count as 0.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import user_id
from app.evaluation.feedback_rules import session_feedback
from app.evaluation.keyword_evaluator import AnswerScore
from app.repository import PersistenceError, get_repo

router = APIRouter()


class AnswerResultOut(BaseModel):
    q_index: int
    question_id: int
    category: str
    prompt: str
    answer: str
    status: Literal["answered", "blank", "unanswered"]
    score: int
    correct: bool
    matched: List[str]
    missing: List[str]
    strengths: str
    improvements: str


class ResultsOut(BaseModel):
    session_id: int
    job_title: str
    interview_type: str
    difficulty: str
    duration_min: int
    overall_score: int
    label: str
    correct_count: int
    answered_count: int
    missed_count: int
    total: int
    strengths: str
    improvements: str
    completed_at: Optional[datetime]
    answers: List[AnswerResultOut]


def score_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Fair"
    return "Needs practice"


def _status(row: dict) -> str:
    if row["response_id"] is None:
        return "unanswered"
    return "blank" if row["is_blank"] else "answered"


def _build(data: dict) -> ResultsOut:
    s, rows = data["session"], data["questions"]
    texts = [row["answer_text"] or "" for row in rows]
    scores = [
        AnswerScore(row["matched_keywords"] or [], row["missing_keywords"] or [], row["score"] or 0,
                    bool(row["correct"]))
        for row in rows
    ]
    fb = session_feedback(scores, texts)

    answers = [
        AnswerResultOut(
            q_index=row["q_index"], question_id=row["question_id"], category=row["category"],
            prompt=row["prompt"], answer=text, status=_status(row),
            score=item["score"], correct=item["correct"], matched=item["matched"],
            missing=item["missing"], strengths=item["strengths"], improvements=item["improvements"],
        )
        for row, text, item in zip(rows, texts, fb["answers"])
    ]
    total = s["total_questions"]
    answered = sum(1 for a in answers if a.status == "answered")
    # Average over every question in the interview, not just the ones asked, so
    # ending early can't give a high score (questions not reached count as 0).
    overall = round(sum(a.score for a in answers) / total) if total else 0
    return ResultsOut(
        session_id=s["id"], job_title=s["job_title"], interview_type=s["interview_type"],
        difficulty=s["difficulty"], duration_min=s["duration_min"],
        overall_score=overall, label=score_label(overall),
        correct_count=fb["correct_count"], answered_count=answered, missed_count=total - answered,
        total=total, strengths=fb["strengths"], improvements=fb["improvements"],
        completed_at=s["completed_at"], answers=answers,
    )


def _load(repo, session_id: int, uid: str) -> dict:
    try:
        data = repo.get_session_with_responses(session_id, uid)
    except PersistenceError:
        raise HTTPException(status_code=503, detail="Could not load the interview. Please retry.")
    if not data:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    return data


@router.post("/sessions/{session_id}/complete", response_model=ResultsOut)
def complete(session_id: int, uid: str = Depends(user_id), repo=Depends(get_repo)):
    data = _load(repo, session_id, uid)
    if data["session"]["status"] == "completed":
        return _build(data)  # finishing twice (double click, retry) just returns the results
    results = _build(data)
    try:
        repo.complete_session(session_id, uid, results.overall_score)
    except PersistenceError:
        raise HTTPException(status_code=503, detail="Could not finish the interview. Please retry.")
    # Reload so completed_at reflects what was saved.
    return _build(_load(repo, session_id, uid))


@router.get("/sessions/{session_id}/results", response_model=ResultsOut)
def get_results(session_id: int, uid: str = Depends(user_id), repo=Depends(get_repo)):
    return _build(_load(repo, session_id, uid))
