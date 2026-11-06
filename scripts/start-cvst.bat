@echo off
REM Start CVST (Django backend + React frontend) on Windows.
REM   scripts\start-cvst.bat           start backend and frontend
REM   scripts\start-cvst.bat celery    also start a Celery worker (needs Redis; see RUN_INSTRUCTIONS.txt)
REM Stop with scripts\stop-cvst.bat. Safe to run from Task Scheduler.
setlocal
set "ROOT=%~dp0.."
pushd "%ROOT%"
set "ROOT=%CD%"
popd
if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"

where python >nul 2>nul || (echo Python is not installed or not on PATH. See RUN_INSTRUCTIONS.txt & exit /b 1)
where node >nul 2>nul || (echo Node.js is not installed or not on PATH. See RUN_INSTRUCTIONS.txt & exit /b 1)

REM --- Backend setup (first run creates the venv and .env) ---
cd /d "%ROOT%\backend"
if not exist venv (python -m venv venv || exit /b 1)
if not exist venv\.deps-installed (
  venv\Scripts\python -m pip install -q -r requirements.txt || exit /b 1
  echo done> venv\.deps-installed
)
if not exist .env (copy .env.example .env >nul & echo Created backend\.env from .env.example)
venv\Scripts\python manage.py migrate --noinput || exit /b 1

REM --- Frontend setup ---
cd /d "%ROOT%\frontend"
if not exist node_modules (call npm install || exit /b 1)

REM --- Launch (minimised windows; titles are used by stop-cvst.bat) ---
start "CVST Backend" /min cmd /c "cd /d %ROOT%\backend && venv\Scripts\python manage.py runserver 127.0.0.1:8000 >> %ROOT%\logs\backend.log 2>&1"
start "CVST Frontend" /min cmd /c "cd /d %ROOT%\frontend && npm run dev -- --host 127.0.0.1 >> %ROOT%\logs\frontend.log 2>&1"
if /i "%~1"=="celery" (
  start "CVST Celery" /min cmd /c "cd /d %ROOT%\backend && venv\Scripts\celery -A config worker -l info --pool=solo >> %ROOT%\logs\celery.log 2>&1"
)

echo.
echo CVST is starting:  frontend http://localhost:5173   backend http://localhost:8000
endlocal
