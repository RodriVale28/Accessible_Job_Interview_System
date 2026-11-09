"""S1-5.3 Tests for the results endpoints"""


def answer(client, user, sid, question, text):
    r = client.post(f"/api/sessions/{sid}/answers", headers=user,
                    json={"question_id": question["id"], "text": text})
    assert r.status_code == 200, r.text
    return r.json()


def test_overall_score_counts_unreached_questions_as_zero(client, user, start, repo):
    s = start()  # 5 questions
    keywords = repo.get_question(s["question"]["id"])["expected_keywords"]
    answer(client, user, s["session_id"], s["question"], " ".join(keywords))

    r = client.post(f"/api/sessions/{s['session_id']}/complete", headers=user)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["answers"][0]["score"] == 100
    assert body["overall_score"] == 20  # 100 / 5, not 100 / 2 asked
    assert body["correct_count"] == 1
    assert body["answered_count"] == 1 and body["missed_count"] == 4
    assert [a["status"] for a in body["answers"]] == ["answered", "unanswered"]
    assert body["completed_at"]
    assert repo.get_session(s["session_id"], user["X-User-Id"])["overall_score"] == 20


def test_full_interview_score_and_label(client, user, start, repo):
    s = start()
    sid, q = s["session_id"], s["question"]
    for i in range(5):
        text = "" if i == 2 else " ".join(repo.get_question(q["id"])["expected_keywords"])
        q = answer(client, user, sid, q, text)["question"]

    body = client.post(f"/api/sessions/{sid}/complete", headers=user).json()
    assert body["overall_score"] == 80  # four perfect answers, one skip
    assert body["label"] == "Strong"
    assert body["correct_count"] == 4
    assert [a["status"] for a in body["answers"]].count("blank") == 1
    assert [a["q_index"] for a in body["answers"]] == [1, 2, 3, 4, 5]


def test_results_match_after_completion_and_reload(client, user, start):
    s = start()
    done = client.post(f"/api/sessions/{s['session_id']}/complete", headers=user).json()
    again = client.get(f"/api/sessions/{s['session_id']}/results", headers=user).json()
    assert done == again
    assert again["overall_score"] == 0


def test_results_are_private(client, user, start):
    s = start()
    other = {"X-User-Id": "00000000-0000-4000-8000-000000000001"}
    assert client.get(f"/api/sessions/{s['session_id']}/results", headers=other).status_code == 404
    assert client.post(f"/api/sessions/{s['session_id']}/complete", headers=other).status_code == 404


# ---- S2-2.2 -----------------------------------------------------------------

def test_soft_labels():
    from app.api.results import score_label
    assert [score_label(s) for s in (100, 80, 79, 50, 49, 0)] == [
        "Strong", "Strong", "Getting there", "Getting there", "Room to grow", "Room to grow"]


def test_results_return_role_id_and_timed(client, user, start):
    s = start(timed=True)
    body = client.post(f"/api/sessions/{s['session_id']}/complete", headers=user).json()
    assert body["timed"] is True
    assert body["role_id"] is None


def test_sprint1_answers_fall_back_to_keywords(client, user, start, repo):
    s = start()
    keywords = repo.get_question(s["question"]["id"])["expected_keywords"]
    # A Sprint 1 row: saved straight to the store with only matched / missing (the API now saves criteria).
    repo.save_answer(s["session_id"], s["question"]["id"], keywords[0], False, {
        "score": 25, "correct": False, "matched": [keywords[0]], "missing": keywords[1:],
        "strengths": "", "improvements": ""}, 0)
    first = client.post(f"/api/sessions/{s['session_id']}/complete", headers=user).json()["answers"][0]
    assert first["question_type"] == "Technical"
    assert first["criteria_met"] == first["matched"] == [keywords[0]]
    assert first["criteria_missed"] == first["missing"] == keywords[1:]
    assert first["evidence"] == []


def test_skipped_and_not_reached_are_kept_apart(client, user, start, repo):
    """Q1 answered, Q2 skipped, Q3 on screen when the interview ended, Q4 and Q5 never shown."""
    s = start()
    sid, q = s["session_id"], s["question"]
    q = answer(client, user, sid, q, " ".join(repo.get_question(q["id"])["expected_keywords"]))["question"]
    answer(client, user, sid, q, "")

    body = client.post(f"/api/sessions/{sid}/complete", headers=user).json()

    assert [a["status"] for a in body["answers"]] == ["answered", "blank", "unanswered"]
    assert body["strengths"].startswith("You made good points in 1 answer.")
    assert body["improvements"] == "You skipped 1 question and did not reach 3 more, so those are the ones to work on next."
    assert "skip" not in body["answers"][2]["improvements"].lower()
    assert "ended" in body["answers"][2]["improvements"]


def test_skip_never_appears_in_strengths(client, user, start):
    s = start()
    answer(client, user, s["session_id"], s["question"], "")
    body = client.post(f"/api/sessions/{s['session_id']}/complete", headers=user).json()
    assert "skip" not in body["answers"][0]["strengths"].lower()
    assert "skip" not in body["strengths"].lower()
    assert "You skipped" in body["improvements"]  # the skip lives under improvements only
