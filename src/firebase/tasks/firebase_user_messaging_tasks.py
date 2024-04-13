from firebase_admin import messaging
import firebase_admin

from traqsale_cloud.celery import app as celery_app
from traqsale_cloud.firebase import app as firebase_app

# pylint: disable=bare-except
# pylint: disable=broad-except


def firebase_user_messaging_tasks(token, payload):
    """
    Sends firebase data message to a single user

    Args: 
       token: Firebase token
       payload: Payload that will be sent as firebase messages
    """

    # return

    # We make sure token_owner_reg_no and type are keys in the payload since our
    # frontend apps use the info to determine the data message type
    if not payload.get('token_owner_reg_no', None):
        print("***** Error firebase payload must have token_owner_reg_no field")
        return
    
    if not payload.get('type', None):
        print("***** Error firebase payload must have type field")
        return
    
    # Don't call _firebase_user_messaging_tasks when we are in test mode
    from django.conf import settings

    if not settings.TESTING_MODE:
        _firebase_user_messaging_tasks.delay(token, payload)

# Should not be called directly. You should use firebase_user_messaging_tasks 
# method to access this
@celery_app.task(name="firebase_user_messaging_tasks")
def _firebase_user_messaging_tasks(token, payload): 
    """
    Sends firebase data message to a single user

    Args: 
       token: Firebase token
       payload: Payload that will be sent as firebase messages
    """
    _FirebaseUserMessagingTasks(token, payload)

# Should not be called directly. You should use _firebase_user_messaging_tasks 
# method to access this
class _FirebaseUserMessagingTasks:
    
    def __init__(self, token, payload):
        self.token = token
        self.payload = payload

        try:

            # See documentation on defining a message payload.
            message = messaging.Message(data=payload, token=token)
        
            # Send a message to the device corresponding to the provided
            # registration token.
            messaging.send(message, app=firebase_app)

        except firebase_admin._messaging_utils.UnregisteredError:

            # if we get unregistered error, we delete the token because we
            # have no use for it anymore

            from firebase.models import FirebaseDevice

            FirebaseDevice.objects.filter(token=token).delete()

        except Exception:
            "Log here"
            