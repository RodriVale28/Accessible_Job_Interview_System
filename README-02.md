# S1-X.1 · Thunder Oyebi

**GitHub Actions CI**  
Cross-cutting engineering · Design & Architecture / Tools & Infrastructure

## Files in this folder

- `prototype_code.py` — the prototype code you own, with explanations (reference copy; the app runs from the original files).
- `ci.yml` — your Sprint 1 starter. The structure and TODOs are there; you write the implementation.

## Where it is in the prototype

- Nothing exists yet. The repo needs a .github/workflows/ folder.
- requirements.txt lists the Python dependencies CI must install

## How it works

- CI runs automatically on every push and pull request, so broken code is caught before it reaches main.

## What you build for Sprint 1

- Workflow 1: set up Python, install requirements, run pytest (Arvin's and Hamidat's tests).
- Workflow 2: set up Node, run Next.js lint, build and tests.
- Make the checks required on pull requests and write a short troubleshooting note.

## Done when

PR/push CI pipeline that blocks obvious broken builds/tests.

## Explain it in one sentence

> I set up CI so every pull request automatically runs our tests and build, and broken code can't be merged.

## Workflow

1. Branch: `feature/S1-X.1-github_actions_ci`
2. Implement the TODOs in your starter file, add tests, open a pull request.
3. Get one review, make sure CI passes, then merge.
