#!/usr/bin/env python
"""Quick server status checker."""
import requests
import sys

print("=" * 60)
print("SERVER STATUS CHECK")
print("=" * 60)
print()

# Check Backend
try:
    response = requests.get("http://localhost:8000/admin/", timeout=2)
    print("✅ Backend Server: RUNNING")
    print("   URL: http://localhost:8000")
    print("   WebSocket: ws://localhost:8000/ws/voice-chat/")
    backend_ok = True
except:
    print("❌ Backend Server: NOT RUNNING")
    print("   Start with: python manage.py runserver")
    backend_ok = False

print()

# Check Frontend
try:
    response = requests.get("http://localhost:19006", timeout=2)
    print("✅ Frontend Server: RUNNING")
    print("   URL: http://localhost:19006")
    frontend_ok = True
except:
    print("❌ Frontend Server: NOT RUNNING")
    print("   Start with: cd frontend && npm start -- --web")
    frontend_ok = False

print()
print("=" * 60)

if backend_ok and frontend_ok:
    print("✅ Both servers are running!")
    print()
    print("Test URLs:")
    print("  Frontend: http://localhost:19006")
    print("  Backend:  http://localhost:8000/admin/")
    print()
    print("To test WebSocket, open browser console on frontend and:")
    print("  const ws = new WebSocket('ws://localhost:8000/ws/voice-chat/', [token]);")
    sys.exit(0)
else:
    print("❌ Some servers are not running")
    sys.exit(1)

