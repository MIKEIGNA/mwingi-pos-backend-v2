from decimal import Decimal
import json
from django.contrib.auth.models import Permission

from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.create_store_models import create_new_store, create_new_discount
from core.test_utils.initial_user_data import InitialUserDataMixin
from core.test_utils.custom_testcase import APITestCase
from core.test_utils.create_user import (
    create_new_user,
    create_new_manager_user,
)
from core.test_utils.make_payment import make_payment

from profiles.models import Profile
from mysettings.models import MySetting
from stores.models import Discount

class EpDiscountPosIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create discounts for top user 1
        self.discount1 = create_new_discount(self.top_profile1, self.store1, 'Standard1')
        self.discount2 = create_new_discount(self.top_profile1, self.store1, 'Standard2')
        self.discount3 = create_new_discount(self.top_profile1, self.store2, 'Standard3')

        # Create discounts for top user 2
        self.discount4 = create_new_discount(self.top_profile2, self.store3, 'Standard4')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_returns_the_user_discounts_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(7):
            response = self.client.get(
                reverse('api:ep_pos_discount_index', args=(self.store1.reg_no,)))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': 'Standard1', 
                    'amount': str(self.discount1.amount), 
                    'reg_no': self.discount1.reg_no
                },
                {
                    'name': 'Standard2', 
                    'amount': str(self.discount2.amount), 
                    'reg_no': self.discount2.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
                reverse('api:ep_pos_discount_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all discounts
        Discount.objects.all().delete()

        pagination_page_size = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION

        model_num_to_be_created = pagination_page_size+1

        discount_names = []
        for i in range(model_num_to_be_created):
            discount_names.append(f'New Discount{i}')

        names_length = len(discount_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm discounts
        for i in range(names_length):
            create_new_discount(self.top_profile1, self.store1, discount_names[i])

        self.assertEqual(
            Discount.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

    
        discounts = Discount.objects.filter(profile=self.top_profile1).order_by('-id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(7):
            response = self.client.get(
                reverse('api:ep_pos_discount_index', args=(self.store1.reg_no,)))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 
            f'http://testserver/api/ep/pos/discounts/{self.store1.reg_no}/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all discounts are listed except the first one since it's in the next paginated page #
        i = 0
        for discount in discounts[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], discount.name)
            self.assertEqual(
                response_data_dict['results'][i]['amount'], str(discount.amount))
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], discount.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
                reverse('api:ep_pos_discount_index', args=(self.store1.reg_no,))  + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': f'http://testserver/api/ep/pos/discounts/{self.store1.reg_no}/',
            'results': [
                {
                    'name': discounts[0].name,  
                    'amount': str(discounts[0].amount),  
                    'reg_no': discounts[0].reg_no,
                }
            ]
        }

        self.assertEqual(response.data, result)
    
    def test_view_returns_discount_that_belong_to_store_only(self):

        response = self.client.get(
                reverse('api:ep_pos_discount_index', args=(self.store2.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_returns_discount_that_belong_to_user_store_only(self):

        response = self.client.get(
                reverse('api:ep_pos_discount_index', args=(self.store3.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_discounts(self):

        # First delete all discounts
        Discount.objects.all().delete()

        response = self.client.get(
                reverse('api:ep_pos_discount_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_a_top_user(self):

        # Login a top user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
                reverse('api:ep_pos_discount_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:ep_pos_discount_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)

class EpDiscountPosIndexViewForCreatingTestCase(APITestCase):

    def setUp(self):

        # Create a top user1
        self.user1 = create_new_user('john')

        self.top_profile = Profile.objects.get(user__email='john@gmail.com')

        self.store = create_new_store(self.top_profile, 'Computer Store')
        self.manager_profile = create_new_manager_user("gucci", self.top_profile, self.store)
        # Make a single payment so that the the profile will be qualified
        # to have locations
        make_payment(self.user1, self.manager_profile.reg_no, 1)

        # Create a top user2
        self.user2 = create_new_user('jack')

        self.top_profile2 = Profile.objects.get(user__email='jack@gmail.com')

        #Create a store
        self.store2 = create_new_store(self.top_profile2, 'Shoe Store')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_if_view_can_create_a_discount(self):

        payload = {
            'name': 'New Discount',
            'amount': 30.05,
        }

        # Count Number of Queries
        with self.assertNumQueries(21):
            response = self.client.post(
                reverse('api:ep_pos_discount_index', 
                args=(self.store.reg_no,)), 
                payload,
            )  
            self.assertEqual(response.status_code, 201)


        # Confirm discount models creation
        self.assertEqual(Discount.objects.all().count(), 1)

        discount = Discount.objects.get(name='New Discount')

        success_response = {
            'name': discount.name, 
            'amount': str(discount.amount), 
            'reg_no': discount.reg_no
        }

        self.assertEqual(response.data, success_response)

        # Check model values
        self.assertEqual(discount.profile.user.email, 'john@gmail.com')
        self.assertEqual(discount.stores.all().count(), 1)
        self.assertEqual(discount.name, payload['name'])
        self.assertEqual(discount.amount, Decimal(str(payload['amount']))) 

    def test_if_view_cant_create_a_discount_when_user_has_no_permission(self):
        
        # Delete permissoin
        Permission.objects.filter(codename='can_manage_items').delete()

        payload = {
            'name': 'New Discount',
            'amount': 30.05,
        }

        response = self.client.post(
            reverse('api:ep_pos_discount_index', 
            args=(self.store.reg_no,)), 
            payload,
        )  
        self.assertEqual(response.status_code, 403)
        
    def test_if_view_can_only_make_discount_with_store_that_belongs_to_the_user(self):

        payload = {
            'name': 'New Discount',
            'amount': 30.05,
        }

        response = self.client.post(
            reverse('api:ep_pos_discount_index', 
            args=(self.store2.reg_no,)), 
            payload,
        )  
        self.assertEqual(response.status_code, 404)


        # Confirm discount model was not created
        self.assertEqual(Discount.objects.all().count(), 0)

    def test_if_a_discount_cant_be_created_with_an_empty_name(self):

        payload = {
            'name': '',
            'amount': 30.05,
        }

        response = self.client.post(
            reverse('api:ep_pos_discount_index', 
            args=(self.store.reg_no,)), 
            payload,
        )  
        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_user_cant_have_2_discounts_with_the_same_name(self):

        create_new_discount(self.top_profile, self.store, 'New Discount')

        payload = {
            'name': 'New Discount',
            'amount': 30.05,
        }

        response = self.client.post(
            reverse('api:ep_pos_discount_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 400)
        
        result = {'name': ['You already have a discount with this name.']}
        
        self.assertEqual(response.data, result)
        
        # Confirm the discount was not created
        self.assertEqual(Discount.objects.all().count(), 1)

    def test_if_2_users_can_have_2_discounts_with_the_same_name(self):

        create_new_discount(self.top_profile2, self.store, 'New Discount')

        payload = {
            'name': 'New Discount',
            'amount': 30.05,
        }

        response = self.client.post(
            reverse('api:ep_pos_discount_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 201)

        # Confirm discount model creation 
        self.assertEqual(Discount.objects.all().count(), 2)

    def test_if_a_discount_cant_be_created_with_an_empty_rate(self):

        payload = {
            'name': 'New Discount',
            'amount': '',
        }

        response = self.client.post(
            reverse('api:ep_pos_discount_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 400)

        result = {'amount': ['A valid number is required.']}

        self.assertEqual(response.data, result)

    def test_if_view_can_create_a_discount_with_a_rate_of_100(self):

        payload = {
            'name': 'New Discount',
            'amount': 100,
        }

        response = self.client.post(
            reverse('api:ep_pos_discount_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 201)

        # Confirm discount models creation
        self.assertEqual(Discount.objects.all().count(), 1)

        discount = Discount.objects.get(name='New Discount')
  
        self.assertEqual(discount.profile.user.email, 'john@gmail.com')
        self.assertEqual(discount.name, payload['name'])
        self.assertEqual(discount.amount, Decimal(str(payload['amount']))) 

    def test_if_discount_cant_be_created_when_maintenance_mode_is_on(self):

        # Turn on maintenance mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        payload = {
            'name': 'New Discount',
            'amount': 30.05,
        }

        response = self.client.post(
            reverse('api:ep_pos_discount_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 401)

        # Confirm discount were not created
        self.assertEqual(Discount.objects.all().count(), 0)

    def test_if_view_can_can_throttle_discount_creation(self):

        throttle_rate = int(
            settings.THROTTLE_RATES['api_discount_rate'].split("/")[0])

        for i in range(throttle_rate): # pylint: disable=unused-variable
            payload = {
                'name': f'New Discount{i}',
                'amount': 30.05,
            }

            response = self.client.post(
                reverse('api:ep_pos_discount_index', 
                args=(self.store.reg_no,)), 
                payload,
            ) 
            self.assertEqual(response.status_code, 201)

        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional
        # request if the previous request was not throttled
        for i in range(throttle_rate): # pylint: disable=unused-variable

            # Try to see if the next request will be throttled
            new_payload = {
                'name': f'New Discount{i+1}',
                'amount': 30.05,
            }

            response = self.client.post(
                reverse('api:ep_pos_discount_index', 
                args=(self.store.reg_no,)), 
                new_payload,
            ) 

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else:
            # Executed because break was not called. This means the request was
            # never throttled
            self.fail()

    def test_if_view_cant_be_viewed_by_a_top_user(self):

        # Login a top user #
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = {
            'name': 'New Discount',
            'amount': 30.05,
        }

        response = self.client.post(
            reverse('api:ep_pos_discount_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = {
            'name': 'New Discount',
            'amount': 30.05,
        }

        response = self.client.post(
            reverse('api:ep_pos_discount_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 401)

class EpDiscountPosEditViewForViewingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create discounts for top user 1
        self.discount1 = create_new_discount(self.top_profile1, self.store1, 'Standard1')
        self.discount2 = create_new_discount(self.top_profile1, self.store1, 'Standard2')

        # Create discounts for top user 2
        self.discount3 = create_new_discount(self.top_profile2, self.store2, 'Standard3')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_can_be_called_successefully(self):

        # Count Number of Queries #
        with self.assertNumQueries(5):
            response = self.client.get(
                reverse('api:ep_pos_discount_edit_view', 
                args=(self.store1.reg_no, self.discount1.reg_no,))
            )
            self.assertEqual(response.status_code, 200)

        result = {
            'name': self.discount1.name,
            'amount': str(self.discount1.amount),
            'reg_no': self.discount1.reg_no,
        }

        self.assertEqual(response.data, result)

        ########################## Test maintaince ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
            reverse('api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

    def test_view_can_handle_wrong_store_reg_no(self):

        response = self.client.get(
            reverse('api:ep_pos_discount_edit_view', args=(4646464, self.discount1.reg_no)))
        self.assertEqual(response.status_code, 404)

    def test_view_can_handle_wrong_discount_reg_no(self):

        response = self.client.get(
            reverse('api:ep_pos_discount_edit_view', args=(self.store1.reg_no, 4646464,)))
        self.assertEqual(response.status_code, 404)

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_a_top_user(self):

        # Login a top user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

class EpDiscountPosEditViewForEditingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create discounts for top user 1
        self.discount1 = create_new_discount(self.top_profile1, self.store1, 'Standard1')
        self.discount2 = create_new_discount(self.top_profile1, self.store1,'Standard2')

        # Create discounts for top user 2
        self.discount3 = create_new_discount(self.top_profile2, self.store2, 'Standard3')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_can_edit_a_discount(self):

        payload = {
            'name': 'New Discount',
            'amount': '30.02',
        }

        # Count Number of Queries #
        with self.assertNumQueries(12):
            response = self.client.put(reverse(
                'api:ep_pos_discount_edit_view', 
                args=(self.store1.reg_no, self.discount1.reg_no,)), 
                payload
            )
            self.assertEqual(response.status_code, 200)

        # Confirm discount was changed
        discount = Discount.objects.get(name='New Discount')
  
        self.assertEqual(discount.profile.user.email, 'john@gmail.com')
        self.assertEqual(discount.name, payload['name'])
        self.assertEqual(discount.amount, Decimal(str(payload['amount'])))

    def test_if_view_cant_edit_a_discount_when_user_has_no_permission(self):
        
        # Delete permissoin
        Permission.objects.filter(codename='can_manage_items').delete()

        payload = {
            'name': 'New Discount',
            'amount': '30.02',
        }

        response = self.client.put(reverse(
            'api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 403)

    def test_if_a_discount_cant_be_edited_with_an_empty_name(self):
        
        payload = {
            'name': '',
            'amount': '30.02',
        }
        
        response = self.client.put(reverse(
            'api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}
        
        self.assertEqual(response.data, result) 

    def test_if_a_user_cant_have_2_discounts_with_the_same_name(self):

        payload = {
            'name': self.discount2.name,
            'amount': '30.02',
        }

        response = self.client.put(reverse(
            'api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 400)

        result = {'name': ['You already have a discount with this name.']}
        
        self.assertEqual(response.data, result)

        # Check that edit discount was not successful
        self.assertEqual(
            Discount.objects.filter(name=self.discount2.name).count()
            ,1
        )

    def test_if_2_users_can_have_2_discounts_with_the_same_name(self):

        payload = {
            'name': self.discount3.name,
            'amount': '30.02',
        }

        response = self.client.put(reverse(
            'api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)
        
        # Check that edit discount was successful
        self.assertEqual(
            Discount.objects.filter(name=self.discount3.name).count()
            ,2
        )

    def test_if_discount_unchange_name_can_be_saved_without_raising_duplicate_error(self):
        
        payload = {
            'name': self.discount1.name,
            'amount': '30.02',
        }
        
        response = self.client.put(reverse(
            'api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        # Check that edit discount was successful
        self.assertEqual(
            Discount.objects.filter(name=self.discount1.name).count()
            ,1
        )

    def test_if_view_can_edit_a_discount_with_a_rate_of_100(self):

        payload = {
            'name': 'New Discount',
            'amount': 100,
        }

        response = self.client.put(reverse(
            'api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        # Confirm discount models creation
        discount = Discount.objects.get(name='New Discount')
  
        self.assertEqual(discount.profile.user.email, 'john@gmail.com')
        self.assertEqual(discount.name, payload['name'])
        self.assertEqual(discount.amount, Decimal(str(payload['amount']))) 

    def test_view_can_handle_a_wrong_store_reg_no(self):

        payload = {
            'name': 'New Discount',
            'amount': '30.02',
        }

        response = self.client.put(
            reverse('api:ep_pos_discount_edit_view', 
            args=(111111111, self.discount1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 404)

    def test_view_can_handle_a_wrong_discount_reg_no(self):

        payload = {
            'name': 'New Discount',
            'amount': '30.02',
        }

        response = self.client.put(
            reverse('api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, 111111111,)), 
            payload
        )
        self.assertEqual(response.status_code, 404)

    def test_if_view_can_only_be_changed_by_its_owner(self):

        # Login a top user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = {
            'name': 'New Discount',
            'amount': '30.02',
        }

        response = self.client.put(reverse(
            'api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_changed_by_a_top_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = {
            'name': 'New Discount',
            'amount': '30.02',
        }

        response = self.client.put(reverse(
            'api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_changed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = {
            'name': 'New Discount',
            'amount': '30.02',
        }

        response = self.client.put(reverse(
            'api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 401)

class EpDiscountPosEditViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create discounts for top user 1
        self.discount1 = create_new_discount(self.top_profile1, self.store1, 'Standard1')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_can_delete_a_discount(self):

        response = self.client.delete(
            reverse('api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,))
        )
        self.assertEqual(response.status_code, 204)

        # Confirm the discount was deleted
        self.assertEqual(Discount.objects.filter(
            reg_no=self.discount1.reg_no).exists(), False
        )

    def test_if_view_cant_delete_a_discount_when_user_has_no_permission(self):
        
        # Delete permissoin
        Permission.objects.filter(codename='can_manage_items').delete()

        response = self.client.delete(
            reverse('api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,))
        )
        self.assertEqual(response.status_code, 403)

        # Confirm the discount was not deleted
        self.assertEqual(Discount.objects.filter(
            reg_no=self.discount1.reg_no).exists(), True
        )

    def test_view_can_handle_wrong_store_reg_no(self):

        response = self.client.delete(
            reverse('api:ep_pos_discount_edit_view', 
            args=(44444, self.discount1.reg_no))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the discount was not deleted
        self.assertEqual(Discount.objects.filter(
            reg_no=self.discount1.reg_no).exists(), True
        )

    def test_view_can_handle_wrong_discount_reg_no(self):

        response = self.client.delete(
            reverse('api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, 44444,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the discount was not deleted
        self.assertEqual(Discount.objects.filter(
            reg_no=self.discount1.reg_no).exists(), True
        )

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='cristiano@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the discount was not deleted
        self.assertEqual(Discount.objects.filter(
            reg_no=self.discount1.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_a_top_user(self):

        # Login a top user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the discount was not deleted
        self.assertEqual(Discount.objects.filter(
            reg_no=self.discount1.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:ep_pos_discount_edit_view', 
            args=(self.store1.reg_no, self.discount1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

        # Confirm the discount was not deleted
        self.assertEqual(Discount.objects.filter(
            reg_no=self.discount1.reg_no).exists(), True
        )
