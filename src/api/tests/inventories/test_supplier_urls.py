from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.crypto import get_random_string

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from core.test_utils.create_store_models import create_new_store

from core.test_utils.initial_user_data import InitialUserDataMixin
from core.test_utils.custom_testcase import APITestCase
from core.test_utils.create_user import (
    create_new_supplier,
    create_new_user,
    create_new_manager_user,
)
from core.test_utils.make_payment import make_payment

from profiles.models import EmployeeProfile, Profile
from mysettings.models import MySetting
from inventories.models import Supplier


class LeanSupplierIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a supplier user
        self.supplier1 = create_new_supplier(self.top_profile1, 'jeremy')
        self.supplier2 = create_new_supplier(self.top_profile1, 'james')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    
    def test_view_returns_the_user_suppliers_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(5):
            response = self.client.get(reverse('api:lean_supplier_index'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.supplier2.name, 
                    'reg_no': self.supplier2.reg_no,
                },
                {
                    'name': self.supplier1.name, 
                    'reg_no': self.supplier1.reg_no,
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:lean_supplier_index'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all suppliers
        Supplier.objects.all().delete()

        pagination_page_size = settings.LEAN_PAGINATION_PAGE_SIZE

        model_num_to_be_created = pagination_page_size+1

        supplier_names = []
        for i in range(model_num_to_be_created):
            supplier_names.append(f'New Supplier{i}')

        names_length = len(supplier_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm suppliers
        for i in range(names_length):

            Supplier.objects.create(
                profile=self.top_profile1,
                name=supplier_names[i]
            )

        self.assertEqual(
            Supplier.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

  
        suppliers = Supplier.objects.filter(profile=self.top_profile1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(5):
            response = self.client.get(reverse('api:lean_supplier_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/suppliers/lean/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all suppliers are listed except the first one since it's in the next paginated page #
        i = 0
        for supplier in suppliers[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], supplier.name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], supplier.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:lean_supplier_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': 'http://testserver/api/suppliers/lean/', 
            'results': [
                {
                    'name': suppliers[0].name,
                    'reg_no': suppliers[0].reg_no,
                }
            ]
        }
    
        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        search_terms = [
            self.supplier2.name,
            self.supplier2.email
        ]

        for search_term in search_terms:
            param = f'?search={search_term}'
            response = self.client.get(reverse('api:lean_supplier_index') + param)
            self.assertEqual(response.status_code, 200)

            result = {
                'count': 1,
                'next': None,
                'previous': None,
                'results': [
                    {
                        'name': self.supplier2.name,
                        'reg_no': self.supplier2.reg_no
                    }
                ]
            }

            self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_suppliers(self):

        # First delete all suppliers
        Supplier.objects.all().delete()

        response = self.client.get(
            reverse('api:lean_supplier_index'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:lean_supplier_index'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:lean_supplier_index'))
        self.assertEqual(response.status_code, 401)


class SupplierIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a supplier user
        self.supplier1 = create_new_supplier(self.top_profile1, 'jeremy')
        self.supplier2 = create_new_supplier(self.top_profile1, 'james')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    
    def test_view_returns_the_user_suppliers_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(5):
            response = self.client.get(reverse('api:supplier_index'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.supplier2.name, 
                    'email': self.supplier2.email, 
                    'phone': self.supplier2.phone, 
                    'reg_no': self.supplier2.reg_no,
                },
                {
                    'name': self.supplier1.name, 
                    'email': self.supplier1.email, 
                    'phone': self.supplier1.phone, 
                    'reg_no': self.supplier1.reg_no,
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:supplier_index'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all suppliers
        Supplier.objects.all().delete()

        pagination_page_size = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION

        model_num_to_be_created = pagination_page_size+1

        supplier_names = []
        for i in range(model_num_to_be_created):
            supplier_names.append(f'New Supplier{i}')

        names_length = len(supplier_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm suppliers
        for i in range(names_length):

            Supplier.objects.create(
                profile=self.top_profile1,
                name=supplier_names[i]
            )

        self.assertEqual(
            Supplier.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

  
        suppliers = Supplier.objects.filter(profile=self.top_profile1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(5):
            response = self.client.get(reverse('api:supplier_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/suppliers/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all suppliers are listed except the first one since it's in the next paginated page #
        i = 0
        for supplier in suppliers[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], supplier.name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], supplier.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:supplier_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': 'http://testserver/api/suppliers/', 
            'results': [
                {
                    'name': suppliers[0].name, 
                    'email': suppliers[0].email, 
                    'phone': suppliers[0].phone, 
                    'reg_no': suppliers[0].reg_no,
                }
            ]
        }
    
        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        search_terms = [
            self.supplier2.name,
            self.supplier2.email
        ]

        for search_term in search_terms:
            param = f'?search={search_term}'
            response = self.client.get(reverse('api:supplier_index') + param)
            self.assertEqual(response.status_code, 200)

            result = {
                'count': 1,
                'next': None,
                'previous': None,
                'results': [
                    {
                        'name': self.supplier2.name, 
                        'email': self.supplier2.email, 
                        'phone': self.supplier2.phone, 
                        'reg_no': self.supplier2.reg_no,
                    }
                ]
            }

            self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_suppliers(self):

        # First delete all suppliers
        Supplier.objects.all().delete()

        response = self.client.get(
            reverse('api:supplier_index'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:supplier_index'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:supplier_index'))
        self.assertEqual(response.status_code, 401)

class SupplierIndexViewForCreatingTestCase(APITestCase):

    def setUp(self):

        # Create a top user1
        self.user1 = create_new_user('john')

        self.top_profile = Profile.objects.get(user__email='john@gmail.com')

        # Create a top user2
        self.user2 = create_new_user('jack')

        self.top_profile2 = Profile.objects.get(user__email='jack@gmail.com')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """

        payload = {
            'name': 'New Supplier',
            'email': 'supplier@gmail.com',
            'phone': 254710101011,
            'address': 'Donholm',
            'city': 'Nairobi',
            'region': 'Africa',
            'postal_code': '11011',
            'country': 'Kenya',
            'supplier_code': 'SupplierCode12',
            'credit_limit': 200.00,
        }

        return payload

    def test_if_view_can_create_a_supplier(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        with self.assertNumQueries(14):
            response = self.client.post(
                reverse('api:supplier_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Confirm supplier models creation
        self.assertEqual(Supplier.objects.all().count(), 1)

        supplier = Supplier.objects.get(name=payload['name'])

        # Check model values
        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(supplier.name, payload['name'])
        self.assertEqual(supplier.email, payload['email'])
        self.assertEqual(supplier.phone, payload['phone'])
        self.assertEqual(supplier.address, payload['address'])
        self.assertEqual(supplier.city, payload['city'])
        self.assertEqual(supplier.region, payload['region'])
        self.assertEqual(supplier.postal_code, payload['postal_code'])
        self.assertEqual(supplier.country, payload['country'])
        self.assertTrue(supplier.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((supplier.created_date).strftime("%B, %d, %Y"), today)

    def test_if_supplier_cant_be_created_when_maintenance_mode_is_on(self):

        # Turn on maintenance mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        payload = self.get_premade_payload()

        response = self.client.post(reverse('api:supplier_index'), payload)
        self.assertEqual(response.status_code, 401)

        # Confirm supplier were not created
        self.assertEqual(Supplier.objects.all().count(), 0)

    def test_if_a_supplier_cant_be_created_with_an_empty_name(self):

        payload = self.get_premade_payload()
  
        payload['name'] = ''

        response = self.client.post(reverse('api:supplier_index'), payload)
        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_user_cant_have_2_suppliers_with_the_same_unique_values(self):
        """
        Tests if user cant have 2 suppliers with the same name, email, phone or
        supplier code
        """

        # Create a supplier for profile 1
        existing_supplier = create_new_supplier(self.top_profile, 'jeremy')

        payload = self.get_premade_payload()
  
        payload['name'] = existing_supplier.name
        payload['email'] = existing_supplier.email
        payload['phone'] = existing_supplier.phone
 
        response = self.client.post(reverse('api:supplier_index'), payload)
        self.assertEqual(response.status_code, 400)

        result = {
            'name': ['You already have a supplier with this name.'], 
            'email': ['You already have a supplier with this email.'], 
            'phone': ['You already have a supplier with this phone.'], 
        }
        
        self.assertEqual(response.data, result)
        
        # Confirm the supplier was not created
        self.assertEqual(Supplier.objects.all().count(), 1)

    def test_if_2_users_can_have_2_suppliers_with_the_same_unique_values(self):
        """
        Tests if 2 users can have 2 suppliers with the same name, email, phone or
        supplier code
        """

        # Create a supplier for profile 2
        existing_supplier = create_new_supplier(self.top_profile2, 'jeremy')

        payload = self.get_premade_payload()
  
        payload['name'] = existing_supplier.name
        payload['email'] = existing_supplier.email
        payload['phone'] = existing_supplier.phone

        response = self.client.post(reverse('api:supplier_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm supplier model creation 
        self.assertEqual(Supplier.objects.all().count(), 2)

    def test_if_suppliers_can_have_the_allowed_empty_fields_without_triggering_unique_validator_or_any_other_error(self):

        # Create a supplier for profile 1
        existing_supplier = create_new_supplier(self.top_profile, 'jeremy')
        existing_supplier.email = ''
        existing_supplier.phone = 0
        existing_supplier.address = ''
        existing_supplier.city = ''
        existing_supplier.region = ''
        existing_supplier.postal_code = ''
        existing_supplier.country = ''
        existing_supplier.save()

        payload = self.get_premade_payload()

        payload['email'] = ''
        payload.pop('phone')
        payload['address'] = ''
        payload['city'] = ''
        payload['region'] = ''
        payload['postal_code'] = ''
        payload['country'] = ''

        response = self.client.post(reverse('api:supplier_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm supplier model creation 
        self.assertEqual(Supplier.objects.all().count(), 2)

    def test_if_a_supplier_cant_be_created_with_a_wrong_email(self):

        wrong_emails = [
            "{}@gmail.com".format("x"*30), # Long email
            "wrongemailformat", # Wrong format
        ]

        i=0
        for email in wrong_emails:
            payload = self.get_premade_payload()

            payload['email'] = email

            response = self.client.post(
                reverse('api:supplier_index'), payload)
            self.assertEqual(response.status_code, 400)

            if i==0:
             
                self.assertEqual(
                    response.data, 
                    {'email': ['Ensure this field has no more than 30 characters.']}
                )

            else:
                self.assertEqual(response.data, {'email': ['Enter a valid email address.']})

            i+=1

    def test_for_successful_supplier_creation_with_correct_phones(self):

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
        i=0
        for phone in phones:
            # Clear cache before every new request 
            cache.clear()

            payload = self.get_premade_payload()
            
            payload['name'] = f'Chris {str(i)}' + str(i) # This prevents unique error
            payload['email'] = emails[i] # This prevents unique error
            payload['supplier_code'] = f'code_{str(i)}' # This prevents unique error

            payload['phone'] = phone

            response = self.client.post(
                reverse('api:supplier_index'), payload)
            self.assertEqual(response.status_code, 201)

            i+=1
            
        self.assertEqual(i, 8)

    def test_if_a_supplier_cant_be_created_with_wrong_phones(self):

        emails = [get_random_string(10) + '@gmail.com' for i in range(8)]
        phones = [
            '25470022332j', # Number with letters
            '2547112233222', # Long Number
            '25471122332', # Short Number
            '254711223323333333333333333333333333333333',   # long Number
        ]
        
        i = 0
        for phone in phones:
            # Clear cache before every new request so that throttling does not work 
            cache.clear()

            payload = self.get_premade_payload()
            
            payload['name'] = f'Chris {str(i)}' + str(i) # This prevents unique error
            payload['email'] = emails[i] # This prevents unique error
            payload['supplier_code'] = f'code_{str(i)}' # This prevents unique error

            payload['phone'] = phone

            response = self.client.post(
                reverse('api:supplier_index'), payload)

            self.assertEqual(response.status_code, 400)

            self.assertEqual(len(response.data['phone']), 1) # Check error key
            
            if i == 1 or i == 3:               
                result = {'phone': ['This phone is too long.']}
                self.assertEqual(response.data, result)

            elif i == 2:
                result = {'phone': ['This phone is too short.']}
                self.assertEqual(response.data, result)

            else:                
                result = {'phone': ['A valid integer is required.']}
                self.assertEqual(response.data, result)

            i+=1

        self.assertEqual(i, 4)

    def test_if_view_can_can_throttle_supplier_creation(self):

        throttle_rate = int(settings.THROTTLE_RATES['api_supplier_rate'].split("/")[0])

        for i in range(throttle_rate): # pylint: disable=unused-variable

            payload = self.get_premade_payload()
            
            payload['name'] = f'Chris {str(i)}' + str(i) # This prevents unique error
            payload['email'] = '' # This prevents unique error
            payload.pop('phone')  # This prevents unique error

            response = self.client.post(
                reverse('api:supplier_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional
        # request if the previous request was not throttled
        for i in range(throttle_rate): # pylint: disable=unused-variable

            # Try to see if the next request will be throttled
            payload = self.get_premade_payload()
            
            payload['name'] = f'Chris {str(i)}' + str(i) # This prevents unique error
            payload['email'] = '' # This prevents unique error
            payload.pop('phone')  # This prevents unique error

            response = self.client.post(
                reverse('api:supplier_index'), payload)

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else:
            # Executed because break was not called. This means the request was
            # never throttled
            self.fail()

    def test_if_view_cant_be_posted_by_an_employee_user(self):

        store = create_new_store(self.top_profile2, 'Computer Store')

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

        payload = self.get_premade_payload()

        response = self.client.post(
            reverse('api:supplier_index'), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_posted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.post(
            reverse('api:supplier_index'), payload)
        self.assertEqual(response.status_code, 401)


class SupplierViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a supplier user
        self.supplier = create_new_supplier(self.top_profile1, 'jeremy')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_if_view_can_be_called_successefully(self):

        # Count Number of Queries #
        with self.assertNumQueries(4):
            response = self.client.get(
                reverse('api:supplier_view', args=(self.supplier.reg_no,)))
            self.assertEqual(response.status_code, 200)

        result = {
            'name': self.supplier.name, 
            'email': self.supplier.email, 
            'phone': self.supplier.phone, 
            'address': self.supplier.address, 
            'city': self.supplier.city, 
            'region': self.supplier.region, 
            'postal_code': self.supplier.postal_code, 
            'country': self.supplier.country,  
            'reg_no': self.supplier.reg_no,
            'location_desc': self.supplier.get_location_desc(),
            'creation_date': self.supplier.get_created_date(
                self.user1.get_user_timezone()
            )
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)))
        self.assertEqual(response.status_code, 401)

    def test_if_view_can_handle_wrong_reg_no(self):

        response = self.client.get(
            reverse('api:supplier_view', args=(4646464,)))
        self.assertEqual(response.status_code, 404)

    def test_if_view_can_only_be_viewed_by_its_owner(self):

        # login a user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)))
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_employee_user(self):

        # login a manageer user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)))
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)))
        self.assertEqual(response.status_code, 401)


class SupplierViewForEditingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a supplier user
        self.supplier = create_new_supplier(self.top_profile1, 'jeremy')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """

        payload = {
            'name': 'New Supplier',
            'email': 'supplier@gmail.com',
            'phone': 254710101011,
            'address': 'Donholm',
            'city': 'Nairobi',
            'region': 'Africa',
            'postal_code': '11011',
            'country': 'Kenya',
        }

        return payload

    def test_if_view_can_edit_a_supplier(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        with self.assertNumQueries(8):
            response = self.client.put(
                reverse('api:supplier_view', args=(self.supplier.reg_no,)), payload)
            self.assertEqual(response.status_code, 200)


        supplier = Supplier.objects.get(name=payload['name'])

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(supplier.name, payload['name'])
        self.assertEqual(supplier.email, payload['email'])
        self.assertEqual(supplier.phone, payload['phone'])
        self.assertEqual(supplier.address, payload['address'])
        self.assertEqual(supplier.city, payload['city'])
        self.assertEqual(supplier.region, payload['region'])
        self.assertEqual(supplier.postal_code, payload['postal_code'])
        self.assertEqual(supplier.country, payload['country'])
        self.assertTrue(supplier.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((supplier.created_date).strftime("%B, %d, %Y"), today)

    def test_if_supplier_cant_be_edited_when_maintenance_mode_is_on(self):

        # Turn on maintenance mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 401)

    def test_view_can_handle_a_wrong_reg_no(self):

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:supplier_view', args=(111111111,)), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_a_supplier_cant_be_edited_with_an_empty_name(self):

        payload = self.get_premade_payload()
  
        payload['name'] = ''

        response = self.client.put(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_user_can_save_user_with_existing_values_without_raising_unique_validator(self):
        """
        Tests if user can save supplier with them same values as before without
        raisng unique validator error
        """
        payload = self.get_premade_payload()
  
        payload['name'] = self.supplier.name
        payload['email'] = self.supplier.email
        payload['phone'] = self.supplier.phone
 
        response = self.client.put(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)
        
    def test_if_a_user_cant_have_2_suppliers_with_the_same_unique_values(self):
        """
        Tests if user cant have 2 suppliers with the same name, email, phone or
        supplier code
        """

        # Create a supplier for profile 1
        existing_supplier = create_new_supplier(self.top_profile1, 'richard')

        payload = self.get_premade_payload()
  
        payload['name'] = existing_supplier.name
        payload['email'] = existing_supplier.email
        payload['phone'] = existing_supplier.phone
 
        response = self.client.put(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 400)

        result = {
            'name': ['You already have a supplier with this name.'], 
            'email': ['You already have a supplier with this email.'], 
            'phone': ['You already have a supplier with this phone.'], 
        }
        
        self.assertEqual(response.data, result)

    def test_if_2_users_can_have_2_suppliers_with_the_same_unique_values(self):
        """
        Tests if 2 users can have 2 suppliers with the same name, email, phone or
        supplier code
        """

        # Create a supplier for profile 2
        existing_supplier = create_new_supplier(self.top_profile2, 'richard')

        payload = self.get_premade_payload()
  
        payload['name'] = existing_supplier.name
        payload['email'] = existing_supplier.email
        payload['phone'] = existing_supplier.phone

        response = self.client.put(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)

    def test_if_suppliers_can_have_the_allowed_empty_fields_without_triggering_unique_validator_or_any_other_error(self):

        # Create a supplier for profile 1
        existing_supplier = create_new_supplier(self.top_profile1, 'richard')
        existing_supplier.email = ''
        existing_supplier.phone = 0
        existing_supplier.address = ''
        existing_supplier.city = ''
        existing_supplier.region = ''
        existing_supplier.postal_code = ''
        existing_supplier.country = ''
        existing_supplier.save()

        payload = self.get_premade_payload()

        payload['email'] = ''
        payload.pop('phone')
        payload['address'] = ''
        payload['city'] = ''
        payload['region'] = ''
        payload['postal_code'] = ''
        payload['country'] = ''

        response = self.client.put(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)

    def test_if_a_supplier_cant_be_edited_with_a_wrong_email(self):

        wrong_emails = [
            "{}@gmail.com".format("x"*30), # Long email
            "wrongemailformat", # Wrong format
        ]

        i=0
        for email in wrong_emails:
            payload = self.get_premade_payload()

            payload['email'] = email

            response = self.client.put(
                reverse('api:supplier_view', args=(self.supplier.reg_no,)), 
                payload
            )
            self.assertEqual(response.status_code, 400)

            if i==0:
             
                self.assertEqual(
                    response.data, 
                    {'email': ['Ensure this field has no more than 30 characters.']}
                )

            else:
                self.assertEqual(response.data, {'email': ['Enter a valid email address.']})

            i+=1

    def test_for_successful_supplier_update_with_correct_phones(self):

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
        i=0
        for phone in phones:
            # Clear cache before every new request 
            cache.clear()

            payload = self.get_premade_payload()
            
            payload['name'] = f'Chris {str(i)}' + str(i) # This prevents unique error
            payload['email'] = emails[i] # This prevents unique error
            payload['supplier_code'] = f'code_{str(i)}' # This prevents unique error

            payload['phone'] = phone

            response = self.client.put(
                reverse('api:supplier_view', args=(self.supplier.reg_no,)), 
                payload
            )
            self.assertEqual(response.status_code, 200)

            i+=1
            
        self.assertEqual(i, 8)

    def test_if_a_supplier_cant_be_edited_with_wrong_phones(self):

        emails = [get_random_string(10) + '@gmail.com' for i in range(8)]
        phones = [
            '25470022332j', # Number with letters
            '2547112233222', # Long Number
            '25471122332', # Short Number
            '254711223323333333333333333333333333333333',   # long Number
        ]
        
        i = 0
        for phone in phones:
            # Clear cache before every new request so that throttling does not work 
            cache.clear()

            payload = self.get_premade_payload()
            
            payload['name'] = f'Chris {str(i)}' + str(i) # This prevents unique error
            payload['email'] = emails[i] # This prevents unique error
            payload['supplier_code'] = f'code_{str(i)}' # This prevents unique error

            payload['phone'] = phone

            response = self.client.put(
                reverse('api:supplier_view', args=(self.supplier.reg_no,)), 
                payload
            )

            self.assertEqual(response.status_code, 400)

            self.assertEqual(len(response.data['phone']), 1) # Check error key
            
            if i == 1 or i == 3:               
                result = {'phone': ['This phone is too long.']}
                self.assertEqual(response.data, result)

            elif i == 2:
                result = {'phone': ['This phone is too short.']}
                self.assertEqual(response.data, result)

            else:                
                result = {'phone': ['A valid integer is required.']}
                self.assertEqual(response.data, result)

            i+=1

        self.assertEqual(i, 4)

    def test_if_view_cant_be_updated_by_an_employee_user(self):

        # Login a employee profile #
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_updated_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 401)


class TpSupplierViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a supplier user
        self.supplier = create_new_supplier(self.top_profile1, 'jeremy')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_can_delete_a_category(self):

        response = self.client.delete(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)))
        self.assertEqual(response.status_code, 204)

        # Confirm the category was deleted
        self.assertEqual(Supplier.objects.filter(
            reg_no=self.supplier.reg_no).exists(), False
        )

    def test_view_can_handle_wrong_reg_no(self):

        response = self.client.delete(
            reverse('api:supplier_view', args=(44444,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the category was not deleted
        self.assertEqual(Supplier.objects.filter(
            reg_no=self.supplier.reg_no).exists(), True
        )

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the category was not deleted
        self.assertEqual(Supplier.objects.filter(
            reg_no=self.supplier.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_employee_user(self):

        # Login a employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the category was not deleted
        self.assertEqual(Supplier.objects.filter(
            reg_no=self.supplier.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:supplier_view', args=(self.supplier.reg_no,)))
        self.assertEqual(response.status_code, 401)

        # Confirm the category was not deleted
        self.assertEqual(Supplier.objects.filter(
            reg_no=self.supplier.reg_no).exists(), True
        )
