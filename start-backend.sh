#!/bin/bash

# Price Tracker Backend Startup Script

echo "🚀 Starting Price Tracker Backend..."

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Navigate to backend directory
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.py first."
    exit 1
fi

# Activate virtual environment and start server
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

echo "📡 Starting FastAPI server on http://localhost:8000"
echo "📚 API documentation available at http://localhost:8000/docs"
echo "🛑 Press Ctrl+C to stop the server"

python main.py