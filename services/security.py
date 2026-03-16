"""
Security utilities for authentication, rate limiting, and input validation.
"""
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from channels.db import database_sync_to_async
from config.settings import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS, RATE_LIMIT_REQUESTS_PER_MINUTE

User = get_user_model()


@database_sync_to_async
def validate_jwt_token(token: str):
    """
    Validate JWT token and return user if valid.
    
    Args:
        token: JWT token string
    
    Returns:
        User object if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        user_id = payload.get('user_id')
        if not user_id:
            return None
        
        try:
            user = User.objects.get(id=user_id, is_active=True)
            return user
        except User.DoesNotExist:
            return None
    
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def create_jwt_token(user_id: str) -> str:
    """
    Create JWT token for user.
    
    Args:
        user_id: User ID
    
    Returns:
        JWT token string
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def check_rate_limit(user_id: str) -> bool:
    """
    Check if user has exceeded rate limit.
    
    Args:
        user_id: User ID
    
    Returns:
        True if within limit, False if exceeded
    """
    cache_key = f'rate_limit_{user_id}'
    current_count = cache.get(cache_key, 0)
    
    if current_count >= RATE_LIMIT_REQUESTS_PER_MINUTE:
        return False
    
    cache.set(cache_key, current_count + 1, 60)  # 60 seconds
    return True


def sanitize_text(text: str) -> str:
    """
    Sanitize text input to prevent XSS and other attacks.
    
    Args:
        text: Input text
    
    Returns:
        Sanitized text
    """
    import html
    # Escape HTML characters
    text = html.escape(text)
    # Remove null bytes
    text = text.replace('\x00', '')
    # Limit length (prevent DoS)
    max_length = 10000
    if len(text) > max_length:
        text = text[:max_length]
    return text


def validate_audio_format(format_str: str) -> bool:
    """
    Validate audio format.
    
    Args:
        format_str: Audio format string
    
    Returns:
        True if valid, False otherwise
    """
    from config.settings import SUPPORTED_AUDIO_FORMATS
    return format_str.lower() in SUPPORTED_AUDIO_FORMATS


def validate_audio_size(size: int) -> bool:
    """
    Validate audio chunk size.
    
    Args:
        size: Size in bytes
    
    Returns:
        True if valid, False otherwise
    """
    from config.settings import MAX_AUDIO_CHUNK_SIZE
    return size <= MAX_AUDIO_CHUNK_SIZE

