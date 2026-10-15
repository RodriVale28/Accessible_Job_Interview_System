# Deploying the Sprint 1 build to Render

About 20 minutes. You need: GitHub Desktop, a Supabase account, a Render account (free plans are enough).
This is a **new** repo and **new** Render services; the existing Flask prototype is not touched.

## 1. Database: Supabase (5 min)

1. supabase.com → **New project** → name `interview-studio`, set a database password (save it), region US East.
2. When it is ready, click **Connect** (top of the project page) → **Session pooler** → copy the URI.
   It looks like `postgresql://postgres.abcd:[YOUR-PASSWORD]@aws-0-us-east-2.pooler.supabase.com:5432/postgres`.
   Replace `[YOUR-PASSWORD]` with your password.
   Use the **Session pooler**, not "Direct connection" - Render cannot reach the direct one.
3. You do not need to run any SQL: the API creates the tables and loads the 50 questions the first time it starts.
   (To do it by hand instead: SQL Editor → run `backend/migrations/001_init.sql`, then `002_seed_questions.sql`.)

## 2. Code: GitHub (5 min)

1. GitHub Desktop → *File → Add Local Repository* → choose `Desktop/CSCE 4901/interview-studio-sprint1`
   → **create a repository** → *Create Repository*.
2. Check the changes list: there must be **no** `.env`, `node_modules` or `.venv` (they are in `.gitignore`).
3. Commit "Sprint 1 build" → **Publish repository** (Private is fine) → add teammates as collaborators.

## 3. Hosting: Render (10 min)

1. render.com → **New → Blueprint** → connect GitHub → pick the `interview-studio-sprint1` repo.
2. Render reads `render.yaml` and shows two services. It asks for two values:
   - `DATABASE_URL` → paste the Supabase Session pooler URI from step 1.
   - `API_ORIGIN` → type `https://interview-studio-api.onrender.com` for now.
3. Click **Apply** and wait until both say *Live*.
4. Open the **interview-studio-api** service and copy its URL from the top of the page.
   If it is not exactly `https://interview-studio-api.onrender.com` (Render adds a suffix when a name is taken):
   open **interview-studio-web → Environment**, set `API_ORIGIN` to that URL, **Save, rebuild and deploy**.

## 4. Smoke test

- `https://<api-url>/health` → `{"ok":true,"store":"postgres","database":true}`.
  `"store":"memory"` means `DATABASE_URL` is missing; `"database":false` means the URI or password is wrong.
- Open the **web** URL → run one 15-minute Easy interview to the results page.
- Supabase → Table Editor → `sessions`, `responses`, `feedback` now have rows.

## Before the presentation

Free Render services fall asleep after 15 minutes idle and take about a minute to wake.
**Open the web URL and the `/health` URL 2-3 minutes before you present**, and run one quick interview.

## Updating

Commit and push in GitHub Desktop → Render redeploys both services automatically.
