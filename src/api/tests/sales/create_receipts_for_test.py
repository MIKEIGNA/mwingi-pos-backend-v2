import datetime
from django.contrib.auth import get_user_model
from core.test_utils.create_product_variants import create_1d_variants

from core.test_utils.initial_user_data import CreateTimeVariablesMixin
from core.test_utils.create_product_models import create_new_product
from core.time_utils.time_localizers import utc_to_local_datetime
from products.models import Product
from stores.models import StorePaymentMethod

from sales.models import Receipt, ReceiptLine, ReceiptPayment

User = get_user_model()

class CreateReceiptsForTesting(CreateTimeVariablesMixin):
    """
    Creates 4 receipts for profile. manager ang cashier respectively. First 
    2 are in store1 while the last one is in store2
    """

    def __init__(self, top_profile, manager, cashier, store1, store2):
        self.top_profile = top_profile
        self.manager = manager
        self.cashier = cashier

        self.store1 = store1
        self.store2 = store2

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

    def create_receipt_payment(self, receipt, amount, payment_type):

        pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=payment_type
        )
        ReceiptPayment.objects.create(
            receipt=receipt,
            payment_method=pay_method,
            amount=amount
        )

    def create_receipts(self, is_debt=False):

        #=============================== Receipt 1

        # Create products
        shampoo = create_new_product(profile=self.top_profile, name="Shampoo")
        conditioner = create_new_product(profile=self.top_profile, name="Conditioner")


        # Create receipt1
        receipt1 = Receipt.objects.create(
            user=self.top_profile.user,
            store=self.store1,
            customer_info={},
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=111,
            receipt_number="110",
            created_date_timestamp = int(self.today.timestamp())
        )
        
        # Create receipt line1
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=shampoo,
            product_info={'name': shampoo.name},
            price=1750,
            units=7
        )
    
        # Create receipt line2
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=conditioner,
            product_info={'name': conditioner.name},
            price=2500,
            units=10
        ) 


        #=============================== Receipt 2
        
        receipt2 = Receipt.objects.create(
            user=self.top_profile.user,
            store=self.store1,
            customer_info={},
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=222,
            receipt_number="111",
            created_date_timestamp = int(self.today.timestamp())
        )

        # Create receipt line1
        ReceiptLine.objects.create(
            receipt=receipt2,
            product=shampoo,
            product_info={'name': shampoo.name},
            price=1750,
            units=8
        )
    
        # Create receipt line2
        ReceiptLine.objects.create(
            receipt=receipt2,
            product=conditioner,
            product_info={'name': conditioner.name},
            price=2500,
            units=11
        )

        
    
        #=============================== Receipt 3

        receipt3 = Receipt.objects.create(
            user=self.manager.user,
            store=self.store1,
            customer_info={},
            discount_amount=501.00,
            tax_amount=70.00,
            given_amount=3900.00,
            change_amount=700.00,
            subtotal_amount=3000,
            total_amount=3599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=333,
            receipt_number="112",
            created_date_timestamp = int(self.first_day_this_month.timestamp())
        )

        # Create receipt line1
        ReceiptLine.objects.create(
            receipt=receipt3,
            product=shampoo,
            product_info={'name': shampoo.name},
            price=2750,
            units=10
        )
    
        # Create receipt line2
        ReceiptLine.objects.create(
            receipt=receipt3,
            product=conditioner,
            product_info={'name': conditioner.name},
            price=3500,
            units=15
        )

        # Refund the receipt
        receipt3.perform_refund()


        #=============================== Receipt 4

        receipt4 = Receipt.objects.create(
            user=self.cashier.user,
            store=self.store2,
            customer_info={},
            discount_amount=601.00,
            tax_amount=80.00,
            given_amount=4900.00,
            change_amount=900.00,
            subtotal_amount=4000,
            total_amount=4599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=444,
            receipt_number="113",
            created_date_timestamp=int(self.last_month.timestamp())
        )

        # Create receipt line1
        ReceiptLine.objects.create(
            receipt=receipt4,
            product=shampoo,
            product_info={'name': shampoo.name},
            price=3750,
            units=10
        )
    
        # Create receipt line2
        ReceiptLine.objects.create(
            receipt=receipt4,
            product=conditioner,
            product_info={'name': conditioner.name},
            price=3500,
            units=15
        )


        ####### Create payments


        if not is_debt:

            # Receipt 1
            self.create_receipt_payment(receipt1, 1599.00, StorePaymentMethod.CASH_TYPE)

            # Receipt 2
            self.create_receipt_payment(receipt2, 1000.00, StorePaymentMethod.CASH_TYPE)
            self.create_receipt_payment(receipt2, 599.00, StorePaymentMethod.MPESA_TYPE)

            # Receipt 3
            self.create_receipt_payment(receipt3, 3599.00, StorePaymentMethod.CASH_TYPE)

            # Receipt 4
            self.create_receipt_payment(receipt4, 4599.00, StorePaymentMethod.CARD_TYPE)

        else:
            # Receipt 1
            self.create_receipt_payment(receipt1, 1599.00, StorePaymentMethod.DEBT_TYPE)

            # Receipt 2
            self.create_receipt_payment(receipt2, 1599.00, StorePaymentMethod.MPESA_TYPE)

            # Receipt 3
            self.create_receipt_payment(receipt3, 3599.00, StorePaymentMethod.DEBT_TYPE)

            # Receipt 4
            self.create_receipt_payment(receipt4, 4599.00, StorePaymentMethod.DEBT_TYPE)


class CreateReceiptsForTesting2(CreateTimeVariablesMixin):
    """
    Creates 3 receipts for profile. manager ang cashier respectively. First 2 are
    in store1 while the last one is in store2
    """

    def __init__(
        self, top_profile, 
        manager, 
        cashier,
        discount,
        tax,
        store1, 
        store2):

        self.top_profile = top_profile
        self.manager = manager
        self.cashier = cashier

        self.discount = discount
        self.tax = tax

        self.store1 = store1
        self.store2 = store2

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

    def create_receipt_payment(self, receipt, payment_type):

        pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=payment_type
        )
        ReceiptPayment.objects.create(
            receipt=receipt,
            payment_method=pay_method,
            amount=receipt.subtotal_amount
        )

    def create_receipts(self):

        #=============================== Receipt 1

        # Create products
        shampoo = create_new_product(profile=self.top_profile, name="Shampoo")
        conditioner = create_new_product(profile=self.top_profile, name="Conditioner")

        # Update prices
        shampoo.price = 2500
        shampoo.save()

        conditioner.price = 1600
        conditioner.save()


        # Create receipt1
        receipt1 = Receipt.objects.create(
            user=self.top_profile.user,
            store=self.store1,
            discount=self.discount,
            tax=self.tax,
            customer_info={},
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=17500,
            receipt_number="110",
            created_date_timestamp = int(self.today.timestamp())
        )

        self.create_receipt_payment(receipt1, StorePaymentMethod.CASH_TYPE)

        # Create receipt line1
        units = 7
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=shampoo,
            product_info={'name': shampoo.name},
            price=shampoo.price * units,
            units=units
        )
    
        # Create receipt line2
        units = 10
        line = ReceiptLine.objects.create(
            receipt=receipt1,
            product=conditioner,
            product_info={'name': conditioner.name},
            price=conditioner.price * units,
            units=units
        )
        ReceiptLine.objects.filter(pk=line.pk).update(
            cost_total=conditioner.price * units
        )

        receipt1.calculate_and_update_total_cost() # Update stock

        #=============================== Receipt 2

        # Create receipt1
        receipt2 = Receipt.objects.create(
            user=self.manager.user,
            store=self.store1,
            discount=self.discount,
            tax=self.tax,
            customer_info={},
            discount_amount=501.00,
            tax_amount=70.00,
            given_amount=2900.00,
            change_amount=700.00,
            subtotal_amount=3000,
            total_amount=2599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=333,
            receipt_number="111",
            created_date_timestamp = int(self.first_day_this_month.timestamp())
        )

        self.create_receipt_payment(receipt2, StorePaymentMethod.CASH_TYPE)

        # Create receipt line1
        units = 9
        ReceiptLine.objects.create(
            receipt=receipt2,
            product=shampoo,
            product_info={'name': shampoo.name},
            price=shampoo.price * units,
            units=units
        )
    
        # Create receipt line2
        units = 15
        ReceiptLine.objects.create(
            receipt=receipt2,
            product=conditioner,
            product_info={'name': conditioner.name},
            price=conditioner.price * units,
            units=units
        )

        receipt2.calculate_and_update_total_cost() # Update stock

        # Refund the receipt
        receipt2.perform_refund()


        #=============================== Receipt 3

        # Create receipt3
        receipt3 = Receipt.objects.create(
            user=self.cashier.user,
            store=self.store2,
            discount=self.discount,
            tax=self.tax,
            customer_info={},
            discount_amount=601.00,
            tax_amount=80.00,
            given_amount=3900.00,
            change_amount=800.00,
            subtotal_amount=4000,
            total_amount=3599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=444,
            receipt_number="112",
            created_date_timestamp=int(self.last_month.timestamp())
        )

        self.create_receipt_payment(receipt3, StorePaymentMethod.CASH_TYPE)

        # Create receipt line1
        units = 6
        ReceiptLine.objects.create(
            receipt=receipt3,
            product=shampoo,
            product_info={'name': shampoo.name},
            price=shampoo.price * units,
            units=units
        )
    
        # Create receipt line2
        units = 12
        ReceiptLine.objects.create(
            receipt=receipt3,
            product=conditioner,
            product_info={'name': conditioner.name},
            price=conditioner.price * units,
            units=units
        )

        receipt3.calculate_and_update_total_cost() # Update stock


class CreateReceiptsForTesting3(CreateTimeVariablesMixin):
    """
    Creates 3 receipts for profile. manager ang cashier respectively. First 2 are
    in store1 while the last one is in store2
    """

    def __init__(
        self, top_profile, 
        manager, 
        cashier,
        discount,
        tax,
        store1, 
        store2):

        self.top_profile = top_profile
        self.manager = manager
        self.cashier = cashier

        self.discount = discount
        self.tax = tax

        self.store1 = store1
        self.store2 = store2

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

    def create_receipt_payment(self, receipt, amount, payment_type):

        pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=payment_type
        )
        ReceiptPayment.objects.create(
            receipt=receipt,
            payment_method=pay_method,
            amount=amount
        )

    def create_receipts(self):

        # Create products
        shampoo = create_new_product(profile=self.top_profile, name="Shampoo")
        conditioner = create_new_product(profile=self.top_profile, name="Conditioner")

        # Update prices
        shampoo.price = 2500
        shampoo.save()

        conditioner.price = 1600
        conditioner.save()

        #=============================== Receipt 1

        # Create receipt1
        receipt1 = Receipt.objects.create(
            user=self.top_profile.user,
            store=self.store1,
            discount=self.discount,
            tax=self.tax,
            customer_info={},
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=33039,
            total_amount=33500.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=17500,
            receipt_number="110",
            created_date_timestamp = int(self.today.timestamp())
        )
        self.create_receipt_payment(
            receipt1, 
            receipt1.subtotal_amount, 
            StorePaymentMethod.CASH_TYPE
        )


        # Create receipt line1
        units = 7
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=shampoo,
            product_info={'name': shampoo.name},
            price=shampoo.price * units,
            units=units
        )
    
        # Create receipt line2
        units = 10
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=conditioner,
            product_info={'name': conditioner.name},
            price=conditioner.price * units,
            units=units
        )

        receipt1 = Receipt.objects.get(pk=receipt1.pk)
        receipt1.calculate_and_update_total_cost() # Update stock

        #=============================== Receipt 2

        receipt2_timestamp = (self.today + datetime.timedelta(hours=6)).timestamp()

        # Create receipt2
        receipt2 = Receipt.objects.create(
            user=self.top_profile.user,
            store=self.store1,
            discount=self.discount,
            tax=self.tax,
            customer_info={},
            discount_amount=301.00,
            tax_amount=50.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=29749,
            total_amount=30100.00,
            transaction_type=Receipt.MULTIPLE_TRANS,
            payment_completed=True,
            local_reg_no=17500,
            receipt_number="111",
            created_date_timestamp = int(receipt2_timestamp)
        )
        self.create_receipt_payment(receipt2, 15000.00, StorePaymentMethod.CASH_TYPE)
        self.create_receipt_payment(receipt2, 15100.00, StorePaymentMethod.MPESA_TYPE)

        # Create receipt line1
        units = 5
        ReceiptLine.objects.create(
            receipt=receipt2,
            product=shampoo,
            product_info={'name': shampoo.name},
            price=shampoo.price * units,
            units=units
        )
    
        # Create receipt line2
        units = 11
        ReceiptLine.objects.create(
            receipt=receipt2,
            product=conditioner,
            product_info={'name': conditioner.name},
            price=conditioner.price * units,
            units=units
        )

        receipt2 = Receipt.objects.get(pk=receipt2.pk)
        receipt2.calculate_and_update_total_cost() # Update stock

        #=============================== Receipt 3

        # Create receipt1
        receipt3 = Receipt.objects.create(
            user=self.manager.user,
            store=self.store1,
            discount=self.discount,
            tax=self.tax,
            customer_info={},
            discount_amount=501.00,
            tax_amount=70.00,
            given_amount=2900.00,
            change_amount=700.00,
            subtotal_amount=45929,
            total_amount=46500.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=333,
            receipt_number="112",
            created_date_timestamp = int(self.first_day_this_month.timestamp())
        )
        self.create_receipt_payment(
            receipt2, 
            receipt2.subtotal_amount, 
            StorePaymentMethod.CASH_TYPE
        )


        # Create receipt line1
        units = 9
        ReceiptLine.objects.create(
            receipt=receipt3,
            product=shampoo,
            product_info={'name': shampoo.name},
            price=shampoo.price * units,
            units=units
        )
    
        # Create receipt line2
        units = 15
        ReceiptLine.objects.create(
            receipt=receipt3,
            product=conditioner,
            product_info={'name': conditioner.name},
            price=conditioner.price * units,
            units=units
        )

        receipt3 = Receipt.objects.get(pk=receipt3.pk)
        receipt3.calculate_and_update_total_cost() # Update stock

        # Refund the receipt
        receipt3 = Receipt.objects.get(pk=receipt3.pk)
        receipt3.perform_refund()


        #=============================== Receipt 4

        # Create receipt3
        receipt4 = Receipt.objects.create(
            user=self.cashier.user,
            store=self.store2,
            discount=self.discount,
            tax=self.tax,
            customer_info={},
            discount_amount=601.00,
            tax_amount=80.00,
            given_amount=3900.00,
            change_amount=800.00,
            subtotal_amount=33520,
            total_amount=34200.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=444,
            receipt_number="113",
            created_date_timestamp=int(self.last_month.timestamp())
        )
        self.create_receipt_payment(receipt4, 4000.00, StorePaymentMethod.CARD_TYPE)


        # Create receipt line1
        units = 6
        ReceiptLine.objects.create(
            receipt=receipt4,
            product=shampoo,
            product_info={'name': shampoo.name},
            price=shampoo.price * units,
            units=units
        )
    
        # Create receipt line2
        units = 12
        ReceiptLine.objects.create(
            receipt=receipt4,
            product=conditioner,
            product_info={'name': conditioner.name},
            price=conditioner.price * units,
            units=units
        )

        receipt4 = Receipt.objects.get(pk=receipt4.pk)
        receipt4.calculate_and_update_total_cost() # Update stock


    
class CreateReceiptsForVariantsTesting(CreateTimeVariablesMixin):
    """
    Creates 3 receipts for profile. manager ang cashier respectively. First 2 are
    in store1 while the last one is in store2
    """

    def __init__(
        self, 
        top_profile,
        product,  
        store1,
        store2
        ):

        self.top_profile = top_profile
        self.product = product

        self.store1 = store1
        self.store2 = store2

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

    def create_receipt_payment(self, receipt, payment_type):

        pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=payment_type
        )
        ReceiptPayment.objects.create(
            receipt=receipt,
            payment_method=pay_method,
            amount=receipt.subtotal_amount
        )

    def create_receipts(self):

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product,
            profile=self.top_profile,
            store1=self.store1,
            store2=self.store2
        )

        # Create products
        small = Product.objects.get(name="Small")
        medium = Product.objects.get(name="Medium")
        large = Product.objects.get(name="Large")

        #=============================== Receipt 1

        # Create receipt1
        receipt1 = Receipt.objects.create(
            user=self.top_profile.user,
            store=self.store1,
            discount=None,
            tax=None,
            customer_info={},
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=17500,
            receipt_number="110",
            created_date_timestamp = int(self.today.timestamp())
        )
        self.create_receipt_payment(receipt1, StorePaymentMethod.CASH_TYPE)


        # Create receipt line1
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=small,
            product_info={'name': small.name},
            price=10500,
            units=7
        )
    
        # Create receipt line2
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=medium,
            product_info={'name': medium.name},
            price=15000,
            units=10
        )

        # Create receipt line3
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=large,
            product_info={'name': large.name},
            price=18000,
            units=12
        )


    #=============================== Receipt 2

        # Create receipt1
        receipt1 = Receipt.objects.create(
            user=self.top_profile.user,
            store=self.store1,
            discount=None,
            tax=None,
            customer_info={},
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=17500,
            receipt_number="111",
            created_date_timestamp = int(self.first_day_this_month.timestamp())
        )
        self.create_receipt_payment(receipt1, StorePaymentMethod.CASH_TYPE)


        # Create receipt line1
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=small,
            product_info={'name': small.name},
            price=4500,
            units=3
        )
    
        # Create receipt line2
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=medium,
            product_info={'name': medium.name},
            price=9000,
            units=6
        )

        # Create receipt line3
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=large,
            product_info={'name': large.name},
            price=7500,
            units=5
        )
