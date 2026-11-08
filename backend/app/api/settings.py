
"""S2-4.1: Accessibility settings API - Sublime Mpanda."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from app.api.deps import user_id
from app.repository import PersistenceError, get_repo

router = APIRouter()


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text_size: Literal["sm", "md", "lg", "xl"] = "md"
    theme: Literal["light", "dark", "contrast"] = "light"
    font: Literal["default", "dyslexic"] = "default"
    read_aloud: bool = False


@router.get("/settings", response_model=Settings)
def get_settings(
    uid: str = Depends(user_id),
    repo=Depends(get_repo),
):
    """Retrieve the current user's accessibility settings."""
    try:
        saved = repo.get_settings(uid)
        return Settings(**saved) if saved else Settings()

    except PersistenceError:
        raise HTTPException(
            status_code=503,
            detail="Could not load your settings. Please try again.",
        )


@router.put("/settings", response_model=Settings)
def update_settings(
    settings: Settings,
    uid: str = Depends(user_id),
    repo=Depends(get_repo),
):
    """Save the current user's accessibility settings."""
    try:
        repo.save_settings(uid, settings.model_dump())
        return settings

    except PersistenceError:
        raise HTTPException(
            status_code=503,
            detail="Could not save your settings. Please try again.",
        )
