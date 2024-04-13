from decimal import Decimal

from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.create_store_models import create_new_store, create_new_tax
from core.test_utils.initial_user_data import (
    InitialUserDataMixin,
    FilterDatesMixin
)
from core.test_utils.custom_testcase import APITestCase
from core.test_utils.create_user import (
    create_new_user,
    create_new_manager_user,
)
from core.test_utils.make_payment import make_payment

from profiles.models import EmployeeProfile, Profile
from mysettings.models import MySetting
from stores.models import Tax

User = get_user_model()
 

class TpTaxPosIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create taxes for top user 1
        self.tax1 = create_new_tax(self.top_profile1, self.store1, 'Standard1')
        self.tax2 = create_new_tax(self.top_profile1, self.store1, 'Standard2')

        # Create taxes for top user 2
        self.tax3 = create_new_tax(self.top_profile2, self.store3, 'Standard3')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_returns_the_user_models_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(5):
            response = self.client.get(
                reverse('api:tp_pos_tax_index', args=(self.store1.reg_no,)))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': 'Standard1', 
                    'rate': str(self.tax1.rate), 
                    'reg_no': self.tax1.reg_no
                },
                {
                    'name': 'Standard2', 
                    'rate': str(self.tax2.rate), 
                    'reg_no': self.tax2.reg_no
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
                reverse('api:tp_pos_tax_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all taxes
        Tax.objects.all().delete()

        pagination_page_size = settings.LEAN_PAGINATION_PAGE_SIZE

        model_num_to_be_created = pagination_page_size+1

        tax_names = []
        for i in range(model_num_to_be_created):
            tax_names.append(f'New Tax{i}')

        names_length = len(tax_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm taxes
        for i in range(names_length):
            create_new_tax(self.top_profile1, self.store1, tax_names[i])

        self.assertEqual(
            Tax.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

    
        taxes = Tax.objects.filter(profile=self.top_profile1).order_by('-id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(5):
            response = self.client.get(
                reverse('api:tp_pos_tax_index', args=(self.store1.reg_no,)))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        print()

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 
            f'http://testserver/api/pos/taxes/{self.store1.reg_no}/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all taxes are listed except the first one since it's in the next paginated page #
        i = 0
        for tax in taxes[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], tax.name)
            self.assertEqual(
                response_data_dict['results'][i]['rate'], str(tax.rate))
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], tax.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
                reverse('api:tp_pos_tax_index', args=(self.store1.reg_no,))  + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': f'http://testserver/api/pos/taxes/{self.store1.reg_no}/',
            'results': [
                {
                    'name': taxes[0].name,  
                    'rate': str(taxes[0].rate),  
                    'reg_no': taxes[0].reg_no,
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_tax_that_belong_to_store_only(self):

        response = self.client.get(
                reverse('api:tp_pos_tax_index', args=(self.store2.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_returns_tax_that_belong_to_user_store_only(self):

        response = self.client.get(
                reverse('api:tp_pos_tax_index', args=(self.store3.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_taxes(self):

        # First delete all taxes
        Tax.objects.all().delete()

        response = self.client.get(
                reverse('api:tp_pos_tax_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
                reverse('api:tp_pos_tax_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:tp_pos_tax_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)

class TpTaxPosIndexViewForCreatingTestCase(APITestCase):

    def setUp(self):

        # Create a top user1
        self.user1 = create_new_user('john')

        self.top_profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store = create_new_store(self.top_profile, 'Computer Store')

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
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_if_view_can_create_a_tax(self):

        payload = {
            'name': 'New Tax',
            'rate': 30.05,
        }

        # Count Number of Queries
        with self.assertNumQueries(15):
            response = self.client.post(
                reverse('api:tp_pos_tax_index', 
                args=(self.store.reg_no,)), 
                payload,
            )  
            self.assertEqual(response.status_code, 201)


        # Confirm tax models creation
        self.assertEqual(Tax.objects.all().count(), 1)

        tax = Tax.objects.get(name='New Tax')

        success_response = {
            'name': tax.name, 
            'rate': str(tax.rate), 
            'reg_no': tax.reg_no
        }

        self.assertEqual(response.data, success_response)

        # Check model values
        self.assertEqual(tax.profile.user.email, 'john@gmail.com')
        self.assertEqual(tax.stores.all().count(), 1)
        self.assertEqual(tax.name, payload['name'])
        self.assertEqual(tax.rate, Decimal(str(payload['rate']))) 

    def test_if_view_can_only_make_tax_with_store_that_belongs_to_the_user(self):

        payload = {
            'name': 'New Tax',
            'rate': 30.05,
        }

        response = self.client.post(
            reverse('api:tp_pos_tax_index', 
            args=(self.store2.reg_no,)), 
            payload,
        )  
        self.assertEqual(response.status_code, 404)


        # Confirm tax model was not created
        self.assertEqual(Tax.objects.all().count(), 0)

    def test_if_a_tax_cant_be_created_with_an_empty_name(self):

        payload = {
            'name': '',
            'rate': 30.05,
        }

        response = self.client.post(
            reverse('api:tp_pos_tax_index', 
            args=(self.store.reg_no,)), 
            payload,
        )  
        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_user_cant_have_2_taxes_with_the_same_name(self):

        create_new_tax(self.top_profile, self.store, 'New Tax')

        payload = {
            'name': 'New Tax',
            'rate': 30.05,
        }

        response = self.client.post(
            reverse('api:tp_pos_tax_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 400)
        
        result = {'name': ['You already have a tax with this name.']}
        
        self.assertEqual(response.data, result)
        
        # Confirm the tax was not created
        self.assertEqual(Tax.objects.all().count(), 1)

    def test_if_2_users_can_have_2_taxes_with_the_same_name(self):

        create_new_tax(self.top_profile2, self.store, 'New Tax')

        payload = {
            'name': 'New Tax',
            'rate': 30.05,
        }

        response = self.client.post(
            reverse('api:tp_pos_tax_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 201)

        # Confirm tax model creation 
        self.assertEqual(Tax.objects.all().count(), 2)

    def test_if_a_tax_cant_be_created_with_an_empty_rate(self):

        payload = {
            'name': 'New Tax',
            'rate': '',
        }

        response = self.client.post(
            reverse('api:tp_pos_tax_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 400)

        result = {'rate': ['A valid number is required.']}

        self.assertEqual(response.data, result)

    def test_if_view_can_create_a_tax_with_a_rate_of_100(self):

        payload = {
            'name': 'New Tax',
            'rate': 100,
        }

        response = self.client.post(
            reverse('api:tp_pos_tax_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 201)

        # Confirm tax models creation
        self.assertEqual(Tax.objects.all().count(), 1)

        tax = Tax.objects.get(name='New Tax')
  
        self.assertEqual(tax.profile.user.email, 'john@gmail.com')
        self.assertEqual(tax.name, payload['name'])
        self.assertEqual(tax.rate, Decimal(str(payload['rate']))) 

    def test_if_a_tax_cant_be_created_with_an_rate_higher_than_a_100(self):

        payload = {
            'name': 'New Tax',
            'rate': '101',
        }

        response = self.client.post(
            reverse('api:tp_pos_tax_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 400)

        result = {'rate': ['This value cannot be bigger than 100.']}

        self.assertEqual(response.data, result)

    def test_if_tax_cant_be_created_when_maintenance_mode_is_on(self):

        # Turn on maintenance mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        payload = {
            'name': 'New Tax',
            'rate': 30.05,
        }

        response = self.client.post(
            reverse('api:tp_pos_tax_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 401)

        # Confirm tax were not created
        self.assertEqual(Tax.objects.all().count(), 0)

    def test_if_view_can_can_throttle_tax_creation(self):

        throttle_rate = int(
            settings.THROTTLE_RATES['api_tax_rate'].split("/")[0])

        for i in range(throttle_rate): # pylint: disable=unused-variable
            payload = {
                'name': f'New Tax{i}',
                'rate': 30.05,
            }

            response = self.client.post(
                reverse('api:tp_pos_tax_index', 
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
                'name': f'New Tax{i+1}',
                'rate': 30.05,
            }

            response = self.client.post(
                reverse('api:tp_pos_tax_index', 
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

    def test_if_view_cant_be_viewed_by_an_employee_user(self):

        store = create_new_store(self.top_profile, 'Computer Store')

        # Create a manager user
        create_new_manager_user("gucci", self.top_profile, store)
        manager_profile = EmployeeProfile.objects.get(
            user__email='gucci@gmail.com')

        # Make a single payment so that the the profile will be qualified
        # to have locations
        make_payment(self.user1, manager_profile.reg_no, 1)

        # Login a employee profile #
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = {
            'name': 'New Tax',
            'rate': 30.05,
        }

        response = self.client.post(
            reverse('api:tp_pos_tax_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = {
            'name': 'New Tax',
            'rate': 30.05,
        }

        response = self.client.post(
            reverse('api:tp_pos_tax_index', 
            args=(self.store.reg_no,)), 
            payload,
        ) 
        self.assertEqual(response.status_code, 401)

class TaxPosEditViewForViewingTestCase(APITestCase, InitialUserDataMixin, FilterDatesMixin):

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

        # Create taxes for top user 1
        self.tax1 = create_new_tax(self.top_profile1, self.store1, 'Standard1')
        self.tax2 = create_new_tax(self.top_profile1, self.store1, 'Standard2')

        # Create taxes for top user 2
        self.tax3 = create_new_tax(self.top_profile2, self.store2, 'Standard3')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_can_be_called_successefully(self):

        # Count Number of Queries #
        with self.assertNumQueries(4):
            response = self.client.get(
                reverse('api:tp_pos_tax_edit_view', 
                args=(self.store1.reg_no, self.tax1.reg_no,))
            )
            self.assertEqual(response.status_code, 200)

        result = {
            'name': self.tax1.name,
            'rate': str(self.tax1.rate),
            'reg_no': self.tax1.reg_no
        }

        self.assertEqual(response.data, result)

        ########################## Test maintaince ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
            reverse('api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

    def test_view_can_handle_wrong_store_reg_no(self):

        response = self.client.get(
            reverse('api:tp_pos_tax_edit_view', args=(4646464, self.tax1.reg_no)))
        self.assertEqual(response.status_code, 404)

    def test_view_can_handle_wrong_tax_reg_no(self):

        response = self.client.get(
            reverse('api:tp_pos_tax_edit_view', args=(self.store1.reg_no, 4646464,)))
        self.assertEqual(response.status_code, 404)

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)


class TaxPosEditViewForEditingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create taxes for top user 1
        self.tax1 = create_new_tax(self.top_profile1, self.store1, 'Standard1')
        self.tax2 = create_new_tax(self.top_profile1, self.store1,'Standard2')

        # Create taxes for top user 2
        self.tax3 = create_new_tax(self.top_profile2, self.store2, 'Standard3')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_can_edit_a_tax(self):

        payload = {
            'name': 'New Tax',
            'rate': '30.02',
        }

        # Count Number of Queries #
        with self.assertNumQueries(9):
            response = self.client.put(reverse(
                'api:tp_pos_tax_edit_view', 
                args=(self.store1.reg_no, self.tax1.reg_no,)), 
                payload
            )
            self.assertEqual(response.status_code, 200)

        # Confirm tax was changed
        tax = Tax.objects.get(name='New Tax')
  
        self.assertEqual(tax.profile.user.email, 'john@gmail.com')
        self.assertEqual(tax.name, payload['name'])
        self.assertEqual(tax.rate, Decimal(str(payload['rate'])))

    def test_if_a_tax_cant_be_edited_with_an_empty_name(self):
        
        payload = {
            'name': '',
            'rate': '30.02',
        }
        
        response = self.client.put(reverse(
            'api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}
        
        self.assertEqual(response.data, result) 

    def test_if_a_user_cant_have_2_taxes_with_the_same_name(self):

        payload = {
            'name': self.tax2.name,
            'rate': '30.02',
        }

        response = self.client.put(reverse(
            'api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 400)

        result = {'name': ['You already have a tax with this name.']}
        
        self.assertEqual(response.data, result)

        # Check that edit tax was not successful
        self.assertEqual(
            Tax.objects.filter(name=self.tax2.name).count()
            ,1
        )

    def test_if_2_users_can_have_2_taxes_with_the_same_name(self):

        payload = {
            'name': self.tax3.name,
            'rate': '30.02',
        }

        response = self.client.put(reverse(
            'api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)
        
        # Check that edit tax was successful
        self.assertEqual(
            Tax.objects.filter(name=self.tax3.name).count()
            ,2
        )

    def test_if_tax_unchange_name_can_be_saved_without_raising_duplicate_error(self):
        
        payload = {
            'name': self.tax1.name,
            'rate': '30.02',
        }
        
        response = self.client.put(reverse(
            'api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        # Check that edit tax was successful
        self.assertEqual(
            Tax.objects.filter(name=self.tax1.name).count()
            ,1
        )

    def test_if_view_can_edit_a_tax_with_a_rate_of_100(self):

        payload = {
            'name': 'New Tax',
            'rate': 100,
        }

        response = self.client.put(reverse(
            'api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        # Confirm tax models creation
        tax = Tax.objects.get(name='New Tax')
  
        self.assertEqual(tax.profile.user.email, 'john@gmail.com')
        self.assertEqual(tax.name, payload['name'])
        self.assertEqual(tax.rate, Decimal(str(payload['rate']))) 

    def test_if_a_tax_cant_be_created_with_an_rate_higher_than_a_100(self):

        payload = {
            'name': 'New Tax',
            'rate': '101',
        }

        response = self.client.put(reverse(
            'api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 400)

        result = {'rate': ['This value cannot be bigger than 100.']}

        self.assertEqual(response.data, result)

    def test_view_can_handle_a_wrong_store_reg_no(self):

        payload = {
            'name': 'New Tax',
            'rate': '30.02',
        }

        response = self.client.put(
            reverse('api:tp_pos_tax_edit_view', 
            args=(111111111, self.tax1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 404)

    def test_view_can_handle_a_wrong_tax_reg_no(self):

        payload = {
            'name': 'New Tax',
            'rate': '30.02',
        }

        response = self.client.put(
            reverse('api:tp_pos_tax_edit_view', 
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
            'name': 'New Tax',
            'rate': '30.02',
        }

        response = self.client.put(reverse(
            'api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_changed_by_an_employee_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = {
            'name': 'New Tax',
            'rate': '30.02',
        }

        response = self.client.put(reverse(
            'api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_changed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = {
            'name': 'New Tax',
            'rate': '30.02',
        }

        response = self.client.put(reverse(
            'api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 401)

class TaxPosEditViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create taxes for top user 1
        self.tax1 = create_new_tax(self.top_profile1, self.store1, 'Standard1')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_can_delete_a_tax(self):

        response = self.client.delete(
            reverse('api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,))
        )
        self.assertEqual(response.status_code, 204)

        # Confirm the tax was deleted
        self.assertEqual(Tax.objects.filter(
            reg_no=self.tax1.reg_no).exists(), False
        )

    def test_view_can_handle_wrong_store_reg_no(self):

        response = self.client.delete(
            reverse('api:tp_pos_tax_edit_view', 
            args=(44444, self.tax1.reg_no))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the tax was not deleted
        self.assertEqual(Tax.objects.filter(
            reg_no=self.tax1.reg_no).exists(), True
        )

    def test_view_can_handle_wrong_tax_reg_no(self):

        response = self.client.delete(
            reverse('api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, 44444,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the tax was not deleted
        self.assertEqual(Tax.objects.filter(
            reg_no=self.tax1.reg_no).exists(), True
        )

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the tax was not deleted
        self.assertEqual(Tax.objects.filter(
            reg_no=self.tax1.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_employee_user(self):

        # Login a employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the tax was not deleted
        self.assertEqual(Tax.objects.filter(
            reg_no=self.tax1.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:tp_pos_tax_edit_view', 
            args=(self.store1.reg_no, self.tax1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

        # Confirm the tax was not deleted
        self.assertEqual(Tax.objects.filter(
            reg_no=self.tax1.reg_no).exists(), True
        )
