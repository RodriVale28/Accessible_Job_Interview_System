"""FastAPI entry point - Interview Studio, Sprint 1.

  app/api/sessions.py                  S1-1.2  Owen      configure/start session
  app/services/question_service.py     S1-2.2  Moshood   question selection
  app/api/answers.py                   S1-3.2  Jayme     submit answer -> next question
  app/repository.py                    S1-4.2  Sublime   persistence (Supabase/PostgreSQL)
  app/evaluation/keyword_evaluator.py  S1-5.1  Prince    scoring
  app/evaluation/feedback_rules.py     S1-5.2  Aisha     feedback text
  app/api/results.py                   S1-5    results payload for the results page
Run locally:  uvicorn app.main:app --reload --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import answers, results, sessions
from app.config import CORS_ORIGINS
from app.repository import PersistenceError, get_repo

log = logging.getLogger("interview_studio")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_repo().init()          # creates tables + loads the 50 questions (idempotent)
    except Exception:
        log.exception("Database initialisation failed - /health will report database=false")
    yield


app = FastAPI(title="Interview Studio API", version="1.0.0-sprint1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(PersistenceError)
def persistence_error(_: Request, exc: PersistenceError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/health")
def health():
    """Render health check + smoke test target (S1-4.3)."""
    repo = get_repo()
    store = "postgres" if type(repo).__name__ == "PostgresRepository" else "memory"
    return {"ok": True, "store": store, "database": repo.ping()}


app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(answers.router, prefix="/api", tags=["answers"])
app.include_router(results.router, prefix="/api", tags=["results"])
