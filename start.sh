#!/bin/bash
# Sahayak Voice V2 — Start both Backend (Port 8001) and Frontend (Port 3000)

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "=================================================="
echo "🚀 Starting Sahayak Voice V2"
echo "=================================================="

# 1. Start Backend on port 8001
echo "🔌 [Backend] Starting FastAPI on http://localhost:8001..."
(cd "$DIR/backend" && PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload) &
BACKEND_PID=$!

# 2. Start Frontend on port 3000
echo "💻 [Frontend] Starting Next.js on http://localhost:3000..."
(cd "$DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

# Handle graceful shutdown on Ctrl+C
cleanup() {
    echo ""
    echo "🛑 Shutting down V2 servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

echo ""
echo "✅ Both servers are running!"
echo "👉 Dashboard: http://localhost:3000/dashboard"
echo "👉 Backend API: http://localhost:8001/api/health"
echo "Press Ctrl+C to stop both servers."
echo "=================================================="

wait
