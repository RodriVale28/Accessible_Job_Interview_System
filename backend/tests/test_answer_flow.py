"""S1-3.3 Tests for the answer flow - owner: Hamidat Oloko"""
from datetime import timedelta
import uuid


def answer(client, user, sid, qid, text="A stack is LIFO with push and pop."):
    return client.post(f"/api/sessions/{sid}/answers", headers=user, json={"question_id": qid, "text": text})


def test_answer_saved_to_correct_session_and_question(client, user, start, repo):
    s = start()
    r = answer(client, user, s["session_id"], s["question"]["id"])
    assert r.status_code == 200 and r.json()["saved"]
    saved = repo.get_responses(s["session_id"])
    assert list(saved) == [s["question"]["id"]]
    assert saved[s["question"]["id"]]["answer_text"].startswith("A stack")


def test_empty_answer_is_saved_as_blank(client, user, start, repo):
    s = start()
    r = answer(client, user, s["session_id"], s["question"]["id"], text="   ")
    assert r.status_code == 200 and r.json()["blank"] is True
    assert repo.get_responses(s["session_id"])[s["question"]["id"]]["is_blank"] is True


def test_interview_advances_and_completes(client, user, start):
    s = start()
    sid, q, idx = s["session_id"], s["question"], 1
    while True:
        body = answer(client, user, sid, q["id"]).json()
        if body["completed"]:
            break
        idx += 1
        assert body["q_index"] == idx and body["question"]["id"] != q["id"]
        q = body["question"]
    assert body["answered"] == 5 and body["question"] is None


def test_running_correct_count(client, user, start, repo):
    s = start()
    kws = repo.get_question(s["question"]["id"])["expected_keywords"]
    body = answer(client, user, s["session_id"], s["question"]["id"], text=" ".join(kws)).json()
    assert body["correct_count"] == 1


def test_wrong_question_id_rejected(client, user, start):
    s = start()
    r = answer(client, user, s["session_id"], s["question"]["id"] + 999)
    assert r.status_code == 409


def test_same_question_cannot_be_answered_twice(client, user, start):
    s = start()
    answer(client, user, s["session_id"], s["question"]["id"])
    assert answer(client, user, s["session_id"], s["question"]["id"]).status_code == 409


def test_other_users_cannot_see_or_answer(client, start):
    s = start()
    other = {"X-User-Id": str(uuid.uuid4())}
    assert client.get(f"/api/sessions/{s['session_id']}", headers=other).status_code == 404
    assert answer(client, other, s["session_id"], s["question"]["id"]).status_code == 404


def test_missing_or_bad_user_id(client, start):
    s = start()
    assert client.get(f"/api/sessions/{s['session_id']}").status_code == 422
    assert client.get(f"/api/sessions/{s['session_id']}", headers={"X-User-Id": "nope"}).status_code == 400


def test_setup_validation_errors(client, user):
    bad = [
        {"job_title": "", "difficulty": "Easy", "duration_min": 15},
        {"job_title": "Dev", "difficulty": "Expert", "duration_min": 15},
        {"job_title": "Dev", "difficulty": "Easy", "duration_min": 20},
        {"job_title": "Dev", "difficulty": "Easy", "duration_min": 15, "interview_type": "Behavioral"},
    ]
    for body in bad:
        assert client.post("/api/sessions", headers=user, json=body).status_code == 422


def test_answer_after_time_is_up_rejected(client, user, start, repo):
    s = start()
    if hasattr(repo, "sessions"):          # memory store: move the start time back
        repo.sessions[s["session_id"]]["started_at"] -= timedelta(minutes=20)
    else:
        with repo.pool.connection() as c:
            c.execute("UPDATE sessions SET started_at = started_at - interval '20 minutes' WHERE id = %s",
                      (s["session_id"],))
    r = answer(client, user, s["session_id"], s["question"]["id"])
    assert r.status_code == 409 and "Time is up" in r.json()["detail"]


def test_answer_after_completion_rejected(client, user, start):
    s = start()
    client.post(f"/api/sessions/{s['session_id']}/complete", headers=user)
    assert answer(client, user, s["session_id"], s["question"]["id"]).status_code == 409
