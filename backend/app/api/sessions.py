"""S1-1.2 Start-session API (FastAPI) — owner: Owen Erickson
S2-1.3 adds role_id, interview_type (Technical / Behavioral / Mixed) and an optional timer.

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

from app.api.deps import expires_at, load_session, seconds_left, time_is_up, user_id
from app.repository import QUESTION_COUNTS, PersistenceError, get_repo
from app.services import question_service as qs

router = APIRouter()


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
class InterviewType(str, Enum):
    technical = "Technical"
    behavioral = "Behavioral"
    mixed = "Mixed"


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
    role_id: Optional[int] = None  # S2-1.3: from POST /api/roles/match or the user's own pick
    timed: bool = False  # S2-1.3: the countdown is optional and off by default

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
    expires_at: Optional[datetime] = None  # None when the interview is not timed
    seconds_left: Optional[int] = None  # None when the interview is not timed
    role_name: Optional[str] = None
    timed: bool = False


def _role_name(repo, s: dict) -> Optional[str]:
    """Name of the session's role, or None for role-less (Sprint 1 style) interviews."""
    role_id = s.get("role_id")
    if role_id is None:
        return None
    role = repo.get_role(role_id)
    return role["name"] if role else None


def session_state(repo, s: dict) -> SessionState:
    current, q_index = qs.current_question(repo, s)
    if (current is None and s["status"] == "in_progress"
            and q_index < s["total_questions"] and not time_is_up(s)):
        # The last answer saved but asking the next question failed (a 503): ask it now
        # instead of leaving the interview stuck with nothing to answer.
        try:
            qs.next_question(s["id"], s["difficulty"], repo=repo, role_id=s.get("role_id"),
                             interview_type=s.get("interview_type") or "Technical")
            current, q_index = qs.current_question(repo, s)
        except (qs.NoQuestionAvailable, PersistenceError):
            pass
    return SessionState(
        session_id=s["id"], job_title=s["job_title"], interview_type=s["interview_type"],
        difficulty=s["difficulty"], duration_min=s["duration_min"], status=s["status"],
        q_index=q_index, total=s["total_questions"], correct_count=s["correct_count"],
        question=QuestionOut(**current) if current and s["status"] == "in_progress" else None,
        started_at=s["started_at"], expires_at=expires_at(s), seconds_left=seconds_left(s),
        role_name=_role_name(repo, s), timed=bool(s.get("timed")),
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
        422: {"description": "Invalid setup data (blank job title, bad duration, unknown role, etc.)"},
        503: {"description": "The session could not be saved"},
    },
)
def start_session(body: SessionCreate, uid: str = Depends(user_id), repo=Depends(get_repo)) -> SessionState:
    session_id = None
    try:
        if body.role_id is not None and repo.get_role(body.role_id) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="That role is not available. Please pick one from the list.",
            )
        session_id = repo.create_session(
            uid, body.job_title, body.difficulty.value, body.duration_min,
            role_id=body.role_id, interview_type=body.interview_type.value, timed=body.timed,
        )
        qs.next_question(session_id, body.difficulty.value, repo=repo,
                         role_id=body.role_id, interview_type=body.interview_type.value)
        return session_state(repo, repo.get_session(session_id, uid))
    except HTTPException:
        raise
    except Exception as exc:
        if session_id is not None:  # never leave an empty in-progress session behind
            try:
                repo.discard_session(session_id, uid)
            except Exception:
                pass
        if isinstance(exc, qs.NoQuestionAvailable):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        if isinstance(exc, PersistenceError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not save the interview session. Please try again.",
            )
        raise


@router.get("/sessions/{session_id}", response_model=SessionState, summary="Load an interview session")
def get_session(session_id: int, uid: str = Depends(user_id), repo=Depends(get_repo)) -> SessionState:
    try:
        return session_state(repo, load_session(repo, session_id, uid))
    except PersistenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not load the interview. Please try again.",
        )


class SessionSummary(BaseModel):
    session_id: int
    job_title: str
    difficulty: str
    duration_min: int
    status: str
    overall_score: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    role_name: Optional[str] = None  # S2-1.3
    interview_type: str = "Technical"  # S2-1.3
    timed: bool = False


@router.get("/sessions", response_model=list[SessionSummary], summary="List the user's past interviews")
def list_sessions(uid: str = Depends(user_id), repo=Depends(get_repo)) -> list[SessionSummary]:
    try:
        rows = repo.list_sessions(uid)
    except PersistenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not load your past interviews. Please try again.",
        )
    return [SessionSummary(session_id=r["id"], **{k: v for k, v in r.items() if k != "id"}) for r in rows]
