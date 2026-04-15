#!/bin/bash
# AMiGA Startup Script

echo "========================================="
echo "  Starting AMiGA Environment  "
echo "========================================="

# Get the directory where the script is located
TARGET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# 1. Start the FastAPI Backend in the background
echo "[1/2] Starting FastAPI Backend on port 8000..."
cd "$TARGET_DIR"
# Activate the virtual environment so fastapi/uvicorn are found
source .venv/bin/activate

# Start backend, capture output for debugging if it fails
python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!
sleep 2 # Give it a second to see if it crashes immediately
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start! Check backend.log for details:"
    cat backend.log
    exit 1
fi
echo "✅ Backend started successfully (PID: $BACKEND_PID)"
echo "[2/2] Starting Vite Frontend on port 5173..."
cd "$TARGET_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo "========================================="
echo "  Servers are running!"
echo "  - Backend Documentation: http://localhost:8000/docs"
echo "  - UI Dashboard:          http://localhost:5173"
echo "  Press Ctrl+C to stop both servers."
echo "========================================="

# Trap Ctrl+C (SIGINT) to gracefully kill both the backend and frontend
trap "echo -e '\nStopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

# Wait indefinitely for the background processes so the script doesn't exit
wait $BACKEND_PID $FRONTEND_PID
