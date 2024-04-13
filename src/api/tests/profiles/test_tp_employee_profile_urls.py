
from pprint import pprint
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from accounts.models import UserGroup
from accounts.utils.user_type import EMPLOYEE_USER
from clusters.models import StoreCluster
from core.test_utils.create_store_models import create_new_store
from core.test_utils.initial_user_data import (
    InitialUserDataMixin,
    FilterDatesMixin
)
from core.test_utils.custom_testcase import APITestCase
from core.test_utils.create_user import (
    create_new_random_cashier_user,
    create_new_user,
    create_new_manager_user,
    create_new_cashier_user
)
from core.test_utils.make_payment import make_payment

from profiles.models import EmployeeProfile, Profile
from mysettings.models import MySetting
from mylogentries.models import UserActivityLog, CREATED

User = get_user_model()


class TpLeanEmployeeProfileIndexViewTestCase(APITestCase, InitialUserDataMixin):

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
    
    def test_view_returns_the_user_empoyees_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(16):
            response = self.client.get(
                reverse('api:tp_employee_profile_index_lean'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 6,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.cashier_profile4.get_full_name(),
                    'reg_no': self.cashier_profile4.reg_no
                },
                {
                    'name': self.manager_profile2.get_full_name(),
                    'reg_no': self.manager_profile2.reg_no
                },
                {
                    'name': self.cashier_profile3.get_full_name(),
                    'reg_no': self.cashier_profile3.reg_no
                },
                {
                    'name': self.cashier_profile2.get_full_name(),
                    'reg_no': self.cashier_profile2.reg_no
                },
                {
                    'name': self.cashier_profile1.get_full_name(),
                    'reg_no': self.cashier_profile1.reg_no
                },
                {
                    'name': self.manager_profile1.get_full_name(),
                    'reg_no': self.manager_profile1.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:tp_employee_profile_index_lean'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_view_for_employees_returns_the_right_content_with_pagination(self):

        # First delete all employe profiles
        EmployeeProfile.objects.all().delete()

        p1 = Profile.objects.get(user__email='john@gmail.com')

        model_num_to_be_created = settings.LEAN_PAGINATION_PAGE_SIZE+1

        cashier_names = create_new_random_cashier_user(
            p1, 
            self.store1, 
            model_num_to_be_created
        )

        names_length = len(cashier_names)
        self.assertEqual(names_length, model_num_to_be_created)  # Confirm number of names

        self.assertEqual(
            EmployeeProfile.objects.filter(
                profile__user__email=p1.user.email).count(),
            names_length
        )  # Confirm models were created

        cashier_profiles = EmployeeProfile.objects.filter(
            profile__user__email=p1.user.email
        ).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(44):
            response = self.client.get(
                reverse('api:tp_employee_profile_index_lean'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/profile/employees/lean/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), settings.LEAN_PAGINATION_PAGE_SIZE)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all cashier proifiles are listed except the first one since it's in the next paginated page #
        i = 0
        for cashier in cashier_profiles[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], cashier.get_full_name())
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], cashier.reg_no)

            i += 1

        self.assertEqual(i, settings.LEAN_PAGINATION_PAGE_SIZE)  # Confirm the number the for loop ran

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
            reverse('api:tp_employee_profile_index_lean') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/profile/employees/lean/',
            'results': [
                {
                    'name': cashier_profiles[0].get_full_name(),
                    'reg_no': cashier_profiles[0].reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        search_terms = [
            self.manager_profile1.user.first_name,
            self.manager_profile1.user.last_name,
            self.manager_profile1.user.email
        ]

        for search_term in search_terms:
            param = f'?search={search_term}'
            response = self.client.get(reverse('api:tp_employee_profile_index_lean') + param)
            self.assertEqual(response.status_code, 200)

            result = {
                'count': 1,
                'next': None,
                'previous': None,
                'results': [
                    {
                        'name': self.manager_profile1.get_full_name(),
                        'reg_no': self.manager_profile1.reg_no
                    }
                ]
            }

            self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_employees(self):

        # First delete all employee profiles
        EmployeeProfile.objects.all().delete()

        response = self.client.get(
            reverse('api:tp_employee_profile_index_lean'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_employee_profile_index_lean'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_employee_profile_index_lean'))
        self.assertEqual(response.status_code, 401)

class TpEmployeeProfileIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

    def test_view_returns_the_user_empoyees_only(self):

        # Count Number of Queries #
        #with self.assertNumQueries(22):
        response = self.client.get(
            reverse('api:tp_employee_profile_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 6,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.cashier_profile4.get_full_name(),
                    'user_email': self.cashier_profile4.user.email, 
                    'user_phone': self.cashier_profile4.user.phone, 
                    'role_name': self.cashier_profile4.role_name, 
                    'reg_no': self.cashier_profile4.reg_no, 
                },
                {
                    'name': self.manager_profile2.get_full_name(),
                    'user_email': self.manager_profile2.user.email, 
                    'user_phone': self.manager_profile2.user.phone, 
                    'role_name': self.manager_profile2.role_name, 
                    'reg_no': self.manager_profile2.reg_no, 
                },
                {
                    'name': self.cashier_profile3.get_full_name(),
                    'user_email': self.cashier_profile3.user.email, 
                    'user_phone': self.cashier_profile3.user.phone, 
                    'role_name': self.cashier_profile3.role_name, 
                    'reg_no': self.cashier_profile3.reg_no, 
                },
                {
                    'name': self.cashier_profile2.get_full_name(),
                    'user_email': self.cashier_profile2.user.email, 
                    'user_phone': self.cashier_profile2.user.phone, 
                    'role_name': self.cashier_profile2.role_name, 
                    'reg_no': self.cashier_profile2.reg_no, 
                },
                {
                    'name': self.cashier_profile1.get_full_name(),
                    'user_email': self.cashier_profile1.user.email, 
                    'user_phone': self.cashier_profile1.user.phone, 
                    'role_name': self.cashier_profile1.role_name, 
                    'reg_no': self.cashier_profile1.reg_no, 
                },
                {
                    'name': self.manager_profile1.get_full_name(),
                    'user_email': self.manager_profile1.user.email, 
                    'user_phone': self.manager_profile1.user.phone, 
                    'role_name': self.manager_profile1.role_name, 
                    'reg_no': self.manager_profile1.reg_no, 
                }
            ],
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:tp_employee_profile_index'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all employe profiles
        EmployeeProfile.objects.all().delete()

        model_num_to_be_created = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION+1

        # Create and confirm employees
        create_new_random_cashier_user(
            self.top_profile1,
            self.store1,
            model_num_to_be_created
        )

        self.assertEqual(
            EmployeeProfile.objects.filter(
                profile=self.top_profile1).count(),
                model_num_to_be_created
        )  # Confirm models were created

  
        employees = EmployeeProfile.objects.filter(profile=self.top_profile1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(25):
            response = self.client.get(reverse('api:tp_employee_profile_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/profile/employees/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(
            len(response_data_dict['results']), 
            settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION
        )

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # Check if all employees are listed except the first one since it's in 
        # the next paginated page #
        i = 0
        for employee in employees[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], employee.get_full_name())
            self.assertEqual(
                response_data_dict['results'][i]['user_email'], employee.user.email)
            self.assertEqual(
                response_data_dict['results'][i]['user_phone'], employee.user.phone)
            self.assertEqual(
                response_data_dict['results'][i]['role_name'], employee.role_name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], employee.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:tp_employee_profile_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': 'http://testserver/api/profile/employees/', 
            'results': [
                {
                    'name': employees[0].get_full_name(),
                    'user_email': employees[0].user.email, 
                    'user_phone': employees[0].user.phone, 
                    'role_name': employees[0].role_name, 
                    'reg_no': employees[0].reg_no, 
                }
            ],
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ]
        }
    
        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        search_terms = [
            self.manager_profile1.user.first_name,
            self.manager_profile1.user.last_name,
            self.manager_profile1.user.email
        ]

        for search_term in search_terms:
            param = f'?search={search_term}'
            response = self.client.get(reverse('api:tp_employee_profile_index') + param)
            self.assertEqual(response.status_code, 200)

            result = {
                'count': 1,
                'next': None,
                'previous': None,
                'results': [
                    {
                        'name': self.manager_profile1.get_full_name(),
                        'user_email': self.manager_profile1.user.email, 
                        'user_phone': self.manager_profile1.user.phone, 
                        'role_name': self.manager_profile1.role_name, 
                        'reg_no': self.manager_profile1.reg_no, 
                    }
                ],
                'stores': [
                    {
                        'name': self.store1.name, 
                        'reg_no': self.store1.reg_no
                    }, 
                    {
                        'name': self.store2.name, 
                        'reg_no': self.store2.reg_no
                    }
                ]
            }

            self.assertEqual(response.data, result)

    def test_view_can_filter_single_store(self):

        param = f'?stores__reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_employee_profile_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 4,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.cashier_profile3.get_full_name(),
                    'user_email': self.cashier_profile3.user.email, 
                    'user_phone': self.cashier_profile3.user.phone, 
                    'role_name': self.cashier_profile3.role_name, 
                    'reg_no': self.cashier_profile3.reg_no, 
                },
                {
                    'name': self.cashier_profile2.get_full_name(),
                    'user_email': self.cashier_profile2.user.email, 
                    'user_phone': self.cashier_profile2.user.phone, 
                    'role_name': self.cashier_profile2.role_name, 
                    'reg_no': self.cashier_profile2.reg_no, 
                },
                {
                    'name': self.cashier_profile1.get_full_name(),
                    'user_email': self.cashier_profile1.user.email, 
                    'user_phone': self.cashier_profile1.user.phone, 
                    'role_name': self.cashier_profile1.role_name, 
                    'reg_no': self.cashier_profile1.reg_no, 
                },
                {
                    'name': self.manager_profile1.get_full_name(),
                    'user_email': self.manager_profile1.user.email, 
                    'user_phone': self.manager_profile1.user.phone, 
                    'role_name': self.manager_profile1.role_name, 
                    'reg_no': self.manager_profile1.reg_no, 
                }
            ],
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_multiple_stores(self):

        param = f'?stores={self.store1.reg_no},{self.store2.reg_no}'
        response = self.client.get(reverse('api:tp_employee_profile_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 6,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.cashier_profile4.get_full_name(),
                    'user_email': self.cashier_profile4.user.email, 
                    'user_phone': self.cashier_profile4.user.phone, 
                    'role_name': self.cashier_profile4.role_name, 
                    'reg_no': self.cashier_profile4.reg_no, 
                },
                {
                    'name': self.manager_profile2.get_full_name(),
                    'user_email': self.manager_profile2.user.email, 
                    'user_phone': self.manager_profile2.user.phone, 
                    'role_name': self.manager_profile2.role_name, 
                    'reg_no': self.manager_profile2.reg_no, 
                },
                {
                    'name': self.cashier_profile3.get_full_name(),
                    'user_email': self.cashier_profile3.user.email, 
                    'user_phone': self.cashier_profile3.user.phone, 
                    'role_name': self.cashier_profile3.role_name, 
                    'reg_no': self.cashier_profile3.reg_no, 
                },
                {
                    'name': self.cashier_profile2.get_full_name(),
                    'user_email': self.cashier_profile2.user.email, 
                    'user_phone': self.cashier_profile2.user.phone, 
                    'role_name': self.cashier_profile2.role_name, 
                    'reg_no': self.cashier_profile2.reg_no, 
                },
                {
                    'name': self.cashier_profile1.get_full_name(),
                    'user_email': self.cashier_profile1.user.email, 
                    'user_phone': self.cashier_profile1.user.phone, 
                    'role_name': self.cashier_profile1.role_name, 
                    'reg_no': self.cashier_profile1.reg_no, 
                },
                {
                    'name': self.manager_profile1.get_full_name(),
                    'user_email': self.manager_profile1.user.email, 
                    'user_phone': self.manager_profile1.user.phone, 
                    'role_name': self.manager_profile1.role_name, 
                    'reg_no': self.manager_profile1.reg_no, 
                }
            ],
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_employees(self):

        # First delete all employee profiles
        EmployeeProfile.objects.all().delete()

        response = self.client.get(
            reverse('api:tp_employee_profile_index'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_employee_profile_index'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_employee_profile_index'))
        self.assertEqual(response.status_code, 401)

class TpEmployeeProfileIndexViewForCreatingTestCase(APITestCase):

    def setUp(self):

        # Create a top user1
        self.user1 = create_new_user('john')

        self.top_profile = Profile.objects.get(user__email='john@gmail.com')
        self.store = create_new_store(self.top_profile, 'Computer Store')

        # Create a top user2
        self.user2 = create_new_user('jack')

        self.top_profile2 = Profile.objects.get(user__email='jack@gmail.com')

        # Get user1 groups
        self.owner_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Owner'
        )
        self.manager_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Manager'
        )
        self.cashier_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Cashier'
        )

        # Get user2 groups
        self.user2_manager_group = UserGroup.objects.get(
            master_user=self.user2, ident_name='Manager'
        )

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
            'first_name': 'Gucci',
            'last_name': 'Gucci',
            'email': 'gucci@gmail.com',
            'phone': '254721223333',
            'position': 'Manager',
            'location': 'Runda',
            'role_reg_no': self.manager_group.reg_no,
            'gender': 0,
            'stores_info': [{'reg_no': self.store.reg_no}],
        }
    
    def test_if_view_can_create_a_manager_employee(self):

        payload = self.get_payload()

        # Count Number of Queries
        with self.assertNumQueries(38):
            response = self.client.post(
                reverse('api:tp_employee_profile_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Confirm EmployeeProfile models creation
        self.assertEqual(EmployeeProfile.objects.all().count(), 1)

        manager_profile = EmployeeProfile.objects.get(
            user__email='gucci@gmail.com')

        """ Test user details """
        user = User.objects.get(email='gucci@gmail.com')

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(str(user), 'gucci@gmail.com')
        self.assertEqual(user.email, 'gucci@gmail.com')
        self.assertEqual(user.first_name, 'Gucci')
        self.assertEqual(user.last_name, 'Gucci')
        self.assertEqual(user.phone, 254721223333)
        self.assertEqual(user.user_type, EMPLOYEE_USER)
        self.assertEqual(user.gender, 0)
        self.assertEqual((user.join_date).strftime("%B, %d, %Y"), today)

        # Make sure user is_active is false when it is
        # being created since it has not been payed for yet
        self.assertEqual(user.is_active, False)
        self.assertEqual(user.is_staff, False)

        """ Test profile """

        self.assertEqual(manager_profile.profile, self.top_profile)
        self.assertEqual(
            manager_profile.image.url, 
            f'/media/images/profiles/{manager_profile.reg_no}_.jpg'
        )
        self.assertEqual(manager_profile.phone,  254721223333)
        # Check if we have a valid reg_no
        self.assertEqual(manager_profile.reg_no, user.reg_no)
        # Test the str method
        self.assertEqual(str(manager_profile), 'gucci@gmail.com')
        # Confirm store was added
        self.assertEqual(manager_profile.stores.all().count(), 1)
        self.assertEqual(manager_profile.stores.all()[0], self.store)


        # Test user group
        group = UserGroup.objects.get(user__email='gucci@gmail.com')

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]

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
            'can_view_customers'
        ]

        self.assertEqual(perms, perms_codenames)

        ########################## UserActivityLog ##############################'#
        # Confirm that the created user was logged correctly

        log = UserActivityLog.objects.get(user__email='john@gmail.com')

        self.assertEqual(
            log.change_message,
            'New EmployeeProfile "gucci@gmail.com" has been created by "john@gmail.com"'
        )
        self.assertEqual(log.object_id, str(manager_profile.pk))
        self.assertEqual(log.object_repr, 'gucci@gmail.com')
        self.assertEqual(log.content_type.model, 'employeeprofile')
        self.assertEqual(log.user.email, 'john@gmail.com')
        self.assertTrue(len(log.ip) > 7)
        self.assertEqual(log.action_type, CREATED)
        self.assertEqual(log.owner_email, '')
        self.assertEqual(log.panel, 'Api')

        self.assertEqual(UserActivityLog.objects.all().count(), 1)

    def test_if_view_can_create_a_cashier_employee(self):

        payload = {
            'first_name': 'Kate',
            'last_name': 'Austen',
            'email': 'kate@gmail.com',
            'phone': '254711223366',
            'role_reg_no': self.cashier_group.reg_no,
            'gender': 0,
            'stores_info': [{'reg_no': self.store.reg_no}],
        }

        # Count Number of Queries
        with self.assertNumQueries(38):
            response = self.client.post(
                reverse('api:tp_employee_profile_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Confirm EmployeeProfile models creation
        self.assertEqual(EmployeeProfile.objects.all().count(), 1)

        cashier_profile = EmployeeProfile.objects.get(
            user__email='kate@gmail.com')

        """ Test user details """
        user = User.objects.get(email='kate@gmail.com')

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(str(user), 'kate@gmail.com')
        self.assertEqual(user.email, 'kate@gmail.com')
        self.assertEqual(user.first_name, 'Kate')
        self.assertEqual(user.last_name, 'Austen')
        self.assertEqual(user.phone, 254711223366)
        self.assertEqual(user.user_type, EMPLOYEE_USER)
        self.assertEqual(user.gender, 0)
        self.assertEqual((user.join_date).strftime("%B, %d, %Y"), today)

        # Make sure user is_active is false when it is
        # being created since it has not been payed for yet
        self.assertEqual(user.is_active, False)
        self.assertEqual(user.is_staff, False)

        """ Test profile """

        self.assertEqual(cashier_profile.profile, self.top_profile)
        self.assertEqual(
            cashier_profile.image.url, 
            f'/media/images/profiles/{cashier_profile.reg_no}_.jpg'
        )
        self.assertEqual(cashier_profile.phone,  254711223366)
        # Check if we have a valid reg_no
        self.assertEqual(cashier_profile.reg_no, user.reg_no)
        # Test the str method
        self.assertEqual(str(cashier_profile), 'kate@gmail.com')

        # Confirm store was added
        self.assertEqual(cashier_profile.stores.all().count(), 1)
        self.assertEqual(cashier_profile.stores.all()[0], self.store)


        # Test user groups
        group = UserGroup.objects.get(user__email='kate@gmail.com')

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]

        self.assertEqual(perms, [])

        ########################## UserActivityLog ##############################'#
        # Confirm that the created user was logged correctly

        log = UserActivityLog.objects.get(user__email='john@gmail.com')

        self.assertEqual(
            log.change_message,
            'New EmployeeProfile "kate@gmail.com" has been created by "john@gmail.com"'
        )
        self.assertEqual(log.object_id, str(cashier_profile.pk))
        self.assertEqual(log.object_repr, 'kate@gmail.com')
        self.assertEqual(log.content_type.model, 'employeeprofile')
        self.assertEqual(log.user.email, 'john@gmail.com')
        self.assertTrue(len(log.ip) > 7)
        self.assertEqual(log.action_type, CREATED)
        self.assertEqual(log.owner_email, '')
        self.assertEqual(log.panel, 'Api')

        self.assertEqual(UserActivityLog.objects.all().count(), 1)

    def test_if_view_can_create_an_employee_with_multiple_stores(self):

        store2 = create_new_store(self.top_profile, 'Computer Store')

        payload = self.get_payload()
        payload['stores_info'] = [
            {'reg_no': self.store.reg_no}, 
            {'reg_no': store2.reg_no}
        ]

        # Count Number of Queries
        with self.assertNumQueries(39):
            response = self.client.post(
                reverse('api:tp_employee_profile_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Confirm EmployeeProfile models creation
        self.assertEqual(EmployeeProfile.objects.all().count(), 1)

        manager_profile = EmployeeProfile.objects.get(
            user__email='gucci@gmail.com')

        # Confirm stores was added
        self.assertEqual(manager_profile.stores.all().count(), 2)
        self.assertEqual(manager_profile.stores.all()[0], self.store)
        self.assertEqual(manager_profile.stores.all()[1], store2)

    def test_if_employee_profile_cant_be_created_when_maintenance_mode_is_on(self):

        # Turn on maintenance mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        payload = self.get_payload()

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 401)

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_an_employee_profile_cant_be_created_when_new_employee_mode_is_off(self):

        # Turn off signups mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.new_employee = False
        ms.save()

        payload = self.get_payload()

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 423)

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_an_employee_profile_cant_be_created_with_an_empty_stores_info(self):

        payload = self.get_payload()
        payload['stores_info'] = ''

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, {'stores_info': ['Expected a list of items but got type "str".']})

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_an_employee_profile_cant_be_created_with_an_empty_stores_info_list(self):

        payload = self.get_payload()
        payload['stores_info'] = []

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'stores_info': [
                         'This list may not be empty.']})

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_an_employee_profile_cant_be_created_with_an_empty_store_reg(self):

        payload = self.get_payload()
        payload['stores_info'] = [{'reg_no': ''}]

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data,
            {'stores_info': {0: {'reg_no': ['A valid integer is required.']}}}
        )

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_an_employee_profile_cant_be_created_with_a_wrong_stores_reg_no(self):

        payload = self.get_payload()
        payload['stores_info'] = [{'reg_no': ''}]

        wrong_stores_reg_nos = [
            '1010',  # Wrong reg no
            'aaaa',  # Non numeric
            3333333333333333333333333333333333333333333333  # Extremely long
        ]

        i = 0
        for reg_no in wrong_stores_reg_nos:

            payload['stores_info'] = [{'reg_no': reg_no}]

            response = self.client.post(
                reverse('api:tp_employee_profile_index'), payload)
            self.assertEqual(response.status_code, 400)

            if i == 0:
                self.assertEqual(
                    response.data, {'stores_info': 'You provided wrong stores.'})

            elif i == 1:
                self.assertEqual(
                    response.data,
                    {'stores_info': {
                        0: {'reg_no': ['A valid integer is required.']}}}
                )

            else:
                self.assertEqual(
                    response.data,
                    {'stores_info': {
                        0: {'reg_no': ['You provided wrong stores']}}}
                )

            # Confirm EmployeeProfile were not created
            self.assertEqual(EmployeeProfile.objects.all().count(), 0)

            i += 1

    def test_if_view_wont_accept_a_store_that_belongs_to_another_user(self):

        # Create a store for user 2
        store = create_new_store(self.top_profile2, 'Toy Store')

        payload = self.get_payload()
        payload['stores_info'] = [{'reg_no': store.reg_no}]

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, {'stores_info': 'You provided wrong stores.'})

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_view_wont_accept_a_correct_store_that_is_accoumpanied_by_1_from_another_user(self):

        # Create a store for user 2
        store2 = create_new_store(self.top_profile2, 'Toy Store')

        payload = self.get_payload()
        payload['stores_info'] = [
            {'reg_no': self.store.reg_no}, 
            {'reg_no': store2.reg_no}
        ]

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, {'stores_info': 'You provided wrong stores.'})

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_view_wont_accept_a_stores_reg_long_than_max_length(self):

        # Create a store for user 2

        stores = []
        for i in range(settings.MAX_STORES_REG_MAX_LENGTH + 1):
            stores.append({'reg_no': self.store.reg_no + i})

        payload = self.get_payload()
        payload['stores_info'] = stores

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data,
            {'stores_info': [
                f'Ensure this field has no more than {settings.MAX_STORES_REG_MAX_LENGTH} elements.']}
        )

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_an_employee_profile_cant_be_created_with_an_empty_first_name(self):

        payload = self.get_payload()
        payload['first_name'] = ''

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'first_name': [
                         'This field may not be blank.']})

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_an_employee_profile_cant_be_created_with_an_empty_last_name(self):

        payload = self.get_payload()
        payload['last_name'] = ''

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'last_name': [
                         'This field may not be blank.']})

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_an_employee_profile_cant_be_created_with_an_empty_email(self):

        payload = self.get_payload()
        payload['email'] = ''

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, {'email': ['This field may not be blank.']})

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_view_cant_accept_long_email(self):

        long_email = "{}@gmail.com".format("x"*30)
 
        payload = self.get_payload()
        payload['email'] = long_email

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        result = {
            'email': ['Ensure this field has no more than 30 characters.']}
        self.assertEqual(response.data, result)

        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_an_employee_profile_cant_be_created_with_a_wrong_email_format(self):

        payload = self.get_payload()
        payload['email'] = 'wrongemailformat'

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, {'email': ['Enter a valid email address.']})

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_an_employee_profile_cant_be_created_with_a_non_unique_email(self):

        payload = self.get_payload()

        # Try to signup with emails from existing users

        top_profile = Profile.objects.get(user__email='john@gmail.com')

        # Create 2 manager users
        create_new_manager_user("gucci", top_profile, self.store)
        create_new_manager_user("lewis", top_profile, self.store)

        # Create 2 cashier users
        create_new_cashier_user("james", top_profile, self.store)
        create_new_cashier_user("ben", top_profile, self.store)

        # Get users emails
        top_user1_email = User.objects.get(email='john@gmail.com').email
        top_user2_email = User.objects.get(email='jack@gmail.com').email

        manager_user1_email = User.objects.get(email='gucci@gmail.com').email
        manager_user2_email = User.objects.get(email='lewis@gmail.com').email

        cashier_user1_email = User.objects.get(email='james@gmail.com').email
        cashier_user2_email = User.objects.get(email='ben@gmail.com').email

        user_emails = [
            top_user1_email,
            top_user2_email,
            manager_user1_email,
            manager_user2_email,
            cashier_user1_email,
            cashier_user2_email
        ]

        i = 0
        for email in user_emails:

            payload = self.get_payload()
            payload['email'] = email
            payload['phone'] = '254711223366'

            response = self.client.post(
                reverse('api:tp_employee_profile_index'), payload)
            self.assertEqual(response.status_code, 400)

            self.assertEqual(
                response.data, {'email': ['User with this Email already exists.']})

            i += 1

        # Confirm how many times the loop ran
        self.assertEqual(i, 6)

    def test_for_successfull_employee_profile_creattion_with_correct_phones(self):

        payload = self.get_payload()

        emails = [get_random_string(10) + '@gmail.com' for i in range(8)]
        phones = ['254700223322',
                  '254709223322',
                  '254711223322',
                  '254719223322',
                  '254720223327',
                  '254729223322',
                  '254790223322',
                  '254799223322',
                  ]

        i = 0
        for phone in phones:
            # Clear cache before every new request
            cache.clear()

            payload = self.get_payload()
            payload['email'] = emails[i]
            payload['phone'] = phone

            response = self.client.post(
                reverse('api:tp_employee_profile_index'), payload)
            self.assertEqual(response.status_code, 201)

            i += 1

        self.assertEqual(EmployeeProfile.objects.all().count(), len(phones))

    def test_if_an_employee_profile_cant_be_created_with_an_empty_phone(self):

        payload = self.get_payload()
        payload['phone'] = ''

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, {'phone': ['A valid integer is required.']})

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

    def test_if_an_employee_profile_cant_be_created_with_a_non_unique_phone(self):

        payload = self.get_payload()

        # Try to signup with phones from existing users

        top_profile = Profile.objects.get(user__email='john@gmail.com')

        # Create 2 manager users
        create_new_manager_user("gucci", top_profile, self.store)
        create_new_manager_user("lewis", top_profile, self.store)

        # Create 2 cashier users
        create_new_cashier_user("james", top_profile, self.store)
        create_new_cashier_user("ben", top_profile, self.store)

        # Get users phones
        top_user1_phone = User.objects.get(email='john@gmail.com').phone
        top_user2_phone = User.objects.get(email='jack@gmail.com').phone

        manager_user1_phone = User.objects.get(email='gucci@gmail.com').phone
        manager_user2_phone = User.objects.get(email='lewis@gmail.com').phone

        cashier_user1_phone = User.objects.get(email='james@gmail.com').phone
        cashier_user2_phone = User.objects.get(email='ben@gmail.com').phone

        user_phones = [
            top_user1_phone,
            top_user2_phone,
            manager_user1_phone,
            manager_user2_phone,
            cashier_user1_phone,
            cashier_user2_phone
        ]

        i = 0
        for phone in user_phones:

            payload['email'] = f'{i}kate@gmail.com'
            payload['phone'] = phone

            response = self.client.post(
                reverse('api:tp_employee_profile_index'), payload)
            self.assertEqual(response.status_code, 400)

            self.assertEqual(User.objects.count(), 6)

            result = {'phone': ['User with this phone already exists.']}
            self.assertEqual(response.data, result)

            i += 1

        # Confirm how many times the loop ran
        self.assertEqual(i, 6)

    def test_if_an_employee_profile_cant_be_created_with_wrong_phones(self):

        payload = self.get_payload()

        phones = [
            '25470022332j',  # Number with letters
            '2547112233222',  # Long Number
            '25471122332',  # Short Number
            '254711223323333333333333333333333333333333',   # long Number
        ]

        i = 0
        for phone in phones:
            # Clear cache before every new request so that throttling does not work
            cache.clear()

            payload['phone'] = phone

            response = self.client.post(
                reverse('api:tp_employee_profile_index'), payload)
            self.assertEqual(response.status_code, 400)

            self.assertEqual(len(response.data['phone']), 1)  # Check error key

            if i == 1 or i == 3:
                result = {'phone': ['This phone is too long.']}
                self.assertEqual(response.data, result)

            elif i == 2:
                result = {'phone': ['This phone is too short.']}
                self.assertEqual(response.data, result)

            else:
                result = {'phone': ['A valid integer is required.']}
                self.assertEqual(response.data, result)

            i += 1

        self.assertEqual(i, 4)
    
    def test_if_an_employee_profile_cant_be_created_with_an_empty_role_reg_no(self):

        payload = self.get_payload()
        payload['role_reg_no'] = ''

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, {'role_reg_no': ['A valid integer is required.']}
        )

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)
    
    def test_if_an_employee_profile_cant_be_created_with_a_wrong_role_reg_no(self):
        
        payload = self.get_payload()

        wrong_role_reg_nos = [
            1010,  # Wrong reg no
            'aaaa',  # Non numeric
            self.owner_group.reg_no, # Owner group 
            self.user2_manager_group.reg_no, # Another user's group
            3333333333333333333333333333333333333333333333  # Extremely long
        ]

        i = 0
        for reg_no in wrong_role_reg_nos:

            payload['role_reg_no'] = reg_no

            response = self.client.post(
                reverse('api:tp_employee_profile_index'), payload)
            self.assertEqual(response.status_code, 400)

            if i == 1:
                self.assertEqual(
                    response.data,
                    {'role_reg_no': ['A valid integer is required.']}
                )

            else:

                self.assertEqual(
                    response.data,
                    {'role_reg_no': ['Wrong role was selected']}
                )
            
            # Confirm EmployeeProfile were not created
            self.assertEqual(EmployeeProfile.objects.all().count(), 0)

            i += 1

    def test_if_an_employee_profile_cant_be_created_with_an_empty_gender(self):

        payload = self.get_payload()
        payload['gender'] = ''

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'gender': [
                         '"" is not a valid choice.']})

        # Confirm EmployeeProfile were not created
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)
    
    def test_if_view_can_can_throttle_employee_profile_creation(self):

        payload = self.get_payload()

        throttle_rate = int(
            settings.THROTTLE_RATES['api_employee_create_rate'].split("/")[0])

        emails = [get_random_string(
            10) + '@gmail.com' for i in range(throttle_rate)]
        phone = 254700000000

        for i in range(throttle_rate): # pylint: disable=unused-variable

            payload['email'] = emails[i]
            payload['phone'] = phone + i # This ensures unique phone.

            response = self.client.post(
                reverse('api:tp_employee_profile_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional
        # request if the previous request was not throttled
        for i in range(throttle_rate): # pylint: disable=unused-variable

            # Try to see if the next request will be throttled
            payload['email'] = f'{i}new_email@gmail.com'
            payload['phone'] = phone + i+1 # This ensures unique phone.

            response = self.client.post(
                reverse('api:tp_employee_profile_index'), payload)

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else:
            # Executed because break was not called. This means the request was
            # never throttled
            self.fail()

    def test_if_view_cant_be_viewed_by_an_employee_user(self):

        # Create a manager user
        create_new_manager_user("gucci", self.top_profile, self.store)
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

        payload = self.get_payload()

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 403)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_payload()

        response = self.client.post(
            reverse('api:tp_employee_profile_index'), payload)
        self.assertEqual(response.status_code, 401)


class TpEmployeeProfileEditViewForViewingTestCase(APITestCase, InitialUserDataMixin, FilterDatesMixin):

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


        # Get user1 groups
        self.owner_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Owner'
        )
        self.manager_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Manager'
        )
        self.cashier_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Cashier'
        )

        # Get user2 groups
        self.user2_manager_group = UserGroup.objects.get(
            master_user=self.user2, ident_name='Manager'
        )

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
        with self.assertNumQueries(8):
            response = self.client.get(
                reverse('api:tp_employee_profile_edit', 
                args=(self.cashier_profile1.reg_no,)))
            self.assertEqual(response.status_code, 200)

        result = {
            'name': self.cashier_profile1.get_full_name(), 
            'user_email': self.cashier_profile1.user.email, 
            'user_phone': self.cashier_profile1.user.phone, 
            'reg_no': self.cashier_profile1.reg_no,
            'roles': [
                {
                    'ident_name': self.cashier_group.ident_name, 
                    'reg_no': self.cashier_group.reg_no, 
                    'assigned': True
                }, 
                {
                    'ident_name': self.manager_group.ident_name, 
                    'reg_no': self.manager_group.reg_no, 
                    'assigned': False
                }
            ], 
            'registered_stores': [
                {
                    'name': self.store1.name,
                    'reg_no': self.store1.reg_no
                }
            ],
            'available_stores': [
                {
                    'name': self.store1.name,
                    'reg_no': self.store1.reg_no
                },
                {
                    'name': self.store2.name,
                    'reg_no': self.store2.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test maintaince ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
            reverse('api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)))
        self.assertEqual(response.status_code, 401)

    def test_view_can_be_called_successefully2(self):

        self.cashier_profile1.stores.add(self.store2)

        # Count Number of Queries #
        with self.assertNumQueries(8):
            response = self.client.get(
                reverse('api:tp_employee_profile_edit', 
                args=(self.cashier_profile1.reg_no,)))
            self.assertEqual(response.status_code, 200)


        result = {
            'name': self.cashier_profile1.get_full_name(), 
            'user_email': self.cashier_profile1.user.email, 
            'user_phone': self.cashier_profile1.user.phone, 
            'reg_no': self.cashier_profile1.reg_no,
            'roles': [
                {
                    'ident_name': self.cashier_group.ident_name, 
                    'reg_no': self.cashier_group.reg_no, 
                    'assigned': True
                }, 
                {
                    'ident_name': self.manager_group.ident_name, 
                    'reg_no': self.manager_group.reg_no, 
                    'assigned': False
                }
            ], 
            'registered_stores': [
                {
                    'name': self.store1.name,
                    'reg_no': self.store1.reg_no
                },
                {
                    'name': self.store2.name,
                    'reg_no': self.store2.reg_no
                }
            ],
            'available_stores': [
                {
                    'name': self.store1.name,
                    'reg_no': self.store1.reg_no
                },
                {
                    'name': self.store2.name,
                    'reg_no': self.store2.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_be_called_successefully3(self):

        self.cashier_profile1.stores.remove(self.store1)

        # Count Number of Queries #
        with self.assertNumQueries(8):
            response = self.client.get(
                reverse('api:tp_employee_profile_edit', 
                args=(self.cashier_profile1.reg_no,)))
            self.assertEqual(response.status_code, 200)

        result = {
            'name': self.cashier_profile1.get_full_name(), 
            'user_email': self.cashier_profile1.user.email, 
            'user_phone': self.cashier_profile1.user.phone, 
            'reg_no': self.cashier_profile1.reg_no,
            'roles': [
                {
                    'ident_name': self.cashier_group.ident_name, 
                    'reg_no': self.cashier_group.reg_no, 
                    'assigned': True
                }, 
                {
                    'ident_name': self.manager_group.ident_name, 
                    'reg_no': self.manager_group.reg_no, 
                    'assigned': False
                }
            ], 
            'registered_stores': [],
            'available_stores': [
                {
                    'name': self.store1.name,
                    'reg_no': self.store1.reg_no
                },
                {
                    'name': self.store2.name,
                    'reg_no': self.store2.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_handle_wrong_reg_no(self):

        response = self.client.get(
            reverse('api:tp_employee_profile_edit', args=(4646464,)))
        self.assertEqual(response.status_code, 404) 

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:tp_employee_profile_edit', 
            args=(self.cashier_profile1.reg_no,)))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)))
        self.assertEqual(response.status_code, 401)


class TpEmployeeProfileEditViewForEditingTestCase(APITestCase, InitialUserDataMixin):

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

        # Get user1 groups
        self.owner_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Owner'
        )
        self.manager_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Manager'
        )
        self.cashier_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Cashier'
        )

        # Get user2 groups
        self.user2_manager_group = UserGroup.objects.get(
            master_user=self.user2, ident_name='Manager'
        )

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
            'role_reg_no': self.manager_group.reg_no,
            'stores_info': [
                {'reg_no': self.store1.reg_no}, 
                {'reg_no': self.store2.reg_no}
            ],
        }
    
    def test_view_can_edit_an_employee_profile(self):

        # Test current user group 
        group = UserGroup.objects.get(user__email='kate@gmail.com')

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]

        self.assertEqual(perms, [])

        payload = self.get_payload()

        # Count Number of Queries #
        with self.assertNumQueries(24):
            response = self.client.put(reverse(
                'api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)), payload)
            self.assertEqual(response.status_code, 200)

        # Confirm EmployeeProfile was changed
        cashier_profile = EmployeeProfile.objects.get(
            user__email='kate@gmail.com')

        self.assertEqual(cashier_profile.user.user_type, EMPLOYEE_USER)

        # Confirm store was added
        self.assertEqual(cashier_profile.stores.all().count(), 2)
        self.assertEqual(cashier_profile.stores.all()[0], self.store1)
        self.assertEqual(cashier_profile.stores.all()[1], self.store2)

        # Test user group
        group = UserGroup.objects.get(user__email='kate@gmail.com')

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]

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
            'can_view_customers'
        ]

        self.assertEqual(perms, perms_codenames)

    def test_view_can_remove_a_store_from_employee_profile(self):

        self.cashier_profile1.stores.add(self.store2)

        # Confirm store was added
        cashier_profile = EmployeeProfile.objects.get(
            user__email='kate@gmail.com')

        self.assertEqual(cashier_profile.stores.all().count(), 2)
        self.assertEqual(cashier_profile.stores.all()[0], self.store1)
        self.assertEqual(cashier_profile.stores.all()[1], self.store2)

        payload = self.get_payload()
        payload['stores_info'] = [{'reg_no': self.store1.reg_no}]

        # Count Number of Queries #
        with self.assertNumQueries(23):
            response = self.client.put(reverse(
                'api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)), payload)
            self.assertEqual(response.status_code, 200)

        # Confirm EmployeeProfile was changed
        cashier_profile = EmployeeProfile.objects.get(
            user__email='kate@gmail.com')

        self.assertEqual(cashier_profile.user.user_type, EMPLOYEE_USER)

        # Confirm store was added
        self.assertEqual(cashier_profile.stores.all().count(), 1)
        self.assertEqual(cashier_profile.stores.all()[0], self.store1)

    def test_view_can_add_a_store_and_remove_another_at_the_same_time(self):

        self.cashier_profile1.stores.add(self.store2)

        # Confirm store was added
        cashier_profile = EmployeeProfile.objects.get(
            user__email='kate@gmail.com')

        self.assertEqual(cashier_profile.stores.all().count(), 2)
        self.assertEqual(cashier_profile.stores.all()[0], self.store1)
        self.assertEqual(cashier_profile.stores.all()[1], self.store2)

        # Create a new store
        new_store = create_new_store(self.top_profile1, 'New Store')

        payload = self.get_payload()
        payload['stores_info'] = [
            {'reg_no': self.store2.reg_no}, 
            {'reg_no': new_store.reg_no}
        ]

        # Count Number of Queries #
        with self.assertNumQueries(25):
            response = self.client.put(reverse(
                'api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)), payload)
            self.assertEqual(response.status_code, 200)

        # Confirm EmployeeProfile was changed
        cashier_profile = EmployeeProfile.objects.get(
            user__email='kate@gmail.com')

        self.assertEqual(cashier_profile.user.user_type, EMPLOYEE_USER)

        # Confirm store was added
        self.assertEqual(cashier_profile.stores.all().count(), 2)
        self.assertEqual(cashier_profile.stores.all()[0], self.store2)
        self.assertEqual(cashier_profile.stores.all()[1], new_store)

    def test_view_can_handle_a_wrong_reg_no(self):

        payload = self.get_payload()
      
        response = self.client.put(
            reverse('api:tp_employee_profile_edit', args=(111111111,)), payload)
        self.assertEqual(response.status_code, 404)

    def test_view_wont_accept_an_empty_store_info(self):

        payload = self.get_payload()
        payload['stores_info'] = ''

        response = self.client.put(reverse(
            'api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'stores_info': [
                         'Expected a list of items but got type "str".']})

        # Confirm EmployeeProfile was not changed
        cashier_profile = EmployeeProfile.objects.get(
            user__email='kate@gmail.com')

        self.assertEqual(cashier_profile.user.user_type, EMPLOYEE_USER)

        self.assertEqual(cashier_profile.stores.all().count(), 1)
        self.assertEqual(cashier_profile.stores.all()[0], self.store1)

    def test_view_wont_accept_an_empty_store_info_list(self):

        payload = self.get_payload()
        payload['stores_info'] = []

        response = self.client.put(reverse(
            'api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'stores_info': [
                         'This list may not be empty.']})

        # Confirm EmployeeProfile was not changed
        cashier_profile = EmployeeProfile.objects.get(
            user__email='kate@gmail.com')

        self.assertEqual(cashier_profile.user.user_type, EMPLOYEE_USER)

        self.assertEqual(cashier_profile.stores.all().count(), 1)
        self.assertEqual(cashier_profile.stores.all()[0], self.store1)

    def test_if_an_employee_profile_cant_be_edited_with_an_empty_store_reg(self):

        payload = self.get_payload()
        payload['stores_info'] = [{'reg_no': ''}]

        response = self.client.put(reverse(
            'api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data,
            {'stores_info': {0: {'reg_no': ['A valid integer is required.']}}}
        )

        # Confirm EmployeeProfile was not changed
        cashier_profile = EmployeeProfile.objects.get(
            user__email='kate@gmail.com')

        self.assertEqual(cashier_profile.user.user_type, EMPLOYEE_USER)

        self.assertEqual(cashier_profile.stores.all().count(), 1)
        self.assertEqual(cashier_profile.stores.all()[0], self.store1)

    def test_if_an_employee_profile_cant_be_edited_with_a_wrong_stores_reg_no(self):

        payload = self.get_payload()

        wrong_stores_reg_nos = [
            '1010',  # Wrong reg no
            'aaaa',  # Non numeric
            3333333333333333333333333333333333333333333333  # Extremely long
        ]

        i = 0
        for reg_no in wrong_stores_reg_nos:
    
            payload['stores_info'] = [{'reg_no': reg_no}]

            response = self.client.put(reverse(
                'api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)), payload)
            self.assertEqual(response.status_code, 400)

            if i == 0:
                self.assertEqual(
                    response.data, {'stores_info': 'You provided wrong stores.'})

            elif i == 1:
                self.assertEqual(
                    response.data,
                    {'stores_info': {
                        0: {'reg_no': ['A valid integer is required.']}}}
                )

            else:
                self.assertEqual(
                    response.data,
                    {'stores_info': {
                        0: {'reg_no': ['You provided wrong stores']}}}
                )

            # Confirm EmployeeProfile was not changed
            cashier_profile = EmployeeProfile.objects.get(
                user__email='kate@gmail.com')

            self.assertEqual(cashier_profile.user.user_type, EMPLOYEE_USER)

            self.assertEqual(cashier_profile.stores.all().count(), 1)
            self.assertEqual(cashier_profile.stores.all()[0], self.store1)

            i += 1

    def test_view_does_not_allow_a_store_that_belongs_to_another_user(self):

        payload = self.get_payload()
        payload['stores_info'] = [{'reg_no': self.store3.reg_no}]

        response = self.client.put(reverse(
            'api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, {'stores_info': 'You provided wrong stores.'})

        # Confirm EmployeeProfile was not changed
        cashier_profile = EmployeeProfile.objects.get(
            user__email='kate@gmail.com')

        self.assertEqual(cashier_profile.user.user_type, EMPLOYEE_USER)

        self.assertEqual(cashier_profile.stores.all().count(), 1)
        self.assertEqual(cashier_profile.stores.all()[0], self.store1)

    def test_if_view_cant_be_edited_with_an_empty_role_reg_no(self):

        payload = self.get_payload()
        payload['role_reg_no'] = ''

        response = self.client.put(reverse(
            'api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, {'role_reg_no': ['A valid integer is required.']}
        )

        # Confirm EmployeeProfile was not changed
        cashier_profile = EmployeeProfile.objects.get(
            user__email='kate@gmail.com')

        self.assertEqual(cashier_profile.user.user_type, EMPLOYEE_USER)

        self.assertEqual(cashier_profile.stores.all().count(), 1)
        self.assertEqual(cashier_profile.stores.all()[0], self.store1)

    def test_if_view_cant_be_edited_with_an_wrong_role(self):

        payload = self.get_payload()

        wrong_role_reg_nos = [
            1010,  # Wrong reg no
            'aaaa',  # Non numeric
            self.owner_group.reg_no, # Owner group 
            self.user2_manager_group.reg_no, # Another user's group
            3333333333333333333333333333333333333333333333  # Extremely long
        ]

        i = 0
        for reg_no in wrong_role_reg_nos:

            payload['role_reg_no'] = reg_no

            response = self.client.put(reverse(
                'api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)), payload)
            self.assertEqual(response.status_code, 400)

            if i == 1:
                self.assertEqual(
                    response.data,
                    {'role_reg_no': ['A valid integer is required.']}
                )

            else:

                self.assertEqual(
                    response.data,
                    {'role_reg_no': ['Wrong role was selected']}
                )

            i += 1

        # Confirm EmployeeProfile was not changed
        cashier_profile = EmployeeProfile.objects.get(
            user__email='kate@gmail.com')

        self.assertEqual(cashier_profile.user.user_type, EMPLOYEE_USER)

        self.assertEqual(cashier_profile.stores.all().count(), 1)
        self.assertEqual(cashier_profile.stores.all()[0], self.store1)

    def test_if_view_can_only_be_changed_by_its_owner(self):

        # Login a top user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_payload()

        response = self.client.put(reverse(
            'api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_changed_by_an_employee_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_payload()

        response = self.client.put(reverse(
            'api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_changed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_payload()

        response = self.client.put(reverse(
            'api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)), payload)
        self.assertEqual(response.status_code, 401)

class TpEmployeeProfileEditViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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

    def test_view_can_delete_a_cashier_profile(self):

        response = self.client.delete(
            reverse('api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)))
        self.assertEqual(response.status_code, 204)

        # Confirm the cashier_profile was deleted
        self.assertEqual(EmployeeProfile.objects.filter(
            user__email='kate@gmail.com').exists(), False)

    def test_view_can_handle_wrong_reg_no(self):

        response = self.client.delete(
            reverse('api:tp_employee_profile_edit', args=(44444,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the cashier_profile was not deleted
        self.assertEqual(EmployeeProfile.objects.filter(
            user__email='kate@gmail.com').exists(), True)

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the cashier_profile was not deleted
        self.assertEqual(EmployeeProfile.objects.filter(
            user__email='kate@gmail.com').exists(), True)

    def test_view_cant_be_deleted_by_an_employee_user(self):

        # Login a employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the cashier_profile was not deleted
        self.assertEqual(EmployeeProfile.objects.filter(
            user__email='kate@gmail.com').exists(), True)

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:tp_employee_profile_edit', args=(self.cashier_profile1.reg_no,)))
        self.assertEqual(response.status_code, 401)

        # Confirm the cashier_profile was not deleted
        self.assertEqual(EmployeeProfile.objects.filter(
            user__email='kate@gmail.com').exists(), True)

class TpEmployeeProfileClusterIndexViewTestCase(APITestCase, InitialUserDataMixin):

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
    '''
    
    def test_view_returns_the_user_empoyees_only(self):

        # Count Number of Queries #
        #with self.assertNumQueries(22):
        response = self.client.get(
            reverse('api:tp_employee_profile_cluster_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 6,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.cashier_profile4.get_full_name(),
                    'cluster_count': self.cashier_profile4.get_registered_clusters_count(), 
                    'reg_no': self.cashier_profile4.reg_no, 
                },
                {
                    'name': self.manager_profile2.get_full_name(),
                    'cluster_count': self.manager_profile2.get_registered_clusters_count(), 
                    'reg_no': self.manager_profile2.reg_no, 
                },
                {
                    'name': self.cashier_profile3.get_full_name(),
                    'cluster_count': self.cashier_profile3.get_registered_clusters_count(), 
                    'reg_no': self.cashier_profile3.reg_no, 
                },
                {
                    'name': self.cashier_profile2.get_full_name(),
                    'cluster_count': self.cashier_profile2.get_registered_clusters_count(), 
                    'reg_no': self.cashier_profile2.reg_no, 
                },
                {
                    'name': self.cashier_profile1.get_full_name(),
                    'cluster_count': self.cashier_profile1.get_registered_clusters_count(), 
                    'reg_no': self.cashier_profile1.reg_no, 
                },
                {
                    'name': self.manager_profile1.get_full_name(),
                    'cluster_count': self.manager_profile1.get_registered_clusters_count(), 
                    'reg_no': self.manager_profile1.reg_no, 
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:tp_employee_profile_cluster_index'))
        self.assertEqual(response.status_code, 401)
    '''

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all employe profiles
        EmployeeProfile.objects.all().delete()

        pagination_num_per_page = 10

        model_num_to_be_created = pagination_num_per_page+1

        # Create and confirm employees
        create_new_random_cashier_user(
            self.top_profile1,
            self.store1,
            model_num_to_be_created
        )

        self.assertEqual(
            EmployeeProfile.objects.filter(
                profile=self.top_profile1).count(),
                model_num_to_be_created
        )  # Confirm models were created

  
        employees = EmployeeProfile.objects.filter(profile=self.top_profile1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(34):
            response = self.client.get(reverse('api:tp_employee_profile_cluster_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/profile/employees/clusters/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(
            len(response_data_dict['results']), 
            pagination_num_per_page
        )

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # Check if all employees are listed except the first one since it's in 
        # the next paginated page #
        i = 0
        for employee in employees[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], employee.get_full_name())
            self.assertEqual(
                response_data_dict['results'][i]['cluster_count'], employee.get_registered_clusters_count())
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], employee.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_num_per_page)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:tp_employee_profile_cluster_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': 'http://testserver/api/profile/employees/clusters/', 
            'results': [
                {
                    'name': employees[0].get_full_name(),
                    'cluster_count': employees[0].get_registered_clusters_count(), 
                    'reg_no': employees[0].reg_no, 
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        search_terms = [
            self.manager_profile1.user.first_name,
            self.manager_profile1.user.last_name,
            self.manager_profile1.user.email
        ]

        for search_term in search_terms:
            param = f'?search={search_term}'
            response = self.client.get(reverse('api:tp_employee_profile_cluster_index') + param)
            self.assertEqual(response.status_code, 200)

            result = {
                'count': 1,
                'next': None,
                'previous': None,
                'results': [
                    {
                        'name': self.manager_profile1.get_full_name(),
                        'cluster_count': self.manager_profile1.get_registered_clusters_count(), 
                        'reg_no': self.manager_profile1.reg_no, 
                    }
                ]
            }

            self.assertEqual(response.data, result)

    def test_view_can_filter_single_store(self):

        param = f'?stores__reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_employee_profile_cluster_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 4,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.cashier_profile3.get_full_name(),
                    'cluster_count': self.cashier_profile3.get_registered_clusters_count(), 
                    'reg_no': self.cashier_profile3.reg_no, 
                },
                {
                    'name': self.cashier_profile2.get_full_name(),
                    'cluster_count': self.cashier_profile2.get_registered_clusters_count(),  
                    'reg_no': self.cashier_profile2.reg_no, 
                },
                {
                    'name': self.cashier_profile1.get_full_name(),
                    'cluster_count': self.cashier_profile1.get_registered_clusters_count(),  
                    'reg_no': self.cashier_profile1.reg_no, 
                },
                {
                    'name': self.manager_profile1.get_full_name(),
                    'cluster_count': self.cashier_profile1.get_registered_clusters_count(), 
                    'reg_no': self.manager_profile1.reg_no, 
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_multiple_stores(self):

        param = f'?stores={self.store1.reg_no},{self.store2.reg_no}'
        response = self.client.get(reverse('api:tp_employee_profile_cluster_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 6,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.cashier_profile4.get_full_name(),
                    'cluster_count': self.cashier_profile4.get_registered_clusters_count(), 
                    'reg_no': self.cashier_profile4.reg_no, 
                },
                {
                    'name': self.manager_profile2.get_full_name(),
                    'cluster_count': self.cashier_profile2.get_registered_clusters_count(), 
                    'reg_no': self.manager_profile2.reg_no, 
                },
                {
                    'name': self.cashier_profile3.get_full_name(),
                    'cluster_count': self.cashier_profile3.get_registered_clusters_count(),  
                    'reg_no': self.cashier_profile3.reg_no, 
                },
                {
                    'name': self.cashier_profile2.get_full_name(),
                    'cluster_count': self.cashier_profile2.get_registered_clusters_count(), 
                    'reg_no': self.cashier_profile2.reg_no, 
                },
                {
                    'name': self.cashier_profile1.get_full_name(),
                    'cluster_count': self.cashier_profile1.get_registered_clusters_count(),  
                    'reg_no': self.cashier_profile1.reg_no, 
                },
                {
                    'name': self.manager_profile1.get_full_name(),
                    'cluster_count': self.manager_profile1.get_registered_clusters_count(), 
                    'reg_no': self.manager_profile1.reg_no, 
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_employees(self):

        # First delete all employee profiles
        EmployeeProfile.objects.all().delete()

        response = self.client.get(
            reverse('api:tp_employee_profile_cluster_index'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': []
        }

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_employee_profile_cluster_index'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_employee_profile_cluster_index'))
        self.assertEqual(response.status_code, 401)


class TpEmployeeProfileClusterViewForViewingTestCase(APITestCase, InitialUserDataMixin, FilterDatesMixin):

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


        # Get user1 groups
        self.owner_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Owner'
        )
        self.manager_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Manager'
        )
        self.cashier_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Cashier'
        )

        # Get user2 groups
        self.user2_manager_group = UserGroup.objects.get(
            master_user=self.user2, ident_name='Manager'
        )

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
        # with self.assertNumQueries(3):
        response = self.client.get(
            reverse('api:tp_employee_profile_cluster_edit', 
            args=(self.cashier_profile1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {
            'name': self.cashier_profile1.get_full_name(), 
            'available_clusters': self.cashier_profile1.get_available_clusters_data(), 
            'registered_clusters': self.cashier_profile1.get_registered_clusters_data(), 
            'reg_no': self.cashier_profile1.reg_no,
        }

        self.assertEqual(response.data, result)

        ########################## Test maintaince ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
            reverse('api:tp_employee_profile_cluster_edit', args=(self.cashier_profile1.reg_no,)))
        self.assertEqual(response.status_code, 401)

    def test_view_can_handle_wrong_reg_no(self):

        response = self.client.get(
            reverse('api:tp_employee_profile_cluster_edit', args=(4646464,)))
        self.assertEqual(response.status_code, 404) 

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:tp_employee_profile_cluster_edit', 
            args=(self.cashier_profile1.reg_no,)))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:tp_employee_profile_cluster_edit', args=(self.cashier_profile1.reg_no,)))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:tp_employee_profile_cluster_edit', args=(self.cashier_profile1.reg_no,)))
        self.assertEqual(response.status_code, 401)



class TpEmployeeProfileClusterViewForEditingTestCase(APITestCase, InitialUserDataMixin, FilterDatesMixin):

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

        # Get user1 groups
        self.owner_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Owner'
        )
        self.manager_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Manager'
        )
        self.cashier_group = UserGroup.objects.get(
            master_user=self.user1, ident_name='Cashier'
        )

        # Get user2 groups
        self.user2_manager_group = UserGroup.objects.get(
            master_user=self.user2, ident_name='Manager'
        )

        # Create cluster models
        self.create_clustter_test_models()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_clustter_test_models(self):

        # Create clusters
        # Create cluster
        self.cluster1 = StoreCluster.objects.create(
           name='Magadi',
           profile=self.top_profile1
        )
        self.cluster2 = StoreCluster.objects.create(
           name='Nairobi',
           profile=self.top_profile1
        )
        self.cluster3 = StoreCluster.objects.create(
           name='Narok',
           profile=self.top_profile1
        )
        self.cluster4 = StoreCluster.objects.create(
           name='Amboseli',
           profile=self.top_profile1
        )

        self.cashier_profile1.clusters.add(self.cluster1, self.cluster2)   

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """
        payload = {
            'clusters_info': [
                {
                    'reg_no': self.cluster1.reg_no
                } 
            ]
        }

        return payload

    def test_view_can_remove_a_store_from_cluster(self):

        # Confirm clusters counts
        employee = EmployeeProfile.objects.get(user__email='kate@gmail.com')
        self.assertEqual(employee.clusters.all().count(), 2)

        payload = self.get_premade_payload()
        payload['clusters_info'] = []

        response = self.client.put(
            reverse('api:tp_employee_profile_cluster_edit', args=(employee.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(employee.clusters.all().count(), 0)

    def test_view_can_add_a_store_and_remove_another_at_the_same_time(self):

        # Confirm cluster counts
        employee = EmployeeProfile.objects.get(user__email='kate@gmail.com')
        self.assertEqual(employee.clusters.all().count(), 2)

        self.assertEqual(
            list(employee.clusters.all().values_list('id', flat=True)),
            [self.cluster1.id, self.cluster2.id]
        )

        payload = self.get_premade_payload()
        payload['clusters_info'] = [
            {
                'reg_no': self.cluster3.reg_no
            },
            {
                'reg_no': self.cluster4.reg_no
            } 
        ]

        response = self.client.put(
            reverse('api:tp_employee_profile_cluster_edit', args=(employee.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 200)

        # Confirm clusters addition and remove
        employee = EmployeeProfile.objects.get(user__email='kate@gmail.com')
        self.assertEqual(employee.clusters.all().count(), 2)

        self.assertEqual(
            list(employee.clusters.all().values_list('id', flat=True)),
            [self.cluster3.id, self.cluster4.id]
        )

    def test_view_can_handle_a_wrong_store_reg_no(self):

        payload = self.get_premade_payload()
        payload['clusters_info']= [{'reg_no': self.cluster2.reg_no},]

        response = self.client.put(
            reverse('api:tp_employee_profile_cluster_edit', args=(111111111,)), payload
        )
        self.assertEqual(response.status_code, 404)

    def test_view_wont_accept_an_empty_store_info(self):

        payload = self.get_premade_payload()
        payload['clusters_info'] = ''

        response = self.client.put(
            reverse(
                'api:tp_employee_profile_cluster_edit', 
                args=(self.cashier_profile1.reg_no,)), 
            payload
        )
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, 
            {'clusters_info': ['Expected a list of items but got type "str".']}
        )

        # Confirm employee clusters were not changed
        employee = EmployeeProfile.objects.get(user__email='kate@gmail.com')
        self.assertEqual(employee.clusters.all().count(), 2)

    def test_if_view_cant_be_edited_with_a_wrong_stores_reg_no(self):

        wrong_stores_reg_nos = [
            '1010',  # Wrong reg no
            'aaaa',  # Non numeric
            #3333333333333333333333333333333333333333333333  # Extremely long
        ]

        i = 0
        for reg_no in wrong_stores_reg_nos:

            payload = self.get_premade_payload()
            payload['clusters_info'][0]['reg_no'] = reg_no

            response = self.client.put(
                reverse('api:tp_employee_profile_cluster_edit', 
                args=(self.cashier_profile1.reg_no,)), 
                payload,
            )
            self.assertEqual(response.status_code, 400)

            if i == 0:
                self.assertEqual(
                    response.data, {'clusters_info': 'You provided wrong clusters.'})

            elif i == 1:
                self.assertEqual(
                    response.data,
                    {'clusters_info': {
                        0: {'reg_no': ['A valid integer is required.']}}}
                )

            else:
                self.assertEqual(
                    response.data,
                    {'clusters_info': {
                        0: {'reg_no': ['You provided wrong clusters']}}}
                )

            i += 1

        # Confirm employee clusters were not changed
        employee = EmployeeProfile.objects.get(user__email='kate@gmail.com')
        self.assertEqual(employee.clusters.all().count(), 2)
    
    def test_if_view_can_handle_a_wrong_product_reg_no(self):

        payload = self.get_premade_payload()

        wrong_reg_nos = [
            7878787, # Wrong reg no,
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        for wrong_reg_no in wrong_reg_nos:
            response = self.client.put(
                reverse('api:tp_employee_profile_cluster_edit', 
                args=(wrong_reg_no,)), 
                payload,
            )

            self.assertEqual(response.status_code, 404)

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:tp_employee_profile_cluster_edit', 
            args=(self.cashier_profile1.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:tp_employee_profile_cluster_edit', 
            args=(self.cashier_profile1.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 403)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:tp_employee_profile_cluster_edit', 
            args=(self.cashier_profile1.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 401)
