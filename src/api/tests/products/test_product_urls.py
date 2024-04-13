import base64
from decimal import Decimal
import json
from pprint import pprint

from PIL import Image

from django.contrib.auth.models import Permission
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from accounts.models import UserGroup

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.create_product_models import create_new_product
from core.test_utils.create_product_variants import create_1d_variants
from core.test_utils.create_store_models import (
    create_new_category,
    create_new_tax,
)

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.initial_user_data import InitialUserDataMixin
from core.test_utils.log_reader import get_test_firebase_sender_log_content
from inventories.models import StockLevel
from mysettings.models import MySetting

from products.models import Modifier, Product, ProductBundle, ProductProductionMap
from stores.models import Category, Store, Tax


class TpProductAvailableDataViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create models
        self.create_categories()
        self.create_taxes()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_categories(self):

        # Create categories for top user 1
        self.category1 = create_new_category(self.top_profile1, 'Category1')
        self.category2 = create_new_category(self.top_profile1, 'Category2')

        # Create categories for top user 2
        self.category3 = create_new_category(self.top_profile2, 'Category3')

    def create_taxes(self):
        
        # Create taxes for top user 1
        self.tax1 = create_new_tax(self.top_profile1, self.store1, 'Standard1')
        self.tax2 = create_new_tax(self.top_profile1, self.store2, 'Standard2')

        # Create taxes for top user 2
        self.tax3 = create_new_tax(self.top_profile2, self.store3, 'Standard3')
    
    def login_user(self, email):

        # Login a top user
        token = Token.objects.get(user__email=email)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_returns_the_user_models_only(self):

        emails = [
            'john@gmail.com', # Owner
            'gucci@gmail.com' # Employe
        ]

        for email in emails:

            # Login user
            self.login_user(email)

            # Count Number of Queries #
            with self.assertNumQueries(7):
                response = self.client.get(
                    reverse('api:tp_product_available_data'))
                self.assertEqual(response.status_code, 200)

            result = {
                'taxes': [
                    {
                        'name': self.tax1.name, 
                        'reg_no': self.tax1.reg_no
                    },
                    {
                        'name': self.tax2.name, 
                        'reg_no': self.tax2.reg_no
                    }
                ], 
                'categories': [
                    {
                        'name': self.category1.name, 
                        'reg_no': self.category1.reg_no
                    },
                    {
                        'name': self.category2.name, 
                        'reg_no': self.category2.reg_no
                    }
                ], 
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

            self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_models(self):

        Modifier.objects.all().delete()
        Tax.objects.all().delete()
        Category.objects.all().delete()
        Store.objects.all().delete()

        response = self.client.get(
            reverse('api:tp_product_available_data'))
        self.assertEqual(response.status_code, 200)

        result = {
            'taxes': [], 
            'categories': [], 
            'stores': []
        }

        self.assertEqual(response.data, result)
    
    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_product_available_data'))
        self.assertEqual(response.status_code, 401)

class TpLeanProductStoreIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')

        # Create a category
        self.category = create_new_category(self.top_profile1, 'Hair')

        self.create_single_product()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_single_product(self):

        # Create a products
        # ------------------------------ Product 1
        product = Product.objects.create(
            profile=self.top_profile1,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123',
        )

        # Update stock units for store 1 and 2
        stock = StockLevel.objects.get(product=product, store=self.store1)
        stock.units = 5100
        stock.save()

        stock = StockLevel.objects.get(product=product, store=self.store2)
        stock.units = 6100
        stock.save()

        # ------------------------------ Product 1
        product2 = Product.objects.create(
            profile=self.top_profile1,
            name="Conditioner",
            price=2000,
            cost=800,
            sku='sku2',
            barcode='code123',
            sold_by_each=False
        )

        # Update stock units for store 1 and 2
        stock = StockLevel.objects.get(product=product2, store=self.store1)
        stock.units = 2100
        stock.save()

        stock = StockLevel.objects.get(product=product2, store=self.store2)
        stock.units = 3100
        stock.save()

    def create_a_bundle_master_product(self):

        # Create master product with 2 bundles
        shampoo = Product.objects.get(name='Shampoo')

        shampoo_bundle = ProductBundle.objects.create(
            product_bundle=shampoo,
            quantity=30
        )

        master_product = Product.objects.create(
            profile=self.top_profile1,
            name="Hair Bundle",
            price=35000,
            cost=30000,
            sku='sku1',
            barcode='code123'
        )
    
        master_product.bundles.add(shampoo_bundle)
    
    def test_if_view_returns_the_products_for_single_store_correctly(self):

        product1 = Product.objects.get(name="Shampoo")
        product2 = Product.objects.get(name="Conditioner")

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(
            reverse('api:tp_lean_product_store_index', args=(self.store1.reg_no, 0)))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'image_url': product2.get_image_url(),
                    'color_code': product2.color_code,
                    'name': product2.name,
                    'show_image': False,
                    'cost': str(product2.cost),
                    'sku': product2.sku,
                    'sold_by_each': product2.sold_by_each,
                    'tax_rate': str(product2.tax_rate),
                    'reg_no': product2.reg_no,
                    'stock_units': [{'units': '2100.00'}]
                },
                {
                    'image_url': product1.get_image_url(),
                    'color_code': product1.color_code,
                    'show_image': False,
                    'name': product1.name,
                    'cost': str(product1.cost),
                    'sku': product1.sku,
                    'sold_by_each': product1.sold_by_each,
                    'tax_rate': str(product1.tax_rate),
                    'reg_no': product1.reg_no,
                    'stock_units': [{'units': '5100.00'}]
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
            reverse('api:tp_lean_product_store_index', args=(self.store1.reg_no, 0)))
        self.assertEqual(response.status_code, 401)

    def test_if_view_does_not_return_soft_deleted_products(self):

        product1 = Product.objects.get(name="Shampoo")
        product2 = Product.objects.get(name="Conditioner")

        product1.soft_delete()
        product2.soft_delete()

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(
            reverse('api:tp_lean_product_store_index', args=(self.store1.reg_no, 0)))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0,
            'next': None,
            'previous': None,
            'results': []
        }

        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        product1 = Product.objects.get(name="Shampoo")

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = '?search=shampoo'
        response = self.client.get(
            reverse('api:tp_lean_product_store_index', 
            args=(self.store1.reg_no, 0)) + param
        )

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'image_url': product1.get_image_url(),
                    'color_code': product1.color_code,
                    'show_image': False,
                    'name': product1.name,
                    'cost': str(product1.cost),
                    'sku': product1.sku,
                    'sold_by_each': product1.sold_by_each,
                    'tax_rate': str(product1.tax_rate),
                    'reg_no': product1.reg_no,
                    'stock_units': [{'units': '5100.00'}]
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)
    
    def test_if_view_returns_the_products_for_multiple_store_correctly(self):

        product1 = Product.objects.get(name="Shampoo")
        product2 = Product.objects.get(name="Conditioner")

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(
            reverse('api:tp_lean_product_store_index', args=(self.store1.reg_no, self.store2.reg_no)))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'image_url': product2.get_image_url(),
                    'color_code': product2.color_code,
                    'name': product2.name,
                    'show_image': False,
                    'cost': str(product2.cost),
                    'sku': product2.sku,
                    'sold_by_each': product2.sold_by_each,
                    'tax_rate': str(product2.tax_rate),
                    'reg_no': product2.reg_no,
                    'stock_units': [
                        {'units': '2100.00'},
                        {'units': '3100.00'},
                    ]
                },
                {
                    'image_url': product1.get_image_url(),
                    'color_code': product1.color_code,
                    'show_image': False,
                    'name': product1.name,
                    'cost': str(product1.cost),
                    'sku': product1.sku,
                    'sold_by_each': product1.sold_by_each,
                    'tax_rate': str(product1.tax_rate),
                    'reg_no': product1.reg_no,
                    'stock_units': [
                        {'units': '5100.00'},
                        {'units': '6100.00'},
                    ]
                }
            ]
        }

        self.assertEqual(response.data, result)
    
    def test_if_view_does_not_show_variant_parents(self):

        product = Product.objects.get(name="Shampoo")
        product2 = Product.objects.get(name="Conditioner")

        # Create 3 variants for master product
        create_1d_variants(
            master_product=product,
            profile=self.top_profile1,
            store1=self.store1,
            store2=self.store2
        )

        variants = Product.objects.filter(is_variant_child=True)

        for v in variants:
            v.save()

        variants = Product.objects.filter(
            productvariant__product=product).order_by('id')

        # Count Number of Queries #
        # with self.assertNumQueries(16):
        response = self.client.get(
            reverse('api:tp_lean_product_store_index', args=(self.store1.reg_no, 0)))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 4,
            'next': None,
            'previous': None,
            'results': [
                {
                    'image_url': product2.get_image_url(),
                    'color_code': product2.color_code,
                    'show_image': False,
                    'name': 'Conditioner',
                    'cost': '800.00',
                    'sku': 'sku2',
                    'sold_by_each': False,
                    'tax_rate': str(product2.tax_rate),
                    'reg_no': product2.reg_no,
                    'stock_units': [{'units': '2100.00'}]
                },
                {
                    'image_url': variants[2].get_image_url(),
                    'color_code': variants[2].color_code,
                    'show_image': False,
                    'name': 'Large',
                    'cost': '800.00',
                    'sku': '',
                    'sold_by_each': True,
                    'tax_rate': str(variants[2].tax_rate),
                    'reg_no': variants[2].reg_no,
                    'stock_units': [{'units': '130.00'}]
                },
                {
                    'image_url': variants[1].get_image_url(),
                    'color_code': variants[1].color_code,
                    'show_image': False,
                    'name': 'Medium',
                    'cost': '800.00',
                    'sku': '',
                    'sold_by_each': True,
                    'tax_rate': str(variants[1].tax_rate),
                    'reg_no': variants[1].reg_no,
                    'stock_units': [{'units': '120.00'}]
                },
                {
                    'image_url': variants[0].get_image_url(),
                    'color_code': variants[0].color_code,
                    'show_image': False,
                    'name': 'Small',
                    'cost': '800.00',
                    'sku': '',
                    'sold_by_each': True,
                    'tax_rate': str(variants[0].tax_rate),
                    'reg_no': variants[0].reg_no,
                    'stock_units': [{'units': '100.00'}]
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_if_view_wont_show_products_from_other_stores(self):

        product1 = Product.objects.get(name="Shampoo")
        product2 = Product.objects.get(name="Conditioner")

        # Remvove store1 from products
        product1.stores.remove(self.store1)
        product2.stores.remove(self.store1)

        response = self.client.get(
            reverse('api:tp_lean_product_store_index', args=(self.store1.reg_no, 0)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_if_view_can_handle_store1_wrong_reg_no(self):

        response = self.client.get(
            reverse('api:tp_lean_product_store_index', args=(4646464, 0)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)
    
    def test_if_view_can_handle_wrong_store2_reg_no(self):

        product1 = Product.objects.get(name="Shampoo")
        product2 = Product.objects.get(name="Conditioner")

        response = self.client.get(
            reverse('api:tp_lean_product_store_index', args=(self.store1.reg_no, 45)))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'image_url': product2.get_image_url(),
                    'color_code': product2.color_code,
                    'name': product2.name,
                    'show_image': False,
                    'cost': str(product2.cost),
                    'sku': product2.sku,
                    'sold_by_each': product2.sold_by_each,
                    'tax_rate': str(product2.tax_rate),
                    'reg_no': product2.reg_no,
                    'stock_units': [{'units': '2100.00'}, {'units': '0'}]
                },
                {
                    'image_url': product1.get_image_url(),
                    'color_code': product1.color_code,
                    'show_image': False,
                    'name': product1.name,
                    'cost': str(product1.cost),
                    'sku': product1.sku,
                    'sold_by_each': product1.sold_by_each,
                    'tax_rate': str(product1.tax_rate),
                    'reg_no': product1.reg_no,
                    'stock_units': [{'units': '5100.00'}, {'units': '0'}]
                }
            ]
        }

        self.assertEqual(response.data, result)
    
    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all products
        Product.objects.all().delete()

        pagination_page_size = settings.PRODUCT_LEAN_WEB_PAGINATION_PAGE_SIZE

        model_num_to_be_created = pagination_page_size+1

        product_names = []
        for i in range(model_num_to_be_created):
            product_names.append(f'New Product{i}')

        names_length = len(product_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)

        # Create and confirm products
        for i in range(names_length):
            create_new_product(
                profile=self.top_profile1,
                store=self.store1,
                tax=self.tax,
                category=self.category,
                name=product_names[i],
            )

        self.assertEqual(
            Product.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

        products = Product.objects.filter(
            profile=self.top_profile1).order_by('-name')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        # with self.assertNumQueries(3):
        response = self.client.get(
            reverse('api:tp_lean_product_store_index', args=(self.store1.reg_no, 0)))
        self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], f'http://testserver/api/products/lean/store/{self.store1.reg_no}/0/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(
            len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all products are listed except the first one since it's in the next paginated page #
        i = 0
        for product in products[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], product.name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], product.reg_no)

            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse(
            'api:tp_lean_product_store_index', args=(self.store1.reg_no, 0)) + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': f'http://testserver/api/products/lean/store/{self.store1.reg_no}/0/',
            'results': [
                {
                    'image_url': products[0].get_image_url(),
                    'color_code': products[0].color_code,
                    'show_image': False,
                    'name': products[0].name,
                    'cost': str(products[0].cost),
                    'sku': 'sku1',
                    'sold_by_each': True,
                    'tax_rate': str(products[0].tax_rate),
                    'reg_no': products[0].reg_no,
                    'stock_units': [{'units': '0.00'}]
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_products(self):

        # First delete all products
        Product.objects.all().delete()

        response = self.client.get(
            reverse('api:tp_lean_product_store_index', args=(self.store1.reg_no, 0)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_its_owner(self):

        # Login an employee user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:tp_lean_product_store_index', args=(self.store1.reg_no, 0)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:tp_lean_product_store_index', args=(self.store1.reg_no, 0)))
        self.assertEqual(response.status_code, 401)

class TpLeanProductIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')

        # Create categories
        self.category1 = create_new_category(self.top_profile1, 'Hair')
        self.category2 = create_new_category(self.top_profile1, 'Body')

        self.create_single_product()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    
    def login_user(self, email):

        # Login a top user
        token = Token.objects.get(user__email=email)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_products_for_filter_test(self):

        # ------------------------------ Product 1
        product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category1,
            name="Band",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        ) 

        # Update stock units
        stock = StockLevel.objects.get(product=product1, store=self.store1)
        stock.units = 500
        stock.save()

        stock = StockLevel.objects.get(product=product1, store=self.store2)
        stock.units = 800
        stock.save()

        # ------------------------------ Product 2
        product2 = Product.objects.create(
            profile=self.top_profile1,
            name="Comb",
            price=3500,
            cost=2000,
            sku='sku1',
            barcode='code123'
        ) 

        # Update stock units
        stock = StockLevel.objects.get(product=product2, store=self.store1)
        stock.units = 300
        stock.save()

        # Update stock units
        stock = StockLevel.objects.get(product=product2, store=self.store2)
        stock.units = 450
        stock.save()

        # ------------------------------ Product 3
        product3 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category2,
            name="Gel",
            price=4500,
            cost=3000,
            sku='sku1',
            barcode='code123'
        ) 

        # Update stock units
        stock = StockLevel.objects.get(product=product3, store=self.store1)
        stock.units = 700
        stock.save()

        stock = StockLevel.objects.get(product=product3, store=self.store2)
        stock.units = 710
        stock.save()
    
    def create_single_product(self):

        # Create a products
        # ------------------------------ Product 1
        product = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category1,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        ) 

        # Update stock units
        stock = StockLevel.objects.get(product=product, store=self.store1)
        stock.units = 5100
        stock.save()

    def create_a_bundle_master_product(self):

        # Create master product with 2 bundles
        shampoo = Product.objects.get(name='Shampoo')

        shampoo_bundle = ProductBundle.objects.create(
            product_bundle=shampoo,
            quantity=30
        )

        master_product = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category1,
            name="Hair Bundle",
            price=35000,
            cost=30000,
            sku='sku1',
            barcode='code123'
        )

        master_product.bundles.add(shampoo_bundle)
    
    def test_if_view_returns_the_products_correctly(self):

        emails = [
            'john@gmail.com', # Owner
            'gucci@gmail.com' # Employe
        ]

        for email in emails:

            # Login user
            self.login_user(email)
        
            # We add another stock level for product by adding a new store
            product = Product.objects.get(name="Shampoo")

            # Confirm we have 2 stock levels
            self.assertEqual(StockLevel.objects.filter(product=product).count(), 2)

            # Count Number of Queries #
            #with self.assertNumQueries(12):
            response = self.client.get(reverse('api:tp_lean_product_index'))
            self.assertEqual(response.status_code, 200)

            result = {
                'count': 1, 
                'next': None, 
                'previous': None, 
                'results': [
                    {
                        'image_url': product.get_image_url(),
                        'color_code': product.color_code,
                        'show_image': product.show_image,
                        'name': product.name,
                        'cost': str(product.cost),
                        'sku': product.sku,
                        'reg_no': product.reg_no  
                    }
                ], 
            
            }

            self.assertEqual(response.data, result)

    def test_if_view_does_not_return_soft_deleted_products(self):

        product1 = Product.objects.get(name="Shampoo")

        product1.soft_delete()

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(reverse('api:tp_lean_product_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0,
            'next': None,
            'previous': None,
            'results': []
        }

        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        product = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category1,
            name='Product2',
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        ) 

        # Confirm product count
        self.assertEqual(Product.objects.all().count(), 2)

        product = Product.objects.get(name="Product2")

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = '?search=Product2'
        response = self.client.get(reverse('api:tp_lean_product_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'image_url': product.get_image_url(),
                    'color_code': product.color_code,
                    'show_image': product.show_image,
                    'name': product.name,
                    'cost': str(product.cost),
                    'sku': product.sku,
                    'reg_no': product.reg_no  
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_if_view_does_not_show_variant_parents(self):

        product = Product.objects.get(name="Shampoo")

        # Create 3 variants for master product
        create_1d_variants(
            master_product=product,
            profile=self.top_profile1,
            store1=self.store1,
            store2=self.store2
        )

        variants = Product.objects.filter(is_variant_child=True)

        for v in variants:
            v.save()

        variants = Product.objects.filter(
            productvariant__product=product).order_by('id')

        response = self.client.get(reverse('api:tp_lean_product_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 3, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'image_url': variants[2].get_image_url(),
                    'color_code': variants[2].color_code,
                    'show_image': variants[2].show_image,
                    'name': variants[2].name,
                    'cost': str(variants[2].cost),
                    'sku': variants[2].sku,
                    'reg_no': variants[2].reg_no
                },
                {
                    'image_url': variants[1].get_image_url(),
                    'color_code': variants[1].color_code,
                    'show_image': variants[1].show_image,
                    'name': variants[1].name,
                    'cost': str(variants[1].cost),
                    'sku': variants[1].sku,
                    'reg_no': variants[1].reg_no
                }, 
                {
                    'image_url': variants[0].get_image_url(),
                    'color_code': variants[0].color_code,
                    'show_image': variants[0].show_image,
                    'name': variants[0].name,
                    'cost': str(variants[0].cost),
                    'sku': variants[0].sku,
                    'reg_no': variants[0].reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all products
        Product.objects.all().delete()

        pagination_page_size = settings.PRODUCT_LEAN_WEB_PAGINATION_PAGE_SIZE

        model_num_to_be_created = pagination_page_size+1

        product_names = []
        for i in range(model_num_to_be_created):
            product_names.append(f'New Product{i}')

        names_length = len(product_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm products
        for i in range(names_length):
            create_new_product(
                profile=self.top_profile1,
                store=self.store1,
                tax=self.tax,
                category=self.category1, 
                name=product_names[i]
            )

        self.assertEqual(
            Product.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

    
        products = Product.objects.filter(profile=self.top_profile1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        #with self.assertNumQueries(3):
        response = self.client.get(reverse('api:tp_lean_product_index'))
        self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/products/lean/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all products are listed except the first one since it's in the next paginated page #
        i = 0
        for product in products[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], product.name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], product.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:tp_lean_product_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': 'http://testserver/api/products/lean/', 
            'results': [
                {

                    'image_url': products[0].get_image_url(),
                    'color_code': products[0].color_code,
                    'show_image': products[0].show_image,
                    'name': products[0].name,
                    'cost': str(products[0].cost),
                    'sku': products[0].sku,
                    'reg_no': products[0].reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_products(self):

        # First delete all products
        Product.objects.all().delete()

        response = self.client.get(reverse('api:tp_lean_product_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': []
        }

        self.assertEqual(response.data, result)

    def test_view_cant_be_created_by_a_bad_owner_and_employee(self):

        emails = [
            'jack@gmail.com',  # Bad owner
            'cristiano@gmail.com' # Bad employee
        ]

        for email in emails:
            # Login user
            self.login_user(email)

            response = self.client.get(reverse('api:tp_lean_product_index'))
            self.assertEqual(response.status_code, 200)

            result = {
                'count': 0, 
                'next': None, 
                'previous': None, 
                'results': [],
            }

            self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_lean_product_index'))
        self.assertEqual(response.status_code, 401)

class TpProductIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')

        # Create categories
        self.category1 = create_new_category(self.top_profile1, 'Hair')
        self.category2 = create_new_category(self.top_profile1, 'Body')

        self.create_single_product()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_products_for_filter_test(self):

        # ------------------------------ Product 1
        product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category1,
            name="Band",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        ) 

        # Update stock units
        stock = StockLevel.objects.get(product=product1, store=self.store1)
        stock.units = 500
        stock.save()

        stock = StockLevel.objects.get(product=product1, store=self.store2)
        stock.units = 800
        stock.save()

        # ------------------------------ Product 2
        product2 = Product.objects.create(
            profile=self.top_profile1,
            name="Comb",
            price=3500,
            cost=2000,
            sku='sku1',
            barcode='code123'
        ) 

        # Update stock units
        stock = StockLevel.objects.get(product=product2, store=self.store1)
        stock.units = 300
        stock.save()

        # Update stock units
        stock = StockLevel.objects.get(product=product2, store=self.store2)
        stock.units = 450
        stock.save()

        # ------------------------------ Product 3
        product3 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category2,
            name="Gel",
            price=4500,
            cost=3000,
            sku='sku1',
            barcode='code123'
        ) 

        # Update stock units
        stock = StockLevel.objects.get(product=product3, store=self.store1)
        stock.units = 700
        stock.save()

        stock = StockLevel.objects.get(product=product3, store=self.store2)
        stock.units = 710
        stock.save()
    
    def create_single_product(self):

        # Create a products
        # ------------------------------ Product 1
        product = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category1,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        ) 

        # Update stock units
        stock = StockLevel.objects.get(product=product, store=self.store1)
        stock.units = 5100
        stock.save()

    def create_a_bundle_master_product(self):

        # Create master product with 2 bundles
        shampoo = Product.objects.get(name='Shampoo')

        shampoo_bundle = ProductBundle.objects.create(
            product_bundle=shampoo,
            quantity=30
        )

        master_product = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category1,
            name="Hair Bundle",
            price=35000,
            cost=30000,
            sku='sku1',
            barcode='code123'
        )
   
        master_product.bundles.add(shampoo_bundle)
    
    def login_user(self, email):

        # Login a top user
        token = Token.objects.get(user__email=email)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    
    def test_if_view_returns_the_products_correctly(self):

        # Login user
        self.login_user('john@gmail.com')
    
        # We add another stock level for product by adding a new store
        product = Product.objects.get(name="Shampoo")
        
        # Confirm we have 2 stock levels
        self.assertEqual(StockLevel.objects.filter(product=product).count(), 2)

        # Count Number of Queries #
        #with self.assertNumQueries(12):
        response = self.client.get(reverse('api:tp_product_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'image_url': f'/media/images/products/{product.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': 'Shampoo', 
                    'price': '2500.00', 
                    'average_price': str(product.average_price),
                    'cost': '1000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product.reg_no, 
                    'valuation_info': {
                        'stock_units': '5100', 
                        'margin': '60'
                    }, 
                    'category_data': {
                        'name': 'Hair', 
                        'reg_no': self.category1.reg_no
                    }, 
                    'index_variants_data': []
                }
            ], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)

        

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:tp_product_index'))
        self.assertEqual(response.status_code, 401)

    def test_if_view_does_not_return_soft_deleted_products(self):

        product1 = Product.objects.get(name="Shampoo")

        product1.soft_delete()

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(reverse('api:tp_product_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }
        self.assertEqual(response.data, result)

    # def test_if_view_returns_the_products_correctly1(self):

    #     # Login user
    #     self.login_user('gucci@gmail.com')
    
    #     # We add another stock level for product by adding a new store
    #     product = Product.objects.get(name="Shampoo")
        
    #     # Confirm we have 2 stock levels
    #     self.assertEqual(StockLevel.objects.filter(product=product).count(), 2)

    #     # Count Number of Queries #
    #     #with self.assertNumQueries(12):
    #     response = self.client.get(reverse('api:tp_product_index'))
    #     self.assertEqual(response.status_code, 200)

    #     result = {
    #         'count': 1, 
    #         'next': None, 
    #         'previous': None, 
    #         'results': [
    #             {
    #                 'image_url': f'/media/images/products/{product.reg_no}_.jpg', 
    #                 'color_code': '#474A49', 
    #                 'name': 'Shampoo', 
    #                 'price': '2500.00', 
    #                 'average_price': str(product.average_price),
    #                 'cost': '1000.00', 
    #                 'is_bundle': False, 
    #                 'show_image': False, 
    #                 'reg_no': product.reg_no, 
    #                 'valuation_info': {
    #                     'stock_units': '5100', 
    #                     'margin': '60'
    #                 }, 
    #                 'category_data': {
    #                     'name': 'Hair', 
    #                     'reg_no': self.category1.reg_no
    #                 }, 
    #                 'index_variants_data': []
    #             }
    #         ], 
    #         'categories': [
    #             {
    #                 'name': self.category2.name, 
    #                 'reg_no': self.category2.reg_no
    #             },
    #             {
    #                 'name': self.category1.name, 
    #                 'reg_no': self.category1.reg_no
    #             }
    #         ],
    #         'stores': [
    #             {
    #                 'name': self.store1.name, 
    #                 'is_shop': True, 
    #                 'is_truck': False, 
    #                 'is_warehouse': False, 
    #                 'reg_no': self.store1.reg_no,
    #                 'is_deleted': self.store1.is_deleted,
    #                 'deleted_date': self.store1.deleted_date
    #             }, 
    #         ]
    #     }

    #     self.assertEqual(response.data, result)

    def test_view_when_proudct_does_not_have_category(self):

        # Remove category
        product = Product.objects.get(name="Shampoo")
        product.category = None
        product.save()

        response = self.client.get(
            reverse('api:tp_product_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'image_url': f'/media/images/products/{product.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': 'Shampoo', 
                    'price': '2500.00', 
                    'average_price': str(product.average_price),
                    'cost': '1000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product.reg_no, 
                    'valuation_info': {
                        'stock_units': '5100', 
                        'margin': '60'
                    }, 
                    'category_data': {}, 
                    'index_variants_data': []
                }
            ],
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_when_there_are_bundle_products(self):

        self.create_a_bundle_master_product()

        product1 = Product.objects.get(name="Shampoo")
        product2 = Product.objects.get(name="Hair Bundle")

        response = self.client.get(reverse('api:tp_product_index'))

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'image_url': f'/media/images/products/{product2.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': 'Hair Bundle', 
                    'price': '35000.00', 
                    'average_price': str(product2.average_price),
                    'cost': '30000.00', 
                    'is_bundle': True, 
                    'show_image': False, 
                    'reg_no': product2.reg_no, 
                    'valuation_info': {
                        'stock_units': '0', 
                        'margin': '0'
                    }, 
                    'category_data': {
                        'name': 'Hair', 
                        'reg_no': self.category1.reg_no
                    }, 
                    'index_variants_data': []
                }, 
                {
                    'image_url': f'/media/images/products/{product1.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': 'Shampoo', 
                    'price': '2500.00', 
                    'average_price': str(product1.average_price),
                    'cost': '1000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product1.reg_no, 
                    'valuation_info': {
                        'stock_units': '5100', 
                        'margin': '60'
                    }, 
                    'category_data': {
                        'name': 'Hair', 
                        'reg_no': self.category1.reg_no
                    }, 
                    'index_variants_data': []
                }
            ], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_when_there_is_a_product_with_variants(self):

        product = Product.objects.get(name="Shampoo")

        # Create 3 variants for master product
        create_1d_variants(
            master_product=product,
            profile=self.top_profile1,
            store1=self.store1,
            store2=self.store2
        )

        # Count Number of Queries #
        #with self.assertNumQueries(16):
        response = self.client.get(reverse('api:tp_product_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'image_url': f'/media/images/products/{product.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': 'Shampoo', 
                    'price': '2500.00', 
                    'average_price': str(product.average_price),
                    'cost': '1000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product.reg_no, 
                    'valuation_info': {
                        'stock_units': '5100', 
                        'margin': '60'
                    }, 
                    'category_data': {
                        'name': 'Hair', 
                        'reg_no': self.category1.reg_no
                    }, 
                    'index_variants_data': [
                        {
                            'name': 'Small', 
                            'valuation_info': 
                            {
                                'stock_units': '300', 
                                'margin': '46.67'
                            }
                        }, 
                        {
                            'name': 'Medium', 
                            'valuation_info': {
                                'stock_units': '340', 
                                'margin': '46.67'
                            }
                        }, 
                        {
                            'name': 'Large', 
                            'valuation_info': {
                                'stock_units': '360', 
                                'margin': '46.67'
                            }
                        }
                    ]
                }
            ], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all products
        Product.objects.all().delete()

        pagination_page_size = settings.PRODUCT_WEB_PAGINATION_PAGE_SIZE

        model_num_to_be_created = pagination_page_size+1

        product_names = []
        for i in range(model_num_to_be_created):
            product_names.append(f'New Product{i}')

        names_length = len(product_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm products
        for i in range(names_length):
            create_new_product(
                profile=self.top_profile1,
                store=self.store1,
                tax=self.tax,
                category=self.category1, 
                name=product_names[i]
            )

        self.assertEqual(
            Product.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

    
        products = Product.objects.filter(profile=self.top_profile1).order_by('-name')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        #with self.assertNumQueries(3):
        response = self.client.get(reverse('api:tp_product_index'))
        self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/products/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all products are listed except the first one since it's in the next paginated page #
        i = 0
        for product in products[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], product.name)
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], product.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:tp_product_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': 'http://testserver/api/products/', 
            'results': [
                {
                    'image_url': f'/media/images/products/{products[0].reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': products[0].name, 
                    'price': '2500.00', 
                    'average_price': str(products[0].average_price),
                    'cost': '1000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': products[0].reg_no, 
                    'valuation_info': {
                        'stock_units': '0', 
                        'margin': '0'
                    }, 
                    'category_data': {
                        'name': 'Hair', 
                        'reg_no': self.category1.reg_no
                    },
                    'index_variants_data': []
                }
            ], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        # First delete all products
        Product.objects.all().delete()

        self.create_products_for_filter_test()
        self.assertEqual(Product.objects.all().count(), 3)

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = '?search=Gel'
        response = self.client.get(reverse('api:tp_product_index') + param)
        self.assertEqual(response.status_code, 200)

        product = Product.objects.get(name='Gel')

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'image_url': f'/media/images/products/{product.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': product.name, 
                    'price': '4500.00', 
                    'average_price': str(product.average_price),
                    'cost': '3000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product.reg_no, 
                    'valuation_info': {
                        'stock_units': '1410', 
                        'margin': '33.33'
                    }, 
                    'category_data': {
                        'name': self.category2.name, 
                        'reg_no': self.category2.reg_no
                    }, 
                    'index_variants_data': []
                }
            ], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_single_store1(self):

        # First delete all products
        Product.objects.all().delete()

        self.create_products_for_filter_test()

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?stores__reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:tp_product_index') + param)

        self.assertEqual(response.status_code, 200)

        product1 = Product.objects.get(name='Band')
        product2 = Product.objects.get(name='Comb')
        product3 = Product.objects.get(name='Gel')

        result = {
            'count': 3, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'image_url': f'/media/images/products/{product1.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': product1.name, 
                    'price': '2500.00', 
                    'average_price': str(product1.average_price),
                    'cost': '1000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product1.reg_no, 
                    'valuation_info': {
                        'stock_units': '500', 
                        'margin': '60'
                    }, 
                    'category_data': {
                        'name': self.category1.name, 
                        'reg_no': self.category1.reg_no
                    },  
                    'index_variants_data': []
                },
                {
                    'image_url': f'/media/images/products/{product2.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': product2.name, 
                    'price': '3500.00', 
                    'average_price': str(product2.average_price),
                    'cost': '2000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product2.reg_no, 
                    'valuation_info': {
                        'stock_units': '300', 
                        'margin': '42.86'
                    }, 
                    'category_data': {}, 
                    'index_variants_data': []
                },
                {
                    'image_url': f'/media/images/products/{product3.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': product3.name, 
                    'price': '4500.00', 
                    'average_price': str(product3.average_price),
                    'cost': '3000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product3.reg_no, 
                    'valuation_info': {
                        'stock_units': '700', 
                        'margin': '33.33'
                    }, 
                    'category_data': {
                        'name': self.category2.name, 
                        'reg_no': self.category2.reg_no
                    }, 
                    'index_variants_data': []
                },
            ], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_single_store2(self):

        # First delete all products
        Product.objects.all().delete()

        self.create_products_for_filter_test()

        product1 = Product.objects.get(name='Band')
        product2 = Product.objects.get(name='Comb')
        product3 = Product.objects.get(name='Gel')

        # Remove store2 from product 3
        product3.stores.remove(self.store2)

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?stores__reg_no={self.store2.reg_no}'
        response = self.client.get(reverse('api:tp_product_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'image_url': f'/media/images/products/{product1.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': product1.name, 
                    'price': '2500.00', 
                    'average_price': str(product1.average_price),
                    'cost': '1000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product1.reg_no, 
                    'valuation_info': {
                        'stock_units': '800', 
                        'margin': '60'
                    }, 
                    'category_data': {
                        'name': self.category1.name, 
                        'reg_no': self.category1.reg_no
                    },  
                    'index_variants_data': []
                },
                {
                    'image_url': f'/media/images/products/{product2.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': product2.name, 
                    'price': '3500.00', 
                    'average_price': str(product2.average_price),
                    'cost': '2000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product2.reg_no, 
                    'valuation_info': {
                        'stock_units': '450', 
                        'margin': '42.86'
                    }, 
                    'category_data': {}, 
                    'index_variants_data': []
                }
            ], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_all_stores(self):

        # First delete all products
        Product.objects.all().delete()

        self.create_products_for_filter_test()

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        response = self.client.get(reverse('api:tp_product_index'))

        self.assertEqual(response.status_code, 200)

        product1 = Product.objects.get(name='Band')
        product2 = Product.objects.get(name='Comb')
        product3 = Product.objects.get(name='Gel')

        result = {
            'count': 3, 
            'next': None, 
            'previous': None, 
            'results': [ 
                {
                    'image_url': f'/media/images/products/{product1.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': product1.name, 
                    'price': '2500.00', 
                    'average_price': str(product1.average_price),
                    'cost': '1000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product1.reg_no, 
                    'valuation_info': {
                        'stock_units': '1300', 
                        'margin': '60'
                    }, 
                    'category_data': {
                        'name': self.category1.name, 
                        'reg_no': self.category1.reg_no
                    },  
                    'index_variants_data': []
                },
                {
                    'image_url': f'/media/images/products/{product2.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': product2.name, 
                    'price': '3500.00', 
                    'average_price': str(product2.average_price),
                    'cost': '2000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product2.reg_no, 
                    'valuation_info': {
                        'stock_units': '750', 
                        'margin': '42.86'
                    }, 
                    'category_data': {}, 
                    'index_variants_data': []
                },
                {
                    'image_url': f'/media/images/products/{product3.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': product3.name, 
                    'price': '4500.00', 
                    'average_price': str(product3.average_price),
                    'cost': '3000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product3.reg_no, 
                    'valuation_info': {
                        'stock_units': '1410', 
                        'margin': '33.33'
                    }, 
                    'category_data': {
                        'name': self.category2.name, 
                        'reg_no': self.category2.reg_no
                    }, 
                    'index_variants_data': []
                }
            ], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }, 
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_single_category(self):

        # First delete all products
        Product.objects.all().delete()

        self.create_products_for_filter_test()

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?category__reg_no={self.category1.reg_no}'
        response = self.client.get(reverse('api:tp_product_index') + param)

        self.assertEqual(response.status_code, 200)

        product1 = Product.objects.get(name='Band')

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'image_url': f'/media/images/products/{product1.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': product1.name, 
                    'price': '2500.00', 
                    'average_price': str(product1.average_price),
                    'cost': '1000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product1.reg_no, 
                    'valuation_info': {
                        'stock_units': '1300', 
                        'margin': '60'
                    }, 
                    'category_data': {
                        'name': self.category1.name, 
                        'reg_no': self.category1.reg_no
                    },  
                    'index_variants_data': []
                }
            ], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }, 
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)
    
    def test_view_can_filter_low_stock(self):

        # First delete all products
        Product.objects.all().delete()

        self.create_products_for_filter_test()

        # Update product 2 to be low in stock
        product2 = Product.objects.get(name='Comb')
        product2.save()

        # We call save to update stock level's status
        stock = StockLevel.objects.get(product=product2, store=self.store1)
        stock.minimum_stock_level = 350
        stock.save()

        param = f'?stocklevel__status={StockLevel.STOCK_LEVEL_LOW_STOCK}'
        response = self.client.get(reverse('api:tp_product_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'image_url': f'/media/images/products/{product2.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': product2.name, 
                    'price': '3500.00', 
                    'average_price': str(product2.average_price),
                    'cost': '2000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product2.reg_no, 
                    'valuation_info': {
                        'stock_units': '750', 
                        'margin': '42.86'
                    }, 
                    'category_data': {},  
                    'index_variants_data': []
                }
            ], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }, 
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_bundle_products(self):

        self.create_a_bundle_master_product()

        product1 = Product.objects.get(name="Shampoo")
        product2 = Product.objects.get(name="Hair Bundle")

        ###### Filter is bundle is true
        param = '?is_bundle=true'
        response = self.client.get(reverse('api:tp_product_index') + param)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'image_url': f'/media/images/products/{product2.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': 'Hair Bundle', 
                    'price': '35000.00', 
                    'average_price': str(product2.average_price),
                    'cost': '30000.00', 
                    'is_bundle': True, 
                    'show_image': False, 
                    'reg_no': product2.reg_no, 
                    'valuation_info': {
                        'stock_units': '0', 
                        'margin': '0'
                    }, 
                    'category_data': {
                        'name': 'Hair', 
                        'reg_no': self.category1.reg_no
                    }, 
                    'index_variants_data': []
                }
            ], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }, 
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)


        ###### Filter is bundle is false
        param = '?is_bundle=false'
        response = self.client.get(reverse('api:tp_product_index') + param)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'image_url': f'/media/images/products/{product1.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': 'Shampoo', 
                    'price': '2500.00', 
                    'average_price': str(product1.average_price),
                    'cost': '1000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product1.reg_no, 
                    'valuation_info': {
                        'stock_units': '5100', 
                        'margin': '60'
                    }, 
                    'category_data': {
                        'name': 'Hair', 
                        'reg_no': self.category1.reg_no
                    }, 
                    'index_variants_data': []
                }
            ], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }, 
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_out_of_stock(self):

        # First delete all products
        Product.objects.all().delete()

        self.create_products_for_filter_test()

        # Update product 3 to be out of stock
        product3 = Product.objects.get(name='Gel')
        product3.minimum_stock_level = 100
        product3.save()

        # We call save to update stock level's status
        stock = StockLevel.objects.get(product=product3, store=self.store1)
        stock.units = 0
        stock.save()

        param = f'?stocklevel__status={StockLevel.STOCK_LEVEL_OUT_OF_STOCK}'
        response = self.client.get(reverse('api:tp_product_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'image_url': f'/media/images/products/{product3.reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': product3.name, 
                    'price': '4500.00', 
                    'average_price': str(product3.average_price),
                    'cost': '3000.00', 
                    'is_bundle': False, 
                    'show_image': False, 
                    'reg_no': product3.reg_no, 
                    'valuation_info': {
                        'stock_units': '710', 
                        'margin': '33.33'
                    }, 
                    'category_data': {
                        'name': self.category2.name, 
                        'reg_no': self.category2.reg_no
                    }, 
                    'index_variants_data': []
                }
            ], 
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }, 
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)


    def test_view_returns_empty_when_there_are_no_products(self):

        # First delete all products
        Product.objects.all().delete()

        response = self.client.get(reverse('api:tp_product_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }, 
            ],
            'stores': [
                {
                    'name': self.store2.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'deleted_date': self.store2.deleted_date
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'deleted_date': self.store1.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_only_be_viewed_by_owner(self):

        # Login an top user2
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_product_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'categories': [],
            'stores': [
                {
                    'name': self.store3.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False,
                    'reg_no': self.store3.reg_no,
                    'is_deleted': self.store3.is_deleted,
                    'deleted_date': self.store3.deleted_date
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_product_index'))
        self.assertEqual(response.status_code, 401)


class TpProductIndexViewForCreatingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')

        # Create a category
        self.category = create_new_category(self.top_profile1, 'Hair')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Test image resources
        self.test_image_name = 'pil_red.png'
        self.full_path=settings.MEDIA_ROOT + self.test_image_name

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """

        payload = {
            'color_code': '#474A40',
            'name': 'Shampoo', 
            'cost': 2500,
            'price': 2500,
            'sku': 'sku1',
            'barcode': 'code123',
            'sold_by_each': True,
            'show_image': True,
            'tax_reg_no': self.tax.reg_no,
            'category_reg_no': self.category.reg_no,
            'bundles_info': [],
            'stores_info': [
                {
                    'is_sellable': True, 
                    'price': 1800,
                    'reg_no': self.store1.reg_no,

                },
                {
                    'is_sellable': True, 
                    'price': 1200,
                    'reg_no': self.store2.reg_no,
                } 
            ]
        }

        return payload

    def create_2_normal_products(self):

        product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Comb",
            price=750,
            cost=120,
            sku='sku1',
            barcode='code123',
        )

        product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Clip",
            price=2800,
            cost=1200,
            barcode='code123'
        )
        return product1, product2
    
    def test_if_view_can_create_a_product(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(reverse('api:tp_product_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm product models creation
        self.assertEqual(Product.objects.all().count(), 1)

        p = Product.objects.get(name='Shampoo')

        # Check model values
        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(p.profile, self.top_profile1)
        self.assertEqual(p.tax, self.tax)
        self.assertEqual(p.category, self.category)
        self.assertEqual(p.bundles.all().count(), 0)
        self.assertEqual(p.image.url, f'/media/images/products/{p.reg_no}_.jpg')
        self.assertEqual(p.color_code, payload['color_code'])
        self.assertEqual(p.name, payload['name'])
        self.assertEqual(p.cost, payload['cost'])
        self.assertEqual(p.price, payload['price'])
        self.assertEqual(p.sku, payload['sku'])
        self.assertEqual(p.barcode, payload['barcode'])
        self.assertEqual(p.sold_by_each, payload['sold_by_each'])
        self.assertEqual(p.is_bundle, False)
        self.assertEqual(p.variant_count, 0)
        self.assertEqual(p.is_variant_child, False)
        self.assertEqual(p.show_product, True)
        self.assertEqual(p.show_image, payload['show_image'])
        self.assertTrue(p.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual((p.created_date).strftime("%B, %d, %Y"), today)

        # Confirm stock levels were created and updated
        stock_levels = StockLevel.objects.filter(product=p).order_by('id')

        # Stock level 1
        self.assertEqual(stock_levels[0].store, self.store1)
        self.assertEqual(stock_levels[0].price, payload['stores_info'][0]['price'])
        self.assertEqual(
            stock_levels[0].is_sellable, payload['stores_info'][0]['is_sellable']
        )

        # Stock level 2
        self.assertEqual(stock_levels[1].store, self.store2)
        self.assertEqual(stock_levels[1].price, payload['stores_info'][1]['price'])
        self.assertEqual(
            stock_levels[1].is_sellable, payload['stores_info'][1]['is_sellable']
        )

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=True
        ms.save()
              
        response = self.client.post(reverse('api:tp_product_index'), payload)
            
        self.assertEqual(response.status_code, 401)
    
    def test_firebase_messages_are_sent_correctly_for_both_sellable_and_not_sellable(self):

        content = get_test_firebase_sender_log_content(only_include=['product'])
        self.assertEqual(len(content), 0)

        # Create request
        payload = self.get_premade_payload()
        payload['stores_info'] = [
            {
                'is_sellable': True, 
                'price': 1800,
                'reg_no': self.store1.reg_no
            }, 
            {
                'is_sellable': False,
                'price': 1200, 
                'reg_no': self.store2.reg_no
            },
        ]

        # Count Number of Queries
        # with self.assertNumQueries(51):
        response = self.client.post(reverse('api:tp_product_index'), payload)
        self.assertEqual(response.status_code, 201)

        

        content = get_test_firebase_sender_log_content(only_include=['product'])

        pprint(content)
        self.assertEqual(len(content), 1)

        product = Product.objects.get(name=payload['name'])

        # Log 1
        result1 = {
            'tokens': [], 
            'payload': {
                'group_id': self.top_profile1.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'product', 
                'action_type': 'create', 

                'image_url': product.get_image_url(),
                'color_code': product.color_code,
                'name': product.name,
                'cost': str(product.cost),
                'sku': product.sku,
                'barcode': product.barcode,
                'sold_by_each': str(product.sold_by_each),
                'is_bundle': str(product.is_bundle),
                'track_stock': str(product.track_stock),
                'variant_count': str(product.variant_count),
                'show_product': str(product.show_product),
                'show_image': str(product.show_image),
                'reg_no': str(product.reg_no),
                'stock_level': str(product.get_store_stock_level_data(self.store1.reg_no)),
                'store_reg_no': str(self.store1.reg_no),
                'category_data': str(product.get_category_data()),
                'tax_data': str(product.get_tax_data()),
                'modifier_data': str(product.get_modifier_list()),
                'variant_data': str(product.get_variants_data_from_store(self.store1.reg_no)),
            }
        }

        self.assertEqual(content[0], result1)

    def test_if_a_product_cant_be_created_when_new_product_mode_is_off(self):

        payload = self.get_premade_payload()

        # Turn off signups mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.new_product = False
        ms.save()

        response = self.client.post(reverse('api:tp_product_index'), payload)
        self.assertEqual(response.status_code, 423)

        # Confirm product model was not created
        self.assertEqual(Product.objects.all().count(), 0)

    def test_if_view_can_only_create_a_product_with_store_that_belongs_to_the_user(self):

        payload = self.get_premade_payload()

        payload['stores_info'] = [
            {
                    'is_sellable': True, 
                    'price': 1800,
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'is_sellable': False, 
                    'price': 1200,
                    'reg_no': self.store3.reg_no
                },
        ]

        response = self.client.post(reverse('api:tp_product_index'), payload)  
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, 
            {'stores_info': 'You provided wrong stores.'}
        )

        # Confirm product model was not created
        self.assertEqual(Product.objects.all().count(), 0)
    
    def test_if_view_can_create_a_product_as_unsellable_from_a_store(self):

        payload = self.get_premade_payload()

        payload['stores_info'][1]['is_sellable'] = False

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(reverse('api:tp_product_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm product models creation
        self.assertEqual(Product.objects.all().count(), 1)

        p = Product.objects.get(name='Shampoo')

        # Confirm stock levels were created and updated
        stock_levels = StockLevel.objects.filter(product=p).order_by('id')

        # Stock level 1
        self.assertEqual(stock_levels[0].store, self.store1)
        self.assertEqual(stock_levels[0].is_sellable, True)

        # Stock level 2
        self.assertEqual(stock_levels[1].store, self.store2)
        self.assertEqual(stock_levels[1].is_sellable, False)

    def test_if_view_can_create_all_products_as_unsellable_from_a_store(self):

        payload = self.get_premade_payload()

        payload['stores_info'][0]['is_sellable'] = False
        payload['stores_info'][1]['is_sellable'] = False

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(reverse('api:tp_product_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm product models creation
        self.assertEqual(Product.objects.all().count(), 1)

        p = Product.objects.get(name='Shampoo')

        # Confirm stock levels were created and updated
        stock_levels = StockLevel.objects.filter(product=p).order_by('id')

        # Stock level 1
        self.assertEqual(stock_levels[0].store, self.store1)
        self.assertEqual(stock_levels[0].is_sellable, False)

        # Stock level 2
        self.assertEqual(stock_levels[1].store, self.store2)
        self.assertEqual(stock_levels[1].is_sellable, False)

    def test_if_a_product_cant_be_created_with_an_empty_name(self):

        payload = self.get_premade_payload()
  
        payload['name'] = ''

        response = self.client.post(reverse('api:tp_product_index'), payload)

        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_user_cant_have_2_products_with_the_same_name(self):

        # Create product
        Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        )

        payload = self.get_premade_payload()

        response = self.client.post(reverse('api:tp_product_index'), payload)
        self.assertEqual(response.status_code, 400)

        result = {'name': ['You already have a product with this name.']}

        self.assertEqual(response.data, result)

        # Confirm the product was not created
        self.assertEqual(Product.objects.all().count(), 1)

    def test_if_2_users_can_have_2_products_with_the_same_name(self):

        # Create product for user 2
        Product.objects.create(
            profile=self.top_profile2,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        )

        payload = self.get_premade_payload()

        response = self.client.post(reverse('api:tp_product_index'), payload)
        
        self.assertEqual(response.status_code, 201)

        # Confirm product model creation
        self.assertEqual(Product.objects.all().count(), 2)

    def test_if_a_product_cant_be_created_with_an_empty_price(self):

        payload = self.get_premade_payload()

        payload['price'] = ''

        response = self.client.post(reverse('api:tp_product_index'), payload)
        
        self.assertEqual(response.status_code, 400)

        result = {'price': ['A valid number is required.']}

        self.assertEqual(response.data, result)

    def test_if_a_product_cant_be_created_with_an_empty_cost(self):

        payload = self.get_premade_payload()
  
        payload['cost'] = ''

        response = self.client.post(reverse('api:tp_product_index'), payload)
        
        self.assertEqual(response.status_code, 400)

        result = {'cost': ['A valid number is required.']}

        self.assertEqual(response.data, result)

    def test_if_a_product_can_be_created_with_an_empty_sku(self):

        payload = self.get_premade_payload()
   
        payload['sku'] = ''

        response = self.client.post(reverse('api:tp_product_index'), payload)
        
        self.assertEqual(response.status_code, 201)

        # Confirm product tax
        p = Product.objects.get(name=payload['name'])
        self.assertEqual(p.sku, '')

    def test_if_a_product_can_be_created_with_an_empty_barcode(self):

        payload = self.get_premade_payload()

        payload['barcode'] = ''

        response = self.client.post(reverse('api:tp_product_index'), payload)
        
        self.assertEqual(response.status_code, 201)

        # Confirm product tax
        p = Product.objects.get(name=payload['name'])
        self.assertEqual(p.barcode, '')

    def test_if_a_product_can_be_created_with_an_empty_tax(self):

        payload = self.get_premade_payload()

        payload['tax_reg_no'] = 0

        response = self.client.post(reverse('api:tp_product_index'), payload)
        
        self.assertEqual(response.status_code, 201)

        # Confirm product tax
        p = Product.objects.get(name=payload['name'])
        self.assertEqual(p.tax, None)

    def test_if_a_product_cant_be_created_with_a_wrong_tax_reg_no(self):

        # Create a tax for another user
        tax2 = create_new_tax(self.top_profile2, self.store3, 'Tax')

        payload = self.get_premade_payload()

        wrong_reg_nos = [
            7878787, # Wrong reg no,
            tax2.reg_no, # Tax for another user
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        i=0
        for wrong_reg_no in wrong_reg_nos:
            i+=1

            payload['name'] = f'product{i}' # This makes the name unique
            payload['tax_reg_no'] = wrong_reg_no

            response = self.client.post(reverse('api:tp_product_index'), payload)
            self.assertEqual(response.status_code, 201)

            # Confirm product tax
            p = Product.objects.get(name=payload['name'])
            self.assertEqual(p.tax, None)

    def test_if_a_product_can_be_created_with_an_empty_category(self):

        payload = self.get_premade_payload()

        payload['category_reg_no'] = 0

        response = self.client.post(reverse('api:tp_product_index'), payload)
        
        self.assertEqual(response.status_code, 201)

        # Confirm product category
        p = Product.objects.get(name=payload['name'])
        self.assertEqual(p.category, None)

    def test_if_a_product_cant_be_created_with_a_wrong_category_reg_no(self):

        # Create a category for another user
        category2 = create_new_category(self.top_profile2, 'Mask')

        payload = self.get_premade_payload()

        wrong_reg_nos = [
            7878787, # Wrong reg no,
            category2.reg_no, # Category for another user
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        i=0
        for wrong_reg_no in wrong_reg_nos:
            i+=1

            payload['name'] = f'product{i}' # This makes the name unique
            payload['category_reg_no'] = wrong_reg_no

            response = self.client.post(reverse('api:tp_product_index'), payload)
            self.assertEqual(response.status_code, 201)

            # Confirm product category
            p = Product.objects.get(name=payload['name'])
            self.assertEqual(p.category, None)
    
    def test_if_view_can_create_a_bundle_product(self):

        payload = self.get_premade_payload()

        product1, product2 = self.create_2_normal_products()

        payload['bundles_info'] = [
            {"reg_no": product1.reg_no, 'quantity': 30, 'is_dirty': True}, 
            {'reg_no': product2.reg_no, 'quantity': 54, 'is_dirty': True},
        ]

        response = self.client.post(reverse('api:tp_product_index'), payload)
        print(response.data)
        self.assertEqual(response.status_code, 201)

        # Confirm product models creation
        self.assertEqual(Product.objects.all().count(), 3)

        p = Product.objects.get(name=payload['name'])

        # Check model values
        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(p.profile, self.top_profile1)
        self.assertEqual(p.tax, None)
        self.assertEqual(p.category, self.category)
        self.assertEqual(p.bundles.all().count(), 2)
        self.assertEqual(p.image.url, f'/media/images/products/{p.reg_no}_.jpg')
        self.assertEqual(p.color_code, payload['color_code'])
        self.assertEqual(p.name, payload['name'])
        self.assertEqual(p.cost, 0)
        self.assertEqual(p.price, payload['price'])
        self.assertEqual(p.sku, payload['sku'])
        self.assertEqual(p.barcode, payload['barcode'])
        self.assertEqual(p.sold_by_each, True)
        self.assertEqual(p.is_bundle, True)
        self.assertEqual(p.variant_count, 0)
        self.assertEqual(p.is_variant_child, False)
        self.assertEqual(p.show_product, True)
        self.assertEqual(p.show_image, payload['show_image'])
        self.assertTrue(p.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual((p.created_date).strftime("%B, %d, %Y"), today)

        # Confirm stock levels 
        stock_levels = StockLevel.objects.filter(product=p).order_by('id')

        # Stock level 1
        self.assertEqual(stock_levels[0].store, self.store1)
        self.assertEqual( stock_levels[0].units, 0)
        self.assertEqual(stock_levels[0].minimum_stock_level, 0)

        # Stock level 2
        self.assertEqual(stock_levels[1].store, self.store2)
        self.assertEqual(stock_levels[1].units, 0)
        self.assertEqual(stock_levels[1].minimum_stock_level, 0)

    def test_if_a_product_bundle_cant_be_created_with_a_wrong_product_reg_no(self):

        # Create a product for another user
        product = Product.objects.create(
            profile=self.top_profile2,
            name="New product",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        wrong_stores_reg_nos = [
            'aaaa',  # Non numeric
            '1010',  # Wrong reg no
            product.reg_no,# Product from another user
            333333333333333333333333333333333333333333333  # Extremely long
        ]

        payload = self.get_premade_payload()

        i=0
        for wrong_reg_no in wrong_stores_reg_nos:
            payload['bundles_info'] = [
                {"reg_no":wrong_reg_no, 'quantity': 30, 'is_dirty': True}, 
            ]

            response = self.client.post(reverse('api:tp_product_index'), payload)
            self.assertEqual(response.status_code, 400)

            if i == 0:
                self.assertEqual(
                    json.loads(json.dumps(response.data)), 
                    {'bundles_info': {'0': {'reg_no': ['A valid integer is required.']}}}
                )
            elif i == 3:
                self.assertEqual(
                    json.loads(json.dumps(response.data)), 
                    {'bundles_info': {'0': {'reg_no': ['You provided wrong stores']}}}
                )

            else:
                self.assertEqual(
                    response.data, 
                    {'non_field_errors': 'Bundle error.'}
                )
                
            # Confirm product were not created
            self.assertEqual(Product.objects.filter(
                profile=self.top_profile1).count(), 0)

            i+=1

    def test_if_an_proudct_cant_be_created_with_an_empty_bundle_info_info(self):

        payload = self.get_premade_payload()

        payload['bundles_info'] = ''

        response = self.client.post(reverse('api:tp_product_index'), payload)
        self.assertEqual(response.status_code, 400)

        error = {'bundles_info': ['Expected a list of items but got type "str".']}
    
        self.assertEqual(response.data, error)

        # Confirm product were not created
        self.assertEqual(Product.objects.all().count(), 0)

    def test_if_a_product_can_be_created_with_an_empty_bundle_info_list(self):

        payload = self.get_premade_payload()
 
        payload['bundles_info'] = []

        response = self.client.post(reverse('api:tp_product_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm product were created
        p = Product.objects.get(name=payload['name'])
        self.assertEqual(p.bundles.all().count(), 0)

    def test_if_a_product_cant_be_created_with_an_empty_bundle_reg_no(self):

        payload = self.get_premade_payload()
   
        payload['bundles_info'] = [
            {"reg_no": '', 'quantity': 30, 'is_dirty': True}
        ]

        response = self.client.post(reverse('api:tp_product_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'bundles_info': {'0': {'reg_no': ['A valid integer is required.']}}}
        )

        # Confirm product were not created
        self.assertEqual(Product.objects.all().count(), 0)

    def test_if_a_product_cant_be_created_with_an_empty_bundle_quantity(self):

        payload = self.get_premade_payload()

        product1, _ = self.create_2_normal_products()
   
        payload['bundles_info'] = [
            {"reg_no": product1.reg_no, 'quantity': '', 'is_dirty': True}
        ]

        response = self.client.post(reverse('api:tp_product_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'bundles_info': {'0': {'quantity': ['A valid integer is required.']}}}
        )

        # Confirm new product was not created
        self.assertEqual(Product.objects.all().count(), 2)

    def test_if_view_can_create_a_product_with_an_image(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        #with self.assertNumQueries(31):
        with open(self.full_path, 'rb') as my_image: 
 
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.post(reverse('api:tp_product_index'), payload)

        self.assertEqual(response.status_code, 201)

        # Confirm product models creation
        self.assertEqual(Product.objects.all().count(), 1)

        p = Product.objects.get(name='Shampoo')

        # Check model url values
        self.assertEqual(
            p.image.url, 
            f'/media/images/products/{p.reg_no}_.jpg'
        )
  
    def test_if_view_can_edit_an_image_with_the_right_dimensions(self):

        payload = self.get_premade_payload()

        # Send data
        with open(self.full_path, 'rb') as my_image:
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.post(reverse('api:tp_product_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Confirm that the product image was saved with the right dimentsions#
        p = Product.objects.get(name='Shampoo')

        image_path = settings.MEDIA_ROOT + (p.image.url).replace('/media/', '')

        image =  Image.open(image_path)
        
        width , height = image.size
        
        self.assertEqual(width, 200)
        self.assertEqual(height, 200)
       
        # Check model url values
        self.assertEqual(p.image.url, f'/media/images/products/{p.reg_no}_.jpg')

    def test_if_view_will_accept_jpg_image(self):

        payload = self.get_premade_payload()

        blue_image_name = 'pil_blue.jpg'
        blue_image_path = settings.MEDIA_ROOT + blue_image_name
        
        blue_image =  Image.open(blue_image_path)
        
        width , height = blue_image.size

        self.assertEqual(width, 3264)
        self.assertEqual(height, 1836)
    
        # Send data
        with open(blue_image_path, 'rb') as my_image:
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.post(reverse('api:tp_product_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Confirm that the product image was saved with the right dimentsions#
        p = Product.objects.get(name='Shampoo')

        image_path = settings.MEDIA_ROOT + (p.image.url).replace('/media/', '')

        image =  Image.open(image_path)
        
        width , height = image.size
        
        self.assertEqual(width, 200)
        self.assertEqual(height, 200)

        # Check model url values
        self.assertEqual(p.image.url, f'/media/images/products/{p.reg_no}_.jpg')

    def test_if_view_will_accept_jpeg_image(self):

        payload = self.get_premade_payload()

        orange_image_name = 'pil_orange.jpeg'
        orange_image_path = settings.MEDIA_ROOT + orange_image_name
        
        orange_image =  Image.open(orange_image_path)
        
        width , height = orange_image.size

        self.assertEqual(width, 3264)
        self.assertEqual(height, 1836)

        # Send data
        with open(orange_image_path, 'rb') as my_image:
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.post(reverse('api:tp_product_index'), payload)
            self.assertEqual(response.status_code, 201)

        # Confirm that the product image was saved with the right dimentsions#
        p = Product.objects.get(name='Shampoo')

        image_path = settings.MEDIA_ROOT + (p.image.url).replace('/media/', '')

        image =  Image.open(image_path)
        
        width , height = image.size
        
        self.assertEqual(width, 200)
        self.assertEqual(height, 200)
       
        # Check model url values
        self.assertEqual(p.image.url, f'/media/images/products/{p.reg_no}_.jpg')

    def test_if_view_wont_accept_an_image_if_its_not_jpeg_jpg_or_png(self):

        payload = self.get_premade_payload()

        gif_image_name = 'animated-love-image-0187.gif'
        gif_image_path = settings.MEDIA_ROOT + gif_image_name
        
        gif_image =  Image.open(gif_image_path)
        
        width , height = gif_image.size

        self.assertEqual(width, 240)
        self.assertEqual(height, 320)

        # Send data
        with open(gif_image_path, 'rb') as my_image:
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.post(reverse('api:tp_product_index'), payload)

            self.assertEqual(response.status_code, 400)
            
        result = {'error': 'Allowed image extensions are .jpg, .jpeg and .png'}
        self.assertEqual(response.data, result)

    def test_if_view_wont_accept_a_non_image_file(self):

        payload = self.get_premade_payload()

        bad_file__name = 'bad_file_extension.py'
        bad_file_path = settings.MEDIA_ROOT + bad_file__name

        # Send data
        with open(bad_file_path, 'rb') as my_image:
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.post(reverse('api:tp_product_index'), payload)

            self.assertEqual(response.status_code, 400)
            
        result = {'uploaded_image': ['Upload a valid image. The file you uploaded was either not an image or a corrupted image.']}
        self.assertEqual(response.data, result)

    def test_if_view_url_can_throttle_post_requests(self):

        payload = self.get_premade_payload()

        throttle_rate = int(settings.THROTTLE_RATES['api_product_rate'].split("/")[0])
    
        for i in range(throttle_rate): # pylint: disable=unused-variable

            payload['name'] = f'product{i}' # This makes the name unique
    
            response = self.client.post(reverse('api:tp_product_index'), payload)
            self.assertEqual(response.status_code, 201)


        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional 
        # request if the previous request was not throttled 
        for i in range(throttle_rate): # pylint: disable=unused-variable

            # Try to see if the next request will be throttled
            payload['name'] = f'product{i}' # This makes the name unique
    
            response = self.client.post(reverse('api:tp_product_index'), payload)

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else: 
            # Executed because break was not called. This means the request was
            # never throttled 
            self.fail()

    # def test_if_view_cant_be_viewed_by_an_employee_user(self):

    #     # Login a employee profile #
    #     # Include an appropriate `Authorization:` header on all requests.
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     payload = self.get_premade_payload()
    
    #     response = self.client.post(reverse('api:tp_product_index'), payload)
    #     self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.post(reverse('api:tp_product_index'), payload)
        self.assertEqual(response.status_code, 401)



class TpProductEditViewForViewingTestCase(APITestCase, InitialUserDataMixin):
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

        # Create a tax
        self.tax1 = create_new_tax(self.top_profile1, self.store1, "Standard")
        self.tax2 = create_new_tax(self.top_profile1, self.store1, "New Standard")

        # Create a category
        self.category1 = create_new_category(self.top_profile1, "Hair")
        self.category2 = create_new_category(self.top_profile1, "Face")

        self.create_single_product()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name="main")
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email="john@gmail.com")
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    def create_single_product(self):
        # Create a products
        # ------------------------------ Product 1
        self.product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category1,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku="sku1",
            barcode="code123",
        )

        # ------------------------------ Product 2
        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category1,
            name="Conditioner",
            price=2500,
            cost=1000,
            sku="sku1",
            barcode="code123",
        )

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product2,
            profile=self.top_profile1,
            store1=self.store1,
            store2=self.store2,
        )

        # Create bundle product
        # self.create_master_product()

    def create_master_product(self):
        # ------------------------------ Product 1
        master_product = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category1,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku="sku1",
            barcode="code123",
        )

        product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category1,
            name="Comb",
            price=750,
            cost=120,
            sku="sku1",
            barcode="code123",
        )

        product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category1,
            name="Clip",
            price=2800,
            cost=1200,
            barcode="code123",
        )
    
        # Create master product with 2 bundles
        comb_bundle = ProductBundle.objects.create(product_bundle=product1, quantity=30)

        clip_bundle = ProductBundle.objects.create(product_bundle=product2, quantity=25)

        master_product.bundles.add(clip_bundle, comb_bundle)

    def test_view_can_be_called_successefully(self):
        """
        Test's product with all stores
        """
        # Count Number of Queries #
        # with self.assertNumQueries(5):
        response = self.client.get(
            reverse("api:tp_product_edit", args=(self.product1.reg_no,))
        )
        self.assertEqual(response.status_code, 200)

        product = Product.objects.get(name="Shampoo")

        result = {
            "color_code": product.color_code,
            "name": product.name,
            "price": str(product.price),
            "cost": str(product.cost),
            "sku": product.sku,
            "barcode": product.barcode,
            "sold_by_each": product.sold_by_each,
            "is_bundle": product.is_bundle,
            "show_product": product.show_product,
            "show_image": product.show_image,
            "image_url": product.get_image_url(),
            "reg_no": product.reg_no,
            "category_data": product.get_category_data(),
            "tax_data": product.get_tax_data(),
            "variant_data": product.get_product_view_variants_data(),
            "bundle_data": product.get_product_view_bundles_data(),
            "available_taxes": [
                {"name": self.tax2.name, "reg_no": self.tax2.reg_no},
                {"name": self.tax1.name, "reg_no": self.tax1.reg_no},
            ],
            "available_categories": [
                {"name": self.category2.name, "reg_no": self.category2.reg_no},
                {"name": self.category1.name, "reg_no": self.category1.reg_no},
            ],
            "registered_stores": [
                {
                    "store_name": self.store2.name,
                    "store_reg_no": self.store2.reg_no,
                    "minimum_stock_level": "0",
                    "units": "0.00",
                    "price": "2500.00",
                    "is_sellable": True,
                },
                {
                    "store_name": self.store1.name,
                    "store_reg_no": self.store1.reg_no,
                    "minimum_stock_level": "0",
                    "units": "0.00",
                    "price": "2500.00",
                    "is_sellable": True,
                }
            ],
            "available_stores": [
                {"name": self.store2.name, "reg_no": self.store2.reg_no},
                {"name": self.store1.name, "reg_no": self.store1.reg_no},
            ],
        }
        self.assertEqual(response.data, result)

    def test_view_can_be_called_successefully2(self):
        """
        Test's product after product has been made unsellable from 1 store
        """

        # Make product unsellable from 1 store
        level = StockLevel.objects.get(product=self.product1, store=self.store2)
        level.is_sellable = False
        level.save()

        # self.product1.stores.remove(self.store2)

        # Count Number of Queries #
        with self.assertNumQueries(12):
            response = self.client.get(
                reverse("api:tp_product_edit", args=(self.product1.reg_no,))
            )
            self.assertEqual(response.status_code, 200)

        product = Product.objects.get(name="Shampoo")

        result = {
            "color_code": product.color_code,
            "name": product.name,
            "price": str(product.price),
            "cost": str(product.cost),
            "sku": product.sku,
            "barcode": product.barcode,
            "sold_by_each": product.sold_by_each,
            "is_bundle": product.is_bundle,
            "show_product": product.show_product,
            "show_image": product.show_image,
            "image_url": product.get_image_url(),
            "reg_no": product.reg_no,
            "category_data": product.get_category_data(),
            "tax_data": product.get_tax_data(),
            "variant_data": product.get_product_view_variants_data(),
            "bundle_data": product.get_product_view_bundles_data(),
            "available_taxes": [
                {"name": self.tax2.name, "reg_no": self.tax2.reg_no},
                {"name": self.tax1.name, "reg_no": self.tax1.reg_no},
            ],
            "available_categories": [
                {"name": self.category2.name, "reg_no": self.category2.reg_no},
                {"name": self.category1.name, "reg_no": self.category1.reg_no}, 
            ],
            "registered_stores": [
                {
                    'store_name': self.store2.name, 
                    'store_reg_no': self.store2.reg_no, 
                    'minimum_stock_level': '0', 
                    'units': '0.00',
                    "price": "2500.00",
                    'is_sellable': False
                },
                {
                    'store_name': self.store1.name, 
                    'store_reg_no': self.store1.reg_no, 
                    'minimum_stock_level': '0', 
                    'units': '0.00',
                    "price": "2500.00",
                    'is_sellable': True
                }
            ],
            "available_stores": [
                {"name": self.store2.name, "reg_no": self.store2.reg_no},
                {"name": self.store1.name, "reg_no": self.store1.reg_no}, 
            ],
        }

        self.assertEqual(response.data, result)

    def test_view_can_be_called_successefully3(self):

        """
        Test's product after product has been made unsellable from all stores
        """

        # Make product unsellable from all stores
        StockLevel.objects.filter(product=self.product1).update(is_sellable = False)
       
        response = self.client.get(
            reverse('api:tp_product_edit', args=(self.product1.reg_no,))
        )
        self.assertEqual(response.status_code, 200)

        product = Product.objects.get(name='Shampoo')

        result = {
            'color_code': product.color_code, 
            'name': product.name, 
            'price': str(product.price), 
            'cost': str(product.cost), 
            'sku': product.sku, 
            'barcode': product.barcode, 
            'sold_by_each': product.sold_by_each, 
            'is_bundle': product.is_bundle,
            'show_product': product.show_product, 
            'show_image': product.show_image, 
            'image_url': product.get_image_url(),
            'reg_no': product.reg_no,
            'category_data': product.get_category_data(),
            'tax_data': product.get_tax_data(),
            'variant_data': product.get_product_view_variants_data(), 
            'bundle_data': product.get_product_view_bundles_data(),
            'available_taxes': [
                {
                    'name': self.tax2.name, 
                    'reg_no': self.tax2.reg_no
                },
                {
                    'name': self.tax1.name, 
                    'reg_no': self.tax1.reg_no
                }
            ], 
            'available_categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }
            ], 
            'registered_stores': [ 
                {
                    'store_name': self.store2.name, 
                    'store_reg_no': self.store2.reg_no, 
                    'minimum_stock_level': '0', 
                    'units': '0.00',
                    "price": "2500.00",
                    'is_sellable': False
                },
                {
                    'store_name': self.store1.name, 
                    'store_reg_no': self.store1.reg_no, 
                    'minimum_stock_level': '0', 
                    'units': '0.00',
                    "price": "2500.00",
                    'is_sellable': False
                }
            ], 
            'available_stores': [
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

        self.assertEqual(response.data, result)

    def test_view_can_be_called_successefully_with_variant_product(self):
        """
        Test's product with all stores
        """
        response = self.client.get(
            reverse('api:tp_product_edit', args=(self.product2.reg_no,))
        )
        self.assertEqual(response.status_code, 200)

        product = Product.objects.get(name='Conditioner')

        result = {
            'color_code': product.color_code, 
            'name': product.name, 
            'price': str(product.price), 
            'cost': str(product.cost), 
            'sku': product.sku, 
            'barcode': product.barcode, 
            'sold_by_each': product.sold_by_each, 
            'is_bundle': product.is_bundle,
            'show_product': product.show_product, 
            'show_image': product.show_image, 
            'image_url': product.get_image_url(),
            'reg_no': product.reg_no,
            'category_data': product.get_category_data(),
            'tax_data': product.get_tax_data(),
            'variant_data': product.get_product_view_variants_data(), 
            'bundle_data': product.get_product_view_bundles_data(),
            'available_taxes': [
                {
                    'name': self.tax2.name, 
                    'reg_no': self.tax2.reg_no
                },
                {
                    'name': self.tax1.name, 
                    'reg_no': self.tax1.reg_no
                }
            ], 
            'available_categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                } 
            ], 
            'registered_stores': [
                {
                    "store_name": self.store2.name,
                    "store_reg_no": self.store2.reg_no,
                    "minimum_stock_level": "0",
                    "units": "0.00",
                    "price": "2500.00",
                    "is_sellable": True,
                },
                {
                    "store_name": self.store1.name,
                    "store_reg_no": self.store1.reg_no,
                    "minimum_stock_level": "0",
                    "units": "0.00",
                    "price": "2500.00",
                    "is_sellable": True,
                }
            ], 
            'available_stores': [
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

        self.assertEqual(response.data, result)
        
        # Confirm variants
        variant_data = response.data['variant_data']
        self.assertEqual(len(variant_data), 3)

        for variant in variant_data:
            self.assertEqual(len(variant['registered_stores']), 2)
            self.assertEqual(
                variant['registered_stores'][0]['store_name'],
                self.store2.name
            )
            self.assertEqual(
                variant['registered_stores'][1]['store_name'],
                self.store1.name
            )

    def test_view_can_be_called_successefully_with_bundle_product(self):
        
        Product.objects.all().delete()

        self.create_master_product()

        product = Product.objects.get(name='Shampoo')

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.get(
            reverse('api:tp_product_edit', args=(product.reg_no,))
        )
        self.assertEqual(response.status_code, 200)

        result = {
            'color_code': product.color_code, 
            'name': product.name, 
            'price': str(product.price), 
            'cost': str(product.cost), 
            'sku': product.sku, 
            'barcode': product.barcode, 
            'sold_by_each': product.sold_by_each, 
            'is_bundle': product.is_bundle,
            'show_product': product.show_product, 
            'show_image': product.show_image, 
            'image_url': product.get_image_url(),
            'reg_no': product.reg_no,
            'category_data': product.get_category_data(),
            'tax_data': product.get_tax_data(),
            'variant_data': product.get_product_view_variants_data(), 
            'bundle_data': product.get_product_view_bundles_data(),
            'available_taxes': [
                {
                    'name': self.tax2.name, 
                    'reg_no': self.tax2.reg_no
                },
                {
                    'name': self.tax1.name, 
                    'reg_no': self.tax1.reg_no
                }
            ], 
            'available_categories': [
                {
                    'name': self.category2.name, 
                    'reg_no': self.category2.reg_no
                },
                {
                    'name': self.category1.name, 
                    'reg_no': self.category1.reg_no
                }
            ], 
            'registered_stores': [
                {
                    "store_name": self.store2.name,
                    "store_reg_no": self.store2.reg_no,
                    "minimum_stock_level": "0",
                    "units": "0.00",
                    "price": "2500.00",
                    "is_sellable": True,
                },
                {
                    "store_name": self.store1.name,
                    "store_reg_no": self.store1.reg_no,
                    "minimum_stock_level": "0",
                    "units": "0.00",
                    "price": "2500.00",
                    "is_sellable": True,
                }
            ], 
            'available_stores': [
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

        self.assertEqual(response.data, result)
        self.assertEqual(len(response.data['bundle_data']), 2)

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:tp_product_edit', args=(self.product1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:tp_product_edit', args=(self.product1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:tp_product_edit', args=(self.product1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

class TpProductEditViewForEditingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')
        self.tax2 = create_new_tax(self.top_profile1, self.store1, 'New Standard')

        # Create a category
        self.category = create_new_category(self.top_profile1, 'Hair')
        self.category2 = create_new_category(self.top_profile1, 'Face')

        self.create_single_product()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Test image resources
        self.test_image_name = 'pil_red.png'
        self.full_path=settings.MEDIA_ROOT + self.test_image_name
 
    def create_single_product(self):

        # Create a products
        # ------------------------------ Product 1
        self.product = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        )

        # Update stock units for store 1 and 2
        stock = StockLevel.objects.get(product=self.product, store=self.store1)
        stock.units = 100
        stock.save()

    def create_2_normal_products(self):

        product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Comb",
            price=750,
            cost=120,
            sku='sku1',
            barcode='code123'
        )

        product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Clip",
            price=2800,
            cost=1200,
            barcode='code123'
        )
      
        return product1, product2

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """
        payload = {
            'color_code': '#000000',
            'name': 'Gel', 
            'cost': 3100,
            'price': 1800,
            'sku': 'sku1_edit',
            'barcode': 'code123_edit',
            'sold_by_each': False,
            'show_product': False,
            'show_image': True,

            'new_stocks_units': 6002,
            'tax_reg_no': self.tax2.reg_no,
            'category_reg_no': self.category2.reg_no,
            'bundles_info': [],
            'modifiers_info': [],
            'variants_info': [],
            'stores_info': [
                {
                    'is_sellable': True, 
                    'price': 1800,
                    'reg_no': self.store1.reg_no,
                    'is_dirty': True

                },
                {
                    'is_sellable': True, 
                    'price': 1200,
                    'reg_no': self.store2.reg_no,
                    'is_dirty': True
                } 
            ]
        }

        return payload
    
    def test_if_view_can_edit_a_product(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        # with self.assertNumQueries(55):
        response = self.client.put(
            reverse('api:tp_product_edit', args=(self.product.reg_no,)), payload
        )

        self.assertEqual(response.status_code, 200)

        """
        Ensure a product has the right fields after it has been edited
        """
        p = Product.objects.get(name="Gel")

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(p.profile, self.top_profile1)
        self.assertEqual(p.tax, self.tax2)
        self.assertEqual(p.category, self.category2)
        self.assertEqual(p.bundles.all().count(), 0)
        self.assertEqual(p.image.url, f'/media/images/products/{p.reg_no}_.jpg')
        self.assertEqual(p.color_code, payload['color_code'])
        self.assertEqual(p.name, payload['name'])
        self.assertEqual(p.cost, payload['cost'])
        self.assertEqual(p.price, payload['price'])
        self.assertEqual(p.sku, payload['sku'])
        self.assertEqual(p.barcode, payload['barcode'])
        self.assertEqual(p.sold_by_each, payload['sold_by_each'])
        self.assertEqual(p.is_bundle, False)
        self.assertEqual(p.variant_count, 0)
        self.assertEqual(p.is_variant_child, False)
        self.assertEqual(p.show_product, payload['show_product'])
        self.assertEqual(p.show_image, payload['show_image'])
        self.assertTrue(p.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual((p.created_date).strftime("%B, %d, %Y"), today)

        # Confirm stock levels were updated
        stock_levels = StockLevel.objects.filter(product=self.product).order_by('id')
        self.assertEqual(stock_levels.count(), 2)

        # Stock level 1
        self.assertEqual(stock_levels[0].store, self.store1)
        self.assertEqual(stock_levels[0].units, Decimal('100.00'))
        self.assertEqual(stock_levels[0].price, Decimal('1800.00'))
        self.assertEqual(stock_levels[0].is_sellable, True)

        # Stock level 2
        self.assertEqual(stock_levels[1].store, self.store2)
        self.assertEqual(stock_levels[1].units, Decimal('0.00'))
        self.assertEqual(stock_levels[1].price, Decimal('1200.00'))
        self.assertEqual(stock_levels[1].is_sellable, True)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=True
        ms.save()

        response = self.client.put(
            reverse('api:tp_product_edit', args=(self.product.reg_no,)), payload
        )  
        self.assertEqual(response.status_code, 401)
  
    def test_firebase_messages_are_sent_correctly_when_products_are_marked_as_sellable_and_not_sellable(self):

        content = get_test_firebase_sender_log_content(only_include=['product'])
        self.assertEqual(len(content), 0)

        # Create request
        payload = self.get_premade_payload()
        payload['stores_info'] = [
            {
                'is_sellable': True, 
                'price': 1800,
                'reg_no': self.store1.reg_no,
                'is_dirty': True

            },
            {
                'is_sellable': False, 
                'price': 1200,
                'reg_no': self.store2.reg_no,
                'is_dirty': True
            }
        ]

        response = self.client.put(
            reverse('api:tp_product_edit', args=(self.product.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 200)

        content = get_test_firebase_sender_log_content(only_include=['product'])
        self.assertEqual(len(content), 2)

        product = Product.objects.get(name=payload['name'])

        product = Product.objects.get(name=payload['name'])

        # Log 1
        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.top_profile1.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'product', 
                'action_type': 'edit', 

                'image_url': product.get_image_url(),
                'color_code': product.color_code,
                'name': payload['name'],
                'price': str(product.price),
                'cost': str(product.cost),
                'sku': product.sku,
                'barcode': product.barcode,
                'sold_by_each': str(product.sold_by_each),
                'is_bundle': str(product.is_bundle),
                'track_stock': str(product.track_stock),
                'variant_count': str(product.variant_count),
                'show_product': str(product.show_product),
                'show_image': str(product.show_image),
                'reg_no': str(product.reg_no),
                'stock_level': str(product.get_store_stock_units(self.store1.reg_no)),
                'category_data': str(product.get_category_data()),
                'tax_data': str(product.get_tax_data()),
                'modifier_data': str(product.get_modifier_list()),
                'variant_data': str(product.get_variants_data_from_store(self.store1.reg_no)),
            }
        }

        self.assertEqual(content[0], result)

        # Log 2
        result2 = {
            'tokens': [], 
            'payload': {
                'group_id': '', 
                'relevant_stores': '[]', 
                'model': 'product', 
                'action_type': 'delete', 
                'reg_no': str(self.product.reg_no),
            }
        }

        self.assertEqual(content[1], result2)

    def test_view_wont_edit_products_that_are_not_dirty(self):

        # Add store2
        product = Product.objects.get(name="Shampoo")
   
        self.assertEqual(product.stores.all().count(), 2)

        # Mark all products as sellable
        StockLevel.objects.all().update(is_sellable=False)

        levels = StockLevel.objects.all()

        for level in levels:
            self.assertEqual(level.is_sellable, False)

        # Confirm store was added
        product = Product.objects.get(name="Shampoo")

        self.assertEqual(product.stores.all().count(), 2)

        payload = self.get_premade_payload()

        payload['stores_info'][0]['is_sellable'] = True
        payload['stores_info'][0]['is_dirty'] = False

        payload['stores_info'][1]['is_sellable'] = True
        payload['stores_info'][1]['is_dirty'] = False

        response = self.client.put(
            reverse('api:tp_product_edit', args=(self.product.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 200)

        # Confirm stock levels were updated
        stock_levels = StockLevel.objects.filter(product=product).order_by('id')
        self.assertEqual(stock_levels.count(), 2)

        # Stock level 1
        self.assertEqual(stock_levels[0].store, self.store1)

        self.assertEqual(stock_levels[0].units, Decimal('100.00'))
        self.assertEqual(stock_levels[0].is_sellable, False)

        # Stock level 2
        self.assertEqual(stock_levels[1].store, self.store2)
        self.assertEqual(stock_levels[1].units, 0)
        self.assertEqual(stock_levels[1].is_sellable, False)
               
    def test_view_can_mark_a_product_as_unsellable_from_a_store(self):

        # Add store2
        product = Product.objects.get(name="Shampoo")

        # Confirm store was added
        product = Product.objects.get(name="Shampoo")

        self.assertEqual(product.stores.all().count(), 2)

        payload = self.get_premade_payload()

        payload['stores_info'][1]['is_sellable'] = False

        response = self.client.put(
            reverse('api:tp_product_edit', args=(self.product.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 200)

        # Confirm stock levels were updated
        stock_levels = StockLevel.objects.filter(product=product).order_by('id')
        self.assertEqual(stock_levels.count(), 2)

        # Stock level 1
        self.assertEqual(stock_levels[0].store, self.store1)
        self.assertEqual(stock_levels[0].units, Decimal('100.00'))
        self.assertEqual(stock_levels[0].is_sellable, True)

        # Stock level 2
        self.assertEqual(stock_levels[1].store, self.store2)
        self.assertEqual(stock_levels[1].units, 0)
        self.assertEqual(stock_levels[1].is_sellable, False)

    def test_view_can_mark_all_products_as_unsellable_from_a_store(self):

        # Add store2
        product = Product.objects.get(name="Shampoo")

        # Confirm store was added
        product = Product.objects.get(name="Shampoo")

        self.assertEqual(product.stores.all().count(), 2)

        payload = self.get_premade_payload()

        payload['stores_info'][0]['is_sellable'] = False
        payload['stores_info'][1]['is_sellable'] = False

        response = self.client.put(
            reverse('api:tp_product_edit', args=(self.product.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 200)

        # Confirm stock levels were updated
        stock_levels = StockLevel.objects.filter(product=product).order_by('id')
        self.assertEqual(stock_levels.count(), 2)

        # Stock level 1
        self.assertEqual(stock_levels[0].store, self.store1)
        self.assertEqual(stock_levels[0].units, Decimal('100.00'))
        self.assertEqual(stock_levels[0].is_sellable, False)

        # Stock level 2
        self.assertEqual(stock_levels[1].store, self.store2)
        self.assertEqual(stock_levels[1].units, 0)
        self.assertEqual(stock_levels[1].is_sellable, False)

    def test_view_can_mark_all_products_as_sellable_from_a_store(self):

        # Mark all products as sellable
        StockLevel.objects.all().update(is_sellable=False)

        # Add store2
        product = Product.objects.get(name="Shampoo")

        # Confirm store was added
        product = Product.objects.get(name="Shampoo")

        self.assertEqual(product.stores.all().count(), 2)

        payload = self.get_premade_payload()

        payload['stores_info'][0]['is_sellable'] = True
        payload['stores_info'][1]['is_sellable'] = True

        response = self.client.put(
            reverse('api:tp_product_edit', args=(self.product.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 200)

        # Confirm stock levels were updated
        stock_levels = StockLevel.objects.filter(product=product).order_by('id')
        self.assertEqual(stock_levels.count(), 2)

        # Stock level 1
        self.assertEqual(stock_levels[0].store, self.store1)
        self.assertEqual(stock_levels[0].units, Decimal('100.00'))
        self.assertEqual(stock_levels[0].is_sellable, True)

        # Stock level 2
        self.assertEqual(stock_levels[1].store, self.store2)
        self.assertEqual(stock_levels[1].units, 0)
        self.assertEqual(stock_levels[1].is_sellable, True)

    def test_view_can_handle_a_wrong_store_reg_no(self):

        payload = self.get_premade_payload()
        payload['stores_info']= [{'reg_no': self.store2.reg_no},]

        response = self.client.put(
            reverse('api:tp_product_edit', args=(111111111,)), payload
        )
        self.assertEqual(response.status_code, 404)


    def test_view_wont_accept_an_empty_store_info(self):

        payload = self.get_premade_payload()
        payload['stores_info'] = ''

        response = self.client.put(
            reverse('api:tp_product_edit', args=(self.product.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, 
            {'stores_info': ['Expected a list of items but got type "str".']}
        )

        # Confirm discount was not changed
        self.assertEqual(Product.objects.filter(name='Shampoo').count(), 1)
    
    def test_view_wont_accept_an_empty_store_info_list(self):

        payload = self.get_premade_payload()
        payload['stores_info'] = []

        response = self.client.put(
            reverse('api:tp_product_edit', args=(self.product.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, 
            {'stores_info': 'You provided wrong stores.'}
        )

        # Confirm discount was not changed
        self.assertEqual(Product.objects.filter(name='Shampoo').count(), 1)
    
    def test_if_view_cant_be_edited_with_a_wrong_stores_reg_no(self):

        wrong_stores_reg_nos = [
            '1010',  # Wrong reg no
            'aaaa',  # Non numeric
            #3333333333333333333333333333333333333333333333  # Extremely long
        ]

        i = 0
        for reg_no in wrong_stores_reg_nos:

            payload = self.get_premade_payload()
            payload['stores_info'][0]['reg_no'] = reg_no

            response = self.client.put(reverse(
                'api:tp_product_edit', 
                args=(self.product.reg_no,)), 
                payload
            )
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

            i += 1

        # Confirm discount was not changed
        self.assertEqual(Product.objects.filter(name='Shampoo').count(), 1)

    def test_view_wont_accept_a_store_that_belongs_to_another_user(self):

        payload = self.get_premade_payload()
        payload['stores_info'][0]['reg_no'] = self.store3.reg_no

        response = self.client.put(
            reverse('api:tp_product_edit', args=(self.product.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, 
            {'stores_info': 'You provided wrong stores.'}
        )

        # Confirm discount was not changed
        self.assertEqual(Product.objects.filter(name='Shampoo').count(), 1)

    def test_if_view_can_handle_a_wrong_product_reg_no(self):

        payload = self.get_premade_payload()

        wrong_reg_nos = [
            7878787, # Wrong reg no,
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        for wrong_reg_no in wrong_reg_nos:
            response = self.client.put(
                reverse('api:tp_product_edit', args=(wrong_reg_no,)), payload
            )

            self.assertEqual(response.status_code, 404)

    def test_if_a_product_cant_be_edited_with_an_empty_name(self):

        payload = self.get_premade_payload()
  
        payload['name'] = ''

        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 400)

        result = {'name': ['This field may not be blank.']}

        self.assertEqual(response.data, result)

    def test_if_a_user_cant_have_2_products_with_the_same_name(self):

        # Create product
        Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Gel",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        )

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
         
        self.assertEqual(response.status_code, 400)

        result = {'name': ['You already have a product with this name.']}

        self.assertEqual(response.data, result)

        # Check that edit product was not successful
        product1_count = Product.objects.filter(
            profile=self.top_profile1, name="Shampoo").count()
        self.assertEqual(product1_count, 1)

        product1_count = Product.objects.filter(
            profile=self.top_profile1, name="Gel").count()
        self.assertEqual(product1_count, 1)

    def test_if_2_users_can_have_2_products_with_the_same_name(self):

        # Create product for user 2
        Product.objects.create(
            profile=self.top_profile2,
            tax=self.tax,
            category=self.category,
            name="Gel",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        )

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        
        self.assertEqual(response.status_code, 200)


        # Check that edit product was not successful
        product1_count = Product.objects.filter(
            profile=self.top_profile1, name="Gel").count()
        self.assertEqual(product1_count, 1)

        product1_count = Product.objects.filter(
            profile=self.top_profile1, name="Gel").count()
        self.assertEqual(product1_count, 1)

    
    def test_if_a_product_cant_be_edited_with_an_empty_price(self):

        payload = self.get_premade_payload()

        payload['price'] = ''

        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        
        self.assertEqual(response.status_code, 400)

        result = {'price': ['A valid number is required.']}

        self.assertEqual(response.data, result)
    
    def test_if_a_product_cant_be_edited_with_an_empty_cost(self):

        payload = self.get_premade_payload()
  
        payload['cost'] = ''

        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        
        self.assertEqual(response.status_code, 400)

        result = {'cost': ['A valid number is required.']}

        self.assertEqual(response.data, result)

    def test_if_a_product_can_be_edited_with_an_empty_sku(self):

        payload = self.get_premade_payload()
   
        payload['sku'] = ''

        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        
        self.assertEqual(response.status_code, 200)

        # Confirm product tax
        p = Product.objects.get(name=payload['name'])
        self.assertEqual(p.sku, '')

    def test_if_a_product_can_be_edited_with_an_empty_barcode(self):

        payload = self.get_premade_payload()

        payload['barcode'] = ''

        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        
        self.assertEqual(response.status_code, 200)

        # Confirm product tax
        p = Product.objects.get(name=payload['name'])
        self.assertEqual(p.barcode, '')

    def test_if_a_product_can_be_edited_with_an_empty_tax(self):

        payload = self.get_premade_payload()

        payload['tax_reg_no'] = 0

        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        
        self.assertEqual(response.status_code, 200)

        # Confirm product tax
        p = Product.objects.get(name=payload['name'])
        self.assertEqual(p.tax, None)

    def test_if_a_product_cant_be_edited_with_a_wrong_tax_reg_no(self):

        # Create a tax for another user
        tax2 = create_new_tax(self.top_profile2, self.store3, 'Tax')

        payload = self.get_premade_payload()

        wrong_reg_nos = [
            7878787, # Wrong reg no,
            tax2.reg_no, # Tax for another user
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        i=0
        for wrong_reg_no in wrong_reg_nos:
            i+=1

            payload['name'] = f'product{i}' # This makes the name unique
            payload['tax_reg_no'] = wrong_reg_no

            response = self.client.put(
                reverse('api:tp_product_edit', 
                args=(self.product.reg_no,)), 
                payload,
            )
        
            self.assertEqual(response.status_code, 200)

            # Confirm product tax
            p = Product.objects.get(name=payload['name'])
            self.assertEqual(p.tax, None)
    
    def test_if_a_product_can_be_edited_with_an_empty_category(self):

        payload = self.get_premade_payload()

        payload['category_reg_no'] = 0

        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        
        self.assertEqual(response.status_code, 200)

        # Confirm product category
        p = Product.objects.get(name=payload['name'])
        self.assertEqual(p.category, None)
 
    def test_if_a_product_cant_be_edited_with_a_wrong_category_reg_no(self):

        # Create a category for another user
        category2 = create_new_category(self.top_profile2, 'Mask')

        payload = self.get_premade_payload()

        wrong_reg_nos = [
            7878787, # Wrong reg no,
            category2.reg_no, # Category for another user
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        i=0
        for wrong_reg_no in wrong_reg_nos:
            i+=1

            payload['name'] = f'product{i}' # This makes the name unique
            payload['category_reg_no'] = wrong_reg_no

            response = self.client.put(
                reverse('api:tp_product_edit', 
                args=(self.product.reg_no,)), 
                payload,
            )
        
            self.assertEqual(response.status_code, 200)

            # Confirm product category
            p = Product.objects.get(name=payload['name'])
            self.assertEqual(p.category, None)

    def test_if_view_can_edit_a_product_image(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        #with self.assertNumQueries(9):
        with open(self.full_path, 'rb') as my_image: 
      
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:tp_product_edit', 
                args=(self.product.reg_no,)), 
                payload
            )

        self.assertEqual(response.status_code, 200)

        p = Product.objects.get(name=payload['name'])

        # Check model url values
        self.assertEqual(
            p.image.url, 
            f'/media/images/products/{p.reg_no}_.jpg'
        )

    def test_if_view_can_edit_an_image_with_the_right_dimensions(self):

        payload = self.get_premade_payload()

        # Send data
        with open(self.full_path, 'rb') as my_image:
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:tp_product_edit', 
                args=(self.product.reg_no,)), 
                payload
            )
            
            self.assertEqual(response.status_code, 200)

        # Confirm that the product image was saved with the right dimentsions#
        p = Product.objects.get(name=payload['name'])

        image_path = settings.MEDIA_ROOT + (p.image.url).replace('/media/', '')

        image =  Image.open(image_path)
        
        width , height = image.size
        
        self.assertEqual(width, 200)
        self.assertEqual(height, 200)
       
        # Check model url values
        self.assertEqual(
            p.image.url, 
            f'/media/images/products/{p.reg_no}_.jpg'
        )

    def test_if_view_will_accept_jpg_image(self):

        payload = self.get_premade_payload()

        blue_image_name = 'pil_blue.jpg'
        blue_image_path = settings.MEDIA_ROOT + blue_image_name
        
        blue_image =  Image.open(blue_image_path)
        
        width , height = blue_image.size

        self.assertEqual(width, 3264)
        self.assertEqual(height, 1836)
    
        # Send data
        with open(blue_image_path, 'rb') as my_image:

            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:tp_product_edit', 
                args=(self.product.reg_no,)), 
                payload
            )
            
            self.assertEqual(response.status_code, 200)

        # Confirm that the product image was saved with the right dimentsions#
        p = Product.objects.get(name=payload['name'])

        image_path = settings.MEDIA_ROOT + (p.image.url).replace('/media/', '')

        image =  Image.open(image_path)
        
        width , height = image.size
        
        self.assertEqual(width, 200)
        self.assertEqual(height, 200)

        # Check model url values
        self.assertEqual(
            p.image.url, 
            f'/media/images/products/{p.reg_no}_.jpg'
        )

    def test_if_view_will_accept_jpeg_image(self):

        payload = self.get_premade_payload()

        orange_image_name = 'pil_orange.jpeg'
        orange_image_path = settings.MEDIA_ROOT + orange_image_name
        
        orange_image =  Image.open(orange_image_path)
        
        width , height = orange_image.size

        self.assertEqual(width, 3264)
        self.assertEqual(height, 1836)

        # Send data
        with open(orange_image_path, 'rb') as my_image:
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:tp_product_edit', 
                args=(self.product.reg_no,)), 
                payload
            )
            
            self.assertEqual(response.status_code, 200)

        # Confirm that the product image was saved with the right dimentsions#
        p = Product.objects.get(name=payload['name'])

        image_path = settings.MEDIA_ROOT + (p.image.url).replace('/media/', '')

        image =  Image.open(image_path)
        
        width , height = image.size
        
        self.assertEqual(width, 200)
        self.assertEqual(height, 200)
       
        # Check model url values
        self.assertEqual(
            p.image.url, 
            f'/media/images/products/{p.reg_no}_.jpg'
        )

    def test_if_view_wont_accept_an_image_if_its_not_jpeg_jpg_or_png(self):

        payload = self.get_premade_payload()

        gif_image_name = 'animated-love-image-0187.gif'
        gif_image_path = settings.MEDIA_ROOT + gif_image_name
        
        gif_image =  Image.open(gif_image_path)
        
        width , height = gif_image.size

        self.assertEqual(width, 240)
        self.assertEqual(height, 320)

        # Send data
        with open(gif_image_path, 'rb') as my_image:
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:tp_product_edit', 
                args=(self.product.reg_no,)), 
                payload
            )

            self.assertEqual(response.status_code, 400)
            
        result = {'error': 'Allowed image extensions are .jpg, .jpeg and .png'}
        self.assertEqual(response.data, result)

    def test_if_view_wont_accept_a_non_image_file(self):

        payload = self.get_premade_payload()

        bad_file__name = 'bad_file_extension.py'
        bad_file_path = settings.MEDIA_ROOT + bad_file__name

        # Send data
        with open(bad_file_path, 'rb') as my_image:
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:tp_product_edit', 
                args=(self.product.reg_no,)), 
                payload
            )

            self.assertEqual(response.status_code, 400)
            
        result = {
            'uploaded_image': [
                'Upload a valid image. The file you uploaded was either not an image or a corrupted image.'
                ]
            }
        self.assertEqual(response.data, result)

    def test_if_view_url_can_throttle_post_requests(self):

        payload = self.get_premade_payload()

        throttle_rate = int(settings.THROTTLE_RATES['api_product_rate'].split("/")[0])
    
        for i in range(throttle_rate): # pylint: disable=unused-variable

            payload['name'] = f'product{i}' # This makes the name unique
    
            response = self.client.put(
                reverse('api:tp_product_edit', 
                args=(self.product.reg_no,)), 
                payload,
            )
            self.assertEqual(response.status_code, 200)


        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional 
        # request if the previous request was not throttled 
        for i in range(throttle_rate): # pylint: disable=unused-variable

            # Try to see if the next request will be throttled
            payload['name'] = f'product{i}' # This makes the name unique
    
            response = self.client.put(
                reverse('api:tp_product_edit', 
                args=(self.product.reg_no,)), 
                payload,
            )

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else: 
            # Executed because break was not called. This means the request was
            # never throttled 
            self.fail()

    def test_if_view_cant_be_viewed_by_an_employee_user(self):

        # Login a employee profile #
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()
    
        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 401)

class TpProductEditViewForEditingWithBundleTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')
        self.tax2 = create_new_tax(self.top_profile1, self.store1, 'New Standard')

        # Create a category
        self.category = create_new_category(self.top_profile1, 'Hair')
        self.category2 = create_new_category(self.top_profile1, 'Face')

        self.create_master_product()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_single_product(self):
        
        # Create a products
        # ------------------------------ Product 1
        self.product = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        )

        # Update stock units for store 1 and 2
        stock = StockLevel.objects.get(product=self.product, store=self.store1)
        stock.units = 100
        stock.save()

    def create_master_product(self):

        self.create_single_product()

        product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Comb",
            price=750,
            cost=120,
            sku='sku1',
            barcode='code123'
        )

        product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Clip",
            price=2800,
            cost=1200,
            barcode='code123'
        )
   
        # Create master product with 2 bundles
        comb_bundle = ProductBundle.objects.create(
            product_bundle=product1,
            quantity=30
        )

        clip_bundle = ProductBundle.objects.create(
            product_bundle=product2,
            quantity=25
        )

        self.product.bundles.add(clip_bundle, comb_bundle)


    def get_premade_payload(self):
        """
        Simplifies creating payload
        """

        bundles = Product.objects.filter(productbundle__product=self.product
        ).order_by('id')

        payload = {
            'color_code': '#000000',
            'name': 'Gel', 
            'cost': 3100,
            'price': 1800,
            'sku': 'sku1_edit',
            'barcode': 'code123_edit',
            'sold_by_each': False,
            'show_product': False,
            'show_image': True,

            'tax_reg_no': self.tax2.reg_no,
            'category_reg_no': self.category2.reg_no,
            'bundles_info': [
                {"reg_no": bundles[0].reg_no, 'quantity': 40, 'is_dirty': True}, 
                {"reg_no": bundles[1].reg_no, 'quantity': 54, 'is_dirty': True}, 
            ],
            'modifiers_info': [],
            'variants_info': [],
            'stores_info': [
                {
                    'is_sellable': True, 
                    'price': 1800,
                    'reg_no': self.store1.reg_no,
                    'is_dirty': True

                },
                {
                    'is_sellable': True, 
                    'price': 1200,
                    'reg_no': self.store2.reg_no,
                    'is_dirty': True
                } 
            ]
        }

        return payload

    def test_if_view_can_edit_a_product(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        #with self.assertNumQueries(28):
        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 200)

        """
        Ensure a product has the right fields after it has been edited
        """
        p = Product.objects.get(name=payload['name'])
        self.assertEqual(p.bundles.all().count(), 2)

        # Confirm bundles
        p_bundles = Product.objects.filter(productbundle__product=self.product
        ).order_by('id')
        bundles = ProductBundle.objects.filter(product=self.product).order_by('id')
           
        i=0
        for bundle in bundles:
            self.assertEqual(bundle.quantity, payload['bundles_info'][i]['quantity'])
            self.assertEqual(bundle.product_bundle, p_bundles[i])

            i+=1

        # Confirm stock levels were updated
        stock_levels = StockLevel.objects.filter(product=self.product).order_by('id')
        self.assertEqual(stock_levels.count(), 2)

        # Stock level 1
        self.assertEqual(stock_levels[0].store, self.store1)
        self.assertEqual(stock_levels[0].units, Decimal('100.00'))
        self.assertEqual(stock_levels[0].price, Decimal('1800.00'))
        self.assertEqual(stock_levels[0].is_sellable, True)

        # Stock level 2
        self.assertEqual(stock_levels[1].store, self.store2)
        self.assertEqual(stock_levels[1].units, Decimal('0.00'))
        self.assertEqual(stock_levels[1].price, Decimal('1200.00'))
        self.assertEqual(stock_levels[1].is_sellable, True)

    def test_if_a_bundle_cant_be_edited_with_an_empty_name(self):

        payload = self.get_premade_payload()

        payload['bundles_info'][0]['reg_no'] = ''

        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 400)
        
        self.assertEqual(
            json.loads(json.dumps(response.data)),
            {'bundles_info': {'0': {'reg_no': ['A valid integer is required.']}}}
        )

        # Check if change was not made
        self.assertEqual(Product.objects.filter(name='Shampoo').exists(), True)

    def test_if_a_bundle_cant_be_edited_with_an_empty_price(self):

        payload = self.get_premade_payload()

        payload['bundles_info'][0]['quantity'] = ''

        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 400)
        
        self.assertEqual(
            json.loads(json.dumps(response.data)),
            {'bundles_info': {'0': {'quantity': ['A valid integer is required.']}}}
        )

        # Check if change was not made
        self.assertEqual(Product.objects.filter(name='Shampoo').exists(), True)

    def test_if_view_can_handle_a_bundle_with_a_wrong_reg_no(self):

        # Create a product for another user
        product = Product.objects.create(
            profile=self.top_profile2,
            name="New product",
            price=2800,
            cost=1200,
            barcode='code123'
        )
    
        wrong_reg_nos = [
            7878787, # Wrong reg no,
            product.reg_no,# Product from another user
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        payload = self.get_premade_payload()

        i=0
        for wrong_reg_no in wrong_reg_nos:

            payload['bundles_info'][0]['reg_no'] = wrong_reg_no

            response = self.client.put(
                reverse('api:tp_product_edit', args=(self.product.reg_no,)), 
                payload,
            )
            self.assertEqual(response.status_code, 400)

            if i==2:
                self.assertEqual(
                    json.loads(json.dumps(response.data)),
                    {'bundles_info': {'0': {'reg_no': ['You provided wrong stores']}}}
                )

            else:
                self.assertEqual(
                    json.loads(json.dumps(response.data)),
                    {'non_field_errors': 'Bundle error.'}

                )

            i+=1

            # Check if change was not made
            self.assertEqual(Product.objects.filter(name='Shampoo').exists(), True)

    def test_if_a_bundle_wont_be_edited_if_its_is_dirty_is_true(self):

        payload = self.get_premade_payload()

        payload['bundles_info'][0]['is_dirty'] = False

        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 200)
        
        # Check if change was made
        product = Product.objects.get(name=payload['name'])

        bundles = ProductBundle.objects.filter(product=product).order_by('id')

        # Check if the first bundle was the only one not updated
        self.assertEqual(bundles[0].quantity, 30)

        self.assertEqual(bundles[1].quantity, payload['bundles_info'][1]['quantity'])

    def test_view_can_remove_bundles_from_product(self):

        # Confirm bundle count
        self.assertEqual(self.product.bundles.all().count(), 2)

        payload = self.get_premade_payload()
        payload['bundles_info'] = [payload['bundles_info'][0]]

        # Count Number of Queries
        #with self.assertNumQueries(28):
        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 200)

        # Confirm 1 bundle were removed
        p_bundles = Product.objects.filter(productbundle__product=self.product
        ).order_by('id')
        bundles = ProductBundle.objects.filter(product=self.product).order_by('id')

        self.assertEqual(p_bundles.count(), 1)
        self.assertEqual(bundles.count(), 1)

        i=0
        for bundle in bundles:
            self.assertEqual(bundle.quantity, payload['bundles_info'][i]['quantity'])
            self.assertEqual(bundle.product_bundle, p_bundles[i])

            i+=1
    
    def test_view_can_add_a_bundle_and_remove_another_at_the_same_time1(self):
        """
        Tests if 1 bundle can be removed and replaced while 1 bundle is just 
        edited
        """

        # Create new product
        product3 = Product.objects.create(
            profile=self.top_profile1,
            name="New product",
            price=2800,
            cost=1200,
            barcode='code123'
        )
  
        payload = self.get_premade_payload()
        payload['bundles_info'][1] = {
            "reg_no": product3.reg_no, 'quantity': 77, 'is_dirty': True
        }

        # Count Number of Queries
        #with self.assertNumQueries(28):
        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 200)

        # Confirm 1 bundle was removed and 1 more addedd
        p_bundles = Product.objects.filter(productbundle__product=self.product
        ).order_by('id')
        bundles = ProductBundle.objects.filter(product=self.product).order_by('id')

        self.assertEqual(p_bundles.count(), 2)
        self.assertEqual(bundles.count(), 2)

     
        p_bundles = Product.objects.filter(productbundle__product=self.product
        ).order_by('id')
        bundles = ProductBundle.objects.filter(product=self.product).order_by('id')

        self.assertEqual(p_bundles.count(), 2)
        self.assertEqual(bundles.count(), 2)

        i=0
        for bundle in bundles:
            self.assertEqual(bundle.quantity, payload['bundles_info'][i]['quantity'])
            self.assertEqual(bundle.product_bundle, p_bundles[i])

            i+=1


        self.assertEqual(
            ProductBundle.objects.filter(product_bundle__name='Comb').exists(), True)
        self.assertEqual(
            ProductBundle.objects.filter(product_bundle__name='Clip').exists(), False)
        self.assertEqual(
            ProductBundle.objects.filter(product_bundle__name='New product').exists(), True)

    def test_view_can_add_a_bundle_and_remove_another_at_the_same_time2(self):

        """
        Tests if all bundles can be removed and replaced with new ones
        """

        # Create 2 new products
        product3 = Product.objects.create(
            profile=self.top_profile1,
            name="New product1",
            price=2800,
            cost=1200,
            barcode='code123'
        )
    
        product4 = Product.objects.create(
            profile=self.top_profile1,
            name="New product2",
            price=2800,
            cost=1200,
            barcode='code123'
        )
   
        payload = self.get_premade_payload()
        payload['bundles_info'][1] = {
            "reg_no": product3.reg_no, 'quantity': 77, 'is_dirty': True
        }

        payload['bundles_info'] = [
            {"reg_no": product3.reg_no, 'quantity': 77, 'is_dirty': True},
            {"reg_no": product4.reg_no, 'quantity': 100, 'is_dirty': True}
        ]

        # Count Number of Queries
        #with self.assertNumQueries(28):
        response = self.client.put(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 200)

        # Confirm 1 bundle was removed and 1 more addedd
        p_bundles = Product.objects.filter(productbundle__product=self.product
        ).order_by('id')
        bundles = ProductBundle.objects.filter(product=self.product).order_by('id')

        self.assertEqual(p_bundles.count(), 2)
        self.assertEqual(bundles.count(), 2)

     
        p_bundles = Product.objects.filter(productbundle__product=self.product
        ).order_by('id')
        bundles = ProductBundle.objects.filter(product=self.product).order_by('id')

        self.assertEqual(p_bundles.count(), 2)
        self.assertEqual(bundles.count(), 2)

        i=0
        for bundle in bundles:
            self.assertEqual(bundle.quantity, payload['bundles_info'][i]['quantity'])
            self.assertEqual(bundle.product_bundle, p_bundles[i])

            i+=1


        self.assertEqual(
            ProductBundle.objects.filter(product_bundle__name='Comb').exists(), False)
        self.assertEqual(
            ProductBundle.objects.filter(product_bundle__name='Clip').exists(), False)
        self.assertEqual(
            ProductBundle.objects.filter(product_bundle__name='New product1').exists(), True)
        self.assertEqual(
            ProductBundle.objects.filter(product_bundle__name='New product1').exists(), True)

class TpProductEditViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')
        self.tax2 = create_new_tax(self.top_profile1, self.store2, 'New Standard')

        # Create a category
        self.category = create_new_category(self.top_profile1, 'Hair')
        self.category2 = create_new_category(self.top_profile1, 'Face')

        self.create_single_product()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_single_product(self):

        # Create a products
        # ------------------------------ Product 1
        self.product = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        )

    def test_if_view_can_delete_a_product(self):

        response = self.client.delete(
            reverse('api:tp_product_edit',args=(self.product.reg_no,))
        )

        self.assertEqual(response.status_code, 204)

        # Confirm the product was soft deleted
        self.assertEqual(
            Product.objects.get(reg_no=self.product.reg_no).is_deleted, 
            True
        )

    def test_firebase_messages_are_sent_correctly(self):

        content = get_test_firebase_sender_log_content(only_include=['product'])
        self.assertEqual(len(content), 0)

        response = self.client.delete(
            reverse('api:tp_product_edit',args=(self.product.reg_no,))
        )

        self.assertEqual(response.status_code, 204)

        content = get_test_firebase_sender_log_content(only_include=['product'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': '', 
                'relevant_stores': '[]', 
                'model': 'product', 
                'action_type': 'delete', 
                'reg_no': str(self.product.reg_no),
            }
        }

        self.assertEqual(content[0], result)

    def test_if_view_can_handle_a_wrong_product_reg_no(self):

        wrong_reg_nos = [
            7878787,  # Wrong reg no,
            445464666666666666666666666666666666666666666666666666666,  # long reg no
        ]

        for wrong_reg_no in wrong_reg_nos:
            response = self.client.delete(
                reverse('api:tp_product_edit', args=(wrong_reg_no,))
            )

            self.assertEqual(response.status_code, 404)

        # Confirm the product was not deleted
        self.assertEqual(
            Product.objects.get(reg_no=self.product.reg_no).is_deleted, 
            False
        )

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:tp_product_edit', 
            args=(self.product.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the product was not deleted
        self.assertEqual(
            Product.objects.get(reg_no=self.product.reg_no).is_deleted, 
            False
        )

    # def test_view_cant_be_deleted_by_an_employee_user(self):

    #     # Login a employee user
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     response = self.client.delete(
    #         reverse('api:tp_product_edit', args=(self.product.reg_no,))
    #     )
    #     self.assertEqual(response.status_code, 404)

    #     # Confirm the product was not deleted
    #     self.assertEqual(Product.objects.filter(
    #         reg_no=self.product.reg_no).exists(), True
    #     )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:tp_product_edit', args=(self.product.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

        # Confirm the product was not deleted
        self.assertEqual(
            Product.objects.get(reg_no=self.product.reg_no).is_deleted, 
            False
        )


class ProductMapIndexViewForCreatingTestCase(APITestCase, InitialUserDataMixin):

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

        self.create_2_normal_products()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_2_normal_products(self):

        self.product1 = Product.objects.create(
            profile=self.top_profile1,
            name="Sack",
            price=650,
            cost=130,
            sku='sku1',
            barcode='code123',
        )

        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            name="Comb",
            price=750,
            cost=120,
            barcode='code123',
        )

        self.product3 = Product.objects.create(
            profile=self.top_profile1,
            name="Clip",
            price=2800,
            cost=1200,
            barcode='code123'
        )

    def login_user(self, email):

        # Login a top user
        token = Token.objects.get(user__email=email)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """

        payload = {
            'reg_no': self.product1.reg_no,
            'map_info': [
                {"reg_no": self.product2.reg_no, 'quantity': 30, 'is_dirty': True}, 
                {'reg_no': self.product3.reg_no, 'quantity': 54, 'is_dirty': True},
            ]
        }

        return payload
    
    def test_if_view_can_create_a_bundle_product_for_owner_and_employee(self):

        emails = [
            'john@gmail.com', # Owner
            'gucci@gmail.com' # Employe
        ]

        for email in emails:

            # We delete models for each loop
            ProductProductionMap.objects.all().delete()

            # Login user
            self.login_user(email)

            # Perform request
            payload = self.get_premade_payload()

            response = self.client.post(reverse('api:product_map_index'), payload)
            self.assertEqual(response.status_code, 201)

            # Confirm product productions
            product_maps = Product.objects.get(
                reg_no=self.product1.reg_no
            ).productions.all().order_by('id')
            
            self.assertEqual(product_maps.count(), 2)

            # Product map 1
            self.assertEqual(product_maps[0].product_map, self.product2)
            self.assertEqual(product_maps[0].quantity, 30)

            # Product map 2
            self.assertEqual(product_maps[1].product_map, self.product3)
            self.assertEqual(product_maps[1].quantity, 54)

    def test_if_a_product_bundle_cant_be_created_with_a_wrong_product_reg_no(self):

        # Create a product for another user
        product = Product.objects.create(
            profile=self.top_profile2,
            name="New product",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        wrong_stores_reg_nos = [
            'aaaa',  # Non numeric
            '1010',  # Wrong reg no
            product.reg_no,# Product from another user
            333333333333333333333333333333333333333333333  # Extremely long
        ]

        payload = self.get_premade_payload()

        i=0
        for wrong_reg_no in wrong_stores_reg_nos:
            payload['map_info'] = [
                {"reg_no":wrong_reg_no, 'quantity': 30, 'is_dirty': True}, 
            ]

            response = self.client.post(reverse('api:product_map_index'), payload)
            self.assertEqual(response.status_code, 400)

            if i == 0:
                self.assertEqual(
                    json.loads(json.dumps(response.data)), 
                    {'map_info': {'0': {'reg_no': ['A valid integer is required.']}}}
                )
            elif i == 3:
                self.assertEqual(
                    json.loads(json.dumps(response.data)), 
                    {'map_info': {'0': {'reg_no': ['You provided wrong stores']}}}
                )

            else:
                self.assertEqual(
                    response.data, 
                    {'non_field_errors': 'Product map error.'}
                )
                
            # Confirm product maps were not created
            self.assertEqual(ProductProductionMap.objects.all().count(), 0)

            i+=1

    def test_if_an_proudct_cant_be_created_with_an_empty_bundle_info_info(self):

        payload = self.get_premade_payload()

        payload['map_info'] = ''

        response = self.client.post(reverse('api:product_map_index'), payload)
        self.assertEqual(response.status_code, 400)

        error = {'map_info': ['Expected a list of items but got type "str".']}
    
        self.assertEqual(response.data, error)

        # Confirm product map were not created
        self.assertEqual(ProductProductionMap.objects.all().count(), 0)

    def test_if_a_product_cant_be_created_with_an_empty_bundle_reg_no(self):

        payload = self.get_premade_payload()
   
        payload['map_info'] = [
            {"reg_no": '', 'quantity': 30, 'is_dirty': True}
        ]

        response = self.client.post(reverse('api:product_map_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'map_info': {'0': {'reg_no': ['A valid integer is required.']}}}
        )

        # Confirm product map were not created
        self.assertEqual(ProductProductionMap.objects.all().count(), 0)

    def test_if_a_product_cant_be_created_with_an_empty_bundle_quantity(self):

        payload = self.get_premade_payload()
   
        payload['map_info'] = [
            {"reg_no": self.product2.reg_no, 'quantity': '', 'is_dirty': True}
        ]

        response = self.client.post(reverse('api:product_map_index'), payload)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            json.loads(json.dumps(response.data)), 
            {'map_info': {'0': {'quantity': ['A valid integer is required.']}}}
        )

        # Confirm new product map was not created
        self.assertEqual(ProductProductionMap.objects.all().count(), 0)

    def test_view_cant_be_created_by_a_bad_owner_and_employee(self):

        emails = [
            'jack@gmail.com',  # Bad owner
            'cristiano@gmail.com' # Bad employee
        ]

        for email in emails:
            # Login user
            self.login_user(email)

            payload = self.get_premade_payload()

            response = self.client.post(reverse('api:product_map_index'), payload)
            self.assertEqual(response.status_code, 404)

            # Confirm new product map was not created
            self.assertEqual(ProductProductionMap.objects.all().count(), 0)

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.post(reverse('api:product_map_index'), payload)
        self.assertEqual(response.status_code, 401)

        # Confirm new product map was not created
        self.assertEqual(ProductProductionMap.objects.all().count(), 0)


class ProductMapEditViewForViewingTestCase(APITestCase, InitialUserDataMixin):
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

        # Create test products
        self.create_master_product()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name="main")
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email="john@gmail.com")
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    def login_user(self, email):

        # Login a top user
        token = Token.objects.get(user__email=email)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        self.add_can_view_items_perm()

    def add_can_view_items_perm(self):

        owner_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Manager',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_items')

        owner_group.permissions.add(permission)
        manager_group.permissions.add(permission)

    def create_master_product(self):
        # ------------------------------ Product 1
        self.master_product = Product.objects.create(
            profile=self.top_profile1,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku="sku1",
            barcode="code123",
        )

        self.product1 = Product.objects.create(
            profile=self.top_profile1,
            name="Comb",
            price=750,
            cost=120,
            sku="sku1",
            barcode="code123",
        )

        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            name="Clip",
            price=2800,
            cost=1200,
            barcode="code123",
        )
    
        # Create master product with 2 bundles
        comb_bundle = ProductProductionMap.objects.create(
            product_map=self.product1, 
            quantity=30
        )

        clip_bundle = ProductProductionMap.objects.create(
            product_map=self.product2, 
            quantity=25
        )

        self.master_product.productions.add(
            clip_bundle, 
            comb_bundle
        )

    def test_view_can_be_called_successefully(self):
        """
        Test's product with all stores
        """

        emails = [
            'john@gmail.com', # Owner
            'gucci@gmail.com' # Employe
        ]

        for email in emails:

            # Login user
            self.login_user(email)

            # with self.assertNumQueries(5):
            response = self.client.get(
                reverse(
                    "api:tp_product_map_edit", 
                    args=(self.master_product.reg_no,)
                )
            )
            self.assertEqual(response.status_code, 200)

            product = Product.objects.get(name="Shampoo")

            result = {
                "name": product.name,
                "map_data": product.get_product_view_production_data(), 
            }
            self.assertEqual(response.data, result)

    # def test_view_cant_be_created_by_a_bad_owner_and_employee(self):

    #     emails = [
    #         'jack@gmail.com',  # Bad owner
    #         'cristiano@gmail.com' # Bad employee
    #     ]

    #     for email in emails:
    #         # Login user
    #         self.login_user(email)

    #         response = self.client.get(
    #             reverse(
    #                 "api:tp_product_map_edit", 
    #                 args=(self.master_product.reg_no,)
    #             )
    #         )
    #         self.assertEqual(response.status_code, 404)

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse(
                "api:tp_product_map_edit", 
                args=(self.master_product.reg_no,)
            )
        )
        self.assertEqual(response.status_code, 401)

class ProductMapEditViewForEditingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')
        self.tax2 = create_new_tax(self.top_profile1, self.store1, 'New Standard')

        # Create a category
        self.category = create_new_category(self.top_profile1, 'Hair')
        self.category2 = create_new_category(self.top_profile1, 'Face')

        self.create_master_product()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        self.add_can_view_items_perm()

    def login_user(self, email):

        # Login a top user
        token = Token.objects.get(user__email=email)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def add_can_view_items_perm(self):

        owner_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Owner',
        )

        manager_group = UserGroup.objects.get(
            master_user=self.top_profile1.user, 
            ident_name='Manager',
        )

        # Get the permission you want to remove
        permission = Permission.objects.get(codename='can_view_items')

        owner_group.permissions.add(permission)
        manager_group.permissions.add(permission)

    def create_single_product(self):
        
        # Create a products
        # ------------------------------ Product 1
        self.product = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        )

    def create_master_product(self):

        self.create_single_product()

        product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Comb",
            price=750,
            cost=120,
            sku='sku1',
            barcode='code123'
        )

        product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Clip",
            price=2800,
            cost=1200,
            barcode='code123'
        )
   
        # Create master product with 2 bundles
        comb_bundle = ProductProductionMap.objects.create(
            product_map=product1,
            quantity=30
        )

        clip_bundle = ProductProductionMap.objects.create(
            product_map=product2,
            quantity=25
        )

        self.product.productions.add(clip_bundle, comb_bundle)


    def get_premade_payload(self):
        """
        Simplifies creating payload
        """

        bundles = Product.objects.filter(productproductionmap__product=self.product
        ).order_by('id')

        payload = {
            'map_info': [
                {
                    "reg_no": bundles[0].reg_no, 
                    'quantity': 40, 
                    'is_auto_repackage': False,
                    'is_dirty': True
                }, 
                {
                    "reg_no": bundles[1].reg_no, 
                    'quantity': 54, 
                    'is_auto_repackage': True,
                    'is_dirty': True
                }, 
            ]
        }

        return payload

    def test_if_view_can_edit_a_product(self):

        emails = [
            'john@gmail.com', # Owner
            'gucci@gmail.com' # Employe
        ]

        for email in emails:

            # Login user
            self.login_user(email)

            payload = self.get_premade_payload()

            # Count Number of Queries
            #with self.assertNumQueries(28):
            response = self.client.put(
                reverse('api:tp_product_map_edit', 
                args=(self.product.reg_no,)), 
                payload,
            )

            self.assertEqual(response.status_code, 200)
            """
            Ensure a product has the right fields after it has been edited
            """
            p = Product.objects.get(reg_no=self.product.reg_no)
            self.assertEqual(p.productions.all().count(), 2)

            # Confirm production maps
            p_productions = Product.objects.filter(productproductionmap__product=self.product
            ).order_by('id')
            productions = ProductProductionMap.objects.filter(product=self.product).order_by('id')
            
            i=0
            for product_map in productions:
                self.assertEqual(product_map.quantity, payload['map_info'][i]['quantity'])
                self.assertEqual(product_map.is_auto_repackage, payload['map_info'][i]['is_auto_repackage'])
                self.assertEqual(product_map.product_map, p_productions[i])

                i+=1

    def test_if_a_product_map_cant_be_edited_with_an_empty_reg_no(self):

        payload = self.get_premade_payload()

        payload['map_info'][0]['reg_no'] = ''

        response = self.client.put(
            reverse('api:tp_product_map_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 400)
        
        self.assertEqual(
            json.loads(json.dumps(response.data)),
            {'map_info': {'0': {'reg_no': ['A valid integer is required.']}}}
        )

    def test_if_a_product_map_cant_be_edited_with_an_empty_quantity(self):

        payload = self.get_premade_payload()

        payload['map_info'][0]['quantity'] = ''

        response = self.client.put(
            reverse('api:tp_product_map_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 400)
        
        self.assertEqual(
            json.loads(json.dumps(response.data)),
            {'map_info': {'0': {'quantity': ['A valid integer is required.']}}}
        )

    def test_if_view_can_handle_a_production_map_with_a_wrong_reg_no(self):

        # Create a product for another user
        product = Product.objects.create(
            profile=self.top_profile2,
            name="New product",
            price=2800,
            cost=1200,
            barcode='code123'
        )
    
        wrong_reg_nos = [
            7878787, # Wrong reg no,
            product.reg_no,# Product from another user
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        payload = self.get_premade_payload()

        i=0
        for wrong_reg_no in wrong_reg_nos:

            payload['map_info'][0]['reg_no'] = wrong_reg_no

            response = self.client.put(
                reverse('api:tp_product_map_edit', args=(self.product.reg_no,)), 
                payload,
            )
            self.assertEqual(response.status_code, 400)

            if i==2:
                self.assertEqual(
                    json.loads(json.dumps(response.data)),
                    {'map_info': {'0': {'reg_no': ['You provided wrong stores']}}}
                )

            else:
                self.assertEqual(
                    json.loads(json.dumps(response.data)),
                    {'non_field_errors': 'Product map error.'}
                )

            i+=1

    def test_if_a_bundle_wont_be_edited_if_its_is_dirty_is_true(self):

        payload = self.get_premade_payload()

        payload['map_info'][0]['is_dirty'] = False

        response = self.client.put(
            reverse('api:tp_product_map_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 200)
        
        # Check if change was made
        product = Product.objects.get(reg_no=self.product.reg_no)

        production_map = ProductProductionMap.objects.filter(product=product).order_by('id')

        # Check if the first bundle was the only one not updated
        self.assertEqual(production_map[0].quantity, 30)

        self.assertEqual(production_map[1].quantity, payload['map_info'][1]['quantity'])

    def test_view_can_remove_product_maps_from_product(self):

        # Confirm product map count
        self.assertEqual(self.product.productions.all().count(), 2)

        payload = self.get_premade_payload()
        payload['map_info'] = [payload['map_info'][0]]

        # Count Number of Queries
        #with self.assertNumQueries(28):
        response = self.client.put(
            reverse('api:tp_product_map_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 200)

        # Confirm 1 product map were removed
        mapped_product = Product.objects.filter(productproductionmap__product=self.product
        ).order_by('id')
        product_maps = ProductProductionMap.objects.filter(product=self.product).order_by('id')

        self.assertEqual(mapped_product.count(), 1)
        self.assertEqual(product_maps.count(), 1)

        i=0
        for product_map in product_maps:
            self.assertEqual(product_map.quantity, payload['map_info'][i]['quantity'])
            self.assertEqual(product_map.product_map, mapped_product[i])

            i+=1

    def test_view_can_add_a_product_map_and_remove_another_at_the_same_time1(self):
        """
        Tests if 1 product map can be removed and replaced while 1 bundle is just 
        edited
        """

        # Create new product
        product3 = Product.objects.create(
            profile=self.top_profile1,
            name="New product",
            price=2800,
            cost=1200,
            barcode='code123'
        )
  
        payload = self.get_premade_payload()
        payload['map_info'][1] = {
            "reg_no": product3.reg_no, 
            'quantity': 77,
            'is_auto_repackage': False, 
            'is_dirty': True
        }

        # Count Number of Queries
        #with self.assertNumQueries(28):
        response = self.client.put(
            reverse('api:tp_product_map_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 200)

        # Confirm 1 product map was removed and 1 more added
        mapped_product = Product.objects.filter(productproductionmap__product=self.product
        ).order_by('id')
        product_maps = ProductProductionMap.objects.filter(product=self.product).order_by('id')

        self.assertEqual(mapped_product.count(), 2)
        self.assertEqual(product_maps.count(), 2)

     
        mapped_product = Product.objects.filter(productproductionmap__product=self.product
        ).order_by('id')
        product_maps = ProductProductionMap.objects.filter(product=self.product).order_by('id')

        self.assertEqual(mapped_product.count(), 2)
        self.assertEqual(product_maps.count(), 2)

        i=0
        for product_map in product_maps:
            self.assertEqual(product_map.quantity, payload['map_info'][i]['quantity'])
            self.assertEqual(product_map.is_auto_repackage, payload['map_info'][i]['is_auto_repackage'])
            self.assertEqual(product_map.product_map, mapped_product[i])

            i+=1

        self.assertEqual(
            ProductProductionMap.objects.filter(product_map__name='Comb').exists(), True)
        self.assertEqual(
            ProductProductionMap.objects.filter(product_map__name='Clip').exists(), False)
        self.assertEqual(
            ProductProductionMap.objects.filter(product_map__name='New product').exists(), True)

    def test_view_can_add_a_product_map_and_remove_another_at_the_same_time2(self):

        """
        Tests if all product maps can be removed and replaced with new ones
        """

        # Create 2 new products
        product3 = Product.objects.create(
            profile=self.top_profile1,
            name="New product1",
            price=2800,
            cost=1200,
            barcode='code123'
        )
    
        product4 = Product.objects.create(
            profile=self.top_profile1,
            name="New product2",
            price=2800,
            cost=1200,
            barcode='code123'
        )
   
        payload = self.get_premade_payload()
        payload['map_info'] = [
            {
                "reg_no": product3.reg_no, 
                'quantity': 77, 
                'is_auto_repackage': False,
                'is_dirty': True
            },
            {
                "reg_no": product4.reg_no, 
                'quantity': 100, 
                'is_auto_repackage': False,
                'is_dirty': True
            }
        ]

        # Count Number of Queries
        #with self.assertNumQueries(28):
        response = self.client.put(
            reverse('api:tp_product_map_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 200)

        # Confirm 1 product map was removed and 1 more addedd
        mapped_product = Product.objects.filter(productproductionmap__product=self.product
        ).order_by('id')
        product_maps = ProductProductionMap.objects.filter(product=self.product).order_by('id')

        self.assertEqual(mapped_product.count(), 2)
        self.assertEqual(product_maps.count(), 2)

     
        mapped_product = Product.objects.filter(productproductionmap__product=self.product
        ).order_by('id')
        product_maps = ProductProductionMap.objects.filter(product=self.product).order_by('id')

        self.assertEqual(mapped_product.count(), 2)
        self.assertEqual(product_maps.count(), 2)

        i=0
        for product_map in product_maps:
            self.assertEqual(product_map.quantity, payload['map_info'][i]['quantity'])
            self.assertEqual(product_map.product_map, mapped_product[i])

            i+=1

        self.assertEqual(
            ProductProductionMap.objects.filter(product_map__name='Comb').exists(), False)
        self.assertEqual(
            ProductProductionMap.objects.filter(product_map__name='Clip').exists(), False)
        self.assertEqual(
            ProductProductionMap.objects.filter(product_map__name='New product1').exists(), True)
        self.assertEqual(
            ProductProductionMap.objects.filter(product_map__name='New product1').exists(), True)

    # def test_view_cant_be_created_by_a_bad_owner_and_employee(self):

    #     emails = [
    #         'jack@gmail.com',  # Bad owner
    #         'cristiano@gmail.com' # Bad employee
    #     ]

    #     for email in emails:
    #         # Login user
    #         self.login_user(email)

    #         payload = self.get_premade_payload()

    #         response = self.client.put(
    #             reverse('api:tp_product_map_edit', 
    #             args=(self.product.reg_no,)), 
    #             payload,
    #         )
    #         self.assertEqual(response.status_code, 404)

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:tp_product_map_edit', 
            args=(self.product.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 401)

class ProductTransformIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        self.create_a_production_product()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_a_production_product(self):

        sugar_sack = Product.objects.create(
            profile=self.top_profile1,
            is_transformable=True,
            name="Sugar 50kg Sack",
            price=10000,
            cost=9000,
            barcode='code1'
        )
        
        pagackaged_sugar_1kg = Product.objects.create(
            profile=self.top_profile1,
            name="Packaged Sugar 1kg",
            price=200,
            cost=180,
            barcode='code3'
        )

        pagackaged_sugar_2kg = Product.objects.create(
            profile=self.top_profile1,
            name="Packaged Sugar 2kg",
            price=400,
            cost=360,
            barcode='code2'
        )
        
        # Create master product with 2 bundles
        pagackaged_sugar_2kg_map = ProductProductionMap.objects.create(
            name="Packaged Sugar 2kg",
            product_map=pagackaged_sugar_2kg,
            quantity=25
        )

        pagackaged_sugar_1kg_map = ProductProductionMap.objects.create(
            name="Packaged Sugar 1kg",
            product_map=pagackaged_sugar_1kg,
            quantity=50
        )

        sugar_sack.productions.add(pagackaged_sugar_1kg_map, pagackaged_sugar_2kg_map)

        # Master product stock levels
        stock_level = StockLevel.objects.get(store=self.store1, product=sugar_sack)
        stock_level.units = 34
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=sugar_sack)
        stock_level.units = 30
        stock_level.save()

        
        # Shampoo stock level
        stock_level = StockLevel.objects.get(store=self.store1, product=pagackaged_sugar_2kg)
        stock_level.units = 24
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=pagackaged_sugar_2kg)
        stock_level.units = 20
        stock_level.save()


        # Conditioner stock levels
        stock_level = StockLevel.objects.get(store=self.store1, product=pagackaged_sugar_1kg)
        stock_level.units = 14
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=pagackaged_sugar_1kg)
        stock_level.units = 10
        stock_level.save()

    def test_if_view_returns_the_products_for_single_store_correctly(self):

        # Count Number of Queries #
        # with self.assertNumQueries(12):
        response = self.client.get(
            reverse('api:product_transform_map_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        sugar_50_sack = Product.objects.get(name="Sugar 50kg Sack")
        pagackaged_sugar_2kg = Product.objects.get(name="Packaged Sugar 2kg")
        pagackaged_sugar_1kg = Product.objects.get(name="Packaged Sugar 1kg")

        result = {
            'count': 3, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'transform_data': {
                        'name': pagackaged_sugar_1kg.name, 
                        'reg_no': pagackaged_sugar_1kg.reg_no, 
                        'cost': '180.00', 
                        'current_quantity': '14.00', 
                        'is_reverse': True,
                        'product_map': [
                            {
                                'name': sugar_50_sack.name, 
                                'sku': '', 
                                'reg_no': sugar_50_sack.reg_no, 
                                'current_quantity': '34.00', 
                                'equivalent_quantity': '0.02'
                            }
                        ]
                    }
                }, 
                {
                    'transform_data': {
                        'name': pagackaged_sugar_2kg.name, 
                        'reg_no': pagackaged_sugar_2kg.reg_no, 
                        'cost': '360.00', 
                        'current_quantity': '24.00', 
                        'is_reverse': True,
                        'product_map': [
                            {
                                'name': sugar_50_sack.name, 
                                'sku': '', 
                                'reg_no': sugar_50_sack.reg_no, 
                                'current_quantity': '34.00', 
                                'equivalent_quantity': '0.04'
                            }
                        ]
                    }
                }, 
                {
                    'transform_data': {
                        'name': sugar_50_sack.name, 
                        'reg_no': sugar_50_sack.reg_no, 
                        'cost': '9000.00', 
                        'current_quantity': '34.00', 
                        'is_reverse': False,
                        'product_map': [
                            {
                                'name': 'Packaged Sugar 2kg', 
                                'sku': '', 
                                'reg_no': pagackaged_sugar_2kg.reg_no, 
                                'current_quantity': '24.00', 
                                'equivalent_quantity': '25'
                            },
                            {
                                'name': 'Packaged Sugar 1kg', 
                                'sku': '', 
                                'reg_no': pagackaged_sugar_1kg.reg_no, 
                                'current_quantity': '14.00', 
                                'equivalent_quantity': '50'
                            }, 
                            
                        ]
                    }
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
            reverse('api:product_transform_map_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)

    def test_if_products_without_product_maps_are_not_displayed(self):

        ProductProductionMap.objects.all().delete()

        response = self.client.get(
            reverse('api:product_transform_map_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_products(self):

        # First delete all products
        Product.objects.all().delete()

        response = self.client.get(
            reverse('api:product_transform_map_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_its_owner(self):

        # Login an employee user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:product_transform_map_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:product_transform_map_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)
