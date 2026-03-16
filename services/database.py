"""
Database operations for conversations and sessions.
"""
from datetime import timedelta
from django.utils import timezone
from channels.db import database_sync_to_async
from models.conversation import Conversation, Session
from config.settings import SESSION_TIMEOUT_MINUTES


@database_sync_to_async
def create_session(user_id: str, stage: str) -> str:
    """
    Create a new session.
    
    Args:
        user_id: User ID
        stage: Current stage (e.g., 'basic_details')
    
    Returns:
        Session identifier (string)
    """
    from datetime import datetime
    import uuid
    
    session_identifier = f"{user_id}_{stage}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    session = Session(
        session_identifier=session_identifier,
        user_id=user_id,
        stage=stage,
        status='active',
        expires_at=timezone.now() + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    )
    session.save()
    
    return session_identifier


@database_sync_to_async
def close_session(session_identifier: str):
    """
    Close a session.
    
    Args:
        session_identifier: Session identifier string
    """
    try:
        session = Session.objects.get(session_identifier=session_identifier)
        session.status = 'closed'
        session.save()
    except Session.DoesNotExist:
        pass


@database_sync_to_async
def get_or_create_conversation(user_id: str, stage: str, session_id: str) -> Conversation:
    """
    Get or create a conversation.
    
    Args:
        user_id: User ID
        stage: Current stage
        session_id: Session ID
    
    Returns:
        Conversation object
    """
    conversation, created = Conversation.objects.get_or_create(
        session_id=session_id,
        defaults={
            'user_id': user_id,
            'stage': stage,
            'messages': [],
            'language': 'en'
        }
    )
    return conversation


async def save_message(user_id: str, stage: str, session_id: str, role: str, content: str, message_type: str = 'text', metadata: dict = None):
    """
    Save a message to conversation.
    
    Args:
        user_id: User ID
        stage: Current stage
        session_id: Session ID
        role: 'user' or 'assistant'
        content: Message content
        message_type: 'text' or 'audio'
        metadata: Optional metadata dict (e.g., interrupted, complete)
    """
    conversation = await get_or_create_conversation(user_id, stage, session_id)
    
    # Add message synchronously (conversation.add_message is a sync method)
    @database_sync_to_async
    def _add_message():
        conversation.add_message(role, content, message_type, metadata)
    
    await _add_message()


@database_sync_to_async
def update_conversation_language(session_id: str, language: str):
    """
    Update conversation language.
    
    Args:
        session_id: Session ID
        language: Language code (e.g., 'en', 'hi', 'ta')
    """
    try:
        conversation = Conversation.objects.get(session_id=session_id)
        conversation.language = language
        conversation.save()
    except Conversation.DoesNotExist:
        pass

