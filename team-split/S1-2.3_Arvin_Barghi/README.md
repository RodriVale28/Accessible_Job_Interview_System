# S1-2.3 · Arvin Barghi

**Tests for question retrieval**  
US-2 Receive Interview Questions · QA / Tools & Infrastructure

## Files in this folder

- `prototype_code.py` — the prototype code you own, with explanations (reference copy; the app runs from the original files).
- `test_questions_api.py` — your Sprint 1 starter. The structure and TODOs are there; you write the implementation.

## Where it is in the prototype

- No automated tests exist in the prototype yet. You are starting the test suite.
- Code under test: Moshood's question endpoint (S1-2.2) and Riket's seeded data (S1-2.1)

## How it works

- Pytest runs Python test functions; FastAPI's TestClient calls the API like a browser would, without a real server.
- A test database (or Supabase test schema) gives every test a known starting point.

## What you build for Sprint 1

- Tests for: a valid question is returned, difficulty filter works, no repeats within a session, empty library returns the error state, and the DB read actually happens.
- Add a small fixture that seeds 3–5 known questions so results are predictable.

## Done when

Pytest + FastAPI TestClient test suite for US-2.

## Explain it in one sentence

> I wrote the automated tests that prove questions come back correctly, never repeat, and fail cleanly when none are left.

## Workflow

1. Branch: `feature/S1-2.3-tests_for_question_retrieval`
2. Implement the TODOs in your starter file, add tests, open a pull request.
3. Get one review, make sure CI passes, then merge.
