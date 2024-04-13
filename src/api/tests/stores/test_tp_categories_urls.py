import json
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.create_store_models import create_new_store, create_new_category
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
from inventories.models import Product

from profiles.models import EmployeeProfile, Profile
from mysettings.models import MySetting
from stores.models import Category
from accounts.models import UserGroup

User = get_user_model()


class TpLeanCategoryIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create categories for top user 1
        self.category1 = create_new_category(self.top_profile1, 'Category1')
        self.category2 = create_new_category(self.top_profile1, 'Category2')

        # Create categories for top user 2
        self.category3 = create_new_category(self.top_profile2, 'Category3')


        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
    def test_view_returns_the_user_categories_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(4):
            response = self.client.get(
                reverse('api:category_index_lean'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': 'Category2', 
                    'reg_no': self.category2.reg_no
                }, 
                {
                    'name': 'Category1', 
                    'reg_no': self.category1.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:category_index_lean'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all categories
        Category.objects.all().delete()

        pagination_page_size = settings.LEAN_PAGINATION_PAGE_SIZE

        model_num_to_be_created = pagination_page_size+1

        category_names = []
        for i in range(model_num_to_be_created):
            category_names.append(f'New Category{i}')

        names_length = len(category_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm categories
        for i in range(names_length):
            create_new_category(self.top_profile1, category_names[i])

        self.assertEqual(
            Category.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

    
        categories = Category.objects.filter(profile=self.top_profile1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(4):
            response = self.client.get(reverse('api:category_index_lean'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/categories/lean/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all categories are listed except the first one since it's in the next paginated page #
        i = 0
        for category in categories[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], category.name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], category.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:category_index_lean') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/categories/lean/',
            'results': [
                {
                    'name': categories[0].name,   
                    'reg_no': categories[0].reg_no,
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        param = '?search=Category1'
        response = self.client.get(reverse('api:category_index_lean') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': 'Category1', 
                    'reg_no': self.category1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_returns_empty_when_there_are_no_categories(self):

        # First delete all categories
        Category.objects.all().delete()

        response = self.client.get(
            reverse('api:category_index_lean'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:category_index_lean'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:category_index_lean'))
        self.assertEqual(response.status_code, 401)

class TpPosCategoryIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create categories for top user 1
        self.category1 = create_new_category(self.top_profile1, 'Category1')
        self.category2 = create_new_category(self.top_profile1, 'Category2')

        # Create categories for top user 2
        self.category3 = create_new_category(self.top_profile2, 'Category3')

        # Create products
        # Create 2 products for category 1
        Product.objects.create(
            profile=self.top_profile1,
            category=self.category1,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        Product.objects.create(
            profile=self.top_profile1,
            category=self.category1,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        # Create 1 product for category 1
        Product.objects.create(
            profile=self.top_profile1,
            category=self.category2,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_returns_the_user_categories_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(5):
            response = self.client.get(
                reverse('api:pos_category_index'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': 'Category1', 
                    'color_code': '#474A49', 
                    'product_count': 2,
                    'reg_no': self.category1.reg_no
                },
                {
                    'name': 'Category2', 
                    'color_code': '#474A49', 
                    'product_count': 1,
                    'reg_no': self.category2.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:pos_category_index'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination_from_pos(self):

        # First delete all categories
        Category.objects.all().delete()

        pagination_page_size = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION

        model_num_to_be_created = pagination_page_size+1

        category_names = []
        for i in range(model_num_to_be_created):
            category_names.append(f'New Category{i}')

        names_length = len(category_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm categories
        for i in range(names_length):
            create_new_category(self.top_profile1, category_names[i])

        self.assertEqual(
            Category.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

    
        categories = Category.objects.filter(profile=self.top_profile1).order_by('-id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(5):
            response = self.client.get(reverse('api:pos_category_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/pos/categories/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all categories are listed except the first one since it's in the next paginated page #
        i = 0
        for category in categories[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], category.name)
            self.assertEqual(
                response_data_dict['results'][i]['color_code'], category.color_code)
            self.assertEqual(
                response_data_dict['results'][i]['product_count'], category.product_count)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], category.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:pos_category_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/pos/categories/',
            'results': [
                {
                    'name': categories[0].name,  
                    'color_code': categories[0].color_code, 
                    'product_count': categories[0].product_count,  
                    'reg_no': categories[0].reg_no,
                }
            ]
        }

        self.assertEqual(response.data, result)

        # Confirm pos ordering
        self.assertEqual(categories[0].name, f'New Category{pagination_page_size}')

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination_from_web(self):

        # First delete all categories
        Category.objects.all().delete()

        pagination_page_size = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION

        model_num_to_be_created = pagination_page_size+1

        category_names = []
        for i in range(model_num_to_be_created):
            category_names.append(f'New Category{i}')

        names_length = len(category_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm categories
        for i in range(names_length):
            create_new_category(self.top_profile1, category_names[i])

        self.assertEqual(
            Category.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

    
        categories = Category.objects.filter(profile=self.top_profile1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(5):
            response = self.client.get(reverse('api:category_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/categories/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all categories are listed except the first one since it's in the next paginated page #
        i = 0
        for category in categories[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], category.name)
            self.assertEqual(
                response_data_dict['results'][i]['color_code'], category.color_code)
            self.assertEqual(
                response_data_dict['results'][i]['product_count'], category.product_count)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], category.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:category_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/categories/',
            'results': [
                {
                    'name': categories[0].name,  
                    'color_code': categories[0].color_code, 
                    'product_count': categories[0].product_count,  
                    'reg_no': categories[0].reg_no,
                }
            ]
        }

        self.assertEqual(response.data, result)

        # Confirm non pos ordering
        self.assertEqual(categories[0].name, 'New Category0')

    def test_view_can_perform_search(self):

        param = '?search=Category1'
        response = self.client.get(reverse('api:category_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': 'Category1', 
                    'color_code': '#474A49', 
                    'product_count': 2,
                    'reg_no': self.category1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_returns_empty_when_there_are_no_categories(self):

        # First delete all categories
        Category.objects.all().delete()

        response = self.client.get(
            reverse('api:pos_category_index'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:pos_category_index'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:pos_category_index'))
        self.assertEqual(response.status_code, 401)


class TpPosCategoryIndexViewForCreatingTestCase(APITestCase):

    def setUp(self):

        # Create a top user1
        self.user1 = create_new_user('john')

        self.top_profile = Profile.objects.get(user__email='john@gmail.com')

        #Create store for user 1
        self.store = create_new_store(self.top_profile, 'Computer Store')

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

    def remove_can_view_items_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_items')

        manager_group.permissions.remove(permission)

    def test_if_view_can_create_a_category(self):

        payload = {
            'name': 'New Category',
            'color_code': '#474A49',
        }

        # Count Number of Queries
        with self.assertNumQueries(13):
            response = self.client.post(
                reverse('api:pos_category_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Confirm category models creation
        self.assertEqual(Category.objects.all().count(), 1)

        category = Category.objects.get(name='New Category')

        success_response = {
            'name': category.name, 
            'color_code': category.color_code, 
            'product_count': 0, 
            'reg_no': category.reg_no
        }

        self.assertEqual(response.data, success_response)

        # Check model values
        self.assertEqual(category.profile.user.email, 'john@gmail.com')
        self.assertEqual(category.name, payload['name'])
        self.assertEqual(category.color_code, payload['color_code']) 

    def test_if_a_category_cant_be_created_with_an_empty_name(self):

        payload = {
            'name': '',
            'color_code': '#474A49',
        }

        response = self.client.post(reverse('api:pos_category_index'), payload)
        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_user_cant_have_2_categories_with_the_same_name(self):

        create_new_category(self.top_profile, 'New Category')

        payload = {
            'name': 'New Category',
            'color_code': '#474A49',
        }

        response = self.client.post(reverse('api:pos_category_index'), payload)
        self.assertEqual(response.status_code, 400)
        
        result = {'name': ['You already have a category with this name.']}
        
        self.assertEqual(response.data, result)
        
        # Confirm the category was not created
        self.assertEqual(Category.objects.all().count(), 1)
    
    def test_if_2_users_can_have_2_categories_with_the_same_name(self):

        create_new_category(self.top_profile2, 'New Category')

        payload = {
            'name': 'New Category',
            'color_code': '#474A49',
        }

        response = self.client.post(reverse('api:pos_category_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm category model creation 
        self.assertEqual(Category.objects.all().count(), 2)

    def test_if_a_category_cant_be_created_with_an_empty_color_code(self):

        payload = {
            'name': 'New Category',
            'color_code': '',
        }

        response = self.client.post(reverse('api:pos_category_index'), payload)
        self.assertEqual(response.status_code, 400)

        result = {'color_code': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_category_cant_be_created_with_an_wrong_color_code(self):

        wrong_color_codes = [
            '1474A49', # Does not start with #
            '4#74A49', # Does not start with #
            '#474A499' # has more than 7 character
        ]
        
        i=0
        for code in wrong_color_codes:
            payload = {
                'name': 'New Category',
                'color_code': code,
            }

            response = self.client.post(reverse('api:pos_category_index'), payload)
            self.assertEqual(response.status_code, 400)

            if i == 2:
                result = {'color_code': ['Ensure this field has no more than 7 characters.']}
            else:
                result = {'color_code': ['Wrong color code.']}
            
            self.assertEqual(response.data, result)

            i+=1
        
    def test_if_category_cant_be_created_when_maintenance_mode_is_on(self):

        # Turn on maintenance mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        payload = {
            'name': 'New Category',
            'color_code': '#474A49',
        }

        response = self.client.post(
            reverse('api:pos_category_index'), payload)
        self.assertEqual(response.status_code, 401)

        # Confirm category were not created
        self.assertEqual(Category.objects.all().count(), 0)

    def test_if_view_can_can_throttle_category_creation(self):

        throttle_rate = int(
            settings.THROTTLE_RATES['api_category_rate'].split("/")[0])

        for i in range(throttle_rate): # pylint: disable=unused-variable
            payload = {
                'name': f'New Category{i}',
                'color_code': '#474A49',
            }

            response = self.client.post(
                reverse('api:pos_category_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional
        # request if the previous request was not throttled
        for i in range(throttle_rate): # pylint: disable=unused-variable

            # Try to see if the next request will be throttled
            new_payload = {
                'name': f'New Category{i+1}',
                'color_code': '#474A49',
            }

            response = self.client.post(
                reverse('api:pos_category_index'), new_payload)

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else:
            # Executed because break was not called. This means the request was
            # never throttled
            self.fail()

    def test_if_view_cant_be_viewed_by_an_employee_user(self):

        create_new_manager_user("gucci", self.top_profile, self.store)

        self.manager_profile1 = EmployeeProfile.objects.get(user__email='gucci@gmail.com')

        # Make a single payment so that the manager will be qualified
        make_payment(self.user1, self.manager_profile1.reg_no, 1)

        # Login a employee profile #
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = {
            'name': 'New Category',
            'color_code': '#474A49',
        }

        response = self.client.post(
            reverse('api:pos_category_index'), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = {
            'name': 'New Category',
            'color_code': '#474A49',
        }

        response = self.client.post(
            reverse('api:pos_category_index'), payload)
        self.assertEqual(response.status_code, 401)


class TpCategoryEditViewForViewingTestCase(APITestCase, InitialUserDataMixin, FilterDatesMixin):

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

        # Create categories for top user 1
        self.category1 = create_new_category(self.top_profile1, 'Category1')
        self.category2 = create_new_category(self.top_profile1, 'Category2')

        # Create categories for top user 2
        self.category3 = create_new_category(self.top_profile2, 'Category3')


        # Create products
        # Create 2 products for category 1
        Product.objects.create(
            profile=self.top_profile1,
            category=self.category1,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        Product.objects.create(
            profile=self.top_profile1,
            category=self.category1,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        # Create 1 product for category 1
        Product.objects.create(
            profile=self.top_profile1,
            category=self.category2,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )


        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def remove_can_view_items_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_items')

        manager_group.permissions.remove(permission)

    def test_view_can_be_called_successefully(self):

        # Count Number of Queries #
        with self.assertNumQueries(4):
            response = self.client.get(
                reverse('api:category_edit_view', args=(self.category1.reg_no,)))
            self.assertEqual(response.status_code, 200)

        result = {
            'name': self.category1.name,
            'color_code': str(self.category1.color_code),
            'product_count': self.category1.product_count,
            'reg_no': self.category1.reg_no,
        }

        self.assertEqual(response.data, result)

        ########################## Test maintaince ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
            reverse('api:category_edit_view', args=(self.category1.reg_no,)))
        self.assertEqual(response.status_code, 401)

    def test_view_can_handle_wrong_reg_no(self):

        response = self.client.get(
            reverse('api:category_edit_view', args=(4646464,)))
        self.assertEqual(response.status_code, 404)

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:category_edit_view',
                    args=(self.category1.reg_no,)))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:category_edit_view', args=(self.category1.reg_no,)))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:category_edit_view', args=(self.category1.reg_no,)))
        self.assertEqual(response.status_code, 401)

class TpCategoryEditViewForEditingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create categories for top user 1
        self.category1 = create_new_category(self.top_profile1, 'Category1')
        self.category2 = create_new_category(self.top_profile1, 'Category2')

        # Create categories for top user 2
        self.category3 = create_new_category(self.top_profile2, 'Category3')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def remove_can_view_items_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_items')

        manager_group.permissions.remove(permission)

    def test_view_can_edit_a_category(self):

        payload = {
            'name': 'New Category',
            'color_code': '#004A49',
        }

        # Count Number of Queries #
        with self.assertNumQueries(10):
            response = self.client.put(reverse(
                'api:category_edit_view', args=(self.category1.reg_no,)), payload)
            self.assertEqual(response.status_code, 200)

        # Confirm category was changed
        category = Category.objects.get(name='New Category')
  
        self.assertEqual(category.profile.user.email, 'john@gmail.com')
        self.assertEqual(category.name, payload['name'])
        self.assertEqual(category.color_code, payload['color_code'])

    def test_if_a_category_cant_be_edited_with_an_empty_name(self):
        
        payload = {
            'name': '',
            'color_code': '#004A49',
        }
        
        response = self.client.put(
            reverse('api:category_edit_view', args=(self.category1.reg_no,)), payload)
        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}
        
        self.assertEqual(response.data, result) 

    def test_if_a_user_cant_have_2_categories_with_the_same_name(self):

        payload = {
            'name': self.category2.name,
            'color_code': '#004A49',
        }

        response = self.client.put(
            reverse('api:category_edit_view', args=(self.category1.reg_no,)), payload)
        self.assertEqual(response.status_code, 400)

        result = {'name': ['You already have a category with this name.']}
        
        self.assertEqual(response.data, result)

        # Check that edit category was not successful
        self.assertEqual(
            Category.objects.filter(name=self.category2.name).count()
            ,1
        )

    def test_if_2_users_can_have_2_categories_with_the_same_name(self):

        payload = {
            'name': self.category3.name,
            'color_code': '#004A49',
        }

        response = self.client.put(reverse(
            'api:category_edit_view', args=(self.category1.reg_no,)), payload)
        self.assertEqual(response.status_code, 200)
        
        # Check that edit category was successful
        self.assertEqual(
            Category.objects.filter(name=self.category3.name).count()
            ,2
        )

    def test_if_category_unchange_name_can_be_saved_without_raising_duplicate_error(self):
        
        payload = {
            'name': self.category1.name,
            'color_code': '#004A49',
        }
        
        response = self.client.put(reverse(
            'api:category_edit_view', args=(self.category1.reg_no,)), payload)
        self.assertEqual(response.status_code, 200)

        # Check that edit category was successful
        self.assertEqual(
            Category.objects.filter(name=self.category1.name).count()
            ,1
        )

    def test_if_a_category_cant_be_created_with_an_empty_color_code(self):

        payload = {
            'name': 'New Category',
            'color_code': '',
        }

        response = self.client.put(reverse(
            'api:category_edit_view', args=(self.category1.reg_no,)), payload)
        self.assertEqual(response.status_code, 400)

        result = {'color_code': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_category_cant_be_created_with_an_wrong_color_code(self):

        wrong_color_codes = [
            '1474A49', # Does not start with #
            '4#74A49', # Does not start with #
            '#474A499' # has more than 7 character
        ]
        
        i=0
        for code in wrong_color_codes:
            payload = {
                'name': 'New Category',
                'color_code': code,
            }

            response = self.client.put(reverse(
            'api:category_edit_view', args=(self.category1.reg_no,)), payload)
            self.assertEqual(response.status_code, 400)

            if i == 2:
                result = {'color_code': ['Ensure this field has no more than 7 characters.']}
            else:
                result = {'color_code': ['Wrong color code.']}
            
            self.assertEqual(response.data, result)

            i+=1

    def test_view_can_handle_a_wrong_reg_no(self):

        payload = {
            'name': 'New Category',
            'color_code': '#004A49',
        }

        response = self.client.put(
            reverse('api:category_edit_view', args=(111111111,)), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_view_can_only_be_changed_by_its_owner(self):

        # Login a top user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = {
            'name': 'New Category',
            'color_code': '#004A49',
        }

        response = self.client.put(reverse(
            'api:category_edit_view', args=(self.category1.reg_no,)), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_changed_by_an_employee_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = {
            'name': 'New Category',
            'color_code': '#004A49',
        }

        response = self.client.put(reverse(
            'api:category_edit_view', args=(self.category1.reg_no,)), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_changed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = {
            'name': 'New Category',
            'color_code': '#004A49',
        }

        response = self.client.put(reverse(
            'api:category_edit_view', args=(self.category1.reg_no,)), payload)
        self.assertEqual(response.status_code, 401)


class TpCategoryEditViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create categories for top user 1
        self.category1 = create_new_category(self.top_profile1, 'Category1')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def remove_can_view_items_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_items')

        manager_group.permissions.remove(permission)

    def test_view_can_delete_a_category(self):

        response = self.client.delete(
            reverse('api:category_edit_view', args=(self.category1.reg_no,)))
        self.assertEqual(response.status_code, 204)

        # Confirm the category was deleted
        self.assertEqual(Category.objects.filter(
            reg_no=self.category1.reg_no).exists(), False
        )

    def test_view_can_handle_wrong_reg_no(self):

        response = self.client.delete(
            reverse('api:category_edit_view', args=(44444,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the category was not deleted
        self.assertEqual(Category.objects.filter(
            reg_no=self.category1.reg_no).exists(), True
        )

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:category_edit_view', args=(self.category1.reg_no,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the category was not deleted
        self.assertEqual(Category.objects.filter(
            reg_no=self.category1.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_employee_user(self):

        # Login a employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:category_edit_view', args=(self.category1.reg_no,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the category was not deleted
        self.assertEqual(Category.objects.filter(
            reg_no=self.category1.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:category_edit_view', args=(self.category1.reg_no,)))
        self.assertEqual(response.status_code, 401)

        # Confirm the category was not deleted
        self.assertEqual(Category.objects.filter(
            reg_no=self.category1.reg_no).exists(), True
        )