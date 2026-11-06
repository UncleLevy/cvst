#!/usr/bin/env bash
# Start CVST (Django backend + React frontend) on Linux/macOS.
#   ./scripts/start-cvst.sh            start backend and frontend in the background
#   ./scripts/start-cvst.sh celery     also start a Celery worker (needs Redis; see RUN_INSTRUCTIONS.txt)
# Logs go to <repo>/logs, process IDs to <repo>/logs/*.pid. Stop with ./scripts/stop-cvst.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS="$ROOT/logs"
mkdir -p "$LOGS"
cd "$ROOT"

for cmd in python3 node npm; do
  command -v "$cmd" >/dev/null || { echo "Missing '$cmd'. Install it first (see RUN_INSTRUCTIONS.txt)."; exit 1; }
done

# --- Backend setup (first run creates the venv and .env) ---
cd "$ROOT/backend"
[ -d venv ] || python3 -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
if [ ! -f venv/.deps-installed ] || [ requirements.txt -nt venv/.deps-installed ]; then
  pip install -q -r requirements.txt
  touch venv/.deps-installed
fi
[ -f .env ] || { cp .env.example .env; echo "Created backend/.env from .env.example"; }
python manage.py migrate --noinput

# --- Frontend setup ---
cd "$ROOT/frontend"
[ -d node_modules ] || npm install

start_bg() {  # name, workdir, command...
  local name="$1" dir="$2"; shift 2
  if [ -f "$LOGS/$name.pid" ] && kill -0 "$(cat "$LOGS/$name.pid")" 2>/dev/null; then
    echo "$name already running (PID $(cat "$LOGS/$name.pid"))"; return
  fi
  ( cd "$dir" && nohup "$@" >"$LOGS/$name.log" 2>&1 </dev/null & echo $! >"$LOGS/$name.pid" )
  echo "Started $name (PID $(cat "$LOGS/$name.pid")), log: logs/$name.log"
}

start_bg backend  "$ROOT/backend"  "$ROOT/backend/venv/bin/python" manage.py runserver 127.0.0.1:8000
start_bg frontend "$ROOT/frontend" npm run dev -- --host 127.0.0.1
if [ "${1:-}" = "celery" ]; then
  start_bg celery "$ROOT/backend" "$ROOT/backend/venv/bin/celery" -A config worker -l info
fi

echo
echo "CVST is starting:  frontend http://localhost:5173   backend http://localhost:8000"
