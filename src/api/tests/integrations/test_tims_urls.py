from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from api.tests.sales.create_receipts_for_test import CreateReceiptsForTesting

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.initial_user_data import CreateTimeVariablesMixin, InitialUserDataMixin

from mysettings.models import MySetting

from sales.models import Receipt
from stores.models import StorePaymentMethod

class TimsReceiptUpdateViewTestCase(APITestCase, InitialUserDataMixin, CreateTimeVariablesMixin):

    def setUp(self):
        """
        This function is defined in the 'InitialUserDataMixin' mixin

        It creates 2 top users, 3 stores and 5 employee users as follows

        * Top User 1 assets:
            self.user1 - top user 
            self.top_profile1 - Profile for top user -- (john@gmail.com)

            - self.store1 - Store -- (Computer Store) 
                self.manager_profile1 - Manger Employee profile for top user 1 -- (gucci@gmail.com)

                self.cashier_profile1 - Cashier Employee profile under manager profile 1 -- (kate@gmail.com)
                self.cashier_profile2 - Cashier Employee profile under manager profile 1 -- (james@gmail.com)
                self.cashier_profile3 - Cashier Employee profile under manager profile 1 -- (ben@gmail.com)

            - self.store2 - Store -- (Cloth Store)
                self.manager_profile2 - Manger Employee profile for top user 1 -- (lewis@gmail.com)

                self.cashier_profile4 - Cashier Employee profile under manager profile 2 -- (hugo@gmail.com)


        * Top User 2 assets:
            self.user2 - top user
            self.top_profile2 - Profile for top user-- (jack@gmail.com)

            - self.store3 - Store -- (Toy Store)
                self.manager_profile3 - Manger Employee profile for top user 2 -- (cristiano@gmail.com):

                self.cashier_profile5 - Cashier Employee profile under manager profile 3 -- (juliet@gmail.com)
        """

        self.create_initial_user_data()

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        """
        Creates 3 receipts for profile. manager ang cashier respectively. First 
        2 are in store1 while the last one is in store2
        """
        CreateReceiptsForTesting(
            self.top_profile1,
            self.manager_profile1, 
            self.cashier_profile1,
            self.store1, 
            self.store2
        ).create_receipts()

        

        self.pagination_users = [
            {
                'name': self.user1.get_full_name(), 
                'reg_no': self.user1.reg_no
            }, 
            {
                'name': self.manager_profile1.get_full_name(), 
                'reg_no': self.manager_profile1.reg_no
            }, 
            {
                'name': self.cashier_profile1.get_full_name(), 
                'reg_no': self.cashier_profile1.reg_no
            }, 
            {
                'name': self.cashier_profile2.get_full_name(), 
                'reg_no': self.cashier_profile2.reg_no
            }, 
            {
                'name': self.cashier_profile3.get_full_name(), 
                'reg_no': self.cashier_profile3.reg_no
            }, 
            {
                'name': self.manager_profile2.get_full_name(), 
                'reg_no': self.manager_profile2.reg_no
            }, 
            {
                'name': self.cashier_profile4.get_full_name(), 
                'reg_no': self.cashier_profile4.reg_no
            }
        ]

        # Get payments
        self.cash_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.CASH_TYPE
        )

        self.mpesa_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.MPESA_TYPE
        )

        self.card_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.CARD_TYPE
        )

        self.points_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.POINTS_TYPE
        )

        self.debt_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.DEBT_TYPE
        )

        self.other_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.OTHER_TYPE
        )

        self.payment_list = [
            {
                'name': self.cash_pay_method.name, 
                'reg_no': self.cash_pay_method.reg_no
            }, 
            {
                'name': self.mpesa_pay_method.name, 
                'reg_no': self.mpesa_pay_method.reg_no
            }, 
            {
                'name': self.card_pay_method.name, 
                'reg_no': self.card_pay_method.reg_no
            }, 
            {
                'name': self.points_pay_method.name, 
                'reg_no': self.points_pay_method.reg_no
            }, 
            {
                'name': self.debt_pay_method.name, 
                'reg_no': self.debt_pay_method.reg_no
            }, 
            {
                'name': self.other_pay_method.name, 
                'reg_no': self.other_pay_method.reg_no
            }
        ]

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """

        receipts = Receipt.objects.all().order_by('id')

        payload = {
            'tims_data': [
                {
                    'receipt_number': receipts[0].receipt_number,
                    'tims_cu_serial_number': 'KRAMW004202110009550 11.08.2022 12\\:11\\:10',
                    'tims_cu_invoice_number': '0040095500000000001',
                    'tims_verification_url': 'https\\://itax.kra.go.ke/KRA-Portal/invoiceChk.htm?actionCode=loadPage&invoiceNo=0040095500000000001',
                    'tims_description': 'Signed successfully.'
                },
                {
                    'receipt_number': receipts[1].receipt_number,
                    'tims_cu_serial_number': 'KRAMW004202110009551 11.08.2022 12\\:11\\:10',
                    'tims_cu_invoice_number': '0040095500000000002',
                    'tims_verification_url': 'https\\://itax.kra.go.ke/KRA-Portal/invoiceChk.htm?actionCode=loadPage&invoiceNo=0040095500000000002',
                    'tims_description': 'Signed successfully.'
                },
                {
                    'receipt_number': receipts[2].receipt_number,
                    'tims_cu_serial_number': 'KRAMW004202110009552 11.08.2022 12\\:11\\:10',
                    'tims_cu_invoice_number': '0040095500000000003',
                    'tims_verification_url': 'https\\://itax.kra.go.ke/KRA-Portal/invoiceChk.htm?actionCode=loadPage&invoiceNo=0040095500000000003',
                    'tims_description': 'Signed successfully.'
                },
                {
                    'receipt_number': receipts[3].receipt_number,
                    'tims_cu_serial_number': 'KRAMW004202110009553 11.08.2022 12\\:11\\:10',
                    'tims_cu_invoice_number': '0040095500000000004',
                    'tims_verification_url': 'https\\://itax.kra.go.ke/KRA-Portal/invoiceChk.htm?actionCode=loadPage&invoiceNo=0040095500000000004',
                    'tims_description': 'Signed successfully.'
                },
            ]
        }

        return payload

    def test_view_can_update_a_multiple_receipt_successfully(self):

        payload = self.get_premade_payload()

        # Confirm data before updating
        receipts = Receipt.objects.all().order_by('id')
        for index, receipt in enumerate(receipts):
            self.assertEqual(
                receipt.receipt_number, 
                payload['tims_data'][index]['receipt_number']
            )
            self.assertEqual(receipt.tims_cu_serial_number, '')
            self.assertEqual(receipt.tims_cu_invoice_number, '')
            self.assertEqual(receipt.tims_verification_url, '')
            self.assertEqual(receipt.tims_description, '')
            self.assertEqual(receipt.tims_success, False)


        # Count Number of Queries #
        # with self.assertNumQueries(13):
        response = self.client.post(
            reverse('api:tims-receipt-update'), 
            payload
        )
        self.assertEqual(response.status_code, 200)


        # Confirm data after updating
        receipts = Receipt.objects.all().order_by('id')
        for index, receipt in enumerate(receipts):
            self.assertEqual(
                receipt.receipt_number, 
                payload['tims_data'][index]['receipt_number']
            )
            self.assertEqual(
                receipt.tims_cu_serial_number, 
                payload['tims_data'][index]['tims_cu_serial_number']
            )
            self.assertEqual(
                receipt.tims_cu_invoice_number, 
                payload['tims_data'][index]['tims_cu_invoice_number']
            )
            self.assertEqual(
                receipt.tims_verification_url, 
                payload['tims_data'][index]['tims_verification_url']
            )
            self.assertEqual(
                receipt.tims_description, 
                payload['tims_data'][index]['tims_description']
            )
            self.assertEqual(receipt.tims_success, True)

    def test_if_view_wont_save_receipts_that_have_a_wrong_receipt_number(self):

        payload = self.get_premade_payload()

        # Confirm data before updating
        receipts = Receipt.objects.all().order_by('id')
        for index, receipt in enumerate(receipts):
            self.assertEqual(
                receipt.receipt_number, 
                payload['tims_data'][index]['receipt_number']
            )
            self.assertEqual(receipt.tims_cu_serial_number, '')
            self.assertEqual(receipt.tims_cu_invoice_number, '')
            self.assertEqual(receipt.tims_verification_url, '')
            self.assertEqual(receipt.tims_description, '')
            self.assertEqual(receipt.tims_success, False)


        # Change the receipt number to a wrong one
        payload['tims_data'][0]['receipt_number'] = 'wrong receipt number'

        # Count Number of Queries #
        # with self.assertNumQueries(13):
        response = self.client.post(
            reverse('api:tims-receipt-update'), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        # Confirm data after updating
        receipts = Receipt.objects.all().order_by('id')
        for index, receipt in enumerate(receipts):

            if index == 0:
                self.assertEqual(receipt.tims_cu_serial_number, '')
                self.assertEqual(receipt.tims_cu_invoice_number, '')
                self.assertEqual(receipt.tims_verification_url, '')
                self.assertEqual(receipt.tims_description, '')
                self.assertEqual(receipt.tims_success, False)
            
            else:

                self.assertEqual(
                    receipt.receipt_number, 
                    payload['tims_data'][index]['receipt_number']
                )
                self.assertEqual(
                    receipt.tims_cu_serial_number, 
                    payload['tims_data'][index]['tims_cu_serial_number']
                )
                self.assertEqual(
                    receipt.tims_cu_invoice_number, 
                    payload['tims_data'][index]['tims_cu_invoice_number']
                )
                self.assertEqual(
                    receipt.tims_verification_url, 
                    payload['tims_data'][index]['tims_verification_url']
                )
                self.assertEqual(
                    receipt.tims_description, 
                    payload['tims_data'][index]['tims_description']
                )
                self.assertEqual(receipt.tims_success, True)
        
    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tims-receipt-update'))
        self.assertEqual(response.status_code, 401)
