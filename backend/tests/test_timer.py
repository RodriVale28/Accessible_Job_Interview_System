"""S2-X.1 Timer tests: timed vs untimed interviews (contract from S2-1.3).

The timer starts when the user begins a timed interview (POST /api/sessions with
timed=true). Timed sessions refuse answers once time and the grace period are up (409);
untimed sessions have no countdown and never refuse an answer for time. Answers are
graded by the keyword grader when the AI is off. Basic cases live in
test_sessions_sprint2.py (S2-1.3); these add the edges.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app import config
from app.config import TIMER_GRACE_SECONDS


def parse(ts):
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def submit(client, user, sid, text="A stack is LIFO: push and pop."):
    """Answer the session's current question."""
    current = client.get(f"/api/sessions/{sid}", headers=user).json()
    return client.post(f"/api/sessions/{sid}/answers", headers=user,
                       json={"question_id": current["question"]["id"], "text": text})


def move_start_back(repo, sid, **delta):
    """Pretend the interview started earlier instead of making the test wait."""
    repo.sessions[sid]["started_at"] -= timedelta(**delta)


@pytest.fixture
def ai_off(monkeypatch):
    """AI_ENABLED=0, and the AI is never reached even if a flag is missed."""
    monkeypatch.setenv("AI_ENABLED", "0")
    monkeypatch.setattr(config, "AI_ENABLED", False, raising=False)
    try:
        from app import ai
    except ImportError:  # S2-2.1 not merged: grading is keyword-only anyway
        return
    monkeypatch.setattr(ai, "ask_json", lambda *a, **k: None)


# --- timed ------------------------------------------------------------------------

@pytest.mark.parametrize("duration", [15, 30, 45])
def test_timer_starts_when_the_user_begins_a_timed_interview(start, repo, duration):
    before = datetime.now(timezone.utc)
    s = start(timed=True, duration=duration)
    after = datetime.now(timezone.utc)

    started = parse(s["started_at"])
    assert before - timedelta(seconds=1) <= started <= after + timedelta(seconds=1)
    assert parse(s["expires_at"]) == started + timedelta(minutes=duration)
    assert duration * 60 - 5 <= s["seconds_left"] <= duration * 60
    assert repo.sessions[s["session_id"]]["timed"] is True


def test_reloading_a_timed_session_keeps_counting_down(client, user, start, repo):
    s = start(timed=True)
    move_start_back(repo, s["session_id"], minutes=5)

    again = client.get(f"/api/sessions/{s['session_id']}", headers=user).json()

    assert again["timed"] is True
    assert parse(again["expires_at"]) == parse(s["expires_at"]) - timedelta(minutes=5)
    assert 10 * 60 - 5 <= again["seconds_left"] <= 10 * 60  # not restarted


def test_timed_session_accepts_answers_while_time_remains(client, user, start, repo):
    s = start(timed=True)
    move_start_back(repo, s["session_id"], minutes=14)

    assert submit(client, user, s["session_id"]).status_code == 200


def test_timed_session_accepts_answers_during_the_grace_period(client, user, start, repo):
    s = start(timed=True)
    move_start_back(repo, s["session_id"], minutes=15, seconds=TIMER_GRACE_SECONDS - 5)

    assert submit(client, user, s["session_id"]).status_code == 200


def test_timed_session_refuses_answers_after_the_grace_period(client, user, start, repo):
    s = start(timed=True)
    sid = s["session_id"]
    move_start_back(repo, sid, minutes=15, seconds=TIMER_GRACE_SECONDS + 5)

    r = submit(client, user, sid)

    assert r.status_code == 409
    assert "Time is up" in r.json()["detail"]
    assert repo.get_responses(sid) == {}
    assert client.get(f"/api/sessions/{sid}", headers=user).json()["seconds_left"] == 0


def test_timed_session_can_still_be_finished_after_time_is_up(client, user, start, repo):
    # The interview page finishes the interview itself when the countdown hits zero.
    s = start(timed=True)
    submit(client, user, s["session_id"])
    move_start_back(repo, s["session_id"], hours=1)

    r = client.post(f"/api/sessions/{s['session_id']}/complete", headers=user)

    assert r.status_code == 200
    assert r.json()["answered_count"] == 1


# --- untimed ----------------------------------------------------------------------

def test_untimed_session_never_gets_a_countdown(client, user, start, repo):
    s = start(timed=False)
    move_start_back(repo, s["session_id"], days=2)

    again = client.get(f"/api/sessions/{s['session_id']}", headers=user).json()

    assert again["timed"] is False
    assert again["expires_at"] is None
    assert again["seconds_left"] is None
    assert repo.sessions[s["session_id"]]["timed"] is False


def test_untimed_session_can_be_finished_long_after_its_length(client, user, start, repo):
    s = start(timed=False, duration=15)
    sid = s["session_id"]
    move_start_back(repo, sid, hours=3)

    for _ in range(s["total"]):
        assert submit(client, user, sid).status_code == 200
    r = client.post(f"/api/sessions/{sid}/complete", headers=user)

    assert r.status_code == 200
    assert r.json()["answered_count"] == s["total"]


@pytest.mark.parametrize("field,value", [
    ("seconds_left", 99999), ("expires_at", "2099-01-01T00:00:00Z"), ("started_at", "2099-01-01T00:00:00Z"),
])
def test_client_cannot_set_its_own_timer(client, user, field, value):
    r = client.post("/api/sessions", headers=user, json={
        "job_title": "Junior Developer", "difficulty": "Easy", "duration_min": 15,
        "timed": True, field: value,
    })
    assert r.status_code == 422


# --- grading with the AI off -----------------------------------------------------

@pytest.mark.parametrize("timed", [False, True])
def test_answers_are_graded_by_keyword_grader_when_ai_is_off(client, user, start, ai_off, timed):
    s = start(timed=timed)
    assert submit(client, user, s["session_id"]).status_code == 200

    r = client.post(f"/api/sessions/{s['session_id']}/complete", headers=user)

    answered = [a for a in r.json()["answers"] if a["status"] == "answered"]
    assert [a["grader"] for a in answered] == ["keyword"]
