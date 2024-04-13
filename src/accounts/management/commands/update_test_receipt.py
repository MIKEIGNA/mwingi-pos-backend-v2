
from pprint import pprint
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
import requests
from accounts.create_permissions import CreatePermission, GetPermission
from accounts.management.commands.utils.create_receipts import create_receipt_payment
from accounts.models import UserGroup
from products.models import Product
from sales.models import Receipt, ReceiptLine
from stores.models import Store, StorePaymentMethod
from django.utils import timezone
from django.conf import settings
from rest_framework.authtoken.models import Token

class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py update_test_receipt
    
    Used to create a superuser
    """
    help = "Updates top user\'s perms"

    def handle(self, *args, **options):

        # line1 = ReceiptLine.objects.get(reg_no=496923491060) # Units 5
        # line1.refunded_units = 2
        # line1.save()


        # line2 = ReceiptLine.objects.get(reg_no=435066078528) # Units 3
        # line3 = ReceiptLine.objects.get(reg_no=436037231012) # Units 1
        # line4 = ReceiptLine.objects.get(reg_no=440381897560) # Units 5
        
        # line5 = ReceiptLine.objects.get(reg_no=365816214660) # Units 2
        # line5.refunded_units = 1
        # line5.save()



        # line6 = ReceiptLine.objects.get(reg_no=438051456886) # Units 1


        # line6.receipt.save()

        store = Store.objects.get(reg_no=286398301783)
        product1 = Product.objects.get(reg_no=462726384731)

        num = 55

        # receipt1 = Receipt.objects.create(
        #     shift=None,
        #     user=store.profile.user,
        #     store=store,
        #     discount=None,
        #     tax=None,
        #     customer=None,
        #     customer_info={},
        #     discount_amount=401.00,
        #     tax_amount=60.00,
        #     given_amount=2600.00,
        #     change_amount=500.00,
        #     subtotal_amount=int(f'1000'),
        #     total_amount=1699.00,
        #     transaction_type=Receipt.MONEY_TRANS,
        #     payment_completed=True,
        #     item_count=17,
        #     local_reg_no=num,
        #     receipt_number=num,
        #     created_date_timestamp = int(timezone.now().timestamp())
        # )
        # create_receipt_payment(
        #     store.profile,
        #     receipt1, 
        #     receipt1.subtotal_amount, 
        #     StorePaymentMethod.CASH_TYPE
        # )

        # # Create receipt line1
        # rl1 = ReceiptLine.objects.create(
        #     receipt=receipt1,
        #     product=product1,
        #     modifier_options_info={},
        #     product_info={'name': product1.name},
        #     price=1750,
        #     discount_amount=401.00,
        #     units=7
        # )

        receipt = Receipt.objects.get(receipt_number='299-13665')

        # receipt.send_firebase_update_message(True)

        receipt.send_firebase_refund_message()

        # receipt.send_firebase_refund_message()

        # # receipt1.save()
        # url = f'http://127.0.0.1:8000/api/pos/internal/receipts/{receipt.store.reg_no}/?reg_no={receipt.reg_no}'

        # print(url)

        # access_token= Token.objects.filter(user__profile=receipt.store.profile).first()

        # if access_token:
        #     my_headers = {'Authorization' : f'Token lllllllllllllllllllllllll'}
        #     response = requests.get(
        #         url=url, 
        #         # headers=my_headers,
        #         timeout=settings.PYTHON_REQUESTS_TIMEOUT
        #     )

        #     pprint(response.json())







        
        self.stdout.write(self.style.SUCCESS('Successfully updated top user perms')) 
        
           
    