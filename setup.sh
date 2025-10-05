#!/bin/bash

echo "🚀 Setting up MidasAnalytics project..."

# Check if pipenv is installed
if ! command -v pipenv &> /dev/null; then
    echo "📦 Installing pipenv..."
    pip install pipenv
fi

# Check if Python 3.10 is available
if ! python3.10 --version &> /dev/null; then
    echo "⚠️  Python 3.10 not found. Please install Python 3.10 first."
    echo "   You can use pyenv or download from python.org"
    exit 1
fi

echo "🐍 Creating virtual environment with Python 3.10..."
pipenv install --python 3.10

echo "📚 Installing all dependencies..."
pipenv install

echo "🔧 Installing development dependencies..."
pipenv install --dev

echo "✅ Setup complete!"
echo ""
echo "To activate the environment, run:"
echo "  pipenv shell"
echo ""
echo "To start the development server, run:"
echo "  pipenv run dev"
echo ""
echo "To run tests:"
echo "  pipenv run test"
echo ""
echo "To format code:"
echo "  pipenv run format"
