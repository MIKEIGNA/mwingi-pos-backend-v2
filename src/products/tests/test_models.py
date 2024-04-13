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

class ProductTestCase(TestCase):

    def setUp(self):

        # Create a user1
        self.user = create_new_user('john')

        self.profile = Profile.objects.get(user__email='john@gmail.com')

        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store2 = create_new_store(self.profile, 'Toy Store')

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
        self.create_a_normal_product()

        # Get the time now (Don't turn it into local)
        now = timezone.now() 

        # Make time aware
        self.today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        self.tomorrow = self.today + datetime.timedelta(days=1)

        self.first_day_this_month = self.today.replace(day=1)

    def create_a_normal_product(self):

        # Create a products
        self.product = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=750,
            cost=120,
            sku='sku1',
            barcode='code123',
            track_stock=True
        )

        self.product.stores.add(self.store1)

    def create_product_with_receipts(self):

        CreateReceiptsForTesting2(
            top_profile=self.profile,
            manager=self.manager.employeeprofile,
            cashier=self.cashier.employeeprofile,
            discount=None,
            tax=None,
            store1=self.store1,
            store2=self.store2
        ).create_receipts()

    def create_variant_product_with_receipts(self):

        # Create 3 variants for master product and sales
        CreateReceiptsForVariantsTesting(
            top_profile=self.profile,
            product=self.product,
            store1=self.store1,
            store2=self.store2
        ).create_receipts()

    def create_a_bundle_product(self):

        product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )
        product2.stores.add(self.store1)


        # Create master product with 2 bundles
        shampoo_bundle = ProductBundle.objects.create(
            product_bundle=self.product,
            quantity=30
        )

        conditoner_bundle = ProductBundle.objects.create(
            product_bundle=product2,
            quantity=25
        )

        master_product = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Hair Bundle",
            price=35000,
            cost=30000,
            barcode='code123'
        )
        master_product.bundles.add(shampoo_bundle, conditoner_bundle)

    def create_a_production_product(self):

        sugar_sack = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Sugar 50kg Sack",
            price=10000,
            cost=9000,
            barcode='code1'
        )

        pagackaged_sugar_2kg = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Packaged Sugar 2kg",
            price=400,
            cost=360,
            barcode='code2'
        )

        pagackaged_sugar_1kg = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Packaged Sugar 1kg",
            price=200,
            cost=180,
            barcode='code3'
        )

        # Create master product with 2 bundles
        pagackaged_sugar_1kg_map = ProductProductionMap.objects.create(
            name="Packaged Sugar 1kg",
            product_map=pagackaged_sugar_1kg,
            quantity=50
        )
        
        pagackaged_sugar_2kg_map = ProductProductionMap.objects.create(
            name="Packaged Sugar 2kg",
            product_map=pagackaged_sugar_2kg,
            quantity=25
        )

        sugar_sack.productions.add(pagackaged_sugar_1kg_map, pagackaged_sugar_2kg_map)


        # Master product stock levels
        stock_level = StockLevel.objects.get(store=self.store1, product=sugar_sack)
        stock_level.units = 34
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=sugar_sack)
        stock_level.units = 30
        stock_level.save()

        
        # Shampoo stock level
        stock_level = StockLevel.objects.get(store=self.store1, product=pagackaged_sugar_2kg)
        stock_level.units = 24
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=pagackaged_sugar_2kg)
        stock_level.units = 20
        stock_level.save()


        # Conditioner stock levels
        stock_level = StockLevel.objects.get(store=self.store1, product=pagackaged_sugar_1kg)
        stock_level.units = 14
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=pagackaged_sugar_1kg)
        stock_level.units = 10
        stock_level.save()
    
    def test_product_fields_verbose_names(self):

        p = Product.objects.get(name="Shampoo")

        self.assertEqual(p._meta.get_field('image').verbose_name, 'image')
        self.assertEqual(p._meta.get_field('color_code').verbose_name, 'color code')
        self.assertEqual(p._meta.get_field('name').verbose_name, 'name')
        self.assertEqual(p._meta.get_field('cost').verbose_name, 'cost')
        self.assertEqual(p._meta.get_field('price').verbose_name, 'price')
        self.assertEqual(p._meta.get_field('average_price').verbose_name, 'average price')
        self.assertEqual(p._meta.get_field('sku').verbose_name, 'sku')
        self.assertEqual(p._meta.get_field('barcode').verbose_name, 'barcode')
        self.assertEqual(p._meta.get_field('sold_by_each').verbose_name, 'sold by each')
        self.assertEqual(p._meta.get_field('is_bundle').verbose_name, 'is bundle')
        self.assertEqual(p._meta.get_field('track_stock').verbose_name, 'track stock')
        self.assertEqual(p._meta.get_field('variant_count').verbose_name, 'variant count')
        self.assertEqual(p._meta.get_field('is_variant_child').verbose_name, 'is variant child')
        self.assertEqual(p._meta.get_field('show_product').verbose_name, 'show product')
        self.assertEqual(p._meta.get_field('show_image').verbose_name, 'show image')
        self.assertEqual(p._meta.get_field('tax_rate').verbose_name, 'tax rate')
        self.assertEqual(p._meta.get_field('reg_no').verbose_name, 'reg no')
        self.assertEqual(p._meta.get_field('loyverse_variant_id').verbose_name, 'loyverse variant id')
        self.assertEqual(p._meta.get_field('created_date').verbose_name, 'created date')

        fields = ([field.name for field in Product._meta.fields])

        self.assertEqual(len(fields), 28)

    def test_product_fields_after_it_has_been_created(self):
        """
        Product fields

        Ensure a product has the right fields after it has been created
        """
        p = Product.objects.get(name="Shampoo")

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(p.profile, self.profile)
        self.assertEqual(p.stores.all().count(), 2)
        self.assertEqual(p.tax, self.tax)
        self.assertEqual(p.category, self.category)
        self.assertEqual(p.bundles.all().count(), 0)
        self.assertEqual(p.productions.all().count(), 0)
        self.assertEqual(p.modifiers.all().count(), 0)
        self.assertEqual(p.image.url, f'/media/images/products/{p.reg_no}_.jpg')
        self.assertEqual(p.color_code, settings.DEFAULT_COLOR_CODE)
        self.assertEqual(p.name, "Shampoo")
        self.assertEqual(p.cost, 120.00)
        self.assertEqual(p.price, 750.00)
        self.assertEqual(p.average_price, Decimal('750.00'))
        self.assertEqual(p.sku, 'sku1')
        self.assertEqual(p.barcode, 'code123')
        self.assertEqual(p.sold_by_each, True)
        self.assertEqual(p.is_bundle, False)
        self.assertEqual(p.track_stock, True)
        self.assertEqual(p.variant_count, 0)
        self.assertEqual(p.is_variant_child, False)
        self.assertEqual(p.show_product, True)
        self.assertEqual(p.show_image, False)
        self.assertTrue(p.reg_no > 100000)  # Check if we have a valid reg_no 1757024354
        self.assertEqual((p.created_date).strftime("%B, %d, %Y"), today)
  
    def test_product_fields_after_it_has_been_created_with_a_master_product(self):
        """
        Product fields

        Ensure a product has the right fields after it has been created as a master bundle
        """

        # Create bundles
        self.create_a_bundle_product()

        master_product = Product.objects.get(name="Hair Bundle")

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(master_product.profile, self.profile)
        self.assertEqual(master_product.tax, self.tax)
        self.assertEqual(master_product.category, self.category)
        self.assertEqual(master_product.bundles.all().count(), 2)
        self.assertEqual(master_product.modifiers.all().count(), 0)
        self.assertEqual(
            master_product.image.url, 
            f'/media/images/products/{master_product.reg_no}_.jpg'
        )
        self.assertEqual(master_product.color_code, settings.DEFAULT_COLOR_CODE)
        self.assertEqual(master_product.name, "Hair Bundle")
        self.assertEqual(master_product.cost, 30000)
        self.assertEqual(master_product.price, 35000)
        self.assertEqual(master_product.barcode, 'code123')
        self.assertEqual(master_product.sold_by_each, True)
        self.assertEqual(master_product.is_bundle, True)
        self.assertEqual(master_product.track_stock, True)
        self.assertEqual(master_product.variant_count, 0)
        self.assertEqual(master_product.is_variant_child, False)
        self.assertEqual(master_product.show_product, True)
        self.assertEqual(master_product.show_image, False)
        # Check if we have a valid reg_no
        self.assertTrue(master_product.reg_no > 100000)
        self.assertEqual(
            (master_product.created_date).strftime("%B, %d, %Y"), today)

    def test_variant_product_parent_fields(self):

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )

        p = Product.objects.get(name="Shampoo")

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(p.profile, self.profile)
        self.assertEqual(p.tax, self.tax)
        self.assertEqual(p.category, self.category)
        self.assertEqual(p.bundles.all().count(), 0)
        self.assertEqual(p.modifiers.all().count(), 0)
        self.assertEqual(p.image.url, f'/media/images/products/{p.reg_no}_.jpg')
        self.assertEqual(p.color_code, settings.DEFAULT_COLOR_CODE)
        self.assertEqual(p.name, "Shampoo")
        self.assertEqual(p.cost, 120.00)
        self.assertEqual(p.price, 750.00)
        self.assertEqual(p.sku, 'sku1')
        self.assertEqual(p.barcode, 'code123')
        self.assertEqual(p.sold_by_each, True)
        self.assertEqual(p.is_bundle, False)
        self.assertEqual(p.track_stock, True)
        self.assertEqual(p.variant_count, 3)
        self.assertEqual(p.is_variant_child, False)
        self.assertEqual(p.show_product, True)
        self.assertEqual(p.show_image, False)
        self.assertTrue(p.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual((p.created_date).strftime("%B, %d, %Y"), today)

    def test_variant_product_child_fields(self):

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )

        p = Product.objects.get(name="Small")

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(p.profile, self.profile)
        self.assertEqual(p.bundles.all().count(), 0)
        self.assertEqual(p.modifiers.all().count(), 0)
        self.assertEqual(p.image.url, f'/media/images/products/{p.reg_no}_.jpg')
        self.assertEqual(p.color_code, settings.DEFAULT_COLOR_CODE)
        self.assertEqual(p.name, "Small")
        self.assertEqual(p.cost, 800)
        self.assertEqual(p.price, 1500)
        self.assertEqual(p.sku, '')
        self.assertEqual(p.barcode, 'code123')
        self.assertEqual(p.sold_by_each, True)
        self.assertEqual(p.is_bundle, False)
        self.assertEqual(p.track_stock, True)
        self.assertEqual(p.variant_count, 0)
        self.assertEqual(p.is_variant_child, True)
        self.assertEqual(p.show_product, True)
        self.assertEqual(p.show_image, False)
        self.assertTrue(p.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual((p.created_date).strftime("%B, %d, %Y"), today)

    def test_if_a_variant_product_cant_be_assigned_tax_and_category(self):

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )


        p = Product.objects.get(name="Small")
        p.tax = self.tax
        p.category= self.category
        p.save()

        self.assertEqual(p.tax, None)
        self.assertEqual(p.category, None)

    def test_if_parent_product_track_stock_will_be_mirrored_by_variant_products(self):

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )

        parent_product = Product.objects.get(name="Shampoo")
        self.assertEqual(parent_product.track_stock, True)

        variants = Product.objects.filter(productvariant__product=parent_product)
        for v in variants:
            self.assertEqual(v.track_stock, True)

        # Turn of track stock
        parent_product.track_stock = False
        parent_product.save()

        parent_product = Product.objects.get(name="Shampoo")
        self.assertEqual(parent_product.track_stock, True)

        variants = Product.objects.filter(productvariant__product=parent_product)
        for v in variants:
            self.assertEqual(v.track_stock, True)

    def test_if_prodcut_can_be_created_without_category(self):

        # Create a products
        self.product = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            name="Gel",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123'
        )

        self.assertEqual(Product.objects.all().count(), 2)

    def test_if_product_creation_will_update_category_product_count(self):

        category = Category.objects.get(name='Hair')
        self.assertEqual(category.product_count, 1)

    
    def test_if_product_deletion_will_update_category_product_count(self):

        category = Category.objects.get(name='Hair')
        self.assertEqual(category.product_count, 1)

        self.product.delete()

        category = Category.objects.get(name='Hair')
        self.assertEqual(category.product_count, 0)

    def test_if_product_category_change_to_none_will_update_category_product_count(self):

        category = Category.objects.get(name='Hair')
        self.assertEqual(category.product_count, 1)

        # Replace product's category to Noe
        self.product.category = None
        self.product.save()

        category1 = Category.objects.get(name='Hair')
        self.assertEqual(category1.product_count, 0)

    def test_if_product_category_change_will_update_both_categorys_product_count(self):

        create_new_category(self.profile, 'Face')

        category1 = Category.objects.get(name='Hair')
        self.assertEqual(category1.product_count, 1)

        category2 = Category.objects.get(name='Face')
        self.assertEqual(category2.product_count, 0)

        # Replace product's category from category1 to category2
        self.product.category = category2
        self.product.save()

        category1 = Category.objects.get(name='Hair')
        self.assertEqual(category1.product_count, 0)

        category2 = Category.objects.get(name='Face')
        self.assertEqual(category2.product_count, 1)

    def test__str__method(self):
        p = Product.objects.get(name="Shampoo")
        self.assertEqual(str(p), 'Shampoo')

    def test_get_name_method(self):
        p = Product.objects.get(name="Shampoo")
        self.assertEqual(p.get_name(), "Shampoo")

    def test_get_profile_method(self):
        p = Product.objects.get(name="Shampoo")
        self.assertEqual(p.get_profile(), self.profile)

    def test_get_currency_method(self):
        p = Product.objects.get(name="Shampoo")
        self.assertEqual(p.get_currency(), self.profile.get_currency())

    def test_get_price_and_currency_method(self):
        
        p = Product.objects.get(name="Shampoo")
        
        self.assertEqual(p.get_price_and_currency(), "Usd 750.00")
        
    def test_get_price_and_currency_desc_method(self):
        
        p = Product.objects.get(name="Shampoo")
        
        self.assertEqual(p.get_price_and_currency_desc(), "Price: Usd 750.00")
        
    def test_get_currency_initials_method(self):
        p = Product.objects.get(name="Shampoo")
        self.assertEqual(p.get_currency_initials(), "Usd")

    def test_get_category_data_method(self):

        # When product has category
        p = Product.objects.get(name="Shampoo")

        data = {'name': 'Hair', 'reg_no': self.category.reg_no}

        self.assertEqual(p.get_category_data(), data)

        # When product has no category
        p = Product.objects.get(name="Shampoo")
        p.category = None
        p.save()

        self.assertEqual(p.get_category_data(), {})

    def test_get_tax_data_method(self):

        # When product has tax
        p = Product.objects.get(name="Shampoo")
        
        data = {
            'name': 'Standard', 
            'rate': '20.05', 
            'reg_no': self.tax.reg_no
        }
        self.assertEqual(p.get_tax_data(), data)


        # When product has no tax
        p = Product.objects.get(name="Shampoo")
        p.tax = None
        p.save()

        self.assertEqual(p.get_tax_data(), {})

    def test_get_sales_count_method(self):

        #######  Confirm get_sales_count when a product does not have sales
        product1 = Product.objects.get(profile=self.profile, name="Shampoo")
        self.assertEqual(product1.get_sales_count(), 0)

        # Product 1
        product1 = Product.objects.get(profile=self.profile, name="Shampoo")

        # Create receipt1
        receipt1 = Receipt.objects.create(
            user=self.user,
            store=self.store1,
            customer=self.customer,
            customer_info={
                'name': self.customer.name, 
                'reg_no': self.customer.reg_no
            },
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            item_count=11,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            receipt_number='22-00'
        )

        # Create receiptline1
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=product1,
            product_info={'name': product1.name},
            units=7
        )

        # Create receiptline2
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=product1,
            product_info={'name': product1.name},
            units=5
        )


        # Product 2
        Product.objects.create(
            profile=self.profile,
            category=self.category,
            name="Gel",
            price=2500,
            cost=1000,
            barcode='code123',
        )

        product2 = Product.objects.get(profile=self.profile, name="Gel")

        # Create receipt2
        receipt2 = Receipt.objects.create(
            user=self.user,
            store=self.store1,
            customer=self.customer,
            customer_info={
                'name': self.customer.name, 
                'reg_no': self.customer.reg_no
            },
            discount_amount=501.00,
            tax_amount=70.00,
            given_amount=3500.00,
            change_amount=600.00,
            subtotal_amount=3000,
            total_amount=2599.00,
            item_count=21,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            receipt_number='22-01'
        )

        # Create receipt line3
        ReceiptLine.objects.create(
            receipt=receipt2,
            product=product2,
            product_info={'name': product2.name},
            units=7
        )

        #######  Confirm get_sales_count when a product has sales
        product1 = Product.objects.get(profile=self.profile, name="Shampoo")
        self.assertEqual(product1.get_sales_count(), 12)

    def test_get_sales_total_method(self):
        
        #######  Confirm get_sales_total when a product does not have sales
        product1 = Product.objects.get(profile=self.profile, name="Shampoo")
        self.assertEqual(product1.get_sales_total(), f'{self.profile.get_currency_initials()} 0')

        # Product 1
        product1 = Product.objects.get(profile=self.profile, name="Shampoo")

        # Create receipt1
        receipt1 = Receipt.objects.create(
            user=self.user,
            store=self.store1,
            customer=self.customer,
            customer_info={
                'name': self.customer.name, 
                'reg_no': self.customer.reg_no
            },
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            item_count=11,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            receipt_number='22-00'
        )

        # Create receipt line1
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=product1,
            product_info={'name': product1.name},
            price=1750,
            units=7
        )

        # Create receipt line2
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=product1,
            product_info={'name': product1.name},
            price=1250,
            units=5)

        # Product 2
        Product.objects.create(
            profile=self.profile,
            category=self.category,
            name="Gel",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        product2 = Product.objects.get(profile=self.profile, name="Gel")

        # Create receipt2
        receipt2 = Receipt.objects.create(
            user=self.user,
            store=self.store1,
            customer=self.customer,
            customer_info={
                'name': self.customer.name, 
                'reg_no': self.customer.reg_no
            },
            discount_amount=501.00,
            tax_amount=70.00,
            given_amount=3500.00,
            change_amount=600.00,
            subtotal_amount=3000,
            total_amount=2599.00,
            item_count=21,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            receipt_number='22-01'
        )

        # Create receipt line3
        ReceiptLine.objects.create(
            receipt=receipt2,
            product=product2,
            product_info={'name': product2.name},
            price=1750,
            units=7)

        #######  Confirm get_sales_pricet when a product has sales
        product1 = Product.objects.get(profile=self.profile, name="Shampoo")

        result = f'{self.profile.get_currency_initials()} 3000.00'

        self.assertEqual(product1.get_sales_total(), result)
    
    def test_get_product_view_stock_level_list_method_from_a_single_store(self):

        # First delete all products
        #Product.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 100
        stock_level.save()

        p = Product.objects.get(name="Shampoo")

        result = [
            {
                'store_name': 'Computer Store', 
                'store_reg_no': self.store1.reg_no, 
                'minimum_stock_level': '0', 
                'units': '100.00', 
                'is_sellable': True,
                'price': '750.00'
            }, 
            {
                'store_name': 'Toy Store', 
                'store_reg_no': self.store2.reg_no, 
                'minimum_stock_level': '0', 
                'units': '0.00', 
                'is_sellable': True,
                'price': '750.00'
            }
        ]

        self.assertEqual(p.get_product_view_stock_level_list(), result)

    def test_get_inventory_valuation_method_from_a_single_store(self):

        # First delete all products
        #Product.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 100
        stock_level.inlude_in_price_calculations=True
        stock_level.price = 700
        stock_level.save()

        p = Product.objects.get(name="Shampoo")

        result = {
            'name': 'Shampoo', 
            'in_stock': '100.00', 
            'cost': '120.00', 
            'inventory_value': '12000.00', 
            'retail_value': '70000.00', 
            'potential_profit': '58000.00', 
            'margin': '82.86', 
            'variants': None
        }

        store_reg_nos = [store.reg_no for store in [self.store1]]

        self.assertEqual(p.get_inventory_valuation(store_reg_nos), result)

    def test_get_inventory_valuation_method_from_multiple_stores(self):

        # First delete all products
        #Product.objects.all().delete()

        # Update stock level for store 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 100
        stock_level.inlude_in_price_calculations=True
        stock_level.price = 700
        stock_level.save()

        # Update stock level for store 2 
        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.units = 100
        stock_level.inlude_in_price_calculations=True
        stock_level.price = 600
        stock_level.save()

        p = Product.objects.get(name="Shampoo")

        result = {
            'name': 'Shampoo', 
            'in_stock': '200.00', 
            'cost': '120.00', 
            'inventory_value': '24000.00', 
            'retail_value': '130000.00', 
            'potential_profit': '106000.00', 
            'margin': '81.54', 
            'variants': None
        }

        store_reg_nos = [store.reg_no for store in [self.store1, self.store2]]

        self.assertEqual(p.get_inventory_valuation(store_reg_nos), result)

    def test_test_get_inventory_valuation_method_when_all_a_levels_are_not_included_in_the_valuation(self):

        # First delete all products
        #Product.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 100
        stock_level.inlude_in_price_calculations=False
        stock_level.save()

        p = Product.objects.get(name="Shampoo")

        result = {
            'name': 'Shampoo', 
            'in_stock': '100.00', 
            'cost': '120.00', 
            'inventory_value': '12000.00', 
            'retail_value': '0.00', 
            'potential_profit': '-12000.00', 
            'margin': '0', 
            'variants': None
        }

        store_reg_nos = [store.reg_no for store in [self.store1]]

        self.assertEqual(p.get_inventory_valuation(store_reg_nos), result)
    
    def test_get_inventory_valuation_method_when_product_has_0_values(self):

        self.product.price = 0
        self.product.cost = 0
        self.product.save()

        p = Product.objects.get(name="Shampoo")

        result = {
            'name': 'Shampoo', 
            'in_stock': '0', 
            'cost': '0.00', 
            'inventory_value': '0.00', 
            'retail_value': '0', 
            'potential_profit': '0.00', 
            'margin': '0', 
            'variants': None
        }

        store_reg_nos = [store.reg_no for store in [self.store1]]

        self.assertEqual(p.get_inventory_valuation(store_reg_nos), result)

    def test_get_inventory_valuation_for_variant_product_from_single_store(self):

        self.product.stores.add(self.store2)

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )

        self.assertEqual(ProductVariant.objects.all().count(), 3)
        self.assertEqual(Product.objects.all().count(), 4)

        p = Product.objects.get(name="Shampoo")

        result = {
            'name': 'Shampoo', 
            'in_stock': '350.00', 
            'cost': '120.00', 
            'inventory_value': '280000.00', 
            'retail_value': '525000.00', 
            'potential_profit': '245000.00', 
            'margin': '46.67',
            'variants': [
                {
                    'name': 'Small', 
                    'in_stock': '100.00', 
                    'cost': '800.00', 
                    'inventory_value': '80000.00', 
                    'retail_value': '150000.00', 
                    'potential_profit': '70000.00', 
                    'margin': '46.67',
                    'variants': None
                }, 
                {
                    'name': 'Medium', 
                    'in_stock': '120.00', 
                    'cost': '800.00', 
                    'inventory_value': '96000.00', 
                    'retail_value': '180000.00', 
                    'potential_profit': '84000.00', 
                    'margin': '46.67',
                    'variants': None
                }, 
                {
                    'name': 'Large', 
                    'in_stock': '130.00', 
                    'cost': '800.00', 
                    'inventory_value': '104000.00', 
                    'retail_value': '195000.00', 
                    'potential_profit': '91000.00', 
                    'margin': '46.67',
                    'variants': None
                }
            ]
        }

        store_reg_nos = [store.reg_no for store in [self.store1]]

        self.assertEqual(p.get_inventory_valuation(store_reg_nos), result)

    def test_get_inventory_valuation_for_variant_product_from_multiple_stores(self):

        self.product.stores.add(self.store1, self.store2)

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )

        self.assertEqual(ProductVariant.objects.all().count(), 3)
        self.assertEqual(Product.objects.all().count(), 4)

        p = Product.objects.get(name="Shampoo")

        result = {
            'name': 'Shampoo', 
            'in_stock': '1000.00', 
            'cost': '120.00', 
            'inventory_value': '800000.00', 
            'retail_value': '1500000.00', 
            'potential_profit': '700000.00', 
            'margin': '46.67', 
            'variants': [
                {
                    'name': 'Small', 
                    'in_stock': '300.00', 
                    'cost': '800.00', 
                    'inventory_value': '240000.00', 
                    'retail_value': '450000.00', 
                    'potential_profit': '210000.00', 
                    'margin': '46.67', 
                    'variants': None
                }, 
                {
                    'name': 'Medium', 
                    'in_stock': '340.00', 
                    'cost': '800.00', 
                    'inventory_value': '272000.00', 
                    'retail_value': '510000.00', 
                    'potential_profit': '238000.00', 
                    'margin': '46.67', 
                    'variants': None
                },  
                {
                    'name': 'Large', 
                    'in_stock': '360.00', 
                    'cost': '800.00', 
                    'inventory_value': '288000.00', 
                    'retail_value': '540000.00', 
                    'potential_profit': '252000.00', 
                    'margin': '46.67', 
                    'variants': None
                }
            ]
        }

        store_reg_nos = [store.reg_no for store in [self.store1, self.store2]]

        self.assertEqual(
            p.get_inventory_valuation(store_reg_nos), 
            result
        )

    def test_get_inventory_valuation_from_all_stores(self):

        self.product.stores.add(self.store1, self.store2)

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )

        self.assertEqual(ProductVariant.objects.all().count(), 3)
        self.assertEqual(Product.objects.all().count(), 4)

        p = Product.objects.get(name="Shampoo")

        result = {
            'name': 'Shampoo', 
            'in_stock': '1000.00', 
            'cost': '120.00', 
            'inventory_value': '800000.00', 
            'retail_value': '1500000.00', 
            'potential_profit': '700000.00', 
            'margin': '46.67', 
            'variants': [
                {
                    'name': 'Small', 
                    'in_stock': '300.00', 
                    'cost': '800.00', 
                    'inventory_value': '240000.00', 
                    'retail_value': '450000.00', 
                    'potential_profit': '210000.00', 
                    'margin': '46.67', 
                    'variants': None
                }, 
                {
                    'name': 'Medium', 
                    'in_stock': '340.00', 
                    'cost': '800.00', 
                    'inventory_value': '272000.00', 
                    'retail_value': '510000.00', 
                    'potential_profit': '238000.00', 
                    'margin': '46.67', 
                    'variants': None
                },  
                {
                    'name': 'Large', 
                    'in_stock': '360.00', 
                    'cost': '800.00', 
                    'inventory_value': '288000.00', 
                    'retail_value': '540000.00', 
                    'potential_profit': '252000.00', 
                    'margin': '46.67', 
                    'variants': None
                }
            ]
        }

        store_reg_nos = [store.reg_no for store in [self.store1, self.store2]]

        self.assertEqual(
            p.get_inventory_valuation(store_reg_nos), 
            result
        )

    def test_get_inventory_valuation_with_wrong_store_reg_no(self):

        self.product.stores.add(self.store1, self.store2)

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )
        
        self.assertEqual(ProductVariant.objects.all().count(), 3)
        self.assertEqual(Product.objects.all().count(), 4)

        p = Product.objects.get(name="Shampoo")

        store_reg_nos = [454545454, 7545454]

        result = {
            'name': 'Shampoo', 
            'in_stock': '0', 
            'cost': '120.00', 
            'inventory_value': '0', 
            'retail_value': '0', 
            'potential_profit': '0', 
            'margin': '0', 'variants': []
        }

        self.assertEqual(
            p.get_inventory_valuation(store_reg_nos), 
            result
        ) 

    def test_get_created_date_method(self):

        p = Product.objects.get(name="Shampoo")
             
        # Check if get_created_date is correct
        self.assertTrue(
            DateUtils.do_created_dates_compare(
                p.get_created_date(self.user.get_user_timezone())
            )
        )

    def test_get_profile_image_url_method(self):
        p = Product.objects.get(name="Shampoo")

        self.assertEqual(p.get_image_url(), p.image.url)

        # Test when image url is empty
        p.image_url = ''
        p.save()

        p = Product.objects.get(name="Shampoo")

        self.assertEqual(p.get_image_url(), f'/media/images/products/{p.reg_no}_.jpg')
    
    def test_if_product_stores_changed_signal_can_create_stock_level(self):

        self.product.stores.remove(self.store1)
        self.assertEqual(StockLevel.objects.all().count(), 1)


        self.product.stores.add(self.store1, self.store2)

        # Check if stock levels will be created
        self.assertEqual(StockLevel.objects.all().count(), 2)

        stock_level1 = StockLevel.objects.get(store=self.store1)

        self.assertEqual(stock_level1.store, self.store1)
        self.assertEqual(stock_level1.product, self.product)
        self.assertEqual(stock_level1.units, 0)


        stock_level2 = StockLevel.objects.get(store=self.store2)
        
        self.assertEqual(stock_level2.store, self.store2)
        self.assertEqual(stock_level2.product, self.product)
        self.assertEqual(stock_level2.units, 0)

    def test_if_product_stores_changed_signal_can_remove_stock_level(self):

        self.product.stores.remove(self.store1)
        self.assertEqual(StockLevel.objects.all().count(), 1)

        self.product.stores.add(self.store1, self.store2)

        # Check if stock levels will be created
        self.assertEqual(StockLevel.objects.all().count(), 2)

        self.product.stores.remove(self.store1, self.store2)

        # Check if stock levels have been deleted
        self.assertEqual(StockLevel.objects.all().count(), 0)

    def test_if_product_stores_changed_signal_wont_create_multiple_stock_levels_for_the_same_store_and_product(self):

        self.product.stores.remove(self.store1)
        self.assertEqual(StockLevel.objects.all().count(), 1)

        self.product.stores.add(self.store1, self.store2)
        self.assertEqual(StockLevel.objects.all().count(), 2)

        # Check even if multiple times, additional stock levels wont be created
        self.product.stores.add(self.store1, self.store2)
        self.product.stores.add(self.store1, self.store2)
        self.product.stores.add(self.store1, self.store2)
        self.assertEqual(StockLevel.objects.all().count(), 2)
 
    def test_if_product_variant_changed_signal_updates_variant_count_field(self):
        
        product1 = Product.objects.get(name="Shampoo")
        self.assertEqual(product1.variant_count, 0)

        # Add variant to product
        product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )
        product2.stores.add(self.store1)

        variant = ProductVariant.objects.create(product_variant=product2)
        
        product1.variants.add(variant)

        product1 = Product.objects.get(name="Shampoo")
        self.assertEqual(product1.variant_count, 1)

        # Remove variant from product
        product1.variants.remove(variant)

        product1 = Product.objects.get(name="Shampoo")
        self.assertEqual(product1.variant_count, 0)

    def test_if_product_bundle_changed_signal_updates_is_bundle_field(self):
        """
        Product fields

        Ensure a product has the right fields after it has been created as a master bundle
        """

        product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )
        product2.stores.add(self.store1)


        # Create master product with 2 bundles
        shampoo_bundle = ProductBundle.objects.create(
            product_bundle=self.product,
            quantity=30
        )

        conditoner_bundle = ProductBundle.objects.create(
            product_bundle=product2,
            quantity=25
        )

        master_product = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Hair Bundle",
            price=35000,
            cost=30000,
            barcode='code123'
        )

        # Without bundles
        master_product = Product.objects.get(name="Hair Bundle")
        self.assertEqual(master_product.is_bundle, False)

        # With bundles
        master_product.bundles.add(shampoo_bundle, conditoner_bundle)

        master_product = Product.objects.get(name="Hair Bundle")
        self.assertEqual(master_product.is_bundle, True)

        # Without bundles again
        master_product.bundles.remove(shampoo_bundle, conditoner_bundle)

        master_product = Product.objects.get(name="Hair Bundle")
        self.assertEqual(master_product.is_bundle, False)

    def test_if_1d_variants_can_be_created_automatically(self):

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )

        self.assertEqual(ProductVariant.objects.all().count(), 3)
        self.assertEqual(Product.objects.all().count(), 4)

        product = Product.objects.get(name="Shampoo")

        variants = product.variants.all()

        self.assertEqual(variants[0].product_variant.name, 'Small')
        self.assertEqual(variants[1].product_variant.name, 'Medium')
        self.assertEqual(variants[2].product_variant.name, 'Large')

    def test_if_2d_variants_can_be_created_automatically(self):

        # Create 9 variants for master product
        create_2d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )

        self.assertEqual(ProductVariant.objects.all().count(), 12)
        self.assertEqual(Product.objects.all().count(), 13)

        product = Product.objects.get(name="Shampoo")

        variants = product.variants.all()

        self.assertEqual(variants[0].product_variant.name, 'Small / White')
        self.assertEqual(variants[1].product_variant.name, 'Small / Black')
        self.assertEqual(variants[2].product_variant.name, 'Small / Red')
        self.assertEqual(variants[3].product_variant.name, 'Small / Green')
        self.assertEqual(variants[4].product_variant.name, 'Medium / White')
        self.assertEqual(variants[5].product_variant.name, 'Medium / Black')
        self.assertEqual(variants[6].product_variant.name, 'Medium / Red')
        self.assertEqual(variants[7].product_variant.name, 'Medium / Green')
        self.assertEqual(variants[8].product_variant.name, 'Large / White')
        self.assertEqual(variants[9].product_variant.name, 'Large / Black')
        self.assertEqual(variants[10].product_variant.name, 'Large / Red')
        self.assertEqual(variants[11].product_variant.name, 'Large / Green')

    def test_get_variants_data_from_store_method_with_1d_variants(self):

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )

        product = Product.objects.get(name="Shampoo")

        options = ProductVariantOption.objects.all().order_by('id')
        choices = ProductVariantOptionChoice.objects.all().order_by('id')
        variants = Product.objects.filter(productvariant__product=product).order_by('id')

        #------------------ Check if store1 variants
        store1_results = {
            'options': [
                { 
                    'name': 'Size', 
                    'reg_no': options[0].reg_no,
                    'values': [
                        {
                            'name': 'Small', 
                            'reg_no': choices[0].reg_no,
                        }, 
                        {
                            'name': 'Medium', 
                            'reg_no': choices[1].reg_no,
                        }, 
                        {  
                            'name': 'Large', 
                            'reg_no': choices[2].reg_no,
                        }
                    ]
                }
            ], 
            'variants': [
                { 
                    'name': 'Small', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '50', 'units': '100.00'}, 
                    'show_product': True,
                    'reg_no': variants[0].reg_no,
                }, 
                {
                    'name': 'Medium', 
                    'price': '1500.00', 
                    'cost': '800.00',  
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '60', 'units': '120.00'}, 
                    'show_product': True,
                    'reg_no': variants[1].reg_no,
                }, 
                { 
                    'name': 'Large', 
                    'price': '1500.00', 
                    'cost': '800.00',  
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '65', 'units': '130.00'}, 
                    'show_product': True,
                    'reg_no': variants[2].reg_no,
                }
            ]
        }

        self.assertEqual(
            product.get_variants_data_from_store(self.store1.reg_no), 
            store1_results
        )

        #------------------ Check if store2 variants
        store2_results = {
            'options': [
                {
                    'name': 'Size', 
                    'reg_no': options[0].reg_no, 
                    'values': [
                        {
                            'name': 'Small', 
                            'reg_no': choices[0].reg_no, 
                        }, 
                        { 
                            'name': 'Medium',
                            'reg_no': choices[1].reg_no, 
                        }, 
                        { 
                            'name': 'Large', 
                            'reg_no': choices[2].reg_no, 
                        }
                    ]
                }
            ], 
            'variants': [
                {
                    'name': 'Small', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '100', 'units': '200.00'}, 
                    'show_product': True,
                    'reg_no': variants[0].reg_no,
                }, 
                {
                    'name': 'Medium', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '110', 'units': '220.00'}, 
                    'show_product': True,
                    'reg_no': variants[1].reg_no,
                }, 
                { 
                    'name': 'Large', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '115', 'units': '230.00'}, 
                    'show_product': True,
                    'reg_no': variants[2].reg_no,
                }
            ]
        }

        self.assertEqual(
            product.get_variants_data_from_store(self.store2.reg_no), 
            store2_results
        )

    def test_if_get_variants_data_from_store_method_with_2d_variants(self):

        # Create 9 variants for master product
        create_2d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )

        product = Product.objects.get(name="Shampoo")

        options = ProductVariantOption.objects.all().order_by('id')
        choices = ProductVariantOptionChoice.objects.all().order_by('id')
        variants = Product.objects.filter(productvariant__product=product).order_by('id')

        result = {
            'options': [
                { 
                    'name': 'Size',  
                    'reg_no': options[0].reg_no,
                    'values': [
                        {
                            'name': 'Small', 
                            'reg_no': choices[0].reg_no, 
                        }, 
                        {
                            'name': 'Medium',
                            'reg_no': choices[1].reg_no, 
                        }, 
                        {
                            'name': 'Large',
                            'reg_no': choices[2].reg_no, 
                        }
                    ]
                }, 
                {
                    'name': 'Color',  
                    'reg_no': options[1].reg_no,
                    'values': [
                        {
                            'name': 'White', 
                            'reg_no': choices[3].reg_no, 
                        }, 
                        { 
                            'name': 'Black', 
                            'reg_no': choices[4].reg_no, 
                        }, 
                        { 
                            'name': 'Red', 
                            'reg_no': choices[5].reg_no, 
                        }, 
                        { 
                            'name': 'Green', 
                            'reg_no': choices[6].reg_no, 
                        }
                    ]
                }
            ], 
            'variants': [
                {
                    'name': 'Small / White', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '0', 'units': '0.00'},
                    'show_product': True,
                    'reg_no': variants[0].reg_no,

                }, 
                {
                    'name': 'Small / Black', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '0', 'units': '0.00'},
                    'show_product': True,
                    'reg_no': variants[1].reg_no,

                }, 
                {
                    'name': 'Small / Red', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '0', 'units': '0.00'},
                    'show_product': True,
                    'reg_no': variants[2].reg_no,

                }, 
                {
                    'name': 'Small / Green', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '0', 'units': '0.00'},
                    'show_product': True,
                    'reg_no': variants[3].reg_no,

                }, 
                {
                    'name': 'Medium / White', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '0', 'units': '0.00'},
                    'show_product': True,
                    'reg_no': variants[4].reg_no,

                }, 
                {
                    'name': 'Medium / Black', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '0', 'units': '0.00'},
                    'show_product': True,
                    'reg_no': variants[5].reg_no,

                }, 
                {
                    'name': 'Medium / Red', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 
                    'code123', 
                    'stock_level': {'minimum_stock_level': '0', 'units': '0.00'}, 
                    'show_product': True,
                    'reg_no': variants[6].reg_no,

                }, 
                {
                    'name': 'Medium / Green', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 
                    'code123', 
                    'stock_level': {'minimum_stock_level': '0', 'units': '0.00'},
                    'show_product': True,
                    'reg_no': variants[7].reg_no,

                }, 
                {
                    'name': 'Large / White', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '0', 'units': '0.00'},
                    'show_product': True,
                    'reg_no': variants[8].reg_no,

                }, 
                {
                    'name': 'Large / Black', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 'code123', 
                    'stock_level': {'minimum_stock_level': '0', 'units': '0.00'},
                    'show_product': True,
                    'reg_no': variants[9].reg_no,

                }, 
                {
                    'name': 'Large / Red', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 
                    'code123', 
                    'stock_level': {'minimum_stock_level': '0', 'units': '0.00'},
                    'show_product': True,
                    'reg_no': variants[10].reg_no,

                }, 
                {
                    'name': 'Large / Green', 
                    'price': '1500.00', 
                    'cost': '800.00', 
                    'sku': '', 
                    'barcode': 
                    'code123', 
                    'stock_level': {'minimum_stock_level': '0', 'units': '0.00'}, 
                    'show_product': True,
                    'reg_no': variants[11].reg_no,

                }
            ]
        }

        self.assertEqual(
            product.get_variants_data_from_store(self.store1.reg_no), 
            result
        )

    def test_get_variants_data_from_store_method_with_wrong_store_reg_no(self):

        self.product.stores.add(self.store1, self.store2)

        self.assertEqual(
            self.product.get_variants_data_from_store(11), 
            {'options': [], 'variants': []}
        )
  
    def test_get_total_stock_level_method_from_a_single_store(self):

        self.product.stores.add(self.store1, self.store2)

        # Update stock levels for product 1 in store 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.units = 20
        stock_level.save()

        self.assertEqual(self.product.get_total_stock_level([self.store1.reg_no]), '100')
        self.assertEqual(self.product.get_total_stock_level([self.store2.reg_no]), '20')
   
    def test_get_total_stock_level_method_from_multiple_stores(self):

        self.product.stores.add(self.store1, self.store2)

        # Update stock levels for product 1 in store 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.units = 20
        stock_level.save()

        self.assertEqual(
            self.product.get_total_stock_level([self.store1.reg_no, self.store2.reg_no]), 
            '120'
        )

    def test_get_total_stock_level_method_from_all_stores(self):

        self.product.stores.add(self.store1, self.store2)

        # Update stock levels for product 1 in store 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.units = 20
        stock_level.save()

        self.assertEqual(
            self.product.get_total_stock_level(), 
            '120'
        )

    def test_get_total_stock_level_method_with_wrong_store_reg_no(self):

        self.product.stores.add(self.store1, self.store2)

        self.assertEqual(
            self.product.get_total_stock_level([11]), 
            '0'
        )

    def test_get_store_stock_level_data_method(self):

        self.product.stores.add(self.store1, self.store2)

        # Update stock levels for product 1 in store 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.minimum_stock_level = 30
        stock_level.price = 600
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.minimum_stock_level = 10
        stock_level.price = 700
        stock_level.units = 70
        stock_level.save()

        self.assertEqual(
            self.product.get_store_stock_level_data(self.store1.reg_no), 
            {
                'units': '100.00', 
                'minimum_stock_level': '30', 
                'is_sellable': 'True', 
                'price': '600.00'
            }
        )

        self.assertEqual(
            self.product.get_store_stock_level_data(self.store2.reg_no), 
            {
                'units': '70.00', 
                'minimum_stock_level': '10', 
                'is_sellable': 'True', 
                'price': '700.00'
            }

        )

    def test_get_store_stock_level_data_method_can_handle_wrong_reg_no(self):

        self.product.stores.add(self.store1, self.store2)

        self.assertEqual(
            self.product.get_store_stock_level_data(11), 
            {
                'units': '0', 
                'minimum_stock_level': '0', 
                'is_sellable': False,
                'price': '0.00'
            }
        )  

    def test_get_store_stock_units_method(self):

        self.product.stores.add(self.store1, self.store2)

        # Update stock levels for product 1 in store 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.minimum_stock_level = 30
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.minimum_stock_level = 10
        stock_level.units = 70
        stock_level.save()

        self.assertEqual(
            self.product.get_store_stock_units(self.store1.reg_no), 
            {'minimum_stock_level': '30', 'units': '100.00'}
        )

        self.assertEqual(
            self.product.get_store_stock_units(self.store2.reg_no), 
            {'minimum_stock_level': '10', 'units': '70.00'}
        )

    def test_get_store_stock_units_method_can_handle_wrong_reg_no(self):

        self.product.stores.add(self.store1, self.store2)

        self.assertEqual(
            self.product.get_store_stock_units(11), 
            {'minimum_stock_level': '0', 'units': '0'}
        )    

    def test_get_valuation_info_method_from_a_single_store(self):

        self.product.stores.add(self.store1, self.store2)

        # Update stock levels for product 1 in store 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.units = 20
        stock_level.save()

        self.assertEqual(
            self.product.get_valuation_info([self.store1.reg_no]), 
            {
                'stock_units': '100',
                'margin': '84', 
            }
        )
    
        self.assertEqual(
            self.product.get_valuation_info([self.store2.reg_no]), 
            {
                'stock_units': '20',
                'margin': '84', 
            }
        )
    
    def test_get_valuation_info_method_from_multiple_stores(self):

        self.product.stores.add(self.store1, self.store2)

        # Update stock levels for product 1 in store 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.units = 20
        stock_level.save()

        self.assertEqual(
            self.product.get_valuation_info([self.store1.reg_no, self.store2.reg_no]), 
            { 
                'stock_units': '120',
                'margin': '84', 
            }
        )

    def test_get_valuation_info_method_from_all_stores(self):

        self.product.stores.add(self.store1, self.store2)

        # Update stock levels for product 1 in store 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.units = 20
        stock_level.save()

        self.assertEqual(
            self.product.get_valuation_info(), 
            {
                'stock_units': '120',
                'margin': '84', 
            }
        )

    def test_get_valuation_info_method_with_wrong_store_reg_no(self):

        self.product.stores.add(self.store1, self.store2)

        self.assertEqual(
            self.product.get_valuation_info([11]), 
            { 
                'stock_units': '0',
                'margin': '0', 
            }
        )

    def test_get_product_view_bundles_data_method(self):
        """
        Product fields

        Ensure a product has the right fields after it has been created as a master bundle
        """
        # Create bundles
        self.create_a_bundle_product()

        master_product = Product.objects.get(name="Hair Bundle")

        product_map1 = ProductBundle.objects.get(product_bundle__name="Shampoo")
        product_map2 = ProductBundle.objects.get(product_bundle__name="Conditioner")

        results = [
            {
                'name': product_map1.product_bundle.name, 
                'sku': product_map1.product_bundle.sku, 
                'reg_no': product_map1.product_bundle.reg_no, 
                'quantity': str(product_map1.quantity)
            }, 
            {
                'name': product_map2.product_bundle.name, 
                'sku': product_map2.product_bundle.sku, 
                'reg_no': product_map2.product_bundle.reg_no, 
                'quantity': str(product_map2.quantity)
            }
        ]

        self.assertEqual(master_product.get_product_view_bundles_data(), results)
    
    def test_if_get_index_variants_data_method_returns_variants_only_in_the_specified_store(self):

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )

        product = Product.objects.get(name="Shampoo")

        #------------------ Check if store1 variants
        store1_results = [
            {
                'name': 'Small', 
                'valuation_info': {
                    'stock_units': '100', 
                    'margin': '46.67'
                }
            }, 
            {
                'name': 'Medium', 
                'valuation_info': {
                    'stock_units': '120', 
                    'margin': '46.67'
                }
            }, 
            {
                'name': 'Large', 
                'valuation_info': {
                    'stock_units': '130', 
                    'margin': '46.67'
                }
            }
        ]

        self.assertEqual(
            product.get_index_variants_data([self.store1.reg_no]), 
            store1_results
        )

        #------------------ Check if store2 variants
        store2_results = [
            {
                'name': 'Small', 
                'valuation_info': {
                    'stock_units': '200', 
                    'margin': '46.67'
                }
            }, 
            {
                'name': 'Medium', 
                'valuation_info': {
                    'stock_units': '220', 
                    'margin': '46.67'
                }
            }, 
            {
                'name': 'Large', 
                'valuation_info': {
                    'stock_units': '230', 
                    'margin': '46.67'
                }
            }
        ]

        self.assertEqual(
            product.get_index_variants_data([self.store2.reg_no]), 
            store2_results
        )

    def test_get_index_variants_data_method_can_get_data_from_all_stores(self):

        # Create 3 variants for master product
        create_1d_variants(
            master_product=self.product,
            profile=self.profile,
            store1=self.store1,
            store2=self.store2
        )

        product = Product.objects.get(name="Shampoo")

        results = [
            {
                'name': 'Small', 
                'valuation_info': {
                    'stock_units': '300',
                    'margin': '46.67'
                }
            }, 
            {
                'name': 'Medium', 
                'valuation_info': {
                    'stock_units': '340', 
                    'margin': '46.67'
                }
            }, 
            {
                'name': 'Large', 
                'valuation_info': {
                    'stock_units': '360', 
                    'margin': '46.67'
                }
            }
        ]

        self.assertEqual(product.get_index_variants_data(), results)
    
    def test_get_index_variants_data_method_with_wrong_store_reg_no(self):

        self.product.stores.add(self.store1, self.store2)

        self.assertEqual(
            self.product.get_index_variants_data([11]), 
            []
        )
    
    def test_get_report_data_method(self):
        
        # Delete current product first
        Product.objects.all().delete()

        self.create_product_with_receipts()

        product = Product.objects.get(name='Shampoo')

        data = product.get_report_data(local_timezone=self.user.get_user_timezone())

        self.assertEqual(
            data, 
            {
                'is_variant': False, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '22', 
                    'net_sales': '55000.00', 
                    'cost': '22000.00', 
                    'profit': '33000.00'
                }, 
                'variant_data': []
            }
        )
    
    def test_get_report_data_method_with_date(self):

        # Delete current product first
        Product.objects.all().delete()

        self.create_product_with_receipts()

        product = Product.objects.get(name='Shampoo')

        # Today date
        data = product.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'is_variant': False, 
                'product_data': {
                    'name': product.name,
                    'items_sold': '7', 
                    'net_sales': '17500.00',
                    'cost': '7000.00',  
                    'profit': '10500.00'
                }, 
                'variant_data': []
            }
        )

        ############ This month
        data = product.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.first_day_this_month.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'is_variant': False, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '16', 
                    'net_sales': '40000.00', 
                    'cost': '16000.00', 
                    'profit': '24000.00'
                }, 
                'variant_data': []
            }
        )

        ############ Date with no receipts
        data = product.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='2011-01-01', 
            date_before='2011-01-02',
        )

        self.assertEqual(
            data, 
            {
                'is_variant': False, 
                'product_data': {
                    'name': product.name,
                    'items_sold': '0', 
                    'net_sales': '0.00', 
                    'cost': '0.00', 
                    'profit': '0.00'
                }, 
                'variant_data': []
            }
        )

        ############# Wrong date from
        data = product.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='20111-01-01', 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'is_variant': False, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '22', 
                    'net_sales': '55000.00', 
                    'cost': '22000.00', 
                    'profit': '33000.00'
                }, 'variant_data': []
            }
        )

        ############ Wrong date to
        data = product.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'),
            date_before='20111-01-01',
        )

        self.assertEqual(
            data, 
            {
                'is_variant': False, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '22', 
                    'net_sales': '55000.00', 
                    'cost': '22000.00', 
                    'profit': '33000.00'
                }, 
                'variant_data': []
            }
        )
    
    def test_get_report_data_method_with_store_reg_no(self):

        # Delete current product first
        Product.objects.all().delete()

        self.create_product_with_receipts()

        product = Product.objects.get(name='Shampoo')

        # Store 1
        self.assertEqual(
            product.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=[self.store1.reg_no]), 
            {
                'is_variant': False, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '16', 
                    'net_sales': '40000.00', 
                    'cost': '16000.00', 
                    'profit': '24000.00'
                }, 
                'variant_data': []
            }
        )

        # Store 2
        self.assertEqual(
            product.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=[self.store2.reg_no]
            ), 
            {
                'is_variant': False, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '6', 
                    'net_sales': '15000.00', 
                    'cost': '6000.00', 
                    'profit': '9000.00'
                }, 
                'variant_data': []
            }
        )

        # Multiple stores 1
        self.assertEqual(
            product.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=[self.store1.reg_no, self.store2.reg_no]), 
            {
                'is_variant': False,
                'product_data': {
                    'cost': '22000.00',
                    'items_sold': '22',
                    'name': 'Shampoo',
                    'net_sales': '55000.00',
                    'profit': '33000.00'
                },
                'variant_data': []
            }
        )

        # Wrong store 
        self.assertEqual(
            product.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=[1111]
            ), 
            {
                'is_variant': False, 
                'product_data': {
                    'name': product.name,
                    'items_sold': '0', 
                    'net_sales': '0.00', 
                    'cost': '0.00', 
                    'profit': '0.00'
                }, 
                'variant_data': []
            }
        )
   
    def test_get_report_data_method_with_user(self):

        # Delete current product first
        Product.objects.all().delete()

        self.create_product_with_receipts()

        product = Product.objects.get(name='Shampoo')

        # User 1
        self.assertEqual(
            product.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=[self.user.reg_no]
            ), 
            {
                'is_variant': False, 
                'product_data': {
                    'name': product.name,
                    'items_sold': '7', 
                    'net_sales': '17500.00', 
                    'cost': '7000.00', 
                    'profit': '10500.00'
                }, 
                'variant_data': []
            }
        )

        # User 2
        self.assertEqual(
            product.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=[self.manager.reg_no]
            ),
            {
                'is_variant': False, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '9', 
                    'net_sales': '22500.00', 
                    'cost': '9000.00', 
                    'profit': '13500.00'
                }, 
                'variant_data': []
            }
        )

        # Multiple users 1
        self.assertEqual(
            product.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=[self.user.reg_no, self.manager.reg_no]
            ), 
            {
                'is_variant': False,
                'product_data': {
                    'cost': '16000.00',
                    'items_sold': '16',
                    'name': 'Shampoo',
                    'net_sales': '40000.00',
                    'profit': '24000.00'},
                'variant_data': []
            }
        )

        # Wrong user 
        self.assertEqual(
            product.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=[111]
            ), 
            {
                'is_variant': False, 
                'product_data': {
                    'name': product.name,
                    'items_sold': '0', 
                    'net_sales': '0.00', 
                    'cost': '0.00', 
                    'profit': '0.00'
                }, 
                'variant_data': []
            }
        )

    def test_get_report_data_method_with_variant_prouct_parent(self):

        self.create_variant_product_with_receipts()
 
        product = Product.objects.get(name='Shampoo')

        data = product.get_report_data(local_timezone=self.user.get_user_timezone())

        self.assertEqual(
            data, 
            {
                'is_variant': True, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '43', 
                    'net_sales': '64500.00', 
                    'cost': '34400.00', 
                    'profit': '30100.00'
                }, 
                'variant_data': [
                    {
                        'name': 'Small', 
                        'items_sold': '10', 
                        'net_sales': '15000.00',
                        'cost': '8000.00', 
                        'profit': '7000.00'
                    }, 
                    {
                        'name': 'Medium', 
                        'items_sold': '16', 
                        'net_sales': '24000.00', 
                        'cost': '12800.00', 
                        'profit': '11200.00'
                    }, 
                    {
                        'name': 'Large', 
                        'items_sold': '17', 
                        'net_sales': '25500.00', 
                        'cost': '13600.00', 
                        'profit': '11900.00'
                    }
                ]
            }
        )

    def test_if_variant_models_with_no_sales_wont_be_displayed(self):

        self.create_variant_product_with_receipts()

        # Remove variants from all sales and replace them with variant small
        lines = ReceiptLine.objects.all()

        small_variant = Product.objects.get(name='Small')

        for line in lines:
            line.product = small_variant
            line.save()

        product = Product.objects.get(name='Shampoo')

        data = product.get_report_data(local_timezone=self.user.get_user_timezone())

        self.assertEqual(
            data, 
            {
                'is_variant': True, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '43', 
                    'net_sales': '64500.00', 
                    'cost': '34400.00', 
                    'profit': '30100.00'
                }, 
                'variant_data': [
                    {
                        'name': 'Small', 
                        'items_sold': '43', 
                        'net_sales': '64500.00', 
                        'cost': '34400.00', 
                        'profit': '30100.00'
                    }
                ]
            }
        )

    def test_get_report_data_method_with_variant_product_with_date(self):

        self.create_variant_product_with_receipts()
 
        product = Product.objects.get(name='Shampoo')

        # Today date
        data = product.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'is_variant': True, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '29', 
                    'net_sales': '43500.00', 
                    'cost': '23200.00', 
                    'profit': '20300.00'
                }, 
                'variant_data': [
                    {
                        'name': 'Small',
                        'items_sold': '7', 
                        'net_sales': '10500.00', 
                        'cost': '5600.00', 
                        'profit': '4900.00'
                    }, 
                    {
                        'name': 'Medium', 
                        'items_sold': '10', 
                        'net_sales': '15000.00', 
                        'cost': '8000.00', 
                        'profit': '7000.00'
                    }, 
                    {
                        'name': 'Large', 
                        'items_sold': '12', 
                        'net_sales': '18000.00', 
                        'cost': '9600.00', 
                        'profit': '8400.00'
                    }
                ]
            }
        )

        ############ This month
        data = product.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.first_day_this_month.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'is_variant': True, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '43', 
                    'net_sales': '64500.00', 
                    'cost': '34400.00', 
                    'profit': '30100.00'
                }, 
                'variant_data': [
                    {
                        'name': 'Small', 
                        'items_sold': '10', 
                        'net_sales': '15000.00', 
                        'cost': '8000.00', 
                        'profit': '7000.00'
                    }, 
                    {
                        'name': 'Medium', 
                        'items_sold': '16', 
                        'net_sales': '24000.00', 
                        'cost': '12800.00', 
                        'profit': '11200.00'
                    }, 
                    {
                        'name': 'Large', 
                        'items_sold': '17', 
                        'net_sales': '25500.00', 
                        'cost': '13600.00', 
                        'profit': '11900.00'
                    }
                ]
            }
        )

        ############ Date with no receipts
        data = product.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='2011-01-01', 
            date_before='2011-01-02',
        )

        self.assertEqual(
            data, 
            {
                'is_variant': True, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '0', 
                    'net_sales': '0.00', 
                    'cost': '0.00', 
                    'profit': '0.00'
                }, 
                'variant_data': [
                    {
                        'name': 'Small', 
                        'items_sold': '0', 
                        'net_sales': '0.00', 
                        'cost': '0.00', 
                        'profit': '0.00'
                    }, 
                    {
                        'name': 'Medium', 
                        'items_sold': '0', 
                        'net_sales': '0.00', 
                        'cost': '0.00', 
                        'profit': '0.00'
                    }, 
                    {
                        'name': 'Large', 
                        'items_sold': '0', 
                        'net_sales': '0.00', 
                        'cost': '0.00', 
                        'profit': '0.00'
                    }
                ]
            }
        )

        ############# Wrong date from
        data = product.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='20111-01-01', 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'is_variant': True, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '43', 
                    'net_sales': '64500.00', 
                    'cost': '34400.00', 
                    'profit': '30100.00'
                }, 
                'variant_data': [
                    {
                        'name': 'Small', 
                        'items_sold': '10', 
                        'net_sales': '15000.00', 
                        'cost': '8000.00', 
                        'profit': '7000.00'
                    }, 
                    {
                        'name': 'Medium', 
                        'items_sold': '16', 
                        'net_sales': '24000.00', 
                        'cost': '12800.00', 
                        'profit': '11200.00'
                    }, 
                    {
                        'name': 'Large', 
                        'items_sold': '17', 
                        'net_sales': '25500.00', 
                        'cost': '13600.00', 
                        'profit': '11900.00'
                    }
                ]
            }
        )

        ############ Wrong date to
        data = product.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'),
            date_before='20111-01-01',
        )

        self.assertEqual(
            data, 
            {
                'is_variant': True, 
                'product_data': {
                    'name': 'Shampoo', 
                    'items_sold': '43', 
                    'net_sales': '64500.00', 
                    'cost': '34400.00', 
                    'profit': '30100.00'
                }, 
                'variant_data': [
                    {
                        'name': 'Small', 
                        'items_sold': '10', 
                        'net_sales': '15000.00', 
                        'cost': '8000.00', 
                        'profit': '7000.00'
                    }, 
                    {
                        'name': 'Medium', 
                        'items_sold': '16', 
                        'net_sales': '24000.00', 
                        'cost': '12800.00', 
                        'profit': '11200.00'
                    }, 
                    {
                        'name': 'Large', 
                        'items_sold': '17', 
                        'net_sales': '25500.00', 
                        'cost': '13600.00', 
                        'profit': '11900.00'
                    }
                ]
            }
        )
    
    def test_firebase_messages_are_sent_correctly_when_product_is_deleted(self):

        Product.objects.all().delete()
        empty_logfiles()

        self.create_a_normal_product()

        #Delete tax
        Product.objects.get(name="Shampoo").delete()

        content = get_test_firebase_sender_log_content(only_include=['product'])

        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': '', 
                'relevant_stores': '[]', 
                'model': 'product', 
                'action_type': 'delete', 
                'reg_no': str(self.product.reg_no)
            }
        }

        self.assertEqual(content[0], result)

    def test_firebase_messages_are_sent_correctly_when_product_is_soft_deleted(self):

        Product.objects.all().delete()
        empty_logfiles()

        self.create_a_normal_product()

        #Delete tax
        Product.objects.get(name="Shampoo").soft_delete()

        content = get_test_firebase_sender_log_content(only_include=['product'])

        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': '', 
                'relevant_stores': '[]', 
                'model': 'product', 
                'action_type': 'delete', 
                'reg_no': str(self.product.reg_no)
            }
        }

        self.assertEqual(content[0], result)

    def test_if_product_image_is_deleted_when_product_is_deleted(self):

        # Confirm product
        self.assertEqual(Product.objects.all().count(), 1)

        product = Product.objects.get(name="Shampoo")

        # Confirm that the initial profile was created
        full_test_path = settings.MEDIA_ROOT + product.image.url
        full_test_path = full_test_path.replace('//media/', '/')

        Image.open(full_test_path)
        
        # Delete product
        product = Product.objects.get(name="Shampoo")
        product.delete()

        # Confirm that the initial profile was deleted
        try:
            Image.open(full_test_path)
            self.fail()
        except: # pylint: disable=bare-except
            pass
    
    def test_get_stock_levels_method(self):

        p = Product.objects.get(name="Shampoo")

        # Update stock levels for product 1 in store 1
        stock_level1 = StockLevel.objects.get(store=self.store1, product=p)
        stock_level1.price = 100
        stock_level1.is_sellable = False
        stock_level1.loyverse_store_id = uuid.uuid4()
        stock_level1.save()

        stock_level2 = StockLevel.objects.get(store=self.store2, product=p)
        stock_level2.price = 20
        stock_level2.loyverse_store_id = uuid.uuid4()
        stock_level2.save()

        results = [
            {
                'is_sellable': False, 
                'price': '100.00', 
                'loyverse_store_id': str(stock_level1.loyverse_store_id)
            }, 
            {
                'is_sellable': True, 
                'price': '20.00', 
                'loyverse_store_id': str(stock_level2.loyverse_store_id)
            }
        ]

        self.assertEqual(len(p.get_stock_levels()), len(results))

        # We using a loop because the list returned is unordered. We do this to
        # try and improve performance
        for result in results:
            self.assertTrue(result in p.get_stock_levels())

    def test_get_product_view_production_data_method(self):
        """
        Product fields

        Ensure a product has the right fields after it has been created as a master production
        """
        Product.objects.all().delete()

        # Create bundles
        self.create_a_production_product()

        sugar_sack = Product.objects.get(name="Sugar 50kg Sack")
        pagackaged_sugar_2kg = Product.objects.get(name="Packaged Sugar 2kg")
        pagackaged_sugar_1kg = Product.objects.get(name="Packaged Sugar 1kg")

        results = [
            {
                'name': 'Packaged Sugar 1kg', 
                'sku': '', 
                'reg_no': pagackaged_sugar_1kg.reg_no, 
                'is_auto_repackage': False, 
                'quantity': '50'
            }, 
            {
                'name': 'Packaged Sugar 2kg', 
                'sku': '', 
                'reg_no': pagackaged_sugar_2kg.reg_no, 
                'is_auto_repackage': False, 
                'quantity': '25'
            }
        ]

        self.assertEqual(
            sugar_sack.get_product_view_production_data(), 
            results
        )

    def test_get_product_view_transform_data_method_wont_return_data_if_filter_for_repackaging_is_true_and_no_map_has_auto_repackage(self):
        """
        Product fields

        Ensure a product has the right fields after it has been created as a master production
        """
        Product.objects.all().delete()

        # Create bundles
        self.create_a_production_product()

        sugar_sack = Product.objects.get(name="Sugar 50kg Sack")

        ProductProductionMap.objects.all().update(is_auto_repackage=False)

        # Master product
        results = {
            'name': sugar_sack.name, 
            'reg_no': sugar_sack.reg_no, 
            'cost': '9000.00', 
            'current_quantity': '34.00', 
            'is_reverse': True,
            'product_map': []
        }

        self.assertEqual(
            sugar_sack.get_product_view_transform_data(
                store=self.store1,
                filter_for_repackaging=True), 
            results
        )

    def test_get_product_view_transform_data_method_will_only_return_a_map_that_is_auto_repackage(self):
        """
        Product fields

        Ensure a product has the right fields after it has been created as a master production
        """
        Product.objects.all().delete()

        # Create bundles
        self.create_a_production_product()

        sugar_sack = Product.objects.get(name="Sugar 50kg Sack")
        pagackaged_sugar_2kg = Product.objects.get(name="Packaged Sugar 2kg")

        ProductProductionMap.objects.filter(
            product_map=pagackaged_sugar_2kg
        ).update(is_auto_repackage=True)

        # Master product
        results = {
            'name': sugar_sack.name, 
            'reg_no': sugar_sack.reg_no, 
            'cost': '9000.00', 
            'current_quantity': '34.00', 
            'is_reverse': False,
            'product_map': [
                {
                    'name': 'Packaged Sugar 2kg', 
                    'sku': '', 
                    'reg_no': pagackaged_sugar_2kg.reg_no, 
                    'current_quantity': '24.00', 
                    'equivalent_quantity': '25'
                }
            ]
        }

        self.assertEqual(
            sugar_sack.get_product_view_transform_data(
                store=self.store1,
                filter_for_repackaging=True), 
            results
        )

    def test_get_product_view_transform_data_method(self):
        """
        Product fields

        Ensure a product has the right fields after it has been created as a master production
        """
        Product.objects.all().delete()

        # Create bundles
        self.create_a_production_product()

        sugar_sack = Product.objects.get(name="Sugar 50kg Sack")
        pagackaged_sugar_2kg = Product.objects.get(name="Packaged Sugar 2kg")
        pagackaged_sugar_1kg = Product.objects.get(name="Packaged Sugar 1kg")

        # Master product
        results = {
            'name': sugar_sack.name, 
            'reg_no': sugar_sack.reg_no, 
            'cost': '9000.00', 
            'current_quantity': '34.00', 
            'is_reverse': False,
            'product_map': [
                {
                    'name': 'Packaged Sugar 1kg', 
                    'sku': '', 
                    'reg_no': pagackaged_sugar_1kg.reg_no, 
                    'current_quantity': '14.00', 
                    'equivalent_quantity': '50'
                }, 
                {
                    'name': 'Packaged Sugar 2kg', 
                    'sku': '', 
                    'reg_no': pagackaged_sugar_2kg.reg_no, 
                    'current_quantity': '24.00', 
                    'equivalent_quantity': '25'
                }
            ]
        }

        self.assertEqual(
            sugar_sack.get_product_view_transform_data(self.store1), 
            results
        )

        # Packaged Sugar 2kg
        pagackaged_sugar_2kg.get_product_view_transform_data(self.store1)

        results = {
            'name': pagackaged_sugar_2kg.name, 
            'reg_no': pagackaged_sugar_2kg.reg_no, 
            'cost': '360.00', 
            'current_quantity': '24.00', 
            'is_reverse': True,
            'product_map': [
                {
                    'name': sugar_sack.name, 
                    'sku': '', 
                    'reg_no': sugar_sack.reg_no, 
                    'current_quantity': '34.00', 
                    'equivalent_quantity': '0.04'
                }
            ]
        }

        self.assertEqual(
            pagackaged_sugar_2kg.get_product_view_transform_data(self.store1), 
            results
        )

        # Packaged Sugar 1kg
        pagackaged_sugar_1kg.get_product_view_transform_data(self.store1)

        results = {
            'name': pagackaged_sugar_1kg.name, 
            'reg_no': pagackaged_sugar_1kg.reg_no, 
            'cost': '180.00', 
            'current_quantity': '14.00', 
            'is_reverse': True,
            'product_map': [
                {
                    'name': sugar_sack.name, 
                    'sku': '', 
                    'reg_no': sugar_sack.reg_no, 
                    'current_quantity': '34.00', 
                    'equivalent_quantity': '0.02'
                }
            ]
        }

        self.assertEqual(
            pagackaged_sugar_1kg.get_product_view_transform_data(self.store1), 
            results
        )

    def test_get_product_view_transform_data_method_when_product_has_multiple_parents(self):
        """
        Product fields

        Ensure a product has the right fields after it has been created as a master production
        """
        Product.objects.all().delete()

        # Create bundles
        self.create_a_production_product()

        # Create new product with Map
        sugar_30_sack = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Sugar 30kg Sack",
            price=5000,
            cost=4500,
            barcode='code4'
        )

        # Create master product with 2 bundles
        pagackaged_sugar_2kg_map = ProductProductionMap.objects.create(
            name="Packaged Sugar 2kg",
            product_map=Product.objects.get(name="Packaged Sugar 2kg"),
            quantity=15
        )

        sugar_30_sack.productions.add(pagackaged_sugar_2kg_map)

        stock_level = StockLevel.objects.get(store=self.store1, product=sugar_30_sack)
        stock_level.units = 74
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=sugar_30_sack)
        stock_level.units = 60
        stock_level.save()



        sugar_50_sack = Product.objects.get(name="Sugar 50kg Sack")
        sugar_30_sack = Product.objects.get(name="Sugar 30kg Sack")
        pagackaged_sugar_2kg = Product.objects.get(name="Packaged Sugar 2kg")
        pagackaged_sugar_1kg = Product.objects.get(name="Packaged Sugar 1kg")

        # Master product
        results = {
            'name': sugar_50_sack.name, 
            'reg_no': sugar_50_sack.reg_no, 
            'cost': '9000.00', 
            'current_quantity': '34.00', 
            'is_reverse': False,
            'product_map': [
                {
                    'name': 'Packaged Sugar 1kg', 
                    'sku': '', 
                    'reg_no': pagackaged_sugar_1kg.reg_no, 
                    'current_quantity': '14.00', 
                    'equivalent_quantity': '50'
                }, 
                {
                    'name': 'Packaged Sugar 2kg', 
                    'sku': '', 
                    'reg_no': pagackaged_sugar_2kg.reg_no, 
                    'current_quantity': '24.00', 
                    'equivalent_quantity': '25'
                }
            ]
        }

        self.assertEqual(
            sugar_50_sack.get_product_view_transform_data(self.store1), 
            results
        )

        # Packaged Sugar 2kg
        pagackaged_sugar_2kg.get_product_view_transform_data(self.store1)

        results = {
            'name': pagackaged_sugar_2kg.name, 
            'reg_no': pagackaged_sugar_2kg.reg_no, 
            'cost': '360.00', 
            'current_quantity': '24.00', 
            'is_reverse': True,
            'product_map': [
                {
                    'name': sugar_30_sack.name, 
                    'sku': '', 
                    'reg_no': sugar_30_sack.reg_no, 
                    'current_quantity': '74.00', 
                    'equivalent_quantity': '0.06666666666666667'
                }, 
                {
                    'name': sugar_50_sack.name, 
                    'sku': '', 
                    'reg_no': sugar_50_sack.reg_no, 
                    'current_quantity': '34.00', 
                    'equivalent_quantity': '0.04'
                }
            ]
        }

        self.assertEqual(
            pagackaged_sugar_2kg.get_product_view_transform_data(self.store1), 
            results
        )

        # Packaged Sugar 1kg
        pagackaged_sugar_1kg.get_product_view_transform_data(self.store1)

        results = {
            'name': pagackaged_sugar_1kg.name, 
            'reg_no': pagackaged_sugar_1kg.reg_no, 
            'cost': '180.00', 
            'current_quantity': '14.00', 
            'is_reverse': True,
            'product_map': [
                {
                    'name': sugar_50_sack.name, 
                    'sku': '', 
                    'reg_no': sugar_50_sack.reg_no, 
                    'current_quantity': '34.00', 
                    'equivalent_quantity': '0.02'
                }
            ]
        }

        self.assertEqual(
            pagackaged_sugar_1kg.get_product_view_transform_data(self.store1), 
            results
        )

    def test_update_product_average_price_method(self):

        # Update product stock levels price
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 10
        stock_level.price = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.units = 15
        stock_level.price = 20
        stock_level.save()

        # Update product price
        Product.objects.get(name="Shampoo").save()
    
        # Confirm product price
        self.assertEqual(Product.objects.get(name="Shampoo").average_price, Decimal('60.00'))

    def test_update_product_average_price_method_will_ignore_stock_levels_that_have_inlude_in_price_calculations_as_false(self):

        # Update product stock levels price
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 10
        stock_level.price = 100
        stock_level.inlude_in_price_calculations = False
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.units = 15
        stock_level.price = 20
        stock_level.save()

        # Update product price
        Product.objects.get(name="Shampoo").save()
    
        # Confirm product price
        self.assertEqual(Product.objects.get(name="Shampoo").average_price, 20)

    def test_update_product_average_price_method_will_ignore_stock_levels_that_have_units_below_1(self):

        # Update product stock levels price
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 0
        stock_level.price = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.units = 15
        stock_level.price = 20
        stock_level.save()

        # Update product price
        Product.objects.get(name="Shampoo").save()
    
        # Confirm product price
        self.assertEqual(Product.objects.get(name="Shampoo").average_price, 20)

    def test_update_product_average_price_method_will_ignore_stock_levels_that_have_price_below_1(self):

        # Update product stock levels price
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 10
        stock_level.price = 0
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.units = 15
        stock_level.price = 20
        stock_level.save()

        # Update product price
        Product.objects.get(name="Shampoo").save()
    
        # Confirm product price
        self.assertEqual(Product.objects.get(name="Shampoo").average_price, 20)

    def test_update_product_average_price_method_wont_ingore_price_and_units_that_have_1(self):

        # Update product stock levels price
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 1
        stock_level.price = 1
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product)
        stock_level.units = 15
        stock_level.price = 20
        stock_level.save()

        # Update product price
        Product.objects.get(name="Shampoo").save()
    
        # Confirm product price
        self.assertEqual(Product.objects.get(name="Shampoo").average_price, Decimal('10.50'))

    def test_soft_delete_method(self):

        product = Product.objects.get(name="Shampoo")
        
        self.assertEqual(product.is_deleted, False)

        product.soft_delete()

        product = Product.objects.get(name="Shampoo")

        self.assertEqual(product.is_deleted, True)
        self.assertEqual(
            (product.deleted_date).strftime("%B, %d, %Y"), 
            (timezone.now()).strftime("%B, %d, %Y")
        )

"""
=========================== ProductCount ===================================
"""  
# ProductCount
class ProductCountTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store = create_new_store(self.profile, 'Computer Store')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.profile, 'chris')

        # Create a product
        self.product = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )
        
    def test_ProductCount_fields_verbose_names(self):
        """
        Ensure all fields in ProductCount have the correct verbose names and can be
        found
        """    
  
        product_count = ProductCount.objects.get(profile=self.profile)
        
        self.assertEqual(product_count._meta.get_field('name').verbose_name,'name')
        self.assertEqual(product_count._meta.get_field('cost').verbose_name,'cost')
        self.assertEqual(product_count._meta.get_field('price').verbose_name,'price')
        self.assertEqual(product_count._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(product_count._meta.get_field('created_date').verbose_name,'created date')
        
        fields = ([field.name for field in ProductCount._meta.fields])
        
        self.assertEqual(len(fields), 9)
 
    def test_ProductCount_existence(self):
        
        product_count = ProductCount.objects.get(profile=self.profile)
        self.assertEqual(product_count.profile, self.profile) 
        self.assertEqual(product_count.tax, self.tax)
        self.assertEqual(product_count.category, self.category) 
        self.assertEqual(product_count.name, "Shampoo")
        self.assertEqual(product_count.cost, 1000)
        self.assertEqual(product_count.price, 2500)
        self.assertEqual(product_count.reg_no, self.product.reg_no)
       
    def test_get_created_date_method(self):
  
        product_count = ProductCount.objects.get(profile=self.profile)
             
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            product_count.get_created_date(self.user.get_user_timezone()))
        )
       
    def test_if_ProductCount_wont_be_deleted_when_profile_is_deleted(self):
        
        self.profile.delete()
        
        # Confirm if the profile has been deleted
        self.assertEqual(Profile.objects.all().count(), 0)
        
        # Confirm number of product counts
        self.assertEqual(ProductCount.objects.all().count(), 1)

    def test_if_ProductCount_wont_be_deleted_when_store_is_deleted(self):
        
        self.profile.delete()
        
        # Confirm if the store has been deleted
        self.assertEqual(Store.objects.all().count(), 0)
        
        # Confirm number of product counts
        self.assertEqual(ProductCount.objects.all().count(), 1)

    def test_if_ProductCount_wont_be_deleted_when_tax_is_deleted(self):
        
        self.profile.delete()
        
        # Confirm if the tax has been deleted
        self.assertEqual(Tax.objects.all().count(), 0)
        
        # Confirm number of product counts
        self.assertEqual(ProductCount.objects.all().count(), 1)

    def test_if_ProductCount_wont_be_deleted_when_category_is_deleted(self):
        
        self.profile.delete()
        
        # Confirm if the category has been deleted
        self.assertEqual(Category.objects.all().count(), 0)
        
        # Confirm number of product counts
        self.assertEqual(ProductCount.objects.all().count(), 1)


"""
=========================== ProductBundle ===================================
"""
class ProductBundleTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')
        
        #Create a store
        self.store = create_new_store(self.profile, 'Computer Store')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.profile, 'chris')

        # Create a product
        self.product = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        self.bundle = ProductBundle.objects.create(
            product_bundle=self.product,
            quantity=30
        )
    
    def test_product_bundle_fields_verbose_names(self):

        bundle = ProductBundle.objects.get(product_bundle=self.product)

        self.assertEqual(bundle._meta.get_field('product_bundle').verbose_name,'product bundle')
        self.assertEqual(bundle._meta.get_field('quantity').verbose_name,'quantity')
        
        fields = ([field.name for field in ProductBundle._meta.fields])
        
        self.assertEqual(len(fields), 3)

    def test_product_bundle_fields_after_it_has_been_created(self):

        bundle = ProductBundle.objects.get(product_bundle=self.product)

        self.assertEqual(bundle.product_bundle, self.product)
        self.assertEqual(bundle.quantity, 30)

        self.assertEqual(bundle.__str__(), f'Bundle {self.product.name}')

"""
=========================== ProductProductionMap ===================================
"""
class ProductProductionMapTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')
        
        #Create a store
        self.store = create_new_store(self.profile, 'Computer Store')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.profile, 'chris')

        # Create a product
        self.product = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        ProductProductionMap.objects.create(
            name='Sugar To 1 Kg',
            product_map=self.product,
            quantity=30
        )

    def test_if_production_count_is_updated_when_production_map_is_added_or_removed(self):
        
        # Check initial state
        product = Product.objects.get(name="Shampoo")
        self.assertEqual(product.production_count, 0)
        self.assertEqual(product.productions.all().count(), 0)

        # Add map
        product_map = ProductProductionMap.objects.get(product_map=self.product)
        product.productions.add(product_map)

        # Check if state was updated
        product = Product.objects.get(name="Shampoo")
        self.assertEqual(product.production_count, 1)
        self.assertEqual(product.productions.all().count(), 1)

        # Remove map
        product_map = ProductProductionMap.objects.get(product_map=self.product)
        product.productions.remove(product_map)

        # Check if state was updated
        product = Product.objects.get(name="Shampoo")
        self.assertEqual(product.production_count, 0)
        self.assertEqual(product.productions.all().count(), 0)

    def test_product_production_map_fields_verbose_names(self):

        product_map = ProductProductionMap.objects.get(product_map=self.product)

        self.assertEqual(product_map._meta.get_field('name').verbose_name,'name')
        self.assertEqual(product_map._meta.get_field('product_map').verbose_name,'product map')
        self.assertEqual(product_map._meta.get_field('quantity').verbose_name,'quantity')
        
        fields = ([field.name for field in ProductProductionMap._meta.fields])
        
        self.assertEqual(len(fields), 5)

    def test_product_production_map_fields_after_it_has_been_created(self):

        product_map = ProductProductionMap.objects.get(product_map=self.product)

        self.assertEqual(product_map.name, 'Sugar To 1 Kg')
        self.assertEqual(product_map.product_map, self.product)
        self.assertEqual(product_map.quantity, 30)

        self.assertEqual(product_map.__str__(), f'Production {self.product.name}')

"""
=========================== ProductVariantOption ===================================
"""  
class ProductVariantOptionTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store = create_new_store(self.profile, 'Computer Store')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a product
        self.product = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        # Create product variant option
        ProductVariantOption.objects.create(
            product=self.product,
            name='Size'
        )

    def test_model_fields_verbose_names(self):
        """
        Ensure all fields have the correct verbose names
        """    
  
        pvo = ProductVariantOption.objects.get(name='Size')
        
        self.assertEqual(pvo._meta.get_field('product').verbose_name,'product')
        self.assertEqual(pvo._meta.get_field('name').verbose_name,'name')
        
        fields = ([field.name for field in ProductVariantOption._meta.fields])
        
        self.assertEqual(len(fields), 4)

    def test_model_existence(self):
        
        pvo = ProductVariantOption.objects.get(name='Size')

        self.assertEqual(pvo.product, self.product)
        self.assertEqual(pvo.name, 'Size')

"""
=========================== ProductVariantOptionChoice ===================================
"""  
class ProductVariantOptionChoiceTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store = create_new_store(self.profile, 'Computer Store')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a product
        self.product = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        # Create product variant option
        self.product_variant_option = ProductVariantOption.objects.create(
            product=self.product,
            name='Size'
        )

        # Create product variant option choices
        ProductVariantOptionChoice.objects.create(
            product_variant_option=self.product_variant_option,
            name='Small'
        )

        # Create product variant option choices
        ProductVariantOptionChoice.objects.create(
            product_variant_option=self.product_variant_option,
            name='Medium'
        )

        # Create product variant option choices
        ProductVariantOptionChoice.objects.create(
            product_variant_option=self.product_variant_option,
            name='Large'
        )

    def test_model_fields_verbose_names(self):
        """
        Ensure all fields have the correct verbose names
        """    
  
        choice = ProductVariantOptionChoice.objects.get(name='Small')
        
        self.assertEqual(choice._meta.get_field('product_variant_option').verbose_name,'product variant option')
        self.assertEqual(choice._meta.get_field('name').verbose_name,'name')
        
        fields = ([field.name for field in ProductVariantOptionChoice._meta.fields])
        
        self.assertEqual(len(fields), 4)

    def test_model_existence(self):
        
        choice = ProductVariantOptionChoice.objects.get(name='Small')

        self.assertEqual(choice.product_variant_option, self.product_variant_option)
        self.assertEqual(choice.name, 'Small')


"""
=========================== ProductVariant ===================================
"""  
class ProductVariantTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store = create_new_store(self.profile, 'Computer Store')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.profile, 'chris')

        # Create a product
        product1 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        # Add variant to product
        self.product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )
        self.product2.stores.add(self.store)

        variant = ProductVariant.objects.create(product_variant=self.product2)
        
        product1.variants.add(variant)

    def test_model_fields_verbose_names(self):
        """
        Ensure all fields in model have the correct verbose names
        """    
  
        variant = ProductVariant.objects.get(product_variant=self.product2)
        
        self.assertEqual(variant._meta.get_field('product_variant').verbose_name,'product variant')
        self.assertEqual(variant._meta.get_field('reg_no').verbose_name,'reg no')
        
        fields = ([field.name for field in ProductVariant._meta.fields])
        
        self.assertEqual(len(fields), 3)

    def test_model_existence(self):
        
        variant = ProductVariant.objects.get(product_variant=self.product2)

        self.assertEqual(variant.product_variant, self.product2) 
        self.assertEqual(variant.reg_no, self.product2.reg_no)

        self.assertEqual(variant.__str__(),  f'Variant {self.product2.name}')
