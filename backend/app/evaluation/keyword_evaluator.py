
"""S1-5.1 Rule-based KeywordEvaluator — owner: Prince Nnadi

S2-2.1: also grades rubric criteria (the basic backup grader). A criterion is met when at
least half of its keywords appear in the answer. This is basic on purpose: it cannot catch
wrong sentences or keyword stuffing, which is the AI grader's job (app/evaluation/ai_grader.py).
"""
from dataclasses import dataclass


@dataclass
class AnswerScore:
    matched: list
    missing: list
    score: int          # 0-100
    correct: bool


class KeywordEvaluator:
    def __init__(self, threshold: int = 50):
        self.threshold = threshold

    def score_answer(self, answer: str, expected_keywords: list) -> AnswerScore:
        # Handle blank answer
        if not answer or not answer.strip():
            return AnswerScore(
                matched=[], 
                missing=expected_keywords.copy(), 
                score=0, 
                correct=False
            )

        answer_lower = answer.lower()
        matched = []
        missing = []

        # Normalise text and find which keywords appear
        for keyword in expected_keywords:
            if keyword.lower() in answer_lower:
                matched.append(keyword)
            else:
                missing.append(keyword)

        # Calculate score (matched / total * 100)
        score = 0
        if expected_keywords:
            score = int((len(matched) / len(expected_keywords)) * 100)

        correct = score >= self.threshold

        return AnswerScore(
            matched=matched,
            missing=missing,
            score=score,
            correct=correct
        )

    def overall(self, scores: list) -> dict:
        if not scores:
            return {"average_score": 0, "correct_count": 0}

        # Overall score (average) and running correct count
        total_score = sum(s.score for s in scores)
        average_score = total_score / len(scores)
        correct_count = sum(1 for s in scores if s.correct)

        return {
            "average_score": average_score,
            "correct_count": correct_count
        }

    def criterion_met(self, answer: str, keywords: list) -> tuple[bool, list]:
        """S2-2.1: (met, keywords found) for one rubric criterion.

        Met when at least half of the criterion's keywords appear (case-insensitive).
        A criterion with no keywords can never be met by keyword grading.
        """
        if not answer or not answer.strip() or not keywords:
            return False, []
        answer_lower = answer.lower()
        found = [k for k in keywords if k.lower() in answer_lower]
        return len(found) * 2 >= len(keywords), found
