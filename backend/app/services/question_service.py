"""S1-2.2 Question-selection service - owner: Moshood Abisoye"""
from __future__ import annotations

from typing import Optional

import random

# How many questions each timer length gets (capped by what the library has).
QUESTIONS_PER_DURATION = {15: 5, 30: 8, 45: 10}


class NoQuestionAvailable(Exception):
    pass


def planned_total(repo, difficulty: str, duration_min: int) -> int:
    available = len(repo.list_questions(difficulty))
    if available == 0:
        raise NoQuestionAvailable(f"No {difficulty} questions are in the library yet.")
    return min(QUESTIONS_PER_DURATION[duration_min], available)


def public_question(q: dict) -> dict:
    """Only what the user needs to see - expected_keywords stay on the server."""
    return {"id": q["id"], "prompt": q["prompt"], "category": q["category"]}


def next_question(repo, session: dict, rng: Optional[random.Random] = None) -> dict:
    """Pick and record the next unused question matching the session difficulty.
    Prefers categories not asked yet so the interview covers more topics."""
    rng = rng or random.Random()
    asked = repo.asked_questions(session["id"])
    if len(asked) >= session["total_questions"]:
        raise NoQuestionAvailable("This interview has no more questions.")
    asked_ids = {a["question_id"] for a in asked}
    pool = [q for q in repo.list_questions(session["difficulty"]) if q["id"] not in asked_ids]
    if not pool:
        raise NoQuestionAvailable("No unused questions are left for this difficulty.")
    asked_cats = {q["category"] for q in (repo.get_question(i) for i in asked_ids) if q}
    fresh = [q for q in pool if q["category"] not in asked_cats]
    choice = rng.choice(fresh or pool)
    repo.add_session_question(session["id"], choice["id"], len(asked) + 1)
    return choice


def current_question(repo, session: dict) -> tuple[Optional[dict], int]:
    """(current unanswered question or None, its 1-based index)."""
    asked = repo.asked_questions(session["id"])
    answered = repo.get_responses(session["id"])
    for a in asked:
        if a["question_id"] not in answered:
            return repo.get_question(a["question_id"]), a["q_index"]
    return None, len(asked)
