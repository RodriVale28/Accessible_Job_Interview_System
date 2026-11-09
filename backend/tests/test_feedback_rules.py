
"""Tests for S2-2.2 feedback generation and scoring."""

from dataclasses import dataclass, field

import pytest

from app.evaluation.feedback_rules import (
    _advice,
    feedback_for_answer,
    next_step_line,
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

    assert result["improvements"] == "Points to add: join."
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
    assert result["improvements"] == "Provide a real-world example."
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

    assert result["improvements"] == "Mention that a linked list is made of nodes connected by pointers."
    assert "Explains" not in result["improvements"]


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
    assert result["improvements"].count("Points to add") == 1


def test_improvements_capped_at_two_without_skips():
    grades = [FakeScore([], [f"point {i}"], 0, False) for i in range(4)]

    result = session_feedback(grades, ["one", "two", "three", "four"])

    assert result["improvements"].count("Points to add") == 2


def test_behavioral_strengths_name_star_parts_without_repeating_the_answer():
    grade = FakeGradeResult(
        score=100,
        correct=True,
        criteria_met=["Situation: Describes the problem.", "Task: Explains the goal.",
                      "Action: Describes the steps.", "Result: Explains the outcome."],
        evidence=["I listened, then walked them through each charge", "walked them through each charge"],
    )

    result = feedback_for_answer(grade, "I listened, then walked them through each charge.")

    assert result["strengths"] == "Your answer covered the Situation, Task, Action and Result."


def test_evidence_inside_a_longer_quote_is_not_repeated():
    grade = FakeGradeResult(score=90, correct=True, criteria_met=["Explains linked lists"],
                            evidence=["nodes and pointers link items", "nodes and pointers"])

    result = feedback_for_answer(grade, "Nodes and pointers link items.")

    assert result["strengths"].count("nodes and pointers") == 1


def test_missing_star_parts_are_named_not_quoted():
    grade = FakeGradeResult(
        score=50,
        correct=False,
        criteria_met=["Situation: Sets the scene", "Action: Says what they did"],
        criteria_missed=["Task: Names their goal", "Result: Explains how it ended"],
    )

    result = feedback_for_answer(grade, "We had a deadline, so I split the work.")

    assert result["improvements"] == "Add the Task and Result parts of STAR to your answer."


def test_session_strengths_is_a_short_summary_not_a_quote():
    grades = [FakeGradeResult(score=100, correct=True, criteria_met=["Explains a"], evidence=["I said a"]),
              FakeGradeResult(score=100, correct=True, criteria_met=["Explains b"], evidence=["I said b"])]

    result = session_feedback(grades, ["I said a", "I said b"])

    assert result["strengths"].startswith("You made good points in 2 answers.")
    assert "I said" not in result["strengths"]
    assert "Your answer" not in result["strengths"]


def test_rubric_wording_becomes_advice():
    grade = FakeGradeResult(
        score=0,
        criteria_missed=["Explains that a cache keeps hot data close.", "Names the main trade-offs",
                         "Identifies the bottleneck", "Explains checking the logs"],
    )

    result = feedback_for_answer(grade, "something")

    assert result["improvements"] == "Mention that a cache keeps hot data close. Name the main trade-offs."
    assert _advice("Identifies the bottleneck") == "Identify the bottleneck"
    assert _advice("Explains checking the logs") == "Explain checking the logs"
    assert _advice("join") == "join"


def test_not_reached_is_not_a_skip():
    grades = [FakeScore([], ["a"], 0, False) for _ in range(3)]

    result = session_feedback(grades, ["one", "", None], not_started=2)

    assert [a["status"] for a in result["answers"]] == ["incorrect", "blank", "not_reached"]
    assert result["unanswered_count"] == 1
    assert result["not_reached_count"] == 3
    assert "skip" not in result["answers"][2]["improvements"].lower()
    assert result["improvements"].endswith(
        "You skipped 1 question and did not reach 3 more, so those are the ones to work on next.")


def test_next_step_line_wording():
    assert next_step_line(0, 1) == "1 question was not reached before the interview ended, so that is the one to work on next."
    assert next_step_line(0, 2) == "2 questions were not reached before the interview ended, so those are the ones to work on next."
    assert next_step_line(1, 0) == "You skipped 1 question, so that is the one to work on next."
