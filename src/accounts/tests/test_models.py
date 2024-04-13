import datetime

from django.contrib.auth.models import Permission

from django.utils import timezone
from django.db.utils import IntegrityError
from django.db import transaction
from django.contrib.auth import get_user_model
from accounts.create_permissions import PERMISSION_DEFS

from accounts.models import UserGroup
from api.tests.sales.create_receipts_for_test import CreateReceiptsForTesting2

from core.test_utils.custom_testcase import TestCase
from core.test_utils.create_store_models import create_new_store
from core.test_utils.create_user import (
    create_new_user, 
    create_new_manager_user, 
    create_new_cashier_user
)
from core.test_utils.date_utils import DateUtils

from profiles.models import (
    Profile, 
    EmployeeProfile
)

from mysettings.models import MySetting
from sales.models import Receipt

from ..utils.user_type import TOP_USER 

User = get_user_model()

"""
=========================== User ===================================
"""
class UserTestCase(TestCase):

    def setUp(self):
        
        #Create a user with email john@gmail.com
        self.user = create_new_user('john') 
        
        self.profile = Profile.objects.get(user=self.user)  

        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store2 = create_new_store(self.profile, 'Cloth Store')

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

        CreateReceiptsForTesting2(
            top_profile= self.profile,
            manager=self.manager.employeeprofile, 
            cashier= self.cashier.employeeprofile,
            discount=None,
            tax=None,
            store1= self.store1, 
            store2= self.store2
        ).create_receipts()

        receipts = Receipt.objects.all()

        for r in receipts:
            r.user = self.profile.user
            r.save()

    def test_verbose_names(self):
        u = User.objects.get(email='john@gmail.com')

        self.assertEqual(u._meta.get_field('email').verbose_name,'email')
        self.assertEqual(u._meta.get_field('first_name').verbose_name,'first name')
        self.assertEqual(u._meta.get_field('last_name').verbose_name,'last name')
        self.assertEqual(u._meta.get_field('phone').verbose_name,'phone')
        self.assertEqual(u._meta.get_field('join_date').verbose_name,'join date')
        self.assertEqual(u._meta.get_field('is_active').verbose_name,'is active')
        self.assertEqual(u._meta.get_field('is_staff').verbose_name,'is staff')
        self.assertEqual(u._meta.get_field('user_type').verbose_name,'user type')
        self.assertEqual(u._meta.get_field('gender').verbose_name,'gender')
                
        fields = ([field.name for field in User._meta.fields])
        
        self.assertEqual(len(fields), 14)

    def test_user_fields_after_it_has_been_created(self):
        """
        User fields
        
        Ensure a user has the right fields after it has been created
        """
        u = User.objects.get(email='john@gmail.com')
        
        today = (timezone.now()).strftime("%B, %d, %Y")
    
        self.assertEqual(str(u), 'john@gmail.com')
        self.assertEqual(u.email, 'john@gmail.com')
        self.assertEqual(u.first_name, 'John')
        self.assertEqual(u.last_name, 'Lock')
        self.assertEqual(u.phone, 254710223322)
        self.assertEqual(u.user_type, TOP_USER)
        self.assertEqual(u.gender, 0)
        self.assertEqual((u.join_date).strftime("%B, %d, %Y"), today)
        self.assertEqual(u.is_active, True)
        self.assertEqual(u.is_staff, False)

    def test_get_short_name_method(self):
        u = User.objects.get(email='john@gmail.com')

        self.assertEqual(u.get_short_name(), 'John')

    def test_get_full_name_method(self):
        u = User.objects.get(email='john@gmail.com')

        self.assertEqual(u.get_full_name(), 'John Lock')

    def test_get_join_date_method(self):
        u = User.objects.get(email='john@gmail.com')

        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            u.get_join_date(u.get_user_timezone()))
        )

    def test_get_profile_image_url_method(self):
        
        top_user = Profile.objects.get(user__email='john@gmail.com')
    
        #Create a manager user
        create_new_manager_user("gucci", top_user, self.store1)
        manager_profile = EmployeeProfile.objects.get(user__email='gucci@gmail.com')
   
        #Create a cashier user
        create_new_cashier_user("kate", top_user, self.store1)
        employee_profile = EmployeeProfile.objects.get(user__email='kate@gmail.com')
       
        # Test get_profile_image_url method for Top user
        self.assertEqual(
            top_user.user.get_profile_image_url(), 
            f'/media/images/profiles/{top_user.reg_no}_.jpg'
        )
              
        # Test get_profile_image_url method for manager user
        self.assertEqual(
            manager_profile.user.get_profile_image_url(), 
            f'/media/images/profiles/{manager_profile.reg_no}_.jpg'
        )
        
        # Test get_profile_image_url method for cashier user
        self.assertEqual(
            employee_profile.user.get_profile_image_url(), 
            f'/media/images/profiles/{employee_profile.reg_no}_.jpg'
        )

    def test_get_profile_reg_no_method(self):

        top_user = Profile.objects.get(user__email='john@gmail.com')
        
        #Create a manager user
        create_new_manager_user("gucci", top_user, self.store1)
        manager_profile = EmployeeProfile.objects.get(user__email='gucci@gmail.com')
        
        #Create a cashier user
        create_new_cashier_user("kate", top_user, self.store1)
        employee_profile = EmployeeProfile.objects.get(user__email='kate@gmail.com')


        # Test get_profile_reg_no method for Top user
        self.assertEqual(top_user.user.get_profile_reg_no(), top_user.reg_no)
        
        # Test get_profile_reg_no method for manager user
        self.assertEqual(manager_profile.user.get_profile_reg_no(), manager_profile.reg_no)
        
        # Test get_profile_reg_no method for cashier user
        self.assertEqual(employee_profile.user.get_profile_reg_no(), employee_profile.reg_no)
        
    def test_if_create_top_user_addittional_models_signal(self):
        """
    
        Ensure the signal creates profile, my settings and user's user groups
        """        
        u = User.objects.get(email='john@gmail.com')
        
        p = Profile.objects.get(user__email='john@gmail.com')
        
        # Check if profile reg_no matches with that of it's user
        self.assertEqual(p.reg_no, u.reg_no)
        
        """
        Check if MySetting is is created
        """        
        self.assertEqual(MySetting.objects.filter(name='main').count(), 1)
        self.assertEqual(MySetting.objects.all().count(), 1)

        """
        Check permissions
        """
        i=0
        for key, _ in PERMISSION_DEFS.items():
            self.assertEqual(Permission.objects.filter(codename=key).count(), 1)

            i+=1

        self.assertEqual(i, 14)

    def test_if_create_top_user_addittional_models_signal_creates_user_groups_for_top_user(self):

        u = User.objects.get(email='john@gmail.com')

        self.assertEqual(UserGroup.objects.filter(master_user=u).count(), 3)

    def test_if_create_top_user_addittional_models_signal_does_not_user_groups_for_non_top_user(self):

        self.store = create_new_store(self.profile, 'Computer Store')
        
        # Create a supervisor user
        create_new_manager_user("gucci", self.profile, self.store)

        create_new_cashier_user("kate", self.profile, self.store)

        manager_user = User.objects.get(email='gucci@gmail.com')
        self.assertEqual(UserGroup.objects.filter(master_user=manager_user).count(), 0)

        cashier_user = User.objects.get(email='kate@gmail.com')
        self.assertEqual(UserGroup.objects.filter(master_user=cashier_user).count(), 0)

    def test_what_happens_when_a_user_is_deleted(self):
        
        # Confirm the existence of a user and profile
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(Profile.objects.all().count(), 1)
        
        # Now delete the user
        user = User.objects.get(email='john@gmail.com')
        user.delete()
        
        # Confrim if the user his profiles were both deleted
        self.assertEqual(User.objects.all().count(), 0)
        self.assertEqual(Profile.objects.all().count(), 0)
    
    def test_get_report_data_method(self):

        self.create_receipts()

        user = User.objects.get(email='john@gmail.com')

        data = user.get_report_data(local_timezone=self.user.get_user_timezone())

        self.assertEqual(
            data, 
            {
                'name': 'John Lock', 
                'discount': '1503.00', 
                'gross_sales': '7797.00', 
                'net_sales': '9000.00', 
                'refund_amount': '2599.00', 
                'receipts_count': 3
            }
        )


    def test_get_report_data_method_with_date(self):

        self.create_receipts()

        user = User.objects.get(email='john@gmail.com')

        # Today date
        data = user.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'name': 'John Lock', 
                'discount': '401.00', 
                'gross_sales': '1599.00', 
                'net_sales': '2000.00', 
                'refund_amount': '0.00', 
                'receipts_count': 1
            }
        )

        ############ This month
        data = user.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.first_day_this_month.strftime('%Y-%m-%d'), 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'name': 'John Lock', 
                'discount': '902.00', 
                'gross_sales': '4198.00', 
                'net_sales': '5000.00', 
                'refund_amount': '2599.00', 
                'receipts_count': 2
            }
        )

        ############ Date with no receipts
        data = user.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='2011-01-01', 
            date_before='2011-01-02',
        )

        self.assertEqual(
            data, 
            {
                'name': 'John Lock', 
                'discount': '0.00', 
                'gross_sales': '0.00', 
                'net_sales': '0.00', 
                'refund_amount': '0.00', 
                'receipts_count': 0
            }
        )

        ############# Wrong date from
        data = user.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after='20111-01-01', 
            date_before=self.tomorrow.strftime('%Y-%m-%d'),
        )

        self.assertEqual(
            data, 
            {
                'name': 'John Lock', 
                'discount': '1503.00', 
                'gross_sales': '7797.00', 
                'net_sales': '9000.00', 
                'refund_amount': '2599.00', 
                'receipts_count': 3
            }
        )

        ############ Wrong date to
        data = user.get_report_data(
            local_timezone=self.user.get_user_timezone(),
            date_after=self.today.strftime('%Y-%m-%d'),
            date_before='20111-01-01',
        )

        self.assertEqual(
            data, 
            {
                'name': 'John Lock', 
                'discount': '1503.00', 
                'gross_sales': '7797.00', 
                'net_sales': '9000.00', 
                'refund_amount': '2599.00', 
                'receipts_count': 3
            }
        )

    def test_get_report_data_method_with_store_reg_no(self):

        self.create_receipts()

        user = User.objects.get(email='john@gmail.com')

        # Store 1
        self.assertEqual(
            user.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_no=self.store1.reg_no
            ), 
            {
                'name': 'John Lock', 
                'discount': '902.00', 
                'gross_sales': '4198.00', 
                'net_sales': '5000.00', 
                'refund_amount': '2599.00', 
                'receipts_count': 2
            }
        )

        # Store 2
        self.assertEqual(
            user.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_no=self.store2.reg_no
            ), 
            {
                'name': 'John Lock', 
                'discount': '601.00', 
                'gross_sales': '3599.00', 
                'net_sales': '4000.00', 
                'refund_amount': '0.00', 
                'receipts_count': 1
            }
        )

        # Wrong store 
        self.assertEqual(
            user.get_report_data(
                local_timezone=self.user.get_user_timezone(),
                store_reg_no=1111
            ), 
            {
                'name': 'John Lock', 
                'discount': '0.00', 
                'gross_sales': '0.00', 
                'net_sales': '0.00', 
                'refund_amount': '0.00', 
                'receipts_count': 0
            }
        )

"""
=========================== UserManager ===================================
"""
# User
class UserManagerTestCase(TestCase):
 
    def test_UserManager_create_user_method(self):
        """
        UserManager's create_user method
        
        Ensure UserManager's create_user method is working correctly
        """
        User.objects.create_user(
            email='john@gmail.com', 
            first_name='John', 
            last_name='Lock', 
            phone='254710223322',
            user_type=TOP_USER,
            gender=0,
            password='secretpass'
        )

        u = User.objects.get(email='john@gmail.com')
        
        today = (timezone.now()).strftime("%B, %d, %Y")
    
        self.assertEqual(u.email, 'john@gmail.com')
        self.assertEqual(u.first_name, 'John')
        self.assertEqual(u.last_name, 'Lock')
        self.assertEqual(u.phone, 254710223322)
        self.assertEqual(u.user_type, TOP_USER)
        self.assertEqual(u.gender, 0)
        self.assertEqual(u.is_superuser, False)
        self.assertEqual((u.join_date).strftime("%B, %d, %Y"), today)
        self.assertEqual(u.is_active, True)
        self.assertEqual(u.is_staff, False)

    def test_if_UserManager_create_user_method_can_raise_email_error(self):
        """
        UserManager's create_user method
        
        Ensure UserManager's create_usermethod can raise email error
        """
        
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='', 
                first_name='John', 
                last_name='Lock', 
                phone='254710223322',
                user_type=TOP_USER,
                gender=0,
                password='secretpass'
            )
            
    def test_device_UserManager_create_user_method_can_raise_first_name_error(self):
        """
        UserManager's create_user method
        
        Ensure UserManager's create_usermethod can raise first_name error
        """
        
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='john@gmail.com', 
                first_name='', 
                last_name='Lock', 
                phone='254710223322',
                user_type=TOP_USER,
                gender=0,
                password='secretpass'
            )
            
    def test_device_UserManager_create_user_method_can_raise_last_name_error(self):
        """
        UserManager's create_user method
        
        Ensure UserManager's create_usermethod can raise last_name error
        """
        
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='john@gmail.com', 
                first_name='John', 
                last_name='', 
                phone='254710223322',
                user_type=TOP_USER,
                gender=0,
                password='secretpass'
            )
            
    def test_device_UserManager_create_user_method_can_raise_phone_error(self):
        """
        UserManager's create_user method
        
        Ensure UserManager's create_usermethod can raise phone error
        """
        
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='john@gmail.com', 
                first_name='John', 
                last_name='Lock', 
                phone='',
                user_type=TOP_USER,
                gender=0,
                password='secretpass'
            )
            
    def test_device_UserManager_can_create_superuser_method(self):
        """
        UserManager's create_user method
        
        Ensure UserManager's create_usermethod is working correctly
        """
        User.objects.create_superuser(
            email='john@gmail.com', 
            first_name='John', 
            last_name='Lock', 
            phone='254710223322',
            gender=0,
            password='secretpass'
        )
        
        u = User.objects.get(email='john@gmail.com')
        
        today = (timezone.now()).strftime("%B, %d, %Y")
    
        self.assertEqual(u.email, 'john@gmail.com')
        self.assertEqual(u.first_name, 'John')
        self.assertEqual(u.last_name, 'Lock')
        self.assertEqual(u.phone, 254710223322)
        self.assertEqual(u.user_type, TOP_USER)
        self.assertEqual(u.gender, 0)
        self.assertEqual(u.is_superuser, True)
        self.assertEqual((u.join_date).strftime("%B, %d, %Y"), today)
        self.assertEqual(u.is_active, True)
        self.assertEqual(u.is_staff, True)
        
    def test_device_UserManager_cant_create_a_user_with_an_non_unique_email(self):
        """
        UserManager's create_user method
        
        Ensure UserManager's create_usermethod cant create a user with a non unique email
        """
        User.objects.create_user(email='john@gmail.com', 
                            first_name='John', 
                            last_name='Lock', 
                            phone='254710223322',
                            user_type=TOP_USER,
                            gender=0,
                            password='secretpass')
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                User.objects.create_user(email='john@gmail.com', 
                            first_name='John2', 
                            last_name='Lock2', 
                            phone='254711223322',
                            user_type=TOP_USER,
                            gender=0,
                            password='secretpass')
        
        
        self.assertEqual(User.objects.filter(email='john@gmail.com').count(), 1)
     
    
    def test_device_UserManager_cant_create_a_user_with_an_non_unique_phone(self):
        """
        UserManager's create_user method
        
        Ensure UserManager's create_usermethod cant create a user with a non unique phone
        """
        User.objects.create_user(
            email='john@gmail.com', 
            first_name='John', 
            last_name='Lock', 
            phone='254710223322',
            user_type=TOP_USER,
            gender=0,
            password='secretpass')
        
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                User.objects.create_user(
                    email='doe@gmail.com', 
                    first_name='Joe', 
                    last_name='Doe', 
                    phone='254710223322',
                    user_type=TOP_USER,
                    gender=0,
                    password='secretpass'
                )
        
        self.assertEqual(User.objects.filter(email='john@gmail.com').count(), 1)

"""
=========================== UserGroup ===================================
"""
class UserGroupTestCase(TestCase):

    def setUp(self):
        
        #Create a user with email john@gmail.com
        self.top_user = create_new_user('john') 
        
        self.profile = Profile.objects.get(user=self.top_user)  

        self.store = create_new_store(self.profile, 'Computer Store')

        #Create a manager user
        create_new_manager_user("gucci", self.profile, self.store)

        #Create a cashier user
        create_new_cashier_user("kate", self.profile, self.store)

    def test_verbose_names(self):

        group = UserGroup.objects.get(user__email='john@gmail.com')

        self.assertEqual(group._meta.get_field('ident_name').verbose_name,'ident name')
        self.assertEqual(group._meta.get_field('is_owner_group').verbose_name,'is owner group')
        self.assertEqual(group._meta.get_field('reg_no').verbose_name,'reg no')

        fields = ([field.name for field in UserGroup._meta.fields])
        
        self.assertEqual(len(fields), 7)

    def test_user_group_fields_after_it_has_been_created(self):

        # Owner group
        owner_group = UserGroup.objects.get(user__email='john@gmail.com')

        self.assertEqual(owner_group.master_user, self.top_user)
        self.assertEqual(owner_group.name, f'Owner {self.top_user.reg_no}')
        self.assertEqual(owner_group.ident_name, 'Owner')
        self.assertEqual(owner_group.is_owner_group, True)
        self.assertTrue(owner_group.reg_no > 100000) 

        # Manager group
        manager_group = UserGroup.objects.get(user__email='gucci@gmail.com')

        self.assertEqual(manager_group.master_user, self.top_user)
        self.assertEqual(manager_group.name, f'Manager {self.top_user.reg_no}')
        self.assertEqual(manager_group.ident_name, 'Manager')
        self.assertEqual(manager_group.is_owner_group, False)
        self.assertTrue(manager_group.reg_no > 100000) 

        # Cashier group
        cashier_group = UserGroup.objects.get(user__email='kate@gmail.com')

        self.assertEqual(cashier_group.master_user, self.top_user)
        self.assertEqual(cashier_group.name, f'Cashier {self.top_user.reg_no}')
        self.assertEqual(cashier_group.ident_name, 'Cashier')
        self.assertEqual(cashier_group.is_owner_group, False)
        self.assertTrue(cashier_group.reg_no > 100000) 

    def test_str_method(self):

        owner_group = UserGroup.objects.get(user__email='john@gmail.com')
        self.assertEqual(str(owner_group), 'Owner')

        manager_group = UserGroup.objects.get(user__email='gucci@gmail.com')
        self.assertEqual(str(manager_group), 'Manager')

        cashier_group = UserGroup.objects.get(user__email='kate@gmail.com')
        self.assertEqual(str(cashier_group), 'Cashier')
    
    def test_if_owner_user_group_has_all_perms(self):
        
        group = UserGroup.objects.get(user__email='john@gmail.com')

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]
        
        perms_codenames  = [key for key, _ in PERMISSION_DEFS.items()]

        self.assertEqual(len(perms_codenames), 23)
        self.assertEqual(perms, perms_codenames)
        
    def test_manager_user_group_perms(self):
        
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
            'can_change_taxes'
        ]

        self.assertEqual(perms, perms_codenames)

    def test_cashier_user_group_perms(self):
        
        group = UserGroup.objects.get(user__email='kate@gmail.com')

        perms = [
            p[0] for p in group.permissions.all().order_by('id').values_list('codename')]

        self.assertEqual(perms, [])

    def test_get_user_permissions_state_method_with_owner_group(self):
        
        group = UserGroup.objects.get(user__email='john@gmail.com')

        perms_state = {
            'can_view_shift_reports': True,
            'can_manage_open_tickets': True,
            'can_void_open_ticket_items': True,
            'can_manage_items': True, 
            'can_refund_sale': True, 
            'can_open_drawer': True, 
            'can_reprint_receipt': True, 
            'can_change_settings': True, 
            'can_apply_discount': True, 
            'can_change_taxes': True, 
            'can_accept_debt': True, 
            'can_manage_customers': True, 
            'can_manage_employees': True, 
            'can_change_general_settings': True
        }

        self.assertEqual(group.get_user_permissions_state(), perms_state)

    def test_get_user_permissions_state_method_with_manager_group(self):
        
        group = UserGroup.objects.get(user__email='gucci@gmail.com')

        perms_state = {
            'can_view_shift_reports': True,
            'can_manage_open_tickets': True,
            'can_void_open_ticket_items': True,
            'can_manage_items': True, 
            'can_refund_sale': True, 
            'can_open_drawer': True, 
            'can_reprint_receipt': True, 
            'can_change_settings': True, 
            'can_apply_discount': True, 
            'can_change_taxes': True, 
            'can_accept_debt': False, 
            'can_manage_customers': False, 
            'can_manage_employees': False, 
            'can_change_general_settings': False
        }

        self.assertEqual(group.get_user_permissions_state(), perms_state)

    def test_get_user_permissions_state_method_with_cashier_group(self):
        
        group = UserGroup.objects.get(user__email='kate@gmail.com')

        perms_state = {
            'can_view_shift_reports': False,
            'can_manage_open_tickets': False,
            'can_void_open_ticket_items': False,
            'can_manage_items': False, 
            'can_refund_sale': False, 
            'can_open_drawer': False, 
            'can_reprint_receipt': False, 
            'can_change_settings': False, 
            'can_apply_discount': False, 
            'can_change_taxes': False, 
            'can_accept_debt': False, 
            'can_manage_customers': False, 
            'can_manage_employees': False, 
            'can_change_general_settings': False
        }

        self.assertEqual(group.get_user_permissions_state(), perms_state)