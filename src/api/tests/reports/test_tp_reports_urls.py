import datetime
import json
from pprint import pprint
from django.urls import reverse
from django.contrib.auth.models import Permission, Group

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from api.tests.sales.create_receipts_for_test import (
    CreateReceiptsForTesting,
    CreateReceiptsForTesting2, 
    CreateReceiptsForTesting3, 
    CreateReceiptsForVariantsTesting
)

from core.test_utils.create_store_models import (
    create_new_category, 
    create_new_discount, 
    create_new_tax
)
from core.test_utils.initial_user_data import (
    CreateTimeVariablesMixin,
    InitialUserDataMixin,
)
from core.test_utils.custom_testcase import APITestCase
from inventories.models import Product

from mysettings.models import MySetting
from products.models import Modifier, ModifierOption
from sales.models import Receipt, ReceiptLine, ReceiptPayment
from stores.models import StorePaymentMethod


class TpSaleSummaryViewTestCase(APITestCase, InitialUserDataMixin, CreateTimeVariablesMixin):

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

        """
        Adds the following date variables into the class context:
        
        today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
        last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

        # Create categories for top user 1
        self.category1 = create_new_category(self.top_profile1, 'Category1')
        self.category2 = create_new_category(self.top_profile1, 'Category2')

        # Create categories for top user 2
        self.category3 = create_new_category(self.top_profile2, 'Category3')

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Create receipts
        CreateReceiptsForTesting3(
            top_profile= self.top_profile1,
            manager=self.manager_profile1, 
            cashier= self.cashier_profile1,
            discount=None,
            tax=None,
            store1= self.store1, 
            store2= self.store2
        ).create_receipts()

        # Update product 1
        product = Product.objects.get(name="Shampoo")
        product.category = self.category1
        product.save()

        self.pagination_users = [
            { 
                'name': self.cashier_profile3.get_full_name(), 
                'reg_no': self.cashier_profile3.reg_no
            },
            { 
                'name': self.manager_profile1.get_full_name(), 
                'reg_no': self.manager_profile1.reg_no
            }, 
            { 
                'name': self.cashier_profile4.get_full_name(), 
                'reg_no': self.cashier_profile4.reg_no
            },
            {
                'name': self.cashier_profile2.get_full_name(), 
                'reg_no': self.cashier_profile2.reg_no
            }, 
            {
                'name': self.user1.get_full_name(), 
                'reg_no': self.user1.reg_no
            }, 
            {
                'name': self.cashier_profile1.get_full_name(), 
                'reg_no': self.cashier_profile1.reg_no
            }, 
            {
                'name': self.manager_profile2.get_full_name(), 
                'reg_no': self.manager_profile2.reg_no
            }, 
        ]

    def get_url_params(self, param_name, reg_nos):
        """
        Returns a string of url params
        """
        url = f'{param_name}='

        for reg_no in reg_nos:

            if reg_no == reg_nos[-1]:
                url += f'{reg_no}'
            else:
                url += f'{reg_no},'

        return url
    
    def get_store_and_user_params(self):
        """
        Returns a tuple of store and user params
        """

        store_param = self.get_url_params(
            'store_reg_no', 
            [
                self.store1.reg_no, 
                self.store2.reg_no
            ]
        )

        user_param = self.get_url_params(
            'user_reg_no',
            [
                self.top_profile1.user.reg_no, 
                self.manager_profile1.user.reg_no,
                self.cashier_profile1.user.reg_no,
            ]
        )

        return store_param, user_param

    def test_view_does_not_return_results_if_user_reg_no_param_is_not_provided(self):

        # Count Number of Queries #
        with self.assertNumQueries(11):
            param = f'?user_reg_no={self.user1.reg_no}'
            response = self.client.get(reverse('api:tp_sale_summary_view') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'total_sales_data': {
                'costs_refunds': '24000.00',
                'costs_sales': '51000.00',
                'discounts': '802.00',
                'gross_sales': '96308.00',
                'net_sale_without_taxes': '51180.00',
                'net_sales': '51300.00',
                'profits': '24300.00',
                'receipts_count': '4',
                'refunds': '47001.00',
                'taxes': '120.00'
            }, 
            'sales_data': [{'costs': '18000.00',
                 'count': '1',
                 'date': 'Jan, 02, 2024',
                 'discounts': '601.00',
                 'gross_sales': '34200.00',
                 'margin': '53.70',
                 'net_sales': '33520.00',
                 'profits': '15520.00',
                 'refunds': '0.00',
                 'taxes': '80.00'},
                {'costs': '0.00',
                 'count': '1',
                 'date': 'Feb, 01, 2024',
                 'discounts': '501.00',
                 'gross_sales': '46500.00',
                 'margin': '0.00',
                 'net_sales': '45929.00',
                 'profits': '45929.00',
                 'refunds': '45929.00',
                 'taxes': '70.00'},
                {'costs': '33000.00',
                 'count': '2',
                 'date': 'Feb, 23, 2024',
                 'discounts': '702.00',
                 'gross_sales': '63600.00',
                 'margin': '52.56',
                 'net_sales': '62788.00',
                 'profits': '29788.00',
                 'refunds': '0.00',
                 'taxes': '110.00'}], 
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)
'''
    def test_view_does_not_return_results_if_store_reg_no_param_is_not_provided(self):

        # Count Number of Queries #
        with self.assertNumQueries(9):
            param = f'?store_reg_no={self.store1.reg_no}'
            response = self.client.get(reverse('api:tp_sale_summary_view') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'sales_data': [],
            'total_sales_data': {
                'costs_refunds': '0.00',
                'costs_sales': '0.00',
                'discounts': '0.00',
                'gross_sales': '0.00',
                'net_sales': '0.00',
                'profits': '0.00',
                'refunds': '0.00'
            },
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_returns_the_user_models_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(8):
            store_param, user_param = self.get_store_and_user_params()
            param = f'?{store_param}&{user_param}'
            response = self.client.get(reverse('api:tp_sale_summary_view') + param)
            self.assertEqual(response.status_code, 200)

        result = {
            'sales_data': [
                {
                    'costs': '0',
                    'count': '1',
                    'date': 'Oct, 02, 2023',
                    'discounts': '601.00',
                    'gross_sales': '34200.00',
                    'margin': '0',
                    'net_sales': '33520.00',
                    'profits': '33520.00',
                    'refunds': '0.00',
                    'taxes': '80.00'
                },
                {
                    'costs': '0',
                    'count': '1',
                    'date': self.first_day_this_month.strftime("%b, %d, %Y"),
                    'discounts': '501.00',
                    'gross_sales': '46500.00',
                    'margin': '0',
                    'net_sales': '45929.00',
                    'profits': '0',
                    'refunds': '45929.00',
                    'taxes': '70.00'
                },
                {
                    'costs': '0',
                    'count': '2',
                    'date': self.today.strftime("%b, %d, %Y"),
                    'discounts': '702.00',
                    'gross_sales': '63600.00',
                    'margin': '0',
                    'net_sales': '62788.00',
                    'profits': '62788.00',
                    'refunds': '0.00',
                    'taxes': '110.00'
                }
            ],
            'total_sales_data': {
                'costs_refunds': '0.00',
                'costs_sales': '0.00',
                'discounts': '802.00',
                'gross_sales': '96308.00',
                'net_sales': '51300.00',
                'profits': '51300.00',
                'refunds': '47001.00'
            },
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:tp_sale_summary_view'))
        self.assertEqual(response.status_code, 401)

    def test_if_view_is_working_for_employee_user(self):

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)


        # Add store 2 to employee user
        self.manager_profile1.stores.add(self.store2)

        # Count Number of Queries #
        with self.assertNumQueries(9):
            store_param, user_param = self.get_store_and_user_params()
            param = f'?{store_param}&{user_param}'
            response = self.client.get(reverse('api:tp_sale_summary_view') + param)
            self.assertEqual(response.status_code, 200)

        result = {
            'sales_data': [
                {
                    'costs': '0',
                    'count': '1',
                    'date': 'Oct, 02, 2023',
                    'discounts': '601.00',
                    'gross_sales': '34200.00',
                    'margin': '0',
                    'net_sales': '33520.00',
                    'profits': '33520.00',
                    'refunds': '0.00',
                    'taxes': '80.00'
                },
                {
                    'costs': '0',
                    'count': '1',
                    'date': self.first_day_this_month.strftime("%b, %d, %Y"),
                    'discounts': '501.00',
                    'gross_sales': '46500.00',
                    'margin': '0',
                    'net_sales': '45929.00',
                    'profits': '0',
                    'refunds': '45929.00',
                    'taxes': '70.00'
                },
                {
                    'costs': '0',
                    'count': '2',
                    'date': self.today.strftime("%b, %d, %Y"),
                    'discounts': '702.00',
                    'gross_sales': '63600.00',
                    'margin': '0',
                    'net_sales': '62788.00',
                    'profits': '62788.00',
                    'refunds': '0.00',
                    'taxes': '110.00'
                }
            ],
            'total_sales_data': {
                'costs_refunds': '0.00',
                'costs_sales': '0.00',
                'discounts': '802.00',
                'gross_sales': '96308.00',
                'net_sales': '51300.00',
                'profits': '51300.00',
                'refunds': '47001.00'
            },
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:tp_sale_summary_view'))
        self.assertEqual(response.status_code, 401)
   
    def test_view_can_show_a_single_day_data(self):

        today_date = self.today.strftime("%Y-%m-%d")
        
        # Today
        param = f'?date_after={today_date}&date_before={today_date}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 200)

        # Confirm response
        self.assertEqual(len(response.data), 4) 

        self.assertEqual(
            response.data['total_sales_data'], 
            {
                'costs_refunds': '0.00',
                'costs_sales': '33000.00',
                'discounts': '702.00',
                'gross_sales': '62788.00',
                'net_sales': '63600.00',
                'profits': '30600.00',
                'refunds': '0.00'
            }
        )
        self.assertEqual(response.data['users'], self.pagination_users)
        self.assertEqual(
            response.data['stores'], 
            [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        )

        # Salse data
        self.assertEqual(len(response.data['sales_data']), 24)
      
        i=0
        for data in response.data['sales_data']:

            if i==3:
                self.assertEqual(
                    data, 
                    {
                        'date': '03:00:AM', 
                        'count': '1', 
                        'gross_sales': '33500.00', 
                        'net_sales': '33039.00', 
                        'discounts': '401.00', 
                        'taxes': '60.00', 
                        'costs': '17000.00', 
                        'profits': '16039.00', 
                        'margin': '51.45', 
                        'refunds': '0.00'
                    }
                )

            elif i==9:
                self.assertEqual(
                    data, 
                    {
                        'date': '09:00:AM', 
                        'count': '1', 
                        'gross_sales': '30100.00', 
                        'net_sales': '29749.00', 
                        'discounts': '301.00', 
                        'taxes': '50.00', 
                        'costs': '16000.00',
                        'profits': '13749.00', 
                        'margin': '53.78', 
                        'refunds': '0.00'
                    }
                )

            else:
                self.assertEqual(
                    data, 
                    {
                        'date': data['date'], 
                        'count': '0', 
                        'gross_sales': '0.00', 
                        'net_sales': '0.00', 
                        'discounts': '0.00', 
                        'taxes': '0.00', 
                        'costs': '0.00', 
                        'profits': '0.00', 
                        'margin': '0', 
                        'refunds': '0.00'
                    } 
                )

            i+=1 

    def test_view_wont_show_profit_and_margin_data_when_user_has_no_perm(self):

        # Remove permisson
        permission = Permission.objects.get(codename='can_view_profits')
        Group.objects.get(user=self.user1).permissions.remove(permission)

        today_date = self.today.strftime("%Y-%m-%d")
        
        # Today
        param = f'?date_after={today_date}&date_before={today_date}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 200)

        # Confirm response
        self.assertEqual(len(response.data), 4) 

        self.assertEqual(
            response.data['total_sales_data'], 
            {
                'costs_refunds': '0.00',
                'costs_sales': '33000.00',
                'discounts': '702.00',
                'gross_sales': '62788.00',
                'net_sales': '63600.00',
                'profits': '30600.00',
                'refunds': '0.00'
            }
        )
        self.assertEqual(response.data['users'], self.pagination_users)
        self.assertEqual(
            response.data['stores'], 
            [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        )

        # Salse data
        self.assertEqual(len(response.data['sales_data']), 24)
      
        i=0
        for data in response.data['sales_data']:

            if i==3:
                self.assertEqual(
                    data, 
                    {
                        'date': '03:00:AM', 
                        'count': '1', 
                        'gross_sales': '33500.00', 
                        'net_sales': '33039.00', 
                        'discounts': '401.00', 
                        'taxes': '60.00', 
                        'costs': '17000.00', 
                        'profits': '16039.00', 
                        'margin': '51.45', 
                        'refunds': '0.00'
                    }
                )

            elif i==9:
                self.assertEqual(
                    data, 
                    {
                        'date': '09:00:AM', 
                        'count': '1', 
                        'gross_sales': '30100.00', 
                        'net_sales': '29749.00', 
                        'discounts': '301.00', 
                        'taxes': '50.00', 
                        'costs': '16000.00',
                        'profits': '13749.00', 
                        'margin': '53.78', 
                        'refunds': '0.00'
                    }
                )

            else:
                self.assertEqual(
                    data, 
                    {
                        'date': data['date'], 
                        'count': '0', 
                        'gross_sales': '0.00', 
                        'net_sales': '0.00', 
                        'discounts': '0.00', 
                        'taxes': '0.00', 
                        'costs': '0.00', 
                        'profits': '0.00', 
                        'margin': '0', 
                        'refunds': '0.00'
                    } 
                )

            i+=1 

    def test_view_can_filter_with_date_for_this_month(self):

        start_date = self.first_day_this_month.strftime("%Y-%m-%d")
        end_date = self.next_month_start.strftime("%Y-%m-%d")

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 200)

        pprint(json.loads(json.dumps(response.data)))


        # Confirm response
        self.assertEqual(len(response.data), 4) 

        self.assertEqual(
            response.data['total_sales_data'], 
            {
                'costs_refunds': '24000.00',
                'costs_sales': '33000.00',
                'discounts': '201.00',
                'gross_sales': '62788.00',
                'net_sales': '17100.00',
                'profits': '8100.00',
                'refunds': '47001.00'
            }
        )
        self.assertEqual(response.data['users'], self.pagination_users)
        self.assertEqual(
            response.data['stores'], 
            [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        )

        # Salse data
        self.assertEqual(len(response.data['sales_data']), 32)

        i=0
        for data in response.data['sales_data']:

            if i==1:

                pprint(data)


                self.assertEqual(
                    data, 
                    {
                        'date': self.first_day_this_month.strftime('%b, %d, %Y'), 
                        'count': '1', 
                        'gross_sales': '46500.00', 
                        'net_sales': '45929.00', 
                        'discounts': '501.00', 
                        'taxes': '70.00', 
                        'costs': '24000.00', 
                        'profits': '21929.00', 
                        'margin': '52', 
                        'refunds': '45929.00'
                    }
                )

                
                

            elif i==datetime.datetime.today().day-1: # Today
                self.assertEqual(
                    data, 
                    {
                        'date': self.today.strftime('%b, %d, %Y'), 
                        'count': '2', 
                        'gross_sales': '63600.00', 
                        'net_sales': '62788.00', 
                        'discounts': '702.00', 
                        'taxes': '110.00', 
                        'costs': '33000.00', 
                        'profits': '29788.00',
                        'margin': '52', 
                        'refunds': '0.00'
                    }
                )

            else:
                self.assertEqual(
                    data, 
                    {
                        'date': data['date'], 
                        'count': '0', 
                        'gross_sales': '0.00', 
                        'net_sales': '0.00', 
                        'discounts': '0.00', 
                        'taxes': '0.00', 
                        'costs': '0.00', 
                        'profits': '0.00', 
                        'margin': '0', 
                        'refunds': '0.00'
                    } 
                )

            i+=1 

    def test_view_can_filter_with_date_that_has_no_receipts(self):

        start_date = '2011-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 200)

        # Confirm response
        self.assertEqual(len(response.data), 4) 

        self.assertEqual(
            response.data['total_sales_data'], 
            {
                'gross_sales': '0.00', 
                    'net_sales': '0.00', 
                    'discounts': '0.00', 
                    'profits': '0.00', 
                    'refunds': '0.00'
            }
        )
        self.assertEqual(response.data['users'], self.pagination_users)
        self.assertEqual(
            response.data['stores'], 
            [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ]
        )

        # Salse data
        self.assertEqual(len(response.data['sales_data']), 2)
      
        i=0
        for data in response.data['sales_data']:

            self.assertEqual(
                data, 
                {
                    'date': data['date'], 
                    'count': '0', 
                    'gross_sales': '0.00', 
                    'net_sales': '0.00', 
                    'discounts': '0.00', 
                    'taxes': '0.00', 
                    'costs': '0.00', 
                    'profits': '0.00', 
                    'margin': '0', 
                    'refunds': '0.00'
                } 
            )

            i+=1 
 
    def test_view_can_filter_with_date_that_is_wrong(self):
        
        # Wrong date after
        start_date = '20111-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

        # Wrong date before
        start_date = '2011-01-01'
        end_date = '20111-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})
    
    def test_view_can_filter_with_store_reg_no(self):

        # Store1
        param = f'?store_reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'total_sales_data': {
                'gross_sales': '110100.00', 
                'net_sales': '108717.00', 
                'discounts': '1203.00', 
                'profits': '51717.00', 
                'refunds': '45929.00'
            },
            'sales_data': [
                {
                    'date': self.first_day_this_month.strftime('%b, %d, %Y'),
                    'count': '1', 
                    'gross_sales': '46500.00', 
                    'net_sales': '45929.00', 
                    'discounts': '501.00', 
                    'taxes': '70.00', 
                    'costs': '24000.00', 
                    'profits': '21929.00', 
                    'margin': '52', 
                    'refunds': '45929.00'
                },
                {
                    'date': self.today.strftime('%b, %d, %Y'), 
                    'count': '2', 
                    'gross_sales': '63600.00', 
                    'net_sales': '62788.00', 
                    'discounts': '702.00', 
                    'taxes': '110.00', 
                    'costs': '33000.00', 
                    'profits': '29788.00', 
                    'margin': '52', 
                    'refunds': '0.00'
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ],
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Store2
        param = f'?store_reg_no={self.store2.reg_no}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'total_sales_data': {
                'gross_sales': '34200.00', 
                'net_sales': '33520.00', 
                'discounts': '601.00', 
                'profits': '15520.00', 
                'refunds': '0.00'
            },
            'sales_data': [
                {
                    'date': self.last_month.strftime('%b, %d, %Y'), 
                    'count': '1', 
                    'gross_sales': '34200.00', 
                    'net_sales': '33520.00', 
                    'discounts': '601.00', 
                    'taxes': '80.00', 
                    'costs': '18000.00', 
                    'profits': '15520.00', 
                    'margin': '53', 
                    'refunds': '0.00'
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ],
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_does_not_exist(self):

        param = f'?store_reg_no={1111}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data, 
            {
                'total_sales_data': {
                    'gross_sales': '0.00', 
                    'net_sales': '0.00', 
                    'discounts': '0.00', 
                    'profits': '0.00', 
                    'refunds': '0.00'
                }, 
                'sales_data': [],
                'users': self.pagination_users,
                'stores': [
                    {
                        'name': self.store1.name, 
                        'reg_no': self.store1.reg_no
                    }, 
                    {
                        'name': self.store2.name, 
                        'reg_no': self.store2.reg_no
                    }
                ],
            }
        )

    def test_view_can_filter_with_store_reg_no_that_is_wrong(self):
        
        param = '?store_reg_no=aaa'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'store_reg_no': ['Enter a number.']}
        )

    def test_view_can_filter_with_user_reg_no(self):
        
        # Top user1
        param = f'?user_reg_no={self.user1.reg_no}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'total_sales_data': {
                'gross_sales': '63600.00', 
                'net_sales': '62788.00', 
                'discounts': '702.00', 
                'profits': '29788.00', 
                'refunds': '0.00'
            },
            'sales_data': [
                {
                    'date': self.today.strftime('%b, %d, %Y'), 
                    'count': '2', 
                    'gross_sales': '63600.00', 
                    'net_sales': '62788.00', 
                    'discounts': '702.00', 
                    'taxes': '110.00', 
                    'costs': '33000.00', 
                    'profits': '29788.00', 
                    'margin': '52', 
                    'refunds': '0.00'
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ],
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Manager user1
        param = f'?user_reg_no={self.manager_profile1.user.reg_no}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'total_sales_data': {
                'gross_sales': '46500.00', 
                'net_sales': '45929.00', 
                'discounts': '501.00', 
                'profits': '21929.00', 
                'refunds': '45929.00'
            },
            'sales_data': [
                {
                    'date': self.first_day_this_month.strftime('%b, %d, %Y'), 
                    'count': '1', 
                    'gross_sales': '46500.00', 
                    'net_sales': '45929.00', 
                    'discounts': '501.00', 
                    'taxes': '70.00', 
                    'costs': '24000.00', 
                    'profits': '21929.00', 
                    'margin': '52', 
                    'refunds': '45929.00'
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ],
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)
        
        # Multiple users
        param = f'?user_reg_no={self.user1.reg_no},{self.manager_profile1.user.reg_no}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'total_sales_data': {
                'gross_sales': '110100.00', 
                'net_sales': '108717.00', 
                'discounts': '1203.00', 
                'profits': '51717.00', 
                'refunds': '45929.00'
            }, 
            'sales_data': [
                {
                    'date': 'Sep, 01, 2023', 
                    'count': '1', 
                    'gross_sales': '46500.00', 
                    'net_sales': '45929.00', 
                    'discounts': '501.00', 
                    'taxes': '70.00', 
                    'costs': '24000.00', 
                    'profits': '21929.00', 
                    'margin': '52', 
                    'refunds': '45929.00'
                }, 
                {
                    'date': 'Sep, 06, 2023', 
                    'count': '2', 
                    'gross_sales': '63600.00', 
                    'net_sales': '62788.00', 
                    'discounts': '702.00', 
                    'taxes': '110.00', 
                    'costs': '33000.00', 
                    'profits': '29788.00', 
                    'margin': '52', 
                    'refunds': '0.00'
                }
            ], 
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ],
        }
        
        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_user_reg_no_that_does_not_exist(self):

        param = f'?user_reg_no={1111}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data, 
            {
                'total_sales_data': {
                    'gross_sales': '0.00', 
                    'net_sales': '0.00', 
                    'discounts': '0.00', 
                    'profits': '0.00', 
                    'refunds': '0.00'
                }, 
                'sales_data': [],
                'users': self.pagination_users,
                'stores': [
                    {
                        'name': self.store1.name, 
                        'reg_no': self.store1.reg_no
                    }, 
                    {
                        'name': self.store2.name, 
                        'reg_no': self.store2.reg_no
                    }
                ],
            }
        )

    def test_view_can_filter_with_user_reg_no_that_is_wrong(self):
        
        param = '?user_reg_no=aaa'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'user_reg_no': ['Enter a number.']}
        )

    def test_view_can_only_be_viewed_by_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_sale_summary_view'))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data, 
            {
                'total_sales_data': {
                    'gross_sales': '0.00', 
                    'net_sales': '0.00', 
                    'discounts': '0.00', 
                    'profits': '0.00', 
                    'refunds': '0.00'
                }, 
                'sales_data': [],
                'users': [
                    {
                        'name': self.user2.get_full_name(), 
                        'reg_no': self.user2.reg_no
                    }, 
                    {
                        'name': self.manager_profile3.get_full_name(), 
                        'reg_no': self.manager_profile3.reg_no
                    }, 
                    {
                        'name': self.cashier_profile5.get_full_name(), 
                        'reg_no': self.cashier_profile5.reg_no
                    }
                ],
                'stores': [ 
                    {
                        'name': self.store3.name, 
                        'reg_no': self.store3.reg_no
                    }
                ]
            }
        )

    def test_if_employee_users_views_can_only_be_viewed_by_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Manager user1
        param = f'?user_reg_no={self.manager_profile1.user.reg_no}'
        response = self.client.get(reverse('api:tp_sale_summary_view') + param)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data, 
            {
                'total_sales_data': {
                    'gross_sales': '0.00', 
                    'net_sales': '0.00', 
                    'discounts': '0.00', 
                    'profits': '0.00', 
                    'refunds': '0.00'
                }, 
                'sales_data': [],
                'users': [
                    {
                        'name': self.user2.get_full_name(), 
                        'reg_no': self.user2.reg_no
                    }, 
                    {
                        'name': self.manager_profile3.get_full_name(), 
                        'reg_no': self.manager_profile3.reg_no
                    }, 
                    {
                        'name': self.cashier_profile5.get_full_name(), 
                        'reg_no': self.cashier_profile5.reg_no
                    }
                ],
                'stores': [ 
                    {
                        'name': self.store3.name, 
                        'reg_no': self.store3.reg_no
                    }
                ]
            }
        )

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_sale_summary_view'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_sale_summary_view'))
        self.assertEqual(response.status_code, 401)


class TpUserReportPosIndexViewTestCase(APITestCase, InitialUserDataMixin, CreateTimeVariablesMixin):

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

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Create receipts
        CreateReceiptsForTesting2(
            top_profile= self.top_profile1,
            manager=self.manager_profile1, 
            cashier= self.cashier_profile1,
            discount=None,
            tax=None,
            store1= self.store1, 
            store2= self.store2
        ).create_receipts()

        # Update product 1
        product = Product.objects.get(name="Shampoo")
        product.category = self.category1
        product.save()

        self.pagination_users = [
            { 
                'name': self.cashier_profile3.get_full_name(), 
                'reg_no': self.cashier_profile3.reg_no
            },
            { 
                'name': self.manager_profile1.get_full_name(), 
                'reg_no': self.manager_profile1.reg_no
            }, 
            { 
                'name': self.cashier_profile4.get_full_name(), 
                'reg_no': self.cashier_profile4.reg_no
            },
            {
                'name': self.cashier_profile2.get_full_name(), 
                'reg_no': self.cashier_profile2.reg_no
            }, 
            {
                'name': self.user1.get_full_name(), 
                'reg_no': self.user1.reg_no
            }, 
            {
                'name': self.cashier_profile1.get_full_name(), 
                'reg_no': self.cashier_profile1.reg_no
            }, 
            {
                'name': self.manager_profile2.get_full_name(), 
                'reg_no': self.manager_profile2.reg_no
            }, 
        ]

    def test_view_returns_the_user_models_only(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        # param = f'?stores__reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_user_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 3, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Kate Austen', 
                        'discount': '601.00', 
                        'gross_sales': '3599.00', 
                        'net_sales': '4000.00', 
                        'refund_amount': '0.00', 
                        'receipts_count': 1
                    }
                }, 
                {
                    'report_data': {
                        'name': 'Gucci Gucci', 
                        'discount': '501.00', 
                        'gross_sales': '2599.00', 
                        'net_sales': '3000.00', 
                        'refund_amount': '2599.00', 
                        'receipts_count': 1
                    }
                }, 
                {
                    'report_data': {
                        'name': 'John Lock', 
                        'discount': '401.00', 
                        'gross_sales': '1599.00', 
                        'net_sales': '2000.00', 
                        'refund_amount': '0.00', 
                        'receipts_count': 1
                    }
                },
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                
            ],
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:tp_user_report_index'))
        self.assertEqual(response.status_code, 401)

    def test_if_models_with_no_sales_wont_be_displayed(self):

        receipts = Receipt.objects.all().order_by('id')

        for r in receipts:
            r.user = self.user1
            r.save()

        response = self.client.get(reverse('api:tp_user_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'John Lock', 
                        'discount': '1503.00', 
                        'gross_sales': '7797.00', 
                        'net_sales': '9000.00', 
                        'refund_amount': '2599.00', 
                        'receipts_count': 3
                    }
                }
            ], 
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                
            ]
        } 

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_today(self):

        today_date = self.today.strftime("%Y-%m-%d")
        tomorrow_date = self.tomorrow.strftime("%Y-%m-%d")
        
        # Today
        param = f'?date_after={today_date}&date_before={tomorrow_date}'
        response = self.client.get(reverse('api:tp_user_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'John Lock', 
                        'discount': '401.00', 
                        'gross_sales': '1599.00', 
                        'net_sales': '2000.00', 
                        'refund_amount': '0.00', 
                        'receipts_count': 1
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ],
        }
            
        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_this_month(self):

        start_date = self.first_day_this_month.strftime("%Y-%m-%d")
        end_date = self.next_month_start.strftime("%Y-%m-%d")

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_user_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Gucci Gucci', 
                        'discount': '501.00', 
                        'gross_sales': '2599.00', 
                        'net_sales': '3000.00', 
                        'refund_amount': '2599.00', 
                        'receipts_count': 1
                    }
                }, 
                {
                    'report_data': {
                        'name': 'John Lock', 
                        'discount': '401.00', 
                        'gross_sales': '1599.00', 
                        'net_sales': '2000.00', 
                        'refund_amount': '0.00', 
                        'receipts_count': 1
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
                
            ],
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_has_no_receipts(self):

        start_date = '2011-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_user_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                
            ],
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_is_wrong(self):
        
        # Wrong date after
        start_date = '20111-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_user_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

        # Wrong date befor
        start_date = '2011-01-01'
        end_date = '20111-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_user_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

    def test_view_can_filter_with_store_reg_no(self):

        # Store1
        param = f'?store_reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_user_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Gucci Gucci', 
                        'discount': '501.00', 
                        'gross_sales': '2599.00', 
                        'net_sales': '3000.00', 
                        'refund_amount': '2599.00', 
                        'receipts_count': 1
                    }
                }, 
                {
                    'report_data': {
                        'name': 'John Lock', 
                        'discount': '401.00', 
                        'gross_sales': '1599.00', 
                        'net_sales': '2000.00', 
                        'refund_amount': '0.00', 
                        'receipts_count': 1
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
            ],
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Store2
        param = f'?store_reg_no={self.store2.reg_no}'
        response = self.client.get(reverse('api:tp_user_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Kate Austen', 
                        'discount': '601.00', 
                        'gross_sales': '3599.00', 
                        'net_sales': '4000.00', 
                        'refund_amount': '0.00', 
                        'receipts_count': 1
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                } 
            ],
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_does_not_exist(self):

        param = f'?store_reg_no={1111}'
        response = self.client.get(reverse('api:tp_user_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                },
            ],
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_is_wrong(self):
        
        param = '?store_reg_no=aaa'
        response = self.client.get(reverse('api:tp_user_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'store_reg_no': ['Enter a number.']}
        )

    def test_view_can_only_be_viewed_by_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_user_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': [
                {
                    'name': self.manager_profile3.get_full_name(), 
                    'reg_no': self.manager_profile3.reg_no
                }, 
                {
                    'name': self.user2.get_full_name(), 
                    'reg_no': self.user2.reg_no
                }, 
                {
                    'name': self.cashier_profile5.get_full_name(), 
                    'reg_no': self.cashier_profile5.reg_no
                }
            ],
            'stores': [ 
                {
                    'name': self.store3.name, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
                reverse('api:tp_user_report_index'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:tp_user_report_index'))
        self.assertEqual(response.status_code, 401)

class TpCategoryReportPosIndexViewTestCase(APITestCase, InitialUserDataMixin, CreateTimeVariablesMixin):

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

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Create receipts
        CreateReceiptsForTesting2(
            top_profile= self.top_profile1,
            manager=self.manager_profile1, 
            cashier= self.cashier_profile1,
            discount=None,
            tax=None,
            store1= self.store1, 
            store2= self.store2
        ).create_receipts()

        # Update product 1
        product = Product.objects.get(name="Shampoo")
        product.category = self.category1
        product.save()

        # Update product 2
        product = Product.objects.get(name="Conditioner")
        product.category = self.category2
        product.save()

        self.pagination_users = [
            { 
                'name': self.cashier_profile3.get_full_name(), 
                'reg_no': self.cashier_profile3.reg_no
            },
            { 
                'name': self.manager_profile1.get_full_name(), 
                'reg_no': self.manager_profile1.reg_no
            }, 
            { 
                'name': self.cashier_profile4.get_full_name(), 
                'reg_no': self.cashier_profile4.reg_no
            },
            {
                'name': self.cashier_profile2.get_full_name(), 
                'reg_no': self.cashier_profile2.reg_no
            }, 
            {
                'name': self.user1.get_full_name(), 
                'reg_no': self.user1.reg_no
            }, 
            {
                'name': self.cashier_profile1.get_full_name(), 
                'reg_no': self.cashier_profile1.reg_no
            }, 
            {
                'name': self.manager_profile2.get_full_name(), 
                'reg_no': self.manager_profile2.reg_no
            }, 
        ]

    def test_view_returns_the_user_models_only(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        # param = f'?stores__reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_category_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Category2', 
                        'items_sold': '37', 
                        'net_sales': '59200.00', 
                        'cost': '37000.00', 
                        'profit': '22200.00'
                    }
                }, 
                {
                    'report_data': {
                        'name': 'Category1', 
                        'items_sold': '22', 
                        'net_sales': '55000.00', 
                        'cost': '22000.00', 
                        'profit': '33000.00'
                    }
                }
            ], 
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        } 

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
                reverse('api:tp_category_report_index'))
        self.assertEqual(response.status_code, 401)

    def test_if_models_with_no_sales_wont_be_displayed(self):

        products = Product.objects.all()

        for p in products:
            p.category = None
            p.save()

        response = self.client.get(reverse('api:tp_category_report_index'))
        self.assertEqual(response.status_code, 200)
        
        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [], 
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        } 

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_today(self):

        today_date = self.today.strftime("%Y-%m-%d")
        tomorrow_date = self.tomorrow.strftime("%Y-%m-%d")
        
        # Today
        param = f'?date_after={today_date}&date_before={tomorrow_date}'
        response = self.client.get(reverse('api:tp_category_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Category2', 
                        'items_sold': '10', 
                        'net_sales': '16000.00', 
                        'cost': '10000.00', 
                        'profit': '6000.00'
                    }
                }, 
                {
                    'report_data': {
                        'name': 'Category1', 
                        'items_sold': '7', 
                        'net_sales': '17500.00', 
                        'cost': '7000.00', 
                        'profit': '10500.00'
                    }
                }
            ], 
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_this_month(self):

        start_date = self.first_day_this_month.strftime("%Y-%m-%d")
        end_date = self.next_month_start.strftime("%Y-%m-%d")

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_category_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Category2', 
                        'items_sold': '25', 
                        'net_sales': '40000.00', 
                        'cost': '25000.00', 
                        'profit': '15000.00'
                    }
                }, 
                {
                    'report_data': {
                        'name': 'Category1', 
                        'items_sold': '16', 
                        'net_sales': '40000.00', 
                        'cost': '16000.00', 
                        'profit': '24000.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_has_no_receipts(self):

        start_date = '2011-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_category_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_is_wrong(self):
        
        # Wrong date after
        start_date = '20111-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_category_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

        # Wrong date befor
        start_date = '2011-01-01'
        end_date = '20111-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_category_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

    def test_view_can_filter_with_store_reg_no(self):

        # Store1
        param = f'?store_reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_category_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Category2', 
                        'items_sold': '25', 
                        'net_sales': '40000.00', 
                        'cost': '25000.00', 
                        'profit': '15000.00'
                    }
                }, 
                {
                    'report_data': {
                        'name': 'Category1', 
                        'items_sold': '16', 
                        'net_sales': '40000.00', 
                        'cost': '16000.00', 
                        'profit': '24000.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Store2
        param = f'?store_reg_no={self.store2.reg_no}'
        response = self.client.get(reverse('api:tp_category_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Category2', 
                        'items_sold': '12', 
                        'net_sales': '19200.00', 
                        'cost': '12000.00', 
                        'profit': '7200.00'
                    }
                }, 
                {
                    'report_data': {
                        'name': 'Category1', 
                        'items_sold': '6', 
                        'net_sales': '15000.00', 
                        'cost': '6000.00', 
                        'profit': '9000.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_does_not_exist(self):

        param = f'?store_reg_no={1111}'
        response = self.client.get(reverse('api:tp_category_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_is_wrong(self):
        
        param = '?store_reg_no=aaa'
        response = self.client.get(reverse('api:tp_category_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'store_reg_no': ['Enter a number.']}
        )

    def test_view_can_filter_with_user_reg_no(self):

        # Top user1
        param = f'?user_reg_no={self.user1.reg_no}'
        response = self.client.get(reverse('api:tp_category_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Category2', 
                        'items_sold': '10', 
                        'net_sales': '16000.00', 
                        'cost': '10000.00', 
                        'profit': '6000.00'
                    }
                }, 
                {
                    'report_data': {
                        'name': 'Category1', 
                        'items_sold': '7', 
                        'net_sales': '17500.00', 
                        'cost': '7000.00', 
                        'profit': '10500.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Manager user1
        param = f'?user_reg_no={self.manager_profile1.user.reg_no}'
        response = self.client.get(reverse('api:tp_category_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Category2', 
                        'items_sold': '15', 
                        'net_sales': '24000.00', 
                        'cost': '15000.00', 
                        'profit': '9000.00'
                    }
                }, 
                {
                    'report_data': {
                        'name': 'Category1', 
                        'items_sold': '9', 
                        'net_sales': '22500.00', 
                        'cost': '9000.00', 
                        'profit': '13500.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_user_reg_no_that_does_not_exist(self):

        param = f'?user_reg_no={1111}'
        response = self.client.get(reverse('api:tp_category_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_user_reg_no_that_is_wrong(self):
        
        param = '?user_reg_no=aaa'
        response = self.client.get(reverse('api:tp_category_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'user_reg_no': ['Enter a number.']}
        )

    def test_view_can_only_be_viewed_by_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_category_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': [
                {
                    'name': self.manager_profile3.get_full_name(), 
                    'reg_no': self.manager_profile3.reg_no
                },
                {
                    'name': self.user2.get_full_name(), 
                    'reg_no': self.user2.reg_no
                }, 
                {
                    'name': self.cashier_profile5.get_full_name(), 
                    'reg_no': self.cashier_profile5.reg_no
                }
            ],
            'stores': [ 
                {
                    'name': self.store3.name, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
                reverse('api:tp_category_report_index'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_category_report_index'))
        self.assertEqual(response.status_code, 401)

class TpDiscountReportPosIndexViewTestCase(APITestCase, InitialUserDataMixin, CreateTimeVariablesMixin):

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

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

        # Create discounts for top user 1
        self.discount1 = create_new_discount(self.top_profile1, self.store1, 'Standard1')
        self.discount2 = create_new_discount(self.top_profile1, self.store2, 'Standard2')

        # Create discounts for top user 2
        self.discount3 = create_new_discount(self.top_profile2, self.store3, 'Standard3')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Create receipts
        self.create_receipts_with_discounts()
        
        self.pagination_users = [
            { 
                'name': self.cashier_profile3.get_full_name(), 
                'reg_no': self.cashier_profile3.reg_no
            },
            { 
                'name': self.manager_profile1.get_full_name(), 
                'reg_no': self.manager_profile1.reg_no
            }, 
            { 
                'name': self.cashier_profile4.get_full_name(), 
                'reg_no': self.cashier_profile4.reg_no
            },
            {
                'name': self.cashier_profile2.get_full_name(), 
                'reg_no': self.cashier_profile2.reg_no
            }, 
            {
                'name': self.user1.get_full_name(), 
                'reg_no': self.user1.reg_no
            }, 
            {
                'name': self.cashier_profile1.get_full_name(), 
                'reg_no': self.cashier_profile1.reg_no
            }, 
            {
                'name': self.manager_profile2.get_full_name(), 
                'reg_no': self.manager_profile2.reg_no
            }, 
        ]

    def create_receipts_with_discounts(self):

        CreateReceiptsForTesting2(
            top_profile= self.top_profile1,
            manager=self.manager_profile1, 
            cashier= self.cashier_profile1,
            discount=None,
            tax=None,
            store1= self.store1, 
            store2= self.store2
        ).create_receipts()

        receipts = Receipt.objects.all().order_by('id')

        receipt1 = receipts[0]
        receipt2 = receipts[1]
        receipt3 = receipts[2]

        receipt1.discount = self.discount1
        receipt1.save()

        receipt2.discount = self.discount2
        receipt2.save()

        receipt3.discount = self.discount1
        receipt3.save()

    def test_view_returns_the_user_models_only(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        # param = f'?stores__reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_discount_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard1', 
                        'count': 2, 
                        'amount': '1002.00'
                    }
                },
                {
                    'report_data': {
                        'name': 'Standard2', 
                        'count': 1, 
                        'amount': '501.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }
        
        self.assertEqual(json.loads(json.dumps(response.data)), result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
                reverse('api:tp_discount_report_index'))
        self.assertEqual(response.status_code, 401)

    def test_if_models_with_no_sales_wont_be_displayed(self):

        receipts = Receipt.objects.all().order_by('id')

        for r in receipts:
            r.discount = None
            r.save()
        
        response = self.client.get(reverse('api:tp_discount_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }
        
        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_today(self):

        today_date = self.today.strftime("%Y-%m-%d")
        tomorrow_date = self.tomorrow.strftime("%Y-%m-%d")
        
        # Today
        param = f'?date_after={today_date}&date_before={tomorrow_date}'
        response = self.client.get(reverse('api:tp_discount_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard1', 
                        'count': 1, 
                        'amount': '401.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_this_month(self):

        start_date = self.first_day_this_month.strftime("%Y-%m-%d")
        end_date = self.next_month_start.strftime("%Y-%m-%d")

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_discount_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard1', 
                        'count': 1, 
                        'amount': '401.00'
                    }
                }, 
                {
                    'report_data': {
                        'name': 'Standard2', 
                        'count': 1, 
                        'amount': '501.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_has_no_receipts(self):

        start_date = '2011-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_discount_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [ 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_is_wrong(self):
        
        # Wrong date after
        start_date = '20111-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_discount_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

        # Wrong date befor
        start_date = '2011-01-01'
        end_date = '20111-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_discount_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

    def test_view_can_filter_with_store_reg_no(self):

        # Store1
        param = f'?store_reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_discount_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard1', 
                        'count': 1, 
                        'amount': '401.00'
                    }
                }, 
                {
                    'report_data': {
                        'name': 'Standard2', 
                        'count': 1, 
                        'amount': '501.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [ 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Store2
        param = f'?store_reg_no={self.store2.reg_no}'
        response = self.client.get(reverse('api:tp_discount_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard1', 
                        'count': 1, 
                        'amount': '601.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_does_not_exist(self):

        param = f'?store_reg_no={1111}'
        response = self.client.get(reverse('api:tp_discount_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
                
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_is_wrong(self):
        
        param = '?store_reg_no=aaa'
        response = self.client.get(reverse('api:tp_discount_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'store_reg_no': ['Enter a number.']}
        )

    def test_view_can_filter_with_user_reg_no(self):

        # Top user1
        param = f'?user_reg_no={self.user1.reg_no}'
        response = self.client.get(reverse('api:tp_discount_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard1', 
                        'count': 1, 
                        'amount': '401.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
                
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Manager user1
        param = f'?user_reg_no={self.manager_profile1.user.reg_no}'
        response = self.client.get(reverse('api:tp_discount_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard2', 
                        'count': 1, 
                        'amount': '501.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                } 
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_user_reg_no_that_does_not_exist(self):

        param = f'?user_reg_no={1111}'
        response = self.client.get(reverse('api:tp_discount_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                } 
                
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_user_reg_no_that_is_wrong(self):
        
        param = '?user_reg_no=aaa'
        response = self.client.get(reverse('api:tp_discount_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'user_reg_no': ['Enter a number.']}
        )

    def test_view_can_only_be_viewed_by_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_discount_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': [
                {
                    'name': self.manager_profile3.get_full_name(), 
                    'reg_no': self.manager_profile3.reg_no
                },
                {
                    'name': self.user2.get_full_name(), 
                    'reg_no': self.user2.reg_no
                },
                {
                    'name': self.cashier_profile5.get_full_name(), 
                    'reg_no': self.cashier_profile5.reg_no
                }
            ],
            'stores': [ 
                {
                    'name': self.store3.name, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
                reverse('api:tp_discount_report_index'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:tp_discount_report_index'))
        self.assertEqual(response.status_code, 401)

class TpTaxReportPosIndexViewTestCase(APITestCase, InitialUserDataMixin, CreateTimeVariablesMixin):

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

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

        # Create taxes for top user 1
        self.tax1 = create_new_tax(self.top_profile1, self.store1, 'Standard1')
        self.tax2 = create_new_tax(self.top_profile1, self.store2, 'Standard2')

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

        # Create receipts
        self.create_receipts_with_taxes()

        self.pagination_users = [
            { 
                'name': self.cashier_profile3.get_full_name(), 
                'reg_no': self.cashier_profile3.reg_no
            },
            { 
                'name': self.manager_profile1.get_full_name(), 
                'reg_no': self.manager_profile1.reg_no
            }, 
            { 
                'name': self.cashier_profile4.get_full_name(), 
                'reg_no': self.cashier_profile4.reg_no
            },
            {
                'name': self.cashier_profile2.get_full_name(), 
                'reg_no': self.cashier_profile2.reg_no
            }, 
            {
                'name': self.user1.get_full_name(), 
                'reg_no': self.user1.reg_no
            }, 
            {
                'name': self.cashier_profile1.get_full_name(), 
                'reg_no': self.cashier_profile1.reg_no
            }, 
            {
                'name': self.manager_profile2.get_full_name(), 
                'reg_no': self.manager_profile2.reg_no
            }, 
        ]

    def create_receipts_with_taxes(self):

        CreateReceiptsForTesting2(
            top_profile= self.top_profile1,
            manager=self.manager_profile1, 
            cashier= self.cashier_profile1,
            discount=None,
            tax=None,
            store1= self.store1, 
            store2= self.store2
        ).create_receipts()

        receipts = Receipt.objects.all().order_by('id')

        receipt1 = receipts[0]
        receipt2 = receipts[1]
        receipt3 = receipts[2]

        receipt1.tax = self.tax1
        receipt1.save()

        receipt2.tax = self.tax2
        receipt2.save()

        receipt3.tax = self.tax1
        receipt3.save()

    def test_view_returns_the_user_models_only(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        # param = f'?stores__reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_tax_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard1', 
                        'rate': '20.05', 
                        'amount': '140.00'
                    }
                }, 
                {
                    'report_data': {
                        'name': 'Standard2', 
                        'rate': '20.05', 
                        'amount': '70.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }   
        
        self.assertEqual(json.loads(json.dumps(response.data)), result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
                reverse('api:tp_tax_report_index'))
        self.assertEqual(response.status_code, 401)

    def test_if_models_with_no_sales_wont_be_displayed(self):

        receipts = Receipt.objects.all().order_by('id')

        for r in receipts:
            r.tax = None
            r.save()
        
        response = self.client.get(reverse('api:tp_tax_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                } 
            ]
        }
        
        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_today(self):

        today_date = self.today.strftime("%Y-%m-%d")
        tomorrow_date = self.tomorrow.strftime("%Y-%m-%d")
        
        # Today
        param = f'?date_after={today_date}&date_before={tomorrow_date}'
        response = self.client.get(reverse('api:tp_tax_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard1', 
                        'rate': '20.05', 
                        'amount': '60.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_this_month(self):

        start_date = self.first_day_this_month.strftime("%Y-%m-%d")
        end_date = self.next_month_start.strftime("%Y-%m-%d")

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_tax_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard1', 
                        'rate': '20.05', 
                        'amount': '60.00'
                    }
                }, 
                {
                    'report_data': {
                        'name': 'Standard2', 
                        'rate': '20.05', 
                        'amount': '70.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                },
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_has_no_receipts(self):

        start_date = '2011-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_tax_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_is_wrong(self):
        
        # Wrong date after
        start_date = '20111-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_tax_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

        # Wrong date befor
        start_date = '2011-01-01'
        end_date = '20111-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_tax_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

    def test_view_can_filter_with_store_reg_no(self):

        # Store1
        param = f'?store_reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_tax_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard1', 
                        'rate': '20.05', 
                        'amount': '60.00'
                    }
                }, 
                {
                    'report_data': {
                        'name': 'Standard2', 
                        'rate': '20.05', 
                        'amount': '70.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Store2
        param = f'?store_reg_no={self.store2.reg_no}'
        response = self.client.get(reverse('api:tp_tax_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard1', 
                        'rate': '20.05', 
                        'amount': '80.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_does_not_exist(self):

        param = f'?store_reg_no={1111}'
        response = self.client.get(reverse('api:tp_tax_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_is_wrong(self):
        
        param = '?store_reg_no=aaa'
        response = self.client.get(reverse('api:tp_tax_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'store_reg_no': ['Enter a number.']}
        )

    def test_view_can_filter_with_user_reg_no(self):

        # Top user1
        param = f'?user_reg_no={self.user1.reg_no}'
        response = self.client.get(reverse('api:tp_tax_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard1', 
                        'rate': '20.05', 
                        'amount': '60.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Manager user1
        param = f'?user_reg_no={self.manager_profile1.user.reg_no}'
        response = self.client.get(reverse('api:tp_tax_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'name': 'Standard2', 
                        'rate': '20.05', 
                        'amount': '70.00'
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_user_reg_no_that_does_not_exist(self):

        param = f'?user_reg_no={1111}'
        response = self.client.get(reverse('api:tp_tax_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_user_reg_no_that_is_wrong(self):
        
        param = '?user_reg_no=aaa'
        response = self.client.get(reverse('api:tp_tax_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'user_reg_no': ['Enter a number.']}
        )

    def test_view_can_only_be_viewed_by_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_tax_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': [
                {
                    'name': self.manager_profile3.get_full_name(), 
                    'reg_no': self.manager_profile3.reg_no
                }, 
                {
                    'name': self.user2.get_full_name(), 
                    'reg_no': self.user2.reg_no
                }, 
                {
                    'name': self.cashier_profile5.get_full_name(), 
                    'reg_no': self.cashier_profile5.reg_no
                }
            ],
            'stores': [ 
                {
                    'name': self.store3.name, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
                reverse('api:tp_tax_report_index'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:tp_tax_report_index'))
        self.assertEqual(response.status_code, 401)





class TpProductReportIndexViewTestCase(APITestCase, InitialUserDataMixin, CreateTimeVariablesMixin):

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

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Create receipts
        CreateReceiptsForTesting2(
            top_profile= self.top_profile1,
            manager=self.manager_profile1, 
            cashier= self.cashier_profile1,
            discount=None,
            tax=None,
            store1= self.store1, 
            store2= self.store2
        ).create_receipts()

        self.pagination_users = [
            { 
                'name': self.cashier_profile3.get_full_name(), 
                'reg_no': self.cashier_profile3.reg_no
            },
            { 
                'name': self.manager_profile1.get_full_name(), 
                'reg_no': self.manager_profile1.reg_no
            }, 
            { 
                'name': self.cashier_profile4.get_full_name(), 
                'reg_no': self.cashier_profile4.reg_no
            },
            {
                'name': self.cashier_profile2.get_full_name(), 
                'reg_no': self.cashier_profile2.reg_no
            }, 
            {
                'name': self.user1.get_full_name(), 
                'reg_no': self.user1.reg_no
            }, 
            {
                'name': self.cashier_profile1.get_full_name(), 
                'reg_no': self.cashier_profile1.reg_no
            }, 
            {
                'name': self.manager_profile2.get_full_name(), 
                'reg_no': self.manager_profile2.reg_no
            }, 
        ]

    def create_a_normal_product(self, name='Shampoo'):

        # Create a products
        self.product = Product.objects.create(
            profile=self.top_profile1,
            tax=None,
            category=None,
            name=name,
            price=750,
            cost=120,
            sku='sku1',
            barcode='code123',
            track_stock=True
        )

        self.product.stores.add(self.store1)

        return Product.objects.get(name=name)

    def create_variant_product_with_receipts(self):

        # Create 3 variants for master product and sales
        CreateReceiptsForVariantsTesting(
            top_profile= self.top_profile1,
            product=self.product,
            store1= self.store1, 
            store2= self.store2 
        ).create_receipts() 

    def create_a_refund_receipt_for_first_receipt(self):

        receipt = Receipt.objects.get(receipt_number="110")
        self.assertEqual(receipt.get_sale_type(), 'Sale')

        receipt_line1 = receipt.receiptline_set.get(product__name="Shampoo")
        receipt_line2 = receipt.receiptline_set.get(product__name="Conditioner")

        # Perform refund
        refund_discount_amount=250
        refund_tax_amount=120
        refund_subtotal_amount=1500
        refund_total_amount=1300
        refund_loyalty_points_amount=2
        refund_item_count=6
        refund_local_reg_no=1234
        refund_created_date_timestamp=1634926712

        receipt_line_data = [
            {
                'price': receipt_line1.product.price * 2,
                'discount_amount': 0,
                'refund_units': 2,
                'reg_no': receipt_line1.reg_no,
            },
            {
                'price': receipt_line2.product.price * 4,
                'discount_amount': 0,
                'refund_units': 4,
                'reg_no': receipt_line2.reg_no,
            },
        ]

        receipt.perform_new_refund(
            discount_amount=refund_discount_amount,
            tax_amount=refund_tax_amount,
            subtotal_amount=refund_subtotal_amount,
            total_amount=refund_total_amount,
            loyalty_points_amount=refund_loyalty_points_amount,
            item_count=refund_item_count,
            local_reg_no=refund_local_reg_no,
            receipt_number='100-1001',
            created_date_timestamp=refund_created_date_timestamp,
            receipt_line_data=receipt_line_data
        )

        receipt = Receipt.objects.get(receipt_number='100-1001')
        self.assertEqual(receipt.get_sale_type(), 'Refund')

    def create_a_refund_receipt_for_third_receipt(self):

        receipt = Receipt.objects.get(receipt_number="112")
        self.assertEqual(receipt.get_sale_type(), 'Sale')

        receipt_line1 = receipt.receiptline_set.get(product__name="Shampoo")
        receipt_line2 = receipt.receiptline_set.get(product__name="Conditioner")

        # Perform refund
        refund_discount_amount=250
        refund_tax_amount=120
        refund_subtotal_amount=1500
        refund_total_amount=1300
        refund_loyalty_points_amount=2
        refund_item_count=6
        refund_local_reg_no=1234
        refund_created_date_timestamp=1634926712

        receipt_line_data = [
            {
                'price': receipt_line1.product.price * 3,
                'discount_amount': 0,
                'refund_units': 3,
                'reg_no': receipt_line1.reg_no,
            },
            {
                'price': receipt_line2.product.price * 5,
                'discount_amount': 0,
                'refund_units': 5,
                'reg_no': receipt_line2.reg_no,
            },
        ]

        receipt.perform_new_refund(
            discount_amount=refund_discount_amount,
            tax_amount=refund_tax_amount,
            subtotal_amount=refund_subtotal_amount,
            total_amount=refund_total_amount,
            loyalty_points_amount=refund_loyalty_points_amount,
            item_count=refund_item_count,
            local_reg_no=refund_local_reg_no,
            receipt_number='100-1002',
            created_date_timestamp=refund_created_date_timestamp,
            receipt_line_data=receipt_line_data
        )

        receipt = Receipt.objects.get(receipt_number='100-1002')
        self.assertEqual(receipt.get_sale_type(), 'Refund')
        
    def test_view_returns_correctly_when_there_is_a_refund(self):

        self.create_a_refund_receipt_for_first_receipt()
        self.create_a_refund_receipt_for_third_receipt()

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        # param = f'?stores__reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '37', 
                            'net_sales': '59200.00', 
                            'cost': '37000.00', 
                            'profit': '22200.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '22', 
                            'net_sales': '55000.00', 
                            'cost': '22000.00', 
                            'profit': '33000.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }   

        pprint(json.loads(json.dumps(response.data))['results'])      
        self.assertEqual(json.loads(json.dumps(response.data)), result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
                reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 401)
  
    def test_view_returns_the_user_models_only(self):

        # Count Number of Queries #
        # with self.assertNumQueries(10):
        response = self.client.get(reverse('api:tp_product_report'))
        self.assertEqual(response.status_code, 200)

        results = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                [
                    {
                        'report_data': {
                            'is_variant': False,
                            'product_data': {
                                'cost': '37000.00',
                                'discount_amount': '0.00',
                                'gross_sales': '750400.0000',
                                'items_sold': '37.00',
                                'margin': '95.07',
                                'name': 'Conditioner',
                                'net_sales': '750400.0000',
                                'net_sales_without_tax': '750400.0000',
                                'profit': '713400.0000',
                                'refunded_units': '0',
                                'refundend_amount': '0',
                                'taxes': '0'
                            }
                        }
                    },
                    {
                        'report_data': {
                            'is_variant': False,
                            'product_data': {
                                'cost': '22000.00',
                                'discount_amount': '0.00',
                                'gross_sales': '415000.0000',
                                'items_sold': '22.00',
                                'margin': '94.70',
                                'name': 'Shampoo',
                                'net_sales': '415000.0000',
                                'net_sales_without_tax': '415000.0000',
                                'profit': '393000.0000',
                                'refunded_units': '0',
                                'refundend_amount': '0',
                                'taxes': '0'
                            }
                        }
                    }
                ]
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }


        pprint(json.loads(json.dumps(response.data)))

        self.assertEqual(json.loads(json.dumps(response.data)), results)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
                reverse('api:tp_product_report'))
        self.assertEqual(response.status_code, 401)

    def test_if_models_with_no_sales_wont_be_displayed(self):

        # Remove conditioner from all sales and replace it with shampoo
        shampoo = Product.objects.get(name="Shampoo")
        conditioner = Product.objects.get(name="Conditioner")

        lines = ReceiptLine.objects.filter(product=conditioner)

        for line in lines:
            line.product = shampoo
            line.save()

        response = self.client.get(reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '59', 
                            'net_sales': '114200.00', 
                            'cost': '59000.00', 
                            'profit': '55200.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        } 

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_today(self):

        today_date = self.today.strftime("%Y-%m-%d")
        tomorrow_date = self.tomorrow.strftime("%Y-%m-%d")
        
        # Today
        param = f'?date_after={today_date}&date_before={tomorrow_date}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '10', 
                            'net_sales': '16000.00', 
                            'cost': '10000.00', 
                            'profit': '6000.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '7', 
                            'net_sales': '17500.00', 
                            'cost': '7000.00', 
                            'profit': '10500.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_this_month(self):

        start_date = self.first_day_this_month.strftime("%Y-%m-%d")
        end_date = self.next_month_start.strftime("%Y-%m-%d")

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '25', 
                            'net_sales': '40000.00', 
                            'cost': '25000.00', 
                            'profit': '15000.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '16', 
                            'net_sales': '40000.00', 
                            'cost': '16000.00', 
                            'profit': '24000.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_has_no_receipts(self):

        start_date = '2011-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_is_wrong(self):
        
        # Wrong date after
        start_date = '20111-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

        # Wrong date befor
        start_date = '2011-01-01'
        end_date = '20111-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

    def test_view_can_filter_with_store_reg_no(self):

        # Store1
        param = f'?store_reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '25', 
                            'net_sales': '40000.00', 
                            'cost': '25000.00', 
                            'profit': '15000.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '16', 
                            'net_sales': '40000.00', 
                            'cost': '16000.00', 
                            'profit': '24000.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Store2
        param = f'?store_reg_no={self.store2.reg_no}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '12', 
                            'net_sales': '19200.00', 
                            'cost': '12000.00', 
                            'profit': '7200.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '6', 
                            'net_sales': '15000.00', 
                            'cost': '6000.00', 
                            'profit': '9000.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_does_not_exist(self):

        param = f'?store_reg_no={1111}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_is_wrong(self):
        
        param = '?store_reg_no=aaa'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'store_reg_no': ['Enter a number.']}
        )

    def test_view_can_filter_with_user_reg_no(self):

        # Top user1
        param = f'?user_reg_no={self.user1.reg_no}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '10', 
                            'net_sales': '16000.00', 
                            'cost': '10000.00', 
                            'profit': '6000.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '7', 
                            'net_sales': '17500.00', 
                            'cost': '7000.00', 
                            'profit': '10500.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Manager user1
        param = f'?user_reg_no={self.manager_profile1.user.reg_no}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '15', 
                            'net_sales': '24000.00', 
                            'cost': '15000.00', 
                            'profit': '9000.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '9', 
                            'net_sales': '22500.00', 
                            'cost': '9000.00', 
                            'profit': '13500.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_user_reg_no_that_does_not_exist(self):

        param = f'?user_reg_no={1111}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_user_reg_no_that_is_wrong(self):
        
        param = '?user_reg_no=aaa'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'user_reg_no': ['Enter a number.']}
        )
    
    def test_view_with_a_variant_product(self):
        
        # First delete existing models
        Receipt.objects.all().delete()
        ReceiptLine.objects.all().delete()
        Product.objects.all().delete()

        # Create new product, variants and receipts
        self.create_a_normal_product()
        self.create_variant_product_with_receipts()

        response = self.client.get(reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': True, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '43', 
                            'net_sales': '64500.00', 
                            'cost': '34400.00', 
                            'profit': '30100.00'
                        }, 
                        'variant_data': [
                            {
                                'name': 'Small', 
                                'items_sold': '10', 
                                'net_sales': '15000.00', 
                                'cost': '8000.00', 
                                'profit': '7000.00'
                            }, 
                            {
                                'name': 'Medium', 
                                'items_sold': '16', 
                                'net_sales': '24000.00', 
                                'cost': '12800.00', 
                                'profit': '11200.00'
                            }, 
                            {
                                'name': 'Large', 
                                'items_sold': '17', 
                                'net_sales': '25500.00', 
                                'cost': '13600.00', 
                                'profit': '11900.00'
                            }
                        ]
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_if_variant_models_with_no_sales_wont_be_displayed(self):
        # First delete existing models
        Receipt.objects.all().delete()
        ReceiptLine.objects.all().delete()
        Product.objects.all().delete()

        # Create new product, variants and receipts
        self.create_a_normal_product()
        self.create_variant_product_with_receipts()

        # Create a new product
        new_product = self.create_a_normal_product('New product')

        # Remove variants from all sales and replace them with new product
        lines = ReceiptLine.objects.all()

        for line in lines:
            line.product = new_product
            line.save()

        # Make request
        response = self.client.get(reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'New product', 
                            'items_sold': '43',
                            'net_sales': '64500.00', 
                            'cost': '5160.00', 
                            'profit': '59340.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }   
        
        self.assertEqual(json.loads(json.dumps(response.data)), result)
  
    def test_view_can_only_be_viewed_by_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': [
                {
                    'name': self.manager_profile3.get_full_name(), 
                    'reg_no': self.manager_profile3.reg_no
                },
                {
                    'name': self.user2.get_full_name(), 
                    'reg_no': self.user2.reg_no
                }, 
                {
                    'name': self.cashier_profile5.get_full_name(), 
                    'reg_no': self.cashier_profile5.reg_no
                }
            ],
            'stores': [
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
                reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 401)






class TpProductReportIndexViewTestCase(APITestCase, InitialUserDataMixin, CreateTimeVariablesMixin):

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

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Create receipts
        CreateReceiptsForTesting2(
            top_profile= self.top_profile1,
            manager=self.manager_profile1, 
            cashier= self.cashier_profile1,
            discount=None,
            tax=None,
            store1= self.store1, 
            store2= self.store2
        ).create_receipts()

        self.pagination_users = [
            { 
                'name': self.cashier_profile3.get_full_name(), 
                'reg_no': self.cashier_profile3.reg_no
            },
            { 
                'name': self.manager_profile1.get_full_name(), 
                'reg_no': self.manager_profile1.reg_no
            }, 
            { 
                'name': self.cashier_profile4.get_full_name(), 
                'reg_no': self.cashier_profile4.reg_no
            },
            {
                'name': self.cashier_profile2.get_full_name(), 
                'reg_no': self.cashier_profile2.reg_no
            }, 
            {
                'name': self.user1.get_full_name(), 
                'reg_no': self.user1.reg_no
            }, 
            {
                'name': self.cashier_profile1.get_full_name(), 
                'reg_no': self.cashier_profile1.reg_no
            }, 
            {
                'name': self.manager_profile2.get_full_name(), 
                'reg_no': self.manager_profile2.reg_no
            }, 
        ]

    def create_a_normal_product(self, name='Shampoo'):

        # Create a products
        self.product = Product.objects.create(
            profile=self.top_profile1,
            tax=None,
            category=None,
            name=name,
            price=750,
            cost=120,
            sku='sku1',
            barcode='code123',
            track_stock=True
        )

        self.product.stores.add(self.store1)

        return Product.objects.get(name=name)

    def create_variant_product_with_receipts(self):

        # Create 3 variants for master product and sales
        CreateReceiptsForVariantsTesting(
            top_profile= self.top_profile1,
            product=self.product,
            store1= self.store1, 
            store2= self.store2 
        ).create_receipts() 

    def create_a_refund_receipt_for_first_receipt(self):

        receipt = Receipt.objects.get(receipt_number="110")
        self.assertEqual(receipt.get_sale_type(), 'Sale')

        receipt_line1 = receipt.receiptline_set.get(product__name="Shampoo")
        receipt_line2 = receipt.receiptline_set.get(product__name="Conditioner")

        # Perform refund
        refund_discount_amount=250
        refund_tax_amount=120
        refund_subtotal_amount=1500
        refund_total_amount=1300
        refund_loyalty_points_amount=2
        refund_item_count=6
        refund_local_reg_no=1234
        refund_created_date_timestamp=1634926712

        receipt_line_data = [
            {
                'price': receipt_line1.product.price * 2,
                'discount_amount': 0,
                'refund_units': 2,
                'reg_no': receipt_line1.reg_no,
            },
            {
                'price': receipt_line2.product.price * 4,
                'discount_amount': 0,
                'refund_units': 4,
                'reg_no': receipt_line2.reg_no,
            },
        ]

        receipt.perform_new_refund(
            discount_amount=refund_discount_amount,
            tax_amount=refund_tax_amount,
            subtotal_amount=refund_subtotal_amount,
            total_amount=refund_total_amount,
            loyalty_points_amount=refund_loyalty_points_amount,
            item_count=refund_item_count,
            local_reg_no=refund_local_reg_no,
            receipt_number='100-1001',
            created_date_timestamp=refund_created_date_timestamp,
            receipt_line_data=receipt_line_data
        )

        receipt = Receipt.objects.get(receipt_number='100-1001')
        self.assertEqual(receipt.get_sale_type(), 'Refund')

    def create_a_refund_receipt_for_third_receipt(self):

        receipt = Receipt.objects.get(receipt_number="112")
        self.assertEqual(receipt.get_sale_type(), 'Sale')

        receipt_line1 = receipt.receiptline_set.get(product__name="Shampoo")
        receipt_line2 = receipt.receiptline_set.get(product__name="Conditioner")

        # Perform refund
        refund_discount_amount=250
        refund_tax_amount=120
        refund_subtotal_amount=1500
        refund_total_amount=1300
        refund_loyalty_points_amount=2
        refund_item_count=6
        refund_local_reg_no=1234
        refund_created_date_timestamp=1634926712

        receipt_line_data = [
            {
                'price': receipt_line1.product.price * 3,
                'discount_amount': 0,
                'refund_units': 3,
                'reg_no': receipt_line1.reg_no,
            },
            {
                'price': receipt_line2.product.price * 5,
                'discount_amount': 0,
                'refund_units': 5,
                'reg_no': receipt_line2.reg_no,
            },
        ]

        receipt.perform_new_refund(
            discount_amount=refund_discount_amount,
            tax_amount=refund_tax_amount,
            subtotal_amount=refund_subtotal_amount,
            total_amount=refund_total_amount,
            loyalty_points_amount=refund_loyalty_points_amount,
            item_count=refund_item_count,
            local_reg_no=refund_local_reg_no,
            receipt_number='100-1002',
            created_date_timestamp=refund_created_date_timestamp,
            receipt_line_data=receipt_line_data
        )

        receipt = Receipt.objects.get(receipt_number='100-1002')
        self.assertEqual(receipt.get_sale_type(), 'Refund')
        
    def test_view_returns_correctly_when_there_is_a_refund(self):

        self.create_a_refund_receipt_for_first_receipt()
        self.create_a_refund_receipt_for_third_receipt()

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        # param = f'?stores__reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '37', 
                            'net_sales': '59200.00', 
                            'cost': '37000.00', 
                            'profit': '22200.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '22', 
                            'net_sales': '55000.00', 
                            'cost': '22000.00', 
                            'profit': '33000.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }   

        pprint(json.loads(json.dumps(response.data))['results'])      
        self.assertEqual(json.loads(json.dumps(response.data)), result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
                reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 401)

    def test_view_returns_the_user_models_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(10):
            response = self.client.get(reverse('api:tp_product_report_index'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '37', 
                            'net_sales': '59200.00', 
                            'cost': '37000.00', 
                            'profit': '22200.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '22', 
                            'net_sales': '55000.00', 
                            'cost': '22000.00', 
                            'profit': '33000.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }   

        pprint(json.loads(json.dumps(response.data)))
        
        self.assertEqual(json.loads(json.dumps(response.data)), result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
                reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 401)

    def test_if_models_with_no_sales_wont_be_displayed(self):

        # Remove conditioner from all sales and replace it with shampoo
        shampoo = Product.objects.get(name="Shampoo")
        conditioner = Product.objects.get(name="Conditioner")

        lines = ReceiptLine.objects.filter(product=conditioner)

        for line in lines:
            line.product = shampoo
            line.save()

        response = self.client.get(reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '59', 
                            'net_sales': '114200.00', 
                            'cost': '59000.00', 
                            'profit': '55200.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        } 

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_today(self):

        today_date = self.today.strftime("%Y-%m-%d")
        tomorrow_date = self.tomorrow.strftime("%Y-%m-%d")
        
        # Today
        param = f'?date_after={today_date}&date_before={tomorrow_date}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '10', 
                            'net_sales': '16000.00', 
                            'cost': '10000.00', 
                            'profit': '6000.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '7', 
                            'net_sales': '17500.00', 
                            'cost': '7000.00', 
                            'profit': '10500.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_this_month(self):

        start_date = self.first_day_this_month.strftime("%Y-%m-%d")
        end_date = self.next_month_start.strftime("%Y-%m-%d")

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '25', 
                            'net_sales': '40000.00', 
                            'cost': '25000.00', 
                            'profit': '15000.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '16', 
                            'net_sales': '40000.00', 
                            'cost': '16000.00', 
                            'profit': '24000.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_has_no_receipts(self):

        start_date = '2011-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_is_wrong(self):
        
        # Wrong date after
        start_date = '20111-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

        # Wrong date befor
        start_date = '2011-01-01'
        end_date = '20111-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

    def test_view_can_filter_with_store_reg_no(self):

        # Store1
        param = f'?store_reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '25', 
                            'net_sales': '40000.00', 
                            'cost': '25000.00', 
                            'profit': '15000.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '16', 
                            'net_sales': '40000.00', 
                            'cost': '16000.00', 
                            'profit': '24000.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Store2
        param = f'?store_reg_no={self.store2.reg_no}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '12', 
                            'net_sales': '19200.00', 
                            'cost': '12000.00', 
                            'profit': '7200.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '6', 
                            'net_sales': '15000.00', 
                            'cost': '6000.00', 
                            'profit': '9000.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_does_not_exist(self):

        param = f'?store_reg_no={1111}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_is_wrong(self):
        
        param = '?store_reg_no=aaa'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'store_reg_no': ['Enter a number.']}
        )

    def test_view_can_filter_with_user_reg_no(self):

        # Top user1
        param = f'?user_reg_no={self.user1.reg_no}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '10', 
                            'net_sales': '16000.00', 
                            'cost': '10000.00', 
                            'profit': '6000.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '7', 
                            'net_sales': '17500.00', 
                            'cost': '7000.00', 
                            'profit': '10500.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Manager user1
        param = f'?user_reg_no={self.manager_profile1.user.reg_no}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Conditioner', 
                            'items_sold': '15', 
                            'net_sales': '24000.00', 
                            'cost': '15000.00', 
                            'profit': '9000.00'
                        }, 
                        'variant_data': []
                    }
                }, 
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '9', 
                            'net_sales': '22500.00', 
                            'cost': '9000.00', 
                            'profit': '13500.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_user_reg_no_that_does_not_exist(self):

        param = f'?user_reg_no={1111}'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_user_reg_no_that_is_wrong(self):
        
        param = '?user_reg_no=aaa'
        response = self.client.get(reverse('api:tp_product_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'user_reg_no': ['Enter a number.']}
        )
    
    def test_view_with_a_variant_product(self):
        
        # First delete existing models
        Receipt.objects.all().delete()
        ReceiptLine.objects.all().delete()
        Product.objects.all().delete()

        # Create new product, variants and receipts
        self.create_a_normal_product()
        self.create_variant_product_with_receipts()

        response = self.client.get(reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': True, 
                        'product_data': {
                            'name': 'Shampoo', 
                            'items_sold': '43', 
                            'net_sales': '64500.00', 
                            'cost': '34400.00', 
                            'profit': '30100.00'
                        }, 
                        'variant_data': [
                            {
                                'name': 'Small', 
                                'items_sold': '10', 
                                'net_sales': '15000.00', 
                                'cost': '8000.00', 
                                'profit': '7000.00'
                            }, 
                            {
                                'name': 'Medium', 
                                'items_sold': '16', 
                                'net_sales': '24000.00', 
                                'cost': '12800.00', 
                                'profit': '11200.00'
                            }, 
                            {
                                'name': 'Large', 
                                'items_sold': '17', 
                                'net_sales': '25500.00', 
                                'cost': '13600.00', 
                                'profit': '11900.00'
                            }
                        ]
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_if_variant_models_with_no_sales_wont_be_displayed(self):
        # First delete existing models
        Receipt.objects.all().delete()
        ReceiptLine.objects.all().delete()
        Product.objects.all().delete()

        # Create new product, variants and receipts
        self.create_a_normal_product()
        self.create_variant_product_with_receipts()

        # Create a new product
        new_product = self.create_a_normal_product('New product')

        # Remove variants from all sales and replace them with new product
        lines = ReceiptLine.objects.all()

        for line in lines:
            line.product = new_product
            line.save()

        # Make request
        response = self.client.get(reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'report_data': {
                        'is_variant': False, 
                        'product_data': {
                            'name': 'New product', 
                            'items_sold': '43',
                            'net_sales': '64500.00', 
                            'cost': '5160.00', 
                            'profit': '59340.00'
                        }, 
                        'variant_data': []
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }   
        
        self.assertEqual(json.loads(json.dumps(response.data)), result)
  
    def test_view_can_only_be_viewed_by_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': [
                {
                    'name': self.manager_profile3.get_full_name(), 
                    'reg_no': self.manager_profile3.reg_no
                },
                {
                    'name': self.user2.get_full_name(), 
                    'reg_no': self.user2.reg_no
                }, 
                {
                    'name': self.cashier_profile5.get_full_name(), 
                    'reg_no': self.cashier_profile5.reg_no
                }
            ],
            'stores': [
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
                reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:tp_product_report_index'))
        self.assertEqual(response.status_code, 401)

class TpStorePaymentMethodReportIndexViewTestCase(APITestCase, InitialUserDataMixin, CreateTimeVariablesMixin):

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

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

        self.create_receipts_with_modifiers()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        self.pagination_users = [
            { 
                'name': self.cashier_profile3.get_full_name(), 
                'reg_no': self.cashier_profile3.reg_no
            },
            { 
                'name': self.manager_profile1.get_full_name(), 
                'reg_no': self.manager_profile1.reg_no
            }, 
            { 
                'name': self.cashier_profile4.get_full_name(), 
                'reg_no': self.cashier_profile4.reg_no
            },
            {
                'name': self.cashier_profile2.get_full_name(), 
                'reg_no': self.cashier_profile2.reg_no
            }, 
            {
                'name': self.user1.get_full_name(), 
                'reg_no': self.user1.reg_no
            }, 
            {
                'name': self.cashier_profile1.get_full_name(), 
                'reg_no': self.cashier_profile1.reg_no
            }, 
            {
                'name': self.manager_profile2.get_full_name(), 
                'reg_no': self.manager_profile2.reg_no
            }, 
        ]

        # Get payments
        self.cash_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.CASH_TYPE
        )

        self.mpesa_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.MPESA_TYPE
        )

        self.card_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.CARD_TYPE
        )

        self.points_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.POINTS_TYPE
        )

        self.debt_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.DEBT_TYPE
        )

        self.other_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.OTHER_TYPE
        )

    def create_receipts_with_modifiers(self):

        # Create receipts
        CreateReceiptsForTesting(
            top_profile= self.top_profile1,
            manager=self.manager_profile1, 
            cashier= self.cashier_profile1,
            store1= self.store1, 
            store2= self.store2
        ).create_receipts()

    def test_view_returns_the_user_models_only(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        # param = f'?stores__reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_store_payment_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 3,
            'next': None,
            'previous': None,
            'results': [
                {
                    'report_data': {
                        'amount': '6198.00',
                        'count': 3,
                        'name': 'Cash',
                        'refund_amount': '3599.00',
                        'refund_count': 1
                    }
                },
                {'report_data': {
                    'amount': '4599.00',
                    'count': 1,
                    'name': 'Card',
                    'refund_amount': '0.00',
                    'refund_count': 0
                    }
                },
                {
                    'report_data': {
                        'amount': '599.00',
                        'count': 1,
                        'name': 'Mpesa',
                        'refund_amount': '0.00',
                        'refund_count': 0
                    }
                },
                {
                    'report_data': {
                        'amount': '11396.00',
                        'count': 5,
                        'name': 'Total',
                        'refund_amount': '3599.00',
                        'refund_count': 1
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
                reverse('api:tp_store_payment_report_index'))
        self.assertEqual(response.status_code, 401)

    def test_if_models_with_no_sales_wont_be_displayed(self):

        # Delete receipt payment
        ReceiptPayment.objects.all().delete()
        
        response = self.client.get(reverse('api:tp_store_payment_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }
        
        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_today(self):

        today_date = self.today.strftime("%Y-%m-%d")
        tomorrow_date = self.tomorrow.strftime("%Y-%m-%d")
        
        # Today
        param = f'?date_after={today_date}&date_before={tomorrow_date}'
        response = self.client.get(reverse('api:tp_store_payment_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'report_data': {
                        'amount': '2599.00',
                        'count': 2,
                        'name': 'Cash',
                        'refund_amount': '0.00',
                        'refund_count': 0
                    }
                },
                {
                    'report_data': {
                        'amount': '599.00',
                        'count': 1,
                        'name': 'Mpesa',
                        'refund_amount': '0.00',
                        'refund_count': 0
                    }
                },
                {
                    'report_data': {
                        'amount': '3198.00',
                        'count': 3,
                        'name': 'Total',
                        'refund_amount': '0.00',
                        'refund_count': 0
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_for_this_month(self):

        start_date = self.first_day_this_month.strftime("%Y-%m-%d")
        end_date = self.next_month_start.strftime("%Y-%m-%d")

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_store_payment_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'report_data': {
                        'amount': '6198.00',
                        'count': 3,
                        'name': 'Cash',
                        'refund_amount': '3599.00',
                        'refund_count': 1
                    }
                },
                {
                    'report_data': {
                        'amount': '599.00',
                        'count': 1,
                        'name': 'Mpesa',
                        'refund_amount': '0.00',
                        'refund_count': 0
                    }
                },
                {
                    'report_data': {
                        'amount': '6797.00',
                        'count': 4,
                        'name': 'Total',
                        'refund_amount': '3599.00',
                        'refund_count': 1
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_has_no_receipts(self):

        start_date = '2011-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_store_payment_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_date_that_is_wrong(self):
        
        # Wrong date after
        start_date = '20111-01-01'
        end_date = '2011-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_store_payment_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

        # Wrong date befor
        start_date = '2011-01-01'
        end_date = '20111-01-02'

        param = f'?date_after={start_date}&date_before={end_date}'
        response = self.client.get(reverse('api:tp_store_payment_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data, {'date': ['Enter a valid date.']})

    def test_view_can_filter_with_store_reg_no(self):

        # Store1
        param = f'?store_reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_store_payment_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'report_data': {
                        'amount': '6198.00',
                        'count': 3,
                        'name': 'Cash',
                        'refund_amount': '3599.00',
                        'refund_count': 1
                    }
                },
                {
                    'report_data': {
                        'amount': '599.00',
                        'count': 1,
                        'name': 'Mpesa',
                        'refund_amount': '0.00',
                        'refund_count': 0
                    }
                },
                {
                    'report_data': {
                        'amount': '6797.00',
                        'count': 4,
                        'name': 'Total',
                        'refund_amount': '3599.00',
                        'refund_count': 1
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Store2
        param = f'?store_reg_no={self.store2.reg_no}'
        response = self.client.get(reverse('api:tp_store_payment_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'report_data': {
                        'amount': '4599.00',
                        'count': 1,
                        'name': 'Card',
                        'refund_amount': '0.00',
                        'refund_count': 0
                    }
                },
                {
                    'report_data': {
                        'amount': '4599.00',
                        'count': 1,
                        'name': 'Total',
                        'refund_amount': '0.00',
                        'refund_count': 0
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_does_not_exist(self):

        param = f'?store_reg_no={1111}'
        response = self.client.get(reverse('api:tp_store_payment_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                } 
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_store_reg_no_that_is_wrong(self):
        
        param = '?store_reg_no=aaa'
        response = self.client.get(reverse('api:tp_store_payment_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'store_reg_no': ['Enter a number.']}
        )

    def test_view_can_filter_with_user_reg_no(self):

        # Top user1
        param = f'?user_reg_no={self.user1.reg_no}'
        response = self.client.get(reverse('api:tp_store_payment_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'report_data': {
                        'amount': '2599.00',
                        'count': 2,
                        'name': 'Cash',
                        'refund_amount': '0.00',
                        'refund_count': 0
                    }
                },
                {
                    'report_data': {
                        'amount': '599.00',
                        'count': 1,
                        'name': 'Mpesa',
                        'refund_amount': '0.00',
                        'refund_count': 0
                    }
                },
                {
                    'report_data': {
                        'amount': '3198.00',
                        'count': 3,
                        'name': 'Total',
                        'refund_amount': '0.00',
                        'refund_count': 0
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }
           
        self.assertEqual(json.loads(json.dumps(response.data)), result)

        # Manager user1
        param = f'?user_reg_no={self.manager_profile1.user.reg_no}'
        response = self.client.get(reverse('api:tp_store_payment_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'report_data': {
                        'amount': '3599.00',
                        'count': 1,
                        'name': 'Cash',
                        'refund_amount': '3599.00',
                        'refund_count': 1
                    }
                },
                {
                    'report_data': {
                        'amount': '3599.00',
                        'count': 1,
                        'name': 'Total',
                        'refund_amount': '3599.00',
                        'refund_count': 1
                    }
                }
            ],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_user_reg_no_that_does_not_exist(self):

        param = f'?user_reg_no={1111}'
        response = self.client.get(reverse('api:tp_store_payment_report_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                },
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_user_reg_no_that_is_wrong(self):
        
        param = '?user_reg_no=aaa'
        response = self.client.get(reverse('api:tp_store_payment_report_index') + param)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'user_reg_no': ['Enter a number.']}
        )

    def test_view_can_only_be_viewed_by_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_store_payment_report_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': [
                {
                    'name': self.manager_profile3.get_full_name(), 
                    'reg_no': self.manager_profile3.reg_no
                },
                {
                    'name': self.user2.get_full_name(), 
                    'reg_no': self.user2.reg_no
                }, 
                {
                    'name': self.cashier_profile5.get_full_name(), 
                    'reg_no': self.cashier_profile5.reg_no
                }
            ],
            'stores': [ 
                {
                    'name': self.store3.name, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_store_payment_report_index'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_store_payment_report_index'))
        self.assertEqual(response.status_code, 401)
'''