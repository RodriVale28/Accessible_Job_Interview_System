"""US-5 tests - scoring, unanswered handling, persisted results."""


def run_interview(client, user, s, texts):
    sid, q = s["session_id"], s["question"]
    for t in texts:
        if not q:
            break
        q = client.post(f"/api/sessions/{sid}/answers", headers=user,
                        json={"question_id": q["id"], "text": t(q) if callable(t) else t}).json()["question"]
    return client.post(f"/api/sessions/{sid}/complete", headers=user)


def test_full_score_when_all_keywords_given(client, user, start, repo):
    s = start()
    full = lambda q: " ".join(repo.get_question(q["id"])["expected_keywords"])  # noqa: E731
    r = run_interview(client, user, s, [full] * 5)
    body = r.json()
    assert r.status_code == 200
    assert body["overall_score"] == 100 and body["correct_count"] == 5 and body["label"] == "Interview-ready"
    assert all(a["status"] == "answered" and a["missing"] == [] for a in body["answers"])


def test_unanswered_and_blank_are_recognized(client, user, start):
    s = start()
    r = run_interview(client, user, s, ["", "something"])    # 1 blank, 1 answered, 1 shown-not-answered, 2 not reached
    body = r.json()
    statuses = [a["status"] for a in body["answers"]]
    assert statuses == ["blank", "answered", "unanswered"]
    assert body["answered_count"] == 1 and body["missed_count"] == 4 and body["total"] == 5
    assert body["answers"][2]["missing"]          # tells the user what they should have covered


def test_results_are_saved_and_retrievable(client, user, start):
    s = start()
    done = run_interview(client, user, s, ["LIFO push pop"] * 5).json()
    again = client.get(f"/api/sessions/{s['session_id']}/results", headers=user)
    assert again.status_code == 200
    assert again.json()["overall_score"] == done["overall_score"]
    assert again.json()["answers"] == done["answers"]


def test_complete_is_idempotent(client, user, start):
    s = start()
    a = run_interview(client, user, s, ["x"]).json()
    b = client.post(f"/api/sessions/{s['session_id']}/complete", headers=user).json()
    assert a["overall_score"] == b["overall_score"] and a["completed_at"] == b["completed_at"]


def test_results_before_completion_is_409(client, user, start):
    s = start()
    assert client.get(f"/api/sessions/{s['session_id']}/results", headers=user).status_code == 409


def test_retry_starts_new_session(client, user, start):
    s1 = start()
    run_interview(client, user, s1, ["x"] * 5)
    s2 = start()
    assert s2["session_id"] != s1["session_id"] and s2["q_index"] == 1
