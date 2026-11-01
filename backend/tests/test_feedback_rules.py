from dataclasses import dataclass

import pytest

from app.evaluation.feedback_rules import feedback_for_answer, session_feedback


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


def test_three_skipped_questions_feedback():
    scores = [
        FakeScore(["python"], [], 100, True),
        FakeScore([], ["loops"], 0, False),
        FakeScore([], ["functions"], 0, False),
        FakeScore([], ["variables"], 0, False),
    ]

    answers = ["I have experience with Python.", "", "   ", "\n"]

    result = session_feedback(scores, answers)

    skip_message = (
        "You skipped 3 questions, "
        "so those are the ones to work on next."
    )

    assert result["unanswered_count"] == 3
    assert result["overall"] == 25
    assert result["improvements"].count(skip_message) == 1
    assert "skipped" not in result["strengths"].lower()
    assert "No answer was provided." not in result["strengths"]

@dataclass
class FakeGradeResult:
    score: int
    correct: bool
    criteria_met: list
    criteria_missed: list
    evidence: list
    reasons: list
    grader: str


def test_sprint2_criteria_feedback():
    grade = FakeGradeResult(
        score=75,
        correct=False,
        criteria_met=["clear explanation", "relevant example"],
        criteria_missed=["error handling", "testing", "documentation"],
        evidence=["Explained the main concept"],
        reasons=[],
        grader="rules",
    )

    result = feedback_for_answer(grade, "I explained the concept.")

    assert "clear explanation" in result["strengths"]
    assert "relevant example" in result["strengths"]
    assert "error handling" in result["improvements"]
    assert "testing" in result["improvements"]
    assert "documentation" not in result["improvements"]


def test_sprint2_blank_answer_scores_zero():
    grade = FakeGradeResult(
        score=100,
        correct=True,
        criteria_met=["clear explanation"],
        criteria_missed=[],
        evidence=[],
        reasons=[],
        grader="rules",
    )

    result = feedback_for_answer(grade, "")

    assert result["score"] == 0
    assert result["correct"] is False
    assert result["status"] == "blank"
