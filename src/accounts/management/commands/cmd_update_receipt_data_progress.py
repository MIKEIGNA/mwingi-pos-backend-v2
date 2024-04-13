
from django.core.management.base import BaseCommand
import os

from sales.models import Receipt



class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py cmd_update_receipt_data_progress
    
    """
    help = 'Creates test data'

    def handle(self, *args, **options):

        # Update receipt lines so that product_name field can have Product.name
        # using F string
        from sales.models import ReceiptLine
    
        print(Receipt.objects.filter(user_reg_no=0).count())
        print(Receipt.objects.filter(store_reg_no=0).count())



        

        