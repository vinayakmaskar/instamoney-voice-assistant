#!/bin/bash

# Quick start script for voice chatbot

echo "=========================================="
echo "Voice Chatbot - Quick Start"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if secrets.json exists
if [ ! -f "secrets.json" ]; then
    echo ""
    echo "⚠️  secrets.json not found!"
    echo "Creating from example..."
    cp secrets.json.example secrets.json
    echo ""
    echo "❌ Please edit secrets.json and add your API keys:"
    echo "   - GEMINI_API_KEY"
    echo "   - SECRET_KEY"
    echo "   - JWT_SECRET_KEY"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check if requirements are installed
if ! python -c "import django" 2>/dev/null; then
    echo "Installing requirements..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Run migrations
echo ""
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Check if Redis is running (optional)
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis is not running (will use InMemoryChannelLayer)"
fi

# Start server
echo ""
echo "=========================================="
echo "Starting Django server..."
echo "Server will be available at http://localhost:8000"
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

python manage.py runserver

