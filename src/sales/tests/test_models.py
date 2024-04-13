from decimal import Decimal
from pprint import pprint
import uuid

from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.tasks import receipt_change_stock_tasks

from core.test_utils.custom_testcase import TestCase, empty_logfiles
from core.test_utils.date_utils import DateUtils
from core.test_utils.create_user import (
    create_new_cashier_user,
    create_new_user, 
    create_new_customer
)
from core.test_utils.create_store_models import (
    create_new_discount,
    create_new_store,
    create_new_tax,
    create_new_category,
)

from accounts.utils.currency_choices import CURRENCY_CHOICES
from core.test_utils.log_reader import get_test_firebase_sender_log_content
from inventories.models import InventoryHistory
from profiles.models import Customer, LoyaltySetting, Profile
from stores.models import Store, StorePaymentMethod
from products.models import (
    Product, 
    ProductBundle, 
    ProductCount, 
    ProductVariant
)

from sales.models import ( 
    CustomerDebt,
    CustomerDebtCount,
    Receipt,
    ReceiptCount,
    ReceiptLine,
    ReceiptLineCount,
    ReceiptPayment,
    StockLevel
)


"""
=========================== Receipt ===================================
"""
class ReceiptTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user1 = create_new_user('john')
        self.user2 = create_new_user('jack')
        
        self.profile1 = Profile.objects.get(user__email='john@gmail.com')
        self.profile2 = Profile.objects.get(user__email='jack@gmail.com')

        #Create a store
        self.store = create_new_store(self.profile1, 'Computer Store')

        # Create a cashier user
        self.cashier_user = create_new_cashier_user(
            "kate", self.profile1, self.store
        )

        #Create a tax
        self.tax = create_new_tax(self.profile1, self.store, 'Standard')

        #Create a discount
        self.discount = create_new_discount(self.profile1, self.store, 'Happy hour')

        #Create a category
        self.category = create_new_category(self.profile1, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.profile1, 'chris')

        self.create_sale_data(user=self.user1)


        self.cash_pay_method = StorePaymentMethod.objects.get(
            profile=self.profile1,
            payment_type=StorePaymentMethod.CASH_TYPE
        )

        self.mpesa_pay_method = StorePaymentMethod.objects.get(
            profile=self.profile1,
            payment_type=StorePaymentMethod.MPESA_TYPE
        )

        self.points_pay_method = StorePaymentMethod.objects.get(
            profile=self.profile1,
            payment_type=StorePaymentMethod.POINTS_TYPE
        )

        self.debt_pay_method = StorePaymentMethod.objects.get(
            profile=self.profile1,
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
            profile=self.profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
        self.product.stores.add(self.store)

        self.product2 = Product.objects.create(
            profile=self.profile1,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
        self.product2.stores.add(self.store)

        # Create receipt1
        self.receipt = Receipt.objects.create(
            user=user,
            store=self.store,
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
            profile=self.profile1,
            payment_type=payment_type
        )

        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=pay_method,
            amount=2500
        )
    

    def create_receipt_with_timestamp(self, created_date_timestamp):

        # Create receipt1
        Receipt.objects.create(
            user=self.user1,
            store=self.store,
            customer=self.customer,
            discount=self.discount,
            tax=self.tax,
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
            receipt_number='100-1000',
            receipt_number_for_testing='100-1000',
            created_date_timestamp=created_date_timestamp,
            changed_stock=False
        )

    def create_receipt_for_user(self, user, store, local_reg_no):

        # Create receipt1
        Receipt.objects.create(
            user=user,
            store=store,
            customer=self.customer,
            discount=self.discount,
            tax=self.tax,
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
            local_reg_no=local_reg_no,
            receipt_number='100-1000',
            receipt_number_for_testing='100-1000',
            created_date_timestamp = 1634926712,
            changed_stock=False
        )

    def create_refund_sale_data(
        self, 
        user, 
        payment_type=StorePaymentMethod.CASH_TYPE, 
        transaction_type=Receipt.MONEY_TRANS,
        payment_completed=True):


        customer = Customer.objects.get(name='Chris Evans')

        loyalty_points_amount = 0

        if payment_type == StorePaymentMethod.POINTS_TYPE:
            loyalty_points_amount = 2000


        # Creates products
        self.product = Product.objects.create(
            profile=self.profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
        self.product.stores.add(self.store)

        self.product2 = Product.objects.create(
            profile=self.profile1,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
        self.product2.stores.add(self.store)

        # Create receipt1
        self.receipt = Receipt.objects.create(
            user=user,
            store=self.store,
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
            receipt_number='100-1000',
            receipt_number_for_testing='100-1000',
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

        # Update all receipt lines for receipts
        self.update_all_receipt_lines([self.receipt.receipt_number])

        pay_method = StorePaymentMethod.objects.get(
            profile=self.profile1,
            payment_type=payment_type
        )

        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=pay_method,
            amount=2500
        )

    def delete_previous_sale_data(self):
        """
        Deletes all receipits, receiplines and products
        """
        Receipt.objects.all().delete()
        ReceiptCount.objects.all().delete()

        ReceiptLine.objects.all().delete()
        ReceiptLineCount.objects.all().delete()

        Product.objects.all().delete()
        ProductCount.objects.all().delete()

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

    def test_get_line_items_method(self):

        receipt = Receipt.objects.get(store=self.store)

        tax1 = create_new_tax(self.profile1, self.store, 'Standard1')
        tax1.loyverse_tax_id = uuid.uuid4()
        tax1.save()

        tax2 = create_new_tax(self.profile1, self.store, 'Standard2')
        tax2.loyverse_tax_id = uuid.uuid4()
        tax2.save()

        self.receiptline1.tax = tax1
        self.receiptline1.save()

        self.receiptline2.tax = tax2
        self.receiptline2.save()

        results = [
            {
                'product_info': {
                    'name': self.product.name, 
                    'reg_no': self.product.reg_no,
                    'loyverse_variant_id': str(self.product.loyverse_variant_id), 
                }, 
                'units': '7.00', 
                'price': '1750.00', 
                'total_amount': '0.00', 
                'gross_total_amount': '0.00', 
                'discount_amount': '0.00', 
                'cost': '7000.00',
                'cost_total': '7000.00',
                'tax_info': {
                    'name': tax1.name,
                    'rate': str(tax1.rate), 
                    'loyverse_tax_id': str(tax1.loyverse_tax_id)
                }
            }, 
            {
                'product_info': {
                    'name': self.product2.name, 
                    'reg_no': self.product2.reg_no,
                    'loyverse_variant_id': str(self.product2.loyverse_variant_id), 
                }, 
                'units': '10.00', 
                'price': '2500.00', 
                'total_amount': '0.00', 
                'gross_total_amount': '0.00', 
                'discount_amount': '0.00', 
                'cost': '12000.00',
                'cost_total': '12000.00',
                'tax_info': {
                    'name': tax2.name,
                    'rate': str(tax2.rate), 
                    'loyverse_tax_id': str(tax2.loyverse_tax_id)
                }
            }
        ]
        
        self.assertEqual(len(receipt.get_line_items()), len(results))

        # We using a loop because the list returned is unordered. We do this to
        # try and improve performance
        for result in results:
            self.assertTrue(result in receipt.get_line_items())

    def test_receipt_fields_verbose_names(self):

        receipt = Receipt.objects.get(store=self.store)
        
        self.assertEqual(receipt._meta.get_field('customer_info').verbose_name,'customer_info')
        self.assertEqual(receipt._meta.get_field('subtotal_amount').verbose_name,'subtotal amount')
        self.assertEqual(receipt._meta.get_field('total_amount').verbose_name,'total amount')
        self.assertEqual(receipt._meta.get_field('discount_amount').verbose_name,'discount amount')
        self.assertEqual(receipt._meta.get_field('tax_amount').verbose_name,'tax amount')
        self.assertEqual(receipt._meta.get_field('given_amount').verbose_name,'given amount')
        self.assertEqual(receipt._meta.get_field('change_amount').verbose_name,'change amount')
        self.assertEqual(receipt._meta.get_field('loyalty_points_amount').verbose_name,'loyalty points amount')
        self.assertEqual(receipt._meta.get_field('total_cost').verbose_name,'total cost')
        self.assertEqual(receipt._meta.get_field('transaction_type').verbose_name,'transaction type')
        self.assertEqual(receipt._meta.get_field('payment_completed').verbose_name,'payment completed')
        self.assertEqual(receipt._meta.get_field(
            'customer_points_update_completed').verbose_name,'customer points update completed')
        self.assertEqual(receipt._meta.get_field('is_debt').verbose_name,'is debt')
        self.assertEqual(receipt._meta.get_field('receipt_closed').verbose_name,'receipt closed')
        self.assertEqual(receipt._meta.get_field('is_refund').verbose_name,'refund completed')
        self.assertEqual(receipt._meta.get_field('was_refunded').verbose_name,'was refunded')
        self.assertEqual(receipt._meta.get_field('refund_for_reg_no').verbose_name,'refund for reg no')
        self.assertEqual(receipt._meta.get_field('item_count').verbose_name,'item count')
        self.assertEqual(receipt._meta.get_field('local_reg_no').verbose_name,'local reg no')
        self.assertEqual(receipt._meta.get_field('receipt_number').verbose_name,'receipt number')
        self.assertEqual(receipt._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(receipt._meta.get_field('created_date').verbose_name,'created date')
        self.assertEqual(receipt._meta.get_field('created_date_timestamp').verbose_name,'created date timestamp')
        self.assertEqual(receipt._meta.get_field('changed_stock').verbose_name,'changed stock')
        self.assertEqual(receipt._meta.get_field('sync_date').verbose_name,'sync date') 

        fields = ([field.name for field in Receipt._meta.fields])
        
        self.assertEqual(len(fields), 44)

    def test_receipt_fields_after_it_has_been_created(self):
        """
        Receipt fields
        
        Ensure a receipt has the right fields after it has been created
        """
        receipt = Receipt.objects.get(store=self.store)

        receipt.calculate_and_update_total_cost()
        
        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(receipt.user, self.user1)
        self.assertEqual(receipt.store, self.store)
        self.assertEqual(receipt.customer, self.customer)
        self.assertEqual(
            receipt.customer_info, 
            {
                'name': self.customer.name, 
                'email': self.customer.email,
                'phone': self.customer.phone,
                'tax_pin': self.customer.tax_pin,
                'reg_no': self.customer.reg_no
            }
        )
        self.assertEqual(receipt.subtotal_amount, 2000.00)
        self.assertEqual(receipt.total_amount, Decimal('1599.00'))
        self.assertEqual(receipt.discount_amount, Decimal('401.00'))
        self.assertEqual(receipt.tax_amount, Decimal('60.00'))
        self.assertEqual(receipt.given_amount, Decimal('2500.00'))
        self.assertEqual(receipt.change_amount, Decimal('500.00'))
        self.assertEqual(receipt.loyalty_points_amount, Decimal('0.00'))
        self.assertEqual(receipt.total_cost, Decimal('0.00'))
        self.assertEqual(receipt.payment_completed, True)
        self.assertEqual(receipt.customer_points_update_completed, False)
        self.assertEqual(receipt.is_debt, False)
        self.assertEqual(receipt.receipt_closed, True)
        self.assertEqual(receipt.is_refund, False)
        self.assertEqual(receipt.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt.item_count, 0)
        self.assertEqual(receipt.local_reg_no, 222)
        self.assertTrue(receipt.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt.receipt_number, '100-1000')
        self.assertEqual((receipt.created_date).strftime("%B, %d, %Y"), 'October, 22, 2021')
        self.assertEqual(receipt.created_date_timestamp, int(receipt.created_date.timestamp()))
        self.assertEqual(receipt.changed_stock, True)
        self.assertEqual((receipt.sync_date).strftime("%B, %d, %Y"), today)

    def test_date_fields_with_seconds_timestamp(self):

        self.delete_previous_sale_data()

        timestamp = 1632801901

        self.create_receipt_with_timestamp(timestamp)

        receipt = Receipt.objects.get(store=self.store)

        self.assertEqual(receipt.created_date_timestamp, timestamp)
        self.assertEqual(
            receipt.get_created_date(self.user1.get_user_timezone()),
            'September, 28, 2021, 07:05:AM'
        ) 

    def test_date_fields_with_millie_seconds_timestamp(self):

        self.delete_previous_sale_data()

        timestamp = 1632801901321

        self.create_receipt_with_timestamp(timestamp)

        receipt = Receipt.objects.get(store=self.store)

        self.assertEqual(receipt.created_date_timestamp, timestamp)
        self.assertEqual(
            receipt.get_created_date(self.user1.get_user_timezone()),
            'September, 28, 2021, 07:05:AM'
        )

    def test_date_fields_with_0_timestamp(self):

        self.delete_previous_sale_data()

        timestamp = 0

        self.create_receipt_with_timestamp(timestamp)

        receipt = Receipt.objects.get(store=self.store)

        today = (timezone.now()).strftime("%B, %d, %Y")
        self.assertEqual((receipt.created_date).strftime("%B, %d, %Y"), today)

        # Check if we have a valid timestamp
        self.assertTrue(len(str(receipt.created_date_timestamp)) == 10)

    def test_date_fields_with_timestamp_that_has_less_than_10_characters(self):

        self.delete_previous_sale_data()

        timestamp = 12345

        self.create_receipt_with_timestamp(timestamp)

        receipt = Receipt.objects.get(store=self.store)

        today = (timezone.now()).strftime("%B, %d, %Y")
        self.assertEqual((receipt.created_date).strftime("%B, %d, %Y"), today)

        # Check if we have a valid timestamp
        self.assertTrue(len(str(receipt.created_date_timestamp)) == 10) 

    def test_date_fields_with_timestamp_that_has_more_than_13_characters(self):

        self.delete_previous_sale_data()

        timestamp = 123456789012345

        self.create_receipt_with_timestamp(timestamp)

        receipt = Receipt.objects.get(store=self.store)

        today = (timezone.now()).strftime("%B, %d, %Y")
        self.assertEqual((receipt.created_date).strftime("%B, %d, %Y"), today)

        # Check if we have a valid timestamp
        self.assertTrue(len(str(receipt.created_date_timestamp)) == 10)
  
    def test__str__method(self):

        # Test when we have a receipt number
        receipt = Receipt.objects.get(store=self.store)
        self.assertEqual(str(receipt), 'Receipt#: 100-1000')

        # Test when we don't have a receipt number
        receipt.receipt_number = ''
        receipt.save()

        receipt = Receipt.objects.get(store=self.store)
        self.assertEqual(str(receipt), f'Receipt#: {receipt.local_reg_no}')

    def test_get_profile_method(self):
        receipt = Receipt.objects.get(store=self.store)
        self.assertEqual(receipt.get_profile(), self.profile1)

    def test_get_sale_maker_desc_method(self):
        receipt = Receipt.objects.get(store=self.store)
        self.assertEqual(
            receipt.get_sale_maker_desc(), 
            "Served by: {}".format(self.user1.get_full_name()))
    
    def test_get_customer_name_desc_method(self):

        receipt = Receipt.objects.get(store=self.store)
        self.assertEqual(
            receipt.get_customer_name_desc(), 
            "Customer: {}".format(self.customer.name))

        # Test for empty string when customer is None
        receipt.customer = None
        receipt.save()

        receipt = Receipt.objects.get(store=self.store)

        self.assertEqual(receipt.get_customer_name_desc(), '')

    def test_get_sale_type_method(self):

        receipt = Receipt.objects.get(store=self.store)
        self.assertEqual(receipt.get_sale_type(), 'Sale')

        # Perform refund
        refund_discount_amount=250
        refund_tax_amount=120
        refund_subtotal_amount=1500
        refund_total_amount=1300
        refund_loyalty_points_amount=2
        refund_item_count=6
        refund_local_reg_no=1234
        refund_created_date_timestamp=1634926712

        receipt_line_data = [
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
                'cost': 1200,
                'total_amount': 9000,
                'gross_total_amount': 9000,
                'discount_amount': 0,
                'refund_units': 6,
                'line_reg_no': self.receiptline2.reg_no,
            },
        ] 

        receipt.perform_new_refund(
            discount_amount=refund_discount_amount,
            tax_amount=refund_tax_amount,
            subtotal_amount=refund_subtotal_amount,
            total_amount=refund_total_amount,
            loyalty_points_amount=refund_loyalty_points_amount,
            item_count=refund_item_count,
            local_reg_no=refund_local_reg_no,
            receipt_number='100-1001',
            created_date_timestamp=refund_created_date_timestamp,
            receipt_line_data=receipt_line_data
        )

        receipt = Receipt.objects.get(receipt_number='100-1001')
        self.assertEqual(receipt.get_sale_type(), 'Refund')

    def test_get_item_units_method(self):
        receipt = Receipt.objects.get(store=self.store)
        self.assertEqual(receipt.get_item_units(), 17)

    def test_get_item_units_desc_method(self):
        receipt = Receipt.objects.get(store=self.store)
        self.assertEqual(receipt.get_item_units_desc(), "Total Items: 17")
   
    def test_get_payment_type_method(self):
        receipt = Receipt.objects.get(store=self.store)

        # Single payment
        self.assertEqual(receipt.get_payment_type(), 'Cash')

        # Multiple payments
        pay_method = StorePaymentMethod.objects.get(
            profile=self.profile1,
            payment_type=StorePaymentMethod.MPESA_TYPE
        )
        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=pay_method,
            amount=2500
        )

        self.assertEqual(receipt.get_payment_type(), 'Cash, Mpesa')

        # With no payments
        ReceiptPayment.objects.all().delete()

        self.assertEqual(receipt.get_payment_type(), '')

    def test_get_total_amount_desc_method(self):
        
        receipt = Receipt.objects.get(store=self.store)

        result = f"Total Amount: {self.profile1.get_currency_initials()} {receipt.total_amount}"

        self.assertEqual(receipt.get_total_amount_desc(), result)

    def test_get_subtotal_amount_and_currency_method(self):
        
        receipt = Receipt.objects.get(store=self.store)

        result = f"{self.profile1.get_currency_initials()} {receipt.subtotal_amount}"
        
        self.assertEqual(receipt.get_subtotal_amount_and_currency(), result)

    def test_get_total_amount_and_currency_method(self):
        
        receipt = Receipt.objects.get(store=self.store)

        result = f"{self.profile1.get_currency_initials()} {receipt.total_amount}"
        
        self.assertEqual(receipt.get_total_amount_and_currency(), result)

    def test_get_discount_amount_and_currency_method(self):
        
        receipt = Receipt.objects.get(store=self.store)

        result = f"{self.profile1.get_currency_initials()} {receipt.discount_amount}"
        
        self.assertEqual(receipt.get_discount_amount_and_currency(), result)

    def test_get_tax_amount_and_currency_method(self):
        
        receipt = Receipt.objects.get(store=self.store)

        result = f"{self.profile1.get_currency_initials()} {receipt.tax_amount}"
        
        self.assertEqual(receipt.get_tax_amount_and_currency(), result)

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 
        
        receipt = Receipt.objects.get(store=self.store)

        # Check if get_created_date is correct
        self.assertEqual(
            receipt.get_created_date(self.user1.get_user_timezone()),
            'October, 22, 2021, 09:18:PM'
        )

    def test_get_admin_created_date_method(self):
        
        receipt = Receipt.objects.get(store=self.store)

        # Check if get_admin_created_date is correct
        self.assertEqual(
            receipt.get_admin_created_date(),
            'October, 22, 2021, 09:18:PM'
        )
    
    def test_get_receipt_view_data_method(self):

        receipt = Receipt.objects.get(store=self.store) 

        # Add 1 more payment
        mpesa_pay_method = StorePaymentMethod.objects.get(
            profile=self.profile1,
            payment_type=StorePaymentMethod.MPESA_TYPE
        )
        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=mpesa_pay_method,
            amount=100
        )
        
        result = {
            'sale_maker_desc': receipt.get_sale_maker_desc(), 
            'payment_list': [
                {
                    'name': self.cash_pay_method.name, 
                    'payment_type': StorePaymentMethod.CASH_TYPE, 
                    'reg_no': str(self.cash_pay_method.reg_no),  
                    'amount': '2500.00'
                }, 
                {
                    'name': mpesa_pay_method.name, 
                    'payment_type': StorePaymentMethod.MPESA_TYPE, 
                    'reg_no': str(mpesa_pay_method.reg_no), 
                    'amount': '100.00'
                }
            ],
            'table_content': [
                {
                    'product_info': {
                        'name': self.product.name, 
                        'reg_no': self.product.reg_no,
                        'loyverse_variant_id': str(self.product.loyverse_variant_id)
                    }, 
                    'price': '1750.00', 
                    'discount_amount': '0.00', 
                    'sold_by_each': True, 
                    'is_variant': False, 
                    'units': '7.00',  
                    'tax_rate': '0.00',
                    'refunded_units': '0.00',
                    'modifier_options_info': [],
                    'total_amount': '0.00',
                    'gross_total_amount': self.receiptline1.gross_total_amount,
                    'reg_no': self.receiptline1.reg_no
                }, 
                {
                    'product_info': {
                        'name': self.product2.name, 
                        'reg_no': self.product2.reg_no,
                        'loyverse_variant_id': str(self.product2.loyverse_variant_id)
                    },
                    'price': '2500.00', 
                    'discount_amount': '0.00', 
                    'sold_by_each': True, 
                    'is_variant': False, 
                    'units': '10.00', 
                    'tax_rate': '0.00',
                    'refunded_units': '0.00',
                    'modifier_options_info': [],
                    'total_amount': '0.00',
                    'reg_no': self.receiptline2.reg_no
                }
            ]
        }

        self.assertEqual(receipt.get_receipt_view_data(), result)

    def test_if_update_debt_fields_method_updates_is_debt_when_payment_type_is_debt(self):

        # Deletes all receipits, receiplines and products
        self.delete_previous_sale_data()
        
        # Create receipt
        self.create_sale_data(
            user=self.user1, 
            payment_type=StorePaymentMethod.DEBT_TYPE, 
            transaction_type=Receipt.DEBT_TRANS,
            payment_completed= False
        )

        receipt = Receipt.objects.get(store=self.store)
        self.assertEqual(receipt.is_debt, True)
        self.assertEqual(receipt.get_payment_type(), 'Debt')

        # Check if update_debt_fields_method wont change is_debt when debt is 
        # payed

        # Set payment completed
        receipt = Receipt.objects.get(store=self.store)
        receipt.perform_credit_payment_completed(
            [
                {
                    'payment_method_reg_no': self.cash_pay_method.reg_no,
                    'amount': Decimal('2000.00')
                }
            ]
        )

        receipt = Receipt.objects.get(store=self.store)
        self.assertEqual(receipt.is_debt, True)
        self.assertEqual(receipt.get_payment_type(), 'Cash')
  
    def test_if_customer_current_debt_is_saved_correctly_when_user_has_set_loyalty_value(self):

        """
        Unfortunatly, when debt is paid and the user has loyalty settings with
        a valaid value, the customer model's save method is called twice.
        1. Wehn customer current debt is being deleted
        2. When customer points are being updated
        This situation introduces a nasty race condtions that's results in
        cusumer model being update with wrong/previous data

        This test checks that the proper mitigations are taken 
        """

        loyalty = LoyaltySetting.objects.get(profile=self.profile1)
        loyalty.value = 6
        loyalty.save()

        # Deletes all receipits, receiplines and products
        self.delete_previous_sale_data()
        
        # Create receipt
        self.create_sale_data(
            user=self.user1, 
            payment_type=StorePaymentMethod.DEBT_TYPE, 
            transaction_type=Receipt.DEBT_TRANS,
            payment_completed= False
        )

        customer = Customer.objects.get(profile=self.profile1)
        self.assertEqual(customer.current_debt, Decimal('2000.00'))

        # Set payment completed
        receipt = Receipt.objects.get(store=self.store)
        receipt.perform_credit_payment_completed(
            [
                {
                    'payment_method_reg_no': self.cash_pay_method.reg_no,
                    'amount': Decimal('2000.00')
                }
            ]
        )

        customer = Customer.objects.get(profile=self.profile1)
        self.assertEqual(customer.current_debt, Decimal('0.00'))
    
    def test_if_customer_debt_wont_be_created_when_payment_type_is_not_debt(self):
        
        self.assertEqual(Receipt.objects.all().count(), 1)
        self.assertEqual(CustomerDebt.objects.all().count(), 0)

    def test_if_customer_debt_will_be_created_when_payment_type_is_debt(self):

        # Deletes all receipits, receiplines and products
        self.delete_previous_sale_data()
        
        # Create receipt
        self.create_sale_data(
            user=self.user1, 
            payment_type=StorePaymentMethod.DEBT_TYPE, 
            transaction_type=Receipt.DEBT_TRANS,
            payment_completed= False
        )

        self.assertEqual(Receipt.objects.all().count(), 1)
        self.assertEqual(CustomerDebt.objects.all().count(), 1)

        # Confirm customer debt
        receipt = Receipt.objects.get(store=self.store)

        customer_debt = CustomerDebt.objects.get(receipt=receipt)

        self.assertEqual(customer_debt.customer, self.customer)
        self.assertEqual(customer_debt.receipt, receipt)
        self.assertEqual(customer_debt.debt, receipt.subtotal_amount)
        self.assertEqual(customer_debt.reg_no, receipt.reg_no)
        self.assertEqual(customer_debt.created_date, receipt.created_date)


        # Test if calling receipt save again wont create another customer debt
        Receipt.objects.get(store=self.store).save()

        self.assertEqual(CustomerDebt.objects.all().count(), 1)
    
    def test_if_perform_credit_payment_completed_wont_accept_payment_debt(self):

        # Deletes all receipits, receiplines and products
        self.delete_previous_sale_data()
        
        # Create receipt
        self.create_sale_data(
            user=self.user1, 
            payment_type=StorePaymentMethod.DEBT_TYPE,
            transaction_type=Receipt.DEBT_TRANS, 
            payment_completed= False
        )

        self.assertEqual(Receipt.objects.all().count(), 1)
        self.assertEqual(CustomerDebt.objects.all().count(), 1)

        # Set payment completed
        receipt = Receipt.objects.get(store=self.store)
        receipt.perform_credit_payment_completed(
            [
                {
                    'payment_method_reg_no': self.debt_pay_method.reg_no,
                    'amount': Decimal('2000.00')
                }
            ]
        )

        receipt = Receipt.objects.get(store=self.store)
        self.assertEqual(receipt.transaction_type, Receipt.DEBT_TRANS)
        self.assertEqual(receipt.payment_completed, False)
        self.assertEqual(receipt.receipt_closed, False)

        self.assertEqual(CustomerDebt.objects.all().count(), 1)

    def test_if_perform_credit_payment_completed_can_accept_single_payments(self):
        """
        Tests if update_receipt_count_and_close_receipt_method will delete
        customer debt when payment is later marked as completed
        """

        # Deletes all receipits, receiplines and products
        self.delete_previous_sale_data()
        
        # Create receipt
        self.create_sale_data(
            user=self.user1, 
            payment_type=StorePaymentMethod.DEBT_TYPE,
            transaction_type=Receipt.DEBT_TRANS, 
            payment_completed= False
        )

        self.assertEqual(Receipt.objects.all().count(), 1)
        self.assertEqual(CustomerDebt.objects.all().count(), 1)


        # Set payment completed
        receipt = Receipt.objects.get(store=self.store)
        receipt.perform_credit_payment_completed(
            [
                {
                    'payment_method_reg_no': self.cash_pay_method.reg_no,
                    'amount': Decimal('2000.00')
                }
            ]
        )

        receipt = Receipt.objects.get(store=self.store)

        self.assertEqual(receipt.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt.payment_completed, True)
        self.assertEqual(receipt.receipt_closed, True)

        self.assertEqual(receipt.get_payment_type(), 'Cash')

        # Confirm receipt payment model creation
        self.assertEqual(ReceiptPayment.objects.filter(receipt=receipt).count(), 1)

        receipt_payments = ReceiptPayment.objects.filter(receipt=receipt).order_by('id')

        # Receipt payment 1
        receipt_payment1 = receipt_payments[0]

        cash_pay_method = self.profile1.get_store_payment_method_from_reg_no(
            self.cash_pay_method.reg_no
        )

        self.assertEqual(receipt_payment1.receipt, receipt)
        self.assertEqual(receipt_payment1.payment_method, cash_pay_method)
        self.assertEqual(receipt_payment1.amount, Decimal('2000.00'))

        # Check if customer debt has been deleted
        self.assertEqual(CustomerDebt.objects.all().count(), 0)

    def test_if_perform_credit_payment_completed_can_accept_multiple_payments(self):
        """
        Tests if update_receipt_count_and_close_receipt_method will delete
        customer debt when payment is later marked as completed
        """

        # Deletes all receipits, receiplines and products
        self.delete_previous_sale_data()
        
        # Create receipt
        self.create_sale_data(
            user=self.user1, 
            payment_type=StorePaymentMethod.DEBT_TYPE,
            transaction_type=Receipt.DEBT_TRANS, 
            payment_completed= False
        )

        self.assertEqual(Receipt.objects.all().count(), 1)
        self.assertEqual(CustomerDebt.objects.all().count(), 1)


        # Set payment completed
        receipt = Receipt.objects.get(store=self.store)
        receipt.perform_credit_payment_completed(
            [
                {
                    'payment_method_reg_no': self.cash_pay_method.reg_no,
                    'amount': Decimal('1200.00')
                },
                {
                    'payment_method_reg_no': self.mpesa_pay_method.reg_no,
                    'amount': Decimal('800.00')
                }
            ]
        )

        receipt = Receipt.objects.get(store=self.store)

        self.assertEqual(receipt.transaction_type, Receipt.MULTIPLE_TRANS)
        self.assertEqual(receipt.payment_completed, True)
        self.assertEqual(receipt.receipt_closed, True)

        self.assertEqual(receipt.get_payment_type(), 'Cash, Mpesa')


        # Confirm receipt payment model creation
        self.assertEqual(ReceiptPayment.objects.filter(receipt=receipt).count(), 2)

        receipt_payments = ReceiptPayment.objects.filter(receipt=receipt).order_by('id')

        # Receipt payment 1
        receipt_payment1 = receipt_payments[0]

        cash_pay_method = self.profile1.get_store_payment_method_from_reg_no(
            self.cash_pay_method.reg_no
        )

        self.assertEqual(receipt_payment1.receipt, receipt)
        self.assertEqual(receipt_payment1.payment_method, cash_pay_method)
        self.assertEqual(receipt_payment1.amount, Decimal('1200.00'))

        # Receipt payment 2
        receipt_payment2 = receipt_payments[1]

        mpesa_pay_method = self.profile1.get_store_payment_method_from_reg_no(
            self.mpesa_pay_method.reg_no
        )

        self.assertEqual(receipt_payment2.receipt, receipt)
        self.assertEqual(receipt_payment2.payment_method, mpesa_pay_method)
        self.assertEqual(receipt_payment2.amount, Decimal('800.00'))

        # Check if customer debt has been deleted
        self.assertEqual(CustomerDebt.objects.all().count(), 0)
    

    def test_update_receipt_count_and_close_receipt_method(self):

        # Delete receipt
        Receipt.objects.all().delete()

         # Create receipt
        self.receipt = Receipt.objects.create(
            user=self.user1,
            store=self.store,
            customer=self.customer,
            discount_amount=401.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=False
        )

        # Create receipt line
        self.receiptline1 =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=self.product,
            product_info = {'name': self.product.name},
            price=1750,
            units=7
        )

        pay_method = self.profile1.get_store_payment_method(
            StorePaymentMethod.CASH_TYPE
        )
        
        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=pay_method,
            amount=2500
        )

        receipt_reg_no = Receipt.objects.get(store=self.store).reg_no


        ### Confirm receipt payment completed and receipt closed fields
        # Receipt
        receipt = Receipt.objects.get(reg_no=receipt_reg_no)
        self.assertEqual(receipt.payment_completed, False)
        self.assertEqual(receipt.receipt_closed, False)

         # ReceiptCount
        receipt_count = ReceiptCount.objects.get(reg_no=receipt_reg_no)
        self.assertEqual(receipt_count.payment_completed, False)

        ### Update receipt payment
        receipt = Receipt.objects.get(reg_no=receipt_reg_no)
        receipt.payment_completed = True
        receipt.save()


        ### Confirm receipt payment completed and receipt closed fields
        # Receipt
        receipt = Receipt.objects.get(reg_no=receipt_reg_no)
        self.assertEqual(receipt.payment_completed, True)
        self.assertEqual(receipt.receipt_closed, True)

        # ReceiptCount
        receipt_count = ReceiptCount.objects.get(reg_no=receipt_reg_no)
        self.assertEqual(receipt_count.payment_completed, True)


        # Check if another receipt update wont update ReceiptCount payment completed
        # field
        ### Update sale payment
        receipt = Receipt.objects.get(reg_no=receipt_reg_no)
        receipt.payment_completed = False
        receipt.save()


        ### Confirm receipt payment completed and receipt closed fields cannot
        # be reversed after thery have been completed
        # Receipt
        receipt = Receipt.objects.get(reg_no=receipt_reg_no)
        self.assertEqual(receipt.payment_completed, True)
        self.assertEqual(receipt.receipt_closed, True)

        # ReceiptCount
        receipt_count = ReceiptCount.objects.get(reg_no=receipt_reg_no)
        self.assertEqual(receipt_count.payment_completed, True)

    def test_if_perform_refund_wont_error_out_when_product_has_no_stock_level_model(self):

        StockLevel.objects.all().delete()
        self.assertEqual(StockLevel.objects.all().count(), 0)

        # Update track stock
        self.product.track_stock = True
        self.product.save()

        self.assertEqual(Product.objects.get(name="Shampoo",).track_stock, True)

        # Perform refund
        Receipt.objects.get(store=self.store).perform_refund()
        self.assertEqual(Receipt.objects.get(store=self.store).is_refund, True)

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.all().count(), 0)

    def test_if_perform_refund_method_will_update_stock_level_units_and_create_inventory_history(self):

        stock_level = StockLevel.objects.get(product=self.product)
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(product=self.product2)
        stock_level.units = 50
        stock_level.save()

        # Update track stock
        self.product.track_stock = True
        self.product.save()

        self.assertEqual(Product.objects.get(name="Shampoo",).track_stock, True)

        ############ Perform refund
        receipt = Receipt.objects.get(store=self.store)

        refund_discount_amount=250
        refund_tax_amount=120
        refund_subtotal_amount=1500
        refund_total_amount=1300
        refund_loyalty_points_amount=2
        refund_item_count=6
        refund_local_reg_no=1234
        refund_created_date_timestamp=1634926712

        receipt_line_data = [
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
                'cost': 1200,
                'discount_amount': 0,
                'total_amount': 9000,
                'gross_total_amount': 9000,
                'refund_units': 6,
                'line_reg_no': self.receiptline2.reg_no,
            },
        ]

        refund_response = receipt.perform_new_refund(
            discount_amount=refund_discount_amount,
            tax_amount=refund_tax_amount,
            subtotal_amount=refund_subtotal_amount,
            total_amount=refund_total_amount,
            loyalty_points_amount=refund_loyalty_points_amount,
            item_count=refund_item_count,
            local_reg_no=refund_local_reg_no,
            receipt_number='100-1001',
            created_date_timestamp=refund_created_date_timestamp,
            receipt_line_data=receipt_line_data
        )

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
                },
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
                    'creation_date': refunded_receipt.get_created_date(
                        self.user1.get_user_timezone()
                    ), 
                    'created_date_timestamp': refunded_receipt.created_date_timestamp,
                    'receipt_data': refunded_receipt.get_receipt_view_data()
                }
            ]
        }

        self.assertEqual(refund_response, results)

        # Force refund receipts lines to update
        self.update_all_receipt_lines(['100-1001'])

        receipts = Receipt.objects.filter(store=self.store)

        ###### Check refunded receipt
        receipt1 = receipts[0]

        self.assertEqual(receipt1.user, self.user1)
        self.assertEqual(receipt1.store, self.store)
        self.assertEqual(receipt1.customer, self.customer)
        self.assertEqual(
            receipt1.customer_info, 
            {
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
        self.assertEqual(receiptline1.store, self.store)
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
        self.assertEqual(receiptline1.cost, 7000.00)
        self.assertEqual(receiptline1.total_amount, 0)
        self.assertEqual(receiptline1.gross_total_amount, 0)
        self.assertEqual(receiptline1.discount_amount, 0)
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
        self.assertEqual(receiptline2.store, self.store)
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
        self.assertEqual(receipt2.store, self.store)
        self.assertEqual(receipt2.customer, self.customer)
        self.assertEqual(
            receipt2.customer_info, 
            {
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
        self.assertEqual(receipt2.loyalty_points_amount, refund_loyalty_points_amount)
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
        self.assertEqual(receiptline1.store, self.store)
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
        self.assertEqual(receiptline1.price, receipt_line_data[0]['price'])
        self.assertEqual(receiptline1.cost, Decimal('5000.00'))
        self.assertEqual(receiptline1.total_amount, receipt_line_data[0]['total_amount'])
        self.assertEqual(receiptline1.gross_total_amount, receipt_line_data[0]['gross_total_amount'])
        self.assertEqual(receiptline1.discount_amount, receipt_line_data[0]['discount_amount'])
        self.assertEqual(receiptline1.is_variant, False)
        self.assertEqual(receiptline1.sold_by_each, True)
        self.assertEqual(receiptline1.units, 5)
        self.assertEqual(receiptline1.refunded_units, 0)
        self.assertTrue(receiptline1.reg_no > 100000) # Check if we have a valid reg_no

        # Receipt line 2
        receiptline2 = receipt2_receiptlines[1]

        self.assertEqual(receiptline2.user, self.user1)
        self.assertEqual(receiptline2.receipt, receipt2)
        self.assertEqual(receiptline2.store, self.store)
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
        self.assertEqual(receiptline2.price, receipt_line_data[1]['price'])
        self.assertEqual(receiptline2.cost, Decimal('7200.00'))
        self.assertEqual(receiptline2.total_amount, receipt_line_data[1]['total_amount'])
        self.assertEqual(receiptline2.gross_total_amount, receipt_line_data[1]['gross_total_amount'])
        self.assertEqual(receiptline2.discount_amount, receipt_line_data[1]['discount_amount'])
        self.assertEqual(receiptline2.price, 1500.00)
        self.assertEqual(receiptline2.discount_amount, 0.00)
        self.assertEqual(receiptline2.is_variant, False)
        self.assertEqual(receiptline2.sold_by_each, True)
        self.assertEqual(receiptline2.units, 6)
        self.assertEqual(receiptline2.refunded_units, 0)
        self.assertTrue(receiptline2.reg_no > 100000) # Check if we have a valid reg_no

        # Confirm stock level units were increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product).units, 105)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 56)

        
        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store).order_by('id')

        self.assertEqual(historys.count(), 4)
        
        # Inventory history 1
        self.assertEqual(historys[0].user, self.user1)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].store, self.store)
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
        self.assertEqual(historys[1].store, self.store)
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
        self.assertEqual(historys[2].store, self.store)
        self.assertEqual(historys[2].product, self.product)
        self.assertEqual(historys[2].reason, InventoryHistory.INVENTORY_HISTORY_REFUND)
        self.assertEqual(historys[2].change_source_reg_no, receipt2.reg_no)
        self.assertEqual(historys[2].change_source_desc, 'Refund')
        self.assertEqual(historys[2].change_source_name, receipt2.__str__())
        self.assertEqual(historys[2].line_source_reg_no, receipt2_receiptlines[0].reg_no)
        self.assertEqual(historys[2].adjustment, Decimal('5.00'))
        self.assertEqual(historys[2].stock_after, Decimal('-2.00'))
        self.assertEqual(
            (historys[2].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

        # Inventory history 2
        self.assertEqual(historys[3].user, self.user1)
        self.assertEqual(historys[3].product, self.product2)
        self.assertEqual(historys[3].store, self.store)
        self.assertEqual(historys[3].product, self.product2)
        self.assertEqual(historys[3].reason, InventoryHistory.INVENTORY_HISTORY_REFUND)
        self.assertEqual(historys[3].change_source_reg_no, receipt2.reg_no)
        self.assertEqual(historys[3].line_source_reg_no, receipt2_receiptlines[1].reg_no)
        self.assertEqual(historys[3].change_source_desc, 'Refund')
        self.assertEqual(historys[3].change_source_name, receipt2.__str__())
        self.assertEqual(historys[3].adjustment, Decimal('6.00'))
        self.assertEqual(historys[3].stock_after, Decimal('-4.00'))
        self.assertEqual(
            (historys[3].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

    def test_if_refund_wont_be_allowed_if_refunded_units_are_above_receipt_line_units(self):

        stock_level = StockLevel.objects.get(product=self.product)
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(product=self.product2)
        stock_level.units = 50
        stock_level.save()

        # Update track stock
        self.product.track_stock = True
        self.product.save()

        self.assertEqual(Product.objects.get(name="Shampoo",).track_stock, True)

        ############ Perform refund
        receipt = Receipt.objects.get(store=self.store)

        refund_discount_amount=250
        refund_tax_amount=120
        refund_subtotal_amount=1500
        refund_total_amount=1300
        refund_loyalty_points_amount=2
        refund_item_count=6
        refund_local_reg_no=1234
        refund_created_date_timestamp=1634926712

        receipt_line_data = [
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
                'cost': 1200,
                'discount_amount': 0,
                'total_amount': 9000,
                'gross_total_amount': 9000,
                'refund_units': 6,
                'line_reg_no': self.receiptline2.reg_no,
            },
        ]

        refund_response1 = receipt.perform_new_refund(
            discount_amount=refund_discount_amount,
            tax_amount=refund_tax_amount,
            subtotal_amount=refund_subtotal_amount,
            total_amount=refund_total_amount,
            loyalty_points_amount=refund_loyalty_points_amount,
            item_count=refund_item_count,
            local_reg_no=refund_local_reg_no,
            receipt_number='100-1001',
            created_date_timestamp=refund_created_date_timestamp,
            receipt_line_data=receipt_line_data
        )

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
                },
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
                    'creation_date': refunded_receipt.get_created_date(
                        self.user1.get_user_timezone()
                    ), 
                    'created_date_timestamp': refunded_receipt.created_date_timestamp,
                    'receipt_data': refunded_receipt.get_receipt_view_data()
                }
            ]
        }

        self.assertEqual(refund_response1, results)

        refund_response2 = receipt.perform_new_refund(
            discount_amount=refund_discount_amount,
            tax_amount=refund_tax_amount,
            subtotal_amount=refund_subtotal_amount,
            total_amount=refund_total_amount,
            loyalty_points_amount=refund_loyalty_points_amount,
            item_count=refund_item_count,
            local_reg_no=refund_local_reg_no,
            receipt_number='100-1002',
            created_date_timestamp=refund_created_date_timestamp,
            receipt_line_data=receipt_line_data
        )

        # Check if refund2 was not successful
        self.assertEqual(refund_response2, [])

        # Force refund receipts lines to update
        self.update_all_receipt_lines(['100-1001'])


        receipts = Receipt.objects.filter(store=self.store)

        self.assertEqual(receipts.count(), 2)


        ###### Check refunded receipt
        receipt1 = receipts[0]

        self.assertEqual(receipt1.user, self.user1)
        self.assertEqual(receipt1.store, self.store)
        self.assertEqual(receipt1.customer, self.customer)
        self.assertEqual(
            receipt1.customer_info, 
            {
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
        self.assertEqual(receiptline1.store, self.store)
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
        self.assertEqual(receiptline2.store, self.store)
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
        self.assertEqual(receipt2.store, self.store)
        self.assertEqual(receipt2.customer, self.customer)
        self.assertEqual(
            receipt2.customer_info, 
            {
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
        self.assertEqual(receipt2.loyalty_points_amount, refund_loyalty_points_amount)
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
        self.assertEqual(receiptline1.store, self.store)
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
        self.assertEqual(receiptline2.store, self.store)
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
        self.assertEqual(StockLevel.objects.get(product=self.product).units, 105)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 56)

        
        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store).order_by('id')

        self.assertEqual(historys.count(), 4)
        
        # Inventory history 1
        self.assertEqual(historys[0].user, self.user1)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].store, self.store)
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
        self.assertEqual(historys[1].store, self.store)
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
        self.assertEqual(historys[2].store, self.store)
        self.assertEqual(historys[2].product, self.product)
        self.assertEqual(historys[2].reason, InventoryHistory.INVENTORY_HISTORY_REFUND)
        self.assertEqual(historys[2].change_source_reg_no, receipt2.reg_no)
        self.assertEqual(historys[2].change_source_desc, 'Refund')
        self.assertEqual(historys[2].change_source_name, receipt2.__str__())
        self.assertEqual(historys[2].line_source_reg_no, receipt2_receiptlines[0].reg_no)
        self.assertEqual(historys[2].adjustment, Decimal('5.00'))
        self.assertEqual(historys[2].stock_after, Decimal('-2.00'))
        self.assertEqual(
            (historys[2].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

        # Inventory history 2
        self.assertEqual(historys[3].user, self.user1)
        self.assertEqual(historys[3].product, self.product2)
        self.assertEqual(historys[3].store, self.store)
        self.assertEqual(historys[3].product, self.product2)
        self.assertEqual(historys[3].reason, InventoryHistory.INVENTORY_HISTORY_REFUND)
        self.assertEqual(historys[3].change_source_reg_no, receipt2.reg_no)
        self.assertEqual(historys[3].line_source_reg_no, receipt2_receiptlines[1].reg_no)
        self.assertEqual(historys[3].change_source_desc, 'Refund')
        self.assertEqual(historys[3].change_source_name, receipt2.__str__())
        self.assertEqual(historys[3].adjustment, Decimal('6.00'))
        self.assertEqual(historys[3].stock_after, Decimal('-4.00'))
        self.assertEqual(
            (historys[3].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

    def test_if_perform_refund_method_will_update_bundled_product_stock_level_units(self):

        master_product = Product.objects.create(
            profile=self.profile1,
            tax=self.tax,
            category=self.category,
            name="Hair Bundle",
            price=35000,
            cost=30000,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
    
        # Update stock levels for products
        stock_level = StockLevel.objects.get(product=self.product)
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(product=self.product2)
        stock_level.units = 160
        stock_level.save()

        stock_level = StockLevel.objects.get(product=master_product)
        stock_level.units = 240
        stock_level.save()


        # Delete all receipts
        deleted_receipt_str = self.receipt.__str__()
        deleted_receipt_reg_no = self.receipt.reg_no
        deleted_receipt_line_reg_no1 = self.receiptline1.reg_no
        deleted_receipt_line_reg_no2 = self.receiptline2.reg_no
        Receipt.objects.all().delete()

        # Update track stock for products
        self.product.track_stock = True
        self.product.save()

        self.assertEqual(
            Product.objects.get(reg_no=self.product.reg_no).track_stock,True)

        self.product2.track_stock = True
        self.product2.save()

        self.assertEqual(
            Product.objects.get(reg_no=self.product2.reg_no).track_stock,True)


        # Create master product with 2 bundles
        shampoo_bundle = ProductBundle.objects.create(
            product_bundle=self.product,
            quantity=30
        )

        conditoner_bundle = ProductBundle.objects.create(
            product_bundle=self.product2,
            quantity=25
        )

        
        master_product.bundles.add(shampoo_bundle, conditoner_bundle)
        master_product.stores.add(self.store)


        # Make sale
        # Create receipt1
        receipt = Receipt.objects.create(
            user=self.user1,
            store=self.store,
            customer=self.customer,
            discount_amount=401.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            receipt_number='120',
            payment_completed=True,
            created_date_timestamp=1634926712
        )
        
        # Create receipt line1
        receipt_line = ReceiptLine.objects.create(
            receipt=receipt,
            product=master_product,
            product_info = {'name': master_product.name, 'reg_no': master_product.reg_no},
            price=1750,
            discount_amount=150,
            units=2
        )

        self.update_all_receipt_lines([receipt.receipt_number])

        # **** Make sure master product's bundled products stock levels was updated
        bundled_product1 = Product.objects.get(name="Shampoo")
        self.assertEqual(StockLevel.objects.get(product=bundled_product1).units, 100)


        bundled_product2 = Product.objects.get(name="Conditioner")
        self.assertEqual(StockLevel.objects.get(product=bundled_product2).units, 160)

        # Make sure master product's stock level was not updated
        master_product = Product.objects.get(name="Hair Bundle")
        self.assertEqual(StockLevel.objects.get(product=master_product).units, 238)

        # **** Perform refund
        receipt = Receipt.objects.get(store=self.store)

        refund_discount_amount=250
        refund_tax_amount=120
        refund_subtotal_amount=1500
        refund_total_amount=1300
        refund_loyalty_points_amount=2
        refund_item_count=6
        refund_local_reg_no=1234
        refund_created_date_timestamp=1634926712

        receipt_line_data = [
            {
                'price': 875,
                'cost': 1000,
                'total_amount': 875,
                'gross_total_amount': 875,
                'discount_amount': 150,
                'refund_units': 1,
                'line_reg_no': receipt_line.reg_no,
            }
        ]

        receipt.perform_new_refund(
            discount_amount=refund_discount_amount,
            tax_amount=refund_tax_amount,
            subtotal_amount=refund_subtotal_amount,
            total_amount=refund_total_amount,
            loyalty_points_amount=refund_loyalty_points_amount,
            item_count=refund_item_count,
            local_reg_no=refund_local_reg_no,
            receipt_number='121',
            created_date_timestamp=refund_created_date_timestamp,
            receipt_line_data=receipt_line_data
        )
        self.update_all_receipt_lines(['121'])
        
        receipts = Receipt.objects.filter(store=self.store)

        ###### Check refunded receipt
        receipt1 = receipts[0]

        self.assertEqual(receipt1.user, self.user1)
        self.assertEqual(receipt1.store, self.store)
        self.assertEqual(receipt1.customer, self.customer)
        self.assertEqual(
            receipt1.customer_info, 
            {
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
        self.assertEqual(receipt1.tax_amount, Decimal('0.00'))
        self.assertEqual(receipt1.given_amount, Decimal('0.00'))
        self.assertEqual(receipt1.change_amount, Decimal('0.00'))
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
        self.assertEqual(receipt1.local_reg_no, 0)
        self.assertTrue(receipt1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receipt1.created_date).strftime("%B, %d, %Y"), 'October, 22, 2021')
        self.assertEqual(receipt1.created_date_timestamp, int(receipt1.created_date.timestamp()))

        receipt1_receiptlines = ReceiptLine.objects.filter(receipt=receipt1).order_by('id')
        self.assertEqual(receipt1_receiptlines.count(), 1)

        # Receipt line 1
        receiptline1 = receipt1_receiptlines[0]

        self.assertEqual(receiptline1.user, self.user1)
        self.assertEqual(receiptline1.receipt, receipt1)
        self.assertEqual(receiptline1.store, self.store)
        self.assertEqual(receiptline1.parent_product, None)
        self.assertEqual(receiptline1.product, master_product)
        self.assertEqual(receiptline1.product_info, {
            'name': master_product.name, 
            'reg_no': master_product.reg_no,
            'loyverse_variant_id': str(master_product.loyverse_variant_id)
            }
        )
        self.assertEqual(receiptline1.modifier_options.all().count(), 0)
        self.assertEqual(receiptline1.modifier_options_info, [])
        self.assertEqual(receiptline1.customer, self.customer)
        self.assertEqual(receiptline1.price, 1750.00)
        self.assertEqual(receiptline1.discount_amount, 150)
        self.assertEqual(receiptline1.is_variant, False)
        self.assertEqual(receiptline1.sold_by_each, True)
        self.assertEqual(receiptline1.units, 2)
        self.assertEqual(receiptline1.refunded_units, 1)
        self.assertTrue(receiptline1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receiptline1.created_date).strftime("%B, %d, %Y"), 'October, 22, 2021')


        ###### Check refund receipt
        receipt2 = receipts[1]

        self.assertEqual(receipt2.user, self.user1)
        self.assertEqual(receipt2.store, self.store)
        self.assertEqual(receipt2.customer, self.customer)
        self.assertEqual(
            receipt2.customer_info, 
            {
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
        self.assertEqual(receipt2.loyalty_points_amount, refund_loyalty_points_amount)
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
        self.assertEqual(receiptline1.store, self.store)
        self.assertEqual(receiptline1.parent_product, None)
        self.assertEqual(receiptline1.product, master_product)
        self.assertEqual(receiptline1.product_info, {
            'name': master_product.name, 
            'reg_no': master_product.reg_no,
            'loyverse_variant_id': str(master_product.loyverse_variant_id)
            }
        )
        self.assertEqual(receiptline1.modifier_options.all().count(), 0)
        self.assertEqual(receiptline1.modifier_options_info, [])
        self.assertEqual(receiptline1.customer, self.customer)
        self.assertEqual(receiptline1.price, receipt_line_data[0]['price'])
        self.assertEqual(receiptline1.cost, Decimal('30000.00'))
        self.assertEqual(receiptline1.total_amount, receipt_line_data[0]['total_amount'])
        self.assertEqual(receiptline1.gross_total_amount, receipt_line_data[0]['gross_total_amount'])
        self.assertEqual(receiptline1.discount_amount, receipt_line_data[0]['discount_amount'])
        self.assertEqual(receiptline1.is_variant, False)
        self.assertEqual(receiptline1.sold_by_each, True)
        self.assertEqual(receiptline1.units, 1)
        self.assertEqual(receiptline1.refunded_units, 0)
        self.assertTrue(receiptline1.reg_no > 100000) # Check if we have a valid reg_no


        # Make sure master product's bundled products stock levels was updated
        bundled_product1 = Product.objects.get(name="Shampoo")
        self.assertEqual(StockLevel.objects.get(product=bundled_product1).units, 100)

        bundled_product2 = Product.objects.get(name="Conditioner")
        self.assertEqual(StockLevel.objects.get(product=bundled_product2).units, 160)

        # Make sure master product's stock level was not updated
        master_product = Product.objects.get(name="Hair Bundle")
        self.assertEqual(StockLevel.objects.get(product=master_product).units, 239)


        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store)

        self.assertEqual(historys.count(), 4)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user1)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].store, self.store)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[0].change_source_reg_no, deleted_receipt_reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Sale')
        self.assertEqual(historys[0].change_source_name, deleted_receipt_str.__str__())
        self.assertEqual(historys[0].line_source_reg_no, deleted_receipt_line_reg_no1)
        self.assertEqual(historys[0].adjustment, Decimal('-7.00'))
        self.assertEqual(historys[0].stock_after, Decimal('-7.00'))
        self.assertEqual(
            (historys[0].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user1)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].store, self.store)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[1].change_source_reg_no, deleted_receipt_reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Sale')
        self.assertEqual(historys[1].change_source_name, deleted_receipt_str.__str__().__str__())
        self.assertEqual(historys[1].line_source_reg_no, deleted_receipt_line_reg_no2)
        self.assertEqual(historys[1].adjustment, Decimal('-10.00'))
        self.assertEqual(historys[1].stock_after, Decimal('-10.00'))
        self.assertEqual(
            (historys[1].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

        # Inventory history 3
        self.assertEqual(historys[2].user, self.user1)
        self.assertEqual(historys[2].product, master_product)
        self.assertEqual(historys[2].store, self.store)
        self.assertEqual(historys[2].product, master_product)
        self.assertEqual(historys[2].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[2].change_source_reg_no, receipt.reg_no)
        self.assertEqual(historys[2].change_source_desc, 'Sale')
        self.assertEqual(historys[2].change_source_name, receipt.__str__())
        self.assertEqual(historys[2].line_source_reg_no, receipt1_receiptlines[0].reg_no)
        self.assertEqual(historys[2].adjustment, Decimal('-2.00'))
        self.assertEqual(historys[2].stock_after, Decimal('238.00'))
        self.assertEqual(
            (historys[2].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

        # Inventory history 4
        self.assertEqual(historys[3].user, self.user1)
        self.assertEqual(historys[3].product, master_product)
        self.assertEqual(historys[3].store, self.store)
        self.assertEqual(historys[3].product, master_product)
        self.assertEqual(historys[3].reason, InventoryHistory.INVENTORY_HISTORY_REFUND)
        self.assertEqual(historys[3].change_source_reg_no, receipt2.reg_no)
        self.assertEqual(historys[3].change_source_desc, 'Refund')
        self.assertEqual(historys[3].change_source_name, receipt2.__str__())
        self.assertEqual(historys[3].line_source_reg_no, receipt2_receiptlines[0].reg_no)
        self.assertEqual(historys[3].adjustment, Decimal('1.00'))
        self.assertEqual(historys[3].stock_after, Decimal('239.00'))
        self.assertEqual(
            (historys[3].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

    def test_if_perform_refund_method_will_update_receipt_count_is_refund(self):

        # Check if receipt count status
        receipt_count = ReceiptCount.objects.get(user=self.user1)
        self.assertEqual(receipt_count.is_refund, False)

        ############ Perform refund
        receipt = Receipt.objects.get(store=self.store)

        refund_discount_amount=250
        refund_tax_amount=120
        refund_subtotal_amount=1500
        refund_total_amount=1300
        refund_loyalty_points_amount=2
        refund_item_count=6
        refund_local_reg_no=1234
        refund_created_date_timestamp=1632801901322

        receipt_line_data = [
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

        receipt.perform_new_refund(
            discount_amount=refund_discount_amount,
            tax_amount=refund_tax_amount,
            subtotal_amount=refund_subtotal_amount,
            total_amount=refund_total_amount,
            loyalty_points_amount=refund_loyalty_points_amount,
            item_count=refund_item_count,
            local_reg_no=refund_local_reg_no,
            receipt_number='120',
            created_date_timestamp=refund_created_date_timestamp,
            receipt_line_data=receipt_line_data
        )

        # Check if receipt counts was updated successfully
        receipt_counts = ReceiptCount.objects.filter(user=self.user1).order_by('id')
        self.assertEqual(receipt_counts[0].is_refund, False)
        self.assertEqual(receipt_counts[1].is_refund, True)
 
    def test_if_update_customer_points_method_will_decrease_customer_points_when_payment_type_is_points(self):

        # Deletes all receipits, receiplines and products
        self.delete_previous_sale_data()

        # Give customer points
        customer = Customer.objects.get(name='Chris Evans')
        customer.points = 10000
        customer.save()

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.profile1)
        loyalty.value = 6
        loyalty.save()

        # Make sale
        self.create_sale_data(
            user=self.user1, 
            payment_type=StorePaymentMethod.POINTS_TYPE,
            transaction_type=Receipt.LOYALTY_TRANS,
        )

        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.points, 8000)


        #*** Test when receipt is saved again, customer points are not changed
        Receipt.objects.get(store=self.store).save()

        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.points, 8000)

    def test_if_update_customer_points_method_can_increase_customer_points(self):

        # Deletes all receipits, receiplines and products
        self.delete_previous_sale_data()

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.profile1)
        loyalty.value = 6
        loyalty.save()

        # Make sale
        self.create_sale_data(user=self.user1)

        customer = Customer.objects.get(name='Chris Evans')

        self.assertEqual(customer.points, 120)

    def test_if_update_customer_points_method_wont_error_when_customer_is_none(self):

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.profile1)
        loyalty.value = 6
        loyalty.save()

        # Create receipt
        self.receipt = Receipt.objects.create(
            user=self.user1,
            store=self.store,
            customer=None,
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
            payment_completed=False
        )

        receipt = Receipt.objects.filter(store=self.store).order_by('id')[1]

        self.assertEqual(receipt.user, self.user1)
        self.assertEqual(receipt.store, self.store)
        self.assertEqual(receipt.customer, None)
        self.assertEqual(receipt.customer_info, {
            'name': self.customer.name, 
            'reg_no': self.customer.reg_no
            }
        )
        
    def test_if_update_customer_points_method_wont_update_customer_if_payment_type_is_debt(self):

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.profile1)
        loyalty.value = 6
        loyalty.save()

        # Create receipt
        self.create_sale_data(
            user=self.user1, 
            receipt_number='100-1001',
            payment_type=StorePaymentMethod.DEBT_TYPE, 
            transaction_type=Receipt.DEBT_TRANS,
            payment_completed= False
        )

        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.points, 0)


        #*** Test when payment is completed customer's points will be added
        receipt = Receipt.objects.filter(store=self.store).order_by('id')[1]
        self.assertEqual(receipt.payment_completed, False)
        self.assertEqual(receipt.receipt_closed, False)

        receipt.perform_credit_payment_completed(
            [
                {
                    'payment_method_reg_no': self.cash_pay_method.reg_no,
                    'amount': Decimal('2000.00')
                }
            ]
        )

        receipt = Receipt.objects.filter(store=self.store).order_by('id')[1]
        self.assertEqual(receipt.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt.payment_completed, True)
        self.assertEqual(receipt.receipt_closed, True)

        # Check if customer was updated
        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.points, 120)


        #*** Test when payment is saved again customer's points wont be added again
        receipt = Receipt.objects.filter(store=self.store).order_by('id')[1]
        receipt.perform_credit_payment_completed(
            [
                {
                    'payment_method_reg_no': self.cash_pay_method.reg_no,
                    'amount': Decimal('2000.00')
                }
            ]
        )

        receipt = Receipt.objects.filter(store=self.store).order_by('id')[1]
        self.assertEqual(receipt.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt.payment_completed, True)
        self.assertEqual(receipt.receipt_closed, True)


        # Check if customer was updated
        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.points, 120)
    
    def test_if_update_customer_points_method_can_handle_debt_paid_with_points(self):

        # Give customer points
        customer = Customer.objects.get(name='Chris Evans')
        customer.points = 10000
        customer.save()

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.profile1)
        loyalty.value = 6
        loyalty.save()

        # Create receipt
        self.create_sale_data(
            user=self.user1, 
            receipt_number='100-1001',
            payment_type=StorePaymentMethod.DEBT_TYPE, 
            transaction_type=Receipt.DEBT_TRANS,
            payment_completed= False
        )

        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.points, 10000)


        #*** Test when payment is completed with points customer's points will 
        # be decreased
        receipt = Receipt.objects.filter(store=self.store).order_by('id')[1]
        self.assertEqual(receipt.payment_completed, False)
        self.assertEqual(receipt.receipt_closed, False)

        receipt.perform_credit_payment_completed(
            [
                {
                    'payment_method_reg_no': self.points_pay_method.reg_no,
                    'amount': Decimal('2000.00')
                }
            ]
        )

        receipt = Receipt.objects.filter(store=self.store).order_by('id')[1]
        self.assertEqual(receipt.transaction_type, Receipt.LOYALTY_TRANS)
        self.assertEqual(receipt.payment_completed, True)
        self.assertEqual(receipt.receipt_closed, True)

        # Check if customer was updated
        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.points, 8000)


        #*** Test when payment is saved again customer's points wont be changed 
        receipt = Receipt.objects.filter(store=self.store).order_by('id')[1]
        receipt.perform_credit_payment_completed(
            [
                {
                    'payment_method_reg_no': self.points_pay_method.reg_no,
                    'amount': Decimal('2000.00')
                }
            ]
        )

        receipt = Receipt.objects.filter(store=self.store).order_by('id')[1]
        self.assertEqual(receipt.transaction_type, Receipt.LOYALTY_TRANS)
        self.assertEqual(receipt.payment_completed, True)
        self.assertEqual(receipt.receipt_closed, True)


        # Check if customer was updated
        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.points, 8000)

    def test_if_update_customer_points_method_will_work_for_employee_user(self):

        # Deletes all receipits, receiplines and products
        self.delete_previous_sale_data()

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.profile1)
        loyalty.value = 6
        loyalty.save()

        # Make sale
        self.create_sale_data(user=self.cashier_user)

        receipt = Receipt.objects.get(store=self.store)
        receipt.user = self.cashier_user
        receipt.save()

        customer = Customer.objects.get(name='Chris Evans')

        self.assertEqual(customer.points, 120)

    def test_create_receipt_count_method(self):
        """
        This method has been automatically tested by ReceiptCountTestCase 
        """

    def test_firebase_messages_are_sent_correctly(self):

        self.delete_previous_sale_data()
        empty_logfiles()

        #Create receipt
        self.create_sale_data(user=self.user1)

        receipt = Receipt.objects.get(store=self.store)

        content = get_test_firebase_sender_log_content(only_include=['receipt'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': '', 
                'relevant_stores': '[]', 
                'model': 'receipt', 
                'action_type': 'create', 
                'transaction_type': str(receipt.transaction_type),
                'payment_completed': str(receipt.payment_completed),
                'is_refund': str(receipt.is_refund),
                'local_reg_no': str(receipt.local_reg_no),
                'reg_no': str(receipt.reg_no),
                'payment_list': '[]',
                'receipt_lines': '[]'
            }
        }

        self.assertEqual(content[0], result)

        # Edit tax
        receipt = Receipt.objects.get(store=self.store)
        receipt.save()

        content = get_test_firebase_sender_log_content(only_include=['receipt'])
        self.assertEqual(len(content), 2)

        # Create receipt lines
        receipt_lines = receipt.receiptline_set.all().values(
            'product__name',
            'reg_no', 
            'refunded_units', 
            'units'
        )

        new_receipt_lines = [
            {
                'product_name': receipt_line['product__name'],
                'reg_no': receipt_line['reg_no'],
                'refunded_units': str(receipt_line['refunded_units']),
                'units': str(receipt_line['units'])
            } for receipt_line in receipt_lines
        ]

        result = {
            'tokens': [], 
            'payload': {
                'group_id': '', 
                'relevant_stores': '[]', 
                'model': 'receipt', 
                'action_type': 'edit', 
                'transaction_type': str(receipt.transaction_type),
                'payment_completed': str(receipt.payment_completed),
                'is_refund': str(receipt.is_refund),
                'local_reg_no': str(receipt.local_reg_no),
                'reg_no': str(receipt.reg_no),
                'payment_list': str(receipt.get_payment_list()),
                'receipt_lines': str(new_receipt_lines)
            }
        }

        self.assertEqual(content[1], result)


"""
=========================== ReceiptCount ===================================
"""  
# ReceiptCount
class ReceiptCountTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user1 = create_new_user('john')
        self.user2 = create_new_user('jack')
        
        self.profile1 = Profile.objects.get(user__email='john@gmail.com')
        self.profile2 = Profile.objects.get(user__email='jack@gmail.com')

        #Create a store
        self.store = create_new_store(self.profile1, 'Computer Store')

        #Create a tax
        self.tax = create_new_tax(self.profile1, self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile1, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.profile1, 'chris')

        # Create receipt1
        self.receipt = Receipt.objects.create(
            user=self.user1,
            store=self.store,
            customer=self.customer,
            discount_amount=401.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True
        )

        pay_method = StorePaymentMethod.objects.get(
            profile=self.profile1,
            payment_type=StorePaymentMethod.CASH_TYPE
        )
        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=pay_method,
            amount=2500
        )

    def create_receipt_for_user(self, user, store, local_reg_no):

        # Create receipt1
        Receipt.objects.create(
            user=user,
            store=store,
            customer=self.customer,
            discount=None,
            tax=self.tax,
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
            local_reg_no=local_reg_no,
            receipt_number="100-1000"
        )

    def test_ReceiptCount_fields_verbose_names(self):
        """
        Ensure all fields in ReceiptCount have the correct verbose names and can be
        found
        """        
        receipt_count = ReceiptCount.objects.get(user=self.user1)
        
        self.assertEqual(receipt_count._meta.get_field('subtotal_amount').verbose_name,'subtotal amount')
        self.assertEqual(receipt_count._meta.get_field('total_amount').verbose_name,'total amount')
        self.assertEqual(receipt_count._meta.get_field('discount_amount').verbose_name,'discount amount')
        self.assertEqual(receipt_count._meta.get_field('tax_amount').verbose_name,'tax amount')
        self.assertEqual(receipt_count._meta.get_field('transaction_type').verbose_name,'transaction type')
        self.assertEqual(receipt_count._meta.get_field('payment_completed').verbose_name,'payment completed')
        self.assertEqual(receipt_count._meta.get_field('is_refund').verbose_name,'refund completed')
        self.assertEqual(receipt_count._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(receipt_count._meta.get_field('created_date').verbose_name,'created date')
        
        fields = ([field.name for field in ReceiptCount._meta.fields])
        
        self.assertEqual(len(fields), 13)

    def test_ReceiptCount_existence(self):

        receipt_count = ReceiptCount.objects.get(user=self.user1)
        
        self.assertEqual(receipt_count.user, self.user1) 
        self.assertEqual(receipt_count.store, self.store) 
        self.assertEqual(receipt_count.customer, self.customer) 
        self.assertEqual(receipt_count.subtotal_amount, self.receipt.subtotal_amount)
        self.assertEqual(receipt_count.total_amount, self.receipt.total_amount) 
        self.assertEqual(receipt_count.discount_amount, self.receipt.discount_amount)
        self.assertEqual(receipt_count.tax_amount, self.receipt.tax_amount)
        self.assertEqual(receipt_count.transaction_type, self.receipt.transaction_type)
        self.assertEqual(receipt_count.payment_completed, self.receipt.payment_completed)
        self.assertEqual(receipt_count.is_refund, self.receipt.is_refund)
        self.assertEqual(receipt_count.reg_no, self.receipt.reg_no)

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 
        
        receipt_count = ReceiptCount.objects.get(user=self.user1)
             
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            receipt_count.get_created_date(self.user1.get_user_timezone()))
        )

    def test_if_ReceiptLineCount_wont_be_deleted_when_user_is_deleted(self):
        # Delete all profile
        Profile.objects.all().delete()
        
        # Confirm if the user has been deleted
        self.assertEqual(get_user_model().objects.all().count(), 0)
        
        # Confirm number of receipt counts
        self.assertEqual(ReceiptCount.objects.all().count(), 1)

    def test_if_ReceiptLineCount_wont_be_deleted_when_store_is_deleted(self):
        
        self.profile1.delete()
        
        # Confirm if the store has been deleted
        self.assertEqual(Store.objects.all().count(), 0)
        
        # Confirm number of receipt counts
        self.assertEqual(ReceiptCount.objects.all().count(), 1)

    def test_if_ReceiptLineCount_wont_be_deleted_when_customer_is_deleted(self):
        
        self.profile1.delete()
        
        # Confirm if the customer has been deleted
        self.assertEqual(Customer.objects.all().count(), 0)
        
        # Confirm number of receipt counts
        self.assertEqual(ReceiptCount.objects.all().count(), 1)

"""
=========================== ReceiptLine ===================================
"""
class ReceiptLineTestCase(TestCase):
    
    def setUp(self):

        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create stores
        self.store = create_new_store(self.profile, 'Computer Store')
        self.store2 = create_new_store(self.profile, 'Toy Store')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.profile, 'chris')

        # Create a product
        self.product = Product.objects.create(
            profile=self.profile,
            category=self.category,
            name="Shampoo",
            price=250,
            cost=100,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )

        # Create receipt1
        self.receipt = self.create_bare_receipt()

        # Create receipt line1
        self.receiptline =  ReceiptLine.objects.create(
            receipt=self.receipt,
            tax=self.tax,
            product=self.product,
            product_info={'name': self.product.name},
            price=1750,
            discount_amount=150,
            units=7
        )

        self.update_all_receipt_lines([self.receipt.receipt_number])

    def create_bare_receipt(self, receipt_number="100-1000"):

        receipt = Receipt.objects.create(
            user=self.user,
            store=self.store,
            customer=self.customer,
            discount_amount=401.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            created_date_timestamp=1634926712,
            receipt_number=receipt_number
        )

        pay_method = StorePaymentMethod.objects.get(
            profile=self.profile,
            payment_type=StorePaymentMethod.CASH_TYPE
        )
        ReceiptPayment.objects.create(
            receipt=receipt,
            payment_method=pay_method,
            amount=2500
        )

        return Receipt.objects.get(reg_no=receipt.reg_no)
    
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
    
    def test_receiptline_fields_verbose_names(self):

        receiptline = ReceiptLine.objects.get(receipt=self.receipt)
        
        self.assertEqual(receiptline._meta.get_field('product_info').verbose_name,'product info')
        self.assertEqual(receiptline._meta.get_field('modifier_options_info').verbose_name,'modifier options info')
        self.assertEqual(receiptline._meta.get_field('price').verbose_name,'price')
        self.assertEqual(receiptline._meta.get_field('cost').verbose_name,'cost')
        self.assertEqual(receiptline._meta.get_field('discount_amount').verbose_name,'discount amount')
        self.assertEqual(receiptline._meta.get_field('is_variant').verbose_name,'is variant')
        self.assertEqual(receiptline._meta.get_field('sold_by_each').verbose_name,'sold by each')
        self.assertEqual(receiptline._meta.get_field('units').verbose_name,'units')
        self.assertEqual(receiptline._meta.get_field('refunded_units').verbose_name,'refunded units')
        self.assertEqual(receiptline._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(receiptline._meta.get_field('created_date').verbose_name,'created date')
        self.assertEqual(receiptline._meta.get_field('user_reg_no').verbose_name,'user reg no')
        self.assertEqual(receiptline._meta.get_field('store_reg_no').verbose_name,'store reg no')
        self.assertEqual(receiptline._meta.get_field('product_name').verbose_name,'product name')
        self.assertEqual(receiptline._meta.get_field('category_name').verbose_name,'category name')
        self.assertEqual(receiptline._meta.get_field('user_name').verbose_name,'user name')
        self.assertEqual(receiptline._meta.get_field('tax_name').verbose_name,'tax name')
        self.assertEqual(receiptline._meta.get_field('tax_rate').verbose_name,'tax rate')
        self.assertEqual(receiptline._meta.get_field('receipt_number').verbose_name,'receipt number')
        self.assertEqual(receiptline._meta.get_field('refund_for_receipt_number').verbose_name,'refund for receipt number')
       
        fields = ([field.name for field in ReceiptLine._meta.fields])
        
        self.assertEqual(len(fields), 33)

    def test_receiptline_fields_after_it_has_been_created(self):
        """
        ReceiptLine fields
        
        Ensure a receiptline has the right fields after it has been created
        """
        receiptline = ReceiptLine.objects.get(receipt=self.receipt)
        
        self.assertEqual(receiptline.user, self.user)
        self.assertEqual(receiptline.receipt, self.receipt)
        self.assertEqual(receiptline.store, self.store)
        self.assertEqual(receiptline.tax, self.tax)
        self.assertEqual(receiptline.parent_product, None)
        self.assertEqual(receiptline.product, self.product)
        self.assertEqual(receiptline.product_info, {
            'name': self.product.name,
            'reg_no': self.product.reg_no,
            'loyverse_variant_id': str(self.product.loyverse_variant_id)
        })
        self.assertEqual(receiptline.modifier_options.all().count(), 0)
        self.assertEqual(receiptline.modifier_options_info, [])
        self.assertEqual(receiptline.customer, self.customer)
        self.assertEqual(receiptline.price, 1750.00)
        self.assertEqual(receiptline.cost, self.product.cost * 7)
        self.assertEqual(receiptline.discount_amount, 150.00)
        self.assertEqual(receiptline.is_variant, False)
        self.assertEqual(receiptline.sold_by_each, True)
        self.assertEqual(receiptline.units, 7)
        self.assertTrue(receiptline.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receiptline.created_date).strftime("%B, %d, %Y"), 'October, 22, 2021')
        
        self.assertEqual(receiptline.user_reg_no, self.user.reg_no)
        self.assertEqual(receiptline.store_reg_no, self.store.reg_no)
        self.assertEqual(receiptline.product_name, self.product.name)
        self.assertEqual(receiptline.category_name, self.category.name)
        self.assertEqual(receiptline.user_name, self.user.get_full_name())
        self.assertEqual(receiptline.tax_name, self.tax.name)
        self.assertEqual(
            receiptline.tax_rate, 
            round(Decimal(self.tax.rate), 2)
        )
        self.assertEqual(receiptline.receipt_number, self.receipt.receipt_number)
        self.assertEqual(
            receiptline.refund_for_receipt_number, 
            self.receipt.refund_for_receipt_number
        )

    def test_if_receipline_product_can_be_none(self):
        
        receiptline = ReceiptLine.objects.get(receipt=self.receipt)
        receiptline.product = None
        receiptline.save()

        receiptline = ReceiptLine.objects.get(receipt=self.receipt)
        self.assertEqual(receiptline.product, None)

    def test_receiptline_fields_after_it_has_been_created_with_a_variant_product(self):

        product1 = Product.objects.get(name="Shampoo")
        self.assertEqual(product1.variant_count, 0)

        # Add variant to product
        product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
        product2.stores.add(self.store)

        variant = ProductVariant.objects.create(product_variant=product2)
        
        product1.variants.add(variant)


        # Create receipt1
        receipt = self.create_bare_receipt(receipt_number="100-1001")

        # Create receipt line1
        receiptline =  ReceiptLine.objects.create(
            receipt=receipt,
            tax=self.tax,
            parent_product=self.product,
            product=product2,
            product_info= {'name': f'{self.product.name} ({product2.name})'},
            price=1750,
            discount_amount=150,
            is_variant= True,
            units=7,
        )

        self.update_all_receipt_lines([receipt.receipt_number])

        receiptline = ReceiptLine.objects.get(receipt=receipt)

        self.assertEqual(receiptline.user, self.user)
        self.assertEqual(receiptline.receipt, receipt)
        self.assertEqual(receiptline.store, self.store)
        self.assertEqual(receiptline.tax, self.tax)
        self.assertEqual(receiptline.parent_product, self.product)
        self.assertEqual(receiptline.product, product2)
        self.assertEqual(
            receiptline.product_info, 
            {
                'name': product2.name,
                'reg_no': product2.reg_no,
                'loyverse_variant_id': str(product2.loyverse_variant_id)
            }
        )
        self.assertEqual(receiptline.modifier_options.all().count(), 0)
        self.assertEqual(receiptline.modifier_options_info, [])
        self.assertEqual(receiptline.customer, self.customer)
        self.assertEqual(receiptline.price, 1750.00)
        self.assertEqual(receiptline.discount_amount, 150.00)
        self.assertEqual(receiptline.is_variant, True)
        self.assertEqual(receiptline.sold_by_each, True)
        self.assertEqual(receiptline.units, 7)
        self.assertTrue(receiptline.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receiptline.created_date).strftime("%B, %d, %Y"), 'October, 22, 2021')
 
    def test_if_update_product_wont_error_out_when_product_has_no_stock_level_model(self):

        old_receipt_str = Receipt.objects.get().__str__()
        old_receipt_line = ReceiptLine.objects.get()

        StockLevel.objects.all().delete()
        self.assertEqual(StockLevel.objects.all().count(), 0)

        # Delete all receipts
        deleted_receipt_reg_no = self.receipt.reg_no
        Receipt.objects.all().delete()

        # Update track stock
        self.product.track_stock = True
        self.product.save()

        self.assertEqual(
            Product.objects.get(profile=self.profile).track_stock, True)


        # Make sale
        # Create receipt1
        receipt = self.create_bare_receipt(receipt_number="100-1001")

        # Create receipt line1
        ReceiptLine.objects.create(
            receipt=receipt,
            product=self.product,
            product_info = {'name': self.product.name},
            price=1750,
            discount_amount=150,
            units=7
        )

        self.update_all_receipt_lines([receipt.receipt_number])

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.all().count(), 0)

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store).order_by('id')
        self.assertEqual(historys.count(), 1)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].store, self.store)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[0].change_source_reg_no, deleted_receipt_reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Sale')
        self.assertEqual(historys[0].change_source_name, old_receipt_str)
        self.assertEqual(historys[0].line_source_reg_no, old_receipt_line.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('-7.00'))
        self.assertEqual(historys[0].stock_after, Decimal('-7.00'))

    def test_if_update_product_stock_units_method_will_update_stock_level_units(self):

        old_receipt_str = Receipt.objects.get().__str__()
        old_receipt_line = ReceiptLine.objects.get()

        stock_level = StockLevel.objects.get(product=self.product, store=self.store)
        stock_level.units = 100
        stock_level.save()

        # Delete all receipts
        deleted_receipt_reg_no = self.receipt.reg_no
        Receipt.objects.all().delete()

        # Update track stock
        self.product.track_stock = True
        self.product.save()

        self.assertEqual(
            Product.objects.get(profile=self.profile).track_stock, True)


        # Make sale
        # Create receipt1
        receipt = self.create_bare_receipt(receipt_number="100-1001")

        # Create receipt line1
        receipt_line = ReceiptLine.objects.create(
            receipt=receipt,
            product=self.product,
            product_info = {'name': self.product.name},
            price=1750,
            discount_amount=150,
            units=7
        )
        self.update_all_receipt_lines([receipt.receipt_number])

        # Confirm stock level units
        self.assertEqual(
            StockLevel.objects.get(product=self.product, store=self.store).units, 
            93
        )

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store).order_by('id')

        self.assertEqual(historys.count(), 2)
        
        # Inventory history 1
        self.assertEqual(historys[0].user, self.user)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].store, self.store)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[0].change_source_reg_no, deleted_receipt_reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Sale')
        self.assertEqual(historys[0].change_source_name, old_receipt_str)
        self.assertEqual(historys[0].line_source_reg_no, old_receipt_line.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('-7.00'))
        self.assertEqual(historys[0].stock_after, Decimal('-7.00'))
        self.assertEqual(
            (historys[0].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user)
        self.assertEqual(historys[1].product, self.product)
        self.assertEqual(historys[1].store, self.store)
        self.assertEqual(historys[1].product, self.product)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[1].change_source_reg_no, receipt.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Sale')
        self.assertEqual(historys[1].change_source_name, receipt.__str__())
        self.assertEqual(historys[1].line_source_reg_no, receipt_line.reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('-7.00'))
        self.assertEqual(historys[1].stock_after, Decimal('-14.00'))
        self.assertEqual(
            (historys[1].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

    def test_if_update_product_stock_units_method_will_update_stock_level_units_to_negative(self):

        old_receipt_str = Receipt.objects.get().__str__()
        old_receipt_line = ReceiptLine.objects.get()

        stock_level = StockLevel.objects.get(product=self.product, store=self.store)
        stock_level.units = 0
        stock_level.save()

        # Delete all receipts
        deleted_receipt_reg_no = self.receipt.reg_no
        Receipt.objects.all()

        # Update track stock
        self.product.track_stock = True
        self.product.save()

        self.assertEqual(
            Product.objects.get(profile=self.profile).track_stock, True)

        # Make sale
        # Create receipt1
        receipt = self.create_bare_receipt(receipt_number="100-1001")

        # Create receipt line1
        receipt_line = ReceiptLine.objects.create(
            receipt=receipt,
            product=self.product,
            product_info = {'name': self.product.name},
            price=1750,
            discount_amount=150,
            units=7
        )

        self.update_all_receipt_lines([receipt.receipt_number])

        # Confirm stock level units
        self.assertEqual(
            StockLevel.objects.get(product=self.product, store=self.store).units, 
            -7
        )

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store).order_by('id')

        self.assertEqual(historys.count(), 2)
        
        # Inventory history 1
        self.assertEqual(historys[0].user, self.user)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].store, self.store)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[0].change_source_reg_no, deleted_receipt_reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Sale')
        self.assertEqual(historys[0].change_source_name, old_receipt_str)
        self.assertEqual(historys[0].line_source_reg_no, old_receipt_line.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('-7.00'))
        self.assertEqual(historys[0].stock_after, Decimal('-7.00'))
        self.assertEqual(
            (historys[0].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user)
        self.assertEqual(historys[1].product, self.product)
        self.assertEqual(historys[1].store, self.store)
        self.assertEqual(historys[1].product, self.product)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[1].change_source_reg_no, receipt.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Sale')
        self.assertEqual(historys[1].change_source_name, receipt.__str__())
        self.assertEqual(historys[1].line_source_reg_no, receipt_line.reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('-7.00'))
        self.assertEqual(historys[1].stock_after, Decimal('-14.00'))
        self.assertEqual(
            (historys[1].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

    def test_if_update_product_stock_units_method_will_update_bundled_product_stock_level_units(self):

        old_receipt_str = Receipt.objects.get().__str__()
        old_receipt_line = ReceiptLine.objects.get()

        product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )

        product2.stores.add(self.store)

        # Update stock levels for products
        stock_level = StockLevel.objects.get(product=self.product, store=self.store)
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(product=product2, store=self.store)
        stock_level.units = 160
        stock_level.save()

        # Delete all receipts
        deleted_receipt_reg_no = self.receipt.reg_no
        Receipt.objects.all()

        # Update track stock for products
        self.product.track_stock = True
        self.product.save()

        self.assertEqual(
            Product.objects.get(reg_no=self.product.reg_no).track_stock,True)

        product2.track_stock = True
        product2.save()

        self.assertEqual(
            Product.objects.get(reg_no=product2.reg_no).track_stock,True)


        # Create master product with 2 bundles
        shampoo_bundle = ProductBundle.objects.create(
            product_bundle=self.product,
            quantity=30
        )

        conditoner_bundle = ProductBundle.objects.create(
            product_bundle=product2,
            quantity=25
        )

        master_product = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Hair Bundle",
            price=35000,
            cost=30000,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
        master_product.bundles.add(shampoo_bundle, conditoner_bundle)
        master_product.stores.add(self.store)


        # Make sale
        # Create receipt1
        receipt = self.create_bare_receipt(receipt_number="100-1001")

        # Create receipt line1
        receipt_line = ReceiptLine.objects.create(
            receipt=receipt,
            product=master_product,
            product_info = {'name': self.product.name},
            price=1750,
            discount_amount=150,
            units=2
        )

        self.update_all_receipt_lines([receipt.receipt_number])

        # Make sure master product's bundled products stock levels was updated
        bundled_product1 = Product.objects.get(name="Shampoo")

        self.assertEqual(
            StockLevel.objects.get(product=bundled_product1, store=self.store).units, 
            100
        )

        bundled_product2 = Product.objects.get(name="Conditioner")

        self.assertEqual(
            StockLevel.objects.get(product=bundled_product2, store=self.store).units, 
            160
        )


        # Make sure master product's stock level was not updated
        master_product = Product.objects.get(name="Hair Bundle")

        self.assertEqual(
            StockLevel.objects.get(product=master_product, store=self.store).units, 
            -2
        )


        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store).order_by('id')

        self.assertEqual(historys.count(), 2)
        
        # Inventory history 1
        self.assertEqual(historys[0].user, self.user)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].store, self.store)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[0].change_source_reg_no, deleted_receipt_reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Sale')
        self.assertEqual(historys[0].change_source_name, old_receipt_str)
        self.assertEqual(historys[0].line_source_reg_no, old_receipt_line.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('-7.00'))
        self.assertEqual(historys[0].stock_after, Decimal('-7.00'))
        self.assertEqual(
            (historys[0].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user)
        self.assertEqual(historys[1].product, master_product)
        self.assertEqual(historys[1].store, self.store)
        self.assertEqual(historys[1].product, master_product)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[1].change_source_reg_no, receipt.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Sale')
        self.assertEqual(historys[1].change_source_name, receipt.__str__())
        self.assertEqual(historys[1].line_source_reg_no, receipt_line.reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('-2.00'))
        self.assertEqual(historys[1].stock_after, Decimal('-2.00'))
        self.assertEqual(
            (historys[1].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

    def test_if_update_product_stock_units_method_will_update_a_single_stock_level_model(self):

        self.product.stores.add(self.store, self.store2)

        self.assertEqual(StockLevel.objects.filter(product=self.product).count(), 2)

        stock_levels = StockLevel.objects.filter(product=self.product)

        for stock_level in stock_levels:
            stock_level.units = 100
            stock_level.save()

        # Delete all receipts
        Receipt.objects.all()

        # Update track stock
        self.product.track_stock = True
        self.product.save()

        self.assertEqual(
            Product.objects.get(profile=self.profile).track_stock, True)


        # Make sale
        # Create receipt1
        receipt = self.create_bare_receipt(receipt_number="100-1001")
        
        # Create receipt line1
        ReceiptLine.objects.create(
            receipt=receipt,
            product=self.product,
            product_info = {'name': self.product.name},
            price=1750,
            discount_amount=150,
            units=7
        )

        self.update_all_receipt_lines([receipt.receipt_number])
        
        # Confirm only stock level for store 1 was updated
        self.assertEqual(StockLevel.objects.get(
            store=self.store, product=self.product).units, 93
        )
        self.assertEqual(StockLevel.objects.get(
            store=self.store2, product=self.product).units, 100
        )
    
    def test__str__method(self):
        receiptline = ReceiptLine.objects.get(receipt=self.receipt)
        self.assertEqual(receiptline.__str__(), f'(ReceiptLine) {receiptline.receipt_number}')

    def test_get_name_method(self):
        receiptline = ReceiptLine.objects.get(receipt=self.receipt)
        self.assertEqual(receiptline.get_name(), f'(ReceiptLine) {receiptline.receipt_number}')

    def test_get_profile_method(self):
        receiptline = ReceiptLine.objects.get(receipt=self.receipt)
        self.assertEqual(receiptline.get_profile(), self.profile)

    def test_get_receiptline_maker_method(self):
        receiptline = ReceiptLine.objects.get(receipt=self.receipt)
        self.assertEqual(receiptline.get_receiptline_maker(), self.user.get_full_name())

    def test_get_receiptline_maker_desc_method(self):
        receiptline = ReceiptLine.objects.get(receipt=self.receipt)
        self.assertEqual(receiptline.get_receiptline_maker_desc(), "Made by: {}".format(self.user.get_full_name()))

    def get_units(self):
        return self.units
    
    def get_units_desc(self):
        return "Units: {}".format(self.units)

    def get_price_and_currency(self):
        return f"{CURRENCY_CHOICES[self.product.get_currency()][1]} {self.price}"

    def get_price_and_currency_desc(self):
        return f"Price: {CURRENCY_CHOICES[self.product.get_currency()][1]} {self.price}"

    def test_get_units_method(self):
        receiptline = ReceiptLine.objects.get(receipt=self.receipt)
        self.assertEqual(receiptline.get_units(), 7)

    def test_get_units_desc_method(self):
        receiptline = ReceiptLine.objects.get(receipt=self.receipt)
        self.assertEqual(receiptline.get_units_desc(), "Units: 7.00")

    def test_get_price_and_currency_method(self):
        receiptline = ReceiptLine.objects.get(receipt=self.receipt)
        self.assertEqual(receiptline.get_price_and_currency(), "Usd 1750.00")

    def test_get_price_and_currency_desc_method(self):
        receiptline = ReceiptLine.objects.get(receipt=self.receipt)
        self.assertEqual(receiptline.get_price_and_currency_desc(), "Price: Usd 1750.00")

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 
        
        receiptline = ReceiptLine.objects.get(receipt=self.receipt)

        # Check if get_created_date is correct
        self.assertEqual(
            receiptline.get_created_date(self.user.get_user_timezone()),
            'October, 22, 2021, 09:18:PM'
        )

    def test_create_receiptline_count_method(self):
        """
        This method has been automatically tested by ReceiptLineCountTestCase 
    
        """

"""
=========================== ReceiptLineCount ===================================
"""  
# ReceiptLineCount
class ReceiptLineCountTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store = create_new_store(self.profile, 'Computer Store')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.profile, 'chris',)

        # Create a product
        self.product = Product.objects.create(
            profile=self.profile,
            category=self.category,
            name="Shampoo",
            price=250,
            cost=100,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )

        # Create receipt1
        self.receipt = Receipt.objects.create(
            user=self.user,
            store=self.store,
            customer=self.customer,
            discount_amount=401.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            receipt_number='100-1000'
        )

        pay_method = StorePaymentMethod.objects.get(
            profile=self.profile,
            payment_type=StorePaymentMethod.CASH_TYPE
        )
        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=pay_method,
            amount=2500
        )

        # Create receipt line1
        self.receiptline =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=self.product,
            product_info = {'name': self.product.name},
            price=1750,
            discount_amount=150,
            units=7
        )
        
    def test_ReceiptLineCount_fields_verbose_names(self):
        """
        Ensure all fields in ReceiptLineCount have the correct verbose names and can be
        found
        """        
        receiptline_count = ReceiptLineCount.objects.get(user=self.user)

        self.assertEqual(receiptline_count._meta.get_field('price').verbose_name,'price')
        self.assertEqual(receiptline_count._meta.get_field('discount_amount').verbose_name,'discount amount')
        self.assertEqual(receiptline_count._meta.get_field('units').verbose_name,'units')
        self.assertEqual(receiptline_count._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(receiptline_count._meta.get_field('created_date').verbose_name,'created date')
        
        fields = ([field.name for field in ReceiptLineCount._meta.fields])
        
        self.assertEqual(len(fields), 10)

    def test_ReceiptLineCount_existence(self):

        receiptline_count = ReceiptLineCount.objects.get(user=self.user)
        
        self.assertEqual(receiptline_count.user, self.user) 
        self.assertEqual(receiptline_count.store, self.store) 
        self.assertEqual(receiptline_count.product, self.product)
        self.assertEqual(receiptline_count.customer, self.customer)
        self.assertEqual(receiptline_count.price, 1750)
        self.assertEqual(receiptline_count.discount_amount, 150)
        self.assertEqual(receiptline_count.units, 7)
        self.assertEqual(receiptline_count.reg_no, self.receiptline.reg_no)

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 
        
        receiptline_count = ReceiptLineCount.objects.get(user=self.user)
             
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            receiptline_count.get_created_date(self.user.get_user_timezone()))
        )

    def test_if_ReceiptLineCount_wont_be_deleted_when_user_is_deleted(self):
        
        self.profile.delete()
        
        # Confirm if the user has been deleted
        self.assertEqual(get_user_model().objects.all().count(), 0)
        
        # Confirm number of sale counts
        self.assertEqual(ReceiptLineCount.objects.all().count(), 1)

    def test_if_ReceiptLineCount_wont_be_deleted_when_store_is_deleted(self):
        
        self.profile.delete()
        
        # Confirm if the store has been deleted
        self.assertEqual(Store.objects.all().count(), 0)
        
        # Confirm number of sale counts
        self.assertEqual(ReceiptLineCount.objects.all().count(), 1)

    def test_if_ReceiptLineCount_wont_be_deleted_when_product_is_deleted(self):
        
        self.profile.delete()
        
        # Confirm if the product has been deleted
        self.assertEqual(Product.objects.all().count(), 0)
        
        # Confirm number of sale counts
        self.assertEqual(ReceiptLineCount.objects.all().count(), 1)

    def test_if_ReceiptLineCount_wont_be_deleted_when_customer_is_deleted(self):
        
        self.profile.delete()
        
        # Confirm if the customer has been deleted
        self.assertEqual(Customer.objects.all().count(), 0)
        
        # Confirm number of sale counts
        self.assertEqual(ReceiptLineCount.objects.all().count(), 1)


"""
=========================== CustomerDebt ===================================
"""
class CustomerDebtTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store = create_new_store(self.profile, 'Computer Store')

        # Create a cashier user
        self.cashier_user = create_new_cashier_user(
            "kate", self.profile, self.store
        )

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.profile, 'chris')

        # Creates products
        self.product = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
        self.product.stores.add(self.store)

        self.product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
        self.product2.stores.add(self.store)

    
    def create_sale_data(
        self, 
        user,
        receipt_number='100-1000',
        subtotal_amount=2000):


        customer = Customer.objects.get(name='Chris Evans')

        # Create receipt1
        self.receipt = Receipt.objects.create(
            user=user,
            store=self.store,
            customer=customer,
            customer_info={
                'name': customer.name, 
                'reg_no': customer.reg_no
            },
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=subtotal_amount,
            total_amount=1599.00,
            transaction_type=Receipt.DEBT_TRANS,
            payment_completed=False,
            receipt_number=receipt_number
        )

        pay_method = StorePaymentMethod.objects.get(
            profile=self.profile,
            payment_type=StorePaymentMethod.DEBT_TYPE
        )
        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=pay_method,
            amount=2500
        )

        # Create receipt line1
        self.receiptline1 =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=self.product,
            product_info={'name': self.product.name},
            price=1750,
            units=7
        )
    
        # Create receipt line2
        self.receiptline2 =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=self.product2,
            product_info={'name': self.product2.name},
            price=2500,
            units=10
        )

        return self.receipt

    def test_customer_debt_fields_verbose_names(self):

        self.create_sale_data(user=self.user)

        receipt = Receipt.objects.get(store=self.store)

        cd = CustomerDebt.objects.get(receipt=receipt)
        
        self.assertEqual(cd._meta.get_field('debt').verbose_name,'debt')
        self.assertEqual(cd._meta.get_field('reg_no').verbose_name, 'reg no')
        self.assertEqual(cd._meta.get_field('created_date').verbose_name, 'created date')

        fields = ([field.name for field in CustomerDebt._meta.fields])
        
        self.assertEqual(len(fields), 6)

    def test_customer_debt_fields_after_it_has_been_created(self):

        self.create_sale_data(user=self.user)

        receipt = Receipt.objects.get(store=self.store)

        cd = CustomerDebt.objects.get(receipt=receipt)

        self.assertEqual(cd.customer, self.customer)
        self.assertEqual(cd.receipt, receipt)
        self.assertEqual(cd.debt, receipt.subtotal_amount)
        self.assertTrue(cd.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual(cd.created_date, receipt.created_date)

    def test_if_customer_debt_creation_n_delete_will_add_up_customer_current_debt_field(self):

        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.current_debt, 0)

        self.create_sale_data(user=self.user)

        receipt = Receipt.objects.get(store=self.store)

        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.current_debt, receipt.subtotal_amount)


        # **** Delete customer debt
        CustomerDebt.objects.filter(receipt=receipt).delete()

        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.current_debt, 0)

    def test_if_multiple_customer_debt_creation_n_delete_will_add_up_customer_current_debt_field(self):
        
        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.current_debt, 0)

        r1 = self.create_sale_data(
            user=self.user, 
            receipt_number='100-1001',
            subtotal_amount=2000.00
        )
        r2 = self.create_sale_data(
            user=self.user, 
            receipt_number='100-1002',
            subtotal_amount=2700.05
        )
        r3 = self.create_sale_data(
            user=self.user, 
            receipt_number='100-1003',
            subtotal_amount=3000.02
        )
    
        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.current_debt, Decimal('7700.07'))

        # Delete receipt 1
        CustomerDebt.objects.filter(receipt=r1).delete()

        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.current_debt, Decimal('5700.07'))

        # Delete receipt 2
        CustomerDebt.objects.filter(receipt=r2).delete()

        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.current_debt, Decimal('3000.02'))

        # Delete receipt 3
        CustomerDebt.objects.filter(receipt=r3).delete()

        customer = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer.current_debt, Decimal('0.00'))

    def test_if_customer_debt_creation_n_delete_updates_right_customer(self):

        # Create another customer user
        create_new_customer(self.profile, 'alex')

        customer1 = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer1.current_debt, 0)

        customer2 = Customer.objects.get(name='Alex Alexo')
        self.assertEqual(customer2.current_debt, 0)


        self.create_sale_data(user=self.user, receipt_number='100-1001')

        receipt = Receipt.objects.get(store=self.store)

        customer1 = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer1.current_debt, receipt.subtotal_amount)

        customer2 = Customer.objects.get(name='Alex Alexo')
        self.assertEqual(customer2.current_debt, 0)


        # **** Delete customer debt
        CustomerDebt.objects.filter(receipt=receipt).delete()

        customer1 = Customer.objects.get(name='Chris Evans')
        self.assertEqual(customer1.current_debt, 0)

        customer2 = Customer.objects.get(name='Alex Alexo')
        self.assertEqual(customer2.current_debt, 0)

    def test_create_customer_debt_count_method(self):
        """
        This method has been automatically tested by CustomerDebtCountTestCase 
        """
      
"""
=========================== ProductCount ===================================
"""  
# ProductCount
class ProductCountTestCase(TestCase):

    def setUp(self):
        
        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store = create_new_store(self.profile, 'Computer Store')

        # Create a cashier user
        self.cashier_user = create_new_cashier_user(
            "kate", self.profile, self.store
        )

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.profile, 'chris')

        # Creates products
        self.product = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )
        self.product.stores.add(self.store)

        self.product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )
        self.product2.stores.add(self.store)

        self.create_sale_data(user=self.user)

    def create_sale_data(
        self, 
        user,
        subtotal_amount=2000):
        
        customer = Customer.objects.get(name='Chris Evans')

        # Create receipt1
        self.receipt = Receipt.objects.create(
            user=user,
            store=self.store,
            customer=customer,
            customer_info={
                'name': customer.name, 
                'reg_no': customer.reg_no
            },
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=subtotal_amount,
            total_amount=1599.00,
            transaction_type=Receipt.DEBT_TRANS,
            payment_completed=False
        )

        pay_method = StorePaymentMethod.objects.get(
            profile=self.profile,
            payment_type=StorePaymentMethod.DEBT_TYPE
        )
        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=pay_method,
            amount=2500
        )

        # Create receipt line1
        self.receiptline1 =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=self.product,
            product_info={'name': self.product.name},
            price=1750,
            units=7
        )
    
        # Create receipt line2
        self.receiptline2 =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=self.product2,
            product_info={'name': self.product2.name},
            price=2500,
            units=10
        )

        return self.receipt

    def test_ProductCount_fields_verbose_names(self):
        """
        Ensure all fields in ProductCount have the correct verbose names and can be
        found
        """    
  
        cdc = CustomerDebtCount.objects.get(customer=self.customer)
        
        self.assertEqual(cdc._meta.get_field('debt').verbose_name,'debt')
        self.assertEqual(cdc._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(cdc._meta.get_field('created_date').verbose_name,'created date')
        
        fields = ([field.name for field in CustomerDebtCount._meta.fields])
        
        self.assertEqual(len(fields), 6)

    def test_CustomerDebtCount_existence(self):
        
        cdc = CustomerDebtCount.objects.get(customer=self.customer)

        self.assertEqual(cdc.customer, self.customer) 
        self.assertEqual(cdc.receipt, self.receipt)
        self.assertEqual(cdc.debt, self.receipt.subtotal_amount) 
        self.assertEqual(cdc.reg_no, self.receipt.reg_no)
     
    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 
        
        cdc = CustomerDebtCount.objects.get(customer=self.customer)
             
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            cdc.get_created_date(self.user.get_user_timezone()))
        )

    def test_if_ProductCount_wont_be_deleted_when_customer_is_deleted(self):
        
        self.customer.delete()
        
        # Confirm if the customer has been deleted
        self.assertEqual(Customer.objects.all().count(), 0)
        
        # Confirm number of customer debt count counts
        self.assertEqual(CustomerDebtCount.objects.all().count(), 1)

    def test_if_CustomerDebtCount_wont_be_deleted_when_receipt_is_deleted(self):
        
        self.receipt.delete()
        
        # Confirm if the receipt has been deleted
        self.assertEqual(Receipt.objects.all().count(), 0)
        
        # Confirm number of customer debt count counts
        self.assertEqual(CustomerDebtCount.objects.all().count(), 1)
