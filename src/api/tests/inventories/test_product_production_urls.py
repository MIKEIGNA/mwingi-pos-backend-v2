import json

from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.initial_user_data import InitialUserDataMixin
from core.test_utils.custom_testcase import APITestCase

from products.models import Product, ProductProductionMap

from mysettings.models import MySetting
from inventories.models import ProductTransform, ProductTransformLine, StockLevel

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

        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        self.product3 = Product.objects.create(
            profile=self.top_profile1,
            name="Gloss",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        self.create_product_transform()

    def create_product_transform(self):

        ########### Create product transform1
        self.product_transform1 = ProductTransform.objects.create(
            user=self.user1,
            store=self.store1,
            total_quantity=1300,
        )

        # Create product_transform1
        ProductTransformLine.objects.create(
            product_transform=self.product_transform1,
            source_product=self.product1,
            target_product=self.product3,
            quantity=10,
            cost=150,
        )
    
        # Create product_transform2
        ProductTransformLine.objects.create(
            product_transform=self.product_transform1,
            source_product=self.product2,
            target_product=self.product3,
            quantity=14,
            cost=100,
        )


        ########### Create product transform2
        self.product_transform2 = ProductTransform.objects.create(
            user=self.user1,
            store=self.store2,
            total_quantity=1400
        )

        # Create product_transform1
        ProductTransformLine.objects.create(
            product_transform=self.product_transform2,
            source_product=self.product1,
            target_product=self.product3,
            quantity=10,
            cost=150,
        )
    
        # Create product_transform2
        ProductTransformLine.objects.create(
            product_transform=self.product_transform2,
            source_product=self.product2,
            target_product=self.product3,
            quantity=5,
            cost=100,
        )

    def test_view_returns_the_user_product_transforms_only(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        response = self.client.get(reverse('api:product_transform_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.product_transform2.__str__(), 
                    'store_name': self.store2.name, 
                    'status': self.product_transform2.status,
                    'total_quantity': f'{self.product_transform2.total_quantity}.00',
                    'reg_no': self.product_transform2.reg_no, 
                    'creation_date': self.product_transform2.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'is_auto_repackaged': self.product_transform2.is_auto_repackaged
                }, 
                {
                    'name': self.product_transform1.__str__(), 
                    'status': self.product_transform1.status,
                    'store_name': self.store1.name, 
                    'total_quantity': f'{self.product_transform1.total_quantity}.00',
                    'reg_no': self.product_transform1.reg_no, 
                    'creation_date': self.product_transform1.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'is_auto_repackaged': self.product_transform1.is_auto_repackaged
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
  
        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
                reverse('api:product_transform_index'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all product_transforms
        ProductTransform.objects.all().delete()

        pagination_page_size = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION

        model_num_to_be_created = pagination_page_size+1

        product_transform_names = []
        for i in range(model_num_to_be_created):
            product_transform_names.append(f'New ProductTransform{i}')

        names_length = len(product_transform_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm product_transforms
        for i in range(names_length):
            ProductTransform.objects.create(
                user=self.user1,
                store=self.store1,
                total_quantity=24,
            )

        self.assertEqual(
            ProductTransform.objects.filter(user=self.user1).count(),
            names_length)  # Confirm models were created

    
        product_transforms = ProductTransform.objects.filter(user=self.user1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(17):
            response = self.client.get(
                reverse('api:product_transform_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 
            'http://testserver/api/product_transformations/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all product transforms are listed except the first one since it's in the next paginated page #
        i = 0
        for product_transform in product_transforms[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], product_transform.__str__())
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], product_transform.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
                reverse('api:product_transform_index')  + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/product_transformations/',
            'results': [
                {
                    'name': product_transforms[0].__str__(), 
                    'store_name': self.store1.name, 
                    'status': product_transforms[0].status,
                    'total_quantity': f'{product_transforms[0].total_quantity}',
                    'reg_no': product_transforms[0].reg_no, 
                    'creation_date': product_transforms[0].get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'is_auto_repackaged': product_transforms[0].is_auto_repackaged
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

    def test_view_can_perform_search(self):

        param = f'?search={self.product_transform2.reg_no}'
        response = self.client.get(reverse('api:product_transform_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {

                    'name': self.product_transform2.__str__(), 
                    'store_name': self.store2.name, 
                    'status': self.product_transform2.status,
                    'total_quantity': f'{self.product_transform2.total_quantity}.00',
                    'reg_no': self.product_transform2.reg_no, 
                    'creation_date': self.product_transform2.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'is_auto_repackaged': self.product_transform2.is_auto_repackaged
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

    def test_view_can_filter_store(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?store_reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:product_transform_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.product_transform1.__str__(), 
                    'store_name': self.store1.name, 
                    'status': self.product_transform1.status,
                    'total_quantity': f'{self.product_transform1.total_quantity}.00',
                    'reg_no': self.product_transform1.reg_no, 
                    'creation_date': self.product_transform1.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'is_auto_repackaged': self.product_transform1.is_auto_repackaged
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

    def test_view_returns_empty_when_there_are_no_product_transforms(self):

        # First delete all product_transforms
        ProductTransform.objects.all().delete()

        response = self.client.get(
                reverse('api:product_transform_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
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
                reverse('api:product_transform_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
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
    #             reverse('api:product_transform_index'))
    #     self.assertEqual(response.status_code, 200)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:product_transform_index'))
        self.assertEqual(response.status_code, 401)

    
class ProductTransformCreateViewTestCase(APITestCase, InitialUserDataMixin):

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

        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        self.product3 = Product.objects.create(
            profile=self.top_profile1,
            name="Gloss",
            price=2800,
            cost=1200,
            barcode='code123'
        )

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """
        
        payload = {
            'store_reg_no': self.store1.reg_no,
            'status': ProductTransform.PRODUCT_TRANSFORM_PENDING,
            'product_transform_lines': [
                {
                    'source_product_reg_no': self.product1.reg_no,
                    'target_product_reg_no': self.product3.reg_no,
                    'quantity': 10,
                    'added_quantity': 6,
                    'cost': 150,
                },
                {
                    'source_product_reg_no': self.product2.reg_no,
                    'target_product_reg_no': self.product3.reg_no,
                    'quantity': 14,
                    'added_quantity': 7,
                    'cost': 100,
                }
            ]
        }

        return payload 

    def test_if_view_can_create_a_product_transform(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        # with self.assertNumQueries(31):
        response = self.client.post(reverse('api:product_transform_index'), payload)
        self.assertEqual(response.status_code, 201)

        pt = ProductTransform.objects.get(store=self.store1)

        # Confirm model creation
        self.assertEqual(ProductTransform.objects.all().count(), 1)
    
        product1 = Product.objects.get(name='Shampoo')
        product2 = Product.objects.get(name='Conditioner')
        product3 = Product.objects.get(name='Gloss')

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(pt.user, self.user1)
        self.assertEqual(pt.store, self.store1)
        self.assertEqual(pt.status, ProductTransform.PRODUCT_TRANSFORM_PENDING)
        self.assertEqual(pt.total_quantity, 24.00)
        self.assertTrue(pt.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((pt.created_date).strftime("%B, %d, %Y"), today)

        # Confirm receipt line model creation
        self.assertEqual(ProductTransformLine.objects.filter(product_transform=pt).count(), 2)

        lines = ProductTransformLine.objects.filter(product_transform=pt).order_by('id')

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.product_transform, pt)
        self.assertEqual(line1.source_product, product1)
        self.assertEqual(line1.target_product, product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line1.quantity, 10.00)
        self.assertEqual(line1.added_quantity, 6.00)
        self.assertEqual(line1.cost, 150.00)
        self.assertEqual(line1.amount, 1500.00)
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.product_transform, pt)
        self.assertEqual(line2.source_product, product2)
        self.assertEqual(line2.target_product, product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line2.quantity, 14.00)
        self.assertEqual(line2.added_quantity, 7.00)
        self.assertEqual(line2.cost, 100.00)
        self.assertEqual(line2.amount, 1400.00)

    def test_if_view_can_handle_with_wrong_store_reg_no(self):

        wrong_reg_nos = [
            33463476347374, # Wrong reg no
            self.store3.reg_no, # Store for another user
            11111111111111111111111111111111111111 # Long reg no
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_reg_nos:

            payload = self.get_premade_payload()
            payload['store_reg_no'] = wrong_reg_no

            response = self.client.post(
                reverse('api:product_transform_index'), 
                payload
            )

            self.assertEqual(response.status_code, 404)

            # Confirm model was not creation
            self.assertEqual(ProductTransform.objects.all().count(), 0)
    
    def test_if_view_can_handle_a_line_wrong_source_product_reg_no(self):

        product_for_another_user = Product.objects.create(
            profile=self.top_profile2,
            name="Lotion",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        wrong_reg_nos = [
            33463476347374, # Wrong reg no
            product_for_another_user.reg_no, # Product for another user
            11111111111111111111111111111111111111 # Long reg no
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_reg_nos:

            # Delete previous models
            ProductTransform.objects.all().delete()
            ProductTransformLine.objects.all().delete()

            payload['product_transform_lines'][0]['source_product_reg_no'] = wrong_reg_no

            response = self.client.post(
                reverse('api:product_transform_index'),
                payload,
            )

            self.assertEqual(response.status_code, 400)

            result = {'non_field_errors': 'Product error.'}
            self.assertEqual(response.data, result)

            # Confirm model creation
            self.assertEqual(ProductTransform.objects.all().count(), 0)

    def test_if_view_can_handle_a_line_wrong_target_product_reg_no(self):

        product_for_another_user = Product.objects.create(
            profile=self.top_profile2,
            name="Lotion",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        wrong_reg_nos = [
            33463476347374, # Wrong reg no
            product_for_another_user.reg_no, # Product for another user
            11111111111111111111111111111111111111 # Long reg no
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_reg_nos:

            # Delete previous models
            ProductTransform.objects.all().delete()
            ProductTransformLine.objects.all().delete()

            payload['product_transform_lines'][0]['target_product_reg_no'] = wrong_reg_no

            response = self.client.post(
                reverse('api:product_transform_index'),
                payload,
            )

            self.assertEqual(response.status_code, 400)

            result = {'non_field_errors': 'Product error.'}
            self.assertEqual(response.data, result)

            # Confirm model creation
            self.assertEqual(ProductTransform.objects.all().count(), 0)

    def test_if_view_url_can_throttle_post_requests(self):

        payload = self.get_premade_payload()

        throttle_rate = int(settings.THROTTLE_RATES['api_10_per_minute_create_rate'].split("/")[0])
    
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:product_transform_index'),
                payload,
            )
            self.assertEqual(response.status_code, 201)


        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional 
        # request if the previous request was not throttled 
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:product_transform_index'),
                payload,
            )

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else: 
            # Executed because break was not called. This means the request was
            # never throttled 
            self.fail()

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.post(
            reverse('api:product_transform_index'), 
            payload,
        )
        self.assertEqual(response.status_code, 401)

class ProductTransformViewForViewingTestCase(APITestCase, InitialUserDataMixin):

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

        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        self.product3 = Product.objects.create(
            profile=self.top_profile1,
            name="Gloss",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        self.create_product_transform()

    def create_product_transform(self):

        ########### Create product transform1
        self.product_transform1 = ProductTransform.objects.create(
            user=self.user1,
            store=self.store1,
            total_quantity=1300,
        )

        # Create product_transform1
        ProductTransformLine.objects.create(
            product_transform=self.product_transform1,
            source_product=self.product1,
            target_product=self.product3,
            quantity=10,
            cost=150,
        )
    
        # Create product_transform2
        ProductTransformLine.objects.create(
            product_transform=self.product_transform1,
            source_product=self.product2,
            target_product=self.product3,
            quantity=14,
            cost=100,
        )


        ########### Create product transform2
        self.product_transform2 = ProductTransform.objects.create(
            user=self.user1,
            store=self.store2,
            total_quantity=1400
        )

        # Create product_transform1
        ProductTransformLine.objects.create(
            product_transform=self.product_transform2,
            source_product=self.product1,
            target_product=self.product3,
            quantity=10,
            added_quantity=4,
            cost=150,
        )
    
        # Create product_transform2
        ProductTransformLine.objects.create(
            product_transform=self.product_transform2,
            source_product=self.product2,
            target_product=self.product3,
            quantity=5,
            added_quantity=3,
            cost=100,
        )

    def test_view_can_be_called_successefully(self):

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.get(
            reverse('api:product_transform_view', 
            args=(self.product_transform1.reg_no,))
        )
        self.assertEqual(response.status_code, 200)

        lines = self.product_transform1.producttransformline_set.all().order_by('id')

        results = {
            'name': self.product_transform1.__str__(),
            'store_data': self.product_transform1.get_store_data(), 
            'status': self.product_transform1.status,
            'total_quantity': f'{str(self.product_transform1.total_quantity)}.00',
            'reg_no': self.product_transform1.reg_no, 
            'created_by': self.user1.get_full_name(), 
            'creation_date': self.product_transform1.get_created_date(
                self.user1.get_user_timezone()
            ),  
            'is_auto_repackaged': self.product_transform1.is_auto_repackaged,
            'auto_repackaged_source_desc': self.product_transform1.auto_repackaged_source_desc,
            'auto_repackaged_source_reg_no': self.product_transform1.auto_repackaged_source_reg_no,
            'line_data': [
                {
                    'source_product_info': {
                        'name': self.product1.name, 
                        'reg_no': self.product1.reg_no
                    }, 
                    'target_product_info': {
                        'name': self.product3.name, 
                        'reg_no': self.product3.reg_no
                    }, 
                    'quantity': str(lines[0].quantity),
                    'added_quantity': str(lines[0].added_quantity),
                    'cost': str(lines[0].cost),
                    'is_reverse': True,
                    'amount': str(lines[0].amount),
                    'reg_no': lines[0].reg_no
                }, 
                {
                    'source_product_info': {
                        'name': self.product2.name, 
                        'reg_no': self.product2.reg_no
                    }, 
                    'target_product_info': {
                        'name': self.product3.name, 
                        'reg_no': self.product3.reg_no
                    }, 
                    'quantity': str(lines[1].quantity),
                    'added_quantity': str(lines[1].added_quantity),
                    'cost': str(lines[1].cost),
                    'is_reverse': True,
                    'amount': str(lines[1].amount),
                    'reg_no': lines[1].reg_no
                }
            ]
        }

        self.assertEqual(response.data, results)

        ########################## Test maintaince ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
            reverse('api:product_transform_view', args=(self.product_transform1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

    def test_view_can_handle_wrong_product_transform_reg_no(self):

        response = self.client.get(
            reverse('api:product_transform_view', args=(4646464,)))
        self.assertEqual(response.status_code, 404)

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:product_transform_view', 
            args=(self.product_transform1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    # def test_view_cant_be_viewed_by_an_employee_user(self):

    #     # Login a employee user
    #     # Include an appropriate `Authorization:` header on all requests.
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     response = self.client.get(
    #         reverse('api:product_transform_view', 
    #         args=(self.product_transform1.reg_no,))
    #     )
    #     self.assertEqual(response.status_code, 200)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:product_transform_view', 
            args=(self.product_transform1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

class ProductTransformViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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

        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        self.product3 = Product.objects.create(
            profile=self.top_profile1,
            name="Gloss",
            price=2800,
            cost=1200,
            barcode='code123'
        )


        self.create_product_transform()

    def create_product_transform(self):

        ########### Create product transform1
        self.product_transform1 = ProductTransform.objects.create(
            user=self.user1,
            store=self.store1,
            total_quantity=1300,
        )

        # Create product_transform1
        ProductTransformLine.objects.create(
            product_transform=self.product_transform1,
            source_product=self.product1,
            target_product=self.product3,
            quantity=10,
            cost=150,
        )
    
        # Create product_transform2
        ProductTransformLine.objects.create(
            product_transform=self.product_transform1,
            source_product=self.product2,
            target_product=self.product3,
            quantity=14,
            cost=100,
        )


        ########### Create product transform2
        self.product_transform2 = ProductTransform.objects.create(
            user=self.user1,
            store=self.store2,
            total_quantity=1400
        )

        # Create product_transform1
        ProductTransformLine.objects.create(
            product_transform=self.product_transform2,
            source_product=self.product1,
            target_product=self.product3,
            quantity=10,
            cost=150,
        )
    
        # Create product_transform2
        ProductTransformLine.objects.create(
            product_transform=self.product_transform2,
            source_product=self.product2,
            target_product=self.product3,
            quantity=5,
            cost=100,
        )

    def test_view_can_delete_a_product_transform(self):

        response = self.client.delete(
            reverse('api:product_transform_view', 
            args=(self.product_transform1.reg_no,))
        )
        self.assertEqual(response.status_code, 204)

        # Confirm the product_transform was deleted
        self.assertEqual(ProductTransform.objects.filter(
            reg_no=self.product_transform1.reg_no).exists(), False
        )

    def test_view_can_handle_wrong_product_transform_reg_no(self):

        response = self.client.delete(
            reverse('api:product_transform_view', 
            args=(44444,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the product_transform was not deleted
        self.assertEqual(ProductTransform.objects.filter(
            reg_no=self.product_transform1.reg_no).exists(), True
        )

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:product_transform_view', 
            args=(self.product_transform1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the product_transform was not deleted
        self.assertEqual(ProductTransform.objects.filter(
            reg_no=self.product_transform1.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_employee_user(self):

        # Login a employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # response = self.client.delete(
        #     reverse('api:product_transform_view', 
        #     args=(self.product_transform1.reg_no,))
        # )
        # self.assertEqual(response.status_code, 404)

        # # Confirm the product_transform was not deleted
        # self.assertEqual(ProductTransform.objects.filter(
        #     reg_no=self.product_transform1.reg_no).exists(), True
        # )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:product_transform_view', 
            args=(self.product_transform1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

        # Confirm the product_transform was not deleted
        self.assertEqual(ProductTransform.objects.filter(
            reg_no=self.product_transform1.reg_no).exists(), True
        )
      
class ProductTransformViewForEditing2TestCase(APITestCase, InitialUserDataMixin):
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
        ms = MySetting.objects.get(name="main")
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email="john@gmail.com")
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        # Create models
        # Creates products
        self.product1 = Product.objects.create(
            profile=self.top_profile1,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        self.product3 = Product.objects.create(
            profile=self.top_profile1,
            name="Gloss",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        self.product4 = Product.objects.create(
            profile=self.top_profile1,
            name="Band",
            price=3800,
            cost=1200,
            barcode='code123'
        )

        self.product5 = Product.objects.create(
            profile=self.top_profile1,
            name="Tea",
            price=3800,
            cost=1200,
            barcode='code123'
        )

        # Change stock amount
        # Product1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 20
        stock_level.save()

        # Product2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 45
        stock_level.save()

        # Product3
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product3)
        stock_level.units = 60
        stock_level.save()

        self.create_product_transform()

    def create_product_transform(self):


        # Create master product with 2 productions
        product_3_map_for_product_1 = ProductProductionMap.objects.create(
            product_map=self.product3,
            quantity=50
        )

        product_3_map_for_product_2 = ProductProductionMap.objects.create(
            product_map=self.product3,
            quantity=100
        )

        product_2_map_for_product_1 = ProductProductionMap.objects.create(
            product_map=self.product2,
            quantity=60
        )

        self.product1.productions.add(product_3_map_for_product_1, product_2_map_for_product_1)
        self.product2.productions.add(product_3_map_for_product_2)

        ########### Create product transform1
        self.product_transform = ProductTransform.objects.create(
            user=self.user1,
            store=self.store1,
            total_quantity=1300,
        )

        # Create product_transform1
        self.po_line1=ProductTransformLine.objects.create(
            product_transform=self.product_transform,
            source_product=self.product1,
            target_product=self.product3,
            quantity=10,
            cost=150,
        )
    
        # Create product_transform2
        self.po_line2=ProductTransformLine.objects.create(
            product_transform=self.product_transform,
            source_product=self.product2,
            target_product=self.product3,
            quantity=14,
            cost=100,
        )

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """
        payload = {
            "status": ProductTransform.PRODUCT_TRANSFORM_PENDING,
            "store_reg_no": self.store2.reg_no,
            "lines_info": [
                {
                    "quantity": 5,
                    "added_quantity": 2,
                    "cost": 120,
                    "target_product_reg_no": self.product3.reg_no,
                    "reg_no": self.po_line1.reg_no,
                    "is_dirty": True,
                },
                {
                    "quantity": 7,
                    "added_quantity": 3,
                    "cost": 80,
                    "target_product_reg_no": self.product3.reg_no,
                    "reg_no": self.po_line2.reg_no,
                    "is_dirty": True,
                },
            ],
            "lines_to_add": [],
            "lines_to_remove": [],
        }

        return payload
    
    def test_view_can_edit_model_successfully(self):

        payload = self.get_premade_payload()

        # Count Number of Queries #
        # with self.assertNumQueries(14):
        response = self.client.put(
            reverse("api:product_transform_view", args=(self.product_transform.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 200)

        ##### ProductTransform
        pt = ProductTransform.objects.get()

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(pt.user, self.user1)
        self.assertEqual(pt.store, self.store2)
        self.assertEqual(pt.status, ProductTransform.PRODUCT_TRANSFORM_PENDING)
        self.assertEqual(pt.total_quantity, 12.00)
        self.assertTrue(pt.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((pt.created_date).strftime("%B, %d, %Y"), today)

        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.product_transform, pt)
        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertEqual(line1.cost, payload["lines_info"][0]["cost"])
        self.assertEqual(line1.amount, 600.00)
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.product_transform, pt)
        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertEqual(line2.cost, payload["lines_info"][1]["cost"])
        self.assertEqual(line2.amount, 560.00)

        # Confirm Stock levels were not changed
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product1).units,
            20
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product2).units,
            45
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product3).units,
            60
        )

    def test_view_can_edit_model_successfully_without_changing_stock(self):

        payload = self.get_premade_payload()
        payload["store_reg_no"] = self.store1.reg_no

        # Count Number of Queries #
        # with self.assertNumQueries(14):
        response = self.client.put(
            reverse("api:product_transform_view", args=(self.product_transform.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 200)

        ##### ProductTransform
        pt = ProductTransform.objects.get()

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(pt.user, self.user1)
        self.assertEqual(pt.store, self.store1)
        self.assertEqual(pt.status, ProductTransform.PRODUCT_TRANSFORM_PENDING)
        self.assertEqual(pt.total_quantity, 12.00)
        self.assertTrue(pt.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((pt.created_date).strftime("%B, %d, %Y"), today)

        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.product_transform, pt)
        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertEqual(line1.cost, payload["lines_info"][0]["cost"])
        self.assertEqual(line1.amount, 600.00)
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.product_transform, pt)
        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertEqual(line2.cost, payload["lines_info"][1]["cost"])
        self.assertEqual(line2.amount, 560.00)

        # Confirm Stock levels were not changed
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product1).units,
            20
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product2).units,
            45
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product3).units,
            60
        )

    def test_view_can_edit_model_successfully_and_changing_stock(self):

        payload = self.get_premade_payload()
        payload['status'] = ProductTransform.PRODUCT_TRANSFORM_RECEIVED
        payload["store_reg_no"] = self.store1.reg_no

        # Count Number of Queries #
        # with self.assertNumQueries(14):
        response = self.client.put(
            reverse("api:product_transform_view", args=(self.product_transform.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 200)

        ##### ProductTransform
        pt = ProductTransform.objects.get()

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(pt.user, self.user1)
        self.assertEqual(pt.store, self.store1)
        self.assertEqual(pt.status, ProductTransform.PRODUCT_TRANSFORM_RECEIVED)
        self.assertEqual(pt.order_completed, True)
        self.assertEqual(pt.total_quantity, 12.00)
        self.assertTrue(pt.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((pt.created_date).strftime("%B, %d, %Y"), today)

        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.product_transform, pt)
        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertEqual(line1.cost, payload["lines_info"][0]["cost"])
        self.assertEqual(line1.amount, 600.00)
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.product_transform, pt)
        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertEqual(line2.cost, payload["lines_info"][1]["cost"])
        self.assertEqual(line2.amount, 560.00)

        # Confirm Stock levels were not changed
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product1).units,
            15
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product2).units,
            38
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product3).units,
            1010.00
        )

    def test_view_cant_edit_a_model_when_it_has_been_received_successfully(self):

        # Make the Purchase order to be received
        po = ProductTransform.objects.get()
        po.status = ProductTransform.PRODUCT_TRANSFORM_RECEIVED
        po.save()

        payload = self.get_premade_payload()

        # Count Number of Queries #
        # with self.assertNumQueries(14):
        response = self.client.put(
            reverse("api:product_transform_view", args=(self.product_transform.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 200)

        ##### ProductTransform
        pt = ProductTransform.objects.get()

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(pt.user, self.user1)
        self.assertNotEqual(pt.store, self.store2)
        self.assertEqual(pt.status, ProductTransform.PRODUCT_TRANSFORM_RECEIVED)
        self.assertNotEqual(pt.total_quantity, 12.00)
        self.assertTrue(pt.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((pt.created_date).strftime("%B, %d, %Y"), today)

        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.product_transform, pt)
        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertNotEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertNotEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertNotEqual(line1.cost, payload["lines_info"][0]["cost"])
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.product_transform, pt)
        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertNotEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertNotEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertNotEqual(line2.cost, payload["lines_info"][1]["cost"])

    def test_view_can_edit_product_map_successfully(self):

        payload = self.get_premade_payload()
        payload['lines_info'][0]['target_product_reg_no'] = self.product2.reg_no
 
        # Count Number of Queries #
        # with self.assertNumQueries(14):
        response = self.client.put(
            reverse("api:product_transform_view", args=(self.product_transform.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 200)

        ##### ProductTransform
        pt = ProductTransform.objects.get()

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(pt.user, self.user1)
        self.assertEqual(pt.store, self.store2)
        self.assertEqual(pt.status, ProductTransform.PRODUCT_TRANSFORM_PENDING)
        self.assertEqual(pt.total_quantity, 12.00)
        self.assertTrue(pt.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((pt.created_date).strftime("%B, %d, %Y"), today)

        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.product_transform, pt)
        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product2)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertEqual(line1.cost, payload["lines_info"][0]["cost"])
        self.assertEqual(line1.amount, 600.00)
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.product_transform, pt)
        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertEqual(line2.cost, payload["lines_info"][1]["cost"])
        self.assertEqual(line2.amount, 560.00)

        # Confirm Stock levels were not changed
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product1).units,
            20
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product2).units,
            45
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product3).units,
            60
        )

    def test_if_view_can_handle_with_wrong_store_reg_no(self):

        wrong_reg_nos = [
            # 33463476347374, # Wrong reg no
            self.store3.reg_no, # Store for another user
            # 11111111111111111111111111111111111111 # Long reg no
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_reg_nos:

            payload = self.get_premade_payload()
            payload['store_reg_no'] = wrong_reg_no

            response = self.client.put(
                reverse(
                    'api:product_transform_view', 
                    args=(self.product_transform.reg_no,)
                ), 
                payload
            )

            self.assertEqual(response.status_code, 404)

        ##### Confirm no edit was done
        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertNotEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertNotEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertNotEqual(line1.cost, payload["lines_info"][0]["cost"])
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertNotEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertNotEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertNotEqual(line2.cost, payload["lines_info"][1]["cost"])

    def test_if_view_wont_edit_product_transform_lines_when_is_dirty_is_false(self):

        payload = self.get_premade_payload()
        payload['lines_info'][0]['is_dirty'] = False

        response = self.client.put(
            reverse(
                'api:product_transform_view', 
                args=(self.product_transform.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertNotEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertNotEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertNotEqual(line1.cost, payload["lines_info"][0]["cost"])
        
        # ProductTransform line 2
        line2 = lines[1]
        
        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertEqual(line2.cost, payload["lines_info"][1]["cost"])

    def test_if_view_can_can_accept_an_empty_lines_info(self):

        payload = self.get_premade_payload()
        payload['lines_info'] = []

        response = self.client.put(
            reverse(
                'api:product_transform_view', 
                args=(self.product_transform.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

    def test_if_view_can_can_handle_a_wrong_product_transform_line_reg_no(self):

        payload = self.get_premade_payload()
        payload['lines_info'][0]['reg_no'] = 112121

        response = self.client.put(
            reverse(
                'api:product_transform_view', 
                args=(self.product_transform.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertNotEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertNotEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertNotEqual(line1.cost, payload["lines_info"][0]["cost"])
        
        # ProductTransform line 2
        line2 = lines[1]
        
        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertEqual(line2.cost, payload["lines_info"][1]["cost"])

    def test_if_a_product_transform_line_can_be_added(self):

        payload = self.get_premade_payload()
        payload['lines_to_add'] = [
            {
                'source_product_reg_no': self.product1.reg_no,
                'target_product_reg_no': self.product4.reg_no,
                'quantity': 15,
                'added_quantity': 9,
                'cost': 320
            }
        ]

        response = self.client.put(
            reverse(
                'api:product_transform_view', 
                args=(self.product_transform.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by('id')
        self.assertEqual(lines.count(), 3)

        # Model 1
        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertEqual(line1.cost, payload["lines_info"][0]["cost"])
        self.assertEqual(line1.amount, 600.00)
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertEqual(line2.cost, payload["lines_info"][1]["cost"])
        self.assertEqual(line2.amount, 560.00)

        # ProductTransform line 3
        line3 = lines[2]

        self.assertEqual(line3.source_product, self.product1)
        self.assertEqual(line3.target_product, self.product4)
        self.assertEqual(
            line3.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line3.target_product_info, 
            {
                'name': self.product4.name,
                'reg_no': self.product4.reg_no
            }
        )
        self.assertEqual(line3.quantity, payload["lines_to_add"][0]["quantity"])
        self.assertEqual(line3.added_quantity, payload["lines_to_add"][0]["added_quantity"])
        self.assertEqual(line3.cost, payload["lines_to_add"][0]["cost"])
        self.assertEqual(line3.amount, 4800.00)

    def test_if_multiple_product_transform_lines_can_be_added(self):
        
        ProductTransformLine.objects.all().delete()

        product_transform_lines = ProductTransformLine.objects.all().order_by('id')
        self.assertEqual(product_transform_lines.count(), 0)

        payload = self.get_premade_payload()
        payload['lines_to_add'] = [
            {
                'source_product_reg_no': self.product1.reg_no,
                'target_product_reg_no': self.product4.reg_no,
                'quantity': 15,
                'added_quantity': 9,
                'cost': 320
            },
            {
                'source_product_reg_no': self.product1.reg_no,
                'target_product_reg_no': self.product5.reg_no,
                'quantity': 3,
                'added_quantity': 1,
                'cost': 103
            },
        ]

        response = self.client.put(
            reverse(
                'api:product_transform_view', 
                args=(self.product_transform.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by('id')
        self.assertEqual(lines.count(), 2)

        # Model 1
        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product4)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product4.name,
                'reg_no': self.product4.reg_no
            }
        )
        self.assertEqual(line1.quantity, payload["lines_to_add"][0]["quantity"])
        self.assertEqual(line1.added_quantity, payload["lines_to_add"][0]["added_quantity"])
        self.assertEqual(line1.cost, payload["lines_to_add"][0]["cost"])
        self.assertEqual(line1.amount, 4800.00)
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.source_product, self.product1)
        self.assertEqual(line2.target_product, self.product5)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product5.name,
                'reg_no': self.product5.reg_no
            }
        )
        self.assertEqual(line2.quantity, payload["lines_to_add"][1]["quantity"])
        self.assertEqual(line2.added_quantity, payload["lines_to_add"][1]["added_quantity"])
        self.assertEqual(line2.cost, payload["lines_to_add"][1]["cost"])
        self.assertEqual(line2.amount, 309.00)


    def test_if_view_can_handle_a_wrong_source_product_reg_no_when_adding(self):

        payload = self.get_premade_payload()
        payload['lines_to_add'] = [
            {
                'source_product_reg_no': 111,
                'target_product_reg_no': self.product4.reg_no,
                'quantity': 15,
                'cost': 320
            },
        ]

        response = self.client.put(
            reverse(
                'api:product_transform_view', 
                args=(self.product_transform.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 2)

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertEqual(line1.cost, payload["lines_info"][0]["cost"])
        self.assertEqual(line1.amount, 600.00)
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertEqual(line2.cost, payload["lines_info"][1]["cost"])
        self.assertEqual(line2.amount, 560.00)

    def test_if_view_can_handle_a_wrong_target_product_reg_no_when_adding(self):

        payload = self.get_premade_payload()
        payload['lines_to_add'] = [
            {
                'source_product_reg_no': self.product4.reg_no,
                'target_product_reg_no': 111,
                'quantity': 15,
                'cost': 320
            },
        ]

        response = self.client.put(
            reverse(
                'api:product_transform_view', 
                args=(self.product_transform.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 2)

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertEqual(line1.cost, payload["lines_info"][0]["cost"])
        self.assertEqual(line1.amount, 600.00)
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertEqual(line2.cost, payload["lines_info"][1]["cost"])
        self.assertEqual(line2.amount, 560.00)

    def test_if_a_product_transform_line_can_be_removed(self):

        payload = self.get_premade_payload()
        payload['lines_to_remove'] = [
            {'reg_no': self.po_line2.reg_no},
        ]

        response = self.client.put(
            reverse(
                'api:product_transform_view', 
                args=(self.product_transform.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 1)

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertEqual(line1.cost, payload["lines_info"][0]["cost"])
        self.assertEqual(line1.amount, 600.00)

    def test_if_all_store_delivery_lines_can_be_removed(self):

        payload = self.get_premade_payload()
        payload['lines_to_remove'] = [
            {'reg_no': self.po_line1.reg_no},
            {'reg_no': self.po_line2.reg_no,},
        ]

        # Count Number of Queries #
        # with self.assertNumQueries(11):
        response = self.client.put(
            reverse(
                'api:product_transform_view', 
                args=(self.product_transform.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        product_transform_lines = ProductTransformLine.objects.all().order_by('id')
        self.assertEqual(product_transform_lines.count(), 0)

    def test_if_when_a_wrong_reg_no_is_passed_in_lines_info_delete(self):

        payload = self.get_premade_payload()
        payload['lines_to_remove'] = [{'reg_no': 111}]

        response = self.client.put(
            reverse(
                'api:product_transform_view', 
                args=(self.product_transform.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 2)

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertEqual(line1.cost, payload["lines_info"][0]["cost"])
        self.assertEqual(line1.amount, 600.00)
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertEqual(line2.cost, payload["lines_info"][1]["cost"])
        self.assertEqual(line2.amount, 560.00)

    def test_view_can_only_be_edited_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse(
                'api:product_transform_view', 
                args=(self.product_transform.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 404)

        ##### Confirm no edit was done
        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertNotEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertNotEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertNotEqual(line1.cost, payload["lines_info"][0]["cost"])
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertNotEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertNotEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertNotEqual(line2.cost, payload["lines_info"][1]["cost"])

    # def test_view_cant_be_edited_by_an_employee_user(self):

    #     # Login a employee user
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     payload = self.get_premade_payload()

    #     response = self.client.put(
    #         reverse(
    #             'api:product_transform_view', 
    #             args=(self.product_transform.reg_no,)
    #         ), 
    #         payload
    #     )
    #     self.assertEqual(response.status_code, 404)

    #     ##### Confirm no edit was done
    #     ##### ProductTransformLines
    #     product_transform_lines = ProductTransformLine.objects.all().order_by('id')

    #     # Model 1
    #     self.assertEqual(product_transform_lines[0].product, self.product1)
    #     self.assertNotEqual(
    #         product_transform_lines[0].quantity, 
    #         payload['lines_info'][0]['quantity']
    #     )
    #     self.assertNotEqual(
    #         product_transform_lines[0].purchase_cost, 
    #         payload['lines_info'][0]['purchase_cost']
    #     )

    #     # Model 2
    #     self.assertEqual(product_transform_lines[1].product, self.product2)
    #     self.assertNotEqual(
    #         product_transform_lines[1].quantity, 
    #         payload['lines_info'][1]['quantity']
    #     )
    #     self.assertNotEqual(
    #         product_transform_lines[1].purchase_cost, 
    #         payload['lines_info'][1]['purchase_cost']
    #     )

    def test_view_cant_be_edited_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse(
                'api:product_transform_view', 
                args=(self.product_transform.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 401)

        ##### Confirm no edit was done
        ##### ProductTransformLines
        lines = ProductTransformLine.objects.all().order_by("id")

        # ProductTransform line 1
        line1 = lines[0]

        self.assertEqual(line1.source_product, self.product1)
        self.assertEqual(line1.target_product, self.product3)
        self.assertEqual(
            line1.source_product_info, 
            {
                'name': self.product1.name,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertNotEqual(line1.quantity, payload["lines_info"][0]["quantity"])
        self.assertNotEqual(line1.added_quantity, payload["lines_info"][0]["added_quantity"])
        self.assertNotEqual(line1.cost, payload["lines_info"][0]["cost"])
        
        # ProductTransform line 2
        line2 = lines[1]

        self.assertEqual(line2.source_product, self.product2)
        self.assertEqual(line2.target_product, self.product3)
        self.assertEqual(
            line2.source_product_info, 
            {
                'name': self.product2.name,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                'name': self.product3.name,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertNotEqual(line2.quantity, payload["lines_info"][1]["quantity"])
        self.assertNotEqual(line2.added_quantity, payload["lines_info"][1]["added_quantity"])
        self.assertNotEqual(line2.cost, payload["lines_info"][1]["cost"])
