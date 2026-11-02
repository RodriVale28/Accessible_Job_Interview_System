
"""Tests for S2-2.2 feedback generation — Aisha Aloma."""

from dataclasses import dataclass

import pytest

from app.evaluation.feedback_rules import (
    feedback_for_answer,
    session_feedback,
)


@dataclass
class FakeScore:
    matched: list
    missing: list
    score: int
    correct: bool


@dataclass
class FakeGradeResult:
    score: int
    correct: bool
    criteria_met: list
    criteria_missed: list
    evidence: list
    reasons: list
    grader: str


def test_matched_keywords_become_strength():
    grade = FakeScore(["index", "join"], [], 100, True)
    result = feedback_for_answer(grade, "index join")

    assert "index" in result["strengths"]
    assert "join" in result["strengths"]
    assert result["status"] == "correct"
    assert result["answered"] is True


def test_missing_keywords_become_improvements():
    grade = FakeScore(["index"], ["join"], 50, False)
    result = feedback_for_answer(grade, "index only")

    assert result["improvements"] == "Work on these areas: join."
    assert result["status"] == "partial"


def test_no_matches_is_incorrect():
    grade = FakeScore([], ["index"], 0, False)
    result = feedback_for_answer(grade, "something else")

    assert result["status"] == "incorrect"


@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_blank_answer_uses_required_wording(blank):
    grade = FakeScore([], ["index"], 0, False)
    result = feedback_for_answer(grade, blank)

    expected = "You skipped this one, so it is one to work on."

    assert result["status"] == "blank"
    assert result["answered"] is False
    assert result["score"] == 0
    assert result["strengths"] == expected
    assert result["improvements"] == expected


def test_answer_text_is_required():
    grade = FakeScore(["a"], [], 100, True)
    result = feedback_for_answer(grade, "a")

    assert result["answered"] is True


def test_session_summary_counts_and_overall():
    scores = [
        FakeScore(["a"], [], 100, True),
        FakeScore([], ["b"], 0, False),
        FakeScore(["c"], ["d"], 50, False),
    ]

    result = session_feedback(scores, ["a", "", "c"])

    assert result["overall"] == 50
    assert result["correct_count"] == 1
    assert result["total"] == 3
    assert result["unanswered_count"] == 1
    assert len(result["answers"]) == 3


def test_empty_session():
    result = session_feedback([])

    assert result["overall"] == 0
    assert result["answers"] == []


def test_length_mismatch_raises():
    scores = [FakeScore([], [], 0, False)]

    with pytest.raises(ValueError):
        session_feedback(scores, [])


def test_three_skipped_questions_feedback():
    scores = [
        FakeScore(["python"], [], 100, True),
        FakeScore([], ["loops"], 0, False),
        FakeScore([], ["functions"], 0, False),
        FakeScore([], ["variables"], 0, False),
    ]

    answers = ["I have experience with Python.", "", "   ", "\n"]

    result = session_feedback(scores, answers)

    expected = (
        "You skipped 3 questions, "
        "so those are the ones to work on next."
    )

    assert result["unanswered_count"] == 3
    assert result["overall"] == 25
    assert result["improvements"].count(expected) == 1
    assert "skipped" not in result["strengths"].lower()


def test_one_skipped_question_uses_singular():
    scores = [
        FakeScore(["python"], [], 100, True),
        FakeScore([], ["testing"], 0, False),
    ]

    result = session_feedback(scores, ["I know Python.", ""])

    assert result["unanswered_count"] == 1
    assert "You skipped 1 question," in result["improvements"]
    assert "1 questions" not in result["improvements"]


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

    assert "Explained the main concept" in result["strengths"]
    assert "error handling" in result["improvements"]
    assert "testing" in result["improvements"]
    assert "documentation" not in result["improvements"]


def test_realistic_linked_list_criterion():
    grade = FakeGradeResult(
        score=60,
        correct=False,
        criteria_met=[
            "Explains that a linked list is made of nodes connected by pointers."
        ],
        criteria_missed=[
            "Explains that each node contains data and a pointer to the next node."
        ],
        evidence=[
            "The answer describes nodes connected by pointers."
        ],
        reasons=[],
        grader="rules",
    )

    result = feedback_for_answer(
        grade,
        "A linked list has nodes connected by pointers.",
    )

    assert "nodes connected by pointers" in result["strengths"]
    assert "Work on these areas:" in result["improvements"]
    assert "Try mentioning Explains that" not in result["improvements"]
    assert ".." not in result["strengths"]
    assert ".." not in result["improvements"]


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


def test_sprint2_evidence_takes_priority():
    grade = FakeGradeResult(
        score=90,
        correct=True,
        criteria_met=["Explains the purpose of a linked list."],
        criteria_missed=[],
        evidence=["You described how nodes connect."],
        reasons=[],
        grader="rules",
    )

    result = feedback_for_answer(
        grade,
        "Nodes connect through pointers.",
    )

    assert "You described how nodes connect" in result["strengths"]
    assert "Try mentioning" not in result["strengths"]
    assert ".." not in result["strengths"]
