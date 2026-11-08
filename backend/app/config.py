"""Settings from environment variables.
Locally these come from backend/.env; on Render they are service env vars."""
import os

from dotenv import load_dotenv

load_dotenv()

# Supabase -> Connect -> Session pooler connection string (URI). Leave empty to use
# the in-memory store (local demo / tests only - data is lost on restart).
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

# Comma-separated list of front-end origins allowed to call the API directly.
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

# Seconds of grace after the timer ends before answers are refused (network lag).
TIMER_GRACE_SECONDS = int(os.environ.get("TIMER_GRACE_SECONDS", "30"))

# Supabase project URL (https://<ref>.supabase.co). The API checks login tokens against
# this project's public signing keys, so no secret is needed.
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")

# Local dev, tests and CI only: accept a browser guest id (X-User-Id) instead of a login.
# Never set this on Render.
ALLOW_GUEST = os.environ.get("ALLOW_GUEST", "").strip().lower() in ("1", "true", "yes")

# ---- S2-2.1 AI grading (Gemini Flash-Lite through its OpenAI-compatible endpoint) ----
# AI_ENABLED=0 turns ALL AI off (grading, role matching, feedback); keyword grading is used.
# Nothing is ever called until AI_API_KEY and LLM_MODEL are both set.
AI_ENABLED = os.environ.get("AI_ENABLED", "1").strip().lower() in ("1", "true", "yes")
AI_BASE_URL = os.environ.get(
    "AI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"
).strip().rstrip("/")
# Render env var only. Never in code, never in the browser, never committed.
AI_API_KEY = os.environ.get("AI_API_KEY", "").strip()
# The current Gemini Flash-Lite model name from Google AI Studio. No default: AI stays off until set.
LLM_MODEL = os.environ.get("LLM_MODEL", "").strip()
AI_TIMEOUT_SECONDS = float(os.environ.get("AI_TIMEOUT_SECONDS", "10"))
