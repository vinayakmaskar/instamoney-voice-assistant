#!/usr/bin/env python
"""
Helper script to generate secrets.json with random keys.
"""
import json
import secrets
import string
from pathlib import Path

def generate_secret_key(length=50):
    """Generate a random secret key."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_django_secret_key():
    """Generate Django secret key."""
    try:
        import django
        from django.core.management.utils import get_random_secret_key
        return get_random_secret_key()
    except ImportError:
        # Fallback if Django not installed
        return generate_secret_key(50)

def create_secrets_file():
    """Create secrets.json file with generated values."""
    project_root = Path(__file__).resolve().parent
    secrets_file = project_root / 'secrets.json'
    
    if secrets_file.exists():
        response = input("secrets.json already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    print("Generating secrets...")
    
    django_secret = generate_django_secret_key()
    jwt_secret = generate_secret_key(32)
    
    secrets_data = {
        "GEMINI_API_KEY": "",  # User must fill this
        "SECRET_KEY": django_secret,
        "JWT_SECRET_KEY": jwt_secret,
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRATION_HOURS": 24,
        "SESSION_TIMEOUT_MINUTES": 30,
        "MAX_CONCURRENT_SESSIONS": 5,
        "RATE_LIMIT_REQUESTS_PER_MINUTE": 60,
        "MAX_AUDIO_CHUNK_SIZE": 1048576,
        "SUPPORTED_AUDIO_FORMATS": ["webm", "opus", "wav", "pcm"],
        "GEMINI_MODEL": "gemini-2.0-flash-exp",
        "ALLOWED_HOSTS": ["localhost", "127.0.0.1"],
        "CORS_ALLOWED_ORIGINS": ["http://localhost:3000"],
        "DEBUG": True,
        "REDIS_HOST": "127.0.0.1",
        "REDIS_PORT": 6379
    }
    
    with open(secrets_file, 'w') as f:
        json.dump(secrets_data, f, indent=2)
    
    print(f"✅ Created {secrets_file}")
    print("\n⚠️  IMPORTANT: Add your GEMINI_API_KEY to secrets.json")
    print("   Get it from: https://makersuite.google.com/app/apikey")

if __name__ == '__main__':
    create_secrets_file()

