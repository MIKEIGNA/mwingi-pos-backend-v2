from asgiref.sync import sync_to_async

from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from channels.sessions import CookieMiddleware, SessionMiddleware
from channels.auth import AuthMiddleware

from .routing import JS_WEBSOCKET_LISTENER_INITIAL_PATH
from accounts.models import WebSocketTicket


from django.contrib.auth import get_user_model

User = get_user_model()

# pylint: disable=bare-except


# Request origin constants
REQUEST_FROM_MOBILE_APP = 0
REQUEST_FROM_ANGULAR = 1
REQUEST_FROM_DJANGO = 2
REQUEST_FROM_SOFTWARE = 3

class WebSocketHelpers:

    @staticmethod
    @sync_to_async
    def get_websocket_ticket_user(reg_no):
        """
        Used when angular app is connecting
        """
        try:
            return WebSocketTicket.objects.get(reg_no=reg_no).user
        except:
            return AnonymousUser()

    @staticmethod
    @sync_to_async
    def delete_websocket_tickets(user):
        """
        Used when angular app is connecting
        """
        # Delete the user's WebSocketTickets so that no other user can
        # # use them to connect
        WebSocketTicket.objects.filter(user=user).delete()

    @staticmethod
    @sync_to_async
    def get_websocket_token_user(token):
        """
        Used when android app is connecting
        """
        try:
            return Token.objects.get(key=token).user
        except:
            return AnonymousUser()

class SessionAndTokenAuthMiddleware(AuthMiddleware):
    """
    Middleware which populates scope["user"] from a Django session.

    If the connection is comming from an api, we also add 'is_api=True' in the scope
    so that the consumer can be able to differenciate between an api and normal
    connection

    Requires SessionMiddleware to function.
    """

    async def resolve_scope(self, scope):
        """
        Get ticket's user and after that delete all the user's tickets
        """

        if self.request_origin == REQUEST_FROM_MOBILE_APP:

            _, token_key = self.headers[b'authorization'].decode("utf-8").split()

            user = await WebSocketHelpers.get_websocket_token_user(token_key)
            scope["user"]._wrapped = user
        
        elif self.request_origin == REQUEST_FROM_ANGULAR:
            """
            Get ticket's user and after that delete all the user's tickets
            """
            user = await WebSocketHelpers.get_websocket_ticket_user(self.reg_no)
            scope["user"]._wrapped = user

            await WebSocketHelpers.delete_websocket_tickets(user)
    
        else:
            await super().resolve_scope(scope)


    async def __call__(self, scope, receive, send):

        self.headers = dict(scope['headers'])

        # Identify request origin
        self.request_origin = REQUEST_FROM_DJANGO

        if b'store-host' in self.headers:
            # Request from software
            self.request_origin = REQUEST_FROM_SOFTWARE

        elif b'authorization' in self.headers:
            # Request from angular
            self.request_origin = REQUEST_FROM_MOBILE_APP

        elif b'sec-websocket-version' in self.headers:

            if JS_WEBSOCKET_LISTENER_INITIAL_PATH in scope['path']:

                # Request from angular
                self.request_origin = REQUEST_FROM_ANGULAR

                self.reg_no = scope['path'].split(JS_WEBSOCKET_LISTENER_INITIAL_PATH)[1]

            else:
                # Request from django templates
                self.request_origin = REQUEST_FROM_DJANGO

        # Peform the proper authorization depending the request origin
        if (self.request_origin == REQUEST_FROM_MOBILE_APP) or \
            (self.request_origin == REQUEST_FROM_ANGULAR):

            try: 

                # Grab the finalized/resolved scope
                await self.resolve_scope(scope)

            except:
                "Log here"
                   
            # Notify consumer that the request is from an api
            scope['is_api'] = True 

            close_old_connections()

            return await super().__call__(scope, receive, send)

        elif self.request_origin == REQUEST_FROM_SOFTWARE:

            # Notify consumer that the request is from an api
            scope['is_api'] = True 

            close_old_connections()

            return await super().__call__(scope, receive, send)

        else:

            scope = dict(scope)
            # Scope injection/mutation per this middleware's needs.
            self.populate_scope(scope)
            # Grab the finalized/resolved scope
            await self.resolve_scope(scope)

            return await super().__call__(scope, receive, send)

"""    
Handy shortcut for applying all three layers at once 
We found it from channels.auth import AuthMiddleware

Our cutstom 'TokenAuthMiddlewareStack' is imported and used in traqsale_cloud.asgi
"""
# Handy shortcut for applying all three layers at once
def TokenAuthMiddlewareStack(inner):
    return CookieMiddleware(SessionMiddleware(SessionAndTokenAuthMiddleware(inner)))