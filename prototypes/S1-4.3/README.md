# Accessible_Job_Interview_System S1-4.3 

**Supabase + Render configuration**  
US-4 Save Session & Responses · PM / Tools & Infrastructure

## How it works

- Settings like DB host, password and API keys come from the environment, so the same code runs locally and on Render with different values.
- requirements.txt already includes gunicorn, the production server Render uses for Python apps.

## What you build for Sprint 1

- Create the Supabase project connection settings and add them as Render environment variables/secrets.
- Make sure .env is in .gitignore, and write a staging smoke test (app starts, can read one question).
