import base64
from decimal import Decimal
import json
from pprint import pprint
from PIL import Image

from django.conf import settings
from django.contrib.auth.models import Permission
from django.utils import timezone
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.create_product_models import create_new_product
from core.test_utils.create_product_variants import create_1d_variants
from core.test_utils.custom_testcase import APITestCase
from core.test_utils.initial_user_data import InitialUserDataMixin

from core.test_utils.create_store_models import (
    create_new_category,
    create_new_tax
)
from core.test_utils.log_reader import get_test_firebase_sender_log_content

from inventories.models import StockLevel

from mysettings.models import MySetting

from products.models import (
   Product,
    ProductBundle
)
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

        # Increase user's store count
        self.manager_profile1.stores.add(self.store2)

        # Create models
        self.create_categories()
        self.create_taxes()

        
        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
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

    def test_view_returns_the_user_models_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(9):
            response = self.client.get(
                reverse('api:ep_product_available_data'))
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

    def test_view_returns_empty_when_there_are_no_models(self):

        Tax.objects.all().delete()
        Category.objects.all().delete()
        Store.objects.all().delete()

        response = self.client.get(
            reverse('api:ep_product_available_data'))
        self.assertEqual(response.status_code, 200)

        result = {
            'taxes': [], 
            'categories': [], 
            'stores': []
        }

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_top_user(self):

        # Login a top user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:ep_product_available_data'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:ep_product_available_data'))
        self.assertEqual(response.status_code, 401)


class EpLeanProductIndexViewTestCase(APITestCase, InitialUserDataMixin):

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
        token = Token.objects.get(user__email='gucci@gmail.com')
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
        
        # We add another stock level for product by adding a new store
        product = Product.objects.get(name="Shampoo")
        
        # Confirm we have 2 stock levels
        self.assertEqual(StockLevel.objects.filter(product=product).count(), 2)

        # Count Number of Queries #
        #with self.assertNumQueries(12):
        response = self.client.get(reverse('api:ep_lean_product_index'))
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

        
        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:ep_lean_product_index'))
        self.assertEqual(response.status_code, 401)

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
        response = self.client.get(reverse('api:ep_lean_product_index') + param)
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

    def test_if_view_does_not_include_bundle_products(self):

        self.create_a_bundle_master_product()

        self.assertEqual(Product.objects.all().count(), 2)

        product = Product.objects.get(name="Shampoo")

        response = self.client.get(reverse('api:ep_lean_product_index'))
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

        self.assertEqual(response.data, result)

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
            v.track_stock = True
            v.save()

        variants = Product.objects.filter(
            productvariant__product=product).order_by('-name')

        response = self.client.get(reverse('api:ep_lean_product_index'))
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
        response = self.client.get(reverse('api:ep_lean_product_index'))
        self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/ep/products/lean/?page=2')
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
        response = self.client.get(reverse('api:ep_lean_product_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': 'http://testserver/api/ep/products/lean/', 
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

    def test_view_can_only_show_product_for_employee_registerd_stores(self):

        # Decrease user's store count
        self.manager_profile1.stores.remove(self.store1)

        response = self.client.get(reverse('api:ep_lean_product_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': []
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_products(self):

        # First delete all products
        Product.objects.all().delete()

        response = self.client.get(reverse('api:ep_lean_product_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': []
        }

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_a_top_user(self):

        # Login a top user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:ep_lean_product_index'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:ep_lean_product_index'))
        self.assertEqual(response.status_code, 401)


class EpProductIndexViewTestCase(APITestCase, InitialUserDataMixin):

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
        token = Token.objects.get(user__email='gucci@gmail.com')
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
        
        # We add another stock level for product by adding a new store
        product = Product.objects.get(name="Shampoo")
     
        # Confirm we have 2 stock levels
        self.assertEqual(StockLevel.objects.filter(product=product).count(), 2)

        # Count Number of Queries #
        #with self.assertNumQueries(12):
        response = self.client.get(reverse('api:ep_product_index'))
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

        self.assertEqual(response.data, result)


        
      
        
        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:ep_product_index'))
        self.assertEqual(response.status_code, 401)

    def test_if_view_returns_the_results_even_for_employee_without_add_permission(self):

        # Delete permissoin
        Permission.objects.filter(codename='can_manage_items').delete()
        
        response = self.client.get(reverse('api:ep_product_index'))
        self.assertEqual(response.status_code, 200)

    def test_view_when_proudct_does_not_have_category(self):

        # Remove category
        product = Product.objects.get(name="Shampoo")
        product.category = None
        product.save()

        response = self.client.get(
            reverse('api:ep_product_index'))
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

        self.assertEqual(response.data, result)

    def test_view_when_there_are_bundle_products(self):

        self.create_a_bundle_master_product()

        product1 = Product.objects.get(name="Shampoo")
        product2 = Product.objects.get(name="Hair Bundle")

        response = self.client.get(reverse('api:ep_product_index'))

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
        response = self.client.get(reverse('api:ep_product_index'))
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
        response = self.client.get(reverse('api:ep_product_index'))
        self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/ep/products/?page=2')
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
        response = self.client.get(reverse('api:ep_product_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': 'http://testserver/api/ep/products/', 
            'results': [
                {
                    'image_url': f'/media/images/products/{products[0].reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': products[0].name, 
                    'price': '2500.00', 
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

        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        # First delete all products
        Product.objects.all().delete()

        self.create_products_for_filter_test()
        self.assertEqual(Product.objects.all().count(), 3)

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = '?search=Gel'
        response = self.client.get(reverse('api:ep_product_index') + param)

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

    def test_view_can_only_show_product_for_employee_registerd_stores(self):

        product = Product.objects.get(name="Shampoo")
        
        # Decrease user's store count
        self.manager_profile1.stores.remove(self.store2)

        response = self.client.get(reverse('api:ep_product_index'))
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
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no
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
        response = self.client.get(reverse('api:ep_product_index') + param)

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
        response = self.client.get(reverse('api:ep_product_index') + param)

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

    def test_view_can_filter_all_stores(self):

        # First delete all products
        Product.objects.all().delete()

        self.create_products_for_filter_test()

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        response = self.client.get(reverse('api:ep_product_index'))

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
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_single_category(self):

        # First delete all products
        Product.objects.all().delete()

        self.create_products_for_filter_test()

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?category__reg_no={self.category1.reg_no}'
        response = self.client.get(reverse('api:ep_product_index') + param)

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
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)
    
    def test_view_can_filter_low_stock(self):

        # First delete all products
        Product.objects.all().delete()

        self.create_products_for_filter_test()

        # Update product 2 to be low in stock
        product2 = Product.objects.get(name='Comb')
        product2.track_stock = True
        product2.save()

        # We call save to update stock level's status
        stock = StockLevel.objects.get(product=product2, store=self.store1)
        stock.minimum_stock_level = 350
        stock.save()

        param = f'?stocklevel__status={StockLevel.STOCK_LEVEL_LOW_STOCK}'
        response = self.client.get(reverse('api:ep_product_index') + param)

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
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_out_of_stock(self):

        # First delete all products
        Product.objects.all().delete()

        self.create_products_for_filter_test()

        # Update product 3 to be out of stock
        product3 = Product.objects.get(name='Gel')
        product3.track_stock = True
        product3.minimum_stock_level = 100
        product3.save()

        # We call save to update stock level's status
        stock = StockLevel.objects.get(product=product3, store=self.store1)
        stock.units = 0
        stock.save()

        param = f'?stocklevel__status={StockLevel.STOCK_LEVEL_OUT_OF_STOCK}'
        response = self.client.get(reverse('api:ep_product_index') + param)

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
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_returns_empty_when_there_are_no_products(self):

        # First delete all products
        Product.objects.all().delete()

        response = self.client.get(reverse('api:ep_product_index'))
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

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_a_top_user(self):

        # Login a top user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:ep_product_index'))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:ep_product_index'))
        self.assertEqual(response.status_code, 401)


class EpProductIndexViewForCreatingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')

        # Create a category
        self.category = create_new_category(self.top_profile1, 'Hair')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
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
            'track_stock': True,
            'show_image': True,
            'tax_reg_no': self.tax.reg_no,
            'category_reg_no': self.category.reg_no,
             'bundles_info': [],
            'modifiers_info': [],
            'variants_info': [],
            'stores_info': [
                {
                    'is_sellable': True, 
                    'price': 1800,
                    'reg_no': self.store1.reg_no
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
            track_stock=True
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
        response = self.client.post(reverse('api:ep_product_index'), payload)
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
        self.assertEqual(p.track_stock, payload['track_stock'])
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
              
        response = self.client.post(reverse('api:ep_product_index'), payload)
            
        self.assertEqual(response.status_code, 401)


    def test_firebase_messages_are_sent_correctly(self):

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

        response = self.client.post(reverse('api:ep_product_index'), payload)
        self.assertEqual(response.status_code, 201)

        content = get_test_firebase_sender_log_content(only_include=['product'])
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

        self.assertEqual(content[0], result1)

    def test_if_a_product_cant_be_created_when_new_product_mode_is_off(self):

        payload = self.get_premade_payload()

        # Turn off signups mode
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.new_product = False
        ms.save()

        response = self.client.post(reverse('api:ep_product_index'), payload)
        self.assertEqual(response.status_code, 423)

        # Confirm product model was not created
        self.assertEqual(Product.objects.all().count(), 0)

    def test_if_a_product_cant_be_created_when_employee_has_no_permission(self):

        # Delete permissoin
        Permission.objects.filter(codename='can_manage_items').delete()

        payload = self.get_premade_payload()

        response = self.client.post(reverse('api:ep_product_index'), payload)
        self.assertEqual(response.status_code, 403)
    
    def test_if_view_can_only_create_a_product_with_store_that_belongs_to_the_user(self):

        # Decrease user's store count
        self.manager_profile1.stores.remove(self.store2)

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

        response = self.client.post(reverse('api:ep_product_index'), payload)  
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
        response = self.client.post(reverse('api:ep_product_index'), payload)
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
        response = self.client.post(reverse('api:ep_product_index'), payload)
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

        response = self.client.post(reverse('api:ep_product_index'), payload)

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

        response = self.client.post(reverse('api:ep_product_index'), payload)
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

        response = self.client.post(reverse('api:ep_product_index'), payload)
        
        self.assertEqual(response.status_code, 201)

        # Confirm product model creation
        self.assertEqual(Product.objects.all().count(), 2)

    def test_if_a_product_cant_be_created_with_an_empty_price(self):

        payload = self.get_premade_payload()

        payload['price'] = ''

        response = self.client.post(reverse('api:ep_product_index'), payload)
        
        self.assertEqual(response.status_code, 400)

        result = {'price': ['A valid number is required.']}

        self.assertEqual(response.data, result)

    def test_if_a_product_cant_be_created_with_an_empty_cost(self):

        payload = self.get_premade_payload()
  
        payload['cost'] = ''

        response = self.client.post(reverse('api:ep_product_index'), payload)
        
        self.assertEqual(response.status_code, 400)

        result = {'cost': ['A valid number is required.']}

        self.assertEqual(response.data, result)

    def test_if_a_product_can_be_created_with_an_empty_sku(self):

        payload = self.get_premade_payload()
   
        payload['sku'] = ''

        response = self.client.post(reverse('api:ep_product_index'), payload)
        
        self.assertEqual(response.status_code, 201)

        # Confirm product tax
        p = Product.objects.get(name=payload['name'])
        self.assertEqual(p.sku, '')

    def test_if_a_product_can_be_created_with_an_empty_barcode(self):

        payload = self.get_premade_payload()

        payload['barcode'] = ''

        response = self.client.post(reverse('api:ep_product_index'), payload)
        
        self.assertEqual(response.status_code, 201)

        # Confirm product tax
        p = Product.objects.get(name=payload['name'])
        self.assertEqual(p.barcode, '')

    def test_if_a_product_can_be_created_with_an_empty_tax(self):

        payload = self.get_premade_payload()

        payload['tax_reg_no'] = 0

        response = self.client.post(reverse('api:ep_product_index'), payload)
        
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

            response = self.client.post(reverse('api:ep_product_index'), payload)
            self.assertEqual(response.status_code, 201)

            # Confirm product tax
            p = Product.objects.get(name=payload['name'])
            self.assertEqual(p.tax, None)

    def test_if_a_product_can_be_created_with_an_empty_category(self):

        payload = self.get_premade_payload()

        payload['category_reg_no'] = 0

        response = self.client.post(reverse('api:ep_product_index'), payload)
        
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

            response = self.client.post(reverse('api:ep_product_index'), payload)
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

        response = self.client.post(reverse('api:ep_product_index'), payload)
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
        self.assertEqual(p.track_stock, True)
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

            response = self.client.post(reverse('api:ep_product_index'), payload)
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

        response = self.client.post(reverse('api:ep_product_index'), payload)
        self.assertEqual(response.status_code, 400)

        error = {'bundles_info': ['Expected a list of items but got type "str".']}
    
        self.assertEqual(response.data, error)

        # Confirm product were not created
        self.assertEqual(Product.objects.all().count(), 0)

    def test_if_a_product_can_be_created_with_an_empty_bundle_info_list(self):

        payload = self.get_premade_payload()
 
        payload['bundles_info'] = []

        response = self.client.post(reverse('api:ep_product_index'), payload)
        self.assertEqual(response.status_code, 201)

        # Confirm product were created
        p = Product.objects.get(name=payload['name'])
        self.assertEqual(p.bundles.all().count(), 0)

    def test_if_a_product_cant_be_created_with_an_empty_bundle_reg_no(self):

        payload = self.get_premade_payload()
   
        payload['bundles_info'] = [
            {"reg_no": '', 'quantity': 30, 'is_dirty': True}
        ]

        response = self.client.post(reverse('api:ep_product_index'), payload)
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

        response = self.client.post(reverse('api:ep_product_index'), payload)
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
        #response = self.client.post(reverse('api:ep_product_index'), payload)
        #self.assertEqual(response.status_code, 201)

        with open(self.full_path, 'rb') as my_image: 
 
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.post(reverse('api:ep_product_index'), payload)

        self.assertEqual(response.status_code, 201)

        # Confirm product models creation
        self.assertEqual(Product.objects.all().count(), 1)

        p = Product.objects.get(name='Shampoo')

        # Check model url values
        self.assertEqual(p.image.url, f'/media/images/products/{p.reg_no}_.jpg')

    def test_if_view_can_edit_an_image_with_the_right_dimensions(self):

        payload = self.get_premade_payload()

        # Send data
        with open(self.full_path, 'rb') as my_image:
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.post(reverse('api:ep_product_index'), payload)
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

            response = self.client.post(reverse('api:ep_product_index'), payload)
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

            response = self.client.post(reverse('api:ep_product_index'), payload)
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

            response = self.client.post(reverse('api:ep_product_index'), payload)

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

            response = self.client.post(reverse('api:ep_product_index'), payload)

            self.assertEqual(response.status_code, 400)
            
        result = {'uploaded_image': ['Upload a valid image. The file you uploaded was either not an image or a corrupted image.']}
        self.assertEqual(response.data, result)

    def test_if_view_url_can_throttle_post_requests(self):

        payload = self.get_premade_payload()

        throttle_rate = int(settings.THROTTLE_RATES['api_product_rate'].split("/")[0])
    
        for i in range(throttle_rate): # pylint: disable=unused-variable

            payload['name'] = f'product{i}' # This makes the name unique
    
            response = self.client.post(reverse('api:ep_product_index'), payload)
            self.assertEqual(response.status_code, 201)


        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional 
        # request if the previous request was not throttled 
        for i in range(throttle_rate): # pylint: disable=unused-variable

            # Try to see if the next request will be throttled
            payload['name'] = f'product{i}' # This makes the name unique
    
            response = self.client.post(reverse('api:ep_product_index'), payload)

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else: 
            # Executed because break was not called. This means the request was
            # never throttled 
            self.fail()

    def test_if_view_cant_be_viewed_by_a_top_user(self):

        # Login a employee profile #
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()
    
        response = self.client.post(reverse('api:ep_product_index'), payload)
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.post(reverse('api:ep_product_index'), payload)
        self.assertEqual(response.status_code, 401)

class EpProductEditViewForViewingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a tax
        self.tax1 = create_new_tax(self.top_profile1, self.store1, 'Standard')
        self.tax2 = create_new_tax(self.top_profile1, self.store2, 'New Standard')

        # Create a category
        self.category1 = create_new_category(self.top_profile1, 'Hair')
        self.category2 = create_new_category(self.top_profile1, 'Face')

        self.create_single_product()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

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
            sku='sku1',
            barcode='code123'
        )

        # ------------------------------ Product 2
        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category1,
            name="Conditioner",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        )

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product2,
            profile=self.top_profile1,
            store1=self.store1,
            store2=self.store2
        )

    def create_master_product(self):

        # ------------------------------ Product 1
        master_product = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category1,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        )

        product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category1,
            name="Comb",
            price=750,
            cost=120,
            sku='sku1',
            barcode='code123',
            track_stock=True
        )

        product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax1,
            category=self.category1,
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

        master_product.bundles.add(clip_bundle, comb_bundle)

    def test_view_can_be_called_successefully(self):
        """
        Test's product with all stores
        """
        # Count Number of Queries #
        # with self.assertNumQueries(5):
        response = self.client.get(
            reverse('api:ep_product_edit', args=(self.product1.reg_no,))
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
            'variant_data': product.get_product_view_variants_data(self.manager_profile1),
            'bundle_data': product.get_product_view_bundles_data(),
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
                    "price": "0.00",
                    "is_sellable": True,
                },
                {
                    "store_name": self.store1.name,
                    "store_reg_no": self.store1.reg_no,
                    "minimum_stock_level": "0",
                    "units": "0.00",
                    "price": "0.00",
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
        Test's product after 1 store has been removed
        """

        self.product1.stores.remove(self.store2)

        # Count Number of Queries #
        # with self.assertNumQueries(5):
        response = self.client.get(
            reverse('api:ep_product_edit', args=(self.product1.reg_no,))
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
            'variant_data': product.get_product_view_variants_data(self.manager_profile1),
            'bundle_data': product.get_product_view_bundles_data(),
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
                    "store_name": self.store1.name,
                    "store_reg_no": self.store1.reg_no,
                    "minimum_stock_level": "0",
                    "units": "0.00",
                    "price": "0.00",
                    "is_sellable": True,
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
        Test's product after all stores have been removed
        """

        self.product1.stores.remove(self.store1)
        self.product1.stores.remove(self.store2)

        response = self.client.get(
            reverse('api:ep_product_edit', args=(self.product1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    def test_view_can_be_called_successefully_with_variant_product(self):
        """
        Test's product with all stores
        """
        response = self.client.get(
            reverse('api:ep_product_edit', args=(self.product2.reg_no,))
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
            'variant_data': product.get_product_view_variants_data(self.manager_profile1),
            'bundle_data': product.get_product_view_bundles_data(),
            'registered_stores': [
                {
                    "store_name": self.store2.name,
                    "store_reg_no": self.store2.reg_no,
                    "minimum_stock_level": "0",
                    "units": "0.00",
                    "price": "0.00",
                    "is_sellable": True,
                },
                {
                    "store_name": self.store1.name,
                    "store_reg_no": self.store1.reg_no,
                    "minimum_stock_level": "0",
                    "units": "0.00",
                    "price": "0.00",
                    "is_sellable": True,
                }
            ],
            "available_taxes": [
                {"name": self.tax2.name, "reg_no": self.tax2.reg_no},
                {"name": self.tax1.name, "reg_no": self.tax1.reg_no},
            ],
            "available_categories": [
                {"name": self.category2.name, "reg_no": self.category2.reg_no},
                {"name": self.category1.name, "reg_no": self.category1.reg_no},
            ],
            "available_stores": [
                {"name": self.store2.name, "reg_no": self.store2.reg_no},
                {"name": self.store1.name, "reg_no": self.store1.reg_no},
            ],
        }

        self.assertEqual(response.data, result)

        # Confirm variants
        variant_data = response.data['variant_data']
        self.assertEqual(len(variant_data), 3)

        for variant in variant_data:
            self.assertEqual(len(variant['registered_stores']), 2)
            self.assertEqual(
                variant['registered_stores'][1]['store_name'],
                self.store1.name
            )
            self.assertEqual(
                variant['registered_stores'][0]['store_name'],
                self.store2.name
            )

    def test_view_can_be_called_successefully_with_bundle_product(self):
        
        Product.objects.all().delete()

        self.create_master_product()

        product = Product.objects.get(name='Shampoo')

        #print(product.get_product_view_bundles_data()
        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.get(
            reverse('api:ep_product_edit', args=(product.reg_no,))
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
                {"name": self.tax2.name, "reg_no": self.tax2.reg_no},
                {"name": self.tax1.name, "reg_no": self.tax1.reg_no},
            ], 
            'available_categories': [
                {"name": self.category2.name, "reg_no": self.category2.reg_no},
                {"name": self.category1.name, "reg_no": self.category1.reg_no},
            ], 
            'registered_stores': [
                {
                    "store_name": self.store2.name,
                    "store_reg_no": self.store2.reg_no,
                    "minimum_stock_level": "0",
                    "units": "0.00",
                    "price": "0.00",
                    "is_sellable": True,
                },
                {
                    "store_name": self.store1.name,
                    "store_reg_no": self.store1.reg_no,
                    "minimum_stock_level": "0",
                    "units": "0.00",
                    "price": "0.00",
                    "is_sellable": True,
                }
            ], 
            'available_stores': [
                {"name": self.store2.name, "reg_no": self.store2.reg_no},
                {"name": self.store1.name, "reg_no": self.store1.reg_no},
            ]
        }

        self.assertEqual(response.data, result)
        self.assertEqual(len(response.data['bundle_data']), 2)

    def test_view_can_only_show_variants_for_employee_registerd_stores(self):

        # Decrease user's store count
        self.manager_profile1.stores.remove(self.store2)

        response = self.client.get(
            reverse('api:ep_product_edit', args=(self.product2.reg_no,))
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
            'variant_data': product.get_product_view_variants_data(self.manager_profile1),
            'bundle_data': product.get_product_view_bundles_data(),
            'available_taxes': [
                {
                    'name': self.tax1.name, 
                    'reg_no': self.tax1.reg_no
                }
            ], 
            "available_categories": [
                {"name": self.category2.name, "reg_no": self.category2.reg_no},
                {"name": self.category1.name, "reg_no": self.category1.reg_no},
            ],
            'registered_stores': [
                {
                    'store_name': self.store1.name,
                    'store_reg_no': self.store1.reg_no,
                    'minimum_stock_level': '0',
                    'units': '0.00',
                    "price": "0.00",
                    'is_sellable': True
                }
            ],
            'available_stores': [
                {
                    'name': self.store1.name,
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        # Confirm variants
        variant_data = response.data['variant_data']
        self.assertEqual(len(variant_data), 3)

        for variant in variant_data:
            self.assertEqual(len(variant['registered_stores']), 1)
            self.assertEqual(
                variant['registered_stores'][0]['store_name'],
                self.store1.name
            )

        self.assertEqual(response.data, result)

    def test_if_view_returns_results_even_for_employee_without_add_permission(self):

        # Delete permissoin
        Permission.objects.filter(codename='can_manage_items').delete()

        response = self.client.get(
            reverse('api:ep_product_edit', args=(self.product2.reg_no,))
        )
        self.assertEqual(response.status_code, 200)

    def test_if_view_only_returns_taxes_from_user_stores(self):

        # Decrease user's store count
        self.manager_profile1.stores.remove(self.store2)
       
        response = self.client.get(
            reverse('api:ep_product_edit', args=(self.product1.reg_no,))
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
            'variant_data': product.get_product_view_variants_data(self.manager_profile1),
            'bundle_data': product.get_product_view_bundles_data(),
            'available_taxes': [
                {
                    'name': self.tax1.name, 
                    'reg_no': self.tax1.reg_no
                },
            ], 
            "available_categories": [
                {"name": self.category2.name, "reg_no": self.category2.reg_no},
                {"name": self.category1.name, "reg_no": self.category1.reg_no},
            ], 
            'registered_stores': [
                {
                    'store_name': self.store1.name,
                    'store_reg_no': self.store1.reg_no,
                    'minimum_stock_level': '0',
                    'units': '0.00',
                    "price": "0.00",
                    'is_sellable': True
                }
            ],
            'available_stores': [
                {
                    'name': self.store1.name,
                    'reg_no': self.store1.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_a_top_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:ep_product_edit', args=(self.product1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:ep_product_edit', args=(self.product1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)


class EpProductEditViewForEditingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')
        self.tax2 = create_new_tax(
            self.top_profile1, self.store1, 'New Standard')

        # Create a category
        self.category = create_new_category(self.top_profile1, 'Hair')
        self.category2 = create_new_category(self.top_profile1, 'Face')

        self.create_single_product()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
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
            'track_stock': True,
            'show_product': False,
            'show_image': True,

            'new_stocks_units': 6002,
            'tax_reg_no': self.tax2.reg_no,
            'category_reg_no': self.category2.reg_no,
            
            'bundles_info': [],
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
        with self.assertNumQueries(56):
            response = self.client.put(
                reverse('api:ep_product_edit', args=(
                    self.product.reg_no,)), payload
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
        self.assertEqual(p.modifiers.all().count(), 0)
        self.assertEqual(p.image.url, f'/media/images/products/{p.reg_no}_.jpg')
        self.assertEqual(p.color_code, payload['color_code'])
        self.assertEqual(p.name, payload['name'])
        self.assertEqual(p.cost, payload['cost'])
        self.assertEqual(p.price, payload['price'])
        self.assertEqual(p.sku, payload['sku'])
        self.assertEqual(p.barcode, payload['barcode'])
        self.assertEqual(p.sold_by_each, payload['sold_by_each'])
        self.assertEqual(p.is_bundle, False)
        self.assertEqual(p.track_stock, payload['track_stock'])
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

        # Stock level 1
        self.assertEqual(stock_levels[1].store, self.store2)
        self.assertEqual(stock_levels[1].units, Decimal('0.00'))
        self.assertEqual(stock_levels[1].price, Decimal('1200.00'))
        self.assertEqual(stock_levels[1].is_sellable, True)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.put(
            reverse('api:ep_product_edit', args=(
                self.product.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 401)
    
    def test_firebase_messages_are_sent_correctly(self):

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
            reverse('api:ep_product_edit', args=(self.product.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 200)

        content = get_test_firebase_sender_log_content(only_include=['product'])
        self.assertEqual(len(content), 2)

        product = Product.objects.get(name=payload['name'])

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

    def test_if_a_product_cant_be_edited_when_employee_has_no_permission(self):

        # Delete permissoin
        Permission.objects.filter(codename='can_manage_items').delete()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:ep_product_edit', args=(
                self.product.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 403)
    
    def test_view_wont_edit_products_that_are_not_dirty(self):

        # Add store2
        product = Product.objects.get(name="Shampoo")

        self.assertEqual(product.stores.all().count(), 2)

        # Mark all products as sellable
        StockLevel.objects.all().update(is_sellable=False)

        levels = StockLevel.objects.all()

        for level in levels:
            self.assertEqual(level.is_sellable, False)

        payload = self.get_premade_payload()

        payload['stores_info'][0]['is_sellable'] = True
        payload['stores_info'][0]['is_dirty'] = False

        payload['stores_info'][1]['is_sellable'] = True
        payload['stores_info'][1]['is_dirty'] = False

        response = self.client.put(
            reverse('api:ep_product_edit', args=(self.product.reg_no,)), payload
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
            reverse('api:ep_product_edit', args=(self.product.reg_no,)), payload
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
            reverse('api:ep_product_edit', args=(self.product.reg_no,)), payload
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
            reverse('api:ep_product_edit', args=(self.product.reg_no,)), payload
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

    def test_if_view_can_only_edit_a_product_with_store_that_belongs_to_the_user(self):

        # Decrease user's store count
        self.manager_profile1.stores.remove(self.store2)

        payload = self.get_premade_payload()

        payload['stores_info'] = [
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
            },
        ]

        response = self.client.put(
            reverse('api:ep_product_edit', args=(
                self.product.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, 
            {'stores_info': 'You provided wrong stores.'}
        )

    def test_view_can_handle_a_wrong_store_reg_no(self):

        payload = self.get_premade_payload()
        payload['stores_info'] = [{'reg_no': self.store2.reg_no}, ]

        response = self.client.put(
            reverse('api:ep_product_edit', args=(111111111,)), payload
        )
        self.assertEqual(response.status_code, 404)

    def test_view_wont_accept_an_empty_store_info(self):

        payload = self.get_premade_payload()
        payload['stores_info'] = ''

        response = self.client.put(
            reverse('api:ep_product_edit', args=(
                self.product.reg_no,)), payload
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
            reverse('api:ep_product_edit', args=(
                self.product.reg_no,)), payload
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
            # 3333333333333333333333333333333333333333333333  # Extremely long
        ]

        i = 0
        for reg_no in wrong_stores_reg_nos:

            payload = self.get_premade_payload()
            payload['stores_info'][0]['reg_no'] = reg_no

            response = self.client.put(reverse(
                'api:ep_product_edit',
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
            reverse('api:ep_product_edit', args=(
                self.product.reg_no,)), payload
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
            7878787,  # Wrong reg no,
            445464666666666666666666666666666666666666666666666666666,  # long reg no
        ]

        for wrong_reg_no in wrong_reg_nos:
            response = self.client.put(
                reverse('api:ep_product_edit', args=(wrong_reg_no,)), payload
            )

            self.assertEqual(response.status_code, 404)

    def test_if_a_product_cant_be_edited_with_an_empty_name(self):

        payload = self.get_premade_payload()

        payload['name'] = ''

        response = self.client.put(
            reverse('api:ep_product_edit',
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
            reverse('api:ep_product_edit',
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
            reverse('api:ep_product_edit',
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
            reverse('api:ep_product_edit',
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
            reverse('api:ep_product_edit',
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
            reverse('api:ep_product_edit',
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
            reverse('api:ep_product_edit',
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
            reverse('api:ep_product_edit',
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
            7878787,  # Wrong reg no,
            tax2.reg_no,  # Tax for another user
            445464666666666666666666666666666666666666666666666666666,  # long reg no
        ]

        i = 0
        for wrong_reg_no in wrong_reg_nos:
            i += 1

            payload['name'] = f'product{i}'  # This makes the name unique
            payload['tax_reg_no'] = wrong_reg_no

            response = self.client.put(
                reverse('api:ep_product_edit',
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
            reverse('api:ep_product_edit',
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
            7878787,  # Wrong reg no,
            category2.reg_no,  # Category for another user
            445464666666666666666666666666666666666666666666666666666,  # long reg no
        ]

        i = 0
        for wrong_reg_no in wrong_reg_nos:
            i += 1

            payload['name'] = f'product{i}'  # This makes the name unique
            payload['category_reg_no'] = wrong_reg_no

            response = self.client.put(
                reverse('api:ep_product_edit',
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
                reverse('api:ep_product_edit', 
                args=(self.product.reg_no,)), 
                payload
            )

        self.assertEqual(response.status_code, 200)

        p = Product.objects.get(name=payload['name'])

        # Check model url values
        self.assertEqual(p.image.url, f'/media/images/products/{p.reg_no}_.jpg')

    def test_if_view_can_edit_an_image_with_the_right_dimensions(self):

        payload = self.get_premade_payload()

        # Send data
        with open(self.full_path, 'rb') as my_image:
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:ep_product_edit', 
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

            response = self.client.put(
                reverse('api:ep_product_edit', 
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

            response = self.client.put(
                reverse('api:ep_product_edit', 
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

            response = self.client.put(
                reverse('api:ep_product_edit', 
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
                reverse('api:ep_product_edit', 
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

        throttle_rate = int(
            settings.THROTTLE_RATES['api_product_rate'].split("/")[0])

        for i in range(throttle_rate):  # pylint: disable=unused-variable

            payload['name'] = f'product{i}'  # This makes the name unique

            response = self.client.put(
                reverse('api:ep_product_edit',
                        args=(self.product.reg_no,)),
                payload,
            )
            self.assertEqual(response.status_code, 200)

        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional
        # request if the previous request was not throttled
        for i in range(throttle_rate):  # pylint: disable=unused-variable

            # Try to see if the next request will be throttled
            payload['name'] = f'product{i}'  # This makes the name unique

            response = self.client.put(
                reverse('api:ep_product_edit',
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

    def test_if_view_cant_be_viewed_by_a_top_user(self):

        # Login a top user #
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:ep_product_edit',
                    args=(self.product.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:ep_product_edit',
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
        token = Token.objects.get(user__email='gucci@gmail.com')
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
            barcode='code123',
            track_stock=True
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
            'track_stock': True,
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

                }
            ]
        }

        return payload

    def test_if_view_can_edit_a_product(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        #with self.assertNumQueries(28):
        response = self.client.put(
            reverse('api:ep_product_edit', 
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
        self.assertEqual(stock_levels[1].price, Decimal('0.00'))
        self.assertEqual(stock_levels[1].is_sellable, True)


    def test_if_a_bundle_cant_be_edited_with_an_empty_name(self):

        payload = self.get_premade_payload()

        payload['bundles_info'][0]['reg_no'] = ''

        response = self.client.put(
            reverse('api:ep_product_edit', 
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
            reverse('api:ep_product_edit', 
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
                reverse('api:ep_product_edit', args=(self.product.reg_no,)), 
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
            reverse('api:ep_product_edit', 
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
            reverse('api:ep_product_edit', 
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
            reverse('api:ep_product_edit', 
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
            reverse('api:ep_product_edit', 
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

class EpProductEditViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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
        token = Token.objects.get(user__email='gucci@gmail.com')
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
            reverse('api:ep_product_edit',args=(self.product.reg_no,))
        )

        self.assertEqual(response.status_code, 204)

        # Confirm the product was deleted
        self.assertEqual(Product.objects.filter(
            reg_no=self.product.reg_no).exists(), False
        )

    def test_firebase_messages_are_sent_correctly(self):

        content = get_test_firebase_sender_log_content(only_include=['product'])
        self.assertEqual(len(content), 0)

        response = self.client.delete(
            reverse('api:ep_product_edit',args=(self.product.reg_no,))
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

    def test_if_a_product_cant_be_deleted_when_employee_has_no_permission(self):

        # Delete permissoin
        Permission.objects.filter(codename='can_manage_items').delete()

        response = self.client.delete(
            reverse('api:ep_product_edit',args=(self.product.reg_no,))
        )
        self.assertEqual(response.status_code, 403)

    def test_if_view_can_only_delete_a_product_with_store_that_belongs_to_the_user(self):

        # Decrease user's store count
        self.manager_profile1.stores.remove(self.store1)

        response = self.client.delete(
            reverse('api:ep_product_edit',args=(self.product.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    def test_if_view_can_handle_a_wrong_product_reg_no(self):

        wrong_reg_nos = [
            7878787,  # Wrong reg no,
            445464666666666666666666666666666666666666666666666666666,  # long reg no
        ]

        for wrong_reg_no in wrong_reg_nos:
            response = self.client.delete(
                reverse('api:ep_product_edit', args=(wrong_reg_no,))
            )

            self.assertEqual(response.status_code, 404)

        # Confirm the product was not deleted
        self.assertEqual(Product.objects.filter(
            reg_no=self.product.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_a_top_user(self):

        # Login a employee user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:ep_product_edit', args=(self.product.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the product was not deleted
        self.assertEqual(Product.objects.filter(
            reg_no=self.product.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:ep_product_edit', args=(self.product.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

        # Confirm the product was not deleted
        self.assertEqual(Product.objects.filter(
            reg_no=self.product.reg_no).exists(), True
        )
