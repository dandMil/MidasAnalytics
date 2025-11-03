# 🚀 Quick Start Guide

## Start the Backend Service

### Method 1: Interactive Mode (See Logs)
```bash
./start_backend.sh
```
This will start the server and show all logs in your terminal.
Press `CTRL+C` to stop.

### Method 2: Background Mode (Detached)
```bash
./start_backend_daemon.sh
```
This starts the server in the background. Logs are saved to `backend.log`.

To stop:
```bash
./stop_backend.sh
```

## Verify Server is Running

Open your browser and go to:
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

## Troubleshooting

### Port Already in Use
If port 8000 is already in use:
```bash
# Find what's using the port
lsof -i :8000

# Kill the process (replace PID with actual process ID)
kill -9 PID
```

### Module Not Found Errors
```bash
# Reinstall dependencies
source .venv/bin/activate
pip install -r requirements.txt
```

### Virtual Environment Not Found
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Server Status

Check if server is running:
```bash
curl http://localhost:8000/docs
```

View logs (when running in background):
```bash
tail -f backend.log
```
