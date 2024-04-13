from django.urls import reverse
from django.core import mail

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from core.test_utils.create_store_models import create_new_category, create_new_discount, create_new_tax
from core.test_utils.create_user import create_new_customer

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.initial_user_data import InitialUserDataMixin

from mysettings.models import MySetting
from products.models import Product
from profiles.models import Customer, ReceiptSetting
from sales.models import Receipt, ReceiptLine, ReceiptPayment
from stores.models import StorePaymentMethod

class ReceiptEmailViewTestCase(APITestCase, InitialUserDataMixin):

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
        ms.maintenance=False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
        # Create receipts

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

        # Store settings
        r_setting = ReceiptSetting.objects.get(store=self.store1)
        r_setting.header1 = 'Header1'
        r_setting.header2 = 'Header2'
        r_setting.header3 = 'Header3'
        r_setting.header4 = 'Header4'
        r_setting.header5 = 'Header5'
        r_setting.header6 = 'Header6'
        r_setting.footer1 = 'Footer1'
        r_setting.footer2 = 'Footer2'
        r_setting.footer3 = 'Footer3'
        r_setting.footer4 = 'Footer4'
        r_setting.footer5 = 'Footer5'
        r_setting.footer6 = 'Footer6'
        r_setting.save()


    def create_sale_data(
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
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )
        self.product.stores.add(self.store1)

        self.product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
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
            local_reg_no=222
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

        pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=payment_type
        )

        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=pay_method,
            amount=2500
        )

    def test_if_receipt_header_sections(self):

        data = {'email': 'customer@gmail.com', 'reg_no': self.receipt.reg_no}
        
        response = self.client.post(reverse('api:email_receipt'), data, format='json')                                        
        self.assertEqual(response.status_code, 200)
        
        message = mail.outbox[0]

        self.assertEqual(message.subject, f'Receipt from {self.store1.name}')
        self.assertEqual(message.from_email, 'webmaster@localhost')
        self.assertEqual(message.recipients(), ['customer@gmail.com'])
        
        
