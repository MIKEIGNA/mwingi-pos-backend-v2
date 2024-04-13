
from django.core.management.base import BaseCommand
import os
from accounts.tasks.update_dev_db_tasks import update_receipt_lines_tasks1

from sales.models import Receipt



class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py cmd_update_receipt_lines
    
    """
    help = 'Creates test data'

    def handle(self, *args, **options):

        # Update receipt lines so that product_name field can have Product.name
        # using F string
        from sales.models import ReceiptLine
        from django.db.models import F

        from products.models import Product
        from products.models import Category
        from products.models import Tax
        from accounts.models import User


        # Update product_name field
        # products = Product.objects.all()
        # for product in products:
        #     ReceiptLine.objects.filter(
        #         product=product
        #     ).update(product_name=product.name)

        # # Update category_name field
        # categories = Category.objects.all()
        # for category in categories:
        #     ReceiptLine.objects.filter(
        #         product__category=category
        #     ).update(category_name=category.name)

        # # # Update tax_name and tax_rate fields
        # taxes = Tax.objects.all()
        # for tax in taxes:
        #     ReceiptLine.objects.filter(
        #         tax=tax
        #     ).update(
        #         tax_name=tax.name,
        #         tax_rate=tax.rate
        #     )

        # # # Update user_name field
        # users = User.objects.all()
        # for user in users:
        #     ReceiptLine.objects.filter(
        #         user=user
        #     ).update(user_name=user.full_name)


        # Update receipt_number field in ReceiptLine
        # receipt_lines = ReceiptLine.objects.filter(receipt_number="")

        # for receipt_line in receipt_lines:
            
        #     ReceiptLine.objects.filter(
        #         id=receipt_line.id
        #     ).update(
        #         receipt_number=receipt_line.receipt.receipt_number,
        #         refund_for_receipt_number=receipt_line.receipt.refund_for_receipt_number,
        #         store_reg_no=receipt_line.receipt.store.reg_no,
        #         user_reg_no=receipt_line.receipt.user.reg_no,
        #     )

        # print(ReceiptLine.objects.filter(store_reg_no=0).count())

        update_receipt_lines_tasks1.delay()



        



        

        