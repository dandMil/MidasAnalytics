#!/bin/bash

# MidasAnalytics Backend Background Startup Script

echo "🚀 Starting MidasAnalytics Backend in background..."

# Change to the project directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if uvicorn is available
if ! command -v uvicorn &> /dev/null; then
    echo "⚠️  Uvicorn not found. Installing dependencies..."
    pip install -q -r requirements.txt
fi

# Start the server in background
echo "🌟 Starting FastAPI server in background on http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo ""

# Start uvicorn in background
nohup uvicorn app:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# Get the process ID
PID=$!
echo "✅ Backend started with PID: $PID"
echo "📝 Logs are being written to: backend.log"
echo ""
echo "To stop the server, run:"
echo "  kill $PID"
echo ""
echo "Or run: ./stop_backend.sh"
echo ""

# Save PID to a file
echo $PID > backend.pid
