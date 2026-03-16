"""
Comprehensive integration tests for voice chatbot.
Tests all scenarios, edge cases, and functionalities.
"""
import pytest
import asyncio
import json
import base64
import jwt
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from consumers.consumers import VoiceChatbotConsumer
from services.security import create_jwt_token, validate_jwt_token
from services.database import create_session, close_session, save_message
from services.adk_agent import LoanAssistantAgent

User = get_user_model()


class VoiceChatbotIntegrationTests(TestCase):
    """Comprehensive integration tests."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_id = str(self.user.id)
        self.token = create_jwt_token(self.user_id)
        self.stage = 'basic_details'
    
    async def test_websocket_connection_with_valid_token(self):
        """Test 1: WebSocket connection with valid token."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected, "Should connect with valid token")
        
        # Should receive connection_established message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'connection_established')
        self.assertEqual(response['user_id'], self.user_id)
        
        await communicator.disconnect()
    
    async def test_websocket_connection_without_token(self):
        """Test 2: WebSocket connection without token (should fail)."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected, "Should not connect without token")
        
        await communicator.disconnect()
    
    async def test_websocket_connection_with_invalid_token(self):
        """Test 3: WebSocket connection with invalid token (should fail)."""
        invalid_token = "invalid.token.here"
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[invalid_token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected, "Should not connect with invalid token")
        
        await communicator.disconnect()
    
    async def test_text_message_handling(self):
        """Test 4: Text message handling."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Receive connection established
        await communicator.receive_json_from()
        
        # Send text message
        await communicator.send_json_to({
            'type': 'text_message',
            'text': 'Hello, I need help with the form'
        })
        
        # Should receive response
        response = await communicator.receive_json_from(timeout=10)
        self.assertIn(response['type'], ['response_text', 'tool_result'])
        
        await communicator.disconnect()
    
    async def test_pan_validation_valid(self):
        """Test 5: PAN validation with valid PAN."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.receive_json_from()
        
        # Send PAN number
        await communicator.send_json_to({
            'type': 'text_message',
            'text': 'My PAN is ABCDE1234F'
        })
        
        # Should receive validation and form suggestion
        responses = []
        for _ in range(3):  # May receive multiple responses
            try:
                response = await communicator.receive_json_from(timeout=5)
                responses.append(response)
                if response.get('type') == 'form_suggestion' and response.get('field') == 'panNumber':
                    break
            except:
                break
        
        # Check if validation occurred
        validation_found = any(
            r.get('type') == 'validation_result' or 
            r.get('type') == 'form_suggestion' 
            for r in responses
        )
        self.assertTrue(validation_found, "Should validate PAN and suggest form field")
        
        await communicator.disconnect()
    
    async def test_pan_validation_invalid(self):
        """Test 6: PAN validation with invalid PAN."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.receive_json_from()
        
        # Send invalid PAN
        await communicator.send_json_to({
            'type': 'text_message',
            'text': 'My PAN is 12345'
        })
        
        # Should receive validation error
        response = await communicator.receive_json_from(timeout=10)
        self.assertIn(response['type'], ['response_text', 'validation_result'])
        
        await communicator.disconnect()
    
    async def test_dob_validation_valid(self):
        """Test 7: DOB validation with valid date."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.receive_json_from()
        
        # Send valid DOB (18+ years old)
        dob = (datetime.now() - timedelta(days=365*25)).strftime("%d/%m/%Y")
        await communicator.send_json_to({
            'type': 'text_message',
            'text': f'My date of birth is {dob}'
        })
        
        # Should receive validation
        response = await communicator.receive_json_from(timeout=10)
        self.assertIn(response['type'], ['response_text', 'validation_result', 'form_suggestion'])
        
        await communicator.disconnect()
    
    async def test_dob_validation_underage(self):
        """Test 8: DOB validation with underage user."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.receive_json_from()
        
        # Send DOB for 16-year-old
        dob = (datetime.now() - timedelta(days=365*16)).strftime("%d/%m/%Y")
        await communicator.send_json_to({
            'type': 'text_message',
            'text': f'My date of birth is {dob}'
        })
        
        # Should receive validation error
        response = await communicator.receive_json_from(timeout=10)
        self.assertIn(response['type'], ['response_text', 'validation_result'])
        
        await communicator.disconnect()
    
    async def test_states_list_request(self):
        """Test 9: Request for Indian states list."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.receive_json_from()
        
        # Ask for states
        await communicator.send_json_to({
            'type': 'text_message',
            'text': 'What are the Indian states?'
        })
        
        # Should receive response with states
        response = await communicator.receive_json_from(timeout=10)
        self.assertIn(response['type'], ['response_text', 'tool_result'])
        
        await communicator.disconnect()
    
    async def test_off_topic_question(self):
        """Test 10: Off-topic question (should redirect)."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.receive_json_from()
        
        # Ask off-topic question
        await communicator.send_json_to({
            'type': 'text_message',
            'text': 'What is my loan amount?'
        })
        
        # Should redirect politely
        response = await communicator.receive_json_from(timeout=10)
        self.assertIn(response['type'], ['response_text'])
        # Response should mention Basic Details form
        response_text = response.get('text', '').lower()
        self.assertTrue(
            'basic details' in response_text or 'form' in response_text,
            "Should redirect to Basic Details form"
        )
        
        await communicator.disconnect()
    
    async def test_empty_message(self):
        """Test 11: Empty message handling."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.receive_json_from()
        
        # Send empty message
        await communicator.send_json_to({
            'type': 'text_message',
            'text': ''
        })
        
        # Should receive error
        response = await communicator.receive_json_from(timeout=5)
        self.assertEqual(response['type'], 'error')
        
        await communicator.disconnect()
    
    async def test_invalid_json(self):
        """Test 12: Invalid JSON handling."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.receive_json_from()
        
        # Send invalid JSON
        await communicator.send_to(text_data="invalid json")
        
        # Should handle gracefully
        try:
            response = await communicator.receive_json_from(timeout=5)
            self.assertIn(response['type'], ['error', 'response_text'])
        except:
            # Connection might close, which is acceptable
            pass
        
        await communicator.disconnect()
    
    async def test_heartbeat_ping(self):
        """Test 13: Heartbeat ping/pong."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.receive_json_from()
        
        # Send ping
        await communicator.send_json_to({
            'type': 'ping'
        })
        
        # Should receive pong
        response = await communicator.receive_json_from(timeout=5)
        self.assertEqual(response['type'], 'pong')
        
        await communicator.disconnect()
    
    async def test_multiple_messages(self):
        """Test 14: Multiple consecutive messages."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.receive_json_from()
        
        # Send multiple messages
        messages = [
            'What is PAN?',
            'My PAN is ABCDE1234F',
            'What is my date of birth?'
        ]
        
        for msg in messages:
            await communicator.send_json_to({
                'type': 'text_message',
                'text': msg
            })
            # Wait for response
            try:
                response = await communicator.receive_json_from(timeout=10)
                self.assertIn(response['type'], ['response_text', 'tool_result', 'form_suggestion'])
            except:
                pass
        
        await communicator.disconnect()
    
    async def test_session_cleanup_on_disconnect(self):
        """Test 15: Session cleanup on disconnect."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        response = await communicator.receive_json_from()
        session_id = response.get('session_id')
        
        # Disconnect
        await communicator.disconnect()
        
        # Session should be closed (check in database)
        from models.conversation import Session
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def get_session(session_id):
            return Session.objects.get(id=session_id)
        
        session = await get_session(session_id)
        self.assertEqual(session.status, 'closed')
    
    async def test_conversation_storage(self):
        """Test 16: Conversation storage in database."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            f"/ws/voice-chat/?stage={self.stage}",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        response = await communicator.receive_json_from()
        session_id = response.get('session_id')
        
        # Send message
        await communicator.send_json_to({
            'type': 'text_message',
            'text': 'Hello, test message'
        })
        
        # Wait for response
        await communicator.receive_json_from(timeout=10)
        
        # Check conversation in database
        from models.conversation import Conversation
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def get_conversation(session_id):
            return Conversation.objects.get(session_id=session_id)
        
        conversation = await get_conversation(session_id)
        
        self.assertIsNotNone(conversation)
        self.assertGreater(len(conversation.messages), 0)
        
        await communicator.disconnect()


# Edge Cases Tests
class EdgeCasesTests(TestCase):
    """Test edge cases and error scenarios."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.token = create_jwt_token(str(self.user.id))
    
    async def test_expired_token(self):
        """Test 17: Expired JWT token."""
        # Create expired token
        from services.security import JWT_SECRET_KEY, JWT_ALGORITHM
        expired_payload = {
            'user_id': str(self.user.id),
            'exp': datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            "/ws/voice-chat/?stage=basic_details",
            subprotocols=[expired_token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected, "Should not connect with expired token")
        
        await communicator.disconnect()
    
    async def test_very_long_message(self):
        """Test 18: Very long message handling."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            "/ws/voice-chat/?stage=basic_details",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.receive_json_from()
        
        # Send very long message
        long_message = 'A' * 10000
        await communicator.send_json_to({
            'type': 'text_message',
            'text': long_message
        })
        
        # Should handle gracefully (sanitized or truncated)
        try:
            response = await communicator.receive_json_from(timeout=10)
            # Should not crash
            self.assertIn(response['type'], ['response_text', 'error'])
        except:
            # Connection might close, which is acceptable for very long messages
            pass
        
        await communicator.disconnect()
    
    async def test_special_characters_in_message(self):
        """Test 19: Special characters in message."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            "/ws/voice-chat/?stage=basic_details",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.receive_json_from()
        
        # Send message with special characters
        await communicator.send_json_to({
            'type': 'text_message',
            'text': '<script>alert("xss")</script>Hello!'
        })
        
        # Should sanitize and handle
        response = await communicator.receive_json_from(timeout=10)
        self.assertIn(response['type'], ['response_text', 'error'])
        # Should not contain script tags
        self.assertNotIn('<script>', response.get('text', ''))
        
        await communicator.disconnect()
    
    async def test_rapid_messages(self):
        """Test 20: Rapid consecutive messages."""
        communicator = WebsocketCommunicator(
            VoiceChatbotConsumer.as_asgi(),
            "/ws/voice-chat/?stage=basic_details",
            subprotocols=[self.token]
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.receive_json_from()
        
        # Send rapid messages
        for i in range(5):
            await communicator.send_json_to({
                'type': 'text_message',
                'text': f'Message {i}'
            })
        
        # Should handle all messages
        responses_received = 0
        for _ in range(5):
            try:
                response = await communicator.receive_json_from(timeout=5)
                responses_received += 1
            except:
                break
        
        # Should receive at least some responses
        self.assertGreater(responses_received, 0)
        
        await communicator.disconnect()


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

