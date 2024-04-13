from django.db.models import Q

from firebase.tasks import firebase_multiple_users_messaging_tasks
from firebase.models import FirebaseDevice


# pylint: disable=bare-except
# pylint: disable=broad-except

class ModifierMessageSender:

    @staticmethod
    def send_modifier_creation_update_to_users(modifier):
        """
        Sends a newly cretaed modifier's data to users through firebase

        Args:
            modifier (Modifier): The new modifier that has been created
        """
        ModifierMessageSender.send_modifier_update_to_users(
            modifier, 
            'create'
        )

    @staticmethod
    def send_modifier_edit_update_to_users(modifier):
        """
        Sends a newly edited modifier's data to users through firebase

        Args:
            modifier (Modifier): The new modifier that has been created
        """
        ModifierMessageSender.send_modifier_update_to_users(
            modifier, 
            'edit'
        )

    @staticmethod
    def send_modifier_deletion_update_to_users(modifier):
        """
        Sends a newly deleted modifier's data to users through firebase

        Args:
            modifier (Modifier): The new modifier that has been created
        """
        ModifierMessageSender.send_modifier_update_to_users(
            modifier, 
            'delete'
        )

    @staticmethod
    def send_modifier_update_to_users(modifier, action_type):
        """
        Sends a newly cretaed modifier's data to users through firebase

        Args:
            modifier (Modifier): The new modifier that has been created
            action (String): A str describing the action type
        """
        owner_profile = modifier.profile
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
            'model': 'modifier',
            'action_type': action_type, 

            'name': modifier.name, 
            'description': modifier.description, 
            'reg_no': str(modifier.reg_no), 
            'modifier_options': str(modifier.get_modifier_options())
        }

        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)
    