@echo off
REM run_local.bat — start backend + frontend for local demo (Windows)
REM Usage: double-click or run from project root.

setlocal
cd /d "%~dp0\.."

if not exist .venv (
  echo [setup] creating virtual environment...
  python -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt -r requirements-dev.txt -q
) else (
  call .venv\Scripts\activate.bat
)

if not exist .env (
  echo [setup] copying .env.example to .env
  copy .env.example .env >nul
)

echo [seed]  creating dummy demo data (idempotent)...
python -m backend.seed_demo

echo [run]   starting backend on http://localhost:8000 ...
start "portal-backend" cmd /k ".venv\Scripts\activate.bat && uvicorn backend.app:app --reload --port 8000"

cd frontend
if not exist node_modules (
  echo [setup] installing frontend dependencies...
  call npm install
)
echo [run]   starting frontend on http://localhost:5173 ...
start "portal-frontend" cmd /k "npm run dev"

echo.
echo Demo accounts:  teacher@demo.edu / Teacher@12345
echo                 student1@demo.edu / Student@12345
echo Open http://localhost:5173 after both windows settle.
endlocal
