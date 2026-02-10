@echo off
echo [INIT] VICKY-GHOST-AGENT v4.0 System Check...

echo [SYSTEM] Activating Shadow Cookie Monitor...
start cmd /k "cd ghost-engine && python monitor.py"

echo [SYSTEM] Launching Engine (Backend)...
start cmd /k "cd ghost-engine && call .venv\Scripts\activate || echo Skipping Virtual Env && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo [SYSTEM] Launching Dashboard (UI)...
timeout /t 5
start cmd /k "cd ghost-ui && npm run dev"

echo [READY] Ghost Agent sequence initiated.
echo [INFO] Access UI at http://localhost:5173
echo [WARN] Execute 'Self-Destruct' in Dashboard before exit.
