# S1-5.1 · Prince Nnadi

**Rule-based KeywordEvaluator**  
US-5 Evaluate Answers + Results · PM / AI

## Files in this folder

- `prototype_code.py` — the prototype code you own, with explanations (reference copy; the app runs from the original files).
- `keyword_evaluator.py` — your Sprint 1 starter. The structure and TODOs are there; you write the implementation.

## Where it is in the prototype

- llm.py: analyze_answer() — the prototype scores with AI (structure, clarity, relevance, completeness, confidence)
- S1-2.1-question-library/questions_data.py: expected_keywords for each question (your input data)

## How it works

- Sprint 1 must not depend on AI to grade, so your evaluator replaces analyze_answer() for scoring.
- Each question already carries the keywords a strong answer should mention.

## What you build for Sprint 1

- Write a deterministic KeywordEvaluator: lower-case and clean the answer, count which expected keywords appear, score = matched ÷ total × 100, mark correct above an agreed threshold.
- Add the overall score (average) and a running correct count for the session.
- Unit-test it with fixed answers so the same input always gives the same score.

## Done when

Deterministic evaluator with unit-testable scoring behavior.

## Explain it in one sentence

> My evaluator scores each answer by checking which expected keywords it mentions, then averages them into the overall score.

## Workflow

1. Branch: `feature/S1-5.1-rule_based_keywordevaluator`
2. Implement the TODOs in your starter file, add tests, open a pull request.
3. Get one review, make sure CI passes, then merge.
