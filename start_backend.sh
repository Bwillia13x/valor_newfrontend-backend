#!/bin/bash
# Valor IVX Backend Startup Script

set -e

echo "🚀 Starting Valor IVX Backend Server..."

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "python.*run.py" 2>/dev/null || true
lsof -ti:5002 | xargs kill -9 2>/dev/null || true

# Change to backend directory
cd backend

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Start the backend server
echo "🔥 Starting Flask server on port 5002..."
nohup python run.py > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 5

# Test the server
echo "🧪 Testing backend health..."
if curl -s http://localhost:5002/api/health > /dev/null; then
    echo "✅ Backend is running successfully!"
    echo "📊 API URL: http://localhost:5002"
    echo "📝 Log file: backend/backend.log"
    echo "🆔 Process ID: $BACKEND_PID"
else
    echo "❌ Backend failed to start properly"
    echo "📋 Checking logs..."
    cat backend.log
    exit 1
fi

echo "🎯 Backend startup complete!" 