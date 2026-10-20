"""Shared request helpers for the API routers."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException

from app.config import TIMER_GRACE_SECONDS


def user_id(x_user_id: str = Header(..., description="Browser guest id (UUID). Replaced by login in US-0.")) -> str:
    try:
        return str(uuid.UUID(x_user_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Missing or invalid user id.")


def load_session(repo, session_id: int, uid: str) -> dict:
    s = repo.get_session(session_id, uid)
    if not s:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    return s


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def expires_at(session: dict) -> datetime:
    return _aware(session["started_at"]) + timedelta(minutes=session["duration_min"])


def seconds_left(session: dict) -> int:
    return max(0, int((expires_at(session) - datetime.now(timezone.utc)).total_seconds()))


def time_is_up(session: dict) -> bool:
    return datetime.now(timezone.utc) > expires_at(session) + timedelta(seconds=TIMER_GRACE_SECONDS)
