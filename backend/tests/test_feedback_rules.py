"""S1-5.2 unit tests - feedback rules."""
from app.evaluation.feedback_rules import feedback_for_answer, score_label, session_feedback
from app.evaluation.keyword_evaluator import KeywordEvaluator

ev = KeywordEvaluator()
KW = ["lifo", "push", "pop", "peek", "top"]


def test_strong_answer_names_strengths():
    r = ev.score_answer("A stack is LIFO: push adds to the top, pop removes it, peek reads it.", KW)
    fb = feedback_for_answer(r, "x " * 20)
    assert fb["status"] == "answered" and "Strong answer" in fb["strengths"]


def test_missing_keywords_become_suggestions():
    r = ev.score_answer("It is LIFO with push and pop operations for data.", KW)
    fb = feedback_for_answer(r, "x " * 20)
    assert '"peek"' in fb["improvements"] and '"top"' in fb["improvements"]


def test_blank_answer_note():
    fb = feedback_for_answer(ev.score_answer("", KW))
    assert fb["status"] == "blank" and "skipped" in fb["improvements"]


def test_unanswered_note():
    fb = feedback_for_answer(ev.score_answer("", KW), answered=False)
    assert fb["status"] == "unanswered" and "not answered" in fb["improvements"]


def test_labels():
    assert [score_label(s) for s in (90, 65, 45, 10)] == ["Interview-ready", "Solid", "Developing", "Needs practice"]


def test_session_summary_counts_missed():
    answers = [{"category": "OOP", "status": "answered", "score": 80},
               {"category": "Python", "status": "blank", "score": 0}]
    s = session_feedback(answers, total_questions=5, overall_score=16, correct_count=1)
    assert s["answered_count"] == 1 and s["missed_count"] == 4
    assert "OOP" in s["strengths"] and "Python" in s["improvements"]


def test_no_strongest_area_when_everything_scored_zero():
    answers = [{"category": "OOP", "status": "answered", "score": 0},
               {"category": "Python", "status": "answered", "score": 0}]
    s = session_feedback(answers, total_questions=2, overall_score=0, correct_count=0)
    assert "strongest" not in s["strengths"] and "Review" not in s["improvements"]
