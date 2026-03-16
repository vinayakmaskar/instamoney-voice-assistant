"""
WSGI config for voice_chatbot project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voice_chatbot.settings')

application = get_wsgi_application()

