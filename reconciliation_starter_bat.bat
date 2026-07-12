@echo off

setlocal

cd /d "%~dp0"
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"



echo.

echo  Bank Reconciliation System

echo  ==========================

echo.



REM Start Frontend

start "Frontend - Next.js" cmd /k "cd /d "%ROOT%\frontend" && npm run dev"



REM Start Backend (pushd changes dir BEFORE start, so the new window inherits the right CWD)

pushd "%ROOT%\backend"
start "Backend - Uvicorn" cmd /k python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
popd



echo  Starting services...

echo  The first frontend compile can take up to a minute on a cold start.

echo  Please wait - the browser will open when the upload page is ready.

echo.



powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\wait-for-frontend.ps1"



echo.

echo  Opening browser...

start "" "http://localhost:3000/upload"



endlocal

