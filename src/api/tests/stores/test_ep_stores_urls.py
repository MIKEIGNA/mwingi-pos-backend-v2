import json
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.create_store_models import create_new_store
from core.test_utils.initial_user_data import InitialUserDataMixin
from core.test_utils.custom_testcase import APITestCase

from mysettings.models import MySetting
from stores.models import Store
from accounts.models import UserGroup

User = get_user_model()

class EpLeanStoreIndexViewTestCase(APITestCase, InitialUserDataMixin):

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
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_returns_the_user_stores_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(4):
            response = self.client.get(
                reverse('api:ep_store_index_lean'))
            self.assertEqual(response.status_code, 200)

        result = result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
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

        response = self.client.get(reverse('api:ep_store_index_lean'))
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
            store = create_new_store(self.top_profile1, store_names[i])
            self.manager_profile1.stores.add(store)

        self.assertEqual(
            Store.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

    
        stores = Store.objects.filter(profile=self.top_profile1).order_by('-name')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(4):
            response = self.client.get(reverse('api:ep_store_index_lean'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/ep/stores/lean/?page=2')
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
        response = self.client.get(reverse('api:ep_store_index_lean') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/ep/stores/lean/',
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

        # Increase user's store count
        self.manager_profile1.stores.add(self.store2)

        param = '?search=cloth'
        response = self.client.get(reverse('api:ep_store_index_lean') + param)
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
            reverse('api:ep_store_index_lean'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_if_employee_without_store_access_will_receive_empty_list(self):

        # Remove store from employee profile
        self.manager_profile1.stores.remove(self.store1)

        response = self.client.get(
            reverse('api:ep_store_index_lean'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_a_top_user(self):

        # Login an top user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:ep_store_index_lean'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:ep_store_index_lean'))
        self.assertEqual(response.status_code, 401)

class EpLeanStoreWithReceiptSettingIndexViewTestCase(APITestCase, InitialUserDataMixin):

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
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_returns_the_user_stores_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(5):
            response = self.client.get(
                reverse('api:ep_store_with_receipt_index_lean'))
            self.assertEqual(response.status_code, 200)

        result = result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
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

        response = self.client.get(reverse('api:ep_store_with_receipt_index_lean'))
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
            store = create_new_store(self.top_profile1, store_names[i])
            self.manager_profile1.stores.add(store)

        self.assertEqual(
            Store.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

    
        stores = Store.objects.filter(profile=self.top_profile1).order_by('-name')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(204):
            response = self.client.get(reverse('api:ep_store_with_receipt_index_lean'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/ep/stores_with_receipt/lean/?page=2')
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
        response = self.client.get(reverse('api:ep_store_with_receipt_index_lean') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/ep/stores_with_receipt/lean/',
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

        # Increase user's store count
        self.manager_profile1.stores.add(self.store2)

        param = '?search=cloth'
        response = self.client.get(reverse('api:ep_store_with_receipt_index_lean') + param)
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
            reverse('api:ep_store_with_receipt_index_lean'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_if_employee_without_store_access_will_receive_empty_list(self):

        # Remove store from employee profile
        self.manager_profile1.stores.remove(self.store1)

        response = self.client.get(
            reverse('api:ep_store_with_receipt_index_lean'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_a_top_user(self):

        # Login an top user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:ep_store_with_receipt_index_lean'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:ep_store_with_receipt_index_lean'))
        self.assertEqual(response.status_code, 401)


class EpStoreIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        self.add_can_view_stores_perm()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def add_can_view_stores_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Manager',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_stores')

        manager_group.permissions.add(permission)

    def remove_can_view_stores_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Manager',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_stores')

        manager_group.permissions.remove(permission)
 
    def test_view_returns_the_user_empoyees_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(7):
            response = self.client.get(
                reverse('api:ep_store_index'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': 'Computer Store', 
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

        response = self.client.get(reverse('api:ep_store_index'))
        self.assertEqual(response.status_code, 401)

    def test_if_view_cant_be_viewed_by_user_with_no_can_view_setting_perm(self):

        self.remove_can_view_stores_perm()
        
        response = self.client.get(reverse('api:ep_store_index'))
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

        # Create and confirm 11 stores
        for i in range(names_length):
            store = create_new_store(self.top_profile1, store_names[i])
            self.manager_profile1.stores.add(store)

        self.assertEqual(
            Store.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

    
        stores = Store.objects.filter(profile=self.top_profile1).order_by('-name')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(206):
            response = self.client.get(reverse('api:ep_store_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/ep/stores/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), page_size)

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
        response = self.client.get(reverse('api:ep_store_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/ep/stores/',
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

        # Increase user's store count
        self.manager_profile1.stores.add(self.store2)

        param = '?search=cloth'
        response = self.client.get(reverse('api:ep_store_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': 'Cloth Store',
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
            reverse('api:ep_store_index'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_if_employee_without_store_access_will_receive_empty_list(self):

        # Remove store from employee profile
        self.manager_profile1.stores.remove(self.store1)

        response = self.client.get(
            reverse('api:ep_store_index'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_a_top_user(self):

        # Login an top user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:ep_store_index'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:ep_store_index'))
        self.assertEqual(response.status_code, 401)

