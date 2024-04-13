import json
from pprint import pprint

from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model
from django.conf import settings

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from accounts.models import UserGroup

from core.test_utils.create_user import create_new_supplier
from core.test_utils.initial_user_data import InitialUserDataMixin
from core.test_utils.custom_testcase import APITestCase

from products.models import Product

from mysettings.models import MySetting
from inventories.models import (
    PurchaseOrder,
    PurchaseOrderAdditionalCost,
    PurchaseOrderLine,
    StockLevel
)

class PurchaseOrderIndexViewTestCase(APITestCase, InitialUserDataMixin):

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
        token = Token.objects.get(user__email='kate@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)


        # Create a supplier users
        self.supplier1 = create_new_supplier(self.top_profile1, 'jeremy')
        self.supplier2 = create_new_supplier(self.top_profile1, 'james')


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

        self.create_purchase_order()

    def create_purchase_order(self):

        # Create purchase order1
        PurchaseOrder.objects.create(
            # user=self.user1,
            user=get_user_model().objects.get(email='james@gmail.com'),
            supplier=self.supplier1,
            store=self.store1,
            notes='This is just a simple note1',
            status=PurchaseOrder.PURCHASE_ORDER_PENDING,
            total_amount=3400.00
        )
        self.purchase_order1 = PurchaseOrder.objects.get(store=self.store1)

        # Create purchase order line 1
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order1,
            product=self.product1,
            quantity=10,
            purchase_cost=150,
        )
    
        # Create purchase order line 2
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order1,
            product=self.product2,
            quantity=14,
            purchase_cost=100
        )


        # Create purchase order additional cost 1
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order1,
            name='Transport',
            amount=200
        )
    
        # Create purchase order additional cost 2
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order1,
            name='Labour',
            amount=300
        )


        ########### Create purchase order2
        PurchaseOrder.objects.create(
            user=self.user1,
            supplier=self.supplier2,
            store=self.store2,
            notes='This is just a simple note2',
            status=PurchaseOrder.PURCHASE_ORDER_RECEIVED,
            total_amount=2300.00
        )
        self.purchase_order2 = PurchaseOrder.objects.get(store=self.store2)

        # Create purchase order line 1
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order2,
            product=self.product1,
            quantity=10,
            purchase_cost=150,
        )
    
        # Create purchase order line 2
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order2,
            product=self.product2,
            quantity=14,
            purchase_cost=100
        )


        # Create purchase order additional cost 1
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order2,
            name='Loading',
            amount=200
        )
    
        # Create purchase order additional cost 2
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order2,
            name='Storage',
            amount=300
        )
    
    def test_view_returns_the_user_purchase_orders_only(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        response = self.client.get(reverse('api:purchase_order_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.purchase_order2.__str__(), 
                    'supplier_name': self.supplier2.name, 
                    'store_name': self.store2.name, 
                    'status': self.purchase_order2.status, 
                    'total_amount': str(self.purchase_order2.total_amount), 
                    'reg_no': self.purchase_order2.reg_no, 
                    'creation_date': self.purchase_order2.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'completion_date': self.purchase_order2.get_completed_date(
                        self.user1.get_user_timezone()
                    ),
                    'expectation_date': self.purchase_order2.get_expected_date(
                        self.user1.get_user_timezone()
                    ),
                    
                }, 
                {
                    'name': self.purchase_order1.__str__(), 
                    'supplier_name': self.supplier1.name, 
                    'store_name': self.store1.name, 
                    'status': self.purchase_order1.status, 
                    'total_amount': str(self.purchase_order1.total_amount), 
                    'reg_no': self.purchase_order1.reg_no, 
                    'creation_date': self.purchase_order1.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'completion_date': self.purchase_order1.get_completed_date(
                        self.user1.get_user_timezone()
                    ),
                    'expectation_date': self.purchase_order1.get_expected_date(
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
                },
            ],
            'suppliers': [
                {
                    'name': self.supplier1.name, 
                    'reg_no': self.supplier1.reg_no
                }, 
                {
                    'name': self.supplier2.name, 
                    'reg_no': self.supplier2.reg_no
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
                reverse('api:purchase_order_index'))
        self.assertEqual(response.status_code, 401)

'''
    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all purchase_orders
        PurchaseOrder.objects.all().delete()

        pagination_page_size = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION

        model_num_to_be_created = pagination_page_size+1

        purchase_order_names = []
        for i in range(model_num_to_be_created):
            purchase_order_names.append(f'New PurchaseOrder{i}')

        names_length = len(purchase_order_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm purchase_orders
        for i in range(names_length):
            PurchaseOrder.objects.create(
                user=self.user1,
                supplier=self.supplier1,
                store=self.store1,
                notes=f'This is just a simple note{i}',
                status=PurchaseOrder.PURCHASE_ORDER_PENDING,
            )

        self.assertEqual(
            PurchaseOrder.objects.filter(user=self.user1).count(),
            names_length)  # Confirm models were created

    
        purchase_orders = PurchaseOrder.objects.filter(user=self.user1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(26):
            response = self.client.get(
                reverse('api:purchase_order_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 
            'http://testserver/api/purchase-orders/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all purchase orders are listed except the first one since it's in the next paginated page #
        i = 0
        for purchase_order in purchase_orders[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], purchase_order.__str__())
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], purchase_order.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
                reverse('api:purchase_order_index')  + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/purchase-orders/',
            'results': [
                {
                    'name': purchase_orders[0].__str__(), 
                    'supplier_name': self.supplier1.name, 
                    'store_name': self.store1.name, 
                    'status': purchase_orders[0].status, 
                    'total_amount': str(purchase_orders[0].total_amount), 
                    'reg_no': purchase_orders[0].reg_no, 
                    'creation_date': purchase_orders[0].get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'completion_date': purchase_orders[0].get_completed_date(
                        self.user1.get_user_timezone()
                    ),
                    'expectation_date': purchase_orders[0].get_expected_date(
                        self.user1.get_user_timezone()
                    )
                },
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
            ],
            'suppliers': [
                {
                    'name': self.supplier1.name, 
                    'reg_no': self.supplier1.reg_no
                }, 
                {
                    'name': self.supplier2.name, 
                    'reg_no': self.supplier2.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_perform_search(self):

        param = f'?search={self.purchase_order2.reg_no}'
        response = self.client.get(reverse('api:purchase_order_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.purchase_order2.__str__(), 
                    'supplier_name': self.supplier2.name, 
                    'store_name': self.store2.name, 
                    'status': self.purchase_order2.status, 
                    'total_amount': str(self.purchase_order2.total_amount), 
                    'reg_no': self.purchase_order2.reg_no, 
                    'creation_date': self.purchase_order2.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'completion_date': self.purchase_order2.get_completed_date(
                        self.user1.get_user_timezone()
                    ),
                    'expectation_date': self.purchase_order2.get_expected_date(
                        self.user1.get_user_timezone()
                    )
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
            ],
            'suppliers': [
                {
                    'name': self.supplier1.name, 
                    'reg_no': self.supplier1.reg_no
                }, 
                {
                    'name': self.supplier2.name, 
                    'reg_no': self.supplier2.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_status(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?status={PurchaseOrder.PURCHASE_ORDER_RECEIVED}'
        response = self.client.get(reverse('api:purchase_order_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.purchase_order2.__str__(), 
                    'supplier_name': self.supplier2.name, 
                    'store_name': self.store2.name, 
                    'status': self.purchase_order2.status, 
                    'total_amount': str(self.purchase_order2.total_amount), 
                    'reg_no': self.purchase_order2.reg_no, 
                    'creation_date': self.purchase_order2.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'completion_date': self.purchase_order2.get_completed_date(
                        self.user1.get_user_timezone()
                    ),
                    'expectation_date': self.purchase_order2.get_expected_date(
                        self.user1.get_user_timezone()
                    )
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
            ],
            'suppliers': [
                {
                    'name': self.supplier1.name, 
                    'reg_no': self.supplier1.reg_no
                }, 
                {
                    'name': self.supplier2.name, 
                    'reg_no': self.supplier2.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_store(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?store_reg_no={self.store1.reg_no}'
        response = self.client.get(reverse('api:purchase_order_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.purchase_order1.__str__(), 
                    'supplier_name': self.supplier1.name, 
                    'store_name': self.store1.name, 
                    'status': self.purchase_order1.status, 
                    'total_amount': str(self.purchase_order1.total_amount), 
                    'reg_no': self.purchase_order1.reg_no, 
                    'creation_date': self.purchase_order1.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'completion_date': self.purchase_order1.get_completed_date(
                        self.user1.get_user_timezone()
                    ),
                    'expectation_date': self.purchase_order1.get_expected_date(
                        self.user1.get_user_timezone()
                    )
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
            ],
            'suppliers': [
                {
                    'name': self.supplier1.name, 
                    'reg_no': self.supplier1.reg_no
                }, 
                {
                    'name': self.supplier2.name, 
                    'reg_no': self.supplier2.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_can_filter_supplier(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?supplier_reg_no={self.supplier1.reg_no}'
        response = self.client.get(reverse('api:purchase_order_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.purchase_order1.__str__(), 
                    'supplier_name': self.supplier1.name, 
                    'store_name': self.store1.name, 
                    'status': self.purchase_order1.status, 
                    'total_amount': str(self.purchase_order1.total_amount), 
                    'reg_no': self.purchase_order1.reg_no, 
                    'creation_date': self.purchase_order1.get_created_date(
                        self.user1.get_user_timezone()
                    ),
                    'completion_date': self.purchase_order1.get_completed_date(
                        self.user1.get_user_timezone()
                    ),
                    'expectation_date': self.purchase_order1.get_expected_date(
                        self.user1.get_user_timezone()
                    )
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
            ],
            'suppliers': [
                {
                    'name': self.supplier1.name, 
                    'reg_no': self.supplier1.reg_no
                }, 
                {
                    'name': self.supplier2.name, 
                    'reg_no': self.supplier2.reg_no
                }
            ]
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    def test_view_returns_empty_when_there_are_no_purchase_orders(self):

        # First delete all purchase_orders
        PurchaseOrder.objects.all().delete()

        response = self.client.get(
                reverse('api:purchase_order_index'))
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
            ],
            'suppliers': [
                {
                    'name': self.supplier1.name, 
                    'reg_no': self.supplier1.reg_no
                }, 
                {
                    'name': self.supplier2.name, 
                    'reg_no': self.supplier2.reg_no
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
                reverse('api:purchase_order_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'stores': [
                {
                    'name': self.store3.name, 
                    'reg_no': self.store3.reg_no
                }
            ],
            'suppliers': []
        }

        self.assertEqual(json.loads(json.dumps(response.data)), result)

    # def test_view_cant_be_viewed_by_an_employee_user(self):

    #     # Login an employee user
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     response = self.client.get(
    #             reverse('api:purchase_order_index'))
    #     self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:purchase_order_index'))
        self.assertEqual(response.status_code, 401)


class PurchaseOrderCreateViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a supplier user
        self.supplier = create_new_supplier(self.top_profile1, 'jeremy')

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
        next_day_timestamp = 1634926712
        
        payload = {
            'notes': 'This is just a simple note',
            'supplier_reg_no': self.supplier.reg_no,
            'store_reg_no': self.store1.reg_no,
            'created_date_timestamp': next_day_timestamp,
            'status': PurchaseOrder.PURCHASE_ORDER_PENDING,
            'purchase_order_lines': [
                {
                    'product_reg_no': self.product1.reg_no,
                    'quantity': 10,
                    'purchase_cost': 150,
                },
                {
                    'product_reg_no': self.product2.reg_no,
                    'quantity': 14,
                    'purchase_cost': 100,
                }
            ],
            'purchase_order_additional_cost': [
                {
                    'name': 'Transport',
                    'amount': 200,
                },
                {
                    'name': 'Labour',
                    'amount': 300,
                }
            ]
        }

        return payload 
    
    def test_if_view_can_create_a_model_with_zero_created_timestamp(self):

        payload = self.get_premade_payload()
        payload['created_date_timestamp'] = 0

        response = self.client.post(
            reverse('api:purchase_order_index'), 
            payload
        )
        self.assertEqual(response.status_code, 201)

        po = PurchaseOrder.objects.get(store=self.store1)

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual((po.created_date).strftime("%B, %d, %Y"), today)

    def test_if_view_wont_change_created_date_if_user_does_not_have_can_edit_purchase_order_date_perm(self):

        # Remove permisson
        permission = Permission.objects.get(codename='can_edit_purchase_order_date')
        Group.objects.get(user=self.user1).permissions.remove(permission)

        # Confirm user has permission
        user = get_user_model().objects.get(email='john@gmail.com')
        self.assertEqual(
            user.has_perm('accounts.can_edit_purchase_order_date'),
            False
        )

        payload = self.get_premade_payload()
        payload['created_date_timestamp'] = 1634926712

        response = self.client.post(
            reverse('api:purchase_order_index'), 
            payload
        )
        self.assertEqual(response.status_code, 201)

        po = PurchaseOrder.objects.get(store=self.store1)

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual((po.created_date).strftime("%B, %d, %Y"), today)

    def test_if_view_only_changes_created_date_if_user_has_can_edit_purchase_order_date_perm(self):

        # Confirm user has permission
        user = get_user_model().objects.get(email='john@gmail.com')
        self.assertEqual(
            user.has_perm('accounts.can_edit_purchase_order_date'),
            True
        )

        payload = self.get_premade_payload()
        payload['created_date_timestamp'] = 1634926712

        response = self.client.post(
            reverse('api:purchase_order_index'), 
            payload
        )
        self.assertEqual(response.status_code, 201)

        po = PurchaseOrder.objects.get(store=self.store1)

        self.assertEqual(
            po.get_created_date(self.user1.get_user_timezone()),
            'October, 22, 2021, 09:18:PM'
        )

    def test_if_view_can_create_a_model_as_draft(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:purchase_order_index'), 
            payload
        )

        self.assertEqual(response.status_code, 201)

        po = PurchaseOrder.objects.get(store=self.store1)

        # Confirm model creation
        self.assertEqual(PurchaseOrder.objects.all().count(), 1)
    
        product1 = Product.objects.get(name='Shampoo')
        product2 = Product.objects.get(name='Conditioner')

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(po.user, self.user1)
        self.assertEqual(po.supplier, self.supplier)
        self.assertEqual(po.store, self.store1)
        self.assertEqual(po.notes, payload['notes'])
        self.assertEqual(po.status, PurchaseOrder.PURCHASE_ORDER_PENDING)
        self.assertEqual(po.total_amount, 3400)
        self.assertEqual(po.order_completed, False)
        self.assertTrue(po.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(po.get_created_date(
            self.user1.get_user_timezone()
        ),'October, 22, 2021, 09:18:PM')

        # Confirm purshase order line model creation
        self.assertEqual(PurchaseOrderLine.objects.filter(purchase_order=po).count(), 2)

        lines = PurchaseOrderLine.objects.filter(purchase_order=po).order_by('id')

        # PurchaseOrder line 1
        line1 = lines[0]

        self.assertEqual(line1.purchase_order, po)
        self.assertEqual(line1.product, product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'tax_rate': str(self.product1.tax_rate),
                'reg_no': self.product1.reg_no,
            }
        )
        self.assertEqual(line1.quantity, 10.00)
        self.assertEqual(line1.purchase_cost, 150.00)
        self.assertEqual(line1.amount, 1500.00)
        

        # PurchaseOrder line 2
        line2 = lines[1]

        self.assertEqual(line2.purchase_order, po)
        self.assertEqual(line2.product, product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku,
                'tax_rate': str(self.product2.tax_rate),
                'reg_no': self.product2.reg_no,
            }
        )
        self.assertEqual(line2.quantity, 14.00)
        self.assertEqual(line2.purchase_cost, 100.00)
        self.assertEqual(line2.amount, 1400.00)


        # Confirm purshase order additional cost model creation
        self.assertEqual(PurchaseOrderAdditionalCost.objects.filter(purchase_order=po).count(), 2)

        costs = PurchaseOrderAdditionalCost.objects.filter(purchase_order=po).order_by('id')

        # PurchaseOrder addititonal cost 1
        cost1 = costs[0]

        self.assertEqual(cost1.purchase_order, po)
        self.assertEqual(cost1.name, 'Transport')

        # PurchaseOrder addititonal cost 2
        cost1 = costs[1]

        self.assertEqual(cost1.purchase_order, po)
        self.assertEqual(cost1.name, 'Labour')

    def test_view_wont_change_stock_if_status_is_pending(self):
        
        # Confirm initial stock levels
        levels = StockLevel.objects.all()
        for level in levels:
            self.assertEqual(level.units, 0)

        payload = self.get_premade_payload()
        payload['status'] = PurchaseOrder.PURCHASE_ORDER_PENDING

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.post(
            reverse('api:purchase_order_index'), 
            payload
        )
        self.assertEqual(response.status_code, 201)

        po = PurchaseOrder.objects.get(store=self.store1)

        self.assertEqual(po.status, PurchaseOrder.PURCHASE_ORDER_PENDING)
        self.assertEqual(po.order_completed, False)

        # Confirm stock levels were not changed
        levels = StockLevel.objects.all()
        for level in levels:
            self.assertEqual(level.units, 0)

    def test_view_will_change_stock_if_status_is_received(self):

        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product1).units, 
            0
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product2).units, 
            0
        )

        payload = self.get_premade_payload()
        payload['status'] = PurchaseOrder.PURCHASE_ORDER_RECEIVED

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.post(
            reverse('api:purchase_order_index'), 
            payload
        )
        self.assertEqual(response.status_code, 201)

        po = PurchaseOrder.objects.get(store=self.store1)

        self.assertEqual(po.status, PurchaseOrder.PURCHASE_ORDER_RECEIVED)
        self.assertEqual(po.order_completed, True)

        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product1).units, 
            10.00
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product2).units, 
            14.00
        )

    def test_if_view_can_handle_with_wrong_supplier_reg_no(self):

        wrong_reg_nos = [
            33463476347374, # Wrong reg no
            self.store3.reg_no, # Store for another user
            11111111111111111111111111111111111111 # Long reg no
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_reg_nos:

            payload = self.get_premade_payload()
            payload['supplier_reg_no'] = wrong_reg_no

            response = self.client.post(
                reverse('api:purchase_order_index'), 
                payload
            )

            self.assertEqual(response.status_code, 404)

            # Confirm model was not creation
            self.assertEqual(PurchaseOrder.objects.all().count(), 0)

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
                reverse('api:purchase_order_index'), 
                payload
            )

            self.assertEqual(response.status_code, 404)

            # Confirm model was not creation
            self.assertEqual(PurchaseOrder.objects.all().count(), 0)
 
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
            PurchaseOrder.objects.all().delete()
            PurchaseOrderLine.objects.all().delete()

            payload['purchase_order_lines'][0]['product_reg_no'] = wrong_reg_no

            response = self.client.post(
                reverse('api:purchase_order_index'),
                payload,
            )

            self.assertEqual(response.status_code, 400)

            result = {'non_field_errors': 'Product error.'}
            self.assertEqual(response.data, result)


            # Confirm model creation
            self.assertEqual(PurchaseOrder.objects.all().count(), 0)

    def test_if_view_can_handle_empty_purchase_order_additional_cost(self):

        payload = self.get_premade_payload()

        payload['purchase_order_additional_cost'] = []

        response = self.client.post(
            reverse('api:purchase_order_index'), 
            payload
        )

        self.assertEqual(response.status_code, 201)

        # Confirm model creation
        self.assertEqual(PurchaseOrder.objects.all().count(), 1)
        self.assertEqual(PurchaseOrderLine.objects.filter().count(), 2)
        self.assertEqual(PurchaseOrderAdditionalCost.objects.filter().count(), 0)

    def test_if_view_url_can_throttle_post_requests(self):

        payload = self.get_premade_payload()

        throttle_rate = int(settings.THROTTLE_RATES['api_purchase_order_rate'].split("/")[0])
    
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:purchase_order_index'),
                payload,
            )
            self.assertEqual(response.status_code, 201)


        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional 
        # request if the previous request was not throttled 
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:purchase_order_index'),
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
            reverse('api:purchase_order_index'), 
            payload,
        )
        self.assertEqual(response.status_code, 401)

class PurchaseOrderViewForViewingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a supplier users
        self.supplier1 = create_new_supplier(self.top_profile1, 'jeremy')
        self.supplier2 = create_new_supplier(self.top_profile1, 'james')

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


        self.create_purchase_order()

    def create_purchase_order(self):

        # Create purchase order1
        self.purchase_order1 = PurchaseOrder.objects.create(
            user=self.user1,
            supplier=self.supplier1,
            store=self.store1,
            notes='This is just a simple note1',
            status=PurchaseOrder.PURCHASE_ORDER_PENDING,
        )

        # Create purchase order line 1
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order1,
            product=self.product1,
            quantity=10,
            purchase_cost=150,
        )
    
        # Create purchase order line 2
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order1,
            product=self.product2,
            quantity=14,
            purchase_cost=100
        )


        # Create purchase order additional cost 1
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order1,
            name='Transport',
            amount=200
        )
    
        # Create purchase order additional cost 2
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order1,
            name='Labour',
            amount=300
        )


        ########### Create purchase order2
        self.purchase_order2 = PurchaseOrder.objects.create(
            user=self.user1,
            supplier=self.supplier2,
            store=self.store2,
            notes='This is just a simple note2',
            status=PurchaseOrder.PURCHASE_ORDER_RECEIVED,
        )

        # Create purchase order line 1
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order2,
            product=self.product1,
            quantity=10,
            purchase_cost=150,
        )
    
        # Create purchase order line 2
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order2,
            product=self.product2,
            quantity=14,
            purchase_cost=100
        )


        # Create purchase order additional cost 1
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order2,
            name='Loading',
            amount=200
        )
    
        # Create purchase order additional cost 2
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order2,
            name='Storage',
            amount=300
        )


    def test_view_can_be_called_successefully(self):

        purchase_order = PurchaseOrder.objects.get(store=self.store1)

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.get(
            reverse('api:purchase_order_view', 
            args=(purchase_order.reg_no,))
        )
        self.assertEqual(response.status_code, 200)

        lines = purchase_order.purchaseorderline_set.all().order_by('id')
        costs = purchase_order.purchaseorderadditionalcost_set.all().order_by('id')

        result = {
            'name': purchase_order.__str__(), 
            'notes': purchase_order.notes, 
            'supplier_data': {
                'name': self.supplier1.name, 
                'email': self.supplier1.email, 
                'phone': self.supplier1.phone, 
                'location': self.supplier1.get_location_desc(),
                'reg_no': self.supplier1.reg_no,

            }, 
            'store_data': {
                'name': self.store1.name, 
                'reg_no': self.store1.reg_no,
            }, 
            'status': 0, 
            'total_amount': str(purchase_order.total_amount),
            'reg_no': purchase_order.reg_no, 
            'ordered_by': self.user1.get_full_name(), 
            'creation_date': purchase_order.get_created_date(
                self.user1.get_user_timezone()
            ),  
            'completion_date': purchase_order.get_completed_date(
                self.user1.get_user_timezone()
            ),
            'expectation_date': purchase_order.get_expected_date(
                self.user1.get_user_timezone()
            ),
            'created_date_timestamp': purchase_order.created_date_timestamp,
            'line_data': [
                {
                    'product_info': {
                        'name': self.product1.name, 
                        'sku': self.product1.sku,
                        "tax_rate": str(self.product1.tax_rate),
                        'reg_no': self.product1.reg_no
                    }, 
                    'quantity': str(lines[0].quantity), 
                    'purchase_cost': str(lines[0].purchase_cost),
                    'amount': str(lines[0].amount),
                    'reg_no': str(lines[0].reg_no)
                },
                {
                    'product_info': {
                        'name': self.product2.name, 
                        'sku': self.product2.sku,
                        "tax_rate": str(self.product2.tax_rate),
                        'reg_no': self.product2.reg_no
                    }, 
                    'quantity': str(lines[1].quantity), 
                    'purchase_cost': str(lines[1].purchase_cost),
                    'amount': str(lines[1].amount),
                    'reg_no': str(lines[1].reg_no)
                }
            ], 
            'additional_cost_data': [
                {
                    'name': costs[0].name, 
                    'amount': str(costs[0].amount)
                }, 
                {
                    'name': costs[1].name, 
                    'amount': str(costs[1].amount)
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
            reverse('api:purchase_order_view', args=(self.purchase_order1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

    def test_view_can_handle_wrong_purchase_order_reg_no(self):

        response = self.client.get(
            reverse('api:purchase_order_view', args=(4646464,)))
        self.assertEqual(response.status_code, 404)

    # def test_view_can_only_be_viewed_by_its_owner(self):

    #     # login a top user user
    #     # Include an appropriate `Authorization:` header on all requests.
    #     token = Token.objects.get(user__email='jack@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     response = self.client.get(
    #         reverse('api:purchase_order_view', 
    #         args=(self.purchase_order1.reg_no,))
    #     )
    #     self.assertEqual(response.status_code, 404)

    # def test_view_cant_be_viewed_by_an_employee_user(self):

    #     # Login a employee user
    #     # Include an appropriate `Authorization:` header on all requests.
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     response = self.client.get(
    #         reverse('api:purchase_order_view', 
    #         args=(self.purchase_order1.reg_no,))
    #     )
    #     self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:purchase_order_view', 
            args=(self.purchase_order1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

class PurchaseOrderViewStatusTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a supplier users
        self.supplier1 = create_new_supplier(self.top_profile1, 'jeremy')
        self.supplier2 = create_new_supplier(self.top_profile1, 'james')

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

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 100
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 155
        stock_level.save()


        self.create_purchase_order()

    def create_purchase_order(self):

        # Create purchase order1
        self.purchase_order1 = PurchaseOrder.objects.create(
            user=self.user1,
            supplier=self.supplier1,
            store=self.store1,
            notes='This is just a simple note1',
            status=PurchaseOrder.PURCHASE_ORDER_PENDING,
        )

        # Create purchase order line 1
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order1,
            product=self.product1,
            quantity=10,
            purchase_cost=150,
        )
    
        # Create purchase order line 2
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order1,
            product=self.product2,
            quantity=14,
            purchase_cost=100
        )


        # Create purchase order additional cost 1
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order1,
            name='Transport',
            amount=200
        )
    
        # Create purchase order additional cost 2
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order1,
            name='Labour',
            amount=300
        )


        ########### Create purchase order2
        self.purchase_order2 = PurchaseOrder.objects.create(
            user=self.user1,
            supplier=self.supplier2,
            store=self.store2,
            notes='This is just a simple note2',
            status=PurchaseOrder.PURCHASE_ORDER_RECEIVED,
        )

        # Create purchase order line 1
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order2,
            product=self.product1,
            quantity=10,
            purchase_cost=150,
        )
    
        # Create purchase order line 2
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order2,
            product=self.product2,
            quantity=14,
            purchase_cost=100
        )


        # Create purchase order additional cost 1
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order2,
            name='Loading',
            amount=200
        )
    
        # Create purchase order additional cost 2
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order2,
            name='Storage',
            amount=300
        )

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """        
        payload = {
            'status': PurchaseOrder.PURCHASE_ORDER_RECEIVED,
        }

        return payload

    def test_view_can_be_called_successefully(self):

        # Confirm purchase order values stock level units
        po = PurchaseOrder.objects.get(store=self.store1)

        self.assertEqual(po.status, PurchaseOrder.PURCHASE_ORDER_PENDING)
        self.assertEqual(po.order_completed, False)

        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product1).units, 
            100.00
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product2).units, 
            155.00
        )

        payload = self.get_premade_payload()

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.put(
            reverse('api:purchase_order_view-status', 
            args=(po.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 200)

        po = PurchaseOrder.objects.get(store=self.store1)

        self.assertEqual(po.status, PurchaseOrder.PURCHASE_ORDER_RECEIVED)
        self.assertEqual(po.order_completed, True)

        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product1).units, 
            110.00
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store1, product=self.product2).units, 
            169.00
        )

        ########################## Test maintaince ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.put(
            reverse('api:purchase_order_view-status', 
            args=(po.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 401)

    # def test_if_view_can_only_be_edited_by_its_owner(self):

    #     # Login a employee profile #
    #     # Include an appropriate `Authorization:` header on all requests.
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     payload = self.get_premade_payload()

    #     po = PurchaseOrder.objects.get(store=self.store1)

    #     response = self.client.put(
    #         reverse('api:purchase_order_view-status', 
    #         args=(po.reg_no,)), 
    #         payload,
    #     )

    #     self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        po = PurchaseOrder.objects.get(store=self.store1)

        response = self.client.put(
            reverse('api:purchase_order_view-status', 
            args=(po.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 401)

class PurchaseOrderViewForEditing2TestCase(APITestCase, InitialUserDataMixin):
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

        # Create a supplier users
        self.supplier1 = create_new_supplier(self.top_profile1, "jeremy")
        self.supplier2 = create_new_supplier(self.top_profile1, "james")
        self.supplier3 = create_new_supplier(self.top_profile2, "richard")

        # Create models
        # Creates products
        self.product1 = Product.objects.create(
            profile=self.top_profile1,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode="code123",
        )
        self.product1.stores.add(self.store1, self.store2)

        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode="code123",
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

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 100
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 155
        stock_level.save()

        self.create_purchase_order()

    def create_purchase_order(self):
        # Create purchase order1
        self.purchase_order = PurchaseOrder.objects.create(
            user=self.user1,
            supplier=self.supplier1,
            store=self.store1,
            notes="This is just a simple note1",
            status=PurchaseOrder.PURCHASE_ORDER_PENDING,

        )

        # Create purchase order line 1
        self.po_line1 = PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order,
            product=self.product1,
            quantity=10,
            purchase_cost=150,
        )

        # Create purchase order line 2
        self.po_line2 = PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order,
            product=self.product2,
            quantity=14,
            purchase_cost=100,
        )

        # Create purchase order additional cost 1
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order, name="Transport", amount=200
        )

        # Create purchase order additional cost 2
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order, name="Labour", amount=300
        )

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """
        next_day_timestamp = 1634926712

        payload = {
            "status": PurchaseOrder.PURCHASE_ORDER_RECEIVED,
            "notes": "This is just a simple note",
            "supplier_reg_no": self.supplier2.reg_no,
            "store_reg_no": self.store2.reg_no,
            "created_date_timestamp": next_day_timestamp,
            "lines_info": [
                {
                    "quantity": 5,
                    "purchase_cost": 120,
                    "reg_no": self.po_line1.reg_no,
                    "is_dirty": True,
                },
                {
                    "quantity": 7,
                    "purchase_cost": 80,
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
            reverse("api:purchase_order_view", args=(self.purchase_order.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 200)

        ##### PurchaseOrder
        po = PurchaseOrder.objects.get()

        self.assertEqual(po.user, self.user1)
        self.assertEqual(po.supplier, self.supplier2)
        self.assertEqual(po.store, self.store2)
        self.assertEqual(po.notes, payload["notes"])
        self.assertEqual(po.total_amount, Decimal("1160.00"))
        self.assertEqual(
            po.get_created_date(self.user1.get_user_timezone()),
            "October, 22, 2021, 09:18:PM",
        )

        ##### PurchaseOrderLines
        purchase_order_lines = PurchaseOrderLine.objects.all().order_by("id")

        # Model 1
        self.assertEqual(purchase_order_lines[0].product, self.product1)
        self.assertEqual(
            purchase_order_lines[0].quantity, payload["lines_info"][0]["quantity"]
        )
        self.assertEqual(
            purchase_order_lines[0].purchase_cost,
            payload["lines_info"][0]["purchase_cost"],
        )

        # Model 2
        self.assertEqual(purchase_order_lines[1].product, self.product2)
        self.assertEqual(
            purchase_order_lines[1].quantity, payload["lines_info"][1]["quantity"]
        )
        self.assertEqual(
            purchase_order_lines[1].purchase_cost,
            payload["lines_info"][1]["purchase_cost"],
        )

    def test_view_cant_edit_a_model_when_it_has_been_received_successfully(self):

        # Make the Purchase order to be received
        po = PurchaseOrder.objects.get()
        po.status = PurchaseOrder.PURCHASE_ORDER_RECEIVED
        po.save()

        payload = self.get_premade_payload()

        # Count Number of Queries #
        # with self.assertNumQueries(14):
        response = self.client.put(
            reverse("api:purchase_order_view", args=(self.purchase_order.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 200)

        ##### PurchaseOrder
        po = PurchaseOrder.objects.get()

        self.assertEqual(po.user, self.user1)
        self.assertNotEqual(po.supplier, self.supplier2)
        self.assertNotEqual(po.store, self.store2)
        self.assertNotEqual(po.notes, payload["notes"])
        self.assertNotEqual(po.total_amount, Decimal("1160.00"))
        self.assertNotEqual(
            po.get_expected_date(self.user1.get_user_timezone()),
            "October, 22, 2021, 09:18:PM",
        )

        ##### PurchaseOrderLines
        purchase_order_lines = PurchaseOrderLine.objects.all().order_by("id")

        # Model 1
        self.assertEqual(purchase_order_lines[0].product, self.product1)
        self.assertNotEqual(
            purchase_order_lines[0].quantity, payload["lines_info"][0]["quantity"]
        )
        self.assertNotEqual(
            purchase_order_lines[0].purchase_cost,
            payload["lines_info"][0]["purchase_cost"],
        )

        # Model 2
        self.assertEqual(purchase_order_lines[1].product, self.product2)
        self.assertNotEqual(
            purchase_order_lines[1].quantity, payload["lines_info"][1]["quantity"]
        )
        self.assertNotEqual(
            purchase_order_lines[1].purchase_cost,
            payload["lines_info"][1]["purchase_cost"],
        )

    def test_if_view_can_create_a_model_with_zero_created_timestamp(self):

        payload = self.get_premade_payload()
        payload['created_date_timestamp'] = 0

        response = self.client.put(
            reverse("api:purchase_order_view", args=(self.purchase_order.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 200)

        po = PurchaseOrder.objects.get()

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual((po.created_date).strftime("%B, %d, %Y"), today)

    def test_if_view_wont_change_created_date_if_user_does_not_have_can_edit_purchase_order_date_perm(self):
        
        # Remove permisson
        permission = Permission.objects.get(codename='can_edit_purchase_order_date')
        Group.objects.get(user=self.user1).permissions.remove(permission)

        # Confirm user has permission
        user = get_user_model().objects.get(email='john@gmail.com')
        self.assertEqual(
            user.has_perm('accounts.can_edit_purchase_order_date'),
            False
        )

        payload = self.get_premade_payload()
        payload['created_date_timestamp'] = 1634926712

        response = self.client.put(
            reverse("api:purchase_order_view", args=(self.purchase_order.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 200)

        po = PurchaseOrder.objects.get()

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual((po.created_date).strftime("%B, %d, %Y"), today)

    def test_if_view_only_changes_created_date_if_user_has_can_edit_purchase_order_date_perm(self):

        # Confirm user has permission
        user = get_user_model().objects.get(email='john@gmail.com')
        self.assertEqual(
            user.has_perm('accounts.can_edit_purchase_order_date'),
            True
        )

        payload = self.get_premade_payload()
        payload['created_date_timestamp'] = 1634926712

        response = self.client.put(
            reverse("api:purchase_order_view", args=(self.purchase_order.reg_no,)),
            payload,
        )
        self.assertEqual(response.status_code, 200)

        po = PurchaseOrder.objects.get()

        self.assertEqual(
            po.get_created_date(self.user1.get_user_timezone()),
            'October, 22, 2021, 09:18:PM'
        )

    def test_if_view_can_handle_with_wrong_supplier_reg_no(self):

        wrong_reg_nos = [
            33463476347374, # Wrong reg no
            self.supplier3.reg_no, # Supplier for another user
            11111111111111111111111111111111111111 # Long reg no
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_reg_nos:

            payload = self.get_premade_payload()
            payload['supplier_reg_no'] = wrong_reg_no

            response = self.client.put(
                reverse(
                    'api:purchase_order_view', 
                    args=(self.purchase_order.reg_no,)
                ), 
                payload
            )

            self.assertEqual(response.status_code, 404)

        ##### Confirm no edit was done
        ##### PurchaseOrderLines
        purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(purchase_order_lines[0].product, self.product1)
        self.assertNotEqual(
            str(purchase_order_lines[0].quantity), 
            payload['lines_info'][0]['quantity']
        )
        self.assertNotEqual(
            str(purchase_order_lines[0].purchase_cost), 
            payload['lines_info'][0]['purchase_cost']
        )

        # Model 2
        self.assertEqual(purchase_order_lines[1].product, self.product2)
        self.assertNotEqual(
            str(purchase_order_lines[1].quantity), 
            payload['lines_info'][1]['quantity']
        )
        self.assertNotEqual(
            str(purchase_order_lines[1].purchase_cost), 
            payload['lines_info'][1]['purchase_cost']
        )

    def test_if_view_can_handle_with_wrong_store_reg_no(self):

        wrong_reg_nos = [
            33463476347374, # Wrong reg no
            self.supplier3.reg_no, # Store for another user
            11111111111111111111111111111111111111 # Long reg no
        ]

        payload = self.get_premade_payload()

        for wrong_reg_no in wrong_reg_nos:

            payload = self.get_premade_payload()
            payload['supplier_reg_no'] = wrong_reg_no

            response = self.client.put(
                reverse(
                    'api:purchase_order_view', 
                    args=(self.purchase_order.reg_no,)
                ), 
                payload
            )

            self.assertEqual(response.status_code, 404)

        ##### Confirm no edit was done
        ##### PurchaseOrderLines
        purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(purchase_order_lines[0].product, self.product1)
        self.assertNotEqual(
            str(purchase_order_lines[0].quantity), 
            payload['lines_info'][0]['quantity']
        )
        self.assertNotEqual(
            str(purchase_order_lines[0].purchase_cost), 
            payload['lines_info'][0]['purchase_cost']
        )

        # Model 2
        self.assertEqual(purchase_order_lines[1].product, self.product2)
        self.assertNotEqual(
            str(purchase_order_lines[1].quantity), 
            payload['lines_info'][1]['quantity']
        )
        self.assertNotEqual(
            str(purchase_order_lines[1].purchase_cost), 
            payload['lines_info'][1]['purchase_cost']
        )

    def test_if_view_wont_edit_purchase_order_lines_when_is_dirty_is_false(self):

        payload = self.get_premade_payload()
        payload['lines_info'][0]['is_dirty'] = False

        response = self.client.put(
            reverse(
                'api:purchase_order_view', 
                args=(self.purchase_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### PurchaseOrderLines
        purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(purchase_order_lines[0].product, self.product1)
        self.assertNotEqual(
            purchase_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )
        self.assertNotEqual(
            purchase_order_lines[0].purchase_cost, 
            payload['lines_info'][0]['purchase_cost']
        )

        # Model 2
        self.assertEqual(purchase_order_lines[1].product, self.product2)
        self.assertEqual(
            purchase_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )
        self.assertEqual(
            purchase_order_lines[1].purchase_cost, 
            payload['lines_info'][1]['purchase_cost']
        )

    def test_if_view_wont_accept_a_non_integer_created_date_timestamp(self):

        payload = self.get_premade_payload()
        payload['created_date_timestamp'] = ''

        response = self.client.put(
            reverse(
                'api:purchase_order_view', 
                args=(self.purchase_order.reg_no,)
            ), 
            payload
        )

        self.assertEqual(
            response.data,
            {'created_date_timestamp': ['A valid integer is required.']}
        )

        self.assertEqual(response.status_code, 400)

    def test_if_view_can_can_accept_an_empty_lines_info(self):

        payload = self.get_premade_payload()
        payload['lines_info'] = []

        response = self.client.put(
            reverse(
                'api:purchase_order_view', 
                args=(self.purchase_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

    def test_if_view_can_can_handle_a_wrong_purchase_order_line_reg_no(self):

        payload = self.get_premade_payload()
        payload['lines_info'][0]['reg_no'] = 112121

        response = self.client.put(
            reverse(
                'api:purchase_order_view', 
                args=(self.purchase_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### PurchaseOrderLines
        purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(purchase_order_lines[0].product, self.product1)
        self.assertNotEqual(
            purchase_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )
        self.assertNotEqual(
            purchase_order_lines[0].purchase_cost, 
            payload['lines_info'][0]['purchase_cost']
        )

        # Model 2
        self.assertEqual(purchase_order_lines[1].product, self.product2)
        self.assertEqual(
            purchase_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )
        self.assertEqual(
            purchase_order_lines[1].purchase_cost, 
            payload['lines_info'][1]['purchase_cost']
        )

    def test_if_a_purchase_order_line_can_be_added(self):

        payload = self.get_premade_payload()
        payload['lines_to_add'] = [
            {
                'quantity': 15,
                'purchase_cost': 320,
                'product_reg_no': self.product3.reg_no,
            }
        ]

        response = self.client.put(
            reverse(
                'api:purchase_order_view', 
                args=(self.purchase_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### PurchaseOrderLines
        purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')
        self.assertEqual(purchase_order_lines.count(), 3)

        # Model 1
        self.assertEqual(purchase_order_lines[0].product, self.product1)
        self.assertEqual(
            purchase_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )
        self.assertEqual(
            purchase_order_lines[0].purchase_cost, 
            payload['lines_info'][0]['purchase_cost']
        )

        # Model 2
        self.assertEqual(purchase_order_lines[1].product, self.product2)
        self.assertEqual(
            purchase_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )
        self.assertEqual(
            purchase_order_lines[1].purchase_cost, 
            payload['lines_info'][1]['purchase_cost']
        )

        # Model 3
        self.assertEqual(purchase_order_lines[2].product, self.product3)
        self.assertEqual(
            purchase_order_lines[2].quantity, 
            15
        )
        self.assertEqual(purchase_order_lines[2].purchase_cost, 320)

    def test_if_multiple_purchase_order_lines_can_be_added(self):
        
        PurchaseOrderLine.objects.all().delete()

        purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')
        self.assertEqual(purchase_order_lines.count(), 0)

        payload = self.get_premade_payload()
        payload['lines_to_add'] = [
            {
                'quantity': 2,
                'purchase_cost': 102,
                'product_reg_no': self.product1.reg_no,
            },
            {
                'quantity': 3,
                'purchase_cost': 103,
                'product_reg_no': self.product2.reg_no,
            },
            {
                'quantity': 4,
                'purchase_cost': 104,
                'product_reg_no': self.product3.reg_no,
            }
        ]

        response = self.client.put(
            reverse(
                'api:purchase_order_view', 
                args=(self.purchase_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        ##### PurchaseOrderLines
        purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')
        self.assertEqual(purchase_order_lines.count(), 3)

        # Model 1
        self.assertEqual(purchase_order_lines[0].product, self.product1)
        self.assertEqual(
            purchase_order_lines[0].quantity, 
            payload['lines_to_add'][0]['quantity']
        )
        self.assertEqual(
            purchase_order_lines[0].purchase_cost, 
            payload['lines_to_add'][0]['purchase_cost']
        )

        # Model 2
        self.assertEqual(purchase_order_lines[1].product, self.product2)
        self.assertEqual(
            purchase_order_lines[1].quantity, 
            payload['lines_to_add'][1]['quantity']
        )
        self.assertEqual(
            purchase_order_lines[1].purchase_cost, 
            payload['lines_to_add'][1]['purchase_cost']
        )

        # Model 3
        self.assertEqual(purchase_order_lines[2].product, self.product3)
        self.assertEqual(
            purchase_order_lines[2].quantity, 
            payload['lines_to_add'][2]['quantity']
        )
        self.assertEqual(
            purchase_order_lines[2].purchase_cost, 
            payload['lines_to_add'][2]['purchase_cost']
        )

    def test_if_view_can_handle_a_wrong_product_reg_no_when_adding(self):

        payload = self.get_premade_payload()
        payload['lines_to_add'] = [
            {
                'quantity': 2,
                'purchase_cost': 102,
                'product_reg_no': 4444,
            }
        ]

        response = self.client.put(
            reverse(
                'api:purchase_order_view', 
                args=(self.purchase_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')
        self.assertEqual(purchase_order_lines.count(), 2)

        ##### PurchaseOrderLines
        # Model 1
        self.assertEqual(purchase_order_lines[0].product, self.product1)
        self.assertEqual(
            purchase_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )
        self.assertEqual(
            purchase_order_lines[0].purchase_cost, 
            payload['lines_info'][0]['purchase_cost']
        )

        # Model 2
        self.assertEqual(purchase_order_lines[1].product, self.product2)
        self.assertEqual(
            purchase_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )
        self.assertEqual(
            purchase_order_lines[1].purchase_cost, 
            payload['lines_info'][1]['purchase_cost']
        )

    def test_if_a_purchase_order_line_can_be_removed(self):

        payload = self.get_premade_payload()
        payload['lines_to_remove'] = [
            {'reg_no': self.po_line2.reg_no},
        ]

        response = self.client.put(
            reverse(
                'api:purchase_order_view', 
                args=(self.purchase_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')
        self.assertEqual(purchase_order_lines.count(), 1)

        ##### PurchaseOrderLines
        # Model 1
        self.assertEqual(purchase_order_lines[0].product, self.product1)
        self.assertEqual(
            purchase_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )
        self.assertEqual(
            purchase_order_lines[0].purchase_cost, 
            payload['lines_info'][0]['purchase_cost']
        )

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
                'api:purchase_order_view', 
                args=(self.purchase_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')
        self.assertEqual(purchase_order_lines.count(), 0)

    def test_if_when_a_wrong_reg_no_is_passed_in_lines_info_delete(self):

        payload = self.get_premade_payload()
        payload['lines_to_remove'] = [{'reg_no': 111}]

        response = self.client.put(
            reverse(
                'api:purchase_order_view', 
                args=(self.purchase_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')
        self.assertEqual(purchase_order_lines.count(), 2)

        ##### PurchaseOrderLines
        # Model 1
        self.assertEqual(purchase_order_lines[0].product, self.product1)
        self.assertEqual(
            purchase_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )
        self.assertEqual(
            purchase_order_lines[0].purchase_cost, 
            payload['lines_info'][0]['purchase_cost']
        )

        # Model 2
        self.assertEqual(purchase_order_lines[1].product, self.product2)
        self.assertEqual(
            purchase_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )
        self.assertEqual(
            purchase_order_lines[1].purchase_cost, 
            payload['lines_info'][1]['purchase_cost']
        )

    def test_view_can_only_be_edited_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse(
                'api:purchase_order_view', 
                args=(self.purchase_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 404)

        ##### Confirm no edit was done
        ##### PurchaseOrderLines
        purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(purchase_order_lines[0].product, self.product1)
        self.assertNotEqual(
            purchase_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )
        self.assertNotEqual(
            purchase_order_lines[0].purchase_cost, 
            payload['lines_info'][0]['purchase_cost']
        )

        # Model 2
        self.assertEqual(purchase_order_lines[1].product, self.product2)
        self.assertNotEqual(
            purchase_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )
        self.assertNotEqual(
            purchase_order_lines[1].purchase_cost, 
            payload['lines_info'][1]['purchase_cost']
        )

    # def test_view_cant_be_edited_by_an_employee_user(self):

    #     # Login a employee user
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     payload = self.get_premade_payload()

    #     response = self.client.put(
    #         reverse(
    #             'api:purchase_order_view', 
    #             args=(self.purchase_order.reg_no,)
    #         ), 
    #         payload
    #     )
    #     self.assertEqual(response.status_code, 404)

    #     ##### Confirm no edit was done
    #     ##### PurchaseOrderLines
    #     purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')

    #     # Model 1
    #     self.assertEqual(purchase_order_lines[0].product, self.product1)
    #     self.assertNotEqual(
    #         purchase_order_lines[0].quantity, 
    #         payload['lines_info'][0]['quantity']
    #     )
    #     self.assertNotEqual(
    #         purchase_order_lines[0].purchase_cost, 
    #         payload['lines_info'][0]['purchase_cost']
    #     )

    #     # Model 2
    #     self.assertEqual(purchase_order_lines[1].product, self.product2)
    #     self.assertNotEqual(
    #         purchase_order_lines[1].quantity, 
    #         payload['lines_info'][1]['quantity']
    #     )
    #     self.assertNotEqual(
    #         purchase_order_lines[1].purchase_cost, 
    #         payload['lines_info'][1]['purchase_cost']
    #     )

    def test_view_cant_be_edited_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse(
                'api:purchase_order_view', 
                args=(self.purchase_order.reg_no,)
            ), 
            payload
        )
        self.assertEqual(response.status_code, 401)

        ##### Confirm no edit was done
        ##### PurchaseOrderLines
        purchase_order_lines = PurchaseOrderLine.objects.all().order_by('id')

        # Model 1
        self.assertEqual(purchase_order_lines[0].product, self.product1)
        self.assertNotEqual(
            purchase_order_lines[0].quantity, 
            payload['lines_info'][0]['quantity']
        )
        self.assertNotEqual(
            purchase_order_lines[0].purchase_cost, 
            payload['lines_info'][0]['purchase_cost']
        )

        # Model 2
        self.assertEqual(purchase_order_lines[1].product, self.product2)
        self.assertNotEqual(
            purchase_order_lines[1].quantity, 
            payload['lines_info'][1]['quantity']
        )
        self.assertNotEqual(
            purchase_order_lines[1].purchase_cost, 
            payload['lines_info'][1]['purchase_cost']
        )

class PurchaseOrderViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create a supplier users
        self.supplier1 = create_new_supplier(self.top_profile1, 'jeremy')
        self.supplier2 = create_new_supplier(self.top_profile1, 'james')


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


        self.create_purchase_order()

    def create_purchase_order(self):

        # Create purchase order1
        self.purchase_order1 = PurchaseOrder.objects.create(
            user=self.user1,
            supplier=self.supplier1,
            store=self.store1,
            notes='This is just a simple note1',
            status=PurchaseOrder.PURCHASE_ORDER_PENDING,
        )

        # Create purchase order line 1
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order1,
            product=self.product1,
            quantity=10,
            purchase_cost=150,
        )
    
        # Create purchase order line 2
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order1,
            product=self.product2,
            quantity=14,
            purchase_cost=100
        )

        # Create purchase order additional cost 1
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order1,
            name='Transport',
            amount=200
        )
    
        # Create purchase order additional cost 2
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order1,
            name='Labour',
            amount=300
        )


        ########### Create purchase order2
        self.purchase_order2 = PurchaseOrder.objects.create(
            user=self.user1,
            supplier=self.supplier2,
            store=self.store2,
            notes='This is just a simple note2',
            status=PurchaseOrder.PURCHASE_ORDER_RECEIVED,
        )

        # Create purchase order line 1
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order2,
            product=self.product1,
            quantity=10,
            purchase_cost=150,
        )
    
        # Create purchase order line 2
        PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order2,
            product=self.product2,
            quantity=14,
            purchase_cost=100
        )

        # Create purchase order additional cost 1
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order2,
            name='Loading',
            amount=200
        )
    
        # Create purchase order additional cost 2
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order2,
            name='Storage',
            amount=300
        )
    def test_view_can_delete_a_purchase_order(self):

        response = self.client.delete(
            reverse('api:purchase_order_view', 
            args=(self.purchase_order1.reg_no,))
        )
        self.assertEqual(response.status_code, 204)

        # Confirm the purchase_order was deleted
        self.assertEqual(PurchaseOrder.objects.filter(
            reg_no=self.purchase_order1.reg_no).exists(), False
        )

    def test_view_can_handle_wrong_purchase_order_reg_no(self):

        response = self.client.delete(
            reverse('api:purchase_order_view', 
            args=(44444,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the purchase_order was not deleted
        self.assertEqual(PurchaseOrder.objects.filter(
            reg_no=self.purchase_order1.reg_no).exists(), True
        )

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:purchase_order_view', 
            args=(self.purchase_order1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the purchase_order was not deleted
        self.assertEqual(PurchaseOrder.objects.filter(
            reg_no=self.purchase_order1.reg_no).exists(), True
        )

    # def test_view_cant_be_deleted_by_an_employee_user(self):

    #     # Login a employee user
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     response = self.client.delete(
    #         reverse('api:purchase_order_view', 
    #         args=(self.purchase_order1.reg_no,))
    #     )
    #     self.assertEqual(response.status_code, 404)

    #     # Confirm the purchase_order was not deleted
    #     self.assertEqual(PurchaseOrder.objects.filter(
    #         reg_no=self.purchase_order1.reg_no).exists(), True
    #     )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:purchase_order_view', 
            args=(self.purchase_order1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

        # Confirm the purchase_order was not deleted
        self.assertEqual(PurchaseOrder.objects.filter(
            reg_no=self.purchase_order1.reg_no).exists(), True
        )
'''