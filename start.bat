@echo off

REM Start Frontend
start cmd /k "cd /d D:\Agentic_AI\Bank Reconciliation System\frontend && npm run dev"

REM Start Backend
start cmd /k "cd /d D:\Agentic_AI\Bank Reconciliation System\backend && python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for services to start
timeout /t 5 /nobreak > nul

REM Open Browser
start http://localhost:3000/upload