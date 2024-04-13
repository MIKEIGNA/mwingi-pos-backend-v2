from django.urls import reverse
from django.utils import timezone

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.initial_user_data import InitialUserDataMixin

from firebase.models import FirebaseDevice
from mysettings.models import MySetting
from profiles.models import LoyaltySetting

from stores.models import StorePaymentMethod


class TokenViewForTopUserTestCase(APITestCase, InitialUserDataMixin):

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

        self.create_initial_user_data_with_superuser()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # My client #
        # Include an appropriate `Authorization:` header on all requests.
        token1 = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token1.key)

        # Create user FirebaseDevice
        FirebaseDevice.objects.create(
            user = self.top_profile1.user,
            store=self.store1,
            token='just simple toekn',
            is_current_active=False,
            last_login_date =timezone.now()
        )

    def get_payment_types(self):

        # Get payments
        cash = StorePaymentMethod.objects.get(
            profile=self.top_profile2,
            payment_type=StorePaymentMethod.CASH_TYPE
        )
        mpesa = StorePaymentMethod.objects.get(
            profile=self.top_profile2,
            payment_type=StorePaymentMethod.MPESA_TYPE
        )
        card = StorePaymentMethod.objects.get(
            profile=self.top_profile2,
            payment_type=StorePaymentMethod.CARD_TYPE
        )
        points = StorePaymentMethod.objects.get(
            profile=self.top_profile2,
            payment_type=StorePaymentMethod.POINTS_TYPE
        )
        debt = StorePaymentMethod.objects.get(
            profile=self.top_profile2,
            payment_type=StorePaymentMethod.DEBT_TYPE
        )
        other = StorePaymentMethod.objects.get(
            profile=self.top_profile2,
            payment_type=StorePaymentMethod.OTHER_TYPE
        )

        return [
            {
                'name': 'Cash', 
                'payment_type': StorePaymentMethod.CASH_TYPE, 
                'reg_no': cash.reg_no
            }, 
            {
                'name': 'Mpesa', 
                'payment_type': StorePaymentMethod.MPESA_TYPE, 
                'reg_no': mpesa.reg_no
            }, 
            {
                'name': 'Card', 
                'payment_type': StorePaymentMethod.CARD_TYPE, 
                'reg_no': card.reg_no
            }, 
            {
                'name': 'Points', 
                'payment_type': StorePaymentMethod.POINTS_TYPE, 
                'reg_no': points.reg_no
            }, 
            {
                'name': 'Debt', 
                'payment_type': StorePaymentMethod.DEBT_TYPE, 
                'reg_no': debt.reg_no
            }, 
            {
                'name': 'Other', 
                'payment_type': StorePaymentMethod.OTHER_TYPE, 
                'reg_no': other.reg_no
            }
        ]

    def test_if_view_is_working_for_user(self):

        # Include an appropriate `Authorization:` header on all requests.
        token1 = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token1.key)

        payload = {'reg_no': self.user2.reg_no}

        response = self.client.post(reverse('api:hijack'), payload, format='json')
        self.assertEqual(response.status_code, 200)

        token2 = Token.objects.get(user__email='jack@gmail.com')
        loyalty_value = LoyaltySetting.objects.get(profile=self.top_profile2).value

        result = {
            'email': self.top_profile2.user.email,
            'name': self.top_profile2.user.get_full_name(),
            'token': token2.key,
            'user_type': self.top_profile2.user.user_type,
            'reg_no': self.top_profile2.user.reg_no,
            'profile_image_url': self.top_profile2.user.get_profile_image_url(),
            'loyalty_value': loyalty_value,
            'general_setting': {
                'enable_shifts': False, 
                'enable_open_tickets': False, 
                'enable_low_stock_notifications': True, 
                'enable_negative_stock_alerts': True
            },
            'user_perms': [ 
                'can_accept_debt', 
                'can_apply_discount', 
                'can_change_general_settings', 
                'can_change_settings', 
                'can_change_taxes', 
                'can_manage_customers', 
                'can_manage_employees', 
                'can_manage_items', 
                'can_manage_open_tickets', 
                'can_open_drawer', 
                'can_refund_sale', 
                'can_reprint_receipt', 
                'can_view_shift_reports', 
                'can_void_open_ticket_items'
            ],
            'payment_types': self.get_payment_types()
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.post(reverse('api:token'), payload, format='json')

        self.assertEqual(response.status_code, 401)

    def test_if_view_can_only_be_viewed_by_a_superuser(self):

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = {'reg_no': self.user2.reg_no}

        response = self.client.post(reverse('api:hijack'), payload, format='json')
        self.assertEqual(response.status_code, 403)

        