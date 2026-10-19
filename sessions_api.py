"""S1-1.2 Start-session API (FastAPI) — owner: Owen Erickson

POST /sessions
    Takes the interview setup form (job title, difficulty, duration), validates it,
    creates the session through the repository (S1-4.2, Sublime), gets the first
    question through the question service (S1-2.2, Moshood) and returns the start
    response the front end needs (session id, first question, progress info).

The repository and question service are injected with FastAPI's Depends(). Until
the real ones exist, the in-memory stubs at the bottom of this file are used, so
the endpoint works and can be tested today. To plug in the real ones, change
get_session_repository() and get_question_service() (or override them in tests).
"""
from enum import Enum
from typing import Dict, Optional, Protocol, Union

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

router = APIRouter()

# Session length (minutes) -> number of questions. Same values as the prototype's config.py.
QUESTIONS_BY_LENGTH: Dict[int, int] = {15: 5, 30: 8, 45: 10}


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
class InterviewType(str, Enum):
    technical = "Technical"  # Sprint 1: technical interviews only


class Difficulty(str, Enum):
    # TODO: confirm these values with Kobra, Kieu and Riket (must match the question seed data)
    easy = "Easy"
    medium = "Medium"
    hard = "Hard"


class SessionCreate(BaseModel):
    """Request body: the interview setup form."""

    model_config = ConfigDict(extra="forbid")

    job_title: str = Field(..., max_length=100, examples=["Backend Developer"])
    interview_type: InterviewType = InterviewType.technical
    difficulty: Difficulty
    duration_min: int = Field(..., examples=[15])

    @field_validator("job_title")
    @classmethod
    def job_title_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Job title is required.")
        return value

    @field_validator("duration_min")
    @classmethod
    def duration_is_supported(cls, value: int) -> int:
        if value not in QUESTIONS_BY_LENGTH:
            raise ValueError("Duration must be 15, 30, or 45 minutes.")
        return value


class Question(BaseModel):
    id: Union[int, str]
    prompt: str


class SessionStartResponse(BaseModel):
    """Response body: everything the front end needs to start the interview."""

    session_id: int
    job_title: str
    interview_type: InterviewType
    difficulty: Difficulty
    duration_min: int
    question: Question
    q_index: int = 1  # the first question is always number 1
    total: int  # total questions in this interview (drives the progress indicator)


# --------------------------------------------------------------------------
# Interfaces for the pieces owned by teammates
# --------------------------------------------------------------------------
class SessionRepository(Protocol):
    """Implemented by Sublime (S1-4.2). Returns the new session's id."""

    def create_session(self, config: SessionCreate, total_questions: int) -> int: ...


class QuestionService(Protocol):
    """Implemented by Moshood (S1-2.2). Returns None if no question is available."""

    def get_first_question(
        self, session_id: int, config: SessionCreate
    ) -> Optional[Question]: ...


# --------------------------------------------------------------------------
# Endpoint
# --------------------------------------------------------------------------
def get_session_repository() -> SessionRepository:
    return _session_repository  # TODO: swap for Sublime's PostgreSQL repository


def get_question_service() -> QuestionService:
    return _question_service  # TODO: swap for Moshood's question-selection service


@router.post(
    "/sessions",
    response_model=SessionStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a technical interview session",
    responses={
        404: {"description": "No questions available for this configuration"},
        422: {"description": "Invalid setup data (blank job title, bad duration, etc.)"},
        503: {"description": "The session could not be saved"},
    },
)
def start_session(
    body: SessionCreate,
    repo: SessionRepository = Depends(get_session_repository),
    questions: QuestionService = Depends(get_question_service),
) -> SessionStartResponse:
    total = QUESTIONS_BY_LENGTH[body.duration_min]

    try:
        session_id = repo.create_session(body, total)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not save the interview session. Please try again.",
        )

    first_question = questions.get_first_question(session_id, body)
    if first_question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions are available for this interview setup.",
        )

    return SessionStartResponse(
        session_id=session_id,
        job_title=body.job_title,
        interview_type=body.interview_type,
        difficulty=body.difficulty,
        duration_min=body.duration_min,
        question=first_question,
        q_index=1,
        total=total,
    )


# --------------------------------------------------------------------------
# Temporary stand-ins until S1-4.2 and S1-2.2 are merged
# --------------------------------------------------------------------------
class InMemorySessionRepository:
    def __init__(self) -> None:
        self.sessions: Dict[int, dict] = {}
        self.next_id = 1

    def create_session(self, config: SessionCreate, total_questions: int) -> int:
        session_id = self.next_id
        self.next_id += 1

        self.sessions[session_id] = {
            **config.model_dump(mode="json"),
            "total_questions": total_questions,
            "status": "in_progress",
        }

        return session_id


class StubQuestionService:
    def get_first_question(
        self, session_id: int, config: SessionCreate
    ) -> Optional[Question]:
        return Question(
            id=1,
            prompt="Placeholder question: explain the difference between a list and a tuple in Python.",
        )


_session_repository = InMemorySessionRepository()
_question_service = StubQuestionService()
