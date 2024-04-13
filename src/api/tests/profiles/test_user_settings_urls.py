from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import Permission
from accounts.models import UserGroup

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.create_store_models import create_new_store
from core.test_utils.initial_user_data import InitialUserDataMixin
from core.test_utils.custom_testcase import APITestCase
from core.test_utils.create_user import (
    create_new_customer,
    create_new_manager_user,
    create_new_user,
)

from mysettings.models import MySetting
from profiles.models import LoyaltySetting, Profile, ReceiptSetting, UserGeneralSetting
from stores.models import Store 


class LoyaltySettingViewExistenceTestCase(APITestCase):
    
    def setUp(self):
    
        # Create a top users
        create_new_user('john')
        create_new_user('jack')
        
        self.top_profile1 = Profile.objects.get(user__email='john@gmail.com')
        self.top_profile2 = Profile.objects.get(user__email='jack@gmail.com')

        self.store = create_new_customer(self.top_profile1, 'Computer Store')
        
        # Create a supervisor user
        create_new_manager_user("gucci", self.top_profile1, self.store)

        loyalty = LoyaltySetting.objects.get(profile=self.top_profile1)
        loyalty.value = 20.05
        loyalty.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def remove_can_view_settings_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_settings')

        manager_group.permissions.remove(permission)

    def test_view_is_returning_a_user_loyalty_setting(self):
  
        response = self.client.get(reverse('api:loyalty_setting_view'))
        self.assertEqual(response.status_code, 200)

        loyalty = LoyaltySetting.objects.get(profile=self.top_profile1)

        result = {'value': str(loyalty.value)}

        self.assertEqual(response.data, result)

    def test_if_view_cant_be_viewed_by_user_with_no_can_view_setting_perm(self):

        self.remove_can_view_settings_perm()
        
        response = self.client.get(reverse('api:loyalty_setting_view'))
        self.assertEqual(response.status_code, 403)

    def test_view_can_edit_a_loyalty_setting(self):

        payload = {'value': '30.11'}

        response = self.client.put(reverse(
            'api:loyalty_setting_view'), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        result = {'value': payload['value']}

        self.assertEqual(response.data, result)

        loyalty = LoyaltySetting.objects.get(profile=self.top_profile1)
        self.assertEqual(str(loyalty.value), payload['value'])

    def test_view_wont_accept_an_empty_value(self):

        payload = {'value': ''}

        response = self.client.put(reverse(
            'api:loyalty_setting_view'), 
            payload
        )
        self.assertEqual(response.status_code, 400)
        
        result = {'value': ['A valid number is required.']}
        self.assertEqual(response.data, result)

    def test_view_wont_accept_a_value_greater_than_100(self):

        payload = {'value': '101'}

        response = self.client.put(reverse(
            'api:loyalty_setting_view'), 
            payload
        )
        self.assertEqual(response.status_code, 400)

        result = {'value': ['Ensure this value is less than or equal to 100.']}
        self.assertEqual(response.data, result)

    def test_view_wont_accept_a_value_less_than_0(self):

        payload = {'value': '-1'}

        response = self.client.put(reverse(
            'api:loyalty_setting_view'), 
            payload
        )
        self.assertEqual(response.status_code, 400)
        
        result = {'value': ['Ensure this value is greater than or equal to 0.']}
        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):
        
        # Unlogged in user
        self.client = APIClient()
        
        response = self.client.get(reverse('api:loyalty_setting_view'))
        self.assertEqual(response.status_code, 401)

class ReceiptSettingIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

    def remove_can_view_settings_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_settings')

        manager_group.permissions.remove(permission)

    def test_view_returns_the_user_stores_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(6):
            response = self.client.get(
                reverse('api:receipt_setting_index'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'store_name': 'Cloth Store', 
                    'reg_no': ReceiptSetting.objects.get(store=self.store2).reg_no,
                }, 
                {
                    'store_name': 'Computer Store',  
                    'reg_no': ReceiptSetting.objects.get(store=self.store1).reg_no,
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:receipt_setting_index'))
        self.assertEqual(response.status_code, 401)

    def test_if_view_cant_be_viewed_by_user_with_no_can_view_setting_perm(self):

        self.remove_can_view_settings_perm()
        
        response = self.client.get(reverse('api:receipt_setting_index'))
        self.assertEqual(response.status_code, 403)

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

    
        stores = Store.objects.filter(profile=self.top_profile1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(6):
            response = self.client.get(reverse('api:receipt_setting_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/settings/receipts/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), settings.LEAN_PAGINATION_PAGE_SIZE)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all store proifiles are listed except the first one since it's in the next paginated page #
        i = 0
        for store in stores[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['store_name'], store.name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], 
                ReceiptSetting.objects.get(store=store).reg_no
            )
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, settings.LEAN_PAGINATION_PAGE_SIZE)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:receipt_setting_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/settings/receipts/',
            'results': [
                {
                    'store_name': stores[0].name,  
                    'reg_no': ReceiptSetting.objects.get(store=stores[0]).reg_no,
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_stores(self):

        # First delete all stores
        Store.objects.all().delete()

        response = self.client.get(
            reverse('api:receipt_setting_index'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:receipt_setting_index'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:receipt_setting_index'))
        self.assertEqual(response.status_code, 401)

class ReceiptSettingViewAndEditTestCase(APITestCase, InitialUserDataMixin):
    
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

        r_setting = ReceiptSetting.objects.get(store=self.store1)
        r_setting.header1 = 'Header1'
        r_setting.header2 = 'Header2'
        r_setting.header3 = 'Header3'
        r_setting.header4 = 'Header4'
        r_setting.header5 = 'Header5'
        r_setting.header6 = 'Header6'
        r_setting.footer1 = 'Footer1'
        r_setting.footer2 = 'Footer2'
        r_setting.footer3 = 'Footer3'
        r_setting.footer4 = 'Footer4'
        r_setting.footer5 = 'Footer5'
        r_setting.footer6 = 'Footer6'
        r_setting.save()

        self.r_setting = ReceiptSetting.objects.get(store=self.store1)

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def remove_can_view_settings_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_settings')

        manager_group.permissions.remove(permission)

    def get_payload(self):
        return {
            'header1': 'This is the edited header1', 
            'header2': 'This is the edited header2', 
            'header3': 'This is the edited header3', 
            'header4': 'This is the edited header4', 
            'header5': 'This is the edited header5', 
            'header6': 'This is the edited header6', 

            'footer1': 'This is the edited footer1',
            'footer2': 'This is the edited footer2',
            'footer3': 'This is the edited footer3',
            'footer4': 'This is the edited footer4',
            'footer5': 'This is the edited footer5',
            'footer6': 'This is the edited footer6',  
        }

    def test_view_is_returning_a_user_receipt_setting(self):
        
        response = self.client.get(
            reverse('api:receipt_setting_view', args=(self.r_setting.reg_no,))
        )
        self.assertEqual(response.status_code, 200)

        result = {
            'store_name': self.store1.name,
            'header1': 'Header1',
            'header2': 'Header2',
            'header3': 'Header3',
            'header4': 'Header4',
            'header5': 'Header5',
            'header6': 'Header6', 

            'footer1': 'Footer1', 
            'footer2': 'Footer2', 
            'footer3': 'Footer3', 
            'footer4': 'Footer4', 
            'footer5': 'Footer5', 
            'footer6': 'Footer6', 
        }

        self.assertEqual(response.data, result)

    def test_if_view_cant_be_viewed_by_user_with_no_can_view_setting_perm(self):

        self.remove_can_view_settings_perm()
        
        response = self.client.put(
            reverse('api:receipt_setting_view', args=(self.r_setting.reg_no,)), 
            self.get_payload()
        )
        self.assertEqual(response.status_code, 403)

    def test_view_can_edit(self):

        payload = self.get_payload()

        response = self.client.put(
            reverse('api:receipt_setting_view', args=(self.r_setting.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        result = {
            'store_name': self.store1.name,
            'header1': payload['header1'],
            'header2': payload['header2'],
            'header3': payload['header3'],
            'header4': payload['header4'],
            'header5': payload['header5'],
            'header6': payload['header6'],

            'footer1': payload['footer1'], 
            'footer2': payload['footer2'], 
            'footer3': payload['footer3'], 
            'footer4': payload['footer4'], 
            'footer5': payload['footer5'], 
            'footer6': payload['footer6'], 
        }

        self.assertEqual(response.data, result)

        r_setting = ReceiptSetting.objects.get(store=self.store1)

        """
        Ensure the model has the right fields after it has been edited
        """
        self.assertEqual(r_setting.header1, payload['header1'])
        self.assertEqual(r_setting.header2, payload['header2'])
        self.assertEqual(r_setting.header3, payload['header3'])
        self.assertEqual(r_setting.header4, payload['header4'])
        self.assertEqual(r_setting.header5, payload['header5'])
        self.assertEqual(r_setting.header6, payload['header6'])

        self.assertEqual(r_setting.footer1, payload['footer1'])
        self.assertEqual(r_setting.footer2, payload['footer2'])
        self.assertEqual(r_setting.footer3, payload['footer3'])
        self.assertEqual(r_setting.footer4, payload['footer4'])
        self.assertEqual(r_setting.footer5, payload['footer5'])
        self.assertEqual(r_setting.footer6, payload['footer6'])

    def test_if_view_will_accept_an_empty_value(self):

        payload = self.get_payload()
        payload['header1'] = ''
        payload['header2'] = ''
        payload['header3'] = ''
        payload['header4'] = ''
        payload['header5'] = ''
        payload['header6'] = ''

        payload['footer1'] = ''
        payload['footer2'] = ''
        payload['footer3'] = ''
        payload['footer4'] = ''
        payload['footer5'] = ''
        payload['footer6'] = ''

        response = self.client.put(
            reverse('api:receipt_setting_view', args=(self.r_setting.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        result = {
            'store_name': self.store1.name,
            'header1': payload['header1'],
            'header2': payload['header2'],
            'header3': payload['header3'],
            'header4': payload['header4'],
            'header5': payload['header5'],
            'header6': payload['header6'],

            'footer1': payload['footer1'], 
            'footer2': payload['footer2'], 
            'footer3': payload['footer3'], 
            'footer4': payload['footer4'], 
            'footer5': payload['footer5'], 
            'footer6': payload['footer6'], 
        }

        self.assertEqual(response.data, result)

        r_setting = ReceiptSetting.objects.get(store=self.store1)

        self.assertEqual(r_setting.header1, payload['header1'])
        self.assertEqual(r_setting.header2, payload['header2'])
        self.assertEqual(r_setting.header3, payload['header3'])
        self.assertEqual(r_setting.header4, payload['header4'])
        self.assertEqual(r_setting.header5, payload['header5'])
        self.assertEqual(r_setting.header6, payload['header6'])

        self.assertEqual(r_setting.footer1, payload['footer1'])
        self.assertEqual(r_setting.footer2, payload['footer2'])
        self.assertEqual(r_setting.footer3, payload['footer3'])
        self.assertEqual(r_setting.footer4, payload['footer4'])
        self.assertEqual(r_setting.footer5, payload['footer5'])
        self.assertEqual(r_setting.footer6, payload['footer6'])

    def test_view_can_only_be_edited_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_payload()

        response = self.client.put(
            reverse('api:receipt_setting_view', args=(self.r_setting.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_edited_by_an_employee_user(self):

        # Login a employee profile #
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_payload()

        response = self.client.put(
            reverse('api:receipt_setting_view', args=(self.r_setting.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):
        
        # Unlogged in user
        self.client = APIClient()
        
        payload = self.get_payload()

        response = self.client.put(
            reverse('api:receipt_setting_view', args=(self.r_setting.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 401)

    def test_if_view_url_can_throttle_post_requests(self):

        payload = self.get_payload()

        throttle_rate = int(settings.THROTTLE_RATES['api_receipt_rate'].split("/")[0])
    
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.put(
                reverse('api:receipt_setting_view', 
                args=(self.r_setting.reg_no,)),
                payload,
            )
            self.assertEqual(response.status_code, 200)


        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional 
        # request if the previous request was not throttled 
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.put(
                reverse('api:receipt_setting_view', 
                args=(self.r_setting.reg_no,)),
                payload,
            )

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else: 
            # Executed because break was not called. This means the request was
            # never throttled 
            self.fail()


class UserGeneralSettingViewExistenceTestCase(APITestCase):
    
    def setUp(self):
    
        # Create a top users
        create_new_user('john')
        create_new_user('jack')
        
        self.top_profile1 = Profile.objects.get(user__email='john@gmail.com')
        self.top_profile2 = Profile.objects.get(user__email='jack@gmail.com')

        self.store = create_new_customer(self.top_profile1, 'Computer Store')
        
        # Create a supervisor user
        create_new_manager_user("gucci", self.top_profile1, self.store)

        g_setting = UserGeneralSetting.objects.get(profile=self.top_profile1)
        g_setting.enable_shifts = False 
        g_setting.enable_open_tickets = False
        g_setting.enable_low_stock_notifications = False 
        g_setting.enable_negative_stock_alerts = False
        g_setting.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def remove_can_view_settings_perm(self):

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_settings')

        manager_group.permissions.remove(permission)

    def test_view_is_returning_a_user_general_setting(self):
        
        response = self.client.get(reverse('api:user_general_setting_view'))
        self.assertEqual(response.status_code, 200)

        result = {
            'enable_shifts': False, 
            'enable_open_tickets': False, 
            'enable_low_stock_notifications': False, 
            'enable_negative_stock_alerts': False
        }

        self.assertEqual(response.data, result)

    def test_if_view_cant_be_viewed_by_user_with_no_can_view_setting_perm(self):

        self.remove_can_view_settings_perm()
        
        response = self.client.get(reverse('api:user_general_setting_view'))
        self.assertEqual(response.status_code, 403)
        
    def test_view_can_edit_a_user_general_setting(self):

        payload = {
            'enable_shifts': True, 
            'enable_open_tickets': True, 
            'enable_low_stock_notifications': True, 
            'enable_negative_stock_alerts': True
        }

        response = self.client.put(reverse(
            'api:user_general_setting_view'), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        result = {
            'enable_shifts': payload['enable_shifts'], 
            'enable_open_tickets': payload['enable_open_tickets'], 
            'enable_low_stock_notifications': payload['enable_low_stock_notifications'], 
            'enable_negative_stock_alerts': payload['enable_negative_stock_alerts']
        }

        self.assertEqual(response.data, result)

        g_setting = UserGeneralSetting.objects.get(profile=self.top_profile1)

        self.assertEqual(g_setting.enable_shifts, payload['enable_shifts'])
        self.assertEqual(g_setting.enable_open_tickets, payload['enable_open_tickets'])
        self.assertEqual(g_setting.enable_low_stock_notifications, payload['enable_low_stock_notifications'])
        self.assertEqual(g_setting.enable_negative_stock_alerts, payload['enable_negative_stock_alerts'])

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):
        
        # Unlogged in user
        self.client = APIClient()
        
        response = self.client.get(reverse('api:user_general_setting_view'))
        self.assertEqual(response.status_code, 401)
