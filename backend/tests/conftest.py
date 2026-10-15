"""Shared fixtures. Every API test runs against the in-memory store, and also
against real PostgreSQL when TEST_DATABASE_URL is set (CI does this)."""
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repository import MemoryRepository, PostgresRepository, get_repo

TEST_DB = os.environ.get("TEST_DATABASE_URL", "").strip()
_pg = None


def _postgres_repo():
    global _pg
    if _pg is None:
        _pg = PostgresRepository(TEST_DB)
        _pg.init()
    with _pg.pool.connection() as c:
        c.execute("TRUNCATE feedback, responses, session_questions, sessions RESTART IDENTITY CASCADE")
    return _pg


@pytest.fixture(params=["memory"] + (["postgres"] if TEST_DB else []))
def repo(request):
    return MemoryRepository() if request.param == "memory" else _postgres_repo()


@pytest.fixture
def client(repo):
    app.dependency_overrides[get_repo] = lambda: repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def user():
    return {"X-User-Id": str(uuid.uuid4())}


@pytest.fixture
def start(client, user):
    def _start(difficulty="Easy", duration=15, title="Junior Software Engineer", headers=None):
        r = client.post("/api/sessions", headers=headers or user,
                        json={"job_title": title, "difficulty": difficulty, "duration_min": duration})
        assert r.status_code == 201, r.text
        return r.json()
    return _start


@pytest.fixture(scope="session", autouse=True)
def _close_pool():
    yield
    if _pg is not None:
        _pg.pool.close()
