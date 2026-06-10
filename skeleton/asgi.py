"""
ASGI config for skeleton project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""
from django.core.asgi import get_asgi_application
import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from .routing import ws_urlpatterns

django_asgi_app = get_asgi_application()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skeleton.settings.local')

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(URLRouter(ws_urlpatterns))
})
