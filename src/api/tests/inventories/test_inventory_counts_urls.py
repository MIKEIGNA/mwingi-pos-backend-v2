import json
from pprint import pprint

from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.initial_user_data import InitialUserDataMixin

from core.test_utils.custom_testcase import APITestCase
from inventories.models.stock_models import StockLevel

from products.models import Product

from mysettings.models import MySetting
from inventories.models import InventoryCount, InventoryCountLine


class InventoryCountIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

    def create_inventory_count(self):

        ########### Create stock adjustment1
        self.inventory_count1 = InventoryCount.objects.create(
            user=self.user1,
            store=self.store1,
            status=InventoryCount.INVENTORY_COUNT_PENDING,
            notes='This is just a simple note1',
        )

        # Create inventory_count1
        InventoryCountLine.objects.create(
            inventory_count=self.inventory_count1,
            product=self.product1,
            expected_stock=100,
            counted_stock=77,
        )
    
        # Create inventory_count2
        InventoryCountLine.objects.create(
            inventory_count=self.inventory_count1,
            product=self.product2,
            expected_stock=155,
            counted_stock=160,
        )


        ########### Create stock adjustment2
        self.inventory_count2 = InventoryCount.objects.create(
            user=self.user1,
            store=self.store2,
            status=InventoryCount.INVENTORY_COUNT_COMPLETED,
            notes='This is just a simple note2',
        )

        # Create inventory_count1
        InventoryCountLine.objects.create(
            inventory_count=self.inventory_count2,
            product=self.product1,
            expected_stock=200,
            counted_stock=87,
        )
    
        # Create inventory_count2
        InventoryCountLine.objects.create(
            inventory_count=self.inventory_count2,
            product=self.product2,
            counted_stock=260,
        )

    def test_view_returns_the_user_inventory_counts_only(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        response = self.client.get(reverse('api:inventory_count_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.inventory_count2.__str__(),  
                    'store_name': self.store2.name, 
                    'status': self.inventory_count2.status, 
                    'reg_no': self.inventory_count2.reg_no, 
                    'creation_date': self.inventory_count2.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'completion_date': self.inventory_count2.get_completed_date(
                        self.user1.get_user_timezone()
                    )
                }, 
                {
                    'name': self.inventory_count1.__str__(), 
                    'store_name': self.store1.name, 
                    'status': self.inventory_count1.status, 
                    'reg_no': self.inventory_count1.reg_no, 
                    'creation_date': self.inventory_count1.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'completion_date': self.inventory_count1.get_completed_date(
                        self.user1.get_user_timezone()
                    )
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
                reverse('api:inventory_count_index'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all inventory_counts
        InventoryCount.objects.all().delete()

        pagination_page_size = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION

        model_num_to_be_created = pagination_page_size+1

        inventory_count_names = []
        for i in range(model_num_to_be_created):
            inventory_count_names.append(f'New InventoryCount{i}')

        names_length = len(inventory_count_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm inventory_counts
        for i in range(names_length):
            InventoryCount.objects.create(
                user=self.user1,
                store=self.store1,
                notes=f'This is just a simple note{i}',
            )

        self.assertEqual(
            InventoryCount.objects.filter(user=self.user1).count(),
            names_length)  # Confirm models were created

    
        inventory_counts = InventoryCount.objects.filter(user=self.user1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(17):
            response = self.client.get(
                reverse('api:inventory_count_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 
            'http://testserver/api/inventory-counts/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all stock adjustments are listed except the first one since it's in the next paginated page #
        i = 0
        for inventory_count in inventory_counts[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], inventory_count.__str__())
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], inventory_count.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
                reverse('api:inventory_count_index')  + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/inventory-counts/',
            'results': [
                {
                    'name': inventory_counts[0].__str__(), 
                    'store_name': self.store1.name, 
                    'status': inventory_counts[0].status, 
                    'reg_no': inventory_counts[0].reg_no, 
                    'creation_date': inventory_counts[0].get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'completion_date': inventory_counts[0].get_completed_date(
                        self.user1.get_user_timezone()
                    )
                },
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
    
    def test_view_can_filter_status(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?status={InventoryCount.INVENTORY_COUNT_COMPLETED}'
        response = self.client.get(reverse('api:inventory_count_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.inventory_count2.__str__(),  
                    'store_name': self.store2.name, 
                    'status': self.inventory_count2.status, 
                    'reg_no': self.inventory_count2.reg_no, 
                    'creation_date': self.inventory_count2.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'completion_date': self.inventory_count2.get_completed_date(
                        self.user1.get_user_timezone()
                    )
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

        param = f'?search={self.inventory_count2.reg_no}'
        response = self.client.get(reverse('api:inventory_count_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.inventory_count2.__str__(),  
                    'store_name': self.store2.name, 
                    'status': self.inventory_count2.status, 
                    'reg_no': self.inventory_count2.reg_no, 
                    'creation_date': self.inventory_count2.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'completion_date': self.inventory_count2.get_completed_date(
                        self.user1.get_user_timezone()
                    )
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
        response = self.client.get(reverse('api:inventory_count_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.inventory_count1.__str__(),
                    'store_name': self.store1.name,  
                    'status': self.inventory_count1.status, 
                    'reg_no': self.inventory_count1.reg_no, 
                    'creation_date': self.inventory_count1.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'completion_date': self.inventory_count1.get_completed_date(
                        self.user1.get_user_timezone()
                    )
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

    def test_view_returns_empty_when_there_are_no_inventory_counts(self):

        # First delete all inventory_counts
        InventoryCount.objects.all().delete()

        response = self.client.get(
                reverse('api:inventory_count_index'))
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
                reverse('api:inventory_count_index'))
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
    #             reverse('api:inventory_count_index'))
    #     self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:inventory_count_index'))
        self.assertEqual(response.status_code, 401)

class InventoryCountCreateViewTestCase(APITestCase, InitialUserDataMixin):

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

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """
        
        payload = {
            'notes': 'A simple note',
            'store_reg_no': self.store1.reg_no,
            'inventory_count_lines': [
                {
                    'product_reg_no': self.product1.reg_no,
                    'expected_stock': 100,
                    'counted_stock': 77,
                },
                {
                    'product_reg_no': self.product2.reg_no,
                    'expected_stock': 155,
                    'counted_stock': 160,
                }
            ]
        }

        return payload    

    def test_if_view_can_create_a_receipt(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:inventory_count_index'), 
            payload
        )

        self.assertEqual(response.status_code, 201)

        ic = InventoryCount.objects.get(store=self.store1)

        # Confirm model creation
        self.assertEqual(InventoryCount.objects.all().count(), 1)
    
        product1 = Product.objects.get(name='Shampoo')
        product2 = Product.objects.get(name='Conditioner')

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(ic.user, self.user1)
        self.assertEqual(ic.store, self.store1)
        self.assertEqual(ic.notes, 'A simple note')
        self.assertEqual(ic.mismatch_found, False)
        self.assertTrue(ic.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((ic.created_date).strftime("%B, %d, %Y"), today)


        # Confirm receipt line model creation
        self.assertEqual(InventoryCountLine.objects.filter(inventory_count=ic).count(), 2)

        lines = InventoryCountLine.objects.filter(inventory_count=ic).order_by('id')

        # InventoryCount line 1
        line1 = lines[0]

        self.assertEqual(line1.inventory_count, ic)
        self.assertEqual(line1.product, product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(line1.expected_stock, 100.00)
        self.assertEqual(line1.counted_stock, 77.00)
        self.assertEqual(line1.difference, -23.00)
        self.assertEqual(line1.cost_difference, -23000.00)
        

        # InventoryCount line 2
        line2 = lines[1]

        self.assertEqual(line2.inventory_count, ic)
        self.assertEqual(line2.product, product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(line2.expected_stock, 155.00)
        self.assertEqual(line2.counted_stock, 160.00)
        self.assertEqual(line2.difference, 5.00)
        self.assertEqual(line2.cost_difference, 6000.00)


        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=True
        ms.save()
              
        response = self.client.post(
            reverse('api:inventory_count_index'), 
            payload,
        )
            
        self.assertEqual(response.status_code, 401)

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
                reverse('api:inventory_count_index'), 
                payload
            )

            self.assertEqual(response.status_code, 404)

            # Confirm model was not creation
            self.assertEqual(InventoryCount.objects.all().count(), 0)
    
    def test_if_view_can_handle_a_line_wrong_product_reg_no(self):

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
            InventoryCount.objects.all().delete()
            InventoryCountLine.objects.all().delete()

            payload['inventory_count_lines'][0]['product_reg_no'] = wrong_reg_no

            response = self.client.post(
                reverse('api:inventory_count_index'),
                payload,
            )

            self.assertEqual(response.status_code, 400)

            result = {'non_field_errors': 'Product error.'}
            self.assertEqual(response.data, result)


            # Confirm model creation
            self.assertEqual(InventoryCount.objects.all().count(), 0)

    def test_if_view_url_can_throttle_post_requests(self):

        payload = self.get_premade_payload()

        throttle_rate = int(settings.THROTTLE_RATES['api_inventory_count_rate'].split("/")[0])
    
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:inventory_count_index'),
                payload,
            )
            self.assertEqual(response.status_code, 201)


        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional 
        # request if the previous request was not throttled 
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:inventory_count_index'),
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
            reverse('api:inventory_count_index'), 
            payload,
        )
        self.assertEqual(response.status_code, 401)

class InventoryCountViewForViewingTestCase(APITestCase, InitialUserDataMixin):

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

    def create_inventory_count(self):

        ########### Create stock adjustment1
        self.inventory_count1 = InventoryCount.objects.create(
            user=self.user1,
            store=self.store1,
            notes='This is just a simple note1',
        )

        # Create inventory_count1
        InventoryCountLine.objects.create(
            inventory_count=self.inventory_count1,
            product=self.product1,
            expected_stock=100,
            counted_stock=77,
        )
    
        # Create inventory_count2
        InventoryCountLine.objects.create(
            inventory_count=self.inventory_count1,
            product=self.product2,
            expected_stock=155,
            counted_stock=160,
        )


        ########### Create stock adjustment2
        self.inventory_count2 = InventoryCount.objects.create(
            user=self.user1,
            store=self.store2,
            notes='This is just a simple note2',
        )

        # Create inventory_count1
        InventoryCountLine.objects.create(
            inventory_count=self.inventory_count2,
            product=self.product1,
            expected_stock=200,
            counted_stock=87,
        )
    
        # Create inventory_count2
        InventoryCountLine.objects.create(
            inventory_count=self.inventory_count2,
            product=self.product2,
            counted_stock=260,
        )

    def test_view_can_be_called_successefully(self):

        inventory_count = InventoryCount.objects.get(
            notes='This is just a simple note1'
        )

        inventory_count.status = InventoryCount.INVENTORY_COUNT_COMPLETED
        inventory_count.save()

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.get(
            reverse('api:inventory_count_view', 
            args=(inventory_count.reg_no,))
        )
        self.assertEqual(response.status_code, 200)

        lines = inventory_count.inventorycountline_set.all().order_by('id')
 
        result = {
            'name': inventory_count.__str__(), 
            'notes': inventory_count.notes,
            'store_data': inventory_count.get_store_data(),
            'status': inventory_count.status, 
            'reg_no': inventory_count.reg_no, 
            'counted_by': self.user1.get_full_name(), 
            'creation_date': inventory_count.get_created_date(
                self.user1.get_user_timezone()
            ), 
            'completion_date': inventory_count.get_completed_date(
                self.user1.get_user_timezone()
            ),
            'line_data': [
                {
                    'product_info': {
                        'name': self.product1.name, 
                        'sku': self.product1.sku,
                        'reg_no': self.product1.reg_no
                    }, 
                    'expected_stock': str(lines[0].expected_stock),
                    'counted_stock': str(lines[0].counted_stock),
                    'difference': str(lines[0].difference), 
                    'cost_difference':str(lines[0].cost_difference),
                    'product_cost':str(lines[0].product_cost),
                    'reg_no': str(lines[0].reg_no)
                },
                {
                    'product_info': {
                        'name': self.product2.name, 
                        'sku': self.product2.sku,
                        'reg_no': self.product2.reg_no
                    }, 
                    'expected_stock': str(lines[1].expected_stock),
                    'counted_stock': str(lines[1].counted_stock),
                    'difference': str(lines[1].difference), 
                    'cost_difference':str(lines[1].cost_difference),
                    'product_cost':str(lines[1].product_cost),
                    'reg_no': str(lines[1].reg_no)
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
            reverse('api:inventory_count_view', args=(self.inventory_count1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

    def test_view_can_handle_wrong_inventory_count_reg_no(self):

        response = self.client.get(
            reverse('api:inventory_count_view', args=(4646464,)))
        self.assertEqual(response.status_code, 404)

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:inventory_count_view', 
            args=(self.inventory_count1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    # def test_view_cant_be_viewed_by_an_employee_user(self):

    #     # Login a employee user
    #     # Include an appropriate `Authorization:` header on all requests.
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     response = self.client.get(
    #         reverse('api:inventory_count_view', 
    #         args=(self.inventory_count1.reg_no,))
    #     )
    #     self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:inventory_count_view', 
            args=(self.inventory_count1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

class InventoryCountViewForEditngTestCase(APITestCase, InitialUserDataMixin):

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

        self.product3 = Product.objects.create(
            profile=self.top_profile1,
            name="Sugar",
            price=4800,
            cost=3200,
            barcode="code123",
        )
        self.product3.stores.add(self.store1, self.store2)


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


        self.create_inventory_count()

    def create_inventory_count(self):

        ########### Create stock adjustment1
        self.inventory_count = InventoryCount.objects.create(
            user=self.user1,
            store=self.store1,
            notes='This is just a simple note1',
        )

        # Create inventory_count1
        self.ic_line1 = InventoryCountLine.objects.create(
            inventory_count=self.inventory_count,
            product=self.product1,
            expected_stock=100,
            counted_stock=77,
        )
    
        # Create inventory_count2
        self.ic_line2 = InventoryCountLine.objects.create(
            inventory_count=self.inventory_count,
            product=self.product2,
            expected_stock=155,
            counted_stock=160,
        )

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """
        payload = {
            'status': InventoryCount.INVENTORY_COUNT_PENDING,
            'notes': 'A simple note',
            'lines_info': [
                {
                    'expected_stock': 200,
                    'counted_stock': 178,
                    "reg_no": self.ic_line1.reg_no
                },
                {
                    'expected_stock': 255,
                    'counted_stock': 320,
                    "reg_no": self.ic_line2.reg_no
                }
            ],
            "lines_to_add": [],
            "lines_to_remove": [],
        }

        return payload
 
    def test_view_can_edit_model_successfully_without_changing_stock(self):
        
        payload = self.get_premade_payload()

        # Count Number of Queries #
        # with self.assertNumQueries(14):
        response = self.client.put(
            reverse("api:inventory_count_view", args=(self.inventory_count.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 200)

        ##### InventoryCount
        ic = InventoryCount.objects.get()

        self.assertEqual(ic.user, self.user1)
        self.assertEqual(ic.store, self.store1)
        self.assertEqual(ic.notes, payload['notes'])
        self.assertEqual(ic.mismatch_found, False)
        self.assertEqual(ic.status, InventoryCount.INVENTORY_COUNT_PENDING)

        ##### InventoryCountLines
        lines = InventoryCountLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 2)

        # InventoryCount line 1
        line1 = lines[0]

        self.assertEqual(line1.inventory_count, ic)
        self.assertEqual(line1.product, self.product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(line1.expected_stock, payload["lines_info"][0]["expected_stock"])
        self.assertEqual(line1.counted_stock, payload["lines_info"][0]["counted_stock"])
        self.assertEqual(line1.difference, -22.00)
        self.assertEqual(line1.cost_difference, -22000.00)
        

        # InventoryCount line 2
        line2 = lines[1]

        self.assertEqual(line2.inventory_count, ic)
        self.assertEqual(line2.product, self.product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(line2.expected_stock, payload["lines_info"][1]["expected_stock"])
        self.assertEqual(line2.counted_stock, payload["lines_info"][1]["counted_stock"])
        self.assertEqual(line2.difference, 65.00)
        self.assertEqual(line2.cost_difference, 78000.00)

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

    def test_view_can_edit_model_successfully_and_change_stock(self):
        
        payload = self.get_premade_payload()
        payload['status'] = InventoryCount.INVENTORY_COUNT_COMPLETED

        # Count Number of Queries #
        # with self.assertNumQueries(14):
        response = self.client.put(
            reverse("api:inventory_count_view", args=(self.inventory_count.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 200)

        ##### InventoryCount
        ic = InventoryCount.objects.get()

        self.assertEqual(ic.user, self.user1)
        self.assertEqual(ic.store, self.store1)
        self.assertEqual(ic.notes, payload['notes'])
        self.assertEqual(ic.mismatch_found, False)
        self.assertEqual(ic.status, InventoryCount.INVENTORY_COUNT_COMPLETED)

        ##### InventoryCountLines
        lines = InventoryCountLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 2)

        # InventoryCount line 1
        line1 = lines[0]

        self.assertEqual(line1.inventory_count, ic)
        self.assertEqual(line1.product, self.product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(line1.expected_stock, payload["lines_info"][0]["expected_stock"])
        self.assertEqual(line1.counted_stock, payload["lines_info"][0]["counted_stock"])
        self.assertEqual(line1.difference, -22.00)
        self.assertEqual(line1.cost_difference, -22000.00)
        

        # InventoryCount line 2
        line2 = lines[1]

        self.assertEqual(line2.inventory_count, ic)
        self.assertEqual(line2.product, self.product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(line2.expected_stock, payload["lines_info"][1]["expected_stock"])
        self.assertEqual(line2.counted_stock, payload["lines_info"][1]["counted_stock"])
        self.assertEqual(line2.difference, 65.00)
        self.assertEqual(line2.cost_difference, 78000.00)

    def test_view_cant_edit_a_model_when_it_has_been_received_successfully(self):

        # Make the Purchase order to be received
        po = InventoryCount.objects.get()
        po.status = InventoryCount.INVENTORY_COUNT_COMPLETED
        po.save()

        payload = self.get_premade_payload()

        # Count Number of Queries #
        # with self.assertNumQueries(14):
        response = self.client.put(
            reverse("api:inventory_count_view", args=(self.inventory_count.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 200)

        ##### InventoryCount
        ic = InventoryCount.objects.get()

        self.assertEqual(ic.user, self.user1)
        self.assertEqual(ic.store, self.store1)
        self.assertNotEqual(ic.notes, payload['notes'])
        self.assertEqual(ic.mismatch_found, False)

        ##### InventoryCountLines
        lines = InventoryCountLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 2)

        # InventoryCount line 1
        line1 = lines[0]

        self.assertEqual(line1.inventory_count, ic)
        self.assertEqual(line1.product, self.product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertNotEqual(line1.expected_stock, payload["lines_info"][0]["expected_stock"])
        self.assertNotEqual(line1.counted_stock, payload["lines_info"][0]["counted_stock"])
        self.assertNotEqual(line1.difference, -22.00)
        self.assertNotEqual(line1.cost_difference, -22000.00)
        

        # InventoryCount line 2
        line2 = lines[1]

        self.assertEqual(line2.inventory_count, ic)
        self.assertEqual(line2.product, self.product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertNotEqual(line2.expected_stock, payload["lines_info"][1]["expected_stock"])
        self.assertNotEqual(line2.counted_stock, payload["lines_info"][1]["counted_stock"])
        self.assertNotEqual(line2.difference, 65.00)
        self.assertNotEqual(line2.cost_difference, 78000.00)

    def test_if_view_can_can_accept_an_empty_lines_info(self):

        payload = self.get_premade_payload()
        payload['lines_info'] = []

        response = self.client.put(
            reverse(
                'api:inventory_count_view', 
                args=(self.inventory_count.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

    def test_if_view_can_can_handle_a_wrong_inventory_count_line_reg_no(self):

        payload = self.get_premade_payload()
        payload['lines_info'][0]['reg_no'] = 112121

        response = self.client.put(
            reverse(
                'api:inventory_count_view', 
                args=(self.inventory_count.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### InventoryCount
        ic = InventoryCount.objects.get()

        self.assertEqual(ic.user, self.user1)
        self.assertEqual(ic.store, self.store1)
        self.assertEqual(ic.notes, payload['notes'])
        self.assertEqual(ic.mismatch_found, False)

        ##### InventoryCountLines
        lines = InventoryCountLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 2)

        # InventoryCount line 1
        line1 = lines[0]

        self.assertEqual(line1.inventory_count, ic)
        self.assertEqual(line1.product, self.product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertNotEqual(line1.expected_stock, payload["lines_info"][0]["expected_stock"])
        self.assertNotEqual(line1.counted_stock, payload["lines_info"][0]["counted_stock"])
        self.assertNotEqual(line1.difference, -22.00)
        self.assertNotEqual(line1.cost_difference, -22000.00)
        
        # InventoryCount line 2
        line2 = lines[1]

        self.assertEqual(line2.inventory_count, ic)
        self.assertEqual(line2.product, self.product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(line2.expected_stock, payload["lines_info"][1]["expected_stock"])
        self.assertEqual(line2.counted_stock, payload["lines_info"][1]["counted_stock"])
        self.assertEqual(line2.difference, 65.00)
        self.assertEqual(line2.cost_difference, 78000.00)

    def test_if_a_inventory_count_line_can_be_added(self):

        payload = self.get_premade_payload()
        payload['lines_to_add'] = [
            {
                'expected_stock': 15,
                'counted_stock': 320,
                'product_reg_no': self.product3.reg_no,
            }
        ]

        response = self.client.put(
            reverse(
                'api:inventory_count_view', 
                args=(self.inventory_count.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### InventoryCount
        ic = InventoryCount.objects.get()

        self.assertEqual(ic.user, self.user1)
        self.assertEqual(ic.store, self.store1)
        self.assertEqual(ic.notes, payload['notes'])
        self.assertEqual(ic.mismatch_found, False)

        ##### InventoryCountLines
        lines = InventoryCountLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 3)

        # InventoryCount line 1
        line1 = lines[0]

        self.assertEqual(line1.inventory_count, ic)
        self.assertEqual(line1.product, self.product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(line1.expected_stock, payload["lines_info"][0]["expected_stock"])
        self.assertEqual(line1.counted_stock, payload["lines_info"][0]["counted_stock"])
        self.assertEqual(line1.difference, -22.00)
        self.assertEqual(line1.cost_difference, -22000.00)
        

        # InventoryCount line 2
        line2 = lines[1]

        self.assertEqual(line2.inventory_count, ic)
        self.assertEqual(line2.product, self.product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(line2.expected_stock, payload["lines_info"][1]["expected_stock"])
        self.assertEqual(line2.counted_stock, payload["lines_info"][1]["counted_stock"])
        self.assertEqual(line2.difference, 65.00)
        self.assertEqual(line2.cost_difference, 78000.00)

        # InventoryCount line 3
        line3 = lines[2]

        self.assertEqual(line3.inventory_count, ic)
        self.assertEqual(line3.product, self.product3)
        self.assertEqual(
            line3.product_info, 
            {
                'name': self.product3.name,
                'sku': self.product3.sku,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line3.expected_stock, payload["lines_to_add"][0]["expected_stock"])
        self.assertEqual(line3.counted_stock, payload["lines_to_add"][0]["counted_stock"])
        self.assertEqual(line3.difference, 305.00)
        self.assertEqual(line3.cost_difference, 976000.00)

    def test_if_multiple_inventory_count_lines_can_be_added(self):
        
        InventoryCountLine.objects.all().delete()

        inventory_count_lines = InventoryCountLine.objects.all().order_by('id')
        self.assertEqual(inventory_count_lines.count(), 0)

        payload = self.get_premade_payload()
        payload['lines_to_add'] = [
            {
                'expected_stock': 50,
                'counted_stock': 100,
                'product_reg_no': self.product1.reg_no,
            },
            {
                'expected_stock': 60,
                'counted_stock': 120,
                'product_reg_no': self.product2.reg_no,
            },
            {
                'expected_stock': 70,
                'counted_stock': 140,
                'product_reg_no': self.product3.reg_no,
            }
        ]

        response = self.client.put(
            reverse(
                'api:inventory_count_view', 
                args=(self.inventory_count.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### InventoryCount
        ic = InventoryCount.objects.get()

        self.assertEqual(ic.user, self.user1)
        self.assertEqual(ic.store, self.store1)
        self.assertEqual(ic.notes, payload['notes'])
        self.assertEqual(ic.mismatch_found, False)

        ##### InventoryCountLines
        lines = InventoryCountLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 3)

        # InventoryCount line 1
        line1 = lines[0]

        self.assertEqual(line1.inventory_count, ic)
        self.assertEqual(line1.product, self.product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(line1.expected_stock, payload["lines_to_add"][0]["expected_stock"])
        self.assertEqual(line1.counted_stock, payload["lines_to_add"][0]["counted_stock"])
        self.assertEqual(line1.difference, 50.00)
        self.assertEqual(line1.cost_difference, 50000.00)
        

        # InventoryCount line 2
        line2 = lines[1]

        self.assertEqual(line2.inventory_count, ic)
        self.assertEqual(line2.product, self.product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(line2.expected_stock, payload["lines_to_add"][1]["expected_stock"])
        self.assertEqual(line2.counted_stock, payload["lines_to_add"][1]["counted_stock"])
        self.assertEqual(line2.difference, 60.00)
        self.assertEqual(line2.cost_difference, 72000.00)

        # InventoryCount line 3
        line3 = lines[2]

        self.assertEqual(line3.inventory_count, ic)
        self.assertEqual(line3.product, self.product3)
        self.assertEqual(
            line3.product_info, 
            {
                'name': self.product3.name,
                'sku': self.product3.sku,
                'reg_no': self.product3.reg_no
            }
        )
        self.assertEqual(line3.expected_stock, payload["lines_to_add"][2]["expected_stock"])
        self.assertEqual(line3.counted_stock, payload["lines_to_add"][2]["counted_stock"])
        self.assertEqual(line3.difference, 70.00)
        self.assertEqual(line3.cost_difference, 224000.00)

    def test_if_view_can_handle_a_wrong_product_reg_no_when_adding(self):

        payload = self.get_premade_payload()
        payload['lines_to_add'] = [
            {
                'expected_stock': 50,
                'counted_stock': 100,
                'product_reg_no': 4444,
            }
        ]

        response = self.client.put(
            reverse(
                'api:inventory_count_view', 
                args=(self.inventory_count.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### InventoryCountLines
        lines = InventoryCountLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 2)

        # InventoryCount line 1
        line1 = lines[0]

        self.assertEqual(line1.product, self.product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(line1.expected_stock, payload["lines_info"][0]["expected_stock"])
        self.assertEqual(line1.counted_stock, payload["lines_info"][0]["counted_stock"])
        self.assertEqual(line1.difference, -22.00)
        self.assertEqual(line1.cost_difference, -22000.00)
        

        # InventoryCount line 2
        line2 = lines[1]

        self.assertEqual(line2.product, self.product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(line2.expected_stock, payload["lines_info"][1]["expected_stock"])
        self.assertEqual(line2.counted_stock, payload["lines_info"][1]["counted_stock"])
        self.assertEqual(line2.difference, 65.00)
        self.assertEqual(line2.cost_difference, 78000.00)


    def test_if_a_inventory_count_line_can_be_removed(self):

        payload = self.get_premade_payload()
        payload['lines_to_remove'] = [
            {'reg_no': self.ic_line2.reg_no},
        ]

        response = self.client.put(
            reverse(
                'api:inventory_count_view', 
                args=(self.inventory_count.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### InventoryCountLines
        lines = InventoryCountLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 1)

        # InventoryCount line 1
        line1 = lines[0]

        self.assertEqual(line1.product, self.product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(line1.expected_stock, payload["lines_info"][0]["expected_stock"])
        self.assertEqual(line1.counted_stock, payload["lines_info"][0]["counted_stock"])
        self.assertEqual(line1.difference, -22.00)
        self.assertEqual(line1.cost_difference, -22000.00)

    def test_if_all_store_delivery_lines_can_be_removed(self):

        payload = self.get_premade_payload()
        payload['lines_to_remove'] = [
            {'reg_no': self.ic_line1.reg_no},
            {'reg_no': self.ic_line2.reg_no,},
        ]

        # Count Number of Queries #
        # with self.assertNumQueries(11):
        response = self.client.put(
            reverse(
                'api:inventory_count_view', 
                args=(self.inventory_count.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        inventory_count_lines = InventoryCountLine.objects.all().order_by('id')
        self.assertEqual(inventory_count_lines.count(), 0)

    def test_if_when_a_wrong_reg_no_is_passed_in_lines_info_delete(self):

        payload = self.get_premade_payload()
        payload['lines_to_remove'] = [{'reg_no': 111}]

        response = self.client.put(
            reverse(
                'api:inventory_count_view', 
                args=(self.inventory_count.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### InventoryCountLines
        lines = InventoryCountLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 2)

        # InventoryCount line 1
        line1 = lines[0]

        self.assertEqual(line1.product, self.product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(line1.expected_stock, payload["lines_info"][0]["expected_stock"])
        self.assertEqual(line1.counted_stock, payload["lines_info"][0]["counted_stock"])
        self.assertEqual(line1.difference, -22.00)
        self.assertEqual(line1.cost_difference, -22000.00)
        

        # InventoryCount line 2
        line2 = lines[1]

        self.assertEqual(line2.product, self.product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(line2.expected_stock, payload["lines_info"][1]["expected_stock"])
        self.assertEqual(line2.counted_stock, payload["lines_info"][1]["counted_stock"])
        self.assertEqual(line2.difference, 65.00)
        self.assertEqual(line2.cost_difference, 78000.00)

    def test_view_can_only_be_edited_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse(
                'api:inventory_count_view', 
                args=(self.inventory_count.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 404)

        ##### Confirm no edit was done
        ##### InventoryCountLines
        lines = InventoryCountLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 2)

        # InventoryCount line 1
        line1 = lines[0]

        self.assertEqual(line1.product, self.product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertNotEqual(line1.expected_stock, payload["lines_info"][0]["expected_stock"])
        self.assertNotEqual(line1.counted_stock, payload["lines_info"][0]["counted_stock"])
        self.assertNotEqual(line1.difference, -22.00)
        self.assertNotEqual(line1.cost_difference, -22000.00)
        

        # InventoryCount line 2
        line2 = lines[1]

        self.assertEqual(line2.product, self.product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertNotEqual(line2.expected_stock, payload["lines_info"][1]["expected_stock"])
        self.assertNotEqual(line2.counted_stock, payload["lines_info"][1]["counted_stock"])
        self.assertNotEqual(line2.difference, 65.00)
        self.assertNotEqual(line2.cost_difference, 78000.00)

    def test_view_cant_be_edited_by_an_employee_user(self):

        # Login a employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse(
                'api:inventory_count_view', 
                args=(self.inventory_count.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 404)

        ##### Confirm no edit was done
        ##### InventoryCountLines
        lines = InventoryCountLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 2)

        # InventoryCount line 1
        line1 = lines[0]

        self.assertEqual(line1.product, self.product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertNotEqual(line1.expected_stock, payload["lines_info"][0]["expected_stock"])
        self.assertNotEqual(line1.counted_stock, payload["lines_info"][0]["counted_stock"])
        self.assertNotEqual(line1.difference, -22.00)
        self.assertNotEqual(line1.cost_difference, -22000.00)
        

        # InventoryCount line 2
        line2 = lines[1]

        self.assertEqual(line2.product, self.product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertNotEqual(line2.expected_stock, payload["lines_info"][1]["expected_stock"])
        self.assertNotEqual(line2.counted_stock, payload["lines_info"][1]["counted_stock"])
        self.assertNotEqual(line2.difference, 65.00)
        self.assertNotEqual(line2.cost_difference, 78000.00)

    def test_view_cant_be_edited_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse(
                'api:inventory_count_view', 
                args=(self.inventory_count.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 401)

        ##### Confirm no edit was done
        ##### InventoryCountLines
        lines = InventoryCountLine.objects.all().order_by("id")
        self.assertEqual(lines.count(), 2)

        # InventoryCount line 1
        line1 = lines[0]

        self.assertEqual(line1.product, self.product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertNotEqual(line1.expected_stock, payload["lines_info"][0]["expected_stock"])
        self.assertNotEqual(line1.counted_stock, payload["lines_info"][0]["counted_stock"])
        self.assertNotEqual(line1.difference, -22.00)
        self.assertNotEqual(line1.cost_difference, -22000.00)
        

        # InventoryCount line 2
        line2 = lines[1]

        self.assertEqual(line2.product, self.product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertNotEqual(line2.expected_stock, payload["lines_info"][1]["expected_stock"])
        self.assertNotEqual(line2.counted_stock, payload["lines_info"][1]["counted_stock"])
        self.assertNotEqual(line2.difference, 65.00)
        self.assertNotEqual(line2.cost_difference, 78000.00)

class InventoryCountViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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

    def create_inventory_count(self):

        ########### Create stock adjustment1
        self.inventory_count1 = InventoryCount.objects.create(
            user=self.user1,
            store=self.store1,
            notes='This is just a simple note1',
        )

        # Create inventory_count1
        InventoryCountLine.objects.create(
            inventory_count=self.inventory_count1,
            product=self.product1,
            expected_stock=100,
            counted_stock=77,
        )
    
        # Create inventory_count2
        InventoryCountLine.objects.create(
            inventory_count=self.inventory_count1,
            product=self.product2,
            expected_stock=155,
            counted_stock=160,
        )


        ########### Create stock adjustment2
        self.inventory_count2 = InventoryCount.objects.create(
            user=self.user1,
            store=self.store2,
            notes='This is just a simple note2',
        )

        # Create inventory_count1
        InventoryCountLine.objects.create(
            inventory_count=self.inventory_count2,
            product=self.product1,
            expected_stock=200,
            counted_stock=87,
        )
    
        # Create inventory_count2
        InventoryCountLine.objects.create(
            inventory_count=self.inventory_count2,
            product=self.product2,
            counted_stock=260,
        )

    def test_view_can_delete_a_inventory_count(self):

        response = self.client.delete(
            reverse('api:inventory_count_view', 
            args=(self.inventory_count1.reg_no,))
        )
        self.assertEqual(response.status_code, 204)

        # Confirm the inventory_count was deleted
        self.assertEqual(InventoryCount.objects.filter(
            reg_no=self.inventory_count1.reg_no).exists(), False
        )

    def test_view_can_handle_wrong_inventory_count_reg_no(self):

        response = self.client.delete(
            reverse('api:inventory_count_view', 
            args=(44444,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the inventory_count was not deleted
        self.assertEqual(InventoryCount.objects.filter(
            reg_no=self.inventory_count1.reg_no).exists(), True
        )

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:inventory_count_view', 
            args=(self.inventory_count1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the inventory_count was not deleted
        self.assertEqual(InventoryCount.objects.filter(
            reg_no=self.inventory_count1.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_employee_user(self):

        # Login a employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:inventory_count_view', 
            args=(self.inventory_count1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the inventory_count was not deleted
        self.assertEqual(InventoryCount.objects.filter(
            reg_no=self.inventory_count1.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:inventory_count_view', 
            args=(self.inventory_count1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

        # Confirm the inventory_count was not deleted
        self.assertEqual(InventoryCount.objects.filter(
            reg_no=self.inventory_count1.reg_no).exists(), True
        )

class InventoryCountViewStatusTestCase(APITestCase, InitialUserDataMixin):

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

        self.product3 = Product.objects.create(
            profile=self.top_profile1,
            name="Sugar",
            price=4800,
            cost=3200,
            barcode="code123",
        )
        self.product3.stores.add(self.store1, self.store2)


        self.create_inventory_count()

    def create_inventory_count(self):

        ########### Create stock adjustment1
        self.inventory_count = InventoryCount.objects.create(
            user=self.user1,
            store=self.store1,
            notes='This is just a simple note1',
        )

        # Create inventory_count1
        self.ic_line1 = InventoryCountLine.objects.create(
            inventory_count=self.inventory_count,
            product=self.product1,
            expected_stock=100,
            counted_stock=77,
        )
    
        # Create inventory_count2
        self.ic_line2 = InventoryCountLine.objects.create(
            inventory_count=self.inventory_count,
            product=self.product2,
            expected_stock=155,
            counted_stock=160,
        )

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """        
        payload = {
            'status': InventoryCount.INVENTORY_COUNT_COMPLETED,
        }

        return payload

    def test_view_can_be_called_successefully(self):

        # Confirm inventory count values stock level units
        po = InventoryCount.objects.get(store=self.store1)

        self.assertEqual(po.status, InventoryCount.INVENTORY_COUNT_PENDING)

        payload = self.get_premade_payload()

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.put(
            reverse('api:inventory_count_view-status', 
            args=(po.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 200)

        po = InventoryCount.objects.get(store=self.store1)

        self.assertEqual(po.status, InventoryCount.INVENTORY_COUNT_COMPLETED)

        ########################## Test maintaince ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.put(
            reverse('api:inventory_count_view-status', 
            args=(po.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 401)

    def test_if_view_can_only_be_edited_by_its_owner(self):

        # Login a employee profile #
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()

        po = InventoryCount.objects.get(store=self.store1)

        response = self.client.put(
            reverse('api:inventory_count_view-status', 
            args=(po.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        po = InventoryCount.objects.get(store=self.store1)

        response = self.client.put(
            reverse('api:inventory_count_view-status', 
            args=(po.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 401)
