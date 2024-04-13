from decimal import Decimal
import json
from pprint import pprint
import uuid

from django.contrib.auth.models import Permission
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from accounts.tasks import receipt_change_stock_tasks

from core.test_utils.create_store_models import create_new_category, create_new_discount, create_new_tax
from core.test_utils.initial_user_data import InitialUserDataMixin

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.create_user import create_new_customer
from core.test_utils.log_reader import get_test_firebase_sender_log_content
from inventories.models.stock_models import InventoryHistory

from profiles.models import Customer, LoyaltySetting

from sales.models import Receipt, ReceiptLine, ReceiptPayment

from mysettings.models import MySetting
from inventories.models import StockLevel
from products.models import Product
from stores.models import StorePaymentMethod

User = get_user_model()

'''
class PosReceiptIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        self.create_receipt()

    def create_receipt(self):

        #Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')

        #Create a category
        self.category = create_new_category(self.top_profile1, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.top_profile1, 'chris')

        # Create a product
        product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        # Create receipt1
        self.receipt = Receipt.objects.create(
            user=self.top_profile1.user,
            store=self.store1,
            customer=self.customer,
            customer_info={
                'name': self.customer.name, 
                'reg_no': self.customer.reg_no
            },
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=222,
            created_date_timestamp=1632748682
        )

        pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.CASH_TYPE
        )
        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=pay_method,
            amount=2500
        )

        # Create receipt line1
        self.receiptline1 =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=product1,
            product_info={'name': product1.name},
            price=1750,
            units=7
        )
    
        # Create receipt line2
        self.receiptline2 =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=product2,
            product_info={'name': product2.name},
            price=2500,
            units=10
        )
   
    def test_view_returns_the_user_receipts_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(7):
            response = self.client.get(
                reverse('api:pos_receipt_index', args=(self.store1.reg_no,)))
            self.assertEqual(response.status_code, 200)

        receipt = Receipt.objects.get(store=self.store1)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'customer_info': {
                        'name': self.customer.name, 
                        'email': self.customer.email,
                        'phone': self.customer.phone,
                        'tax_pin': self.customer.tax_pin,
                        'reg_no': self.customer.reg_no,
                    }, 
                    'name': receipt.__str__(), 
                    'receipt_number': receipt.receipt_number,
                    'refund_for_receipt_number': receipt.refund_for_receipt_number,
                    'discount_amount': f'{receipt.discount_amount}',  
                    'tax_amount': f'{receipt.tax_amount}', 
                    'subtotal_amount': f'{receipt.subtotal_amount}', 
                    'total_amount': f'{receipt.total_amount}', 
                    'given_amount': f'{receipt.given_amount}', 
                    'change_amount': f'{receipt.change_amount}', 
                    'transaction_type': receipt.transaction_type, 
                    'payment_completed': receipt.payment_completed, 
                    'receipt_closed': receipt.receipt_closed, 
                    'is_refund': receipt.is_refund, 
                    'item_count': receipt.item_count,
                    'local_reg_no': receipt.local_reg_no, 
                    'reg_no': receipt.reg_no, 
                    'creation_date': receipt.get_created_date(
                        self.user1.get_user_timezone()
                    ), 
                    'created_date_timestamp': receipt.created_date_timestamp,
                    'receipt_data': receipt.get_receipt_view_data()
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
            reverse('api:pos_receipt_index', args=(self.store1.reg_no,))
        )
        self.assertEqual(response.status_code, 401)
    
    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all receipt
        Receipt.objects.all().delete()

        pagination_page_size = settings.LEAN_PAGINATION_PAGE_SIZE

        model_num_to_be_created = pagination_page_size+1

        # Create and confirm receipts
        for i in range(model_num_to_be_created):
            Receipt.objects.create(
                user=self.top_profile1.user,
                store=self.store1,
                customer=self.customer,
                discount_amount=401.00,
                tax_amount=60.00,
                given_amount=2500.00,
                change_amount=500.00,
                subtotal_amount=2000,
                total_amount=1599.00,
                transaction_type=0,
                payment_completed=True,
                local_reg_no=i,
                receipt_number=i,
            )

        self.assertEqual(
            Receipt.objects.filter(user=self.user1).count(),
            model_num_to_be_created)  # Confirm models were created

    
        receipts = Receipt.objects.filter(user=self.user1).order_by('-id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        #with self.assertNumQueries(3):
        response = self.client.get(reverse('api:pos_receipt_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], f'http://testserver/api/pos/receipts/{self.store1.reg_no}/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # Check if all receipts are listed except the first one since it's in 
        # the next paginated page #
        i = 0
        for receipt in receipts[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], receipt.__str__())
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], receipt.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)


        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:pos_receipt_index', args=(self.store1.reg_no,)) + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': f'http://testserver/api/pos/receipts/{self.store1.reg_no}/', 
            'results': [
                {
                    'customer_info': receipts[0].customer_info, 
                    'name': receipts[0].__str__(), 
                    'receipt_number': receipts[0].receipt_number,
                    'refund_for_receipt_number': receipts[0].refund_for_receipt_number,
                    'discount_amount': f'{receipts[0].discount_amount}',  
                    'tax_amount': f'{receipts[0].tax_amount}', 
                    'subtotal_amount': f'{receipts[0].subtotal_amount}', 
                    'total_amount': f'{receipts[0].total_amount}', 
                    'given_amount': f'{receipts[0].given_amount}', 
                    'change_amount': f'{receipts[0].change_amount}', 
                    'transaction_type': receipts[0].transaction_type, 
                    'payment_completed': receipts[0].payment_completed, 
                    'receipt_closed': receipts[0].receipt_closed, 
                    'is_refund': receipts[0].is_refund, 
                    'item_count': receipts[0].item_count,
                    'local_reg_no': receipts[0].local_reg_no,
                    'reg_no': receipts[0].reg_no, 
                    'creation_date': receipts[0].get_created_date(
                        self.user1.get_user_timezone()
                    ), 
                    'created_date_timestamp': receipts[0].created_date_timestamp,
                    'receipt_data': receipts[0].get_receipt_view_data()
                }
            ]
        }

        self.assertEqual(response.data, result)
   
    def test_view_be_viewed_by_an_employee_user(self):

        # Login an employee user
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)


        # Change user
        receipt = Receipt.objects.get(store=self.store1)
        receipt.user = self.manager_profile1.user
        receipt.save()

        response = self.client.get(
            reverse('api:pos_receipt_index', args=(self.store1.reg_no,))
        )
        self.assertEqual(response.status_code, 200)

        receipt = Receipt.objects.get(store=self.store1)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'customer_info': {
                        'name': self.customer.name, 
                        'email': self.customer.email,
                        'phone': self.customer.phone,
                        'tax_pin': self.customer.tax_pin,
                        'reg_no': self.customer.reg_no,
                    }, 
                    'name': receipt.__str__(), 
                    'receipt_number': receipt.receipt_number,
                    'refund_for_receipt_number': receipt.refund_for_receipt_number,
                    'discount_amount': f'{receipt.discount_amount}',  
                    'tax_amount': f'{receipt.tax_amount}', 
                    'subtotal_amount': f'{receipt.subtotal_amount}', 
                    'total_amount': f'{receipt.total_amount}', 
                    'given_amount': f'{receipt.given_amount}', 
                    'change_amount': f'{receipt.change_amount}', 
                    'transaction_type': receipt.transaction_type, 
                    'payment_completed': receipt.payment_completed, 
                    'receipt_closed': receipt.receipt_closed,  
                    'is_refund': receipt.is_refund, 
                    'item_count': receipt.item_count,
                    'local_reg_no': receipt.local_reg_no,
                    'reg_no': receipt.reg_no, 
                    'creation_date': receipt.get_created_date(
                        self.user1.get_user_timezone()
                    ), 
                    'created_date_timestamp': receipt.created_date_timestamp,
                    'receipt_data': receipt.get_receipt_view_data()
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_receipts(self):

        # First delete all receipts
        Receipt.objects.all().delete()

        response = self.client.get(reverse('api:pos_receipt_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_can_only_be_viewed_by_its_owner(self):

        # Login an employee user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:pos_receipt_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:pos_receipt_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)

'''
class PosReceiptCreateViewTestCase(APITestCase, InitialUserDataMixin):

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


        #Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')

        #Create a category
        self.category = create_new_category(self.top_profile1, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.top_profile1, 'chris')

        # Create product models
        self.create_products_and_modifier_options()


        # Get the time now (Don't turn it into local)
        now = timezone.now()
        
        # Make time aware
        self.midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)


        # Get payment methods
        self.cash_pay_method = self.top_profile1.get_store_payment_method(
            StorePaymentMethod.CASH_TYPE
        )
        self.mpesa_pay_method = self.top_profile1.get_store_payment_method(
            StorePaymentMethod.MPESA_TYPE
        )
        self.points_pay_method = self.top_profile1.get_store_payment_method(
            StorePaymentMethod.POINTS_TYPE
        )
        self.debt_pay_method = self.top_profile1.get_store_payment_method(
            StorePaymentMethod.DEBT_TYPE
        )

    def create_products_and_modifier_options(self):
        
        # Create a product
        self.product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """
        payload = {
            'receipt_number': '1000-1000',
            'customer_details': {
                'data': {
                    'name': self.customer.name, 
                    'customer_reg_no': self.customer.reg_no
                }
            },
            'discount_amount': 401.00,
            'tax_amount': 60.00,
            'subtotal_amount': 2000.00,
            'total_amount': 1599.00,
            'given_amount': 2500.00,
            'change_amount': 500.00,
            'transaction_type': Receipt.MONEY_TRANS,
            'payment_completed': True,
            'item_count': 17,
            'local_reg_no': 222,
            'created_date_timestamp': int(timezone.now().timestamp()),
            'payment_methods': [
                {
                    'amount': 2000.00,
                    'payment_method_reg_no': self.cash_pay_method.reg_no
                }
            ],
            'receipt_lines': [
                {
                    'tax_reg_no': self.tax.reg_no,
                    'parent_product_reg_no': 0,
                    'product_details': {
                        'data': {
                            'name': self.product1.name, 
                            'product_reg_no': self.product1.reg_no
                        }
                    },
                    'modifier_option_reg_nos': [],
                    'modifier_options_details': [],
                    'price': 1750,
                    'is_variant': False,
                    'sold_by_each': True,
                    'discount_amount': 250,
                    'units': 7
                },
                {
                    'tax_reg_no': self.tax.reg_no,
                    'parent_product_reg_no': 0,
                    'product_details': {
                        'data': {
                            'name': self.product2.name, 
                            'product_reg_no': self.product2.reg_no
                        }
                    },
                    'modifier_option_reg_nos': [],
                    'modifier_options_details': [],
                    'price': 2500,
                    'is_variant': False,
                    'sold_by_each': True,
                    'discount_amount': 0,
                    'units': 10
                },
            ],
            'shift_details': {
                'data': {
                    'starting_cash': 4500, 
                    'start_date_timestamp': int(self.midnight.timestamp()),
                    'local_reg_no': 222
                }
            },
            
        }

        return payload 
    
    def test_if_view_can_create_a_receipt(self):

        payload = self.get_premade_payload()

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        ) 

        self.assertEqual(response.status_code, 201)

        receipt = Receipt.objects.get(store=self.store1)

        results = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'customer_info': {
                        'name': self.customer.name, 
                        'email': self.customer.email,
                        'phone': self.customer.phone,
                        'tax_pin': self.customer.tax_pin,
                        'reg_no': self.customer.reg_no,
                    }, 
                    'name': receipt.__str__(), 
                    'receipt_number': receipt.receipt_number,
                    'refund_for_receipt_number': receipt.refund_for_receipt_number,
                    'discount_amount': f'{receipt.discount_amount}',  
                    'tax_amount': f'{receipt.tax_amount}', 
                    'subtotal_amount': f'{receipt.subtotal_amount}', 
                    'total_amount': f'{receipt.total_amount}', 
                    'given_amount': f'{receipt.given_amount}', 
                    'change_amount': f'{receipt.change_amount}', 
                    'transaction_type': receipt.transaction_type, 
                    'payment_completed': receipt.payment_completed, 
                    'receipt_closed': receipt.receipt_closed, 
                    'is_refund': receipt.is_refund, 
                    'item_count': receipt.item_count,
                    'local_reg_no': receipt.local_reg_no, 
                    'reg_no': receipt.reg_no, 
                    'id': receipt.id,
                    'creation_date': receipt.get_created_date(
                        self.user1.get_user_timezone()
                    ), 
                    'created_date_timestamp': receipt.created_date_timestamp,
                    'receipt_data': receipt.get_receipt_view_data()
                },
                
            ]
        }

        self.assertEqual(response.data, results)

        # Confirm receipt model creation
        self.assertEqual(Receipt.objects.all().count(), 1)
    
        product1 = Product.objects.get(name='Shampoo')
        product2 = Product.objects.get(name='Conditioner')

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(receipt.user, self.user1)
        self.assertEqual(receipt.store, self.store1)
        self.assertEqual(receipt.receipt_number, payload['receipt_number'])
        self.assertEqual(receipt.customer, self.customer)
        self.assertEqual(receipt.customer_info, {
                'name': self.customer.name, 
                'email': self.customer.email,
                'phone': self.customer.phone,
                'tax_pin': self.customer.tax_pin,
                'reg_no': self.customer.reg_no,
            }
        )
        self.assertEqual(receipt.total_amount, Decimal('1599.00'))
        self.assertEqual(receipt.subtotal_amount, 2000.00)
        self.assertEqual(receipt.discount_amount, Decimal('401.00'))
        self.assertEqual(receipt.tax_amount, Decimal('60.00'))
        self.assertEqual(receipt.given_amount, Decimal('2500.00'))
        self.assertEqual(receipt.change_amount, Decimal('500.00'))
        self.assertEqual(receipt.total_cost, Decimal('19000.00'))
        self.assertEqual(receipt.payment_completed, True)
        self.assertEqual(receipt.receipt_closed, True)
        self.assertEqual(receipt.is_refund, False)
        self.assertEqual(receipt.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt.item_count, 17)
        self.assertEqual(receipt.local_reg_no, 222)
        self.assertTrue(receipt.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receipt.created_date).strftime("%B, %d, %Y"), today)
        self.assertEqual(receipt.created_date_timestamp, int(receipt.created_date.timestamp()))

        # Confirm receipt payment model creation
        self.assertEqual(ReceiptPayment.objects.filter(receipt=receipt).count(), 1)

        receipt_payment = ReceiptPayment.objects.get(receipt=receipt)

        pay_method = self.top_profile1.get_store_payment_method_from_reg_no(
            payload['payment_methods'][0]['payment_method_reg_no']
        )

        self.assertEqual(receipt_payment.receipt, receipt)
        self.assertEqual(receipt_payment.payment_method, pay_method)
        self.assertEqual(
            receipt_payment.amount, 
            payload['payment_methods'][0]['amount']
        )

        # Confirm receipt line model creation
        self.assertEqual(ReceiptLine.objects.filter(receipt=receipt).count(), 2)
 
        receiptlines = ReceiptLine.objects.filter(receipt=receipt).order_by('id')

        # Receipt line 1
        receiptline1 = receiptlines[0]

        today = (timezone.now()).strftime("%B, %d, %Y")
        
        self.assertEqual(receiptline1.user, self.user1)
        self.assertEqual(receiptline1.receipt, receipt)
        self.assertEqual(receiptline1.store, self.store1)
        self.assertEqual(receiptline1.tax, self.tax)
        self.assertEqual(receiptline1.parent_product, None)
        self.assertEqual(receiptline1.product, product1)
        self.assertEqual(receiptline1.product_info, {
            'name': product1.name, 
            'reg_no': product1.reg_no,
            'loyverse_variant_id': 'None'
            }
        )
        self.assertEqual(receiptline1.modifier_options_info, [])
        self.assertEqual(receiptline1.customer, self.customer)
        self.assertEqual(receiptline1.price, 1750.00)
        self.assertEqual(receiptline1.total_amount, Decimal('12000.00'))
        self.assertEqual(receiptline1.gross_total_amount, Decimal('12250.00'))
        self.assertEqual(receiptline1.discount_amount, 250.00)
        self.assertEqual(receiptline1.is_variant, False)
        self.assertEqual(receiptline1.sold_by_each, True)
        self.assertEqual(receiptline1.units, 7)
        self.assertTrue(receiptline1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receiptline1.created_date).strftime("%B, %d, %Y"), today)


        # Receipt line 2
        receiptline2 = receiptlines[1]

        today = (timezone.now()).strftime("%B, %d, %Y")
        
        self.assertEqual(receiptline2.user, self.user1)
        self.assertEqual(receiptline2.receipt, receipt)
        self.assertEqual(receiptline2.store, self.store1)
        self.assertEqual(receiptline2.tax, self.tax)
        self.assertEqual(receiptline2.parent_product, None)
        self.assertEqual(receiptline2.product, product2)
        self.assertEqual(receiptline2.product_info, {
            'name': product2.name, 
            'reg_no': product2.reg_no,
            'loyverse_variant_id': 'None'
            }
        )
        self.assertEqual(receiptline2.modifier_options.all().count(), 0)
        self.assertEqual(receiptline2.modifier_options_info, [])
        self.assertEqual(receiptline2.customer, self.customer)
        self.assertEqual(receiptline2.price, 2500.00)
        self.assertEqual(receiptline2.total_amount, Decimal('25000.00'))
        self.assertEqual(receiptline2.gross_total_amount, Decimal('25000.00'))
        self.assertEqual(receiptline2.discount_amount, 0.00)
        self.assertEqual(receiptline2.is_variant, False)
        self.assertEqual(receiptline2.sold_by_each, True)
        self.assertEqual(receiptline2.units, 10)
        self.assertTrue(receiptline2.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receiptline2.created_date).strftime("%B, %d, %Y"), today)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=True
        ms.save()
              
        response = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )
            
        self.assertEqual(response.status_code, 401)

'''
    def test_if_view_can_create_a_receipt_for_an_employee_user(self):

        # Login a employee profile #
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 201)

        receipt = Receipt.objects.get(store=self.store1)

        self.assertEqual(
            response.data, 
            {
                'reg_no': receipt.reg_no,
                'transaction_type': receipt.transaction_type,
                'payment_completed': receipt.payment_completed,
                'local_reg_no': receipt.local_reg_no,
                'is_refund': receipt.is_refund,
                'id': receipt.id,
            }
        )

        # Confirm receipt model creation
        self.assertEqual(Receipt.objects.all().count(), 1)

        product1 = Product.objects.get(name='Shampoo')
        product2 = Product.objects.get(name='Conditioner')

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(receipt.user, self.manager_profile1.user)
        self.assertEqual(receipt.store, self.store1)
        self.assertEqual(receipt.receipt_number, payload['receipt_number'])
        self.assertEqual(receipt.customer, self.customer)
        self.assertEqual(receipt.customer_info, {
                'name': self.customer.name, 
                'email': self.customer.email,
                'phone': self.customer.phone,
                'tax_pin': self.customer.tax_pin,
                'reg_no': self.customer.reg_no,
            }
        )
        self.assertEqual(receipt.total_amount, Decimal('1599.00'))
        self.assertEqual(receipt.subtotal_amount, 2000.00)
        self.assertEqual(receipt.discount_amount, Decimal('401.00'))
        self.assertEqual(receipt.tax_amount, Decimal('60.00'))
        self.assertEqual(receipt.given_amount, Decimal('2500.00'))
        self.assertEqual(receipt.change_amount, Decimal('500.00'))
        self.assertEqual(receipt.total_cost, Decimal('19000.00'))
        self.assertEqual(receipt.payment_completed, True)
        self.assertEqual(receipt.receipt_closed, True)
        self.assertEqual(receipt.is_refund, False)
        self.assertEqual(receipt.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt.item_count, 17)
        self.assertEqual(receipt.local_reg_no, 222)
        self.assertTrue(receipt.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receipt.created_date).strftime("%B, %d, %Y"), today)
        self.assertEqual(receipt.created_date_timestamp, int(receipt.created_date.timestamp()))


        # Confirm receipt payment model creation
        self.assertEqual(ReceiptPayment.objects.filter(receipt=receipt).count(), 1)

        receipt_payment = ReceiptPayment.objects.get(receipt=receipt)

        pay_method = self.top_profile1.get_store_payment_method_from_reg_no(
            payload['payment_methods'][0]['payment_method_reg_no']
        )

        self.assertEqual(receipt_payment.receipt, receipt)
        self.assertEqual(receipt_payment.payment_method, pay_method)
        self.assertEqual(
            receipt_payment.amount, 
            payload['payment_methods'][0]['amount']
        )

        # Confirm receipt line model creation
        self.assertEqual(ReceiptLine.objects.filter(receipt=receipt).count(), 2)

        receiptlines = ReceiptLine.objects.filter(receipt=receipt).order_by('id')

        # Receipt line 1
        receiptline1 = receiptlines[0]

        today = (timezone.now()).strftime("%B, %d, %Y")
        
        self.assertEqual(receiptline1.user, self.manager_profile1.user)
        self.assertEqual(receiptline1.receipt, receipt)
        self.assertEqual(receiptline1.store, self.store1)
        self.assertEqual(receiptline1.parent_product, None)
        self.assertEqual(receiptline1.product, product1)
        self.assertEqual(receiptline1.product_info, {
            'name': product1.name, 
            'reg_no': product1.reg_no,
            'loyverse_variant_id': 'None'
            }
        )
        self.assertEqual(receiptline1.modifier_options.all().count(), 0)
        self.assertEqual(receiptline1.modifier_options_info, [])
        self.assertEqual(receiptline1.customer, self.customer)
        self.assertEqual(receiptline1.price, 1750.00)
        self.assertEqual(receiptline1.discount_amount, 250.00)
        self.assertEqual(receiptline1.is_variant, False)
        self.assertEqual(receiptline1.sold_by_each, True)
        self.assertEqual(receiptline1.units, 7)
        self.assertTrue(receiptline1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receiptline1.created_date).strftime("%B, %d, %Y"), today)


        # Receipt line 2
        receiptline2 = receiptlines[1]

        today = (timezone.now()).strftime("%B, %d, %Y")
        
        self.assertEqual(receiptline2.user, self.manager_profile1.user)
        self.assertEqual(receiptline2.receipt, receipt)
        self.assertEqual(receiptline2.store, self.store1)
        self.assertEqual(receiptline2.parent_product, None)
        self.assertEqual(receiptline2.product, product2)
        self.assertEqual(receiptline2.product_info, {
            'name': product2.name, 
            'reg_no': product2.reg_no,
            'loyverse_variant_id': 'None'
            }
        )
        self.assertEqual(receiptline2.modifier_options.all().count(), 0)
        self.assertEqual(receiptline2.modifier_options_info, [])
        self.assertEqual(receiptline2.customer, self.customer)
        self.assertEqual(receiptline2.price, 2500.00)
        self.assertEqual(receiptline2.discount_amount, 0.00)
        self.assertEqual(receiptline2.is_variant, False)
        self.assertEqual(receiptline2.sold_by_each, True)
        self.assertEqual(receiptline2.units, 10)
        self.assertTrue(receiptline2.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receiptline2.created_date).strftime("%B, %d, %Y"), today)
  
    def test_if_a_user_cannot_create_2_receipts_with_the_same_local_reg_no(self):

        payload = self.get_premade_payload()

        # Request 1
        response1 = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )

        self.assertEqual(response1.status_code, 201)


        # Request 1
        response2 = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )

        self.assertEqual(response2.status_code, 201)

        # Confirm receipt model creation
        self.assertEqual(Receipt.objects.all().count(), 1)

        receipt = Receipt.objects.get(store=self.store1)

        self.assertEqual(
            response1.data, 
            {
                'reg_no': receipt.reg_no,
                'transaction_type': receipt.transaction_type,
                'payment_completed': receipt.payment_completed,
                'local_reg_no': receipt.local_reg_no,
                'is_refund': receipt.is_refund,
                'id': receipt.id,
            }
        )

        self.assertEqual(
            response1.data, 
            {
                'reg_no': receipt.reg_no,
                'transaction_type': receipt.transaction_type,
                'payment_completed': receipt.payment_completed,
                'local_reg_no': receipt.local_reg_no,
                'is_refund': receipt.is_refund,
                'id': receipt.id,
            }
        )

    def test_if_view_cant_create_a_receipt_with_multiple_payments(self):

        payload = self.get_premade_payload()
        payload['payment_methods'] = [
            {
                'amount': 1200.00,
                'payment_method_reg_no': self.cash_pay_method.reg_no
            },
            {
                'amount': 800.00,
                'payment_method_reg_no': self.mpesa_pay_method.reg_no
            }
        ]

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 201)

        receipt = Receipt.objects.get(store=self.store1)

        self.assertEqual(
            response.data, 
            {
                'reg_no': receipt.reg_no,
                'transaction_type': receipt.transaction_type,
                'payment_completed': receipt.payment_completed,
                'local_reg_no': receipt.local_reg_no,
                'is_refund': receipt.is_refund,
                'id': receipt.id,
            }
        )

        # Confirm receipt model creation
        self.assertEqual(Receipt.objects.all().count(), 1)

        # Confirm receipt payment model creation
        self.assertEqual(ReceiptPayment.objects.filter(receipt=receipt).count(), 2)

        receipt_payments = ReceiptPayment.objects.filter(receipt=receipt).order_by('id')

        # Receipt payment 1
        receipt_payment1 = receipt_payments[0]

        pay_method = self.top_profile1.get_store_payment_method_from_reg_no(
            payload['payment_methods'][0]['payment_method_reg_no']
        )

        self.assertEqual(receipt_payment1.receipt, receipt)
        self.assertEqual(receipt_payment1.payment_method, pay_method)
        self.assertEqual(
            receipt_payment1.amount, 
            payload['payment_methods'][0]['amount']
        )

        # Receipt payment 2
        receipt_payment2 = receipt_payments[1]

        pay_method = self.top_profile1.get_store_payment_method_from_reg_no(
            payload['payment_methods'][1]['payment_method_reg_no']
        )

        self.assertEqual(receipt_payment2.receipt, receipt)
        self.assertEqual(receipt_payment2.payment_method, pay_method)
        self.assertEqual(
            receipt_payment2.amount, 
            payload['payment_methods'][1]['amount']
        )
    
    def test_if_view_cant_create_a_receipt_with_wrong_payment_method_with_a_wrong_reg_no(self):

        pay_method = self.top_profile2.get_store_payment_method(
            StorePaymentMethod.CASH_TYPE
        )

        wrong_payment_reg_nos = [
            10000, # Wrong reg no
            pay_method.reg_no # Payment for another user
        ]

        for wrong_reg_no in wrong_payment_reg_nos:

            payload = self.get_premade_payload()
            payload['payment_methods'] = [
                {
                    'amount': 2000.00,
                    'payment_method_reg_no': wrong_reg_no
                }
            ]

            # Count Number of Queries
            #with self.assertNumQueries(31):
            response = self.client.post(
                reverse('api:pos_receipt_index', 
                args=(self.store1.reg_no,)), 
                payload,
            )

            # Check if the request was successful #
            self.assertEqual(response.status_code, 400)
            
            result = {'non_field_errors': 'Choose a correct payment option'}
            self.assertEqual(response.data, result)

    def test_if_view_can_create_a_receipt_with_points(self):

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.top_profile1)
        loyalty.value = 6
        loyalty.save()

        # Give customer points
        customer = Customer.objects.get(name='Chris Evans')
        customer.points = 2000
        customer.save()

        # Confirm customer points 
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.points, 2000)

        payload = self.get_premade_payload()

        payload['transaction_type'] = Receipt.LOYALTY_TRANS
        payload['payment_methods'] = [
            {
                'amount': 2000.00,
                'payment_method_reg_no': self.points_pay_method.reg_no
            }
        ]
    
        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 201)

        receipt = Receipt.objects.get(store=self.store1)
        self.assertEqual(receipt.loyalty_points_amount, Decimal('2000.00'))
        self.assertEqual(receipt.transaction_type, Receipt.LOYALTY_TRANS)

        self.assertEqual(
            response.data, 
            {
                'reg_no': receipt.reg_no,
                'transaction_type': receipt.transaction_type,
                'payment_completed': receipt.payment_completed,
                'local_reg_no': receipt.local_reg_no,
                'is_refund': receipt.is_refund,
                'id': receipt.id,
            }
        )

        # Confirm receipt model creation
        self.assertEqual(Receipt.objects.all().count(), 1)

        # Confirm receipt line model creation
        self.assertEqual(ReceiptLine.objects.filter(receipt=receipt).count(), 2)

        # Confirm receipt payment model creation
        self.assertEqual(ReceiptPayment.objects.filter(receipt=receipt).count(), 1)

        receipt_payment = ReceiptPayment.objects.get(receipt=receipt)

        pay_method = self.top_profile1.get_store_payment_method_from_reg_no(
            payload['payment_methods'][0]['payment_method_reg_no']
        )

        self.assertEqual(receipt_payment.receipt, receipt)
        self.assertEqual(receipt_payment.payment_method, pay_method)
        self.assertEqual(receipt_payment.amount, Decimal('2000.00'))

        # Check if customer points was updated
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.points, 0)
    
    def test_if_view_can_create_a_receipt_with_points_plus_other_payments(self):

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.top_profile1)
        loyalty.value = 6
        loyalty.save()

        # Give customer points
        customer = Customer.objects.get(name='Chris Evans')
        customer.points = 2000
        customer.save()

        # Confirm customer points 
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.points, 2000)

        payload = self.get_premade_payload()

        payload['transaction_type'] = Receipt.MULTIPLE_TRANS
        payload['payment_methods'] = [
            {
                'amount': 1200.00,
                'payment_method_reg_no': self.cash_pay_method.reg_no
            },
            {
                'amount': 800.00,
                'payment_method_reg_no': self.points_pay_method.reg_no
            }
        ]
    
        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 201)

        receipt = Receipt.objects.get(store=self.store1)
        self.assertEqual(receipt.loyalty_points_amount, Decimal('800.00'))
        self.assertEqual(receipt.transaction_type, Receipt.MULTIPLE_TRANS)

        self.assertEqual(
            response.data, 
            {
                'reg_no': receipt.reg_no,
                'transaction_type': receipt.transaction_type,
                'payment_completed': receipt.payment_completed,
                'local_reg_no': receipt.local_reg_no,
                'is_refund': receipt.is_refund,
                'id': receipt.id,
            }
        )

        # Confirm receipt model creation
        self.assertEqual(Receipt.objects.all().count(), 1)

        # Confirm receipt line model creation
        self.assertEqual(ReceiptLine.objects.filter(receipt=receipt).count(), 2)
        

        # Confirm receipt payment model creation
        self.assertEqual(ReceiptPayment.objects.filter(receipt=receipt).count(), 2)

        receipt_payments = ReceiptPayment.objects.filter(receipt=receipt).order_by('id')

        # Receipt payment 1
        receipt_payment1 = receipt_payments[0]

        self.assertEqual(receipt_payment1.receipt, receipt)
        self.assertEqual(receipt_payment1.payment_method, self.cash_pay_method)
        self.assertEqual(receipt_payment1.amount, Decimal('1200.00'))

        # Receipt payment 2
        receipt_payment2 = receipt_payments[1]

        self.assertEqual(receipt_payment2.receipt, receipt)
        self.assertEqual(receipt_payment2.payment_method, self.points_pay_method)
        self.assertEqual(receipt_payment2.amount, Decimal('800.00'))

        
        # Check if customer points was updated
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.points, 1200)

    def test_if_view_cant_create_a_receipt_with_points_if_loyalty_setting_value_is_0(self):

        # Confirme loyalty setting value
        loyalty = LoyaltySetting.objects.get(profile=self.top_profile1)
        self.assertEqual(loyalty.value, Decimal('0.00'))

        payload = self.get_premade_payload()

        payload['transaction_type'] = Receipt.LOYALTY_TRANS
        payload['payment_methods'] = [
            {
                'amount': 2000.00,
                'payment_method_reg_no': self.points_pay_method.reg_no
            }
        ]
    
        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )

        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
        result = {'non_field_errors': 'Point payment is not enabled'}
        self.assertEqual(response.data, result)

        # Confirm receipt model was not creation
        self.assertEqual(Receipt.objects.all().count(), 0)
  
    def test_if_view_cant_create_a_receipt_with_points_if_customer_points_are_less(self):

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.top_profile1)
        loyalty.value = 6
        loyalty.save()

        # Give customer points
        customer = Customer.objects.get(name='Chris Evans')
        customer.points = 1999
        customer.save()

        # Confirm customer points 
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.points, 1999)

        payload = self.get_premade_payload()

        payload['transaction_type'] = Receipt.LOYALTY_TRANS
        payload['payment_methods'] = [
            {
                'amount': 2000.00,
                'payment_method_reg_no': self.points_pay_method.reg_no
            }
        ]
    
        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )

        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
        result = {'non_field_errors': 'Customer does not have enough points'}
        self.assertEqual(response.data, result)

        # Confirm receipt model was not creation
        self.assertEqual(Receipt.objects.all().count(), 0)
    
    def test_if_view_can_create_a_receipt_with_debt(self):

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        customer.credit_limit = 2000
        customer.save()

        # Confirm customer current debt 
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.current_debt, Decimal('0.00'))

        payload = self.get_premade_payload()

        payload['transaction_type'] = Receipt.DEBT_TRANS
        payload['payment_completed'] = False
        payload['payment_methods'] = [
            {
                'amount': 2000.00,
                'payment_method_reg_no': self.debt_pay_method.reg_no
            }
        ]

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 201)

        receipt = Receipt.objects.get(store=self.store1)
        self.assertEqual(receipt.transaction_type, Receipt.DEBT_TRANS)

        self.assertEqual(
            response.data, 
            {
                'reg_no': receipt.reg_no,
                'transaction_type': receipt.transaction_type,
                'payment_completed': receipt.payment_completed,
                'local_reg_no': receipt.local_reg_no,
                'is_refund': receipt.is_refund,
                'id': receipt.id,
            }
        )

        # Confirm receipt model creation
        self.assertEqual(Receipt.objects.all().count(), 1)

        # Confirm receipt line model creation
        self.assertEqual(ReceiptLine.objects.filter(receipt=receipt).count(), 2)

        # Check if customer current debt was updated
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.current_debt, Decimal('2000.00'))

    def test_if_view_cant_create_a_receipt_with_debt_if_customer_is_not_eligible(self):

        payload = self.get_premade_payload()

        payload['transaction_type'] = Receipt.DEBT_TRANS
        payload['payment_completed'] = False
        payload['payment_methods'] = [
            {
                'amount': 2000.00,
                'payment_method_reg_no': self.debt_pay_method.reg_no
            }
        ]

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )

        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
        result = {'non_field_errors': 'Customer is not qualified for debt'}
        self.assertEqual(response.data, result)

        # Confirm receipt model was not creation
        self.assertEqual(Receipt.objects.all().count(), 0)

    def test_if_view_can_create_a_receipt_with_an_empty_customer_details(self):

        payload = self.get_premade_payload()

        payload['customer_details'] = {}

        response = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )


        self.assertEqual(response.status_code, 201)

        receipt = Receipt.objects.get(store=self.store1)

        self.assertEqual(
            response.data, 
            {
                'reg_no': receipt.reg_no,
                'transaction_type': receipt.transaction_type,
                'payment_completed': receipt.payment_completed,
                'local_reg_no': receipt.local_reg_no,
                'is_refund': receipt.is_refund,
                'id': receipt.id,
            }
        )

        # Confirm receipt model creation
        self.assertEqual(Receipt.objects.all().count(), 1)

        self.assertEqual(receipt.customer, None)
        self.assertEqual(receipt.customer_info, {})

        # Confirm receipt line model creation
        self.assertEqual(ReceiptLine.objects.filter(receipt=receipt).count(), 2)
    
    def test_if_view_can_create_a_receipt_with_a_customer_who_was_deleted(self):

        payload = self.get_premade_payload()

        # Create a customer user
        customer_for_another_user = create_new_customer(self.top_profile2, 'alex')

        wrong_reg_nos = [
            33463476347374, # Wrong reg no
            customer_for_another_user.reg_no, # Customer for another user
            11111111111111111111111111111111111111 # Long reg no
        ]

        for wrong_reg_no in wrong_reg_nos:

            # Delete previous models
            Receipt.objects.all().delete()
            ReceiptLine.objects.all().delete()

            payload['customer_details'] = {
                'data': {
                    'name': self.customer.name, 
                    'customer_reg_no': wrong_reg_no
                }
            }

            response = self.client.post(
                reverse('api:pos_receipt_index', 
                args=(self.store1.reg_no,)), 
                payload,
            )

            self.assertEqual(response.status_code, 201)

            receipt = Receipt.objects.get(store=self.store1)

            self.assertEqual(
                response.data, 
                {
                    'reg_no': receipt.reg_no,
                    'transaction_type': receipt.transaction_type,
                    'payment_completed': receipt.payment_completed,
                    'local_reg_no': receipt.local_reg_no,
                    'is_refund': receipt.is_refund,
                    'id': receipt.id,
                }
            )

            # Confirm receipt model creation
            self.assertEqual(Receipt.objects.all().count(), 1)

            self.assertEqual(receipt.customer, None)
            self.assertEqual(
                receipt.customer_info, 
                {
                    'name': self.customer.name, 
                    'reg_no': wrong_reg_no,
                }
            )

            # Confirm receipt line model creation
            self.assertEqual(ReceiptLine.objects.filter(receipt=receipt).count(), 2)

    def test_if_view_can_handle_a_receipt_line_with_wrong_parent_product_reg_no(self):

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

        product1 = Product.objects.get(name='Shampoo')

        for wrong_reg_no in wrong_reg_nos:

            # Delete previous models
            Receipt.objects.all().delete()
            ReceiptLine.objects.all().delete()


            payload['receipt_lines'][0]['parent_product_reg_no'] = wrong_reg_no
            payload['receipt_lines'][0]['product_details'] = {
                'data': {
                    'name': f'{product1.name}', 
                    'product_reg_no': product1.reg_no
                }
            }
            payload['receipt_lines'][1]['is_variant'] = True

            response = self.client.post(
                reverse('api:pos_receipt_index', 
                args=(self.store1.reg_no,)), 
                payload,
            )

            self.assertEqual(response.status_code, 201)

            receipt = Receipt.objects.get(store=self.store1)

            self.assertEqual(
            response.data, 
                {
                    'reg_no': receipt.reg_no,
                    'transaction_type': receipt.transaction_type,
                    'payment_completed': receipt.payment_completed,
                    'local_reg_no': receipt.local_reg_no,
                    'is_refund': receipt.is_refund,
                    'id': receipt.id,
                }
            )

            # Confirm receipt model creation
            self.assertEqual(Receipt.objects.all().count(), 1)

            # Confirm receipt line model creation
            self.assertEqual(ReceiptLine.objects.filter(receipt=receipt).count(), 2)

            receiptlines = ReceiptLine.objects.filter(receipt=receipt).order_by('id')

            receiptline1 = receiptlines[0]

            self.assertEqual(receiptline1.parent_product, None)
            self.assertEqual(receiptline1.product, product1)
            self.assertEqual(receiptline1.product_info, {
                'name': f'{product1.name}', 
                'reg_no': product1.reg_no,
                'loyverse_variant_id': 'None'
                }
            )
    
    def test_if_view_can_create_a_receipt_with_an_empty_product_details(self):

        payload = self.get_premade_payload()

        payload['receipt_lines'][0]['product_details'] = {}

        response = self.client.post(
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )

        self.assertEqual(response.status_code, 201)

        receipt = Receipt.objects.get(store=self.store1)

        # self.assertEqual(response.data, {'reg_no': receipt.reg_no })

        # Confirm receipt model creation
        self.assertEqual(Receipt.objects.all().count(), 1)


        # Confirm receipt line model creation
        self.assertEqual(ReceiptLine.objects.filter(receipt=receipt).count(), 2)

        receiptlines = ReceiptLine.objects.filter(receipt=receipt).order_by('id')

        receiptline1 = receiptlines[0]

        self.assertEqual(receiptline1.product, None)
        self.assertEqual(
            receiptline1.product_info, 
            {'name': 'Not found', 'reg_no': 0} 
        )

    def test_if_view_can_handle_a_receipt_line_with_wrong_product_reg_no(self):

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

        product1 = Product.objects.get(name='Shampoo')

        for wrong_reg_no in wrong_reg_nos:

            # Delete previous models
            Receipt.objects.all().delete()
            ReceiptLine.objects.all().delete()

            payload['receipt_lines'][0]['product_details'] = {
                'data': {
                    'name': f'{product1.name}', 
                    'product_reg_no': wrong_reg_no
                }
            }

            response = self.client.post(
                reverse('api:pos_receipt_index', 
                args=(self.store1.reg_no,)), 
                payload,
            )

            self.assertEqual(response.status_code, 201)

            receipt = Receipt.objects.get(store=self.store1)

            self.assertEqual(
            response.data, 
                {
                    'reg_no': receipt.reg_no,
                    'transaction_type': receipt.transaction_type,
                    'payment_completed': receipt.payment_completed,
                    'local_reg_no': receipt.local_reg_no,
                    'is_refund': receipt.is_refund,
                    'id': receipt.id,
                }
            )

            # Confirm receipt model creation
            self.assertEqual(Receipt.objects.all().count(), 1)

            # Confirm receipt line model creation
            self.assertEqual(ReceiptLine.objects.filter(receipt=receipt).count(), 2)

            receiptlines = ReceiptLine.objects.filter(receipt=receipt).order_by('id')

            receiptline1 = receiptlines[0]

            self.assertEqual(receiptline1.product, None)
            self.assertEqual(
                receiptline1.product_info, 
                {
                    'name': f'{product1.name}', 
                    'reg_no': wrong_reg_no
                }
            )

    def test_if_view_url_can_throttle_post_requests(self):

        payload = self.get_premade_payload()

        throttle_rate = int(settings.THROTTLE_RATES['api_receipt_rate'].split("/")[0])
    
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:pos_receipt_index', 
                args=(self.store1.reg_no,)), 
                payload,
            )
            self.assertEqual(response.status_code, 201)


        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional 
        # request if the previous request was not throttled 
        for i in range(throttle_rate): # pylint: disable=unused-variable

            response = self.client.post(
                reverse('api:pos_receipt_index', 
                args=(self.store1.reg_no,)), 
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
            reverse('api:pos_receipt_index', 
            args=(self.store1.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 401)


class PosReceiptCompletePaymentViewTestCase(APITestCase, InitialUserDataMixin):

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

        self.create_receipt()

        # Get payment methods
        self.cash_pay_method = self.top_profile1.get_store_payment_method(
            StorePaymentMethod.CASH_TYPE
        )
        self.mpesa_pay_method = self.top_profile1.get_store_payment_method(
            StorePaymentMethod.MPESA_TYPE
        )
        self.points_pay_method = self.top_profile1.get_store_payment_method(
            StorePaymentMethod.POINTS_TYPE
        )
        self.debt_pay_method = self.top_profile1.get_store_payment_method(
            StorePaymentMethod.DEBT_TYPE
        )

    def create_receipt(self):

        #Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')

        #Create a category
        self.category = create_new_category(self.top_profile1, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.top_profile1, 'chris')

        # Create a product
        product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        # Create receipt1
        self.receipt = Receipt.objects.create(
            user=self.top_profile1.user,
            store=self.store1,
            customer=self.customer,
            customer_info={
                'name': self.customer.name, 
                'reg_no': self.customer.reg_no
            },
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=0.00,
            change_amount=0.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.DEBT_TRANS,
            payment_completed=False
        )

        pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.DEBT_TYPE
        )
        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=pay_method,
            amount=2000
        )

        # Create receipt line1
        self.receiptline1 =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=product1,
            product_info={'name': product1.name},
            price=1750,
            units=7
        )
    
        # Create receipt line2
        self.receiptline2 =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=product2,
            product_info={'name': product2.name},
            price=2500,
            units=10
        )

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """

        payload = {
            'given_amount': 2500.00,
            'change_amount': 500,
            'transaction_type': Receipt.MONEY_TRANS,
            'payment_completed': True,

            'payment_methods': [
                {
                    'amount': 2000.00,
                    'payment_method_reg_no': self.cash_pay_method.reg_no
                }
            ],
        }

        return payload

    def test_if_view_can_edit_a_receipt(self):

        # First confirm receipt values before edit
        receipt = Receipt.objects.get(store=self.store1)

        payload = self.get_premade_payload()

        # Count Number of Queries
        with self.assertNumQueries(27):
            response = self.client.put(
                reverse('api:pos_receipt_complete_payment', 
                args=(self.store1.reg_no, receipt.reg_no)), 
                payload,
            )

        self.assertEqual(response.status_code, 200)

        """
        Ensure a product has the right fields after it has been edited
        """
        receipt = Receipt.objects.get(store=self.store1)
        
        self.assertEqual(receipt.given_amount, payload['given_amount'])
        self.assertEqual(receipt.change_amount, payload['change_amount'])
        self.assertEqual(receipt.transaction_type, payload['transaction_type'])
        self.assertEqual(receipt.payment_completed, payload['payment_completed'])

        # Confirm receipt payment model creation
        self.assertEqual(ReceiptPayment.objects.filter(receipt=receipt).count(), 1)

        receipt_payment = ReceiptPayment.objects.get(receipt=receipt)

        pay_method = self.top_profile1.get_store_payment_method_from_reg_no(
            payload['payment_methods'][0]['payment_method_reg_no']
        )

        self.assertEqual(receipt_payment.receipt, receipt)
        self.assertEqual(receipt_payment.payment_method, pay_method)
        
        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=True
        ms.save()

        response = self.client.put(
            reverse('api:pos_receipt_complete_payment', 
            args=(self.store1.reg_no, receipt.reg_no)), 
            payload,
        )
            
        self.assertEqual(response.status_code, 401)

    def test_if_view_can_edit_a_receipt_for_employee_user(self):

        # Login a employee profile #
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Change receipt user first
        receipt = Receipt.objects.get(store=self.store1)
        receipt.user = self.manager_profile1.user
        receipt.save() 

        payload = self.get_premade_payload()

        # Count Number of Queries
        #with self.assertNumQueries(34):
        response = self.client.put(
            reverse('api:pos_receipt_complete_payment', 
            args=(self.store1.reg_no, receipt.reg_no)), 
            payload,
        )

        self.assertEqual(response.status_code, 200)

        """
        Ensure a product has the right fields after it has been edited
        """
        receipt = Receipt.objects.get(store=self.store1)
        
        self.assertEqual(receipt.given_amount, payload['given_amount'])
        self.assertEqual(receipt.change_amount, payload['change_amount'])
        self.assertEqual(receipt.transaction_type, payload['transaction_type'])
        self.assertEqual(receipt.payment_completed, payload['payment_completed'])

        # Confirm receipt payment model creation
        self.assertEqual(ReceiptPayment.objects.filter(receipt=receipt).count(), 1)

        receipt_payment = ReceiptPayment.objects.get(receipt=receipt)

        pay_method = self.top_profile1.get_store_payment_method_from_reg_no(
            payload['payment_methods'][0]['payment_method_reg_no']
        )

        self.assertEqual(receipt_payment.receipt, receipt)
        self.assertEqual(receipt_payment.payment_method, pay_method)
    
    def test_if_view_cant_create_a_receipt_with_multiple_payments(self):

        receipt = Receipt.objects.get(store=self.store1)

        payload = self.get_premade_payload()
        payload['payment_methods'] = [
            {
                'amount': 1200.00,
                'payment_method_reg_no': self.cash_pay_method.reg_no
            },
            {
                'amount': 800.00,
                'payment_method_reg_no': self.mpesa_pay_method.reg_no
            }
        ]

        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.put(
            reverse('api:pos_receipt_complete_payment', 
            args=(self.store1.reg_no, receipt.reg_no)), 
            payload,
        )

        self.assertEqual(response.status_code, 200)

        receipt = Receipt.objects.get(store=self.store1)

        # Confirm receipt model creation
        self.assertEqual(Receipt.objects.all().count(), 1)

        # Confirm receipt payment model creation
        self.assertEqual(ReceiptPayment.objects.filter(receipt=receipt).count(), 2)

        receipt_payments = ReceiptPayment.objects.filter(receipt=receipt).order_by('id')

        # Receipt payment 1
        receipt_payment1 = receipt_payments[0]

        pay_method = self.top_profile1.get_store_payment_method_from_reg_no(
            payload['payment_methods'][0]['payment_method_reg_no']
        )

        self.assertEqual(receipt_payment1.receipt, receipt)
        self.assertEqual(receipt_payment1.payment_method, pay_method)
        self.assertEqual(
            receipt_payment1.amount, 
            payload['payment_methods'][0]['amount']
        )

        # Receipt payment 2
        receipt_payment2 = receipt_payments[1]

        pay_method = self.top_profile1.get_store_payment_method_from_reg_no(
            payload['payment_methods'][1]['payment_method_reg_no']
        )

        self.assertEqual(receipt_payment2.receipt, receipt)
        self.assertEqual(receipt_payment2.payment_method, pay_method)
        self.assertEqual(
            receipt_payment2.amount, 
            payload['payment_methods'][1]['amount']
        )

    def test_if_view_can_create_a_receipt_with_points(self):

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.top_profile1)
        loyalty.value = 6
        loyalty.save()

        # Give customer points
        customer = Customer.objects.get(name='Chris Evans')
        customer.points = 2000
        customer.save()

        # Confirm customer points 
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.points, 2000)

        receipt = Receipt.objects.get(store=self.store1)

        payload = self.get_premade_payload()

        payload['transaction_type'] = Receipt.LOYALTY_TRANS
        payload['payment_methods'] = [
            {
                'amount': 2000.00,
                'payment_method_reg_no': self.points_pay_method.reg_no
            }
        ]
    
        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.put(
            reverse('api:pos_receipt_complete_payment', 
            args=(self.store1.reg_no, receipt.reg_no)), 
            payload,
        )

        self.assertEqual(response.status_code, 200)

        """
        Ensure a product has the right fields after it has been edited
        """
        receipt = Receipt.objects.get(store=self.store1)
        
        self.assertEqual(receipt.given_amount, payload['given_amount'])
        self.assertEqual(receipt.change_amount, payload['change_amount'])
        self.assertEqual(receipt.transaction_type, payload['transaction_type'])
        self.assertEqual(receipt.payment_completed, payload['payment_completed'])

        # Confirm receipt payment model creation
        self.assertEqual(ReceiptPayment.objects.filter(receipt=receipt).count(), 1)

        receipt_payment = ReceiptPayment.objects.get(receipt=receipt)

        pay_method = self.top_profile1.get_store_payment_method_from_reg_no(
            payload['payment_methods'][0]['payment_method_reg_no']
        )

        self.assertEqual(receipt_payment.receipt, receipt)
        self.assertEqual(receipt_payment.payment_method, pay_method)

        # Check if customer points was updated
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.points, 0)

    def test_if_view_can_edit_a_receipt_with_points_plus_other_payments(self):

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.top_profile1)
        loyalty.value = 6
        loyalty.save()

        # Give customer points
        customer = Customer.objects.get(name='Chris Evans')
        customer.points = 2000
        customer.save()

        # Confirm customer points 
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.points, 2000)

        receipt = Receipt.objects.get(store=self.store1)

        payload = self.get_premade_payload()

        payload['transaction_type'] = Receipt.MULTIPLE_TRANS
        payload['payment_methods'] = [
            {
                'amount': 1200.00,
                'payment_method_reg_no': self.cash_pay_method.reg_no
            },
            {
                'amount': 800.00,
                'payment_method_reg_no': self.points_pay_method.reg_no
            }
        ]
    
        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.put(
            reverse('api:pos_receipt_complete_payment', 
            args=(self.store1.reg_no, receipt.reg_no)), 
            payload,
        )

        self.assertEqual(response.status_code, 200)

        receipt = Receipt.objects.get(store=self.store1)
        self.assertEqual(receipt.loyalty_points_amount, Decimal('800.00'))
        self.assertEqual(receipt.transaction_type, Receipt.MULTIPLE_TRANS)

        # Confirm receipt model creation
        self.assertEqual(Receipt.objects.all().count(), 1)

        # Confirm receipt line model creation
        self.assertEqual(ReceiptLine.objects.filter(receipt=receipt).count(), 2)
        

        # Confirm receipt payment model creation
        self.assertEqual(ReceiptPayment.objects.filter(receipt=receipt).count(), 2)

        receipt_payments = ReceiptPayment.objects.filter(receipt=receipt).order_by('id')

        # Receipt payment 1
        receipt_payment1 = receipt_payments[0]

        self.assertEqual(receipt_payment1.receipt, receipt)
        self.assertEqual(receipt_payment1.payment_method, self.cash_pay_method)
        self.assertEqual(receipt_payment1.amount, Decimal('1200.00'))

        # Receipt payment 2
        receipt_payment2 = receipt_payments[1]

        self.assertEqual(receipt_payment2.receipt, receipt)
        self.assertEqual(receipt_payment2.payment_method, self.points_pay_method)
        self.assertEqual(receipt_payment2.amount, Decimal('800.00'))

        
        # Check if customer points was updated
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.points, 1200)

    def test_if_view_cant_edit_a_receipt_with_points_if_loyalty_setting_value_is_0(self):

        # Confirme loyalty setting value
        loyalty = LoyaltySetting.objects.get(profile=self.top_profile1)
        self.assertEqual(loyalty.value, Decimal('0.00'))

        receipt = Receipt.objects.get(store=self.store1)

        payload = self.get_premade_payload()

        payload['transaction_type'] = Receipt.LOYALTY_TRANS
        payload['payment_methods'] = [
            {
                'amount': 2000.00,
                'payment_method_reg_no': self.points_pay_method.reg_no
            }
        ]
        
        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.put(
            reverse('api:pos_receipt_complete_payment', 
            args=(self.store1.reg_no, receipt.reg_no)), 
            payload,
        )

        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
        result = {'non_field_errors': 'Point payment is not enabled'}
        self.assertEqual(response.data, result)

    def test_if_view_cant_edit_a_receipt_with_points_if_customer_points_are_less(self):

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.top_profile1)
        loyalty.value = 6
        loyalty.save()

        # Give customer points
        customer = Customer.objects.get(name='Chris Evans')
        customer.points = 1999
        customer.save()

        # Confirm customer points 
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.points, 1999)

        receipt = Receipt.objects.get(store=self.store1)

        payload = self.get_premade_payload()

        payload['transaction_type'] = Receipt.LOYALTY_TRANS
        payload['payment_methods'] = [
            {
                'amount': 2000.00,
                'payment_method_reg_no': self.points_pay_method.reg_no
            }
        ]
    
        # Count Number of Queries
        #with self.assertNumQueries(31):
        response = self.client.put(
            reverse('api:pos_receipt_complete_payment', 
            args=(self.store1.reg_no, receipt.reg_no)), 
            payload,
        )

        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
        result = {'non_field_errors': 'Customer does not have enough points'}
        self.assertEqual(response.data, result)

    def test_if_view_cant_edit_a_receipt_with_debt_payment(self):
    
        # First confirm receipt values before edit
        receipt = Receipt.objects.get(store=self.store1)

        payload = self.get_premade_payload()

        payload['transaction_type'] = Receipt.DEBT_TRANS
        payload['payment_methods'] = [
            {
                'amount': 2000.00,
                'payment_method_reg_no': self.debt_pay_method.reg_no
            }
        ]

        # Count Number of Queries
        #with self.assertNumQueries(34):
        response = self.client.put(
            reverse('api:pos_receipt_complete_payment', 
            args=(self.store1.reg_no, receipt.reg_no)), 
            payload,
        )

        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
        result = {'non_field_errors': 'Choose another payment option'}
        self.assertEqual(response.data, result)

    def test_if_view_cant_edit_a_receipt_with_wrong_payment_method_with_a_wrong_reg_no(self):

        # First confirm receipt values before edit
        receipt = Receipt.objects.get(store=self.store1)

        payload = self.get_premade_payload()

        pay_method = self.top_profile2.get_store_payment_method(
            StorePaymentMethod.CASH_TYPE
        )

        wrong_payment_reg_nos = [
            10000, # Wrong reg no
            pay_method.reg_no # Payment for another user
        ]

        for wrong_reg_no in wrong_payment_reg_nos:

            payload['transaction_type'] = Receipt.MONEY_TRANS
            payload['payment_methods'] = [
                {
                    'amount': 2000.00,
                    'payment_method_reg_no': wrong_reg_no
                }
            ]

            response = self.client.put(
                reverse('api:pos_receipt_complete_payment', 
                args=(self.store1.reg_no, receipt.reg_no)), 
                payload,
            )

            # Check if the request was successful #
            self.assertEqual(response.status_code, 400)
            
            result = {'non_field_errors': 'Choose a correct payment option'}
            self.assertEqual(response.data, result)

    def test_if_view_can_handle_a_wrong_store_reg_no(self):

        payload = self.get_premade_payload()

        wrong_reg_nos = [
            7878787, # Wrong reg no,
            self.store2.reg_no, # Store that does not have access to product
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        for wrong_reg_no in wrong_reg_nos:
            response = self.client.put(
                reverse('api:pos_receipt_complete_payment', 
                args=(wrong_reg_no, self.receipt.reg_no)), 
                payload
            )
            
            self.assertEqual(response.status_code, 404)

    def test_if_view_can_handle_a_wrong_receipt_reg_no(self):

        payload = self.get_premade_payload()

        wrong_reg_nos = [
            7878787, # Wrong reg no,
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        for wrong_reg_no in wrong_reg_nos:
            response = self.client.put(
                reverse('api:pos_receipt_complete_payment', 
                args=(self.store1.reg_no, wrong_reg_no)), 
                payload
            )

            self.assertEqual(response.status_code, 404)

    def test_if_view_can_only_be_edited_by_its_owner(self):

        # Login a employee profile #
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # First confirm receipt values before edit
        receipt = Receipt.objects.get(store=self.store1)
        
        payload = self.get_premade_payload()

        # Count Number of Queries
        #with self.assertNumQueries(34):
        response = self.client.put(
            reverse('api:pos_receipt_complete_payment', 
            args=(self.store1.reg_no, receipt.reg_no)), 
            payload,
        )

        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        receipt = Receipt.objects.get(store=self.store1)

        response = self.client.put(
            reverse('api:pos_receipt_complete_payment', 
            args=(self.store1.reg_no, receipt.reg_no)),
            payload,
        )
        self.assertEqual(response.status_code, 401)


class PosReceiptRefundPerLineViewTestCase(APITestCase, InitialUserDataMixin):

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

        #Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')

        #Create a discount
        self.discount = create_new_discount(self.top_profile1, self.store1, 'Happy hour')

        #Create a category
        self.category = create_new_category(self.top_profile1, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.top_profile1, 'chris')

        self.create_sale_data(user=self.user1)


        self.cash_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.CASH_TYPE
        )

        self.mpesa_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.MPESA_TYPE
        )

        self.points_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.POINTS_TYPE
        )

        self.debt_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.DEBT_TYPE
        )

    def create_sale_data(
        self, 
        user, 
        receipt_number='100-1000',
        payment_type=StorePaymentMethod.CASH_TYPE,
        transaction_type=Receipt.MONEY_TRANS,
        payment_completed=True):


        customer = Customer.objects.get(name='Chris Evans')

        loyalty_points_amount = 0

        if payment_type == StorePaymentMethod.POINTS_TYPE:
            loyalty_points_amount = 2000


        # Creates products
        self.product = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
        self.product.stores.add(self.store1)

        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
        self.product2.stores.add(self.store1)

        # Create receipt1
        self.receipt = Receipt.objects.create(
            user=user,
            store=self.store1,
            customer=customer,
            customer_info={
                'name': customer.name, 
                'reg_no': customer.reg_no
            },
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            loyalty_points_amount=loyalty_points_amount,
            transaction_type=transaction_type,
            payment_completed=payment_completed,
            local_reg_no=222,
            receipt_number=receipt_number,
            receipt_number_for_testing=receipt_number,
            created_date_timestamp = 1634926712,
            changed_stock=False
        )
    
        # Create receipt line1
        self.receiptline1 =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=self.product,
            product_info={'name': self.product.name, 'reg_no': self.product.reg_no},
            price=1750,
            units=7
        )
    
        # Create receipt line2
        self.receiptline2 =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=self.product2,
            product_info={'name': self.product2.name, 'reg_no': self.product2.reg_no},
            price=2500,
            units=10
        )

        # Update all receipt lines
        self.update_all_receipt_lines([receipt_number])

        pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=payment_type
        )

        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=pay_method,
            amount=2500
        )

        # Create stock levels
        stock_level = StockLevel.objects.get(product=self.product, store=self.store1)
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(product=self.product2, store=self.store1)
        stock_level.units = 50
        stock_level.save()

    def update_all_receipt_lines(self, receipt_numbers):
        """
        Updates all receipt lines for receipts
        """
        # Force receipts lines to update
        Receipt.objects.filter(
            receipt_number__in=receipt_numbers
        ).update(   
            changed_stock=False
        )
        receipt_change_stock_tasks(ignore_dates=True)
    

    def get_premade_payload(self):

        # Perform refund
        refund_discount_amount=250
        refund_tax_amount=120
        refund_subtotal_amount=1500
        refund_total_amount=1300
        refund_item_count=6
        refund_local_reg_no=1234
        refund_created_date_timestamp=1634926713

        return {
            'receipt_number': '100-1001',
            'discount_amount': refund_discount_amount,
            'tax_amount': refund_tax_amount,
            'subtotal_amount': refund_subtotal_amount,
            'total_amount': refund_total_amount,
            'item_count': refund_item_count,
            'local_reg_no': refund_local_reg_no,
            'created_date_timestamp': refund_created_date_timestamp,
            'receipt_lines': [
                {
                    'price': 1250,
                    'cost': 1000,
                    'total_amount': 6250,
                    'gross_total_amount': 6250,
                    'discount_amount': 0,
                    'refund_units': 5,
                    'line_reg_no': self.receiptline1.reg_no,
                },
                {
                    'price': 1500,
                    'cost': 1000,
                    'discount_amount': 0,
                    'total_amount': 9000,
                    'gross_total_amount': 9000,
                    'refund_units': 6,
                    'line_reg_no': self.receiptline2.reg_no,
                }
            ]
        }
    
    def test_if_a_receipt_can_be_refunded(self):

        payload = self.get_premade_payload()

        # Perform refund
        refund_discount_amount=250
        refund_tax_amount=120
        refund_subtotal_amount=1500
        refund_total_amount=1300
        refund_item_count=6
        refund_local_reg_no=1234
        refund_created_date_timestamp=1634926713

        receipt = Receipt.objects.get(store=self.store1)

        # Count Number of Queries
        #with self.assertNumQueries(34):
        response = self.client.put(
            reverse('api:pos_receipt_refund', 
            args=(self.store1.reg_no, receipt.reg_no)), 
            payload,
        )
        self.assertEqual(response.status_code, 200)

        refunded_receipt = Receipt.objects.get(receipt_number='100-1001')


        results = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'customer_info': {
                        'name': self.customer.name, 
                        'email': self.customer.email,
                        'phone': self.customer.phone,
                        'tax_pin': self.customer.tax_pin,
                        'reg_no': self.customer.reg_no,
                    }, 
                    'name': refunded_receipt.__str__(), 
                    'receipt_number': refunded_receipt.receipt_number,
                    'refund_for_receipt_number': refunded_receipt.refund_for_receipt_number,
                    'discount_amount': f'{refunded_receipt.discount_amount}',  
                    'tax_amount': f'{refunded_receipt.tax_amount}', 
                    'subtotal_amount': f'{refunded_receipt.subtotal_amount}', 
                    'total_amount': f'{refunded_receipt.total_amount}', 
                    'given_amount': f'{refunded_receipt.given_amount}', 
                    'change_amount': f'{refunded_receipt.change_amount}', 
                    'transaction_type': refunded_receipt.transaction_type, 
                    'payment_completed': refunded_receipt.payment_completed, 
                    'receipt_closed': refunded_receipt.receipt_closed, 
                    'is_refund': refunded_receipt.is_refund, 
                    'item_count': refunded_receipt.item_count,
                    'local_reg_no': refunded_receipt.local_reg_no, 
                    'reg_no': refunded_receipt.reg_no, 
                    'id': refunded_receipt.id,
                    'creation_date': refunded_receipt.get_created_date(
                        self.user1.get_user_timezone()
                    ), 
                    'created_date_timestamp': refunded_receipt.created_date_timestamp,
                    'receipt_data': refunded_receipt.get_receipt_view_data()
                },
                {
                    'customer_info': {
                        'name': self.customer.name, 
                        'email': self.customer.email,
                        'phone': self.customer.phone,
                        'tax_pin': self.customer.tax_pin,
                        'reg_no': self.customer.reg_no,
                    }, 
                    'name': receipt.__str__(), 
                    'receipt_number': receipt.receipt_number,
                    'refund_for_receipt_number': receipt.refund_for_receipt_number,
                    'discount_amount': f'{receipt.discount_amount}',  
                    'tax_amount': f'{receipt.tax_amount}', 
                    'subtotal_amount': f'{receipt.subtotal_amount}', 
                    'total_amount': f'{receipt.total_amount}', 
                    'given_amount': f'{receipt.given_amount}', 
                    'change_amount': f'{receipt.change_amount}', 
                    'transaction_type': receipt.transaction_type, 
                    'payment_completed': receipt.payment_completed, 
                    'receipt_closed': receipt.receipt_closed, 
                    'is_refund': receipt.is_refund, 
                    'item_count': receipt.item_count,
                    'local_reg_no': receipt.local_reg_no, 
                    'reg_no': receipt.reg_no, 
                    'id': receipt.id,
                    'creation_date': receipt.get_created_date(
                        self.user1.get_user_timezone()
                    ), 
                    'created_date_timestamp': receipt.created_date_timestamp,
                    'receipt_data': receipt.get_receipt_view_data()
                },
                
            ]
        }

        self.assertEqual(response.data, results)

        # Force refund receipts lines to update
        self.update_all_receipt_lines(['100-1001'])

        receipts = Receipt.objects.filter(store=self.store1)

        ###### Check refunded receipt
        receipt1 = receipts[0]

        self.assertEqual(receipt1.user, self.user1)
        self.assertEqual(receipt1.store, self.store1)
        self.assertEqual(receipt1.customer, self.customer)
        self.assertEqual(receipt1.customer_info, {
                'name': self.customer.name, 
                'email': self.customer.email,
                'phone': self.customer.phone,
                'tax_pin': self.customer.tax_pin,
                'reg_no': self.customer.reg_no
            }
        )
        self.assertEqual(receipt1.subtotal_amount, 2000.00)
        self.assertEqual(receipt1.total_amount, Decimal('1599.00'))
        self.assertEqual(receipt1.discount_amount, Decimal('401.00'))
        self.assertEqual(receipt1.tax_amount, Decimal('60.00'))
        self.assertEqual(receipt1.given_amount, Decimal('2500.00'))
        self.assertEqual(receipt1.change_amount, Decimal('500.00'))
        self.assertEqual(receipt1.loyalty_points_amount, Decimal('0.00'))
        self.assertEqual(receipt1.total_cost, Decimal('0.00'))
        self.assertEqual(receipt1.payment_completed, True)
        self.assertEqual(receipt1.customer_points_update_completed, False)
        self.assertEqual(receipt1.is_debt, False)
        self.assertEqual(receipt1.receipt_closed, True)
        self.assertEqual(receipt1.is_refund, False)
        self.assertEqual(receipt1.was_refunded, True)
        self.assertEqual(receipt1.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt1.refund_for_reg_no, 0)
        self.assertEqual(receipt1.item_count, 0)
        self.assertEqual(receipt1.local_reg_no, 222)
        self.assertTrue(receipt1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receipt1.created_date).strftime("%B, %d, %Y"), 'October, 22, 2021')
        self.assertEqual(receipt1.created_date_timestamp, int(receipt1.created_date.timestamp()))

        receipt1_receiptlines = ReceiptLine.objects.filter(receipt=receipt1).order_by('id')

        # Receipt line 1
        receiptline1 = receipt1_receiptlines[0]
        
        self.assertEqual(receiptline1.user, self.user1)
        self.assertEqual(receiptline1.receipt, receipt1)
        self.assertEqual(receiptline1.store, self.store1)
        self.assertEqual(receiptline1.parent_product, None)
        self.assertEqual(receiptline1.product, self.product)
        self.assertEqual(
            receiptline1.product_info, {
                'name': self.product.name, 
                'reg_no': self.product.reg_no,
                'loyverse_variant_id': str(self.product.loyverse_variant_id),
            }
        )
        self.assertEqual(receiptline1.modifier_options.all().count(), 0)
        self.assertEqual(receiptline1.modifier_options_info, [])
        self.assertEqual(receiptline1.customer, self.customer)
        self.assertEqual(receiptline1.price, 1750.00)
        self.assertEqual(receiptline1.discount_amount, .00)
        self.assertEqual(receiptline1.is_variant, False)
        self.assertEqual(receiptline1.sold_by_each, True)
        self.assertEqual(receiptline1.units, 7)
        self.assertEqual(receiptline1.refunded_units, 5)
        self.assertTrue(receiptline1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receiptline1.created_date).strftime("%B, %d, %Y"), 'October, 22, 2021')

        # Receipt line 2
        receiptline2 = receipt1_receiptlines[1]
        
        self.assertEqual(receiptline2.user, self.user1)
        self.assertEqual(receiptline2.receipt, receipt1)
        self.assertEqual(receiptline2.store, self.store1)
        self.assertEqual(receiptline2.parent_product, None)
        self.assertEqual(receiptline2.product, self.product2)
        self.assertEqual(
            receiptline2.product_info, {
                'name': self.product2.name, 
                'reg_no': self.product2.reg_no,
                'loyverse_variant_id': str(self.product2.loyverse_variant_id)
            }
        )
        self.assertEqual(receiptline2.modifier_options.all().count(), 0)
        self.assertEqual(receiptline2.modifier_options_info, [])
        self.assertEqual(receiptline2.customer, self.customer)
        self.assertEqual(receiptline2.price, 2500.00)
        self.assertEqual(receiptline2.discount_amount, 0.00)
        self.assertEqual(receiptline2.is_variant, False)
        self.assertEqual(receiptline2.sold_by_each, True)
        self.assertEqual(receiptline2.units, 10)
        self.assertEqual(receiptline2.refunded_units, 6)
        self.assertTrue(receiptline2.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receiptline2.created_date).strftime("%B, %d, %Y"), 'October, 22, 2021')


        ###### Check refund receipt
        receipt2 = receipts[1]

        self.assertEqual(receipt2.user, self.user1)
        self.assertEqual(receipt2.store, self.store1)
        self.assertEqual(receipt2.customer, self.customer)
        self.assertEqual(receipt2.customer_info, {
                'name': self.customer.name, 
                'email': self.customer.email,
                'phone': self.customer.phone,
                'tax_pin': self.customer.tax_pin,
                'reg_no': self.customer.reg_no
            }
        )
        self.assertEqual(receipt2.subtotal_amount, refund_subtotal_amount)
        self.assertEqual(receipt2.total_amount, refund_total_amount)
        self.assertEqual(receipt2.discount_amount, refund_discount_amount)
        self.assertEqual(receipt2.tax_amount, refund_tax_amount)
        self.assertEqual(receipt2.given_amount, 0)
        self.assertEqual(receipt2.change_amount, 0)
        self.assertEqual(receipt2.loyalty_points_amount, 0)
        self.assertEqual(receipt2.total_cost, Decimal('0.00'))
        self.assertEqual(receipt2.payment_completed, True)
        self.assertEqual(receipt2.customer_points_update_completed, False)
        self.assertEqual(receipt2.is_debt, False)
        self.assertEqual(receipt2.receipt_closed, True)
        self.assertEqual(receipt2.is_refund, True)
        self.assertEqual(receipt2.was_refunded, False)
        self.assertEqual(receipt2.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt2.refund_for_reg_no, receipt1.reg_no)
        self.assertEqual(receipt2.item_count, refund_item_count)
        self.assertEqual(receipt2.local_reg_no, refund_local_reg_no)
        self.assertTrue(receipt2.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt2.created_date_timestamp, refund_created_date_timestamp)

        receipt2_receiptlines = ReceiptLine.objects.filter(receipt=receipt2).order_by('id')

        # Receipt line 1
        receiptline1 = receipt2_receiptlines[0]
        
        self.assertEqual(receiptline1.user, self.user1)
        self.assertEqual(receiptline1.receipt, receipt2)
        self.assertEqual(receiptline1.store, self.store1)
        self.assertEqual(receiptline1.parent_product, None)
        self.assertEqual(receiptline1.product, self.product)
        self.assertEqual(receiptline1.product_info, {
            'name': self.product.name, 
            'reg_no': self.product.reg_no,
            'loyverse_variant_id': str(self.product.loyverse_variant_id)
            }
        )
        self.assertEqual(receiptline1.modifier_options.all().count(), 0)
        self.assertEqual(receiptline1.modifier_options_info, [])
        self.assertEqual(receiptline1.customer, self.customer)
        self.assertEqual(receiptline1.price, 1250.00)
        self.assertEqual(receiptline1.discount_amount, .00)
        self.assertEqual(receiptline1.is_variant, False)
        self.assertEqual(receiptline1.sold_by_each, True)
        self.assertEqual(receiptline1.units, 5)
        self.assertEqual(receiptline1.refunded_units, 0)
        self.assertTrue(receiptline1.reg_no > 100000) # Check if we have a valid reg_no

        # Receipt line 2
        receiptline2 = receipt2_receiptlines[1]
        
        self.assertEqual(receiptline2.user, self.user1)
        self.assertEqual(receiptline2.receipt, receipt2)
        self.assertEqual(receiptline2.store, self.store1)
        self.assertEqual(receiptline2.parent_product, None)
        self.assertEqual(receiptline2.product, self.product2)
        self.assertEqual(receiptline2.product_info, {
            'name': self.product2.name, 
            'reg_no': self.product2.reg_no,
            'loyverse_variant_id': str(self.product2.loyverse_variant_id)
            }
        )
        self.assertEqual(receiptline2.modifier_options.all().count(), 0)
        self.assertEqual(receiptline2.modifier_options_info, [])
        self.assertEqual(receiptline2.customer, self.customer)
        self.assertEqual(receiptline2.price, 1500.00)
        self.assertEqual(receiptline2.discount_amount, 0.00)
        self.assertEqual(receiptline2.is_variant, False)
        self.assertEqual(receiptline2.sold_by_each, True)
        self.assertEqual(receiptline2.units, 6)
        self.assertEqual(receiptline2.refunded_units, 0)
        self.assertTrue(receiptline2.reg_no > 100000) # Check if we have a valid reg_no


        # Confirm stock level units were increased by receipt line units
        self.assertEqual(
            StockLevel.objects.get(product=self.product, store=self.store1).units, 
            105
        )
        self.assertEqual(
            StockLevel.objects.get(product=self.product2, store=self.store1).units, 
            56
        )

        
        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store1).order_by('id')

        self.assertEqual(historys.count(), 4)
        
        # Inventory history 1
        self.assertEqual(historys[0].user, self.user1)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].store, self.store1)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[0].change_source_reg_no, receipt.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Sale')
        self.assertEqual(historys[0].change_source_name, receipt.__str__())
        self.assertEqual(historys[0].line_source_reg_no, receipt1_receiptlines[0].reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('-7.00'))
        self.assertEqual(historys[0].stock_after, Decimal('-7.00'))
        self.assertEqual(
            (historys[0].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user1)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].store, self.store1)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[1].change_source_reg_no, receipt.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Sale')
        self.assertEqual(historys[1].change_source_name, receipt.__str__())
        self.assertEqual(historys[1].line_source_reg_no, receipt1_receiptlines[1].reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('-10.00'))
        self.assertEqual(historys[1].stock_after, Decimal('-10.00'))
        self.assertEqual(
            (historys[1].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

        # Inventory history 1
        self.assertEqual(historys[2].user, self.user1)
        self.assertEqual(historys[2].product, self.product)
        self.assertEqual(historys[2].store, self.store1)
        self.assertEqual(historys[2].product, self.product)
        self.assertEqual(historys[2].reason, InventoryHistory.INVENTORY_HISTORY_REFUND)
        self.assertEqual(historys[2].change_source_reg_no, receipt2.reg_no)
        self.assertEqual(historys[2].change_source_desc, 'Refund')
        self.assertEqual(historys[2].change_source_name, receipt2.__str__())
        self.assertEqual(historys[2].line_source_reg_no, receipt2_receiptlines[0].reg_no)
        self.assertEqual(historys[2].adjustment, Decimal('5.00'))
        self.assertEqual(historys[2].stock_after, Decimal('105.00'))
        self.assertEqual(
            (historys[2].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

        # Inventory history 2
        self.assertEqual(historys[3].user, self.user1)
        self.assertEqual(historys[3].product, self.product2)
        self.assertEqual(historys[3].store, self.store1)
        self.assertEqual(historys[3].product, self.product2)
        self.assertEqual(historys[3].reason, InventoryHistory.INVENTORY_HISTORY_REFUND)
        self.assertEqual(historys[3].change_source_reg_no, receipt2.reg_no)
        self.assertEqual(historys[3].line_source_reg_no, receipt2_receiptlines[1].reg_no)
        self.assertEqual(historys[3].change_source_desc, 'Refund')
        self.assertEqual(historys[3].change_source_name, receipt2.__str__())
        self.assertEqual(historys[3].adjustment, Decimal('6.00'))
        self.assertEqual(historys[3].stock_after, Decimal('56.00'))
        self.assertEqual(
            (historys[3].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

    def test_if_receipt_can_only_be_refunded_by_user_with_permission_refund(self):

        # Delete permission
        Permission.objects.filter(codename='can_refund_sale').delete()

        receipt = Receipt.objects.get(store=self.store1)

        response = self.client.put(
            reverse('api:pos_receipt_refund', 
            args=(self.store1.reg_no, receipt.reg_no)), 
            self.get_premade_payload(),
        )
        self.assertEqual(response.status_code, 403)

    def test_if_view_can_handle_a_wrong_store_reg_no(self):

        payload = self.get_premade_payload()

        wrong_reg_nos = [
            7878787, # Wrong reg no,
            self.store2.reg_no, # Store that does not have access to product
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        for wrong_reg_no in wrong_reg_nos:
            response = self.client.put(
                reverse('api:pos_receipt_refund', 
                args=(wrong_reg_no, self.receipt.reg_no)), 
                payload
            )
            
            self.assertEqual(response.status_code, 404)

    def test_if_view_can_handle_a_wrong_receipt_reg_no(self):

        payload = self.get_premade_payload()

        wrong_reg_nos = [
            7878787, # Wrong reg no,
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        for wrong_reg_no in wrong_reg_nos:
            response = self.client.put(
                reverse('api:pos_receipt_refund', 
                args=(self.store1.reg_no, wrong_reg_no)), 
                payload
            )

            self.assertEqual(response.status_code, 404)

    # def test_if_view_can_only_be_edited_by_its_owner(self):

    #     # Login a employee profile #
    #     # Include an appropriate `Authorization:` header on all requests.
    #     token = Token.objects.get(user__email='gucci@gmail.com')
    #     self.client = APIClient()
    #     self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    #     # First confirm receipt values before edit
    #     receipt = Receipt.objects.get(store=self.store1)
        
    #     payload = self.get_premade_payload()

    #     # Count Number of Queries
    #     #with self.assertNumQueries(34):
    #     response = self.client.put(
    #         reverse('api:pos_receipt_refund', 
    #         args=(self.store1.reg_no, receipt.reg_no)), 
    #         payload,
    #     )

    #     self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        receipt = Receipt.objects.get(store=self.store1)

        response = self.client.put(
            reverse('api:pos_receipt_refund', 
            args=(self.store1.reg_no, receipt.reg_no)),
            payload,
        )
        self.assertEqual(response.status_code, 401)
'''