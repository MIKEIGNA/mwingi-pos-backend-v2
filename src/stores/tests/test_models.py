import datetime
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from api.tests.sales.create_receipts_for_test import CreateReceiptsForTesting, CreateReceiptsForTesting2

from core.test_utils.date_utils import DateUtils
from core.test_utils.custom_testcase import TestCase, empty_logfiles
from core.test_utils.create_user import create_new_cashier_user, create_new_manager_user, create_new_user
from core.test_utils.create_store_models import (
    create_new_store,
    create_new_tax,
    create_new_category,
    create_new_discount
)
from core.test_utils.log_reader import get_test_firebase_sender_log_content
from core.time_utils.date_helpers import DateHelperMethods
from core.time_utils.time_localizers import utc_to_local_datetime_with_format
from inventories.models import Product, StockLevel
from sales.models import Receipt, ReceiptPayment

from stores.models import (
    StoreCount, 
    Store,
    StorePaymentMethod,
    Tax, 
    TaxCount,
    Category,
    CategoryCount,
    Discount,
    DiscountCount
)
from profiles.models import Profile, ReceiptSetting

"""
=========================== Store ===================================
"""
class StoreTestCase(TestCase):

    def setUp(self):

        #Create a user1
        self.user1 = create_new_user('john')
        self.user2 = create_new_user('jack')
        
        self.profile1 = Profile.objects.get(user__email='john@gmail.com')
        self.profile2 = Profile.objects.get(user__email='jack@gmail.com')
        
        #Create a store
        self.store = create_new_store(self.profile1, 'Computer Store')

        # Create a manager user
        manager = create_new_manager_user("gucci", self.profile1, self.store)
        self.manager_profile = manager.employeeprofile

    def create_test_products(self):

        # Create a product 1
        Product.objects.create(
            profile=self.profile1,
            name="Product 1",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        # Create a product 2
        Product.objects.create( 
            profile=self.profile1,
            name="Product 2",
            price=5000,
            cost=2000,
            barcode='code456'
        )

    def test_Store_fields_verbose_names(self):
        """
        Ensure all fields in Store have the correct verbose names and can be
        found
        """
        store = Store.objects.get(name='Computer Store')

        self.assertEqual(store._meta.get_field('name').verbose_name, 'name')
        self.assertEqual(store._meta.get_field('address').verbose_name, 'address')
        self.assertEqual(store._meta.get_field('loyverse_store_id').verbose_name, 'loyverse store id')
        self.assertEqual(store._meta.get_field('increamental_id').verbose_name, 'increamental id')
        self.assertEqual(store._meta.get_field('is_shop').verbose_name, 'is shop')
        self.assertEqual(store._meta.get_field('is_truck').verbose_name, 'is truck')
        self.assertEqual(store._meta.get_field('is_warehouse').verbose_name, 'is warehouse')
        self.assertEqual(store._meta.get_field('reg_no').verbose_name, 'reg no')
        self.assertEqual(store._meta.get_field('created_date').verbose_name, 'created date')
        self.assertEqual(store._meta.get_field('till_number').verbose_name, 'till number')
        self.assertEqual(store._meta.get_field('is_deleted').verbose_name, 'is deleted')
        self.assertEqual(store._meta.get_field('deleted_date').verbose_name, 'deleted date')
        self.assertEqual(store._meta.get_field('synced_with_tally').verbose_name, 'synced with tally')

        self.assertEqual(store._meta.get_field('created_date_str').verbose_name, 'created date str')
        self.assertEqual(store._meta.get_field('deleted_date_str').verbose_name, 'deleted date str')

        fields = ([field.name for field in Store._meta.fields])

        self.assertEqual(len(fields), 17)

    def test_store_fields_after_it_has_been_created(self):

        store = Store.objects.get(name='Computer Store')
  
        self.assertEqual(store.profile.user.email, 'john@gmail.com')
        self.assertEqual(store.name, 'Computer Store')
        self.assertEqual(store.address, 'Nairobi')
        self.assertEqual(store.is_shop, True)
        self.assertEqual(store.is_truck, False)
        self.assertEqual(store.is_warehouse, False)
        self.assertEqual(store.increamental_id, 100)
        self.assertTrue(store.reg_no > 100000)  # Check if we have a valid reg_no
        self.assertEqual(store.is_deleted, False)
        self.assertEqual(
            store.deleted_date, 
            timezone.make_aware(
                DateHelperMethods.get_date_from_date_str(
                    settings.DEFAULT_START_DATE
                )
            )
        )
        self.assertEqual(
            store.created_date_str[0:11], 
            timezone.now().isoformat()[0:11]
        )
        self.assertEqual(store.deleted_date_str, store.deleted_date.isoformat())

    def test__str__method(self):
        store = Store.objects.get(name='Computer Store')
        self.assertEqual(str(store),'Computer Store')

    def test_get_profile_method(self):
        store = Store.objects.get(name='Computer Store')
        self.assertEqual(str(store.get_profile()),'john@gmail.com')


    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 
        
        store = Store.objects.get(name='Computer Store')
                     
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            store.get_created_date(self.user1.get_user_timezone()))
        )

    def test_get_employee_count_method(self):

        store = Store.objects.get(name='Computer Store')
        self.assertEqual(store.get_employee_count(), 1)


        # When store has no employees
        self.manager_profile.stores.remove(store)
        store = Store.objects.get(name='Computer Store')
        self.assertEqual(store.get_employee_count(), 0)

    def test_get_receipt_setting_method(self):

        store = Store.objects.get(name='Computer Store')

        r_setting = ReceiptSetting.objects.get(store=store)
        r_setting.header1 = 'Header1'
        r_setting.header2 = 'Header2'
        r_setting.header3 = 'Header3'
        r_setting.header4 = 'Header4'
        r_setting.header5 = 'Header5'
        r_setting.header6 = 'Header6'
        r_setting.footer1 = 'Footer1'
        r_setting.footer2 = 'Footer2'
        r_setting.footer3 = 'Footer3'
        r_setting.footer4 = 'Footer4'
        r_setting.footer5 = 'Footer5'
        r_setting.footer6 = 'Footer6'
        r_setting.save()

        store = Store.objects.get(name='Computer Store')

        self.assertEqual(
            store.get_receipt_setting(), 
            {
                'header1': 'Header1', 
                'header2': 'Header2', 
                'header3': 'Header3', 
                'header4': 'Header4', 
                'header5': 'Header5', 
                'header6': 'Header6', 
                'footer1': 'Footer1', 
                'footer2': 'Footer2', 
                'footer3': 'Footer3', 
                'footer4': 'Footer4', 
                'footer5': 'Footer5', 
                'footer6': 'Footer6'
            }
        )

    def test_create_receipt_setting_model_method(self):

        self.assertEqual(ReceiptSetting.objects.all().count(), 1)

        r_setting = ReceiptSetting.objects.get(store__name='Computer Store')
        
        self.assertEqual(r_setting.profile, self.profile1)

    def test_if_store_increaments_increamental_id_only_for_one_profile(self):

        # ********************** Create stores for the first time
        # Delete all stores first
        Store.objects.all().delete()

        ##### Create 2 stores for user 1
        create_new_store(self.profile1, 'Computer Store')
        create_new_store(self.profile1, 'Toy Store')

        # Store 1
        store1 = Store.objects.get(name='Computer Store')
        store_count1 = StoreCount.objects.get(reg_no=store1.reg_no)

        self.assertEqual(store1.increamental_id, 101)
        self.assertEqual(store_count1.increamental_id, 101) 

        # Store 2
        store2 = Store.objects.get(name='Toy Store')
        store_count2 = StoreCount.objects.get(reg_no=store2.reg_no)

        self.assertEqual(store2.increamental_id, 102)
        self.assertEqual(store_count2.increamental_id, 102) 

        ##### Create 2 stores for user 2
        create_new_store(self.profile2, 'Juice Store')
        create_new_store(self.profile2, 'Shoe Store')

        # Store 3
        store3 = Store.objects.get(name='Juice Store')
        store_count3 = StoreCount.objects.get(reg_no=store3.reg_no)

        self.assertEqual(store3.increamental_id, 100)
        self.assertEqual(store_count3.increamental_id, 100) 

        # Store 4
        store4 = Store.objects.get(name='Shoe Store')
        store_count4 = StoreCount.objects.get(reg_no=store4.reg_no)

        self.assertEqual(store4.increamental_id, 101)
        self.assertEqual(store_count4.increamental_id, 101) 


        # ********************** Create stores for the second time
        # Delete all stores first
        Store.objects.all().delete()

        ##### Create 2 stores for user 1
        create_new_store(self.profile1, 'Computer Store')
        create_new_store(self.profile1, 'Toy Store')

        # Store 1
        store1 = Store.objects.get(name='Computer Store')
        store_count1 = StoreCount.objects.get(reg_no=store1.reg_no)

        self.assertEqual(store1.increamental_id, 103)
        self.assertEqual(store_count1.increamental_id, 103) 

        # Store 2
        store2 = Store.objects.get(name='Toy Store')
        store_count2 = StoreCount.objects.get(reg_no=store2.reg_no)

        self.assertEqual(store2.increamental_id, 104)
        self.assertEqual(store_count2.increamental_id, 104) 

        ##### Create 2 stores for user 2
        create_new_store(self.profile2, 'Juice Store')
        create_new_store(self.profile2, 'Shoe Store')

        # Store 3
        store3 = Store.objects.get(name='Juice Store')
        store_count3 = StoreCount.objects.get(reg_no=store3.reg_no)

        self.assertEqual(store3.increamental_id, 102)
        self.assertEqual(store_count3.increamental_id, 102) 

        # Store 4
        store4 = Store.objects.get(name='Shoe Store')
        store_count4 = StoreCount.objects.get(reg_no=store4.reg_no)

        self.assertEqual(store4.increamental_id, 103)
        self.assertEqual(store_count4.increamental_id, 103) 

    def test_update_store_type_method(self):

        Store.objects.all().delete()
        
        create_new_store(self.profile1, 'Amboseli')
        create_new_store(self.profile1, 'A_Truck 2')
        create_new_store(self.profile1, 'A_Warehouse')

        # Store
        store1 = Store.objects.get(name='Amboseli')

        self.assertEqual(store1.is_shop, True)
        self.assertEqual(store1.is_truck, False)
        self.assertEqual(store1.is_warehouse, False)

        # Truck
        store2 = Store.objects.get(name='A_Truck 2')

        self.assertEqual(store2.is_shop, False)
        self.assertEqual(store2.is_truck, True)
        self.assertEqual(store2.is_warehouse, False)

        # Warehouse
        store3 = Store.objects.get(name='A_Warehouse')

        self.assertEqual(store3.is_shop, False)
        self.assertEqual(store3.is_truck, False)
        self.assertEqual(store3.is_warehouse, True)

    def test_create_stock_levels_for_all_products_method(self):

        # Check if we don't have any stock levels
        self.assertEqual(StockLevel.objects.all().count(), 0)

        Store.objects.all().delete()

        self.create_test_products()

        product1 = Product.objects.get(name='Product 1')
        product2 = Product.objects.get(name='Product 2')

        store = create_new_store(self.profile1, 'Amboseli')

        # Test if stock levels are created
        stock_levels = StockLevel.objects.all().order_by('id')

        self.assertEqual(stock_levels.count(), 2)

        # Stock level 1
        self.assertEqual(stock_levels[0].store, store)
        self.assertEqual(stock_levels[0].product, product1)
        self.assertEqual(stock_levels[0].minimum_stock_level, 0)
        self.assertEqual(stock_levels[0].units, 0)
        self.assertEqual(stock_levels[0].price, Decimal('2500.00'))

        # Stock level 2
        self.assertEqual(stock_levels[1].store, store)
        self.assertEqual(stock_levels[1].product, product2)
        self.assertEqual(stock_levels[1].minimum_stock_level, 0)
        self.assertEqual(stock_levels[1].units, 0)
        self.assertEqual(stock_levels[1].price, Decimal('5000.00'))

    def test_create_stock_levels_for_all_products_method_wont_create_duplicates(self):

        # Check if we don't have any stock levels
        self.assertEqual(StockLevel.objects.all().count(), 0)

        Store.objects.all().delete()

        self.create_test_products()

        store = create_new_store(self.profile1, 'Amboseli')

        # Test if stock levels are created
        self.assertEqual(StockLevel.objects.all().count(), 2)

        # Call store method again
        store.create_stock_levels_for_all_products()

        # Test if more stock levels were not created
        self.assertEqual(StockLevel.objects.all().count(), 2)

    def test_soft_delete_method(self):

        store = Store.objects.get(name='Computer Store')
        
        self.assertEqual(store.is_deleted, False)

        store.soft_delete()

        store = Store.objects.get(name='Computer Store')

        self.assertEqual(store.is_deleted, True)
        self.assertEqual(
            (store.deleted_date).strftime("%B, %d, %Y"), 
            (timezone.now()).strftime("%B, %d, %Y")
        )

"""
=========================== StoreCount ===================================
"""
class StoreCountTestCase(TestCase):

    def setUp(self):

        #Create a user1
        self.user1 = create_new_user('john')
        self.user2 = create_new_user('jack')
        
        self.profile1 = Profile.objects.get(user__email='john@gmail.com')
        self.profile2 = Profile.objects.get(user__email='jack@gmail.com')
        
        #Create a store
        self.store = create_new_store(self.profile1, 'Computer Store')

    def test_StoreCount_fields_verbose_names(self):
        """
        Ensure all fields in StoreCount have the correct verbose names and can be
        found
        """
        store_count = StoreCount.objects.get(profile=self.profile1)

        self.assertEqual(store_count._meta.get_field(
            'reg_no').verbose_name, 'reg no')
        self.assertEqual(store_count._meta.get_field(
            'increamental_id').verbose_name, 'increamental id')
        self.assertEqual(store_count._meta.get_field(
            'created_date').verbose_name, 'created date')

        fields = ([field.name for field in StoreCount._meta.fields])

        self.assertEqual(len(fields), 5)

    def test_StoreCount_existence(self):

        store_count = StoreCount.objects.get(profile=self.profile1)
        self.assertEqual(store_count.profile, self.profile1)
        self.assertEqual(store_count.reg_no, self.store.reg_no)
        self.assertEqual(store_count.increamental_id, 100)
        self.assertEqual(store_count.created_date, self.store.created_date)

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time

        store_count = StoreCount.objects.get(profile=self.profile1)

        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            store_count.get_created_date(self.user1.get_user_timezone()))
        )

    def test_if_StoreCount_wont_be_deleted_when_profile_is_deleted(self):

        self.profile1.delete()

        # Confirm if the profile has been deleted
        self.assertEqual(Profile.objects.filter(
            reg_no=self.profile1.reg_no).count(), 0)

        # Confirm number of store counts
        self.assertEqual(StoreCount.objects.all().count(), 1)

    def test_if_StoreCount_wont_be_deleted_when_store_is_deleted(self):

        self.store.delete()

        # Confirm if the store has been deleted
        self.assertEqual(Store.objects.filter(
            reg_no=self.profile1.reg_no).count(), 0)

        # Confirm number of store counts
        self.assertEqual(StoreCount.objects.all().count(), 1)

    def test_if_store_increaments_increamental_id_only_for_one_profile(self):

        # ********************** Create stores for the first time
        # Delete all stores first
        Store.objects.all().delete()

        ##### Create 2 stores for user 1
        create_new_store(self.profile1, 'Computer Store')
        create_new_store(self.profile1, 'Toy Store')

        # Store 1
        store1 = Store.objects.get(name='Computer Store')
        store_count1 = StoreCount.objects.get(reg_no=store1.reg_no)

        self.assertEqual(store1.increamental_id, 101)
        self.assertEqual(store_count1.increamental_id, 101) 

        # Store 2
        store2 = Store.objects.get(name='Toy Store')
        store_count2 = StoreCount.objects.get(reg_no=store2.reg_no)

        self.assertEqual(store2.increamental_id, 102)
        self.assertEqual(store_count2.increamental_id, 102) 

        ##### Create 2 stores for user 2
        create_new_store(self.profile2, 'Juice Store')
        create_new_store(self.profile2, 'Shoe Store')

        # Store 3
        store3 = Store.objects.get(name='Juice Store')
        store_count3 = StoreCount.objects.get(reg_no=store3.reg_no)

        self.assertEqual(store3.increamental_id, 100)
        self.assertEqual(store_count3.increamental_id, 100) 

        # Store 4
        store4 = Store.objects.get(name='Shoe Store')
        store_count4 = StoreCount.objects.get(reg_no=store4.reg_no)

        self.assertEqual(store4.increamental_id, 101)
        self.assertEqual(store_count4.increamental_id, 101) 


        # ********************** Create stores for the second time
        # Delete all stores first
        Store.objects.all().delete()

        ##### Create 2 stores for user 1
        create_new_store(self.profile1, 'Computer Store')
        create_new_store(self.profile1, 'Toy Store')

        # Store 1
        store1 = Store.objects.get(name='Computer Store')
        store_count1 = StoreCount.objects.get(reg_no=store1.reg_no)

        self.assertEqual(store1.increamental_id, 103)
        self.assertEqual(store_count1.increamental_id, 103) 

        # Store 2
        store2 = Store.objects.get(name='Toy Store')
        store_count2 = StoreCount.objects.get(reg_no=store2.reg_no)

        self.assertEqual(store2.increamental_id, 104)
        self.assertEqual(store_count2.increamental_id, 104) 

        ##### Create 2 stores for user 2
        create_new_store(self.profile2, 'Juice Store')
        create_new_store(self.profile2, 'Shoe Store')

        # Store 3
        store3 = Store.objects.get(name='Juice Store')
        store_count3 = StoreCount.objects.get(reg_no=store3.reg_no)

        self.assertEqual(store3.increamental_id, 102)
        self.assertEqual(store_count3.increamental_id, 102) 

        # Store 4
        store4 = Store.objects.get(name='Shoe Store')
        store_count4 = StoreCount.objects.get(reg_no=store4.reg_no)

        self.assertEqual(store4.increamental_id, 103)
        self.assertEqual(store_count4.increamental_id, 103) 

"""
=========================== StorePaymentMethod ===================================
"""

class StorePaymentMethodTestCase(TestCase):

    def setUp(self):

        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        self.cash = StorePaymentMethod.objects.get(
            profile=self.profile,
            payment_type=StorePaymentMethod.CASH_TYPE
        )

        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store2 = create_new_store(self.profile, 'Cloth Store')

        self.create_receipts()

    def create_receipts(self):

        # Create employee user
        self.manager = create_new_manager_user("gucci", self.profile, self.store1)
        self.cashier = create_new_cashier_user("kate", self.profile, self.store1)

        # Get the time now (Don't turn it into local)
        now = timezone.now()
        
        # Make time aware
        self.today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        self.tomorrow = self.today + datetime.timedelta(days=1)

        self.first_day_this_month = self.today.replace(day=1)

        CreateReceiptsForTesting(
            top_profile= self.profile,
            manager=self.manager.employeeprofile, 
            cashier= self.cashier.employeeprofile,
            store1= self.store1, 
            store2= self.store2
        ).create_receipts()
    
    def test_model_fields_verbose_names(self):
        """
        Ensure all fields in model have the correct verbose names and can be
        found
        """
        self.assertEqual(self.cash._meta.get_field('payment_type').verbose_name, 'payment type')
        self.assertEqual(self.cash._meta.get_field('name').verbose_name, 'name')
        self.assertEqual(self.cash._meta.get_field('reg_no').verbose_name, 'reg no')

        fields = ([field.name for field in StorePaymentMethod._meta.fields])

        self.assertEqual(len(fields), 5)

    def test_store_fields_after_it_has_been_created(self):
  
        self.assertEqual(self.cash.profile.user.email, 'john@gmail.com')
        self.assertEqual(self.cash.payment_type, StorePaymentMethod.CASH_TYPE)
        self.assertEqual(self.cash.name, 'Cash')
        self.assertTrue(self.cash.reg_no > 100000)  # Check if we have a valid reg_no

    def test__str__method(self):
        self.assertEqual(str(self.cash),'Cash')

    def test_get_profile_method(self):
        self.assertEqual(str(self.cash.get_profile()),'john@gmail.com')
    
    def test_get_report_data_method(self):

        data = self.cash.get_report_data(local_timezone=self.user.get_user_timezone())

        self.assertEqual(
            data, 
            {
                'name': 'Cash', 
                'count': 3, 
                'amount': '6198.00', 
                'refund_count': 1,
                'refund_amount': '3599.00', 
            }
        )


    def test_get_report_data_method_with_date(self):

        # Today date
        data = self.cash.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'name': 'Cash', 
                'count': 2, 
                'amount': '2599.00', 
                'refund_count': 0,
                'refund_amount': '0.00', 
            }
        )

        ############ This month
        data = self.cash.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.first_day_this_month.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'name': 'Cash', 
                'count': 3, 
                'amount': '6198.00',  
                'refund_count': 1,
                'refund_amount': '3599.00',
            }
        )

        ############ Date with no receipts
        data = self.cash.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='2011-01-01', 
            date_before='2011-01-02',
        )

        self.assertEqual(
            data, 
            {
                'name': 'Cash', 
                'count': 0, 
                'amount': '0.00',  
                'refund_count': 0,
                'refund_amount': '0.00',
            }
        )

        ############# Wrong date from
        data = self.cash.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='20111-01-01', 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'name': 'Cash',
                'count': 3, 
                'amount': '6198.00', 
                'refund_count': 1,
                'refund_amount': '3599.00' 
            }
        )
    
        ############ Wrong date to
        data = self.cash.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'),
            date_before='20111-01-01',
        )

        self.assertEqual(
            data, 
            {
                'name': 'Cash', 
                'count': 3, 
                'amount': '6198.00', 
                'refund_count': 1,
                'refund_amount': '3599.00' 
            }
        )

    def test_get_report_data_method_with_store_reg_no(self):

        # Store 1
        self.assertEqual(
            self.cash.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=[self.store1.reg_no]
            ), 
            {
                'name': 'Cash', 
                'count': 3, 
                'amount': '6198.00', 
                'refund_count': 1,
                'refund_amount': '3599.00' 
            }
        )

        # Store 2
        r_payment = ReceiptPayment.objects.get(receipt__local_reg_no=444)
        r_payment.payment_method = self.cash
        r_payment.save()

        self.assertEqual(
            self.cash.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=[self.store2.reg_no]
            ), 
            {
                'name': 'Cash', 
                'count': 1, 
                'amount': '4599.00',  
                'refund_count': 0,
                'refund_amount': '0.00',
            }
        )

        # Wrong store 
        self.assertEqual(
            self.cash.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=[1111]
            ), 
            {
                'name': 'Cash', 
                'count': 0, 
                'amount': '0.00', 
                'refund_count': 0,
                'refund_amount': '0.00',
            }
        )
    
    def test_get_report_data_method_with_user(self):

        # User 1
        self.assertEqual(
            self.cash.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=[self.user.reg_no]
            ), 
            {
                'name': 'Cash', 
                'count': 2, 
                'amount': '2599.00', 
                'refund_count': 0,
                'refund_amount': '0.00',
            }
        )

        # User 2
        self.assertEqual(
            self.cash.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=[self.manager.reg_no]
            ), 
            {
                'name': 'Cash', 
                'count': 1, 
                'amount': '3599.00', 
                'refund_count': 1,
                'refund_amount': '3599.00' 
            }
        )

        # Wrong user 
        self.assertEqual(
            self.cash.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=[111]
            ), 
            {
                'name': 'Cash', 
                'count': 0, 
                'amount': '0.00', 
                'refund_count': 0,
                'refund_amount': '0.00',
            }
        )

"""
=========================== Tax ===================================
"""
class TaxTestCase(TestCase):

    def setUp(self):

        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store2 = create_new_store(self.profile, 'Cloth Store')

        self.manager = create_new_manager_user("gucci", self.profile, self.store1)
        self.cashier = create_new_cashier_user("kate", self.profile, self.store1)
        
        #Create a tax
        self.tax = create_new_tax(self.profile, self.store1, 'Standard')

        # Get the time now (Don't turn it into local)
        now = timezone.now()
        
        # Make time aware
        self.today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        self.tomorrow = self.today + datetime.timedelta(days=1)

        self.first_day_this_month = self.today.replace(day=1)

        CreateReceiptsForTesting2( 
            top_profile= self.profile,
            manager=self.manager.employeeprofile, 
            cashier= self.cashier.employeeprofile,
            discount=None,
            tax=self.tax,
            store1= self.store1, 
            store2= self.store2
        ).create_receipts()
        
    def test_tax_fields_verbose_names(self):
        """
        Ensure all fields in tax have the correct verbose names and can be
        found
        """
        tax = Tax.objects.get(name='Standard')

        self.assertEqual(tax._meta.get_field('name').verbose_name, 'name')
        self.assertEqual(tax._meta.get_field('rate').verbose_name, 'rate')
        self.assertEqual(tax._meta.get_field('reg_no').verbose_name, 'reg no')
        self.assertEqual(tax._meta.get_field('created_date').verbose_name, 'created date')

        fields = ([field.name for field in Tax._meta.fields])

        self.assertEqual(len(fields), 7)

    def test_store_fields_after_it_has_been_created(self):

        tax = Tax.objects.get(name='Standard')
  
        self.assertEqual(tax.profile.user.email, 'john@gmail.com')
        self.assertEqual(tax.stores.all().count(), 1)
        self.assertEqual(tax.name, 'Standard')
        self.assertEqual(tax.rate, Decimal('20.05'))
        self.assertTrue(tax.reg_no > 100000)  # Check if we have a valid reg_no

    def test__str__method(self):
        tax = Tax.objects.get(name='Standard')
        self.assertEqual(str(tax),'Standard')

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 
        
        tax = Tax.objects.get(name='Standard')
                     
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            tax.get_created_date(self.user.get_user_timezone()))
        )

    def test_get_report_data_method(self):

        tax = Tax.objects.get(name='Standard')

        data = tax.get_report_data(local_timezone=self.user.get_user_timezone())

        self.assertEqual(
            data, 
            {'name': tax.name, 'rate': '20.05', 'amount': '210.00'}
        )

    def test_get_report_data_method_with_date(self):

        tax = Tax.objects.get(name='Standard')

        # Today date
        data = tax.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )
        self.assertEqual(
            data, 
            {'name': tax.name, 'rate': '20.05', 'amount': '60.00'}
        )
    
        ############ This month
        data = tax.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.first_day_this_month.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(data, {'name': tax.name, 'rate': '20.05', 'amount': '130.00'})

        ############ Date with no receipts
        data = tax.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='2011-01-01', 
            date_before='2011-01-02',
        )

        self.assertEqual(data, {'name': tax.name, 'rate': '20.05', 'amount': '0.00'})
    
        ############# Wrong date from
        data = tax.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='20111-01-01', 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(data, {'name': tax.name, 'rate': '20.05', 'amount': '210.00'})
    
        ############ Wrong date to
        data = tax.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'),
            date_before='20111-01-01',
        )

        self.assertEqual(data, {'name': tax.name, 'rate': '20.05', 'amount': '210.00'})
    
    def test_get_report_data_method_with_store_reg_no(self):

        tax = Tax.objects.get(name='Standard')

        # Store 1
        self.assertEqual(
            tax.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=[self.store1.reg_no]
            ), 
            {'name': tax.name, 'rate': '20.05', 'amount': '130.00'}
        )

        # Store 2
        self.assertEqual(
            tax.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=[self.store2.reg_no]
            ), 
            {'name': tax.name, 'rate': '20.05', 'amount': '80.00'}
        )

        # Wrong store 
        self.assertEqual(
            tax.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=[1111]
            ), 
            {'name': tax.name, 'rate': '20.05', 'amount': '0.00'}
        )
    
    def test_get_report_data_method_with_user(self):

        tax = Tax.objects.get(name='Standard')

        # User 1
        self.assertEqual(
            tax.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=[self.user.reg_no]
            ), 
            {'name': tax.name, 'rate': '20.05', 'amount': '60.00'}
        )

        # User 2
        self.assertEqual(
            tax.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=[self.manager.reg_no]
            ), 
            {'name': tax.name, 'rate': '20.05', 'amount': '70.00'}
        )

        # Wrong user 
        self.assertEqual(
            tax.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=[111]
            ), 
            {'name': tax.name, 'rate': '20.05', 'amount': '0.00'}
        )

    def test_firebase_messages_are_sent_correctly(self):

        Tax.objects.all().delete()
        empty_logfiles()

        #Create a tax
        tax = create_new_tax(self.profile, self.store1, 'Standard')

        content = get_test_firebase_sender_log_content(only_include=['tax'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'tax', 
                'action_type': 'create', 
                'name': 'Standard', 
                'rate': '20.05', 
                'reg_no': str(tax.reg_no)
            }
        }

        self.assertEqual(content[0], result)


        # Edit tax
        tax = Tax.objects.get(name='Standard')
        tax.name = 'New name'
        tax.rate = 25.01
        tax.save()

        content = get_test_firebase_sender_log_content(only_include=['tax'])
        self.assertEqual(len(content), 2)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'tax', 
                'action_type': 'edit', 
                'name': 'New name', 
                'rate': '25.01',
                'reg_no': str(tax.reg_no)
            }
        }

        self.assertEqual(content[1], result)

    
        #Delete tax
        Tax.objects.get(name='New name').delete()

        content = get_test_firebase_sender_log_content(only_include=['tax'])
        self.assertEqual(len(content), 3)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'tax', 
                'action_type': 'delete', 
                'name': 'New name', 
                'rate': '25.01',
                'reg_no': str(tax.reg_no)
            }
        }

        self.assertEqual(content[2], result)

    
"""
=========================== TaxCount ===================================
"""
class TaxCountTestCase(TestCase):

    def setUp(self):

        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        # Create store
        self.store = create_new_store(self.profile, 'Computer Store')
        
        #Create a tax
        self.tax = create_new_tax(self.profile, self.store, 'Standard')

    def test_TaxCount_fields_verbose_names(self):
        """
        Ensure all fields in TaxCount have the correct verbose names and can be
        found
        """
        tax_count = TaxCount.objects.get(profile=self.profile)

        self.assertEqual(tax_count._meta.get_field(
            'reg_no').verbose_name, 'reg no')
        self.assertEqual(tax_count._meta.get_field(
            'created_date').verbose_name, 'created date')

        fields = ([field.name for field in TaxCount._meta.fields])

        self.assertEqual(len(fields), 4)

    def test_TaxCount_existence(self):

        tax_count = TaxCount.objects.get(profile=self.profile)

        self.assertEqual(tax_count.profile, self.profile)
        self.assertEqual(tax_count.reg_no, self.tax.reg_no)
        self.assertEqual(tax_count.created_date, self.tax.created_date)

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time

        tax_count = TaxCount.objects.get(profile=self.profile)

        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            tax_count.get_created_date(self.user.get_user_timezone()))
        )

    def test_if_TaxCount_wont_be_deleted_when_profile_is_deleted(self):

        self.profile.delete()

        # Confirm if the profile has been deleted
        self.assertEqual(Profile.objects.filter(
            reg_no=self.profile.reg_no).count(), 0)

        # Confirm number of tax counts
        self.assertEqual(TaxCount.objects.all().count(), 1)

    def test_if_TaxCount_wont_be_deleted_when_store_is_deleted(self):

        self.tax.delete()

        # Confirm if the tax has been deleted
        self.assertEqual(Tax.objects.filter(
            reg_no=self.profile.reg_no).count(), 0)

        # Confirm number of tax counts
        self.assertEqual(TaxCount.objects.all().count(), 1)


"""
=========================== Category ===================================
"""
class CategoryTestCase(TestCase):

    def setUp(self):

        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')
        
        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store2 = create_new_store(self.profile, 'Cloth Store')

        # Create employee user
        self.manager = create_new_manager_user("gucci", self.profile, self.store1)
        self.cashier = create_new_cashier_user("kate", self.profile, self.store1)
        
        #Create a category
        self.category = create_new_category(self.profile, 'Hair')
        
        # Get the time now (Don't turn it into local)
        now = timezone.now()
        
        # Make time aware
        self.today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        self.tomorrow = self.today + datetime.timedelta(days=1)

        self.first_day_this_month = self.today.replace(day=1)

        CreateReceiptsForTesting2(
            top_profile= self.profile,
            manager=self.manager.employeeprofile, 
            cashier= self.cashier.employeeprofile,
            discount=None,
            tax=None,
            store1= self.store1, 
            store2= self.store2
        ).create_receipts()
        
        # Update product 1
        product = Product.objects.get(name="Shampoo")
        product.category = self.category
        product.save()
    
    def test_category_fields_verbose_names(self):
        """
        Ensure all fields in category have the correct verbose names and can be
        found
        """
        category = Category.objects.get(name='Hair')

        self.assertEqual(category._meta.get_field('name').verbose_name, 'name')
        self.assertEqual(category._meta.get_field('color_code').verbose_name, 'color code')
        self.assertEqual(category._meta.get_field('product_count').verbose_name, 'product count')
        self.assertEqual(category._meta.get_field('reg_no').verbose_name, 'reg no')
        self.assertEqual(category._meta.get_field('created_date').verbose_name, 'created date')

        fields = ([field.name for field in Category._meta.fields])

        self.assertEqual(len(fields), 8)

    def test_category_fields_after_it_has_been_created(self):

        category = Category.objects.get(name='Hair')
  
        self.assertEqual(category.profile.user.email, 'john@gmail.com')
        self.assertEqual(category.name, 'Hair')
        self.assertEqual(category.color_code, '#474A49')
        self.assertEqual(category.product_count, 1)
        self.assertTrue(category.reg_no > 100000)  # Check if we have a valid reg_no

    def test__str__method(self):
        category = Category.objects.get(name='Hair')
        self.assertEqual(str(category),'Hair')

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 
        
        category = Category.objects.get(name='Hair')
                     
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            category.get_created_date(self.user.get_user_timezone()))
        )

    def test_if_prodcut_count_will_be_updated_when_model_is_saved(self):

        # When category has no products
        category = Category.objects.get(name='Hair')
        self.assertEqual(category.product_count, 1)


        # When category has products
        # Create a product
        Product.objects.create(
            profile=self.profile,
            category=category,
            name="Shampoo2",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        category = Category.objects.get(name='Hair')
        category.save()

        category = Category.objects.get(name='Hair')
        self.assertEqual(category.product_count, 2)
    
    def test_get_report_data_method(self):

        category = Category.objects.get(name='Hair')

        data = category.get_report_data(local_timezone=self.user.get_user_timezone())

        self.assertEqual(
            data, 
            {
                'name': category.name, 
                'items_sold': '22', 
                'net_sales': '55000.00', 
                'cost': '22000.00', 
                'profit': '33000.00'
            }
        )

    def test_get_report_data_method_with_date(self):

        category = Category.objects.get(name='Hair')

        # Today date
        data = category.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'name': category.name,
                'items_sold': '7', 
                'net_sales': '17500.00',
                'cost': '7000.00',  
                'profit': '10500.00'
            }
        )

        ############ This month
        data = category.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.first_day_this_month.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'name': category.name,
                'items_sold': '16', 
                'net_sales': '40000.00', 
                'cost': '16000.00', 
                'profit': '24000.00'
            }
        )

        ############ Date with no receipts
        data = category.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='2011-01-01', 
            date_before='2011-01-02',
        )

        self.assertEqual(
            data, 
            {
                'name': category.name,
                'items_sold': '0', 
                'net_sales': '0.00', 
                'cost': '0.00', 
                'profit': '0.00'
            }
        )

        ############# Wrong date from
        data = category.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='20111-01-01', 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'name': category.name,
                'items_sold': '22', 
                'net_sales': '55000.00', 
                'cost': '22000.00', 
                'profit': '33000.00'
            }
        )

        ############ Wrong date to
        data = category.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'),
            date_before='20111-01-01',
        )

        self.assertEqual(
            data, 
            {
                'name': category.name,
                'items_sold': '22', 
                'net_sales': '55000.00', 
                'cost': '22000.00', 
                'profit': '33000.00'
            }
        )

    def test_get_report_data_method_with_store_reg_no(self):

        category = Category.objects.get(name='Hair')

        # Store 1
        self.assertEqual(
            category.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=self.store1.reg_no), 
            {
                'name': category.name,
                'items_sold': '16', 
                'net_sales': '40000.00', 
                'cost': '16000.00', 
                'profit': '24000.00'
            }
        )

        # Store 2
        self.assertEqual(
            category.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=self.store2.reg_no
            ), 
            {
                'name': category.name,
                'items_sold': '6', 
                'net_sales': '15000.00', 
                'cost': '6000.00', 
                'profit': '9000.00'
            }
        )

        # Wrong store 
        self.assertEqual(
            category.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=1111
            ), 
            {
                'name': category.name,
                'items_sold': '0', 
                'net_sales': '0.00', 
                'cost': '0.00', 
                'profit': '0.00'
            }
        )

    def test_get_report_data_method_with_user(self):

        category = Category.objects.get(name='Hair')

        # User 1
        self.assertEqual(
            category.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=self.user.reg_no
            ), 
            {
                'name': category.name,
                'items_sold': '7', 
                'net_sales': '17500.00', 
                'cost': '7000.00', 
                'profit': '10500.00'
            }
        )

        # User 2
        self.assertEqual(
            category.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=self.manager.reg_no
            ), 
            {
                'name': category.name,
                'items_sold': '9', 
                'net_sales': '22500.00', 
                'cost': '9000.00', 
                'profit': '13500.00'
            }
        )

        # Wrong user 
        self.assertEqual(
            category.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=111
            ), 
            {
                'name': category.name,
                'items_sold': '0', 
                'net_sales': '0.00', 
                'cost': '0.00', 
                'profit': '0.00'
            } 
        )

    def test_firebase_messages_are_sent_correctly(self):

        Category.objects.all().delete()
        empty_logfiles()

        # Create category
        category = create_new_category(self.profile, 'Hair')

        content = get_test_firebase_sender_log_content(only_include=['category'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'category', 
                'action_type': 'create', 
                'name': 'Hair', 
                'color_code': '#474A49', 
                'product_count': '0', 
                'reg_no': str(category.reg_no)
            }
        }

        self.assertEqual(content[0], result)

        # Edit category
        category = Category.objects.get(name='Hair')
        category.name = 'New name'
        category.color_code = '#474A40'
        category.save()

        content = get_test_firebase_sender_log_content(only_include=['category'])
        self.assertEqual(len(content), 2)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'category', 
                'action_type': 'edit', 
                'name': 'New name', 
                'color_code': '#474A40', 
                'product_count': '0', 
                'reg_no': str(category.reg_no)
            }
        }

        self.assertEqual(content[1], result)

        # Delete category
        Category.objects.get(name='New name').delete()

        content = get_test_firebase_sender_log_content(only_include=['category'])
        self.assertEqual(len(content), 3)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'category', 
                'action_type': 'delete', 
                'name': 'New name', 
                'color_code': '#474A40', 
                'product_count': '0', 
                'reg_no': str(category.reg_no)
            }
        }

        self.assertEqual(content[2], result)

"""
=========================== CategoryCount ===================================
"""
class CategoryCountTestCase(TestCase):

    def setUp(self):

        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')
        
        #Create a category
        self.category = create_new_category(self.profile, 'Hair')

    def test_CategoryCount_fields_verbose_names(self):
        """
        Ensure all fields in CategoryCount have the correct verbose names and can be
        found
        """
        category_count = CategoryCount.objects.get(profile=self.profile)

        self.assertEqual(category_count._meta.get_field(
            'reg_no').verbose_name, 'reg no')
        self.assertEqual(category_count._meta.get_field(
            'created_date').verbose_name, 'created date')

        fields = ([field.name for field in CategoryCount._meta.fields])

        self.assertEqual(len(fields), 4)

    def test_CategoryCount_existence(self):

        category_count = CategoryCount.objects.get(profile=self.profile)

        self.assertEqual(category_count.profile, self.profile)
        self.assertEqual(category_count.reg_no, self.category.reg_no)
        self.assertEqual(category_count.created_date, self.category.created_date)

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time

        category_count = CategoryCount.objects.get(profile=self.profile)


        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            category_count.get_created_date(self.user.get_user_timezone()))
        )

    def test_if_CategoryCount_wont_be_deleted_when_profile_is_deleted(self):

        self.profile.delete()

        # Confirm if the profile has been deleted
        self.assertEqual(Profile.objects.filter(
            reg_no=self.profile.reg_no).count(), 0)

        # Confirm number of category counts
        self.assertEqual(CategoryCount.objects.all().count(), 1)

    def test_if_CategoryCount_wont_be_deleted_when_store_is_deleted(self):

        self.category.delete()

        # Confirm if the category has been deleted
        self.assertEqual(Category.objects.filter(
            reg_no=self.profile.reg_no).count(), 0)

        # Confirm number of category counts
        self.assertEqual(CategoryCount.objects.all().count(), 1)

"""
=========================== Discount ===================================
"""

class DiscountTestCase(TestCase):

    def setUp(self):

        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store2 = create_new_store(self.profile, 'Cloth Store')

        self.manager = create_new_manager_user("gucci", self.profile, self.store1)
        self.cashier = create_new_cashier_user("kate", self.profile, self.store1)
   
        #Create a discount
        self.discount = create_new_discount(self.profile, self.store1, 'Happy hour')

        # Get the time now (Don't turn it into local)
        now = timezone.now()
        
        # Make time aware
        self.today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        self.tomorrow = self.today + datetime.timedelta(days=1)

        self.first_day_this_month = self.today.replace(day=1)

        CreateReceiptsForTesting2(
            top_profile= self.profile,
            manager=self.manager.employeeprofile, 
            cashier= self.cashier.employeeprofile,
            discount=self.discount,
            tax=None,
            store1= self.store1, 
            store2= self.store2
        ).create_receipts()

    def test_discount_fields_verbose_names(self):
        """
        Ensure all fields in discount have the correct verbose names and can be
        found
        """
        discount = Discount.objects.get(name='Happy hour')

        self.assertEqual(discount._meta.get_field('name').verbose_name, 'name')
        self.assertEqual(discount._meta.get_field('value').verbose_name, 'value')
        self.assertEqual(discount._meta.get_field('amount').verbose_name, 'amount')
        self.assertEqual(discount._meta.get_field('reg_no').verbose_name, 'reg no')
        self.assertEqual(discount._meta.get_field('created_date').verbose_name, 'created date')

        fields = ([field.name for field in Discount._meta.fields])

        self.assertEqual(len(fields), 7)

    def test_store_fields_after_it_has_been_created(self):

        discount = Discount.objects.get(name='Happy hour')
  
        self.assertEqual(discount.profile.user.email, 'john@gmail.com')
        self.assertEqual(discount.stores.all().count(), 1)
        self.assertEqual(discount.name, 'Happy hour')
        self.assertEqual(discount.value, Decimal('20.05'))
        self.assertEqual(discount.amount, Decimal('50.05'))
        self.assertTrue(discount.reg_no > 100000)  # Check if we have a valid reg_no

    def test__str__method(self):
        discount = Discount.objects.get(name='Happy hour')
        self.assertEqual(str(discount),'Happy hour')

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 
        
        discount = Discount.objects.get(name='Happy hour')
                     
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            discount.get_created_date(self.user.get_user_timezone()))
        )

    def test_get_report_data_method(self):

        discount = Discount.objects.get(name='Happy hour')

        data = discount.get_report_data(local_timezone=self.user.get_user_timezone())

        self.assertEqual(data, {'name': discount.name, 'count': 3, 'amount': '1503.00'})
    
    def test_get_report_data_method_with_date(self):

        discount = Discount.objects.get(name='Happy hour')

        # Today date
        data = discount.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(data, {'name': discount.name,  'count': 1, 'amount': '401.00'})

        ############ This month
        data = discount.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.first_day_this_month.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(data, {'name': discount.name, 'count': 2, 'amount': '902.00'})

        ############ Date with no receipts
        data = discount.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='2011-01-01', 
            date_before='2011-01-02',
        )

        self.assertEqual(data, {'name': discount.name, 'count': 0, 'amount': '0.00'})

        ############# Wrong date from
        data = discount.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='20111-01-01', 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {'name': discount.name, 'count': 3, 'amount': '1503.00'}
        )

        ############ Wrong date to
        data = discount.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'),
            date_before='20111-01-01',
        )

        self.assertEqual(
            data, 
            {'name': discount.name, 'count': 3, 'amount': '1503.00'}
        )

    def test_get_report_data_method_with_store_reg_no(self):

        discount = Discount.objects.get(name='Happy hour')

        # Store 1
        self.assertEqual(
            discount.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=self.store1.reg_no
            ), 
            {'name': discount.name, 'count': 2, 'amount': '902.00'}
        )

        # Store 2
        self.assertEqual(
            discount.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=self.store2.reg_no
            ), 
            {'name': discount.name, 'count': 1, 'amount': '601.00'}
        )

        # Wrong store 
        self.assertEqual(
            discount.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_nos=1111
            ), 
            {'name': discount.name, 'count': 0, 'amount': '0.00'}
        )

    def test_get_report_data_method_with_user(self):

        discount = Discount.objects.get(name='Happy hour')

        # User 1
        self.assertEqual(
            discount.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=self.user.reg_no
            ), 
            {'name': discount.name, 'count': 1, 'amount': '401.00'}
        )

        # User 2
        self.assertEqual(
            discount.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=self.manager.reg_no
            ), 
            {'name': discount.name, 'count': 1, 'amount': '501.00'}
        )

        # Wrong user 
        self.assertEqual(
            discount.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                user_reg_nos=111
            ), 
            {'name': discount.name, 'count': 0, 'amount': '0.00'}
        )

    def test_firebase_messages_are_sent_correctly(self):

        Discount.objects.all().delete()
        empty_logfiles()

        #Create a discount
        discount = create_new_discount(self.profile, self.store1, 'Standard')

        content = get_test_firebase_sender_log_content(only_include=['discount'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'discount', 
                'action_type': 'create', 
                'name': 'Standard', 
                'value': '20.05', 
                'amount': '50.05', 
                'reg_no': str(discount.reg_no)
            }
        }

        self.assertEqual(content[0], result)


        # Edit discount
        discount = Discount.objects.get(name='Standard')
        discount.name = 'New name'
        discount.value = 25.01
        discount.save()

        content = get_test_firebase_sender_log_content(only_include=['discount'])
        self.assertEqual(len(content), 2)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'discount', 
                'action_type': 'edit', 
                'name': 'New name', 
                'value': '25.01',
                'amount': '50.05', 
                'reg_no': str(discount.reg_no)
            }
        }

        self.assertEqual(content[1], result)

    
        #Delete discount
        Discount.objects.get(name='New name').delete()

        content = get_test_firebase_sender_log_content(only_include=['discount'])
        self.assertEqual(len(content), 3)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'discount', 
                'action_type': 'delete', 
                'name': 'New name', 
                'value': '25.01',
                'amount': '50.05', 
                'reg_no': str(discount.reg_no)
            }
        }

        self.assertEqual(content[2], result)


"""
=========================== DiscountCount ===================================
"""
class DiscountCountTestCase(TestCase):

    def setUp(self):

        #Create a user1
        self.user = create_new_user('john')
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        # Create store
        self.store = create_new_store(self.profile, 'Computer Store')
        
        #Create a discount
        self.discount = create_new_discount(self.profile, self.store, 'Happy hour')

    def test_DiscountCount_fields_verbose_names(self):
        """
        Ensure all fields in DiscountCount have the correct verbose names and can be
        found
        """
        discount_count = DiscountCount.objects.get(profile=self.profile)

        self.assertEqual(discount_count._meta.get_field(
            'reg_no').verbose_name, 'reg no')
        self.assertEqual(discount_count._meta.get_field(
            'created_date').verbose_name, 'created date')

        fields = ([field.name for field in DiscountCount._meta.fields])

        self.assertEqual(len(fields), 4)

    def test_DiscountCount_existence(self):

        discount_count = DiscountCount.objects.get(profile=self.profile)

        self.assertEqual(discount_count.profile, self.profile)
        self.assertEqual(discount_count.reg_no, self.discount.reg_no)
        self.assertEqual(discount_count.created_date, self.discount.created_date)

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time

        discount_count = DiscountCount.objects.get(profile=self.profile)

        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            discount_count.get_created_date(self.user.get_user_timezone()))
        )

    def test_if_DiscountCount_wont_be_deleted_when_profile_is_deleted(self):

        self.profile.delete()

        # Confirm if the profile has been deleted
        self.assertEqual(Profile.objects.filter(
            reg_no=self.profile.reg_no).count(), 0)

        # Confirm number of discount counts
        self.assertEqual(DiscountCount.objects.all().count(), 1)

    def test_if_DiscountCount_wont_be_deleted_when_store_is_deleted(self):

        self.discount.delete()

        # Confirm if the discount has been deleted
        self.assertEqual(Discount.objects.filter(
            reg_no=self.profile.reg_no).count(), 0)

        # Confirm number of discount counts
        self.assertEqual(DiscountCount.objects.all().count(), 1)


