
import random
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from accounts.create_permissions import CreatePermission, GetPermission
from accounts.models import UserGroup

from inventories.models import StockLevel

class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py update_stock_levels
    
    Used to create a superuser
    """
    help = "Updates top user\'s perms"

        
    def handle(self, *args, **options):

        stocks = StockLevel.objects.all()

        for stock in stocks:
            stock.units = random.randint(150, 1000)
            stock.save()
           
    