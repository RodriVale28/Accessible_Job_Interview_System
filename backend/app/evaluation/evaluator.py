"""S2-2.1 AI evaluator - owner: Prince Nnadi

One interface, two graders:
- AI grader (app/evaluation/ai_grader.py): marks a criterion met only if the answer states
  it correctly, with an exact quote from the answer as evidence.
- Keyword grader (basic backup): a criterion is met when at least half its keywords appear.
  Used when the AI is off, has no key or model, times out, is rate limited, or replies badly.

evaluate(question, answer_text) -> GradeResult
  question = {id, prompt, question_type, expected_keywords, rubric: [{text, keywords}]}
  blank answer -> score 0, nothing met, no AI call
  no rubric yet -> one criterion per expected keyword (Sprint 1 questions still grade)
"""
from __future__ import annotations

from dataclasses import dataclass

from app.evaluation import ai_grader
from app.evaluation.keyword_evaluator import KeywordEvaluator

_keywords = KeywordEvaluator()


@dataclass
class GradeResult:
    score: int                    # 0-100 = criteria met / total criteria
    correct: bool                 # score >= 50
    criteria_met: list[str]       # criterion texts
    criteria_missed: list[str]
    evidence: list[str]           # exact quote from the answer for each criteria_met item, same order
    reasons: list[str]            # one short reason per criterion
    grader: str                   # 'ai' or 'keyword'


def criteria_for(question: dict) -> list[dict]:
    """The question's rubric [{text, keywords}], or one criterion per expected keyword."""
    rubric = [c for c in (question.get("rubric") or []) if c.get("text")]
    if rubric:
        return [{"text": c["text"], "keywords": list(c.get("keywords") or [])} for c in rubric]
    return [{"text": k, "keywords": [k]} for k in (question.get("expected_keywords") or [])]


def _result(criteria: list[dict], met_flags: list[bool], evidence_by_criterion: list[str],
            reasons: list[str], grader: str) -> GradeResult:
    met = [c["text"] for c, m in zip(criteria, met_flags) if m]
    missed = [c["text"] for c, m in zip(criteria, met_flags) if not m]
    evidence = [e for e, m in zip(evidence_by_criterion, met_flags) if m]
    score = int(len(met) / len(criteria) * 100) if criteria else 0
    return GradeResult(score=score, correct=score >= 50, criteria_met=met, criteria_missed=missed,
                       evidence=evidence, reasons=reasons, grader=grader)


def _keyword_grade(criteria: list[dict], answer_text: str) -> GradeResult:
    flags, reasons = [], []
    for c in criteria:
        met, found = _keywords.criterion_met(answer_text, c["keywords"])
        flags.append(met)
        total = len(c["keywords"])
        reasons.append(f"Basic grading found {len(found)} of {total} key terms." if total
                       else "Basic grading could not check this point.")
    return _result(criteria, flags, [""] * len(criteria), reasons, "keyword")


def evaluate(question: dict, answer_text: str) -> GradeResult:
    """Grade one answer against the question's rubric. Never raises because of the AI."""
    criteria = criteria_for(question)
    text = (answer_text or "").strip()
    if not text:
        return _result(criteria, [False] * len(criteria), [""] * len(criteria),
                       ["No answer was given."] * len(criteria), "keyword")

    verdicts = ai_grader.grade(question, [c["text"] for c in criteria], text)
    if verdicts is None:
        return _keyword_grade(criteria, text)
    return _result(criteria, [v.met for v in verdicts], [v.quote for v in verdicts],
                   [v.reason for v in verdicts], "ai")
