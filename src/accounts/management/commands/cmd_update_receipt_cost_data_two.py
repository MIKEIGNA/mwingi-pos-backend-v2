
from django.core.management.base import BaseCommand
import os
from accounts.tasks.update_dev_db_tasks import update_receipt_lines_tasks1, update_receipt_tasks1, update_receipt_total_cost_tasks, update_receipt_total_cost_tasks2

from sales.models import Receipt



class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py cmd_update_receipt_cost_data_two
    
    """
    help = 'Creates test data'

    def handle(self, *args, **options):

        # Update receipt lines so that product_name field can have Product.name
        # using F string

        # update_receipt_total_cost_tasks.delay()


        from celery import group

        receipt_ids = list(Receipt.objects.filter(total_cost=0).values_list('id', flat=True))
        chunk_size = 1000
        receipt_chunks = [receipt_ids[i:i + chunk_size] for i in range(0, len(receipt_ids), chunk_size)]
        tasks = group(update_receipt_total_cost_tasks2.s(chunk) for chunk in receipt_chunks)
        result = tasks.apply_async()
        print(result)



        



        

        