from django.db.models import Q

from firebase.tasks import firebase_multiple_users_messaging_tasks
from firebase.models import FirebaseDevice

class DiscountMessageSender:

    @staticmethod
    def send_discount_creation_update_to_users(discount):
        """
        Sends a newly cretaed discount's data to users through firebase

        Args:
            discount (Discount): The new discount that has been created
        """
        DiscountMessageSender.send_discount_update_to_users(
            discount, 
            'create'
        )

    @staticmethod
    def send_discount_edit_update_to_users(discount):
        """
        Sends a newly edited discount's data to users through firebase

        Args:
            discount (Discount): The new discount that has been created
        """
        DiscountMessageSender.send_discount_update_to_users(
            discount, 
            'edit'
        )

    @staticmethod
    def send_discount_deletion_update_to_users(discount):
        """
        Sends a newly deleted discount's data to users through firebase

        Args:
            discount (Discount): The new discount that has been created
        """
        DiscountMessageSender.send_discount_update_to_users(
            discount, 
            'delete'
        )

    @staticmethod
    def send_discount_update_to_users(discount, action_type):
        """
        Sends a newly cretaed discount's data to users through firebase

        Args:
            discount (Discount): The new discount that has been created
            action (String): A str describing the action type
        """
        owner_profile = discount.profile
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
            'model': 'discount',
            'action_type': action_type, 

            'name': discount.name,
            'value': str(discount.value),
            'amount': str(discount.amount),
            'reg_no': str(discount.reg_no)
        }

        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)
    