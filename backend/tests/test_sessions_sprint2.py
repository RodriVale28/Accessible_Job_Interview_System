"""S2-1.3 Tests: sessions accept role_id, interview_type and an optional timer."""
from datetime import timedelta




def submit(client, user, session, text="A stack uses LIFO, push and pop."):
    return client.post(
        f"/api/sessions/{session['session_id']}/answers", headers=user,
        json={"question_id": session["question"]["id"], "text": text},
    )


def test_old_clients_still_work(start):
    s = start()
    assert s["timed"] is False
    assert s["role_name"] is None
    assert s["interview_type"] == "Technical"


def test_role_and_type_are_saved(start, fake_roles):
    s = start(role_id=2, interview_type="Mixed")
    assert s["role_name"] == "Data Analyst"
    assert s["interview_type"] == "Mixed"


def test_unknown_role_is_422(client, user, fake_roles):
    r = client.post("/api/sessions", headers=user, json={
        "job_title": "Analyst", "difficulty": "Easy", "duration_min": 15, "role_id": 999})
    assert r.status_code == 422
    assert "role" in r.json()["detail"].lower()


def test_bad_interview_type_is_422(client, user):
    r = client.post("/api/sessions", headers=user, json={
        "job_title": "Analyst", "difficulty": "Easy", "duration_min": 15, "interview_type": "Quiz"})
    assert r.status_code == 422


def test_untimed_session_has_no_countdown(start):
    s = start(timed=False)
    assert s["timed"] is False
    assert s["expires_at"] is None
    assert s["seconds_left"] is None


def test_timed_session_has_a_countdown(start):
    s = start(timed=True, duration=15)
    assert s["timed"] is True
    assert s["expires_at"] is not None
    assert 0 < s["seconds_left"] <= 15 * 60


def test_untimed_session_accepts_an_answer_after_45_minutes(client, user, start, repo):
    s = start(timed=False)
    repo.sessions[s["session_id"]]["started_at"] -= timedelta(minutes=45)
    assert submit(client, user, s).status_code == 200


def test_timed_session_still_returns_409_when_time_is_up(client, user, start, repo):
    s = start(timed=True)
    repo.sessions[s["session_id"]]["started_at"] -= timedelta(minutes=45)
    r = submit(client, user, s)
    assert r.status_code == 409
    assert "Time is up" in r.json()["detail"]


def test_reloaded_state_keeps_role_and_timer(client, user, start, fake_roles):
    s = start(timed=False, role_id=3)
    again = client.get(f"/api/sessions/{s['session_id']}", headers=user).json()
    assert again["role_name"] == "IT Support"
    assert again["seconds_left"] is None


def test_history_rows_show_role_and_type(client, user, start, fake_roles):
    start(role_id=4, interview_type="Behavioral")
    row = client.get("/api/sessions", headers=user).json()[0]
    assert row["role_name"] == "Customer Service"
    assert row["interview_type"] == "Behavioral"


def test_behavioral_interview_starts_with_a_behavioral_question(start, repo):
    s = start(interview_type="Behavioral")
    assert repo.questions[s["question"]["id"]]["question_type"] == "Behavioral"


def test_timer_flag_must_be_a_boolean(client, user):
    r = client.post("/api/sessions", headers=user, json={
        "job_title": "Analyst", "difficulty": "Easy", "duration_min": 15, "timed": "maybe"})
    assert r.status_code == 422


def test_start_logged_out_401(client):
    r = client.post("/api/sessions", json={"job_title": "Analyst", "difficulty": "Easy", "duration_min": 15})
    assert r.status_code == 401
