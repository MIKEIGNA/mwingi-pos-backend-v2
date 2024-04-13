from django.db.models import Q

from firebase.tasks import firebase_multiple_users_messaging_tasks
from firebase.models import FirebaseDevice

class CategoryMessageSender:

    @staticmethod
    def send_category_creation_update_to_users(category):
        """
        Sends a newly cretaed category's data to users through firebase

        Args:
            category (Category): The new category that has been created
        """
        CategoryMessageSender.send_category_update_to_users(
            category, 
            'create'
        )

    @staticmethod
    def send_category_edit_update_to_users(category):
        """
        Sends a newly edited category's data to users through firebase

        Args:
            category (Category): The new category that has been created
        """
        CategoryMessageSender.send_category_update_to_users(
            category, 
            'edit'
        )

    @staticmethod
    def send_category_deletion_update_to_users(category):
        """
        Sends a newly deleted category's data to users through firebase

        Args:
            category (Category): The new category that has been created
        """
        CategoryMessageSender.send_category_update_to_users(
            category, 
            'delete'
        )

    @staticmethod
    def send_category_update_to_users(category, action_type):
        """
        Sends a newly cretaed category's data to users through firebase

        Args:
            category (Category): The new category that has been created
            action (String): A str describing the action type
        """
        owner_profile = category.profile
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
            'model': 'category',
            'action_type': action_type, 

            'name': category.name,
            'color_code': category.color_code,
            'product_count': str(category.product_count),
            'reg_no': str(category.reg_no)
        }
        
        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)
    