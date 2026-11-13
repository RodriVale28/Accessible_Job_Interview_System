#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
pip install -r backend/requirements.txt
(cd frontend && npm ci)
if [[ ! -f backend/.env ]]; then
  printf 'DATABASE_URL=\nALLOW_GUEST=1\nAI_ENABLED=0\nCORS_ORIGINS=http://localhost:3000\n' > backend/.env
fi
if [[ ! -f frontend/.env.local ]]; then
  printf 'API_ORIGIN=http://127.0.0.1:8000\nNEXT_PUBLIC_SUPABASE_URL=\nNEXT_PUBLIC_SUPABASE_ANON_KEY=\n' > frontend/.env.local
fi
echo "Setup done."
