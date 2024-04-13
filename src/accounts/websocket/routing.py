from django.urls import path

from .consumers.user_consumers import MqConsumer

# This variable is accessed in websocket auth middleware so that we know which
# part of the url we should cut for us to remain with the reg_no
JS_WEBSOCKET_LISTENER_INITIAL_PATH = "listener2/"

websocket_urlpatterns = [
    path(f'{JS_WEBSOCKET_LISTENER_INITIAL_PATH}<int:reg_no>', MqConsumer.as_asgi()),
    path('listener/', MqConsumer.as_asgi()),

    #path('store/listener/', StoreHostConsumer.as_asgi()),
]