
"""S2-4.1: Practice API tests - Sublime Mpanda."""

import uuid


def test_get_practice_question(client, user):
    """An authenticated user can request a practice question."""
    response = client.post(
        "/api/practice/question",
        headers=user,
        json={"difficulty": "Easy", "interview_type": "Technical"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data["id"], int)
    assert data["prompt"]
    assert data["category"]
    assert "expected_keywords" not in data
    assert "rubric" not in data


def test_get_specific_practice_question(client, user, repo):
    """A user can retrieve a specific question by ID."""
    question_id = next(
        qid for qid, q in repo.questions.items()
        if q.get("question_type", "Technical") == "Technical"
    )

    response = client.post(
        "/api/practice/question",
        headers=user,
        json={"question_id": question_id},
    )

    assert response.status_code == 200, response.text
    assert response.json()["id"] == question_id


def test_practice_link_opens_a_behavioral_question(client, user, repo):
    """S2-4.2: /practice?question_id=<id> from results sends only the id, so a behavioral id must load."""
    question_id = next(
        qid for qid, q in repo.questions.items() if q.get("question_type") == "Behavioral"
    )

    response = client.post("/api/practice/question", headers=user, json={"question_id": question_id})

    assert response.status_code == 200, response.text
    assert response.json()["id"] == question_id


def test_submit_practice_answer(client, user, repo):
    """A practice answer is graded and saved for its owner."""
    question_id = next(iter(repo.questions))

    response = client.post(
        "/api/practice/answer",
        headers=user,
        json={"question_id": question_id, "text": "A practice answer"},
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["question_id"] == question_id
    assert data["answer"] == "A practice answer"
    assert 0 <= data["score"] <= 100
    assert data["grader"] in ("ai", "keyword")

    assert len(repo.practice_attempts) == 1
    saved = next(iter(repo.practice_attempts.values()))
    assert saved["user_id"] == user["X-User-Id"]
    assert saved["question_id"] == question_id


def test_practice_users_have_separate_attempts(client, user, repo):
    """Practice attempts are associated with the correct user."""
    question_id = next(iter(repo.questions))
    other_user = {"X-User-Id": str(uuid.uuid4())}

    for headers in (user, other_user):
        response = client.post(
            "/api/practice/answer",
            headers=headers,
            json={"question_id": question_id, "text": "Practice response"},
        )
        assert response.status_code == 200, response.text

    saved_users = {
        attempt["user_id"] for attempt in repo.practice_attempts.values()
    }
    assert saved_users == {user["X-User-Id"], other_user["X-User-Id"]}


def test_unknown_practice_question_returns_404(client, user):
    """An unavailable question returns 404."""
    response = client.post(
        "/api/practice/answer",
        headers=user,
        json={"question_id": 999999, "text": "My answer"},
    )
    assert response.status_code == 404


def test_invalid_practice_answer_returns_422(client, user):
    """An invalid question ID is rejected."""
    response = client.post(
        "/api/practice/answer",
        headers=user,
        json={"question_id": -1, "text": "My answer"},
    )
    assert response.status_code == 422


def test_practice_requires_authentication(client, monkeypatch):
    """Both practice endpoints reject unauthenticated users."""
    from app import config

    monkeypatch.setattr(config, "ALLOW_GUEST", False)

    question = client.post("/api/practice/question", json={})
    answer = client.post(
        "/api/practice/answer",
        json={"question_id": 1, "text": "My answer"},
    )

    assert question.status_code == 401
    assert answer.status_code == 401


def test_practice_answer_over_5000_characters_is_rejected(client, user, repo):
    """Same cap as interview answers."""
    qid = next(iter(repo.questions))
    r = client.post("/api/practice/answer", headers=user, json={"question_id": qid, "text": "x" * 5001})
    assert r.status_code == 422
    r = client.post("/api/practice/answer", headers=user, json={"question_id": qid, "text": "x" * 5000})
    assert r.status_code == 200, r.text


def test_whitespace_only_practice_answer_is_a_blank_answer(client, user, repo):
    qid = next(iter(repo.questions))
    r = client.post("/api/practice/answer", headers=user, json={"question_id": qid, "text": "   \n "})
    assert r.status_code == 200, r.text
    assert r.json()["answer"] == "" and r.json()["score"] == 0
