from django.db.models import Q

from firebase.tasks import firebase_multiple_users_messaging_tasks
from firebase.models import FirebaseDevice

class LoyaltySettingsMessageSender:

    @staticmethod
    def send_model_update_to_users(loyalty):
        """
        Sends a newly edited loyalty settings value users through firebase

        Args:
            loyalty (LoyaltySetting): The new loyalty setting that has been edited
        """
        owner_profile = loyalty.profile
        owner_user = owner_profile.user
        group_id = owner_profile.get_user_group_identification()

        tokens = FirebaseDevice.objects.filter(
            Q(user=owner_user) | Q(user__employeeprofile__profile__user=owner_user)
            ).values_list('token')

        retrieved_tokens=[]
        for token in tokens:
            retrieved_tokens.append(token[0])

        relevant_stores = []
        
        payload = {
            'group_id': group_id,
            'relevant_stores': str(relevant_stores),
            'model': 'loyalty',
            'action_type': 'edit', 

            'value': str(loyalty.value),
        }

        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)
    
    