from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from accounts.models import UserGroup

from core.test_utils.initial_user_data import (
    InitialUserDataMixin,
    FilterDatesMixin
)
from core.test_utils.custom_testcase import APITestCase

from mysettings.models import MySetting

User = get_user_model()


class LeanRoleIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

    def test_view_returns_the_user_user_groups_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(4):
            response = self.client.get(
                reverse('api:lean_role_index'))
            self.assertEqual(response.status_code, 200)

        groups = UserGroup.objects.filter(
            master_user__email='john@gmail.com'
        ).order_by('id')


        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'ident_name': groups[2].ident_name, 
                    'reg_no': groups[2].reg_no, 
                }, 
               {
                    'ident_name': groups[1].ident_name, 
                    'reg_no': groups[1].reg_no, 
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:lean_role_index'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all user groups
        UserGroup.objects.all().delete()

        model_num_to_be_created = settings.LEAN_PAGINATION_PAGE_SIZE+1

        group_names = [f'name {i}' for i in range(model_num_to_be_created)]
        
        names_length = len(group_names)
        self.assertEqual(names_length, model_num_to_be_created)  # Confirm number of names

        # Create and confirm models
        for i in range(names_length):
            UserGroup.objects.create(
                master_user=self.user1, 
                name=group_names[i],
                ident_name=group_names[i]
            )

        self.assertEqual(
            UserGroup.objects.filter(master_user=self.user1).count(), names_length
        )  # Confirm models were created

        groups = UserGroup.objects.filter(master_user=self.user1).order_by('id')


        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(4):
            response = self.client.get(
                reverse('api:lean_role_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/roles/lean/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), settings.LEAN_PAGINATION_PAGE_SIZE)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all cashier proifiles are listed except the first one since it's in the next paginated page #
        i = 0
        for group in groups[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['ident_name'], group.ident_name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], group.reg_no)

            i += 1

        self.assertEqual(i, settings.LEAN_PAGINATION_PAGE_SIZE)  # Confirm the number the for loop ran

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
            reverse('api:lean_role_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/roles/lean/',
            'results': [
                {
                    'ident_name': groups[0].ident_name, 
                    'reg_no': groups[0].reg_no, 
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_roles(self):

        # First delete all roles
        UserGroup.objects.all().delete()

        response = self.client.get(
            reverse('api:lean_role_index'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:lean_role_index'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:lean_role_index'))
        self.assertEqual(response.status_code, 401)

class RoleIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

    def test_view_returns_the_user_user_groups_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(6):
            response = self.client.get(
                reverse('api:role_index'))
            self.assertEqual(response.status_code, 200)

        groups = UserGroup.objects.filter(
            master_user__email='john@gmail.com',
            is_owner_group=False
        ).order_by('id')

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
               {
                    'ident_name': groups[1].ident_name, 
                    'reg_no': groups[1].reg_no, 
                    'employee_count': groups[1].get_employee_count()
                }, 
                {
                    'ident_name': groups[0].ident_name, 
                    'reg_no': groups[0].reg_no, 
                    'employee_count': groups[0].get_employee_count()
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:role_index'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all user groups
        UserGroup.objects.filter(is_owner_group=False).delete()

        model_num_to_be_created = settings.LEAN_PAGINATION_PAGE_SIZE+1

        group_names = [f'name {i}' for i in range(model_num_to_be_created)]
        
        names_length = len(group_names)
        self.assertEqual(names_length, model_num_to_be_created)  # Confirm number of names

        # Create and confirm models
        for i in range(names_length):
            UserGroup.objects.create(
                master_user=self.user1, 
                name=group_names[i],
                ident_name=group_names[i],
                is_owner_group=False
            )

        self.assertEqual(
            UserGroup.objects.filter(
                master_user=self.user1, is_owner_group=False).count(), 
                names_length
        )  # Confirm models were created

        groups = UserGroup.objects.filter(
            master_user=self.user1, 
            is_owner_group=False
        ).order_by('id')


        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(24):
            response = self.client.get(
                reverse('api:role_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/roles/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), settings.LEAN_PAGINATION_PAGE_SIZE)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all cashier proifiles are listed except the first one since it's in the next paginated page #
        i = 0
        for group in groups[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['ident_name'], group.ident_name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], group.reg_no)

            i += 1

        self.assertEqual(i, settings.LEAN_PAGINATION_PAGE_SIZE)  # Confirm the number the for loop ran

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
            reverse('api:role_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/roles/',
            'results': [
                {
                    'ident_name': groups[0].ident_name, 
                    'reg_no': groups[0].reg_no, 
                    'employee_count': groups[0].get_employee_count()
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_roles(self):

        # First delete all roles
        UserGroup.objects.all().delete()

        response = self.client.get(
            reverse('api:role_index'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:role_index'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:role_index'))
        self.assertEqual(response.status_code, 401)

class RoleIndexViewForCreatingTestCase(APITestCase, InitialUserDataMixin):

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

    def get_payload(self):

        return {
            'ident_name': 'New group',
            'can_view_shift_reports': False,
            'can_manage_open_tickets': False,
            'can_void_open_ticket_items': False,
            'can_manage_items': True,
            'can_refund_sale': False,
            'can_open_drawer': True,
            'can_reprint_receipt': True,
            'can_change_settings': False,
            'can_apply_discount': True,
            'can_change_taxes': False,
            'can_accept_debt': True,
            'can_manage_customers': False,
            'can_manage_employees': True,
            'can_change_general_settings': False, 
        }
    
    def test_if_view_can_create_a_user_group(self):

        payload = self.get_payload()

        # Count Number of Queries
        with self.assertNumQueries(9):
            response = self.client.post(reverse('api:role_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Confirm user group models creation
        self.assertEqual(UserGroup.objects.filter(
            ident_name=payload['ident_name']
        ).count(), 1)

        group = UserGroup.objects.get(ident_name=payload['ident_name'])

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]
  
        self.assertEqual(group.master_user, self.user1)
        self.assertEqual(group.name, f"{payload['ident_name']} {self.user1.reg_no}")
        self.assertEqual(group.ident_name, payload['ident_name'])
        self.assertEqual(group.is_owner_group, False)
        self.assertTrue(group.reg_no > 100000)  

        self.assertEqual(group.permissions.count(), 6)

        perms_codenames = [
            'can_manage_items',
            'can_open_drawer',
            'can_reprint_receipt',
            'can_apply_discount',
            'can_accept_debt',
            'can_manage_employees',
        ]

        self.assertEqual(perms, perms_codenames)

    def test_if_view_can_create_a_user_group_with_all_permissions(self):

        payload = {
            'ident_name': 'New group',
            'can_view_shift_reports': True,
            'can_manage_open_tickets': True,
            'can_void_open_ticket_items': True,
            'can_manage_items': True,
            'can_refund_sale': True,
            'can_open_drawer': True,
            'can_reprint_receipt': True,
            'can_change_settings': True,
            'can_apply_discount': True,
            'can_change_taxes': True,
            'can_accept_debt': True,
            'can_manage_customers': True,
            'can_manage_employees': True,
            'can_change_general_settings': True, 
        }

        response = self.client.post(reverse('api:role_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm user group models creation
        self.assertEqual(UserGroup.objects.filter(
            ident_name=payload['ident_name']
        ).count(), 1)

        group = UserGroup.objects.get(ident_name=payload['ident_name'])

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]
  
        self.assertEqual(group.master_user, self.user1)
        self.assertEqual(group.name, f"{payload['ident_name']} {self.user1.reg_no}")
        self.assertEqual(group.ident_name, payload['ident_name'])
        self.assertEqual(group.is_owner_group, False)
        self.assertTrue(group.reg_no > 100000)  

        self.assertEqual(group.permissions.count(), 14)

        perms_codenames = [
            'can_view_shift_reports', 
            'can_manage_open_tickets', 
            'can_void_open_ticket_items', 
            'can_manage_items', 
            'can_refund_sale', 
            'can_open_drawer', 
            'can_reprint_receipt', 
            'can_change_settings', 
            'can_apply_discount', 
            'can_change_taxes', 
            'can_accept_debt', 
            'can_manage_customers', 
            'can_manage_employees', 
            'can_change_general_settings'
        ]

        self.assertEqual(perms, perms_codenames)

    def test_if_view_can_create_a_user_group_without_permissions(self):

        payload = {
            'ident_name': 'New group',
            'can_view_shift_reports': False,
            'can_manage_open_tickets': False,
            'can_void_open_ticket_items': False,
            'can_manage_items': False,
            'can_refund_sale': False,
            'can_open_drawer': False,
            'can_reprint_receipt': False,
            'can_change_settings': False,
            'can_apply_discount': False,
            'can_change_taxes': False,
            'can_accept_debt': False,
            'can_manage_customers': False,
            'can_manage_employees': False,
            'can_change_general_settings': False, 
        }

        response = self.client.post(reverse('api:role_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm user group model creation
        self.assertEqual(UserGroup.objects.filter(
            ident_name=payload['ident_name']
        ).count(), 1)

        group = UserGroup.objects.get(ident_name=payload['ident_name'])

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]
  
        self.assertEqual(group.master_user, self.user1)
        self.assertEqual(group.name, f"{payload['ident_name']} {self.user1.reg_no}")
        self.assertEqual(group.ident_name, payload['ident_name'])
        self.assertEqual(group.is_owner_group, False)
        self.assertTrue(group.reg_no > 100000)  

        self.assertEqual(group.permissions.count(), 0)

        self.assertEqual(perms, [])

    def test_if_a_user_group_cant_be_created_with_an_empty_ident_name(self):

        payload = self.get_payload()
        payload['ident_name'] = ''

        response = self.client.post(reverse('api:role_index'), payload)
        self.assertEqual(response.status_code, 400)

        result = {'ident_name': ['This field may not be blank.']}

        self.assertEqual(response.data, result)
    
    def test_if_a_user_cant_have_2_user_groups_with_the_same_ident_name(self):

        payload = self.get_payload()
        payload['ident_name'] = 'Owner'

        response = self.client.post(reverse('api:role_index'), payload)
        self.assertEqual(response.status_code, 400)
        
        result = {'ident_name': ['You already have a role with this name.']}
        
        self.assertEqual(response.data, result)
        
        # Confirm the model was not created
        self.assertEqual(UserGroup.objects.filter(
            master_user=self.user1,
            ident_name=payload['ident_name']
        ).count(), 1)

    def test_if_2_users_can_have_2_user_groups_with_the_same_name(self):

        group_name = 'New group'

        # Create group for user two with the same naem
        UserGroup.objects.create(
            master_user=self.user2, 
            name=f'{group_name} {self.user2.reg_no}',
            ident_name=group_name,
        )

        payload = self.get_payload()
        payload['ident_name'] = group_name

        response = self.client.post(reverse('api:role_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm model creation
        self.assertEqual(UserGroup.objects.filter(
            ident_name=group_name
        ).count(), 2) 

    def test_if_user_group_cant_be_created_when_maintenance_mode_is_on(self):

        # Turn on maintenance mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        payload = self.get_payload()

        response = self.client.post(reverse('api:role_index'), payload)
        self.assertEqual(response.status_code, 401)

        # Confirm model was not created
        self.assertEqual(UserGroup.objects.filter(
            ident_name=payload['ident_name']
        ).count(), 0)

    def test_if_view_cant_be_viewed_by_an_employee_user(self):

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_payload()

        response = self.client.post(reverse('api:role_index'), payload)
        self.assertEqual(response.status_code, 403)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_payload()

        response = self.client.post(reverse('api:role_index'), payload)
        self.assertEqual(response.status_code, 401)


class RoleEditViewForViewingTestCase(APITestCase, InitialUserDataMixin, FilterDatesMixin):

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
        
        self.owner_group = UserGroup.objects.get(user__email='john@gmail.com')
        self.manager_group = UserGroup.objects.get(user__email='gucci@gmail.com')
        self.cashier_group = UserGroup.objects.get(user__email='kate@gmail.com')

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
                reverse('api:role_edit_view', args=(self.owner_group.reg_no,)))
            self.assertEqual(response.status_code, 200)

        result = {
            'ident_name': self.owner_group.ident_name, 
            'reg_no': self.owner_group.reg_no, 
            'perms_state': self.owner_group.get_user_permissions_state()
        }

        self.assertEqual(response.data, result)

        ########################## Test maintaince ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
            reverse('api:role_edit_view', args=(self.owner_group.reg_no,)))
        self.assertEqual(response.status_code, 401)

    def test_view_can_handle_wrong_reg_no(self):

        response = self.client.get(
            reverse('api:role_edit_view', args=(4646464,)))
        self.assertEqual(response.status_code, 404)

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:role_edit_view', args=(self.owner_group.reg_no,)))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:role_edit_view', args=(self.owner_group.reg_no,)))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:role_edit_view', args=(self.owner_group.reg_no,)))
        self.assertEqual(response.status_code, 401)

class RoleEditViewForEditingTestCase(APITestCase, InitialUserDataMixin):

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

        self.owner_group = UserGroup.objects.get(user__email='john@gmail.com')
        self.manager_group = UserGroup.objects.get(user__email='gucci@gmail.com')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def get_payload(self):

        return {
            'ident_name': 'New group',
            'can_view_shift_reports': False,
            'can_manage_open_tickets': False,
            'can_void_open_ticket_items': False,
            'can_manage_items': True,
            'can_refund_sale': False,
            'can_open_drawer': True,
            'can_reprint_receipt': True,
            'can_change_settings': False,
            'can_apply_discount': True,
            'can_change_taxes': False,
            'can_accept_debt': True,
            'can_manage_customers': False,
            'can_manage_employees': True,
            'can_change_general_settings': False, 
        }

    def test_view_can_edit_a_user_group(self):

        payload = self.get_payload()

        # Count Number of Queries #
        with self.assertNumQueries(12):
            response = self.client.put(reverse(
                'api:role_edit_view', args=(self.manager_group.reg_no,)), payload)
            self.assertEqual(response.status_code, 200)

        # Confirm group was changed
        group = UserGroup.objects.get(ident_name=payload['ident_name'])

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]
  
        self.assertEqual(group.master_user, self.user1)
        self.assertEqual(group.name, f"{payload['ident_name']} {self.user1.reg_no}")
        self.assertEqual(group.ident_name, payload['ident_name'])
        self.assertEqual(group.is_owner_group, False)
        self.assertTrue(group.reg_no > 100000)  

        self.assertEqual(group.permissions.count(), 6)

        perms_codenames = [
            'can_manage_items',
            'can_open_drawer',
            'can_reprint_receipt',
            'can_apply_discount',
            'can_accept_debt',
            'can_manage_employees',
        ]

        self.assertEqual(perms, perms_codenames)

    def test_view_cannot_edit_a_user_group_that_is_marked_as_owner(self):

        payload = self.get_payload()

        response = self.client.put(reverse(
            'api:role_edit_view', args=(self.owner_group.reg_no,)), payload)
        self.assertEqual(response.status_code, 403)

    def test_if_view_can_edit_a_user_group_with_all_permissions(self):

        payload = {
            'ident_name': 'New group',
            'can_view_shift_reports': True,
            'can_manage_open_tickets': True,
            'can_void_open_ticket_items': True,
            'can_manage_items': True,
            'can_refund_sale': True,
            'can_open_drawer': True,
            'can_reprint_receipt': True,
            'can_change_settings': True,
            'can_apply_discount': True,
            'can_change_taxes': True,
            'can_accept_debt': True,
            'can_manage_customers': True,
            'can_manage_employees': True,
            'can_change_general_settings': True, 
        }

        response = self.client.put(reverse(
            'api:role_edit_view', args=(self.manager_group.reg_no,)), payload)
        self.assertEqual(response.status_code, 200)

        # Confirm user group model update
        self.assertEqual(UserGroup.objects.filter(
            ident_name=payload['ident_name']
        ).count(), 1)

        group = UserGroup.objects.get(ident_name=payload['ident_name'])

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]
  
        self.assertEqual(group.master_user, self.user1)
        self.assertEqual(group.name, f"{payload['ident_name']} {self.user1.reg_no}")
        self.assertEqual(group.ident_name, payload['ident_name'])
        self.assertEqual(group.is_owner_group, False)
        self.assertTrue(group.reg_no > 100000)  

        self.assertEqual(group.permissions.count(), 14)

        perms_codenames = [
            'can_view_shift_reports', 
            'can_manage_open_tickets', 
            'can_void_open_ticket_items', 
            'can_manage_items', 
            'can_refund_sale', 
            'can_open_drawer', 
            'can_reprint_receipt', 
            'can_change_settings', 
            'can_apply_discount', 
            'can_change_taxes', 
            'can_accept_debt', 
            'can_manage_customers', 
            'can_manage_employees', 
            'can_change_general_settings'
        ]

        self.assertEqual(perms, perms_codenames)

    def test_if_view_can_create_a_user_group_without_permissions(self):

        payload = {
            'ident_name': 'New group',
            'can_view_shift_reports': False,
            'can_manage_open_tickets': False,
            'can_void_open_ticket_items': False,
            'can_manage_items': False,
            'can_refund_sale': False,
            'can_open_drawer': False,
            'can_reprint_receipt': False,
            'can_change_settings': False,
            'can_apply_discount': False,
            'can_change_taxes': False,
            'can_accept_debt': False,
            'can_manage_customers': False,
            'can_manage_employees': False,
            'can_change_general_settings': False, 
        }

        response = self.client.put(reverse(
            'api:role_edit_view', args=(self.manager_group.reg_no,)), payload)
        self.assertEqual(response.status_code, 200)

        # Confirm user group model creation
        self.assertEqual(UserGroup.objects.filter(
            ident_name=payload['ident_name']
        ).count(), 1)

        group = UserGroup.objects.get(ident_name=payload['ident_name'])

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]
  
        self.assertEqual(group.master_user, self.user1)
        self.assertEqual(group.name, f"{payload['ident_name']} {self.user1.reg_no}")
        self.assertEqual(group.ident_name, payload['ident_name'])
        self.assertEqual(group.is_owner_group, False)
        self.assertTrue(group.reg_no > 100000)  

        self.assertEqual(group.permissions.count(), 0)

        self.assertEqual(perms, [])

    def test_if_a_user_group_cant_be_created_with_an_empty_ident_name(self):

        payload = self.get_payload()
        payload['ident_name'] = ''

        response = self.client.put(reverse(
            'api:role_edit_view', args=(self.manager_group.reg_no,)), payload)
        self.assertEqual(response.status_code, 400)

        result = {'ident_name': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_user_cant_have_2_user_groups_with_the_same_ident_name(self):

        payload = self.get_payload()
        payload['ident_name'] = 'Owner'

        response = self.client.put(reverse(
            'api:role_edit_view', args=(self.manager_group.reg_no,)), payload)
        self.assertEqual(response.status_code, 400)
        
        result = {'ident_name': ['You already have a role with this name.']}
        
        self.assertEqual(response.data, result)
        
        # Confirm the model was not updated
        self.assertEqual(UserGroup.objects.filter(
            master_user=self.user1,
            ident_name=payload['ident_name']
        ).count(), 1)

    def test_if_2_users_can_have_2_user_groups_with_the_same_name(self):

        group_name = 'New group'

        # Create group for user two with the same naem
        UserGroup.objects.create(
            master_user=self.user2, 
            name=f'{group_name} {self.user2.reg_no}',
            ident_name=group_name,
        )

        payload = self.get_payload()
        payload['ident_name'] = group_name

        response = self.client.put(reverse(
            'api:role_edit_view', args=(self.manager_group.reg_no,)), payload)
        self.assertEqual(response.status_code, 200)

        # Confirm model update
        self.assertEqual(UserGroup.objects.filter(
            ident_name=group_name
        ).count(), 2) 
    
    def test_if_user_group_name_can_be_saved_without_raising_duplicate_error(self):
        
        payload = self.get_payload()
        payload['ident_name'] = self.manager_group.ident_name
        
        response = self.client.put(reverse(
            'api:role_edit_view', args=(self.manager_group.reg_no,)), payload)
        self.assertEqual(response.status_code, 200)

    def test_view_can_handle_a_wrong_reg_no(self):

        payload = self.get_payload()

        response = self.client.put(
            reverse('api:role_edit_view', args=(111111111,)), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_view_can_only_be_changed_by_its_owner(self):

        # Login a top user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_payload()

        response = self.client.put(reverse(
            'api:role_edit_view', args=(self.manager_group.reg_no,)), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_changed_by_an_employee_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_payload()

        response = self.client.put(reverse(
            'api:role_edit_view', args=(self.manager_group.reg_no,)), payload)
        self.assertEqual(response.status_code, 403)

    def test_if_view_cant_be_changed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_payload()

        response = self.client.put(reverse(
            'api:role_edit_view', args=(self.manager_group.reg_no,)), payload)
        self.assertEqual(response.status_code, 401)

class RoleEditViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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

        self.owner_group = UserGroup.objects.get(user__email='john@gmail.com')
        self.manager_group = UserGroup.objects.get(user__email='gucci@gmail.com')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_can_delete_a_user_group(self):

        response = self.client.delete(
            reverse('api:role_edit_view', args=(self.manager_group.reg_no,)))
        self.assertEqual(response.status_code, 204)

        # Confirm the model was deleted
        self.assertEqual(UserGroup.objects.filter(
            reg_no=self.manager_group.reg_no).exists(), False
        )

    def test_view_cannot_delete_a_user_group_that_is_marked_as_owner(self):

        response = self.client.delete(
            reverse('api:role_edit_view', args=(self.owner_group.reg_no,)))
        self.assertEqual(response.status_code, 403)

        # Confirm the model was not deleted
        self.assertEqual(UserGroup.objects.filter(
            reg_no=self.owner_group.reg_no).exists(), True
        )

    def test_view_can_handle_wrong_reg_no(self):

        response = self.client.delete(
            reverse('api:role_edit_view', args=(44444,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the model was not deleted
        self.assertEqual(UserGroup.objects.filter(
            reg_no=self.manager_group.reg_no).exists(), True
        )

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:role_edit_view', args=(self.owner_group.reg_no,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the model was not deleted
        self.assertEqual(UserGroup.objects.filter(
            reg_no=self.manager_group.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_employee_user(self):

        # Login a employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:role_edit_view', args=(self.owner_group.reg_no,)))
        self.assertEqual(response.status_code, 403)

        # Confirm the model was not deleted
        self.assertEqual(UserGroup.objects.filter(
            reg_no=self.manager_group.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:role_edit_view', args=(self.owner_group.reg_no,)))
        self.assertEqual(response.status_code, 401)

        # Confirm the model was not deleted
        self.assertEqual(UserGroup.objects.filter(
            reg_no=self.manager_group.reg_no).exists(), True
        )
