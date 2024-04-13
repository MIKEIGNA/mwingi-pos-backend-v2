
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from inventories.models.stock_models import StockLevel
from products.models import Product
from sales.models import ReceiptLine
from stores.models import Store

#from .utils.create_sales import create_sales
#from .utils.create_notifications import create_notifications

User = get_user_model()

class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py cmd_update_product_prices
    
    """
    help = 'Creates test data'
  
    def handle(self, *args, **options):

        line = ReceiptLine.objects.order_by('receipt__created_date').last()

        print(line.receipt)
        print(line.receipt.created_date)



        # products = Product.objects.all()

        # for product in products:
        #     line = ReceiptLine.objects.filter(product=product).order_by('receipt__created_date').last()

        #     if line:
        #         product.price = line.price
        #         product.save()


        stores = Store.objects.all()

        for store in stores:
            products = Product.objects.filter(stores=store)

            for product in products:
                line = ReceiptLine.objects.filter(
                    product=product, receipt__store=store).order_by('receipt__created_date').last()

                if line:
                    stock_level = StockLevel.objects.filter(product=product, store=store).first()

                    if stock_level:
                        stock_level.price = line.price
                        stock_level.save()

                        product.save()

