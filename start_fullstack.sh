#!/bin/bash
# Valor IVX Full-Stack Startup Script

set -euo pipefail

echo "🚀 Starting Valor IVX Full-Stack Application..."
echo "================================================"

# Function to cleanup processes
cleanup() {
    echo "🧹 Cleaning up processes..."
    pkill -f "python.*run.py" 2>/dev/null || true
    pkill -f "python.*http.server" 2>/dev/null || true
    # Best-effort kill on known ports (will refine after PORT is resolved)
    lsof -ti:5002 | xargs kill -9 2>/dev/null || true
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
}

# Set up cleanup on script exit
trap cleanup EXIT

# Load backend environment if present
if [ -f "backend/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source backend/.env
  set +a
fi

# Resolve backend port (PORT > BACKEND_PORT > default 5002)
PORT="${PORT:-${BACKEND_PORT:-5002}}"

# Clean up any existing processes
cleanup

# Start Backend
echo "🔥 Starting Backend Server..."
cd backend
source venv/bin/activate
nohup PORT="$PORT" python run.py > backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Test backend
echo "🧪 Testing backend..."
if curl -s "http://localhost:${PORT}/api/health" > /dev/null; then
    echo "✅ Backend is running on http://localhost:${PORT}"
else
    echo "❌ Backend failed to start"
    cat backend/backend.log
    exit 1
fi

# Start Frontend
echo "🌐 Starting Frontend Server..."
nohup python3 -m http.server 8000 > frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 3

# Test frontend
echo "🧪 Testing frontend..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Frontend is running on http://localhost:8000"
else
    echo "❌ Frontend failed to start"
    cat frontend.log
    exit 1
fi

echo ""
echo "🎉 Valor IVX Full-Stack Application Started Successfully!"
echo "================================================"
echo "📊 Backend API: http://localhost:${PORT}"
echo "🌐 Frontend: http://localhost:8000"
echo "📝 Backend Logs: backend/backend.log"
echo "📝 Frontend Logs: frontend.log"
echo "🆔 Backend PID: $BACKEND_PID"
echo "🆔 Frontend PID: $FRONTEND_PID"
echo ""
echo "🔧 To stop the application, press Ctrl+C"
echo ""

# Keep the script running
wait 