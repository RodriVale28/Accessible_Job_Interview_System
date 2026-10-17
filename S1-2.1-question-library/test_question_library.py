# ==========================================================================
# Interview Studio - Sprint 1, Task S1-2.1: 50-question technical library + seed script
# Story: US-2 Receive Interview Questions
# Author: Riket Sanketkumar Patel (GitHub: Riketpatel25)
# This file: validates the library (50 rows, Easy 20/Medium 20/Hard 10, 5 per category). Run: pytest
# ==========================================================================
"""S1-2.1 tests: validate the 50-question library before seeding."""
from collections import Counter
from questions_data import QUESTIONS

def test_count():
    assert len(QUESTIONS) == 50

def test_difficulty_split():
    c = Counter(d for _, d, _, _ in QUESTIONS)
    assert c == {"Easy": 20, "Medium": 20, "Hard": 10}

def test_five_per_category():
    c = Counter(cat for cat, _, _, _ in QUESTIONS)
    assert len(c) == 10 and all(n == 5 for n in c.values())

def test_unique_prompts():
    prompts = [p for _, _, p, _ in QUESTIONS]
    assert len(prompts) == len(set(prompts))

def test_keywords_lowercase_nonempty():
    for _, _, p, kws in QUESTIONS:
        assert kws, p
        assert all(k == k.lower() for k in kws), p
