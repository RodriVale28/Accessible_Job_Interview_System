"""S1-5.1 unit tests - KeywordEvaluator is deterministic."""
from app.evaluation.keyword_evaluator import AnswerScore, KeywordEvaluator

KW = ["sorted", "middle", "half", "o(log n)", "left", "right"]
ev = KeywordEvaluator()


def test_full_match_scores_100():
    r = ev.score_answer("Sorted array, check the middle, go left or right, drop half: O(log n).", KW)
    assert r.score == 100 and r.correct and r.missing == []


def test_partial_match_scores_fraction():
    r = ev.score_answer("You need a sorted list and look at the middle.", KW)
    assert r.matched == ["sorted", "middle"]
    assert r.score == 33 and not r.correct


def test_blank_answer_scores_zero_and_is_flagged():
    r = ev.score_answer("   ", KW)
    assert r.blank and r.score == 0 and r.missing == KW


def test_case_plural_and_notation_variants():
    r = ev.score_answer("Nodes hold POINTERS. Lookup is O(logn).", ["node", "pointer", "o(log n)"])
    assert r.score == 100


def test_whole_words_only():
    # "top" must not match inside "stop", "push" not inside "pushover"
    r = ev.score_answer("stop the pushover", ["top", "push"])
    assert r.score == 0


def test_hyphen_and_space_are_equivalent():
    assert ev.score_answer("a red black tree", ["red-black"]).score == 100


def test_same_input_same_score():
    a = ev.score_answer("middle half sorted", KW)
    b = ev.score_answer("middle half sorted", KW)
    assert a == b


def test_overall_counts_unanswered_as_zero_and_counts_correct():
    scores = [AnswerScore(score=100, correct=True), AnswerScore(score=50, correct=True)]
    assert ev.overall(scores, total_questions=5) == {"overall_score": 30, "correct_count": 2}
