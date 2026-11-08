# ==========================================================================
# Interview Studio - Sprint 2, Task S2-1.4: questions, rubrics, roles
# Story: US-2 Receive Interview Questions
# Author: Riket Sanketkumar Patel (GitHub: Riketpatel25)
# This file: validates the question library and roles before seeding. Run: pytest
# ==========================================================================
"""S2-1.4 tests: every question is tagged and has a rubric; role weights add up to 1."""
import re
from collections import Counter

import pytest

from questions_data import QUESTIONS
from roles_data import BEHAVIORAL_SKILLS, ROLES, SKILLS

try:
    from behavioral_data import BEHAVIORAL_QUESTIONS  # S2-3.1, validated once it merges
except ImportError:
    BEHAVIORAL_QUESTIONS = []

ALL_QUESTIONS = list(QUESTIONS) + list(BEHAVIORAL_QUESTIONS)
FIELDS = {"category", "difficulty", "question_type", "prompt", "expected_keywords", "skills", "rubric"}
DIFFICULTIES = {"Easy", "Medium", "Hard"}
SENTENCE = re.compile(r"^[A-Z].*\S.*[.!?]$")


def _ids(questions):
    return [q["prompt"][:60] for q in questions]


# ---- every question (technical and behavioral) -------------------------------
@pytest.mark.parametrize("q", ALL_QUESTIONS, ids=_ids(ALL_QUESTIONS))
def test_question_shape(q):
    assert isinstance(q, dict)
    assert FIELDS <= set(q), f"missing {FIELDS - set(q)}"
    assert q["difficulty"] in DIFFICULTIES
    assert q["question_type"] in {"Technical", "Behavioral"}
    assert q["category"].strip() and q["prompt"].strip()


@pytest.mark.parametrize("q", ALL_QUESTIONS, ids=_ids(ALL_QUESTIONS))
def test_keywords_lowercase_nonempty(q):
    kws = q["expected_keywords"]
    assert kws, "expected_keywords must not be empty (the database requires it)"
    assert all(k == k.lower() and k.strip() == k and k for k in kws)
    assert len(kws) == len(set(kws)), "duplicate keyword"


@pytest.mark.parametrize("q", ALL_QUESTIONS, ids=_ids(ALL_QUESTIONS))
def test_skills_are_known(q):
    assert q["skills"], "every question needs at least one skill"
    unknown = set(q["skills"]) - set(SKILLS)
    assert not unknown, f"unknown skills {unknown}"


@pytest.mark.parametrize("q", ALL_QUESTIONS, ids=_ids(ALL_QUESTIONS))
def test_rubric(q):
    rubric = q["rubric"]
    assert 2 <= len(rubric) <= 4, "rubric needs 2 to 4 criteria"
    texts = [c["text"] for c in rubric]
    assert len(texts) == len(set(texts)), "duplicate criterion"
    for c in rubric:
        assert SENTENCE.match(c["text"]), f"not a full sentence: {c['text']!r}"
        assert c["keywords"], f"criterion has no keywords: {c['text']!r}"
        missing = set(c["keywords"]) - set(q["expected_keywords"])
        assert not missing, f"rubric keywords not in expected_keywords: {missing}"


def test_unique_prompts():
    prompts = [q["prompt"] for q in ALL_QUESTIONS]
    dupes = [p for p, n in Counter(prompts).items() if n > 1]
    assert not dupes, dupes


def test_technical_file_is_technical():
    assert all(q["question_type"] == "Technical" for q in QUESTIONS)


# ---- Sprint 1 library kept, new role questions added --------------------------
def test_sprint1_questions_kept():
    sprint1 = QUESTIONS[:50]
    assert Counter(q["difficulty"] for q in sprint1) == {"Easy": 20, "Medium": 20, "Hard": 10}
    per_category = Counter(q["category"] for q in sprint1)
    assert len(per_category) == 10 and all(n == 5 for n in per_category.values())


@pytest.mark.parametrize("category", ["Data Analysis", "IT Support"])
def test_role_questions(category):
    qs = [q for q in QUESTIONS if q["category"] == category]
    assert len(qs) >= 15
    split = Counter(q["difficulty"] for q in qs)
    assert all(split[d] >= 5 for d in DIFFICULTIES), split


# ---- skills and roles -------------------------------------------------------
def test_skills_unique_lowercase():
    assert len(SKILLS) == len(set(SKILLS))
    assert all(s == s.lower().strip() and s for s in SKILLS)


def test_behavioral_skills_present():
    assert {"communication", "teamwork", "conflict resolution", "customer service",
            "problem solving"} <= set(BEHAVIORAL_SKILLS) <= set(SKILLS)


def test_four_roles():
    assert [r["name"] for r in ROLES] == ["Software Engineer", "Data Analyst", "IT Support", "Customer Service"]


@pytest.mark.parametrize("role", ROLES, ids=[r["name"] for r in ROLES])
def test_role_weights(role):
    assert 0 <= role["technical_share"] <= 1
    assert role["keywords"] and all(k == k.lower() for k in role["keywords"])
    assert set(role["skills"]) <= set(SKILLS)
    assert all(0 < w <= 1 for w in role["skills"].values())
    assert sum(role["skills"].values()) == pytest.approx(1.0)


def test_customer_service_is_behavioral_only():
    cs = next(r for r in ROLES if r["name"] == "Customer Service")
    assert cs["technical_share"] == 0
    assert set(cs["skills"]) <= set(BEHAVIORAL_SKILLS)


@pytest.mark.parametrize("role", [r for r in ROLES if r["technical_share"] > 0], ids=lambda r: r["name"])
def test_role_has_technical_questions(role):
    """Every technical skill a role weights has at least one technical question to pick from."""
    tagged = {s for q in QUESTIONS for s in q["skills"]}
    for skill in set(role["skills"]) - set(BEHAVIORAL_SKILLS):
        assert skill in tagged, f"{role['name']}: no question tagged {skill!r}"


@pytest.mark.parametrize("title,expected", [
    ("Junior Data Analyst", "Data Analyst"),
    ("Help desk technician", "IT Support"),
    ("Call center agent", "Customer Service"),
    ("Software Developer", "Software Engineer"),
    ("Pastry chef", None),
])
def test_role_keywords_match_titles(title, expected):
    from app.services.role_matcher import match_by_keyword

    roles = [{**r, "id": i} for i, r in enumerate(ROLES, start=1)]
    role = match_by_keyword(title, roles)
    assert (role["name"] if role else None) == expected


# ---- seed ------------------------------------------------------------------
def test_seed_is_up_to_date():
    """seed_postgres.sql must be regenerated after any data change: python3 generate_seed.py"""
    import os

    from generate_seed import build

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "seed_postgres.sql")) as f:
        assert f.read() == build()[0], "seed_postgres.sql is stale: run python3 generate_seed.py"
