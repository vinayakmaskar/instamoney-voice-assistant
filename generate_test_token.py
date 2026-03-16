#!/usr/bin/env python
"""
Generate a test JWT token for WebSocket testing.
"""
import sys
import os
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voice_chatbot.settings')
django.setup()

from services.security import create_jwt_token
from django.contrib.auth import get_user_model

User = get_user_model()

# Create or get test user
test_user, created = User.objects.get_or_create(
    username='testuser',
    defaults={
        'email': 'test@example.com',
        'is_active': True
    }
)

if created:
    test_user.set_password('testpass123')
    test_user.save()
    print(f"✅ Created test user: {test_user.username}")

# Generate token
token = create_jwt_token(str(test_user.id))

print("=" * 60)
print("TEST JWT TOKEN GENERATED")
print("=" * 60)
print()
print("Token:")
print(token)
print()
print("=" * 60)
print("Use this token to connect to WebSocket:")
print("=" * 60)
print()
print("In browser console:")
print(f"const token = '{token}';")
print("const ws = new WebSocket('ws://localhost:8000/ws/voice-chat/?stage=basic_details', [token]);")
print()
print("Or copy the token to the test page:")
print("http://localhost:19006")
print()

