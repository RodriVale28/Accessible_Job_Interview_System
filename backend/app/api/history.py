
"""S2-4.1: Discard unfinished interview sessions."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.deps import user_id
from app.repository import PersistenceError, get_repo

router = APIRouter()


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def discard_interview(
    session_id: int,
    uid: str = Depends(user_id),
    repo=Depends(get_repo),
):
    """Discard an unfinished interview belonging to the current user."""
    try:
        session = repo.get_session(session_id, uid)

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Interview not found.",
            )

        if session["status"] != "in_progress":
            raise HTTPException(
                status_code=409,
                detail="Completed interviews cannot be discarded.",
            )

        if not repo.discard_session(session_id, uid):
            raise HTTPException(
                status_code=409,
                detail="This interview could not be discarded.",
            )

        return Response(status_code=204)

    except PersistenceError:
        raise HTTPException(
            status_code=503,
            detail="Could not discard your interview. Please try again.",
        )
