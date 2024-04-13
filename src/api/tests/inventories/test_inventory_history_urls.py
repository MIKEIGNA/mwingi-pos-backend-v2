import json

from django.urls import reverse
from django.conf import settings

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.initial_user_data import InitialUserDataMixin

from core.test_utils.custom_testcase import APITestCase

from products.models import Product

from mysettings.models import MySetting
from inventories.models import InventoryHistory, StockLevel


class InventoryHistoryIndexViewTestCase(APITestCase, InitialUserDataMixin):

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


        # Create models
        # Creates products
        self.product1 = Product.objects.create(
            profile=self.top_profile1,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )
        self.product1.stores.add(self.store1, self.store2)

        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )
        self.product2.stores.add(self.store1, self.store2)

        self.create_inventory_count()

        # Check test users
        self.results_users = [
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

        self.results_products = [
            {
                'name': 'Conditioner', 
                'reg_no': self.product2.reg_no
            },
            {
                'name': 'Shampoo', 
                'reg_no': self.product1.reg_no
            }
        ]

    def create_inventory_count(self):

        # Update stock level for product 1
        StockLevel.update_level( 
            user=self.user1,
            store=self.store1, 
            product=self.product1, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_RECEIVE,
            change_source_reg_no=self.product1.reg_no,
            change_source_name=self.product1.__str__(),
            line_source_reg_no=111,
            adjustment=300, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_ADDING
        )

        # Inventory history 2
        StockLevel.update_level(
            user=self.manager_profile1.user,
            store=self.store2, 
            product=self.product2, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_REFUND,
            change_source_reg_no=self.product1.reg_no,
            change_source_name=self.product1.__str__(),
            line_source_reg_no=222,
            adjustment=5, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        self.inventory_history1 = InventoryHistory.objects.get(product=self.product1)
        self.inventory_history2 = InventoryHistory.objects.get(product=self.product2)

    def test_view_returns_the_user_inventory_counts_only(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        response = self.client.get(reverse('api:inventory_history_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'product_name': self.inventory_history2.product_name, 
                    'store_name': self.inventory_history2.store_name, 
                    'user_name': self.inventory_history2.user_name, 
                    'reason': self.inventory_history2.reason, 
                    'change_source_reg_no': self.inventory_history2.change_source_reg_no,
                    'change_source_desc': self.inventory_history2.change_source_desc,
                    'change_source_name': self.inventory_history2.change_source_name,
                    'adjustment': str(self.inventory_history2.adjustment), 
                    'stock_after': str(self.inventory_history2.stock_after),
                    'creation_date': self.inventory_history2.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'synced_date': self.inventory_history2.get_synced_date(
                        self.user1.get_user_timezone()
                    ),
                    'reg_no': self.inventory_history2.reg_no
                }, 
                {
                    'product_name': self.inventory_history1.product_name, 
                    'store_name': self.inventory_history1.store_name, 
                    'user_name': self.inventory_history1.user_name, 
                    'reason': self.inventory_history1.reason, 
                    'change_source_reg_no': self.inventory_history1.change_source_reg_no,
                    'change_source_desc': self.inventory_history1.change_source_desc,
                    'change_source_name': self.inventory_history1.change_source_name,
                    'adjustment': str(self.inventory_history1.adjustment), 
                    'stock_after': str(self.inventory_history1.stock_after),
                    'creation_date': self.inventory_history1.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'synced_date': self.inventory_history1.get_synced_date(
                        self.user1.get_user_timezone()
                    ),
                    'reg_no': self.inventory_history1.reg_no
                }
            ], 
            'users': self.results_users,
            'products': self.results_products,
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

        response = self.client.get(
                reverse('api:inventory_history_index'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all inventory_counts
        InventoryHistory.objects.all().delete()

        pagination_page_size = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION

        model_num_to_be_created = pagination_page_size+1

        # Create and confirm inventory_counts
        for i in range(model_num_to_be_created):
            StockLevel.update_level(
                user=self.user1,
                store=self.store1, 
                product=self.product1, 
                inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_RECEIVE,
                change_source_reg_no=self.product1.reg_no,
                change_source_name=self.product1.__str__(),
                line_source_reg_no=i,
                adjustment=i, 
                update_type=StockLevel.STOCK_LEVEL_UPDATE_ADDING
            )


        inventory_historys = InventoryHistory.objects.filter(user=self.user1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(9):
            response = self.client.get(
                reverse('api:inventory_history_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 
            'http://testserver/api/inventory-history/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all stock adjustments are listed except the first one since it's in the next paginated page #
        i = 0
        for inventory_count in inventory_historys[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['product_name'], inventory_count.product_name)
            self.assertEqual(
                response_data_dict['results'][i]['adjustment'], f'{i+1}.00')
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
                reverse('api:inventory_history_index')  + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/inventory-history/',
            'results': [
                {
                    'product_name': inventory_historys[0].product_name, 
                    'store_name': inventory_historys[0].store_name, 
                    'user_name': inventory_historys[0].user_name, 
                    'reason': inventory_historys[0].reason, 
                    'change_source_reg_no': inventory_historys[0].change_source_reg_no,
                    'change_source_desc': inventory_historys[0].change_source_desc,
                    'change_source_name': inventory_historys[0].change_source_name,
                    'adjustment': str(inventory_historys[0].adjustment), 
                    'stock_after': str(inventory_historys[0].stock_after),
                    'creation_date': inventory_historys[0].get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'synced_date': inventory_historys[0].get_synced_date(
                        self.user1.get_user_timezone()
                    ),
                    'reg_no': inventory_historys[0].reg_no
                },
            ],
            'users': self.results_users,
            'products': self.results_products,
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

    def test_view_can_filter_store(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?store_reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:inventory_history_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'product_name': self.inventory_history1.product_name, 
                    'store_name': self.inventory_history1.store_name, 
                    'user_name': self.inventory_history1.user_name, 
                    'reason': self.inventory_history1.reason, 
                    'change_source_reg_no': self.inventory_history1.change_source_reg_no,
                    'change_source_desc': self.inventory_history1.change_source_desc,
                    'change_source_name':self.inventory_history1.change_source_name,
                    'adjustment': str(self.inventory_history1.adjustment), 
                    'stock_after': str(self.inventory_history1.stock_after),
                    'creation_date': self.inventory_history1.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'synced_date': self.inventory_history1.get_synced_date(
                        self.user1.get_user_timezone()
                    ),
                    'reg_no': self.inventory_history1.reg_no
                }
            ],
            'users': self.results_users,
            'products': self.results_products,
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

    def test_view_can_filter_product(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?product_reg_no={self.product1.reg_no}'
        response = self.client.get(reverse('api:inventory_history_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'product_name': self.inventory_history1.product_name, 
                    'store_name': self.inventory_history1.store_name, 
                    'user_name': self.inventory_history1.user_name, 
                    'reason': self.inventory_history1.reason, 
                    'change_source_reg_no': self.inventory_history1.change_source_reg_no,
                    'change_source_desc': self.inventory_history1.change_source_desc,
                    'change_source_name':self.inventory_history1.change_source_name,
                    'adjustment': str(self.inventory_history1.adjustment), 
                    'stock_after': str(self.inventory_history1.stock_after),
                    'creation_date': self.inventory_history1.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'synced_date': self.inventory_history1.get_synced_date(
                        self.user1.get_user_timezone()
                    ),
                    'reg_no': self.inventory_history1.reg_no
                }
            ],
            'users': self.results_users,
            'products': self.results_products,
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

    def test_view_can_filter_user(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?user_reg_no={self.user1.reg_no}'
        response = self.client.get(reverse('api:inventory_history_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'product_name': self.inventory_history1.product_name, 
                    'store_name': self.inventory_history1.store_name, 
                    'user_name': self.inventory_history1.user_name, 
                    'reason': self.inventory_history1.reason, 
                    'change_source_reg_no': self.inventory_history1.change_source_reg_no,
                    'change_source_desc': self.inventory_history1.change_source_desc,
                    'change_source_name':self.inventory_history1.change_source_name,
                    'adjustment': str(self.inventory_history1.adjustment), 
                    'stock_after': str(self.inventory_history1.stock_after),
                    'creation_date': self.inventory_history1.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'synced_date': self.inventory_history1.get_synced_date(
                        self.user1.get_user_timezone()
                    ),
                    'reg_no': self.inventory_history1.reg_no
                }
            ],
            'users': self.results_users,
            'products': self.results_products,
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

    def test_view_can_filter_reason(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?reason={InventoryHistory.INVENTORY_HISTORY_REFUND}'
        response = self.client.get(reverse('api:inventory_history_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'product_name': self.inventory_history2.product_name, 
                    'store_name': self.inventory_history2.store_name, 
                    'user_name': self.inventory_history2.user_name, 
                    'reason': self.inventory_history2.reason, 
                    'change_source_reg_no': self.inventory_history2.change_source_reg_no,
                    'change_source_desc': self.inventory_history2.change_source_desc,
                    'change_source_name':self.inventory_history1.change_source_name,
                    'adjustment': str(self.inventory_history2.adjustment), 
                    'stock_after': str(self.inventory_history2.stock_after),
                    'creation_date': self.inventory_history2.get_created_date(
                        self.manager_profile1.user.get_user_timezone()
                    ),
                    'synced_date': self.inventory_history2.get_synced_date(
                        self.manager_profile1.user.get_user_timezone()
                    ),
                    'reg_no': self.inventory_history2.reg_no
                }
            ],
            'users': self.results_users,
            'products': self.results_products,
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
    
    def test_view_returns_empty_when_there_are_no_inventory_counts(self):

        # First delete all inventory_counts
        InventoryHistory.objects.all().delete()

        response = self.client.get(
                reverse('api:inventory_history_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'users': self.results_users,
            'products': self.results_products,
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

        # Login an employee user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
                reverse('api:inventory_history_index'))
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
            'products': [],
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

    # def test_view_cant_be_viewed_by_an_employee_user(self):

    #     # Login an employee user
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     response = self.client.get(
    #             reverse('api:inventory_history_index'))
    #     self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:inventory_history_index'))
        self.assertEqual(response.status_code, 401)
