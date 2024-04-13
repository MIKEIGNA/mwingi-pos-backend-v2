from django.db.models import Q

from firebase.tasks import firebase_multiple_users_messaging_tasks
from firebase.models import FirebaseDevice

class UserGeneralSettingMessageSender:

    @staticmethod
    def send_model_update_to_users(user_general_setting):
        """
        Sends a newly edited user_general_setting's data to users through firebase

        Args:
            user_general_setting (UserGeneralSetting): The new user_general_setting that has been edited
        """
        owner_profile = user_general_setting.profile
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
            'model': 'user_general_setting',
            'action_type': 'edit', 
 
            'enable_shifts': str(user_general_setting.enable_shifts), 
            'enable_open_tickets': str(user_general_setting.enable_open_tickets), 
            'enable_low_stock_notifications': str(user_general_setting.enable_low_stock_notifications),
            'enable_negative_stock_alerts': str(user_general_setting.enable_negative_stock_alerts),
        }
        
        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)
    