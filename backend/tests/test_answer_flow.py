"""Automated tests for the interview answer-submission flow.

Task: S1-3.3
Owner: Hamidat Oloko
User story: US-3 — Answer Interview Questions

Coverage:
- Saving answers to the correct session and question.
- Empty, missing, invalid, and boundary-length answers.
- Next-question progression and interview completion.
- Duplicate, expired, unauthorized, and failed submissions.
"""

from copy import deepcopy
from datetime import timedelta
import uuid

import pytest

from app.repository import AlreadyAnswered, PersistenceError


def submit(client, user, session, text="A stack uses LIFO, push and pop."):
    """Submit an answer to the current question."""
    return client.post(
        f"/api/sessions/{session['session_id']}/answers",
        headers=user,
        json={
            "question_id": session["question"]["id"],
            "text": text,
        },
    )


def snapshot(repo, sid, user):
    """Capture state to check that rejected requests change nothing."""
    return deepcopy(
        (
            repo.get_session(sid, user["X-User-Id"]),
            repo.asked_questions(sid),
            repo.get_responses(sid),
            repo.get_feedback(sid),
        )
    )


def test_answer_saved_to_correct_session_and_question(client, user, start, repo):
    """A submitted answer must belong to the correct session/question."""
    session, other = start(), start()

    response = submit(client, user, session, "  A stack uses LIFO.  ")

    assert response.status_code == 200, response.text
    assert response.json()["saved"] is True

    sid = session["session_id"]
    qid = session["question"]["id"]
    saved = repo.get_responses(sid)

    assert set(saved) == {qid}
    assert saved[qid]["session_id"] == sid
    assert saved[qid]["question_id"] == qid

    # The API should trim surrounding whitespace before saving.
    assert saved[qid]["answer_text"] == "A stack uses LIFO."
    assert saved[qid]["is_blank"] is False

    # Submitting to one interview must not affect another.
    assert repo.get_responses(other["session_id"]) == {}


@pytest.mark.parametrize("text", ["", "   ", "\t\n"])
def test_empty_answer_is_saved_and_flagged(client, user, start, repo, text):
    """Empty and whitespace answers are saved as identifiable blanks."""
    session = start()
    response = submit(client, user, session, text)

    assert response.status_code == 200, response.text

    body = response.json()
    assert body["blank"] is True
    assert body["answered"] == 1
    assert body["q_index"] == 2

    qid = session["question"]["id"]
    saved = repo.get_responses(session["session_id"])[qid]

    assert saved["answer_text"] == ""
    assert saved["is_blank"] is True

    feedback = repo.get_feedback(session["session_id"])[qid]
    assert feedback["score"] == 0
    assert feedback["correct"] is False


def test_missing_text_defaults_to_blank(client, user, start, repo):
    """Omitting text follows the API's default blank-answer behavior."""
    session = start()

    response = client.post(
        f"/api/sessions/{session['session_id']}/answers",
        headers=user,
        json={"question_id": session["question"]["id"]},
    )

    assert response.status_code == 200, response.text
    assert response.json()["blank"] is True

    saved = repo.get_responses(session["session_id"])
    assert saved[session["question"]["id"]]["is_blank"] is True


@pytest.mark.parametrize(
    "text",
    [None, 123, [], {}, "x" * 5001],
    ids=["null", "number", "list", "object", "over-limit"],
)
def test_invalid_text_does_not_save_or_advance(client, user, start, repo, text):
    """Reject invalid text without saving or advancing the interview."""
    session = start()
    before = snapshot(repo, session["session_id"], user)

    response = submit(client, user, session, text)

    assert response.status_code == 422, response.text
    assert snapshot(repo, session["session_id"], user) == before


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"text": "answer"},
        {"question_id": "invalid", "text": "answer"},
        {"question_id": None},
    ],
    ids=[
        "empty-body",
        "missing-question-id",
        "invalid-question-id",
        "null-question-id",
    ],
)
def test_invalid_question_payload_does_not_advance(
    client, user, start, repo, payload
):
    """A missing or invalid question ID must not change session state."""
    session = start()
    before = snapshot(repo, session["session_id"], user)

    response = client.post(
        f"/api/sessions/{session['session_id']}/answers",
        headers=user,
        json=payload,
    )

    assert response.status_code == 422, response.text
    assert snapshot(repo, session["session_id"], user) == before


def test_malformed_json_is_rejected(client, user, start, repo):
    """Invalid JSON should produce a validation error."""
    session = start()
    before = snapshot(repo, session["session_id"], user)

    response = client.post(
        f"/api/sessions/{session['session_id']}/answers",
        headers={**user, "Content-Type": "application/json"},
        content="{",
    )

    assert response.status_code == 422
    assert snapshot(repo, session["session_id"], user) == before


@pytest.mark.parametrize(
    "text",
    ["x" * 5000, "LIFO — café, résumé, 数据结构"],
    ids=["maximum-length", "unicode"],
)
def test_valid_answer_text_is_preserved(client, user, start, repo, text):
    """Accept the length boundary and preserve Unicode text."""
    session = start()
    response = submit(client, user, session, text)

    assert response.status_code == 200, response.text

    saved = repo.get_responses(session["session_id"])
    assert saved[session["question"]["id"]]["answer_text"] == text


@pytest.mark.parametrize("duration,total", [(15, 5), (30, 8), (45, 10)])
def test_progression_reaches_completion_without_repeats(
    client, user, start, repo, duration, total
):
    """Check every question, progress counter, and final completion."""
    session = start(duration=duration)
    sid = session["session_id"]
    seen = set()

    # A bounded loop fails instead of hanging if advancement breaks.
    for answered in range(1, total + 1):
        qid = session["question"]["id"]

        assert qid not in seen
        seen.add(qid)

        response = submit(client, user, session)
        assert response.status_code == 200, response.text

        body = response.json()

        assert body["saved"] is True
        assert body["answered"] == answered
        assert body["total"] == total
        assert len(repo.get_responses(sid)) == answered
        assert body["completed"] is (answered == total)
        assert body["q_index"] == min(answered + 1, total)

        if answered < total:
            # Internal scoring keywords must not be returned to the user.
            assert set(body["question"]) == {"id", "prompt", "category"}

            session = {
                "session_id": sid,
                "question": body["question"],
            }

            # Reloading the session should show the same next question.
            state = client.get(f"/api/sessions/{sid}", headers=user)
            assert state.status_code == 200
            assert state.json()["question"] == body["question"]
        else:
            assert body["question"] is None

    # The client finalizes the session after the final answer.
    done = client.post(f"/api/sessions/{sid}/complete", headers=user)

    assert done.status_code == 200, done.text
    assert done.json()["answered_count"] == total
    assert repo.get_session(sid, user["X-User-Id"])["status"] == "completed"


def test_running_correct_count_and_duplicate_rejection(client, user, start, repo):
    """A correct answer counts once, even if submission is repeated."""
    session = start()

    keywords = repo.get_question(
        session["question"]["id"]
    )["expected_keywords"]

    response = submit(client, user, session, " ".join(keywords))

    assert response.status_code == 200
    assert response.json()["correct_count"] == 1

    before = snapshot(repo, session["session_id"], user)

    assert submit(client, user, session).status_code == 409
    assert snapshot(repo, session["session_id"], user) == before


def test_question_from_another_session_is_rejected(client, user, start, repo):
    """Reject an answer using a different interview's current question."""
    session = start(difficulty="Easy")
    other = start(difficulty="Hard")
    before = snapshot(repo, session["session_id"], user)

    response = client.post(
        f"/api/sessions/{session['session_id']}/answers",
        headers=user,
        json={
            "question_id": other["question"]["id"],
            "text": "answer",
        },
    )

    assert response.status_code == 409, response.text
    assert snapshot(repo, session["session_id"], user) == before
    assert repo.get_responses(other["session_id"]) == {}


def test_unknown_session_returns_404(client, user):
    """Submitting to a nonexistent session should return not found."""
    response = client.post(
        "/api/sessions/999999/answers",
        headers=user,
        json={"question_id": 1, "text": "answer"},
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "headers,status",
    [
        ({}, 401),  # not logged in (was 422 when the guest header was required)
        ({"X-User-Id": "invalid"}, 400),
        ({"X-User-Id": str(uuid.UUID(int=1))}, 404),
    ],
    ids=["missing-user", "invalid-user", "other-user"],
)
def test_unauthorized_answer_does_not_change_state(
    client, user, start, repo, headers, status
):
    """Missing, invalid, and different users cannot submit an answer."""
    session = start()
    before = snapshot(repo, session["session_id"], user)

    assert submit(client, headers, session).status_code == status
    assert snapshot(repo, session["session_id"], user) == before


def test_answer_after_expiration_is_rejected(client, user, start, repo):
    """An expired interview must reject additional answers."""
    session = start()
    sid = session["session_id"]

    # Move the start time back instead of making the test wait.
    repo.sessions[sid]["started_at"] -= timedelta(hours=1)
    before = snapshot(repo, sid, user)

    response = submit(client, user, session)

    assert response.status_code == 409
    assert "Time is up" in response.json()["detail"]
    assert snapshot(repo, sid, user) == before


def test_answer_after_completion_is_rejected(client, user, start, repo):
    """A completed interview must reject additional answers."""
    session = start()
    sid = session["session_id"]

    response = client.post(f"/api/sessions/{sid}/complete", headers=user)
    assert response.status_code == 200

    before = snapshot(repo, sid, user)

    assert submit(client, user, session).status_code == 409
    assert snapshot(repo, sid, user) == before


def test_persistence_failure_returns_503_and_allows_retry(
    client, user, start, repo, monkeypatch
):
    """A failed save leaves state unchanged and allows a later retry."""
    session = start()
    before = snapshot(repo, session["session_id"], user)

    def fail(*args, **kwargs):
        raise PersistenceError("Unable to save answer. Please retry.")

    # Simulate a storage failure only for the first request.
    with monkeypatch.context() as patch:
        patch.setattr(repo, "save_answer", fail)
        response = submit(client, user, session)

    assert response.status_code == 503, response.text
    assert "retry" in response.json()["detail"]
    assert snapshot(repo, session["session_id"], user) == before

    # The retry should save exactly one response.
    assert submit(client, user, session).status_code == 200
    assert len(repo.get_responses(session["session_id"])) == 1


def test_duplicate_storage_error_returns_409(
    client, user, start, repo, monkeypatch
):
    """A duplicate detected by storage becomes a clear conflict error."""
    session = start()
    before = snapshot(repo, session["session_id"], user)

    def duplicate(*args, **kwargs):
        raise AlreadyAnswered()

    monkeypatch.setattr(repo, "save_answer", duplicate)
    response = submit(client, user, session)

    assert response.status_code == 409
    assert "already answered" in response.json()["detail"]
    assert snapshot(repo, session["session_id"], user) == before


def test_blank_answer_remains_identifiable_in_results(client, user, start):
    """Final results must identify a skipped answer and provide feedback."""
    session = start()

    assert submit(client, user, session, "").status_code == 200

    response = client.post(
        f"/api/sessions/{session['session_id']}/complete",
        headers=user,
    )

    assert response.status_code == 200, response.text

    result = next(
        answer
        for answer in response.json()["answers"]
        if answer["question_id"] == session["question"]["id"]
    )

    assert result["status"] == "blank"
    assert result["answer"] == ""
    assert result["score"] == 0
    assert result["improvements"]


def test_no_remaining_question_returns_terminal_answer_response(
    client, user, start, repo
):
    """Keep the saved answer when no next question is available."""
    session = start()
    qid = session["question"]["id"]

    # Simulate other questions becoming unavailable after session start.
    repo.questions = {qid: repo.questions[qid]}

    response = submit(client, user, session)

    assert response.status_code == 200, response.text
    assert response.json()["saved"] is True
    assert response.json()["completed"] is True
    assert response.json()["question"] is None
    assert set(repo.get_responses(session["session_id"])) == {qid}
