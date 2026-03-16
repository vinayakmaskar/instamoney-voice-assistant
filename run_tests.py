#!/usr/bin/env python
"""
Quick test runner for voice chatbot.
Run this after starting Django server.
"""
import asyncio
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voice_chatbot.settings')

import django
django.setup()

from tests.test_manual import test_websocket_connection

if __name__ == '__main__':
    print("=" * 60)
    print("Voice Chatbot Test Runner")
    print("=" * 60)
    print("\nMake sure Django server is running:")
    print("  python manage.py runserver")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        asyncio.run(test_websocket_connection())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

