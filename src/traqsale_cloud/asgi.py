"""
ASGI config for traqsale_cloud project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

import django
django.setup()

from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter

import accounts.websocket.routing
from accounts.websocket.token_auth import TokenAuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "traqsale_cloud.settings")

application = ProtocolTypeRouter({
  "http": get_asgi_application(),
  "websocket": TokenAuthMiddlewareStack(
        URLRouter(
            accounts.websocket.routing.websocket_urlpatterns
        )
    ),
})
