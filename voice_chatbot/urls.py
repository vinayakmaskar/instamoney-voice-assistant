"""
URL configuration for voice_chatbot project.
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path('admin/', admin.site.urls),
]

# Serve the Expo web frontend from /frontend-dist/
frontend_dist = os.path.join(settings.BASE_DIR, 'frontend', 'dist')
if os.path.exists(frontend_dist):
    from django.views.static import serve as static_serve
    from django.http import FileResponse

    def serve_frontend(request, path='index.html'):
        file_path = os.path.join(frontend_dist, path)
        if os.path.isfile(file_path):
            return FileResponse(open(file_path, 'rb'))
        return FileResponse(open(os.path.join(frontend_dist, 'index.html'), 'rb'))

    urlpatterns += [
        path('', serve_frontend, name='frontend-index'),
        path('<path:path>', serve_frontend, name='frontend-files'),
    ]

