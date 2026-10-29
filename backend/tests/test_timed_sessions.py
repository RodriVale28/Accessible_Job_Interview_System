"""S2 Tests for timed and untimed interview sessions, and the fallback to untimed.

Written ahead of the feature: every test here is skipped until POST /api/sessions
accepts a `timed` field. The tests expect this behaviour:

    POST /api/sessions {..., "timed": true | false}
        The timer starts when this request is made (the user pressed Begin Interview
        with "Timed" chosen). The repository is called with timed=... and stores it
        (sessions.timed column from S2-1.1).

    SessionState gains "timed": bool.
        timed:   expires_at = started_at + duration_min, seconds_left counts down,
                 answers are refused once time (plus the grace period) is up.
        untimed: expires_at and seconds_left are null, answers are never refused for time.

    Fallback: if the timed part fails (the timed session cannot be saved, or the timer
    cannot be worked out for a stored session), the interview still runs, untimed,
    and the response says timed=false. A plain database outage is still a 503.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.api.sessions import SessionCreate
from app.config import TIMER_GRACE_SECONDS
from app.repository import MemoryRepository, PersistenceError

pytestmark = pytest.mark.skipif(
    "timed" not in SessionCreate.model_fields, reason="Timed sessions not implemented yet"
)


def parse(ts):
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@pytest.fixture
def begin(client, user):
    """Start a session the way the setup page does; return (response, request start, request end)."""
    def _begin(timed, duration=15):
        before = datetime.now(timezone.utc)
        r = client.post("/api/sessions", headers=user, json={
            "job_title": "Junior Developer", "difficulty": "Easy",
            "duration_min": duration, "timed": timed,
        })
        after = datetime.now(timezone.utc)
        return r, before, after
    return _begin


def answer(client, user, session, text="A stack is LIFO: push and pop."):
    return client.post(f"/api/sessions/{session['session_id']}/answers", headers=user,
                       json={"question_id": session["question"]["id"], "text": text})


def assert_untimed(state):
    assert state["timed"] is False
    assert state["expires_at"] is None
    assert state["seconds_left"] is None


# --- timed ------------------------------------------------------------------------

@pytest.mark.parametrize("duration", [15, 30, 45])
def test_timer_starts_when_user_begins_a_timed_interview(begin, repo, duration):
    r, before, after = begin(True, duration)

    assert r.status_code == 201, r.text
    state = r.json()
    assert state["timed"] is True
    started = parse(state["started_at"])
    assert before - timedelta(seconds=1) <= started <= after + timedelta(seconds=1)
    assert parse(state["expires_at"]) == started + timedelta(minutes=duration)
    assert duration * 60 - 5 <= state["seconds_left"] <= duration * 60
    assert repo.sessions[state["session_id"]]["timed"] is True


def test_reloading_a_timed_session_keeps_the_same_timer(client, user, begin, repo):
    state = begin(True)[0].json()
    sid = state["session_id"]
    repo.sessions[sid]["started_at"] -= timedelta(minutes=5)

    again = client.get(f"/api/sessions/{sid}", headers=user).json()

    assert again["timed"] is True
    assert parse(again["started_at"]) == parse(state["started_at"]) - timedelta(minutes=5)
    assert 10 * 60 - 5 <= again["seconds_left"] <= 10 * 60  # counted down, not restarted


def test_timed_session_accepts_answers_while_time_remains(client, user, begin):
    state = begin(True)[0].json()
    assert answer(client, user, state).status_code == 200


def test_timed_session_refuses_answers_after_time_is_up(client, user, begin, repo):
    state = begin(True)[0].json()
    repo.sessions[state["session_id"]]["started_at"] -= timedelta(minutes=15, seconds=TIMER_GRACE_SECONDS + 5)

    r = answer(client, user, state)

    assert r.status_code == 409
    assert "Time is up" in r.json()["detail"]
    assert client.get(f"/api/sessions/{state['session_id']}", headers=user).json()["seconds_left"] == 0


# --- untimed ----------------------------------------------------------------------

def test_untimed_interview_has_no_timer(begin, repo):
    r, _, _ = begin(False)

    assert r.status_code == 201, r.text
    state = r.json()
    assert_untimed(state)
    assert state["question"] is not None
    assert repo.sessions[state["session_id"]]["timed"] is False


def test_reloading_an_untimed_session_stays_untimed(client, user, begin):
    state = begin(False)[0].json()
    assert_untimed(client.get(f"/api/sessions/{state['session_id']}", headers=user).json())


def test_untimed_session_accepts_answers_long_after_its_length(client, user, begin, repo):
    state = begin(False)[0].json()
    repo.sessions[state["session_id"]]["started_at"] -= timedelta(hours=3)

    assert answer(client, user, state).status_code == 200


# --- fallback to untimed ----------------------------------------------------------

class TimedSaveFails(MemoryRepository):
    """A store that cannot save the timed part of a session (e.g. column missing)."""

    def __init__(self, exc):
        super().__init__()
        self.exc = exc
        self.timed_calls = 0

    def create_session(self, *args, timed=False, **kwargs):
        if timed:
            self.timed_calls += 1
            raise self.exc
        return super().create_session(*args, timed=timed, **kwargs)


@pytest.fixture
def use_repo():
    from app.main import app
    from app.repository import get_repo

    def _use(store):
        app.dependency_overrides[get_repo] = lambda: store
        return store
    return _use


@pytest.mark.parametrize("exc", [
    PersistenceError("column sessions.timed does not exist"),
    TypeError("create_session() got an unexpected keyword argument 'timed'"),
    RuntimeError("timer service unavailable"),
], ids=["persistence", "type", "runtime"])
def test_timed_start_failure_falls_back_to_untimed(begin, use_repo, exc):
    store = use_repo(TimedSaveFails(exc))

    r, _, _ = begin(True)

    assert store.timed_calls == 1
    assert r.status_code == 201, r.text
    state = r.json()
    assert_untimed(state)
    assert state["question"] is not None


def test_fallback_session_works_as_an_untimed_interview(client, user, begin, use_repo):
    store = use_repo(TimedSaveFails(PersistenceError("timed column missing")))
    state = begin(True)[0].json()
    store.sessions[state["session_id"]]["started_at"] -= timedelta(hours=3)

    assert_untimed(client.get(f"/api/sessions/{state['session_id']}", headers=user).json())
    assert answer(client, user, state).status_code == 200


def test_database_outage_is_still_an_error_not_a_silent_fallback(begin, use_repo):
    class DatabaseDown(MemoryRepository):
        def create_session(self, *args, **kwargs):
            raise PersistenceError("database is down")

    use_repo(DatabaseDown())
    r, _, _ = begin(True)

    assert r.status_code == 503
    assert "Could not save the interview session" in r.json()["detail"]


def test_broken_timer_on_stored_session_falls_back_to_untimed(client, user, begin, repo):
    state = begin(True)[0].json()
    sid = state["session_id"]
    repo.sessions[sid]["started_at"] = None  # timer start was never recorded

    r = client.get(f"/api/sessions/{sid}", headers=user)

    assert r.status_code == 200, r.text
    assert r.json()["timed"] is False
    assert r.json()["seconds_left"] is None
    assert answer(client, user, state).status_code == 200
