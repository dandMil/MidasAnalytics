#!/bin/bash

# MidasAnalytics Backend Startup Script

echo "🚀 Starting MidasAnalytics Backend..."

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

# Start the server
echo "🌟 Starting FastAPI server on http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 8000
