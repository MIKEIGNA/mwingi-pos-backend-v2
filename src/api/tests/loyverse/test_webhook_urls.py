import copy
from decimal import Decimal

from django.urls import reverse

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.create_user import create_new_user
from core.test_utils.loyverse_data.loyverse_test_data import LOYVERSE_RECEIPT_WEBHOOK_UPDATE_DATA6

from inventories.models import StockLevel
from loyverse.models import LoyverseAppData

from products.models import Product
from profiles.models import Customer, Profile
from sales.models import Receipt, ReceiptCount, ReceiptLine
from stores.models import Store, Tax

class LoyverseWebhookReceiptUpdateViewTestCase(APITestCase):

    def setUp(self):

        # Loyverse ids that will be used during testing
        self.employee_id = '330a125a-71a9-11ea-8d93-0603130a05b8'
        self.store_id = '89a5aa2b-78f6-416f-acf3-c28d5266a636'
        self.customer_id = '9ec86d1c-cad9-4886-8d9b-b799d9a71bff'
        
        #Create a user with email john@gmail.com
        self.user = create_new_user('angelina')
        self.profile = Profile.objects.get(user=self.user)

        ReceiptCount.objects.create()

        # We use deepcopy so that we dont edit the global source
        self.receipts_data = copy.deepcopy(
            LOYVERSE_RECEIPT_WEBHOOK_UPDATE_DATA6
        )
        
        # Input a similar employee id and store id to the user and to all receipts
        for data in self.receipts_data['receipts']: 
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
        for receipt in self.receipts_data['receipts']:
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
                loyverse_variant_id=variant_id
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
    
    def test_if(self):

        response = self.client.post(reverse('api:loyverse_webhook_receipt_update'), self.receipts_data)
        self.assertEqual(response.status_code, 200)

    def test_if_receipts_are_created_correctly(self):

        response = self.client.post(reverse('api:loyverse_webhook_receipt_update'), self.receipts_data)
        self.assertEqual(response.status_code, 200)

        # Confirm receipts were created
        receipts = Receipt.objects.all().order_by('-id')
        self.assertEqual(receipts.count(), 4)

        receipts_data = self.receipts_data['receipts']
         
        ########## Receipt 1
        receipt1 = receipts[0]

        self.assertEqual(receipt1.user, self.user)
        self.assertEqual(receipt1.store, self.store)
        self.assertEqual(receipt1.customer, self.customer)
        self.assertEqual(receipt1.customer_info, {
                'name': self.customer.name, 
                'reg_no': self.customer.reg_no
            }
        )
        self.assertEqual(receipt1.subtotal_amount, Decimal('470134.85'))
        self.assertEqual(receipt1.total_amount, Decimal('483800.00'))
        self.assertEqual(receipt1.discount_amount, Decimal('1600.00'))
        self.assertEqual(receipt1.tax_amount, Decimal('13665.15'))
        self.assertEqual(receipt1.given_amount, Decimal('0.00'))
        self.assertEqual(receipt1.change_amount, Decimal('0.00'))
        self.assertEqual(receipt1.loyalty_points_amount, Decimal('0.00'))
        self.assertEqual(receipt1.total_cost, Decimal('0.00'))
        self.assertEqual(receipt1.payment_completed, True)
        self.assertEqual(receipt1.customer_points_update_completed, False)
        self.assertEqual(receipt1.is_debt, False)
        self.assertEqual(receipt1.receipt_closed, True)
        self.assertEqual(receipt1.is_refund, False)
        self.assertEqual(receipt1.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt1.item_count, 0)
        self.assertEqual(receipt1.local_reg_no, 222)
        self.assertTrue(receipt1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt1.receipt_number, receipts_data[0]['receipt_number'])
        self.assertEqual(receipt1.refund_for_receipt_number, '')
        self.assertEqual(receipt1.refund_for_reg_no, 0)
        self.assertEqual((receipt1.created_date).strftime("%B, %d, %Y"), 'September, 16, 2022')
        self.assertEqual(receipt1.created_date_timestamp, int(receipt1.created_date.timestamp()))

        # Receipt 2
        receipt2 = receipts[1]

        self.assertEqual(receipt2.user, self.user)
        self.assertEqual(receipt2.store, self.store)
        self.assertEqual(receipt2.customer, self.customer)
        self.assertEqual(receipt2.customer_info, {
                'name': self.customer.name, 
                'reg_no': self.customer.reg_no
            }
        )
        self.assertEqual(receipt2.subtotal_amount, Decimal('1277.76'))
        self.assertEqual(receipt2.total_amount, Decimal('1375.00'))
        self.assertEqual(receipt2.discount_amount, Decimal('50.00'))
        self.assertEqual(receipt2.tax_amount, Decimal('97.24'))
        self.assertEqual(receipt2.given_amount, Decimal('0.00'))
        self.assertEqual(receipt2.change_amount, Decimal('0.00'))
        self.assertEqual(receipt2.loyalty_points_amount, Decimal('0.00'))
        self.assertEqual(receipt2.total_cost, Decimal('0.00'))
        self.assertEqual(receipt2.payment_completed, True)
        self.assertEqual(receipt2.customer_points_update_completed, False)
        self.assertEqual(receipt2.is_debt, False)
        self.assertEqual(receipt2.receipt_closed, True)
        self.assertEqual(receipt2.is_refund, False)
        self.assertEqual(receipt2.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt2.item_count, 0)
        self.assertEqual(receipt2.local_reg_no, 222)
        self.assertTrue(receipt2.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt2.receipt_number, receipts_data[1]['receipt_number'])
        self.assertEqual(receipt2.refund_for_receipt_number, '')
        self.assertEqual(receipt2.refund_for_reg_no, 0)
        self.assertEqual((receipt2.created_date).strftime("%B, %d, %Y"), 'September, 16, 2022')
        self.assertEqual(receipt2.created_date_timestamp, int(receipt2.created_date.timestamp()))

        # Receipt 3
        receipt3 = receipts[2]

        self.assertEqual(receipt3.user, self.user)
        self.assertEqual(receipt3.store, self.store)
        self.assertEqual(receipt3.customer, self.customer)
        self.assertEqual(receipt3.customer_info, {
                'name': self.customer.name, 
                'reg_no': self.customer.reg_no
            }
        )
        self.assertEqual(receipt3.subtotal_amount, Decimal('436.90'))
        self.assertEqual(receipt3.total_amount, Decimal('450.00'))
        self.assertEqual(receipt3.discount_amount, Decimal('0.00'))
        self.assertEqual(receipt3.tax_amount, Decimal('13.10'))
        self.assertEqual(receipt3.given_amount, Decimal('0.00'))
        self.assertEqual(receipt3.change_amount, Decimal('0.00'))
        self.assertEqual(receipt3.loyalty_points_amount, Decimal('0.00'))
        self.assertEqual(receipt3.total_cost, Decimal('0.00'))
        self.assertEqual(receipt3.payment_completed, True)
        self.assertEqual(receipt3.customer_points_update_completed, False)
        self.assertEqual(receipt3.is_debt, False)
        self.assertEqual(receipt3.receipt_closed, True)
        self.assertEqual(receipt3.is_refund, False)
        self.assertEqual(receipt3.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt3.item_count, 0)
        self.assertEqual(receipt3.local_reg_no, 222)
        self.assertTrue(receipt3.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt3.receipt_number, receipts_data[2]['receipt_number'])
        self.assertEqual(receipt3.refund_for_receipt_number, '')
        self.assertEqual(receipt3.refund_for_reg_no, 0)
        self.assertEqual((receipt3.created_date).strftime("%B, %d, %Y"), 'September, 16, 2022')
        self.assertEqual(receipt3.created_date_timestamp, int(receipt3.created_date.timestamp()))

        # Receipt 4
        receipt4 = receipts[3]

        self.assertEqual(receipt4.user, self.user)
        self.assertEqual(receipt4.store, self.store)
        self.assertEqual(receipt4.customer, self.customer)
        self.assertEqual(receipt4.customer_info, {
                'name': self.customer.name, 
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
        self.assertEqual(receipt4.total_cost, Decimal('0.00'))
        self.assertEqual(receipt4.payment_completed, True)
        self.assertEqual(receipt4.customer_points_update_completed, False)
        self.assertEqual(receipt4.is_debt, False)
        self.assertEqual(receipt4.receipt_closed, True)
        self.assertEqual(receipt4.is_refund, True)
        self.assertEqual(receipt4.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt4.item_count, 0)
        self.assertEqual(receipt4.local_reg_no, 222)
        self.assertTrue(receipt4.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt4.receipt_number, receipts_data[3]['receipt_number'])
        self.assertEqual(receipt4.refund_for_receipt_number, receipts_data[2]['receipt_number'])
        self.assertEqual(receipt4.refund_for_reg_no, 0)
        self.assertEqual((receipt4.created_date).strftime("%B, %d, %Y"), 'September, 16, 2022')
        self.assertEqual(receipt4.created_date_timestamp, int(receipt4.created_date.timestamp()))

    def test_if_all_receipt_lines_are_created_correctly(self):

        response = self.client.post(reverse('api:loyverse_webhook_receipt_update'), self.receipts_data)
        self.assertEqual(response.status_code, 200)

        # Confirm receipts were created
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

    def test_if_receipt_lines_are_created_correctly(self):
    
        response = self.client.post(reverse('api:loyverse_webhook_receipt_update'), self.receipts_data)
        self.assertEqual(response.status_code, 200)

        # Confirm receipts were created
        receipts = Receipt.objects.all().order_by('-id')
        self.assertEqual(receipts.count(), 4)

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
        self.assertEqual(receiptline1.product_info, {'name': self.products[0].name})
        self.assertEqual(receiptline1.modifier_options.all().count(), 0)
        self.assertEqual(receiptline1.modifier_options_info, [])
        self.assertEqual(receiptline1.customer, self.customer)
        self.assertEqual(receiptline1.price, Decimal('6600.00'))
        self.assertEqual(receiptline1.cost, self.products[0].cost * 7)
        self.assertEqual(receiptline1.discount_amount, Decimal('304.57'))
        self.assertEqual(receiptline1.is_variant, False)
        self.assertEqual(receiptline1.sold_by_each, True)
        self.assertEqual(receiptline1.units, Decimal('14.00'))
        self.assertTrue(receiptline1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receiptline1.created_date).strftime("%B, %d, %Y"), 'September, 16, 2022')


    def test_if_receipt_lines_creation_when_tax_is_not_found(self):

        # Delete taxes
        Tax.objects.all().delete()

        response = self.client.post(reverse('api:loyverse_webhook_receipt_update'), self.receipts_data)
        self.assertEqual(response.status_code, 200)

        # Confirm receipts were created
        receipts = Receipt.objects.all().order_by('-id')
        self.assertEqual(receipts.count(), 4)
        
        receipt1 = receipts[0]
        
        ########## Receipt 1 receipt lines
        receiptlines = ReceiptLine.objects.filter(receipt=receipt1)
        self.assertEqual(receiptlines.count(), 4)

        receiptline1 = receiptlines[0]

        self.assertEqual(receiptline1.user, self.user)
        self.assertEqual(receiptline1.receipt, receipt1)
        self.assertEqual(receiptline1.store, self.store)
        self.assertEqual(receiptline1.tax, None)
        self.assertEqual(receiptline1.parent_product, None)
        self.assertEqual(receiptline1.product, self.products[0])
        self.assertEqual(receiptline1.product_info, {'name': self.products[0].name})
        self.assertEqual(receiptline1.modifier_options.all().count(), 0)
        self.assertEqual(receiptline1.modifier_options_info, [])
        self.assertEqual(receiptline1.customer, self.customer)
        self.assertEqual(receiptline1.price, Decimal('6600.00'))
        self.assertEqual(receiptline1.cost, self.products[0].cost * 7)
        self.assertEqual(receiptline1.discount_amount, Decimal('304.57'))
        self.assertEqual(receiptline1.is_variant, False)
        self.assertEqual(receiptline1.sold_by_each, True)
        self.assertEqual(receiptline1.units, Decimal('14.00'))
        self.assertTrue(receiptline1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((receiptline1.created_date).strftime("%B, %d, %Y"), 'September, 16, 2022')

    def test_if_receipt_creation_when_customer_is_not_found(self):

        # Delete customer
        Customer.objects.all().delete()

        response = self.client.post(reverse('api:loyverse_webhook_receipt_update'), self.receipts_data)
        self.assertEqual(response.status_code, 200)

        # Confirm receipts were created
        receipts = Receipt.objects.all().order_by('-id')
        self.assertEqual(receipts.count(), 4)

        receipts_data = self.receipts_data['receipts']

        receipts = Receipt.objects.all().order_by('-id')
        self.assertEqual(receipts.count(), 4)
         
        ########## Receipt 1
        receipt1 = receipts[0]

        self.assertEqual(receipt1.user, self.user)
        self.assertEqual(receipt1.store, self.store)
        self.assertEqual(receipt1.customer, None)
        self.assertEqual(receipt1.customer_info, {})
        self.assertEqual(receipt1.subtotal_amount, Decimal('470134.85'))
        self.assertEqual(receipt1.total_amount, Decimal('483800.00'))
        self.assertEqual(receipt1.discount_amount, Decimal('1600.00'))
        self.assertEqual(receipt1.tax_amount, Decimal('13665.15'))
        self.assertEqual(receipt1.given_amount, Decimal('0.00'))
        self.assertEqual(receipt1.change_amount, Decimal('0.00'))
        self.assertEqual(receipt1.loyalty_points_amount, Decimal('0.00'))
        self.assertEqual(receipt1.total_cost, Decimal('0.00'))
        self.assertEqual(receipt1.payment_completed, True)
        self.assertEqual(receipt1.customer_points_update_completed, False)
        self.assertEqual(receipt1.is_debt, False)
        self.assertEqual(receipt1.receipt_closed, True)
        self.assertEqual(receipt1.is_refund, False)
        self.assertEqual(receipt1.transaction_type, Receipt.MONEY_TRANS)
        self.assertEqual(receipt1.item_count, 0)
        self.assertEqual(receipt1.local_reg_no, 222)
        self.assertTrue(receipt1.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual(receipt1.receipt_number, receipts_data[0]['receipt_number'])
        self.assertEqual(receipt1.refund_for_receipt_number, '')
        self.assertEqual(receipt1.refund_for_reg_no, 0)
        self.assertEqual((receipt1.created_date).strftime("%B, %d, %Y"), 'September, 16, 2022')
        self.assertEqual(receipt1.created_date_timestamp, int(receipt1.created_date.timestamp()))
    
    def test_if_receipt_sale_and_refund_updates_stock_level(self):

        # First confirm initial stock level for product 23
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=self.products[24]).units, 
            0
        )

        ###### Create a sale only for receipt 3
        receipts_data = copy.deepcopy(self.receipts_data)
        receipts_data['receipts'] = [self.receipts_data['receipts'][2]]

        response = self.client.post(reverse('api:loyverse_webhook_receipt_update'), receipts_data)
        self.assertEqual(response.status_code, 200)

        # Confirm stock level for product 23
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=self.products[24]).units, 
            -1
        )

        ###### Create a refund only for receipt 4
        receipts_data = copy.deepcopy(self.receipts_data)
        receipts_data['receipts'] = [self.receipts_data['receipts'][3]]

        response = self.client.post(reverse('api:loyverse_webhook_receipt_update'), receipts_data)
        self.assertEqual(response.status_code, 200)

        # Confirm stock level for product 23
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=self.products[24]).units, 
            0
        )

class LoyverseLoyverseAppDataUpdateViewTestCase(APITestCase):

    def setUp(self):

        #Create a user with email john@gmail.com
        self.user = create_new_user('john')
        self.profile = Profile.objects.get(user=self.user)

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """

        payload = {
            'access_token': 'hGVXj4bW0ricTMm1eXJ8F_RJqKI',
            'refresh_token': 'hGVXj4bW0uicTMm1eXJ8F_RJqKI'
        }

        return payload

    def test_if_model_can_be_updated_correctly(self):

        payload = self.get_premade_payload()

        response = self.client.post(
            reverse('api:loyverse_webhook_loyverse_app_data'), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        data = LoyverseAppData.objects.get()

        self.assertEqual(str(data), 'main')

        self.assertEqual(str(data.access_token), payload['access_token'])
        self.assertEqual(str(data.refresh_token), payload['refresh_token'])
        self.assertEqual(data.access_token_expires_in, 0)