from decimal import Decimal
import json
from pprint import pprint
import uuid

from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.initial_user_data import InitialUserDataMixin
from core.test_utils.custom_testcase import APITestCase

from products.models import Product, ProductProductionMap

from mysettings.models import MySetting
from inventories.models import StockLevel, TransferOrder, TransferOrderLine


class TransferOrderIndexViewTestCase(APITestCase, InitialUserDataMixin):

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


        self.create_transfer_order()

    def create_transfer_order(self):

        ########### Create stock adjustment1
        self.transfer_order1 = TransferOrder.objects.create(
            user=self.user1,
            source_store=self.store1,
            destination_store=self.store2,
            notes='This is just a simple note1',
            quantity=24,
        )

        # Create transfer_order1
        TransferOrderLine.objects.create(
            transfer_order=self.transfer_order1,
            product=self.product1,
            quantity=10,
        )
    
        # Create transfer_order2
        TransferOrderLine.objects.create(
            transfer_order=self.transfer_order1,
            product=self.product2,
            quantity=14,
        )


        ########### Create stock adjustment2
        self.transfer_order2 = TransferOrder.objects.create(
            user=self.user1,
            source_store=self.store2,
            destination_store=self.store1,
            notes='This is just a simple note2',
            status=TransferOrder.TRANSFER_ORDER_PENDING,
            quantity=15 
        )

        # Create transfer_order1
        TransferOrderLine.objects.create(
            transfer_order=self.transfer_order2,
            product=self.product1,
            quantity=10,
        )
    
        # Create transfer_order2
        TransferOrderLine.objects.create(
            transfer_order=self.transfer_order2,
            product=self.product2,
            quantity=5,
        )

    def test_view_returns_the_user_transfer_orders_only(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        response = self.client.get(reverse('api:transfer_order_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.transfer_order2.__str__(), 
                    'source_store_name': self.store2.name, 
                    'destination_store_name': self.store1.name, 
                    'status': self.transfer_order2.status,
                    'str_quantity': f'{self.transfer_order2.quantity}.00',
                    'reg_no': self.transfer_order2.reg_no, 
                    'creation_date': self.transfer_order2.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'is_auto_created': self.transfer_order2.is_auto_created,
                    'source_description': self.transfer_order2.source_description,
                    'completion_date': self.transfer_order2.get_completed_date(
                        self.user1.get_user_timezone()
                    )
                }, 
                {
                    'name': self.transfer_order1.__str__(),  
                    'source_store_name': self.store1.name, 
                    'destination_store_name': self.store2.name, 
                    'status': self.transfer_order1.status,
                    'str_quantity': f'{self.transfer_order1.quantity}.00',
                    'reg_no': self.transfer_order1.reg_no, 
                    'creation_date': self.transfer_order1.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'is_auto_created': self.transfer_order1.is_auto_created,
                    'source_description': self.transfer_order1.source_description,
                    'completion_date': self.transfer_order1.get_completed_date(
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
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
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
                reverse('api:transfer_order_index'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all transfer_orders
        TransferOrder.objects.all().delete()

        pagination_page_size = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION

        model_num_to_be_created = pagination_page_size+1

        transfer_order_names = []
        for i in range(model_num_to_be_created):
            transfer_order_names.append(f'New TransferOrder{i}')

        names_length = len(transfer_order_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm transfer_orders
        for i in range(names_length):
            TransferOrder.objects.create(
                user=self.user1,
                source_store=self.store1,
                destination_store=self.store2,
                notes='This is just a simple note1',
                quantity=24,
            )

        self.assertEqual(
            TransferOrder.objects.filter(user=self.user1).count(),
            names_length)  # Confirm models were created

    
        transfer_orders = TransferOrder.objects.filter(user=self.user1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(27):
            response = self.client.get(
                reverse('api:transfer_order_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 
            'http://testserver/api/transfer-orders/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all stock adjustments are listed except the first one since it's in the next paginated page #
        i = 0
        for transfer_order in transfer_orders[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], transfer_order.__str__())
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], transfer_order.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
                reverse('api:transfer_order_index')  + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/transfer-orders/',
            'results': [
                {
                    'name': transfer_orders[0].__str__(),  
                    'source_store_name': self.store1.name, 
                    'destination_store_name': self.store2.name, 
                    'status': transfer_orders[0].status,
                    'str_quantity': f'{transfer_orders[0].quantity}',
                    'reg_no': transfer_orders[0].reg_no, 
                    'creation_date': transfer_orders[0].get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'is_auto_created': transfer_orders[0].is_auto_created,
                    'source_description': transfer_orders[0].source_description,
                    'completion_date': transfer_orders[0].get_completed_date(
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
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_perform_search(self):

        param = f'?search={self.transfer_order2.reg_no}'
        response = self.client.get(reverse('api:transfer_order_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.transfer_order2.__str__(), 
                    'source_store_name': self.store2.name, 
                    'destination_store_name': self.store1.name, 
                    'status': self.transfer_order2.status,
                    'str_quantity': f'{self.transfer_order2.quantity}.00',
                    'reg_no': self.transfer_order2.reg_no, 
                    'creation_date': self.transfer_order2.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'is_auto_created': self.transfer_order2.is_auto_created,
                    'source_description': self.transfer_order2.source_description,
                    'completion_date': self.transfer_order2.get_completed_date(
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
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_with_source_store(self):

        param = f'?source_store_reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:transfer_order_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.transfer_order1.__str__(),  
                    'source_store_name': self.store1.name, 
                    'destination_store_name': self.store2.name, 
                    'status': self.transfer_order1.status,
                    'str_quantity': f'{self.transfer_order1.quantity}.00',
                    'reg_no': self.transfer_order1.reg_no, 
                    'creation_date': self.transfer_order1.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'is_auto_created': self.transfer_order1.is_auto_created,
                    'source_description': self.transfer_order1.source_description,
                    'completion_date': self.transfer_order1.get_completed_date(
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
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_with_destination_store(self):

        param = f'?destination_store_reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:transfer_order_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.transfer_order2.__str__(),  
                    'source_store_name': self.store2.name, 
                    'destination_store_name': self.store1.name, 
                    'status': self.transfer_order2.status,
                    'str_quantity': f'{self.transfer_order2.quantity}.00',
                    'reg_no': self.transfer_order2.reg_no, 
                    'creation_date': self.transfer_order2.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'is_auto_created': self.transfer_order2.is_auto_created,
                    'source_description': self.transfer_order2.source_description,
                    'completion_date': self.transfer_order2.get_completed_date(
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
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_status(self):

        self.transfer_order2.status = TransferOrder.TRANSFER_ORDER_RECEIVED
        self.transfer_order2.save()

        param = f'?status={TransferOrder.TRANSFER_ORDER_RECEIVED}'
        response = self.client.get(reverse('api:transfer_order_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.transfer_order2.__str__(),  
                    'source_store_name': self.store2.name, 
                    'destination_store_name': self.store1.name, 
                    'status': self.transfer_order2.status,
                    'str_quantity': f'{self.transfer_order2.quantity}.00',
                    'reg_no': self.transfer_order2.reg_no, 
                    'creation_date': self.transfer_order2.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'is_auto_created': self.transfer_order2.is_auto_created,
                    'source_description': self.transfer_order2.source_description,
                    'completion_date': self.transfer_order2.get_completed_date(
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
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_returns_empty_when_there_are_no_transfer_orders(self):

        # First delete all transfer_orders
        TransferOrder.objects.all().delete()

        response = self.client.get(
                reverse('api:transfer_order_index'))
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
                    'reg_no': self.store2.reg_no,
                    'is_deleted': self.store2.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
                }, 
                {
                    'name': self.store1.name, 
                    'is_shop': True, 
                    'is_truck': False, 
                    'is_warehouse': False, 
                    'reg_no': self.store1.reg_no,
                    'is_deleted': self.store1.is_deleted,
                    'created_date_str': self.store2.created_date_str,
                    'deleted_date_str': self.store2.deleted_date_str
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
                reverse('api:transfer_order_index'))
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
                    'reg_no': self.store3.reg_no,
                    'is_deleted': self.store3.is_deleted,
                    'created_date_str': self.store3.created_date_str,
                    'deleted_date_str': self.store3.deleted_date_str
                },
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
                reverse('api:transfer_order_index'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:transfer_order_index'))
        self.assertEqual(response.status_code, 401)
        

class TransferOrderCreateViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 100
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 155
        stock_level.save()
        

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """
        
        payload = {
            'notes': 'A simple note',
            'status': TransferOrder.TRANSFER_ORDER_PENDING,
            'source_store_reg_no': self.store1.reg_no,
            'destination_store_reg_no': self.store2.reg_no,
            'source_description': '',
            'transfer_order_lines': [
                {
                    'product_reg_no': self.product1.reg_no,
                    'quantity': 60,
                },
                {
                    'product_reg_no': self.product2.reg_no,
                    'quantity': 40,
                }
            ]
        }

        return payload 
      
    def test_if_view_can_create_a_normal_transfer_order(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:transfer_order_index'), 
            payload
        )

        self.assertEqual(response.status_code, 201)

        to = TransferOrder.objects.get(source_store=self.store1)

        # Confirm model creation
        self.assertEqual(TransferOrder.objects.all().count(), 1)
    
        product1 = Product.objects.get(name='Shampoo')
        product2 = Product.objects.get(name='Conditioner')


        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(to.user, self.user1)
        self.assertEqual(to.source_store, self.store1)
        self.assertEqual(to.destination_store, self.store2)
        self.assertEqual(to.notes, 'A simple note')
        self.assertEqual(to.quantity, Decimal('100.00'))
        self.assertEqual(to.status, TransferOrder.TRANSFER_ORDER_PENDING)
        self.assertTrue(to.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((to.created_date).strftime("%B, %d, %Y"), today)
        self.assertEqual(to.is_auto_created, False)
        self.assertEqual(to.source_description, '')


        # Confirm receipt line model creation
        self.assertEqual(TransferOrderLine.objects.filter(transfer_order=to).count(), 2)

        lines = TransferOrderLine.objects.filter(transfer_order=to).order_by('id')

        # TransferOrder line 1
        line1 = lines[0]

        self.assertEqual(line1.transfer_order, to)
        self.assertEqual(line1.product, product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(line1.quantity, 60.00)
        

        # TransferOrder line 2
        line2 = lines[1]

        self.assertEqual(line2.transfer_order, to)
        self.assertEqual(line2.product, product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(line2.quantity, 40.00)


        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=True
        ms.save()
              
        response = self.client.post(
            reverse('api:transfer_order_index'), 
            payload,
        )
            
        self.assertEqual(response.status_code, 401)

    def test_view_wont_change_stock_if_status_is_pending(self):

        # Empty all stocks
        StockLevel.objects.all().update(units=0)

        # Confirm initial stock levels
        levels = StockLevel.objects.all()
        for level in levels:
            self.assertEqual(level.units, 0)

        payload = self.get_premade_payload()
        payload['status'] = TransferOrder.TRANSFER_ORDER_PENDING

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.post(
            reverse('api:transfer_order_index'), 
            payload,
        )
        self.assertEqual(response.status_code, 201)

        to = TransferOrder.objects.get(source_store=self.store1)

        self.assertEqual(to.status, TransferOrder.TRANSFER_ORDER_PENDING)
        self.assertEqual(to.order_completed, False)

        # Confirm stock levels were not changed
        levels = StockLevel.objects.all()
        for level in levels:
            self.assertEqual(level.units, 0)

    def test_view_will_change_stock_if_status_is_received(self):

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 100.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 155.00)

        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 0.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 0.00)

        payload = self.get_premade_payload()
        payload['status'] = TransferOrder.TRANSFER_ORDER_RECEIVED

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.post(
            reverse('api:transfer_order_index'), 
            payload,
        )

        self.assertEqual(response.status_code, 201)

        to = TransferOrder.objects.get(source_store=self.store1)

        self.assertEqual(to.status, TransferOrder.TRANSFER_ORDER_RECEIVED)
        self.assertEqual(to.order_completed, True)

        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 40.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 115.00)

        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 60.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 40.00)

    def test_if_view_can_handle_with_wrong_source_store_reg_no(self):

        wrong_reg_nos = [
            33463476347374, # Wrong reg no
            self.store3.reg_no, # Store for another user
            11111111111111111111111111111111111111 # Long reg no
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_reg_nos:

            payload = self.get_premade_payload()
            payload['source_store_reg_no'] = wrong_reg_no

            response = self.client.post(
                reverse('api:transfer_order_index'), 
                payload
            )

            self.assertEqual(response.status_code, 404)

            # Confirm model was not creation
            self.assertEqual(TransferOrder.objects.all().count(), 0)

    def test_if_view_can_handle_with_wrong_destination_store_reg_no(self):

        wrong_reg_nos = [
            33463476347374, # Wrong reg no
            self.store3.reg_no, # Store for another user
            11111111111111111111111111111111111111 # Long reg no
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_reg_nos:

            payload = self.get_premade_payload()
            payload['destination_store_reg_no'] = wrong_reg_no

            response = self.client.post(
                reverse('api:transfer_order_index'), 
                payload
            )

            self.assertEqual(response.status_code, 404)

            # Confirm model was not creation
            self.assertEqual(TransferOrder.objects.all().count(), 0)

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
            TransferOrder.objects.all().delete()
            TransferOrderLine.objects.all().delete()

            payload['transfer_order_lines'][0]['product_reg_no'] = wrong_reg_no

            response = self.client.post(
                reverse('api:transfer_order_index'),
                payload,
            )

            self.assertEqual(response.status_code, 400)

            result = {'non_field_errors': 'Product error.'}
            self.assertEqual(response.data, result)


            # Confirm model creation
            self.assertEqual(TransferOrder.objects.all().count(), 0)

    def test_if_view_url_can_throttle_post_requests(self):

        payload = self.get_premade_payload()

        throttle_rate = int(settings.THROTTLE_RATES['api_transfer_order_rate'].split("/")[0])
    
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:transfer_order_index'),
                payload,
            )
            self.assertEqual(response.status_code, 201)


        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional 
        # request if the previous request was not throttled 
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:transfer_order_index'),
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
            reverse('api:transfer_order_index'), 
            payload,
        )
        self.assertEqual(response.status_code, 401)

class TransferOrderCompletedViewTestCase(APITestCase, InitialUserDataMixin):

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

        self.create_product_maps_for_sugar()


        # Create models
        # Creates products
        self.product1 = Product.objects.create(
            profile=self.top_profile1,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
  
        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 100
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 155
        stock_level.save()

    def create_product_maps_for_sugar(self):

        sugar_sack = Product.objects.create(
            profile=self.top_profile1,
            name="Sugar 50kg Sack",
            price=10000,
            cost=9000,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )

        sugar_1kg = Product.objects.create(
            profile=self.top_profile1,
            name="Sugar 1kg",
            price=200,
            cost=180,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )

        sugar_500g = Product.objects.create(
            profile=self.top_profile1,
            name="Sugar 500g",
            price=100,
            cost=90,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )

        sugar_250g = Product.objects.create(
            profile=self.top_profile1,
            name="Sugar 250g",
            price=50,
            cost=45,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )

        # Create master product with 2 productions
        sugar_1kg_map = ProductProductionMap.objects.create(
            product_map=sugar_1kg,
            quantity=50,
            is_auto_repackage=True

        )

        sugar_500g_map = ProductProductionMap.objects.create(
            product_map=sugar_500g,
            quantity=100
        )

        sugar_250g_map = ProductProductionMap.objects.create(
            product_map=sugar_250g,
            quantity=200
        )

        sugar_sack.productions.add(sugar_1kg_map, sugar_500g_map, sugar_250g_map)

        # Change stock amount
        # Product1
        stock_level = StockLevel.objects.get(store=self.store1, product=sugar_sack)
        stock_level.units = 20
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=sugar_sack)
        stock_level.units = 30
        stock_level.save()

        # Product2
        stock_level = StockLevel.objects.get(store=self.store1, product=sugar_1kg)
        stock_level.units = 45
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=sugar_1kg)
        stock_level.units = 70
        stock_level.save()
        
    def get_premade_payload(self):
        """
        Simplifies creating payload
        """

        sugar1kg = Product.objects.get(name='Sugar 1kg')
        
        payload = {
            'notes': 'A simple note',
            'source_store_id': self.store1.loyverse_store_id,
            'destination_store_id': self.store2.loyverse_store_id,
            'source_description': 'From delivery note 1200',
            'transfer_order_lines': [
                {
                    'loyverse_variant_id': self.product1.loyverse_variant_id,
                    'quantity': 60,
                },
                {
                    'loyverse_variant_id': self.product2.loyverse_variant_id,
                    'quantity': 40,
                },
                {
                    'loyverse_variant_id': sugar1kg.loyverse_variant_id,
                    'quantity': 100,
                }
            ]
        }

        return payload 
      
    def test_if_view_can_create_an_auto_transfer_order(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:transfer_order_index_auto'), 
            payload
        )

        print(response.data)

        self.assertEqual(response.status_code, 201)

        to = TransferOrder.objects.get(source_store=self.store1)

        # Confirm model creation
        self.assertEqual(TransferOrder.objects.all().count(), 1)
    
        product1 = Product.objects.get(name='Shampoo')
        product2 = Product.objects.get(name='Conditioner')
        product3 = Product.objects.get(name='Sugar 50kg Sack')

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(to.user, self.user1)
        self.assertEqual(to.source_store, self.store1)
        self.assertEqual(to.destination_store, self.store2)
        self.assertEqual(to.notes, 'A simple note')
        self.assertEqual(to.quantity, Decimal('102.00'))
        self.assertEqual(to.status, TransferOrder.TRANSFER_ORDER_PENDING)
        self.assertTrue(to.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((to.created_date).strftime("%B, %d, %Y"), today)
        self.assertEqual(to.is_auto_created, True)
        self.assertEqual(to.source_description, 'From delivery note 1200')

        # Confirm receipt line model creation
        self.assertEqual(TransferOrderLine.objects.filter(transfer_order=to).count(), 3)

        lines = TransferOrderLine.objects.filter(transfer_order=to).order_by('id')

        # TransferOrder line 1
        line1 = lines[0]

        self.assertEqual(line1.transfer_order, to)
        self.assertEqual(line1.product, product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(line1.quantity, 60.00)
        
        # TransferOrder line 2
        line2 = lines[1]

        self.assertEqual(line2.transfer_order, to)
        self.assertEqual(line2.product, product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'reg_no': self.product2.reg_no
            }
        )
        self.assertEqual(line2.quantity, 40.00)

        # TransferOrder line 3
        line3 = lines[2]

        self.assertEqual(line3.transfer_order, to)
        self.assertEqual(line3.product, product3)
        self.assertEqual(
            line3.product_info, 
            {
                'name': product3.name,
                'sku': product3.sku,
                'reg_no': product3.reg_no
            }
        )
        self.assertEqual(line3.quantity, 2.00)

    def test_if_view_can_create_an_auto_transfer_order_that_has_been_received(self):

        payload = self.get_premade_payload()
        
        payload['status'] = TransferOrder.TRANSFER_ORDER_RECEIVED

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:transfer_order_index_auto'), 
            payload
        )

        self.assertEqual(response.status_code, 201)

        to = TransferOrder.objects.get(source_store=self.store1)

        # Confirm model creation
        self.assertEqual(TransferOrder.objects.all().count(), 1)

        self.assertEqual(to.status, TransferOrder.TRANSFER_ORDER_PENDING)
        self.assertEqual(to.is_auto_created, True)
        self.assertEqual(to.source_description, 'From delivery note 1200')

        # Confirm receipt line model creation
        self.assertEqual(TransferOrderLine.objects.filter(transfer_order=to).count(), 3)

    def test_if_view_can_handle_with_wrong_source_store_id(self):

        wrong_store_ids = [
            '33463476347374', # Wrong store id
            self.store3.loyverse_store_id, # Store for another user
            '11111111111111111111111111111111111111' # Long store id
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_store_ids:

            payload = self.get_premade_payload()
            payload['source_store_id'] = wrong_reg_no

            response = self.client.post(
                reverse('api:transfer_order_index_auto'), 
                payload
            )

            self.assertEqual(response.status_code, 404)

            # Confirm model was not creation
            self.assertEqual(TransferOrder.objects.all().count(), 0)

    def test_if_view_can_handle_with_wrong_destination_store_reg_no(self):

        wrong_store_ids = [
            '33463476347374', # Wrong store id
            self.store3.loyverse_store_id, # Store for another user
            '11111111111111111111111111111111111111' # Long store id
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_store_ids:

            payload = self.get_premade_payload()
            payload['destination_store_id'] = wrong_reg_no

            response = self.client.post(
                reverse('api:transfer_order_index_auto'), 
                payload
            )

            self.assertEqual(response.status_code, 404)

            # Confirm model was not creation
            self.assertEqual(TransferOrder.objects.all().count(), 0)

    def test_if_view_can_handle_a_line_wrong_product_reg_no(self):

        wrong_product_variant_ids = [
            '33463476347374', # Wrong store id
            '11111111111111111111111111111111111111' # Long store id
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_product_variant_ids:

            # Delete previous models
            TransferOrder.objects.all().delete()
            TransferOrderLine.objects.all().delete()

            payload['transfer_order_lines'][0]['loyverse_variant_id'] = wrong_reg_no

            response = self.client.post(
                reverse('api:transfer_order_index_auto'),
                payload,
            )

            self.assertEqual(response.status_code, 400)

            result = {'non_field_errors': 'Product error.'}
            self.assertEqual(response.data, result)


            # Confirm model creation
            self.assertEqual(TransferOrder.objects.all().count(), 0)

    def test_if_view_url_can_throttle_post_requests(self):

        payload = self.get_premade_payload()

        throttle_rate = int(settings.THROTTLE_RATES['api_transfer_order_rate'].split("/")[0])
    
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:transfer_order_index_auto'),
                payload,
            )
            self.assertEqual(response.status_code, 201)


        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional 
        # request if the previous request was not throttled 
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:transfer_order_index_auto'),
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
            reverse('api:transfer_order_index_auto'), 
            payload,
        )
        self.assertEqual(response.status_code, 401)


class TransferOrderViewForViewingTestCase(APITestCase, InitialUserDataMixin):

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


        self.create_transfer_order()

    def create_transfer_order(self):

        ########### Create stock adjustment1
        self.transfer_order1 = TransferOrder.objects.create(
            user=self.user1,
            source_store=self.store1,
            destination_store=self.store2,
            notes='This is just a simple note1',
            quantity=24,
        )

        # Create transfer_order1
        TransferOrderLine.objects.create(
            transfer_order=self.transfer_order1,
            product=self.product1,
            quantity=10,
        )
    
        # Create transfer_order2
        TransferOrderLine.objects.create(
            transfer_order=self.transfer_order1,
            product=self.product2,
            quantity=14,
        )

        ########### Create stock adjustment2
        self.transfer_order2 = TransferOrder.objects.create(
            user=self.user1,
            source_store=self.store2,
            destination_store=self.store1,
            notes='This is just a simple note2',
            quantity=15
        )

        # Create transfer_order1
        TransferOrderLine.objects.create(
            transfer_order=self.transfer_order2,
            product=self.product1,
            quantity=10,
        )
    
        # Create transfer_order2
        TransferOrderLine.objects.create(
            transfer_order=self.transfer_order2,
            product=self.product2,
            quantity=5,
        )

    def test_view_can_be_called_successefully(self):

        transfer_order = TransferOrder.objects.get(quantity=24)

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.get(
            reverse('api:transfer_order_view', 
            args=(transfer_order.reg_no,))
        )
        self.assertEqual(response.status_code, 200)


        lines = transfer_order.transferorderline_set.all().order_by('id')

        # Stock level for product1
        product1_source_store_units = StockLevel.objects.get(
            product__reg_no=self.product1.reg_no,
            store=self.store1
        ).units

        product1_destination_store_units = StockLevel.objects.get(
            product__reg_no=self.product1.reg_no,
            store=self.store2
        ).units


        # Stock level for product2
        product2_source_store_units = StockLevel.objects.get(
            product__reg_no=self.product2.reg_no,
            store=self.store1
        ).units

        product2_destination_store_units = StockLevel.objects.get(
            product__reg_no=self.product2.reg_no,
            store=self.store2
        ).units

        result = {
            'name': transfer_order.__str__(), 
            'notes': transfer_order.notes, 
            'status': transfer_order.status,
            'stores_data': transfer_order.get_stores_data(), 
            'source_store_name': self.store1.name, 
            'destination_store_name': self.store2.name, 
            'quantity': str(transfer_order.quantity), 
            'reg_no': transfer_order.reg_no, 
            'ordered_by': self.user1.get_full_name(), 
            'creation_date': transfer_order.get_created_date(
                self.user1.get_user_timezone()
            ), 
            'completion_date': self.transfer_order2.get_completed_date(
                self.user1.get_user_timezone()
            ),
            'source_description': transfer_order.source_description,
            'is_auto_created': transfer_order.is_auto_created,
            'line_data': [ 
                {
                    'product_info': {
                        'name': self.product1.name, 
                        'sku': self.product1.sku,
                        'reg_no': self.product1.reg_no
                    }, 
                    'quantity': str(lines[0].quantity),
                    'destination_store_units': product1_destination_store_units,
                    'source_store_units': product1_source_store_units,
                    'reg_no': str(lines[0].reg_no),
                },
                {
                    'product_info': {
                        'name': self.product2.name, 
                        'sku': self.product2.sku,
                        'reg_no': self.product2.reg_no
                    }, 
                    'quantity': str(lines[1].quantity),
                    'destination_store_units': product2_destination_store_units,
                    'source_store_units': product2_source_store_units,
                    'reg_no': str(lines[1].reg_no),
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
            reverse('api:transfer_order_view', args=(self.transfer_order1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

    def test_view_can_handle_wrong_transfer_order_reg_no(self):

        response = self.client.get(
            reverse('api:transfer_order_view', args=(4646464,)))
        self.assertEqual(response.status_code, 404)

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:transfer_order_view', 
            args=(self.transfer_order1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_employee_user(self):

        # Login a employee user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:transfer_order_view', 
            args=(self.transfer_order1.reg_no,))
        )
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:transfer_order_view', 
            args=(self.transfer_order1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)


class TranferOrderViewForEditingTestCase(APITestCase, InitialUserDataMixin):

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
            barcode='code123'
        )
        self.product3.stores.add(self.store1, self.store2)

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 100
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 155
        stock_level.save()

        # Update stock level for product 3
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product3)
        stock_level.units = 255
        stock_level.save()

        self.create_transfer_order()

    def create_transfer_order(self):

        # Create tranfer order
        self.transfer_order = TransferOrder.objects.create(
            user=self.user1,
            source_store=self.store1,
            destination_store=self.store2,
            notes='This is just a simple note',
            quantity=24,
        )

        # Create line 1
        self.transfer_order_line1 =  TransferOrderLine.objects.create(
            transfer_order=self.transfer_order,
            product=self.product1,
            quantity=10
        )
    
        # Create line 2
        self.transfer_order_line2 = TransferOrderLine.objects.create(
            transfer_order=self.transfer_order,
            product=self.product2,
            quantity=14,
        )

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """        
        payload = {
            'notes': 'This is just a new simple note',
            'source_store_reg_no': self.store2.reg_no,
            'destination_store_reg_no': self.store1.reg_no,
            'lines_info': [
                {
                    'quantity': 5,
                    'reg_no': self.transfer_order_line1.reg_no,
                    'is_dirty': True,
                },
                {
                    'quantity': 7,
                    'reg_no': self.transfer_order_line2.reg_no,
                    'is_dirty': True
                } 
            ],
            'lines_to_add': [],
            'lines_to_remove': []
        }

        return payload
    

    def test_view_can_edit_model_successfully(self):

        payload = self.get_premade_payload()

        # Count Number of Queries #
        # with self.assertNumQueries(14):
        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### TransferOrder
        to = TransferOrder.objects.get()

        self.assertEqual(to.user, self.user1)
        self.assertEqual(to.source_store, self.store2)
        self.assertEqual(to.destination_store, self.store1)
        self.assertEqual(to.notes, payload['notes'])
        self.assertEqual(to.quantity, 12)

        ##### TransferOrderLines
        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertEqual(
            transfer_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )

        # Model 2
        self.assertEqual(transfer_order_lines[1].product, self.product2)
        self.assertEqual(
            transfer_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )

    def test_view_cant_edit_a_model_when_it_has_been_received_successfully(self):

        # Make the Transfer order to be received
        to = TransferOrder.objects.get()
        to.status = TransferOrder.TRANSFER_ORDER_RECEIVED
        to.save()

        payload = self.get_premade_payload()

        # Count Number of Queries #
        # with self.assertNumQueries(14):
        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### TransferOrder
        to = TransferOrder.objects.get()

        self.assertEqual(to.user, self.user1)
        self.assertNotEqual(to.source_store, self.store2)
        self.assertNotEqual(to.destination_store, self.store1)
        self.assertNotEqual(to.notes, payload['notes'])
        self.assertEqual(to.quantity, 24)

        ##### TransferOrderLines
        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertNotEqual(
            transfer_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )

        # Model 2
        self.assertEqual(transfer_order_lines[1].product, self.product2)
        self.assertNotEqual(
            transfer_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )

    def test_if_view_can_handle_with_wrong_destination_store_reg_no(self):

        wrong_reg_nos = [
            33463476347374, # Wrong reg no
            11111111111111111111111111111111111111 # Long reg no
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_reg_nos:

            payload = self.get_premade_payload()
            payload['destination_store_reg_no'] = wrong_reg_no

            response = self.client.put(
                reverse(
                    'api:transfer_order_view', 
                    args=(self.transfer_order.reg_no,)
                ), 
                payload
            )

            self.assertEqual(response.status_code, 404)

        ##### Confirm no edit was done
        ##### TransferOrderLines
        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertNotEqual(
            str(transfer_order_lines[0].quantity), 
            payload['lines_info'][0]['quantity']
        )

        # Model 2
        self.assertEqual(transfer_order_lines[1].product, self.product2)
        self.assertNotEqual(
            str(transfer_order_lines[1].quantity), 
            payload['lines_info'][1]['quantity']
        )

    def test_if_view_can_handle_with_wrong_source_store_reg_no(self):

        wrong_reg_nos = [
            33463476347374, # Wrong reg no
            11111111111111111111111111111111111111 # Long reg no
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_reg_nos:

            payload = self.get_premade_payload()
            payload['source_store_reg_no'] = wrong_reg_no

            response = self.client.put(
                reverse(
                    'api:transfer_order_view', 
                    args=(self.transfer_order.reg_no,)
                ), 
                payload
            )

            self.assertEqual(response.status_code, 404)

        ##### Confirm no edit was done
        ##### TransferOrderLines
        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertNotEqual(
            str(transfer_order_lines[0].quantity), 
            payload['lines_info'][0]['quantity']
        )

        # Model 2
        self.assertEqual(transfer_order_lines[1].product, self.product2)
        self.assertNotEqual(
            str(transfer_order_lines[1].quantity), 
            payload['lines_info'][1]['quantity']
        )

    def test_if_view_wont_edit_transfer_order_lines_when_is_dirty_is_false(self):

        payload = self.get_premade_payload()
        payload['lines_info'][0]['is_dirty'] = False

        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### TransferOrderLines
        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertNotEqual(
            transfer_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )

        # Model 2
        self.assertEqual(transfer_order_lines[1].product, self.product2)
        self.assertEqual(
            transfer_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )

    def test_if_view_can_can_accept_an_empty_lines_info(self):

        payload = self.get_premade_payload()
        payload['lines_info'] = []

        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

    def test_if_view_can_can_handle_a_wrong_transfer_order_line_reg_no(self):

        payload = self.get_premade_payload()
        payload['lines_info'][0]['reg_no'] = 112121

        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### TransferOrderLines
        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertNotEqual(
            transfer_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )

        # Model 2
        self.assertEqual(transfer_order_lines[1].product, self.product2)
        self.assertEqual(
            transfer_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )

    def test_if_a_transfer_order_line_can_be_added(self):

        payload = self.get_premade_payload()
        payload['lines_to_add'] = [
            {
                'quantity': 15,
                'product_reg_no': self.product3.reg_no,
            }
        ]

        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### TransferOrderLines
        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')
        self.assertEqual(transfer_order_lines.count(), 3)

        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertEqual(
            transfer_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )

        # Model 2
        self.assertEqual(transfer_order_lines[1].product, self.product2)
        self.assertEqual(
            transfer_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )

        # Model 3
        self.assertEqual(transfer_order_lines[2].product, self.product3)
        self.assertEqual(
            transfer_order_lines[2].quantity, 
            15
        )
    
    def test_if_multiple_transfer_order_lines_can_be_added(self):
        
        TransferOrderLine.objects.all().delete()

        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')
        self.assertEqual(transfer_order_lines.count(), 0)

        payload = self.get_premade_payload()
        payload['lines_to_add'] = [
            {
                'quantity': 2,
                'product_reg_no': self.product1.reg_no,
            },
            {
                'quantity': 3,
                'product_reg_no': self.product2.reg_no,
            },
            {
                'quantity': 4,
                'product_reg_no': self.product3.reg_no,
            }
        ]

        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### TransferOrderLines
        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')
        self.assertEqual(transfer_order_lines.count(), 3)

        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertEqual(
            transfer_order_lines[0].quantity, 
            payload['lines_to_add'][0]['quantity']
        )

        # Model 2
        self.assertEqual(transfer_order_lines[1].product, self.product2)
        self.assertEqual(
            transfer_order_lines[1].quantity, 
            payload['lines_to_add'][1]['quantity']
        )

        # Model 3
        self.assertEqual(transfer_order_lines[2].product, self.product3)
        self.assertEqual(
            transfer_order_lines[2].quantity, 
            payload['lines_to_add'][2]['quantity']
        )

    def test_if_view_can_handle_a_wrong_product_reg_no_when_adding(self):

        payload = self.get_premade_payload()
        payload['lines_to_add'] = [
            {
                'quantity': 2,
                'product_reg_no': 4444,
            }
        ]

        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')
        self.assertEqual(transfer_order_lines.count(), 2)

        ##### TransferOrderLines
        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertEqual(
            transfer_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )

        # Model 2
        self.assertEqual(transfer_order_lines[1].product, self.product2)
        self.assertEqual(
            transfer_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )

    def test_if_a_transfer_order_line_can_be_removed(self):

        payload = self.get_premade_payload()
        payload['lines_to_remove'] = [
            {'reg_no': self.transfer_order_line2.reg_no},
        ]

        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')
        self.assertEqual(transfer_order_lines.count(), 1)

        ##### TransferOrderLines
        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertEqual(
            transfer_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )

    def test_if_all_store_delivery_lines_can_be_removed(self):

        payload = self.get_premade_payload()
        payload['lines_to_remove'] = [
            {'reg_no': self.transfer_order_line1.reg_no},
            {'reg_no': self.transfer_order_line2.reg_no,},
        ]

        # Count Number of Queries #
        # with self.assertNumQueries(11):
        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')
        self.assertEqual(transfer_order_lines.count(), 0)
    
    def test_if_when_a_wrong_reg_no_is_passed_in_lines_info_delete(self):

        payload = self.get_premade_payload()
        payload['lines_to_remove'] = [{'reg_no': 111}]

        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')
        self.assertEqual(transfer_order_lines.count(), 2)

        ##### TransferOrderLines
        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertEqual(
            transfer_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )

        # Model 2
        self.assertEqual(transfer_order_lines[1].product, self.product2)
        self.assertEqual(
            transfer_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )

    def test_view_can_only_be_edited_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 404)

        ##### Confirm no edit was done
        ##### TransferOrderLines
        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertNotEqual(
            transfer_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )

        # Model 2
        self.assertEqual(transfer_order_lines[1].product, self.product2)
        self.assertNotEqual(
            transfer_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )

    def test_view_cant_be_edited_by_an_employee_user(self):

        # Login a employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 403)

        ##### Confirm no edit was done
        ##### TransferOrderLines
        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertNotEqual(
            transfer_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )

        # Model 2
        self.assertEqual(transfer_order_lines[1].product, self.product2)
        self.assertNotEqual(
            transfer_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )
    def test_view_cant_be_edited_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse(
                'api:transfer_order_view', 
                args=(self.transfer_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 401)

        ##### Confirm no edit was done
        ##### TransferOrderLines
        transfer_order_lines = TransferOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(transfer_order_lines[0].product, self.product1)
        self.assertNotEqual(
            transfer_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )

        # Model 2
        self.assertEqual(transfer_order_lines[1].product, self.product2)
        self.assertNotEqual(
            transfer_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )

class TransferOrderViewStatusForEditingTestCase(APITestCase, InitialUserDataMixin):

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
            barcode='code123'
        )
        self.product3.stores.add(self.store1, self.store2)

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 100
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 155
        stock_level.save()

        # Update stock level for product 3
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product3)
        stock_level.units = 255
        stock_level.save()

        self.create_transfer_order()

    def create_transfer_order(self):

        # Create tranfer order
        self.transfer_order = TransferOrder.objects.create(
            user=self.user1,
            source_store=self.store1,
            destination_store=self.store2,
            notes='This is just a simple note',
            quantity=24,
        )

        # Create line 1
        self.transfer_order_line1 =  TransferOrderLine.objects.create(
            transfer_order=self.transfer_order,
            product=self.product1,
            quantity=10
        )
    
        # Create line 2
        self.transfer_order_line2 = TransferOrderLine.objects.create(
            transfer_order=self.transfer_order,
            product=self.product2,
            quantity=14,
        )

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """        
        payload = {
            'status': TransferOrder.TRANSFER_ORDER_RECEIVED, 
        }

        return payload

    def test_view_can_be_called_successefully(self):

        # Confirm purchase order values stock level units
        po = TransferOrder.objects.get(source_store=self.store1)

        self.assertEqual(po.status, TransferOrder.TRANSFER_ORDER_PENDING)
        self.assertEqual(po.order_completed, False)

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 100.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 155.00)

        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 0.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 0.00)

        payload = self.get_premade_payload()

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.put(
            reverse('api:transfer_order_view-status', 
            args=(po.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 200)

        po = TransferOrder.objects.get(source_store=self.store1)

        self.assertEqual(po.status, TransferOrder.TRANSFER_ORDER_RECEIVED)
        self.assertEqual(po.order_completed, True)

        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 90.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 141.00)

        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 10.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 14.00)

        ########################## Test maintaince ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.put(
            reverse('api:transfer_order_view-status', 
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

        po = TransferOrder.objects.get(source_store=self.store1)

        response = self.client.put(
            reverse('api:transfer_order_view-status', 
            args=(po.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 403)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        po = TransferOrder.objects.get(source_store=self.store1)

        response = self.client.put(
            reverse('api:transfer_order_view-status', 
            args=(po.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 401)



class TransferOrderViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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


        self.create_transfer_order()

    def create_transfer_order(self):

        ########### Create stock adjustment1
        self.transfer_order1 = TransferOrder.objects.create(
            user=self.user1,
            source_store=self.store1,
            destination_store=self.store2,
            notes='This is just a simple note1',
            quantity=24,
        )

        # Create transfer_order1
        TransferOrderLine.objects.create(
            transfer_order=self.transfer_order1,
            product=self.product1,
            quantity=10,
        )
    
        # Create transfer_order2
        TransferOrderLine.objects.create(
            transfer_order=self.transfer_order1,
            product=self.product2,
            quantity=14,
        )


        ########### Create stock adjustment2
        self.transfer_order2 = TransferOrder.objects.create(
            user=self.user1,
            source_store=self.store2,
            destination_store=self.store1,
            notes='This is just a simple note2',
            quantity=15
        )

        # Create transfer_order1
        TransferOrderLine.objects.create(
            transfer_order=self.transfer_order2,
            product=self.product1,
            quantity=10,
        )
    
        # Create transfer_order2
        TransferOrderLine.objects.create(
            transfer_order=self.transfer_order2,
            product=self.product2,
            quantity=5,
        )

    def test_view_can_delete_a_transfer_order(self):

        response = self.client.delete(
            reverse('api:transfer_order_view', 
            args=(self.transfer_order1.reg_no,))
        )
        self.assertEqual(response.status_code, 204)

        # Confirm the transfer_order was deleted
        self.assertEqual(TransferOrder.objects.filter(
            reg_no=self.transfer_order1.reg_no).exists(), False
        )

    def test_view_can_handle_wrong_transfer_order_reg_no(self):

        response = self.client.delete(
            reverse('api:transfer_order_view', 
            args=(44444,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the transfer_order was not deleted
        self.assertEqual(TransferOrder.objects.filter(
            reg_no=self.transfer_order1.reg_no).exists(), True
        )

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:transfer_order_view', 
            args=(self.transfer_order1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the transfer_order was not deleted
        self.assertEqual(TransferOrder.objects.filter(
            reg_no=self.transfer_order1.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_employee_user(self):

        # Login a employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:transfer_order_view', 
            args=(self.transfer_order1.reg_no,))
        )
        self.assertEqual(response.status_code, 403)

        # Confirm the transfer_order was not deleted
        self.assertEqual(TransferOrder.objects.filter(
            reg_no=self.transfer_order1.reg_no).exists(), True
        )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:transfer_order_view', 
            args=(self.transfer_order1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

        # Confirm the transfer_order was not deleted
        self.assertEqual(TransferOrder.objects.filter(
            reg_no=self.transfer_order1.reg_no).exists(), True
        )
