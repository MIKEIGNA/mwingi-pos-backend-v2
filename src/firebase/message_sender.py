from firebase.tasks import firebase_user_messaging_tasks
from firebase.models import FirebaseDevice


# pylint: disable=bare-except
# pylint: disable=broad-except

class FirebaseMessageSender:

    @staticmethod
    def send_notification_update_to_user(new_notification):
        """ Sends the received location update from a store to top and supervisor
        user's websocket websocket client/s

        Args:
            new_notification (Notification): The new notification that should be sent to the
                appropiate websocket client/s
        """
        try:

            profile = new_notification.profile

            unread_notification_count = profile.get_all_unread_notifications()

            # Gets all firebase tokens for the receiving users and then sends the 
            # notification update
            devices = FirebaseDevice.objects.filter(user=profile.user)

            for device in devices:
                # To avoid Message.data must not contain non-string values error,
                # we make sure every value is a string including ints
                payload = {
                    'token_owner_reg_no': str(profile.reg_no),
                    'type': 'notification',
                    'count': str(unread_notification_count),
                }

                firebase_user_messaging_tasks(device.token, payload)

        except:
            # Log error
            pass


