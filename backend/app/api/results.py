"""S1-5 Results API (uses S1-5.1 evaluator + S1-5.2 feedback rules)

POST /api/sessions/{id}/complete  finish the interview (all answered, time up, or "End now")
GET  /api/sessions/{id}/results   saved score + per-answer feedback (works after logout/return)
"""
from __future__ import annotations

from typing import Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import load_session, user_id
from app.evaluation.feedback_rules import feedback_for_answer, session_feedback
from app.evaluation.keyword_evaluator import AnswerScore, KeywordEvaluator
from app.repository import get_repo

router = APIRouter()
evaluator = KeywordEvaluator()


class AnswerResult(BaseModel):
    q_index: int
    question_id: int
    category: str
    prompt: str
    answer: str
    status: str          # answered | blank | unanswered
    score: int
    correct: bool
    matched: list[str]
    missing: list[str]
    strengths: str
    improvements: str


class Results(BaseModel):
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
    answers: list[AnswerResult]


def build_results(repo, s: dict) -> Results:
    asked = repo.asked_questions(s["id"])
    responses = repo.get_responses(s["id"])
    feedback = repo.get_feedback(s["id"])
    answers = []
    for a in asked:
        q = repo.get_question(a["question_id"])
        r = responses.get(a["question_id"])
        f = feedback.get(a["question_id"], {})
        status = "unanswered" if not r else ("blank" if r["is_blank"] else "answered")
        answers.append(AnswerResult(
            q_index=a["q_index"], question_id=q["id"], category=q["category"], prompt=q["prompt"],
            answer=r["answer_text"] if r else "", status=status, score=f.get("score", 0),
            correct=f.get("correct", False), matched=list(f.get("matched") or []),
            missing=list(f["missing"] if "missing" in f else q["expected_keywords"]),
            strengths=f.get("strengths", ""), improvements=f.get("improvements", "")))
    summary = session_feedback([a.model_dump() for a in answers], s["total_questions"],
                               s["overall_score"] or 0, s["correct_count"])
    return Results(
        session_id=s["id"], job_title=s["job_title"], interview_type=s["interview_type"],
        difficulty=s["difficulty"], duration_min=s["duration_min"], overall_score=s["overall_score"] or 0,
        correct_count=s["correct_count"], total=s["total_questions"], completed_at=s["completed_at"],
        answers=answers, **summary)


@router.post("/sessions/{session_id}/complete", response_model=Results)
def complete_session(session_id: int, uid: str = Depends(user_id), repo=Depends(get_repo)):
    s = load_session(repo, session_id, uid)
    if s["status"] != "completed":
        responses = repo.get_responses(session_id)
        feedback = repo.get_feedback(session_id)
        missing = {}
        for a in repo.asked_questions(session_id):
            if a["question_id"] not in responses:   # shown but never answered
                q = repo.get_question(a["question_id"])
                res = AnswerScore(matched=[], missing=list(q["expected_keywords"]), score=0, correct=False)
                fb = feedback_for_answer(res, answered=False)
                missing[q["id"]] = {"score": 0, "correct": False, "matched": [], "missing": res.missing,
                                    "strengths": fb["strengths"], "improvements": fb["improvements"]}
        scores = [AnswerScore(score=f["score"], correct=f["correct"]) for f in feedback.values()]
        totals = evaluator.overall(scores, s["total_questions"])
        repo.complete_session(session_id, totals["overall_score"], totals["correct_count"], missing)
        s = load_session(repo, session_id, uid)
    return build_results(repo, s)


@router.get("/sessions/{session_id}/results", response_model=Results)
def get_results(session_id: int, uid: str = Depends(user_id), repo=Depends(get_repo)):
    s = load_session(repo, session_id, uid)
    if s["status"] != "completed":
        raise HTTPException(status_code=409, detail="This interview is still in progress.")
    return build_results(repo, s)
