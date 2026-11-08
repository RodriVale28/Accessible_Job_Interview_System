"""S2-1.2 Interview builder tests: 4 roles x 3 types, no repeats, Mixed split, fallbacks."""
import uuid

import pytest

from app.repository import MemoryRepository
from app.services.question_service import NoQuestionAvailable, next_question

ROLES = [
    {"name": "Software Engineer", "keywords": ["software", "engineer"], "technical_share": 0.7,
     "skills": {"data structures": 0.5, "algorithms": 0.3, "teamwork": 0.2}},
    {"name": "Data Analyst", "keywords": ["data", "analyst"], "technical_share": 0.6,
     "skills": {"sql": 0.5, "statistics": 0.3, "communication": 0.2}},
    {"name": "IT Support", "keywords": ["help desk", "it"], "technical_share": 0.5,
     "skills": {"troubleshooting": 0.5, "networking": 0.3, "communication": 0.2}},
    {"name": "Customer Service", "keywords": ["call center", "agent"], "technical_share": 0.0,
     "skills": {"customer service": 0.6, "communication": 0.4}},
]
TECH_SKILLS = ["sql", "statistics", "troubleshooting", "networking", "data structures", "algorithms"]
BEHAVIORAL_SKILLS = ["communication", "teamwork", "customer service"]


def make_question(n, qtype, difficulty, skill):
    return {
        "category": skill.title(), "difficulty": difficulty, "question_type": qtype,
        "prompt": f"{qtype} question {n} about {skill} ({difficulty})?",
        "expected_keywords": ["alpha", "beta"], "skills": [skill],
        "rubric": [{"text": "Explains the main idea.", "keywords": ["alpha"]}],
    }


def make_questions():
    qs, n = [], 0
    for skill in TECH_SKILLS:
        for difficulty in ("Easy", "Medium", "Hard"):
            for _ in range(2):
                n += 1
                qs.append(make_question(n, "Technical", difficulty, skill))
    for skill in BEHAVIORAL_SKILLS:
        for _ in range(6):
            n += 1
            qs.append(make_question(n, "Behavioral", "Medium", skill))
    return qs


@pytest.fixture
def lib():
    return MemoryRepository(questions=make_questions(), roles=ROLES)


def new_session(repo, role_id=None, interview_type="Technical", duration=45):
    return repo.create_session(str(uuid.uuid4()), "Tester", "Medium", duration,
                               role_id=role_id, interview_type=interview_type)


def run_interview(repo, role_id, interview_type, difficulty="Medium"):
    sid = new_session(repo, role_id, interview_type)
    total = repo.get_total_questions(sid)
    ids = [next_question(sid, difficulty, repo=repo, role_id=role_id,
                         interview_type=interview_type)["id"] for _ in range(total)]
    return sid, ids


@pytest.mark.parametrize("role_id", [1, 2, 3, 4])
@pytest.mark.parametrize("interview_type", ["Technical", "Behavioral", "Mixed"])
def test_full_interview_no_repeats(lib, role_id, interview_type):
    _, ids = run_interview(lib, role_id, interview_type)
    assert len(ids) == 10
    assert len(set(ids)) == len(ids)


@pytest.mark.parametrize("role_id", [1, 2, 3, 4])
def test_mixed_split_within_one(lib, role_id):
    sid, _ = run_interview(lib, role_id, "Mixed")
    technical = lib.count_session_question_types(sid).get("Technical", 0)
    target = ROLES[role_id - 1]["technical_share"] * 10
    assert abs(technical - target) <= 1


def test_mixed_without_role_uses_half(lib):
    sid, _ = run_interview(lib, None, "Mixed")
    technical = lib.count_session_question_types(sid).get("Technical", 0)
    assert abs(technical - 5) <= 1


def test_behavioral_needs_no_role_and_ignores_difficulty(lib):
    sid = new_session(lib, None, "Behavioral")
    q = next_question(sid, "Hard", repo=lib, interview_type="Behavioral")
    assert lib.questions[q["id"]]["question_type"] == "Behavioral"


def test_technical_without_role_is_technical_only(lib):
    sid, ids = run_interview(lib, None, "Technical")
    assert all(lib.questions[i]["question_type"] == "Technical" for i in ids)


def test_missing_skill_falls_back(lib):
    only_sql = [make_question(i, "Technical", "Medium", "sql") for i in range(1, 4)]
    role = {"name": "Net", "keywords": [], "technical_share": 1.0, "skills": {"networking": 1.0}}
    repo = MemoryRepository(questions=only_sql, roles=[role])
    sid = new_session(repo, 1, "Technical", duration=15)
    q = next_question(sid, "Medium", repo=repo, role_id=1, interview_type="Technical")
    assert q["id"] in repo.questions


def test_pool_exhausted_raises(lib):
    tiny = [make_question(i, "Technical", "Medium", "sql") for i in range(1, 3)]
    repo = MemoryRepository(questions=tiny, roles=[])
    sid = new_session(repo, None, "Technical", duration=15)
    next_question(sid, "Medium", repo=repo)
    next_question(sid, "Medium", repo=repo)
    with pytest.raises(NoQuestionAvailable):
        next_question(sid, "Medium", repo=repo)




def test_technical_interview_only_asks_role_skills_with_technical_questions():
    """A skill with only Behavioral questions must never be drawn for a Technical
    interview; the role's skill mix must hold instead of silently falling back."""
    questions, n = [], 0
    for skill in ("sql", "statistics", "networking"):  # networking is not in the role
        for _ in range(12):
            n += 1
            questions.append(make_question(n, "Technical", "Medium", skill))
    for _ in range(6):
        n += 1
        questions.append(make_question(n, "Behavioral", "Medium", "communication"))
    roles = [{"name": "Analyst", "keywords": ["analyst"], "technical_share": 0.6,
              "skills": {"sql": 0.5, "statistics": 0.3, "communication": 0.2}}]
    repo = MemoryRepository(questions=questions, roles=roles)

    assert repo.skills_with_questions("Technical") == {"sql", "statistics", "networking"}
    assert "communication" not in repo.skills_with_questions("Technical")

    role_technical_skills = {"sql", "statistics"}
    for _ in range(20):  # the old bug failed about half of single interviews
        _, ids = run_interview(repo, 1, "Technical")
        for qid in ids:
            assert set(repo.questions[qid]["skills"]) <= role_technical_skills