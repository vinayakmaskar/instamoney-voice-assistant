"""
ASGI config for voice_chatbot project.
"""

import os

# Set Django settings module BEFORE any Django imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voice_chatbot.settings')

# Now import Django and initialize
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Initialize Django ASGI application FIRST
django_asgi_app = get_asgi_application()

# Import consumers AFTER Django is initialized
import consumers.routing

application = ProtocolTypeRouter({
    # HTTP requests go to Django
    "http": django_asgi_app,
    
    # WebSocket requests go to Channels
    "websocket": AuthMiddlewareStack(
        URLRouter(
            consumers.routing.websocket_urlpatterns
        )
    ),
})

