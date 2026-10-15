# Interview Studio - Sprint 1 build

Accessible Job Interview System · Team Savage 17 · UNT CSCE 4901 Capstone

**Stack:** Next.js (front end) · FastAPI (back end) · Supabase PostgreSQL · Render · GitHub Actions

## What this build does (Sprint 1 scope only)

Start → configure a technical interview → one question at a time → type answers →
answers saved → keyword scoring → overall score + feedback per answer → retry or new session.

| Story | Done in this build |
|---|---|
| US-1 Configure | Job title, type fixed to Technical, Easy/Medium/Hard, 15/30/45-min timer (5/8/10 questions), accessible validation |
| US-2 Questions | 50-question technical library in PostgreSQL, filtered by difficulty, no repeats, keywords never sent to the browser |
| US-3 Answer | Text answer, Enter to submit, Skip, progress bar "Question X of N", countdown timer, End now |
| US-4 Save | Sessions, asked questions, responses and feedback stored in Supabase; results reopen after leaving |
| US-5 Score | Rule-based keyword matching, running correct count, overall score, per-answer strengths/improvements, skipped/unanswered flagged |

**Not in this build (later sprints):** login/accounts (Sprint 1 uses a private guest id saved in the
browser), behavioral track, AI/NLP scoring, voice input, pause/resume, live score, history page,
accessibility settings panel (TTS, text size, themes), lesson plans.

## Who owns which file

| Task | Owner | File |
|---|---|---|
| S1-4.1 | Kieu Le | `backend/migrations/001_init.sql` |
| S1-2.1 | Riket Sanketkumar Patel | `backend/app/data/questions_data.py`, `backend/scripts/generate_seed_sql.py`, `backend/migrations/002_seed_questions.sql` |
| S1-4.2 | Sublime Mpanda | `backend/app/repository.py` |
| S1-2.2 | Moshood Abisoye | `backend/app/services/question_service.py` |
| S1-1.2 | Owen Erickson | `backend/app/api/sessions.py` |
| S1-3.2 | Jayme Nguyen | `backend/app/api/answers.py`, `frontend/lib/submitAnswer.ts` |
| S1-5.1 | Prince Nnadi | `backend/app/evaluation/keyword_evaluator.py` |
| S1-5.2 | Aisha Aloma | `backend/app/evaluation/feedback_rules.py` |
| S1-1.1 | Kobra Amiri | `frontend/app/setup/page.tsx` |
| S1-1.3 | Blake Hawkins | `frontend/lib/setupValidation.ts` |
| S1-3.1 | Hongli Pan | `frontend/app/session/[id]/page.tsx` |
| S1-5.3 | Shegofa Ahmadi | `frontend/app/results/[id]/page.tsx`, `backend/app/api/results.py` |
| S1-2.3 | Arvin Barghi | `backend/tests/test_questions_api.py` |
| S1-3.3 | Hamidat Oloko | `backend/tests/test_answer_flow.py` |
| S1-5.4 | Christofer Arias | `frontend/e2e/critical-path.spec.ts` |
| S1-X.1 | Thunder Oyebi | `.github/workflows/ci.yml` |
| S1-4.3 | Valeria Rodriguez Hernandez | `render.yaml`, `DEPLOY.md` |

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/sessions` | Start: `{job_title, difficulty, duration_min}` → session + first question |
| GET | `/api/sessions/{id}` | Current state (question, index, timer, correct count) |
| POST | `/api/sessions/{id}/answers` | `{question_id, text}` → saved, next question (empty text = skip) |
| POST | `/api/sessions/{id}/complete` | Finish and score (idempotent) |
| GET | `/api/sessions/{id}/results` | Saved score and feedback |
| GET | `/health` | Render health check: `{"ok":true,"store":"postgres","database":true}` |

Every request sends `X-User-Id` (the browser's guest id); a user only ever sees their own sessions.
Interactive docs: `http://localhost:8000/docs`.

## Run it locally

**Back end** (Python 3.9+):
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # paste your Supabase URL, or leave DATABASE_URL empty for in-memory
pytest                      # unit + API tests
uvicorn app.main:app --reload --port 8000
```
On startup the API creates the tables and loads the 50 questions automatically (safe to repeat).

**Front end** (Node 20.9+):
```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev                 # http://localhost:3000
npm run lint && npm run build
npm run test:e2e            # needs both servers running
```

## Test results at hand-off

- Backend: 65 tests pass against both the in-memory store and real PostgreSQL 16; coverage 94% (QA target > 70%).
- Front end: lint clean, production build passes.
- Playwright: 3 end-to-end tests pass (critical path, setup validation, empty answer / end early).

Deploying: see [DEPLOY.md](DEPLOY.md).
