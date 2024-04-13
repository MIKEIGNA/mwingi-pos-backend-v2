
from django.core.management.base import BaseCommand

from accounts.tasks.loyverse_receipts_tasks import sync_loyverse_receipts_task
from sales.models import Receipt



class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py cmd_sync_receipts
    
    """
    help = 'Creates test data'
  
    def handle(self, *args, **options):
        sync_loyverse_receipts_task() 

        