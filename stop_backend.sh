#!/bin/bash

# MidasAnalytics Backend Stop Script

echo "🛑 Stopping MidasAnalytics Backend..."

# Change to the project directory
cd "$(dirname "$0")"

# Check if PID file exists
if [ -f "backend.pid" ]; then
    PID=$(cat backend.pid)
    echo "📌 Found PID: $PID"
    
    # Check if process is still running
    if ps -p $PID > /dev/null 2>&1; then
        echo "🔄 Stopping backend process..."
        kill $PID
        sleep 2
        
        # Check if process is still running
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️  Process still running, forcing termination..."
            kill -9 $PID
        fi
        
        echo "✅ Backend stopped successfully"
    else
        echo "⚠️  Process with PID $PID is not running"
    fi
    
    # Remove PID file
    rm -f backend.pid
else
    echo "⚠️  No PID file found"
    
    # Try to find and kill any running uvicorn processes
    echo "🔍 Searching for running uvicorn processes..."
    PIDS=$(ps aux | grep '[u]vicorn app:app' | awk '{print $2}')
    
    if [ -z "$PIDS" ]; then
        echo "❌ No uvicorn processes found"
    else
        echo "Found processes: $PIDS"
        for PID in $PIDS; do
            echo "Killing process: $PID"
            kill $PID
        done
        echo "✅ All uvicorn processes stopped"
    fi
fi

echo ""
echo "🏁 Done"
