from dataclasses import dataclass

import pytest

from feedback_rules import feedback_for_answer, session_feedback


@dataclass
class FakeScore:
    matched: list
    missing: list
    score: int
    correct: bool


def test_matched_keywords_become_strength():
    fb = feedback_for_answer(FakeScore(["index", "join"], [], 100, True), "index join")
    assert "index" in fb["strengths"] and "join" in fb["strengths"]
    assert fb["status"] == "correct"
    assert fb["answered"] is True


def test_missing_keywords_become_try_mentioning():
    fb = feedback_for_answer(FakeScore(["index"], ["join"], 50, False), "index only")
    assert fb["improvements"] == "Try mentioning join."
    assert fb["status"] == "partial"


def test_no_matches_is_incorrect():
    fb = feedback_for_answer(FakeScore([], ["index"], 0, False), "something else")
    assert fb["status"] == "incorrect"


@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_blank_answer_gets_missing_answer_note(blank):
    fb = feedback_for_answer(FakeScore([], ["index"], 0, False), blank)
    assert fb["status"] == "blank"
    assert fb["answered"] is False
    assert fb["strengths"] == "No answer was provided."


def test_answer_text_not_passed_still_works():
    fb = feedback_for_answer(FakeScore(["a"], [], 100, True))
    assert fb["answered"] is True


def test_session_summary_counts_and_overall():
    scores = [
        FakeScore(["a"], [], 100, True),
        FakeScore([], ["b"], 0, False),
        FakeScore(["c"], ["d"], 50, False),
    ]
    out = session_feedback(scores, ["a", "", "c"])
    assert out["overall"] == 50
    assert out["correct_count"] == 1
    assert out["total"] == 3
    assert out["unanswered_count"] == 1
    assert len(out["answers"]) == 3


def test_empty_session():
    out = session_feedback([])
    assert out["overall"] == 0
    assert out["answers"] == []


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        session_feedback([FakeScore([], [], 0, False)], [])
