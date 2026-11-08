
"""S2-4.1: Single-question practice API - Sublime Mpanda."""

from types import SimpleNamespace
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import user_id
from app.evaluation.feedback_rules import feedback_for_answer
from app.evaluation.keyword_evaluator import KeywordEvaluator
from app.repository import PersistenceError, get_repo

router = APIRouter()


class PracticeQuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: int | None = Field(default=None, ge=1)
    role_id: int | None = Field(default=None, ge=1)
    skill: str | None = None
    interview_type: Literal["Technical", "Behavioral"] = "Technical"
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"


class PracticeAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: int = Field(ge=1)
    text: str


class PracticeResult(BaseModel):
    question_id: int
    prompt: str
    answer: str
    score: int
    correct: bool
    criteria_met: list[str]
    criteria_missed: list[str]
    evidence: list[str]
    grader: str
    strengths: str
    improvements: str


def _fallback_grade(question: dict, answer_text: str):
    """S2-4.1 stand-in until S2-2.1's evaluate() is merged."""
    evaluator = KeywordEvaluator()
    rubric = question.get("rubric") or []

    if not rubric:
        rubric = [
            {"text": word, "keywords": [word]}
            for word in question.get("expected_keywords", [])
        ]

    met = []
    missed = []

    for criterion in rubric:
        keywords = criterion.get("keywords", [])
        result = evaluator.score_answer(answer_text, keywords)

        if answer_text.strip() and keywords and result.score >= 50:
            met.append(criterion["text"])
        else:
            missed.append(criterion["text"])

    score = int(len(met) / len(rubric) * 100) if rubric else 0

    return SimpleNamespace(
        score=score,
        correct=score >= 50,
        criteria_met=met,
        criteria_missed=missed,
        evidence=[""] * len(met),
        reasons=[],
        grader="keyword",
    )


@router.post("/practice/question")
def practice_question(
    request: PracticeQuestionRequest,
    uid: str = Depends(user_id),
    repo=Depends(get_repo),
):
    """Select one question for individual practice."""
    try:
        if request.question_id is not None:
            question = repo.get_question(request.question_id)

            if question is None:
                raise HTTPException(
                    status_code=404,
                    detail="Practice question not found.",
                )
        elif hasattr(repo, "pick_question_for"):
            skills = [request.skill] if request.skill else None

            if request.role_id is not None:
                role = repo.get_role(request.role_id)
                if role is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Practice role not found.",
                    )
                if skills is None:
                    skills = list(role["skills"])

            question = repo.pick_question_for(
                None,
                request.difficulty,
                skills,
                request.interview_type,
            )
        else:
            # Temporary S2-1.2 fallback: difficulty-only selection.
            # Only return Technical questions until the new builder lands.
            question = None

            if request.interview_type == "Technical":
                for _ in range(20):
                    candidate = repo.pick_unused_question(
                        -1, request.difficulty
                    )
                    if candidate is None:
                        break

                    full = repo.get_question(candidate["id"])
                    if full and full.get("question_type", "Technical") == "Technical":
                        question = candidate
                        break

        if question is None:
            raise HTTPException(
                status_code=404,
                detail="No matching practice question is available.",
            )

        return {
            "id": question["id"],
            "prompt": question["prompt"],
            "category": question["category"],
        }

    except PersistenceError:
        raise HTTPException(
            status_code=503,
            detail="Could not load a practice question. Please try again.",
        )


@router.post("/practice/answer", response_model=PracticeResult)
def practice_answer(
    request: PracticeAnswerRequest,
    uid: str = Depends(user_id),
    repo=Depends(get_repo),
):
    """Grade an individual answer and save the practice attempt."""
    try:
        question = repo.get_question(request.question_id)

        if question is None:
            raise HTTPException(
                status_code=404,
                detail="Practice question not found.",
            )

        question = dict(question)
        question["rubric"] = repo.get_rubric(request.question_id)

        try:
            from app.evaluation.evaluator import evaluate
        except ImportError:
            evaluate = None

        if evaluate is not None:
            grade = evaluate(question, request.text)
        else:
            grade = _fallback_grade(question, request.text)

        feedback = feedback_for_answer(grade, request.text)

        result = PracticeResult(
            question_id=request.question_id,
            prompt=question["prompt"],
            answer=request.text,
            score=grade.score,
            correct=grade.correct,
            criteria_met=grade.criteria_met,
            criteria_missed=grade.criteria_missed,
            evidence=grade.evidence,
            grader=grade.grader,
            strengths=feedback["strengths"],
            improvements=feedback["improvements"],
        )

        repo.save_practice_attempt(
            uid,
            request.question_id,
            request.text,
            result.model_dump(),
        )

        return result

    except PersistenceError:
        raise HTTPException(
            status_code=503,
            detail="Could not save your practice answer. Please try again.",
        )
