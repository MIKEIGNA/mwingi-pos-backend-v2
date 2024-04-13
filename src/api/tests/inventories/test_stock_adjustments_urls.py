import json

from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.initial_user_data import InitialUserDataMixin

from core.test_utils.custom_testcase import APITestCase

from products.models import Product

from mysettings.models import MySetting
from inventories.models import StockAdjustment, StockAdjustmentLine


class StockAdjustmentIndexViewTestCase(APITestCase, InitialUserDataMixin):

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


        self.create_stock_adjustment()

    def create_stock_adjustment(self):

        ########### Create stock adjustment1
        self.stock_adjustment1 = StockAdjustment.objects.create(
            user=self.user1,
            store=self.store1,
            notes='This is just a simple note1',
            reason=StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS,
            quantity=24,
        )

        # Create stock_adjustment1
        StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment1,
            product=self.product1,
            add_stock=10,
            cost=150,
        )
    
        # Create stock_adjustment2
        StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment1,
            product=self.product2,
            add_stock=14,
            cost=100,
        )


        ########### Create stock adjustment2
        self.stock_adjustment2 = StockAdjustment.objects.create(
            user=self.user1,
            store=self.store2,
            notes='This is just a simple note2',
            reason=StockAdjustment.STOCK_ADJUSTMENT_LOSS,
            quantity=15
        )

        # Create stock_adjustment1
        StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment2,
            product=self.product1,
            add_stock=10,
            cost=150,
        )
    
        # Create stock_adjustment2
        StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment2,
            product=self.product2,
            add_stock=5,
            cost=100,
        )

    def test_view_returns_the_user_stock_adjustments_only(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        response = self.client.get(reverse('api:stock_adjustment_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.stock_adjustment2.__str__(), 
                    'reason': StockAdjustment.STOCK_ADJUSTMENT_LOSS, 
                    'reason_desc': self.stock_adjustment2.get_reason_desc(), 
                    'store_name': self.store2.name, 
                    'str_quantity': f'{self.stock_adjustment2.quantity}.00', 
                    'reg_no': self.stock_adjustment2.reg_no, 
                    'creation_date': self.stock_adjustment2.get_created_date(
                        self.user1.get_user_timezone()
                    )
                }, 
                {
                    'name': self.stock_adjustment1.__str__(), 
                    'reason': StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS, 
                    'reason_desc': self.stock_adjustment1.get_reason_desc(), 
                    'store_name': self.store1.name, 
                    'str_quantity': f'{self.stock_adjustment1.quantity}.00', 
                    'reg_no': self.stock_adjustment1.reg_no, 
                    'creation_date': self.stock_adjustment1.get_created_date(
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
                reverse('api:stock_adjustment_index'))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all stock_adjustments
        StockAdjustment.objects.all().delete()

        pagination_page_size = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION

        model_num_to_be_created = pagination_page_size+1

        stock_adjustment_names = []
        for i in range(model_num_to_be_created):
            stock_adjustment_names.append(f'New StockAdjustment{i}')

        names_length = len(stock_adjustment_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm stock_adjustments
        for i in range(names_length):
            StockAdjustment.objects.create(
                user=self.user1,
                store=self.store1,
                notes=f'This is just a simple note{i}',
                reason=StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS,
                quantity=24,
            )

        self.assertEqual(
            StockAdjustment.objects.filter(user=self.user1).count(),
            names_length)  # Confirm models were created

    
        stock_adjustments = StockAdjustment.objects.filter(user=self.user1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(17):
            response = self.client.get(
                reverse('api:stock_adjustment_index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 
            'http://testserver/api/stock-adjustments/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all stock adjustments are listed except the first one since it's in the next paginated page #
        i = 0
        for stock_adjustment in stock_adjustments[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], stock_adjustment.__str__())
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], stock_adjustment.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
                reverse('api:stock_adjustment_index')  + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/stock-adjustments/',
            'results': [
                {
                    'name': stock_adjustments[0].__str__(), 
                    'reason': StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS, 
                    'reason_desc': stock_adjustments[0].get_reason_desc(), 
                    'store_name': self.store1.name, 
                    'str_quantity': '24.00', 
                    'reg_no': stock_adjustments[0].reg_no, 
                    'creation_date': stock_adjustments[0].get_created_date(
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

    def test_view_can_perform_search(self):

        param = f'?search={self.stock_adjustment2.reg_no}'
        response = self.client.get(reverse('api:stock_adjustment_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.stock_adjustment2.__str__(), 
                    'reason': StockAdjustment.STOCK_ADJUSTMENT_LOSS, 
                    'reason_desc': self.stock_adjustment2.get_reason_desc(), 
                    'store_name': self.store2.name, 
                    'str_quantity': f'{self.stock_adjustment2.quantity}.00', 
                    'reg_no': self.stock_adjustment2.reg_no, 
                    'creation_date': self.stock_adjustment2.get_created_date(
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
        response = self.client.get(reverse('api:stock_adjustment_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.stock_adjustment1.__str__(), 
                    'reason': StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS, 
                    'reason_desc': self.stock_adjustment1.get_reason_desc(), 
                    'store_name': self.store1.name, 
                    'str_quantity': f'{self.stock_adjustment1.quantity}.00', 
                    'reg_no': self.stock_adjustment1.reg_no, 
                    'creation_date': self.stock_adjustment1.get_created_date(
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

    def test_view_can_filter_reason(self):

        # Count Number of Queries #
        #with self.assertNumQueries(6):
        param = f'?reason={StockAdjustment.STOCK_ADJUSTMENT_LOSS}'
        response = self.client.get(reverse('api:stock_adjustment_index') + param)

        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.stock_adjustment2.__str__(), 
                    'reason': StockAdjustment.STOCK_ADJUSTMENT_LOSS, 
                    'reason_desc': self.stock_adjustment2.get_reason_desc(), 
                    'store_name': self.store2.name, 
                    'str_quantity': f'{self.stock_adjustment2.quantity}.00', 
                    'reg_no': self.stock_adjustment2.reg_no, 
                    'creation_date': self.stock_adjustment2.get_created_date(
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

    def test_view_returns_empty_when_there_are_no_stock_adjustments(self):

        # First delete all stock_adjustments
        StockAdjustment.objects.all().delete()

        response = self.client.get(
                reverse('api:stock_adjustment_index'))
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
                reverse('api:stock_adjustment_index'))
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
    #             reverse('api:stock_adjustment_index'))
    #     self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:stock_adjustment_index'))
        self.assertEqual(response.status_code, 401)

class StockAdjustmentCreateViewTestCase(APITestCase, InitialUserDataMixin):

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

    def get_premade_payload_for_receive_items(self):
        """
        Simplifies creating payload
        """
        
        payload = {
            'notes': 'A simple note',
            'reason': StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS,
            'store_reg_no': self.store1.reg_no,
            'stock_adjustment_lines': [
                {
                    'product_reg_no': self.product1.reg_no,
                    'add_stock': 60,
                    'counted_stock': 80,
                    'remove_stock': 90,
                    'cost': 180,
                },
                {
                    'product_reg_no': self.product2.reg_no,
                    'add_stock': 40,
                    'counted_stock': 60,
                    'remove_stock': 70,
                    'cost': 150,
                }
            ]
        }

        return payload  

    def get_premade_payload_for_loss_or_damage(self, is_loss=True):
        """
        Simplifies creating payload
        """

        if is_loss:
            reason = StockAdjustment.STOCK_ADJUSTMENT_LOSS
        else:
            reason = StockAdjustment.STOCK_ADJUSTMENT_DAMAGE

        payload = {
            'notes': 'A simple note',
            'reason': reason,
            'store_reg_no': self.store1.reg_no,
            'stock_adjustment_lines': [
                {
                    'product_reg_no': self.product1.reg_no,
                    'add_stock': 60,
                    'counted_stock': 80,
                    'remove_stock': 90,
                    'cost': 180,
                },
                {
                    'product_reg_no': self.product2.reg_no,
                    'add_stock': 40,
                    'counted_stock': 60,
                    'remove_stock': 70,
                    'cost': 150,
                }
            ]
        }

        return payload 
    
    def get_premade_payload_for_removing(self, reason):
        """
        Simplifies creating payload
        """

        # if is_loss:
        #     reason = StockAdjustment.STOCK_ADJUSTMENT_LOSS
        # else:
        #     reason = StockAdjustment.STOCK_ADJUSTMENT_DAMAGE

        payload = {
            'notes': 'A simple note',
            'reason': reason,
            'store_reg_no': self.store1.reg_no,
            'stock_adjustment_lines': [
                {
                    'product_reg_no': self.product1.reg_no,
                    'add_stock': 60,
                    'counted_stock': 80,
                    'remove_stock': 90,
                    'cost': 180,
                },
                {
                    'product_reg_no': self.product2.reg_no,
                    'add_stock': 40,
                    'counted_stock': 60,
                    'remove_stock': 70,
                    'cost': 150,
                }
            ]
        }

        return payload
  
    def test_if_view_when_we_are_in_maintenance_mode(self):

        payload = self.get_premade_payload_for_receive_items()

        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=True
        ms.save()
              
        response = self.client.post(
            reverse('api:stock_adjustment_index'), 
            payload,
        )
            
        self.assertEqual(response.status_code, 401)

    def test_if_view_can_create_a_stock_adjustment_for_received_items(self):

        payload = self.get_premade_payload_for_receive_items()

        # Count Number of Queries
        # with self.assertNumQueries(31):
        response = self.client.post(reverse('api:stock_adjustment_index'), payload)
        self.assertEqual(response.status_code, 201)

        sa = StockAdjustment.objects.get(store=self.store1)

        # Confirm model creation
        self.assertEqual(StockAdjustment.objects.all().count(), 1)
    
        product1 = Product.objects.get(name='Shampoo')
        product2 = Product.objects.get(name='Conditioner')

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(sa.user, self.user1)
        self.assertEqual(sa.store, self.store1)
        self.assertEqual(sa.notes, payload['notes'])
        self.assertEqual(sa.reason, StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS)
        self.assertEqual(sa.quantity, 100.00)
        self.assertTrue(sa.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((sa.created_date).strftime("%B, %d, %Y"), today)


        # Confirm receipt line model creation
        self.assertEqual(StockAdjustmentLine.objects.filter(stock_adjustment=sa).count(), 2)

        lines = StockAdjustmentLine.objects.filter(stock_adjustment=sa).order_by('id')

        # StockAdjustment line 1
        line1 = lines[0]

        self.assertEqual(line1.stock_adjustment, sa)
        self.assertEqual(line1.product, product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku
            }
        )
        self.assertEqual(line1.add_stock, 60.00)
        self.assertEqual(line1.counted_stock, 0.00)
        self.assertEqual(line1.remove_stock, 0.00)
        self.assertEqual(line1.cost, 180.00)
        

        # StockAdjustment line 2
        line2 = lines[1]

        self.assertEqual(line2.stock_adjustment, sa)
        self.assertEqual(line2.product, product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku
            }
        )
        self.assertEqual(line2.add_stock, 40.00)
        self.assertEqual(line2.counted_stock, 0.00)
        self.assertEqual(line2.remove_stock, 0.00)
        self.assertEqual(line2.cost, 150.00)
    
    def test_if_view_can_create_a_stock_adjustment_for_loss(self):

        payload = self.get_premade_payload_for_removing(
            reason=StockAdjustment.STOCK_ADJUSTMENT_LOSS
        )

        # Count Number of Queries
        # with self.assertNumQueries(31):
        response = self.client.post(reverse('api:stock_adjustment_index'), payload)
        self.assertEqual(response.status_code, 201)

        sa = StockAdjustment.objects.get(store=self.store1)

        # Confirm model creation
        self.assertEqual(StockAdjustment.objects.all().count(), 1)
    
        product1 = Product.objects.get(name='Shampoo')
        product2 = Product.objects.get(name='Conditioner')

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(sa.user, self.user1)
        self.assertEqual(sa.store, self.store1)
        self.assertEqual(sa.notes, payload['notes'])
        self.assertEqual(sa.reason, StockAdjustment.STOCK_ADJUSTMENT_LOSS)
        self.assertEqual(sa.quantity, 160.00)
        self.assertTrue(sa.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((sa.created_date).strftime("%B, %d, %Y"), today)


        # Confirm receipt line model creation
        self.assertEqual(StockAdjustmentLine.objects.filter(stock_adjustment=sa).count(), 2)

        lines = StockAdjustmentLine.objects.filter(stock_adjustment=sa).order_by('id')

        # StockAdjustment line 1
        line1 = lines[0]

        self.assertEqual(line1.stock_adjustment, sa)
        self.assertEqual(line1.product, product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku
            }
        )
        self.assertEqual(line1.add_stock, 0.00)
        self.assertEqual(line1.counted_stock, 0.00)
        self.assertEqual(line1.remove_stock, 90.00)
        self.assertEqual(line1.cost, 0.00)
        

        # StockAdjustment line 2
        line2 = lines[1]

        self.assertEqual(line2.stock_adjustment, sa)
        self.assertEqual(line2.product, product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku
            }
        )
        self.assertEqual(line2.add_stock, 0.00)
        self.assertEqual(line2.counted_stock, 0.00)
        self.assertEqual(line2.remove_stock, 70.00)
        self.assertEqual(line2.cost, 0.00)
    
    def test_if_view_can_create_a_stock_adjustment_for_damage(self):

        payload = self.get_premade_payload_for_removing(
            reason=StockAdjustment.STOCK_ADJUSTMENT_DAMAGE
        )

        # Count Number of Queries
        # with self.assertNumQueries(31):
        response = self.client.post(reverse('api:stock_adjustment_index'), payload)
        self.assertEqual(response.status_code, 201)

        sa = StockAdjustment.objects.get(store=self.store1)

        # Confirm model creation
        self.assertEqual(StockAdjustment.objects.all().count(), 1)
    
        product1 = Product.objects.get(name='Shampoo')
        product2 = Product.objects.get(name='Conditioner')

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(sa.user, self.user1)
        self.assertEqual(sa.store, self.store1)
        self.assertEqual(sa.notes, payload['notes'])
        self.assertEqual(sa.reason, StockAdjustment.STOCK_ADJUSTMENT_DAMAGE)
        self.assertEqual(sa.quantity, 160.00)
        self.assertTrue(sa.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((sa.created_date).strftime("%B, %d, %Y"), today)


        # Confirm receipt line model creation
        self.assertEqual(StockAdjustmentLine.objects.filter(stock_adjustment=sa).count(), 2)

        lines = StockAdjustmentLine.objects.filter(stock_adjustment=sa).order_by('id')

        # StockAdjustment line 1
        line1 = lines[0]

        self.assertEqual(line1.stock_adjustment, sa)
        self.assertEqual(line1.product, product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku
            }
        )
        self.assertEqual(line1.add_stock, 0.00)
        self.assertEqual(line1.counted_stock, 0.00)
        self.assertEqual(line1.remove_stock, 90.00)
        self.assertEqual(line1.cost, 0.00)
        

        # StockAdjustment line 2
        line2 = lines[1]

        self.assertEqual(line2.stock_adjustment, sa)
        self.assertEqual(line2.product, product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku
            }
        )
        self.assertEqual(line2.add_stock, 0.00)
        self.assertEqual(line2.counted_stock, 0.00)
        self.assertEqual(line2.remove_stock, 70.00)
        self.assertEqual(line2.cost, 0.00)

    def test_if_view_can_create_a_stock_adjustment_for_expired(self):

        payload = self.get_premade_payload_for_removing(
            reason=StockAdjustment.STOCK_ADJUSTMENT_EXPIRY
        )

        # Count Number of Queries
        # with self.assertNumQueries(31):
        response = self.client.post(reverse('api:stock_adjustment_index'), payload)
        self.assertEqual(response.status_code, 201)

        sa = StockAdjustment.objects.get(store=self.store1)

        # Confirm model creation
        self.assertEqual(StockAdjustment.objects.all().count(), 1)
    
        product1 = Product.objects.get(name='Shampoo')
        product2 = Product.objects.get(name='Conditioner')

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(sa.user, self.user1)
        self.assertEqual(sa.store, self.store1)
        self.assertEqual(sa.notes, payload['notes'])
        self.assertEqual(sa.reason, StockAdjustment.STOCK_ADJUSTMENT_EXPIRY)
        self.assertEqual(sa.quantity, 160.00)
        self.assertTrue(sa.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((sa.created_date).strftime("%B, %d, %Y"), today)


        # Confirm receipt line model creation
        self.assertEqual(StockAdjustmentLine.objects.filter(stock_adjustment=sa).count(), 2)

        lines = StockAdjustmentLine.objects.filter(stock_adjustment=sa).order_by('id')

        # StockAdjustment line 1
        line1 = lines[0]

        self.assertEqual(line1.stock_adjustment, sa)
        self.assertEqual(line1.product, product1)
        self.assertEqual(
            line1.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku
            }
        )
        self.assertEqual(line1.add_stock, 0.00)
        self.assertEqual(line1.counted_stock, 0.00)
        self.assertEqual(line1.remove_stock, 90.00)
        self.assertEqual(line1.cost, 0.00)
        

        # StockAdjustment line 2
        line2 = lines[1]

        self.assertEqual(line2.stock_adjustment, sa)
        self.assertEqual(line2.product, product2)
        self.assertEqual(
            line2.product_info, 
            {
                'name': self.product2.name,
                'sku': self.product2.sku
            }
        )
        self.assertEqual(line2.add_stock, 0.00)
        self.assertEqual(line2.counted_stock, 0.00)
        self.assertEqual(line2.remove_stock, 70.00)
        self.assertEqual(line2.cost, 0.00)
       
    def test_if_view_can_handle_with_wrong_store_reg_no(self):

        wrong_reg_nos = [
            33463476347374, # Wrong reg no
            self.store3.reg_no, # Store for another user
            11111111111111111111111111111111111111 # Long reg no
        ]

        payload = self.get_premade_payload_for_receive_items()

        for wrong_reg_no in wrong_reg_nos:

            payload = self.get_premade_payload_for_receive_items()
            payload['store_reg_no'] = wrong_reg_no

            response = self.client.post(
                reverse('api:stock_adjustment_index'), 
                payload
            )

            self.assertEqual(response.status_code, 404)

            # Confirm model was not creation
            self.assertEqual(StockAdjustment.objects.all().count(), 0)
    
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

        payload = self.get_premade_payload_for_receive_items()

        for wrong_reg_no in wrong_reg_nos:

            # Delete previous models
            StockAdjustment.objects.all().delete()
            StockAdjustmentLine.objects.all().delete()

            payload['stock_adjustment_lines'][0]['product_reg_no'] = wrong_reg_no

            response = self.client.post(
                reverse('api:stock_adjustment_index'),
                payload,
            )

            self.assertEqual(response.status_code, 400)

            result = {'non_field_errors': 'Product error.'}
            self.assertEqual(response.data, result)


            # Confirm model creation
            self.assertEqual(StockAdjustment.objects.all().count(), 0)


    def test_if_view_url_can_throttle_post_requests(self):

        payload = self.get_premade_payload_for_receive_items()

        throttle_rate = int(settings.THROTTLE_RATES['api_10_per_minute_create_rate'].split("/")[0])
    
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:stock_adjustment_index'),
                payload,
            )
            self.assertEqual(response.status_code, 201)


        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional 
        # request if the previous request was not throttled 
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:stock_adjustment_index'),
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

        payload = self.get_premade_payload_for_receive_items()

        response = self.client.post(
            reverse('api:stock_adjustment_index'), 
            payload,
        )
        self.assertEqual(response.status_code, 401)


class StockAdjustmentViewForViewingTestCase(APITestCase, InitialUserDataMixin):

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


        self.create_stock_adjustment()

    def create_stock_adjustment(self):

        ########### Create stock adjustment1
        self.stock_adjustment1 = StockAdjustment.objects.create(
            user=self.user1,
            store=self.store1,
            notes='This is just a simple note1',
            reason=StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS,
            quantity=24,
        )

        # Create stock_adjustment1
        StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment1,
            product=self.product1,
            add_stock=10,
            cost=150,
        )
    
        # Create stock_adjustment2
        StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment1,
            product=self.product2,
            add_stock=14,
            cost=100,
        )


        ########### Create stock adjustment2
        self.stock_adjustment2 = StockAdjustment.objects.create(
            user=self.user1,
            store=self.store2,
            notes='This is just a simple note2',
            reason=StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS,
            quantity=15
        )

        # Create stock_adjustment1
        StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment2,
            product=self.product1,
            add_stock=10,
            cost=150,
        )
    
        # Create stock_adjustment2
        StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment2,
            product=self.product2,
            add_stock=5,
            cost=100,
        )

    def test_view_can_be_called_successefully(self):

        stock_adjustment = StockAdjustment.objects.get(quantity=24)

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.get(
            reverse('api:stock_adjustment_view', 
            args=(stock_adjustment.reg_no,))
        )
        self.assertEqual(response.status_code, 200)

        lines = stock_adjustment.stockadjustmentline_set.all().order_by('id')

        result = {
            'name': stock_adjustment.__str__(), 
            'notes': stock_adjustment.notes, 
            'reason': stock_adjustment.reason, 
            'reason_desc': self.stock_adjustment1.get_reason_desc(), 
            'store_name': stock_adjustment.get_store_name(), 
            'quantity': str(stock_adjustment.quantity), 
            'reg_no': stock_adjustment.reg_no, 
            'adjusted_by': self.user1.get_full_name(), 
            'creation_date': stock_adjustment.get_created_date(
                self.user1.get_user_timezone()
            ), 
            'line_data': [
                {
                    'product_info': {
                        'name': self.product1.name, 
                        'sku': self.product1.sku
                    }, 
                    'add_stock': str(lines[0].add_stock), 
                    'remove_stock': str(lines[0].remove_stock),
                    'cost': str(lines[0].cost)
                },
                {
                    'product_info': {
                        'name': self.product2.name, 
                        'sku': self.product2.sku
                    }, 
                    'add_stock': str(lines[1].add_stock), 
                    'remove_stock': str(lines[1].remove_stock),
                    'cost': str(lines[1].cost)
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
            reverse('api:stock_adjustment_view', args=(self.stock_adjustment1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

    def test_view_can_handle_wrong_stock_adjustment_reg_no(self):

        response = self.client.get(
            reverse('api:stock_adjustment_view', args=(4646464,)))
        self.assertEqual(response.status_code, 404)

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
            reverse('api:stock_adjustment_view', 
            args=(self.stock_adjustment1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    # def test_view_cant_be_viewed_by_an_employee_user(self):

    #     # Login a employee user
    #     # Include an appropriate `Authorization:` header on all requests.
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     response = self.client.get(
    #         reverse('api:stock_adjustment_view', 
    #         args=(self.stock_adjustment1.reg_no,))
    #     )
    #     self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:stock_adjustment_view', 
            args=(self.stock_adjustment1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

class StockAdjustmentViewForDeletingTestCase(APITestCase, InitialUserDataMixin):

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


        self.create_stock_adjustment()

    def create_stock_adjustment(self):

        ########### Create stock adjustment1
        self.stock_adjustment1 = StockAdjustment.objects.create(
            user=self.user1,
            store=self.store1,
            notes='This is just a simple note1',
            reason=StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS,
            quantity=24,
        )

        # Create stock_adjustment1
        StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment1,
            product=self.product1,
            add_stock=10,
            cost=150,
        )
    
        # Create stock_adjustment2
        StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment1,
            product=self.product2,
            add_stock=14,
            cost=100,
        )


        ########### Create stock adjustment2
        self.stock_adjustment2 = StockAdjustment.objects.create(
            user=self.user1,
            store=self.store2,
            notes='This is just a simple note2',
            reason=StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS,
            quantity=15
        )

        # Create stock_adjustment1
        StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment2,
            product=self.product1,
            add_stock=10,
            cost=150,
        )
    
        # Create stock_adjustment2
        StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment2,
            product=self.product2,
            add_stock=5,
            cost=100,
        )

    def test_view_can_delete_a_stock_adjustment(self):

        response = self.client.delete(
            reverse('api:stock_adjustment_view', 
            args=(self.stock_adjustment1.reg_no,))
        )
        self.assertEqual(response.status_code, 204)

        # Confirm the stock_adjustment was deleted
        self.assertEqual(StockAdjustment.objects.filter(
            reg_no=self.stock_adjustment1.reg_no).exists(), False
        )

    def test_view_can_handle_wrong_stock_adjustment_reg_no(self):

        response = self.client.delete(
            reverse('api:stock_adjustment_view', 
            args=(44444,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the stock_adjustment was not deleted
        self.assertEqual(StockAdjustment.objects.filter(
            reg_no=self.stock_adjustment1.reg_no).exists(), True
        )

    def test_view_can_only_be_deleted_by_the_owner(self):

        # Login a top user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(
            reverse('api:stock_adjustment_view', 
            args=(self.stock_adjustment1.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

        # Confirm the stock_adjustment was not deleted
        self.assertEqual(StockAdjustment.objects.filter(
            reg_no=self.stock_adjustment1.reg_no).exists(), True
        )

    # def test_view_cant_be_deleted_by_an_employee_user(self):

    #     # Login a employee user
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     response = self.client.delete(
    #         reverse('api:stock_adjustment_view', 
    #         args=(self.stock_adjustment1.reg_no,))
    #     )
    #     self.assertEqual(response.status_code, 404)

    #     # Confirm the stock_adjustment was not deleted
    #     self.assertEqual(StockAdjustment.objects.filter(
    #         reg_no=self.stock_adjustment1.reg_no).exists(), True
    #     )

    def test_view_cant_be_deleted_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:stock_adjustment_view', 
            args=(self.stock_adjustment1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

        # Confirm the stock_adjustment was not deleted
        self.assertEqual(StockAdjustment.objects.filter(
            reg_no=self.stock_adjustment1.reg_no).exists(), True
        )
