"""S2-1.3 Roles endpoints: list roles and match a job title to a role."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import user_id
from app.repository import PersistenceError, get_repo  # assumption: check where PersistenceError lives
from app.services.role_matcher import match_role

router = APIRouter()


class RoleOut(BaseModel):
    id: int
    name: str


class MatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    job_title: str = Field(min_length=1, max_length=100)


class RoleMatchOut(BaseModel):
    role_id: int | None
    role_name: str | None
    matched_by: Literal["ai", "keyword"]


@router.get("/roles", response_model=list[RoleOut], summary="List interview roles")
def get_roles(uid: str = Depends(user_id), repo=Depends(get_repo)) -> list[RoleOut]:
    try:
        return [RoleOut(id=r["id"], name=r["name"]) for r in repo.list_roles()]
    except PersistenceError:
        raise HTTPException(status_code=503, detail="Could not load the roles. Please try again.")


@router.post("/roles/match", response_model=RoleMatchOut, summary="Match a job title to a role")
def post_match(body: MatchRequest, uid: str = Depends(user_id), repo=Depends(get_repo)) -> RoleMatchOut:
    try:
        roles = repo.list_roles()
    except PersistenceError:
        raise HTTPException(status_code=503, detail="Could not match the job title. Please try again.")
    return RoleMatchOut(**match_role(body.job_title, roles))
