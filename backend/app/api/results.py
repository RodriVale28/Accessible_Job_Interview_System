"""S1-5.3 Results endpoints - owner: Shegofa Ahmadi
S2-2.2 additions (Aisha Aloma): soft labels, role_id / timed on Results, and per answer
question_type, criteria_met / criteria_missed / evidence / grader. Old Sprint 1 answers have
empty criteria arrays and fall back to matched_keywords / missing_keywords. Per-answer
strengths / improvements are read from the feedback saved with the answer; results never
call the AI.

POST /api/sessions/{id}/complete   mark the session done, return its results
GET  /api/sessions/{id}/results    return the results (Results in frontend/lib/types.ts)

Scores come from the feedback rows saved when each answer was submitted (S1-3.2);
asked questions with no saved answer count as unanswered. The overall score averages
over all of the interview's questions, so questions never reached count as 0.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import user_id
from app.evaluation.feedback_rules import session_feedback
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
    question_type: Optional[str] = None
    criteria_met: List[str] = []
    criteria_missed: List[str] = []
    evidence: List[str] = []
    grader: Optional[str] = None


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
    role_id: Optional[int] = None
    timed: bool = False


def score_label(score: int) -> str:
    if score >= 80:
        return "Strong"
    if score >= 50:
        return "Getting there"
    return "Room to grow"


@dataclass
class _StoredGrade:
    """A saved feedback row in the shape feedback_for_answer reads."""
    score: int
    correct: bool
    criteria_met: list
    criteria_missed: list
    evidence: list


def _stored_grade(row: dict) -> _StoredGrade:
    met, missed = list(row.get("criteria_met") or []), list(row.get("criteria_missed") or [])
    if not met and not missed:  # Sprint 1 answer: no criteria saved, use the keywords
        met, missed = list(row["matched_keywords"] or []), list(row["missing_keywords"] or [])
    return _StoredGrade(row["score"] or 0, bool(row["correct"]), met, missed,
                        list(row.get("evidence") or []))


def _status(row: dict) -> str:
    if row["response_id"] is None:
        return "unanswered"
    return "blank" if row["is_blank"] else "answered"


def _build(data: dict) -> ResultsOut:
    s, rows = data["session"], data["questions"]
    texts = [row["answer_text"] or "" for row in rows]
    grades = [_stored_grade(row) for row in rows]
    fb = session_feedback(grades, texts)

    def saved(row, key, fallback):
        # Text saved with the answer wins; unanswered rows have none, so use the template.
        value = row.get(key)
        return value if row["response_id"] is not None and value is not None else fallback

    answers = [
        AnswerResultOut(
            q_index=row["q_index"], question_id=row["question_id"], category=row["category"],
            prompt=row["prompt"], answer=text, status=_status(row),
            score=item["score"], correct=item["correct"],
            matched=list(row["matched_keywords"] or []), missing=list(row["missing_keywords"] or []),
            strengths=saved(row, "strengths", item["strengths"]),
            improvements=saved(row, "improvements", item["improvements"]),
            question_type=row.get("question_type"),
            criteria_met=grade.criteria_met, criteria_missed=grade.criteria_missed,
            evidence=grade.evidence, grader=row.get("grader"),
        )
        for row, text, item, grade in zip(rows, texts, fb["answers"], grades)
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
        role_id=s.get("role_id"), timed=bool(s.get("timed")),
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
    for _ in range(3):  # a retry covers a second /complete or an answer landing mid-scoring
        data = _load(repo, session_id, uid)
        if data["session"]["status"] == "completed":
            return _build(data)  # finishing twice (double click, retry) just returns the results
        results = _build(data)
        try:
            repo.complete_session(session_id, uid, results.overall_score,
                                  answered=sum(1 for r in data["questions"] if r["response_id"] is not None))
            break
        except PersistenceError:
            continue
    else:
        raise HTTPException(status_code=503, detail="Could not finish the interview. Please retry.")
    # Reload so completed_at reflects what was saved.
    return _build(_load(repo, session_id, uid))


@router.get("/sessions/{session_id}/results", response_model=ResultsOut)
def get_results(session_id: int, uid: str = Depends(user_id), repo=Depends(get_repo)):
    return _build(_load(repo, session_id, uid))
