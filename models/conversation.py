"""
Database models for conversations and sessions.
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta
import json


class Session(models.Model):
    """Active WebSocket sessions"""
    
    id = models.BigAutoField(primary_key=True)
    session_identifier = models.CharField(max_length=255, unique=True, db_index=True)
    user_id = models.CharField(max_length=255, db_index=True)
    stage = models.CharField(max_length=100, default='basic_details')
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('closed', 'Closed'),
            ('expired', 'Expired'),
        ],
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'sessions'
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Session {self.id} - User {self.user_id} - {self.status}"
    
    def is_expired(self):
        """Check if session is expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def extend_expiry(self, minutes=30):
        """Extend session expiry"""
        self.expires_at = timezone.now() + timedelta(minutes=minutes)
        self.save()


class Conversation(models.Model):
    """Store full conversation history"""
    
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=255, db_index=True)
    stage = models.CharField(max_length=100, default='basic_details')
    session_id = models.CharField(max_length=255, unique=True, db_index=True)
    messages = models.JSONField(default=list)
    language = models.CharField(max_length=10, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'conversations'
        indexes = [
            models.Index(fields=['user_id', 'stage']),
            models.Index(fields=['session_id']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Conversation {self.id} - User {self.user_id} - {self.stage}"
    
    def add_message(self, role, content, message_type='text', metadata=None):
        """Add a message to the conversation"""
        if not self.messages:
            self.messages = []
        
        message = {
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'type': message_type,  # 'text' or 'audio'
            'timestamp': timezone.now().isoformat(),
        }
        
        if metadata:
            message['metadata'] = metadata
        
        self.messages.append(message)
        self.save()
    
    def get_messages(self, limit=None):
        """Get messages from conversation"""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def get_last_n_messages(self, n=10):
        """Get last N messages"""
        return self.messages[-n:] if len(self.messages) > n else self.messages

