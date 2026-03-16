"""
Configuration management for voice chatbot.
Loads from secrets.json with fallback to environment variables.
"""
import os
import json
from pathlib import Path

# Load secrets from secrets.json
def _load_secrets():
    """Load secrets from secrets.json file. Checks multiple paths for Cloud Run compatibility."""
    search_paths = [
        Path(__file__).resolve().parent.parent / 'secrets.json',
        Path('/secrets/secrets.json'),
    ]
    for secrets_file in search_paths:
        try:
            if secrets_file.exists():
                with open(secrets_file, 'r') as f:
                    return json.load(f)
        except Exception:
            continue
    return {}

SECRETS = _load_secrets()

# Helper function to get config value
def _get_config(key, default=None, env_key=None):
    """Get config value from secrets.json or environment variable."""
    env_key = env_key or key
    return SECRETS.get(key) or os.environ.get(env_key, default)

def _get_django_setting(key, default=None):
    """Safely get Django setting, returns default if Django not configured."""
    try:
        from django.conf import settings
        # Check if Django is configured
        if hasattr(settings, 'SECRET_KEY'):
            return getattr(settings, key, default)
    except:
        pass
    return default

# Gemini API Configuration
GEMINI_API_KEY = _get_config('GEMINI_API_KEY', _get_django_setting('GEMINI_API_KEY', ''))
GEMINI_MODEL = _get_config('GEMINI_MODEL', 'gemini-2.5-flash-native-audio-preview-12-2025')  # Latest model with working function calling

# JWT Configuration
_django_secret = _get_django_setting('SECRET_KEY', '')
JWT_SECRET_KEY = _get_config('JWT_SECRET_KEY', _get_django_setting('JWT_SECRET_KEY', _django_secret))
JWT_ALGORITHM = _get_config('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(_get_config('JWT_EXPIRATION_HOURS', 24))

# Session Configuration
SESSION_TIMEOUT_MINUTES = int(_get_config('SESSION_TIMEOUT_MINUTES', 30))
MAX_CONCURRENT_SESSIONS = int(_get_config('MAX_CONCURRENT_SESSIONS', 5))

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE = int(_get_config('RATE_LIMIT_REQUESTS_PER_MINUTE', 60))

# Audio Configuration
MAX_AUDIO_CHUNK_SIZE = int(_get_config('MAX_AUDIO_CHUNK_SIZE', 1048576))  # 1MB in bytes
SUPPORTED_AUDIO_FORMATS = _get_config('SUPPORTED_AUDIO_FORMATS', ['webm', 'opus', 'wav', 'pcm'])

