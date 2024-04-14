import yaml
import json

from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.cache import cache
from django.urls import reverse
from django.conf import settings

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from core.test_utils.create_store_models import create_new_store

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.create_user import (
    create_new_user, 
    create_new_manager_user, 
    create_new_cashier_user
)
from core.test_utils.log_reader import get_log_content
from core.test_utils.initial_user_data import InitialUserDataMixin

from accounts.utils.currency_choices import KSH, USD
from firebase.models import FirebaseDevice

from mylogentries.models import UserActivityLog, CREATED
from accounts.models import User
from mysettings.models import MySetting
from profiles.models import LoyaltySetting, Profile
from accounts.utils.user_type import TOP_USER
from stores.models import Store, StorePaymentMethod

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

        self.create_initial_user_data()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

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
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.CASH_TYPE
        )
        mpesa = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.MPESA_TYPE
        )
        card = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.CARD_TYPE
        )
        points = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.POINTS_TYPE
        )
        debt = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.DEBT_TYPE
        )
        other = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
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

    def test_if_TokenView_is_working_for_top_user(self):

        data = {
            'username': 'john@gmail.com',
            'password': 'secretpass',
        }

        response = self.client.post(reverse('api:token'), data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.top_profile1.user.is_active, True)

        token = Token.objects.get(user__email=data['username'])

        loyalty_value = LoyaltySetting.objects.get(profile=self.top_profile1).value

        result = {
            'email': self.top_profile1.user.email,
            'name': self.top_profile1.user.get_full_name(),
            'token': token.key,
            'user_type': self.top_profile1.user.user_type,
            'reg_no': self.top_profile1.user.reg_no,
            'profile_image_url': self.top_profile1.user.get_profile_image_url(),
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

        response = self.client.post(reverse('api:token'), data, format='json')

        self.assertEqual(response.status_code, 503)

    def test_if_TokenView_wont_work_when_user_is_not_active(self):

        u = User.objects.get(email='john@gmail.com')
        u.is_active = False
        u.save()

        data = {
            'username': 'john@gmail.com',
            'password': 'secretpass',
        }

        response = self.client.post(reverse('api:token'), data, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'non_field_errors': [
            'Unable to log in with provided credentials.']}
        self.assertEqual(response.data, result)

    def test_if_normal_view_does_not_return_error_if_user_has_an_active_device(self):

        FirebaseDevice.objects.update(is_current_active = True)
       
        data = {
            'username': 'john@gmail.com',
            'password': 'secretpass',
        }

        response = self.client.post(reverse('api:token'), data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.top_profile1.user.is_active, True)

    def test_if_pos_view_returns_error_if_user_has_an_active_device(self):

        FirebaseDevice.objects.update(is_current_active = True)
       
        data = {
            'username': 'john@gmail.com',
            'password': 'secretpass',
        }

        response = self.client.post(reverse('api:token_pos'), data, format='json')

        self.assertEqual(response.status_code, 412)
        self.assertEqual(self.top_profile1.user.is_active, True)

    def test_if_pos_view_does_not_return_error_if_user_does_not_have_an_active_device(self):

        FirebaseDevice.objects.update(is_current_active = False)
       
        data = {
            'username': 'john@gmail.com',
            'password': 'secretpass',
        }

        response = self.client.post(reverse('api:token_pos'), data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.top_profile1.user.is_active, True)

    def test_TokenView_with_empty_email(self):

        data = {
            'username': '',
            'password': 'secretpass',
        }

        response = self.client.post(reverse('api:token'), data, format='json')

        self.assertEqual(response.status_code, 400)

        result = {'username': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

    def test_TokenView_with_wrong_email(self):

        data = {
            'username': 'wrong@gmail.com',
            'password': 'secretpass',
        }

        response = self.client.post(reverse('api:token'), data, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'non_field_errors': [
            'Unable to log in with provided credentials.']}
        self.assertEqual(response.data, result)

    def test_TokenView_with_wrong_password(self):

        data = {
            'username': 'john@gmail.com',
            'password': 'yunggodfdfd',
        }

        response = self.client.post(reverse('api:token'), data, format='json')

        self.assertEqual(response.status_code, 400)

        result = {'non_field_errors': [
            'Unable to log in with provided credentials.']}
        self.assertEqual(response.data, result)

    def test_TokenView_with_empty_password(self):

        data = {
            'username': 'john@gmail.com',
            'password': '',
        }

        response = self.client.post(reverse('api:token'), data, format='json')

        self.assertEqual(response.status_code, 400)

        result = {'password': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

    def test_if_TokenView_is_throttling_logins(self):

        data = {
            'username': 'john@gmail.com',
            'password': 'secretpass',
        }

        # Make sure the first requests are not throttled
        throttle_rate = int(
            settings.THROTTLE_RATES['api_token_rate'].split("/")[0])
        for i in range(throttle_rate):  # pylint: disable=unused-variable
            response = self.client.post(
                reverse('api:token'), data, format='json')
            self.assertEqual(response.status_code, 200)

        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional
        # request if the previous request was not throttled
        for i in range(throttle_rate):  # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:token'), data, format='json')

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else:
            # Executed because break was not called. This means the request was
            # never throttled
            self.fail()

        result = {
            'detail': 'Request was throttled. Expected available in 1 second.'}
        self.assertEqual(response.data, result)

        # Test if throttled views will be logged #
        content = get_log_content()

        self.assertTrue(len(content) >= int(throttle_rate)+1)

        data = content[len(content)-1]

        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/api/api-token-auth/')
        self.assertEqual(data['status_code'], '429')
        self.assertEqual(data['process'], 'Request_throttled')

    def test_if_TokenView_is_throttling_ip(self):

        emails = [get_random_string(10) + '@gmail.com' for i in range(10)]

        # Make sure the first requests are not throttled
        throttle_rate = int(
            settings.THROTTLE_RATES['login_rate'].split("/")[0])
        for i in range(throttle_rate):  # pylint: disable=unused-variable
            data = {
                'username': emails[i],
                'password': 'secretpass',
            }

            response = self.client.post(
                reverse('api:token'), data, format='json')
            self.assertEqual(response.status_code, 400)

        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional
        # request if the previous request was not throttled
        for i in range(throttle_rate):  # pylint: disable=unused-variable

            data = {
                'username': get_random_string(10) + '@gmail.com',
                'password': 'secretpass',
            }

            # Ensure next request return 429(Too many requests) #
            response = self.client.post(
                reverse('api:token'), data, format='json')

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else:
            # Executed because break was not called. This means the request was
            # never throttled
            self.fail()

        result = {
            'detail': 'Request was throttled. Expected available in 1 second.'}
        self.assertEqual(response.data, result)

        # Test if throttled views will be logged #
        content = get_log_content()

        self.assertTrue(len(content) >= int(throttle_rate)+1)

        data = content[len(content)-1]

        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/api/api-token-auth/')
        self.assertEqual(data['status_code'], '429')
        self.assertEqual(data['process'], 'Request_throttled')

class LogoutViewForTopUserTestCase(APITestCase, InitialUserDataMixin):
    # Test if TokenView urls  #
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

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # My client #
        # Include an appropriate `Authorization:` header on all requests.
        token1 = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token1.key)

        # Make sure user has been logged in
        response = self.client.get(reverse('api:tp_edit_profile'))
        self.assertEqual(response.status_code, 200)

        # Create user FirebaseDevice
        FirebaseDevice.objects.create(
            user = self.top_profile1.user,
            store=self.store1,
            token=token1,
            last_login_date =timezone.now()
        )

    def test_if_logout_is_working(self):

        # Include an appropriate `Authorization:` header on all requests.
        token1 = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token1.key)

        response = self.client.get(reverse('api:logout'))
        self.assertEqual(response.status_code, 200)

        token2 = Token.objects.get(user__email='john@gmail.com')

        # Make sure the user's token was not regenerated
        self.assertEqual(token1 == token2, True)

        # Check active firebase has not been marked as in active
        self.assertEqual(FirebaseDevice.objects.get().is_current_active, True)

    def test_if_logout_pos_is_working(self):

        # Include an appropriate `Authorization:` header on all requests.
        token1 = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token1.key)

        response = self.client.get(reverse('api:logout_pos'))
        self.assertEqual(response.status_code, 200)

        token2 = Token.objects.get(user__email='john@gmail.com')

        # Make sure the user's token was not regenerated
        self.assertEqual(token1 == token2, True)

        # Check active firebase has not been marked as in active
        self.assertEqual(FirebaseDevice.objects.get().is_current_active, False)

    def test_if_logout_everywhere_is_working(self):

        # Include an appropriate `Authorization:` header on all requests.
        token1 = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token1.key)

        response = self.client.get(reverse('api:logout_everywhere'))
        self.assertEqual(response.status_code, 200)

        token2 = Token.objects.get(user__email='john@gmail.com')

        # Make sure the user's token was regenerated
        self.assertEqual(token1 == token2, False)

        # Make sure the user was logged out
        response = self.client.get(reverse('api:tp_edit_profile'))
        self.assertEqual(response.status_code, 401)

        # Check active firebase has not been marked as in active
        self.assertEqual(FirebaseDevice.objects.get().is_current_active, False)

    def test_if_LogoutView_is_not_working_for_unloggedin_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:logout'))
        self.assertEqual(response.status_code, 401)

class PasswordChangeViewForTopUserTestCase(APITestCase, InitialUserDataMixin):
    # Test if TokenView urls  #
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

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_if_PasswordChangeView_can_change_a_password(self):

        payload = {
            "old_password": "secretpass",
            "new_password1": "new_person",
            "new_password2": "new_person"
        }

        # get original token
        token1 = Token.objects.get(user__email='john@gmail.com')

        # confirm password before changing
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(payload['old_password']), True)
        self.assertEqual(user.check_password(payload['new_password1']), False)

        # change password
        response = self.client.post(
            reverse('api:password_change'), payload, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data, {'detail': 'New password has been saved.'})

        # check if password was changed
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(payload['old_password']), False)
        self.assertEqual(user.check_password(payload['new_password1']), True)

        # Make sure the user's token was regenerated
        token2 = Token.objects.get(user__email='john@gmail.com')
        self.assertEqual(token1 == token2, False)

    def test_if_PasswordChangeView_wont_work_if_old_password_is_wrong(self):

        payload = {
            "old_password": "wrong_old_pass",
            "new_password1": "new_person",
            "new_password2": "new_person"
        }

        # get original token
        token1 = Token.objects.get(user__email='john@gmail.com')

        # try change password
        response = self.client.post(
            reverse('api:password_change'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'old_password': [
            'Your old password was entered incorrectly. Please enter it again.']}
        self.assertEqual(response.data, result)

        # check if password was not changed
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password('secretpass'), True)
        self.assertEqual(user.check_password(payload['new_password1']), False)

        # Make sure the user's token was not regenerated
        token2 = Token.objects.get(user__email='john@gmail.com')
        self.assertEqual(token1 == token2, True)

    def test_if_PasswordChangeView_wont_work_if_new_passwords_dont_match(self):

        payload = {
            "old_password": "secretpass",
            "new_password1": "new_person1",
            "new_password2": "new_person2"
        }

        # get original token
        token1 = Token.objects.get(user__email='john@gmail.com')

        # try change password
        response = self.client.post(
            reverse('api:password_change'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        json_result = json.loads(json.dumps(response.data))['new_password2']

        self.assertEqual(
            json_result, ["The two password fields didn’t match."])

        # check if password was not changed
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(payload['old_password']), True)
        self.assertEqual(user.check_password(payload['new_password1']), False)

        # Make sure the user's token was not regenerated
        token2 = Token.objects.get(user__email='john@gmail.com')
        self.assertEqual(token1 == token2, True)

    def test_if_PasswordChangeView_wont_work_if_new_passwords_are_short(self):

        payload = {
            "old_password": "secretpass",
            "new_password1": "short",
            "new_password2": "short"
        }

        # get original token
        token1 = Token.objects.get(user__email='john@gmail.com')

        # try change password
        response = self.client.post(
            reverse('api:password_change'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'new_password2': [
            'This password is too short. It must contain at least 8 characters.']}

        self.assertEqual(response.data, result)

        # Make sure the user's token was not regenerated
        token2 = Token.objects.get(user__email='john@gmail.com')
        self.assertEqual(token1 == token2, True)

    def test_if_PasswordChangeView_is_not_working_for_unlogged_in_users(self):

        # This makes sure the user is not logged in
        self.client = APIClient()

        payload = {
            "old_password": "old_person",
            "new_password1": "new_person",
            "new_password2": "new_person"
        }

        # get original token
        token1 = Token.objects.get(user__email='john@gmail.com')

        response = self.client.post(
            reverse('api:password_change'), payload, format='json')

        self.assertEqual(response.status_code, 401)

        # Make sure the user's token was not regenerated
        token2 = Token.objects.get(user__email='john@gmail.com')
        self.assertEqual(token1 == token2, True)

class SignupView(APITestCase):

    def setUp(self):

        # Create a user with email john@gmail.com
        create_new_user('john')

        # Create a user with email jack@gmail.com
        create_new_user('jack')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

    def get_payment_types(self):

        payload = self.get_premade_payload()

        user = User.objects.get(email=payload['email'])

        profile = Profile.objects.get(user__email=user)

        # Get payments
        cash = StorePaymentMethod.objects.get(
            profile=profile,
            payment_type=StorePaymentMethod.CASH_TYPE
        )
        mpesa = StorePaymentMethod.objects.get(
            profile=profile,
            payment_type=StorePaymentMethod.MPESA_TYPE
        )
        card = StorePaymentMethod.objects.get(
            profile=profile,
            payment_type=StorePaymentMethod.CARD_TYPE
        )
        points = StorePaymentMethod.objects.get(
            profile=profile,
            payment_type=StorePaymentMethod.POINTS_TYPE
        )
        debt = StorePaymentMethod.objects.get(
            profile=profile,
            payment_type=StorePaymentMethod.DEBT_TYPE
        )
        other = StorePaymentMethod.objects.get(
            profile=profile,
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

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """

        payload = {
            "first_name": "Ben",
            "last_name": "Linus",
            "email": "linus@gmail.com",
            "phone": "254723223322",
            'business_name': "Skypac",
            "location": "Nairobi",
            "currency": KSH,
            "gender": 0,
            "password": "secretpass"
        }

        return payload

    def test_if_SignupView_can_create_a_new_user(self):

        payload = self.get_premade_payload()

        response = self.client.post(
            reverse('api:signup'), payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 3)

        user = User.objects.get(email=payload['email'])
        token = Token.objects.get(user=user)

        loyalty_value = LoyaltySetting.objects.get(profile=user.profile).value

        result = {
            'email': user.email,
            'name': user.get_full_name(),
            'token': token.key,
            'user_type': user.user_type,
            'reg_no': user.reg_no,
            'profile_image_url': user.get_profile_image_url(),
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

        # Confirm user details
        self.assertEqual(user.first_name, 'Ben')
        self.assertEqual(user.last_name, 'Linus')
        self.assertEqual(user.email, 'linus@gmail.com')
        self.assertEqual(user.phone, 254723223322)
        self.assertEqual(user.user_type, TOP_USER)
        self.assertEqual(user.gender, 0)
        self.assertEqual(user.is_active, True)
        self.assertEqual(user.is_staff, False)

        # Confirm if profile business name and location
        profile = Profile.objects.get(user__email=user)

        self.assertEqual(profile.business_name, 'Skypac')
        self.assertEqual(profile.location, 'Nairobi')
        self.assertEqual(profile.currency, USD)

        # Confirm Store models creation
        self.assertEqual(Store.objects.all().count(), 1)

        store = Store.objects.get(name=settings.DEFAULT_STORE_NAME)

        self.assertEqual(store.profile ,profile)
        self.assertEqual(store.name, settings.DEFAULT_STORE_NAME)
        self.assertEqual(store.address, payload['location'])

        ########################## UserActivityLog ##############################'#
        # Confirm that the created user was logged correctly

        log = UserActivityLog.objects.get(user__email='linus@gmail.com')

        self.assertEqual(
            log.change_message, 'New User "linus@gmail.com" has been created by "linus@gmail.com"')
        self.assertEqual(log.object_id, str(user.pk))
        self.assertEqual(log.object_repr, 'linus@gmail.com')
        self.assertEqual(log.content_type.model, 'user')
        self.assertEqual(log.user.email, 'linus@gmail.com')
        self.assertTrue(len(log.ip) > 7)
        self.assertEqual(log.action_type, CREATED)
        self.assertEqual(log.owner_email, '')
        self.assertEqual(log.panel, 'Api')

        self.assertEqual(UserActivityLog.objects.all().count(), 1)

        ########################## Test Logging ##############################'#
        # Confirm that the request was logged correctly in a file

        content = get_log_content()

        self.assertEqual(len(content), 1)

        data = content[0]

        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/api/signup/')
        self.assertEqual(data['status_code'], '201')

    def test_if_SignupView_cant_accept_empty_first_name(self):

        payload = self.get_premade_payload()
        payload['first_name'] = ''

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        # Check error key
        self.assertEqual(len(response.data['first_name']), 1)

        result = {'first_name': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

    def test_if_SignupView_cant_accept_empty_last_name(self):

        payload = self.get_premade_payload()
        payload['last_name'] = ''

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(len(response.data['last_name']), 1)  # Check error key

        result = {'last_name': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

    def test_if_SignupView_cant_accept_empty_email(self):

        payload = self.get_premade_payload()
        payload['email'] = ''

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'email': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

    def test_if_SignupView_cant_accept_a_wrong_format_email(self):

        payload = self.get_premade_payload()
        payload['email'] = 'wrongformatemail'

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'email': ['Enter a valid email address.']}
        self.assertEqual(response.data, result)

    def test_if_SignupView_cant_accept_long_email(self):

        long_email = "{}@gmail.com".format("x"*90)

        payload = self.get_premade_payload()
        payload['email'] = long_email

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {
            'email': ['Ensure this field has no more than 30 characters.']}
        self.assertEqual(response.data, result)

    def test_if_SignupView_cant_accept_non_unqiue_email(self):

        # Try to signup with emails from existing users

        top_profile = Profile.objects.get(user__email='john@gmail.com')

        store = create_new_store(top_profile, 'Computer Store')

        # Create 2 supervisor users
        create_new_manager_user("gucci", top_profile, store)
        create_new_manager_user("lewis", top_profile, store)

        # Create 2 team users
        create_new_cashier_user("james", top_profile, store)
        create_new_cashier_user("ben", top_profile, store)

        # Get users emails
        top_user1_email = User.objects.get(email='john@gmail.com').email
        top_user2_email = User.objects.get(email='jack@gmail.com').email

        supervisor_user1_email = User.objects.get(
            email='gucci@gmail.com').email
        supervisor_user2_email = User.objects.get(
            email='lewis@gmail.com').email

        team_user1_email = User.objects.get(email='james@gmail.com').email
        team_user2_email = User.objects.get(email='ben@gmail.com').email

        user_emails = [top_user1_email,
                       top_user2_email,
                       supervisor_user1_email,
                       supervisor_user2_email,
                       team_user1_email, team_user2_email]

        i = 0
        for email in user_emails:

            # Clear cache before every new request
            cache.clear()

            payload = self.get_premade_payload()
            payload['email'] = email

            response = self.client.post(
                reverse('api:signup'), payload, format='json')
            self.assertEqual(response.status_code, 400)

            result = {'email': ['User with this Email already exists.']}
            self.assertEqual(response.data, result)

            i += 1

        # Confirm how many times the loop ran
        self.assertEqual(i, 6)

    def test_for_successful_SignupView_with_correct_phones(self):

        emails = [get_random_string(10) + '@gmail.com' for i in range(8)]
        phones = [
            '254700223322',
            '254709223322',
            '254711223322',
            '254719223322',
            '254720223327',
            '254729223322',
            '254790223322',
            '254799223322',
        ]

        i = 0
        for phone in phones:

            # Clear cache before every new request
            cache.clear()

            payload = self.get_premade_payload()
            payload['email'] = emails[i]
            payload['phone'] = phone

            response = self.client.post(
                reverse('api:signup'), payload, format='json')
            self.assertEqual(response.status_code, 201)

            i += 1

        self.assertEqual(User.objects.count(), 10)

    def test_if_SignupView_cant_accept_an_empty_phone(self):

        payload = self.get_premade_payload()
        payload['phone'] = ''

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 2)

        result = {'phone': ['A valid integer is required.']}
        self.assertEqual(response.data, result)

    def test_if_a_user_cant_signup_with_a_non_unique_phone(self):

        # Try to signup with phones from existing users

        top_profile = Profile.objects.get(user__email='john@gmail.com')

        store = create_new_store(top_profile, 'Computer Store')

        # Creat 2 supervisor user
        create_new_manager_user("gucci", top_profile, store)
        create_new_manager_user("lewis", top_profile, store)

        # Creat 2 team users
        create_new_cashier_user("james", top_profile, store)
        create_new_cashier_user("ben", top_profile, store)

        # Get users phones
        top_user1_phone = User.objects.get(email='john@gmail.com').phone
        top_user2_phone = User.objects.get(email='jack@gmail.com').phone

        supervisor_user1_phone = User.objects.get(
            email='gucci@gmail.com').phone
        supervisor_user2_phone = User.objects.get(
            email='lewis@gmail.com').phone

        team_user1_phone = User.objects.get(email='james@gmail.com').phone
        team_user2_phone = User.objects.get(email='ben@gmail.com').phone

        user_phones = [
            top_user1_phone,
            top_user2_phone,
            supervisor_user1_phone,
            supervisor_user2_phone,
            team_user1_phone,
            team_user2_phone
        ]

        i = 0
        for phone in user_phones:

            # Clear cache before every new request
            cache.clear()

            payload = self.get_premade_payload()
            payload['phone'] = phone

            response = self.client.post(
                reverse('api:signup'), payload, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(User.objects.count(), 6)

            result = {'phone': ['User with this phone already exists.']}
            self.assertEqual(response.data, result)

            i += 1

        # Confirm how many times the loop ran
        self.assertEqual(i, 6)

    def test_if_a_user_cant_signup_with_a_wrong_phone(self):

        phones = [
            '25470022332j',  # Number with letters
            '2547112233222',  # Long Number
            '25471122332',  # Short Number
            '254711223323333333333333333333333333333333',   # long Number
        ]

        i = 0
        for phone in phones:
            # Clear cache before every new request so that throttling does not work
            cache.clear()

            payload = self.get_premade_payload()
            payload['phone'] = phone

            response = self.client.post(
                reverse('api:signup'), payload, format='json')
            self.assertEqual(response.status_code, 400)

            self.assertEqual(len(response.data['phone']), 1)  # Check error key

            if i == 1 or i == 3:
                result = {'phone': ['This phone is too long.']}
                self.assertEqual(response.data, result)

            elif i == 2:
                result = {'phone': ['This phone is too short.']}
                self.assertEqual(response.data, result)

            else:
                result = {'phone': ['A valid integer is required.']}
                self.assertEqual(response.data, result)

            i += 1

        self.assertEqual(i, 4)

    def test_if_a_user_cant_signup_with_an_empty_business_name(self):

        payload = self.get_premade_payload()
        payload['business_name'] = ''

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 2)

        result = {'business_name': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

    def test_if_a_user_cant_signup_with_an_empty_location(self):

        payload = self.get_premade_payload()
        payload['location'] = ''

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 2)

        result = {'location': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

    def test_if_a_user_cant_signup_with_an_empty_gender(self):

        payload = self.get_premade_payload()
        payload['gender'] = ''

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 2)

        result = {'gender': ['"" is not a valid choice.']}
        self.assertEqual(response.data, result)

    def test_SignupView_with_short_password(self):

        payload = self.get_premade_payload()
        payload['password'] = 'short'

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 2)

        result = {'password': [
            'Ensure this field has at least 8 characters.']}
        self.assertEqual(response.data, result)

        ########################## Test Logging ##############################'#
        # Confirm that the created was logged correctly in a file

        content = get_log_content()

        self.assertEqual(len(content), 1)

        data = content[0]

        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/api/signup/')
        self.assertEqual(data['status_code'], '400')

        self.assertEqual(data['process'].split('<=>')[0], 'login_invalid')
        self.assertEqual(data['process'].split('<=>')[
                         1], "form_invalid{'password': [ErrorDetail(string='Ensure this field has at least 8 characters.', code='min_length')]}")

        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['first_name'], 'Ben')

        # Make sure passwords are not logged and are changed to "*********"
        self.assertEqual(process_dict['password'], '*********')

    def test_SignupView_with_an_empty_password(self):
        
        payload = self.get_premade_payload()
        payload['password'] = ''

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'password': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

    def test_SignupView_cant_accept_long_password(self):

        long_password = "{}password".format("x"*60)

        payload = self.get_premade_payload()
        payload['password'] = long_password

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'password': [
            'Ensure this field has no more than 50 characters.']}
        self.assertEqual(response.data, result)

    def test_if_SignupView_when_maintenance_is_on(self):
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        payload = self.get_premade_payload()

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 503)

    def test_if_SignupView_when_new_signups_is_false(self):
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.signups = False
        ms.save()

        payload = self.get_premade_payload()

        response = self.client.post(
            reverse('api:signup'), payload, format='json')
        self.assertEqual(response.status_code, 423)

    def test_if_SignupView_can_throttle(self):

        emails = [get_random_string(10) + '@gmail.com' for i in range(10)]
        phone = '25472322332'

        # Make sure the first requests are not throttled
        throttle_rate = int(
            settings.THROTTLE_RATES['signup_rate'].split("/")[0])
        for i in range(throttle_rate):  # pylint: disable=unused-variable

            payload = self.get_premade_payload()
            payload['email'] = emails[i]
            payload['phone'] = phone + str(i)  # This ensures unique phone

            response = self.client.post(
                reverse('api:signup'), payload, format='json')
            self.assertEqual(response.status_code, 201)

        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional
        # request if the previous request was not throttled
        for i in range(throttle_rate):  # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:signup'), payload, format='json')

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else:
            # Executed because break was not called. This means the request was
            # never throttled
            self.fail()

        # Test if throttled views will be logged #
        content = get_log_content()

        self.assertEqual(len(content), int(throttle_rate)+1)

        data = content[int(throttle_rate)]

        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/api/signup/')
        self.assertEqual(data['status_code'], '429')
        self.assertEqual(data['process'], 'Request_throttled')


class TokenViewAndSignupViewThrottleTestCase(APITestCase):
    def setUp(self):

        # Create a user with email john@gmail.com
        self.user = create_new_user('john')

        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

    def test_if_TokenView_and_SignupView_do_not_share_the_same_cache_name(self):

        emails = [get_random_string(10) + '@gmail.com' for i in range(10)]

        token_throttle_rate = int(
            settings.THROTTLE_RATES['login_rate'].split("/")[0])
        for i in range(token_throttle_rate):
            payload = {'username': emails[i],
                       'password': 'secretpass',
                       }

            self.client.post(reverse('api:token'), payload, format='json')

        signup_throttle_rate = int(
            settings.THROTTLE_RATES['signup_rate'].split("/")[0])
        for i in range(signup_throttle_rate):

            payload = {
                "first_name": "Ben",
                "last_name": "Linus",
                'email': emails[i],
                "phone": "254723223322",
                'business_name': "Skypac",
                "location": "Nairobi",
                'currency': KSH,
                "gender": 0,
                "password": "secretpass"
            }

            response = self.client.post(
                reverse('api:signup'), payload, format='json')

            self.assertEqual(response.status_code, 503)


class ContactViewForTopUserTestCase(APITestCase, InitialUserDataMixin):

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

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Make sure user has been logged in
        response = self.client.get(reverse('api:tp_edit_profile'))
        self.assertEqual(response.status_code, 200)

    def test_if_ContactView_is_working(self):

        payload = {
            'phone': "254723223322",
            'email': 'example@gmail.com',
            'business_name': "Skypac",
            'message': 'Hey admin',
        }

        response = self.client.post(
            reverse('api:contact'), payload, format='json')
        self.assertEqual(response.status_code, 200)

        result = {'message': 'Message sent succesfully'}
        self.assertEqual(response.data, result)

    def test_if_ContactView_cant_accept_an_empty_phone(self):

        payload = {
            'phone': "",
            'email': 'example@gmail.com',
            'business_name': "Skypac",
            'message': 'Hey admin',
        }

        response = self.client.post(
            reverse('api:contact'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'phone': ['A valid integer is required.']}
        self.assertEqual(response.data, result)

    def test_if_a_user_cant_contact_with_a_wrong_phone(self):

        phones = [
            '25470022332j',  # Number with letters
            '2547112233222',  # Long Number
            '25471122332',  # Short Number
            '254711223323333333333333333333333333333333',   # long Number
        ]

        i = 0
        for phone in phones:
            # Clear cache before every new request so that throttling does not work
            cache.clear()

            payload = {
                'phone': phone,
                'email': 'example@gmail.com',
                'business_name': "Skypac",
                'message': 'Hey admin',
            }

            response = self.client.post(
                reverse('api:contact'), payload, format='json')
            self.assertEqual(response.status_code, 400)

            self.assertEqual(len(response.data['phone']), 1)  # Check error key

            if i == 1 or i == 3:
                result = {'phone': ['This phone is too long.']}
                self.assertEqual(response.data, result)

            elif i == 2:
                result = {'phone': ['This phone is too short.']}
                self.assertEqual(response.data, result)

            else:
                result = {'phone': ['A valid integer is required.']}
                self.assertEqual(response.data, result)

            i += 1

        self.assertEqual(i, 4)

    def test_if_contact_cant_accept_empty_email(self):

        payload = {
            'phone': "254723223322",
            'email': '',
            'business_name': "Skypac",
            'message': 'Hey admin',
        }

        response = self.client.post(
            reverse('api:contact'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'email': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

    def test_if_ContactView_cant_accept_a_wrong_format_email(self):

        payload = {
            'phone': "254723223322",
            'email': 'wrongformatemail',
            'business_name': "Skypac",
            'message': 'Hey admin',
        }

        response = self.client.post(
            reverse('api:contact'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'email': ['Enter a valid email address.']}
        self.assertEqual(response.data, result)

    def test_if_ContactView_cant_accept_long_email(self):

        long_email = "{}@gmail.com".format("x"*90)

        payload = {
            'phone': "254723223322",
            'email': long_email,
            'business_name': "Skypac",
            'message': 'Hey admin',
        }

        response = self.client.post(
            reverse('api:contact'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {
            'email': ['Ensure this field has no more than 30 characters.']}
        self.assertEqual(response.data, result)

    def test_if_a_user_cant_contact_with_an_empty_business_name(self):

        payload = {
            'phone': "254723223322",
            'email': 'example@gmail.com',
            'business_name': "",
            'message': 'Hey admin',
        }

        response = self.client.post(
            reverse('api:contact'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'business_name': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

    def test_if_ContactView_wont_accept_an_empty_message(self):

        payload = {
            'phone': "254723223322",
            'email': 'example@gmail.com',
            'business_name': "Skypac",
            'message': '',
        }

        response = self.client.post(
            reverse('api:contact'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'message': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

    def test_if_ContactView_cant_accept_long_messasge(self):

        long_message = "{} message".format('x'*500)

        payload = {
            'phone': "254723223322",
            'email': 'example@gmail.com',
            'business_name': "Skypac",
            'message': long_message,
        }

        response = self.client.post(
            reverse('api:contact'), payload, format='json')
        self.assertEqual(response.status_code, 400)

        result = {'message': [
            'Ensure this field has no more than 500 characters.']}
        self.assertEqual(response.data, result)

    def test_if_ContactView_is_unsuccessful_when_maintenace_is_True(self):
        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        payload = {
            'phone': "254723223322",
            'email': 'example@gmail.com',
            'business_name': "Skypac",
            'message': 'Hey admin',
        }

        response = self.client.post(
            reverse('api:contact'), payload, format='json')
        self.assertEqual(response.status_code, 401)

    def test_if_ContactView_is_unsuccessful_when_allow_contact_is_False(self):
        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.allow_contact = False
        ms.save()

        payload = {
            'phone': "254723223322",
            'email': 'example@gmail.com',
            'business_name': "Skypac",
            'message': 'Hey admin',
        }

        response = self.client.post(
            reverse('api:contact'), payload, format='json')
        self.assertEqual(response.status_code, 423)

    def test_if_ContactView_is_working_for_unlogged_in(self):

        # Unlogged in user
        self.client = APIClient()

        payload = {
            'phone': "254723223322",
            'email': 'example@gmail.com',
            'business_name': "Skypac",
            'message': 'Hey admin',
        }

        response = self.client.post(
            reverse('api:contact'), payload, format='json')
        self.assertEqual(response.status_code, 200)

    def test_if_ContactView_is_throttling_logged_in_users(self):

        payload = {
            'phone': "254723223322",
            'email': 'example@gmail.com',
            'business_name': "Skypac",
            'message': 'Hey admin',
        }

        throttle_rate = int(
            settings.THROTTLE_RATES['contact_rate'].split("/")[0])
        for i in range(throttle_rate):  # pylint: disable=unused-variable
            response = self.client.post(
                reverse('api:contact'), payload, format='json')
            self.assertEqual(response.status_code, 200)

        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional
        # request if the previous request was not throttled
        for i in range(throttle_rate):  # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:contact'), payload, format='json')

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else:
            # Executed because break was not called. This means the request was
            # never throttled
            self.fail()

        # Test if throttled views will be logged #
        content = get_log_content()

        self.assertTrue(len(content) >= int(throttle_rate)+1)

        data = content[len(content)-1]

        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/api/contact/')
        self.assertEqual(data['status_code'], '429')
        self.assertEqual(data['process'], 'Request_throttled')

    def test_if_ContactView_is_throttling_unlogged_in_users(self):

        # Unlogged in user
        self.client = APIClient()

        payload = {
            'phone': "254723223322",
            'email': 'example@gmail.com',
            'business_name': "Skypac",
            'message': 'Hey admin',
        }

        throttle_rate = int(
            settings.THROTTLE_RATES['contact_rate'].split("/")[0])
        for i in range(throttle_rate):  # pylint: disable=unused-variable
            response = self.client.post(
                reverse('api:contact'), payload, format='json')
            self.assertEqual(response.status_code, 200)

        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional
        # request if the previous request was not throttled
        for i in range(throttle_rate):  # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:contact'), payload, format='json')

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else:
            # Executed because break was not called. This means the request was
            # never throttled
            self.fail()

        # Test if throttled views will be logged #
        content = get_log_content()

        self.assertTrue(len(content) >= int(throttle_rate)+1)

        data = content[len(content)-1]

        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/api/contact/')
        self.assertEqual(data['status_code'], '429')
        self.assertEqual(data['process'], 'Request_throttled')
