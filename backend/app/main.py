"""FastAPI entry point - Interview Studio, Sprint 1.
Run locally (from backend/):  uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api import answers, results, roles, sessions
from app.config import CORS_ORIGINS
from app.repository import get_repo

app = FastAPI(title="Interview Studio API", version="0.1.0-sprint1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Render health check + smoke test target (S1-4.3)."""
    return {"ok": True}

@app.get("/health/db")
def health_db():
    """Check database connectivity."""
    if not get_repo().ping():
        raise HTTPException(
            status_code=503,
            detail="Database health check failed",
        )
    return {"ok": True}

app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(answers.router, prefix="/api", tags=["answers"])
app.include_router(results.router, prefix="/api", tags=["results"])
app.include_router(roles.router, prefix="/api", tags=["roles"])  # S2-1.3
