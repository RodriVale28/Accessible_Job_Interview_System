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
        # TODO: normalise text, find which keywords appear, score = matched / total * 100
        # TODO: blank answer -> score 0, all keywords missing
        raise NotImplementedError

    def overall(self, scores: list) -> dict:
        # TODO: overall score (average) and running correct count
        raise NotImplementedError
