#!/bin/bash

# Start both servers for voice chatbot

echo "=========================================="
echo "Starting Voice Chatbot Servers"
echo "=========================================="
echo ""

# Kill any existing servers
echo "Stopping existing servers..."
pkill -f "manage.py runserver"
pkill -f "daphne"
pkill -f "expo start"

sleep 2

# Start Django with Daphne (for WebSocket support)
echo "Starting Django backend with Daphne..."
cd /Users/vinayakmasker/PycharmProjects/voice_chatbot2
source venv/bin/activate
daphne -b 127.0.0.1 -p 8000 voice_chatbot.asgi:application > django.log 2>&1 &
DJANGO_PID=$!
echo "Django PID: $DJANGO_PID"

# Wait for Django to start
sleep 3

# Check if Django started
if curl -s http://localhost:8000/admin/ > /dev/null; then
    echo "✅ Django server started on http://localhost:8000"
else
    echo "❌ Django server failed to start. Check django.log"
    exit 1
fi

# Start Frontend
echo ""
echo "Starting Frontend (Expo)..."
cd frontend
npm start -- --web > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

sleep 5

# Check if Frontend started
if curl -s http://localhost:19006 > /dev/null; then
    echo "✅ Frontend server started on http://localhost:19006"
else
    echo "⚠️  Frontend server may still be starting..."
fi

echo ""
echo "=========================================="
echo "Servers Started!"
echo "=========================================="
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:19006"
echo "WebSocket: ws://localhost:8000/ws/voice-chat/"
echo ""
echo "Logs:"
echo "  Django:   django.log"
echo "  Frontend: frontend.log"
echo ""
echo "To stop servers:"
echo "  pkill -f daphne"
echo "  pkill -f expo"
echo ""

# Keep script running
wait

