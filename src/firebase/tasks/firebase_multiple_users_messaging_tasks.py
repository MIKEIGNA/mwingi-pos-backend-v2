import json
import logging

from firebase_admin import messaging

from traqsale_cloud.celery import app as celery_app
from traqsale_cloud.firebase import app as firebase_app

# pylint: disable=bare-except
# pylint: disable=broad-except

def firebase_multiple_users_messaging_tasks(tokens, payload, origin='unknown'):
    """
    Sends firebase data message to multiple users

    Args: 
       tokens: Firebase tokens
       payload: Payload that will be sent as firebase messages
    """
    # Don't call _firebase_tokens_messaging_tasks when we are in test mode
    from django.conf import settings

    if not settings.TESTING_MODE:
        _firebase_multiple_users_messaging_tasks.delay(tokens, payload)
    else:
        logger = logging.getLogger('test_firebase_sender_logger')
        
        logger.info(json.dumps({'tokens': tokens, 'payload': payload}))
   


# Should not be called directly. You should use firebase_multiple_users_messaging_tasks 
# method to access this
@celery_app.task(name="firebase_multiple_users_messaging_tasks")
def _firebase_multiple_users_messaging_tasks(tokens, payload): 
    """
    Sends firebase data message to multiple users

    Args: 
       tokens: Firebase tokens
       payload: Payload that will be sent as firebase messages
    """
    # print('Calling multiple')

    _FirebaseMultipleUsersMessagingTasks(tokens, payload)

# Should not be called directly. You should use _firebase_multiple_users_messaging_tasks 
# method to access this
class _FirebaseMultipleUsersMessagingTasks:

    def __init__(self, tokens, payload):

        from firebase.models import FirebaseDevice

        # print()
        # print(">>> ",  payload)

        self.tokens = tokens
        self.payload = payload

        message = messaging.MulticastMessage(
            data=payload,
            tokens=tokens,
        )

        response = messaging.send_multicast(message, app=firebase_app)

        if response.failure_count > 0:
            responses = response.responses
            failed_tokens = []
            for idx, resp in enumerate(responses):
                if not resp.success:
                    # The order of responses corresponds to the order of the registration tokens.
                    failed_tokens.append(tokens[idx])

            
            if failed_tokens:
                # print('List of tokens that caused failures: {0}'.format(failed_tokens))

                for token in failed_tokens:
                    FirebaseDevice.objects.filter(token=token).delete()

            else:
                '''
                print('Firebase success')
                '''


            


        