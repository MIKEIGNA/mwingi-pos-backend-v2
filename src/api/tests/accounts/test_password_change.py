import datetime

from django.core import mail
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.test import TestCase

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.log_reader import get_log_content
from core.test_utils.initial_user_data import InitialUserDataMixin
from core.token_generator import RandomNumberTokenGenerator, RandomStringTokenGenerator

from accounts.models import ResetPasswordToken, User

from mysettings.models import MySetting

RESET_TOKEN_EXPIRY_TIME = settings.DJANGO_REST_MULTITOKENAUTH_RESET_TOKEN_EXPIRY_TIME
FRONTEND_SITE_NAME = settings.FRONTEND_SITE_NAME


class TokenGeneratorTestCase(TestCase):
    """
    Tests that the token generators work as expected
    """
    def setUp(self):
        pass

    def test_string_token_generator(self):
        token_generator = RandomStringTokenGenerator(min_length=10, max_length=15)

        tokens = []

        # generate 100 tokens
        for _ in range(0, 100):
            tokens.append(token_generator.generate_token())

        # validate that those 100 tokens are unique
        unique_tokens = list(set(tokens))

        self.assertEqual(
            len(tokens), len(unique_tokens), msg="StringTokenGenerator must create unique tokens"
        )
        ################################################################################################################
        # Please note: The above does not guarantee true randomness, it's just a
        # necessity to make sure that we do not return the same token all the 
        # time (by accident)
        ################################################################################################################

        # validate that each token is between 10 and 15 characters
        for token in tokens:
            self.assertGreaterEqual(
                len(token), 10, msg="StringTokenGenerator must create tokens of min. length of 10"
            )
            self.assertLessEqual(
                len(token), 15, msg="StringTokenGenerator must create tokens of max. length of 15"
            )

    def test_number_token_generator(self):
        token_generator = RandomNumberTokenGenerator(min_number=1000000000, max_number=9999999999)

        tokens = []

        # generate 100 tokens
        for i in range(0, 100):
            tokens.append(token_generator.generate_token())

        # validate that those 100 tokens are unique
        unique_tokens = list(set(tokens))

        self.assertEqual(
            len(tokens), len(unique_tokens), msg="RandomNumberTokenGenerator must create unique tokens"
        )
        ################################################################################################################
        # Please note: The above does not guarantee true randomness, it's just a necessity to make sure that we do not
        # return the same token all the time (by accident)
        ################################################################################################################

        # validate that each token is a number between 100000 and 999999
        for token in tokens:
            is_number = False
            try:
                num = int(token)
                is_number = True
            except:
                is_number = False

            self.assertEqual(is_number, True, msg="RandomNumberTokenGenerator must return a number, but returned "
                                                   + token)

            self.assertGreaterEqual(num, 1000000000, msg="RandomNumberTokenGenerator must return a number greater or equal to 1000000000")
            self.assertLess(num, 9999999999, msg="RandomNumberTokenGenerator must return a number less or equal to 9999999999")
            

class ResetPasswordRequestTokenTestCase(APITestCase, InitialUserDataMixin):

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
        ms.maintenance=False
        ms.save()

    def test_if_password_reset_request_is_working_with_valid_email(self):

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # At this point the system will "send" us an email. We can "check" the 
        # subject: 
        self.assertEqual(len(mail.outbox), 1) 
        self.assertEqual(mail.outbox[0].subject, f'Password reset on {FRONTEND_SITE_NAME}') 

        # There should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)

        # Check if key is valid and if it's assigned to top_profile1.user
        token = ResetPasswordToken.objects.get(user=self.top_profile1.user)
        self.assertTrue(len(token.key) >=  10)

    def test_if_password_reset_request_wont_work_when_user_is_not_active(self):

        u = User.objects.get(email=self.top_profile1.user.email)
        u.is_active = False
        u.save()

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # There should be one token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

    def test_if_password_reset_request_is_not_working_with_an_empty_email(self):

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': ""}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 400)

        result = {'email': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

        # There should be no token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

    def test_if_password_reset_request_is_not_working_with_non_existent_email(self):

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': "notexistent@email.com"}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # There should be no token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

    def test_if_multiple_tokens_can_be_created_for_different_users(self):
        
        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        # Create token for top_profile1
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Create token for top_profile2
        data = {'email': self.top_profile2.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Create token for manager_profile1
        data = {'email': self.manager_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Create token for employee_profile1
        data = {'email': self.cashier_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # There should be 4 tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 4)

       
        # Confirm all token keys are unique
        tokens = ResetPasswordToken.objects.all()
        tokens_list = []
        for token in tokens:
            tokens_list.append(token.key)
            self.assertEqual(tokens_list.count(token.key), 1)

    def test_if_ResetPasswordRequestToken_when_maintenance_is_true(self):

        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=True
        ms.save()

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 503)

        # There should be no token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

    def test_if_ResetPasswordRequestToken_is_throttling_request(self):

        data = {'email': self.top_profile1.user.email}

        # Make sure the first requests are not throttled
        throttle_rate = int(settings.THROTTLE_RATES['password_reset_rate'].split("/")[0])
        for i in range(throttle_rate): # pylint: disable=unused-variable
            response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
            self.assertEqual(response.status_code, 200)


        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional 
        # request if the previous request was not throttled 
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(reverse('api:password_reset'), data, format='json')

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
        self.assertEqual(data['full_path'], '/api/password/reset/')
        self.assertEqual(data['status_code'], '429')
        self.assertEqual(data['process'], 'Request_throttled')


class ResetPasswordValidateTokenTestCase(APITestCase, InitialUserDataMixin):

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
        ms.maintenance=False
        ms.save()
    
    def test_if_ResetPasswordValidateToken_can_validate_valid_token(self):

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Get token
        token = ResetPasswordToken.objects.get(user=self.top_profile1.user)

        # Check if token is valid
        data = {'token': token.key}
        
        response = self.client.post(reverse('api:password_validate_token'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=True
        ms.save()
        
        response = self.client.post(reverse('api:password_validate_token'), data, format='json')                                                  
        self.assertEqual(response.status_code, 503)

    def test_if_ResetPasswordValidateToken_will_validate_a_token_just_about_to_expire(self):

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Set token created date just about to expire
        token = ResetPasswordToken.objects.get(user=self.top_profile1.user)
        token.created_date = timezone.now() - datetime.timedelta(hours=RESET_TOKEN_EXPIRY_TIME-1)
        token.save()

        # Check if token is valid
        data = {'token': token.key}
        
        response = self.client.post(reverse('api:password_validate_token'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

    def test_if_ResetPasswordValidateToken_wont_validate_an_expired_token(self):

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Set token created date past last 24 hours
        token = ResetPasswordToken.objects.get(user=self.top_profile1.user)
        token.created_date = timezone.now() - datetime.timedelta(hours=RESET_TOKEN_EXPIRY_TIME)
        token.save()

        # Check if token is invalid
        data = {'token': token.key}
        
        response = self.client.post(reverse('api:password_validate_token'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 404)

    def test_if_ResetPasswordValidateToken_wont_validate_an_invalid_token(self):

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Check if token is valid
        data = {'token': "wrongtoken"}
        
        response = self.client.post(reverse('api:password_validate_token'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 404)

    

   

class ResetPasswordConfirmTestCase(APITestCase, InitialUserDataMixin):

    print('hello')

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
        ms.maintenance=False
        ms.save()

    def test_if_ResetPasswordConfirm_can_change_a_password(self):

        old_password ='secretpass'
        new_password = 'new_password'

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Make a change password request

        # confirm password before changing
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), True)
        self.assertEqual(user.check_password(new_password), False)

        # Get token
        token = ResetPasswordToken.objects.get(user=self.top_profile1.user)

        payload = {"password": new_password, "token": token.key}

        response = self.client.post(reverse('api:password_reset_confirm'), payload, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Confirm password was changed
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), False)
        self.assertEqual(user.check_password(new_password), True)

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

    def test_if_ResetPasswordConfirm_wont_work_if_new_password_is_empty(self):

        old_password ='secretpass'
        new_password = ''

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Make a change password request

        # confirm password before changing
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), True)
        self.assertEqual(user.check_password(new_password), False)

        # Get token
        token = ResetPasswordToken.objects.get(user=self.top_profile1.user)

        payload = {"password": new_password, "token": token.key}

        response = self.client.post(reverse('api:password_reset_confirm'), payload, format='json') 
        self.assertEqual(response.status_code, 400)

        result = {'password': ['This field may not be blank.']}
        self.assertEqual(response.data, result)                                                           
    
        # Confirm password was not changed
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), True)
        self.assertEqual(user.check_password(new_password), False)

        # There still should have 1 token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)

    def test_if_ResetPasswordConfirm_wont_work_if_new_password_is_short(self):

        old_password ='secretpass'
        new_password = 'short'

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Make a change password request

        # confirm password before changing
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), True)
        self.assertEqual(user.check_password(new_password), False)

        # Get token
        token = ResetPasswordToken.objects.get(user=self.top_profile1.user)

        payload = {"password": new_password, "token": token.key}

        response = self.client.post(reverse('api:password_reset_confirm'), payload, format='json') 
        self.assertEqual(response.status_code, 400)

        result = {'password': ['This password is too short. It must contain at least 8 characters.']}
        self.assertEqual(response.data, result)                                                           
    
        # Confirm password was not changed
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), True)
        self.assertEqual(user.check_password(new_password), False)

        # There still should have 1 token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)

    def test_if_ResetPasswordConfirm_wont_work_if_token_is_empty(self):

        old_password ='secretpass'
        new_password = 'new_password'

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Make a change password request

        # confirm password before changing
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), True)
        self.assertEqual(user.check_password(new_password), False)

        payload = {"password": new_password, "token": ''}

        response = self.client.post(reverse('api:password_reset_confirm'), payload, format='json')                                                                  
        self.assertEqual(response.status_code, 400)

        result = {'token': ['This field may not be blank.']}
        self.assertEqual(response.data, result) 

        # Confirm password was not changed
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), True)
        self.assertEqual(user.check_password(new_password), False)

        # There still should have 1 token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)

    def test_if_ResetPasswordConfirm_wont_work_if_token_is_wrong(self):

        old_password ='secretpass'
        new_password = 'new_password'

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Make a change password request

        # confirm password before changing
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), True)
        self.assertEqual(user.check_password(new_password), False)

        payload = {"password": new_password, "token": 'wrongtoken'}

        response = self.client.post(reverse('api:password_reset_confirm'), payload, format='json')                                                                  
        self.assertEqual(response.status_code, 404)

        # Confirm password was not changed
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), True)
        self.assertEqual(user.check_password(new_password), False)

        # There still should have 1 token
        self.assertEqual(ResetPasswordToken.objects.all().count(), 1)

    def test_ResetPasswordConfirm_will_accept_a_token_just_about_to_expire(self):

        old_password ='secretpass'
        new_password = 'new_password'

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Make a change password request

        # confirm password before changing
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), True)
        self.assertEqual(user.check_password(new_password), False)

        # Set token created date just about to expire
        token = ResetPasswordToken.objects.get(user=self.top_profile1.user)
        token.created_date = timezone.now() - datetime.timedelta(hours=RESET_TOKEN_EXPIRY_TIME-1)
        token.save()

        payload = {"password": new_password, "token": token.key}

        response = self.client.post(reverse('api:password_reset_confirm'), payload, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Confirm password was changed
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), False)
        self.assertEqual(user.check_password(new_password), True)

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)

    def test_ResetPasswordConfirm_wont_accept_an_expired_token(self):

        old_password ='secretpass'
        new_password = 'new_password'

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
    
        data = {'email': self.top_profile1.user.email}
        
        response = self.client.post(reverse('api:password_reset'), data, format='json')                                                                  
        self.assertEqual(response.status_code, 200)

        # Make a change password request

        # confirm password before changing
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), True)
        self.assertEqual(user.check_password(new_password), False)

        # Set token created date past last 24 hours
        token = ResetPasswordToken.objects.get(user=self.top_profile1.user)
        token.created_date = timezone.now() - datetime.timedelta(hours=RESET_TOKEN_EXPIRY_TIME)
        token.save()

        payload = {"password": new_password, "token": token.key}

        response = self.client.post(reverse('api:password_reset_confirm'), payload, format='json')                                                                  
        self.assertEqual(response.status_code, 404)

        # Confirm password was not changed
        user = User.objects.get(email=self.top_profile1.user.email)
        self.assertEqual(user.check_password(old_password), True)
        self.assertEqual(user.check_password(new_password), False)

        # There should be zero tokens
        self.assertEqual(ResetPasswordToken.objects.all().count(), 0)
