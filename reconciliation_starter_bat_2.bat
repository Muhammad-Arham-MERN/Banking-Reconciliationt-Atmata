@echo off
cd /d "%~dp0"
set "ROOT=%~dp0"

echo.
echo  Bank Reconciliation System
echo  ==========================
echo.

REM ── Step 1: Ensure dependencies are installed ─────────────────────────────
echo  Checking dependencies...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\setup-dependencies.ps1" -RootDir "%ROOT%"

if %ERRORLEVEL% neq 0 (
    echo.
    echo  ERROR: Dependency setup failed. See messages above.
    pause
    exit /b 1
)

REM ── Step 2: Start services ────────────────────────────────────────────────

start "Backend - Uvicorn" cmd /k "cd /d "%ROOT%backend" && uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"

start "Frontend - Next.js" cmd /k "cd /d "%ROOT%frontend" && npm run dev"

echo.
echo  Starting services...
echo  The first frontend compile can take up to a minute on a cold start.
echo  Please wait - the browser will open when the upload page is ready.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\wait-for-frontend.ps1"

echo  Opening browser...
start "" "http://localhost:3000/upload"
