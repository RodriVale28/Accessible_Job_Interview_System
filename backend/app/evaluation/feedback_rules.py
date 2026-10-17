"""S1-5.2 Feedback-generation rules - owner: Aisha Aloma

Turns KeywordEvaluator results into plain-language feedback (no AI in Sprint 1).
"""
from __future__ import annotations

from app.evaluation.keyword_evaluator import AnswerScore

SHORT_ANSWER_WORDS = 15


def _join(words: list, limit: int = 4) -> str:
    words = list(words)[:limit]
    if not words:
        return ""
    if len(words) == 1:
        return f'"{words[0]}"'
    return ", ".join(f'"{w}"' for w in words[:-1]) + f' and "{words[-1]}"'


def feedback_for_answer(result: AnswerScore, answer_text: str = "", answered: bool = True) -> dict:
    """Return {"strengths": str, "improvements": str, "status": answered|blank|unanswered}."""
    if not answered:
        return {
            "status": "unanswered",
            "strengths": "",
            "improvements": ("This question was not answered before the interview ended. "
                             f"A strong answer would cover {_join(result.missing)}."),
        }
    if result.blank:
        return {
            "status": "blank",
            "strengths": "",
            "improvements": ("You skipped this question. Next time, try a short answer that covers "
                             f"{_join(result.missing)} - even a partial answer earns points."),
        }

    matched, missing, score = result.matched, result.missing, result.score
    if score >= 80:
        strengths = f"Strong answer - you covered the key ideas, including {_join(matched)}."
    elif score >= 50:
        strengths = f"Good coverage of {_join(matched)}."
    elif matched:
        strengths = f"You touched on {_join(matched)}, which is the right direction."
    else:
        strengths = "You gave an answer, which is a good start."

    if not missing:
        improvements = "Nothing important was missing. Add a short example to make it even stronger."
    elif score >= 50:
        improvements = f"To make it complete, also mention {_join(missing)}."
    elif matched:
        improvements = f"This answer missed several key ideas. Try mentioning {_join(missing)}."
    else:
        improvements = (f"None of the expected key terms appeared. A strong answer would cover "
                        f"{_join(missing)}.")

    if len((answer_text or "").split()) < SHORT_ANSWER_WORDS and missing:
        improvements += " Your answer was short - explain the idea, then give a quick example."

    return {"status": "answered", "strengths": strengths, "improvements": improvements}


def score_label(overall: int) -> str:
    if overall >= 80:
        return "Interview-ready"
    if overall >= 60:
        return "Solid"
    if overall >= 40:
        return "Developing"
    return "Needs practice"


def session_feedback(answers: list, total_questions: int, overall_score: int, correct_count: int) -> dict:
    """Overall summary for the results page (S1-5.3).
    `answers` = list of dicts with keys: category, status, score."""
    answered = [a for a in answers if a["status"] == "answered"]
    missed = total_questions - len(answered)

    by_cat: dict = {}
    for a in answers:
        by_cat.setdefault(a["category"], []).append(a["score"])
    cat_avg = {c: sum(v) / len(v) for c, v in by_cat.items()}

    best = max(cat_avg, key=cat_avg.get) if cat_avg else None
    if answered and best and cat_avg[best] > 0:
        strengths = (f"Your strongest area was {best}. You answered {len(answered)} of "
                     f"{total_questions} questions and {correct_count} met the keyword target.")
    elif answered:
        strengths = (f"You answered {len(answered)} of {total_questions} questions. None hit the key terms "
                     "yet - the terms listed under each answer show what to include.")
    else:
        strengths = "You started an interview - that is the first step. Answer a few questions next time to get feedback."

    tips = []
    worst = min(cat_avg, key=cat_avg.get) if cat_avg else None
    if worst and cat_avg[worst] < cat_avg[best]:
        tips.append(f"Review {worst} - it scored lowest in this session.")
    if missed > 0:
        tips.append(f"{missed} question{'s were' if missed != 1 else ' was'} skipped or not reached. "
                    "Even a short answer earns partial credit.")
    tips.append("Name the key terms explicitly (for example Big-O, data structures, protocols) - "
                "the evaluator looks for them.")

    return {
        "label": score_label(overall_score),
        "strengths": strengths,
        "improvements": " ".join(tips),
        "answered_count": len(answered),
        "missed_count": missed,
    }
