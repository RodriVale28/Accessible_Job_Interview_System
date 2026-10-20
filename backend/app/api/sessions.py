"""S1-1.2 Start-session API (FastAPI) — owner: Owen Erickson

POST /api/sessions
    Takes the interview setup form (job title, difficulty, duration), validates it,
    creates the session through the repository (S1-4.2), picks the first question
    through the question service (S1-2.2) and returns the session state.

GET /api/sessions/{id}
    Returns the same state, so the interview page can load or reload a session.

Both answer with SessionState (frontend/lib/types.ts).
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.deps import expires_at, load_session, seconds_left, user_id
from app.repository import QUESTION_COUNTS, PersistenceError, get_repo
from app.services import question_service as qs

router = APIRouter()


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
class InterviewType(str, Enum):
    technical = "Technical"  # Sprint 1: technical interviews only


class Difficulty(str, Enum):
    easy = "Easy"
    medium = "Medium"
    hard = "Hard"


class SessionCreate(BaseModel):
    """Request body: the interview setup form."""

    model_config = ConfigDict(extra="forbid")

    job_title: str = Field(..., max_length=120, examples=["Backend Developer"])
    interview_type: InterviewType = InterviewType.technical
    difficulty: Difficulty
    duration_min: int = Field(..., examples=[15])

    @field_validator("job_title")
    @classmethod
    def job_title_valid(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Job title is required.")
        if len(value) < 2:
            raise ValueError("Job title must be at least 2 characters.")
        if not any(ch.isalpha() for ch in value):
            raise ValueError("Job title must include letters, not only numbers or special characters.")
        return value

    @field_validator("duration_min")
    @classmethod
    def duration_is_supported(cls, value: int) -> int:
        if value not in QUESTION_COUNTS:
            raise ValueError("Duration must be 15, 30, or 45 minutes.")
        return value


class QuestionOut(BaseModel):
    """A question as shown to the user (expected_keywords is never included)."""

    id: int
    prompt: str
    category: Optional[str] = None


class SessionState(BaseModel):
    """Everything the interview page needs to show the current question."""

    session_id: int
    job_title: str
    interview_type: str
    difficulty: str
    duration_min: int
    status: str
    q_index: int
    total: int
    correct_count: int
    question: Optional[QuestionOut]
    started_at: datetime
    expires_at: datetime
    seconds_left: int


def session_state(repo, s: dict) -> SessionState:
    current, q_index = qs.current_question(repo, s)
    return SessionState(
        session_id=s["id"], job_title=s["job_title"], interview_type=s["interview_type"],
        difficulty=s["difficulty"], duration_min=s["duration_min"], status=s["status"],
        q_index=q_index, total=s["total_questions"], correct_count=s["correct_count"],
        question=QuestionOut(**current) if current and s["status"] == "in_progress" else None,
        started_at=s["started_at"], expires_at=expires_at(s), seconds_left=seconds_left(s),
    )


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------
@router.post(
    "/sessions",
    response_model=SessionState,
    status_code=status.HTTP_201_CREATED,
    summary="Start a technical interview session",
    responses={
        404: {"description": "No questions available for this configuration"},
        422: {"description": "Invalid setup data (blank job title, bad duration, etc.)"},
        503: {"description": "The session could not be saved"},
    },
)
def start_session(body: SessionCreate, uid: str = Depends(user_id), repo=Depends(get_repo)) -> SessionState:
    try:
        session_id = repo.create_session(uid, body.job_title, body.difficulty.value, body.duration_min)
        qs.next_question(session_id, body.difficulty.value, repo=repo)
        s = repo.get_session(session_id, uid)
    except qs.NoQuestionAvailable as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PersistenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not save the interview session. Please try again.",
        )
    return session_state(repo, s)


@router.get("/sessions/{session_id}", response_model=SessionState, summary="Load an interview session")
def get_session(session_id: int, uid: str = Depends(user_id), repo=Depends(get_repo)) -> SessionState:
    try:
        return session_state(repo, load_session(repo, session_id, uid))
    except PersistenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not load the interview. Please try again.",
        )
