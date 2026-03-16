"""
Unit tests for security utilities.
"""
import pytest
from django.test import TestCase
from services.security import sanitize_text, validate_audio_format, validate_audio_size, create_jwt_token, validate_jwt_token


class SecurityTests(TestCase):
    """Test security utilities."""
    
    def test_sanitize_text(self):
        """Test text sanitization."""
        # Test HTML escaping
        text = "<script>alert('xss')</script>"
        sanitized = sanitize_text(text)
        self.assertNotIn('<script>', sanitized)
        
        # Test null byte removal
        text = "Hello\x00World"
        sanitized = sanitize_text(text)
        self.assertNotIn('\x00', sanitized)
    
    def test_validate_audio_format(self):
        """Test audio format validation."""
        self.assertTrue(validate_audio_format('webm'))
        self.assertTrue(validate_audio_format('opus'))
        self.assertFalse(validate_audio_format('invalid'))
    
    def test_validate_audio_size(self):
        """Test audio size validation."""
        # Valid size (1MB)
        self.assertTrue(validate_audio_size(1048576))
        # Invalid size (2MB)
        self.assertFalse(validate_audio_size(2097152))

