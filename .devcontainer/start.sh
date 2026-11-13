#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
LOGS=/tmp/interview-studio
mkdir -p "$LOGS"
if ! curl -sf http://127.0.0.1:8000/health > /dev/null; then
  (cd backend && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$LOGS/backend.log" 2>&1 &)
fi
if ! curl -sf http://127.0.0.1:3000/ > /dev/null; then
  (cd frontend && npm run build > "$LOGS/build.log" 2>&1 || { echo "Build failed:"; tail -n 40 "$LOGS/build.log"; exit 1; })
  (cd frontend && nohup npm run start -- --hostname 0.0.0.0 --port 3000 > "$LOGS/frontend.log" 2>&1 &)
fi
for url in http://127.0.0.1:8000/health http://127.0.0.1:3000/; do
  for _ in $(seq 90); do curl -sf "$url" > /dev/null && break; sleep 1; done
  if ! curl -sf "$url" > /dev/null; then echo "ERROR: $url did not start"; tail -n 40 "$LOGS"/*.log; exit 1; fi
done
echo "Interview Studio is running -> PORTS tab -> port 3000."
