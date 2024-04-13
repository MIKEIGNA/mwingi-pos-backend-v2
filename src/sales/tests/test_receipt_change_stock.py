import uuid
import datetime

from django.test import override_settings

from django.utils import timezone
from django.conf import settings
from accounts.tasks import receipt_change_stock_tasks

from core.test_utils.custom_testcase import TestCase
from core.test_utils.create_user import (
    create_new_cashier_user,
    create_new_user, 
    create_new_customer
)
from core.test_utils.create_store_models import (
    create_new_discount,
    create_new_store,
    create_new_tax,
    create_new_category,
)
from mysettings.models import MySetting

from profiles.models import Customer, Profile
from products.models import Product

from sales.models import ( 
    Receipt,
    ReceiptLine,
    StockLevel
)

 
"""
=========================== Receipt ===================================
"""
class ReceiptTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user1
        self.user1 = create_new_user('angelina')
        
        self.profile1 = Profile.objects.get(user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)

        #Create a store
        self.store = create_new_store(self.profile1, 'Computer Store')

        # Create a cashier user
        self.cashier_user = create_new_cashier_user(
            "kate", self.profile1, self.store
        )

        #Create a tax
        self.tax = create_new_tax(self.profile1, self.store, 'Standard')

        #Create a discount
        self.discount = create_new_discount(self.profile1, self.store, 'Happy hour')

        #Create a category
        self.category = create_new_category(self.profile1, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.profile1, 'chris')

        self.create_products()

    def create_products(self):

        # Creates products
        self.product1 = Product.objects.create(
            profile=self.profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
        self.product1.stores.add(self.store)

        self.product2 = Product.objects.create(
            profile=self.profile1,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )
        self.product2.stores.add(self.store)

        # Add stock to products
        StockLevel.objects.filter(
            product=self.product1,
            store=self.store
        ).update(units=100)

        StockLevel.objects.filter(
            product=self.product2,
            store=self.store
        ).update(units=150)

    def create_duplicate_receipts(
        self, receipt_number, 
        receipt_number_for_testing,
        num_of_seconds_to_go_back=50
        ):

        sync_date = timezone.now() - datetime.timedelta(seconds=num_of_seconds_to_go_back)

        customer = Customer.objects.get(name='Chris Evans')

        # Create receipt1
        receipt = Receipt.objects.create(
            user=self.user1,
            store=self.store,
            customer=customer,
            customer_info={
                'name': customer.name, 
                'reg_no': customer.reg_no
            },
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            local_reg_no=222,
            receipt_number=receipt_number,
            receipt_number_for_testing=receipt_number_for_testing,
            created_date_timestamp = 1634926712,
            changed_stock=False,
            sync_date=sync_date
        )
    
        # Create receipt line1
        self.receiptline1 =  ReceiptLine.objects.create(
            receipt=receipt,
            product=self.product1,
            product_info={'name': self.product1.name, 'reg_no': self.product1.reg_no},
            price=1750,
            units=7
        )
    
        # Create receipt line2
        self.receiptline2 =  ReceiptLine.objects.create(
            receipt=receipt,
            product=self.product2,
            product_info={'name': self.product2.name, 'reg_no': self.product2.reg_no},
            price=2500,
            units=10
        )

        return receipt

    def test_get_receipt_number_field_to_use_during_testing_method_during_test_mode(self):

        # Test when we are in test mode
        self.assertEqual(Receipt.get_receipt_number_field_to_use_during_testing(), 'receipt_number_for_testing')

    @override_settings(TESTING_MODE=False)
    def test_get_receipt_number_field_to_use_during_testing_method_during_production_mode(self):

        # Test when we are not in  mode
        self.assertEqual(Receipt.get_receipt_number_field_to_use_during_testing(), 'receipt_number')

    def test_if_receipts_created_not_more_30_secs_ago_are_not_evaluated(self):
        
        seconds_to_go_back = [
            0, # 0 secs
            10, # 10 secs
            29, # 29 secs
        ]

        for index, seconds in enumerate(seconds_to_go_back):
            starting_number = index + 1

            # Add stock to products
            StockLevel.objects.filter(
                product=self.product1,
                store=self.store
            ).update(units=100)

            StockLevel.objects.filter(
                product=self.product2,
                store=self.store
            ).update(units=150)

            # Confirm stock level units were increased by receipt line units
            self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
            self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

            # Create receipts 5 receipts with the different receipt number
            for i in range(5): 
                self.create_duplicate_receipts(
                    receipt_number=f'{starting_number }00{i}',
                    receipt_number_for_testing=f'{starting_number}00{i}',
                    num_of_seconds_to_go_back=seconds
                )

            # Run receipt stock change
            receipt_change_stock_tasks()

            # Confirm stock level units were increased by receipt line units
            self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
            self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

    def test_if_receipts_created_more_than_1hr_ago_are_not_evaluated(self):
        
        seconds_to_go_back = [
            3600, # 1 hr
            3601, # 1 hr 1 sec
            4000, # 1 hr 6 mins 40 secs
        ]

        for index, seconds in enumerate(seconds_to_go_back):
            starting_number = index + 1

            # Add stock to products
            StockLevel.objects.filter(
                product=self.product1,
                store=self.store
            ).update(units=100)

            StockLevel.objects.filter(
                product=self.product2,
                store=self.store
            ).update(units=150)

            # Confirm stock level units were increased by receipt line units
            self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
            self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

            # Create receipts 5 receipts with the different receipt number
            for i in range(5): 
                self.create_duplicate_receipts(
                    receipt_number=f'{starting_number }00{i}',
                    receipt_number_for_testing=f'{starting_number}00{i}',
                    num_of_seconds_to_go_back=seconds
                )

            # Run receipt stock change
            receipt_change_stock_tasks()

            # Confirm stock level units were increased by receipt line units
            self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
            self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

    def test_if_receipts_created_between_30_secs_to_1_hr_ago_are_evaluated(self):
        
        seconds_to_go_back = [
            3599, # 59 mins 59 secs
            3000, # 50 mins
            30, # 30 secs
        ]

        for index, seconds in enumerate(seconds_to_go_back):
            starting_number = index + 1

            # Add stock to products
            StockLevel.objects.filter(
                product=self.product1,
                store=self.store
            ).update(units=100)

            StockLevel.objects.filter(
                product=self.product2,
                store=self.store
            ).update(units=150)

            # Confirm stock level units were increased by receipt line units
            self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
            self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

            # Create receipts 5 receipts with the different receipt number
            receipt_numbers = []
            for i in range(5): 
                receipt_number = f'{starting_number }00{i}'
                receipt_numbers.append(receipt_number)
                self.create_duplicate_receipts(
                    receipt_number=receipt_number,
                    receipt_number_for_testing=f'{starting_number}00{i}',
                    num_of_seconds_to_go_back=seconds
                )

            # Confirm initial receipt values
            for receipt_number in receipt_numbers:
                receipt = Receipt.objects.get(receipt_number=receipt_number)
                self.assertEqual(receipt.changed_stock, False)

            # Run receipt stock change
            receipt_change_stock_tasks()

            # Confirm stock level units were increased by receipt line units
            self.assertEqual(StockLevel.objects.get(product=self.product1).units, 65)
            self.assertEqual(StockLevel.objects.get(product=self.product2).units, 100)

            # Confirm initial receipt values were changed
            for receipt_number in receipt_numbers:
                receipt = Receipt.objects.get(receipt_number=receipt_number)
                self.assertEqual(receipt.changed_stock, True)
 
    def test_duplicate_receipt_numbers_when_we_have_duplicates_only(self):
        # Check initial stock levels for products
        self.assertEqual(StockLevel.objects.all().count(), 2)   

        # Confirm stock level units were increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

        receipts_num_to_test = 5

        # Create receipts 5 receipts with the same receipt number
        for i in range(receipts_num_to_test): 
            self.create_duplicate_receipts(
            receipt_number=f'100{i}',
            receipt_number_for_testing='100'
        )
            
        # Confirm receipts changed stock value
        receipts = Receipt.objects.all()
        for receipt in receipts:
            self.assertEqual(receipt.changed_stock, False)


        # Confirm stock level units were not increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

        # Confirm that only 1 receipt was created
        self.assertEqual(Receipt.objects.all().count(), receipts_num_to_test)

        # Call receipt change stock tasks
        with self.assertNumQueries(99):
            receipt_change_stock_tasks()

        # Confirm that only 1 receipt was created
        self.assertEqual(Receipt.objects.all().count(), 1)
        self.assertEqual(Receipt.objects.get().changed_stock,True)

        # Confirm stock level units were increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 93)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 140)

        # Test if calling receipt change stock tasks again wont change stock levels
        with self.assertNumQueries(6):
            receipt_change_stock_tasks()

        # Confirm stock level units were not increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 93)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 140)

    def test_duplicate_receipt_numbers_when_we_dont_have_duplicates(self):
        # Check initial stock levels for products
        self.assertEqual(StockLevel.objects.all().count(), 2)   

        # Confirm stock level units were increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

        receipts_num_to_test = 5

        # Create receipts 5 receipts with the same receipt number
        for i in range(receipts_num_to_test): 
            self.create_duplicate_receipts(
            receipt_number=f'100{i}',
            receipt_number_for_testing=f'100{i}',
        )
            
        # Confirm receipts changed stock value
        receipts = Receipt.objects.all()
        for receipt in receipts:
            self.assertEqual(receipt.changed_stock, False)

        # Confirm stock level units were not increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

        # Confirm that only 1 receipt was created
        self.assertEqual(Receipt.objects.all().count(), receipts_num_to_test)

        # Call receipt change stock tasks
        with self.assertNumQueries(166):
            receipt_change_stock_tasks()

        # Confirm receipts changed stock value
        receipts = Receipt.objects.all()
        for receipt in receipts:
            self.assertEqual(receipt.changed_stock, True)

        # Confirm that only 1 receipt was created
        self.assertEqual(Receipt.objects.all().count(), 5)

        # Confirm stock level units were increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 65)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 100)

    def test_duplicate_receipt_numbers_when_we_have_duplicates_and_non_duplicates(self):
        # Check initial stock levels for products
        self.assertEqual(StockLevel.objects.all().count(), 2)   

        # Confirm stock level units were increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

        # Create receipts 3 receipts with the same receipt number
        for i in range(3): 
            self.create_duplicate_receipts(
            receipt_number=f'100{i}',
            receipt_number_for_testing='100',
        )

        # Create receipts 2 receipts with different receipt number
        for i in range(2): 
            self.create_duplicate_receipts(
            receipt_number=f'200{i}',
            receipt_number_for_testing=f'200{i}',
        )
            
        # Confirm receipts changed stock value
        receipts = Receipt.objects.all()
        for receipt in receipts:
            self.assertEqual(receipt.changed_stock, False)

        # Confirm stock level units were not increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

        # Confirm receipts created
        self.assertEqual(Receipt.objects.all().count(), 5)

        # Call receipt change stock tasks
        with self.assertNumQueries(133):
            receipt_change_stock_tasks()

        # Confirm receipts changed stock value
        receipts = Receipt.objects.all()
        for receipt in receipts:
            self.assertEqual(receipt.changed_stock, True)

        # Confirm that only 1 receipt was created
        self.assertEqual(Receipt.objects.all().count(), 3)

        # Confirm stock level units were increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 79)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 120)

        # Test if calling receipt change stock tasks again wont change stock levels
        with self.assertNumQueries(6):
            receipt_change_stock_tasks()

        # Confirm stock level units were not increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 79)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 120)
  
    def test_if_stock_level_cannot_be_deducted_twice_from_the_same_line_sources(self):

        receipts_num_to_test = 5

        # Create receipts 5 receipts with the same receipt number
        for i in range(receipts_num_to_test): 
            self.create_duplicate_receipts(
            receipt_number=f'100{i}',
            receipt_number_for_testing=f'100{i}',
        )

        # Call receipt change stock tasks
        # with self.assertNumQueries(172):
        receipt_change_stock_tasks()

        Receipt.objects.all().update(changed_stock=False)

        # Confirm stock level units were increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 65)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 100)

        # Test if calling receipt change stock tasks again wont change stock levels
        with self.assertNumQueries(62):
            receipt_change_stock_tasks()
            receipt_change_stock_tasks()

        # Confirm stock level units were not increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 65)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 100)

    def test_if_stock_level_cannot_be_deducted_if_mysettings_receipt_change_stock_tasks_is_true(self):

        self.create_duplicate_receipts(
            receipt_number='100',
            receipt_number_for_testing='100',
        )

        # Preveent receipt change stock tasks from running
        MySetting.objects.all().update(receipt_change_stock_task_running=True)
        self.assertEqual(MySetting.objects.get().receipt_change_stock_task_running, True)

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

        receipt_change_stock_tasks()

        # Confirm stock level units were not increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

    def test_if_stock_level_will_turn_mysettings_receipt_change_stock_tasks_to_false_when_its_done(self):

        self.create_duplicate_receipts(
            receipt_number='100',
            receipt_number_for_testing='100',
        )

        # Check if receipt_change_stock_task_running is False
        self.assertEqual(MySetting.objects.get().receipt_change_stock_task_running, False)

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

        receipt_change_stock_tasks()

        # Confirm stock level units were not increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 93)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 140)

        # Check if receipt_change_stock_task_running is False
        self.assertEqual(MySetting.objects.get().receipt_change_stock_task_running, False)

    def test_if_receipt_change_stock_tasks_will_run_if_mysettings_was_last_updated_more_than_5_minutes_ago(self):

        update_date = timezone.now() - datetime.timedelta(
            seconds=10*60 + 1
        )
        
        self.create_duplicate_receipts(
            receipt_number='100',
            receipt_number_for_testing='100',
        )

        # Preveent receipt change stock tasks from running
        MySetting.objects.all().update(
            receipt_change_stock_task_running=True,
            stock_task_update_date=update_date
        )

        # Check if receipt_change_stock_task_running is True
        self.assertEqual(
            MySetting.objects.get().receipt_change_stock_task_running, 
            True
        )

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

        receipt_change_stock_tasks()

        # Confirm stock level units were not increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 93)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 140)

        # Check if receipt_change_stock_task_running is False
        self.assertEqual(
            MySetting.objects.get().receipt_change_stock_task_running, 
            False
        )
    
    def test_if_receipt_change_stock_tasks_wont_run_if_mysettings_was_last_updated_less_than_5_minutes_ago(self):

        update_date = timezone.now() - datetime.timedelta(
            seconds=4*60 + 1
        )
        
        self.create_duplicate_receipts(
            receipt_number='100',
            receipt_number_for_testing='100',
        )

        # Preveent receipt change stock tasks from running
        MySetting.objects.all().update(
            receipt_change_stock_task_running=True,
            stock_task_update_date=update_date
        )
        
        # Check if receipt_change_stock_task_running is True
        self.assertEqual(
            MySetting.objects.get().receipt_change_stock_task_running, 
            True
        )

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

        receipt_change_stock_tasks()

        # Confirm stock level units were not increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

        # Check if receipt_change_stock_task_running is True
        self.assertEqual(
            MySetting.objects.get().receipt_change_stock_task_running, 
            True
        )

    def test_if_receipt_change_stock_tasks_will_update_mysetting_stock_task_update_date(self):

        update_date = timezone.now() - datetime.timedelta(
            seconds=11*60
        )
        
        self.create_duplicate_receipts(
            receipt_number='100',
            receipt_number_for_testing='100',
        )

        # Preveent receipt change stock tasks from running
        MySetting.objects.all().update(
            receipt_change_stock_task_running=True,
            stock_task_update_date=update_date
        )
        
        # Check if receipt_change_stock_task_running is True
        self.assertEqual(
            MySetting.objects.get().receipt_change_stock_task_running, 
            True
        )
        self.assertEqual(
            MySetting.objects.get().stock_task_update_date, update_date
        )

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

        receipt_change_stock_tasks()

        # Confirm stock level units were not increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 93)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 140)

        # Check if receipt_change_stock_task_running is True
        self.assertEqual(
            MySetting.objects.get().receipt_change_stock_task_running, 
            False
        )
        self.assertNotEqual(
            MySetting.objects.get().stock_task_update_date, update_date
        )

    def test_if_receipt_change_stock_tasks_wont_run_(self):

        number_of_seconds = [
            45, # 45 secs
            1*60 + 1, # 1 min 1 sec
            4*60 + 1, # 4 mins 1 sec
            5*60 + 1, # 5 mins 1 sec
            6*60 + 1, # 6 mins 1 sec
        ]

        # Confirm stock level units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 100)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 150)

        for index, seconds in enumerate(number_of_seconds):

            update_date = timezone.now() - datetime.timedelta(seconds=seconds)
            
            self.create_duplicate_receipts(
                receipt_number=f'100{index}',
                receipt_number_for_testing=f'100{index}',
            )

            # Preveent receipt change stock tasks from running
            MySetting.objects.all().update(
                receipt_change_stock_task_running=False,
                stock_task_update_date=update_date
            )
            
            # Check if receipt_change_stock_task_running is True
            self.assertEqual(
                MySetting.objects.get().receipt_change_stock_task_running, 
                False
            )

            receipt_change_stock_tasks()

            # Check if receipt_change_stock_task_running is True
            self.assertEqual(
                MySetting.objects.get().receipt_change_stock_task_running, 
                False
            )

        # Confirm stock level units were not increased by receipt line units
        self.assertEqual(StockLevel.objects.get(product=self.product1).units, 65)
        self.assertEqual(StockLevel.objects.get(product=self.product2).units, 100)
