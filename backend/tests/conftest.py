import os
import uuid

os.environ.setdefault("ALLOW_GUEST", "1")  # tests sign in with a guest id (X-User-Id)

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repository import MemoryRepository, get_repo


@pytest.fixture
def repo():
    """A fresh in-memory store seeded with the 50-question library, used by the API."""
    store = MemoryRepository()
    app.dependency_overrides[get_repo] = lambda: store
    yield store
    app.dependency_overrides.clear()


@pytest.fixture
def client(repo):
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def user():
    """Request headers for a guest user."""
    return {"X-User-Id": str(uuid.uuid4())}


@pytest.fixture
def start(client, user):
    """Start a session for `user` and return the response body."""
    def _start(difficulty="Easy", duration=15, job_title="Junior Developer"):
        r = client.post("/api/sessions", headers=user,
                        json={"job_title": job_title, "difficulty": difficulty, "duration_min": duration})
        assert r.status_code == 201, r.text
        return r.json()
    return _start
