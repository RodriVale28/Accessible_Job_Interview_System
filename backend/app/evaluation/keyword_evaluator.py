"""S1-5.1 Rule-based KeywordEvaluator - owner: Prince Nnadi

Deterministic scoring for Sprint 1 (no AI): the same answer always gets the same score.
  score   = matched keywords / expected keywords x 100   (rounded)
  correct = score >= threshold (default 50)
"""
from __future__ import annotations

from typing import Optional

import re
from dataclasses import dataclass, field

DEFAULT_THRESHOLD = 50


@dataclass
class AnswerScore:
    matched: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    score: int = 0          # 0-100
    correct: bool = False
    blank: bool = False


def normalize(text: str) -> str:
    """Lower-case, treat hyphens/underscores/dashes as spaces, collapse whitespace."""
    text = (text or "").lower()
    text = re.sub(r"[‐-―_\-]", " ", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    return re.sub(r"\s+", " ", text).strip()


def keyword_in(answer_norm: str, keyword: str) -> bool:
    """True if keyword appears in the normalized answer as a whole word/phrase.
    Simple plurals count ("pointers" matches "pointer"). Notation like O(log n)
    also matches without spaces ("o(logn)")."""
    kw = normalize(keyword)
    if not kw:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(kw) + r"(?:e?s)?(?![a-z0-9])"
    if re.search(pattern, answer_norm):
        return True
    if re.search(r"[^a-z0-9 ]", kw):  # symbols, e.g. o(n^2), i/o bound
        return kw.replace(" ", "") in answer_norm.replace(" ", "")
    return False


class KeywordEvaluator:
    def __init__(self, threshold: int = DEFAULT_THRESHOLD):
        self.threshold = threshold

    def score_answer(self, answer: str, expected_keywords: list) -> AnswerScore:
        keywords = [k for k in (expected_keywords or []) if k and k.strip()]
        if not answer or not answer.strip():
            return AnswerScore(matched=[], missing=list(keywords), score=0, correct=False, blank=True)
        if not keywords:
            return AnswerScore(matched=[], missing=[], score=0, correct=False)
        norm = normalize(answer)
        matched = [k for k in keywords if keyword_in(norm, k)]
        missing = [k for k in keywords if k not in matched]
        score = round(len(matched) / len(keywords) * 100)
        return AnswerScore(matched=matched, missing=missing, score=score,
                           correct=score >= self.threshold)

    def overall(self, scores: list, total_questions: Optional[int] = None) -> dict:
        """Overall score = average over every planned question (questions never
        answered count as 0), plus the running correct count."""
        total = max(total_questions or len(scores), 1)
        overall = round(sum(s.score for s in scores) / total)
        correct = sum(1 for s in scores if s.correct)
        return {"overall_score": overall, "correct_count": correct}
