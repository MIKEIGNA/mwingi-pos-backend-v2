from decimal import Decimal
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.crypto import get_random_string

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from clusters.models import StoreCluster
from core.test_utils.create_store_models import create_new_store

from core.test_utils.initial_user_data import InitialUserDataMixin
from core.test_utils.custom_testcase import APITestCase
from core.test_utils.create_user import (
    create_new_customer,
    create_new_user,
    create_new_manager_user,
)
from core.test_utils.make_payment import make_payment

from profiles.models import EmployeeProfile, Profile
from mysettings.models import MySetting
from profiles.models import Customer

class TpPosCustomerIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a customer user
        self.customer = create_new_customer(self.top_profile1, 'chris')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    
    def test_view_returns_the_user_customers_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(5):
            response = self.client.get(reverse('api:tp_pos_customer_index'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.customer.name, 
                    'email': self.customer.email, 
                    'village_name': self.customer.village_name,
                    'cluster_data': self.customer.get_cluster_data(),
                    'non_null_phone': self.customer.get_non_null_phone(),
                    'phone': self.customer.phone, 
                    'address': self.customer.address, 
                    'city': self.customer.city, 
                    'region': self.customer.region, 
                    'postal_code': self.customer.postal_code, 
                    'country': self.customer.country, 
                    'customer_code': self.customer.customer_code, 
                    'credit_limit': f'{self.customer.credit_limit}.00',
                    'current_debt': Decimal('0.00'),
                    'points': 0,
                    'reg_no': self.customer.reg_no,
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:tp_pos_customer_index'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all customers
        Customer.objects.all().delete()

        pagination_page_size = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION

        model_num_to_be_created = pagination_page_size+1

        customer_names = []
        for i in range(model_num_to_be_created):
            customer_names.append(f'New Customer{i}')

        names_length = len(customer_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm customers
        for i in range(names_length):

            Customer.objects.create(
                profile=self.top_profile1,
                name=customer_names[i]
            )

        self.assertEqual(
            Customer.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

  
        customers = Customer.objects.filter(profile=self.top_profile1).order_by('-id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(5):
            response = self.client.get(reverse('api:tp_pos_customer_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/pos/customers/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all customers are listed except the first one since it's in the next paginated page #
        i = 0
        for customer in customers[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], customer.name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], customer.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:tp_pos_customer_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': 'http://testserver/api/pos/customers/', 
            'results': [
                {
                    'name': customers[0].name, 
                    'email': customers[0].email, 
                    'village_name': customers[0].village_name,
                    'cluster_data': customers[0].get_cluster_data(),
                    'non_null_phone': customers[0].get_non_null_phone(),
                    'phone': customers[0].phone, 
                    'address': customers[0].address, 
                    'city': customers[0].city, 
                    'region': customers[0].region, 
                    'postal_code': customers[0].postal_code, 
                    'country': customers[0].country, 
                    'customer_code': customers[0].customer_code, 
                    'credit_limit': '0.00',
                    'current_debt': Decimal('0.00'),
                    'points': 0,
                    'reg_no': customers[0].reg_no,
                }
            ]
        }
    
        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_customers(self):

        # First delete all customers
        Customer.objects.all().delete()

        response = self.client.get(
            reverse('api:tp_pos_customer_index'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_pos_customer_index'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_pos_customer_index'))
        self.assertEqual(response.status_code, 401)


class TpPosCustomerIndexViewForCreatingTestCase(APITestCase):

    def setUp(self):

        # Create a top user1
        self.user1 = create_new_user('john')

        self.top_profile = Profile.objects.get(user__email='john@gmail.com')

        # Create cluster
        self.cluster = StoreCluster.objects.create(name='Magadi')

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
            'name': 'New Customer',
            'email': 'customer@gmail.com',
            'village_name': 'Village 1',
            'phone': 254710101011,
            'address': 'Donholm',
            'city': 'Nairobi',
            'region': 'Africa',
            'postal_code': '11011',
            'country': 'Kenya',
            'customer_code': 'CustomerCode12',
            'credit_limit': 200.00,
            'cluster_reg_no': self.cluster.reg_no,
        }

        return payload

    def test_if_view_can_create_a_customer(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        with self.assertNumQueries(19):
            response = self.client.post(
                reverse('api:tp_pos_customer_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Confirm customer models creation
        self.assertEqual(Customer.objects.all().count(), 1)

        customer = Customer.objects.get(name=payload['name'])

        success_response = {
            'name': customer.name, 
            'email': customer.email, 
            'village_name': 'Village 1',
            'cluster_data': customer.get_cluster_data(),
            'non_null_phone': customer.get_non_null_phone(),
            'phone': customer.phone, 
            'address': customer.address, 
            'city': customer.city, 
            'region': customer.region, 
            'postal_code': customer.postal_code, 
            'country': customer.country, 
            'customer_code': customer.customer_code, 
            'credit_limit': str(customer.credit_limit), 
            'current_debt': Decimal('0.00'),
            'points': customer.points, 
            'reg_no': customer.reg_no
        }

        self.assertEqual(response.data, success_response)

        # Check model values
        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(customer.cluster, self.cluster)
        self.assertEqual(customer.name, payload['name'])
        self.assertEqual(customer.email, payload['email'])
        self.assertEqual(customer.village_name, payload['village_name'])
        self.assertEqual(customer.phone, payload['phone'])
        self.assertEqual(customer.address, payload['address'])
        self.assertEqual(customer.city, payload['city'])
        self.assertEqual(customer.region, payload['region'])
        self.assertEqual(customer.postal_code, payload['postal_code'])
        self.assertEqual(customer.country, payload['country'])
        self.assertEqual(customer.customer_code, payload['customer_code'])
        self.assertEqual(customer.credit_limit, payload['credit_limit'])
        self.assertEqual(customer.current_debt, 0.00)
        self.assertTrue(customer.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((customer.created_date).strftime("%B, %d, %Y"), today)


    def test_if_customer_cant_be_created_when_maintenance_mode_is_on(self):

        # Turn on maintenance mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        payload = self.get_premade_payload()

        response = self.client.post(reverse('api:tp_pos_customer_index'), payload)
        self.assertEqual(response.status_code, 401)

        # Confirm customer were not created
        self.assertEqual(Customer.objects.all().count(), 0)

    def test_if_a_customer_cant_be_created_when_new_customer_mode_is_off(self):
                
        # Turn off signups mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.new_customer = False
        ms.save()

        payload = self.get_premade_payload()
        
        response = self.client.post(reverse('api:tp_pos_customer_index'), payload)
        self.assertEqual(response.status_code, 423)

    def test_if_a_customer_cant_be_created_with_an_empty_name(self):

        payload = self.get_premade_payload()
  
        payload['name'] = ''

        response = self.client.post(reverse('api:tp_pos_customer_index'), payload)
        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_customer_cant_be_created_with_an_empty_cluster_reg_no(self):

        payload = self.get_premade_payload()
  
        payload['cluster_reg_no'] = ''

        response = self.client.post(reverse('api:tp_pos_customer_index'), payload)
        self.assertEqual(response.status_code, 400)

        result = {'cluster_reg_no': ['A valid integer is required.']}

        self.assertEqual(response.data, result)

    def test_if_a_customer_cant_be_created_with_a_wrong_cluster_reg_no(self):

        payload = self.get_premade_payload()
  
        payload['cluster_reg_no'] = 2000

        response = self.client.post(reverse('api:tp_pos_customer_index'), payload)
        self.assertEqual(response.status_code, 400)

        result = {'cluster_reg_no': ['Cluster does not exist.']}

        self.assertEqual(response.data, result)

    def test_if_a_user_cant_have_2_customers_with_the_same_unique_values(self):
        """
        Tests if user cant have 2 customers with the same name, email, phone or
        customer code
        """

        # Create a customer for profile 1
        existing_customer = create_new_customer(self.top_profile, 'chris')

        payload = self.get_premade_payload()
  
        payload['name'] = existing_customer.name
        payload['email'] = existing_customer.email
        payload['phone'] = existing_customer.phone
        payload['customer_code'] = existing_customer.customer_code
 
        response = self.client.post(reverse('api:tp_pos_customer_index'), payload)
        self.assertEqual(response.status_code, 400)

        result = {
            'name': ['You already have a customer with this name.'], 
            'email': ['You already have a customer with this email.'], 
            'phone': ['You already have a customer with this phone.'], 
            'customer_code': ['You already have a customer with this phone.']
        }
        
        self.assertEqual(response.data, result)
        
        # Confirm the customer was not created
        self.assertEqual(Customer.objects.all().count(), 1)

    def test_if_2_users_can_have_2_customers_with_the_same_unique_values(self):
        """
        Tests if 2 users can have 2 customers with the same name, email, phone or
        customer code
        """

        # Create a customer for profile 2
        existing_customer = create_new_customer(self.top_profile2, 'chris')

        payload = self.get_premade_payload()
  
        payload['name'] = existing_customer.name
        payload['email'] = existing_customer.email
        payload['phone'] = existing_customer.phone
        payload['customer_code'] = existing_customer.customer_code

        response = self.client.post(reverse('api:tp_pos_customer_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm customer model creation 
        self.assertEqual(Customer.objects.all().count(), 2)

    def test_if_customers_can_have_the_allowed_empty_fields_without_triggering_unique_validator_or_any_other_error(self):

        # Create a customer for profile 1
        existing_customer = create_new_customer(self.top_profile, 'chris')
        existing_customer.email = ''
        existing_customer.phone = 0
        existing_customer.address = ''
        existing_customer.city = ''
        existing_customer.region = ''
        existing_customer.postal_code = ''
        existing_customer.country = ''
        existing_customer.customer_code = ''
        existing_customer.credit_limit = 0
        existing_customer.customer_code = ''
        existing_customer.save()

        payload = self.get_premade_payload()

        payload['email'] = ''
        payload.pop('phone')
        payload['address'] = ''
        payload['city'] = ''
        payload['region'] = ''
        payload['postal_code'] = ''
        payload['country'] = ''
        payload['customer_code'] = ''
        payload['credit_limit'] = 0
        payload['customer_code'] = ''

        response = self.client.post(reverse('api:tp_pos_customer_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm customer model creation 
        self.assertEqual(Customer.objects.all().count(), 2)

    def test_if_a_customer_cant_be_created_with_a_wrong_email(self):

        wrong_emails = [
            "{}@gmail.com".format("x"*30), # Long email
            "wrongemailformat", # Wrong format
        ]

        i=0
        for email in wrong_emails:
            payload = self.get_premade_payload()

            payload['email'] = email

            response = self.client.post(
                reverse('api:tp_pos_customer_index'), payload)
            self.assertEqual(response.status_code, 400)

            if i==0:
             
                self.assertEqual(
                    response.data, 
                    {'email': ['Ensure this field has no more than 30 characters.']}
                )

            else:
                self.assertEqual(response.data, {'email': ['Enter a valid email address.']})

            i+=1

    def test_for_successful_customer_creation_with_correct_phones(self):

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
            payload['customer_code'] = f'code_{str(i)}' # This prevents unique error

            payload['phone'] = phone

            response = self.client.post(
                reverse('api:tp_pos_customer_index'), payload)
            self.assertEqual(response.status_code, 201)

            i+=1
            
        self.assertEqual(i, 8)

    def test_if_a_customer_cant_be_created_with_wrong_phones(self):

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
            payload['customer_code'] = f'code_{str(i)}' # This prevents unique error

            payload['phone'] = phone

            response = self.client.post(
                reverse('api:tp_pos_customer_index'), payload)

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

    def test_if_view_can_can_throttle_customer_creation(self):

        throttle_rate = int(settings.THROTTLE_RATES['api_customer_rate'].split("/")[0])

        for i in range(throttle_rate): # pylint: disable=unused-variable

            payload = self.get_premade_payload()
            
            payload['name'] = f'Chris {str(i)}' + str(i) # This prevents unique error
            payload['email'] = '' # This prevents unique error
            payload['customer_code'] = '' # This prevents unique error
            payload.pop('phone')  # This prevents unique error

            response = self.client.post(
                reverse('api:tp_pos_customer_index'), payload)
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
            payload['customer_code'] = '' # This prevents unique error
            payload.pop('phone')  # This prevents unique error

            response = self.client.post(
                reverse('api:tp_pos_customer_index'), payload)

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
            reverse('api:tp_pos_customer_index'), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_posted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.post(
            reverse('api:tp_pos_customer_index'), payload)
        self.assertEqual(response.status_code, 401)


class TpPosCustomerViewForEditingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create cluster
        self.cluster = StoreCluster.objects.create(name='Magadi')

        # Create a customer user
        self.customer = create_new_customer(self.top_profile1, 'chris')

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
            'name': 'New Customer',
            'email': 'customer@gmail.com',
            'village_name': 'Village 1',
            'phone': 254710101011,
            'address': 'Donholm',
            'city': 'Nairobi',
            'region': 'Africa',
            'postal_code': '11011',
            'country': 'Kenya',
            'customer_code': 'CustomerCode12',
            'credit_limit': 200.00,
            'cluster_reg_no': self.cluster.reg_no,
        }

        return payload

    def test_if_view_can_edit_a_customer(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        with self.assertNumQueries(14):
            response = self.client.put(
                reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), payload)
            self.assertEqual(response.status_code, 200)

        customer = Customer.objects.get(name=payload['name'])

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(customer.cluster, self.cluster)
        self.assertEqual(customer.name, payload['name'])
        self.assertEqual(customer.email, payload['email'])
        self.assertEqual(customer.village_name, payload['village_name'])
        self.assertEqual(customer.phone, payload['phone'])
        self.assertEqual(customer.address, payload['address'])
        self.assertEqual(customer.city, payload['city'])
        self.assertEqual(customer.region, payload['region'])
        self.assertEqual(customer.postal_code, payload['postal_code'])
        self.assertEqual(customer.country, payload['country'])
        self.assertEqual(customer.customer_code, payload['customer_code'])
        self.assertEqual(customer.credit_limit, payload['credit_limit'])
        self.assertEqual(customer.current_debt, 0.00)
        self.assertTrue(customer.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((customer.created_date).strftime("%B, %d, %Y"), today)

    def test_if_customer_cant_be_edited_when_maintenance_mode_is_on(self):

        # Turn on maintenance mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 401)

    def test_view_can_handle_a_wrong_reg_no(self):

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:tp_pos_customer_edit_view', args=(111111111,)), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_a_customer_cant_be_edited_with_an_empty_name(self):

        payload = self.get_premade_payload()
  
        payload['name'] = ''

        response = self.client.put(
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_customer_cant_be_created_with_an_empty_cluster_reg_no(self):

        payload = self.get_premade_payload()
  
        payload['cluster_reg_no'] = ''

        response = self.client.put(
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 400)

        result = {'cluster_reg_no': ['A valid integer is required.']}

        self.assertEqual(response.data, result)

    def test_if_a_customer_cant_be_created_with_a_wrong_cluster_reg_no(self):

        payload = self.get_premade_payload()
  
        payload['cluster_reg_no'] = 2000

        response = self.client.put(
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 400)

        result = {'cluster_reg_no': ['Cluster does not exist.']}

        self.assertEqual(response.data, result)

    def test_if_a_user_can_save_user_with_existing_values_without_raising_unique_validator(self):
        """
        Tests if user can save customer with them same values as before without
        raisng unique validator error
        """
        payload = self.get_premade_payload()
  
        payload['name'] = self.customer.name
        payload['email'] = self.customer.email
        payload['phone'] = self.customer.phone
        payload['customer_code'] = self.customer.customer_code
 
        response = self.client.put(
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)
        
    def test_if_a_user_cant_have_2_customers_with_the_same_unique_values(self):
        """
        Tests if user cant have 2 customers with the same name, email, phone or
        customer code
        """

        # Create a customer for profile 1
        existing_customer = create_new_customer(self.top_profile1, 'alex')

        payload = self.get_premade_payload()
  
        payload['name'] = existing_customer.name
        payload['email'] = existing_customer.email
        payload['phone'] = existing_customer.phone
        payload['customer_code'] = existing_customer.customer_code
 
        response = self.client.put(
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 400)

        result = {
            'name': ['You already have a customer with this name.'], 
            'email': ['You already have a customer with this email.'], 
            'phone': ['You already have a customer with this phone.'], 
            'customer_code': ['You already have a customer with this phone.']
        }
        
        self.assertEqual(response.data, result)

    def test_if_2_users_can_have_2_customers_with_the_same_unique_values(self):
        """
        Tests if 2 users can have 2 customers with the same name, email, phone or
        customer code
        """

        # Create a customer for profile 2
        existing_customer = create_new_customer(self.top_profile2, 'alex')

        payload = self.get_premade_payload()
  
        payload['name'] = existing_customer.name
        payload['email'] = existing_customer.email
        payload['phone'] = existing_customer.phone
        payload['customer_code'] = existing_customer.customer_code

        response = self.client.put(
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)

    def test_if_customers_can_have_the_allowed_empty_fields_without_triggering_unique_validator_or_any_other_error(self):

        # Create a customer for profile 1
        existing_customer = create_new_customer(self.top_profile1, 'alex')
        existing_customer.email = ''
        existing_customer.phone = 0
        existing_customer.address = ''
        existing_customer.city = ''
        existing_customer.region = ''
        existing_customer.postal_code = ''
        existing_customer.country = ''
        existing_customer.customer_code = ''
        existing_customer.credit_limit = 0
        existing_customer.customer_code = ''
        existing_customer.save()

        payload = self.get_premade_payload()

        payload['email'] = ''
        payload.pop('phone')
        payload['address'] = ''
        payload['city'] = ''
        payload['region'] = ''
        payload['postal_code'] = ''
        payload['country'] = ''
        payload['customer_code'] = ''
        payload['credit_limit'] = 0
        payload['customer_code'] = ''

        response = self.client.put(
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)

    def test_if_a_customer_cant_be_edited_with_a_wrong_email(self):

        wrong_emails = [
            "{}@gmail.com".format("x"*30), # Long email
            "wrongemailformat", # Wrong format
        ]

        i=0
        for email in wrong_emails:
            payload = self.get_premade_payload()

            payload['email'] = email

            response = self.client.put(
                reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), 
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

    def test_for_successful_customer_update_with_correct_phones(self):

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
            payload['customer_code'] = f'code_{str(i)}' # This prevents unique error

            payload['phone'] = phone

            response = self.client.put(
                reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), 
                payload
            )
            self.assertEqual(response.status_code, 200)

            i+=1
            
        self.assertEqual(i, 8)

    def test_if_a_customer_cant_be_edited_with_wrong_phones(self):

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
            payload['customer_code'] = f'code_{str(i)}' # This prevents unique error

            payload['phone'] = phone

            response = self.client.put(
                reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), 
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
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_updated_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 401)


class TpPosCustomerViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a customer user
        self.customer = create_new_customer(self.top_profile1, 'chris')

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
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)))
        self.assertEqual(response.status_code, 204)

        # Confirm the category was deleted
        self.assertEqual(Customer.objects.filter(
            reg_no=self.customer.reg_no).exists(), False
        )

    def test_view_can_handle_wrong_reg_no(self):

        response = self.client.delete(
            reverse('api:tp_pos_customer_edit_view', args=(44444,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the category was not deleted
        self.assertEqual(Customer.objects.filter(
            reg_no=self.customer.reg_no).exists(), True
        )

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the category was not deleted
        self.assertEqual(Customer.objects.filter(
            reg_no=self.customer.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_employee_user(self):

        # Login a employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the category was not deleted
        self.assertEqual(Customer.objects.filter(
            reg_no=self.customer.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:tp_pos_customer_edit_view', args=(self.customer.reg_no,)))
        self.assertEqual(response.status_code, 401)

        # Confirm the category was not deleted
        self.assertEqual(Customer.objects.filter(
            reg_no=self.customer.reg_no).exists(), True
        )
