"""
Unit tests for database operations.
"""
import pytest
from django.test import TestCase
from channels.db import database_sync_to_async
from services.database import create_session, close_session, get_or_create_conversation, save_message


class DatabaseTests(TestCase):
    """Test database operations."""
    
    @pytest.mark.asyncio
    async def test_create_session(self):
        """Test session creation."""
        session_id = await create_session('test_user', 'basic_details')
        self.assertIsNotNone(session_id)
        self.assertIsInstance(session_id, str)
    
    @pytest.mark.asyncio
    async def test_save_message(self):
        """Test message saving."""
        session_id = await create_session('test_user', 'basic_details')
        await save_message('test_user', 'basic_details', session_id, 'user', 'Hello', 'text')
        # Verify message was saved
        conversation = await get_or_create_conversation('test_user', 'basic_details', session_id)
        self.assertEqual(len(conversation.messages), 1)

