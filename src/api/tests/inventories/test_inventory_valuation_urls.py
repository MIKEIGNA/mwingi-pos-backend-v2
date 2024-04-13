
import datetime
from decimal import Decimal
import json
from pprint import pprint
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.create_store_models import (
    create_new_category, 
    create_new_tax
)
from core.test_utils.custom_testcase import APITestCase
from core.test_utils.initial_user_data import InitialUserDataMixin
from inventories.models import StockLevel
from inventories.models.inventory_valuation_models import InventoryValuation

from mysettings.models import MySetting

from products.models import Product

class InventoryValuationMixin:

    def create_products(self):

        # Create 5 products
        self.product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category1,
            name="Coca Cola",
            price=60,
            cost=45,
        )

        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category1,
            name="Fanta",
            price=62,
            cost=46,
        )

        self.product3 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category1,
            name="Sprite",
            price=64,
            cost=47,
        )

        self.product4 = Product.objects.create( 
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category2,
            name="Radio",
            price=500,
            cost=350,
        )

        self.product5 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category2,
            name="TV",
            price=1000,
            cost=700,
        )

        # Add stock to the products
        # Product 1
        StockLevel.objects.filter(
            product=self.product1, 
            store=self.store1
        ).update(units=100)

        StockLevel.objects.filter(
            product=self.product1, 
            store=self.store2
        ).update(units=110)

        StockLevel.objects.filter(
            product=self.product1, 
            store=self.store3
        ).update(units=120)

        # Product 2
        StockLevel.objects.filter(
            product=self.product2, 
            store=self.store1
        ).update(units=200)

        StockLevel.objects.filter(
            product=self.product2, 
            store=self.store2
        ).update(units=210)

        StockLevel.objects.filter(
            product=self.product2, 
            store=self.store3
        ).update(units=220)

        # Product 3
        StockLevel.objects.filter(
            product=self.product3, 
            store=self.store1
        ).update(units=300)

        StockLevel.objects.filter(
            product=self.product3, 
            store=self.store2
        ).update(units=310)

        stock = StockLevel.objects.get(
            product=self.product3,
            store=self.store2
        )

        StockLevel.objects.filter(
            product=self.product3, 
            store=self.store3
        ).update(units=320)

        # Product 4
        StockLevel.objects.filter(
            product=self.product4, 
            store=self.store1
        ).update(units=400)

        StockLevel.objects.filter(
            product=self.product4, 
            store=self.store2
        ).update(units=410)

        StockLevel.objects.filter(
            product=self.product4, 
            store=self.store3
        ).update(units=420)

        # Product 5
        StockLevel.objects.filter(
            product=self.product5, 
            store=self.store1
        ).update(units=500)

        StockLevel.objects.filter(
            product=self.product5, 
            store=self.store2
        ).update(units=510)

        StockLevel.objects.filter(
            product=self.product5, 
            store=self.store3
        ).update(units=520)


'''
class TpProductPosIndexViewTestCase(APITestCase, InitialUserDataMixin, InventoryValuationMixin):

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

        # Change store3 profile to top_profile1
        self.store3.profile = self.top_profile1
        self.store3.save()

        #Create a category
        self.category1 = create_new_category(self.top_profile1, 'Beverages')
        self.category2 = create_new_category(self.top_profile1, 'Electronics')

        #Create a tax
        self.tax1 = create_new_tax(self.top_profile1, self.store1 ,'VAT 16', Decimal('7.00'))


        self.create_products()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_if_view_returns_the_products_for_store1_correctly(self):

        param = f'?stores__reg_no__in={self.store1.reg_no}'

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(
            reverse('api:inventory_valuation_index_view') + param)

        self.assertEqual(response.status_code, 200)

        results = {
            'count': 5, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'inventory_valuation': {
                        'name': 'Coca Cola', 
                        'in_stock': '100.00', 
                        'cost': '45.00', 
                        'inventory_value': '4500.00', 
                        'retail_value': '6000.00', 
                        'potential_profit': '1500.00', 
                        'margin': '25.00', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Fanta', 
                        'in_stock': '200.00', 
                        'cost': '46.00', 
                        'inventory_value': '9200.00', 
                        'retail_value': '12400.00', 
                        'potential_profit': '3200.00', 
                        'margin': '25.81', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Radio', 
                        'in_stock': '400.00', 
                        'cost': '350.00', 
                        'inventory_value': '140000.00', 
                        'retail_value': '200000.00', 
                        'potential_profit': '60000.00', 
                        'margin': '30.00', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Sprite', 
                        'in_stock': '300.00', 
                        'cost': '47.00', 
                        'inventory_value': '14100.00', 
                        'retail_value': '19200.00', 
                        'potential_profit': '5100.00', 
                        'margin': '26.56', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'TV', 
                        'in_stock': '500.00', 
                        'cost': '700.00', 
                        'inventory_value': '350000.00', 
                        'retail_value': '500000.00', 
                        'potential_profit': '150000.00', 
                        'margin': '30.00', 
                        'variants': None
                    }
                }
            ], 
            'profile_inventory_valuation': {
                'inventory_value': '517800.00', 
                'retail_value': '737600.00', 
                'potential_profit': '219800.00', 
                'margin': '29.80'
            }, 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                },
            ]
        }

        pprint(response.data)
        pprint(json.loads(json.dumps(response.data)))

        self.assertEqual(response.data, results)

    def test_if_view_returns_the_products_for_store2_correctly(self):

        param = f'?store_reg_no={self.store2.reg_no}'

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(
            reverse('api:inventory_valuation_index_view') + param)

        self.assertEqual(response.status_code, 200)

        results = {
            'count': 5, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'inventory_valuation': {
                        'name': 'Coca Cola', 
                        'in_stock': '110.00', 
                        'cost': '45.00', 
                        'inventory_value': '4950.00', 
                        'retail_value': '6600.00', 
                        'potential_profit': '1650.00', 
                        'margin': '25.00', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Fanta', 
                        'in_stock': '210.00', 
                        'cost': '46.00', 
                        'inventory_value': '9660.00', 
                        'retail_value': '13020.00', 
                        'potential_profit': '3360.00', 
                        'margin': '25.81', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Radio', 
                        'in_stock': '410.00', 
                        'cost': '350.00', 
                        'inventory_value': '143500.00', 
                        'retail_value': '205000.00', 
                        'potential_profit': '61500.00', 
                        'margin': '30.00', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Sprite', 
                        'in_stock': '310.00', 
                        'cost': '47.00', 
                        'inventory_value': '14570.00', 
                        'retail_value': '19840.00', 
                        'potential_profit': '5270.00', 
                        'margin': '26.56', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'TV', 
                        'in_stock': '510.00', 
                        'cost': '700.00', 
                        'inventory_value': '357000.00', 
                        'retail_value': '510000.00', 
                        'potential_profit': '153000.00', 
                        'margin': '30.00', 
                        'variants': None
                    }
                }
            ], 
            'profile_inventory_valuation': {
                'inventory_value': '529680.00', 
                'retail_value': '754460.00', 
                'potential_profit': '224780.00', 
                'margin': '29.79'
            }, 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                },
            ]
        }

        self.assertEqual(response.data, results)

    def test_if_view_returns_the_products_for_store3_correctly(self):

        param = f'?store_reg_no={self.store3.reg_no}'

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(
            reverse('api:inventory_valuation_index_view') + param)

        self.assertEqual(response.status_code, 200)

        results = {
            'count': 5, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'inventory_valuation': {
                        'name': 'Coca Cola', 
                        'in_stock': '120.00', 
                        'cost': '45.00', 
                        'inventory_value': '5400.00', 
                        'retail_value': '7200.00', 
                        'potential_profit': '1800.00', 
                        'margin': '25.00', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Fanta', 
                        'in_stock': '220.00', 
                        'cost': '46.00', 
                        'inventory_value': '10120.00', 
                        'retail_value': '13640.00', 
                        'potential_profit': '3520.00', 
                        'margin': '25.81', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Radio', 
                        'in_stock': '420.00', 
                        'cost': '350.00', 
                        'inventory_value': '147000.00', 
                        'retail_value': '210000.00', 
                        'potential_profit': '63000.00', 
                        'margin': '30.00', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Sprite', 
                        'in_stock': '320.00', 
                        'cost': '47.00', 
                        'inventory_value': '15040.00', 
                        'retail_value': '20480.00', 
                        'potential_profit': '5440.00', 
                        'margin': '26.56', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'TV', 
                        'in_stock': '520.00', 
                        'cost': '700.00', 
                        'inventory_value': '364000.00', 
                        'retail_value': '520000.00', 
                        'potential_profit': '156000.00', 
                        'margin': '30.00', 
                        'variants': None
                    }
                }
            ], 
            'profile_inventory_valuation': {
                'inventory_value': '541560.00', 
                'retail_value': '771320.00', 
                'potential_profit': '229760.00', 
                'margin': '29.79'
            }, 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                },
            ]
        }

        self.assertEqual(response.data, results)

    def test_if_view_returns_the_products_for_store1_and_store2_correctly(self):

        param = f'?store_reg_no={self.store1.reg_no},{self.store2.reg_no}'

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(
            reverse('api:inventory_valuation_index_view') + param)

        self.assertEqual(response.status_code, 200)

        results = {
            'count': 5, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'inventory_valuation': {
                        'name': 'Coca Cola', 
                        'in_stock': '210.00', 
                        'cost': '45.00', 
                        'inventory_value': '9450.00', 
                        'retail_value': '12600.00', 
                        'potential_profit': '3150.00', 
                        'margin': '25.00', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Fanta', 
                        'in_stock': '410.00', 
                        'cost': '46.00', 
                        'inventory_value': '18860.00', 
                        'retail_value': '25420.00', 
                        'potential_profit': '6560.00', 
                        'margin': '25.81', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Radio', 
                        'in_stock': '810.00', 
                        'cost': '350.00', 
                        'inventory_value': '283500.00', 
                        'retail_value': '405000.00', 
                        'potential_profit': '121500.00', 
                        'margin': '30.00', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Sprite', 
                        'in_stock': '610.00', 
                        'cost': '47.00', 
                        'inventory_value': '28670.00', 
                        'retail_value': '39040.00', 
                        'potential_profit': '10370.00', 
                        'margin': '26.56', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'TV', 
                        'in_stock': '1010.00', 
                        'cost': '700.00', 
                        'inventory_value': '707000.00', 
                        'retail_value': '1010000.00', 
                        'potential_profit': '303000.00', 
                        'margin': '30.00', 
                        'variants': None
                    }
                }
            ], 
            'profile_inventory_valuation': {
                'inventory_value': '1047480.00', 
                'retail_value': '1492060.00', 
                'potential_profit': '444580.00', 
                'margin': '29.80'
            }, 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                },
            ]
        }

        self.assertEqual(response.data, results)

    def test_if_view_returns_the_products_for_all_stores_correctly(self):

        param = f'?store_reg_no={self.store1.reg_no},{self.store2.reg_no},{self.store3.reg_no}'

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(
            reverse('api:inventory_valuation_index_view') + param)

        self.assertEqual(response.status_code, 200)

        results = {
            'count': 5, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'inventory_valuation': {
                        'name': 'Coca Cola', 
                        'in_stock': '330.00', 
                        'cost': '45.00',
                        'inventory_value': '14850.00', 
                        'retail_value': '19800.00', 
                        'potential_profit': '4950.00', 
                        'margin': '25.00', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Fanta', 
                        'in_stock': '630.00', 
                        'cost': '46.00', 
                        'inventory_value': '28980.00', 
                        'retail_value': '39060.00', 
                        'potential_profit': '10080.00', 
                        'margin': '25.81', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Radio', 
                        'in_stock': '1230.00', 
                        'cost': '350.00', 
                        'inventory_value': '430500.00', 
                        'retail_value': '615000.00', 
                        'potential_profit': '184500.00', 
                        'margin': '30.00', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'Sprite', 
                        'in_stock': '930.00', 
                        'cost': '47.00', 
                        'inventory_value': '43710.00', 
                        'retail_value': '59520.00', 
                        'potential_profit': '15810.00', 
                        'margin': '26.56', 
                        'variants': None
                    }
                }, 
                {
                    'inventory_valuation': {
                        'name': 'TV', 
                        'in_stock': '1530.00', 
                        'cost': '700.00', 
                        'inventory_value': '1071000.00', 
                        'retail_value': '1530000.00', 
                        'potential_profit': '459000.00', 
                        'margin': '30.00', 
                        'variants': None
                    }
                }
            ], 
            'profile_inventory_valuation': {
                'inventory_value': '1589040.00', 
                'retail_value': '2263380.00', 
                'potential_profit': '674340.00', 
                'margin': '29.79'
            }, 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(response.data, results)

    def test_view_returns_empty_when_there_are_no_products(self):

        # First delete all products
        Product.objects.all().delete()

        response = self.client.get(
            reverse('api:inventory_valuation_index_view'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [], 
            'profile_inventory_valuation': {
                'inventory_value': '0', 
                'retail_value': '0', 
                'potential_profit': '0', 
                'margin': '0'
            }, 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_its_owner(self):

        # Login an employee user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:inventory_valuation_index_view'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [], 
            'profile_inventory_valuation': {
                'inventory_value': '0', 
                'retail_value': '0', 
                'potential_profit': '0', 
                'margin': '0'
            }, 
            'stores': []
        }

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:inventory_valuation_index_view'))
        self.assertEqual(response.status_code, 401)
'''

class InventoryValuationViewTestCase(APITestCase, InitialUserDataMixin, InventoryValuationMixin):

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

        # Change store3 profile to top_profile1
        self.store3.profile = self.top_profile1
        self.store3.save()

        #Create a category
        self.category1 = create_new_category(self.top_profile1, 'Beverages')
        self.category2 = create_new_category(self.top_profile1, 'Electronics')

        #Create a tax
        self.tax1 = create_new_tax(self.top_profile1, self.store1 ,'VAT 16', Decimal('7.00'))

        self.create_products()

        InventoryValuation.create_inventory_valutions(
            profile=self.top_profile1,
            created_date=timezone.now()
        )

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
  
    def test_if_view_returns_the_products_for_store1_correctly(self):

        date_after = timezone.now().strftime("%Y-%m-%d")

        param = f'?store_reg_no={self.store1.reg_no}&date={date_after}'

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(reverse('api:inventory_valuation_view') + param)
        self.assertEqual(response.status_code, 200)

        results = {
            'total_inventory_data': {
                'total_inventory_value': '517800.00', 
                'total_retail_value': '737600.00', 
                'total_potential_profit': '219800.00', 
                'margin': '29.80'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'cost': '45.00', 
                    'in_stock': '100.00', 
                    'margin': '25.00', 
                    'inventory_value': '4500.00', 
                    'retail_value': '6000.00', 
                    'potential_profit': '1500.00'
                }, 
                {
                    'name': 'Fanta', 
                    'cost': '46.00', 
                    'in_stock': '200.00', 
                    'margin': '25.81', 
                    'inventory_value': '9200.00', 
                    'retail_value': '12400.00', 
                    'potential_profit': '3200.00'
                }, 
                {
                    'name': 'Radio', 
                    'cost': '350.00', 
                    'in_stock': '400.00', 
                    'margin': '30.00', 
                    'inventory_value': '140000.00', 
                    'retail_value': '200000.00', 
                    'potential_profit': '60000.00'
                }, 
                {
                    'name': 'Sprite', 
                    'cost': '47.00', 
                    'in_stock': '300.00', 
                    'margin': '26.56', 
                    'inventory_value': '14100.00', 
                    'retail_value': '19200.00', 
                    'potential_profit': '5100.00'
                }, 
                {
                    'name': 'TV', 
                    'cost': '700.00', 
                    'in_stock': '500.00', 
                    'margin': '30.00', 
                    'inventory_value': '350000.00', 
                    'retail_value': '500000.00', 
                    'potential_profit': '150000.00'
                }
            ], 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(response.data, results)

    def test_if_view_returns_the_products_for_store1_correctly_for_employees(self):

        # Add store1 to manager_profile1
        self.manager_profile1.stores.add(self.store1, self.store2, self.store3)

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        date_after = timezone.now().strftime("%Y-%m-%d")

        param = f'?store_reg_no={self.store1.reg_no}&date={date_after}'

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(reverse('api:inventory_valuation_view') + param)
        self.assertEqual(response.status_code, 200)

        results = {
            'total_inventory_data': {
                'total_inventory_value': '517800.00', 
                'total_retail_value': '737600.00', 
                'total_potential_profit': '219800.00', 
                'margin': '29.80'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'cost': '45.00', 
                    'in_stock': '100.00', 
                    'margin': '25.00', 
                    'inventory_value': '4500.00', 
                    'retail_value': '6000.00', 
                    'potential_profit': '1500.00'
                }, 
                {
                    'name': 'Fanta', 
                    'cost': '46.00', 
                    'in_stock': '200.00', 
                    'margin': '25.81', 
                    'inventory_value': '9200.00', 
                    'retail_value': '12400.00', 
                    'potential_profit': '3200.00'
                }, 
                {
                    'name': 'Radio', 
                    'cost': '350.00', 
                    'in_stock': '400.00', 
                    'margin': '30.00', 
                    'inventory_value': '140000.00', 
                    'retail_value': '200000.00', 
                    'potential_profit': '60000.00'
                }, 
                {
                    'name': 'Sprite', 
                    'cost': '47.00', 
                    'in_stock': '300.00', 
                    'margin': '26.56', 
                    'inventory_value': '14100.00', 
                    'retail_value': '19200.00', 
                    'potential_profit': '5100.00'
                }, 
                {
                    'name': 'TV', 
                    'cost': '700.00', 
                    'in_stock': '500.00', 
                    'margin': '30.00', 
                    'inventory_value': '350000.00', 
                    'retail_value': '500000.00', 
                    'potential_profit': '150000.00'
                }
            ], 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(response.data, results)

    def test_if_view_returns_the_products_for_store2_correctly(self):

        date_after = timezone.now().strftime("%Y-%m-%d")

        param = f'?store_reg_no={self.store2.reg_no}&date={date_after}'

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(reverse('api:inventory_valuation_view') + param)
        self.assertEqual(response.status_code, 200)

        results = {
            'total_inventory_data': {
                'total_inventory_value': '529680.00', 
                'total_retail_value': '754460.00', 
                'total_potential_profit': '224780.00', 
                'margin': '29.79'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'cost': '45.00', 
                    'in_stock': '110.00', 
                    'margin': '25.00', 
                    'inventory_value': '4950.00', 
                    'retail_value': '6600.00', 
                    'potential_profit': '1650.00'
                }, 
                {
                    'name': 'Fanta', 
                    'cost': '46.00', 
                    'in_stock': '210.00', 
                    'margin': '25.81', 
                    'inventory_value': '9660.00', 
                    'retail_value': '13020.00', 
                    'potential_profit': '3360.00'
                }, 
                {
                    'name': 'Radio', 
                    'cost': '350.00', 
                    'in_stock': '410.00', 
                    'margin': '30.00', 
                    'inventory_value': '143500.00', 
                    'retail_value': '205000.00', 
                    'potential_profit': '61500.00'
                }, 
                {
                    'name': 'Sprite', 
                    'cost': '47.00', 
                    'in_stock': '310.00', 
                    'margin': '26.56', 
                    'inventory_value': '14570.00', 
                    'retail_value': '19840.00', 
                    'potential_profit': '5270.00'
                }, 
                {
                    'name': 'TV', 
                    'cost': '700.00', 
                    'in_stock': '510.00', 
                    'margin': '30.00', 
                    'inventory_value': '357000.00', 
                    'retail_value': '510000.00', 
                    'potential_profit': '153000.00'
                }
            ], 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(response.data, results)

    def test_if_view_returns_the_products_for_store3_correctly(self):

        date_after = timezone.now().strftime("%Y-%m-%d")

        param = f'?store_reg_no={self.store3.reg_no}&date={date_after}'

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(reverse('api:inventory_valuation_view') + param)
        self.assertEqual(response.status_code, 200)

        results = {
            'total_inventory_data': {
                'total_inventory_value': '541560.00', 
                'total_retail_value': '771320.00', 
                'total_potential_profit': '229760.00', 
                'margin': '29.79'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'cost': '45.00', 
                    'in_stock': '120.00', 
                    'margin': '25.00', 
                    'inventory_value': '5400.00', 
                    'retail_value': '7200.00', 
                    'potential_profit': '1800.00'
                }, 
                {
                    'name': 'Fanta', 
                    'cost': '46.00', 
                    'in_stock': '220.00', 
                    'margin': '25.81', 
                    'inventory_value': '10120.00', 
                    'retail_value': '13640.00', 
                    'potential_profit': '3520.00'
                }, 
                {
                    'name': 'Radio', 
                    'cost': '350.00', 
                    'in_stock': '420.00', 
                    'margin': '30.00', 
                    'inventory_value': '147000.00', 
                    'retail_value': '210000.00', 
                    'potential_profit': '63000.00'
                }, 
                {
                    'name': 'Sprite', 
                    'cost': '47.00', 
                    'in_stock': '320.00', 
                    'margin': '26.56', 
                    'inventory_value': '15040.00', 
                    'retail_value': '20480.00', 
                    'potential_profit': '5440.00'
                }, 
                {
                    'name': 'TV', 
                    'cost': '700.00', 
                    'in_stock': '520.00', 
                    'margin': '30.00', 
                    'inventory_value': '364000.00', 
                    'retail_value': '520000.00', 
                    'potential_profit': '156000.00'
                }
            ], 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(response.data, results)
  
    def test_if_view_returns_the_products_for_all_stores_correctly(self):

        date_after = timezone.now().strftime("%Y-%m-%d")

        param = f'?store_reg_no={self.store1.reg_no},{self.store2.reg_no},{self.store3.reg_no}&date={date_after}'

        response = self.client.get(reverse('api:inventory_valuation_view') + param)
        self.assertEqual(response.status_code, 200)

        results = {
            'total_inventory_data': {
                'total_inventory_value': '1589040.00', 
                'total_retail_value': '2263380.00', 
                'total_potential_profit': '674340.00', 
                'margin': '29.79'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'cost': '45.00', 
                    'in_stock': '330.00', 
                    'margin': '25.00', 
                    'inventory_value': '14850.00', 
                    'retail_value': '19800.00', 
                    'potential_profit': '4950.00'
                }, 
                {
                    'name': 'Fanta', 
                    'cost': '46.00', 
                    'in_stock': '630.00', 
                    'margin': '25.81', 
                    'inventory_value': '28980.00', 
                    'retail_value': '39060.00', 
                    'potential_profit': '10080.00'
                }, 
                {
                    'name': 'Radio', 
                    'cost': '350.00', 
                    'in_stock': '1230.00', 
                    'margin': '30.00', 
                    'inventory_value': '430500.00', 
                    'retail_value': '615000.00', 
                    'potential_profit': '184500.00'
                }, 
                {
                    'name': 'Sprite', 
                    'cost': '47.00', 
                    'in_stock': '930.00', 
                    'margin': '26.56', 
                    'inventory_value': '43710.00', 
                    'retail_value': '59520.00', 
                    'potential_profit': '15810.00'
                }, 
                {
                    'name': 'TV', 
                    'cost': '700.00', 
                    'in_stock': '1530.00', 
                    'margin': '30.00', 
                    'inventory_value': '1071000.00', 
                    'retail_value': '1530000.00', 
                    'potential_profit': '459000.00'
                }
            ], 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(response.data, results)
        
    def test_if_view_filters_with_date(self):

        # Create dates
        today = timezone.now()
        yesterday = today - datetime.timedelta(days=1)
        yesterday2 = today - datetime.timedelta(days=2)

        today_str = today.strftime("%Y-%m-%d")
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        yesterday2_str = yesterday2.strftime("%Y-%m-%d")

        # Update inventory valuation
        inventory_valuations = InventoryValuation.objects.all().order_by('id')

        self.assertEqual(len(inventory_valuations), 3)

        inventory_valuation1 = inventory_valuations[0]
        inventory_valuation2 = inventory_valuations[1]
        inventory_valuation3 = inventory_valuations[2]

        inventory_valuation1.created_date = today
        inventory_valuation1.save()

        inventory_valuation2.created_date = yesterday
        inventory_valuation2.save()

        inventory_valuation3.created_date = yesterday2
        inventory_valuation3.save()

        def get_params(date_after):
            param = f'?store_reg_no={self.store1.reg_no},{self.store2.reg_no},{self.store3.reg_no}&date={date_after}'
            return param
        
        # Test filtering by today
        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(
            reverse('api:inventory_valuation_view') + get_params(today_str))
        self.assertEqual(response.status_code, 200)

        results = {
            'total_inventory_data': {
                'total_inventory_value': '1589040.00', 
                'total_retail_value': '2263380.00', 
                'total_potential_profit': '674340.00', 
                'margin': '29.79'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'in_stock': '330.00', 
                    'cost': '45.00', 
                    'inventory_value': '14850.00', 
                    'retail_value': '19800.00', 
                    'potential_profit': '4950.00', 
                    'margin': '25.00'
                }, 
                {
                    'name': 'Fanta', 
                    'in_stock': '630.00', 
                    'cost': '46.00', 
                    'inventory_value': '28980.00', 
                    'retail_value': '39060.00', 
                    'potential_profit': '10080.00', 
                    'margin': '25.81'
                }, 
                {
                    'name': 'Radio', 
                    'in_stock': '1230.00', 
                    'cost': '350.00', 
                    'inventory_value': '430500.00', 
                    'retail_value': '615000.00', 
                    'potential_profit': '184500.00', 
                    'margin': '30.00'
                }, 
                {
                    'name': 'Sprite', 
                    'in_stock': '930.00', 
                    'cost': '47.00', 
                    'inventory_value': '43710.00', 
                    'retail_value': '59520.00', 
                    'potential_profit': '15810.00', 
                    'margin': '26.56'
                }, 
                {
                    'name': 'TV', 
                    'in_stock': '1530.00', 
                    'cost': '700.00', 
                    'inventory_value': '1071000.00', 
                    'retail_value': '1530000.00', 
                    'potential_profit': '459000.00', 
                    'margin': '30.00'
                }
            ], 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(response.data, results)

        # Test filtering by yesterday
        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(
            reverse('api:inventory_valuation_view') + get_params(yesterday_str))
        self.assertEqual(response.status_code, 200)

        results = {
            'total_inventory_data': {
                'total_inventory_value': '529680.00', 
                'total_retail_value': '754460.00', 
                'total_potential_profit': '224780.00', 
                'margin': '29.79'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'cost': '45.00', 
                    'in_stock': '110.00', 
                    'margin': '25.00', 
                    'inventory_value': '4950.00', 
                    'retail_value': '6600.00', 
                    'potential_profit': '1650.00'
                }, 
                {
                    'name': 'Fanta', 
                    'cost': '46.00', 
                    'in_stock': '210.00', 
                    'margin': '25.81', 
                    'inventory_value': '9660.00', 
                    'retail_value': '13020.00', 
                    'potential_profit': '3360.00'
                }, 
                {
                    'name': 'Radio', 
                    'cost': '350.00', 
                    'in_stock': '410.00', 
                    'margin': '30.00', 
                    'inventory_value': '143500.00', 
                    'retail_value': '205000.00', 
                    'potential_profit': '61500.00'
                }, 
                {
                    'name': 'Sprite', 
                    'cost': '47.00', 
                    'in_stock': '310.00', 
                    'margin': '26.56', 
                    'inventory_value': '14570.00', 
                    'retail_value': '19840.00', 
                    'potential_profit': '5270.00'
                }, 
                {
                    'name': 'TV', 
                    'cost': '700.00', 
                    'in_stock': '510.00', 
                    'margin': '30.00', 
                    'inventory_value': '357000.00', 
                    'retail_value': '510000.00', 
                    'potential_profit': '153000.00'
                }
            ], 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(response.data, results)

        # Test filtering by yesterday2
        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(
            reverse('api:inventory_valuation_view') + get_params(yesterday2_str))
        self.assertEqual(response.status_code, 200)

        results = {
            'total_inventory_data': {
                'total_inventory_value': '541560.00', 
                'total_retail_value': '771320.00', 
                'total_potential_profit': '229760.00', 
                'margin': '29.79'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'cost': '45.00', 
                    'in_stock': '120.00', 
                    'margin': '25.00', 
                    'inventory_value': '5400.00', 
                    'retail_value': '7200.00', 
                    'potential_profit': '1800.00'
                }, 
                {
                    'name': 'Fanta', 
                    'cost': '46.00', 
                    'in_stock': '220.00', 
                    'margin': '25.81', 
                    'inventory_value': '10120.00', 
                    'retail_value': '13640.00', 
                    'potential_profit': '3520.00'
                }, 
                {
                    'name': 'Radio', 
                    'cost': '350.00', 
                    'in_stock': '420.00', 
                    'margin': '30.00', 
                    'inventory_value': '147000.00', 
                    'retail_value': '210000.00', 
                    'potential_profit': '63000.00'
                }, 
                {
                    'name': 'Sprite', 
                    'cost': '47.00', 
                    'in_stock': '320.00', 
                    'margin': '26.56', 
                    'inventory_value': '15040.00', 
                    'retail_value': '20480.00', 
                    'potential_profit': '5440.00'
                }, 
                {
                    'name': 'TV', 
                    'cost': '700.00', 
                    'in_stock': '520.00', 
                    'margin': '30.00', 
                    'inventory_value': '364000.00', 
                    'retail_value': '520000.00', 
                    'potential_profit': '156000.00'
                }
            ], 
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
                },
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store3.reg_no
                }
            ]
        }

        self.assertEqual(response.data, results)

