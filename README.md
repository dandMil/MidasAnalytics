# MidasAnalytics

A comprehensive financial analytics platform with AI-powered trading insights, Reddit sentiment analysis, and technical indicators.

## 🚀 Quick Setup

### 🎯 Easiest Way - Using Start Scripts

```bash
# Start the backend (foreground - see logs)
./start_backend.sh

# OR start in background (detached)
./start_backend_daemon.sh

# Stop the backend
./stop_backend.sh
```

### Option 1: Using Pipenv (Recommended)
```bash
# Run the setup script
./setup.sh

# Activate the environment
pipenv shell

# Start the development server
pipenv run dev
```

### Option 2: Using pip
```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Using Conda
```bash
# Create environment from yml file
conda env create -f environment.yml

# Activate environment
conda activate MidasAnalytics

# Start the server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## 📦 Dependencies

### Core Dependencies
- **FastAPI** - Modern web framework for building APIs
- **Uvicorn** - ASGI server for FastAPI
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **TA** - Technical analysis library
- **OpenAI** - AI/LLM integration
- **PRAW** - Reddit API wrapper
- **Requests** - HTTP library

### Development Dependencies
- **Pytest** - Testing framework
- **Black** - Code formatter
- **Flake8** - Linting
- **Jupyter** - Interactive development

## 🔧 Available Commands (with Pipenv)

```bash
# Development
pipenv run dev          # Start development server with auto-reload
pipenv run start        # Start production server

# Testing & Quality
pipenv run test         # Run tests
pipenv run lint         # Run linting
pipenv run format       # Format code with Black

# Environment
pipenv shell           # Activate virtual environment
pipenv install         # Install dependencies
pipenv install --dev   # Install dev dependencies
```

## 🌐 API Endpoints

- `GET /midas/daily_summary` - Daily market summary
- `GET /midas/asset/top_movers` - Top gaining/losing stocks
- `GET /midas/asset/get_signal/{ticker}/{type}` - Technical analysis
- `GET /midas/asset/shorts_squeeze` - Shorts squeeze analysis
- `GET /midas/asset/volume` - Volume data
- `GET /midas/crypto_summary` - Crypto market data
- `POST /query` - AI-powered financial queries

## 🔑 Environment Variables

Create a `.env` file with:
```
OPENAI_API_KEY=your_openai_api_key
POLYGON_API_KEY=your_polygon_api_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_reddit_user_agent
```
