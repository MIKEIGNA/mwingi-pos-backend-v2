from decimal import Decimal
import uuid
from PIL import Image
import datetime
from django.utils import timezone
from django.conf import settings
from api.tests.sales.create_receipts_for_test import (
    CreateReceiptsForTesting2,
    CreateReceiptsForVariantsTesting
)

from core.test_utils.create_product_variants import create_1d_variants, create_2d_variants
from core.test_utils.custom_testcase import TestCase, empty_logfiles
from core.test_utils.date_utils import DateUtils
from core.test_utils.create_user import (
    create_new_cashier_user,
    create_new_manager_user,
    create_new_user,
    create_new_customer
)
from core.test_utils.create_store_models import (
    create_new_store,
    create_new_tax,
    create_new_category,
)
from core.test_utils.log_reader import get_test_firebase_sender_log_content

from profiles.models import Profile
from stores.models import Store, Tax, Category

from sales.models import Receipt, ReceiptLine
from inventories.models import StockLevel

from products.models import (
    ProductBundle,
    ProductCount,
    Product,
    ProductProductionMap,
    ProductVariant,
    ProductVariantOption,
    ProductVariantOptionChoice
)


"""
=========================== Product ===================================
"""

class ProfileTestCase(TestCase):

    def setUp(self):

        self.store1_uuid = uuid.uuid4()
        self.store2_uuid = uuid.uuid4()

        self.product1_uuid = uuid.uuid4()
        self.product2_uuid = uuid.uuid4()
        self.product3_uuid = uuid.uuid4()

        # Create a user1
        self.user = create_new_user('john')

        self.profile = Profile.objects.get(user__email='john@gmail.com')

        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store1.loyverse_store_id = self.store1_uuid
        self.store1.save()


        self.store2 = create_new_store(self.profile, 'Toy Store')
        self.store2.loyverse_store_id = self.store2_uuid
        self.store2.save()

        # Create employee user
        self.manager = create_new_manager_user(
            "gucci", self.profile, self.store1)
        self.cashier = create_new_cashier_user(
            "kate", self.profile, self.store1)

        # Create a tax
        self.tax = create_new_tax(self.profile, self.store1, 'Standard')

        # Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.profile, 'chris')

        # Create a products
        self.create_products()

        # Get the time now (Don't turn it into local)
        now = timezone.now() 

        # Make time aware
        self.today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        self.tomorrow = self.today + datetime.timedelta(days=1)

        self.first_day_this_month = self.today.replace(day=1)

    def create_products(self):

        ####################### Create a product
        self.product1 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Sugar 1kg",
            price=750,
            cost=100,
            sku='sku1',
            barcode='code123',
            track_stock=True,
            loyverse_variant_id = self.product1_uuid
        )

        # Product1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 60
        stock_level.save()

        # Product2
        stock_level = StockLevel.objects.get(store=self.store2, product=self.product1)
        stock_level.units = 40
        stock_level.save()

        ####################### Create a produc2
        self.product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Sugar 2kg",
            price=750,
            cost=120,
            sku='sku1',
            barcode='code123',
            track_stock=True,
            loyverse_variant_id = self.product2_uuid
        )

        # Product1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 100
        stock_level.save()

        # Product2
        stock_level = StockLevel.objects.get(store=self.store2, product=self.product2)
        stock_level.units = 80
        stock_level.save()


        ####################### Create a product3
        self.product3 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="MM Nafuu bale",
            price=750,
            cost=130,
            sku='sku1',
            barcode='code123',
            track_stock=True,
            loyverse_variant_id = self.product3_uuid
        )

        # Product1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product3)
        stock_level.units = 150
        stock_level.save()

        # Product2
        stock_level = StockLevel.objects.get(store=self.store2, product=self.product3)
        stock_level.units = 110
        stock_level.save()

    def test_product_fields_verbose_names(self):
        
        result = {
            'inventory_levels': [
                {
                    'in_stock': '60.00', 
                    'store_id': str(self.store1.loyverse_store_id), 
                    'variant_id': str(self.product1.loyverse_variant_id)
                }, 
                {
                    'in_stock': '40.00', 
                    'store_id': str(self.store2.loyverse_store_id), 
                    'variant_id': str(self.product1.loyverse_variant_id)
                }, 
                {
                    'in_stock': '80.00', 
                    'store_id': str(self.store2.loyverse_store_id), 
                    'variant_id': str(self.product2.loyverse_variant_id)
                }, 
                {
                    'in_stock': '100.00', 
                    'store_id': str(self.store1.loyverse_store_id), 
                    'variant_id': str(self.product2.loyverse_variant_id)
                }, 
                {
                    'in_stock': '110.00', 
                    'store_id': str(self.store2.loyverse_store_id), 
                    'variant_id': str(self.product3.loyverse_variant_id)
                }, 
                {
                    'in_stock': '150.00', 
                    'store_id': str(self.store1.loyverse_store_id), 
                    'variant_id': str(self.product3.loyverse_variant_id)
                }
            ]
        }

        profile_levels = self.profile.get_inventory_levels()['inventory_levels']

        for i in range(6): 
            self.assertTrue(result['inventory_levels'][i] in profile_levels)
