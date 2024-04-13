from django.db.models import Q

from firebase.tasks import firebase_multiple_users_messaging_tasks
from firebase.models import FirebaseDevice

class StockLevelsMessageSender:

    @staticmethod
    def send_model_update_to_users(stock_level, notify_low_stock):
        """
        Sends a newly edited stock level units data to users through firebase

        Args:
            stock_level (StockLevel): The stock level that has been edited
            notify_low_stock: A flag indicating if we should notify for low stock
            or not
        """
        owner_profile = stock_level.store.profile
        owner_user = owner_profile.user
        group_id = owner_profile.get_user_group_identification()

        tokens = FirebaseDevice.objects.filter(
            Q(user=owner_user) | Q(user__employeeprofile__profile__user=owner_user),
            store=stock_level.store
            ).values_list('token')

        retrieved_tokens=[]
        for token in tokens:
            retrieved_tokens.append(token[0])

        relevant_stores = []
        
        payload = {
            'group_id': group_id,
            'relevant_stores': str(relevant_stores),
            'model': 'stock_level',
            'action_type': 'edit', 

            'product_reg_no': str(stock_level.product.reg_no),
            'minimum_stock_level': str(stock_level.minimum_stock_level),
            'units': str(stock_level.units),
            'notify_low_stock': str(notify_low_stock)
        }

        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)
    
    