import datetime
from decimal import Decimal

from django.utils import timezone

from accounts.tasks.local_midnight_task import local_midnight_tasks
from core.test_utils.custom_testcase import TestCase
from core.test_utils.create_user import create_new_user
from core.test_utils.create_store_models import (
    create_new_category, 
    create_new_store, 
    create_new_tax
)

from inventories.models.stock_models import StockLevel
from products.models import Product
from profiles.models import Profile
from inventories.models import InventoryValuation

class InventoryValuationModelsTestCase(TestCase):
    def setUp(self):

        #Create a user1
        self.user1 = create_new_user('john')
        self.user2 = create_new_user('jack')

        self.profile = Profile.objects.get(user__email='john@gmail.com')
        self.profile2 = Profile.objects.get(user__email='jack@gmail.com')

        #Create a store
        self.store1 = create_new_store(self.profile, 'Amboselli')
        self.store2 = create_new_store(self.profile, 'Dorobo')
        self.store3 = create_new_store(self.profile, 'Kilimanjaro')

        #Create a category
        self.category1 = create_new_category(self.profile, 'Beverages')
        self.category2 = create_new_category(self.profile, 'Electronics')

        #Create a tax
        self.tax1 = create_new_tax(self.profile, self.store1 ,'VAT 16', Decimal('7.00'))

        # Create 5 products
        self.create_products()
        self.create_stock_levels1()

        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=timezone.now()
        )

    def create_products(self):

        # Create 5 products
        self.product1 = Product.objects.create(
            profile=self.profile,
            tax=self.tax1,
            category=self.category1,
            name="Coca Cola",
            price=60,
            cost=45,
            sku="M-COCA-COLA-1",
            barcode="1234567890",
        )

        self.product2 = Product.objects.create(
            profile=self.profile,
            tax=self.tax1,
            category=self.category1,
            name="Fanta",
            price=62,
            cost=46,
            sku="M-FANTA-1",
            barcode="12345678901",
        )

        self.product3 = Product.objects.create(
            profile=self.profile,
            tax=self.tax1,
            category=self.category1,
            name="Sprite",
            price=64,
            cost=47,
            sku="M-SPRITE-1",
            barcode="1234567892",
        )

        self.product4 = Product.objects.create( 
            profile=self.profile,
            tax=self.tax1,
            category=self.category2,
            name="Radio",
            price=500,
            cost=350,
            sku="M-RADIO-1",
            barcode="1234567893",
        )

        self.product5 = Product.objects.create(
            profile=self.profile,
            tax=self.tax1,
            category=self.category2,
            name="TV",
            price=1000,
            cost=700,
            sku="M-TV-1",
            barcode="1234567894",
        )

    def create_stock_levels1(self):

        # Add stock to the products
        # Product 1
        StockLevel.objects.filter(
            product=self.product1, 
            store=self.store1
        ).update(units=100, price=60)

        self.product1_level1 = StockLevel.objects.get(
            product=self.product1,
            store=self.store1
        )

        self.product1_level2 = StockLevel.objects.filter(
            product=self.product1, 
            store=self.store2
        ).update(units=110, price=60)

        self.product1_level3 = StockLevel.objects.filter(
            product=self.product1, 
            store=self.store3
        ).update(units=120, price=60)

        # Product 2
        self.product2_level1 = StockLevel.objects.filter(
            product=self.product2, 
            store=self.store1
        ).update(units=200)

        self.product2_level2 = StockLevel.objects.filter(
            product=self.product2, 
            store=self.store2
        ).update(units=210)

        self.product2_level3 = StockLevel.objects.filter(
            product=self.product2, 
            store=self.store3
        ).update(units=220)

        # Product 3
        self.product3_level1 = StockLevel.objects.filter(
            product=self.product3, 
            store=self.store1
        ).update(units=300)

        self.product3_level2 = StockLevel.objects.filter(
            product=self.product3, 
            store=self.store2
        ).update(units=310)

        self.product3_level3 = StockLevel.objects.filter(
            product=self.product3, 
            store=self.store3
        ).update(units=320)

        # Product 4
        self.product4_level1 = StockLevel.objects.filter(
            product=self.product4, 
            store=self.store1
        ).update(units=400)

        self.product4_level2 = StockLevel.objects.filter(
            product=self.product4, 
            store=self.store2
        ).update(units=410)

        self.product4_level3 = StockLevel.objects.filter(
            product=self.product4, 
            store=self.store3
        ).update(units=420)

        # Product 5
        self.product5_level1 = StockLevel.objects.filter(
            product=self.product5, 
            store=self.store1
        ).update(units=500)

        self.product5_level2 = StockLevel.objects.filter(
            product=self.product5, 
            store=self.store2
        ).update(units=510)

        self.product5_level3 = StockLevel.objects.filter(
            product=self.product5, 
            store=self.store3
        ).update(units=520)  
    
    def test_inventory_valution_model(self):
        
        inventory_valuations = InventoryValuation.objects.all().order_by('id')

        self.assertEqual(len(inventory_valuations), 3)

        inventory_valuation1 = inventory_valuations[0]
        inventory_valuation2 = inventory_valuations[1]
        inventory_valuation3 = inventory_valuations[2]

        # Test inventory valuation 1
        self.assertEqual(inventory_valuation1.user, self.user1)
        self.assertEqual(inventory_valuation1.store.name, 'Amboselli')

        valuations_lines = inventory_valuation1.inventoryvaluationline_set.all().order_by('id')

        self.assertEqual(len(valuations_lines), 5)

        valuation_line1 = valuations_lines[0]
        valuation_line2 = valuations_lines[1]
        valuation_line3 = valuations_lines[2]
        valuation_line4 = valuations_lines[3]
        valuation_line5 = valuations_lines[4]

        self.assertEqual(valuation_line1.product.name, 'Coca Cola')

        self.assertEqual(valuation_line1.price, self.product1_level1.price)
        self.assertEqual(valuation_line1.cost, self.product1.cost)
        self.assertEqual(valuation_line1.units, 100)
        self.assertEqual(valuation_line1.barcode, self.product1.barcode)
        self.assertEqual(valuation_line1.sku, self.product1.sku)
        self.assertEqual(valuation_line1.category_name, self.product1.category.name)
        self.assertEqual(valuation_line1.is_sellable, True)
        self.assertEqual(valuation_line1.inventory_value, Decimal('4500.00'))
        self.assertEqual(valuation_line1.retail_value, Decimal('6000.00'))
        self.assertEqual(valuation_line1.potential_profit, Decimal('1500.00'))
        self.assertEqual(valuation_line1.margin, Decimal('25.00'))

        self.assertEqual(valuation_line2.product.name, 'Fanta')
        self.assertEqual(valuation_line2.cost, self.product2.cost)
        self.assertEqual(valuation_line2.units, 200)
        self.assertEqual(valuation_line2.barcode, self.product2.barcode)
        self.assertEqual(valuation_line2.sku, self.product2.sku)
        self.assertEqual(valuation_line2.category_name, self.product2.category.name)
        self.assertEqual(valuation_line2.is_sellable, True)
        self.assertEqual(valuation_line2.inventory_value, Decimal('9200.00'))
        self.assertEqual(valuation_line2.retail_value, Decimal('12400.00'))
        self.assertEqual(valuation_line2.potential_profit, Decimal('3200.00'))
        self.assertEqual(valuation_line2.margin, Decimal('25.81'))

        self.assertEqual(valuation_line3.product.name, 'Sprite')
        self.assertEqual(valuation_line3.cost, self.product3.cost)
        self.assertEqual(valuation_line3.units, 300)
        self.assertEqual(valuation_line3.barcode, self.product3.barcode)
        self.assertEqual(valuation_line3.sku, self.product3.sku)
        self.assertEqual(valuation_line3.category_name, self.product3.category.name)
        self.assertEqual(valuation_line3.is_sellable, True)
        self.assertEqual(valuation_line3.inventory_value, Decimal('14100.00'))
        self.assertEqual(valuation_line3.retail_value, Decimal('19200.00'))
        self.assertEqual(valuation_line3.potential_profit, Decimal('5100.00'))
        self.assertEqual(valuation_line3.margin, Decimal('26.56'))

        self.assertEqual(valuation_line4.product.name, 'Radio')
        self.assertEqual(valuation_line4.cost, self.product4.cost)
        self.assertEqual(valuation_line4.units, 400)
        self.assertEqual(valuation_line4.barcode, self.product4.barcode)
        self.assertEqual(valuation_line4.sku, self.product4.sku)
        self.assertEqual(valuation_line4.category_name, self.product4.category.name)
        self.assertEqual(valuation_line4.is_sellable, True)
        self.assertEqual(valuation_line4.inventory_value, Decimal('140000.00'))
        self.assertEqual(valuation_line4.retail_value, Decimal('200000.00'))
        self.assertEqual(valuation_line4.potential_profit, Decimal('60000.00'))
        self.assertEqual(valuation_line4.margin, Decimal('30.00'))

        self.assertEqual(valuation_line5.product.name, 'TV')
        self.assertEqual(valuation_line5.cost, self.product5.cost)
        self.assertEqual(valuation_line5.units, 500)
        self.assertEqual(valuation_line5.barcode, self.product5.barcode)
        self.assertEqual(valuation_line5.sku, self.product5.sku)
        self.assertEqual(valuation_line5.category_name, self.product5.category.name)
        self.assertEqual(valuation_line5.is_sellable, True)
        self.assertEqual(valuation_line5.inventory_value, Decimal('350000.00'))
        self.assertEqual(valuation_line5.retail_value, Decimal('500000.00'))
        self.assertEqual(valuation_line5.potential_profit, Decimal('150000.00'))
        self.assertEqual(valuation_line5.margin, Decimal('30.00'))


        # Test inventory valuation 2
        self.assertEqual(inventory_valuation2.user, self.user1)
        self.assertEqual(inventory_valuation2.store.name, 'Dorobo')

        valuations_lines = inventory_valuation2.inventoryvaluationline_set.all().order_by('id')

        self.assertEqual(len(valuations_lines), 5)

        valuation_line1 = valuations_lines[0]
        valuation_line2 = valuations_lines[1]
        valuation_line3 = valuations_lines[2]
        valuation_line4 = valuations_lines[3]
        valuation_line5 = valuations_lines[4]

        self.assertEqual(valuation_line1.product.name, 'Coca Cola')
        self.assertEqual(valuation_line1.cost, self.product1.cost)
        self.assertEqual(valuation_line1.units, 110)
        self.assertEqual(valuation_line1.barcode, self.product1.barcode)
        self.assertEqual(valuation_line1.sku, self.product1.sku)
        self.assertEqual(valuation_line1.category_name, self.product1.category.name)
        self.assertEqual(valuation_line1.is_sellable, True)
        self.assertEqual(valuation_line1.sku, self.product1.sku)
        self.assertEqual(valuation_line1.category_name, self.product1.category.name)
        self.assertEqual(valuation_line1.is_sellable, True)
        self.assertEqual(valuation_line1.inventory_value, Decimal('4950.00'))
        self.assertEqual(valuation_line1.retail_value, Decimal('6600.00'))
        self.assertEqual(valuation_line1.potential_profit, Decimal('1650.00'))
        self.assertEqual(valuation_line1.margin, Decimal('25.00'))

        self.assertEqual(valuation_line2.product.name, 'Fanta')
        self.assertEqual(valuation_line2.cost, self.product2.cost)
        self.assertEqual(valuation_line2.units, 210)
        self.assertEqual(valuation_line2.barcode, self.product2.barcode)
        self.assertEqual(valuation_line2.sku, self.product2.sku)
        self.assertEqual(valuation_line2.category_name, self.product2.category.name)
        self.assertEqual(valuation_line2.is_sellable, True)
        self.assertEqual(valuation_line2.inventory_value, Decimal('9660.00'))
        self.assertEqual(valuation_line2.retail_value, Decimal('13020.00'))
        self.assertEqual(valuation_line2.potential_profit, Decimal('3360.00'))
        self.assertEqual(valuation_line2.margin, Decimal('25.81'))

        self.assertEqual(valuation_line3.product.name, 'Sprite')
        self.assertEqual(valuation_line3.cost, self.product3.cost)
        self.assertEqual(valuation_line3.units, 310)
        self.assertEqual(valuation_line3.barcode, self.product3.barcode)
        self.assertEqual(valuation_line3.sku, self.product3.sku)
        self.assertEqual(valuation_line3.category_name, self.product3.category.name)
        self.assertEqual(valuation_line3.is_sellable, True)
        self.assertEqual(valuation_line3.inventory_value, Decimal('14570.00'))
        self.assertEqual(valuation_line3.retail_value, Decimal('19840.00'))
        self.assertEqual(valuation_line3.potential_profit, Decimal('5270.00'))
        self.assertEqual(valuation_line3.margin, Decimal('26.56'))

        self.assertEqual(valuation_line4.product.name, 'Radio')
        self.assertEqual(valuation_line4.cost, self.product4.cost)
        self.assertEqual(valuation_line4.units, 410)
        self.assertEqual(valuation_line4.barcode, self.product4.barcode)
        self.assertEqual(valuation_line4.sku, self.product4.sku)
        self.assertEqual(valuation_line4.category_name, self.product4.category.name)
        self.assertEqual(valuation_line4.is_sellable, True)
        self.assertEqual(valuation_line4.inventory_value, Decimal('143500.00'))
        self.assertEqual(valuation_line4.retail_value, Decimal('205000.00'))
        self.assertEqual(valuation_line4.potential_profit, Decimal('61500.00'))
        self.assertEqual(valuation_line4.margin, Decimal('30.00'))

        self.assertEqual(valuation_line5.product.name, 'TV')
        self.assertEqual(valuation_line5.cost, self.product5.cost)
        self.assertEqual(valuation_line5.units, 510)
        self.assertEqual(valuation_line5.barcode, self.product5.barcode)
        self.assertEqual(valuation_line5.sku, self.product5.sku)
        self.assertEqual(valuation_line5.category_name, self.product5.category.name)
        self.assertEqual(valuation_line5.is_sellable, True)
        self.assertEqual(valuation_line5.inventory_value, Decimal('357000.00'))
        self.assertEqual(valuation_line5.retail_value, Decimal('510000.00'))
        self.assertEqual(valuation_line5.potential_profit, Decimal('153000.00'))
        self.assertEqual(valuation_line5.margin, Decimal('30.00'))


        # Test inventory valuation 3
        self.assertEqual(inventory_valuation3.user, self.user1)
        self.assertEqual(inventory_valuation3.store.name, 'Kilimanjaro')

        valuations_lines = inventory_valuation3.inventoryvaluationline_set.all().order_by('id')

        self.assertEqual(len(valuations_lines), 5)

        valuation_line1 = valuations_lines[0]
        valuation_line2 = valuations_lines[1]
        valuation_line3 = valuations_lines[2]
        valuation_line4 = valuations_lines[3]
        valuation_line5 = valuations_lines[4]

        self.assertEqual(valuation_line1.product.name, 'Coca Cola')
        self.assertEqual(valuation_line1.cost, self.product1.cost)
        self.assertEqual(valuation_line1.units, 120)
        self.assertEqual(valuation_line1.barcode, self.product1.barcode)
        self.assertEqual(valuation_line1.sku, self.product1.sku)
        self.assertEqual(valuation_line1.category_name, self.product1.category.name)
        self.assertEqual(valuation_line1.is_sellable, True)
        self.assertEqual(valuation_line1.inventory_value, Decimal('5400.00'))
        self.assertEqual(valuation_line1.retail_value, Decimal('7200.00'))
        self.assertEqual(valuation_line1.potential_profit, Decimal('1800.00'))
        self.assertEqual(valuation_line1.margin, Decimal('25.00'))

        self.assertEqual(valuation_line2.product.name, 'Fanta')
        self.assertEqual(valuation_line2.cost, self.product2.cost)
        self.assertEqual(valuation_line2.units, 220)
        self.assertEqual(valuation_line2.barcode, self.product2.barcode)
        self.assertEqual(valuation_line2.sku, self.product2.sku)
        self.assertEqual(valuation_line2.category_name, self.product2.category.name)
        self.assertEqual(valuation_line2.is_sellable, True)
        self.assertEqual(valuation_line2.inventory_value, Decimal('10120.00'))
        self.assertEqual(valuation_line2.retail_value, Decimal('13640.00'))
        self.assertEqual(valuation_line2.potential_profit, Decimal('3520.00'))
        self.assertEqual(valuation_line2.margin, Decimal('25.81'))

        self.assertEqual(valuation_line3.product.name, 'Sprite')
        self.assertEqual(valuation_line3.cost, self.product3.cost)
        self.assertEqual(valuation_line3.units, 320)
        self.assertEqual(valuation_line3.barcode, self.product3.barcode)
        self.assertEqual(valuation_line3.sku, self.product3.sku)
        self.assertEqual(valuation_line3.category_name, self.product3.category.name)
        self.assertEqual(valuation_line3.is_sellable, True)
        self.assertEqual(valuation_line3.inventory_value, Decimal('15040.00'))
        self.assertEqual(valuation_line3.retail_value, Decimal('20480.00'))
        self.assertEqual(valuation_line3.potential_profit, Decimal('5440.00'))
        self.assertEqual(valuation_line3.margin, Decimal('26.56'))        

        self.assertEqual(valuation_line4.product.name, 'Radio')
        self.assertEqual(valuation_line4.cost, self.product4.cost)
        self.assertEqual(valuation_line4.units, 420)
        self.assertEqual(valuation_line4.barcode, self.product4.barcode)
        self.assertEqual(valuation_line4.sku, self.product4.sku)
        self.assertEqual(valuation_line4.category_name, self.product4.category.name)
        self.assertEqual(valuation_line4.is_sellable, True)
        self.assertEqual(valuation_line4.inventory_value, Decimal('147000.00'))
        self.assertEqual(valuation_line4.retail_value, Decimal('210000.00'))
        self.assertEqual(valuation_line4.potential_profit, Decimal('63000.00'))
        self.assertEqual(valuation_line4.margin, Decimal('30.00'))

        self.assertEqual(valuation_line5.product.name, 'TV')
        self.assertEqual(valuation_line5.cost, self.product5.cost)
        self.assertEqual(valuation_line5.units, 520)
        self.assertEqual(valuation_line5.barcode, self.product5.barcode)
        self.assertEqual(valuation_line5.sku, self.product5.sku)
        self.assertEqual(valuation_line5.category_name, self.product5.category.name)
        self.assertEqual(valuation_line5.is_sellable, True)
        self.assertEqual(valuation_line5.inventory_value, Decimal('364000.00'))
        self.assertEqual(valuation_line5.retail_value, Decimal('520000.00'))
        self.assertEqual(valuation_line5.potential_profit, Decimal('156000.00'))
        self.assertEqual(valuation_line5.margin, Decimal('30.00'))

    def test_get_inventory_valuation_data_method_is_filtering_correctly(self):

        start_date = timezone.now().strftime("%Y-%m-%d")
        
        ######## Filter store 1
        inventory_valuation_data = InventoryValuation.get_inventory_valuation_data(
            profile=self.profile,
            request_user=self.user1,
            date=start_date,
            stores_reg_nos=[self.store1.reg_no,]
        )

        results = {
            'total_inventory_data': {
                'total_inventory_value': '517800.00', 
                'total_retail_value': '737600.00', 
                'total_potential_profit': '219800.00', 
                'margin': '29.80'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'cost': '45.00', 
                    'in_stock': '100.00', 
                    'margin': '25.00', 
                    'inventory_value': '4500.00', 
                    'retail_value': '6000.00', 
                    'potential_profit': '1500.00'
                }, 
                {
                    'name': 'Fanta', 
                    'cost': '46.00', 
                    'in_stock': '200.00', 
                    'margin': '25.81', 
                    'inventory_value': '9200.00', 
                    'retail_value': '12400.00', 
                    'potential_profit': '3200.00'
                }, 
                {
                    'name': 'Radio', 
                    'cost': '350.00', 
                    'in_stock': '400.00', 
                    'margin': '30.00', 
                    'inventory_value': '140000.00', 
                    'retail_value': '200000.00', 
                    'potential_profit': '60000.00'
                }, 
                {
                    'name': 'Sprite', 
                    'cost': '47.00', 
                    'in_stock': '300.00', 
                    'margin': '26.56', 
                    'inventory_value': '14100.00', 
                    'retail_value': '19200.00', 
                    'potential_profit': '5100.00'
                }, 
                {
                    'name': 'TV', 
                    'cost': '700.00', 
                    'in_stock': '500.00', 
                    'margin': '30.00', 
                    'inventory_value': '350000.00', 
                    'retail_value': '500000.00', 
                    'potential_profit': '150000.00'
                }
            ]
        }

        self.assertEqual(inventory_valuation_data, results)

        ######## Filter store 2
        inventory_valuation_data = InventoryValuation.get_inventory_valuation_data(
            profile=self.profile,
            request_user=self.user1,
            date=start_date,
            stores_reg_nos=[self.store2.reg_no,]
        )

        results = {
            'total_inventory_data': {
                'total_inventory_value': '529680.00', 
                'total_retail_value': '754460.00', 
                'total_potential_profit': '224780.00', 
                'margin': '29.79'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'cost': '45.00', 
                    'in_stock': '110.00', 
                    'margin': '25.00', 
                    'inventory_value': '4950.00', 
                    'retail_value': '6600.00', 
                    'potential_profit': '1650.00'
                }, 
                {
                    'name': 'Fanta', 
                    'cost': '46.00', 
                    'in_stock': '210.00', 
                    'margin': '25.81', 
                    'inventory_value': '9660.00', 
                    'retail_value': '13020.00', 
                    'potential_profit': '3360.00'
                }, 
                {
                    'name': 'Radio', 
                    'cost': '350.00', 
                    'in_stock': '410.00', 
                    'margin': '30.00', 
                    'inventory_value': '143500.00', 
                    'retail_value': '205000.00', 
                    'potential_profit': '61500.00'
                }, 
                {
                    'name': 'Sprite', 
                    'cost': '47.00', 
                    'in_stock': '310.00', 
                    'margin': '26.56', 
                    'inventory_value': '14570.00', 
                    'retail_value': '19840.00', 
                    'potential_profit': '5270.00'
                }, 
                {
                    'name': 'TV', 
                    'cost': '700.00', 
                    'in_stock': '510.00', 
                    'margin': '30.00', 
                    'inventory_value': '357000.00', 
                    'retail_value': '510000.00', 
                    'potential_profit': '153000.00'
                }
            ]
        }

        self.assertEqual(inventory_valuation_data, results)

        ######## Filter store 3
        inventory_valuation_data = InventoryValuation.get_inventory_valuation_data(
            profile=self.profile,
            request_user=self.user1,
            date=start_date,
            stores_reg_nos=[self.store3.reg_no,]
        )

        results = {
            'total_inventory_data': {
                'total_inventory_value': '541560.00', 
                'total_retail_value': '771320.00', 
                'total_potential_profit': '229760.00', 
                'margin': '29.79'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'cost': '45.00', 
                    'in_stock': '120.00', 
                    'margin': '25.00', 
                    'inventory_value': '5400.00', 
                    'retail_value': '7200.00', 
                    'potential_profit': '1800.00'
                }, 
                {
                    'name': 'Fanta', 
                    'cost': '46.00', 
                    'in_stock': '220.00', 
                    'margin': '25.81', 
                    'inventory_value': '10120.00', 
                    'retail_value': '13640.00', 
                    'potential_profit': '3520.00'
                }, 
                {
                    'name': 'Radio', 
                    'cost': '350.00', 
                    'in_stock': '420.00', 
                    'margin': '30.00', 
                    'inventory_value': '147000.00', 
                    'retail_value': '210000.00', 
                    'potential_profit': '63000.00'
                }, 
                {
                    'name': 'Sprite', 
                    'cost': '47.00', 
                    'in_stock': '320.00', 
                    'margin': '26.56', 
                    'inventory_value': '15040.00', 
                    'retail_value': '20480.00', 
                    'potential_profit': '5440.00'
                }, 
                {
                    'name': 'TV', 
                    'cost': '700.00', 
                    'in_stock': '520.00', 
                    'margin': '30.00', 
                    'inventory_value': '364000.00', 
                    'retail_value': '520000.00', 
                    'potential_profit': '156000.00'
                }
            ]
        }

        self.assertEqual(inventory_valuation_data, results)
        
        ######## Filter store 1, 2 and 3
        inventory_valuation_data = InventoryValuation.get_inventory_valuation_data(
            profile=self.profile,
            request_user=self.user1,
            date=start_date,
            stores_reg_nos=[self.store1.reg_no, self.store2.reg_no, self.store3.reg_no]
        )

        results = {
            'total_inventory_data': {
                'total_inventory_value': '1589040.00', 
                'total_retail_value': '2263380.00', 
                'total_potential_profit': '674340.00', 
                'margin': '29.79'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'cost': '45.00', 
                    'in_stock': '330.00', 
                    'margin': '25.00', 
                    'inventory_value': '14850.00', 
                    'retail_value': '19800.00', 
                    'potential_profit': '4950.00'
                }, 
                {
                    'name': 'Fanta', 
                    'cost': '46.00', 
                    'in_stock': '630.00', 
                    'margin': '25.81', 
                    'inventory_value': '28980.00', 
                    'retail_value': '39060.00', 
                    'potential_profit': '10080.00'
                }, 
                {
                    'name': 'Radio', 
                    'cost': '350.00', 
                    'in_stock': '1230.00', 
                    'margin': '30.00', 
                    'inventory_value': '430500.00', 
                    'retail_value': '615000.00', 
                    'potential_profit': '184500.00'
                }, 
                {
                    'name': 'Sprite', 
                    'cost': '47.00', 
                    'in_stock': '930.00', 
                    'margin': '26.56', 
                    'inventory_value': '43710.00', 
                    'retail_value': '59520.00', 
                    'potential_profit': '15810.00'
                }, 
                {
                    'name': 'TV', 
                    'cost': '700.00', 
                    'in_stock': '1530.00', 
                    'margin': '30.00', 
                    'inventory_value': '1071000.00', 
                    'retail_value': '1530000.00', 
                    'potential_profit': '459000.00'
                }
            ]
        }

        self.assertEqual(inventory_valuation_data, results)

    def test_get_inventory_valuation_data_method_can_filter_date(self):

        today = timezone.now()
        yesterday = today - datetime.timedelta(days=1)
        yesterday2 = today - datetime.timedelta(days=2)

        today_str = today.strftime("%Y-%m-%d")
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        yesterday2_str = yesterday2.strftime("%Y-%m-%d")

        inventory_valuations = InventoryValuation.objects.all().order_by('id')

        self.assertEqual(len(inventory_valuations), 3)

        inventory_valuation1 = inventory_valuations[0]
        inventory_valuation2 = inventory_valuations[1]
        inventory_valuation3 = inventory_valuations[2]

        inventory_valuation1.created_date = today
        inventory_valuation1.save()

        inventory_valuation2.created_date = yesterday
        inventory_valuation2.save()

        inventory_valuation3.created_date = yesterday2
        inventory_valuation3.save()

        # Test filtering by today
        inventory_valuation_data = InventoryValuation.get_inventory_valuation_data(
            profile=self.profile,
            request_user=self.user1,
            date=today_str,
            stores_reg_nos=[self.store1.reg_no, self.store2.reg_no, self.store3.reg_no]
        )

        results = {
            'total_inventory_data': {
                'total_inventory_value': '1589040.00', 
                'total_retail_value': '2263380.00', 
                'total_potential_profit': '674340.00', 
                'margin': '29.79'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'in_stock': '330.00', 
                    'cost': '45.00', 
                    'inventory_value': '14850.00', 
                    'retail_value': '19800.00', 
                    'potential_profit': '4950.00', 
                    'margin': '25.00'
                }, 
                {
                    'name': 'Fanta', 
                    'in_stock': '630.00', 
                    'cost': '46.00', 
                    'inventory_value': '28980.00', 
                    'retail_value': '39060.00', 
                    'potential_profit': '10080.00', 
                    'margin': '25.81'
                }, 
                {
                    'name': 'Radio', 
                    'in_stock': '1230.00', 
                    'cost': '350.00', 
                    'inventory_value': '430500.00', 
                    'retail_value': '615000.00', 
                    'potential_profit': '184500.00', 
                    'margin': '30.00'
                }, 
                {
                    'name': 'Sprite', 
                    'in_stock': '930.00', 
                    'cost': '47.00', 
                    'inventory_value': '43710.00', 
                    'retail_value': '59520.00', 
                    'potential_profit': '15810.00', 
                    'margin': '26.56'
                }, 
                {
                    'name': 'TV', 
                    'in_stock': '1530.00', 
                    'cost': '700.00', 
                    'inventory_value': '1071000.00', 
                    'retail_value': '1530000.00', 
                    'potential_profit': '459000.00', 
                    'margin': '30.00'
                }
            ], 
        }

        self.assertEqual(inventory_valuation_data, results)

        # Test filtering by yesterday
        inventory_valuation_data = InventoryValuation.get_inventory_valuation_data(
            profile=self.profile,
            request_user=self.user1,
            date=yesterday_str,
            stores_reg_nos=[self.store1.reg_no, self.store2.reg_no, self.store3.reg_no]
        )

        results = {
            'total_inventory_data': {
                'total_inventory_value': '529680.00', 
                'total_retail_value': '754460.00', 
                'total_potential_profit': '224780.00', 
                'margin': '29.79'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'cost': '45.00', 
                    'in_stock': '110.00', 
                    'margin': '25.00', 
                    'inventory_value': '4950.00', 
                    'retail_value': '6600.00', 
                    'potential_profit': '1650.00'
                }, 
                {
                    'name': 'Fanta', 
                    'cost': '46.00', 
                    'in_stock': '210.00', 
                    'margin': '25.81', 
                    'inventory_value': '9660.00', 
                    'retail_value': '13020.00', 
                    'potential_profit': '3360.00'
                }, 
                {
                    'name': 'Radio', 
                    'cost': '350.00', 
                    'in_stock': '410.00', 
                    'margin': '30.00', 
                    'inventory_value': '143500.00', 
                    'retail_value': '205000.00', 
                    'potential_profit': '61500.00'
                }, 
                {
                    'name': 'Sprite', 
                    'cost': '47.00', 
                    'in_stock': '310.00', 
                    'margin': '26.56', 
                    'inventory_value': '14570.00', 
                    'retail_value': '19840.00', 
                    'potential_profit': '5270.00'
                }, 
                {
                    'name': 'TV', 
                    'cost': '700.00', 
                    'in_stock': '510.00', 
                    'margin': '30.00', 
                    'inventory_value': '357000.00', 
                    'retail_value': '510000.00', 
                    'potential_profit': '153000.00'
                }
            ]
        }

        self.assertEqual(inventory_valuation_data, results)

        # Test filtering by yesterday2
        inventory_valuation_data = InventoryValuation.get_inventory_valuation_data(
            profile=self.profile,
            request_user=self.user1,
            date=yesterday2_str,
            stores_reg_nos=[self.store1.reg_no, self.store2.reg_no, self.store3.reg_no]
        )

        results = {
            'total_inventory_data': {
                'total_inventory_value': '541560.00', 
                'total_retail_value': '771320.00', 
                'total_potential_profit': '229760.00', 
                'margin': '29.79'
            }, 
            'product_data': [
                {
                    'name': 'Coca Cola', 
                    'cost': '45.00', 
                    'in_stock': '120.00', 
                    'margin': '25.00', 
                    'inventory_value': '5400.00', 
                    'retail_value': '7200.00', 
                    'potential_profit': '1800.00'
                }, 
                {
                    'name': 'Fanta', 
                    'cost': '46.00', 
                    'in_stock': '220.00', 
                    'margin': '25.81', 
                    'inventory_value': '10120.00', 
                    'retail_value': '13640.00', 
                    'potential_profit': '3520.00'
                }, 
                {
                    'name': 'Radio', 
                    'cost': '350.00', 
                    'in_stock': '420.00', 
                    'margin': '30.00', 
                    'inventory_value': '147000.00', 
                    'retail_value': '210000.00', 
                    'potential_profit': '63000.00'
                }, 
                {
                    'name': 'Sprite', 
                    'cost': '47.00', 
                    'in_stock': '320.00', 
                    'margin': '26.56', 
                    'inventory_value': '15040.00', 
                    'retail_value': '20480.00', 
                    'potential_profit': '5440.00'
                }, 
                {
                    'name': 'TV', 
                    'cost': '700.00', 
                    'in_stock': '520.00', 
                    'margin': '30.00', 
                    'inventory_value': '364000.00', 
                    'retail_value': '520000.00', 
                    'potential_profit': '156000.00'
                }
            ]
        }

        self.assertEqual(inventory_valuation_data, results)
    
    def test_get_inventory_product_data_for_short_report(self):
        
        # Update product prices to make sure we don't get the default prices
        Product.objects.filter(name="Coca Cola").update(price=70)
        Product.objects.filter(name="Fanta").update(price=72)
        Product.objects.filter(name="Sprite").update(price=74)
        Product.objects.filter(name="Radio").update(price=550)
        Product.objects.filter(name="TV").update(price=1100)

        start_date = timezone.now().strftime("%Y-%m-%d")
        
        inventory_valuation_data = InventoryValuation.get_inventory_product_data(
            profile=self.profile,
            date=start_date,
            long_report=False
        )

        results = {
            'stores': ['Amboselli', 'Dorobo', 'Kilimanjaro'],
            'product_data': {
                "Coca Cola": [
                    {
                        "units": "100.00",
                    },
                    {
                        "units": "110.00",
                    },
                    {
                        "units": "120.00"
                    }
                ],
                "Fanta": [
                    {
                        "units": "200.00",
                    },
                    {
                        "units": "210.00",
                    },
                    {
                        "units": "220.00",
                    }
                ],
                "Sprite": [
                    {
                        "units": "300.00"
                    },
                    {
                        "units": "310.00",
                    },
                    {
                        "units": "320.00",
                    }
                ],
                "Radio": [
                    {
                        "units": "400.00",
                    },
                    {
                        "units": "410.00",
                    },
                    {
                        "units": "420.00",
                    }
                ],
                "TV": [
                    {
                        "units": "500.00",
                    },
                    {
                        "units": "510.00",
                    },
                    {
                        "units": "520.00",
                    }
                ]
            },
            'product_units_agg_data': {
                "Coca Cola": '330',
                "Fanta": '630',
                "Sprite": '930',
                "Radio": '1230',
                "TV": '1530'
            },
        }

        self.assertEqual(inventory_valuation_data, results)
    
    def test_get_inventory_product_data_method_can_filter_date_for_short_report(self):

        today = timezone.now()
        yesterday = today - datetime.timedelta(days=1)
        yesterday2 = today - datetime.timedelta(days=2)

        today_str = today.strftime("%Y-%m-%d")
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        yesterday2_str = yesterday2.strftime("%Y-%m-%d")

        inventory_valuations = InventoryValuation.objects.all().order_by('id')

        self.assertEqual(len(inventory_valuations), 3)

        inventory_valuation1 = inventory_valuations[0]
        inventory_valuation2 = inventory_valuations[1]
        inventory_valuation3 = inventory_valuations[2]

        inventory_valuation1.created_date = today
        inventory_valuation1.save()

        inventory_valuation2.created_date = yesterday
        inventory_valuation2.save()

        inventory_valuation3.created_date = yesterday2
        inventory_valuation3.save()

        ######### Filter by today
        inventory_valuation_data = InventoryValuation.get_inventory_product_data(
            profile=self.profile,
            date=today_str,
            long_report=False
        )

        results = {
            'stores': ['Amboselli', 'Dorobo', 'Kilimanjaro'],
            'product_data': {
                "Coca Cola": [
                    {
                        "units": "100.00",
                    },
                    {
                        "units": "110.00",
                    },
                    {
                        "units": "120.00",
                    }
                ],
                "Fanta": [
                    {
                        "units": "200.00",
                    },
                    {
                        "units": "210.00",
                    },
                    {
                        "units": "220.00",
                    }
                ],
                "Sprite": [
                    {
                        "units": "300.00",
                    },
                    {
                        "units": "310.00",
                    },
                    {
                        "units": "320.00",
                    }
                ],
                "Radio": [
                    {
                        "units": "400.00",
                    },
                    {
                        "units": "410.00",
                    },
                    {
                        "units": "420.00",
                    }
                ],
                "TV": [
                    {
                        "units": "500.00",
                    },
                    {
                        "units": "510.00",
                    },
                    {
                        "units": "520.00",
                    }
                ]
            },
            'product_units_agg_data': {
                "Coca Cola": '330',
                "Fanta": '630',
                "Sprite": '930',
                "Radio": '1230',
                "TV": '1530'
            },
        }

        self.assertEqual(inventory_valuation_data, results)


        ######### Filter by yesterday
        inventory_valuation_data = InventoryValuation.get_inventory_product_data(
            profile=self.profile,
            date=yesterday_str,
            long_report=False
        )

        results = {
            'stores': ['Dorobo',],
            'product_data': {
                "Coca Cola": [
                    {
                        "units": "110.00",
                    }
                ],
                "Fanta": [
                    {
                        "units": "210.00",
                    }
                ],
                "Sprite": [
                    {
                        "units": "310.00",
                    }
                ],
                "Radio": [
                    {
                        "units": "410.00",
                    }
                ],
                "TV": [
                    {
                        "units": "510.00",
                    }
                ]
            },
            'product_units_agg_data': {
                "Coca Cola": '110',
                "Fanta": '210',
                "Sprite": '310',
                "Radio": '410',
                "TV": '510'
            },
        }

        self.assertEqual(inventory_valuation_data, results)

        ######### Filter by yesterday2
        inventory_valuation_data = InventoryValuation.get_inventory_product_data(
            profile=self.profile,
            date=yesterday2_str,
            long_report=False
        )

        results = {
            'stores': ['Kilimanjaro'],
            'product_data': {
                "Coca Cola": [
                    {
                        "units": "120.00",
                    }
                ],
                "Fanta": [
                    {
                        "units": "220.00",
                    }
                ],
                "Sprite": [
                    {
                        "units": "320.00",
                    }
                ],
                "Radio": [
                    {
                        "units": "420.00",
                    }
                ],
                "TV": [
                    {
                        "units": "520.00",
                    }
                ]
            },
            'product_units_agg_data': {
                "Coca Cola": '120',
                "Fanta": '220',
                "Sprite": '320',
                "Radio": '420',
                "TV": '520'
            },
        }

        self.assertEqual(inventory_valuation_data, results)

    def test_get_inventory_product_data_for_long_report(self):
        
        # Update product prices to make sure we don't get the default prices
        Product.objects.filter(name="Coca Cola").update(price=70)
        Product.objects.filter(name="Fanta").update(price=72)
        Product.objects.filter(name="Sprite").update(price=74)
        Product.objects.filter(name="Radio").update(price=550)
        Product.objects.filter(name="TV").update(price=1100)

        start_date = timezone.now().strftime("%Y-%m-%d")
        
        inventory_valuation_data = InventoryValuation.get_inventory_product_data(
            profile=self.profile,
            date=start_date
        )

        results = {
            'stores': ['Amboselli', 'Dorobo', 'Kilimanjaro'],
            'product_data': {
                "Coca Cola": [
                    {
                        "price": "60.00",
                        "cost": "45.00",
                        "units": "100.00",
                        "is_sellable": True,
                        "barcode": "1234567890",
                        "sku": "M-COCA-COLA-1",
                        "category_name": "Beverages"
                    },
                    {
                        "price": "60.00",
                        "cost": "45.00",
                        "units": "110.00",
                        "is_sellable": True,
                        "barcode": "1234567890",
                        "sku": "M-COCA-COLA-1",
                        "category_name": "Beverages"
                    },
                    {
                        "price": "60.00",
                        "cost": "45.00",
                        "units": "120.00",
                        "is_sellable": True,
                        "barcode": "1234567890",
                        "sku": "M-COCA-COLA-1",
                        "category_name": "Beverages"
                    }
                ],
                "Fanta": [
                    {
                        "price": "62.00",
                        "cost": "46.00",
                        "units": "200.00",
                        "is_sellable": True,
                        "barcode": "12345678901",
                        "sku": "M-FANTA-1",
                        "category_name": "Beverages"
                    },
                    {
                        "price": "62.00",
                        "cost": "46.00",
                        "units": "210.00",
                        "is_sellable": True,
                        "barcode": "12345678901",
                        "sku": "M-FANTA-1",
                        "category_name": "Beverages"
                    },
                    {
                        "price": "62.00",
                        "cost": "46.00",
                        "units": "220.00",
                        "is_sellable": True,
                        "barcode": "12345678901",
                        "sku": "M-FANTA-1",
                        "category_name": "Beverages"
                    }
                ],
                "Sprite": [
                    {
                        "price": "64.00",
                        "cost": "47.00",
                        "units": "300.00",
                        "is_sellable": True,
                        "barcode": "1234567892",
                        "sku": "M-SPRITE-1",
                        "category_name": "Beverages"
                    },
                    {
                        "price": "64.00",
                        "cost": "47.00",
                        "units": "310.00",
                        "is_sellable": True,
                        "barcode": "1234567892",
                        "sku": "M-SPRITE-1",
                        "category_name": "Beverages"
                    },
                    {
                        "price": "64.00",
                        "cost": "47.00",
                        "units": "320.00",
                        "is_sellable": True,
                        "barcode": "1234567892",
                        "sku": "M-SPRITE-1",
                        "category_name": "Beverages"
                    }
                ],
                "Radio": [
                    {
                        "price": "500.00",
                        "cost": "350.00",
                        "units": "400.00",
                        "is_sellable": True,
                        "barcode": "1234567893",
                        "sku": "M-RADIO-1",
                        "category_name": "Electronics"
                    },
                    {
                        "price": "500.00",
                        "cost": "350.00",
                        "units": "410.00",
                        "is_sellable": True,
                        "barcode": "1234567893",
                        "sku": "M-RADIO-1",
                        "category_name": "Electronics"
                    },
                    {
                        "price": "500.00",
                        "cost": "350.00",
                        "units": "420.00",
                        "is_sellable": True,
                        "barcode": "1234567893",
                        "sku": "M-RADIO-1",
                        "category_name": "Electronics"
                    }
                ],
                "TV": [
                    {
                        "price": "1000.00",
                        "cost": "700.00",
                        "units": "500.00",
                        "is_sellable": True,
                        "barcode": "1234567894",
                        "sku": "M-TV-1",
                        "category_name": "Electronics"
                    },
                    {
                        "price": "1000.00",
                        "cost": "700.00",
                        "units": "510.00",
                        "is_sellable": True,
                        "barcode": "1234567894",
                        "sku": "M-TV-1",
                        "category_name": "Electronics"
                    },
                    {
                        "price": "1000.00",
                        "cost": "700.00",
                        "units": "520.00",
                        "is_sellable": True,
                        "barcode": "1234567894",
                        "sku": "M-TV-1",
                        "category_name": "Electronics"
                    }
                ]
            },
            'product_units_agg_data': {
                "Coca Cola": '330',
                "Fanta": '630',
                "Sprite": '930',
                "Radio": '1230',
                "TV": '1530'
            },
        }

        self.assertEqual(inventory_valuation_data, results)
    
    def test_get_inventory_product_data_method_can_filter_date_for_long_report(self):

        today = timezone.now()
        yesterday = today - datetime.timedelta(days=1)
        yesterday2 = today - datetime.timedelta(days=2)

        today_str = today.strftime("%Y-%m-%d")
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        yesterday2_str = yesterday2.strftime("%Y-%m-%d")

        inventory_valuations = InventoryValuation.objects.all().order_by('id')

        self.assertEqual(len(inventory_valuations), 3)

        inventory_valuation1 = inventory_valuations[0]
        inventory_valuation2 = inventory_valuations[1]
        inventory_valuation3 = inventory_valuations[2]

        inventory_valuation1.created_date = today
        inventory_valuation1.save()

        inventory_valuation2.created_date = yesterday
        inventory_valuation2.save()

        inventory_valuation3.created_date = yesterday2
        inventory_valuation3.save()

        ######### Filter by today
        inventory_valuation_data = InventoryValuation.get_inventory_product_data(
            profile=self.profile,
            date=today_str
        )

        results = {
            'stores': ['Amboselli', 'Dorobo', 'Kilimanjaro'],
            'product_data': {
                "Coca Cola": [
                    {
                        "price": "60.00",
                        "cost": "45.00",
                        "units": "100.00",
                        "is_sellable": True,
                        "barcode": "1234567890",
                        "sku": "M-COCA-COLA-1",
                        "category_name": "Beverages"
                    },
                    {
                        "price": "60.00",
                        "cost": "45.00",
                        "units": "110.00",
                        "is_sellable": True,
                        "barcode": "1234567890",
                        "sku": "M-COCA-COLA-1",
                        "category_name": "Beverages"
                    },
                    {
                        "price": "60.00",
                        "cost": "45.00",
                        "units": "120.00",
                        "is_sellable": True,
                        "barcode": "1234567890",
                        "sku": "M-COCA-COLA-1",
                        "category_name": "Beverages"
                    }
                ],
                "Fanta": [
                    {
                        "price": "62.00",
                        "cost": "46.00",
                        "units": "200.00",
                        "is_sellable": True,
                        "barcode": "12345678901",
                        "sku": "M-FANTA-1",
                        "category_name": "Beverages"
                    },
                    {
                        "price": "62.00",
                        "cost": "46.00",
                        "units": "210.00",
                        "is_sellable": True,
                        "barcode": "12345678901",
                        "sku": "M-FANTA-1",
                        "category_name": "Beverages"
                    },
                    {
                        "price": "62.00",
                        "cost": "46.00",
                        "units": "220.00",
                        "is_sellable": True,
                        "barcode": "12345678901",
                        "sku": "M-FANTA-1",
                        "category_name": "Beverages"
                    }
                ],
                "Sprite": [
                    {
                        "price": "64.00",
                        "cost": "47.00",
                        "units": "300.00",
                        "is_sellable": True,
                        "barcode": "1234567892",
                        "sku": "M-SPRITE-1",
                        "category_name": "Beverages"
                    },
                    {
                        "price": "64.00",
                        "cost": "47.00",
                        "units": "310.00",
                        "is_sellable": True,
                        "barcode": "1234567892",
                        "sku": "M-SPRITE-1",
                        "category_name": "Beverages"
                    },
                    {
                        "price": "64.00",
                        "cost": "47.00",
                        "units": "320.00",
                        "is_sellable": True,
                        "barcode": "1234567892",
                        "sku": "M-SPRITE-1",
                        "category_name": "Beverages"
                    }
                ],
                "Radio": [
                    {
                        "price": "500.00",
                        "cost": "350.00",
                        "units": "400.00",
                        "is_sellable": True,
                        "barcode": "1234567893",
                        "sku": "M-RADIO-1",
                        "category_name": "Electronics"
                    },
                    {
                        "price": "500.00",
                        "cost": "350.00",
                        "units": "410.00",
                        "is_sellable": True,
                        "barcode": "1234567893",
                        "sku": "M-RADIO-1",
                        "category_name": "Electronics"
                    },
                    {
                        "price": "500.00",
                        "cost": "350.00",
                        "units": "420.00",
                        "is_sellable": True,
                        "barcode": "1234567893",
                        "sku": "M-RADIO-1",
                        "category_name": "Electronics"
                    }
                ],
                "TV": [
                    {
                        "price": "1000.00",
                        "cost": "700.00",
                        "units": "500.00",
                        "is_sellable": True,
                        "barcode": "1234567894",
                        "sku": "M-TV-1",
                        "category_name": "Electronics"
                    },
                    {
                        "price": "1000.00",
                        "cost": "700.00",
                        "units": "510.00",
                        "is_sellable": True,
                        "barcode": "1234567894",
                        "sku": "M-TV-1",
                        "category_name": "Electronics"
                    },
                    {
                        "price": "1000.00",
                        "cost": "700.00",
                        "units": "520.00",
                        "is_sellable": True,
                        "barcode": "1234567894",
                        "sku": "M-TV-1",
                        "category_name": "Electronics"
                    }
                ]
            },
            'product_units_agg_data': {
                "Coca Cola": '330',
                "Fanta": '630',
                "Sprite": '930',
                "Radio": '1230',
                "TV": '1530'
            },
        }

        self.assertEqual(inventory_valuation_data, results)


        ######### Filter by yesterday
        inventory_valuation_data = InventoryValuation.get_inventory_product_data(
            profile=self.profile,
            date=yesterday_str
        )

        results = {
            'stores': ['Dorobo',],
            'product_data': {
                "Coca Cola": [
                    {
                        "price": "60.00",
                        "cost": "45.00",
                        "units": "110.00",
                        "is_sellable": True,
                        "barcode": "1234567890",
                        "sku": "M-COCA-COLA-1",
                        "category_name": "Beverages"
                    }
                ],
                "Fanta": [
                    {
                        "price": "62.00",
                        "cost": "46.00",
                        "units": "210.00",
                        "is_sellable": True,
                        "barcode": "12345678901",
                        "sku": "M-FANTA-1",
                        "category_name": "Beverages"
                    }
                ],
                "Sprite": [
                    {
                        "price": "64.00",
                        "cost": "47.00",
                        "units": "310.00",
                        "is_sellable": True,
                        "barcode": "1234567892",
                        "sku": "M-SPRITE-1",
                        "category_name": "Beverages"
                    }
                ],
                "Radio": [
                    {
                        "price": "500.00",
                        "cost": "350.00",
                        "units": "410.00",
                        "is_sellable": True,
                        "barcode": "1234567893",
                        "sku": "M-RADIO-1",
                        "category_name": "Electronics"
                    }
                ],
                "TV": [
                    {
                        "price": "1000.00",
                        "cost": "700.00",
                        "units": "510.00",
                        "is_sellable": True,
                        "barcode": "1234567894",
                        "sku": "M-TV-1",
                        "category_name": "Electronics"
                    }
                ]
            },
            'product_units_agg_data': {
                "Coca Cola": '110',
                "Fanta": '210',
                "Sprite": '310',
                "Radio": '410',
                "TV": '510'
            },
        }

        self.assertEqual(inventory_valuation_data, results)

        ######### Filter by yesterday2
        inventory_valuation_data = InventoryValuation.get_inventory_product_data(
            profile=self.profile,
            date=yesterday2_str
        )

        results = {
            'stores': ['Kilimanjaro'],
            'product_data': {
                "Coca Cola": [
                    {
                        "price": "60.00",
                        "cost": "45.00",
                        "units": "120.00",
                        "is_sellable": True,
                        "barcode": "1234567890",
                        "sku": "M-COCA-COLA-1",
                        "category_name": "Beverages"
                    }
                ],
                "Fanta": [
                    {
                        "price": "62.00",
                        "cost": "46.00",
                        "units": "220.00",
                        "is_sellable": True,
                        "barcode": "12345678901",
                        "sku": "M-FANTA-1",
                        "category_name": "Beverages"
                    }
                ],
                "Sprite": [
                    {
                        "price": "64.00",
                        "cost": "47.00",
                        "units": "320.00",
                        "is_sellable": True,
                        "barcode": "1234567892",
                        "sku": "M-SPRITE-1",
                        "category_name": "Beverages"
                    }
                ],
                "Radio": [
                    {
                        "price": "500.00",
                        "cost": "350.00",
                        "units": "420.00",
                        "is_sellable": True,
                        "barcode": "1234567893",
                        "sku": "M-RADIO-1",
                        "category_name": "Electronics"
                    }
                ],
                "TV": [
                    {
                        "price": "1000.00",
                        "cost": "700.00",
                        "units": "520.00",
                        "is_sellable": True,
                        "barcode": "1234567894",
                        "sku": "M-TV-1",
                        "category_name": "Electronics"
                    }
                ]
            },
            'product_units_agg_data': {
                "Coca Cola": '120',
                "Fanta": '220',
                "Sprite": '320',
                "Radio": '420',
                "TV": '520'
            },
        }

        self.assertEqual(inventory_valuation_data, results)

    def test_recalculate_inventory_valuation_line_method(self):
        
        inventory_valuations = InventoryValuation.objects.all().order_by('id')

        self.assertEqual(len(inventory_valuations), 3)

        inventory_valuation1 = inventory_valuations[0]

        # Test inventory valuation 1
        self.assertEqual(inventory_valuation1.user, self.user1)
        self.assertEqual(inventory_valuation1.store.name, 'Amboselli')

        valuations_lines = inventory_valuation1.inventoryvaluationline_set.all().order_by('id')

        self.assertEqual(len(valuations_lines), 5)

        valuation_line1 = valuations_lines[0]

        self.assertEqual(valuation_line1.product.name, 'Coca Cola')

        self.assertEqual(valuation_line1.price, self.product1_level1.price)
        self.assertEqual(valuation_line1.cost, self.product1.cost)
        self.assertEqual(valuation_line1.units, 100)
        self.assertEqual(valuation_line1.barcode, self.product1.barcode)
        self.assertEqual(valuation_line1.sku, self.product1.sku)
        self.assertEqual(valuation_line1.category_name, self.product1.category.name)
        self.assertEqual(valuation_line1.is_sellable, True)
        self.assertEqual(valuation_line1.inventory_value, Decimal('4500.00'))
        self.assertEqual(valuation_line1.retail_value, Decimal('6000.00'))
        self.assertEqual(valuation_line1.potential_profit, Decimal('1500.00'))
        self.assertEqual(valuation_line1.margin, Decimal('25.00'))

        ### Change cost and recalculate inventory valuation
        valuation_line1.cost = self.product1.cost + 10
        valuation_line1.save()

        valuations_lines = inventory_valuation1.inventoryvaluationline_set.all().order_by('id')

        valuation_line1 = valuations_lines[0]
        valuation_line1.recalculate_inventory_valuation_line()

        self.assertEqual(valuation_line1.price, self.product1_level1.price)
        self.assertEqual(valuation_line1.cost, self.product1.cost + 10)
        self.assertEqual(valuation_line1.units, 100)
        self.assertEqual(valuation_line1.barcode, self.product1.barcode)
        self.assertEqual(valuation_line1.sku, self.product1.sku)
        self.assertEqual(valuation_line1.category_name, self.product1.category.name)
        self.assertEqual(valuation_line1.is_sellable, True)
        self.assertEqual(valuation_line1.inventory_value, Decimal('5500.00'))
        self.assertEqual(valuation_line1.retail_value, Decimal('6000.00'))
        self.assertEqual(valuation_line1.potential_profit, Decimal('500.00'))
        self.assertEqual(round(valuation_line1.margin, 2), Decimal('8.33'))

    def test_get_inventory_product_data_returns_data_for_the_correct_profile(self):

        today_str = timezone.now().strftime("%Y-%m-%d")

        inventory_valuation_data = InventoryValuation.get_inventory_product_data(
            profile=self.profile2,
            date=today_str
        )

        self.assertEqual(
            inventory_valuation_data, 
            {'stores': [], 'product_data': {}, 'product_units_agg_data': {}},
        )
    
    def test_if_local_midnight_tasks_creates_inventory_valuations(self):

        InventoryValuation.objects.all().delete()

        local_midnight_tasks()

        inventory_valuations = InventoryValuation.objects.all().order_by('id')

        self.assertEqual(len(inventory_valuations), 3)

        yesterday = (timezone.now() + datetime.timedelta(days=-1)).strftime("%B, %d, %Y 20:59")

        for inventory_valuation in inventory_valuations:
            self.assertEqual(
                (inventory_valuation.created_date).strftime("%B, %d, %Y %H:%M"), 
                yesterday
            )

    def test_if_local_midnight_tasks_wont_create_multiple_valuations_for_the_same_date(self):

        InventoryValuation.objects.all().delete()

        local_midnight_tasks()
        local_midnight_tasks()

        inventory_valuations = InventoryValuation.objects.all().order_by('id')

        self.assertEqual(len(inventory_valuations), 3)

    def test_if_local_midnight_tasks_will_create_inventory_valuations_even_if_there_are_models_for_the_previous_date(self):

        InventoryValuation.objects.all().delete()

        yesterday_but_1 = (timezone.now() + datetime.timedelta(days=-2))

        InventoryValuation.create_inventory_valutions(
            profile=self.profile,
            created_date=yesterday_but_1 
        )

        inventory_valuations = InventoryValuation.objects.all().order_by('id')

        self.assertEqual(len(inventory_valuations), 3)

        for inventory_valuation in inventory_valuations:
            self.assertEqual(
                (inventory_valuation.created_date).strftime("%B, %d, %Y %H:%M"), 
                yesterday_but_1.strftime("%B, %d, %Y %H:%M")
            )
        
        # Create inventory valuations for yesterday
        local_midnight_tasks()

        inventory_valuations = InventoryValuation.objects.all().order_by('id')

        self.assertEqual(len(inventory_valuations), 6)
