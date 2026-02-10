#!/bin/bash
echo "[INIT] VICKY-GHOST-AGENT v4.0"

# Start Shadow Monitor
echo "[SYSTEM] Activating Shadow Cookie Monitor..."
cd ghost-engine
python3 monitor.py &
MONITOR_PID=$!
cd ..

# Start Backend
echo "[SYSTEM] Launching Engine (Backend)..."
cd ghost-engine
# Check for venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "[SYSTEM] Launching Dashboard (UI)..."
sleep 5
cd ghost-ui
npm run dev &
FRONTEND_PID=$!
cd ..

echo "[READY] Ghost Agent sequence initiated."
echo "[INFO] Access UI at http://localhost:5173"
echo "[WARN] Execute 'Self-Destruct' in Dashboard before exit."

# Trap cleanup
trap "kill $BACKEND_PID $FRONTEND_PID $MONITOR_PID; exit" SIGINT SIGTERM
wait
