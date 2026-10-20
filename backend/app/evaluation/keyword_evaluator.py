
"""S1-5.1 Rule-based KeywordEvaluator — owner: Prince Nnadi"""
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

