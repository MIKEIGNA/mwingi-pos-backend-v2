import json
import ast

from asgiref.sync import async_to_sync

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from ...models import UserChannelRecord


class MqConsumer(AsyncWebsocketConsumer):
    """ Handles all websocket connection for the whole application """
    
    async def connect(self):
        """
        Called when a WebSocket connection is opened.
        """

        # Check if this is an api request
        self.is_api = self.scope.get('is_api', False)

        if await self.create_user_channel_record():
            await self.accept()
            
    async def disconnect(self, close_code):
        """
        Called when a WebSocket connection is closed.
        """
        
        # Note that in some rare cases (power loss, etc) disconnect may fail
        # to run; this naive example would leave zombie channel names around.
        await self.delete_user_channel_record(self.channel_name)
        
    async def receive(self, text_data=None, bytes_data=None):
        pass
                     
    async def send_message_to_websocket(self, event):
        """
        # Receive message and then it sends it to the websocket
        """
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
    
    
    @database_sync_to_async
    def create_user_channel_record(self):
        """ Creates a UserChannelRecord for the current channel name so that
        the channel name can stored in the db and be able to be accessed later
        """
        user = self.scope["user"]
  
        # Only connect if user is authenticated
        if not user.is_anonymous:
            
            # To avoid having duplicates in our db, we only create a new 
            # user channel record if there is no client in the db 
            
            try:
                client = UserChannelRecord.objects.get(
                    user=user,
                    is_api=self.is_api
                )
                
                # Before storing the new channel name, get the previous one
                previous_channel_name = client.channel_name
                    
                    
                # Make sure we dont connect more than one web socket in a given channel
                if previous_channel_name == self.channel_name:
                    return False
                    
                # Update channel name
                client.channel_name = self.channel_name
                client.save()
                        
                self.send_disconnect_request(previous_channel_name)
  
            except Exception as e:

                try:
                
                    # To prevent having multiple UserChannelRecord for the same user
                    # we fisrt delete his/her previous records
                    UserChannelRecord.objects.filter(user=user, 
                                                 is_api=self.is_api).delete()
                    
                    # Then create an new record
                    UserChannelRecord.objects.create(user=user,
                                                 is_api=self.is_api,
                                                 channel_name=self.channel_name)

                    print("Channel created successfully")

                except Exception as k:
                    print("Exception K ", k)

            return True
            
        # Log error
        return False
    
    def send_disconnect_request(self, channel_name):
        """ Send a disconnect request to web socket client

        Args:
            channel_name (string): The name of the channel that a disconnect
                request will be sent
        """
 
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.send)(
                channel_name,
                {'type': 'send_message_to_websocket', 
                 'message': {'type': 'close',
                             'content': 1008
                             },
                             }
                 )
    
    @database_sync_to_async
    def delete_user_channel_record(self, channel_name):
        """ Deletes the provided channel_name's  UserChannelRecord  

        Args:
            channel_name (string): The name of the channel whose UserChannelRecord
            should be deleted
        """
        UserChannelRecord.objects.filter(
            is_api=self.is_api,
            channel_name=channel_name).delete()



class WebSocketMessageSender:

    @staticmethod
    def send_profile_update_to_user(user, payload):
        """ Sends the received profile data from Profile to their websocket 
        websocket 
        client/s

        Args:
            user (User): The user whose websocket's should receive the data
            payload (dict): The new data that should be sent to the
                appropiate websocket client/s
            
        """
        try:
            
            # Gets all channel names for the receiving users and then sends the 
            # location updates to all of them
            channel_records = UserChannelRecord.objects.filter(user=user)

            for channel_record in channel_records:          
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.send)(
                    channel_record.channel_name,
                    {'type': 'send_message_to_websocket', 
                     'message': payload,
                    })

        except Exception as e:
            print(e)
            pass
