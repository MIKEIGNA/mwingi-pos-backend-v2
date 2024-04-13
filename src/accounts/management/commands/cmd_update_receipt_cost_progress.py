
from django.core.management.base import BaseCommand
import os

from sales.models import Receipt



class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py cmd_update_receipt_cost_progress
    
    """
    help = 'Creates test data'

    def handle(self, *args, **options):

        
    
        print(Receipt.objects.filter(total_cost=0).count())



        

        