from pprint import pprint
import requests

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.conf import settings
from django.urls import reverse

from firebase.tasks import firebase_multiple_users_messaging_tasks
from firebase.models import FirebaseDevice



class ReceiptMessageSender:

    @staticmethod
    def send_receipt_creation_update_to_user(receipt):
        """
        Sends a newly cretaed receipt's data to user through firebase

        Args:
            receipt (Receipt): The new receipt that has been created
        """
        
        ReceiptMessageSender.send_receipt_update_to_users(receipt, 'create')

    @staticmethod
    def send_receipt_edit_update_to_user(receipt):
        """
        Sends a newly edited receipt's data to user through firebase

        Args:
            receipt (Receipt): The new receipt that has been created
        """
        ReceiptMessageSender.send_receipt_update_to_users(receipt, 'edit')

    @staticmethod
    def get_receipt_from_url_withreg_no(receipt):

        if settings.TESTING_MODE:
            # Include an appropriate `Authorization:` header on all requests.
            token = Token.objects.get(user__email='john@gmail.com')
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

            param = f'?reg_no__in={receipt.reg_no},{receipt.refund_for_reg_no}'
            response = client.get(
                reverse('api:pos_receipt_index', args=(receipt.store.reg_no,))+param)
            
        else:

            # receipt1.save()
            url = f'{settings.MY_SITE_URL}/api/pos/receipts/{receipt.store.reg_no}/?reg_no={receipt.reg_no}'

            access_token=Token.objects.filter(user__profile=receipt.store.profile).first()

            if access_token:
                my_headers = {'Authorization' : f'Token {access_token}'}
                response = requests.get(
                    url=url, 
                    headers=my_headers,
                    timeout=settings.PYTHON_REQUESTS_TIMEOUT
                )

        if response.status_code == 200:
            return response.json()['results']
        else:
            return None
        
    @staticmethod
    def send_receipt_refund_update_to_user(receipt):
        """
        Sends a newly refunded receipt's data to user through firebase

        Args:
            receipt (Receipt): The new receipt that has been created
        """
        tokens = FirebaseDevice.objects.filter(
            user=receipt.user).values_list('token')

        retrieved_tokens = []
        for token in tokens:
            retrieved_tokens.append(token[0])

        relevant_stores = []

        results = ReceiptMessageSender.get_receipt_from_url_withreg_no(receipt)

        print("####################")
        pprint(results)

        payload = {
            'group_id': '',
            'relevant_stores': str(relevant_stores),
            'model': 'refund_receipt',
            'action_type': 'create',

            'results': str(results),
        }

        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)

    @staticmethod
    def send_receipt_deletion_update_to_user(receipt, tokens):
        """
        Sends a newly deleted receipt's data to user through firebase

        Args:
            tokens (FirebaseDevice List): The tokens that will receive the notification
            receipt (Receipt): The new receipt that has been created
        """

        retrieved_tokens = []
        for token in tokens:
            retrieved_tokens.append(token[0])

        relevant_stores = []

        payload = {
            'group_id': '',
            'relevant_stores': str(relevant_stores),
            'model': 'receipt',
            'action_type': 'delete',

            'reg_no': str(receipt.reg_no),
        }

        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)

    @staticmethod
    def send_receipt_update_to_users(receipt, action_type):
        """
        Sends a newly cretaed receipt's data to users through firebase

        Args:
            receipt (Receipt): The new receipt that has been created
            action (String): A str describing the action type
        """
        tokens = FirebaseDevice.objects.filter(
            user=receipt.user).values_list('token')

        retrieved_tokens = []
        for token in tokens:
            retrieved_tokens.append(token[0])

        relevant_stores = []

        receipt_lines = receipt.receiptline_set.all().values(
            'product__name',
            'reg_no', 
            'refunded_units', 
            'units'
        )

        new_receipt_lines = [
            {
                'product_name': receipt_line['product__name'],
                'reg_no': receipt_line['reg_no'],
                'refunded_units': str(receipt_line['refunded_units']),
                'units': str(receipt_line['units'])
            } for receipt_line in receipt_lines
        ]
        
        payload = {
            'group_id': '',
            'relevant_stores': str(relevant_stores),
            'model': 'receipt',
            'action_type': action_type,

            'transaction_type': str(receipt.transaction_type),
            'payment_completed': str(receipt.payment_completed),
            'is_refund': str(receipt.is_refund),
            'local_reg_no': str(receipt.local_reg_no),
            'reg_no': str(receipt.reg_no),
            'id': str(receipt.id),
            'payment_list': str(receipt.get_payment_list()),
            'receipt_lines': str(new_receipt_lines),
        }

        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)

  