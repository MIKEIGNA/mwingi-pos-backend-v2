import copy
import datetime
from decimal import Decimal
from accounts.tasks import receipt_change_stock_tasks
from core.test_utils.create_user import create_new_user
from core.test_utils.custom_testcase import TestCase
from core.test_utils.log_reader import get_test_firebase_sender_log_content
from core.test_utils.loyverse_data.loyverse_test_data import LOYVERSE_RECEIPT_WEBHOOK_UPDATE_DATA6
from core.time_utils.date_helpers import DateHelperMethods
from inventories.models import StockLevel
from loyverse.utils.loyverse_receipts_creator import LoyverseReceiptSync
from products.models import Product
from profiles.models import Customer, Profile
from sales.models import Receipt, ReceiptCount, ReceiptLine
from stores.models import Store, Tax
from django.utils import timezone
from django.contrib.auth import get_user_model

class LoyverseReceiptSyncTestCase(TestCase):

    def setUp(self):

        # Loyverse ids that will be used during testing
        self.employee_id = '330a125a-71a9-11ea-8d93-0603130a05b8'
        self.store_id = '89a5aa2b-78f6-416f-acf3-c28d5266a636'
        self.customer_id = '9ec86d1c-cad9-4886-8d9b-b799d9a71bff'
        
        #Create a user with email john@gmail.com
        self.user = create_new_user('john')
        self.profile = Profile.objects.get(user=self.user)

        ReceiptCount.objects.create()

        # We use deepcopy so that we dont edit the global source
        self.receipts_data = copy.deepcopy(
            LOYVERSE_RECEIPT_WEBHOOK_UPDATE_DATA6['receipts']
        )
        
        # Input a similar employee id and store id to the user and to all receipts
        for data in self.receipts_data: 
            data['employee_id'] = self.employee_id
            data['store_id'] = self.store_id
            data['customer_id'] = self.customer_id

        self.user.loyverse_employee_id = self.employee_id
        self.user.save()

        # Create store
        self.store = Store.objects.create(
            profile=self.profile,
            name="Kawai",
            address="Nairobi",
            loyverse_store_id=self.store_id
        )

        # Create customer
        self.customer = Customer.objects.create(
            profile=self.profile,
            name='Customer Test',
            email='test@gmail.com',
            phone=423456768788,
            customer_code='gggg',
            loyverse_customer_id=self.customer_id
        )

        # Create products
        self.create_test_products()
        
    def create_test_products(self):

        product_variant_ids = []
        taxes_ids = []
        for receipt in self.receipts_data:
            for item in receipt['line_items']:
                # Collect varaint ids
                variant_id = item['variant_id']

                if not variant_id in product_variant_ids:
                    product_variant_ids.append(variant_id)

                # Collect tax ids
                line_taxes = item['line_taxes']
                if line_taxes:
                    tax_id = item['line_taxes'][0]['id']

                    if not tax_id in taxes_ids:
                        taxes_ids.append(tax_id)

        # Create products
        self.products = []
        for count, variant_id in enumerate(product_variant_ids):
            product = Product.objects.create(
                profile=self.profile,
                name=f'Product{count}',
                sku=f'Product{count}',
                barcode=f'barcode{count}',
                loyverse_variant_id=variant_id,
                price=1000+count, # This creates a unique price for each product
                cost=700+count, # This creates a unique cost for each product
            )

            self.products.append(product)

        # Create taxes
        self.taxes = []
        for count, tax_id in enumerate(taxes_ids):
            tax = Tax.objects.create(
                profile=self.profile,
                name=f'Tax{count}',
                rate=count,
                loyverse_tax_id=tax_id
            )

            self.taxes.append(tax)

    def create_receipts(self, receipts):
        LoyverseReceiptSync(profile=self.profile, receipts=receipts).sync_receipts()
        # Force run receipt_change_stock_tasks
        receipt_change_stock_tasks(ignore_dates=True)
    '''
    
    def test_when_receipt_is_created_or_saved_mwingi_connector_is_notified(self):

        self.create_receipts(self.receipts_data)
        receipts = Receipt.objects.all().order_by('-id')
        self.assertEqual(receipts.count(), 4)

        content = get_test_firebase_sender_log_content(only_include=['connector_receipt'])
        self.assertEqual(len(content), 4)

        self.assertEqual(
            content[0], 
            {'payload': {'model': 'connector_receipt', 'payload': f'{receipts[3].reg_no} payload data'}}
        )
        self.assertEqual(
            content[1], 
            {'payload': {'model': 'connector_receipt', 'payload': f'{receipts[2].reg_no} payload data'}}
        )
        self.assertEqual(
            content[2], 
            {'payload': {'model': 'connector_receipt', 'payload': f'{receipts[1].reg_no} payload data'}}
        )
        self.assertEqual(
            content[3], 
            {'payload': {'model': 'connector_receipt', 'payload': f'{receipts[0].reg_no} payload data'}}
        )

        # Test when receipt is saved
        for receipt in receipts: receipt.save()

        content = get_test_firebase_sender_log_content(only_include=['connector_receipt'])
        self.assertEqual(len(content), 4)

        self.assertEqual(
            content[0], 
            {'payload': {'model': 'connector_receipt', 'payload': f'{receipts[3].reg_no} payload data'}}
        )
        self.assertEqual(
            content[1], 
            {'payload': {'model': 'connector_receipt', 'payload': f'{receipts[2].reg_no} payload data'}}
        )
        self.assertEqual(
            content[2], 
            {'payload': {'model': 'connector_receipt', 'payload': f'{receipts[1].reg_no} payload data'}}
        )
        self.assertEqual(
            content[3], 
            {'payload': {'model': 'connector_receipt', 'payload': f'{receipts[0].reg_no} payload data'}}
        )
    
    def test_if_duplicates_cannot_be_created(self):

        self.create_receipts(self.receipts_data)
        self.create_receipts(self.receipts_data)

        receipts = Receipt.objects.all().order_by('-id')
        self.assertEqual(receipts.count(), 4)
    
    def test_if_receipts_are_created_correctly(self):

        self.create_receipts(self.receipts_data)
     
        receipts = Receipt.objects.all().order_by('-id')
        self.assertEqual(receipts.count(), 4)

        ########## Receipt 1
        receipt1 = receipts[0]

        self.assertEqual(receipt1.user, self.user)
        self.assertEqual(receipt1.store, self.store)
        self.assertEqual(receipt1.customer, self.customer)
        self.assertEqual(receipt1.customer_info, {
                'name': self.customer.name, 
                'email': self.customer.email,
                'phone': self.customer.phone,
                'tax_pin': self.customer.tax_pin,
                'reg_no': self.customer.reg_no
            }
        )
        self.assertEqual(receipt1.subtotal_amount, Decimal('485400.00'))
        self.assertEqual(receipt1.total_amount, Decimal('483800.00'))
        self.assertEqual(receipt1.discount_amount, Decimal('1600.00'))
        self.assertEqual(receipt1.tax_amount, Decimal('13665.15'))
        self.assertEqual(receipt1.given_amount, Decimal('0.00'))
        self.assertEqual(receipt1.change_amount, Decimal('0.00'))
        self.assertEqual(receipt1.loyalty_points_amount, Decimal('0.00'))
        self.assertEqual(receipt1.total_cost, Decimal('174052.00'))
        self.assertEqual(receipt1.payment_completed, True)
        self.assertEqual(receipt1.customer_points_update_completed, False)
        self.assertEqual(receipt1.is_debt, False)
        self.assertEqual(receipt1.receipt_closed, True)
        self.assertEqual(receipt1.is_refund, False)
        self.assertEqual(receipt1.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt1.item_count, 0)
        self.assertEqual(receipt1.local_reg_no, 222)
        self.assertTrue(receipt1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt1.receipt_number, self.receipts_data[0]['receipt_number'])
        self.assertEqual(receipt1.refund_for_receipt_number, '')
        self.assertEqual(receipt1.refund_for_reg_no, 0)
        self.assertEqual((receipt1.created_date).strftime("%B, %d, %Y"), 'January, 16, 2024')
        self.assertEqual(receipt1.created_date_timestamp, int(receipt1.created_date.timestamp()))
        self.assertEqual(receipt1.changed_stock, True)

        # Receipt 2
        receipt2 = receipts[1]

        self.assertEqual(receipt2.user, self.user)
        self.assertEqual(receipt2.store, self.store)
        self.assertEqual(receipt2.customer, self.customer)
        self.assertEqual(receipt2.customer_info, {
                'name': self.customer.name, 
                'email': self.customer.email,
                'phone': self.customer.phone,
                'tax_pin': self.customer.tax_pin,
                'reg_no': self.customer.reg_no
            }
        )
        self.assertEqual(receipt2.subtotal_amount, Decimal('1425.00'))
        self.assertEqual(receipt2.total_amount, Decimal('1375.00'))
        self.assertEqual(receipt2.discount_amount, Decimal('50.00'))
        self.assertEqual(receipt2.tax_amount, Decimal('97.24'))
        self.assertEqual(receipt2.given_amount, Decimal('0.00'))
        self.assertEqual(receipt2.change_amount, Decimal('0.00'))
        self.assertEqual(receipt2.loyalty_points_amount, Decimal('0.00'))
        self.assertEqual(receipt2.total_cost, Decimal('41984.00'))
        self.assertEqual(receipt2.payment_completed, True)
        self.assertEqual(receipt2.customer_points_update_completed, False)
        self.assertEqual(receipt2.is_debt, False)
        self.assertEqual(receipt2.receipt_closed, True)
        self.assertEqual(receipt2.is_refund, False)
        self.assertEqual(receipt2.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt2.item_count, 0)
        self.assertEqual(receipt2.local_reg_no, 222)
        self.assertTrue(receipt2.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt2.receipt_number, self.receipts_data[1]['receipt_number'])
        self.assertEqual(receipt2.refund_for_receipt_number, '')
        self.assertEqual(receipt2.refund_for_reg_no, 0)
        self.assertEqual((receipt2.created_date).strftime("%B, %d, %Y"), 'January, 16, 2024')
        self.assertEqual(receipt2.created_date_timestamp, int(receipt2.created_date.timestamp()))
        self.assertEqual(receipt2.changed_stock, True)

        # Receipt 3
        receipt3 = receipts[2]

        self.assertEqual(receipt3.user, self.user)
        self.assertEqual(receipt3.store, self.store)
        self.assertEqual(receipt3.customer, self.customer)
        self.assertEqual(receipt3.customer_info, {
                'name': self.customer.name, 
                'email': self.customer.email,
                'phone': self.customer.phone,
                'tax_pin': self.customer.tax_pin,
                'reg_no': self.customer.reg_no
            }
        )
        self.assertEqual(receipt3.subtotal_amount, Decimal('450.00'))
        self.assertEqual(receipt3.total_amount, Decimal('450.00'))
        self.assertEqual(receipt3.discount_amount, Decimal('0.00'))
        self.assertEqual(receipt3.tax_amount, Decimal('13.10'))
        self.assertEqual(receipt3.given_amount, Decimal('0.00'))
        self.assertEqual(receipt3.change_amount, Decimal('0.00'))
        self.assertEqual(receipt3.loyalty_points_amount, Decimal('0.00'))
        self.assertEqual(receipt3.total_cost, Decimal('3054.25'))
        self.assertEqual(receipt3.payment_completed, True)
        self.assertEqual(receipt3.customer_points_update_completed, False)
        self.assertEqual(receipt3.is_debt, False)
        self.assertEqual(receipt3.receipt_closed, True)
        self.assertEqual(receipt3.is_refund, False)
        self.assertEqual(receipt3.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt3.item_count, 0)
        self.assertEqual(receipt3.local_reg_no, 222)
        self.assertTrue(receipt3.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt3.receipt_number, self.receipts_data[2]['receipt_number'])
        self.assertEqual(receipt3.refund_for_receipt_number, '')
        self.assertEqual(receipt3.refund_for_reg_no, 0)
        self.assertEqual((receipt3.created_date).strftime("%B, %d, %Y"), 'January, 16, 2024')
        self.assertEqual(receipt3.created_date_timestamp, int(receipt3.created_date.timestamp()))
        self.assertEqual(receipt3.changed_stock, True)

        # Receipt 4
        receipt4 = receipts[3]

        self.assertEqual(receipt4.user, self.user)
        self.assertEqual(receipt4.store, self.store)
        self.assertEqual(receipt4.customer, self.customer)
        self.assertEqual(receipt4.customer_info, {
                'name': self.customer.name, 
                'email': self.customer.email,
                'phone': self.customer.phone,
                'tax_pin': self.customer.tax_pin,
                'reg_no': self.customer.reg_no
            }
        )
        self.assertEqual(receipt4.subtotal_amount, 220.00)
        self.assertEqual(receipt4.total_amount, Decimal('220.00'))
        self.assertEqual(receipt4.discount_amount, Decimal('0.00'))
        self.assertEqual(receipt4.tax_amount, Decimal('0.00'))
        self.assertEqual(receipt4.given_amount, Decimal('0.00'))
        self.assertEqual(receipt4.change_amount, Decimal('0.00'))
        self.assertEqual(receipt4.loyalty_points_amount, Decimal('0.00'))
        self.assertEqual(receipt4.total_cost, Decimal('724.00'))
        self.assertEqual(receipt4.payment_completed, True)
        self.assertEqual(receipt4.customer_points_update_completed, False)
        self.assertEqual(receipt4.is_debt, False)
        self.assertEqual(receipt4.receipt_closed, True)
        self.assertEqual(receipt4.is_refund, True)
        self.assertEqual(receipt4.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt4.item_count, 0)
        self.assertEqual(receipt4.local_reg_no, 222)
        self.assertTrue(receipt4.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt4.receipt_number, self.receipts_data[3]['receipt_number'])
        self.assertEqual(receipt4.refund_for_receipt_number, self.receipts_data[2]['receipt_number'])
        self.assertEqual(receipt4.refund_for_reg_no, 0)
        self.assertEqual((receipt4.created_date).strftime("%B, %d, %Y"), 'January, 16, 2024')
        self.assertEqual(receipt4.created_date_timestamp, int(receipt4.created_date.timestamp()))
        self.assertEqual(receipt4.changed_stock, True)

    def test_if_all_receipt_lines_are_created_correctly(self):

        self.create_receipts(self.receipts_data)

        receipts = Receipt.objects.all().order_by('-id')
        self.assertEqual(receipts.count(), 4)

        receiptlines = ReceiptLine.objects.all()
        self.assertEqual(receiptlines.count(), 30)

        # Receipt 1 receipt lines
        self.assertEqual(
            ReceiptLine.objects.filter(receipt=receipts[0]).count(), 
            4
        )

        # Receipt 2 receipt lines
        self.assertEqual(
            ReceiptLine.objects.filter(receipt=receipts[1]).count(), 
            20
        )

        # Receipt 3 receipt lines
        self.assertEqual(
            ReceiptLine.objects.filter(receipt=receipts[2]).count(), 
            5
        )

        # Receipt 4 receipt lines
        self.assertEqual(
            ReceiptLine.objects.filter(receipt=receipts[3]).count(), 
            1
        )
    '''

    def test_if_receipt_lines_when_products_dont_exit(self):

        # Delete products
        Product.objects.all().delete()
        self.assertEqual(Product.objects.all().count(), 0)

        self.create_receipts(self.receipts_data) 

        # Check if new products were created
        products = Product.objects.all().order_by('-id')
        self.assertEqual(products.count(), 27)

        receipts = Receipt.objects.all().order_by('-id')

        receipt1 = receipts[0]
        
        ########## Receipt 1 receipt lines
        receiptlines = ReceiptLine.objects.filter(receipt=receipt1)
        self.assertEqual(receiptlines.count(), 4)

        receiptline1 = receiptlines[0]

        self.assertEqual(receiptline1.user, self.user)
        self.assertEqual(receiptline1.receipt, receipt1)
        self.assertEqual(receiptline1.store, self.store)
        self.assertEqual(receiptline1.tax, self.taxes[0])
        self.assertEqual(receiptline1.parent_product, None)
        self.assertEqual(receiptline1.product, self.products[0])
        self.assertEqual(
            receiptline1.product_info, 
            {
                'name': self.products[0].name,
                'reg_no': self.products[0].reg_no,
                'loyverse_variant_id': str(self.products[0].loyverse_variant_id)
            }
        )
        self.assertEqual(receiptline1.modifier_options.all().count(), 0)
        self.assertEqual(receiptline1.modifier_options_info, [])
        self.assertEqual(receiptline1.customer, self.customer)
        self.assertEqual(receiptline1.price, Decimal('6600.00'))
        self.assertEqual(receiptline1.cost, self.products[0].cost * receiptline1.units)
        self.assertEqual(receiptline1.cost_total, self.products[0].cost * receiptline1.units)
        self.assertEqual(receiptline1.discount_amount, Decimal('304.57'))
        self.assertEqual(receiptline1.is_variant, False)
        self.assertEqual(receiptline1.sold_by_each, True)
        self.assertEqual(receiptline1.units, Decimal('14.00'))
        self.assertTrue(receiptline1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receiptline1.created_date).strftime("%B, %d, %Y"), 'January, 16, 2024')

        self.assertEqual(receiptline1.user_reg_no, self.user.reg_no)
        self.assertEqual(receiptline1.store_reg_no, self.store.reg_no)
        self.assertEqual(receiptline1.product_name, self.products[0].name)
        self.assertEqual(receiptline1.category_name, '')
        self.assertEqual(receiptline1.user_name, self.user.get_full_name())
        self.assertEqual(receiptline1.tax_name, self.taxes[0].name)
        self.assertEqual(
            receiptline1.tax_rate, 
            round(Decimal(self.taxes[0].rate), 2)
        )
        self.assertEqual(receiptline1.receipt_number, receipt1.receipt_number)
        self.assertEqual(
            receiptline1.refund_for_receipt_number, 
            receipt1.refund_for_receipt_number
        )

    '''
    def test_if_receipt_lines_are_created_correctly(self):

        self.create_receipts(self.receipts_data) 

        receipts = Receipt.objects.all().order_by('-id')

        receipt1 = receipts[0]
        
        ########## Receipt 1 receipt lines
        receiptlines = ReceiptLine.objects.filter(receipt=receipt1)
        self.assertEqual(receiptlines.count(), 4)

        receiptline1 = receiptlines[0]

        self.assertEqual(receiptline1.user, self.user)
        self.assertEqual(receiptline1.receipt, receipt1)
        self.assertEqual(receiptline1.store, self.store)
        self.assertEqual(receiptline1.tax, self.taxes[0])
        self.assertEqual(receiptline1.parent_product, None)
        self.assertEqual(receiptline1.product, self.products[0])
        self.assertEqual(
            receiptline1.product_info, 
            {
                'name': self.products[0].name,
                'reg_no': self.products[0].reg_no,
                'loyverse_variant_id': str(self.products[0].loyverse_variant_id)
            }
        )
        self.assertEqual(receiptline1.modifier_options.all().count(), 0)
        self.assertEqual(receiptline1.modifier_options_info, [])
        self.assertEqual(receiptline1.customer, self.customer)
        self.assertEqual(receiptline1.price, Decimal('6600.00'))
        self.assertEqual(receiptline1.cost, self.products[0].cost * receiptline1.units)
        self.assertEqual(receiptline1.cost_total, self.products[0].cost * receiptline1.units)
        self.assertEqual(receiptline1.discount_amount, Decimal('304.57'))
        self.assertEqual(receiptline1.is_variant, False)
        self.assertEqual(receiptline1.sold_by_each, True)
        self.assertEqual(receiptline1.units, Decimal('14.00'))
        self.assertTrue(receiptline1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receiptline1.created_date).strftime("%B, %d, %Y"), 'January, 16, 2024')

        self.assertEqual(receiptline1.user_reg_no, self.user.reg_no)
        self.assertEqual(receiptline1.store_reg_no, self.store.reg_no)
        self.assertEqual(receiptline1.product_name, self.products[0].name)
        self.assertEqual(receiptline1.category_name, '')
        self.assertEqual(receiptline1.user_name, self.user.get_full_name())
        self.assertEqual(receiptline1.tax_name, self.taxes[0].name)
        self.assertEqual(
            receiptline1.tax_rate, 
            round(Decimal(self.taxes[0].rate), 2)
        )
        self.assertEqual(receiptline1.receipt_number, receipt1.receipt_number)
        self.assertEqual(
            receiptline1.refund_for_receipt_number, 
            receipt1.refund_for_receipt_number
        )

    def test_if_receipt_lines_dates_are_increamenting_their_creation_dates(self):

        self.create_receipts(self.receipts_data) 

        receipts = Receipt.objects.all().order_by('-id')

        receipt1 = receipts[0]

        receiptlines = ReceiptLine.objects.filter(receipt=receipt1)
        self.assertEqual(receiptlines.count(), 4)

        for index, line in enumerate(receiptlines):
            self.assertEqual(
                line.created_date, 
                receipt1.created_date + datetime.timedelta(microseconds=index)
            )

    def test_if_receipt_lines_creation_when_tax_is_not_found(self):
        
        # Delete taxes
        Tax.objects.all().delete()

        self.create_receipts(self.receipts_data)

        receipts = Receipt.objects.all().order_by('-id')

        receipt1 = receipts[0]
        
        ########## Receipt 1 receipt lines
        receiptlines = ReceiptLine.objects.filter(receipt=receipt1)
        self.assertEqual(receiptlines.count(), 4)

        # Receipt line1
        receiptline1 = receiptlines[0]

        self.assertEqual(receiptline1.user, self.user)
        self.assertEqual(receiptline1.receipt, receipt1)
        self.assertEqual(receiptline1.store, self.store)
        self.assertEqual(receiptline1.tax, None)
        self.assertEqual(receiptline1.parent_product, None)
        self.assertEqual(receiptline1.product, self.products[0])
        self.assertEqual(
            receiptline1.product_info, 
            {
                'name': self.products[0].name,
                'reg_no': self.products[0].reg_no,
                'loyverse_variant_id': str(self.products[0].loyverse_variant_id)
            }
        )
        self.assertEqual(receiptline1.modifier_options.all().count(), 0)
        self.assertEqual(receiptline1.modifier_options_info, [])
        self.assertEqual(receiptline1.customer, self.customer)
        self.assertEqual(receiptline1.price, Decimal('6600.00'))
        self.assertEqual(receiptline1.cost, self.products[0].cost * receiptline1.units)
        self.assertEqual(receiptline1.cost_total, self.products[0].cost * receiptline1.units)
        self.assertEqual(receiptline1.discount_amount, Decimal('304.57'))
        self.assertEqual(receiptline1.is_variant, False)
        self.assertEqual(receiptline1.sold_by_each, True)
        self.assertEqual(receiptline1.units, Decimal('14.00'))
        self.assertTrue(receiptline1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receiptline1.created_date, receipt1.created_date)

        self.assertEqual(receiptline1.user_reg_no, self.user.reg_no)
        self.assertEqual(receiptline1.store_reg_no, self.store.reg_no)
        self.assertEqual(receiptline1.product_name, self.products[0].name)
        self.assertEqual(receiptline1.category_name, '')
        self.assertEqual(receiptline1.user_name, self.user.get_full_name())
        self.assertEqual(receiptline1.tax_name, '0')
        self.assertEqual(receiptline1.tax_rate, 0)
        self.assertEqual(receiptline1.receipt_number, receipt1.receipt_number)
        self.assertEqual(
            receiptline1.refund_for_receipt_number, 
            receipt1.refund_for_receipt_number
        )
    
    def test_if_receipt_creation_when_customer_is_not_found(self):

        # Delete customer
        Customer.objects.all().delete()

        self.create_receipts(self.receipts_data)

        receipts = Receipt.objects.all().order_by('-id')
        self.assertEqual(receipts.count(), 4)
         
        ########## Receipt 1
        receipt1 = receipts[0]

        self.assertEqual(receipt1.user, self.user)
        self.assertEqual(receipt1.store, self.store)
        self.assertEqual(receipt1.customer, None)
        self.assertEqual(receipt1.customer_info, {})
        self.assertEqual(receipt1.subtotal_amount, Decimal('485400.00'))
        self.assertEqual(receipt1.total_amount, Decimal('483800.00'))
        self.assertEqual(receipt1.discount_amount, Decimal('1600.00'))
        self.assertEqual(receipt1.tax_amount, Decimal('13665.15'))
        self.assertEqual(receipt1.given_amount, Decimal('0.00'))
        self.assertEqual(receipt1.change_amount, Decimal('0.00'))
        self.assertEqual(receipt1.loyalty_points_amount, Decimal('0.00'))
        self.assertEqual(receipt1.total_cost, Decimal('174052.00'))
        self.assertEqual(receipt1.payment_completed, True)
        self.assertEqual(receipt1.customer_points_update_completed, False)
        self.assertEqual(receipt1.is_debt, False)
        self.assertEqual(receipt1.receipt_closed, True)
        self.assertEqual(receipt1.is_refund, False)
        self.assertEqual(receipt1.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt1.item_count, 0)
        self.assertEqual(receipt1.local_reg_no, 222)
        self.assertTrue(receipt1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt1.receipt_number, self.receipts_data[0]['receipt_number'])
        self.assertEqual(receipt1.refund_for_receipt_number, '')
        self.assertEqual(receipt1.refund_for_reg_no, 0)
        self.assertEqual((receipt1.created_date).strftime("%B, %d, %Y"), 'January, 16, 2024')
        self.assertEqual(receipt1.created_date_timestamp, int(receipt1.created_date.timestamp()))
        self.assertEqual(receipt1.changed_stock, True)
    
    def test_if_receipt_creation_when_user_is_not_found(self):

        new_employee_id = 'ea74d75d-0ca0-408c-943c-7b3a47fb8fa3'

        # Input a similar employee id and store id to the user and to all receipts
        for receipt in self.receipts_data: 
            receipt['employee_id'] = new_employee_id

        self.create_receipts(self.receipts_data)

        new_user = get_user_model().objects.get(
            loyverse_employee_id=new_employee_id
        )

        receipts = Receipt.objects.all().order_by('-id')
        self.assertEqual(receipts.count(), 4)
   
        ########## Receipt 1
        receipt1 = receipts[0]

        self.assertEqual(receipt1.user, new_user)
        self.assertEqual(receipt1.store, self.store)
        self.assertEqual(receipt1.customer_info, {
                'name': self.customer.name, 
                'email': self.customer.email,
                'phone': self.customer.phone,
                'tax_pin': self.customer.tax_pin,
                'reg_no': self.customer.reg_no
            }
        )
        self.assertEqual(receipt1.subtotal_amount, Decimal('485400.00'))
        self.assertEqual(receipt1.total_amount, Decimal('483800.00'))
        self.assertEqual(receipt1.discount_amount, Decimal('1600.00'))
        self.assertEqual(receipt1.tax_amount, Decimal('13665.15'))
        self.assertEqual(receipt1.given_amount, Decimal('0.00'))
        self.assertEqual(receipt1.change_amount, Decimal('0.00'))
        self.assertEqual(receipt1.loyalty_points_amount, Decimal('0.00'))
        self.assertEqual(receipt1.total_cost, Decimal('174052.00'))
        self.assertEqual(receipt1.payment_completed, True)
        self.assertEqual(receipt1.customer_points_update_completed, False)
        self.assertEqual(receipt1.is_debt, False)
        self.assertEqual(receipt1.receipt_closed, True)
        self.assertEqual(receipt1.is_refund, False)
        self.assertEqual(receipt1.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt1.item_count, 0)
        self.assertEqual(receipt1.local_reg_no, 222)
        self.assertTrue(receipt1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt1.receipt_number, self.receipts_data[0]['receipt_number'])
        self.assertEqual(receipt1.refund_for_receipt_number, '')
        self.assertEqual(receipt1.refund_for_reg_no, 0)
        self.assertEqual((receipt1.created_date).strftime("%B, %d, %Y"), 'January, 16, 2024')
        self.assertEqual(receipt1.created_date_timestamp, int(receipt1.created_date.timestamp()))
        self.assertEqual(receipt1.changed_stock, True)

    def test_if_receipt_creation_when_store_is_not_found(self):

        # Delete store model
        Store.objects.all().delete()

        self.create_receipts(self.receipts_data)

        receipts = Receipt.objects.all().order_by('-id')
        self.assertEqual(receipts.count(), 4)

        store = Store.objects.get()
  
        self.assertEqual(store.profile.user.email, 'john@gmail.com')
        self.assertEqual(store.name, '89a5aa2b-7')
        self.assertEqual(store.address, '')
        self.assertEqual(store.is_shop, True)
        self.assertEqual(store.is_truck, False)
        self.assertEqual(store.is_warehouse, False)
        self.assertEqual(store.increamental_id, 101)
        self.assertTrue(store.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual(store.is_deleted, True)
        self.assertEqual(
            store.deleted_date, 
            timezone.make_aware(
                DateHelperMethods.get_date_from_date_str(
                    '2023-12-01T00:00:00.000Z'
                )
            )
        )
         
        ########## Receipt 1
        receipt1 = receipts[0]

        self.assertEqual(receipt1.user, self.user)
        self.assertEqual(receipt1.store, store)
        self.assertEqual(receipt1.customer, self.customer)
        self.assertEqual(receipt1.customer_info, {
                'name': self.customer.name, 
                'email': self.customer.email,
                'phone': self.customer.phone,
                'tax_pin': self.customer.tax_pin,
                'reg_no': self.customer.reg_no
            }
        )
        self.assertEqual(receipt1.subtotal_amount, Decimal('485400.00'))
        self.assertEqual(receipt1.total_amount, Decimal('483800.00'))
        self.assertEqual(receipt1.discount_amount, Decimal('1600.00'))
        self.assertEqual(receipt1.tax_amount, Decimal('13665.15'))
        self.assertEqual(receipt1.given_amount, Decimal('0.00'))
        self.assertEqual(receipt1.change_amount, Decimal('0.00'))
        self.assertEqual(receipt1.loyalty_points_amount, Decimal('0.00'))
        self.assertEqual(receipt1.total_cost, Decimal('174052.00'))
        self.assertEqual(receipt1.payment_completed, True)
        self.assertEqual(receipt1.customer_points_update_completed, False)
        self.assertEqual(receipt1.is_debt, False)
        self.assertEqual(receipt1.receipt_closed, True)
        self.assertEqual(receipt1.is_refund, False)
        self.assertEqual(receipt1.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt1.item_count, 0)
        self.assertEqual(receipt1.local_reg_no, 222)
        self.assertTrue(receipt1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt1.receipt_number, self.receipts_data[0]['receipt_number'])
        self.assertEqual(receipt1.refund_for_receipt_number, '')
        self.assertEqual(receipt1.refund_for_reg_no, 0)
        self.assertEqual((receipt1.created_date).strftime("%B, %d, %Y"), 'January, 16, 2024')
        self.assertEqual(receipt1.created_date_timestamp, int(receipt1.created_date.timestamp()))
        self.assertEqual(receipt1.changed_stock, True)

    def test_if_receipt_sale_and_refund_updates_stock_level(self):

        product = self.products[24]

        # Make sure all stock levels atleast have 1 unit
        StockLevel.objects.filter(store=self.store, product=product).update(units=5)

        # First confirm initial stock level for product 23
        self.assertEqual(StockLevel.objects.get(store=self.store, product=product).units, Decimal('5.00'))
        self.assertEqual(StockLevel.objects.get(store=self.store, product=product).price, Decimal('1024.00'))

        self.assertEqual(Product.objects.get(id=product.id).price, Decimal('1024.00'))

        ###### Create a sale only for receipt 3
        self.create_receipts([self.receipts_data[2]])

        # Confirm stock level for product 23
        self.assertEqual(StockLevel.objects.get(store=self.store, product=product).units, Decimal('4.00'))
        self.assertEqual(StockLevel.objects.get(store=self.store, product=product).price, Decimal('220.00'))

        self.assertEqual(Product.objects.get(id=product.id).average_price, Decimal('220.00'))   

        ###### Create a refund only for receipt 4
        self.create_receipts([self.receipts_data[3]])

        # Confirm stock level for product 23
        self.assertEqual(StockLevel.objects.get(store=self.store, product=product).units, Decimal('5.00'))
        self.assertEqual(StockLevel.objects.get(store=self.store, product=product).price, Decimal('220.00'))

        self.assertEqual(Product.objects.get(id=product.id).average_price, Decimal('220.00'))

    def test_if_receipt_sale_and_refund_updates_stock_level_wont_update_for_receipts_older_than_2024(self):

        product = self.products[24]

        # Make sure all stock levels atleast have 1 unit
        StockLevel.objects.filter(store=self.store, product=product).update(units=5)

        # First confirm initial stock level for product 23
        self.assertEqual(StockLevel.objects.get(store=self.store, product=product).units, Decimal('5.00'))
        self.assertEqual(StockLevel.objects.get(store=self.store, product=product).price, Decimal('1024.00'))

        self.assertEqual(Product.objects.get(id=product.id).price, Decimal('1024.00'))

        self.receipts_data[2]['receipt_date'] = '2023-12-31T11:50:59.000Z'
        self.receipts_data[3]['receipt_date'] = '2023-12-31T11:50:59.000Z'

        ###### Create a sale only for receipt 3
        self.create_receipts([self.receipts_data[2]])

        # Confirm stock level for product 23
        self.assertEqual(StockLevel.objects.get(store=self.store, product=product).units, Decimal('5.00'))
        self.assertEqual(StockLevel.objects.get(store=self.store, product=product).price, Decimal('220.00'))

        self.assertEqual(Product.objects.get(id=product.id).average_price, Decimal('220.00'))   

        ###### Create a refund only for receipt 4
        self.create_receipts([self.receipts_data[3]])

        # Confirm stock level for product 23
        self.assertEqual(StockLevel.objects.get(store=self.store, product=product).units, Decimal('5.00'))
        self.assertEqual(StockLevel.objects.get(store=self.store, product=product).price, Decimal('220.00'))

        self.assertEqual(Product.objects.get(id=product.id).average_price, Decimal('220.00'))

    def test_if_receipt_sale_will_update_stock_level_product_prices_if_they_change(self):

        product1 = self.products[6]
        product2 = self.products[24]
        product3 = self.products[25]
        product4 = self.products[17]
        product5 = self.products[26]

        # Confirm prices
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product1).price, 
            Decimal('1006.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product2).price, 
            Decimal('1024.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product3).price, 
            Decimal('1025.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product4).price, 
            Decimal('1017.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product5).price, 
            Decimal('1026.00')
        )

        ###### Create a sale only for receipt 3
        with self.assertNumQueries(169):
            self.create_receipts([self.receipts_data[2]])

        # Confirm prices
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product1).price, 
            Decimal('35.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product2).price, 
            Decimal('220.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product3).price, 
            Decimal('140.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product4).price, 
            Decimal('100.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product5).price, 
            Decimal('60.00')
        )

        ###### Update prices
        new_receipt = self.receipts_data[2]
        new_receipt['receipt_number'] = '123456789'
        new_receipt['line_items'][0]['price'] = 1400
        new_receipt['line_items'][1]['price'] = 1500
        new_receipt['line_items'][2]['price'] = 1600
        new_receipt['line_items'][3]['price'] = 1700
        new_receipt['line_items'][4]['price'] = 1800

        with self.assertNumQueries(239):
            self.create_receipts([new_receipt])

        # Confirm prices
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product1).price, 
            Decimal('1400.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product2).price, 
            Decimal('1500.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product3).price, 
            Decimal('1600.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product4).price, 
            Decimal('1700.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product5).price, 
            Decimal('1800.00')
        )

        # Update receipt number only and check if prices wont be updated
        new_receipt = self.receipts_data[2]
        new_receipt['receipt_number'] = '1234'
        with self.assertNumQueries(209):
            self.create_receipts([new_receipt])

        # Confirm prices
        self.assertEqual(    
            StockLevel.objects.get(store=self.store, product=product1).price, 
            Decimal('1400.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product2).price, 
            Decimal('1500.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product3).price, 
            Decimal('1600.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product4).price, 
            Decimal('1700.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product5).price, 
            Decimal('1800.00')
        )
    
    def test_if_product_price_will_average_from_different_stores(self):

        # Create store
        store2 = Store.objects.create(
            profile=self.profile,
            name="Amboseli",
            address="Nairobi",
            loyverse_store_id='5e519bae-bc34-4e00-8000-2c0ab6ff3ec6'
        )

        # Make sure all stock levels atleast have 1 unit
        StockLevel.objects.all().update(units=1)

        product1 = self.products[6]
        product2 = self.products[24]
        product3 = self.products[25]
        product4 = self.products[17]
        product5 = self.products[26]

        receipt1 = self.receipts_data[2]
        receipt2 = copy.deepcopy(receipt1)

        receipt1['store_id'] = self.store_id
        receipt2['store_id'] = store2.loyverse_store_id

        ###### Update prices for receipt 2
        receipt2['receipt_number'] = '123456789'
        receipt2['line_items'][0]['price'] = 1400
        receipt2['line_items'][1]['price'] = 1500
        receipt2['line_items'][2]['price'] = 1600
        receipt2['line_items'][3]['price'] = 1700
        receipt2['line_items'][4]['price'] = 1800

        # Confirm prices
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product1).price, 
            Decimal('1006.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product2).price, 
            Decimal('1024.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product3).price, 
            Decimal('1025.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product4).price, 
            Decimal('1017.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product5).price, 
            Decimal('1026.00')
        )

        self.create_receipts([receipt1, receipt2])

        # Confirm prices
        self.assertEqual(Product.objects.get(id=product1.id).average_price, Decimal('717.50'))  
        self.assertEqual(Product.objects.get(id=product2.id).average_price, Decimal('860.00')) 
        self.assertEqual(Product.objects.get(id=product3.id).average_price, Decimal('870.00')) 
        self.assertEqual(Product.objects.get(id=product4.id).average_price, Decimal('900.00')) 
        self.assertEqual(Product.objects.get(id=product5.id).average_price, Decimal('930.00')) 
    
    def test_if_product_price_will_wont_average_when_stock_is_zero(self):

        # Create store
        store2 = Store.objects.create(
            profile=self.profile,
            name="Amboseli",
            address="Nairobi",
            loyverse_store_id='5e519bae-bc34-4e00-8000-2c0ab6ff3ec6'
        )

        # Make sure all stock levels atleast have 1 unit
        StockLevel.objects.all().update(units=0)

        product1 = self.products[6]
        product2 = self.products[24]
        product3 = self.products[25]
        product4 = self.products[17]
        product5 = self.products[26]



        # Confirm prices
        self.assertEqual(Product.objects.get(id=product1.id).average_price, Decimal('1006.00'))  
        self.assertEqual(Product.objects.get(id=product2.id).average_price, Decimal('1024.00'))
        self.assertEqual(Product.objects.get(id=product3.id).average_price, Decimal('1025.00'))
        self.assertEqual(Product.objects.get(id=product4.id).average_price, Decimal('1017.00'))
        self.assertEqual(Product.objects.get(id=product5.id).average_price, Decimal('1026.00'))

        receipt1 = self.receipts_data[2]
        receipt2 = copy.deepcopy(receipt1)

        receipt1['store_id'] = self.store_id
        receipt2['store_id'] = store2.loyverse_store_id

        ###### Update prices for receipt 2
        receipt2['receipt_number'] = '123456789'
        receipt2['line_items'][0]['price'] = 1400
        receipt2['line_items'][1]['price'] = 1500
        receipt2['line_items'][2]['price'] = 1600
        receipt2['line_items'][3]['price'] = 1700
        receipt2['line_items'][4]['price'] = 1800

        # Confirm prices
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product1).price, 
            Decimal('1006.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product2).price, 
            Decimal('1024.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product3).price, 
            Decimal('1025.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product4).price, 
            Decimal('1017.00')
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=product5).price, 
            Decimal('1026.00')
        )

        self.create_receipts([receipt1, receipt2])

        # Confirm prices
        self.assertEqual(Product.objects.get(id=product1.id).average_price, Decimal('1006.00'))  
        self.assertEqual(Product.objects.get(id=product2.id).average_price, Decimal('1024.00'))
        self.assertEqual(Product.objects.get(id=product3.id).average_price, Decimal('1025.00'))
        self.assertEqual(Product.objects.get(id=product4.id).average_price, Decimal('1017.00'))
        self.assertEqual(Product.objects.get(id=product5.id).average_price, Decimal('1026.00'))
'''