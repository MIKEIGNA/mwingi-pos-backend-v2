
from django.core.management.base import BaseCommand
import os
from accounts.tasks.update_dev_db_tasks import update_receipt_lines_tasks1, update_receipt_tasks1

from sales.models import Receipt



class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py cmd_update_receipt_data
    
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


        update_receipt_tasks1.delay()



        



        

        