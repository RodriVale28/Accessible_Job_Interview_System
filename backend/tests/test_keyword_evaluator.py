"""S1-5.1 Tests for the rule-based KeywordEvaluator"""
import pytest

from app.evaluation.keyword_evaluator import AnswerScore, KeywordEvaluator

KEYWORDS = ["LIFO", "push", "pop", "stack"]


@pytest.fixture
def evaluator():
    return KeywordEvaluator()


@pytest.mark.parametrize("answer", ["", "   ", "\t\n", None])
def test_blank_answer_scores_zero(evaluator, answer):
    result = evaluator.score_answer(answer, KEYWORDS)
    assert result.score == 0
    assert result.correct is False
    assert result.matched == []
    assert result.missing == KEYWORDS


def test_blank_answer_does_not_mutate_keywords(evaluator):
    keywords = list(KEYWORDS)
    evaluator.score_answer("", keywords).missing.append("extra")
    assert keywords == KEYWORDS


def test_some_keywords_matched(evaluator):
    result = evaluator.score_answer("A stack is LIFO.", KEYWORDS)
    assert result.matched == ["LIFO", "stack"]
    assert result.missing == ["push", "pop"]
    assert result.score == 50
    assert result.correct is True  # exactly at the default threshold


def test_below_threshold_is_not_correct(evaluator):
    result = evaluator.score_answer("It is LIFO.", KEYWORDS)
    assert result.score == 25
    assert result.correct is False


def test_all_keywords_matched_case_insensitive(evaluator):
    result = evaluator.score_answer("You PUSH and Pop on a Stack, which is lifo.", KEYWORDS)
    assert result.matched == KEYWORDS
    assert result.missing == []
    assert result.score == 100
    assert result.correct is True


def test_custom_threshold():
    result = KeywordEvaluator(threshold=75).score_answer("A stack is LIFO.", KEYWORDS)
    assert result.score == 50
    assert result.correct is False


def test_overall_averages_and_counts_correct(evaluator):
    scores = [
        AnswerScore([], [], 100, True),
        AnswerScore([], [], 50, True),
        AnswerScore([], [], 0, False),
    ]
    assert evaluator.overall(scores) == {"average_score": 50, "correct_count": 2}


def test_overall_with_no_scores(evaluator):
    assert evaluator.overall([]) == {"average_score": 0, "correct_count": 0}
