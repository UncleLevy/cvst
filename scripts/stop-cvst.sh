#!/usr/bin/env bash
# Stop everything started by start-cvst.sh
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for name in frontend backend celery; do
  pidfile="$ROOT/logs/$name.pid"
  [ -f "$pidfile" ] || continue
  pid="$(cat "$pidfile")"
  if kill -0 "$pid" 2>/dev/null; then
    pkill -P "$pid" 2>/dev/null || true   # child processes (npm -> node, runserver reloader)
    kill "$pid" 2>/dev/null || true
    echo "Stopped $name"
  fi
  rm -f "$pidfile"
done
