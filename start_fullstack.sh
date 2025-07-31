#!/bin/bash
# Valor IVX Full-Stack Startup Script

set -e

echo "🚀 Starting Valor IVX Full-Stack Application..."
echo "=" * 50

# Function to cleanup processes
cleanup() {
    echo "🧹 Cleaning up processes..."
    pkill -f "python.*run.py" 2>/dev/null || true
    pkill -f "python.*http.server" 2>/dev/null || true
    lsof -ti:5002 | xargs kill -9 2>/dev/null || true
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
}

# Set up cleanup on script exit
trap cleanup EXIT

# Clean up any existing processes
cleanup

# Start Backend
echo "🔥 Starting Backend Server..."
cd backend
source venv/bin/activate
nohup python run.py > backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Test backend
echo "🧪 Testing backend..."
if curl -s http://localhost:5002/api/health > /dev/null; then
    echo "✅ Backend is running on http://localhost:5002"
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
echo "=" * 50
echo "📊 Backend API: http://localhost:5002"
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