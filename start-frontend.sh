#!/bin/bash

# Price Tracker Frontend Startup Script

echo "🚀 Starting Price Tracker Frontend..."

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ Node modules not found. Please run setup.py first."
    exit 1
fi

echo "🌐 Starting Vite dev server on http://localhost:5173"
echo "🛑 Press Ctrl+C to stop the server"

npm run dev