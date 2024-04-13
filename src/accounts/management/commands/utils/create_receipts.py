

import os
from django.utils import timezone

from products.models import Modifier, ModifierOption, Product
from profiles.models import Customer, Profile
from sales.models import Receipt, ReceiptLine, ReceiptPayment
from stores.models import Discount, Store, StorePaymentMethod, Tax


def create_receipt_payment(profile, receipt, amount, payment_type):

    pay_method = StorePaymentMethod.objects.get(
        profile=profile,
        payment_type=payment_type
    )
    ReceiptPayment.objects.create(
        receipt=receipt,
        payment_method=pay_method,
        amount=amount
    )


def bulk_receipt_creator(profile, num, ident):

    # Get the time now (Don't turn it into local)
    now = timezone.now()
    
    # Make time aware
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    #print(dir(self.today))
    #print(self.today.strftime("%B, %d, %Y"))
    #print(self.today.strftime("%Y-%m-%d"))

    first_day_this_month = today.replace(day=1)

    store1 = Store.objects.filter(profile=profile).order_by('id').first()
    store2 = Store.objects.filter(profile=profile).order_by('id').last()

    discount1 = Discount.objects.filter(profile=profile).order_by('id').first()
    discount2 = Discount.objects.filter(profile=profile).order_by('id').last()

    tax1 = Tax.objects.filter(profile=profile).order_by('id').first()
    tax2 = Tax.objects.filter(profile=profile).order_by('id').last()

    customer1 = Customer.objects.filter(profile=profile).order_by('id').first()

    product1 = Product.objects.filter(stores=store1).order_by('id').first()
    product2 = Product.objects.filter(stores=store1).order_by('id').last()

    modifier1 = Modifier.objects.filter(stores=store1).order_by('id').first()
    modifier2 = Modifier.objects.filter(stores=store1).order_by('id').last()

    modifier1_options_data = list(ModifierOption.objects.filter(
        modifier=modifier1
    ).values_list('id', 'name', 'price'))

    modifier1_options = [l[0] for l in modifier1_options_data ]
    modifier_options_info1 = [f'{l[1]} ({l[2]}.00)' for l in modifier1_options_data]


    modifier2_options_data = list(ModifierOption.objects.filter(
        modifier=modifier2
    ).values_list('id', 'name', 'price'))

    modifier2_options = [l[0] for l in modifier2_options_data ]
    modifier_options_info2 = [f'{l[1]} ({l[2]}.00)' for l in modifier2_options_data]


    num = num//2

    for i in range(num):
        
        # ----------------- Receipt 1

        # Create receipt1
        receipt1 = Receipt.objects.create(
            user=profile.user,
            store=store1,
            discount=discount1,
            tax=tax1,
            customer=customer1,
            customer_info={
                'name': customer1.name, 
                'reg_no': customer1.reg_no
            },
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=int(f'1000{i}'),
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            item_count=17,
            local_reg_no=int(f'11{i}'),
            created_date_timestamp = int(today.timestamp())
        )
        create_receipt_payment(
            profile,
            receipt1, 
            receipt1.subtotal_amount, 
            StorePaymentMethod.CASH_TYPE
        )

        # Create receipt line1
        rl1 = ReceiptLine.objects.create(
            receipt=receipt1,
            product=product1,
            modifier_options_info=modifier_options_info1,
            product_info={'name': product1.name},
            price=1750,
            discount_amount=401.00,
            units=7
        )

        rl1.modifier_options.add(*modifier1_options)


        # Create receipt line2
        rl2 = ReceiptLine.objects.create(
            receipt=receipt1,
            product=product2,
            modifier_options_info=modifier_options_info2,
            product_info={'name': product2.name},
            price=2500,
            units=10
        )

        rl2.modifier_options.add(*modifier2_options)
        
        
        # ----------------- Receipt 2

        # Create receipt1
        receipt2 = Receipt.objects.create(
            user=profile.user,
            store=store1,
            discount=discount1,
            tax=tax1,
            customer=customer1,
            customer_info={
                'name': customer1.name, 
                'reg_no': customer1.reg_no
            },
            discount_amount=501.00,
            tax_amount=80.00,
            subtotal_amount=int(f'4000{i}'),
            total_amount=3599.00,
            transaction_type=Receipt.MULTIPLE_TRANS,
            payment_completed=True,
            item_count=120,
            local_reg_no=int(f'22{i}'),
            created_date_timestamp = int(today.timestamp())
        )
        create_receipt_payment(
            profile,
            receipt2, 
            1000.00, 
            StorePaymentMethod.CASH_TYPE
        )
        create_receipt_payment(
            profile,
            receipt2, 
            2599.00, 
            StorePaymentMethod.MPESA_TYPE
        )

        # Create receipt line1
        rl1 = ReceiptLine.objects.create(
            receipt=receipt2,
            product=product1,
            modifier_options_info=modifier_options_info1,
            product_info={'name': product1.name},
            price=1750,
            discount_amount=401.00,
            units=7
        )

        rl1.modifier_options.add(*modifier1_options)
    
        # Create receipt line2
        rl2 = ReceiptLine.objects.create(
            receipt=receipt2,
            product=product2,
            modifier_options_info=modifier_options_info2,
            product_info={'name': product2.name},
            price=2500,
            units=10
        )

        rl2.modifier_options.add(*modifier2_options)

 
        #=============================== Receipt 3

        # Create receipt1
        receipt3 = Receipt.objects.create(
            user=profile.user,
            store=store1,
            discount=discount2,
            tax=tax2,
            customer_info={},
            discount_amount=501.00,
            tax_amount=70.00,
            given_amount=2900.00,
            change_amount=700.00,
            subtotal_amount=int(f'3000{i}'),
            total_amount=2599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            item_count=25,
            local_reg_no=int(f'33{i}'),
            created_date_timestamp = int(first_day_this_month.timestamp())
        )
        create_receipt_payment(
            profile,
            receipt3, 
            receipt3.subtotal_amount, 
            StorePaymentMethod.CARD_TYPE
        )

        # Create receipt line1
        rl1 = ReceiptLine.objects.create(
            receipt=receipt3,
            product=product1,
            modifier_options_info=modifier_options_info1,
            product_info={'name': product1.name},
            price=2750,
            units=10
        )

        rl1.modifier_options.add(*modifier1_options)
    
        # Create receipt line2
        rl2 = ReceiptLine.objects.create(
            receipt=receipt3,
            product=product2,
            modifier_options_info=modifier_options_info2,
            product_info={'name': product2.name},
            price=3500,
            units=15
        )

        rl2.modifier_options.add(*modifier2_options)

        # Refund the receipt
        receipt3.perform_refund()



        #=============================== Receipt 4
        receipt4 = Receipt.objects.create(
            user=profile.user,
            store=store1,
            discount=discount2,
            tax=tax2,
            customer_info={},
            discount_amount=701.00,
            tax_amount=70.00,
            given_amount=2900.00,
            change_amount=700.00,
            subtotal_amount=int(f'5000{i}'),
            total_amount=3599.00,
            transaction_type=Receipt.DEBT_TRANS,
            payment_completed=False,
            item_count=25,
            local_reg_no=int(f'44{i}'),
            created_date_timestamp = int(first_day_this_month.timestamp())
        )
        create_receipt_payment(
            profile,
            receipt4, 
            receipt4.subtotal_amount, 
            StorePaymentMethod.DEBT_TYPE
        )

        # Create receipt line1
        rl1 = ReceiptLine.objects.create(
            receipt=receipt4,
            product=product1,
            modifier_options_info=modifier_options_info1,
            product_info={'name': product1.name},
            price=2750,
            units=10
        )

        rl1.modifier_options.add(*modifier1_options)
    
        # Create receipt line2
        rl2 = ReceiptLine.objects.create(
            receipt=receipt4,
            product=product2,

            product_info={'name': product2.name},
            price=3500,
            units=15
        )

        cash = StorePaymentMethod.objects.get(
            profile=profile,
            payment_type=StorePaymentMethod.CASH_TYPE
        )

        receipt4.perform_credit_payment_completed(
            [
                {
                    'payment_method_reg_no': cash.reg_no,
                    'amount': receipt4.subtotal_amount
                }
            ]
        )
        
    
        #=============================== Receipt 5
        receipt5 = Receipt.objects.create(
            user=profile.user,
            store=store1,
            discount=discount2,
            tax=tax2,
            customer_info={},
            discount_amount=701.00,
            tax_amount=70.00,
            given_amount=2900.00,
            change_amount=700.00,
            subtotal_amount=int(f'6000{i}'),
            total_amount=3599.00,
            transaction_type=Receipt.DEBT_TRANS,
            payment_completed=False,
            item_count=25,
            local_reg_no=int(f'55{i}'),
            created_date_timestamp = int(first_day_this_month.timestamp())
        )
        create_receipt_payment(
            profile,
            receipt5, 
            receipt5.subtotal_amount, 
            StorePaymentMethod.DEBT_TYPE
        )

        # Create receipt line1
        rl1 = ReceiptLine.objects.create(
            receipt=receipt5,
            product=product1,
            modifier_options_info=modifier_options_info1,
            product_info={'name': product1.name},
            price=2750,
            units=10
        )

        rl1.modifier_options.add(*modifier1_options)
    
        # Create receipt line2
        rl2 = ReceiptLine.objects.create(
            receipt=receipt5,
            product=product2,

            product_info={'name': product2.name},
            price=3500,
            units=15
        )
  
    
def create_receipts(count=2):

    Receipt.objects.all().delete()
    ReceiptLine.objects.all().delete()
    ReceiptPayment.objects.all().delete()

    try:

        profile1 = Profile.objects.get(user__email=os.environ.get("FIRST_USER_EMAIL"))
        bulk_receipt_creator(profile1, count, 'b')

        profile2 = Profile.objects.get(user__email='jack@gmail.com')
        # bulk_receipt_creator(profile2, count, 'j')
        
    except Exception as e:
        print("Receipt cant be created since ", e)