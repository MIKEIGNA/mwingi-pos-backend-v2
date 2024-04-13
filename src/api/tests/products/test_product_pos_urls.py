import json

from django.conf import settings
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from core.encoders.encoder_utils import DecimalEncoder

from core.test_utils.create_product_models import create_new_product
from core.test_utils.create_product_variants import create_1d_variants
from core.test_utils.create_store_models import create_new_category, create_new_tax

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.initial_user_data import InitialUserDataMixin
from inventories.models import StockLevel

from mysettings.models import MySetting

from products.models import (
    Product,
    ProductBundle,
    ProductVariantOption,
    ProductVariantOptionChoice
)

class TpProductPosIndexViewTestCase(APITestCase, InitialUserDataMixin):

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
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        ) 

        product.stores.add(self.store1)

        # Update stock units
        stock = StockLevel.objects.get(product=product, store=self.store1)
        stock.minimum_stock_level = 120
        stock.units = 5100
        stock.price = 3000
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
            category=self.category,
            name="Hair Bundle",
            price=35000,
            cost=30000,
            sku='sku1',
            barcode='code123'
        )
        master_product.stores.add(self.store1)

        master_product.bundles.add(shampoo_bundle)
    
    def test_if_view_returns_the_products_correctly(self):
        
        # We add another stock level for product by adding a new store
        product = Product.objects.get(name="Shampoo")
        product.stores.add(self.store1, self.store2)
        
        # Confirm we have 2 stock levels
        self.assertEqual(StockLevel.objects.filter(product=product).count(), 2)

        # Count Number of Queries #
        with self.assertNumQueries(12):
            response = self.client.get(
                reverse('api:tp_pos_product_index', args=(self.store1.reg_no,)))
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
                    'price': '3000.00',
                    'cost': '1000.00',
                    'sku': 'sku1',
                    'barcode': 'code123',
                    'sold_by_each': True,
                    'is_bundle': False,
                    'track_stock': True,
                    'variant_count': 0,
                    'show_product': True,
                    'show_image': False,
                    'reg_no': product.reg_no,
                    'stock_level': {
                        'minimum_stock_level': '120',
                        'units': '5100.00'
                    },
                    'category_data': {
                        'name': 'Hair',
                        'reg_no': self.category.reg_no
                    },
                    'tax_data': {
                        'name': 'Standard',
                        'rate': '20.05',
                        'reg_no': self.tax.reg_no
                    },
                    'modifier_data': [],
                    'variant_data': {'options': [], 'variants': []},
                }
            ]
        }

        self.assertEqual(
            json.loads(json.dumps(response.data, cls=DecimalEncoder)), 
            result
        )

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
            reverse('api:tp_pos_product_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)

    def test_if_view_does_not_return_stock_data_for_unsellable_products(self):

        product = Product.objects.get(name="Shampoo")
        
        # Make product unsellable in store 1
        level = StockLevel.objects.get(store=self.store1, product=product)
        level.is_sellable = False
        level.save()

        response = self.client.get(
            reverse('api:tp_pos_product_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0,
            'next': None,
            'previous': None,
            'results': []
        }

        self.assertEqual(
            json.loads(json.dumps(response.data, cls=DecimalEncoder)), 
            result
        )

    def test_view_when_proudct_does_not_have_tax_category(self):

        # Remove tax and category
        product = Product.objects.get(name="Shampoo")
        product.tax = None
        product.category = None
        product.save()

        response = self.client.get(
            reverse('api:tp_pos_product_index', args=(self.store1.reg_no,)))
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
                    'price': '3000.00',
                    'cost': '1000.00',
                    'sku': 'sku1',
                    'barcode': 'code123',
                    'sold_by_each': True,
                    'is_bundle': False,
                    'track_stock': True,
                    'variant_count': 0,
                    'show_product': True,
                    'show_image': False,
                    'stock_level': {
                        'minimum_stock_level': '120',
                        'units': '5100.00'
                    },
                    'reg_no': product.reg_no,
                    'category_data': {},
                    'tax_data': {},
                    'modifier_data': [],
                    'variant_data': {'options': [], 'variants': []},
                }
            ]
        }

        self.assertEqual(
            json.loads(json.dumps(response.data, cls=DecimalEncoder)), 
            result
        )

    def test_view_when_there_are_bundle_products(self):

        self.create_a_bundle_master_product()

        product1 = Product.objects.get(name="Shampoo")
        product2 = Product.objects.get(name="Hair Bundle")

        response = self.client.get(
            reverse('api:tp_pos_product_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'image_url': f'/media/images/products/{product1.reg_no}_.jpg',
                    'color_code': '#474A49',
                    'name': 'Shampoo',
                    'price': '3000.00',
                    'cost': '1000.00',
                    'sku': 'sku1',
                    'barcode': 'code123',
                    'sold_by_each': True,
                    'is_bundle': False,
                    'track_stock': True,
                    'variant_count': 0,
                    'show_product': True,
                    'show_image': False,
                    'reg_no': product1.reg_no,
                    'stock_level': {
                        'minimum_stock_level': '120',
                        'units': '5100.00'
                    },
                    'category_data': {
                        'name': 'Hair',
                        'reg_no': self.category.reg_no
                    },
                    'tax_data': {
                        'name': 'Standard',
                        'rate': '20.05',
                        'reg_no': self.tax.reg_no
                    },
                    'modifier_data': [],
                    'variant_data': {'options': [], 'variants': []},
                },
                {
                    'image_url': f'/media/images/products/{product2.reg_no}_.jpg',
                    'color_code': '#474A49',
                    'name': 'Hair Bundle',
                    'cost': '30000.00',
                    'price': '35000.00',
                    'sku': 'sku1',
                    'barcode': 'code123',
                    'sold_by_each': True,
                    'is_bundle': True,
                    'track_stock': True,
                    'variant_count': 0,
                    'show_product': True,
                    'show_image': False,
                    'reg_no': product2.reg_no,
                    'stock_level': {
                        'minimum_stock_level': '0',
                        'units': '0.00'
                    },
                    'category_data': {
                        'name': 'Hair',
                        'reg_no': self.category.reg_no
                    },
                    'tax_data': {
                        'name': 'Standard',
                        'rate': '20.05',
                        'reg_no': self.tax.reg_no
                    },
                    'modifier_data': [],
                    'variant_data': {'options': [], 'variants': []},
                }
            ]
        }

        self.assertEqual(
            json.loads(json.dumps(response.data, cls=DecimalEncoder)), 
            result
        )

    def test_view_when_there_is_a_product_with_variants(self):

        product = Product.objects.get(name="Shampoo")

        # Create 3 variants for master product
        create_1d_variants(
            master_product=product,
            profile=self.top_profile1,
            store1=self.store1,
            store2=self.store2
        )

        options = ProductVariantOption.objects.all().order_by('id')
        choices = ProductVariantOptionChoice.objects.all().order_by('id')
        variants = Product.objects.filter(productvariant__product=product).order_by('id')

        # Count Number of Queries #
        with self.assertNumQueries(16):
            response = self.client.get(reverse('api:tp_pos_product_index', args=(self.store1.reg_no,)))
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
                    'price': '3000.00',
                    'cost': '1000.00',
                    'sku': 'sku1',
                    'barcode': 'code123',
                    'sold_by_each': True,
                    'is_bundle': False,
                    'track_stock': True,
                    'variant_count': 3,
                    'show_product': True,
                    'show_image': False,
                    'reg_no': product.reg_no,
                    'stock_level': {
                        'minimum_stock_level': '120',
                        'units': '5100.00'
                    },
                    'category_data': {
                        'name': 'Hair',
                        'reg_no': self.category.reg_no
                    },
                    'tax_data': {
                        'name': 'Standard',
                        'rate': '20.05',
                        'reg_no': self.tax.reg_no
                    },
                    'modifier_data': [],
                    'variant_data': {
                        'options': [
                            {
                                'name': 'Size',
                                'reg_no': options[0].reg_no,
                                'values': [
                                    {
                                        'name': 'Small',
                                        'reg_no': choices[0].reg_no,
                                    },
                                    {
                                        'name': 'Medium',
                                        'reg_no': choices[1].reg_no,
                                    },
                                    {
                                        'name': 'Large',
                                        'reg_no': choices[2].reg_no,
                                    }
                                ]
                            }
                        ],
                        'variants': [
                            {
                                'name': 'Small',
                                'price': '1500.00', 
                                'cost': '800.00', 
                                'sku': '',
                                'barcode': 'code123',
                                'stock_level': {
                                    'minimum_stock_level': '50',
                                    'units': '100.00'
                                },
                                'show_product': True,
                                'reg_no': variants[0].reg_no,
                            },
                            {
                                'name': 'Medium',
                                'price': '1500.00', 
                                'cost': '800.00', 
                                'sku': '',
                                'barcode': 'code123',
                                'stock_level': {
                                    'minimum_stock_level': '60',
                                    'units': '120.00'
                                },
                                'show_product': True,
                                'reg_no': variants[1].reg_no,
                            },
                            {
                                'name': 'Large',
                                'price': '1500.00', 
                                'cost': '800.00', 
                                'sku': '',
                                'barcode': 'code123',
                                'stock_level': {
                                    'minimum_stock_level': '65',
                                    'units': '130.00'
                                },
                                'show_product': True,
                                'reg_no': variants[2].reg_no,
                            }
                        ]
                    },
                }
            ]
        }

        self.assertEqual(
            json.loads(json.dumps(response.data, cls=DecimalEncoder)), 
            result
        )

    def test_if_view_does_not_show_product_variants_that_belong_to_other_stores(self):

        product = Product.objects.get(name="Shampoo")

        # Create 3 variants for master product
        create_1d_variants(
            master_product=product,
            profile=self.top_profile1,
            store1=self.store1,
            store2=self.store2
        )

        # Remove 2 products from store1    
        medium_product = Product.objects.get(name='Medium')
        medium_product.stores.remove(self.store1)

        large_product = Product.objects.get(name='Large')
        large_product.stores.remove(self.store1)

        options = ProductVariantOption.objects.all().order_by('id')
        choices = ProductVariantOptionChoice.objects.all().order_by('id')
        variants = Product.objects.filter(productvariant__product=product).order_by('id')

        response = self.client.get(reverse('api:tp_pos_product_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        self.maxDiff = None

        result = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'image_url': f'/media/images/products/{product.reg_no}_.jpg',
                    'color_code': '#474A49',
                    'name': 'Shampoo',
                    'price': '3000.00',
                    'cost': '1000.00',
                    'sku': 'sku1',
                    'barcode': 'code123',
                    'sold_by_each': True,
                    'is_bundle': False,
                    'track_stock': True,
                    'variant_count': 3,
                    'show_product': True,
                    'show_image': False,
                    'reg_no': product.reg_no,
                    'stock_level': {
                        'minimum_stock_level': '120',
                        'units': '5100.00'
                    },
                    'category_data': {
                        'name': 'Hair',
                        'reg_no': self.category.reg_no
                    },
                    'tax_data': {
                        'name': 'Standard',
                        'rate': '20.05',
                        'reg_no': self.tax.reg_no
                    },
                    'modifier_data': [],
                    'variant_data': {
                        'options': [
                            {
                                'name': 'Size',
                                'reg_no': options[0].reg_no,
                                'values': [
                                    {
                                        'name': 'Small',
                                        'reg_no': choices[0].reg_no,
                                    },
                                    {
                                        'name': 'Medium',
                                        'reg_no': choices[1].reg_no,
                                    },
                                    {
                                        'name': 'Large',
                                        'reg_no': choices[2].reg_no,
                                    }
                                ]
                            }
                        ],
                        'variants': [
                            {
                                'name': 'Small',
                                'price': '1500.00', 
                                'cost': '800.00', 
                                'sku': '',
                                'barcode': 'code123',
                                'stock_level': {
                                    'minimum_stock_level': '50',
                                    'units': '100.00'
                                },
                                'show_product': True,
                                'reg_no': variants[0].reg_no,
                            }
                        ]
                    },
                }
            ]
        }
        
        self.assertEqual(
            json.loads(json.dumps(response.data, cls=DecimalEncoder)), 
            result
        ) 

    def test_if_view_wont_show_products_from_other_stores(self):

        product = Product.objects.get(name="Shampoo")

        # Remvove store1 from product
        product.stores.remove(self.store1)

        response = self.client.get(reverse('api:tp_pos_product_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_if_view_can_handle_wrong_reg_no(self):

        response = self.client.get(reverse('api:tp_pos_product_index', args=(4646464,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all products
        Product.objects.all().delete()

        pagination_page_size = settings.PRODUCT_POS_PAGINATION_PAGE_SIZE

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
                name=product_names[i]
            )

        self.assertEqual(
            Product.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

    
        products = Product.objects.filter(profile=self.top_profile1).order_by('name')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        #with self.assertNumQueries(3):
        response = self.client.get(reverse('api:tp_pos_product_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], f'http://testserver/api/pos/products/{self.store1.reg_no}/?page=2')
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
        response = self.client.get(reverse('api:tp_pos_product_index', args=(self.store1.reg_no,)) + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 21, 
            'next': None, 
            'previous': f'http://testserver/api/pos/products/{self.store1.reg_no}/', 
            'results': [
                {
                    'image_url': f'/media/images/products/{products[0].reg_no}_.jpg', 
                    'color_code': '#474A49', 
                    'name': products[0].name, 
                    'price': '2500.00', 
                    'cost': '1000.00', 
                    'sku': 'sku1', 
                    'barcode': 'code123', 
                    'sold_by_each': True, 
                    'is_bundle': False, 
                    'track_stock': True, 
                    'variant_count': 0, 
                    'show_product': True, 
                    'show_image': False, 
                    'reg_no': products[0].reg_no, 
                    'stock_level': {
                        'minimum_stock_level': '0',
                        'units': '0.00'
                    },
                    'category_data': {
                        'name': 'Hair', 
                        'reg_no': self.category.reg_no
                    }, 
                    'tax_data': {
                        'name': 'Standard', 
                        'rate': '20.05', 
                        'reg_no': self.tax.reg_no
                    }, 
                    'modifier_data': [], 
                    'variant_data': {'options': [], 'variants': []}
                }
            ]
        }

        self.assertEqual(
            json.loads(json.dumps(response.data, cls=DecimalEncoder)), 
            result
        )

    def test_view_returns_empty_when_there_are_no_products(self):

        # First delete all products
        Product.objects.all().delete()

        response = self.client.get(reverse('api:tp_pos_product_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:tp_pos_product_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:tp_pos_product_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)
'''