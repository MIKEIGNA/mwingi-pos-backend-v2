from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from django.db.models.aggregates import Count, Sum
from django.db.models.functions import Trunc
from accounts.management.commands.utils.create_users import create_user
from accounts.tasks.local_midnight_task import _RealMidnightTasks, local_midnight_tasks
from inventories.models import StockLevel
from products.models import Product
from profiles.models import Profile, UserGeneralSetting
from PIL import Image
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.storage import default_storage as storage

from sales.models import Receipt, ReceiptLine
from stores.models import StorePaymentMethod


class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py script_runner
    
    Used to run custom scripts to perform various operations
    """
    
    
    
    help = 'Used to run custom scripts to perform various operations'

        
    def handle(self, *args, **options):

        # local_midnight_tasks()

        print("Running script_runner command")
        _RealMidnightTasks()




    


        
        
           
    
