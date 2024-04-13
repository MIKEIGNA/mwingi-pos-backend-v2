from pprint import pprint
from PIL import Image
import datetime

from django.utils import timezone
from django.conf import settings
from clusters.models import StoreCluster

from core.test_utils.date_utils import DateUtils
from core.test_utils.create_store_models import (
    create_new_category,
    create_new_discount, 
    create_new_store, 
    create_new_tax
)
from core.test_utils.create_product_variants import create_1d_variants
from core.test_utils.create_user import (
    create_cashier_assets,
    create_new_user, 
    create_new_manager_user, 
    create_new_cashier_user,
    create_new_customer
)
from core.test_utils.custom_testcase import TestCase, empty_logfiles
from core.test_utils.log_reader import get_test_firebase_sender_log_content
from inventories.models import StockLevel
from stores.models import Store, StorePaymentMethod
from profiles.models import (
    LoyaltySetting,
    ProfileCount, 
    Profile, 
    EmployeeProfile,
    EmployeeProfileCount,
    Customer,
    CustomerCount,
    ReceiptSetting,
    UserGeneralSetting
)
from accounts.utils.currency_choices import USD
from accounts.models import User, UserGroup  
from accounts.utils.user_type import EMPLOYEE_USER 

from billing.models import Subscription

from products.models import Product
from sales.models import Receipt, ReceiptLine

# =========================== Profile ===================================
class ProfileExistenceTestCase(TestCase):
    
    def setUp(self):
        self.create_test_models()
    
    def create_test_models(self):

        # Create a top user
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')

        self.store = create_new_store(self.top_profile, 'Computer Store')
        
        # Create a supervisor user
        create_new_manager_user("gucci", self.top_profile, self.store)
        
        self.manager_profile = EmployeeProfile.objects.get(user__email='gucci@gmail.com')
    
    def test_profile_fields_verbose_names(self):
        # Ensure all fields in profile have the correct verbose names and can be
        # found
        
        p = Profile.objects.get(user__email='john@gmail.com')
        
        self.assertEqual(p._meta.get_field('image').verbose_name,'image')
        self.assertEqual(p._meta.get_field('phone').verbose_name,'phone')
        self.assertEqual(p._meta.get_field('approved').verbose_name,'approved')
        self.assertEqual(p._meta.get_field('join_date').verbose_name,'join date')
        self.assertEqual(p._meta.get_field('business_name').verbose_name,'business name')
        self.assertEqual(p._meta.get_field('location').verbose_name,'location')
        self.assertEqual(p._meta.get_field('currency').verbose_name,'currency')
        self.assertEqual(p._meta.get_field('reg_no').verbose_name,'reg no')
        
        fields = ([field.name for field in Profile._meta.fields])
        
        self.assertEqual(len(fields), 10)
    
    def test_profile_after_user_has_been_created(self):
        # Profile fields
        
        # Ensure everytime a user is created, a profile is created with
        # the right fields and values
        self.assertEqual(
            self.top_profile.image.url, 
            f'/media/images/profiles/{self.top_profile.reg_no}_.jpg'
        )
        self.assertEqual(self.top_profile.phone, int(self.user.phone))
        self.assertEqual(self.top_profile.business_name,'Skypac')
        self.assertEqual(self.top_profile.location,'Nairobi')
        self.assertEqual(self.top_profile.currency, USD)
        self.assertEqual(self.top_profile.reg_no, self.user.reg_no) # Check if we have a valid reg_no

    def test_profile_after_user_has_been_updated(self):
        # Profile fields
        
        # Ensure everytime a user is updated, a profile is updated with
        # the right fields and values
        
        u = User.objects.get(email='john@gmail.com')
        u.email = 'jane@gmail.com'
        u.save()
        
        p = Profile.objects.get(user__email='jane@gmail.com')
        
        self.assertEqual(p.user.email,'jane@gmail.com')
        self.assertEqual(p.phone, int(self.user.phone))

    def test__str__method(self):
        self.assertEqual(str(self.top_profile),'john@gmail.com') # Test the str method
 
    def test_get_short_name_method(self):
        self.assertEqual(self.top_profile.get_short_name(),'John')

    def test_get_full_name_method(self):
        self.assertEqual(self.top_profile.get_full_name(),'John Lock')

    def test_get_join_date_method(self):
  
        self.assertTrue(DateUtils.do_created_dates_compare(
            self.top_profile.get_join_date(
                self.top_profile.user.get_user_timezone()
            ))
        )
          
    def test_get_last_login_date_method(self):
        # Confirm that get_last_login_date_method returns last_login_date
        # in local time 
        
        # The user's last login field is now empty since we havent logged so we have
        # insert it manually

        user = self.top_profile.user
        user.last_login = timezone.now()
        user.save()
        
        profile = Profile.objects.get(user__email='john@gmail.com')
                
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            profile.get_last_login_date(
                self.top_profile.user.get_user_timezone()
            ))
        )

    def test_get_profile_image_url_method(self):
        self.assertEqual(self.top_profile.get_profile_image_url(), self.top_profile.image.url)
  
    def test_get_location_method(self):
        
        # Check result when locaiton has been provided
        self.assertEqual(self.top_profile.get_location(),'Nairobi')
        
        # Unset location
        profile = Profile.objects.get(user__email='john@gmail.com')
        profile.location = ""
        profile.save()
        
        profile = Profile.objects.get(user__email='john@gmail.com')
        
        # Check result when location has not been provided
        self.assertEqual(profile.get_location(),'Not set')
    
    def test_get_user_group_identification_method(self):
        profile = Profile.objects.get(user__email='john@gmail.com')
        self.assertEqual(profile.get_user_group_identification(), f'group_{profile.reg_no}')
    
    def test_sync_profile_phone_and_its_user_phone_method(self):
        
        # sync_profile_phone_and_its_user_phone
                
        p = Profile.objects.get(user__email='john@gmail.com')
        p.phone = 254701444555
        p.save()

        u = User.objects.get(email='john@gmail.com')
        self.assertEqual(u.phone, 254701444555)

    def test_get_currency_desc_method(self):

        # Test with default currency

        profile = Profile.objects.get(user__email='john@gmail.com')
        self.assertEqual(profile.get_currency_initials(), 'Usd')

        # Test with Usd

        # Change currency
        profile = Profile.objects.get(user__email='john@gmail.com')
        profile.currency = USD
        profile.save()

        profile = Profile.objects.get(user__email='john@gmail.com')
        self.assertEqual(profile.get_currency_initials(), 'Usd')

    def test_create_profile_count_method(self):
        """
        This method functionality has been tested in ProfileCountTestCase
        """
        
    def test_if_top_profile_can_own_multiple_manager_employee_profiles(self):
                        
        create_new_manager_user("lewis", self.top_profile, self.store)
        create_new_manager_user("lionel", self.top_profile, self.store)
        
        profiles = EmployeeProfile.objects.filter(
            user__user_type=EMPLOYEE_USER).count()
        
        self.assertEqual(profiles, 3)

    def test_if_top_profile_can_own_multiple_employee_profiles(self):
                        
        create_new_cashier_user("kate", self.top_profile, self.store)
        create_new_cashier_user("james", self.top_profile, self.store)
        create_new_cashier_user("ben", self.top_profile, self.store)
        
        profiles = EmployeeProfile.objects.filter(
            user__user_type=EMPLOYEE_USER).count()
        
        self.assertEqual(profiles, 4)

    def test_if_a_top_profile_cant_be_assigned_an_employee_user_model(self):
                                                
        user = User.objects.get(email='gucci@gmail.com')
        
        # Try to create a Profile with a supervisor user model
        Profile.objects.create(user=user,)
        
        profile = Profile.objects.filter(user__email='gucci@gmail.com').exists()
        
        self.assertEqual(profile, False)
    
    def test_profile_created_signal_creates_a_loyalty_setting_for_the_profile(self):

        setting = LoyaltySetting.objects.get(profile=self.top_profile)

        self.assertEqual(setting.profile, self.top_profile)
        self.assertEqual(setting.value, 0.00)

        self.assertEqual(
            LoyaltySetting.objects.filter(profile=self.top_profile).count(), 
            1
        )

    def test_profile_created_signal_creates_a_user_general_setting_for_the_profile(self):

        self.assertEqual(
            UserGeneralSetting.objects.filter(profile=self.top_profile).count(), 
            1
        )
    
    def test_get_store_payments_method(self):

        cash = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=StorePaymentMethod.CASH_TYPE
        )
        mpesa = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=StorePaymentMethod.MPESA_TYPE
        )
        card = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=StorePaymentMethod.CARD_TYPE
        )
        points = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=StorePaymentMethod.POINTS_TYPE
        )
        debt = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=StorePaymentMethod.DEBT_TYPE
        )
        other = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=StorePaymentMethod.OTHER_TYPE
        )

        result = [
            {
                'name': 'Cash', 
                'payment_type': StorePaymentMethod.CASH_TYPE, 
                'reg_no': cash.reg_no
            }, 
            {
                'name': 'Mpesa', 
                'payment_type': StorePaymentMethod.MPESA_TYPE, 
                'reg_no': mpesa.reg_no
            }, 
            {
                'name': 'Card', 
                'payment_type': StorePaymentMethod.CARD_TYPE, 
                'reg_no': card.reg_no
            }, 
            {
                'name': 'Points', 
                'payment_type': StorePaymentMethod.POINTS_TYPE, 
                'reg_no': points.reg_no
            }, 
            {
                'name': 'Debt', 
                'payment_type': StorePaymentMethod.DEBT_TYPE, 
                'reg_no': debt.reg_no
            }, 
            {
                'name': 'Other', 
                'payment_type': StorePaymentMethod.OTHER_TYPE, 
                'reg_no': other.reg_no
            }
        ]

        self.assertEqual(self.top_profile.get_store_payments(), result)

    def test_profile_created_signal_creates_a_user_store_payment_methods(self):

        self.assertEqual(
            StorePaymentMethod.objects.filter(profile=self.top_profile).count(), 
            6
        )

        cash = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=StorePaymentMethod.CASH_TYPE
        )
        mpesa = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=StorePaymentMethod.MPESA_TYPE
        )
        card = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=StorePaymentMethod.CARD_TYPE
        )
        points = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=StorePaymentMethod.POINTS_TYPE
        )
        debt = StorePaymentMethod.objects.get(
            profile=self.top_profile,
            payment_type=StorePaymentMethod.DEBT_TYPE
        )
        
        self.assertEqual(cash.name, 'Cash')
        self.assertEqual(mpesa.name, 'Mpesa')
        self.assertEqual(card.name, 'Card')
        self.assertEqual(points.name, 'Points')
        self.assertEqual(debt.name, 'Debt')

    def test_if_profile_image_is_deleted_when_profile_is_deleted(self):

        # Ensure delete_profile_assests_signal deletes the image and the 
        # profile's User
        
        # The Deletion of the user's image is handled in the url settings
         
        # Confirm there is a profile
        self.assertEqual(Profile.objects.all().count(), 1)

        profile = Profile.objects.get(user__email='john@gmail.com')

        # Confirm that the initial profile was created
        full_test_path = settings.MEDIA_ROOT + profile.image.url
        full_test_path = full_test_path.replace('//media/', '/')

        Image.open(full_test_path)
        
        # Delete profile
        profile = Profile.objects.get(user__email='john@gmail.com')
        profile.delete()

        # Confirm that the initial profile was deleted
        try:
            Image.open(full_test_path)
            self.fail()
        except: # pylint: disable=bare-except
            pass
 
    def test_delete_profile_assests_signal(self):

        # Ensure delete_profile_assests_signal deletes the profile's User
         
        # Confirm there is a profile
        self.assertEqual(Profile.objects.all().count(), 1)

        # Delete profile
        profile = Profile.objects.get(user__email='john@gmail.com')
        profile.delete()
        
        # Confirm the profiles were deleted
        self.assertEqual(Profile.objects.all().count(), 0)
                
        # Confirm the user was deleted
        user_exists = User.objects.filter(email='john@gmail.com').exists()
        self.assertEqual(False, user_exists)

# =========================== ProfileCount ===================================

class ProfileCountTestCase(TestCase):
    
    def setUp(self):
    
        #Create a user with email john@gmail.com
        self.user = create_new_user('john')

    def test_ProfileCount_fields_verbose_names(self):
        # Ensure all fields in ProfileCount have the correct verbose names and can be
        # found
               
        self.assertEqual(ProfileCount.objects.all().count(), 1)
        
        profile_count = ProfileCount.objects.get(profile=self.user.profile)

        self.assertEqual(profile_count._meta.get_field('created_date').verbose_name,'created date')
        
        fields = ([field.name for field in ProfileCount._meta.fields])
        
        self.assertEqual(len(fields), 3)

    def test__str__method(self):

        profile_count = ProfileCount.objects.get(profile=self.user.profile)

        # When profile_count has profile
        self.assertEqual(str(profile_count),'john@gmail.com') # Test the str method

        # When profile_count's profile has been delted
        profile = Profile.objects.get(user__email='john@gmail.com')
        profile.delete()

        profile_count = ProfileCount.objects.filter()[0]

        self.assertEqual(str(profile_count),'No profile') # Test the str method

    def test_get_created_date_method(self):
 
        profile_count = ProfileCount.objects.get(profile=self.user.profile)

        self.assertTrue(DateUtils.do_created_dates_compare(
            profile_count.get_created_date(self.user.get_user_timezone()))
        )
       
    def test_if_ProfileCount_wont_be_deleted_when_profile_is_deleted(self):
        
        profile = Profile.objects.get(user__email='john@gmail.com')
        
        profile.delete()
        
        # Confirm if the profile has been deleted
        self.assertEqual(Profile.objects.all().count(), 0)
        
        # Confirm number of profile counts
        self.assertEqual(ProfileCount.objects.all().count(), 1)

        profile_count = ProfileCount.objects.all()[0]
        
        self.assertEqual(profile_count.profile, None)


    """
    Ps has been tested below in ProfileInventoryValueTestCase
    """

"""
=========================== Profile Inventory value ===================================
"""
class ProfileInventoryValueTestCase(TestCase):

    def setUp(self):

        # Create users
        self.user1 = create_new_user('john')
        self.user2 = create_new_user('jack')

        self.profile1 = Profile.objects.get(user__email='john@gmail.com')
        self.profile2 = Profile.objects.get(user__email='jack@gmail.com')

        # Create stores
        self.store1 = create_new_store(self.profile1, 'Computer Store')
        self.store2 = create_new_store(self.profile1, 'Toy Store')
        self.store3 = create_new_store(self.profile2, 'Book Store')

        # Create a tax
        self.tax = create_new_tax(self.profile1, self.store1, 'Standard')

        # Create a category
        self.category = create_new_category(self.profile1, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.profile1, 'chris')

    def create_user2_products(self):

        Product.objects.create(
            profile=self.profile2,
            name="Band",
            price=1000,
            cost=200,
            sku='sku1',
            barcode='code123',
            track_stock=True
        )

        product = Product.objects.get(name="Band")

        product.stores.add(self.store3)

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store3, product=product)
        stock_level.units = 500


    def create_user1_products(self):

        """
        - store1

            * Shampoo
                Inventory value > 100.00 * 120.00 = 12000
                Retail value > 100.00 * 750.00 = 75000
            
            * Conditiner
                Inventory value > 150.00 * 160.00 = 24000
                Retail value > 150.00 * 950.00 = 142500
            
            * Small
                Inventory value > 100.00 * 800.00 = 80000
                Retail value > 100.00 * 1500.00 = 150000
            
            * Medium
                Inventory value > 120.00 * 800.00 = 96000
                Retail value > 120.00 * 1500.00 = 180000
            
            * Large
                Inventory value > 130.00 * 800.00 = 104000
                Retail value > 130.00 * 1500.00 = 195000
            
            Store inventory value  316000
            Store retail value  742500

        - store2

            * Shampoo
                Inventory value > 120.00 * 120.00 = 14400
                Retail value > 120.00 * 750.00 = 90000
                -----------------------
            * Conditiner
                Inventory value > 575.00 * 160.00 = 92000
                Retail value > 575.00 * 950.00 = 546250
                -----------------------
            * Small
                Inventory value > 200.00 * 800.00 = 160000
                Retail value > 200.00 * 1500.00 = 300000
                -----------------------
            * Medium
                Inventory value > 220.00 * 800.00 = 176000
                Retail value > 220.00 * 1500.00 = 330000
                -----------------------
            * Large
                Inventory value > 230.00 * 800.00 = 184000
                Retail value > 230.00 * 1500.00 = 345000

            Store inventory value  626400
            Store retail value  1611250

        Total inventory value  942400
        Total retail value  2353750
        """

        # Create a products
        Product.objects.create(
            profile=self.profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=750,
            cost=120,
            sku='sku1',
            barcode='code123',
            track_stock=True
        )

        Product.objects.create(
            profile=self.profile1,
            tax=self.tax,
            category=self.category,
            name="Conditiner",
            price=950,
            cost=160,
            sku='sku1',
            barcode='code123',
            track_stock=True
        )

        self.product1 = Product.objects.get(name="Shampoo")
        self.product2 = Product.objects.get(name="Conditiner")

        self.product1.stores.add(self.store1, self.store2)
        self.product2.stores.add(self.store1, self.store2)

        # Update stock level for product 1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 100
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product1)
        stock_level.units = 120
        stock_level.save()

        # Update stock level for product 2
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 150
        stock_level.save()

        stock_level = StockLevel.objects.get(store=self.store2, product=self.product2)
        stock_level.units = 575
        stock_level.save()

        # Create variants
        self.create_user1_variant_product_and_its_childs()

    def create_user1_variant_product_and_its_childs(self):

        Product.objects.create(
            profile=self.profile1,
            tax=self.tax,
            category=self.category,
            name="Variant master",
            price=150,
            cost=320,
            sku='sku1',
            barcode='code123',
            track_stock=True
        )

        master_product = Product.objects.get(name="Variant master")

        master_product.stores.add(self.store1, self.store2)

        # Create 3 variants for master product
        create_1d_variants(
            master_product=master_product,
            profile=self.profile1,
            store1=self.store1,
            store2=self.store2
        )

    def create_products(self):
        self.create_user1_products()
        self.create_user2_products()

        # Check if products for both users were created
        self.assertEqual(Product.objects.all().count(), 7)
    
    def test_get_inventory_valuation_from_a_single_store(self):

        self.create_products()

        result = {
            'inventory_value': '316000', 
            'retail_value': '742500',
            'potential_profit': '426500', 
            'margin': '57.44'
        }


        profile = Profile.objects.get(user__email='john@gmail.com')

        store_reg_nos = [store.reg_no for store in [self.store1]]

        self.assertEqual(profile.get_inventory_valuation(store_reg_nos), result)

    def test_get_inventory_valuation_from_multipile_stores(self):

        self.create_products()

        result = {
            'inventory_value': '942400', 
            'retail_value': '2353750', 
            'potential_profit': '1411350', 
            'margin': '59.96'
        }

        profile = Profile.objects.get(user__email='john@gmail.com')

        store_reg_nos = [store.reg_no for store in [self.store1, self.store2]]

        self.assertEqual(profile.get_inventory_valuation(store_reg_nos), result)

    def test_get_inventory_valuation_when_products_have_0_values(self):

        self.create_products()

        products = Product.objects.all()

        for p in products:
            p.price = 0
            p.cost = 0
            p.save()

        result = {
            'inventory_value': '0', 
            'retail_value': '0', 
            'potential_profit': '0', 
            'margin': '0'
        }

        profile = Profile.objects.get(user__email='john@gmail.com')

        store_reg_nos = [store.reg_no for store in [self.store1, self.store2]]

        self.assertEqual(profile.get_inventory_valuation(store_reg_nos), result)

    def test_get_inventory_valuation_from_all_stores(self):

        self.create_products()

        result = {
            'inventory_value': '942400', 
            'retail_value': '2353750', 
            'potential_profit': '1411350',
            'margin': '59.96'
        }

        profile = Profile.objects.get(user__email='john@gmail.com')

        self.assertEqual(profile.get_inventory_valuation(), result)
    
    def test_get_inventory_valuation_with_wrong_store_reg_no(self):

        self.create_products()

        result = {
            'inventory_value': '0', 
            'retail_value': '0', 
            'potential_profit': '0', 
            'margin': '0'
        }

        profile = Profile.objects.get(user__email='john@gmail.com')

        store_reg_nos = [454545454, 7545454]

        self.assertEqual(profile.get_inventory_valuation(store_reg_nos), result)

# =========================== EmployeeProfile ===================================
class EmployeeProfileExistenceTestCase(TestCase):
    
    def setUp(self):
        
        #Create a top user
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')

        self.store = create_new_store(self.top_profile, 'Computer Store')
        self.store2 = create_new_store(self.top_profile, 'Toy Store')

        #Create a manager user
        self.manager_user = create_new_manager_user("gucci", self.top_profile, self.store)
        
        self.manager_profile = EmployeeProfile.objects.get(user__email='gucci@gmail.com')
                
        #Create a employee user
        self.employee_user = create_new_cashier_user("ben", self.top_profile, self.store)


        # Create clusters
        self.cluster1 = StoreCluster.objects.create(
            profile=self.top_profile,
            name='Magadi'
        )
        self.cluster2 = StoreCluster.objects.create(
            profile=self.top_profile,
            name='Narok'
        )
        self.cluster3 = StoreCluster.objects.create(
            profile=self.top_profile,
            name='Amboseli'
        )

        # Add cluster to cashier_profile
        cashier_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        cashier_profile.clusters.add(self.cluster1, self.cluster2)
        cashier_profile.save()

        #Create a employee user
        self.cashier_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')

    '''
    def test_employee_profile_fields_verbose_names(self):
        # Ensure all fields in employee profile have the correct verbose names and can be
        # found
        
        self.assertEqual(self.cashier_profile._meta.get_field('image').verbose_name,'image')
        self.assertEqual(self.cashier_profile._meta.get_field('phone').verbose_name,'phone')
        self.assertEqual(self.cashier_profile._meta.get_field('join_date').verbose_name,'join date')
        self.assertEqual(self.cashier_profile._meta.get_field('location').verbose_name,'location')
        self.assertEqual(self.cashier_profile._meta.get_field('role_name').verbose_name,'role name')
        self.assertEqual(self.cashier_profile._meta.get_field('role_reg_no').verbose_name,'role reg no')
        self.assertEqual(self.cashier_profile._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(self.cashier_profile._meta.get_field('is_api_user').verbose_name,'is api user')
        
        fields = ([field.name for field in EmployeeProfile._meta.fields])
        
        self.assertEqual(len(fields), 14)

    def test_cashier_employee_profile_after_it_has_been_created(self):

        cashier_group = UserGroup.objects.get(
            master_user=self.user, ident_name='Cashier'
        )
                
        self.assertEqual(self.cashier_profile.profile, self.top_profile)
        self.assertEqual(
            self.cashier_profile.image.url, 
            f'/media/images/profiles/{self.cashier_profile.reg_no}_.jpg'
        )
        self.assertEqual(self.cashier_profile.phone,  254711223344)
        self.assertEqual(self.cashier_profile.reg_no, self.employee_user.reg_no) # Check if we have a valid reg_no
        self.assertEqual(self.cashier_profile.location,'Killimani')
        self.assertEqual(self.cashier_profile.role_name, cashier_group.ident_name)
        self.assertEqual(self.cashier_profile.role_reg_no, cashier_group.reg_no)
        self.assertEqual(self.cashier_profile.role_reg_no, cashier_group.reg_no)
        self.assertEqual(self.cashier_profile.is_api_user, False)

        # Check permissions
        group = UserGroup.objects.get(user__email='ben@gmail.com')

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]

        self.assertEqual(perms, [])

    def test_manager_employee_profile_after_it_has_been_created(self):

        manager_group = UserGroup.objects.get(
            master_user=self.user, ident_name='Manager'
        )
                
        self.assertEqual(self.manager_profile.profile, self.top_profile)
        self.assertEqual(
            self.manager_profile.image.url, 
            f'/media/images/profiles/{self.manager_profile.reg_no}_.jpg'
        )
        self.assertEqual(self.manager_profile.phone,  254721223333)
        self.assertEqual(self.manager_profile.reg_no, self.manager_user.reg_no) # Check if we have a valid reg_no
        self.assertEqual(self.manager_profile.location,'Upper Hill')
        self.assertEqual(self.manager_profile.role_name, manager_group.ident_name)
        self.assertEqual(self.manager_profile.role_reg_no, manager_group.reg_no)
        self.assertEqual(self.manager_profile.is_api_user, False)

        # Check permissions
        group = UserGroup.objects.get(user__email='gucci@gmail.com')

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]

        perms_codenames = [
            'can_view_shift_reports', 
            'can_manage_open_tickets', 
            'can_void_open_ticket_items', 
            'can_manage_items', 
            'can_refund_sale', 
            'can_open_drawer', 
            'can_reprint_receipt',
            'can_change_settings', 
            'can_apply_discount', 
            'can_change_taxes',
            'can_view_customers'
        ]

        self.assertEqual(perms, perms_codenames)

    def test__str__method(self):
        self.assertEqual(str(self.cashier_profile),'ben@gmail.com')

    def test_get_short_name_method(self):
        self.assertEqual(self.cashier_profile.get_short_name(),'Ben')

    def test_get_full_name_method(self):
        self.assertEqual(self.cashier_profile.get_full_name(),'Ben Linus')

    def test_get_join_date_method(self):
 
        self.assertTrue(DateUtils.do_created_dates_compare(
            self.cashier_profile.get_join_date(
                self.cashier_profile.user.get_user_timezone()
            ))
        )
          
    def test_get_last_login_date_method(self):
        # Confirm that get_last_login_date_method returns last_login_date
        # in local time 
        
        # The user's last login field is now empty since we havent logged so we have
        # insert it manually

        user = self.cashier_profile.user
        user.last_login = timezone.now()
        user.save()
        
        employee_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
                
        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            employee_profile.get_last_login_date(
                employee_profile.user.get_user_timezone()
            ))
        )

    def test_get_profile_image_url_method(self):
        self.assertEqual(self.cashier_profile.get_profile_image_url(), self.cashier_profile.image.url)

    def test_get_location_method(self):
        
        # Check result when locaiton has been provided
        self.assertEqual(self.cashier_profile.get_location(),'Killimani')
        
        # Unset location
        employee_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        employee_profile.location = ""
        employee_profile.save()
        
        employee_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        
        # Check result when location has not been provided
        self.assertEqual(employee_profile.get_location(),'Not set')
    
    def test_sync_employee_profile_phone_and_its_user_phone_method(self):
        
        # sync_employee_profile_phone_and_its_user_phone
                
        employee_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        employee_profile.phone = 254701444555
        employee_profile.save()

        u = User.objects.get(email='ben@gmail.com')
        self.assertEqual(u.phone, 254701444555)

    def test_create_employee_profile_count_method(self):
        """
        This method functionality has been tested in EmployeeProfileCountTestCase
        """

    def test_get_due_date_method(self):
        # Confirm that get_due_date_method returns created_date
        # in local time 
        
        employee_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        
        user_timezone = self.cashier_profile.user.get_user_timezone()

        self.assertEqual(
            employee_profile.get_due_date(user_timezone), 
            employee_profile.subscription.get_due_date(user_timezone)
        )

    def test_is_employee_qualified_method_returns_true(self):
        
        # is_employee_qualified_method
        
        # Ensure is_employee_qualified_method returns true if the employee is unlocked and 
        # it's subscription has not expired
        
        employee_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        employee_profile.unlocked=True
        employee_profile.save()
        
        s = Subscription.objects.get(employee_profile=self.cashier_profile)
        
        # 1 whole day to go #
        s.last_payment_date = timezone.now() - datetime.timedelta(days=1)
        s.due_date = timezone.now() + datetime.timedelta(days=2)
        s.save()
     
        s = Subscription.objects.get(employee_profile=self.cashier_profile)
        
        self.assertEqual(s.days_to_go, 1)
        self.assertEqual(s.expired, False)

        employee_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        
        self.assertEqual(employee_profile.is_employee_qualified(), True)
    
    def test_is_employee_qualified_method_returns_false(self):
        
        # is_employee_qualified_method
        
        # Ensure is_employee_qualified_method returns false if the employee is not unlocked and 
        # it's subscription has not expired
        
        employee_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        employee_profile.unlocked=False
        employee_profile.save()
                                                             
        s = Subscription.objects.get(employee_profile=self.cashier_profile)
        
        # 1 whole day to go #
        s.last_payment_date = timezone.now() - datetime.timedelta(days=1)
        s.due_date = timezone.now() + datetime.timedelta(days=2)
        s.save()
        
        s = Subscription.objects.get(employee_profile=self.cashier_profile)
        
        self.assertEqual(s.days_to_go, 1)
        self.assertEqual(s.expired, False)
        
        employee_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        
        self.assertEqual(employee_profile.is_employee_qualified(), False)

    def test_is_employee_qualified_method_returns_false2(self):
        
        # is_employee_qualified_method
        
        # Ensure is_employee_qualified_method returns false if the employee is unlocked and 
        # it's subscription has expired
        
        employee_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        employee_profile.unlocked=True
        employee_profile.save()
        
        s = Subscription.objects.get(employee_profile=self.cashier_profile)
        
        # 2 days late #
        s.last_payment_date = timezone.now() - datetime.timedelta(days=1)
        s.due_date = timezone.now() - datetime.timedelta(days=2)
        s.save()
        
        s = Subscription.objects.get(employee_profile=self.cashier_profile)
        
        self.assertEqual(s.days_to_go, -3)
        self.assertEqual(s.expired, True)
        
        employee_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        
        self.assertEqual(employee_profile.is_employee_qualified(), False)
    
    def test_get_registered_clusters_data_method(self):

        cashier = EmployeeProfile.objects.get(user__email='ben@gmail.com')

        self.assertEqual(
            cashier.get_registered_clusters_data(),
            [
                {
                    'name': self.cluster1.name, 
                    'reg_no': self.cluster1.reg_no
                }, 
                {
                    'name': self.cluster2.name, 
                    'reg_no': self.cluster2.reg_no
                } 
            ]
        )

    def test_get_registered_clusters_count_method(self):

        cashier = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        self.assertEqual(cashier.get_registered_clusters_count(), 2)

        # Remove one cluster
        cashier.clusters.remove(self.cluster1)

        cashier = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        self.assertEqual(cashier.get_registered_clusters_count(), 1)

    def test_get_available_stores_method(self):

        cashier = EmployeeProfile.objects.get(user__email='ben@gmail.com')

        stores_data = cashier.get_available_clusters_data()
        results = [
            {
                'name': self.cluster1.name, 
                'reg_no': self.cluster1.reg_no
            }, 
            {
                'name': self.cluster2.name, 
                'reg_no': self.cluster2.reg_no
            }, 
            {
                'name': self.cluster3.name, 
                'reg_no': self.cluster3.reg_no
            },
        ]

        self.assertEqual(len(stores_data), len(results))

        for store in stores_data:
            self.assertTrue(store in results)

    def test_get_clusters_store_names_method(self):

        cashier = EmployeeProfile.objects.get(user__email='ben@gmail.com')

        self.assertEqual(
            cashier.get_cluster_names_list().sort(),  
            [self.cluster1.name, self.cluster2.name].sort()
        )

    def test_if_cashier_can_be_created_without_a_cluster(self):

        # Remove clusters from cashier
        cashier = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        cashier.clusters.remove(self.cluster1, self.cluster2)
        cashier.save()

        self.assertEqual(cashier.clusters.all().count(), 0)

    def test_if_a_employee_profile_cant_be_assigned_a_top_user_model(self):
        
        user = User.objects.get(email='john@gmail.com')
        
        top_profile = Profile.objects.get(user__email='john@gmail.com')
        employee_profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        
        # Try creating a EmployeeProfile for a top level user#
        EmployeeProfile.objects.create(
            user=user,
            profile=top_profile,
        )
        
        employee_profile = EmployeeProfile.objects.filter(user__email='john@gmail.com').exists()
        
        self.assertEqual(employee_profile, False)
    '''

    def test_employee_profile_model_manager(self):

        # Create an api user for the top profile
        self.top_profile.user.create_api_user() 

        # Ensure the model manager returns only non api user employees
        employees = EmployeeProfile.objects.filter().order_by('id')
        self.assertEqual(employees.count(), 2)

        self.assertEqual(employees[0].user.email, 'gucci@gmail.com')
        self.assertEqual(employees[1].user.email, 'ben@gmail.com')

        # Ensure the model manager returns all employees
        employees = EmployeeProfile.objects.all_filter().order_by('id')
        self.assertEqual(employees.count(), 3)

        self.assertEqual(employees[0].user.email, 'gucci@gmail.com')
        self.assertEqual(employees[1].user.email, 'ben@gmail.com')
        self.assertEqual(
            employees[2].user.email, 
            f'api-{employees[2].reg_no}-{employees[2].profile.user.email}'
        )

    def test_delete_employee_profile_assests_signal(self):
    
        # Confirm there is an employee profile
        self.assertEqual(EmployeeProfile.objects.all().count(), 2)
        
        EmployeeProfile.objects.all().delete()
        
        # Confirm the profiles were deleted
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)

        self.assertEqual(User.objects.filter(email='ben@gmail.com').exists(), False)
        self.assertEqual(User.objects.filter(email='gucci@gmail.com').exists(), False)

    def test_if_profile_image_is_deleted_when_profile_is_deleted(self):

        # Confirm employee profiles
        self.assertEqual(EmployeeProfile.objects.all().count(), 2)

        profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')

        # Confirm that the initial profile was created
        full_test_path = settings.MEDIA_ROOT + profile.image.url
        full_test_path = full_test_path.replace('//media/', '/')

        Image.open(full_test_path)
        
        # Delete profile
        profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        profile.delete()

        # Confirm that the initial profile was deleted
        try:
            Image.open(full_test_path)
            self.fail()
        except: # pylint: disable=bare-except
            pass
 
    def test_delete_profile_assests_signal_deletes_user(self):

        # Confirm employee profiles
        self.assertEqual(EmployeeProfile.objects.all().count(), 2)

        # Delete profile
        profile = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        profile.delete()
        
        # Confirm the profiles were deleted
        self.assertEqual(EmployeeProfile.objects.all().count(), 1)
                
        # Confirm the user was deleted
        user_exists = User.objects.filter(email='ben@gmail.com').exists()
        self.assertEqual(False, user_exists)
    
# =========================== EmployeeProfileCount ===================================
class EmployeeProfileCountTestCase(TestCase):
    
    def setUp(self):

        #Create a user with email john@gmail.com
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')

        self.store = create_new_store(self.top_profile, 'Computer Store')
        
        #Create a employee user with email james@gmail.com
        create_new_cashier_user("james", self.top_profile, self.store)

        self.cashier_profile = EmployeeProfile.objects.get(user__email='james@gmail.com')

    def test_EmployeeProfileCount_fields_verbose_names(self):
        # Ensure all fields in EmployeeProfileCount have the correct verbose names and can be
        # found
               
        self.assertEqual(EmployeeProfileCount.objects.all().count(), 1)
        
        employee_profile_count = EmployeeProfileCount.objects.get(
            employee_profile=self.cashier_profile)

        self.assertEqual(employee_profile_count._meta.get_field(
            'created_date').verbose_name,'created date')
        
        fields = ([field.name for field in EmployeeProfileCount._meta.fields])
        
        self.assertEqual(len(fields), 4)

    def test_EmployeeProfileCount_existence(self):
        
        employee_profile_count = EmployeeProfileCount.objects.get(
            employee_profile=self.cashier_profile)

        self.assertEqual(employee_profile_count.profile, self.top_profile) 

    def test__str__method(self):

        employee_profile_count = EmployeeProfileCount.objects.get(
            employee_profile=self.cashier_profile)

        # When employee_profile_count has profile
        self.assertEqual(str(employee_profile_count),'james@gmail.com')

        # When employee_profile_count's profile has been delted
        employee_profile = EmployeeProfile.objects.get(user__email='james@gmail.com')
        employee_profile.delete()

        employee_profile_count = EmployeeProfileCount.objects.filter()[0]

        self.assertEqual(str(employee_profile_count),'No profile') 

    def test_get_created_date_method(self):
  
        employee_profile_count = EmployeeProfileCount.objects.get(
            employee_profile=self.cashier_profile)
     
        self.assertTrue(DateUtils.do_created_dates_compare(
            employee_profile_count.get_created_date(
                self.cashier_profile.user.get_user_timezone()))
        )

    def test_if_EmployeeProfileCount_wont_be_deleted_when_profile_is_deleted(self):
        
        employee_profile = EmployeeProfile.objects.get(
            user__email='james@gmail.com')
        
        employee_profile.delete()
        
        # Confirm if the employee profile has been deleted
        self.assertEqual(EmployeeProfile.objects.all().count(), 0)
        
        # Confirm number of employee profile counts
        self.assertEqual(EmployeeProfileCount.objects.all().count(), 1)

        employee_profile_count = EmployeeProfileCount.objects.all()[0]
    
        self.assertEqual(employee_profile_count.profile, self.top_profile)
        self.assertEqual(employee_profile_count.employee_profile, None)

"""
=========================== Customer ===================================
"""  
class CustomerTestCase(TestCase):
    
    def setUp(self):

        #Create a top user1
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')
        
        #Create a store
        self.store = create_new_store(self.top_profile , 'Computer Store')

        #Create a tax
        self.tax = create_new_tax(self.top_profile , self.store, 'Standard')

        #Create a category
        self.category = create_new_category(self.top_profile , 'Hair')

        #Create a discount
        self.discount = create_new_discount(self.top_profile, self.store, 'Happy hour')

        # Create a customer user
        self.customer = create_new_customer(self.top_profile, 'chris')

        # Create cluster
        self.cluster = StoreCluster.objects.create(
            profile=self.top_profile,
            name='Magadi'
        )

        # Add cluster to customer
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        customer.cluster = self.cluster
        customer.save()

    def create_2_paid_sales_for_customer(self):
        """
        This reduces the repeatability of the following model creations

        Creates 2 paid (4000) sales for the customer
        """

        customer = Customer.objects.get(reg_no=self.customer.reg_no)

        # Product 1
        Product.objects.create(
            profile=self.top_profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        product1 = Product.objects.get(name="Shampoo")

        # Create receipt1
        receipt1 = Receipt.objects.create(
            user=self.user,
            store=self.store,
            customer=customer,
            discount_amount=401.00,
            subtotal_amount=2000,
            total_amount=2000.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True
        )

        # Create sale1
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=product1,
            product_info={'name': product1.name},
            price=1750,
            units=7
        )

        # Create sale2
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=product1,
            product_info={'name': product1.name},
            price=1750,
            units=5
        )

        # Product 2
        Product.objects.create(
            profile=self.top_profile,
            tax=self.tax,
            category=self.category,
            name="Gel",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        product2 = Product.objects.get(profile=self.top_profile, name="Gel")

        # Create receipt2
        receipt2 = Receipt.objects.create(
            user=self.user,
            store=self.store,
            customer=customer,
            discount_amount=401.00,
            subtotal_amount=2000,
            total_amount=2000.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True
        )

        # Create sale3
        ReceiptLine.objects.create(
            receipt=receipt2,
            product=product2,
            product_info={'name': product2.name},
            price=1750,
            units=7
        )

    def create_1_paid_and_1_updaid_sales_for_customer(self):
        """
        This reduces the repeatability of the following model creations

        Creates 1 paid (2000) and 1 updaid (2000) sales for the customer
        """

        customer = Customer.objects.get(reg_no=self.customer.reg_no)

        # Product 1
        Product.objects.create(
            profile=self.top_profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        product1 = Product.objects.get(name="Shampoo")

        # Create receipt1
        receipt1 = Receipt.objects.create(
            user=self.user,
            store=self.store,
            customer=customer,
            discount_amount=401.00,
            subtotal_amount=2000,
            total_amount=2000.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True
        )

        # Create sale1
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=product1,
            product_info={'name': product1.name},
            price=1750,
            units=7
        )

        # Create sale2
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=product1,
            product_info={'name': product1.name},
            price=1750,
            units=5
        )

        # Product 2
        Product.objects.create(
            profile=self.top_profile,
            tax=self.tax,
            category=self.category,
            name="Gel",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        product2 = Product.objects.get(profile=self.top_profile, name="Gel")

        # Create receipt2
        receipt2 = Receipt.objects.create(
            user=self.user,
            store=self.store,
            customer=customer,
            discount_amount=401.00,
            subtotal_amount=2000,
            total_amount=2000.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=False
        )

        # Create sale3
        ReceiptLine.objects.create(
            receipt=receipt2,
            product=product2,
            product_info={'name': product2.name},
            price=1750,
            units=7
        )

    def create_2_unpaid_sales_for_customer(self):
        """
        This reduces the repeatability of the following model creations

        Creates 2 unpaid (4000) sales for the customer
        """

        customer = Customer.objects.get(reg_no=self.customer.reg_no)

        # Product 1
        Product.objects.create(
            profile=self.top_profile,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        product1 = Product.objects.get(name="Shampoo")

        # Create receipt1
        receipt1 = Receipt.objects.create(
            user=self.user,
            store=self.store,
            customer=customer,
            discount_amount=401.00,
            subtotal_amount=2000,
            total_amount=2000.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=False
        )

        # Create sale1
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=product1,
            product_info={'name': product1.name},
            price=1750,
            units=7
        )

        # Create sale2
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=product1,
            product_info={'name': product1.name},
            price=1750,
            units=5
        )

        # Product 2
        Product.objects.create(
            profile=self.top_profile,
            tax=self.tax,
            category=self.category,
            name="Gel",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        product2 = Product.objects.get(profile=self.top_profile, name="Gel")

        # Create receipt2
        receipt2 = Receipt.objects.create(
            user=self.user,
            store=self.store,
            customer=customer,
            discount_amount=401.00,
            subtotal_amount=2000,
            total_amount=2000.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=False
        )

        # Create sale3
        ReceiptLine.objects.create(
            receipt=receipt2,
            product=product2,
            product_info={'name': product2.name},
            price=1750,
            units=7
        )

    def test_when_customer_is_created_or_saved_mwingi_connector_is_notified(self):

        # Test when customer is created
        customer = Customer.objects.get(profile=self.top_profile)
        
        content = get_test_firebase_sender_log_content(only_include=['connector_customer'])
    
        self.assertEqual(
            content, 
            [
                {
                    'payload': {
                        'model': 'connector_customer',
                        'payload': f'{customer.reg_no} payload data'}},
                {
                    'payload': {
                        'model': 'connector_customer',
                        'payload': f'{customer.reg_no} payload data'
                    }
                }
            ]
        )

        # Test when customer is saved
        customer.save()

        content = get_test_firebase_sender_log_content(only_include=['connector_customer'])

        self.assertEqual(
            content, 
            [
                {
                    'payload': {
                        'model': 'connector_customer',
                        'payload': f'{customer.reg_no} payload data'
                    }
                },
                {
                    'payload': {
                        'model': 'connector_customer',
                        'payload': f'{customer.reg_no} payload data'
                    }
                },
                {
                    'payload': {
                        'model': 'connector_customer',
                        'payload': f'{customer.reg_no} payload data'
                    }
                }
            ]
        )

    def test_customer_fields_verbose_names(self):

        customer = Customer.objects.get(profile=self.top_profile)
            
        self.assertEqual(customer._meta.get_field('name').verbose_name,'name')
        self.assertEqual(customer._meta.get_field('email').verbose_name,'email')
        self.assertEqual(customer._meta.get_field('village_name').verbose_name,'village name')
        self.assertEqual(customer._meta.get_field('phone').verbose_name,'phone')
        self.assertEqual(customer._meta.get_field('address').verbose_name,'address')
        self.assertEqual(customer._meta.get_field('city').verbose_name,'city')
        self.assertEqual(customer._meta.get_field('region').verbose_name,'region')
        self.assertEqual(customer._meta.get_field('postal_code').verbose_name,'postal code')
        self.assertEqual(customer._meta.get_field('country').verbose_name,'country')
        self.assertEqual(customer._meta.get_field('credit_limit').verbose_name,'credit limit')
        self.assertEqual(customer._meta.get_field('current_debt').verbose_name,'current debt')
        self.assertEqual(customer._meta.get_field('points').verbose_name,'points')
        self.assertEqual(customer._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(customer._meta.get_field('created_date').verbose_name,'created date')

        fields = ([field.name for field in Customer._meta.fields])
        
        self.assertEqual(len(fields), 18)

    def test_customer_fields_after_it_has_been_created(self):
        """
        Product fields
        
        Ensure a customer has the right fields after it has been created
        """
        customer = Customer.objects.get(profile=self.top_profile)
        
        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(customer.profile, self.top_profile)
        
        self.assertEqual(customer.cluster, self.cluster)
        self.assertEqual(customer.name, "Chris Evans")
        self.assertEqual(customer.email, "chris@gmail.com")
        self.assertEqual(customer.village_name, "Village")
        self.assertEqual(customer.phone, 254710101010)
        self.assertEqual(customer.address, 'Donholm')
        self.assertEqual(customer.city, 'Nairobi')
        self.assertEqual(customer.region, 'Africa')
        self.assertEqual(customer.postal_code, '11011')
        self.assertEqual(customer.country, 'Kenya')
        self.assertEqual(customer.customer_code, f'Cu_{customer.reg_no}')
        self.assertEqual(customer.credit_limit, 0)
        self.assertEqual(customer.current_debt, 0)
        self.assertEqual(customer.points, 0)
        self.assertTrue(customer.reg_no > 100000) # Check if we have a valid reg_no
        self.assertEqual((customer.created_date).strftime("%B, %d, %Y"), today)

    def test_if_customer_can_be_created_without_a_cluster(self):

        # Add cluster to customer
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        customer.cluster = None
        customer.save()

        self.assertEqual(customer.cluster, None)

    def test_if_customer_code_can_be_edited(self):

        customer = Customer.objects.get(profile=self.top_profile)

        customer.customer_code = 'Customer code'
        customer.save()

        self.assertEqual(customer.customer_code, 'Customer code')

        # Test if an empty customer code will be filled automatically
        customer.customer_code = ''
        customer.save()

        self.assertEqual(customer.customer_code, f'Cu_{customer.reg_no}')

    def test__str__method(self):
        customer = Customer.objects.get(profile=self.top_profile)
        self.assertEqual(str(customer), customer.email)

    def test_get_non_null_phone_method(self):

        # When customer has phone
        customer = Customer.objects.get(profile=self.top_profile)
        self.assertEqual(customer.get_non_null_phone(), customer.phone)

        # When cusomer has null phone
        customer = Customer.objects.get(profile=self.top_profile)
        customer.phone = None
        customer.save()

        customer = Customer.objects.get(profile=self.top_profile)
        self.assertEqual(customer.get_non_null_phone(), '')

    def test_get_location_desc_method1(self):

        customer = Customer.objects.get(profile=self.top_profile)

        # When all location fields are available
        self.assertEqual(
            customer.get_location_desc(), 
            f'{customer.address}, {customer.city}, {customer.region}, {customer.postal_code}, {customer.country}'
        )

        # When country field is not available
        customer.country = ''
        customer.save()

        self.assertEqual(
            customer.get_location_desc(), 
            f'{customer.address}, {customer.city}, {customer.region}, {customer.postal_code}'
        )

        # When postal code field is not available
        customer.postal_code = ''
        customer.save()

        self.assertEqual(
            customer.get_location_desc(), 
            f'{customer.address}, {customer.city}, {customer.region}'
        )

        # When region field is not available
        customer.region = ''
        customer.save()

        self.assertEqual(
            customer.get_location_desc(), f'{customer.address}, {customer.city}'
        )

        # When city field is not available
        customer.city = ''
        customer.save()

        self.assertEqual(customer.get_location_desc(), f'{customer.address}')

        # When all location fields are not available
        customer.address = ''
        customer.save()

        self.assertEqual(customer.get_location_desc(), '')

    def test_get_location_desc_method2(self):

        customer = Customer.objects.get(profile=self.top_profile)

        # When all location fields are available
        self.assertEqual(
            customer.get_location_desc(), 
            f'{customer.address}, {customer.city}, {customer.region}, {customer.postal_code}, {customer.country}'
        )

        # When address field is not available
        customer.address = ''
        customer.save()

        self.assertEqual(
            customer.get_location_desc(), 
            f'{customer.city}, {customer.region}, {customer.postal_code}, {customer.country}'
        )

        # When city field is not available
        customer.city = ''
        customer.save()

        self.assertEqual(
            customer.get_location_desc(), 
            f'{customer.region}, {customer.postal_code}, {customer.country}'
        )

        # When region field is not available
        customer.region = ''
        customer.save()

        self.assertEqual(
            customer.get_location_desc(), f'{customer.postal_code}, {customer.country}'
        )

        # When postal code field is not available
        customer.postal_code = ''
        customer.save()

        self.assertEqual(customer.get_location_desc(), f'{customer.country}')

        # When all locaion fields are not available
        customer.country = ''
        customer.save()

        self.assertEqual(customer.get_location_desc(), '')

    def test_get_created_date_method(self):

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
                     
        self.assertTrue(DateUtils.do_created_dates_compare(
            customer.get_created_date(self.user.get_user_timezone()))
        )

    def test_get_currency_initials_method(self):
        customer = Customer.objects.get(profile=self.top_profile)
        self.assertEqual(customer.get_currency_initials(), "Usd")

    def test_get_sales_count_method(self):

        #######  Confirm get_sales_count when a customer does not have sales
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.get_sales_count(), 0)

        # Creates 2 unpaid (4000) sales for the customer
        self.create_2_paid_sales_for_customer()
        
        #######  Confirm get_sales_count when a customer has sales
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.get_sales_count(), 19)
    
    def test_get_total_visits_method(self):

        #######  Confirm get_total_visits when a customer does not have sales
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.get_total_visits(), 0)

        # Creates 2 unpaid (4000) sales for the customer
        self.create_2_paid_sales_for_customer()

        #######  Confirm get_total_visits when a customer has sales
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.get_total_visits(), 2)
  
    def test_get_credit_limit_method(self):

        # Test when limit is 0
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.get_credit_limit_desc(), 'Usd 0.00')

        # Test when debt is not 0
        customer.credit_limit = 2500
        customer.save()

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.get_credit_limit_desc(), 'Usd 2500.00')

    def test_customer_get_cluster_data_method(self):

        # When customer has cluster
        customer = Customer.objects.get(profile=self.top_profile)

        self.assertEqual(
            customer.get_cluster_data(), 
            {
                'name': self.cluster.name, 
                'reg_no': self.cluster.reg_no
            }
        )

        # When customer has no cluster
        customer = Customer.objects.get(profile=self.top_profile)
        customer.cluster = None
        customer.save()

        customer = Customer.objects.get(profile=self.top_profile)

        self.assertEqual(
            customer.get_cluster_data(), 
            {
                'name': None, 
                'reg_no': None
            }
        )

    def test_get_current_debt_desc(self):

        # Test when debt is 0
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.get_current_debt_desc(), 'Usd 0.00')

        # Test when debt is not 0
        # Creates 2 unpaid (4000) sales for the customer
        self.create_2_unpaid_sales_for_customer()

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.get_current_debt_desc(), 'Usd 4000.00')

    def test_if_is_eligible_for_debt_when_credit_limit_is_0(self):

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.credit_limit, 0)
        self.assertEqual(customer.is_eligible_for_debt(2000), False)

    def test_if_is_eligible_for_debt_when_there_are_paid_sales(self):

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        customer.credit_limit = 2000
        customer.save()

        # Creates 2 paid (4000) sales for the customer
        self.create_2_paid_sales_for_customer()

        #######  Confirm is_eligible_for_debt when a customer has paid sales
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.is_eligible_for_debt(2000), True)

    def test_if_is_eligible_for_debt_when_credit_limit_has_not_been_exceeded(self):

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        customer.credit_limit = 2000
        customer.save()

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.is_eligible_for_debt(2000), True)

    def test_if_is_eligible_for_debt_when_debt_wont_be_exceeded_passed_the_credit_limit(self):
        """
        Test if a customer has a debt, they will be eligible for another debt
        as long the new addition of debt wont exceed the allowed credit limit

        For example if a customer has a credit limit of 4000 and they already have
        a 2000 debt, they should be allowed to add another 2000 debt
        """

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        customer.credit_limit = 4000
        customer.save()

        # Creates 1 paid (2000) and 1 updaid (2000) sales for the customer
        self.create_1_paid_and_1_updaid_sales_for_customer()

        #######  Confirm is_eligible_for_debt when a customer has 1 unpaid sale
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.is_eligible_for_debt(2000), True)

    def test_if_is_eligible_for_debt_when_credit_limit_has_been_exceeded(self):

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        customer.credit_limit = 2000
        customer.save()

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.is_eligible_for_debt(2001), False)

    def test_if_is_eligible_for_debt_when_debt_is_about_to_be_exceeded_passed_the_credit_limit(self):
        """
        Test if a customer has a debt, they wont be eligible for another debt
        when the new addition of debt will exceed the allowed credit limit

        For example if a customer has a credit limit of 2000 and they already have
        a 2000 debt, they should not be allowed to add even another 1 of debt
        """

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        customer.credit_limit = 2000
        customer.save()

        # Creates 1 paid (2000) and 1 updaid (2000) sales for the customer
        self.create_1_paid_and_1_updaid_sales_for_customer()

        #######  Confirm is_eligible_for_debt when a customer has 1 unpaid sale
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.is_eligible_for_debt(1), False)

    def test_if_is_eligible_for_point_payment_method_when_customer_points_is_0(self):

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.top_profile)
        loyalty.value = 6
        loyalty.save()

        # Confirm customer
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(customer.points, 0)

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(
            customer.is_eligible_for_point_payment(120), 
            (False, False)
        )

    def test_if_is_eligible_for_point_payment_method_when_loyalty_settings_value_is_0(self):

        # Confirm loyalty setting
        loyalty = LoyaltySetting.objects.get(profile=self.top_profile)
        self.assertEqual(loyalty.value, 0)

        # Give customer pints
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        customer.points = 120
        customer.save()

      
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(
            customer.is_eligible_for_point_payment(120), 
            (False, False)
        )
    
    def test_if_is_eligible_for_point_payment_method_when_amount_has_not_been_exceeded(self):

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.top_profile)
        loyalty.value = 6
        loyalty.save()

        # Give customer pints
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        customer.points = 120
        customer.save()

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(
            customer.is_eligible_for_point_payment(120), 
            (True, True)
        )

    def test_if_is_eligible_for_point_payment_method_when_amount_has_been_exceeded(self):

        # Update loyalty settings
        loyalty = LoyaltySetting.objects.get(profile=self.top_profile)
        loyalty.value = 6
        loyalty.save()

        # Give customer pints
        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        customer.points = 120
        customer.save()

        customer = Customer.objects.get(reg_no=self.customer.reg_no)
        self.assertEqual(
            customer.is_eligible_for_point_payment(121), 
            (True, False)
        )

    def test_firebase_messages_are_sent_correctly(self):

        Customer.objects.all().delete()
        empty_logfiles()

        #Create a customer
        customer = create_new_customer(self.top_profile, 'chris')

        content = get_test_firebase_sender_log_content(only_include=['customer'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.top_profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'customer', 
                'action_type': 'create', 
                'name': 'Chris Evans', 
                'email': 'chris@gmail.com', 
                'village_name': 'Village', 
                'non_null_phone': '254710101010', 
                'phone': '254710101010', 
                'address': 'Donholm', 
                'city': 'Nairobi', 
                'region': 'Africa', 
                'postal_code': '11011', 
                'country': 'Kenya', 
                'customer_code': customer.customer_code, 
                'credit_limit': '0', 
                'current_debt': '0', 
                'cluster_data': str(customer.get_cluster_data()),
                'points': '0', 
                'reg_no': str(customer.reg_no)
            }
        }

        self.assertEqual(content[0], result)
    

        # Edit customer
        customer = Customer.objects.get(profile=self.top_profile)
        customer.name = 'New name'
        customer.phone = 254710101011
        customer.save()

        content = get_test_firebase_sender_log_content(only_include=['customer'])
        self.assertEqual(len(content), 2)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.top_profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'customer', 
                'action_type': 'edit', 
                'name': 'New name', 
                'email': 'chris@gmail.com', 
                'village_name': 'Village', 
                'non_null_phone': '254710101011', 
                'phone': '254710101011', 
                'address': 'Donholm', 
                'city': 'Nairobi', 
                'region': 'Africa', 
                'postal_code': '11011', 
                'country': 'Kenya', 
                'customer_code': customer.customer_code, 
                'credit_limit': '0.00', 
                'current_debt': '0.00', 
                'cluster_data': str(customer.get_cluster_data()),
                'points': '0', 
                'reg_no': str(customer.reg_no)
            }
        }

        self.assertEqual(content[1], result)
    

        #Delete customer
        Customer.objects.get(name='New name').delete()

        content = get_test_firebase_sender_log_content(only_include=['customer'])
        self.assertEqual(len(content), 3)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.top_profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'customer', 
                'action_type': 'delete', 
                'name': 'New name', 
                'email': 'chris@gmail.com', 
                'village_name': 'Village', 
                'non_null_phone': '254710101011', 
                'phone': '254710101011', 
                'address': 'Donholm', 
                'city': 'Nairobi', 
                'region': 'Africa', 
                'postal_code': '11011', 
                'country': 'Kenya', 
                'customer_code': customer.customer_code, 
                'credit_limit': '0.00', 
                'current_debt': '0.00', 
                'cluster_data': str(customer.get_cluster_data()),
                'points': '0', 
                'reg_no': str(customer.reg_no)
            }
        }

        self.assertEqual(content[2], result)


"""
=========================== CustomerCount ===================================
"""  
# CustomerCount
class CustomerCountTestCase(TestCase):
    
    def setUp(self):
        
        #Create a top user1
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')
        
        self.store = create_new_store(self.top_profile, 'Computer Store')

        # Create a customer user
        self.customer = create_new_customer(self.top_profile, 'chris')

    def test_CustomerCount_fields_verbose_names(self):
        """
        Ensure all fields in ProductCount have the correct verbose names and can be
        found
        """        
        customer_count = CustomerCount.objects.get(profile=self.top_profile)

        self.assertEqual(customer_count._meta.get_field('created_date').verbose_name,'created date')
        
        fields = ([field.name for field in CustomerCount._meta.fields])
        
        self.assertEqual(len(fields), 4)
      
    def test_CustomerCount_existence(self):

        customer_count = CustomerCount.objects.get(profile=self.top_profile)

        today = (timezone.now()).strftime("%B, %d, %Y")
        
        self.assertEqual(customer_count.profile, self.top_profile)
        self.assertEqual((customer_count.created_date).strftime("%B, %d, %Y"), today)

    def test_get_created_date_method(self):
        
        customer_count = CustomerCount.objects.get(profile=self.top_profile)
      
        self.assertTrue(DateUtils.do_created_dates_compare(
            customer_count.get_created_date(self.user.get_user_timezone()))
        )
  
    def test_if_CustomerCount_wont_be_deleted_when_customer_is_deleted(self):
        
        self.customer.delete()
        
        # Confirm if the customer has been deleted
        self.assertEqual(Customer.objects.all().count(), 0)
        
        # Confirm number of customer counts
        self.assertEqual(CustomerCount.objects.all().count(), 1)
        
    def test_if_CustomerCount_wont_be_deleted_when_profile_is_deleted(self):
        
        self.top_profile.delete()
        
        # Confirm if the profile has been deleted
        self.assertEqual(Profile.objects.all().count(), 0)
        
        # Confirm number of customer counts
        self.assertEqual(CustomerCount.objects.all().count(), 1)

    def test_if_CustomerCount_wont_be_deleted_when_store_is_deleted(self):
        
        self.store.delete()
        
        # Confirm if the store has been deleted
        self.assertEqual(Store.objects.all().count(), 0)
        
        # Confirm number of customer counts
        self.assertEqual(CustomerCount.objects.all().count(), 1)


"""
=========================== LoyaltySetting ===================================
"""  
class LoyaltySettingTestCase(TestCase):
    
    def setUp(self):
        
        #Create a top user1
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')
        
        self.store = create_new_store(self.top_profile, 'Computer Store')

        self.l_setting = LoyaltySetting.objects.get(profile=self.top_profile)

    def test_mode_fields_verbose_names(self):

        self.assertEqual(self.l_setting._meta.get_field('value').verbose_name,'value')
        
        fields = ([field.name for field in LoyaltySetting._meta.fields])
        
        self.assertEqual(len(fields), 3)

    def test_model_after_user_has_been_created(self):

        self.assertEqual(self.l_setting.value, 0)

    def test_firebase_messages_are_sent_correctly(self):

        content = get_test_firebase_sender_log_content(only_include=['loyalty'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.top_profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'loyalty', 
                'action_type': 'edit', 
                'value': '0.0'
            }
        }

        self.assertEqual(content[0], result)

        # Edit model
        l_setting = LoyaltySetting.objects.get(profile=self.top_profile)
        l_setting.value = 20.04
        l_setting.save()

        content = get_test_firebase_sender_log_content(only_include=['loyalty'])
        self.assertEqual(len(content), 2)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.top_profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'loyalty', 
                'action_type': 'edit', 
                'value': '20.04'
            }
        }

        self.assertEqual(content[1], result)


"""
=========================== ReceiptSetting ===================================
"""  
class ReceiptSettingTestCase(TestCase):
    
    def setUp(self):
        
        #Create a top user1
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')
        
        self.store = create_new_store(self.top_profile, 'Computer Store')

        r_setting = ReceiptSetting.objects.get(profile=self.top_profile)
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

    def test_mode_fields_verbose_names(self):
              
        r_setting = ReceiptSetting.objects.get(profile=self.top_profile)

        self.assertEqual(r_setting._meta.get_field('header1').verbose_name,'header1')
        self.assertEqual(r_setting._meta.get_field('header2').verbose_name,'header2')
        self.assertEqual(r_setting._meta.get_field('header3').verbose_name,'header3')
        self.assertEqual(r_setting._meta.get_field('header4').verbose_name,'header4')
        self.assertEqual(r_setting._meta.get_field('header5').verbose_name,'header5')
        self.assertEqual(r_setting._meta.get_field('header6').verbose_name,'header6')

        self.assertEqual(r_setting._meta.get_field('footer1').verbose_name,'footer1')
        self.assertEqual(r_setting._meta.get_field('footer2').verbose_name,'footer2')
        self.assertEqual(r_setting._meta.get_field('footer3').verbose_name,'footer3')
        self.assertEqual(r_setting._meta.get_field('footer4').verbose_name,'footer4')
        self.assertEqual(r_setting._meta.get_field('footer5').verbose_name,'footer5')
        self.assertEqual(r_setting._meta.get_field('footer6').verbose_name,'footer6')

        self.assertEqual(r_setting._meta.get_field('reg_no').verbose_name,'reg no')
        
        fields = ([field.name for field in ReceiptSetting._meta.fields])
        
        self.assertEqual(len(fields), 16)

    def test_model_after_user_has_been_created(self):

        r_setting = ReceiptSetting.objects.get(profile=self.top_profile)
        
        self.assertEqual(r_setting.header1, 'Header1')
        self.assertEqual(r_setting.header2, 'Header2')
        self.assertEqual(r_setting.header3, 'Header3')
        self.assertEqual(r_setting.header4, 'Header4')
        self.assertEqual(r_setting.header5, 'Header5')
        self.assertEqual(r_setting.header6, 'Header6')

        self.assertEqual(r_setting.footer1, 'Footer1')
        self.assertEqual(r_setting.footer2, 'Footer2')
        self.assertEqual(r_setting.footer3, 'Footer3')
        self.assertEqual(r_setting.footer4, 'Footer4')
        self.assertEqual(r_setting.footer5, 'Footer5')
        self.assertEqual(r_setting.footer6, 'Footer6')

        self.assertTrue(r_setting.reg_no > 100000) # Check if we have a valid reg_no

"""
=========================== UserGeneralSetting ===================================
"""  
class UserGeneralSettingTestCase(TestCase):
    
    def setUp(self):
        
        #Create a top user1
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')
        
        self.store = create_new_store(self.top_profile, 'Computer Store')

        self.g_setting = UserGeneralSetting.objects.get(profile=self.top_profile)

    def test_mode_fields_verbose_names(self):

        self.assertEqual(self.g_setting._meta.get_field('enable_shifts')\
            .verbose_name,'enable shifts')
        self.assertEqual(self.g_setting._meta.get_field('enable_open_tickets')\
            .verbose_name,'enable open tickets')
        self.assertEqual(self.g_setting._meta.get_field('enable_low_stock_notifications')\
            .verbose_name,'enable low stock notifications')
        self.assertEqual(self.g_setting._meta.get_field('enable_negative_stock_alerts')\
            .verbose_name,'enable negative stock alerts')
        self.assertEqual(self.g_setting._meta.get_field('reg_no').verbose_name,'reg no')
        
        fields = ([field.name for field in UserGeneralSetting._meta.fields])
        
        self.assertEqual(len(fields), 7)

    def test_model_after_user_has_been_created(self):

        self.assertEqual(self.g_setting.enable_shifts, False)
        self.assertEqual(self.g_setting.enable_open_tickets, False)
        self.assertEqual(self.g_setting.enable_low_stock_notifications, True)
        self.assertEqual(self.g_setting.enable_negative_stock_alerts, True)
        self.assertTrue(self.g_setting.reg_no > 100000) # Check if we have a valid reg_no

    def test_get_settings_dict_method(self):

        self.assertEqual(
            self.g_setting.get_settings_dict(), 
            {
                'enable_shifts': False, 
                'enable_open_tickets': False, 
                'enable_low_stock_notifications': True, 
                'enable_negative_stock_alerts': True
            }
        )

    def test_firebase_messages_are_sent_correctly(self):

        content = get_test_firebase_sender_log_content(only_include=['user_general_setting'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.top_profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'user_general_setting', 
                'action_type': 'edit', 
                'enable_shifts': 'False', 
                'enable_open_tickets': 'False', 
                'enable_low_stock_notifications': 'True', 
                'enable_negative_stock_alerts': 'True'
            }
        }

        self.assertEqual(content[0], result)

        # Edit model
        g_setting = UserGeneralSetting.objects.get(profile=self.top_profile)
        g_setting.enable_shifts = True
        g_setting.enable_open_tickets = True
        g_setting.enable_low_stock_notifications = False
        g_setting.enable_negative_stock_alerts = False
        g_setting.save()

        content = get_test_firebase_sender_log_content(only_include=['user_general_setting'])
        self.assertEqual(len(content), 2)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.top_profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'user_general_setting', 
                'action_type': 'edit', 
                'enable_shifts': 'True', 
                'enable_open_tickets': 'True', 
                'enable_low_stock_notifications': 'False', 
                'enable_negative_stock_alerts': 'False'
            }
        }

        self.assertEqual(content[1], result)
