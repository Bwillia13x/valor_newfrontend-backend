#!/bin/bash

# Valor IVX - Full Stack Startup Script
# This script starts both the frontend and backend services

set -euo pipefail

echo "🚀 Starting Valor IVX Full Stack Application..."
echo "================================================"

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $1 is already in use"
        return 1
    else
        echo "✅ Port $1 is available"
        return 0
    fi
}

# Load backend environment if present
if [ -f "backend/.env" ]; then
  # Export vars from .env for child processes
  set -a
  # shellcheck disable=SC1091
  source backend/.env
  set +a
fi

# Resolve backend port (PORT > BACKEND_PORT > default 5002)
PORT="${PORT:-${BACKEND_PORT:-5002}}"

# Check if ports are available
echo "Checking port availability..."
check_port 8000 || exit 1
check_port "$PORT" || exit 1

# Function to start backend
start_backend() {
    echo "🔧 Starting Backend Server..."
    cd backend
    
    # Check if Python virtual environment exists
    if [ ! -d "venv" ]; then
        echo "📦 Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Start backend server
    echo "🚀 Starting Flask backend on http://localhost:${PORT}"
    # Ensure PORT is passed to backend
    PORT="$PORT" python run.py &
    BACKEND_PID=$!
    cd ..
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting Frontend Server..."
    echo "🚀 Starting frontend on http://localhost:8000"
    python3 -m http.server 8000 &
    FRONTEND_PID=$!
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "✅ Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "✅ Frontend stopped"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start services
start_backend
sleep 3  # Give backend time to start

start_frontend

echo ""
echo "🎉 Valor IVX is now running!"
echo "================================================"
echo "📊 Frontend: http://localhost:8000"
echo "🔧 Backend API: http://localhost:${PORT}"
echo "🏥 Health Check: http://localhost:${PORT}/api/health"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for user to stop
wait 