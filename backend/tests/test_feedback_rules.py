
"""Tests for S2-2.2 feedback generation and scoring."""

from dataclasses import dataclass, field

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
    score: int = 0
    correct: bool = False
    criteria_met: list = field(default_factory=list)
    criteria_missed: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    reasons: list = field(default_factory=list)
    grader: str = "rules"


def test_matched_keywords_become_strength():
    grade = FakeScore(["index", "join"], [], 100, True)
    result = feedback_for_answer(grade, "index join")

    assert "index" in result["strengths"]
    assert "join" in result["strengths"]
    assert set(result) == {"strengths", "improvements"}


def test_missing_keywords_become_improvements():
    grade = FakeScore(["index"], ["join"], 50, False)
    result = feedback_for_answer(grade, "index only")

    assert result["improvements"] == "Work on these areas: join."
    assert set(result) == {"strengths", "improvements"}


def test_no_matches_is_incorrect():
    grade = FakeScore([], ["index"], 0, False)
    result = feedback_for_answer(grade, "something else")

    assert "index" in result["improvements"]
    assert "Keep working" in result["strengths"]


@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_blank_answer_uses_required_wording(blank):
    grade = FakeScore([], ["index"], 0, False)
    result = feedback_for_answer(grade, blank)

    expected = "You skipped this one, so it is one to work on."
    assert result["strengths"] == ""
    assert "skip" not in result["strengths"].lower()
    assert result["improvements"] == expected
    assert set(result) == {"strengths", "improvements"}


def test_answer_text_is_required():
    grade = FakeScore(["a"], [], 100, True)

    answered = feedback_for_answer(grade, "a")
    skipped = feedback_for_answer(grade, "")

    assert "a" in answered["strengths"]
    assert "You skipped this one" in skipped["improvements"]


def test_session_summary_counts_and_overall():
    grades = [
        FakeScore(["index"], [], 100, True),
        FakeScore(["join"], ["filter"], 50, False),
    ]

    result = session_feedback(grades, ["index", "join"])

    assert result["overall"] == 75
    assert result["correct_count"] == 1
    assert result["total"] == 2
    assert result["unanswered_count"] == 0
    assert result["answers"][0]["score"] == 100
    assert result["answers"][0]["status"] == "correct"
    assert result["answers"][1]["status"] == "partial"


def test_empty_session():
    result = session_feedback([], [])

    assert result["overall"] == 0
    assert result["correct_count"] == 0
    assert result["total"] == 0
    assert result["answers"] == []


def test_length_mismatch_raises():
    grades = [FakeScore(["a"], [], 100, True)]

    with pytest.raises(ValueError):
        session_feedback(grades, ["a", "b"])


def test_three_skipped_questions_feedback():
    grades = [FakeScore([], ["a"], 0, False) for _ in range(3)]

    result = session_feedback(grades, ["", " ", "\n"])

    assert result["unanswered_count"] == 3
    assert "You skipped 3 questions" in result["improvements"]


def test_one_skipped_question_uses_singular():
    grade = FakeScore([], ["a"], 0, False)

    result = session_feedback([grade], [""])

    assert result["unanswered_count"] == 1
    assert "You skipped 1 question" in result["improvements"]
    assert "1 questions" not in result["improvements"]


def test_sprint2_criteria_feedback():
    grade = FakeGradeResult(
        score=75,
        criteria_met=["Explains the basic concept"],
        criteria_missed=["Provides a real-world example"],
    )

    result = feedback_for_answer(grade, "The concept is explained.")

    assert "Explains the basic concept" in result["strengths"]
    assert "Provides a real-world example" in result["improvements"]
    assert set(result) == {"strengths", "improvements"}


def test_realistic_linked_list_criterion():
    grade = FakeGradeResult(
        score=50,
        criteria_met=[
            "Explains that a linked list consists of connected nodes"
        ],
        criteria_missed=[
            "Explains that a linked list is made of nodes connected by pointers."
        ],
    )

    result = feedback_for_answer(
        grade, "A linked list stores connected nodes."
    )

    assert "Try mentioning Explains that" not in result["improvements"]
    assert ".." not in result["improvements"]
    assert "Work on these areas:" in result["improvements"]


def test_sprint2_blank_answer_scores_zero():
    grade = FakeGradeResult(
        score=100,
        correct=True,
        criteria_met=["clear explanation"],
    )

    result = session_feedback([grade], [""])

    assert result["answers"][0]["score"] == 0
    assert result["answers"][0]["correct"] is False
    assert result["answers"][0]["status"] == "blank"
    assert result["unanswered_count"] == 1


def test_sprint2_evidence_takes_priority():
    grade = FakeGradeResult(
        score=90,
        correct=True,
        criteria_met=["Explains the concept"],
        evidence=["You described how the nodes connect"],
    )

    result = feedback_for_answer(grade, "Nodes connect to each other.")

    assert "You described how the nodes connect" in result["strengths"]


def test_evidence_inside_criteria_met():
    grade = FakeGradeResult(
        score=90,
        correct=True,
        criteria_met=[
            {
                "description": "Explains linked lists",
                "evidence": "The answer identifies nodes and pointers",
            }
        ],
    )

    result = feedback_for_answer(
        grade, "Linked lists use nodes and pointers."
    )

    assert "nodes and pointers" in result["strengths"]


def test_session_feedback_preserves_api_fields():
    grade = FakeScore(["index"], ["join"], 50, False)

    result = session_feedback([grade], ["index"])

    answer = result["answers"][0]

    for key in (
        "score",
        "correct",
        "matched",
        "missing",
        "strengths",
        "improvements",
    ):
        assert key in answer


def test_improvements_capped_at_two_with_a_skip():
    grades = [FakeScore([], [f"point {i}"], 0, False) for i in range(5)]
    answers = ["one", "two", "three", "four", ""]

    result = session_feedback(grades, answers)

    assert result["improvements"].count("You skipped 1 question") == 1
    assert result["improvements"].count("Work on these areas") == 1


def test_improvements_capped_at_two_without_skips():
    grades = [FakeScore([], [f"point {i}"], 0, False) for i in range(4)]

    result = session_feedback(grades, ["one", "two", "three", "four"])

    assert result["improvements"].count("Work on these areas") == 2
