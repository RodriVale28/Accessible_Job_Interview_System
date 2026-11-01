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
    def _start(difficulty="Easy", duration=15, job_title="Junior Developer",
               timed=False, role_id=None, interview_type=None):
        body = {"job_title": job_title, "difficulty": difficulty, "duration_min": duration, "timed": timed}
        if role_id is not None:
            body["role_id"] = role_id
        if interview_type is not None:
            body["interview_type"] = interview_type
        r = client.post("/api/sessions", headers=user, json=body)
        assert r.status_code == 201, r.text
        return r.json()
    return _start


# ---- S2-1.3 -----------------------------------------------------------------
FAKE_ROLES = [
    {"id": 1, "name": "Software Engineer", "keywords": ["software", "engineer", "developer", "programmer"], "technical_share": 0.8},
    {"id": 2, "name": "Data Analyst", "keywords": ["data", "analyst", "analytics", "sql", "bi"], "technical_share": 0.6},
    {"id": 3, "name": "IT Support", "keywords": ["it", "help desk", "technician", "support"], "technical_share": 0.6},
    {"id": 4, "name": "Customer Service", "keywords": ["customer", "call center", "agent", "service"], "technical_share": 0.0},
]


@pytest.fixture
def fake_roles(repo, monkeypatch):
    """The 4 roles, whether or not S2-1.1 / S2-1.4 have merged (raising=False)."""
    by_id = {r["id"]: r for r in FAKE_ROLES}
    monkeypatch.setattr(repo, "list_roles", lambda: [dict(r) for r in FAKE_ROLES], raising=False)
    monkeypatch.setattr(repo, "get_role", lambda rid: dict(by_id[rid]) if rid in by_id else None, raising=False)
    return FAKE_ROLES
