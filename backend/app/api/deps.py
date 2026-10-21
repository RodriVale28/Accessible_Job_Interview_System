"""Shared request helpers for the API routers."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Header, HTTPException

from app import config
from app.config import TIMER_GRACE_SECONDS

_jwks: jwt.PyJWKClient | None = None


def _verify_token(token: str) -> str:
    """Check a Supabase login token against the project's public keys; return the user id."""
    global _jwks
    if _jwks is None:
        _jwks = jwt.PyJWKClient(f"{config.SUPABASE_URL}/auth/v1/.well-known/jwks.json", cache_keys=True)
    key = _jwks.get_signing_key_from_jwt(token).key
    # leeway: Render's clock can run a little behind Supabase's, which would reject a fresh token
    claims = jwt.decode(token, key, algorithms=["ES256", "RS256"], audience="authenticated",
                        issuer=f"{config.SUPABASE_URL}/auth/v1", leeway=30)
    return str(uuid.UUID(claims["sub"]))


def user_id(
    authorization: str | None = Header(None, description="Bearer <Supabase access token>"),
    x_user_id: str | None = Header(None, description="Guest id (UUID); only when ALLOW_GUEST is on"),
) -> str:
    """The signed-in user's id (Supabase auth.users.id)."""
    if authorization and authorization.lower().startswith("bearer "):
        if not config.SUPABASE_URL:
            raise HTTPException(status_code=500, detail="Login is not configured on the server.")
        try:
            return _verify_token(authorization[7:].strip())
        except (jwt.PyJWTError, KeyError, ValueError):
            raise HTTPException(status_code=401, detail="Your login has expired. Please log in again.")
    if config.ALLOW_GUEST and x_user_id:
        try:
            return str(uuid.UUID(x_user_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Missing or invalid user id.")
    raise HTTPException(status_code=401, detail="Please log in to continue.")


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
