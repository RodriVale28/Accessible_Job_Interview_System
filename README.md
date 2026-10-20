# Accessible Job Interview System

CSCE 4901 Capstone, Savage 17. Sprint 1: a technical mock interview on Next.js + FastAPI + Supabase (PostgreSQL) with keyword scoring.

## Layout

```
backend/            FastAPI app (app/), migrations, question library, tests
frontend/           Next.js app (app/, lib/, components/), Playwright e2e
prototypes/         prototype reference code and task notes per task
render.yaml         Render services (S1-4.3)
.github/workflows/  CI (S1-X.1)
```

## Run locally

Backend (from `backend/`):
```
pip install fastapi "uvicorn[standard]" pydantic "psycopg[binary]" python-dotenv pytest httpx
uvicorn app.main:app --reload --port 8000
```

Frontend (from `frontend/`):
```
npm install
npm run dev
```
The frontend forwards `/api/*` to `API_ORIGIN` (default `http://127.0.0.1:8000`). Copy the `.env.example` files to set your own values; never commit `.env`.

## Tasks and files

| Task | Owner | File |
|---|---|---|
| S1-1.1 | Kobra Amiri | `frontend/app/setup/page.tsx` |
| S1-1.2 | Owen Erickson | `backend/app/api/sessions.py` |
| S1-1.3 | Blake Hawkins | `frontend/lib/setupValidation.ts` |
| S1-2.1 | Riket Sanketkumar Patel | `backend/question_library/` |
| S1-2.2 | Moshood Abisoye | `backend/app/services/question_service.py` |
| S1-2.3 | Arvin Barghi | `backend/tests/test_questions_api.py` |
| S1-3.1 | Hongli Pan | `frontend/app/session/[id]/page.tsx` |
| S1-3.2 | Jayme Nguyen | `backend/app/api/answers.py`, `frontend/lib/submitAnswer.ts` |
| S1-3.3 | Hamidat Oloko | `backend/tests/test_answer_flow.py` |
| S1-4.1 | Kieu Le | `backend/migrations/001_init.sql` |
| S1-4.2 | Sublime Mpanda | `backend/app/repository.py` |
| S1-4.3 | Valeria Rodriguez Hernandez | `render.yaml`, `backend/scripts/smoke_test.py` |
| S1-5.1 | Prince Nnadi | `backend/app/evaluation/keyword_evaluator.py` |
| S1-5.2 | Aisha Aloma | `backend/app/evaluation/feedback_rules.py` |
| S1-5.3 | Shegofa Ahmadi | `frontend/app/results/[id]/page.tsx`, `backend/app/api/results.py` |
| S1-5.4 | Christofer Arias | `frontend/e2e/critical-path.spec.ts` |
| S1-X.1 | Thunder Oyebi | `.github/workflows/ci.yml` |

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/sessions` | Start: `{job_title, difficulty, duration_min}` returns session + first question |
| GET | `/api/sessions/{id}` | Current state (question, index, timer, correct count) |
| POST | `/api/sessions/{id}/answers` | `{question_id, text}` saves the answer, returns the next question (empty text = skip) |
| POST | `/api/sessions/{id}/complete` | Finish and score |
| GET | `/api/sessions/{id}/results` | Saved score and feedback |
| GET | `/health` | Health check: `{"ok": true}` |

Users are a browser guest id sent as the `X-User-Id` header (`frontend/lib/user.ts`, `backend/app/api/deps.py`) until login exists.
