#!/usr/bin/env bash
# run_local.sh — start backend + frontend for local demo (macOS/Linux)
set -e
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "[setup] creating virtual environment..."
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt -r requirements-dev.txt -q
else
  source .venv/bin/activate
fi

if [ ! -f .env ]; then
  echo "[setup] copying .env.example to .env"
  cp .env.example .env
fi

echo "[seed]  creating dummy demo data (idempotent)..."
python -m backend.seed_demo

echo "[run]   starting backend on http://localhost:8000 ..."
uvicorn backend.app:app --reload --port 8000 &
BACK_PID=$!

cd frontend
if [ ! -d node_modules ]; then
  echo "[setup] installing frontend dependencies..."
  npm install
fi
echo "[run]   starting frontend on http://localhost:5173 ..."
npm run dev &
FRONT_PID=$!

trap 'kill $BACK_PID $FRONT_PID 2>/dev/null' EXIT
echo
echo "Demo accounts:  teacher@demo.edu / Teacher@12345"
echo "                student1@demo.edu / Student@12345"
echo "Open http://localhost:5173 — Ctrl+C stops both."
wait
