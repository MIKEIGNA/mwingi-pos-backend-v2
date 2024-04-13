import datetime

from django.utils import timezone

from core.test_utils.make_payment import make_payment
from core.test_utils.custom_testcase import TestCase
from core.test_utils.create_store_models import create_new_store
from core.test_utils.create_user import (
    create_new_user,
    create_new_manager_user, 
    create_new_cashier_user
)

from profiles.models import Profile, EmployeeProfile

from billing.models import Subscription


"""
=========================== Subscription ===================================
"""
class SubscriptionTestCase(TestCase):
    def setUp(self):

        #Create a top user1
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')

        # Create a store
        self.store = create_new_store(self.top_profile, 'Computer Store')
        
        #Create a manager user
        self.manager_user = create_new_manager_user("gucci", self.top_profile, self.store)
        
        self.manager_profile = EmployeeProfile.objects.get(user__email='gucci@gmail.com')
        
        #Create a employee user
        self.employee_user = create_new_cashier_user("kate", self.top_profile, self.store)
        
        self.cashier_profile = EmployeeProfile.objects.get(user__email='kate@gmail.com') 
  
    def test_subscription_existence_and_fields_verbose_names(self):

        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)

        self.assertEqual(s._meta.get_field('due_date').verbose_name,'due date')
        self.assertEqual(s._meta.get_field('last_payment_date').verbose_name,'last payment date')
        self.assertEqual(s._meta.get_field('days_to_go').verbose_name,'days to go')
        self.assertEqual(s._meta.get_field('expired').verbose_name,'expired')
        
        # Subscription fields
        
        # Ensure a Subscription has the right fields after it has been created
        
        self.assertEqual((s.due_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        #Make sure when created, last_payment_date takes employee_profile.join_date#
        self.assertEqual(s.last_payment_date, s.employee_profile.join_date)
        self.assertEqual(s.days_to_go, 0)
        self.assertEqual(s.expired, True)
        
        self.assertEqual(s.get_profile(), self.top_profile)
        self.assertEqual(s.get_employee_profile(), self.cashier_profile)
        self.assertEqual(s.get_employee_profile_reg_no(), self.cashier_profile.reg_no)
        self.assertEqual(s.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        
        self.assertEqual(str(s),'Subs - kate@gmail.com')

    def test__str__method(self):
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        self.assertEqual(str(s),'Subs - kate@gmail.com')

    def test_get_profile_method(self):
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        self.assertEqual(s.get_profile(), self.top_profile)

    def test_get_employee_profile_method(self):
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        self.assertEqual(s.get_employee_profile(), self.cashier_profile)

    def test_get_due_date_method(self):
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        self.assertEqual(s.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))

    def test_last_payment_date_method(self):
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        self.assertEqual(s.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))

    def test_get_employee_reg_no_method(self):
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        self.assertEqual(s.get_employee_profile_reg_no(), self.cashier_profile.reg_no)

    def test_set_days_to_go_method(self):
        
        # set_days_to_go()
        
        # Ensure Subscription set_days_to_go method is working correctly
        
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        
        # 1 whole day to go #
        days =  datetime.timedelta(days=2)
        
        s.last_payment_date = timezone.now() - datetime.timedelta(days=1)
        s.due_date = timezone.now() + days
        s.save()
        
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        
        self.assertEqual(s.days_to_go, 1)
        self.assertEqual(s.get_due_date(),(timezone.now() + days).strftime("%B, %d, %Y"))
        
        # 0 days to go #
        days =  datetime.timedelta(days=1)
        
        s.last_payment_date = timezone.now() - datetime.timedelta(days=1)
        s.due_date = timezone.now() + days
        s.save()
        
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        
        self.assertEqual(s.days_to_go, 0)
        self.assertEqual(s.get_due_date(),(timezone.now() + days).strftime("%B, %d, %Y"))
        
        # -1 whole day to go #
        days =  datetime.timedelta(days=0)
        
        s.last_payment_date = timezone.now() - datetime.timedelta(days=1)
        s.due_date = timezone.now()
        s.save()
        
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        
        self.assertEqual(s.days_to_go, -1)
        self.assertEqual(s.get_due_date(),(timezone.now() + days).strftime("%B, %d, %Y"))
      
    def test_is_expired_method(self):
        
        # is_expired()
        
        # Ensure Subscription is_expired method is working correctly
        
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        # Test that new device unlocked is False and expired is True#
        self.assertEqual(s.days_to_go, 0)
        self.assertEqual(s.expired, True)
        
        # 1 whole day to go #
        s.last_payment_date = timezone.now() - datetime.timedelta(days=1)
        s.due_date = timezone.now() + datetime.timedelta(days=2)
        s.save()
        
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        
        self.assertEqual(s.days_to_go, 1)
        self.assertEqual(s.expired, False)
        
        
        # 0 days to go #
        s.last_payment_date = timezone.now() - datetime.timedelta(days=1)
        s.due_date = timezone.now() + datetime.timedelta(days=1)
        s.save()
        
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        
        self.assertEqual(s.days_to_go, 0)
        self.assertEqual(s.expired, False)
        
        
                
        # -1 days to go #
        s.last_payment_date = timezone.now() - datetime.timedelta(days=1)
        s.due_date = timezone.now()
        s.save()
        
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        
        self.assertEqual(s.days_to_go, -1)
        self.assertEqual(s.expired, True)
    
    def test_if_subscription_cant_be_deleted_by_delete_method(self):
        
        # is_expired()
        
        # Ensure Subscription is_expired method is working correctly
        
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        s.delete()
        
        self.assertEqual(Subscription.objects.filter(employee_profile__reg_no=self.cashier_profile.reg_no).exists(), True)
        
    def test_if_subscription_expiry_will_turn_employee_profile_into_an_active_user(self):
                
        # Confirm user is active when subscription has not been saved #  
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        
        user = EmployeeProfile.objects.get(user__email='kate@gmail.com').user
        
        self.assertEqual(user.is_active, False)
        self.assertEqual(s.expired, True)
        
        # Confirm user is not active when subscription has been saved #  
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        s.save()
        
        user = EmployeeProfile.objects.get(user__email='kate@gmail.com').user
        
        self.assertEqual(user.is_active, False)
        self.assertEqual(s.expired, True)
        
        # Confirm user will be turned into active when expired is not true
        # Lets say when a payment is made
         
        # Make a single payment so that the the device will be qualified
        # to have locations
        
        make_payment(self.user, self.cashier_profile.reg_no, 1)
        
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile.reg_no)
        
        user = EmployeeProfile.objects.get(user__email='kate@gmail.com').user
        
        self.assertEqual(user.is_active, True)
        self.assertEqual(s.expired, False)
