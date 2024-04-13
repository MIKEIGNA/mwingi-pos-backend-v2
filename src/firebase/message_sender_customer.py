from django.db.models import Q

from firebase.tasks import firebase_multiple_users_messaging_tasks
from firebase.models import FirebaseDevice

class CustomerMessageSender:

    @staticmethod
    def send_customer_creation_update_to_users(customer):
        """
        Sends a newly cretaed customer's data to users through firebase

        Args:
            customer (Customer): The new customer that has been created
        """
        CustomerMessageSender.send_customer_update_to_users(
            customer, 
            'create'
        )

    @staticmethod
    def send_customer_edit_update_to_users(customer):
        """
        Sends a newly edited customer's data to users through firebase

        Args:
            customer (Customer): The new customer that has been created
        """
        CustomerMessageSender.send_customer_update_to_users(
            customer, 
            'edit'
        )

    @staticmethod
    def send_customer_deletion_update_to_users(customer):
        """
        Sends a newly deleted customer's data to users through firebase

        Args:
            customer (Customer): The new customer that has been created
        """
        CustomerMessageSender.send_customer_update_to_users(
            customer, 
            'delete'
        )

    @staticmethod
    def send_customer_update_to_users(customer, action_type):
        """
        Sends a newly cretaed customer's data to users through firebase

        Args:
            customer (Customer): The new customer that has been created
            action (String): A str describing the action type
        """
        owner_profile = customer.profile
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
            'model': 'customer',
            'action_type': action_type, 

            'name': customer.name, 
            'email': customer.email if customer.email else '', 
            'village_name': customer.village_name if customer.village_name else '', 
            'non_null_phone': str(customer.get_non_null_phone()),
            'phone': str(customer.phone), 
            'address': customer.address, 
            'city': customer.city, 
            'region': customer.region, 
            'postal_code': str(customer.postal_code), 
            'country': str(customer.country), 
            'customer_code': str(customer.customer_code), 
            'credit_limit': str(customer.credit_limit),
            'current_debt': str(customer.current_debt),
            'cluster_data': str(customer.get_cluster_data()),

            # When receipt calculates customer points, this value is temporary decimal
            # even though it needs to be an IntegerField. So we make sure it's
            # always an int
            'points': str(int(customer.points)), 

            'reg_no': str(customer.reg_no)

        }

        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)
    