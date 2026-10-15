"""S1-1.2 Start-session API (FastAPI) - owner: Owen Erickson

POST /api/sessions        configure + start a technical interview, returns the first question
GET  /api/sessions/{id}   current state (used when the session page loads or reloads)
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.api.deps import expires_at, load_session, seconds_left, user_id
from app.repository import get_repo
from app.services import question_service as qs

router = APIRouter()

Difficulty = Literal["Easy", "Medium", "Hard"]


class SessionCreate(BaseModel):
    job_title: str = Field(..., min_length=2, max_length=120)
    interview_type: Literal["Technical"] = "Technical"   # Sprint 1: technical only
    difficulty: Difficulty
    duration_min: Literal[15, 30, 45]

    @field_validator("job_title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Job title must be at least 2 characters.")
        return v


class QuestionOut(BaseModel):
    id: int
    prompt: str
    category: str


class SessionState(BaseModel):
    session_id: int
    job_title: str
    interview_type: str
    difficulty: str
    duration_min: int
    status: Literal["in_progress", "completed"]
    q_index: int
    total: int
    correct_count: int
    question: Optional[QuestionOut]
    started_at: datetime
    expires_at: datetime
    seconds_left: int


def session_state(repo, s: dict) -> SessionState:
    q, idx = (None, s["total_questions"]) if s["status"] == "completed" else qs.current_question(repo, s)
    return SessionState(
        session_id=s["id"], job_title=s["job_title"], interview_type=s["interview_type"],
        difficulty=s["difficulty"], duration_min=s["duration_min"], status=s["status"],
        q_index=idx, total=s["total_questions"], correct_count=s["correct_count"],
        question=QuestionOut(**qs.public_question(q)) if q else None,
        started_at=s["started_at"], expires_at=expires_at(s), seconds_left=seconds_left(s),
    )


@router.post("/sessions", response_model=SessionState, status_code=201)
def start_session(body: SessionCreate, uid: str = Depends(user_id), repo=Depends(get_repo)):
    try:
        total = qs.planned_total(repo, body.difficulty, body.duration_min)
        s = repo.create_session(uid, body.job_title, body.difficulty, body.duration_min, total)
        qs.next_question(repo, s)
    except qs.NoQuestionAvailable as e:
        raise HTTPException(status_code=404, detail=str(e))
    return session_state(repo, s)


@router.get("/sessions/{session_id}", response_model=SessionState)
def get_session(session_id: int, uid: str = Depends(user_id), repo=Depends(get_repo)):
    return session_state(repo, load_session(repo, session_id, uid))
