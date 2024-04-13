
from django.urls import reverse
from django.conf import settings

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.initial_user_data import InitialUserDataMixin
from core.test_utils.custom_testcase import APITestCase
from core.test_utils.create_user import create_new_random_cashier_user

from profiles.models import EmployeeProfile
from mysettings.models import MySetting

    
class MgLeanEmployeeProfileIndexViewTestCase(APITestCase, InitialUserDataMixin):
    
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

        # Increase user's store count
        self.manager_profile1.stores.add(self.store2)
        
        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
        
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
    def test_view_returns_the_user_empoyees_only(self):

        # Count Number of Queries #        
        with self.assertNumQueries(15):
            response = self.client.get(reverse('api:mg_employee_profile_index_lean'))
            self.assertEqual(response.status_code, 200)


        result = {
            'count': 5,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.cashier_profile4.get_full_name(),
                    'reg_no': self.cashier_profile4.reg_no, 
                },
                {
                    'name': self.manager_profile2.get_full_name(),
                    'reg_no': self.manager_profile2.reg_no, 
                },
                {
                    'name': self.cashier_profile3.get_full_name(),
                    'reg_no': self.cashier_profile3.reg_no, 
                },
                {
                    'name': self.cashier_profile2.get_full_name(),
                    'reg_no': self.cashier_profile2.reg_no, 
                },
                {
                    'name': self.cashier_profile1.get_full_name(),
                    'reg_no': self.cashier_profile1.reg_no, 
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=True
        ms.save()
        
        response = self.client.get(reverse('api:mg_employee_profile_index_lean'))
        self.assertEqual(response.status_code, 401)

    def test_view_can_only_show_employees_for_employee_registerd_stores(self):

        # Decrease user's store count
        self.manager_profile1.stores.remove(self.store2)

        response = self.client.get(reverse('api:mg_employee_profile_index_lean'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 3,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.cashier_profile3.get_full_name(), 
                    'reg_no': self.cashier_profile3.reg_no, 
                },
                {
                    'name': self.cashier_profile2.get_full_name(),
                    'reg_no': self.cashier_profile2.reg_no, 
                },
                {
                    'name': self.cashier_profile1.get_full_name(), 
                    'reg_no': self.cashier_profile1.reg_no, 
                }
            ]
        }

        self.assertEqual(response.data, result)
       
    # ******************************************************************* # 
    #                            Test Content                             #                  
    # ******************************************************************* #
    def test_view_for_employees_returns_the_right_content_with_pagination(self):
        
        # First delete all employe profiles apart from the manager
        EmployeeProfile.objects.all().exclude(
            reg_no=self.manager_profile1.reg_no
        ).delete()

        model_num_to_be_created = settings.LEAN_PAGINATION_PAGE_SIZE+1

        # Create and confirm employees
        create_new_random_cashier_user(
            self.top_profile1,
            self.store1,
            model_num_to_be_created
        )

        self.assertEqual(
            EmployeeProfile.objects.filter(
                profile=self.top_profile1
            ).exclude(reg_no=self.manager_profile1.reg_no).count(),
            model_num_to_be_created
        )  # Confirm models were created

  
        employees = EmployeeProfile.objects.filter(
            profile=self.top_profile1
        ).exclude(reg_no=self.manager_profile1.reg_no).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(45):
            response = self.client.get(reverse('api:mg_employee_profile_index_lean'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/mg/profile/employees/lean/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(
            len(response_data_dict['results']), 
            settings.LEAN_PAGINATION_PAGE_SIZE
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
                response_data_dict['results'][i]['reg_no'], employee.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, settings.LEAN_PAGINATION_PAGE_SIZE)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:mg_employee_profile_index_lean') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': 'http://testserver/api/mg/profile/employees/lean/', 
            'results': [
                {
                    'name': employees[0].get_full_name(),
                    'reg_no': employees[0].reg_no, 
                }
            ] 
        }
    
        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        search_terms = [
            self.cashier_profile1.user.first_name,
            self.cashier_profile1.user.last_name,
            self.cashier_profile1.user.email
        ]

        for search_term in search_terms:
            param = f'?search={search_term}'
            response = self.client.get(reverse('api:mg_employee_profile_index_lean') + param)
            self.assertEqual(response.status_code, 200)

            result = {
                'count': 1,
                'next': None,
                'previous': None,
                'results': [
                    {
                        'name': self.cashier_profile1.get_full_name(),
                        'reg_no': self.cashier_profile1.reg_no
                    }
                ]
            }

            self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_employees(self):
        
        # First delete all employe profiles apart from the manager
        EmployeeProfile.objects.all().exclude(
            reg_no=self.manager_profile1.reg_no
        ).delete()
        
        response = self.client.get(reverse('api:mg_employee_profile_index_lean'), follow=True)
        self.assertEqual(response.status_code, 200)
        
        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': []
        }
        
        self.assertEqual(response.data, result)

    def test_if_view_cant_be_viewed_by_a_top_user(self):
        
        # Login a top user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
        response = self.client.get(reverse('api:mg_employee_profile_index_lean'))
        self.assertEqual(response.status_code, 403)
                       
    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):
        
        # Unlogged in user
        self.client = APIClient()
        
        response = self.client.get(reverse('api:mg_employee_profile_index_lean'))
        self.assertEqual(response.status_code, 401)


class MgEmployeeProfileIndexViewTestCase(APITestCase, InitialUserDataMixin):
    
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

        # Increase user's store count
        self.manager_profile1.stores.add(self.store2)
        
        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
        
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
    def test_view_returns_the_user_empoyees_only(self):

        # Count Number of Queries #        
        with self.assertNumQueries(17):
            response = self.client.get(reverse('api:mg_employee_profile_index'))
            self.assertEqual(response.status_code, 200)


        result = {
            'count': 5,
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
        ms.maintenance=True
        ms.save()
        
        response = self.client.get(reverse('api:mg_employee_profile_index'))
        self.assertEqual(response.status_code, 401)

    def test_view_can_only_show_employees_for_employee_registerd_stores(self):

        # Decrease user's store count
        self.manager_profile1.stores.remove(self.store2)

        response = self.client.get(reverse('api:mg_employee_profile_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 3,
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
                }
            ],
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)
       
    # ******************************************************************* # 
    #                            Test Content                             #                  
    # ******************************************************************* #
    def test_view_for_employees_returns_the_right_content_with_pagination(self):
        
        # First delete all employe profiles apart from the manager
        EmployeeProfile.objects.all().exclude(
            reg_no=self.manager_profile1.reg_no
        ).delete()

        model_num_to_be_created = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION+1

        # Create and confirm employees
        create_new_random_cashier_user(
            self.top_profile1,
            self.store1,
            model_num_to_be_created
        )

        self.assertEqual(
            EmployeeProfile.objects.filter(
                profile=self.top_profile1
            ).exclude(reg_no=self.manager_profile1.reg_no).count(),
            model_num_to_be_created
        )  # Confirm models were created

  
        employees = EmployeeProfile.objects.filter(
            profile=self.top_profile1
        ).exclude(reg_no=self.manager_profile1.reg_no).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(27):
            response = self.client.get(reverse('api:mg_employee_profile_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/mg/profile/employees/?page=2')
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
        response = self.client.get(reverse('api:mg_employee_profile_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': 'http://testserver/api/mg/profile/employees/', 
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
            self.cashier_profile1.user.first_name,
            self.cashier_profile1.user.last_name,
            self.cashier_profile1.user.email
        ]

        for search_term in search_terms:
            param = f'?search={search_term}'
            response = self.client.get(reverse('api:mg_employee_profile_index') + param)
            self.assertEqual(response.status_code, 200)

            result = {
                'count': 1,
                'next': None,
                'previous': None,
                'results': [
                    {
                        'name': self.cashier_profile1.get_full_name(),
                        'user_email': self.cashier_profile1.user.email, 
                        'user_phone': self.cashier_profile1.user.phone, 
                        'role_name': self.cashier_profile1.role_name, 
                        'reg_no': self.cashier_profile1.reg_no, 
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
        response = self.client.get(reverse('api:mg_employee_profile_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 3,
            'next': None,
            'previous': None,
            'results': [{
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
        response = self.client.get(reverse('api:mg_employee_profile_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 5,
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
        
        # First delete all employe profiles apart from the manager
        EmployeeProfile.objects.all().exclude(
            reg_no=self.manager_profile1.reg_no
        ).delete()
        
        response = self.client.get(reverse('api:mg_employee_profile_index'), follow=True)
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

    def test_if_view_cant_be_viewed_by_a_top_user(self):
        
        # Login a top user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
        response = self.client.get(reverse('api:mg_employee_profile_index'))
        self.assertEqual(response.status_code, 403)
                       
    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):
        
        # Unlogged in user
        self.client = APIClient()
        
        response = self.client.get(reverse('api:mg_employee_profile_index'))
        self.assertEqual(response.status_code, 401)

