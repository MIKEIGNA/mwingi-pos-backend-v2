from django.db.models import Q

from firebase.tasks import firebase_multiple_users_messaging_tasks
from firebase.models import FirebaseDevice


# pylint: disable=bare-except
# pylint: disable=broad-except

class TaxMessageSender:

    @staticmethod
    def send_tax_creation_update_to_users(tax):
        """
        Sends a newly cretaed tax's data to users through firebase

        Args:
            tax (Tax): The new tax that has been created
        """
        TaxMessageSender.send_tax_update_to_users(
            tax, 
            'create'
        )

    @staticmethod
    def send_tax_edit_update_to_users(tax):
        """
        Sends a newly edited tax's data to users through firebase

        Args:
            tax (Tax): The new tax that has been created
        """
        TaxMessageSender.send_tax_update_to_users(
            tax, 
            'edit'
        )

    @staticmethod
    def send_tax_deletion_update_to_users(tax):
        """
        Sends a newly deleted tax's data to users through firebase

        Args:
            tax (Tax): The new tax that has been created
        """
        TaxMessageSender.send_tax_update_to_users(
            tax, 
            'delete'
        )

    @staticmethod
    def send_tax_update_to_users(tax, action_type):
        """
        Sends a newly cretaed tax's data to users through firebase

        Args:
            tax (Tax): The new tax that has been created
            action (String): A str describing the action type
        """
        owner_profile = tax.profile
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
            'model': 'tax',
            'action_type': action_type, 

            'name': tax.name,
            'rate': str(tax.rate),
            'reg_no': str(tax.reg_no)
        }

        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)
    