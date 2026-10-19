# S1-4.2 · Sublime Mpanda

**Persistence (repository) layer**  
US-4 Save Session & Responses · QA / Tools & Infrastructure

## Files in this folder

- `prototype_code.py` — the prototype code you own, with explanations (reference copy; the app runs from the original files).
- `repository.py` — your Sprint 1 starter. The structure and TODOs are there; you write the implementation.

## Where it is in the prototype

- database.py: the whole file — query() / execute() helpers plus one function per action (create_interview, add_answer, complete_interview, get_transcript…)

## How it works

- Routes never write SQL themselves; they call database.py. This keeps every SQL statement in one place.
- Every read and write is scoped by user_id, so one user can never see another user's interview.
- All queries use %s placeholders (parameterised), which prevents SQL injection.

## What you build for Sprint 1

- Write the FastAPI repository module for PostgreSQL: create_session, save_response, complete_session, get_session_with_responses.
- Catch database errors and raise a clear application error so the API can show a safe message.

## Done when

Testable persistence service used by the session and answer endpoints.

## Explain it in one sentence

> I wrote the layer that saves and loads sessions and answers, scoped to the logged-in user, with safe error handling.

## Workflow

1. Branch: `feature/S1-4.2-persistence_repository_layer`
2. Implement the TODOs in your starter file, add tests, open a pull request.
3. Get one review, make sure CI passes, then merge.
