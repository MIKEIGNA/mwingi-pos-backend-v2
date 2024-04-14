import datetime
from decimal import Decimal
from django.utils import timezone
from core.test_utils.custom_testcase import TestCase
from core.test_utils.create_user import (
    create_new_cashier_user,
    create_new_customer,
    create_new_supplier,
    create_new_user, 
)
from core.test_utils.create_store_models import create_new_category, create_new_store, create_new_tax

from core.test_utils.date_utils import DateUtils
from core.test_utils.log_reader import get_test_firebase_sender_log_content
from inventories.models.inventory_valuation_models import InventoryValuation, InventoryValuationLine
from products.models import Product, ProductProductionMap 

from profiles.models import Profile

from inventories.models import (
    InventoryCount,
    InventoryCountCount, 
    InventoryCountLine,
    InventoryHistory,
    ProductTransform,
    ProductTransformCount,
    ProductTransformLine, 
    PurchaseOrder, 
    PurchaseOrderAdditionalCost,
    PurchaseOrderCount, 
    PurchaseOrderLine, 
    StockAdjustment,
    StockAdjustmentCount, 
    StockAdjustmentLine, 
    StockLevel, 
    Supplier, 
    SupplierCount, 
    TransferOrder,
    TransferOrderCount, 
    TransferOrderLine
)
from stores.models import Store

"""
=========================== StockLevel ===================================
"""  
# StockLevel
class StockLevelTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store1.loyverse_store_id = 'eca0890b-cbd9-4172-9b34-703ef2f84705'
        self.store1.save()

        self.store2 = create_new_store(self.profile, 'Toy Store')
        self.store2.loyverse_store_id = '82158310-3276-4962-8210-2ca88d7e7f13'
        self.store2.save()

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store1, 'Standard')

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
            barcode='code123',
            track_stock = True,
            loyverse_variant_id = '1ec7f40d-750a-449e-a53d-2e7bb8476a51'
        )

    def create_bundles(self):

        # Delete all products first
        Product.objects.all().delete()

        sugar_sack = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Sugar 50kg Sack",
            price=35000,
            cost=30000,
            barcode='code123'
        )

        sugar_1kg = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Sugar 1kg",
            price=2500,
            cost=1000,
            barcode='code123' 
        )

        sugar_500g = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Sugar 500g",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        sugar_250g = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Sugar 250g",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        # Create master product with 2 productions
        sugar_1kg_map = ProductProductionMap.objects.create(
            product_map=sugar_1kg,
            quantity=50
        )

        sugar_500g_map = ProductProductionMap.objects.create(
            product_map=sugar_500g,
            quantity=100
        )

        sugar_250g_map = ProductProductionMap.objects.create(
            product_map=sugar_250g,
            quantity=200
        )

        sugar_sack.productions.add(sugar_1kg_map, sugar_500g_map, sugar_250g_map)


        # Change stock amount
        # Product1
        stock_level = StockLevel.objects.get(store=self.store1, product=sugar_sack)
        stock_level.units = 20
        stock_level.save()

        # Product2
        stock_level = StockLevel.objects.get(store=self.store1, product=sugar_1kg)
        stock_level.units = 45
        stock_level.save()

        # Product3
        stock_level = StockLevel.objects.get(store=self.store1, product=sugar_500g)
        stock_level.units = 60
        stock_level.save()

        # Product4
        stock_level = StockLevel.objects.get(store=self.store1, product=sugar_250g)
        stock_level.units = 75
        stock_level.save()
    
    def test_stock_level_fields_verbose_names(self):
        """
        Ensure all fields in stock_level have the correct verbose names and can be
        found
        """    
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
       
        self.assertEqual(stock_level._meta.get_field('store').verbose_name,'store')
        self.assertEqual(stock_level._meta.get_field('product').verbose_name,'product')
        self.assertEqual(stock_level._meta.get_field('minimum_stock_level').verbose_name,'minimum stock level')
        self.assertEqual(stock_level._meta.get_field('units').verbose_name,'units')
        self.assertEqual(stock_level._meta.get_field('price').verbose_name,'price')
        self.assertEqual(stock_level._meta.get_field('status').verbose_name,'status')
        self.assertEqual(stock_level._meta.get_field('is_sellable').verbose_name,'is sellable')
        self.assertEqual(
            stock_level._meta.get_field('inlude_in_price_calculations').verbose_name,
            'inlude in price calculations'
        )
        
        fields = ([field.name for field in StockLevel._meta.fields])
        
        self.assertEqual(len(fields), 12)

    def test_stock_level_fields_after_it_has_been_created(self):

        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)

        self.assertEqual(stock_level.store, self.store1)
        self.assertEqual(stock_level.product, self.product)
        self.assertEqual(stock_level.minimum_stock_level, 0)
        self.assertEqual(stock_level.units, 0)
        self.assertEqual(stock_level.price, Decimal('2500.00'))
        self.assertEqual(stock_level.status, StockLevel.STOCK_LEVEL_OUT_OF_STOCK)
        self.assertEqual(stock_level.is_sellable, True)
        self.assertEqual(stock_level.inlude_in_price_calculations, True)

    def test_if_stock_level_status_will_change_to_in_stock(self):

        # Test with 50 units
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.minimum_stock_level = 50
        stock_level.units = 50
        stock_level.save()

        self.assertEqual(stock_level.units, 50)
        self.assertEqual(stock_level.status, StockLevel.STOCK_LEVEL_IN_STOCK)

        # Test with 51 units
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 51
        stock_level.save()

        self.assertEqual(stock_level.units, 51)
        self.assertEqual(stock_level.status, StockLevel.STOCK_LEVEL_IN_STOCK)

    def test_if_stock_level_status_will_change_to_low_stock(self):

        # Test with 30 units
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.minimum_stock_level = 50
        stock_level.units = 30
        stock_level.save()

        self.assertEqual(stock_level.units, 30)
        self.assertEqual(stock_level.status, StockLevel.STOCK_LEVEL_LOW_STOCK)

        # Test with 1 units
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 1
        stock_level.save()

        self.assertEqual(stock_level.units, 1)
        self.assertEqual(stock_level.status, StockLevel.STOCK_LEVEL_LOW_STOCK)

    def test_if_stock_level_status_will_change_to_out_of_stock(self):

        # Test with 0 units
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.minimum_stock_level = 50
        stock_level.units = 0
        stock_level.save()

        self.assertEqual(stock_level.units, 0)
        self.assertEqual(stock_level.status, StockLevel.STOCK_LEVEL_OUT_OF_STOCK)

        # Test with -1 units
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = -1
        stock_level.save()

        self.assertEqual(stock_level.units, -1)
        self.assertEqual(stock_level.status, StockLevel.STOCK_LEVEL_OUT_OF_STOCK)

    def test_firebase_message_are_sent_correctly(self):

        # *************** Change to in ctock
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.minimum_stock_level = 50
        stock_level.units = 50
        stock_level.save()

        self.assertEqual(stock_level.units, 50)
        self.assertEqual(stock_level.status, StockLevel.STOCK_LEVEL_IN_STOCK)

        content = get_test_firebase_sender_log_content(only_include=['stock_level'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'stock_level', 
                'action_type': 'edit', 
                'product_reg_no': str(self.product.reg_no), 
                'minimum_stock_level': '50',
                'units': '50', 
                'notify_low_stock': 'False'
            }
        }

        self.assertEqual(content[0], result)

        # *************** Change to low ctock from in stock
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.minimum_stock_level = 50
        stock_level.units = 30
        stock_level.save()

        self.assertEqual(stock_level.units, 30)
        self.assertEqual(stock_level.status, StockLevel.STOCK_LEVEL_LOW_STOCK)

        content = get_test_firebase_sender_log_content(only_include=['stock_level'])
        self.assertEqual(len(content), 2)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'stock_level', 
                'action_type': 'edit', 
                'product_reg_no': str(self.product.reg_no), 
                'minimum_stock_level': '50',
                'units': '30', 
                'notify_low_stock': 'True'
            }
        }

        self.assertEqual(content[1], result)

        # *************** Change to out of ctock
        # Test with 0 units
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.minimum_stock_level = 50
        stock_level.units = 0
        stock_level.save()

        self.assertEqual(stock_level.units, 0)
        self.assertEqual(stock_level.status, StockLevel.STOCK_LEVEL_OUT_OF_STOCK)

        content = get_test_firebase_sender_log_content(only_include=['stock_level'])
        self.assertEqual(len(content), 3)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'stock_level', 
                'action_type': 'edit', 
                'product_reg_no': str(self.product.reg_no), 
                'minimum_stock_level': '50',
                'units': '0', 
                'notify_low_stock': 'False'
            }
        }

        self.assertEqual(content[2], result)

    def test_notify_low_stock_wont_be_sent_when_stock_changes_from_out_of_stock_to_low_stock(self):

        # Change from out of stock to low stock
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.minimum_stock_level = 50
        stock_level.units = 30
        stock_level.save()

        self.assertEqual(stock_level.units, 30)
        self.assertEqual(stock_level.status, StockLevel.STOCK_LEVEL_LOW_STOCK)

        content = get_test_firebase_sender_log_content(only_include=['stock_level'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'stock_level', 
                'action_type': 'edit', 
                'product_reg_no': str(self.product.reg_no), 
                'minimum_stock_level': '50',
                'units': '30', 
                'notify_low_stock': 'False'
            }
        }

        self.assertEqual(content[0], result)

    def test_notify_low_stock_will_be_sent_when_stock_changes_from_in_of_stock_to_low_stock(self):

        # Change from in stock to low stock
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.minimum_stock_level = 50
        stock_level.status = StockLevel.STOCK_LEVEL_IN_STOCK
        stock_level.units = 30
        stock_level.save()

        self.assertEqual(stock_level.units, 30)
        self.assertEqual(stock_level.status, StockLevel.STOCK_LEVEL_LOW_STOCK)

        content = get_test_firebase_sender_log_content(only_include=['stock_level'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'stock_level', 
                'action_type': 'edit', 
                'product_reg_no': str(self.product.reg_no), 
                'minimum_stock_level': '50',
                'units': '30', 
                'notify_low_stock': 'True'
            }
        }

        self.assertEqual(content[0], result)

    def test_update_level_method_when_adding_stock(self):

        # Start with a stock of 50
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 50
        stock_level.save()

        # Update stock level for product 1
        StockLevel.update_level(
            user=self.user,
            store=self.store1, 
            product=self.product, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_RECEIVE,
            change_source_reg_no=self.product.reg_no,
            change_source_name="TO23",
            line_source_reg_no=111,
            adjustment=300, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_ADDING
        )

        history = InventoryHistory.objects.get(store=self.store1)
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.store, self.store1)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.reason, InventoryHistory.INVENTORY_HISTORY_RECEIVE)
        self.assertEqual(history.change_source_reg_no, self.product.reg_no)
        self.assertEqual(history.change_source_desc,'Receive')
        self.assertEqual(history.change_source_name,'TO23')
        self.assertEqual(history.line_source_reg_no, 111)
        self.assertEqual(history.adjustment, Decimal('300.00'))
        self.assertEqual(history.stock_after, Decimal('350.00'))
    
    def test_update_level_method_wont_update_the_stock_from_the_same_line_source_twice(self):

        today = timezone.now()

        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=today
        )

        valuation = InventoryValuation.objects.get(store=self.store1)

        lines = valuation.inventoryvaluationline_set.all()

        self.assertEqual(lines[0].product, self.product)
        self.assertEqual(lines[0].cost, Decimal('1000.00'))
        self.assertEqual(lines[0].units, Decimal('0.00'))
        self.assertEqual(lines[0].inventory_value, Decimal('0.00'))
        self.assertEqual(lines[0].retail_value, Decimal('0.00'))
        self.assertEqual(lines[0].potential_profit, Decimal('0.00'))
        self.assertEqual(lines[0].margin, 0)

        # Start with a stock of 50
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 5400
        stock_level.save()

        for _ in range(2):
            # Update stock level for product 1
            StockLevel.update_level(
                user=self.user,
                store=self.store1, 
                product=self.product, 
                inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_SALE,
                change_source_reg_no=self.product.reg_no,
                change_source_name="#12345",
                line_source_reg_no=111,
                adjustment=300, 
                update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
            )
      
        # Confirm stock level
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        self.assertEqual(stock_level.units, 5100)

        # Confirm inventory history was updated
        history = InventoryHistory.objects.get(store=self.store1)
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.store, self.store1)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(history.change_source_reg_no, self.product.reg_no)
        self.assertEqual(history.change_source_desc, 'Sale')
        self.assertEqual(history.change_source_name,'#12345')
        self.assertEqual(history.line_source_reg_no, 111)
        self.assertEqual(history.adjustment, Decimal('-300.00'))
        self.assertEqual(history.stock_after, Decimal('5100.00'))

        # Confirm inventory valuation was updated
        lines = valuation.inventoryvaluationline_set.all()

        self.assertEqual(lines[0].product, self.product)
        self.assertEqual(lines[0].price, Decimal('2500.00'))
        self.assertEqual(lines[0].cost, Decimal('1000.00'))
        self.assertEqual(lines[0].units, Decimal('5100.00'))
        self.assertEqual(lines[0].inventory_value, Decimal('5100000.00'))
        self.assertEqual(lines[0].retail_value, Decimal('12750000.00'))
        self.assertEqual(lines[0].potential_profit, Decimal('7650000.00'))
        self.assertEqual(lines[0].margin, 60)

    def test_update_level_method_will_update_the_stock_from_the_same_source_if_the_line_source_reg_no_is_different(self):

        today = timezone.now()

        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=today
        )

        valuation = InventoryValuation.objects.get(store=self.store1)

        lines = valuation.inventoryvaluationline_set.all()

        self.assertEqual(lines[0].product, self.product)
        self.assertEqual(lines[0].cost, Decimal('1000.00'))
        self.assertEqual(lines[0].units, Decimal('0.00'))
        self.assertEqual(lines[0].inventory_value, Decimal('0.00'))
        self.assertEqual(lines[0].retail_value, Decimal('0.00'))
        self.assertEqual(lines[0].potential_profit, Decimal('0.00'))
        self.assertEqual(lines[0].margin, 0)

        # Start with a stock of 50
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 5400
        stock_level.save()

        for i in range(2):
            # Update stock level for product 1
            StockLevel.update_level(
                user=self.user,
                store=self.store1, 
                product=self.product, 
                inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_SALE,
                change_source_reg_no=self.product.reg_no,
                change_source_name="#12345",
                line_source_reg_no=i,
                adjustment=300, 
                update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
            )
      
        # Confirm stock level
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        self.assertEqual(stock_level.units, 4800)

        # Confirm inventory historys were updated
        historys = InventoryHistory.objects.filter(store=self.store1).order_by('id')

        self.assertEqual(historys.count(), 2)
        
        self.assertEqual(historys[0].user, self.user)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].store, self.store1)
        self.assertEqual(historys[0].product, self.product)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[0].change_source_reg_no, self.product.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Sale')
        self.assertEqual(historys[0].change_source_name,'#12345')
        self.assertEqual(historys[0].line_source_reg_no, 0)
        self.assertEqual(historys[0].adjustment, Decimal('-300.00'))
        self.assertEqual(historys[0].stock_after, Decimal('5100.00'))

        self.assertEqual(historys[1].user, self.user)
        self.assertEqual(historys[1].product, self.product)
        self.assertEqual(historys[1].store, self.store1)
        self.assertEqual(historys[1].product, self.product)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(historys[1].change_source_reg_no, self.product.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Sale')
        self.assertEqual(historys[1].change_source_name,'#12345')
        self.assertEqual(historys[1].line_source_reg_no, 1)
        self.assertEqual(historys[1].adjustment, Decimal('-300.00'))
        self.assertEqual(historys[1].stock_after, Decimal('4800.00'))

        # Confirm inventory valuation was updated
        lines = valuation.inventoryvaluationline_set.all()

        self.assertEqual(lines[0].product, self.product)
        self.assertEqual(lines[0].price, Decimal('2500.00'))
        self.assertEqual(lines[0].cost, Decimal('1000.00'))
        self.assertEqual(lines[0].units, Decimal('4800.00'))
        self.assertEqual(lines[0].inventory_value, Decimal('4800000.00'))
        self.assertEqual(lines[0].retail_value, Decimal('12000000.00'))
        self.assertEqual(lines[0].potential_profit, Decimal('7200000.00'))
        self.assertEqual(lines[0].margin, 60)

    def test_update_inventory_valuation_line_when_a_sale_is_happening(self):

        today = timezone.now()

        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=today
        )

        valuation = InventoryValuation.objects.get(store=self.store1)

        lines = valuation.inventoryvaluationline_set.all()

        self.assertEqual(lines[0].product, self.product)
        self.assertEqual(lines[0].cost, Decimal('1000.00'))
        self.assertEqual(lines[0].units, Decimal('0.00'))
        self.assertEqual(lines[0].inventory_value, Decimal('0.00'))
        self.assertEqual(lines[0].retail_value, Decimal('0.00'))
        self.assertEqual(lines[0].potential_profit, Decimal('0.00'))
        self.assertEqual(lines[0].margin, 0)

        # Start with a stock of 50
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 5400
        stock_level.save()

        # Update stock level for product 1
        StockLevel.update_level(
            user=self.user,
            store=self.store1, 
            product=self.product, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_SALE,
            change_source_reg_no=self.product.reg_no,
            change_source_name="#12345",
            line_source_reg_no=111,
            adjustment=300, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm inventory history was updated
        history = InventoryHistory.objects.get(store=self.store1)
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.store, self.store1)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(history.change_source_reg_no, self.product.reg_no)
        self.assertEqual(history.change_source_desc, 'Sale')
        self.assertEqual(history.change_source_name,'#12345')
        self.assertEqual(history.line_source_reg_no, 111)
        self.assertEqual(history.adjustment, Decimal('-300.00'))
        self.assertEqual(history.stock_after, Decimal('5100.00'))

        # Confirm inventory valuation was updated
        lines = valuation.inventoryvaluationline_set.all()

        self.assertEqual(lines[0].product, self.product)
        self.assertEqual(lines[0].price, Decimal('2500.00'))
        self.assertEqual(lines[0].cost, Decimal('1000.00'))
        self.assertEqual(lines[0].units, Decimal('5100.00'))
        self.assertEqual(lines[0].inventory_value, Decimal('5100000.00'))
        self.assertEqual(lines[0].retail_value, Decimal('12750000.00'))
        self.assertEqual(lines[0].potential_profit, Decimal('7650000.00'))
        self.assertEqual(lines[0].margin, 60)

    def test_update_inventory_valuation_line_when_a_refund_is_happening(self):

        today = timezone.now()

        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=today
        )

        valuation = InventoryValuation.objects.get(store=self.store1)

        lines = valuation.inventoryvaluationline_set.all()

        self.assertEqual(lines[0].product, self.product)
        self.assertEqual(lines[0].cost, Decimal('1000.00'))
        self.assertEqual(lines[0].units, Decimal('0.00'))
        self.assertEqual(lines[0].inventory_value, Decimal('0.00'))
        self.assertEqual(lines[0].retail_value, Decimal('0.00'))
        self.assertEqual(lines[0].potential_profit, Decimal('0.00'))
        self.assertEqual(lines[0].margin, 0)

        # Start with a stock of 50
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 5400
        stock_level.save()

        # Update stock level for product 1
        StockLevel.update_level(
            user=self.user,
            store=self.store1, 
            product=self.product, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_REFUND,
            change_source_reg_no=self.product.reg_no,
            change_source_name="#12345",
            line_source_reg_no=111,
            adjustment=300, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_ADDING
        )

        # Confirm inventory history was updated
        history = InventoryHistory.objects.get(store=self.store1)
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.store, self.store1)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.reason, InventoryHistory.INVENTORY_HISTORY_REFUND)
        self.assertEqual(history.change_source_reg_no, self.product.reg_no)
        self.assertEqual(history.change_source_desc, 'Refund')
        self.assertEqual(history.change_source_name,'#12345')
        self.assertEqual(history.line_source_reg_no, 111)
        self.assertEqual(history.adjustment, Decimal('300.00'))
        self.assertEqual(history.stock_after, Decimal('5700.00'))

        # Confirm inventory valuation was updated
        lines = valuation.inventoryvaluationline_set.all()

        self.assertEqual(lines[0].product, self.product)
        self.assertEqual(lines[0].price, Decimal('2500.00'))
        self.assertEqual(lines[0].cost, Decimal('1000.00'))
        self.assertEqual(lines[0].units, Decimal('5700.00'))
        self.assertEqual(lines[0].inventory_value, Decimal('5700000.00'))
        self.assertEqual(lines[0].retail_value, Decimal('14250000.00'))
        self.assertEqual(lines[0].potential_profit, Decimal('8550000.00'))
        self.assertEqual(lines[0].margin, 60)
    
    def test_inventory_valuation_line_update_when_product_price_is_zero(self):

        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=timezone.now()
        )

        valuation = InventoryValuation.objects.get(store=self.store1)

        valuation_line = valuation.inventoryvaluationline_set.get()
        valuation_line.price = 0
        valuation_line.save()

        self.assertEqual(valuation_line.product, self.product)
        self.assertEqual(valuation_line.price, Decimal('0.00'))
        self.assertEqual(valuation_line.cost, Decimal('1000.00'))
        self.assertEqual(valuation_line.units, Decimal('0.00'))
        self.assertEqual(valuation_line.inventory_value, Decimal('0.00'))
        self.assertEqual(valuation_line.retail_value, Decimal('0.00'))
        self.assertEqual(valuation_line.potential_profit, Decimal('0.00'))
        self.assertEqual(valuation_line.margin, 0)

        # Start with a stock of 50
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 5400
        stock_level.save()

        # Update stock level for product 1
        StockLevel.update_level(
            user=self.user,
            store=self.store1, 
            product=self.product, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_SALE,
            change_source_reg_no=self.product.reg_no,
            change_source_name="#12345",
            line_source_reg_no=111,
            adjustment=300, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm inventory history was updated
        history = InventoryHistory.objects.get(store=self.store1)
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.store, self.store1)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(history.change_source_reg_no, self.product.reg_no)
        self.assertEqual(history.change_source_desc, 'Sale')
        self.assertEqual(history.change_source_name,'#12345')
        self.assertEqual(history.line_source_reg_no, 111)
        self.assertEqual(history.adjustment, Decimal('-300.00'))
        self.assertEqual(history.stock_after, Decimal('5100.00'))

        # Confirm inventory valuation was updated
        valuation_line = valuation.inventoryvaluationline_set.get()

        self.assertEqual(valuation_line.product, self.product)
        self.assertEqual(valuation_line.price, Decimal('0.00'))
        self.assertEqual(valuation_line.cost, Decimal('1000.00'))
        self.assertEqual(valuation_line.units, Decimal('5100.00'))
        self.assertEqual(valuation_line.inventory_value, Decimal('5100000.00'))
        self.assertEqual(valuation_line.retail_value, Decimal('0.00'))
        self.assertEqual(valuation_line.potential_profit, Decimal('-5100000.00'))
        self.assertEqual(valuation_line.margin, Decimal('0.00'))

    def test_inventory_valuation_line_update_when_product_cost_is_zero(self):

        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=timezone.now()
        )

        valuation = InventoryValuation.objects.get(store=self.store1)

        valuation_line = valuation.inventoryvaluationline_set.get()
        valuation_line.cost = 0
        valuation_line.save()

        self.assertEqual(valuation_line.product, self.product)
        self.assertEqual(valuation_line.price, Decimal('2500.00'))
        self.assertEqual(valuation_line.cost, Decimal('0.00'))
        self.assertEqual(valuation_line.units, Decimal('0.00'))
        self.assertEqual(valuation_line.inventory_value, Decimal('0.00'))
        self.assertEqual(valuation_line.retail_value, Decimal('0.00'))
        self.assertEqual(valuation_line.potential_profit, Decimal('0.00'))
        self.assertEqual(valuation_line.margin, 0)

        # Start with a stock of 50
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 5400
        stock_level.save()

        # Update stock level for product 1
        StockLevel.update_level(
            user=self.user,
            store=self.store1, 
            product=self.product, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_SALE,
            change_source_reg_no=self.product.reg_no,
            change_source_name="#12345",
            line_source_reg_no=111,
            adjustment=300, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm inventory history was updated
        history = InventoryHistory.objects.get(store=self.store1)
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.store, self.store1)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(history.change_source_reg_no, self.product.reg_no)
        self.assertEqual(history.change_source_desc, 'Sale')
        self.assertEqual(history.change_source_name,'#12345')
        self.assertEqual(history.line_source_reg_no, 111)
        self.assertEqual(history.adjustment, Decimal('-300.00'))
        self.assertEqual(history.stock_after, Decimal('5100.00'))

        # Confirm inventory valuation was updated
        valuation_line = valuation.inventoryvaluationline_set.get()

        self.assertEqual(valuation_line.product, self.product)
        self.assertEqual(valuation_line.price, Decimal('2500.00'))
        self.assertEqual(valuation_line.cost, Decimal('0.00'))
        self.assertEqual(valuation_line.units, Decimal('5100.00'))
        self.assertEqual(valuation_line.inventory_value, Decimal('0.00'))
        self.assertEqual(valuation_line.retail_value, Decimal('12750000.00'))
        self.assertEqual(valuation_line.potential_profit, Decimal('12750000.00'))
        self.assertEqual(valuation_line.margin, Decimal('100.00'))

    def test_inventory_valuation_line_update_when_product_price_and_cost_are_zero(self):

        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=timezone.now()
        )

        valuation = InventoryValuation.objects.get(store=self.store1)

        valuation_line = valuation.inventoryvaluationline_set.get()
        valuation_line.price = 0
        valuation_line.cost = 0
        valuation_line.save()

        self.assertEqual(valuation_line.product, self.product)
        self.assertEqual(valuation_line.price, Decimal('0.00'))
        self.assertEqual(valuation_line.cost, Decimal('0.00'))
        self.assertEqual(valuation_line.units, Decimal('0.00'))
        self.assertEqual(valuation_line.inventory_value, Decimal('0.00'))
        self.assertEqual(valuation_line.retail_value, Decimal('0.00'))
        self.assertEqual(valuation_line.potential_profit, Decimal('0.00'))
        self.assertEqual(valuation_line.margin, 0)

        # Start with a stock of 50
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 5400
        stock_level.save()

        # Update stock level for product 1
        StockLevel.update_level(
            user=self.user,
            store=self.store1, 
            product=self.product, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_SALE,
            change_source_reg_no=self.product.reg_no,
            change_source_name="#12345",
            line_source_reg_no=111,
            adjustment=300, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm inventory history was updated
        history = InventoryHistory.objects.get(store=self.store1)
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.store, self.store1)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(history.change_source_reg_no, self.product.reg_no)
        self.assertEqual(history.change_source_desc, 'Sale')
        self.assertEqual(history.change_source_name,'#12345')
        self.assertEqual(history.line_source_reg_no, 111)
        self.assertEqual(history.adjustment, Decimal('-300.00'))
        self.assertEqual(history.stock_after, Decimal('5100.00'))

        # Confirm inventory valuation was updated
        valuation_line = valuation.inventoryvaluationline_set.get()

        self.assertEqual(valuation_line.product, self.product)
        self.assertEqual(valuation_line.price, Decimal('0.00'))
        self.assertEqual(valuation_line.cost, Decimal('0.00'))
        self.assertEqual(valuation_line.units, Decimal('5100.00'))
        self.assertEqual(valuation_line.inventory_value, Decimal('0.00'))
        self.assertEqual(valuation_line.retail_value, Decimal('0.00'))
        self.assertEqual(valuation_line.potential_profit, Decimal('0.00'))
        self.assertEqual(valuation_line.margin, Decimal('0.00'))

    def test_inventory_valuation_line_update_when_product_units_are_zero(self):

        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=timezone.now()
        )

        valuation = InventoryValuation.objects.get(store=self.store1)

        valuation_line = valuation.inventoryvaluationline_set.get()

        self.assertEqual(valuation_line.product, self.product)
        self.assertEqual(valuation_line.price, Decimal('2500.00'))
        self.assertEqual(valuation_line.cost, Decimal('1000.00'))
        self.assertEqual(valuation_line.units, Decimal('0.00'))
        self.assertEqual(valuation_line.inventory_value, Decimal('0.00'))
        self.assertEqual(valuation_line.retail_value, Decimal('0.00'))
        self.assertEqual(valuation_line.potential_profit, Decimal('0.00'))
        self.assertEqual(valuation_line.margin, 0)

        # Start with a stock of 50
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 300
        stock_level.save()

        # Update stock level for product 1
        StockLevel.update_level(
            user=self.user,
            store=self.store1, 
            product=self.product, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_SALE,
            change_source_reg_no=self.product.reg_no,
            change_source_name="#12345",
            line_source_reg_no=111,
            adjustment=300, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm inventory history was updated
        history = InventoryHistory.objects.get(store=self.store1)
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.store, self.store1)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(history.change_source_reg_no, self.product.reg_no)
        self.assertEqual(history.change_source_desc, 'Sale')
        self.assertEqual(history.change_source_name,'#12345')
        self.assertEqual(history.line_source_reg_no, 111)
        self.assertEqual(history.adjustment, Decimal('-300.00'))
        self.assertEqual(history.stock_after, Decimal('0.00'))

        # Confirm inventory valuation was updated
        valuation_line = valuation.inventoryvaluationline_set.get()

        self.assertEqual(valuation_line.product, self.product)
        self.assertEqual(valuation_line.price, Decimal('2500.00'))
        self.assertEqual(valuation_line.cost, Decimal('1000.00'))
        self.assertEqual(valuation_line.units, Decimal('0.00'))
        self.assertEqual(valuation_line.inventory_value, Decimal('0.00'))
        self.assertEqual(valuation_line.retail_value, Decimal('0.00'))
        self.assertEqual(valuation_line.potential_profit, Decimal('0.00'))
        self.assertEqual(valuation_line.margin, Decimal('0.00'))

    def test_inventory_valuation_line_update_picks_the_correct_date(self):

        today = timezone.now()
        yesterday = today - timezone.timedelta(days=1)
        yesterday_but_1 = today - timezone.timedelta(days=2)

        # Create inventory valuations
        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=today
        )
        
        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=yesterday
        )

        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=yesterday_but_1
        )

        ### Confirm inventory valuations lines
        # Today
        valuation_line1 = InventoryValuation.objects.get(store=self.store1, created_date=today).inventoryvaluationline_set.get()

        self.assertEqual(valuation_line1.product, self.product)
        self.assertEqual(valuation_line1.price, Decimal('2500.00'))
        self.assertEqual(valuation_line1.cost, Decimal('1000.00'))
        self.assertEqual(valuation_line1.units, Decimal('0.00'))
        self.assertEqual(valuation_line1.inventory_value, Decimal('0.00'))
        self.assertEqual(valuation_line1.retail_value, Decimal('0.00'))
        self.assertEqual(valuation_line1.potential_profit, Decimal('0.00'))
        self.assertEqual(valuation_line1.margin, 0)


        # Yesterday
        valuation_line2 = InventoryValuation.objects.get(store=self.store1, created_date=yesterday).inventoryvaluationline_set.get()

        self.assertEqual(valuation_line2.product, self.product)
        self.assertEqual(valuation_line2.price, Decimal('2500.00'))
        self.assertEqual(valuation_line2.cost, Decimal('1000.00'))
        self.assertEqual(valuation_line2.units, Decimal('0.00'))
        self.assertEqual(valuation_line2.inventory_value, Decimal('0.00'))
        self.assertEqual(valuation_line2.retail_value, Decimal('0.00'))
        self.assertEqual(valuation_line2.potential_profit, Decimal('0.00'))
        self.assertEqual(valuation_line2.margin, 0)

        # Yesterday but 1
        valuation_line3 = InventoryValuation.objects.get(store=self.store1, created_date=yesterday_but_1).inventoryvaluationline_set.get()

        self.assertEqual(valuation_line3.product, self.product)
        self.assertEqual(valuation_line3.price, Decimal('2500.00'))
        self.assertEqual(valuation_line3.cost, Decimal('1000.00'))
        self.assertEqual(valuation_line3.units, Decimal('0.00'))
        self.assertEqual(valuation_line3.inventory_value, Decimal('0.00'))
        self.assertEqual(valuation_line3.retail_value, Decimal('0.00'))
        self.assertEqual(valuation_line3.potential_profit, Decimal('0.00'))
        self.assertEqual(valuation_line3.margin, 0)


        # Update stock level for product 1 on yesterday
        StockLevel.update_level(
            user=self.user,
            store=self.store1, 
            product=self.product, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_SALE,
            change_source_reg_no=self.product.reg_no,
            change_source_name="#12345",
            line_source_reg_no=111,
            adjustment=300, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING,
            created_date=yesterday
        )

        # Confirm inventory valuation was updated
        ### Confirm inventory valuations lines
        # Today
        valuation_line1 = InventoryValuation.objects.get(store=self.store1, created_date=today).inventoryvaluationline_set.get()

        self.assertEqual(valuation_line1.product, self.product)
        self.assertEqual(valuation_line1.price, Decimal('2500.00'))
        self.assertEqual(valuation_line1.cost, Decimal('1000.00'))
        self.assertEqual(valuation_line1.units, Decimal('0.00'))
        self.assertEqual(valuation_line1.inventory_value, Decimal('0.00'))
        self.assertEqual(valuation_line1.retail_value, Decimal('0.00'))
        self.assertEqual(valuation_line1.potential_profit, Decimal('0.00'))
        self.assertEqual(valuation_line1.margin, 0)


        # Yesterday
        valuation_line2 = InventoryValuation.objects.get(store=self.store1, created_date=yesterday).inventoryvaluationline_set.get()

        self.assertEqual(valuation_line2.product, self.product)
        self.assertEqual(valuation_line2.price, Decimal('2500.00'))
        self.assertEqual(valuation_line2.cost, Decimal('1000.00'))
        self.assertEqual(valuation_line2.units, Decimal('-300.00'))
        self.assertEqual(valuation_line2.inventory_value, Decimal('-300000.00'))
        self.assertEqual(valuation_line2.retail_value, Decimal('-750000.00'))
        self.assertEqual(valuation_line2.potential_profit, Decimal('-450000.00'))
        self.assertEqual(valuation_line2.margin, 60)

        # Yesterday but 1
        valuation_line3 = InventoryValuation.objects.get(store=self.store1, created_date=yesterday_but_1).inventoryvaluationline_set.get()

        self.assertEqual(valuation_line3.product, self.product)
        self.assertEqual(valuation_line3.price, Decimal('2500.00'))
        self.assertEqual(valuation_line3.cost, Decimal('1000.00'))
        self.assertEqual(valuation_line3.units, Decimal('0.00'))
        self.assertEqual(valuation_line3.inventory_value, Decimal('0.00'))
        self.assertEqual(valuation_line3.retail_value, Decimal('0.00'))
        self.assertEqual(valuation_line3.potential_profit, Decimal('0.00'))
        self.assertEqual(valuation_line3.margin, 0)
    
    def test_update_level_method_when_subrtracting_stock(self):

        today = timezone.now()

        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=today
        )

        valuation = InventoryValuation.objects.get(store=self.store1)

        lines = valuation.inventoryvaluationline_set.all()

        self.assertEqual(lines[0].product, self.product)
        self.assertEqual(lines[0].cost, Decimal('1000.00'))
        self.assertEqual(lines[0].units, Decimal('0.00'))
        self.assertEqual(lines[0].inventory_value, Decimal('0.00'))
        self.assertEqual(lines[0].retail_value, Decimal('0.00'))
        self.assertEqual(lines[0].potential_profit, Decimal('0.00'))
        self.assertEqual(lines[0].margin, 0)

        # Start with a stock of 50
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 5400
        stock_level.save()

        # Update stock level for product 1
        StockLevel.update_level(
            user=self.user,
            store=self.store1, 
            product=self.product, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_SALE,
            change_source_reg_no=self.product.reg_no,
            change_source_name="#12345",
            line_source_reg_no=111,
            adjustment=300, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm inventory history was updated
        history = InventoryHistory.objects.get(store=self.store1)
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.store, self.store1)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.reason, InventoryHistory.INVENTORY_HISTORY_SALE)
        self.assertEqual(history.change_source_reg_no, self.product.reg_no)
        self.assertEqual(history.change_source_desc, 'Sale')
        self.assertEqual(history.change_source_name,'#12345')
        self.assertEqual(history.line_source_reg_no, 111)
        self.assertEqual(history.adjustment, Decimal('-300.00'))
        self.assertEqual(history.stock_after, Decimal('5100.00'))

        # Confirm inventory valuation was updated
        lines = valuation.inventoryvaluationline_set.all()

        self.assertEqual(lines[0].product, self.product)
        self.assertEqual(lines[0].price, Decimal('2500.00'))
        self.assertEqual(lines[0].cost, Decimal('1000.00'))
        self.assertEqual(lines[0].units, Decimal('5100.00'))
        self.assertEqual(lines[0].inventory_value, Decimal('5100000.00'))
        self.assertEqual(lines[0].retail_value, Decimal('12750000.00'))
        self.assertEqual(lines[0].potential_profit, Decimal('7650000.00'))
        self.assertEqual(lines[0].margin, 60)

    def test_update_level_method_when_overwriting_stock_by_a_bigger_number(self):

        # Start with a stock of 50
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 50
        stock_level.save()

        # Update stock level for product 1
        StockLevel.update_level(
            user=self.user,
            store=self.store1, 
            product=self.product, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_REPACKAGE,
            change_source_reg_no=self.product.reg_no,
            change_source_name=self.product.__str__(),
            line_source_reg_no=111,
            adjustment=300, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_OVERWRITING
        )

        history = InventoryHistory.objects.get(store=self.store1)
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.store, self.store1)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(history.change_source_reg_no, self.product.reg_no)
        self.assertEqual(history.change_source_desc, 'Repackage')
        self.assertEqual(history.change_source_name, 'Shampoo')
        self.assertEqual(history.line_source_reg_no, 111)
        self.assertEqual(history.adjustment, Decimal('250.00'))
        self.assertEqual(history.stock_after, Decimal('300.00'))
      
    def test_update_level_method_when_overwriting_stock_by_a_smaller_number(self):

        # Start with a stock of 50
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 50
        stock_level.save()

        # Update stock level for product 1
        StockLevel.update_level(
            user=self.user,
            store=self.store1, 
            product=self.product, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_REPACKAGE,
            change_source_reg_no=self.product.reg_no,
            change_source_name=self.product.__str__(),
            line_source_reg_no=111,
            adjustment=30, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_OVERWRITING
        )

        history = InventoryHistory.objects.get(store=self.store1)
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.store, self.store1)
        self.assertEqual(history.product, self.product)
        self.assertEqual(history.reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(history.change_source_reg_no, self.product.reg_no)
        self.assertEqual(history.change_source_desc, 'Repackage')
        self.assertEqual(history.change_source_name, 'Shampoo')
        self.assertEqual(history.line_source_reg_no, 111)
        self.assertEqual(history.adjustment, Decimal('-20.00'))
        self.assertEqual(history.stock_after, Decimal('30.00'))

    def test_when_stock_level_is_created_or_saved_mwingi_connector_is_notified(self):

        # Product1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product)
        stock_level.units = 20
        stock_level.save()
 
        # Test when stock level is created and saved        
        content = get_test_firebase_sender_log_content(only_include=['connector_inventory'])

        payload = [
            {
                'payload': {
                    'model': 'connector_inventory', 
                    'payload': "{'count': 1, 'next': None, 'previous': None, 'results': [{'units': '0', 'loyverse_store_id': 'eca0890b-cbd9-4172-9b34-703ef2f84705', 'loyverse_variant_id': '1ec7f40d-750a-449e-a53d-2e7bb8476a51'}]}"
                    }
                }, 
            {
                'payload': {
                    'model': 'connector_inventory', 
                    'payload': "{'count': 1, 'next': None, 'previous': None, 'results': [{'units': '0', 'loyverse_store_id': 'eca0890b-cbd9-4172-9b34-703ef2f84705', 'loyverse_variant_id': '1ec7f40d-750a-449e-a53d-2e7bb8476a51'}]}"
                    }
            }, 
            {
                'payload': {
                    'model': 'connector_inventory', 
                    'payload': "{'count': 1, 'next': None, 'previous': None, 'results': [{'units': '0', 'loyverse_store_id': '82158310-3276-4962-8210-2ca88d7e7f13', 'loyverse_variant_id': '1ec7f40d-750a-449e-a53d-2e7bb8476a51'}]}"
                }
            }, 
            {
                'payload': {
                    'model': 'connector_inventory', 
                    'payload': "{'count': 1, 'next': None, 'previous': None, 'results': [{'units': '0', 'loyverse_store_id': '82158310-3276-4962-8210-2ca88d7e7f13', 'loyverse_variant_id': '1ec7f40d-750a-449e-a53d-2e7bb8476a51'}]}"
                }
            }, 
            {
                'payload': {
                    'model': 'connector_inventory', 
                    'payload': "{'count': 1, 'next': None, 'previous': None, 'results': [{'units': '20', 'loyverse_store_id': 'eca0890b-cbd9-4172-9b34-703ef2f84705', 'loyverse_variant_id': '1ec7f40d-750a-449e-a53d-2e7bb8476a51'}]}"
                }
            }, 
            {
                'payload': {
                    'model': 'connector_inventory', 
                    'payload': "{'count': 1, 'next': None, 'previous': None, 'results': [{'units': '20', 'loyverse_store_id': 'eca0890b-cbd9-4172-9b34-703ef2f84705', 'loyverse_variant_id': '1ec7f40d-750a-449e-a53d-2e7bb8476a51'}]}"
                }
            }
        ]

        self.assertEqual(content, payload)

"""
=========================== Supplier ===================================
"""  
class SupplierTestCase(TestCase):
    
    def setUp(self):

        #Create a top user1
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')
        
        # Create a supplier user
        self.supplier = create_new_supplier(self.top_profile, 'jeremy')
    
    def test_supplier_fields_verbose_names(self):

        supplier = Supplier.objects.get(profile=self.top_profile)
            
        self.assertEqual(supplier._meta.get_field('name').verbose_name,'name')
        self.assertEqual(supplier._meta.get_field('email').verbose_name,'email')
        self.assertEqual(supplier._meta.get_field('phone').verbose_name,'phone')
        self.assertEqual(supplier._meta.get_field('address').verbose_name,'address')
        self.assertEqual(supplier._meta.get_field('city').verbose_name,'city')
        self.assertEqual(supplier._meta.get_field('region').verbose_name,'region')
        self.assertEqual(supplier._meta.get_field('postal_code').verbose_name,'postal code')
        self.assertEqual(supplier._meta.get_field('country').verbose_name,'country')
        self.assertEqual(supplier._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(supplier._meta.get_field('created_date').verbose_name,'created date')

        fields = ([field.name for field in Supplier._meta.fields])
        
        self.assertEqual(len(fields), 12)

    def test_supplier_fields_after_it_has_been_created(self):
        """
        Product fields
        
        Ensure a supplier has the right fields after it has been created
        """
        supplier = Supplier.objects.get(profile=self.top_profile)
        
        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(supplier.profile, self.top_profile)
        
        self.assertEqual(supplier.name, "Jeremy Clackson")
        self.assertEqual(supplier.email, "jeremy@gmail.com")
        self.assertEqual(supplier.phone, 254710104010)
        self.assertEqual(supplier.address, 'Donholm')
        self.assertEqual(supplier.city, 'Nairobi')
        self.assertEqual(supplier.region, 'Africa')
        self.assertEqual(supplier.postal_code, '11011')
        self.assertEqual(supplier.country, 'Kenya')
        self.assertTrue(supplier.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((supplier.created_date).strftime("%B, %d, %Y"), today)

    def test__str__method(self):
        supplier = Supplier.objects.get(profile=self.top_profile)
        self.assertEqual(str(supplier), supplier.email)

    def test_get_non_null_phone_method(self):

        # When supplier has phone
        supplier = Supplier.objects.get(profile=self.top_profile)
        self.assertEqual(supplier.get_non_null_phone(), supplier.phone)

        # When cusomer has null phone
        supplier = Supplier.objects.get(profile=self.top_profile)
        supplier.phone = None
        supplier.save()

        supplier = Supplier.objects.get(profile=self.top_profile)
        self.assertEqual(supplier.get_non_null_phone(), '')

    def test_get_location_desc_method1(self):

        supplier = Supplier.objects.get(profile=self.top_profile)

        # When all location fields are available
        self.assertEqual(
            supplier.get_location_desc(), 
            f'{supplier.address}, {supplier.city}, {supplier.region}, {supplier.country}'
        )

        # When country field is not available
        supplier.country = ''
        supplier.save()

        self.assertEqual(
            supplier.get_location_desc(), 
            f'{supplier.address}, {supplier.city}, {supplier.region}'
        )

        # When region field is not available
        supplier.region = ''
        supplier.save()

        self.assertEqual(
            supplier.get_location_desc(), f'{supplier.address}, {supplier.city}'
        )

        # When city field is not available
        supplier.city = ''
        supplier.save()

        self.assertEqual(supplier.get_location_desc(), f'{supplier.address}')

        # When all location fields are not available
        supplier.address = ''
        supplier.save()

        self.assertEqual(supplier.get_location_desc(), '')

    def test_get_location_desc_method2(self):

        supplier = Supplier.objects.get(profile=self.top_profile)

        # When all location fields are available
        self.assertEqual(
            supplier.get_location_desc(), 
            f'{supplier.address}, {supplier.city}, {supplier.region}, {supplier.country}'
        )

        # When address field is not available
        supplier.address = ''
        supplier.save()

        self.assertEqual(
            supplier.get_location_desc(), 
            f'{supplier.city}, {supplier.region}, {supplier.country}'
        )

        # When city field is not available
        supplier.city = ''
        supplier.save()

        self.assertEqual(
            supplier.get_location_desc(), 
            f'{supplier.region}, {supplier.country}'
        )

        # When region field is not available
        supplier.region = ''
        supplier.save()

        self.assertEqual(
            supplier.get_location_desc(), f'{supplier.country}'
        )

        # When all locaion fields are not available
        supplier.country = ''
        supplier.save()

        self.assertEqual(supplier.get_location_desc(), '')

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 
        
        supplier = Supplier.objects.get(reg_no=self.supplier.reg_no)
                     
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            supplier.get_created_date(self.user.get_user_timezone()))
        )

"""
=========================== SupplierCount ===================================
"""  
# SupplierCount
class SupplierCountTestCase(TestCase):
    
    def setUp(self):
        
        #Create a top user1
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')
        
        self.store = create_new_store(self.top_profile, 'Computer Store')

        # Create a supplier user
        self.supplier = create_new_supplier(self.top_profile, 'jeremy')

    def test_SupplierCount_fields_verbose_names(self):
        """
        Ensure all fields in ProductCount have the correct verbose names and can be
        found
        """        
        supplier_count = SupplierCount.objects.get(profile=self.top_profile)

        self.assertEqual(supplier_count._meta.get_field('created_date').verbose_name,'created date')
        
        fields = ([field.name for field in SupplierCount._meta.fields])
        
        self.assertEqual(len(fields), 4)
      
    def test_SupplierCount_existence(self):

        supplier_count = SupplierCount.objects.get(profile=self.top_profile)

        today = (timezone.now()).strftime("%B, %d, %Y")
        
        self.assertEqual(supplier_count.profile, self.top_profile)
        self.assertEqual((supplier_count.created_date).strftime("%B, %d, %Y"), today)

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 
        
        supplier_count = SupplierCount.objects.get(profile=self.top_profile)
                     
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            supplier_count.get_created_date(self.user.get_user_timezone()))
        )
  
    def test_if_SupplierCount_wont_be_deleted_when_supplier_is_deleted(self):
        
        self.supplier.delete()
        
        # Confirm if the supplier has been deleted
        self.assertEqual(Supplier.objects.all().count(), 0)
        
        # Confirm number of supplier counts
        self.assertEqual(SupplierCount.objects.all().count(), 1)
        
    def test_if_SupplierCount_wont_be_deleted_when_profile_is_deleted(self):
        
        self.top_profile.delete()
        
        # Confirm if the profile has been deleted
        self.assertEqual(Profile.objects.all().count(), 0)
        
        # Confirm number of supplier counts
        self.assertEqual(SupplierCount.objects.all().count(), 1)

"""
=========================== StockAdjustment ===================================
"""
class StockAdjustmentTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user1 = create_new_user('john')
        self.user2 = create_new_user('jack')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store = create_new_store(self.profile, 'Computer Store')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Creates products
        self.product1 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )
        self.product1.stores.add(self.store)

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

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(product=self.product1)
        stock_level.units = 100
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(product=self.product2)
        stock_level.units = 155
        stock_level.save()

        # Create stock adjustment
        self.create_receive_items_stock_adjustment(user=self.user1, reg_no=0)

    def create_receive_items_stock_adjustment(self, user, reg_no=0):

        # Create stock adjustment1
        self.stock_adjustment = StockAdjustment.objects.create(
            user=user,
            store=self.store,
            notes='This is just a simple note',
            reason=StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS,
            quantity=24,
            reg_no=reg_no
        )

        # Create stock_adjustment1
        self.stock_adjustment1 =  StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment,
            product=self.product1,
            add_stock=10,
            cost=150,
        )
    
        # Create stock_adjustment2
        self.stock_adjustment2 =  StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment,
            product=self.product2,
            add_stock=14,
            cost=100,
        )

    def test_stock_adjustment_fields_verbose_names(self):

        sa = StockAdjustment.objects.get(store=self.store)

        self.assertEqual(sa._meta.get_field('notes').verbose_name,'notes')
        self.assertEqual(sa._meta.get_field('reason').verbose_name,'reason')
        self.assertEqual(sa._meta.get_field('quantity').verbose_name,'quantity')
        self.assertEqual(sa._meta.get_field('increamental_id').verbose_name,'increamental id')
        self.assertEqual(sa._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(sa._meta.get_field('created_date').verbose_name,'created date')

        fields = ([field.name for field in StockAdjustment._meta.fields])
        
        self.assertEqual(len(fields), 9)


    def test_stock_adjustment_fields_after_it_has_been_created(self):

        sa = StockAdjustment.objects.get(store=self.store)
        
        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(sa.user, self.user1)
        self.assertEqual(sa.store, self.store)
        self.assertEqual(sa.notes, 'This is just a simple note')
        self.assertEqual(sa.reason, StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS)
        self.assertEqual(sa.quantity, 24)
        self.assertTrue(sa.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((sa.created_date).strftime("%B, %d, %Y"), today)

    def test__str__method(self):

        sa = StockAdjustment.objects.get(store=self.store)
        self.assertEqual(str(sa), f'SA{sa.increamental_id}')

    def test_get_adjusted_by_method(self):

        sa = StockAdjustment.objects.get(store=self.store)
        self.assertEqual(sa.get_adjusted_by(), self.user1.get_full_name())

    def test_get_store_name_method(self):
    
        sa = StockAdjustment.objects.get(store=self.store)
        self.assertEqual(sa.get_store_name(), self.store.name)

    def test_get_created_date_method(self):

        # Confirm that get_created_date_method returns created_date
        # in local time 

        sa = StockAdjustment.objects.get(store=self.store)
             
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            sa.get_created_date(self.user1.get_user_timezone()))
        )
    
    def test_get_line_data_method(self):

        sa = StockAdjustment.objects.get(store=self.store)

        lines = sa.stockadjustmentline_set.all().order_by('id')

        result = [
            {
                'product_info': {
                    'name': self.product1.name, 
                    'sku': self.product1.sku
                }, 
                'add_stock': str(lines[0].add_stock),
                'remove_stock': str(lines[0].remove_stock), 
                'cost': str(lines[0].cost)
            },
            {
                'product_info': {
                    'name': self.product2.name, 
                    'sku': self.product2.sku
                }, 
                'add_stock': str(lines[1].add_stock), 
                'remove_stock': str(lines[1].remove_stock), 
                'cost': str(lines[1].cost)
            }
        ]

        self.assertEqual(sa.get_line_data(), result)

    def test_if_increamental_id_increaments_only_for_one_profile(self):
        """
        We test if the increamental id increases only top user profiles. If an
        an employee user is the one creating, then it increases for his/her
        top user
        """

        profile2 = Profile.objects.get(user__email='jack@gmail.com')

        employee_for_user1 = create_new_cashier_user("kate", self.profile, self.store)
        employee_for_user2 = create_new_cashier_user("ben", profile2, self.store)

        # ********************** Create transfers for the first time
        # Delete all stock adjustements first
        StockAdjustment.objects.all().delete()

        ##### Create 2 stock adjustements for user 1
        self.create_receive_items_stock_adjustment(user=self.user1, reg_no=111)
        self.create_receive_items_stock_adjustment(user=employee_for_user1, reg_no=222)

        # Stock adjsutment 1
        adjustment1 = StockAdjustment.objects.get(reg_no=111)
        adjustment_count1 = StockAdjustmentCount.objects.get(reg_no=adjustment1.reg_no)

        self.assertEqual(adjustment1.increamental_id, 1001)
        self.assertEqual(adjustment1.__str__(), f'SA{adjustment1.increamental_id}')
        self.assertEqual(adjustment_count1.increamental_id, 1001) 

        # Stock adjsutment 2
        adjustment2 = StockAdjustment.objects.get(reg_no=222)
        adjustment_count2 = StockAdjustmentCount.objects.get(reg_no=adjustment2.reg_no)

        self.assertEqual(adjustment2.increamental_id, 1002)
        self.assertEqual(adjustment2.__str__(), f'SA{adjustment2.increamental_id}')
        self.assertEqual(adjustment_count2.increamental_id, 1002) 

        ##### Create 2 stock adjustements for user 2
        self.create_receive_items_stock_adjustment(user=self.user2, reg_no=333)
        self.create_receive_items_stock_adjustment(user=employee_for_user2, reg_no=444)

        # Stock adjsutment 3
        adjustment3 = StockAdjustment.objects.get(reg_no=333)
        adjustment_count3 = StockAdjustmentCount.objects.get(reg_no=adjustment3.reg_no)

        self.assertEqual(adjustment3.increamental_id, 1000)
        self.assertEqual(adjustment3.__str__(), f'SA{adjustment3.increamental_id}')
        self.assertEqual(adjustment_count3.increamental_id, 1000) 

        # Stock adjsutment 4
        adjustment4 = StockAdjustment.objects.get(reg_no=444)
        adjustment_count4 = StockAdjustmentCount.objects.get(reg_no=adjustment4.reg_no)

        self.assertEqual(adjustment4.increamental_id, 1001)
        self.assertEqual(adjustment4.__str__(), f'SA{adjustment4.increamental_id}')
        self.assertEqual(adjustment_count4.increamental_id, 1001) 


        # ********************** Create stock adjustements for the second time
        # Delete all stock adjustements first
        StockAdjustment.objects.all().delete()

        ##### Create 2 stock adjustements for user 1
        self.create_receive_items_stock_adjustment(user=self.user1, reg_no=555)
        self.create_receive_items_stock_adjustment(user=employee_for_user1, reg_no=666)

        # Stock adjsutment 1
        adjustment1 = StockAdjustment.objects.get(reg_no=555)
        adjustment_count1 = StockAdjustmentCount.objects.get(reg_no=adjustment1.reg_no)

        self.assertEqual(adjustment1.increamental_id, 1003)
        self.assertEqual(adjustment1.__str__(), f'SA{adjustment1.increamental_id}')
        self.assertEqual(adjustment_count1.increamental_id, 1003) 

        # Stock adjsutment 2
        adjustment2 = StockAdjustment.objects.get(reg_no=666)
        adjustment_count2 = StockAdjustmentCount.objects.get(reg_no=adjustment2.reg_no)

        self.assertEqual(adjustment2.increamental_id, 1004)
        self.assertEqual(adjustment2.__str__(), f'SA{adjustment2.increamental_id}')
        self.assertEqual(adjustment_count2.increamental_id, 1004) 

        ##### Create 2 stock adjustements for user 2
        self.create_receive_items_stock_adjustment(user=self.user2, reg_no=777)
        self.create_receive_items_stock_adjustment(user=employee_for_user2, reg_no=888)

        # Stock adjsutment 3
        adjustment3 = StockAdjustment.objects.get(reg_no=777)
        adjustment_count3 = StockAdjustmentCount.objects.get(reg_no=adjustment3.reg_no)

        self.assertEqual(adjustment3.increamental_id, 1002)
        self.assertEqual(adjustment3.__str__(), f'SA{adjustment3.increamental_id}')
        self.assertEqual(adjustment_count3.increamental_id, 1002) 

        # Stock adjsutment 4
        adjustment4 = StockAdjustment.objects.get(reg_no=888)
        adjustment_count4 = StockAdjustmentCount.objects.get(reg_no=adjustment4.reg_no)

        self.assertEqual(adjustment4.increamental_id, 1003)
        self.assertEqual(adjustment4.__str__(), f'SA{adjustment4.increamental_id}')
        self.assertEqual(adjustment_count4.increamental_id, 1003)

"""
=========================== StockAdjustmentLine ===================================
"""
class StockAdjustmentLineTestCase(TestCase):
    
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

        # Creates products
        self.product1 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=500,
            cost=200,
            barcode='code123'
        )
        self.product1.stores.add(self.store)

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

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(product=self.product1)
        stock_level.units = 300
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(product=self.product2)
        stock_level.units = 155
        stock_level.save() 

    def create_receive_items_stock_adjustment(self):

        # Create stock adjustment1
        self.stock_adjustment = StockAdjustment.objects.create(
            user=self.user,
            store=self.store,
            notes='This is just a simple note',
            reason=StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS,
            quantity=24,
        )

        # Create stock_adjustment1
        self.stock_adjustment1 =  StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment,
            product=self.product1,
            add_stock=350,
            cost=190,
        )
    
        # Create stock_adjustment2
        self.stock_adjustment2 =  StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment,
            product=self.product2,
            add_stock=14,
            cost=100,
        )

    def create_loss_damage_stock_adjustment(self, reason):

        # Create stock adjustment1
        self.stock_adjustment = StockAdjustment.objects.create(
            user=self.user,
            store=self.store,
            notes='This is just a simple note',
            reason=reason,
            quantity=24,
        )

        # Create stock_adjustment1
        self.stock_adjustment1 =  StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment,
            product=self.product1,
            remove_stock=30,
            cost=150,
        )
    
        # Create stock_adjustment2
        self.stock_adjustment2 =  StockAdjustmentLine.objects.create(
            stock_adjustment=self.stock_adjustment,
            product=self.product2,
            remove_stock=25,
            cost=100,
        )
    
    def test__str__method(self):

        self.create_receive_items_stock_adjustment()

        sal = StockAdjustmentLine.objects.get(product=self.product1)
        self.assertEqual(str(sal), sal.product.name)

    def test_stock_adjustment_line_fields_verbose_names(self):

        self.create_receive_items_stock_adjustment()

        sal = StockAdjustmentLine.objects.get(product=self.product1)

        self.assertEqual(sal._meta.get_field('product_info').verbose_name,'product info')
        self.assertEqual(sal._meta.get_field('add_stock').verbose_name,'add stock')
        self.assertEqual(sal._meta.get_field('counted_stock').verbose_name,'expected stock')
        self.assertEqual(sal._meta.get_field('remove_stock').verbose_name,'remove stock')
        self.assertEqual(sal._meta.get_field('cost').verbose_name,'cost')
        self.assertEqual(sal._meta.get_field('reg_no').verbose_name,'reg no')

        fields = ([field.name for field in StockAdjustmentLine._meta.fields])
        
        self.assertEqual(len(fields), 10)

    def test_received_items_stock_adjustment_line_fields_after_it_has_been_created(self):

        self.create_receive_items_stock_adjustment()

        sal = StockAdjustmentLine.objects.get(product=self.product1)
        
        self.assertEqual(sal.stock_adjustment, self.stock_adjustment)
        self.assertEqual(sal.product, self.product1)
        self.assertEqual(
            sal.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku
            }
        )
        self.assertEqual(sal.add_stock, 350.00)
        self.assertEqual(sal.counted_stock, 0.00)
        self.assertEqual(sal.remove_stock, 0.00)
        self.assertEqual(sal.cost, 190.00)
        self.assertTrue(sal.reg_no > 100000) 

    def test_if_received_items_stock_adjustment_line_creation_will_update_stock_level_units(self):
        
        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 300.00)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 155.00)

        self.create_receive_items_stock_adjustment()

        # Check if stock was updated
        self.assertEqual(StockLevel.objects.get(store=self.store, product=self.product1).units, 650.00)
        self.assertEqual(StockLevel.objects.get(store=self.store, product=self.product2).units, 169.00)

        # Check if cost was updated
        self.assertEqual(Product.objects.get(id=self.product1.id).cost, Decimal('194.62'))
        self.assertEqual(Product.objects.get(id=self.product2.id).cost, Decimal('1108.88'))

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store).order_by('id')
        self.assertEqual(historys.count(), 2)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].store, self.store)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_RECEIVE)
        self.assertEqual(historys[0].change_source_reg_no, self.stock_adjustment.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Receive')
        self.assertEqual(historys[0].change_source_name, self.stock_adjustment.__str__())
        self.assertEqual(historys[0].line_source_reg_no, self.stock_adjustment1.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('350.00'))
        self.assertEqual(historys[0].stock_after, Decimal('650.00'))

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].store, self.store)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_RECEIVE)
        self.assertEqual(historys[1].change_source_reg_no, self.stock_adjustment.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Receive')
        self.assertEqual(historys[1].change_source_name, self.stock_adjustment.__str__())
        self.assertEqual(historys[1].line_source_reg_no, self.stock_adjustment2.reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('14.00'))
        self.assertEqual(historys[1].stock_after, Decimal('169.00'))

    def test_if_received_items_stock_adjustment_line_creation_will_update_stock_level_and_product_when_units_are_negative(self):
        
        # Update stock level for product 1 to negative
        StockLevel.objects.filter(product=self.product1).update(units=-300)

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, -300.00)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 155.00)

        self.create_receive_items_stock_adjustment()

        # Check if stock was updated
        self.assertEqual(StockLevel.objects.get(store=self.store, product=self.product1).units, 50.00)
        self.assertEqual(StockLevel.objects.get(store=self.store, product=self.product2).units, 169.00)

        # Check if cost was updated
        self.assertEqual(Product.objects.get(id=self.product1.id).cost, Decimal('194.62'))
        self.assertEqual(Product.objects.get(id=self.product2.id).cost, Decimal('1108.88'))

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store).order_by('id')
        self.assertEqual(historys.count(), 2)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].store, self.store)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_RECEIVE)
        self.assertEqual(historys[0].change_source_reg_no, self.stock_adjustment.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Receive')
        self.assertEqual(historys[0].change_source_name, self.stock_adjustment.__str__())
        self.assertEqual(historys[0].line_source_reg_no, self.stock_adjustment1.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('350.00'))
        self.assertEqual(historys[0].stock_after, Decimal('50.00'))

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].store, self.store)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_RECEIVE)
        self.assertEqual(historys[1].change_source_reg_no, self.stock_adjustment.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Receive')
        self.assertEqual(historys[1].change_source_name, self.stock_adjustment.__str__())
        self.assertEqual(historys[1].line_source_reg_no, self.stock_adjustment2.reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('14.00'))
        self.assertEqual(historys[1].stock_after, Decimal('169.00'))

    def test_loss_stock_adjustment_line_fields_after_it_has_been_created(self):

        self.create_loss_damage_stock_adjustment(StockAdjustment.STOCK_ADJUSTMENT_LOSS)

        sal = StockAdjustmentLine.objects.get(product=self.product1)
        
        self.assertEqual(sal.stock_adjustment, self.stock_adjustment)
        self.assertEqual(sal.product, self.product1)
        self.assertEqual(
            sal.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku
            }
        )
        self.assertEqual(sal.add_stock, 0.00)
        self.assertEqual(sal.counted_stock, 0.00)
        self.assertEqual(sal.remove_stock, 30.00)
        self.assertEqual(sal.cost, 150.00)
    
    def test_if_loss_stock_adjustment_line_creation_will_update_stock_level_units(self):
        
        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 300.00)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 155.00)

        self.create_loss_damage_stock_adjustment(StockAdjustment.STOCK_ADJUSTMENT_LOSS)

        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 270.00)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 130.00)

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store).order_by('id')
        self.assertEqual(historys.count(), 2)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].store, self.store)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_LOSS)
        self.assertEqual(historys[0].change_source_reg_no, self.stock_adjustment.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Loss')
        self.assertEqual(historys[0].change_source_name, self.stock_adjustment.__str__())
        self.assertEqual(historys[0].line_source_reg_no, self.stock_adjustment1.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('-30.00'))
        self.assertEqual(historys[0].stock_after, Decimal('270.00'))

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].store, self.store)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_LOSS)
        self.assertEqual(historys[1].change_source_reg_no, self.stock_adjustment.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Loss')
        self.assertEqual(historys[1].change_source_name, self.stock_adjustment.__str__())
        self.assertEqual(historys[1].line_source_reg_no, self.stock_adjustment2.reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('-25.00'))
        self.assertEqual(historys[1].stock_after, Decimal('130.00'))

    def test_damage_stock_adjustment_line_fields_after_it_has_been_created(self):

        self.create_loss_damage_stock_adjustment(StockAdjustment.STOCK_ADJUSTMENT_DAMAGE)

        sal = StockAdjustmentLine.objects.get(product=self.product1)
        
        self.assertEqual(sal.stock_adjustment, self.stock_adjustment)
        self.assertEqual(sal.product, self.product1)
        self.assertEqual(
            sal.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku
            }
        )
        self.assertEqual(sal.add_stock, 0.00)
        self.assertEqual(sal.counted_stock, 0.00)
        self.assertEqual(sal.remove_stock, 30.00)
        self.assertEqual(sal.cost, 150.00)

    def test_if_damage_stock_adjustment_line_creation_will_update_stock_level_units(self):
        
        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 300.00)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 155.00)

        self.create_loss_damage_stock_adjustment(StockAdjustment.STOCK_ADJUSTMENT_DAMAGE)

        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 270.00)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 130.00)

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store).order_by('id')
        self.assertEqual(historys.count(), 2)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].store, self.store)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_DAMAGE)
        self.assertEqual(historys[0].change_source_reg_no, self.stock_adjustment.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Damage')
        self.assertEqual(historys[0].change_source_name, self.stock_adjustment.__str__())
        self.assertEqual(historys[0].line_source_reg_no, self.stock_adjustment1.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('-30.00'))
        self.assertEqual(historys[0].stock_after, Decimal('270.00'))

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].store, self.store)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_DAMAGE)
        self.assertEqual(historys[1].change_source_reg_no, self.stock_adjustment.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Damage')
        self.assertEqual(historys[1].change_source_name, self.stock_adjustment.__str__())
        self.assertEqual(historys[1].line_source_reg_no, self.stock_adjustment2.reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('-25.00'))
        self.assertEqual(historys[1].stock_after, Decimal('130.00'))

    def test_expiry_stock_adjustment_line_fields_after_it_has_been_created(self):

        self.create_loss_damage_stock_adjustment(StockAdjustment.STOCK_ADJUSTMENT_EXPIRY)

        sal = StockAdjustmentLine.objects.get(product=self.product1)
        
        self.assertEqual(sal.stock_adjustment, self.stock_adjustment)
        self.assertEqual(sal.product, self.product1)
        self.assertEqual(
            sal.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku
            }
        )
        self.assertEqual(sal.add_stock, 0.00)
        self.assertEqual(sal.counted_stock, 0.00)
        self.assertEqual(sal.remove_stock, 30.00)
        self.assertEqual(sal.cost, 150.00)
    
    def test_if_expiry_stock_adjustment_line_creation_will_update_stock_level_units(self):
        
        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 300.00)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 155.00)

        self.create_loss_damage_stock_adjustment(StockAdjustment.STOCK_ADJUSTMENT_EXPIRY)

        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 270.00)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 130.00)

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store).order_by('id')
        self.assertEqual(historys.count(), 2)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].store, self.store)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_EXPIRY) 
        self.assertEqual(historys[0].change_source_reg_no, self.stock_adjustment.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Expiry')
        self.assertEqual(historys[0].change_source_name, self.stock_adjustment.__str__())
        self.assertEqual(historys[0].line_source_reg_no, self.stock_adjustment1.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('-30.00'))
        self.assertEqual(historys[0].stock_after, Decimal('270.00'))

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].store, self.store)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_EXPIRY)
        self.assertEqual(historys[1].change_source_reg_no, self.stock_adjustment.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Expiry')
        self.assertEqual(historys[1].change_source_name, self.stock_adjustment.__str__())
        self.assertEqual(historys[1].line_source_reg_no, self.stock_adjustment2.reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('-25.00'))
        self.assertEqual(historys[1].stock_after, Decimal('130.00'))

    def test_if_stock_adjustment_line_creation_wont_error_out_when_product_has_no_stock_level_model(self):

        StockLevel.objects.all().delete()
        self.assertEqual(StockLevel.objects.all().count(), 0)

        self.create_receive_items_stock_adjustment()

        self.assertEqual(StockLevel.objects.all().count(), 0)

"""
=========================== TransferOrder ===================================
"""
class TransferOrderModelsMixin:

    def create_transfer_order(self, user, reg_no=0):

        # Create tranfer order
        self.transfer_order = TransferOrder.objects.create(
            user=user,
            source_store=self.store1,
            destination_store=self.store2,
            notes='This is just a simple note',
            quantity=24,
            reg_no=reg_no
        )

        # Create line 1
        self.transfer_order_line1 =  TransferOrderLine.objects.create(
            transfer_order=self.transfer_order,
            product=self.product1,
            quantity=10
        )
    
        # Create line 2
        self.transfer_order_line2 = TransferOrderLine.objects.create(
            transfer_order=self.transfer_order,
            product=self.product2,
            quantity=14,
        ) 

    def create_product_maps_for_sugar(self):

        sugar_sack = Product.objects.create(
            profile=self.profile,
            name="Sugar 50kg Sack",
            price=10000,
            cost=9000,
            barcode='code123'
        )

        sugar_1kg = Product.objects.create(
            profile=self.profile,
            name="Sugar 1kg",
            price=200,
            cost=180,
            barcode='code123'
        )

        sugar_500g = Product.objects.create(
            profile=self.profile,
            name="Sugar 500g",
            price=100,
            cost=90,
            barcode='code123'
        )

        sugar_250g = Product.objects.create(
            profile=self.profile,
            name="Sugar 250g",
            price=50,
            cost=45,
            barcode='code123'
        )

        # Create master product with 2 productions
        sugar_1kg_map = ProductProductionMap.objects.create(
            product_map=sugar_1kg,
            quantity=50,
            is_auto_repackage=True

        )

        sugar_500g_map = ProductProductionMap.objects.create(
            product_map=sugar_500g,
            quantity=100
        )

        sugar_250g_map = ProductProductionMap.objects.create(
            product_map=sugar_250g,
            quantity=200
        )

        sugar_sack.productions.add(sugar_1kg_map, sugar_500g_map, sugar_250g_map)

        # Change stock amount
        # Product1
        stock_level = StockLevel.objects.get(store=self.store1, product=sugar_sack)
        stock_level.units = 20
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=sugar_sack)
        stock_level.units = 30
        stock_level.save()

        # Product2
        stock_level = StockLevel.objects.get(store=self.store1, product=sugar_1kg)
        stock_level.units = 45
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=sugar_1kg)
        stock_level.units = 70
        stock_level.save()

    def create_product_maps_for_rice(self):

        rice_25_sack = Product.objects.create(
            profile=self.profile,
            name="Rice 25kg Sack",
            price=3200,
            cost=3000,
            barcode='code123'
        )

        rice_1kg = Product.objects.create(
            profile=self.profile,
            name="Rice 1kg",
            price=150,
            cost=120,
            barcode='code123',
        )

        rice_500g = Product.objects.create(
            profile=self.profile,
            name="Rice 500g",
            price=75,
            cost=60,
            barcode='code123'
        )

        # Create master product with 2 productions
        rice_1kg_map = ProductProductionMap.objects.create(
            product_map=rice_1kg,
            quantity=25,
            is_auto_repackage=True
        )

        rice_500g_map = ProductProductionMap.objects.create(
            product_map=rice_500g,
            quantity=50
        )

        rice_25_sack.productions.add(rice_1kg_map, rice_500g_map)

        # Change stock amount
        # Product1
        stock_level = StockLevel.objects.get(store=self.store1, product=rice_25_sack)
        stock_level.units = 25
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=rice_25_sack)
        stock_level.units = 31
        stock_level.save()

        # Product2
        stock_level = StockLevel.objects.get(store=self.store1, product=rice_1kg)
        stock_level.units = 21
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=rice_1kg)
        stock_level.units = 37
        stock_level.save()

    def create_transfer_order_products_to_be_transformed(self, user, reg_no=0):

        sugar_sack = Product.objects.get(name="Sugar 50kg Sack")
        rice_25_sack = Product.objects.get(name="Rice 25kg Sack")

        # Create tranfer order
        self.transfer_order = TransferOrder.objects.create(
            user=user,
            source_store=self.store1,
            destination_store=self.store2,
            notes='This is just a simple note',
            quantity=24,
            reg_no=reg_no
        )

        # Create line 1
        self.transfer_order_line1 =  TransferOrderLine.objects.create(
            transfer_order=self.transfer_order,
            product=sugar_sack,
            quantity=10
        )

        # Create line 2
        self.transfer_order_line2 = TransferOrderLine.objects.create(
            transfer_order=self.transfer_order,
            product=rice_25_sack,
            quantity=14,
        )
    

class TransferOrderTestCase(TestCase, TransferOrderModelsMixin):
    
    def setUp(self):
        
        #Create a user1
        self.user1 = create_new_user('john')
        self.user2 = create_new_user('jack')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create 2 stores
        self.store1 = create_new_store(self.profile, 'Computer Store1')
        self.store2 = create_new_store(self.profile, 'Computer Store2')

        # Change store types
        Store.objects.filter(pk=self.store1.pk).update(is_truck=True)
        Store.objects.filter(pk=self.store2.pk).update(is_shop=True)

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store1, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Creates products
        self.product1 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )
        self.product1.stores.add(self.store1, self.store2)

        self.product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )
        self.product2.stores.add(self.store1, self.store2)

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 100
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 155
        stock_level.save()

        self.create_transfer_order(user=self.user1)
    
    def test_transfer_order_fields_verbose_names(self):

        to = TransferOrder.objects.get(source_store=self.store1)

        self.assertEqual(to._meta.get_field('notes').verbose_name,'notes')
        self.assertEqual(to._meta.get_field('status').verbose_name,'status')
        self.assertEqual(to._meta.get_field('quantity').verbose_name,'quantity')
        self.assertEqual(to._meta.get_field('increamental_id').verbose_name,'increamental id')
        self.assertEqual(to._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(to._meta.get_field('order_completed').verbose_name,'order completed')
        self.assertEqual(to._meta.get_field('created_date').verbose_name,'created date')
        self.assertEqual(to._meta.get_field('completed_date').verbose_name,'completed date')
        self.assertEqual(to._meta.get_field('is_auto_created').verbose_name,'is auto created')
        self.assertEqual(to._meta.get_field('source_description').verbose_name,'source description')

        fields = ([field.name for field in TransferOrder._meta.fields])
        
        self.assertEqual(len(fields), 14)

    def test_transfer_order_fields_after_it_has_been_created(self):

        to = TransferOrder.objects.get(source_store=self.store1)
        
        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(to.user, self.user1)
        self.assertEqual(to.source_store, self.store1)
        self.assertEqual(to.destination_store, self.store2)
        self.assertEqual(to.notes, 'This is just a simple note')
        self.assertEqual(to.quantity, 24)
        self.assertTrue(to.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((to.created_date).strftime("%B, %d, %Y"), today)
        self.assertEqual(to.is_auto_created, False)
        self.assertEqual(to.source_description, '')

    def test__str__method(self):

        to = TransferOrder.objects.get(source_store=self.store1)
        self.assertEqual(str(to), f'TO{to.increamental_id}')

    def test_get_ordered_by_method(self):

        to = TransferOrder.objects.get(source_store=self.store1)
        self.assertEqual(to.get_ordered_by(), self.user1.get_full_name())

    def test_get_stores_data_method(self):

        to = TransferOrder.objects.get(source_store=self.store1)
        self.assertEqual(
            to.get_stores_data(), 
            {
                'source_store': {
                    "name": self.store1.name, 
                    "reg_no": self.store1.reg_no
                },
                'destination_store': {
                    "name": self.store2.name, 
                    "reg_no": self.store2.reg_no
                }
            }
        )

    def test_get_source_store_name_method(self):

        to = TransferOrder.objects.get(source_store=self.store1)
        self.assertEqual(to.get_source_store_name(), self.store1.name)

    def test_get_destnation_store_name_method(self):

        to = TransferOrder.objects.get(source_store=self.store1)
        self.assertEqual(to.get_destination_store_name(), self.store2.name)

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 

        to = TransferOrder.objects.get(source_store=self.store1)
             
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            to.get_created_date(self.user1.get_user_timezone()))
        )
    
    def test_get_line_data_method(self):
        
        to = TransferOrder.objects.get(source_store=self.store1)

        lines = to.transferorderline_set.all().order_by('id')

        result = [
            {
                'product_info': {
                    'name': self.product1.name, 
                    'sku': self.product1.sku,
                    'reg_no': self.product1.reg_no
                }, 
                'quantity': str(lines[0].quantity),
                "source_store_units": Decimal('100.00'),
                "destination_store_units": Decimal('0.00'),
                'reg_no': str(lines[0].reg_no),
            },
            {
                'product_info': {
                    'name': self.product2.name, 
                    'sku': self.product2.sku,
                    'reg_no': self.product2.reg_no
                }, 
                'quantity': str(lines[1].quantity),
                "source_store_units": Decimal('155.00'),
                "destination_store_units": Decimal('0.00'),
                'reg_no': str(lines[1].reg_no),
            }
        ]

        self.assertEqual(to.get_line_data(), result)
    
    def test_if_transfer_received_fasle_wont_update_stock_level_units(self):

        # First delete all the models
        TransferOrder.objects.all().delete()
        TransferOrderLine.objects.all().delete()

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 100.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 155.00)

        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 0.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 0.00)

        self.create_transfer_order(user=self.user1)

        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 100.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 155.00)

        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 0.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 0.00)

    def test_if_transfer_received_true_will_update_product_stock_level_units(self):

        # First delete all the models
        TransferOrder.objects.all().delete()
        TransferOrderLine.objects.all().delete()

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 100.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 155.00)

        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 0.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 0.00)

        self.create_transfer_order(user=self.user1)

        transfer_lines = TransferOrderLine.objects.all().order_by('id')

        to = TransferOrder.objects.get()

        to.status = TransferOrder.TRANSFER_ORDER_RECEIVED
        to.save()

        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 90.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 141.00)

        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 10.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 14.00)

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.all().order_by('id')
        self.assertEqual(historys.count(), 4)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user1)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].store, self.store1)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_TRANSFER)
        self.assertEqual(historys[0].change_source_reg_no, to.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Transfer')
        self.assertEqual(historys[0].change_source_name, self.transfer_order.__str__())
        self.assertEqual(historys[0].line_source_reg_no, int(f'{transfer_lines[0].reg_no}0'))
        self.assertEqual(historys[0].adjustment, Decimal('-10.00'))
        self.assertEqual(historys[0].stock_after, Decimal('90.00'))

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user1)
        self.assertEqual(historys[1].product, self.product1)
        self.assertEqual(historys[1].store, self.store2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_TRANSFER)
        self.assertEqual(historys[1].change_source_reg_no, to.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Transfer')
        self.assertEqual(historys[1].change_source_name, self.transfer_order.__str__())
        self.assertEqual(historys[1].line_source_reg_no, int(f'{transfer_lines[0].reg_no}1'))
        self.assertEqual(historys[1].adjustment, Decimal('10.00'))
        self.assertEqual(historys[1].stock_after, Decimal('10.00'))

        # Inventory history 3
        self.assertEqual(historys[2].user, self.user1)
        self.assertEqual(historys[2].product, self.product2)
        self.assertEqual(historys[2].store, self.store1)
        self.assertEqual(historys[2].reason, InventoryHistory.INVENTORY_HISTORY_TRANSFER)
        self.assertEqual(historys[2].change_source_reg_no, to.reg_no)
        self.assertEqual(historys[2].change_source_desc, 'Transfer')
        self.assertEqual(historys[2].change_source_name, self.transfer_order.__str__())
        self.assertEqual(historys[2].line_source_reg_no, int(f'{transfer_lines[1].reg_no}0'))
        self.assertEqual(historys[2].adjustment, Decimal('-14.00'))
        self.assertEqual(historys[2].stock_after, Decimal('141.00'))

        # Inventory history 4
        self.assertEqual(historys[3].user, self.user1)
        self.assertEqual(historys[3].product, self.product2)
        self.assertEqual(historys[3].store, self.store2)
        self.assertEqual(historys[3].reason, InventoryHistory.INVENTORY_HISTORY_TRANSFER)
        self.assertEqual(historys[3].change_source_reg_no, to.reg_no)
        self.assertEqual(historys[3].change_source_desc, 'Transfer')
        self.assertEqual(historys[3].change_source_name, self.transfer_order.__str__())
        self.assertEqual(historys[3].line_source_reg_no, int(f'{transfer_lines[1].reg_no}1'))
        self.assertEqual(historys[3].adjustment, Decimal('14.00'))
        self.assertEqual(historys[3].stock_after, Decimal('14.00'))
    
    def test_if_transfer_received_true_will_also_create_product_transform(self):

        self.create_product_maps_for_sugar()
        self.create_product_maps_for_rice()

        # First delete all the models
        TransferOrder.objects.all().delete()
        TransferOrderLine.objects.all().delete()

        
        sugar_sack = Product.objects.get(name="Sugar 50kg Sack")
        sugar_1kg = Product.objects.get(name="Sugar 1kg")

        rice_25_sack = Product.objects.get(name="Rice 25kg Sack")
        rice_1kg = Product.objects.get(name="Rice 1kg")

        # Confirm stock level units for sugar
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=sugar_sack).units, 20.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=sugar_sack).units, 30.00)

        self.assertEqual(StockLevel.objects.get(store=self.store1, product=sugar_1kg).units, 45.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=sugar_1kg).units, 70.00)

        # Confirm stock level units for rice
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=rice_25_sack).units, 25.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=rice_25_sack).units, 31.00)

        self.assertEqual(StockLevel.objects.get(store=self.store1, product=rice_1kg).units, 21.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=rice_1kg).units, 37.00)

        self. create_transfer_order_products_to_be_transformed(user=self.user1)


        transfer_lines = TransferOrderLine.objects.all().order_by('id')

        
        to = TransferOrder.objects.get()

        to.status = TransferOrder.TRANSFER_ORDER_RECEIVED
        to.save()


        product_transform = ProductTransform.objects.get()

        # Check if product transform is created and marked as auto repackaged
        self.assertEqual(product_transform.is_auto_repackaged, True)
        self.assertEqual(product_transform.auto_repackaged_source_desc, to.__str__())
        self.assertEqual(product_transform.auto_repackaged_source_reg_no, to.reg_no)

        product_transform_lines = ProductTransformLine.objects.all().order_by('id')

        # Confirm stock level units for sugar
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=sugar_sack).units, 10.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=sugar_sack).units, 30.00)

        self.assertEqual(StockLevel.objects.get(store=self.store1, product=sugar_1kg).units, 45.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=sugar_1kg).units, 570.00)

        # Confirm stock level units for rice
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=rice_25_sack).units, 11.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=rice_25_sack).units, 31.00)

        self.assertEqual(StockLevel.objects.get(store=self.store1, product=rice_1kg).units, 21.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=rice_1kg).units, 387.00)

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.all().order_by('id')
        self.assertEqual(historys.count(), 8)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user1)
        self.assertEqual(historys[0].product, sugar_sack)
        self.assertEqual(historys[0].store, self.store1)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_TRANSFER)
        self.assertEqual(historys[0].change_source_reg_no, to.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Transfer')
        self.assertEqual(historys[0].change_source_name, self.transfer_order.__str__())
        self.assertEqual(historys[0].line_source_reg_no, int(f'{transfer_lines[0].reg_no}0'))
        self.assertEqual(historys[0].adjustment, Decimal('-10.00'))
        self.assertEqual(historys[0].stock_after, Decimal('10.00'))

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user1)
        self.assertEqual(historys[1].product, sugar_sack)
        self.assertEqual(historys[1].store, self.store2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_TRANSFER)
        self.assertEqual(historys[1].change_source_reg_no, to.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Transfer')
        self.assertEqual(historys[1].change_source_name, self.transfer_order.__str__())
        self.assertEqual(historys[1].line_source_reg_no, int(f'{transfer_lines[0].reg_no}1'))
        self.assertEqual(historys[1].adjustment, Decimal('10.00'))
        self.assertEqual(historys[1].stock_after, Decimal('40.00'))

        # Inventory history 3
        self.assertEqual(historys[2].user, self.user1)
        self.assertEqual(historys[2].product, rice_25_sack)
        self.assertEqual(historys[2].store, self.store1)
        self.assertEqual(historys[2].reason, InventoryHistory.INVENTORY_HISTORY_TRANSFER)
        self.assertEqual(historys[2].change_source_reg_no, to.reg_no)
        self.assertEqual(historys[2].change_source_desc, 'Transfer')
        self.assertEqual(historys[2].change_source_name, self.transfer_order.__str__())
        self.assertEqual(historys[2].line_source_reg_no, int(f'{transfer_lines[1].reg_no}0'))
        self.assertEqual(historys[2].adjustment, Decimal('-14.00'))
        self.assertEqual(historys[2].stock_after, Decimal('11.00'))

        # Inventory history 4
        self.assertEqual(historys[3].user, self.user1)
        self.assertEqual(historys[3].product, rice_25_sack)
        self.assertEqual(historys[3].store, self.store2)
        self.assertEqual(historys[3].reason, InventoryHistory.INVENTORY_HISTORY_TRANSFER)
        self.assertEqual(historys[3].change_source_reg_no, to.reg_no)
        self.assertEqual(historys[3].change_source_desc, 'Transfer')
        self.assertEqual(historys[3].change_source_name, self.transfer_order.__str__())
        self.assertEqual(historys[3].line_source_reg_no, int(f'{transfer_lines[1].reg_no}1'))
        self.assertEqual(historys[3].adjustment, Decimal('14.00'))
        self.assertEqual(historys[3].stock_after, Decimal('45.00'))

        # Inventory history 5
        self.assertEqual(historys[4].user, self.user1)
        self.assertEqual(historys[4].product, sugar_sack)
        self.assertEqual(historys[4].store, self.store2)
        self.assertEqual(historys[4].reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(historys[4].change_source_reg_no, product_transform.reg_no)
        self.assertEqual(historys[4].change_source_desc, 'Repackage')
        self.assertEqual(historys[4].change_source_name, product_transform.__str__())
        self.assertEqual(historys[4].line_source_reg_no, int(f'{product_transform_lines[0].reg_no}0'))
        self.assertEqual(historys[4].adjustment, Decimal('-10.00'))
        self.assertEqual(historys[4].stock_after, Decimal('30.00'))

        # Inventory history 6
        self.assertEqual(historys[5].user, self.user1)
        self.assertEqual(historys[5].product, sugar_1kg)
        self.assertEqual(historys[5].store, self.store2)
        self.assertEqual(historys[5].reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(historys[5].change_source_reg_no, product_transform.reg_no)
        self.assertEqual(historys[5].change_source_desc, 'Repackage')
        self.assertEqual(historys[5].change_source_name, product_transform.__str__())
        self.assertEqual(historys[5].line_source_reg_no, int(f'{product_transform_lines[0].reg_no}1'))
        self.assertEqual(historys[5].adjustment, Decimal('500.00'))
        self.assertEqual(historys[5].stock_after, Decimal('570.00'))

        # Inventory history 7
        self.assertEqual(historys[6].user, self.user1)
        self.assertEqual(historys[6].product, rice_25_sack)
        self.assertEqual(historys[6].store, self.store2)
        self.assertEqual(historys[6].reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(historys[6].change_source_reg_no, product_transform.reg_no)
        self.assertEqual(historys[6].change_source_desc, 'Repackage')
        self.assertEqual(historys[6].change_source_name, product_transform.__str__())
        self.assertEqual(historys[6].line_source_reg_no, int(f'{product_transform_lines[1].reg_no}0'))
        self.assertEqual(historys[6].adjustment, Decimal('-14.00'))
        self.assertEqual(historys[6].stock_after, Decimal('31.00'))

        # Inventory history 8
        self.assertEqual(historys[7].user, self.user1)
        self.assertEqual(historys[7].product, rice_1kg)
        self.assertEqual(historys[7].store, self.store2)
        self.assertEqual(historys[7].reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(historys[7].change_source_reg_no, product_transform.reg_no)
        self.assertEqual(historys[7].change_source_desc, 'Repackage')
        self.assertEqual(historys[7].change_source_name, product_transform.__str__())
        self.assertEqual(historys[7].line_source_reg_no, int(f'{product_transform_lines[1].reg_no}1'))
        self.assertEqual(historys[7].adjustment, Decimal('350.00'))
        self.assertEqual(historys[7].stock_after, Decimal('387.00'))
    
    def test_if_repackaging_wont_be_done_if_there_are_no_maps_set_as_auto_repackage(self):

        # Change store types
        Store.objects.filter(pk=self.store1.pk).update(is_truck=True)
        Store.objects.filter(pk=self.store2.pk).update(is_shop=True)

        self.create_product_maps_for_sugar()
        self.create_product_maps_for_rice()

        # Mark all product production maps as False
        ProductProductionMap.objects.all().update(is_auto_repackage=False)

        # First delete all the models
        TransferOrder.objects.all().delete()
        TransferOrderLine.objects.all().delete()

        self. create_transfer_order_products_to_be_transformed(user=self.user1)

        to = TransferOrder.objects.get()

        to.status = TransferOrder.TRANSFER_ORDER_RECEIVED
        to.save()

        self.assertEqual(TransferOrder.objects.all().count(), 1)
        self.assertEqual(TransferOrderLine.objects.all().count(), 2)
        
        self.assertEqual(ProductTransform.objects.all().count(), 0)
        self.assertEqual(ProductTransformLine.objects.all().count(), 0)

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.all().order_by('id')
        self.assertEqual(historys.count(), 4)

    def test_if_repackaging_wont_be_done_for_one_product_if_the_map_set_as_auto_repackage(self):

        # Change store types
        Store.objects.filter(pk=self.store1.pk).update(is_truck=True)
        Store.objects.filter(pk=self.store2.pk).update(is_shop=True)

        self.create_product_maps_for_sugar()
        self.create_product_maps_for_rice()

        # Mark all product production maps as False
        ProductProductionMap.objects.filter(
            product_map__name="Sugar 1kg"
        ).update(is_auto_repackage=False)

        # First delete all the models
        TransferOrder.objects.all().delete()
        TransferOrderLine.objects.all().delete()

        self. create_transfer_order_products_to_be_transformed(user=self.user1)

        to = TransferOrder.objects.get()

        to.status = TransferOrder.TRANSFER_ORDER_RECEIVED
        to.save()

        self.assertEqual(TransferOrder.objects.all().count(), 1)
        self.assertEqual(TransferOrderLine.objects.all().count(), 2)
        
        self.assertEqual(ProductTransform.objects.all().count(), 1)
        self.assertEqual(ProductTransformLine.objects.all().count(), 1)

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.all().order_by('id')
        self.assertEqual(historys.count(), 6)

    def test_if_product_will_get_created_if_source_store_is_truck_and_destination_is_shop(self):

        # Change store types
        Store.objects.filter(pk=self.store1.pk).update(is_truck=True)
        Store.objects.filter(pk=self.store2.pk).update(is_shop=True)

        self.create_product_maps_for_sugar()
        self.create_product_maps_for_rice()

        # First delete all the models
        TransferOrder.objects.all().delete()
        TransferOrderLine.objects.all().delete()

        self. create_transfer_order_products_to_be_transformed(user=self.user1)

        to = TransferOrder.objects.get()

        to.status = TransferOrder.TRANSFER_ORDER_RECEIVED
        to.save()

        self.assertEqual(TransferOrder.objects.all().count(), 1)
        self.assertEqual(TransferOrderLine.objects.all().count(), 2)
        
        self.assertEqual(ProductTransform.objects.all().count(), 1)
        self.assertEqual(ProductTransformLine.objects.all().count(), 2)

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.all().order_by('id')
        self.assertEqual(historys.count(), 8)

    def test_if_product_wont_get_created_if_source_store_is_not_truck(self):

        # Change store types
        Store.objects.filter(pk=self.store1.pk).update(is_truck=False)
        Store.objects.filter(pk=self.store2.pk).update(is_shop=True)

        self.create_product_maps_for_sugar()
        self.create_product_maps_for_rice()

        # First delete all the models
        TransferOrder.objects.all().delete()
        TransferOrderLine.objects.all().delete()

        self. create_transfer_order_products_to_be_transformed(user=self.user1)

        to = TransferOrder.objects.get()

        to.status = TransferOrder.TRANSFER_ORDER_RECEIVED
        to.save()

        self.assertEqual(TransferOrder.objects.all().count(), 1)
        self.assertEqual(TransferOrderLine.objects.all().count(), 2)
        
        self.assertEqual(ProductTransform.objects.all().count(), 0)
        self.assertEqual(ProductTransformLine.objects.all().count(), 0)

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.all().order_by('id')
        self.assertEqual(historys.count(), 4)

    def test_if_product_wont_get_created_if_destination_store_is_not_shop(self):

        # Change store types
        Store.objects.filter(pk=self.store1.pk).update(is_truck=True)
        Store.objects.filter(pk=self.store2.pk).update(is_shop=False)

        self.create_product_maps_for_sugar()
        self.create_product_maps_for_rice()

        # First delete all the models
        TransferOrder.objects.all().delete()
        TransferOrderLine.objects.all().delete()

        self. create_transfer_order_products_to_be_transformed(user=self.user1)

        to = TransferOrder.objects.get()

        to.status = TransferOrder.TRANSFER_ORDER_RECEIVED
        to.save()

        self.assertEqual(TransferOrder.objects.all().count(), 1)
        self.assertEqual(TransferOrderLine.objects.all().count(), 2)
        
        self.assertEqual(ProductTransform.objects.all().count(), 0)
        self.assertEqual(ProductTransformLine.objects.all().count(), 0)

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.all().order_by('id')
        self.assertEqual(historys.count(), 4)

    def test_if_transfer_received_true_will_also_create_product_transform3(self):

        self.create_product_maps_for_sugar()
        self.create_product_maps_for_rice()

        # First delete all the models
        TransferOrder.objects.all().delete()
        TransferOrderLine.objects.all().delete()

        self. create_transfer_order_products_to_be_transformed(user=self.user1)

        to = TransferOrder.objects.get()

        to.status = TransferOrder.TRANSFER_ORDER_RECEIVED
        to.save()

        self.assertEqual(TransferOrder.objects.all().count(), 1)
        self.assertEqual(TransferOrderLine.objects.all().count(), 2)
        
        self.assertEqual(ProductTransform.objects.all().count(), 1)
        self.assertEqual(ProductTransformLine.objects.all().count(), 2)

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.all().order_by('id')
        self.assertEqual(historys.count(), 8)

    def test_if_transfer_order_line_creation_wont_error_out_when_product_has_no_stock_level_model(self):

        # First delete all the models
        TransferOrder.objects.all().delete()
        TransferOrderLine.objects.all().delete()
        
        StockLevel.objects.all().delete()
        self.assertEqual(StockLevel.objects.all().count(), 0)

        self.create_transfer_order(user=self.user1)

        to = TransferOrder.objects.get()

        to.status = TransferOrder.TRANSFER_ORDER_RECEIVED
        to.save()

        self.assertEqual(StockLevel.objects.all().count(), 0)

    def test_if_transfer_order_line_creation_wont_change_levels_when_source_store_levels_are_not_there(self):

        # First delete all the models
        TransferOrder.objects.all().delete()
        TransferOrderLine.objects.all().delete()
        
        StockLevel.objects.filter(store=self.store1).delete()

        self.create_transfer_order(user=self.user1)

        to = TransferOrder.objects.get()

        to.status = TransferOrder.TRANSFER_ORDER_RECEIVED
        to.save()

        # Confirm destination stock level units were not edited
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 0.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 0.00)

    def test_if_transfer_order_line_creation_wont_change_levels_when_destination_store_levels_are_not_there(self):

        # First delete all the models
        TransferOrder.objects.all().delete()
        TransferOrderLine.objects.all().delete()
        
        StockLevel.objects.filter(store=self.store2).delete()

        self.create_transfer_order(user=self.user1)

        to = TransferOrder.objects.get()

        to.status = TransferOrder.TRANSFER_ORDER_RECEIVED
        to.save()

        # Confirm source stock level units were not edited
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 100.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 155.00)
    
    def test_if_increamental_id_increaments_only_for_one_profile(self):
        """
        We test if the increamental id increases only top user profiles. If an
        an employee user is the one creating, then it increases for his/her
        top user
        """

        profile2 = Profile.objects.get(user__email='jack@gmail.com')

        employee_for_user1 = create_new_cashier_user("kate", self.profile, self.store1)
        employee_for_user2 = create_new_cashier_user("ben", profile2, self.store1)

        # ********************** Create transfers for the first time
        # Delete all transfers first
        TransferOrder.objects.all().delete()

        ##### Create 2 transfer for user 1
        self.create_transfer_order(user=self.user1, reg_no=111)
        self.create_transfer_order(user=employee_for_user1, reg_no=222)

        # Transfer 1
        transfer1 = TransferOrder.objects.get(reg_no=111)
        transfer_count1 = TransferOrderCount.objects.get(reg_no=transfer1.reg_no)

        self.assertEqual(transfer1.increamental_id, 1001)
        self.assertEqual(transfer1.__str__(), f'TO{transfer1.increamental_id}')
        self.assertEqual(transfer_count1.increamental_id, 1001) 

        # Transfer 2
        transfer2 = TransferOrder.objects.get(reg_no=222)
        transfer_count2 = TransferOrderCount.objects.get(reg_no=transfer2.reg_no)

        self.assertEqual(transfer2.increamental_id, 1002)
        self.assertEqual(transfer2.__str__(), f'TO{transfer2.increamental_id}')
        self.assertEqual(transfer_count2.increamental_id, 1002) 

        ##### Create 2 transfers for user 2
        self.create_transfer_order(user=self.user2, reg_no=333)
        self.create_transfer_order(user=employee_for_user2, reg_no=444)

        # Transfer 3
        transfer3 = TransferOrder.objects.get(reg_no=333)
        transfer_count3 = TransferOrderCount.objects.get(reg_no=transfer3.reg_no)

        self.assertEqual(transfer3.increamental_id, 1000)
        self.assertEqual(transfer3.__str__(), f'TO{transfer3.increamental_id}')
        self.assertEqual(transfer_count3.increamental_id, 1000) 

        # Transfer 4
        transfer4 = TransferOrder.objects.get(reg_no=444)
        transfer_count4 = TransferOrderCount.objects.get(reg_no=transfer4.reg_no)

        self.assertEqual(transfer4.increamental_id, 1001)
        self.assertEqual(transfer4.__str__(), f'TO{transfer4.increamental_id}')
        self.assertEqual(transfer_count4.increamental_id, 1001) 


        # ********************** Create transfers for the second time
        # Delete all transfers first
        TransferOrder.objects.all().delete()

        ##### Create 2 transfers for user 1
        self.create_transfer_order(user=self.user1, reg_no=555)
        self.create_transfer_order(user=employee_for_user1, reg_no=666)

        # Store 1
        transfer1 = TransferOrder.objects.get(reg_no=555)
        transfer_count1 = TransferOrderCount.objects.get(reg_no=transfer1.reg_no)

        self.assertEqual(transfer1.increamental_id, 1003)
        self.assertEqual(transfer1.__str__(), f'TO{transfer1.increamental_id}')
        self.assertEqual(transfer_count1.increamental_id, 1003) 

        # Store 2
        transfer2 = TransferOrder.objects.get(reg_no=666)
        transfer_count2 = TransferOrderCount.objects.get(reg_no=transfer2.reg_no)

        self.assertEqual(transfer2.increamental_id, 1004)
        self.assertEqual(transfer2.__str__(), f'TO{transfer2.increamental_id}')
        self.assertEqual(transfer_count2.increamental_id, 1004) 

        ##### Create 2 transfers for user 2
        self.create_transfer_order(user=self.user2, reg_no=777)
        self.create_transfer_order(user=employee_for_user2, reg_no=888)

        # Transfer 3
        transfer3 = TransferOrder.objects.get(reg_no=777)
        transfer_count3 = TransferOrderCount.objects.get(reg_no=transfer3.reg_no)

        self.assertEqual(transfer3.increamental_id, 1002)
        self.assertEqual(transfer3.__str__(), f'TO{transfer3.increamental_id}')
        self.assertEqual(transfer_count3.increamental_id, 1002) 

        # Transfer 4
        transfer4 = TransferOrder.objects.get(reg_no=888)
        transfer_count4 = TransferOrderCount.objects.get(reg_no=transfer4.reg_no)

        self.assertEqual(transfer4.increamental_id, 1003)
        self.assertEqual(transfer4.__str__(), f'TO{transfer4.increamental_id}')
        self.assertEqual(transfer_count4.increamental_id, 1003) 

"""
=========================== TransferOrderLine ===================================
"""
class TransferOrderLineTestCase(TestCase, TransferOrderModelsMixin):
    
    def setUp(self):
        
        #Create a user1
        self.user1 = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create 2 stores
        self.store1 = create_new_store(self.profile, 'Computer Store1')
        self.store2 = create_new_store(self.profile, 'Computer Store2')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store1, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Creates products
        self.product1 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )
        self.product1.stores.add(self.store1, self.store2)

        self.product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )
        self.product2.stores.add(self.store1, self.store2)

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 100
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 155
        stock_level.save()

    def test_transfer_order_line_fields_verbose_names(self):

        self.create_transfer_order(user=self.user1)

        tol = TransferOrderLine.objects.get(product=self.product1)

        self.assertEqual(tol._meta.get_field('product_info').verbose_name,'product info')
        self.assertEqual(tol._meta.get_field('quantity').verbose_name,'quantity')
        self.assertEqual(tol._meta.get_field('reg_no').verbose_name,'reg no')

        fields = ([field.name for field in TransferOrderLine._meta.fields])
        
        self.assertEqual(len(fields), 7)

    def test_transfer_order_line_fields_after_it_has_been_created(self):

        self.create_transfer_order(user=self.user1)

        tol = TransferOrderLine.objects.get(product=self.product1)
        
        self.assertEqual(tol.transfer_order, self.transfer_order)
        self.assertEqual(tol.product, self.product1)
        self.assertEqual(
            tol.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(tol.quantity, 10.00)

    def test__str__method(self):

        self.create_transfer_order(user=self.user1)

        tol = TransferOrderLine.objects.get(product=self.product1)
        self.assertEqual(str(tol), tol.product.name)

"""
=========================== InventoryCount ===================================
"""
class InventoryCountTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user1 = create_new_user('john')
        self.user2 = create_new_user('jack')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store = create_new_store(self.profile, 'Computer Store')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Creates products
        self.product1 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )
        self.product1.stores.add(self.store)

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

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(product=self.product1)
        stock_level.units = 200
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(product=self.product2)
        stock_level.units = 157
        stock_level.save()

        self.create_inventory_count(self.user1)

    def create_inventory_count(self, user, reg_no=0):

        # Create inventory count
        self.inventory_count = InventoryCount.objects.create(
            user=user,
            store=self.store,
            notes='This is just a simple note',
            mismatch_found=True,
            reg_no=reg_no
        )

        # Create inventory count1
        self.inventory_count_line1 =  InventoryCountLine.objects.create(
            inventory_count=self.inventory_count,
            product=self.product1,
            expected_stock=100,
            counted_stock=77,
        )
    
        # Create inventory count2
        self.inventory_count_line2 =  InventoryCountLine.objects.create(
            inventory_count=self.inventory_count,
            product=self.product2,
            expected_stock=155,
            counted_stock=160,
        )
    
    def test_inventory_count_fields_verbose_names(self):

        ic = InventoryCount.objects.get(store=self.store)

        self.assertEqual(ic._meta.get_field('notes').verbose_name,'notes')
        self.assertEqual(ic._meta.get_field('mismatch_found').verbose_name,'mismatch found')
        self.assertEqual(ic._meta.get_field('status').verbose_name,'status')
        self.assertEqual(ic._meta.get_field('increamental_id').verbose_name,'increamental id')
        self.assertEqual(ic._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(ic._meta.get_field('created_date').verbose_name,'created date')
        self.assertEqual(ic._meta.get_field('completed_date').verbose_name,'completed date')

        fields = ([field.name for field in InventoryCount._meta.fields])
        
        self.assertEqual(len(fields), 10)
   
    def test_inventory_count_fields_after_it_has_been_created(self):

        ic = InventoryCount.objects.get(store=self.store)
        
        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(ic.user, self.user1)
        self.assertEqual(ic.store, self.store)
        self.assertEqual(ic.notes, 'This is just a simple note')
        self.assertEqual(ic.mismatch_found, True)
        self.assertTrue(ic.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((ic.created_date).strftime("%B, %d, %Y"), today)

    def test__str__method(self):

        ic = InventoryCount.objects.get(store=self.store)
        self.assertEqual(str(ic), f'IC{ic.increamental_id}')

    def test_get_counted_by_method(self):

        ic = InventoryCount.objects.get(store=self.store)
        self.assertEqual(ic.get_counted_by(), self.user1.get_full_name())

    def test_get_store_name_method(self):

        ic = InventoryCount.objects.get(store=self.store)
        self.assertEqual(ic.get_store_name(), self.store.name)

    def test_get_store_data_method(self):

        ic = InventoryCount.objects.get(store=self.store)
        self.assertEqual(
            ic.get_store_data(), 
            {"name": self.store.name, "reg_no": self.store.reg_no}
        )

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 

        ic = InventoryCount.objects.get(store=self.store)
             
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            ic.get_created_date(self.user1.get_user_timezone()))
        )
    
    def test_get_line_data_method_when_status_is_not_completed(self):
        """
        Confirm if model is not completed, expected stock is retrieved from the
        stock levels and differences are calculated seperately
        """
        ic = InventoryCount.objects.get(store=self.store)

        lines = ic.inventorycountline_set.all().order_by('id')

        result = [
            {
                'product_info': {
                    'name': self.product1.name, 
                    'sku': self.product1.sku,
                    'reg_no': self.product1.reg_no,
                }, 
                'expected_stock': '200.00',
                'counted_stock': '77.00',
                'difference': '-123.00', 
                'cost_difference': '-123000.00',
                'product_cost': '1000.00',
                'reg_no':str(lines[0].reg_no),
            },
            {
                'product_info': {
                    'name': self.product2.name, 
                    'sku': self.product2.sku,
                    'reg_no': self.product2.reg_no
                }, 
                'expected_stock': '157.00',
                'counted_stock': '160.00',
                'difference': '3.00', 
                'cost_difference': '3600.00',
                'product_cost': '1200.00',
                'reg_no':str(lines[1].reg_no),
                }
        ]

        self.assertEqual(ic.get_line_data(), result)

    def test_get_line_data_method_when_status_is_completed(self):
        """
        Confirm if model is completed, all data is retrieved from the 
        inventorycountline
        """
        ic = InventoryCount.objects.get(store=self.store)
        ic.status = InventoryCount.INVENTORY_COUNT_COMPLETED
        ic.save()

        ic = InventoryCount.objects.get(store=self.store)

        lines = ic.inventorycountline_set.all().order_by('id')

        result = [
            {
                'product_info': {
                    'name': self.product1.name, 
                    'sku': self.product1.sku,
                    'reg_no': self.product1.reg_no,
                }, 
                'expected_stock': '100.00',
                'counted_stock': '77.00',
                'difference': '-23.00', 
                'cost_difference': '-23000.00',
                'product_cost': '1000.00',
                'reg_no':str(lines[0].reg_no),
            },
            {
                'product_info': {
                    'name': self.product2.name, 
                    'sku': self.product2.sku,
                    'reg_no': self.product2.reg_no
                }, 
                'expected_stock': '155.00',
                'counted_stock': '160.00',
                'difference': '5.00', 
                'cost_difference': '6000.00',
                'product_cost': '1200.00',
                'reg_no':str(lines[1].reg_no),
                }
        ]

        self.assertEqual(ic.get_line_data(), result)

    def test_if_increamental_id_increaments_only_for_one_profile(self):
        """
        We test if the increamental id increases only top user profiles. If an
        an employee user is the one creating, then it increases for his/her
        top user
        """

        profile2 = Profile.objects.get(user__email='jack@gmail.com')

        employee_for_user1 = create_new_cashier_user("kate", self.profile, self.store)
        employee_for_user2 = create_new_cashier_user("ben", profile2, self.store)

        # ********************** Create inventory counts for the first time
        # Delete all counts first
        InventoryCount.objects.all().delete()

        ##### Create 2 counts for user 1
        self.create_inventory_count(user=self.user1, reg_no=111)
        self.create_inventory_count(user=employee_for_user1, reg_no=222)

        # Inventory count 1
        ic1 = InventoryCount.objects.get(reg_no=111)
        ic_count1 = InventoryCountCount.objects.get(reg_no=ic1.reg_no)

        self.assertEqual(ic1.increamental_id, 1001)
        self.assertEqual(ic1.__str__(), f'IC{ic1.increamental_id}')
        self.assertEqual(ic_count1.increamental_id, 1001) 

        # Inventory count 2
        ic2 = InventoryCount.objects.get(reg_no=222)
        ic_count2 = InventoryCountCount.objects.get(reg_no=ic2.reg_no)

        self.assertEqual(ic2.increamental_id, 1002)
        self.assertEqual(ic2.__str__(), f'IC{ic2.increamental_id}')
        self.assertEqual(ic_count2.increamental_id, 1002) 

        ##### Create 2 transfers for user 2
        self.create_inventory_count(user=self.user2, reg_no=333)
        self.create_inventory_count(user=employee_for_user2, reg_no=444)

        # Inventory count 3
        ic3 = InventoryCount.objects.get(reg_no=333)
        ic_count3 = InventoryCountCount.objects.get(reg_no=ic3.reg_no)

        self.assertEqual(ic3.increamental_id, 1000)
        self.assertEqual(ic3.__str__(), f'IC{ic3.increamental_id}')
        self.assertEqual(ic_count3.increamental_id, 1000) 

        # Inventory count 4
        ic4 = InventoryCount.objects.get(reg_no=444)
        ic_count4 = InventoryCountCount.objects.get(reg_no=ic4.reg_no)

        self.assertEqual(ic4.increamental_id, 1001)
        self.assertEqual(ic4.__str__(), f'IC{ic4.increamental_id}')
        self.assertEqual(ic_count4.increamental_id, 1001) 


        # ********************** Create inventory counts for the second time
        # Delete all counts first
        InventoryCount.objects.all().delete()

        ##### Create 2 counts for user 1
        self.create_inventory_count(user=self.user1, reg_no=555)
        self.create_inventory_count(user=employee_for_user1, reg_no=666)

        # Inventory count 1
        ic1 = InventoryCount.objects.get(reg_no=555)
        ic_count1 = InventoryCountCount.objects.get(reg_no=ic1.reg_no)

        self.assertEqual(ic1.increamental_id, 1003)
        self.assertEqual(ic1.__str__(), f'IC{ic1.increamental_id}')
        self.assertEqual(ic_count1.increamental_id, 1003) 

        # Inventory count 2
        ic2 = InventoryCount.objects.get(reg_no=666)
        ic_count2 = InventoryCountCount.objects.get(reg_no=ic2.reg_no)

        self.assertEqual(ic2.increamental_id, 1004)
        self.assertEqual(ic2.__str__(), f'IC{ic2.increamental_id}')
        self.assertEqual(ic_count2.increamental_id, 1004) 

        ##### Create 2 counts for user 2
        self.create_inventory_count(user=self.user2, reg_no=777)
        self.create_inventory_count(user=employee_for_user2, reg_no=888)

        # Inventory count 3
        ic3 = InventoryCount.objects.get(reg_no=777)
        ic_count3 = InventoryCountCount.objects.get(reg_no=ic3.reg_no)

        self.assertEqual(ic3.increamental_id, 1002)
        self.assertEqual(ic3.__str__(), f'IC{ic3.increamental_id}')
        self.assertEqual(ic_count3.increamental_id, 1002) 

        # Inventory count 4
        ic4 = InventoryCount.objects.get(reg_no=888)
        ic_count4 = InventoryCountCount.objects.get(reg_no=ic4.reg_no)

        self.assertEqual(ic4.increamental_id, 1003)
        self.assertEqual(ic4.__str__(), f'IC{ic4.increamental_id}')
        self.assertEqual(ic_count4.increamental_id, 1003)


"""
=========================== InventoryCountLine ===================================
"""
class InventoryCountLineTestCase(TestCase):
    
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

        # Creates products
        self.product1 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )
        self.product1.stores.add(self.store)

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

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(product=self.product1)
        stock_level.units = 100
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(product=self.product2)
        stock_level.units = 155
        stock_level.save()

    def create_inventory_count(self):

        # Create inventory count
        self.inventory_count = InventoryCount.objects.create(
            user=self.user,
            store=self.store,
            notes='This is just a simple note',
            mismatch_found=True,
        )

        # Create inventory count1
        self.inventory_count_line1 =  InventoryCountLine.objects.create(
            inventory_count=self.inventory_count,
            product=self.product1,
            expected_stock=100,
            counted_stock=77,
        )
    
        # Create inventory count2
        self.inventory_count_line2 =  InventoryCountLine.objects.create(
            inventory_count=self.inventory_count,
            product=self.product2,
            expected_stock=155,
            counted_stock=160,
        )

    def test_inventory_count_line_fields_verbose_names(self):

        self.create_inventory_count()

        icl = InventoryCountLine.objects.get(product=self.product1)

        self.assertEqual(icl._meta.get_field('product_info').verbose_name,'product info')
        self.assertEqual(icl._meta.get_field('expected_stock').verbose_name,'expected stock')
        self.assertEqual(icl._meta.get_field('counted_stock').verbose_name,'counted stock')
        self.assertEqual(icl._meta.get_field('difference').verbose_name,'difference')
        self.assertEqual(icl._meta.get_field('cost_difference').verbose_name,'cost difference')
        self.assertEqual(icl._meta.get_field('product_cost').verbose_name,'product cost')
        self.assertEqual(icl._meta.get_field('reg_no').verbose_name,'reg no')

        fields = ([field.name for field in InventoryCountLine._meta.fields])
        
        self.assertEqual(len(fields), 10)
    
    def test_inventory_count_line_fields_after_it_has_been_created(self):

        self.create_inventory_count()

        icl = InventoryCountLine.objects.get(product=self.product1)
        
        self.assertEqual(icl.inventory_count, self.inventory_count)
        self.assertEqual(icl.product, self.product1)
        self.assertEqual(
            icl.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no
            }
        )
        self.assertEqual(icl.expected_stock, 100.00)
        self.assertEqual(icl.counted_stock, 77.00)
        self.assertEqual(icl.difference, -23.00)
        self.assertEqual(icl.cost_difference, -23000.00)
        self.assertEqual(icl.product_cost, 1000.00)
        self.assertTrue(icl.reg_no > 100000) # Check if we have a valid reg_no

    def test__str__method(self):

        self.create_inventory_count()

        icl = InventoryCountLine.objects.get(product=self.product1)
        self.assertEqual(str(icl), icl.product.name)

    def test_if_difference_and_cost_difference_are_update_correctly(self):

        self.create_inventory_count()

        line1 = InventoryCountLine.objects.get(product=self.product1)
        self.assertEqual(line1.difference, -23.00)
        self.assertEqual(line1.cost_difference, -23000.00)

        line2 = InventoryCountLine.objects.get(product=self.product2)
        self.assertEqual(line2.difference, 5.00)
        self.assertEqual(line2.cost_difference, 6000.00)

"""
=========================== PurchaseOrder ===================================
"""

class PurchaseOrderModelsMixin:

    def create_purchase_order(self, user, reg_no=0, created_timestamp=0):

        #today_timestamp = 1634840312
        #next_day_timestamp = 1634926712
        #previous_day_timestamp = 1634753912

        # Create purchase order1
        self.purchase_order = PurchaseOrder.objects.create(
            user=user,
            supplier=self.supplier,
            store=self.store1,
            notes='This is just a simple note',
            status=PurchaseOrder.PURCHASE_ORDER_PENDING,
            total_amount=1300,
            created_date_timestamp=created_timestamp,
            reg_no=reg_no
        )

        # Create purchase order line 1
        self.purchase_order_line1 =  PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order,
            product=self.product1,
            quantity=350,
            purchase_cost=190,
        )
    
        # Create purchase order line 2
        self.purchase_order_line2 =  PurchaseOrderLine.objects.create(
            purchase_order=self.purchase_order,
            product=self.product2,
            quantity=14,
            purchase_cost=1300
        )


        # Create purchase order additional cost 1
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order,
            name='Transport',
            amount=200
        )
    
        # Create purchase order additional cost 2
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=self.purchase_order,
            name='Labour',
            amount=300
        )


class PurchaseOrderTestCase(TestCase, PurchaseOrderModelsMixin):
    
    def setUp(self):
        
        #Create a user1
        self.user1 = create_new_user('john')
        self.user2 = create_new_user('jack')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store2 = create_new_store(self.profile, 'Toy Store')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store1, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a supplier user
        self.supplier = create_new_supplier(self.profile, 'jeremy')

        # Creates products
        self.product1 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=500,
            cost=200,
            barcode='code123'
        )
        self.product1.stores.add(self.store1)

        self.product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=200,
            barcode='code123'
        )
        self.product2.stores.add(self.store1)

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 300
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product1)
        stock_level.units = 0
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 155
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product2)
        stock_level.units = 0
        stock_level.save()

        self.create_purchase_order(self.user1)

    def test_purchase_order_fields_verbose_names(self):

        po = PurchaseOrder.objects.get(store=self.store1)

        self.assertEqual(po._meta.get_field('notes').verbose_name,'notes')
        self.assertEqual(po._meta.get_field('status').verbose_name,'status')
        self.assertEqual(po._meta.get_field('total_amount').verbose_name,'total amount')
        self.assertEqual(po._meta.get_field('order_completed').verbose_name,'order completed')
        self.assertEqual(po._meta.get_field('increamental_id').verbose_name,'increamental id')
        self.assertEqual(po._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(po._meta.get_field('created_date').verbose_name,'created date')
        self.assertEqual(po._meta.get_field('expected_date').verbose_name,'expected date')
        self.assertEqual(po._meta.get_field('expected_date_timestamp').verbose_name,'expected date timestamp')
        self.assertEqual(po._meta.get_field('completed_date').verbose_name,'completed date')

        fields = ([field.name for field in PurchaseOrder._meta.fields])
        
        self.assertEqual(len(fields), 15)

    def test_purchase_order_fields_after_it_has_been_created(self):

        po = PurchaseOrder.objects.get(store=self.store1)
        
        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(po.user, self.user1)
        self.assertEqual(po.supplier, self.supplier)
        self.assertEqual(po.store, self.store1)
        self.assertEqual(po.notes, 'This is just a simple note')
        self.assertEqual(po.status, PurchaseOrder.PURCHASE_ORDER_PENDING)
        self.assertEqual(po.total_amount, 1300)
        self.assertEqual(po.order_completed, False)
        self.assertTrue(po.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((po.created_date).strftime("%B, %d, %Y"), today)
        self.assertEqual((po.expected_date).strftime("%B, %d, %Y"), today)

    def test__str__method(self):

        po = PurchaseOrder.objects.get(store=self.store1)
        self.assertEqual(str(po), f'PO{po.increamental_id}')

    def test_get_ordered_by_method(self):

        po = PurchaseOrder.objects.get(store=self.store1)
        self.assertEqual(po.get_ordered_by(), self.user1.get_full_name())

    def test_get_supplier_name_method(self):

        po = PurchaseOrder.objects.get(store=self.store1)
        self.assertEqual(po.get_supplier_name(), self.supplier.name)

    def test_get_store_name_method(self):

        po = PurchaseOrder.objects.get(store=self.store1)
        self.assertEqual(po.get_store_name(), self.store1.name)

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 

        po = PurchaseOrder.objects.get(store=self.store1)
             
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            po.get_created_date(self.user1.get_user_timezone()))
        )

    def test_get_expected_date_method(self):
        # Confirm that get_expected_date_method returns created_date
        # in local time 

        po = PurchaseOrder.objects.get(store=self.store1)
             
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            po.get_expected_date(self.user1.get_user_timezone()))
        )

    def test_get_line_data_method(self):
        
        po = PurchaseOrder.objects.get(store=self.store1)

        lines = po.purchaseorderline_set.all().order_by('id')

        result = [
            {
                'product_info': {
                    'name': self.product1.name, 
                    'sku': self.product1.sku,
                    'reg_no': self.product1.reg_no,
                    'tax_rate': str(self.product1.tax_rate)
                }, 
                'quantity': str(lines[0].quantity), 
                'purchase_cost': str(lines[0].purchase_cost),
                'amount': str(lines[0].amount),
                'reg_no': str(lines[0].reg_no)
            },
            {
                'product_info': {
                    'name': self.product2.name, 
                    'sku': self.product2.sku,
                    'reg_no': self.product2.reg_no,
                    'tax_rate': str(self.product2.tax_rate)
                    
                }, 
                'quantity': str(lines[1].quantity), 
                'purchase_cost': str(lines[1].purchase_cost),
                'amount': str(lines[1].amount),
                'reg_no': str(lines[1].reg_no)
            }
        ]

        self.assertEqual(po.get_line_data(), result)

    def test_if_purchase_received_fasle_wont_update_stock_level_units(self):

        # First delete all the models
        PurchaseOrder.objects.all().delete()
        PurchaseOrderLine.objects.all().delete()

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 300.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 155.00)

        self.create_purchase_order(self.user1)

        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 300.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 155.00)

    def test_if_po_received_true_with_0_purchase_cost_will_update_product_stock_level_units_and_price(self):

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 160
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product1)
        stock_level.units = 140
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 145
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product2)
        stock_level.units = 10
        stock_level.save()

        # First delete all the models
        PurchaseOrder.objects.all().delete()
        PurchaseOrderLine.objects.all().delete()

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 160.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 140.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 145.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 10.00)

        self.create_purchase_order(self.user1)
        # Update all purchase order line purchase cost to 0
        PurchaseOrderLine.objects.all().update(purchase_cost=0, amount=0)

        po = PurchaseOrder.objects.get()

        po.status = PurchaseOrder.PURCHASE_ORDER_RECEIVED
        po.save()

        # Check if stock was updated
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 510.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 140.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 159.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 10.00)

        # Check if cost was updated
        self.assertEqual(Product.objects.get(id=self.product1.id).cost, Decimal('92.31'))
        self.assertEqual(Product.objects.get(id=self.product2.id).cost, Decimal('183.43'))

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store1).order_by('id')
        self.assertEqual(historys.count(), 2)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user1)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].store, self.store1)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_PO_RECEIVE)
        self.assertEqual(historys[0].change_source_reg_no, po.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Receive')
        self.assertEqual(historys[0].change_source_name, self.purchase_order.__str__())
        self.assertEqual(historys[0].line_source_reg_no, self.purchase_order_line1.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('350.00'))
        self.assertEqual(historys[0].stock_after, Decimal('510.00'))

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user1)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].store, self.store1)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_PO_RECEIVE)
        self.assertEqual(historys[1].change_source_reg_no, po.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Receive')
        self.assertEqual(historys[1].change_source_name, self.purchase_order.__str__())
        self.assertEqual(historys[1].line_source_reg_no, self.purchase_order_line2.reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('14.00'))
        self.assertEqual(historys[1].stock_after, Decimal('159.00'))

    def test_if_po_received_true_will_update_product_stock_level_units_and_price_when_we_have_additional_costs(self):

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 160
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product1)
        stock_level.units = 140
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 145
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product2)
        stock_level.units = 10
        stock_level.save()

        # First delete all the models
        PurchaseOrder.objects.all().delete()
        PurchaseOrderLine.objects.all().delete()

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 160.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 140.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 145.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 10.00)

        self.create_purchase_order(self.user1)

        po = PurchaseOrder.objects.get()

        po.status = PurchaseOrder.PURCHASE_ORDER_RECEIVED
        po.save()

        # Check if stock was updated
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 510.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 140.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 159.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 10.00)

        # Check if cost was updated
        self.assertEqual(Product.objects.get(id=self.product1.id).cost, Decimal('195.22'))
        self.assertEqual(Product.objects.get(id=self.product2.id).cost, Decimal('291.76'))

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store1).order_by('id')
        self.assertEqual(historys.count(), 2)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user1)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].store, self.store1)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_PO_RECEIVE)
        self.assertEqual(historys[0].change_source_reg_no, po.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Receive')
        self.assertEqual(historys[0].change_source_name, self.purchase_order.__str__())
        self.assertEqual(historys[0].line_source_reg_no, self.purchase_order_line1.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('350.00'))
        self.assertEqual(historys[0].stock_after, Decimal('510.00'))

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user1)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].store, self.store1)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_PO_RECEIVE)
        self.assertEqual(historys[1].change_source_reg_no, po.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Receive')
        self.assertEqual(historys[1].change_source_name, self.purchase_order.__str__())
        self.assertEqual(historys[1].line_source_reg_no, self.purchase_order_line2.reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('14.00'))
        self.assertEqual(historys[1].stock_after, Decimal('159.00'))

    def test_if_po_received_true_will_update_product_stock_level_units_and_price_when_we_dont_have_additional_costs(self):

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 160
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product1)
        stock_level.units = 140
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 145
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product2)
        stock_level.units = 10
        stock_level.save()

        # First delete all the models
        PurchaseOrder.objects.all().delete()
        PurchaseOrderLine.objects.all().delete()

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 160.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 140.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 145.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 10.00)

        self.create_purchase_order(self.user1)

        # Delete all additional costs
        PurchaseOrderAdditionalCost.objects.all().delete()

        po = PurchaseOrder.objects.get()

        po.status = PurchaseOrder.PURCHASE_ORDER_RECEIVED
        po.save()

        # Check if stock was updated
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 510.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, 140.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 159.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 10.00)

        # Check if cost was updated
        self.assertEqual(Product.objects.get(id=self.product1.id).cost, Decimal('194.62'))
        self.assertEqual(Product.objects.get(id=self.product2.id).cost, Decimal('291.12'))

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store1).order_by('id')
        self.assertEqual(historys.count(), 2)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user1)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].store, self.store1)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_PO_RECEIVE)
        self.assertEqual(historys[0].change_source_reg_no, po.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Receive')
        self.assertEqual(historys[0].change_source_name, self.purchase_order.__str__())
        self.assertEqual(historys[0].line_source_reg_no, self.purchase_order_line1.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('350.00'))
        self.assertEqual(historys[0].stock_after, Decimal('510.00'))

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user1)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].store, self.store1)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_PO_RECEIVE)
        self.assertEqual(historys[1].change_source_reg_no, po.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Receive')
        self.assertEqual(historys[1].change_source_name, self.purchase_order.__str__())
        self.assertEqual(historys[1].line_source_reg_no, self.purchase_order_line2.reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('14.00'))
        self.assertEqual(historys[1].stock_after, Decimal('159.00'))

    def test_if_po_received_true_will_update_product_stock_level_units_and_price_when_units_is_negative(self):

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = -160
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product1)
        stock_level.units = -140
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 145
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product2)
        stock_level.units = 10
        stock_level.save()

        # First delete all the models
        PurchaseOrder.objects.all().delete()
        PurchaseOrderLine.objects.all().delete()

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, -160.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, -140.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 145.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 10.00)

        self.create_purchase_order(self.user1)

        # Delete all additional costs
        PurchaseOrderAdditionalCost.objects.all().delete()

        po = PurchaseOrder.objects.get()

        po.status = PurchaseOrder.PURCHASE_ORDER_RECEIVED
        po.save()

        # Check if stock was updated
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 190.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product1).units, -140.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 159.00)
        self.assertEqual(StockLevel.objects.get(store=self.store2, product=self.product2).units, 10.00)

        # Check if cost was updated
        self.assertEqual(Product.objects.get(id=self.product1.id).cost, Decimal('194.62'))
        self.assertEqual(Product.objects.get(id=self.product2.id).cost, Decimal('291.12'))

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store1).order_by('id')
        self.assertEqual(historys.count(), 2)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user1)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].store, self.store1)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_PO_RECEIVE)
        self.assertEqual(historys[0].change_source_reg_no, po.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Receive')
        self.assertEqual(historys[0].change_source_name, self.purchase_order.__str__())
        self.assertEqual(historys[0].line_source_reg_no, self.purchase_order_line1.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('350.00'))
        self.assertEqual(historys[0].stock_after, Decimal('190.00'))

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user1)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].store, self.store1)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_PO_RECEIVE)
        self.assertEqual(historys[1].change_source_reg_no, po.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Receive')
        self.assertEqual(historys[1].change_source_name, self.purchase_order.__str__())
        self.assertEqual(historys[1].line_source_reg_no, self.purchase_order_line2.reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('14.00'))
        self.assertEqual(historys[1].stock_after, Decimal('159.00'))

    def test_if_po_received_true_will_update_product_stock_level_units(self):

        today = (timezone.now()).strftime("%B, %d, %Y") 

        # First delete all the models
        PurchaseOrder.objects.all().delete()
        PurchaseOrderLine.objects.all().delete()

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 300.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 155.00)

        self.create_purchase_order(self.user1)

        po = PurchaseOrder.objects.get()

        po.status = PurchaseOrder.PURCHASE_ORDER_RECEIVED
        po.save()

        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 650.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 169.00)

        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store1).order_by('id')
        self.assertEqual(historys.count(), 2)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user1)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].store, self.store1)
        self.assertEqual(historys[0].product, self.product1)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_PO_RECEIVE)
        self.assertEqual(historys[0].change_source_reg_no, po.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Receive')
        self.assertEqual(historys[0].change_source_name, self.purchase_order.__str__())
        self.assertEqual(historys[0].line_source_reg_no, self.purchase_order_line1.reg_no)
        self.assertEqual(historys[0].adjustment, Decimal('350.00'))
        self.assertEqual(historys[0].stock_after, Decimal('650.00'))
        self.assertEqual((historys[0].created_date).strftime("%B, %d, %Y"), today)

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user1)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].store, self.store1)
        self.assertEqual(historys[1].product, self.product2)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_PO_RECEIVE)
        self.assertEqual(historys[1].change_source_reg_no, po.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Receive')
        self.assertEqual(historys[1].change_source_name, self.purchase_order.__str__())
        self.assertEqual(historys[1].line_source_reg_no, self.purchase_order_line2.reg_no)
        self.assertEqual(historys[1].adjustment, Decimal('14.00'))
        self.assertEqual(historys[1].stock_after, Decimal('169.00'))
        self.assertEqual((historys[1].created_date).strftime("%B, %d, %Y"), today)

    def test_if_po_will_update_inventory_history_with_po_creation_date(self):

        # First delete all the models
        PurchaseOrder.objects.all().delete()
        PurchaseOrderLine.objects.all().delete()

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product1).units, 300.00)
        self.assertEqual(StockLevel.objects.get(store=self.store1, product=self.product2).units, 155.00)

        self.create_purchase_order(self.user1)

        po = PurchaseOrder.objects.get()
        po.created_date_timestamp = 1634926712
        po.save()

        po = PurchaseOrder.objects.get()
        po.status = PurchaseOrder.PURCHASE_ORDER_RECEIVED
        po.save()


        ############ Test if Inventory History will be created
        historys = InventoryHistory.objects.filter(store=self.store1).order_by('id')
        self.assertEqual(historys.count(), 2)

        # Inventory history 1
        self.assertEqual(
            (historys[0].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

        # Inventory history 2
        self.assertEqual(
            (historys[1].created_date).strftime("%B, %d, %Y"),
            'October, 22, 2021'
        )

    def test_if_purchase_order_line_creation_wont_error_out_when_product_has_no_stock_level_model(self):

        # First delete all the models
        PurchaseOrder.objects.all().delete()
        PurchaseOrderLine.objects.all().delete()
        
        StockLevel.objects.all().delete()
        self.assertEqual(StockLevel.objects.all().count(), 0)

        self.create_purchase_order(self.user1)

        po = PurchaseOrder.objects.get()

        po.status = PurchaseOrder.PURCHASE_ORDER_RECEIVED
        po.save()

        self.assertEqual(StockLevel.objects.all().count(), 0)

    def test_get_additional_cost_line_data_method(self):
        
        po = PurchaseOrder.objects.get(store=self.store1)

        lines = po.purchaseorderadditionalcost_set.all().order_by('id')

        result = [
            { 
                'name': lines[0].name,
                'amount': str(lines[0].amount),
            },
            {
                'name': lines[1].name,
                'amount': str(lines[1].amount),
            }
        ]

        self.assertEqual(po.get_additional_cost_line_data(), result)
    
    def test_date_fields_with_millie_seconds_timestamp(self):

        # First delete all the models
        PurchaseOrder.objects.all().delete()
        PurchaseOrderLine.objects.all().delete()
        PurchaseOrderAdditionalCost.objects.all().delete()

        # Create purchase order
        created_timestamp=1634926712000

        self.create_purchase_order(
            user=self.user1, 
            created_timestamp=created_timestamp
        )

        po = PurchaseOrder.objects.get(store=self.store1)

        self.assertEqual(po.created_date_timestamp, created_timestamp)
        self.assertEqual(
            po.get_created_date(self.user1.get_user_timezone()),
            'October, 22, 2021, 09:18:PM'
        )

    def test_date_fields_with_0_timestamp(self):

        # First delete all the models
        PurchaseOrder.objects.all().delete()
        PurchaseOrderLine.objects.all().delete()
        PurchaseOrderAdditionalCost.objects.all().delete()

        # Create purchase order
        created_timestamp=0

        self.create_purchase_order(
            user=self.user1, 
            created_timestamp=created_timestamp
        )

        po = PurchaseOrder.objects.get(store=self.store1)

        today = (timezone.now()).strftime("%B, %d, %Y")
        
        self.assertEqual((po.created_date).strftime("%B, %d, %Y"), today)

    def test_date_fields_with_timestamp_that_has_less_than_10_characters(self):

        # First delete all the models
        PurchaseOrder.objects.all().delete()
        PurchaseOrderLine.objects.all().delete()
        PurchaseOrderAdditionalCost.objects.all().delete()

        # Create purchase order
        created_timestamp=12345

        self.create_purchase_order(
            user=self.user1, 
            created_timestamp=created_timestamp
        )

        po = PurchaseOrder.objects.get(store=self.store1)

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual((po.created_date).strftime("%B, %d, %Y"), today)

    def test_date_fields_with_timestamp_that_has_more_than_13_characters(self):

        # First delete all the models
        PurchaseOrder.objects.all().delete()
        PurchaseOrderLine.objects.all().delete()
        PurchaseOrderAdditionalCost.objects.all().delete()

        # Create purchase order
        created_timestamp=123456789012345

        self.create_purchase_order(
            user=self.user1, 
            created_timestamp=created_timestamp
        )

        po = PurchaseOrder.objects.get(store=self.store1)

        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual((po.created_date).strftime("%B, %d, %Y"), today)
    
    def test_if_increamental_id_increaments_only_for_one_profile(self):
        """
        We test if the increamental id increases only top user profiles. If an
        an employee user is the one creating, then it increases for his/her
        top user
        """

        profile2 = Profile.objects.get(user__email='jack@gmail.com')

        employee_for_user1 = create_new_cashier_user("kate", self.profile, self.store1)
        employee_for_user2 = create_new_cashier_user("ben", profile2, self.store1)

        #Create a store
        # ********************** Create inventory counts for the first time
        # Delete all purchase orders first
        PurchaseOrder.objects.all().delete()

        ##### Create 2 purchase orders for user 1
        self.create_purchase_order(user=self.user1, reg_no=111)
        self.create_purchase_order(user=employee_for_user1, reg_no=222)

        # Purchase order 1
        po1 = PurchaseOrder.objects.get(reg_no=111)
        po_count1 = PurchaseOrderCount.objects.get(reg_no=po1.reg_no)

        self.assertEqual(po1.increamental_id, 1001)
        self.assertEqual(po1.__str__(), f'PO{po1.increamental_id}')
        self.assertEqual(po_count1.increamental_id, 1001) 

        # Purchase order 2
        po2 = PurchaseOrder.objects.get(reg_no=222)
        po_count2 = PurchaseOrderCount.objects.get(reg_no=po2.reg_no)

        self.assertEqual(po2.increamental_id, 1002)
        self.assertEqual(po2.__str__(), f'PO{po2.increamental_id}')
        self.assertEqual(po_count2.increamental_id, 1002) 
        

        ##### Create 2 purchase orders for user 2
        self.create_purchase_order(user=self.user2, reg_no=333)
        self.create_purchase_order(user=employee_for_user2, reg_no=444)

        # Purchase order 3
        po3 = PurchaseOrder.objects.get(reg_no=333)
        po_count3 = PurchaseOrderCount.objects.get(reg_no=po3.reg_no)

        self.assertEqual(po3.increamental_id, 1000)
        self.assertEqual(po3.__str__(), f'PO{po3.increamental_id}')
        self.assertEqual(po_count3.increamental_id, 1000) 

        # Purchase order 4
        po4 = PurchaseOrder.objects.get(reg_no=444)
        po_count4 = PurchaseOrderCount.objects.get(reg_no=po4.reg_no)

        self.assertEqual(po4.increamental_id, 1001)
        self.assertEqual(po4.__str__(), f'PO{po4.increamental_id}')
        self.assertEqual(po_count4.increamental_id, 1001) 


        # ********************** Create purchase orders for the second time
        # Delete all purchase orders first
        PurchaseOrder.objects.all().delete()

        ##### Create 2 purchase orders for user 1
        self.create_purchase_order(user=self.user1, reg_no=555)
        self.create_purchase_order(user=employee_for_user1, reg_no=666)

        # Purchase order 1
        po1 = PurchaseOrder.objects.get(reg_no=555)
        po_count1 = PurchaseOrderCount.objects.get(reg_no=po1.reg_no)

        self.assertEqual(po1.increamental_id, 1003)
        self.assertEqual(po1.__str__(), f'PO{po1.increamental_id}')
        self.assertEqual(po_count1.increamental_id, 1003) 

        # Purchase order 2
        po2 = PurchaseOrder.objects.get(reg_no=666)
        po_count2 = PurchaseOrderCount.objects.get(reg_no=po2.reg_no)

        self.assertEqual(po2.increamental_id, 1004)
        self.assertEqual(po2.__str__(), f'PO{po2.increamental_id}')
        self.assertEqual(po_count2.increamental_id, 1004) 

        ##### Create 2 purchase orders for user 2
        self.create_purchase_order(user=self.user2, reg_no=777)
        self.create_purchase_order(user=employee_for_user2, reg_no=888)

        # Purchase order 3
        po3 = PurchaseOrder.objects.get(reg_no=777)
        po_count3 = PurchaseOrderCount.objects.get(reg_no=po3.reg_no)

        self.assertEqual(po3.increamental_id, 1002)
        self.assertEqual(po3.__str__(), f'PO{po3.increamental_id}')
        self.assertEqual(po_count3.increamental_id, 1002) 

        # Purchase order 4
        po4 = PurchaseOrder.objects.get(reg_no=888)
        po_count4 = PurchaseOrderCount.objects.get(reg_no=po4.reg_no)

        self.assertEqual(po4.increamental_id, 1003)
        self.assertEqual(po4.__str__(), f'PO{po4.increamental_id}')
        self.assertEqual(po_count4.increamental_id, 1003)


"""
=========================== PurchaseOrderLine ===================================
"""
class PurchaseOrderLineTestCase(TestCase, PurchaseOrderModelsMixin):
    
    def setUp(self):
        
        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store1 = create_new_store(self.profile, 'Computer Store')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store1, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a supplier user
        self.supplier = create_new_supplier(self.profile, 'jeremy')

        # Creates products
        self.product1 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )
        self.product1.stores.add(self.store1)

        self.product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        self.create_purchase_order(self.user)

    def test_purchase_order_line_fields_verbose_names(self):

        pol = PurchaseOrderLine.objects.get(product=self.product1)

        self.assertEqual(pol._meta.get_field('product_info').verbose_name,'product info')
        self.assertEqual(pol._meta.get_field('quantity').verbose_name,'quantity')
        self.assertEqual(pol._meta.get_field('purchase_cost').verbose_name,'purchase cost')
        self.assertEqual(pol._meta.get_field('amount').verbose_name,'amount')
        self.assertEqual(pol._meta.get_field('reg_no').verbose_name,'reg no')

        fields = ([field.name for field in PurchaseOrderLine._meta.fields])
        
        self.assertEqual(len(fields), 9)

    def test_purchase_order_line_fields_after_it_has_been_created(self):

        pol = PurchaseOrderLine.objects.get(product=self.product1)
        
        self.assertEqual(pol.purchase_order, self.purchase_order)
        self.assertEqual(pol.product, self.product1)
        self.assertEqual(
            pol.product_info, 
            {
                'name': self.product1.name,
                'sku': self.product1.sku,
                'reg_no': self.product1.reg_no,
                'tax_rate': str(self.product1.tax_rate)
            }
        )
        self.assertEqual(pol.quantity, Decimal('350.00'))
        self.assertEqual(pol.purchase_cost, Decimal('190.00'))
        self.assertEqual(pol.amount, Decimal('66500.00'))

    def test__str__method(self):

        pol = PurchaseOrderLine.objects.get(product=self.product1)
        self.assertEqual(str(pol), pol.product.name)


"""
=========================== PurchaseOrderAdditionalCost ===================================
"""
class PurchaseOrderAdditionalCostTestCase(TestCase, PurchaseOrderModelsMixin):
    
    def setUp(self):
        
        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store1 = create_new_store(self.profile, 'Computer Store')

        #Create a tax
        self.tax = create_new_tax(self.profile, self.store1, 'Standard')

        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

        # Create a supplier user
        self.supplier = create_new_supplier(self.profile, 'jeremy')

        # Creates products
        self.product1 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )
        self.product1.stores.add(self.store1)

        self.product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )
        self.product2.stores.add(self.store1)

        self.create_purchase_order(self.user)

    def test_purchase_order_additional_cost_fields_verbose_names(self):

        cost = PurchaseOrderAdditionalCost.objects.get(name='Transport')

        self.assertEqual(cost._meta.get_field('name').verbose_name,'name')
        self.assertEqual(cost._meta.get_field('amount').verbose_name,'amount')

        fields = ([field.name for field in PurchaseOrderAdditionalCost._meta.fields])
        
        self.assertEqual(len(fields), 4)

    def test_purchase_order_additional_cost_fields_after_it_has_been_created(self):

        cost = PurchaseOrderAdditionalCost.objects.get(name='Transport')
        
        self.assertEqual(cost.name, 'Transport')
        self.assertEqual(cost.amount, 200.00)

class InventoryHistoryTestCase(TestCase):

    def creaet_products_and_upate_stock_levels(self):

        # Creates products
        self.product1 = Product.objects.create(
            profile=self.user1.profile,
            name="Shampoo",
            price=2500,
            cost=200,
            barcode='code123'
        )

        self.product2 = Product.objects.create(
            profile=self.user1.profile,
            name="Biscuits",
            price=1500,
            cost=100,
            barcode='code124'
        )

        # Update stock level for product 1
        StockLevel.update_level(
            user=self.user1,
            store=self.store1, 
            product=self.product1, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_REPACKAGE,
            change_source_reg_no=self.product1.reg_no,
            change_source_name=self.product1.__str__(),
            line_source_reg_no=111,
            adjustment=300, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_ADDING
        )

        # Update stock level for product 2
        StockLevel.update_level(
            user=self.user1,
            store=self.store1, 
            product=self.product2, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_REPACKAGE,
            change_source_reg_no=self.product2.reg_no,
            change_source_name=self.product2.__str__(),
            line_source_reg_no=222,
            adjustment=200, 
            update_type=StockLevel.STOCK_LEVEL_UPDATE_ADDING
        )

    def setUp(self):
        
        #Create a users
        self.user1 = create_new_user('john')
        self.user2 = create_new_user('jack')
  
        #Create stores for user1
        self.store1 = create_new_store(self.user1.profile, 'Computer Store')
        self.store2 = create_new_store(self.user1.profile, 'Show Store')

        # Creates products
        self.creaet_products_and_upate_stock_levels()

        # Create date variables
        self.today_morning = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.yesterday_morning = self.today_morning - datetime.timedelta(days=1)
        self.yesterday_midday = self.yesterday_morning + datetime.timedelta(hours=12)
        self.yesterday_4pm = self.yesterday_morning + datetime.timedelta(hours=16)
        self.yesterday_evening = self.yesterday_morning + datetime.timedelta(hours=23, minutes=59, seconds=59)
        
        self.yesterday_but_one_midday = self.yesterday_midday - datetime.timedelta(days=1)
        self.yesterday_but_one_4pm = self.yesterday_4pm - datetime.timedelta(days=1)
        self.yesterday_but_one_evening = self.yesterday_evening - datetime.timedelta(days=1)

        self.yesterday_but_two_midday = self.yesterday_but_one_midday - datetime.timedelta(days=1)
        self.yesterday_but_two_4pm = self.yesterday_but_one_4pm - datetime.timedelta(days=1)
        self.yesterday_but_two_evening = self.yesterday_but_one_evening - datetime.timedelta(days=1)

        # print(f'Today morning: {self.today_morning}')
        # print(f'Yesterday morning: {self.yesterday_morning}')
        # print(f'Yesterday but one midday: {self.yesterday_but_one_midday}')
        # print(f'Yesterday but two midday: {self.yesterday_but_two_midday}')

        # Create inventory historys
        InventoryValuation.create_inventory_valutions(
            profile=self.user1.profile,
            created_date=self.yesterday_but_two_evening
        )

        InventoryValuation.create_inventory_valutions(
            profile=self.user1.profile,
            created_date=self.yesterday_but_one_evening
        )

        InventoryValuation.create_inventory_valutions(
            profile=self.user1.profile,
            created_date=self.yesterday_evening
        )



    def create_stock_level_update(
            self,
            line_source_reg_no,
            adjustment,
            created_date,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_ADDING
        ):

        StockLevel.update_level(
            user=self.user1,
            store=self.store1, 
            product=self.product1, 
            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_REPACKAGE,
            change_source_reg_no=self.product1.reg_no,
            change_source_name=self.product1.__str__(),
            line_source_reg_no=line_source_reg_no,
            adjustment=adjustment, 
            update_type=update_type,
            created_date=created_date
        )

    def test_inventory_history_fields_verbose_names(self):

        history = InventoryHistory.objects.get(store=self.store1, line_source_reg_no=222)

        self.assertEqual(history._meta.get_field('reason').verbose_name,'reason')
        self.assertEqual(history._meta.get_field('change_source_reg_no').verbose_name,'change source reg no')
        self.assertEqual(history._meta.get_field('change_source_desc').verbose_name,'change source desc')
        self.assertEqual(history._meta.get_field('change_source_name').verbose_name,'change source name')
        self.assertEqual(history._meta.get_field('line_source_reg_no').verbose_name,'line source reg no')
        self.assertEqual(history._meta.get_field('adjustment').verbose_name,'adjustment')
        self.assertEqual(history._meta.get_field('stock_after').verbose_name,'stock_after')
        self.assertEqual(history._meta.get_field('store_name').verbose_name,'store name')
        self.assertEqual(history._meta.get_field('product_name').verbose_name,'product name')
        self.assertEqual(history._meta.get_field('user_name').verbose_name,'user name')
        self.assertEqual(history._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(history._meta.get_field('created_date').verbose_name,'created date')
        self.assertEqual(history._meta.get_field('sync_date').verbose_name,'sync date')
     
        fields = ([field.name for field in InventoryHistory._meta.fields])
        
        self.assertEqual(len(fields), 18)

    def test_inventory_history_fields_after_it_has_been_created(self):

        history = InventoryHistory.objects.get(store=self.store1, line_source_reg_no=222)
        
        self.assertEqual(history.user, self.user1)
        self.assertEqual(history.product, self.product2)
        self.assertEqual(history.store, self.store1)
        self.assertEqual(history.product, self.product2)
        self.assertEqual(history.reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(history.change_source_reg_no, self.product2.reg_no)
        self.assertEqual(history.change_source_desc, 'Repackage')
        self.assertEqual(history.change_source_name, self.product2.__str__())
        self.assertEqual(history.line_source_reg_no, 222)
        self.assertEqual(history.adjustment, Decimal('200.00'))
        self.assertEqual(history.stock_after, Decimal('200.00'))

    def test_get_adjusted_by_method(self):

        history = InventoryHistory.objects.get(store=self.store1, line_source_reg_no=222)
        self.assertEqual(history.get_adjusted_by(), self.user1.get_full_name())

    def test_get_store_data_method(self):

        history = InventoryHistory.objects.get(store=self.store1, line_source_reg_no=222)
        self.assertEqual(
            history.get_store_data(), 
            {"name": self.store1.name, "reg_no": self.store1.reg_no}
        )

    def test_get_store_name_method(self):

        history = InventoryHistory.objects.get(store=self.store1, line_source_reg_no=222)
        self.assertEqual(history.get_store_name(), self.store1.name)

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 

        history = InventoryHistory.objects.get(store=self.store1, line_source_reg_no=222)
             
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            history.get_created_date(self.user1.get_user_timezone()))
        )
    
    def test_update_change_source_desc_method(self):

        def change_inventory_reason(reason):
            """
            Simplifies the changing of inventory reason
            """

            history = InventoryHistory.objects.get(
                store=self.store1,
                line_source_reg_no=222
            )
            history.reason = reason
            history.save()

            return history.change_source_desc
    
        ##### Sale
        self.assertEqual(
            change_inventory_reason(InventoryHistory.INVENTORY_HISTORY_SALE), 
            'Sale'
        )

        ##### Refund
        self.assertEqual(
            change_inventory_reason(InventoryHistory.INVENTORY_HISTORY_REFUND), 
            'Refund'
        )

        ##### Receive
        self.assertEqual(
            change_inventory_reason(InventoryHistory.INVENTORY_HISTORY_RECEIVE), 
            'Receive'
        )

        ##### Transfer
        self.assertEqual(
            change_inventory_reason(InventoryHistory.INVENTORY_HISTORY_TRANSFER), 
            'Transfer'
        )

        ##### Damage
        self.assertEqual(
            change_inventory_reason(InventoryHistory.INVENTORY_HISTORY_DAMAGE), 
            'Damage'
        )

        ##### Loss
        self.assertEqual(
            change_inventory_reason(InventoryHistory.INVENTORY_HISTORY_LOSS), 
            'Loss'
        )

        ##### Repackage
        self.assertEqual(
            change_inventory_reason(InventoryHistory.INVENTORY_HISTORY_REPACKAGE), 
            'Repackage'
        )

        ##### Expiry
        self.assertEqual(
            change_inventory_reason(InventoryHistory.INVENTORY_HISTORY_EXPIRY), 
            'Expiry'
        )
    
    def test_recalculate_inventory_valuations(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 2000
        stock_level.save()
        
        #### Create 3 Inventory history for yesterday but two
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_but_two_midday,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=self.yesterday_but_two_4pm,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=self.yesterday_but_two_evening,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )


        #### Create 3 Inventory history for yesterday but one
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=450,
            created_date=self.yesterday_but_one_midday,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )
        self.create_stock_level_update(
            line_source_reg_no=115,
            adjustment=10,
            created_date=self.yesterday_but_one_4pm,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )
        self.create_stock_level_update(
            line_source_reg_no=116,
            adjustment=70,
            created_date=self.yesterday_but_one_evening,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        #### Create 3 Inventory history for yesterday
        self.create_stock_level_update(
            line_source_reg_no=117,
            adjustment=550,
            created_date=self.yesterday_midday,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )
        self.create_stock_level_update(
            line_source_reg_no=118,
            adjustment=40,
            created_date=self.yesterday_4pm,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )
        self.create_stock_level_update(
            line_source_reg_no=119,
            adjustment=80,
            created_date=self.yesterday_evening,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )


        # Confirm inventory historys adjsutments and stock after
        histories = InventoryHistory.objects.filter(store=self.store1).order_by('id')

        # Inventory history 1
        self.assertEqual(histories[0].adjustment, -350)
        self.assertEqual(histories[0].stock_after, 1650)

        # Inventory history 2
        self.assertEqual(histories[1].adjustment, -20)
        self.assertEqual(histories[1].stock_after, 1630)

        # Inventory history 3
        self.assertEqual(histories[2].adjustment, -60)
        self.assertEqual(histories[2].stock_after, 1570)

        # Inventory history 4
        self.assertEqual(histories[3].adjustment, -450)
        self.assertEqual(histories[3].stock_after, 1120)

        # Inventory history 5
        self.assertEqual(histories[4].adjustment, -10)
        self.assertEqual(histories[4].stock_after, 1110)

        # Inventory history 6
        self.assertEqual(histories[5].adjustment, -70)
        self.assertEqual(histories[5].stock_after, 1040)

        # Inventory history 7
        self.assertEqual(histories[6].adjustment, -550)
        self.assertEqual(histories[6].stock_after, 490)

        # Inventory history 8
        self.assertEqual(histories[7].adjustment, -40)
        self.assertEqual(histories[7].stock_after, 450)

        # Inventory history 9
        self.assertEqual(histories[8].adjustment, -80)
        self.assertEqual(histories[8].stock_after, 370)


        #### Change inventory valuations units to 0
        InventoryValuationLine.objects.all().update(units=0)

        inventory_valuations = InventoryValuationLine.objects.all().order_by('id')
        for valuation in inventory_valuations:self.assertEqual(valuation.units, 0)


        # Run recalculate_inventory_valuations
        histories[0].recalculate_inventory_valuations(
            first_date=histories[0].created_date,
            end_date=histories[8].created_date
        )


        # Confirm inventory valuations
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            1570
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            1040
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            370
        )

    def test_recalculate_inventory_valuations_when_there_are_no_inventory_history(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 2000
        stock_level.save()
        
    
        #### Change inventory valuations units to 0
        InventoryValuationLine.objects.all().update(units=0)

        inventory_valuations = InventoryValuationLine.objects.all().order_by('id')
        for valuation in inventory_valuations:self.assertEqual(valuation.units, 0)


        InventoryHistory.start_recalculating_stock_afters_reversee(
            store=self.store1,
            product=self.product1,
            start_date=self.yesterday_but_two_midday,
            end_date=self.today_morning
        )


        # Confirm inventory valuations
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            2000
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            2000
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            2000
        )

    def test_if_inventory_historys_substract_update_themselves_in_reverse_correctly_static22(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 2000
        stock_level.save()

        self.assertEqual(stock_level.units, 2000)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)
        
        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1650)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1650
        )
        
        #### Create history 2
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=self.yesterday_midday,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor2 and stock level
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1630)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1630
        )
        
        #### Create history 3
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=self.yesterday_evening,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor3 and stock level
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1570)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1570
        )
        
        #### Create history 4
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=110,
            created_date=self.today_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor4 and stock level
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1460)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1570
        )

        #### Change stock afters to 0
        InventoryHistory.objects.all().update(stock_after=0)

        inventory_historys = InventoryHistory.objects.all().order_by('id')
        for history in inventory_historys:self.assertEqual(history.stock_after, 0)

        #### Change inventory valuations units to 0
        InventoryValuationLine.objects.all().update(units=0)

        inventory_valuations = InventoryValuationLine.objects.all().order_by('id')
        for valuation in inventory_valuations:self.assertEqual(valuation.units, 0)

        #### Call start_recalculating_stock_afters_reverse
        # history1.start_recalculating_stock_afters_reverse()

        InventoryHistory.start_recalculating_stock_afters_reversee(
            store=self.store1,
            product=self.product1,
            start_date=self.yesterday_but_two_midday,
            end_date=self.today_morning
        )

        # Confirm histor1
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)

        # Confirm histor2
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        # Confirm histor4
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        # Confirm histor4
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)


        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            2000
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1570
        )
    
    def test_if_inventory_historys_substract_update_themselves_in_reverse_correctly_static(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 2000
        stock_level.save()

        self.assertEqual(stock_level.units, 2000)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_but_one_midday,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)
        
        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1650)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            1650
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            300
        )
        
        #### Create history 2
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=self.yesterday_but_one_4pm,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor2 and stock level
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1630)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            1630
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            300
        )
        
        #### Create history 3
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=self.yesterday_but_one_evening,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor3 and stock level
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1570)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            1570
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            300
        )
        
        #### Create history 4
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=110,
            created_date=self.today_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor4 and stock level
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1460)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            1570
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            300
        )

        #### Change stock afters to 0
        InventoryHistory.objects.all().update(stock_after=0)

        inventory_historys = InventoryHistory.objects.all().order_by('id')
        for history in inventory_historys:self.assertEqual(history.stock_after, 0)

        #### Change inventory valuations units to 0
        InventoryValuationLine.objects.all().update(units=0)

        inventory_valuations = InventoryValuationLine.objects.all().order_by('id')
        for valuation in inventory_valuations:self.assertEqual(valuation.units, 0)

        #### Call start_recalculating_stock_afters_reverse
        # history1.start_recalculating_stock_afters_reverse()

        InventoryHistory.start_recalculating_stock_afters_reversee(
            store=self.store1,
            product=self.product1,
            start_date=self.yesterday_but_two_midday,
            end_date=self.today_morning
        )
        
        # Confirm histor1
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)

        # Confirm histor2
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        # Confirm histor4
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        # Confirm histor4
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)


        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            2000
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            1570
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1570
        )

    def test_if_inventory_historys_add_update_themselves_in_reverse_correctly_static(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 50
        stock_level.save()

        self.assertEqual(stock_level.units, 50)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_morning
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, 350)
        self.assertEqual(history1.stock_after, 400)
        
        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 400)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            400
        )


        #### Create history 2
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=self.yesterday_midday
        )

        # Confirm histor2 and stock level
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, 20)
        self.assertEqual(history2.stock_after, 420)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 420)


        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            420
        )

        #### Create history 3
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=self.yesterday_evening
        )

        # Confirm histor3 and stock level
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, 60)
        self.assertEqual(history3.stock_after, 480)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 480)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            480
        )

        #### Create history 4
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=110,
            created_date=self.today_morning
        )

        # Confirm histor4 and stock level
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, 110)
        self.assertEqual(history4.stock_after, 590)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 590)


        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            480
        )

        #### Change stock afters to 0
        InventoryHistory.objects.all().update(stock_after=0)

        inventory_historys = InventoryHistory.objects.all().order_by('id')
        for history in inventory_historys:self.assertEqual(history.stock_after, 0)

        #### Change inventory valuations units to 0
        InventoryValuationLine.objects.all().update(units=0)

        inventory_valuations = InventoryValuationLine.objects.all().order_by('id')
        for valuation in inventory_valuations:self.assertEqual(valuation.units, 0)

        #### Call start_recalculating_stock_afters_reverse
        # history1.start_recalculating_stock_afters_reverse()

        InventoryHistory.start_recalculating_stock_afters_reversee(
            store=self.store1,
            product=self.product1,
            start_date=self.yesterday_but_two_midday,
            end_date=self.today_morning
        )

        # Confirm histor1
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, 350)
        self.assertEqual(history1.stock_after, 400)

        # Confirm histor2
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, 20)
        self.assertEqual(history2.stock_after, 420)

        # Confirm histor3
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, 60)
        self.assertEqual(history3.stock_after, 480)

        # Confirm histor4
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, 110)
        self.assertEqual(history4.stock_after, 590)

    def test_if_inventory_historys_substract_update_themselves_correctly(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 2000
        stock_level.save()

        self.assertEqual(stock_level.units, 2000)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)
        
        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1650)

        #### Create history 2
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=self.yesterday_midday,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor2 and stock level
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1630)

        #### Create history 3
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=self.yesterday_evening,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor3 and stock level
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1570)

        #### Create history 4
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=110,
            created_date=self.today_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor4 and stock level
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1460)
    
    def test_if_inventory_historys_substract_update_themselves_correctly_when_a_new_one_is_added_in_between(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 2000
        stock_level.save()

        self.assertEqual(stock_level.units, 2000)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)
        
        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1650)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1650
        )
        
        #### Create history 2
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=self.yesterday_midday,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor2 and stock level
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1630)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1630
        )
        
        #### Create history 3
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=self.yesterday_evening,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor3 and stock level
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1570)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1570
        )
        
        #### Create history 4
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=110,
            created_date=self.today_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor4 and stock level
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1460)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1570
        )

        #### Create history 5
        self.create_stock_level_update(
            line_source_reg_no=115,
            adjustment=70,
            created_date=self.yesterday_4pm,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor5 and stock level
        history5 = InventoryHistory.objects.get(line_source_reg_no=115)

        self.assertEqual(history5.adjustment, -70)
        self.assertEqual(history5.stock_after, 1560)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1390)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1500
        )

        # Confirm histor1
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)

        # Confirm histor2
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        # Confirm histor3
        history3 = InventoryHistory.objects.get(line_source_reg_no=115)

        self.assertEqual(history3.adjustment, -70)
        self.assertEqual(history3.stock_after, 1560)

        # Confirm histor4
        history4 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history4.adjustment, -60)
        self.assertEqual(history4.stock_after, 1500)

        # Confirm histor5
        history5 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history5.adjustment, -110)
        self.assertEqual(history5.stock_after, 1390)
        
    def test_if_inventory_historys_substract_when_a_middle_inventory_history_is_not_found(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 2000
        stock_level.save()

        self.assertEqual(stock_level.units, 2000)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)
        
        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1650)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1650
        )
        
        #### Create history 2
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=self.yesterday_midday,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor2 and stock level
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1630)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1630
        )
        
        #### Create history 3
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=self.yesterday_evening,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor3 and stock level
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1570)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1570
        )
        
        #### Create history 4
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=110,
            created_date=self.today_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor4 and stock level
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1460)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1570
        )

        # Confirm histor1
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)

        # Confirm histor2
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        # Confirm histor3
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        # Confirm histor4
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)


        # Change dates for history 1 and 2 to 1 day ago
        history1.created_date = self.yesterday_but_two_midday
        history1.save()

        history2.created_date = self.yesterday_but_two_4pm
        history2.save()

        history3.created_date = self.yesterday_but_two_evening
        history3.save()
        
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)
        history4.created_date = self.yesterday_morning
        history4.save()

        # Call recalculate stock after
        history2.start_recalculating_stock_afters_forward(True)

        # Confirm histor1
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)

        # Confirm histor2
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        # Confirm histor3
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        # Confirm histor4
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)


        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            1570
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            1570
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1460
        )

    def test_if_inventory_historys_substract_will_add_back_to_the_stock_levels(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 2000
        stock_level.save()

        self.assertEqual(stock_level.units, 2000)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)
        
        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1650)
 
        history1.delete()

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 2000)

    def test_if_inventory_historys_add_will_add_back_to_the_stock_levels(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 2000
        stock_level.save()

        self.assertEqual(stock_level.units, 2000)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_ADDING
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, 350)
        self.assertEqual(history1.stock_after, 2350)
        
        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 2350)
 
        history1.delete()

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 2000)

    def test_if_inventory_historys_substract_when_date_does_not_have_an_inventory_history(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 2000
        stock_level.save()

        self.assertEqual(stock_level.units, 2000)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)
        
        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1650)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1650
        )
        
        #### Create history 2
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=self.yesterday_midday,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor2 and stock level
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1630)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1630
        )
        
        #### Create history 3
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=self.yesterday_evening,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor3 and stock level
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1570)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1570
        )
        
        #### Create history 4
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=110,
            created_date=self.today_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor4 and stock level
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1460)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1570
        )

        # Confirm histor1
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)

        # Confirm histor2
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        # Confirm histor3
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        # Confirm histor4
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)


        # Change dates for history 1 and 2 to 1 day ago
        history1.created_date = self.yesterday_but_two_midday
        history1.save()

        history2.created_date = self.yesterday_but_two_4pm
        history2.save()

        history3.created_date = self.yesterday_but_two_evening
        history3.save()
        
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)
        history4.created_date = self.yesterday_morning
        history4.save()

        print(history1.created_date)
        print(history2.created_date)
        print(history3.created_date)
        print(history4.created_date)

        # Call recalculate stock after
        history2.start_recalculating_stock_afters_forward(True)

        # Confirm histor1
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)

        # Confirm histor2
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        # Confirm histor3
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        # Confirm histor4
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)


        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_two_evening.date()
            ).units, 
            1570
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            1570
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            1460
        )
    
    def test_if_inventory_historys_substract_update_themselves_correctly_when_a_new_one_is_added_in_between_and_another_at_the_beginning(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 2000
        stock_level.save()

        self.assertEqual(stock_level.units, 2000)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1650)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units,
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units,
            1650
        )

        #### Create history 2
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=self.yesterday_midday,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor2 and stock level
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1630)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units,
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units,
            1630
        )

        #### Create history 3
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=self.yesterday_evening,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor3 and stock level
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1570)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units,
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units,
            1570
        )

        #### Create history 4
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=110,
            created_date=self.today_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor4 and stock level
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1460)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units,
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units,
            1570
        )

        #### Create history 5
        self.create_stock_level_update(
            line_source_reg_no=115,
            adjustment=70,
            created_date=self.yesterday_4pm,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor5 and stock level
        history5 = InventoryHistory.objects.get(line_source_reg_no=115)

        self.assertEqual(history5.adjustment, -70)
        self.assertEqual(history5.stock_after, 1560)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1390)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units,
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units,
            1500
        )

        #### Create history 6
        self.create_stock_level_update(
            line_source_reg_no=116,
            adjustment=1,
            created_date=self.yesterday_but_one_evening,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor6 and stock level
        history6 = InventoryHistory.objects.get(line_source_reg_no=116)

        self.assertEqual(history6.adjustment, -1)
        self.assertEqual(history6.stock_after, 1389)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1389)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units,
            1389
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units,
            1500
        )

        # Confirm histor1
        history1 = InventoryHistory.objects.get(line_source_reg_no=116)

        self.assertEqual(history1.adjustment, -1)
        self.assertEqual(history1.stock_after, 1389)

        # Confirm histor2
        history2 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history2.adjustment, -350)
        self.assertEqual(history2.stock_after, 1650)

        # Confirm histor3
        history3 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history3.adjustment, -20)
        self.assertEqual(history3.stock_after, 1630)

        # Confirm histor4
        history4 = InventoryHistory.objects.get(line_source_reg_no=115)

        self.assertEqual(history4.adjustment, -70)
        self.assertEqual(history4.stock_after, 1560)

        # Confirm histor5
        history5 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history5.adjustment, -60)
        self.assertEqual(history5.stock_after, 1500)

        # Confirm histor6
        history6 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history6.adjustment, -110)
        self.assertEqual(history6.stock_after, 1390)


    def test_if_inventory_historys_substract_update_themselves_correctly_when_a_new_one_is_added_in_between_and_another_at_the_end(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 2000
        stock_level.save()

        self.assertEqual(stock_level.units, 2000)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1650)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units,
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units,
            1650
        )

        #### Create history 2
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=self.yesterday_midday,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor2 and stock level
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1630)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units,
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units,
            1630
        )

        #### Create history 3
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=self.yesterday_evening,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor3 and stock level
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, -60)
        self.assertEqual(history3.stock_after, 1570)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1570)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units,
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units,
            1570
        )

        #### Create history 4
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=110,
            created_date=self.today_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor4 and stock level
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, -110)
        self.assertEqual(history4.stock_after, 1460)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1460)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units,
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units,
            1570
        )

        #### Create history 5
        self.create_stock_level_update(
            line_source_reg_no=115,
            adjustment=70,
            created_date=self.yesterday_4pm,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor5 and stock level
        history5 = InventoryHistory.objects.get(line_source_reg_no=115)

        self.assertEqual(history5.adjustment, -70)
        self.assertEqual(history5.stock_after, 1560)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1390)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units,
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units,
            1500
        )

        #### Create history 6
        self.create_stock_level_update(
            line_source_reg_no=116,
            adjustment=1,
            created_date=self.today_morning,
            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
        )

        # Confirm histor6 and stock level
        history6 = InventoryHistory.objects.get(line_source_reg_no=116)

        self.assertEqual(history6.adjustment, -1)
        self.assertEqual(history6.stock_after, 1389)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 1389)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units,
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1,
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units,
            1500
        )

        # Confirm histor1
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, -350)
        self.assertEqual(history1.stock_after, 1650)

        # Confirm histor2
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, -20)
        self.assertEqual(history2.stock_after, 1630)

        # Confirm histor3
        history3 = InventoryHistory.objects.get(line_source_reg_no=115)

        self.assertEqual(history3.adjustment, -70)
        self.assertEqual(history3.stock_after, 1560)

        # Confirm histor4
        history4 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history4.adjustment, -60)
        self.assertEqual(history4.stock_after, 1500)

        # Confirm histor5
        history5 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history5.adjustment, -110)
        self.assertEqual(history5.stock_after, 1390)

        # Confirm histor6
        history6 = InventoryHistory.objects.get(line_source_reg_no=116)

        self.assertEqual(history6.adjustment, -1)
        self.assertEqual(history6.stock_after, 1389)

    def test_if_inventory_historys_add_update_themselves_correctly(self):

        today_morning = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_morning = today_morning - datetime.timedelta(days=1)
        yesterday_midday = yesterday_morning + datetime.timedelta(hours=12)
        yesterday_evening = yesterday_morning + datetime.timedelta(hours=23)

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 50
        stock_level.save()

        self.assertEqual(stock_level.units, 50)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=yesterday_morning
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, 350)
        self.assertEqual(history1.stock_after, 400)
        
        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 400)

        #### Create history 2
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=yesterday_midday
        )

        # Confirm histor2 and stock level
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, 20)
        self.assertEqual(history2.stock_after, 420)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 420)

        #### Create history 3
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=yesterday_evening
        )

        # Confirm histor3 and stock level
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, 60)
        self.assertEqual(history3.stock_after, 480)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 480)

        #### Create history 4
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=110,
            created_date=today_morning
        )

        # Confirm histor4 and stock level
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, 110)
        self.assertEqual(history4.stock_after, 590)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 590)

    def test_if_inventory_historys_add_update_themselves_correctly_when_a_new_one_is_added_in_between(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 50
        stock_level.save()

        self.assertEqual(stock_level.units, 50)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_morning
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, 350)
        self.assertEqual(history1.stock_after, 400)
        
        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 400)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            400
        )


        #### Create history 2
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=self.yesterday_midday
        )

        # Confirm histor2 and stock level
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, 20)
        self.assertEqual(history2.stock_after, 420)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 420)


        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            420
        )

        #### Create history 3
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=self.yesterday_evening
        )

        # Confirm histor3 and stock level
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, 60)
        self.assertEqual(history3.stock_after, 480)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 480)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            480
        )

        #### Create history 4
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=110,
            created_date=self.today_morning
        )

        # Confirm histor4 and stock level
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, 110)
        self.assertEqual(history4.stock_after, 590)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 590)


        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            480
        )

        #### Create history 5
        self.create_stock_level_update(
            line_source_reg_no=115,
            adjustment=70,
            created_date=self.yesterday_4pm
        )

        # Confirm histor5 and stock level
        history5 = InventoryHistory.objects.get(line_source_reg_no=115)

        self.assertEqual(history5.adjustment, 70)
        self.assertEqual(history5.stock_after, 490)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 660)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            550
        )

        # Confirm histor1
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, 350)
        self.assertEqual(history1.stock_after, 400)

        # Confirm histor2
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, 20)
        self.assertEqual(history2.stock_after, 420)

        # Confirm histor3
        history3 = InventoryHistory.objects.get(line_source_reg_no=115)

        self.assertEqual(history3.adjustment, 70)
        self.assertEqual(history3.stock_after, 490)

        # Confirm histor4
        history4 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history4.adjustment, 60)
        self.assertEqual(history4.stock_after, 550)

        # Confirm histor5
        history5 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history5.adjustment, 110)
        self.assertEqual(history5.stock_after, 660)

    def test_if_inventory_historys_add_update_themselves_correctly_when_a_new_one_is_added_in_between_and_another_at_the_beginning(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 50
        stock_level.save()

        self.assertEqual(stock_level.units, 50)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_morning
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, 350)
        self.assertEqual(history1.stock_after, 400)
        
        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 400)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            400
        )


        #### Create history 2
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=self.yesterday_midday
        )

        # Confirm histor2 and stock level
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, 20)
        self.assertEqual(history2.stock_after, 420)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 420)


        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            420
        )

        #### Create history 3
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=self.yesterday_evening
        )

        # Confirm histor3 and stock level
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, 60)
        self.assertEqual(history3.stock_after, 480)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 480)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            480
        )

        #### Create history 4
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=110,
            created_date=self.today_morning
        )

        # Confirm histor4 and stock level
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, 110)
        self.assertEqual(history4.stock_after, 590)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 590)


        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            480
        )


        #### Create history 5
        self.create_stock_level_update(
            line_source_reg_no=115,
            adjustment=70,
            created_date=self.yesterday_4pm
        )

        # Confirm histor5 and stock level
        history5 = InventoryHistory.objects.get(line_source_reg_no=115)

        self.assertEqual(history5.adjustment, 70)
        self.assertEqual(history5.stock_after, 490)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 660)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            550
        )

        #### Create history 6
        self.create_stock_level_update(
            line_source_reg_no=116,
            adjustment=1,
            created_date=self.yesterday_but_one_evening
        )

        # Confirm histor5 and stock level
        history6 = InventoryHistory.objects.get(line_source_reg_no=116)

        self.assertEqual(history6.adjustment, 1)
        self.assertEqual(history6.stock_after, 661)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 661)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            661
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            550
        )


        # Confirm history1
        history1 = InventoryHistory.objects.get(line_source_reg_no=116)

        self.assertEqual(history1.adjustment, 1)
        self.assertEqual(history1.stock_after, 661)
        
        # Confirm history2
        history2 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history2.adjustment, 350)
        self.assertEqual(history2.stock_after, 400)

        # Confirm history3
        history3 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history3.adjustment, 20)
        self.assertEqual(history3.stock_after, 420)

        # Confirm history4
        history4 = InventoryHistory.objects.get(line_source_reg_no=115)

        self.assertEqual(history4.adjustment, 70)
        self.assertEqual(history4.stock_after, 490)

        # Confirm history5
        history5 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history5.adjustment, 60)
        self.assertEqual(history5.stock_after, 550)

        # Confirm history6
        history6 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history6.adjustment, 110)
        self.assertEqual(history6.stock_after, 660)
 
    def test_if_inventory_historys_add_update_themselves_correctly_when_a_new_one_is_added_in_between_and_another_at_the_end(self):

        # First delete all the models
        InventoryHistory.objects.all().delete()

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.minimum_stock_level = 50
        stock_level.units = 50
        stock_level.save()

        self.assertEqual(stock_level.units, 50)

        #### Create history 1
        self.create_stock_level_update(
            line_source_reg_no=111,
            adjustment=350,
            created_date=self.yesterday_morning
        )

        # Confirm histor1 and stock level
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, 350)
        self.assertEqual(history1.stock_after, 400)
        
        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 400)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            400
        )


        #### Create history 2
        self.create_stock_level_update(
            line_source_reg_no=112,
            adjustment=20,
            created_date=self.yesterday_midday
        )

        # Confirm histor2 and stock level
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, 20)
        self.assertEqual(history2.stock_after, 420)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 420)


        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            420
        )

        #### Create history 3
        self.create_stock_level_update(
            line_source_reg_no=113,
            adjustment=60,
            created_date=self.yesterday_evening
        )

        # Confirm histor3 and stock level
        history3 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history3.adjustment, 60)
        self.assertEqual(history3.stock_after, 480)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 480)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            480
        )

        #### Create history 4
        self.create_stock_level_update(
            line_source_reg_no=114,
            adjustment=110,
            created_date=self.today_morning
        )

        # Confirm histor4 and stock level
        history4 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history4.adjustment, 110)
        self.assertEqual(history4.stock_after, 590)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 590)


        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            480
        )

        #### Create history 5
        self.create_stock_level_update(
            line_source_reg_no=115,
            adjustment=70,
            created_date=self.yesterday_4pm
        )

        # Confirm histor5 and stock level
        history5 = InventoryHistory.objects.get(line_source_reg_no=115)

        self.assertEqual(history5.adjustment, 70)
        self.assertEqual(history5.stock_after, 490)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 660)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            550
        )

        #### Create history 6
        self.create_stock_level_update(
            line_source_reg_no=116,
            adjustment=1,
            created_date=self.today_morning
        )

        # Confirm histor5 and stock level
        history6 = InventoryHistory.objects.get(line_source_reg_no=116)

        self.assertEqual(history6.adjustment, 1)
        self.assertEqual(history6.stock_after, 661)

        self.assertEqual(StockLevel.objects.get(product=self.product1, store=self.store1).units, 661)

        # Confirm inventory valuation
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_but_one_evening.date()
            ).units, 
            300
        )
        self.assertEqual(
            InventoryValuationLine.objects.get(
                store=self.store1, 
                product=self.product1,
                inventory_valution__created_date__date=self.yesterday_evening.date()
            ).units, 
            550
        )

        # Confirm histor1
        history1 = InventoryHistory.objects.get(line_source_reg_no=111)

        self.assertEqual(history1.adjustment, 350)
        self.assertEqual(history1.stock_after, 400)

        # Confirm histor2
        history2 = InventoryHistory.objects.get(line_source_reg_no=112)

        self.assertEqual(history2.adjustment, 20)
        self.assertEqual(history2.stock_after, 420)

        # Confirm histor3
        history3 = InventoryHistory.objects.get(line_source_reg_no=115)

        self.assertEqual(history3.adjustment, 70)
        self.assertEqual(history3.stock_after, 490)

        # Confirm histor4
        history4 = InventoryHistory.objects.get(line_source_reg_no=113)

        self.assertEqual(history4.adjustment, 60)
        self.assertEqual(history4.stock_after, 550)

        # Confirm histor5
        history5 = InventoryHistory.objects.get(line_source_reg_no=114)

        self.assertEqual(history5.adjustment, 110)
        self.assertEqual(history5.stock_after, 660)

        # Confirm histor6
        history6 = InventoryHistory.objects.get(line_source_reg_no=116)

        self.assertEqual(history6.adjustment, 1)
        self.assertEqual(history6.stock_after, 661)
 
"""
=========================== ProductTransform ===================================
"""

class ProductTransformModelsMixin:

    def create_product_maps_for_rice(self):

        rice_25_sack = Product.objects.create(
            profile=self.profile,
            name="Rice 25kg Sack",
            price=3200,
            cost=3000,
            barcode='code123'
        )

        rice_1kg = Product.objects.create(
            profile=self.profile,
            name="Rice 1kg",
            price=150,
            cost=120,
            barcode='code123'
        )

        rice_500g = Product.objects.create(
            profile=self.profile,
            name="Rice 500g",
            price=75,
            cost=60,
            barcode='code123'
        )

        # Create master product with 2 productions
        rice_1kg_map = ProductProductionMap.objects.create(
            product_map=rice_1kg,
            quantity=25
        )

        rice_500g_map = ProductProductionMap.objects.create(
            product_map=rice_500g,
            quantity=50
        )

        rice_25_sack.productions.add(rice_1kg_map, rice_500g_map)


        # Change stock amount
        # Product1
        stock_level = StockLevel.objects.get(store=self.store, product=rice_25_sack)
        stock_level.units = 30
        stock_level.save()

        # Product2
        stock_level = StockLevel.objects.get(store=self.store, product=rice_1kg)
        stock_level.units = 21
        stock_level.save()

        # Product3
        stock_level = StockLevel.objects.get(store=self.store, product=rice_500g)
        stock_level.units = 10
        stock_level.save()

    def create_product_maps_for_sugar(self):

        sugar_sack = Product.objects.create(
            profile=self.profile,
            name="Sugar 50kg Sack",
            price=10000,
            cost=9000,
            barcode='code123'
        )

        sugar_1kg = Product.objects.create(
            profile=self.profile,
            name="Sugar 1kg",
            price=200,
            cost=180,
            barcode='code123'
        )

        sugar_500g = Product.objects.create(
            profile=self.profile,
            name="Sugar 500g",
            price=100,
            cost=90,
            barcode='code123'
        )

        sugar_250g = Product.objects.create(
            profile=self.profile,
            name="Sugar 250g",
            price=50,
            cost=45,
            barcode='code123'
        )

        # Create master product with 2 productions
        sugar_1kg_map = ProductProductionMap.objects.create(
            product_map=sugar_1kg,
            quantity=50
        )

        sugar_500g_map = ProductProductionMap.objects.create(
            product_map=sugar_500g,
            quantity=100
        )

        sugar_250g_map = ProductProductionMap.objects.create(
            product_map=sugar_250g,
            quantity=200
        )

        sugar_sack.productions.add(sugar_1kg_map, sugar_500g_map, sugar_250g_map)


        # Change stock amount
        # Product1
        stock_level = StockLevel.objects.get(store=self.store, product=sugar_sack)
        stock_level.units = 20
        stock_level.save()

        # Product2
        stock_level = StockLevel.objects.get(store=self.store, product=sugar_1kg)
        stock_level.units = 45
        stock_level.save()

        # Product3
        stock_level = StockLevel.objects.get(store=self.store, product=sugar_500g)
        stock_level.units = 60
        stock_level.save()

        # Product4
        stock_level = StockLevel.objects.get(store=self.store, product=sugar_250g)
        stock_level.units = 75
        stock_level.save()

    def create_a_product_assembly(self, user, store, reg_no):

        sugar_sack = Product.objects.get(name="Sugar 50kg Sack")
        sugar_1kg = Product.objects.get(name="Sugar 1kg")

        rice_sack = Product.objects.get(name="Rice 25kg Sack")
        rice_500g = Product.objects.get(name="Rice 500g")

        # Create product disassembly
        product_transform = ProductTransform.objects.create(
            user=user,
            store=store,
            total_quantity=1300,
            reg_no=reg_no
        )

        ProductTransformLine.objects.create(
            product_transform=product_transform,
            source_product=sugar_sack,
            target_product=sugar_1kg ,
            quantity=1,
            added_quantity=50,
            cost=1100,
        )

        ProductTransformLine.objects.create(
            product_transform=product_transform,
            source_product=rice_sack,
            target_product=rice_500g,
            quantity=2,
            added_quantity=100,
            cost=62,
        )

    def create_a_reverse_product_assembly(self, user, store, reg_no):

        sugar_sack = Product.objects.get(name="Sugar 50kg Sack")
        sugar_1kg = Product.objects.get(name="Sugar 1kg")

        rice_sack = Product.objects.get(name="Rice 25kg Sack")
        rice_500g = Product.objects.get(name="Rice 500g")

        # Create product disassembly
        product_transform = ProductTransform.objects.create(
            user=user,
            store=store,
            total_quantity=1300,
            reg_no=reg_no
        )

        ProductTransformLine.objects.create(
            product_transform=product_transform,
            source_product=sugar_1kg ,
            target_product=sugar_sack,
            quantity=100,
            added_quantity=2,
            cost=9100,
        )

        ProductTransformLine.objects.create(
            product_transform=product_transform,
            source_product=rice_500g,
            target_product=rice_sack,
            quantity=100,
            added_quantity=2,
            cost=3100,
        )
        
class ProductTransformTestCase(TestCase, ProductTransformModelsMixin):
    
    def setUp(self):
        
        #Create a user1
        self.user1 = create_new_user('john')
        self.user2 = create_new_user('jack')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        #Create a store
        self.store = create_new_store(self.profile, 'Computer Store')

        self.create_product_maps_for_rice()
        self.create_product_maps_for_sugar()
    
    def test_product_transform_fields_verbose_names(self):

        # Create disassembly
        self.create_a_product_assembly(self.user1, self.store, reg_no=111)

        pt = ProductTransform.objects.get(store=self.store)

        self.assertEqual(pt._meta.get_field('status').verbose_name,'status')
        self.assertEqual(pt._meta.get_field('order_completed').verbose_name,'order completed')
        self.assertEqual(pt._meta.get_field('total_quantity').verbose_name,'total quantity')
        self.assertEqual(pt._meta.get_field('increamental_id').verbose_name,'increamental id')
        self.assertEqual(pt._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(pt._meta.get_field('created_date').verbose_name,'created date')

        self.assertEqual(pt._meta.get_field('is_auto_repackaged').verbose_name,'is auto repackaged')
        self.assertEqual(pt._meta.get_field('auto_repackaged_source_desc').verbose_name,'auto repackaged source desc')
        self.assertEqual(pt._meta.get_field('auto_repackaged_source_reg_no').verbose_name,'auto repackaged source reg no')

        fields = ([field.name for field in ProductTransform._meta.fields])
        
        self.assertEqual(len(fields), 12)

    def test_product_transform_fields_after_it_has_been_created(self):

        # Create disassembly
        self.create_a_product_assembly(self.user1, self.store, reg_no=0)

        pt = ProductTransform.objects.get(store=self.store)
        
        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(pt.user, self.user1)
        self.assertEqual(pt.store, self.store)
        self.assertEqual(pt.status, ProductTransform.PRODUCT_TRANSFORM_PENDING)
        self.assertEqual(pt.total_quantity, 1300)
        self.assertEqual(pt.increamental_id, 1000)
        self.assertTrue(pt.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((pt.created_date).strftime("%B, %d, %Y"), today)

        self.assertEqual(pt.is_auto_repackaged, False)
        self.assertEqual(pt.auto_repackaged_source_desc, '')
        self.assertEqual(pt.auto_repackaged_source_reg_no, 0)

    def test__str__method(self):

        # Create disassembly
        self.create_a_product_assembly(self.user1, self.store, reg_no=0)

        po = ProductTransform.objects.get(store=self.store)
        self.assertEqual(po.__str__(), f"DS{po.increamental_id}")

    def test_get_created_by_method(self):

        # Create disassembly
        self.create_a_product_assembly(self.user1, self.store, reg_no=0)

        po = ProductTransform.objects.get(store=self.store)
        self.assertEqual(po.get_created_by(), self.user1.get_full_name())

    def test_get_store_name_method(self):

        # Create disassembly
        self.create_a_product_assembly(self.user1, self.store, reg_no=0)

        po = ProductTransform.objects.get(store=self.store)
        self.assertEqual(po.get_store_name(), self.store.name)

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 

        # Create disassembly
        self.create_a_product_assembly(self.user1, self.store, reg_no=0)

        po = ProductTransform.objects.get(store=self.store)
             
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            po.get_created_date(self.user1.get_user_timezone()))
        )

    def test_get_line_data_method(self):

        sugar_sack = Product.objects.get(name="Sugar 50kg Sack")
        sugar_1kg = Product.objects.get(name="Sugar 1kg")

        rice_sack = Product.objects.get(name="Rice 25kg Sack")
        rice_500g = Product.objects.get(name="Rice 500g")

        # Create disassembly
        self.create_a_product_assembly(self.user1, self.store, reg_no=0)
        
        po = ProductTransform.objects.get(store=self.store)

        lines = po.producttransformline_set.all().order_by('id')

        result = [
            {
                'source_product_info': {
                    'name': sugar_sack.name, 
                    'reg_no': sugar_sack.reg_no
                }, 
                'target_product_info': {
                    'name': sugar_1kg.name, 
                    'reg_no': sugar_1kg.reg_no
                }, 
                'quantity': '1.00', 
                'added_quantity': '50.00', 
                'cost': '1100.00', 
                'amount': '1100.00', 
                'is_reverse': lines[0].is_reverse,
                'reg_no': lines[0].reg_no
            }, 
            {
                'source_product_info': {
                    'name': rice_sack.name,
                    'reg_no': rice_sack.reg_no
                }, 
                'target_product_info': {
                    'name': rice_500g.name, 
                    'reg_no': rice_500g.reg_no
                }, 
                'quantity': '2.00', 
                'added_quantity': '100.00', 
                'cost': '62.00', 
                'amount': '124.00', 
                'is_reverse': lines[1].is_reverse,
                'reg_no': lines[1].reg_no
            }
        ]

        self.assertEqual(po.get_line_data(), result)
   
    def test_if_transform_received_true_will_update_product_stock_level_units_and_cost_for_one_sack2(self):

        sugar_sack = Product.objects.get(name="Sugar 50kg Sack")
        sugar_1kg = Product.objects.get(name="Sugar 1kg")

        rice_sack = Product.objects.get(name="Rice 25kg Sack")
        rice_500g = Product.objects.get(name="Rice 500g")

        # Confirm Stock levels first
        # Sugar
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=sugar_sack).units,
            20
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=sugar_1kg).units,
            45
        )

        # Rice
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=rice_sack).units,
            30
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=rice_500g).units,
            10
        )

        # Check if cost first
        # Sugar costs
        self.assertEqual(
            Product.objects.get(id=sugar_sack.id).cost, Decimal('9000.00'))
        self.assertEqual(
            Product.objects.get(id=sugar_1kg.id).cost, Decimal('180.00'))
        
        # Rice costs
        self.assertEqual(
            Product.objects.get(id=rice_sack.id).cost, Decimal('3000.00'))
        self.assertEqual(
            Product.objects.get(id=rice_500g.id).cost, Decimal('60.00'))

        # Create disassembly
        self.create_a_product_assembly(self.user1, self.store, reg_no=111)
        pt = ProductTransform.objects.get()
        pt.status = ProductTransform.PRODUCT_TRANSFORM_RECEIVED
        pt.save()
        
        # Confirm Stock levels were changed
        # Sugar
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=sugar_sack).units,
            19
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=sugar_1kg).units,
            95
        )

        # Rice
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=rice_sack).units,
            28
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=rice_500g).units,
            110
        )

        # Check if cost was updated
        # Sugar
        self.assertEqual(
            Product.objects.get(id=sugar_sack.id).cost, Decimal('9000.00'))
        self.assertEqual(
            Product.objects.get(id=sugar_1kg.id).cost, Decimal('664.21'))
        
        # Rice
        self.assertEqual(
            Product.objects.get(id=rice_sack.id).cost, Decimal('3000.00'))
        self.assertEqual(
            Product.objects.get(id=rice_500g.id).cost, Decimal('61.82'))
        
        ############ Test if Inventory History will be created
        pt = ProductTransform.objects.get(store=self.store)
        lines = ProductTransformLine.objects.all().order_by('id')
        self.assertEqual(lines.count(), 2)

        historys = InventoryHistory.objects.filter(store=self.store).order_by('id')
        self.assertEqual(historys.count(), 4)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user1)
        self.assertEqual(historys[0].product, sugar_sack)
        self.assertEqual(historys[0].store, self.store)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(historys[0].change_source_reg_no, pt.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Repackage')
        self.assertEqual(historys[0].change_source_name, pt.__str__())
        self.assertEqual(historys[0].line_source_reg_no, int(f'{lines[0].reg_no}0'))
        self.assertEqual(historys[0].adjustment, Decimal('-1.00'))
        self.assertEqual(historys[0].stock_after, Decimal('19.00'))

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user1)
        self.assertEqual(historys[1].product, sugar_1kg)
        self.assertEqual(historys[1].store, self.store)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(historys[1].change_source_reg_no, pt.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Repackage')
        self.assertEqual(historys[1].change_source_name, pt.__str__())
        self.assertEqual(historys[1].line_source_reg_no, int(f'{lines[0].reg_no}1'))
        self.assertEqual(historys[1].adjustment, Decimal('50.00'))
        self.assertEqual(historys[1].stock_after, Decimal('95.00'))

        # Inventory history 3
        self.assertEqual(historys[2].user, self.user1)
        self.assertEqual(historys[2].product, rice_sack)
        self.assertEqual(historys[2].store, self.store)
        self.assertEqual(historys[2].reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(historys[2].change_source_reg_no, pt.reg_no)
        self.assertEqual(historys[2].change_source_desc, 'Repackage')
        self.assertEqual(historys[2].change_source_name, pt.__str__())
        self.assertEqual(historys[2].line_source_reg_no, int(f'{lines[1].reg_no}0'))
        self.assertEqual(historys[2].adjustment, Decimal('-2.00'))
        self.assertEqual(historys[2].stock_after, Decimal('28.00'))

        # Inventory history 4
        self.assertEqual(historys[3].user, self.user1)
        self.assertEqual(historys[3].product, rice_500g)
        self.assertEqual(historys[3].store, self.store)
        self.assertEqual(historys[3].reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(historys[3].change_source_reg_no, pt.reg_no)
        self.assertEqual(historys[3].change_source_desc, 'Repackage')
        self.assertEqual(historys[3].change_source_name, pt.__str__())
        self.assertEqual(historys[3].line_source_reg_no, int(f'{lines[1].reg_no}1'))
        self.assertEqual(historys[3].adjustment, Decimal('100.00'))
        self.assertEqual(historys[3].stock_after, Decimal('110.00'))

    def test_if_transform_received_true_will_update_product_stock_level_units_and_cost_for_one_sack3(self):

        sugar_sack = Product.objects.get(name="Sugar 50kg Sack")
        sugar_1kg = Product.objects.get(name="Sugar 1kg")

        rice_sack = Product.objects.get(name="Rice 25kg Sack")
        rice_500g = Product.objects.get(name="Rice 500g")

        # Confirm Stock levels first
        # Sugar
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=sugar_sack).units,
            20
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=sugar_1kg).units,
            45
        )

        # Rice
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=rice_sack).units,
            30
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=rice_500g).units,
            10
        )

        # Check if cost first
        # Sugar costs
        self.assertEqual(
            Product.objects.get(id=sugar_sack.id).cost, Decimal('9000.00'))
        self.assertEqual(
            Product.objects.get(id=sugar_1kg.id).cost, Decimal('180.00'))
        
        # Rice costs
        self.assertEqual(
            Product.objects.get(id=rice_sack.id).cost, Decimal('3000.00'))
        self.assertEqual(
            Product.objects.get(id=rice_500g.id).cost, Decimal('60.00'))

        # Create disassembly
        self.create_a_reverse_product_assembly(self.user1, self.store, reg_no=111)
        pt = ProductTransform.objects.get()
        pt.status = ProductTransform.PRODUCT_TRANSFORM_RECEIVED
        pt.save()
        
        # Confirm Stock levels were changed
        # Sugar
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=sugar_sack).units,
            22
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=sugar_1kg).units,
            -55
        )

        # Rice
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=rice_sack).units,
            32
        )
        self.assertEqual(
            StockLevel.objects.get(store=self.store, product=rice_500g).units,
            -90
        )

        # Check if cost was updated
        # Sugar
        self.assertEqual(
            Product.objects.get(id=sugar_sack.id).cost, Decimal('9009.09'))
        self.assertEqual(
            Product.objects.get(id=sugar_1kg.id).cost, Decimal('180.00'))
        
        # Rice
        self.assertEqual(
            Product.objects.get(id=rice_sack.id).cost, Decimal('3006.25'))
        self.assertEqual(
            Product.objects.get(id=rice_500g.id).cost, Decimal('60.00'))
        
        ############ Test if Inventory History will be created
        pt = ProductTransform.objects.get(store=self.store)
        lines = ProductTransformLine.objects.all().order_by('id')
        self.assertEqual(lines.count(), 2)

        historys = InventoryHistory.objects.filter(store=self.store).order_by('id')
        self.assertEqual(historys.count(), 4)

        # Inventory history 1
        self.assertEqual(historys[0].user, self.user1)
        self.assertEqual(historys[0].product, sugar_1kg)
        self.assertEqual(historys[0].store, self.store)
        self.assertEqual(historys[0].reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(historys[0].change_source_reg_no, pt.reg_no)
        self.assertEqual(historys[0].change_source_desc, 'Repackage')
        self.assertEqual(historys[0].change_source_name, pt.__str__())
        self.assertEqual(historys[0].line_source_reg_no, int(f'{lines[0].reg_no}0'))
        self.assertEqual(historys[0].adjustment, Decimal('-100.00'))
        self.assertEqual(historys[0].stock_after, Decimal('-55.00'))

        # Inventory history 2
        self.assertEqual(historys[1].user, self.user1)
        self.assertEqual(historys[1].product, sugar_sack)
        self.assertEqual(historys[1].store, self.store)
        self.assertEqual(historys[1].reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(historys[1].change_source_reg_no, pt.reg_no)
        self.assertEqual(historys[1].change_source_desc, 'Repackage')
        self.assertEqual(historys[1].change_source_name, pt.__str__())
        self.assertEqual(historys[1].line_source_reg_no, int(f'{lines[0].reg_no}1'))
        self.assertEqual(historys[1].adjustment, Decimal('2.00'))
        self.assertEqual(historys[1].stock_after, Decimal('22.00'))

        # Inventory history 3
        self.assertEqual(historys[2].user, self.user1)
        self.assertEqual(historys[2].product, rice_500g)
        self.assertEqual(historys[2].store, self.store)
        self.assertEqual(historys[2].reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(historys[2].change_source_reg_no, pt.reg_no)
        self.assertEqual(historys[2].change_source_desc, 'Repackage')
        self.assertEqual(historys[2].change_source_name, pt.__str__())
        self.assertEqual(historys[2].line_source_reg_no, int(f'{lines[1].reg_no}0'))
        self.assertEqual(historys[2].adjustment, Decimal('-100.00'))
        self.assertEqual(historys[2].stock_after, Decimal('-90.00'))

        # Inventory history 4
        self.assertEqual(historys[3].user, self.user1)
        self.assertEqual(historys[3].product, rice_sack)
        self.assertEqual(historys[3].store, self.store)
        self.assertEqual(historys[3].reason, InventoryHistory.INVENTORY_HISTORY_REPACKAGE)
        self.assertEqual(historys[3].change_source_reg_no, pt.reg_no)
        self.assertEqual(historys[3].change_source_desc, 'Repackage')
        self.assertEqual(historys[3].change_source_name, pt.__str__())
        self.assertEqual(historys[3].line_source_reg_no, int(f'{lines[1].reg_no}1'))
        self.assertEqual(historys[3].adjustment, Decimal('2.00'))
        self.assertEqual(historys[3].stock_after, Decimal('32.00'))

    def test_if_product_transform_line_creation_wont_error_out_when_product_has_no_stock_level_model(self):

        # First delete all the models
        ProductTransform.objects.all().delete()
        ProductTransform.objects.all().delete()
        
        StockLevel.objects.all().delete()
        self.assertEqual(StockLevel.objects.all().count(), 0)

        # Create disassembly
        self.create_a_product_assembly(self.user1, self.store, reg_no=111)

        self.assertEqual(StockLevel.objects.all().count(), 0)
 

    def test_if_increamental_id_increaments_only_for_one_profile(self):
        """
        We test if the increamental id increases only top user profiles. If an
        an employee user is the one creating, then it increases for his/her
        top user
        """
        profile2 = Profile.objects.get(user__email='jack@gmail.com')

        employee_for_user1 = create_new_cashier_user("kate", self.profile, self.store)
        employee_for_user2 = create_new_cashier_user("ben", profile2, self.store)


        self.create_a_product_assembly(self.user1, self.store, reg_no=0)
        # ********************** Create inventory counts for the first time
        # Delete all purchase orders first
        ProductTransform.objects.all().delete()

        ##### Create 2 product assemblies for user 1
        self.create_a_product_assembly(self.user1, self.store, reg_no=111)
        self.create_a_product_assembly(employee_for_user1, self.store, reg_no=222)

        # Product assembly 1
        po1 = ProductTransform.objects.get(reg_no=111)
        po_count1 = ProductTransformCount.objects.get(reg_no=po1.reg_no)

        self.assertEqual(po1.increamental_id, 1001)
        self.assertEqual(po1.__str__(), f'DS{po1.increamental_id}')
        self.assertEqual(po_count1.increamental_id, 1001) 
        # Product assembly 2
        po2 = ProductTransform.objects.get(reg_no=222)
        po_count2 = ProductTransformCount.objects.get(reg_no=po2.reg_no)

        self.assertEqual(po2.increamental_id, 1002)
        self.assertEqual(po2.__str__(), f'DS{po2.increamental_id}')
        self.assertEqual(po_count2.increamental_id, 1002) 
 

        ##### Create 2 purchase orders for user 2
        self.create_a_product_assembly(self.user2, self.store, reg_no=333)
        self.create_a_product_assembly(employee_for_user2, self.store, reg_no=444)

        # Purchase order 3
        po3 = ProductTransform.objects.get(reg_no=333)
        po_count3 = ProductTransformCount.objects.get(reg_no=po3.reg_no)

        self.assertEqual(po3.increamental_id, 1000)
        self.assertEqual(po3.__str__(), f'DS{po3.increamental_id}')
        self.assertEqual(po_count3.increamental_id, 1000) 

        # Purchase order 4
        po4 = ProductTransform.objects.get(reg_no=444)
        po_count4 = ProductTransformCount.objects.get(reg_no=po4.reg_no)

        self.assertEqual(po4.increamental_id, 1001)
        self.assertEqual(po4.__str__(), f'DS{po4.increamental_id}')
        self.assertEqual(po_count4.increamental_id, 1001) 


        # ********************** Create purchase orders for the second time
        # Delete all purchase orders first
        ProductTransform.objects.all().delete()

        ##### Create 2 purchase orders for user 1
        self.create_a_product_assembly(self.user1, self.store, reg_no=555)
        self.create_a_product_assembly(employee_for_user1, self.store, reg_no=666)

        # Purchase order 1
        po1 = ProductTransform.objects.get(reg_no=555)
        po_count1 = ProductTransformCount.objects.get(reg_no=po1.reg_no)

        self.assertEqual(po1.increamental_id, 1003)
        self.assertEqual(po1.__str__(), f'DS{po1.increamental_id}')
        self.assertEqual(po_count1.increamental_id, 1003) 

        # Purchase order 2
        po2 = ProductTransform.objects.get(reg_no=666)
        po_count2 = ProductTransformCount.objects.get(reg_no=po2.reg_no)

        self.assertEqual(po2.increamental_id, 1004)
        self.assertEqual(po2.__str__(), f'DS{po2.increamental_id}')
        self.assertEqual(po_count2.increamental_id, 1004) 

        ##### Create 2 purchase orders for user 2
        self.create_a_product_assembly(self.user2, self.store, reg_no=777)
        self.create_a_product_assembly(employee_for_user2, self.store, reg_no=888)

        # Purchase order 3
        po3 = ProductTransform.objects.get(reg_no=777)
        po_count3 = ProductTransformCount.objects.get(reg_no=po3.reg_no)

        self.assertEqual(po3.increamental_id, 1002)
        self.assertEqual(po3.__str__(), f'DS{po3.increamental_id}')
        self.assertEqual(po_count3.increamental_id, 1002) 

        # Purchase order 4
        po4 = ProductTransform.objects.get(reg_no=888)
        po_count4 = ProductTransformCount.objects.get(reg_no=po4.reg_no)

        self.assertEqual(po4.increamental_id, 1003)
        self.assertEqual(po4.__str__(), f'DS{po4.increamental_id}')
        self.assertEqual(po_count4.increamental_id, 1003)

"""
=========================== ProductTransformLine ===================================
"""
class ProductTransformLineTestCase(TestCase, ProductTransformModelsMixin):
    
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

        # Create sugar product map
        self.create_product_maps_for_rice()
        self.create_product_maps_for_sugar()

        # Create disassembly
        self.create_a_product_assembly(self.user, self.store, reg_no=0)
        
    def test_inventory_count_line_fields_verbose_names(self):

        pdis = ProductTransformLine.objects.get(target_product__name="Sugar 1kg")

        self.assertEqual(pdis._meta.get_field('source_product_info').verbose_name,'source product info')
        self.assertEqual(pdis._meta.get_field('target_product_info').verbose_name,'target product info')
        self.assertEqual(pdis._meta.get_field('quantity').verbose_name,'quantity')
        self.assertEqual(pdis._meta.get_field('added_quantity').verbose_name,'added quantity')
        self.assertEqual(pdis._meta.get_field('cost').verbose_name,'cost')
        self.assertEqual(pdis._meta.get_field('amount').verbose_name,'amount')
        self.assertEqual(pdis._meta.get_field('is_reverse').verbose_name,'is reverse')
        self.assertEqual(pdis._meta.get_field('reg_no').verbose_name,'reg no')

        fields = ([field.name for field in ProductTransformLine._meta.fields])
        
        self.assertEqual(len(fields), 12)

    def test_model_fields_after_it_has_been_created(self):

        sugar_sack = Product.objects.get(name="Sugar 50kg Sack")
        sugar_1kg = Product.objects.get(name="Sugar 1kg")

        rice_sack = Product.objects.get(name="Rice 25kg Sack")
        rice_500g = Product.objects.get(name="Rice 500g")

        product_transform = ProductTransform.objects.get()

        # Model 1
        line1 = ProductTransformLine.objects.get(target_product__name="Sugar 1kg")
        
        self.assertEqual(line1.product_transform, product_transform)
        self.assertEqual(line1.source_product, sugar_sack)
        self.assertEqual(line1.target_product, sugar_1kg)
        self.assertEqual(
            line1.source_product_info, 
            {
                "name": line1.source_product.name,
                "reg_no": line1.source_product.reg_no,
            }
        )
        self.assertEqual(
            line1.target_product_info, 
            {
                "name": line1.target_product.name,
                "reg_no": line1.target_product.reg_no,
            }
        )
        self.assertEqual(line1.quantity, 1.00)
        self.assertEqual(line1.added_quantity, 50.00)
        self.assertEqual(line1.cost, 1100.00)
        self.assertEqual(line1.amount, 1100.00)
        self.assertTrue(line1.reg_no > 100000) # Check if we have a valid reg_no


        # Model 2
        line2 = ProductTransformLine.objects.get(target_product__name="Rice 500g")

        self.assertEqual(line2.product_transform, product_transform)
        self.assertEqual(line2.source_product, rice_sack)
        self.assertEqual(line2.target_product, rice_500g)
        self.assertEqual(
            line2.source_product_info, 
            {
                "name": line2.source_product.name,
                "reg_no": line2.source_product.reg_no,
            }
        )
        self.assertEqual(
            line2.target_product_info, 
            {
                "name": line2.target_product.name,
                "reg_no": line2.target_product.reg_no,
            }
        )
        self.assertEqual(line2.quantity, 2.00)
        self.assertEqual(line2.added_quantity, 100.00)
        self.assertEqual(line2.cost, 62.00)
        self.assertEqual(line2.amount, 124.00)
        self.assertTrue(line2.reg_no > 100000) # Check if we have a valid reg_no

    def test__str__method(self):

        product = Product.objects.get(name="Sugar 1kg")

        line1 = ProductTransformLine.objects.get(target_product=product)
        self.assertEqual(str(line1), product.name)

    def test_model_is_reverse_fields(self):

        self.create_a_reverse_product_assembly(self.user, self.store, reg_no=0)

        sugar_sack = Product.objects.get(name="Sugar 50kg Sack")
        sugar_1kg = Product.objects.get(name="Sugar 1kg")

        line1 = ProductTransformLine.objects.get(source_product=sugar_sack)
        line2 = ProductTransformLine.objects.get(source_product=sugar_1kg)

        self.assertEqual(line1.is_reverse, False)
        self.assertEqual(line2.is_reverse, True)
