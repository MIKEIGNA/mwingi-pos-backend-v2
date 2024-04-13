
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from accounts.management.commands.utils.create_cashier_users import create_cashier_users
from accounts.management.commands.utils.create_inventory_count import create_inventory_counts
from accounts.management.commands.utils.create_purchase_order import create_purchase_orders
from accounts.management.commands.utils.create_receipts import create_receipts


from accounts.management.commands.utils.create_transfer_orders import create_transfer_orders

from .utils.create_superuser import create_superuser
from .utils.create_users import create_users
from .utils.create_stores import create_stores
from .utils.create_manager_users import create_manager_users
from .utils.create_categories import create_categories
from .utils.create_customers import create_customers
from .utils.create_modifiers import create_modifiers
from .utils.create_taxes import create_taxes
from .utils.create_discounts import create_discounts
from .utils.create_products import create_products
from .utils.create_suppliers import create_suppliers
from .utils.create_stock_adjustments import create_stock_adjustments

from django.utils import timezone
from datetime

#from .utils.create_sales import create_sales
#from .utils.create_notifications import create_notifications

User = get_user_model()

class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py create_sample_data
    
    """
    help = 'Creates test data'
  
    def handle(self, *args, **options):

        # create_superuser()
        # create_users(False)
        # create_stores(False) 
        # create_manager_users(False)
        # create_cashier_users(True)
        # create_categories(True)
        # create_customers(True)
        # create_taxes(True)
        # create_discounts(True)
        # create_modifiers(True)
        # create_products(True)
        # create_suppliers(True)
        # create_stock_adjustments(True)
        # create_transfer_orders(True)
        # create_inventory_counts(True)
        # create_purchase_orders(True)
        # create_receipts()

        # self.stdout.write(self.style.SUCCESS('Successfully prepaired sample data')) 


        self.start_time = timezone.now() - datetime.timedelta(seconds=hours_to_go_back*60)
        self.end_time = timezone.now() - datetime.timedelta(seconds=30)
        
        