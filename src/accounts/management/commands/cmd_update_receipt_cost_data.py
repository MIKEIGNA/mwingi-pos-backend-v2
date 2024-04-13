
from django.core.management.base import BaseCommand
import os
from accounts.tasks.update_dev_db_tasks import update_receipt_lines_tasks1, update_receipt_tasks1, update_receipt_total_cost_tasks

from sales.models import Receipt



class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py cmd_update_receipt_cost_data
    
    """
    help = 'Creates test data'

    def handle(self, *args, **options):

        # Update receipt lines so that product_name field can have Product.name
        # using F string

        update_receipt_total_cost_tasks.delay()

        



        

        