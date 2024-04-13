
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from accounts.models import UserGroup

from core.test_utils.create_store_models import create_new_store
from core.test_utils.initial_user_data import (
    InitialUserDataMixin,
    FilterDatesMixin
)
from core.test_utils.custom_testcase import APITestCase
from core.test_utils.create_user import create_new_user

from profiles.models import Profile
from mysettings.models import MySetting
from stores.models import Store

User = get_user_model()


class TpLeanStoreIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

    def test_view_returns_the_user_stores_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(4):
            response = self.client.get(
                reverse('api:tp_store_index_lean'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'increamental_id': self.store2.increamental_id,
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deletion_date': self.store2.get_deleted_date(
                        self.top_profile1.user.get_user_timezone()
                    )
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'increamental_id': self.store1.increamental_id,
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deletion_date': self.store1.get_deleted_date(
                        self.top_profile1.user.get_user_timezone()
                    )
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:tp_store_index_lean'))
        self.assertEqual(response.status_code, 401) 

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all stores
        Store.objects.all().delete()

        model_num_to_be_created = settings.LEAN_PAGINATION_PAGE_SIZE+1

        store_names = []
        for i in range(model_num_to_be_created):
            store_names.append(f'New Store{i}')

        names_length = len(store_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)

        # Create and confirm stores
        for i in range(names_length):
            create_new_store(self.top_profile1, store_names[i])

        self.assertEqual(
            Store.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

        stores = Store.objects.filter(profile=self.top_profile1).order_by('-name')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(4):
            response = self.client.get(reverse('api:tp_store_index_lean'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/stores/lean/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(
            len(response_data_dict['results']), settings.LEAN_PAGINATION_PAGE_SIZE)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all store proifiles are listed except the first one since it's in the next paginated page #
        i = 0
        for store in stores[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], store.name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], store.reg_no)

            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, settings.LEAN_PAGINATION_PAGE_SIZE)

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
            reverse('api:tp_store_index_lean') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/stores/lean/',
            'results': [
                {
                    'name': stores[0].name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'increamental_id': stores[0].increamental_id,
                    'reg_no': stores[0].reg_no,
                    'is_deleted': stores[0].is_deleted,
                    'deletion_date': stores[0].get_deleted_date(
                        self.top_profile1.user.get_user_timezone()
                    )

                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        param = '?search=cloth'
        response = self.client.get(reverse('api:tp_store_index_lean') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'increamental_id': self.store2.increamental_id,
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deletion_date': self.store2.get_deleted_date(
                        self.top_profile1.user.get_user_timezone()
                    )
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_stores(self):

        # First delete all stores
        Store.objects.all().delete()

        response = self.client.get(
            reverse('api:tp_store_index_lean'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_store_index_lean'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_store_index_lean'))
        self.assertEqual(response.status_code, 401)

class TpLeanStoreWithReceiptSettingIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

    def test_view_returns_the_user_stores_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(6):
            response = self.client.get(
                reverse('api:tp_store_with_receipt_index_lean'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.store2.name,
                    'reg_no': self.store2.reg_no,
                    'receipt_setting': self.store2.get_receipt_setting(),
                    'is_deleted': self.store2.is_deleted,
                    'deletion_date': self.store2.get_deleted_date(
                        self.top_profile1.user.get_user_timezone()
                    )
                },
                {
                    'name': self.store1.name,
                    'reg_no': self.store1.reg_no,
                    'receipt_setting': self.store1.get_receipt_setting(),
                    'is_deleted': self.store1.is_deleted,
                    'deletion_date': self.store1.get_deleted_date(
                        self.top_profile1.user.get_user_timezone()
                    )
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:tp_store_with_receipt_index_lean'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all stores
        Store.objects.all().delete()

        model_num_to_be_created = settings.LEAN_PAGINATION_PAGE_SIZE+1

        store_names = []
        for i in range(model_num_to_be_created):
            store_names.append(f'New Store{i}')

        names_length = len(store_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)

        # Create and confirm stores
        for i in range(names_length):
            create_new_store(self.top_profile1, store_names[i])

        self.assertEqual(
            Store.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

        stores = Store.objects.filter(profile=self.top_profile1).order_by('-name')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(204):
            response = self.client.get(reverse('api:tp_store_with_receipt_index_lean'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/stores_with_receipt/lean/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(
            len(response_data_dict['results']), settings.LEAN_PAGINATION_PAGE_SIZE)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all store proifiles are listed except the first one since it's in the next paginated page #
        i = 0
        for store in stores[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], store.name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], store.reg_no)

            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, settings.LEAN_PAGINATION_PAGE_SIZE)

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
            reverse('api:tp_store_with_receipt_index_lean') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/stores_with_receipt/lean/',
            'results': [
                {
                    'name': stores[0].name,
                    'reg_no': stores[0].reg_no,
                    'receipt_setting': stores[0].get_receipt_setting(),
                    'is_deleted': stores[0].is_deleted,
                    'deletion_date': stores[0].get_deleted_date(
                        self.top_profile1.user.get_user_timezone()
                    )
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        param = '?search=cloth'
        response = self.client.get(reverse('api:tp_store_with_receipt_index_lean') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': 'Cloth Store',
                    'reg_no': self.store2.reg_no,
                    'receipt_setting': self.store2.get_receipt_setting(),
                    'is_deleted': self.store2.is_deleted,
                    'deletion_date': self.store2.get_deleted_date(
                        self.top_profile1.user.get_user_timezone()
                    )
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_stores(self):

        # First delete all stores
        Store.objects.all().delete()

        response = self.client.get(
            reverse('api:tp_store_with_receipt_index_lean'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_store_with_receipt_index_lean'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_store_with_receipt_index_lean'))
        self.assertEqual(response.status_code, 401)

class TpStoreIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

    def remove_can_view_stores_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_stores')

        manager_group.permissions.remove(permission)
  
    def test_view_returns_the_user_empoyees_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(9):
            response = self.client.get(
                reverse('api:tp_store_index'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.store2.name,
                    'address': self.store2.address,
                    'reg_no': self.store2.reg_no,
                    'employee_count': self.store2.get_employee_count()
                },
                {
                    'name': self.store1.name,
                    'address': self.store1.address,
                    'reg_no': self.store1.reg_no,
                    'employee_count': self.store1.get_employee_count()
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:tp_store_index'))
        self.assertEqual(response.status_code, 401)

    def test_view_does_not_return_soft_deleted(self):

        # Soft delete store 1
        self.store1.soft_delete()

        # Soft delete store 2
        self.store2.soft_delete()

        response = self.client.get(
            reverse('api:tp_store_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0,
            'next': None,
            'previous': None,
            'results': []
        }

        self.assertEqual(response.data, result)

    def test_if_view_cant_be_viewed_by_user_with_no_can_view_stores_perm(self):

        self.remove_can_view_stores_perm()
        
        response = self.client.get(reverse('api:tp_store_index'))
        self.assertEqual(response.status_code, 403)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        page_size = 200

        # First delete all stores
        Store.objects.all().delete()

        model_num_to_be_created = page_size+1

        store_names = []
        for i in range(model_num_to_be_created):
            store_names.append(f'New Store{i}')

        names_length = len(store_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm stores
        for i in range(names_length):
            store = create_new_store(self.top_profile1, store_names[i])

        self.assertEqual(
            Store.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

    
        stores = Store.objects.filter(profile=self.top_profile1).order_by('-name')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(207):
            response = self.client.get(reverse('api:tp_store_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/stores/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), settings.LEAN_PAGINATION_PAGE_SIZE)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all store proifiles are listed except the first one since it's in the next paginated page #
        i = 0
        for store in stores[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], store.name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], store.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, settings.LEAN_PAGINATION_PAGE_SIZE)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:tp_store_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/stores/',
            'results': [
                {
                    'name': stores[0].name,
                    'address': stores[0].address,
                    'reg_no': stores[0].reg_no,
                    'employee_count': stores[0].get_employee_count()
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        param = '?search=cloth'
        response = self.client.get(reverse('api:tp_store_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.store2.name,
                    'address': self.store2.address,
                    'reg_no': self.store2.reg_no,
                    'employee_count': self.store2.get_employee_count()
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_stores(self):

        # First delete all stores
        Store.objects.all().delete()

        response = self.client.get(
            reverse('api:tp_store_index'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_store_index'))
        self.assertEqual(response.status_code, 401)


class TpStoreIndexViewForCreatingTestCase(APITestCase):

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

    def remove_can_view_stores_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile.user, 
            ident_name='Owner',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_stores')

        manager_group.permissions.remove(permission)

    def test_if_view_can_create_a_store(self):

        payload = {
            'name': 'New Store',
            'address': 'Nairobi',
        }

        # Count Number of Queries
        with self.assertNumQueries(19):
            response = self.client.post(reverse('api:tp_store_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Confirm Store models creation
        self.assertEqual(Store.objects.all().count(), 1)

        store = Store.objects.get(name='New Store')

        self.assertEqual(store.profile.user.email, 'john@gmail.com')
        self.assertEqual(store.name, 'New Store')
        self.assertEqual(store.address, 'Nairobi')

    def test_if_view_cant_be_viewed_by_user_with_no_can_view_stores_perm(self):

        self.remove_can_view_stores_perm()

        payload = {
            'name': 'New Store',
            'address': 'Nairobi',
        }
        
        response = self.client.post(reverse('api:tp_store_index'), payload)
        self.assertEqual(response.status_code, 403)

    def test_if_a_store_cant_be_created_with_an_empty_name(self):

        payload = {
            'name': '',
            'address': 'Nairobi',
        }

        response = self.client.post(reverse('api:tp_store_index'), payload)
        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_user_cant_have_2_stores_with_the_same_name(self):

        create_new_store(self.top_profile, 'Computer Store')

        payload = {
            'name': 'Computer Store',
            'address': 'Nairobi',
        }

        response = self.client.post(reverse('api:tp_store_index'), payload)
        self.assertEqual(response.status_code, 400)

        result = {'name': ['You already have a store with this name.']}

        self.assertEqual(response.data, result)

        # Confirm the store was not created
        self.assertEqual(Store.objects.all().count(), 1)

    def test_if_2_users_can_have_2_stores_with_the_same_name(self):

        create_new_store(self.top_profile2, 'Computer Store')

        payload = {
            'name': 'Computer Store',
            'address': 'Nairobi',
        }

        response = self.client.post(reverse('api:tp_store_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm store model creation
        self.assertEqual(Store.objects.all().count(), 2)

    def test_if_store_cant_be_created_when_maintenance_mode_is_on(self):

        # Turn on maintenance mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        payload = {
            'name': 'New Store',
            'address': 'Nairobi',
        }

        response = self.client.post(
            reverse('api:tp_store_index'), payload)
        self.assertEqual(response.status_code, 401)

        # Confirm store were not created
        self.assertEqual(Store.objects.all().count(), 0)

    def test_if_view_can_can_throttle_store_creation(self):

        throttle_rate = int(
            settings.THROTTLE_RATES['api_store_rate'].split("/")[0])

        for i in range(throttle_rate):  # pylint: disable=unused-variable
            payload = {
                'name': f'New Store{i}',
                'address': 'Nairobi',
            }

            response = self.client.post(
                reverse('api:tp_store_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional
        # request if the previous request was not throttled
        for i in range(throttle_rate):  # pylint: disable=unused-variable

            # Try to see if the next request will be throttled
            new_payload = {
                'name': f'New Store{i+1}',
                'address': 'Nairobi',
            }

            response = self.client.post(
                reverse('api:tp_store_index'), new_payload)

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else:
            # Executed because break was not called. This means the request was
            # never throttled
            self.fail()

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = {
            'name': 'New Store',
            'address': 'Nairobi',
        }

        response = self.client.post(
            reverse('api:tp_store_index'), payload)
        self.assertEqual(response.status_code, 401)


class TpStoreEditViewForViewingTestCase(APITestCase, InitialUserDataMixin, FilterDatesMixin):

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

    def remove_can_view_stores_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_stores')

        manager_group.permissions.remove(permission)

    def test_view_can_be_called_successefully(self):

        # Count Number of Queries #
        with self.assertNumQueries(6):
            response = self.client.get(
                reverse('api:tp_store_edit_view', args=(self.store1.reg_no,)))
            self.assertEqual(response.status_code, 200)

        result = {
            'name': self.store1.name,
            'address': self.store1.address,
            'reg_no': self.store1.reg_no,
        }

        self.assertEqual(response.data, result)

        ########################## Test maintaince ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
            reverse('api:tp_store_edit_view', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)

    def test_if_view_cant_be_viewed_by_user_with_no_can_view_stores_perm(self):

        self.remove_can_view_stores_perm()

        response = self.client.get(
            reverse('api:tp_store_edit_view', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 403)

    def test_view_can_handle_wrong_reg_no(self):

        response = self.client.get(
            reverse('api:tp_store_edit_view', args=(4646464,)))
        self.assertEqual(response.status_code, 404)

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:tp_store_edit_view',
                    args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:tp_store_edit_view', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)


class TpStoreEditViewForEditingTestCase(APITestCase, InitialUserDataMixin):

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

    def remove_can_view_stores_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_stores')

        manager_group.permissions.remove(permission)

    def test_view_can_edit_a_store(self):

        payload = {
            'name': 'New Store',
            'address': 'Mombasa',
        }

        # Count Number of Queries #
        with self.assertNumQueries(8):
            response = self.client.put(reverse(
                'api:tp_store_edit_view', args=(self.store1.reg_no,)), payload)
            self.assertEqual(response.status_code, 200)

        # Confirm Store was changed
        store = Store.objects.get(name='New Store')

        self.assertEqual(store.profile.user.email, 'john@gmail.com')
        self.assertEqual(store.name, payload['name'])
        self.assertEqual(store.address, payload['address'])

    def test_if_view_cant_be_viewed_by_user_with_no_can_view_stores_perm(self):

        self.remove_can_view_stores_perm()

        payload = {
            'name': 'New Store',
            'address': 'Mombasa',
        }

        response = self.client.put(reverse(
                'api:tp_store_edit_view', args=(self.store1.reg_no,)), payload)
        self.assertEqual(response.status_code, 403)

    def test_if_a_store_cant_be_edited_with_an_empty_name(self):

        payload = {
            'name': '',
            'address': 'Mombasa',
        }

        response = self.client.put(
            reverse('api:tp_store_edit_view', args=(self.store1.reg_no,)), payload)
        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_user_cant_have_2_stores_with_the_same_name(self):

        payload = {
            'name': self.store2.name,
            'address': 'Mombasa',
        }

        response = self.client.put(
            reverse('api:tp_store_edit_view', args=(self.store1.reg_no,)), payload)
        self.assertEqual(response.status_code, 400)

        result = {'name': ['You already have a store with this name.']}

        self.assertEqual(response.data, result)

        # Check that edit store was not successful
        self.assertEqual(
            Store.objects.filter(name=self.store2.name).count(), 1
        )

    def test_if_2_users_can_have_2_stores_with_the_same_name(self):

        payload = {
            'name': self.store3.name,
            'address': 'Mombasa',
        }

        response = self.client.put(reverse(
            'api:tp_store_edit_view', args=(self.store1.reg_no,)), payload)
        self.assertEqual(response.status_code, 200)

        # Check that edit store was successful
        self.assertEqual(
            Store.objects.filter(name=self.store3.name).count(), 2
        )

    def test_if_store_unchange_name_can_be_saved_without_raising_duplicate_error(self):

        payload = {
            'name': self.store1.name,
            'address': 'Mombasa',
        }

        response = self.client.put(reverse(
            'api:tp_store_edit_view', args=(self.store1.reg_no,)), payload)
        self.assertEqual(response.status_code, 200)

    def test_view_can_handle_a_wrong_reg_no(self):

        payload = {
            'name': 'New Store',
            'address': 'Mombasa',
        }

        response = self.client.put(
            reverse('api:tp_store_edit_view', args=(111111111,)), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_view_can_only_be_changed_by_its_owner(self):

        # Login a top user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = {
            'name': 'New Store',
            'address': 'Mombasa',
        }

        response = self.client.put(reverse(
            'api:tp_store_edit_view', args=(self.store1.reg_no,)), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_changed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = {
            'name': 'New Store',
            'address': 'Mombasa',
        }

        response = self.client.put(reverse(
            'api:tp_store_edit_view', args=(self.store1.reg_no,)), payload)
        self.assertEqual(response.status_code, 401)

class TpStoreEditViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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

    def remove_can_view_stores_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_stores')

        manager_group.permissions.remove(permission)

    def test_view_can_delete_a_store(self):

        response = self.client.delete(
            reverse('api:tp_store_edit_view', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 204)

        # Confirm the store was soft deleted
        self.assertEqual(
            Store.objects.get(reg_no=self.store1.reg_no).is_deleted, 
            True
        )
        
    def test_if_view_cant_be_viewed_by_user_with_no_can_view_stores_perm(self):

        self.remove_can_view_stores_perm()

        response = self.client.delete(
            reverse('api:tp_store_edit_view', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 403)

        self.assertEqual(
            Store.objects.get(reg_no=self.store1.reg_no).is_deleted, 
            False
        )

    def test_view_can_handle_wrong_reg_no(self):

        response = self.client.delete(
            reverse('api:tp_store_edit_view', args=(44444,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the store was not deleted
        self.assertEqual(
            Store.objects.get(reg_no=self.store1.reg_no).is_deleted, 
            False
        )

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:tp_store_edit_view', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the store was not deleted
        self.assertEqual(
            Store.objects.get(reg_no=self.store1.reg_no).is_deleted, 
            False
        )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:tp_store_edit_view', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)

        # Confirm the store was not deleted
        self.assertEqual(
            Store.objects.get(reg_no=self.store1.reg_no).is_deleted, 
            False
        )
