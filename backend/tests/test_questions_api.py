"""S1-2.3 Tests for question retrieval - owner: Arvin Barghi"""
from app.repository import MemoryRepository, get_repo
from app.main import app


def test_returns_a_question_for_valid_session(start):
    s = start()
    assert s["q_index"] == 1 and s["total"] == 5
    assert s["question"]["prompt"] and s["question"]["id"]


def test_expected_keywords_are_not_exposed(start):
    s = start()
    assert set(s["question"]) == {"id", "prompt", "category"}


def test_filters_by_difficulty(start, repo):
    for _ in range(5):
        s = start(difficulty="Hard")
        assert repo.get_question(s["question"]["id"])["difficulty"] == "Hard"


def test_duration_sets_question_count(start):
    assert start(duration=15)["total"] == 5
    assert start(duration=30)["total"] == 8
    assert start(difficulty="Hard", duration=45)["total"] == 10


def test_never_repeats_within_a_session(client, user, start):
    s = start(difficulty="Hard", duration=45)
    seen = [s["question"]["id"]]
    sid, q = s["session_id"], s["question"]
    while q:
        r = client.post(f"/api/sessions/{sid}/answers", headers=user, json={"question_id": q["id"], "text": "answer"})
        q = r.json()["question"]
        if q:
            seen.append(q["id"])
    assert len(seen) == 10 and len(set(seen)) == 10


def test_get_session_returns_current_question(client, user, start):
    s = start()
    r = client.get(f"/api/sessions/{s['session_id']}", headers=user)
    assert r.status_code == 200 and r.json()["question"]["id"] == s["question"]["id"]


def test_empty_library_returns_error_state(client, user):
    app.dependency_overrides[get_repo] = lambda: MemoryRepository(questions=[])
    r = client.post("/api/sessions", headers=user,
                    json={"job_title": "Dev", "difficulty": "Easy", "duration_min": 15})
    assert r.status_code == 404 and "No Easy questions" in r.json()["detail"]
