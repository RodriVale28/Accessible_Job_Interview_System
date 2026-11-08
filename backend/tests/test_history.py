
"""S2-4.1: Interview history and discard API tests - Sublime Mpanda."""

import uuid


def test_discard_unfinished_session(client, user, start, repo):
    """The owner can discard an unfinished interview."""
    session = start()
    session_id = session["session_id"]

    response = client.delete(
        f"/api/sessions/{session_id}",
        headers=user,
    )

    assert response.status_code == 204
    assert repo.get_session(session_id, user["X-User-Id"]) is None


def test_other_user_cannot_discard_session(client, user, start, repo):
    """An interview belonging to another user returns 404."""
    session = start()
    session_id = session["session_id"]

    other_user = {"X-User-Id": str(uuid.uuid4())}

    response = client.delete(
        f"/api/sessions/{session_id}",
        headers=other_user,
    )

    assert response.status_code == 404
    assert repo.get_session(session_id, user["X-User-Id"]) is not None


def test_completed_session_cannot_be_discarded(client, user, start, repo):
    """A completed interview cannot be discarded."""
    session = start()
    session_id = session["session_id"]

    repo.complete_session(session_id, user["X-User-Id"], 80)

    response = client.delete(
        f"/api/sessions/{session_id}",
        headers=user,
    )

    assert response.status_code == 409
    assert repo.get_session(session_id, user["X-User-Id"]) is not None


def test_nonexistent_session_returns_404(client, user):
    """An unknown interview ID returns 404."""
    response = client.delete(
        "/api/sessions/999999",
        headers=user,
    )

    assert response.status_code == 404


def test_discard_requires_authentication(client, start, monkeypatch):
    """Unauthenticated users cannot discard interviews."""
    from app import config

    session = start()
    session_id = session["session_id"]

    monkeypatch.setattr(config, "ALLOW_GUEST", False)

    response = client.delete(f"/api/sessions/{session_id}")

    assert response.status_code == 401


def test_discard_invalid_session_id(client, user):
    """Invalid session IDs are rejected."""
    response = client.delete(
        "/api/sessions/not-a-number",
        headers=user,
    )

    assert response.status_code == 422
