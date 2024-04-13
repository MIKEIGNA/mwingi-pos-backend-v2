from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.test import Client
from django.urls import reverse

from core.test_utils.custom_testcase import TestCase
from core.test_utils.initial_user_data import InitialUserDataMixin

from mysettings.models import MySetting
from profiles.models import EmployeeProfile
from mylogentries.models import PaymentLog, MpesaLog

from billing.models import Subscription, Payment
from billing.utils.payment_utils.price_gen import PriceGeneratorClass


class SuperPaymentCompleteViewTestCase(TestCase, InitialUserDataMixin):
    def setUp(self):

        """
        This function is defined in the 'InitialUserDataMixin' mixin
        
        It creates 2 top users, 3 stores and 5 employee users as follows

        * Top User 1 assets:
            self.user1 - top user 
            self.top_profile1 - Profile for top user -- (john@gmail.com)

            - self.store1 - Store -- (Computer Store) 
                self.manager_profile1 - Manger Employee profile for top user 1 -- (gucci@gmail.com)

                self.cashier_profile1 - Cashier Employee profile under manager profile 1 -- (kate@gmail.com)
                self.cashier_profile2 - Cashier Employee profile under manager profile 1 -- (james@gmail.com)
                self.cashier_profile3 - Cashier Employee profile under manager profile 1 -- (ben@gmail.com)

            - self.store2 - Store -- (Cloth Store)
                self.manager_profile2 - Manger Employee profile for top user 1 -- (lewis@gmail.com)

                self.cashier_profile4 - Cashier Employee profile under manager profile 2 -- (hugo@gmail.com)


        * Top User 2 assets:
            self.user2 - top user
            self.top_profile2 - Profile for top user-- (jack@gmail.com)

            - self.store3 - Store -- (Toy Store)
                self.manager_profile3 - Manger Employee profile for top user 2 -- (cristiano@gmail.com):

                self.cashier_profile5 - Cashier Employee profile under manager profile 3 -- (juliet@gmail.com)
        """
        
        self.create_initial_user_data_with_superuser()
        
        
        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
        
        # My client
        self.client = Client()
        self.client.login(username='john@gmail.com', password='secretpass')
        
         
    def test_if_SuperPaymentCompleteView_can_be_viewed_successfully(self):
               
        response = self.client.get(reverse('billing:super_payment_complete'), follow=True)        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'billing/superuser_payment_completed.html')


        # ######### Test Content ######### #
        self.assertContains(response, 'Payment Completed')
        self.assertContains(response, '<p>Your payment request has been successfully.</p>')
       
    def test_if_SuperPaymentCompleteView___cant_be_viewed_by_a_top_user(self):
        
        # Login a top user
        self.client = Client()
        self.client.login(username='jack@gmail.com', password='secretpass')
        
        response = self.client.get(reverse('billing:super_payment_complete'), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_if_SuperPaymentCompleteView___cant_be_viewed_by_a_supervisor_user(self):
                
        # Login an superviosr user
        self.client = Client()
        self.client.login(username='gucci@gmail.com', password='secretpass')

        response = self.client.get(reverse('billing:super_payment_complete'), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_if_SuperPaymentCompleteView___cant_be_viewed_by_a_employee_user(self):
                
        # Login another user #
        self.client = Client()
        self.client.login(username='kate@gmail.com', password='secretpass')
        
        response = self.client.get(reverse('billing:super_payment_complete'), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_if_SuperPaymentCompleteView___cant_be_viewed_by_an_unlogged_in_user(self):
        
        # Unlogged in user
        self.client = Client()
        
        response = self.client.get(reverse('billing:super_payment_complete'), follow=True)
        self.assertEqual(response.status_code, 404)
        
   
class SuperPaymentsNotAllowedViewTestCase(TestCase, InitialUserDataMixin):
    def setUp(self):

        """
        This function is defined in the 'InitialUserDataMixin' mixin
        
        It creates 2 top users, 3 stores and 5 employee users as follows

        * Top User 1 assets:
            self.user1 - top user 
            self.top_profile1 - Profile for top user -- (john@gmail.com)

            - self.store1 - Store -- (Computer Store) 
                self.manager_profile1 - Manger Employee profile for top user 1 -- (gucci@gmail.com)

                self.cashier_profile1 - Cashier Employee profile under manager profile 1 -- (kate@gmail.com)
                self.cashier_profile2 - Cashier Employee profile under manager profile 1 -- (james@gmail.com)
                self.cashier_profile3 - Cashier Employee profile under manager profile 1 -- (ben@gmail.com)

            - self.store2 - Store -- (Cloth Store)
                self.manager_profile2 - Manger Employee profile for top user 1 -- (lewis@gmail.com)

                self.cashier_profile4 - Cashier Employee profile under manager profile 2 -- (hugo@gmail.com)


        * Top User 2 assets:
            self.user2 - top user
            self.top_profile2 - Profile for top user-- (jack@gmail.com)

            - self.store3 - Store -- (Toy Store)
                self.manager_profile3 - Manger Employee profile for top user 2 -- (cristiano@gmail.com):

                self.cashier_profile5 - Cashier Employee profile under manager profile 3 -- (juliet@gmail.com)
        """
        
        self.create_initial_user_data_with_superuser()
        
        
        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
        
        # My client
        self.client = Client()
        self.client.login(username='john@gmail.com', password='secretpass')
        
            
    def test_if_SuperPaymentsNotAllowedView_can_be_viewed_successfully(self):
               
        response = self.client.get(reverse('billing:super_payment_not_allowed'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'billing/superuser_payments_not_allowed.html')

        # ######### Test Content ######### #
        self.assertContains(response, 'Currently New Payments are not allowed')
        self.assertContains(response, '<p>The system has been set to reject new payments.</p>')
        self.assertContains(response, '<p>Try later when the payments settings has been changed.</p>') 

    def test_if_SuperPaymentsNotAllowedView__cant_be_viewed_by_a_top_user(self):
        
        # Login a top user
        self.client = Client()
        self.client.login(username='jack@gmail.com', password='secretpass')
        
        response = self.client.get(reverse('billing:super_payment_not_allowed'), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_if_SuperPaymentsNotAllowedView__cant_be_viewed_by_a_supervisor_user(self):
                
        # Login an superviosr user
        self.client = Client()
        self.client.login(username='gucci@gmail.com', password='secretpass')

        response = self.client.get(reverse('billing:super_payment_not_allowed'), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_if_SuperPaymentsNotAllowedView__cant_be_viewed_by_a_employee_user(self):
                
        # Login another user #
        self.client = Client()
        self.client.login(username='kate@gmail.com', password='secretpass')
        
        response = self.client.get(reverse('billing:super_payment_not_allowed'), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_if_SuperPaymentsNotAllowedView__cant_be_viewed_by_an_unlogged_in_user(self):
        
        # Unlogged in user
        self.client = Client()
        
        response = self.client.get(reverse('billing:super_payment_not_allowed'), follow=True)
        self.assertEqual(response.status_code, 404)


class MakePaymentViewTestCase(TestCase, InitialUserDataMixin):
    def setUp(self):

        """
        This function is defined in the 'InitialUserDataMixin' mixin
        
        It creates 2 top users, 3 stores and 5 employee users as follows

        * Top User 1 assets:
            self.user1 - top user 
            self.top_profile1 - Profile for top user -- (john@gmail.com)

            - self.store1 - Store -- (Computer Store) 
                self.manager_profile1 - Manger Employee profile for top user 1 -- (gucci@gmail.com)

                self.cashier_profile1 - Cashier Employee profile under manager profile 1 -- (kate@gmail.com)
                self.cashier_profile2 - Cashier Employee profile under manager profile 1 -- (james@gmail.com)
                self.cashier_profile3 - Cashier Employee profile under manager profile 1 -- (ben@gmail.com)

            - self.store2 - Store -- (Cloth Store)
                self.manager_profile2 - Manger Employee profile for top user 1 -- (lewis@gmail.com)

                self.cashier_profile4 - Cashier Employee profile under manager profile 2 -- (hugo@gmail.com)


        * Top User 2 assets:
            self.user2 - top user
            self.top_profile2 - Profile for top user-- (jack@gmail.com)

            - self.store3 - Store -- (Toy Store)
                self.manager_profile3 - Manger Employee profile for top user 2 -- (cristiano@gmail.com):

                self.cashier_profile5 - Cashier Employee profile under manager profile 3 -- (juliet@gmail.com)
        """
        
        self.create_initial_user_data_with_superuser()
        
        
        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
        
        # My client
        self.client = Client()
        self.client.login(username='john@gmail.com', password='secretpass')

    def test_if_MakePaymentView_can_be_viewed_successfully(self):

        with self.assertNumQueries(5):
            response = self.client.get(reverse('billing:super_make_payment'))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.template_name[0], 'billing/make_payment_form.html')
        
        
        # ######### Test Content ######### #
        self.assertContains(response, 'Make Payment') # title
        self.assertContains(response, 'Account no') # fields
        self.assertContains(response, 'Amount') # fields
        self.assertContains(response, 'Submit') # button

        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's accept_payments is False#                  
        # ******************************************************************* #

        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=False
        ms.save()
        
        # Try to make a new payment#
        response = self.client.get(reverse('billing:super_make_payment'), follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'billing/superuser_payments_not_allowed.html')

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=True
        ms.maintenance=True
        ms.save()
        
        response = self.client.get(reverse('billing:super_make_payment'), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_if_MakePaymentView_cant_be_viewed_by_a_top_user(self):
        
        # Login a top user
        self.client = Client()
        self.client.login(username='jack@gmail.com', password='secretpass')
        
        response = self.client.get(reverse('billing:super_make_payment'), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_if_MakePaymentView_cant_be_viewed_by_a_supervisor_user(self):
                
        # Login an superviosr user
        self.client = Client()
        self.client.login(username='gucci@gmail.com', password='secretpass')

        response = self.client.get(reverse('billing:super_make_payment'))
        self.assertEqual(response.status_code, 404)

    def test_if_MakePaymentView_cant_be_viewed_by_a_employee_user(self):
                
        # Login another user #
        self.client = Client()
        self.client.login(username='kate@gmail.com', password='secretpass')
        
        response = self.client.get(reverse('billing:super_make_payment'))
        self.assertEqual(response.status_code, 404)

    def test_if_AdminUserAnalyticsView_cant_be_viewed_by_an_unlogged_in_user(self):
        
        # Unlogged in user
        self.client = Client()
        
        response = self.client.get(reverse('billing:super_make_payment'))
            
        self.assertEqual(response.status_code, 404)


class MakePaymentViewForSingleEmployeeProfileTestCase(TestCase, InitialUserDataMixin):
    def setUp(self):

        """
        This function is defined in the 'InitialUserDataMixin' mixin
        
        It creates 2 top users, 3 stores and 5 employee users as follows

        * Top User 1 assets:
            self.user1 - top user 
            self.top_profile1 - Profile for top user -- (john@gmail.com)

            - self.store1 - Store -- (Computer Store) 
                self.manager_profile1 - Manger Employee profile for top user 1 -- (gucci@gmail.com)

                self.cashier_profile1 - Cashier Employee profile under manager profile 1 -- (kate@gmail.com)
                self.cashier_profile2 - Cashier Employee profile under manager profile 1 -- (james@gmail.com)
                self.cashier_profile3 - Cashier Employee profile under manager profile 1 -- (ben@gmail.com)

            - self.store2 - Store -- (Cloth Store)
                self.manager_profile2 - Manger Employee profile for top user 1 -- (lewis@gmail.com)

                self.cashier_profile4 - Cashier Employee profile under manager profile 2 -- (hugo@gmail.com)


        * Top User 2 assets:
            self.user2 - top user
            self.top_profile2 - Profile for top user-- (jack@gmail.com)

            - self.store3 - Store -- (Toy Store)
                self.manager_profile3 - Manger Employee profile for top user 2 -- (cristiano@gmail.com):

                self.cashier_profile5 - Cashier Employee profile under manager profile 3 -- (juliet@gmail.com)
        """
        
        self.create_initial_user_data_with_superuser_with_no_payment_history()

        # We reduce the number of employee profiles to make the test managable
        self.manager_profile1.delete()
        self.cashier_profile2.delete()
        self.cashier_profile3.delete()

        self.manager_profile2.delete()

        self.assertEqual(EmployeeProfile.objects.filter(
            profile=self.top_profile1).count(), 2)


        # Turn off maintenance mode 
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
        

        # My client
        self.client = Client()
        self.client.login(username='john@gmail.com', password='secretpass')


    def test_if_MpesaPaymentView_can_confirm_1_month_payment_for_employee_profiles(self):
        
        duration = 1

        # ############## Before making Payment ############### #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        
        
        # Ensure subscription has the right values #
        # Subscription 1
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        
        self.assertEqual((s.due_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s.last_payment_date, s.employee_profile.join_date)
        self.assertEqual(s.days_to_go, 0)
        self.assertEqual(s.expired, True)
        self.assertEqual(s.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s.get_profile(), self.top_profile1)
        self.assertEqual(s.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
        self.assertEqual(str(s),'Subs - kate@gmail.com')
        
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
    
        response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':self.cashier_profile1.reg_no, 'amount': one_month_price}, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'billing/superuser_payment_completed.html')
        
        # ############## Make sure no payment was made during confirmation ################
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().count(), 1) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().count(), 0) # Make sure there are no Mpesa
        
        # ############## After making Payment ################
        
        # Ensure a PaymentLog has the right fields after it has been created #
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there is only 1 PaymentLog
        
        pl = PaymentLog.objects.get(reg_no=self.cashier_profile1.reg_no)
                
        self.assertEqual(pl.amount, one_month_price)
        self.assertEqual(pl.payment_method, "manual_payment")
        self.assertEqual(pl.mpesa_id, 0)
        self.assertEqual(pl.payment_type, 'single account')
        self.assertEqual(pl.email, self.top_profile1.user.email)
        self.assertEqual(pl.reg_no, self.cashier_profile1.reg_no)
        self.assertEqual(pl.duration, 1)
        
        
        
        # Ensure payments have been made for each employee profile #
        self.assertEqual(Payment.objects.all().count(), 1) # Make sure there is only 1 Payment
        
        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        
        # Payment    
        self.assertEqual(p.paymentlog, pl)
        self.assertEqual(p.amount, one_month_price)
        self.assertEqual((p.payed_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(p.parent_reg_no, 0)
        self.assertEqual(p.account_reg_no, self.cashier_profile1.reg_no)
        self.assertEqual(p.account_type, 'account')
        self.assertEqual(p.duration, 1)
        
        # Ensure there is no MpesaLog #
        self.assertEqual(MpesaLog.objects.all().count(), 0)
        
        # Ensure subscription has been updated #
        # Subscription
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        correct_due_date = (p.payed_date + relativedelta(months=1)).strftime("%B, %d, %Y")
        
        self.assertEqual((s.due_date).strftime("%B, %d, %Y"), correct_due_date)
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s.last_payment_date, p.payed_date)
        
        # Due to months with 28, 29, 30 and 31 days, we cant be sure 
        # of days_to_go value but we know the range is btwn 28 an 31#
        self.assertTrue(s.days_to_go > 28)
        self.assertTrue(s.days_to_go < 31)
        
        self.assertEqual(s.expired, False)
        self.assertEqual(s.get_due_date(), correct_due_date)
        self.assertEqual(s.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s.get_profile(), self.top_profile1)
        self.assertEqual(s.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
        self.assertEqual(str(s),'Subs - kate@gmail.com')
      
    def test_if_MpesaPaymentView_can_confirm_6_month_payment_for_employee_profiles(self):
        
        duration = 6

        # ############## Before making Payment ############### #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        
        
        # Ensure subscription has the right values #
        # Subscription 1
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        
        self.assertEqual((s.due_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s.last_payment_date, s.employee_profile.join_date)
        self.assertEqual(s.days_to_go, 0)
        self.assertEqual(s.expired, True)
        self.assertEqual(s.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s.get_profile(), self.top_profile1)
        self.assertEqual(s.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
        self.assertEqual(str(s),'Subs - kate@gmail.com')
        
        
        
        six_months_price = PriceGeneratorClass.account_price_calc(duration)
    
        response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':self.cashier_profile1.reg_no, 'amount': six_months_price}, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'billing/superuser_payment_completed.html')
        
        # ############## After making Payment ################
        
        # Ensure a PaymentLog has the right fields after it has been created #
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there is only 1 PaymentLog
        
        pl = PaymentLog.objects.get(reg_no=self.cashier_profile1.reg_no)
        
        self.assertEqual(pl.amount, six_months_price)
        self.assertEqual(pl.payment_method, "manual_payment")
        self.assertEqual(pl.mpesa_id, 0)
        self.assertEqual(pl.payment_type, 'single account')
        self.assertEqual(pl.email, self.top_profile1.user.email)
        self.assertEqual(pl.reg_no, self.cashier_profile1.reg_no)
        self.assertEqual(pl.duration, 6)
        

        
        # Ensure payments have been made for each employee profile #
        self.assertEqual(Payment.objects.all().count(), 1) # Make sure there is only 1 Payment
        
        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        
        # Payment 
        self.assertEqual(p.paymentlog, pl)
        self.assertEqual(p.amount, six_months_price)
        self.assertEqual((p.payed_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(p.parent_reg_no, 0)
        self.assertEqual(p.account_reg_no, self.cashier_profile1.reg_no)
        self.assertEqual(p.account_type, 'account')
        self.assertEqual(p.duration, 6)
        
        # Ensure there is no MpesaLog #
        self.assertEqual(MpesaLog.objects.all().count(), 0)
        
        # Ensure subscription has been updated #
        # Subscription
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        correct_due_date = (p.payed_date + relativedelta(months=6)).strftime("%B, %d, %Y")
        
        self.assertEqual((s.due_date).strftime("%B, %d, %Y"), correct_due_date)
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s.last_payment_date, p.payed_date)
        
        # Due to months with 28, 29, 30 and 31 days, we cant be sure 
        # of days_to_go value but we know the range is btwn 180 an 185        
        self.assertTrue(s.days_to_go >= 180)
        self.assertTrue(s.days_to_go < 185)
        
        self.assertEqual(s.expired, False)
        self.assertEqual(s.get_due_date(), correct_due_date)
        self.assertEqual(s.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s.get_profile(), self.top_profile1)
        self.assertEqual(s.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
        self.assertEqual(str(s),'Subs - kate@gmail.com')
        
    def test_if_MpesaPaymentView_can_confirm_12_month_payment_for_employee_profiles(self):
        
        duration = 12

        # ############## Before making Payment ############### #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        
        
        # Ensure subscription has the right values #
        # Subscription 1
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        
        self.assertEqual((s.due_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s.last_payment_date, s.employee_profile.join_date)
        self.assertEqual(s.days_to_go, 0)
        self.assertEqual(s.expired, True)
        self.assertEqual(s.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s.get_profile(), self.top_profile1)
        self.assertEqual(s.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
        self.assertEqual(str(s),'Subs - kate@gmail.com')
        
        one_year_price = PriceGeneratorClass.account_price_calc(duration)
        
        response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':self.cashier_profile1.reg_no, 'amount': one_year_price}, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'billing/superuser_payment_completed.html')
        
        # ############## After making Payment ################
        
        # Ensure a PaymentLog has the right fields after it has been created #
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there is only 1 PaymentLog
        
        pl = PaymentLog.objects.get(reg_no=self.cashier_profile1.reg_no)
                
        self.assertEqual(pl.amount, one_year_price)
        self.assertEqual(pl.payment_method, "manual_payment")
        self.assertEqual(pl.mpesa_id, 0)
        self.assertEqual(pl.payment_type, 'single account')
        self.assertEqual(pl.email, self.top_profile1.user.email)
        self.assertEqual(pl.reg_no, self.cashier_profile1.reg_no)
        self.assertEqual(pl.duration, 12)
        
        # Ensure payments have been made for each employee profile #
        self.assertEqual(Payment.objects.all().count(), 1) # Make sure there is only 1 Payment
        
        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        
        # Payment 
        self.assertEqual(p.paymentlog, pl)
        self.assertEqual(p.amount, one_year_price)
        self.assertEqual((p.payed_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(p.parent_reg_no, 0)
        self.assertEqual(p.account_reg_no, self.cashier_profile1.reg_no)
        self.assertEqual(p.account_type, 'account')
        self.assertEqual(p.duration, 12)
        
        # Ensure there is no MpesaLog #
        self.assertEqual(MpesaLog.objects.all().count(), 0)
        
        # Ensure subscription has been updated #
        # Subscription
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        correct_due_date = (p.payed_date + relativedelta(months=12)).strftime("%B, %d, %Y")
        
        self.assertEqual((s.due_date).strftime("%B, %d, %Y"), correct_due_date)
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s.last_payment_date, p.payed_date)
        
        # Due to months with 28, 29, 30 and 31 days, we cant be sure 
        # of days_to_go value but we know the range is btwn 363 an 368
        self.assertTrue(s.days_to_go > 363)
        self.assertTrue(s.days_to_go < 368)
        
        self.assertEqual(s.expired, False)
        self.assertEqual(s.get_due_date(), correct_due_date)
        self.assertEqual(s.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s.get_profile(), self.top_profile1)
        self.assertEqual(s.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
        self.assertEqual(str(s),'Subs - kate@gmail.com')
           
    def test_if_MpesaPaymentView_can_handle_a_wrong_amount_for_employee_profiles(self):
        
     
        # ############## Before making Payment ############### #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False)
        
        
        # Amounts below 1 wont pass form validation so those type of values 
        # should be tested in the form
        
        wrong_prices = ['wrong format',
                        555555555555555555555555555555555555555555555555555555555555, #Extremley long interger
                        -1, 
                        0,
                        3100, 
                        14500, 
                        2300, 
                        200000,
                        ]
   
        i = 0
        for wrong_price in wrong_prices:
            i+=1
            
            if i == 1 or i == 3 or i == 4:
                # Check if the request will fail if given a non integer and zero and below numbers#
                response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':self.cashier_profile1.reg_no, 'amount': wrong_price}, follow=True)
        
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.templates[0].name, 'billing/make_payment_form.html')
                
            else:
                # Check if the request will fail if given wrong amounts#
                response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':self.cashier_profile1.reg_no, 'amount': wrong_price}, follow=True)
        
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'An Error Found - Wrong amount.')
                self.assertEqual(response.templates[0].name, 'billing/make_payment_form.html')
                
                
    
        # ############## After making Payment ################
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False)
            
        # Ensure subscription doesent get updated #
        # Subscription 
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
            
        self.assertEqual((s.due_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s.last_payment_date, s.employee_profile.join_date)
        self.assertEqual(s.days_to_go, 0)
        self.assertEqual(s.expired, True)
        self.assertEqual(s.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s.get_profile(), self.top_profile1)
        self.assertEqual(s.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
        self.assertEqual(str(s),'Subs - kate@gmail.com')
    
   
    def test_if_MpesaPaymentView_can_handle_a_wrong_reg_no_for_employee_profiles(self):       
        # Create DeviceKey and Device1 #

        durations = [1, 6, 12]

        wrong_reg_nos = [555555555555555555555555555555555555555555555555555555555555, #Extremley long interger
                         6000000000001, # Should not accept more than 6 trillion (6 000 000 000 000)
                         -1, # A zero,
                         'non interger',
                        1734908754, # The DeviceKey does not exist
                        10, # Just a guessed number
                        0,
                        ]
        
        
        for duration in durations:
            
            i=0
            for wrong_reg_no in wrong_reg_nos:
                i+=1
                
                price = PriceGeneratorClass.account_price_calc(duration)
                
                if i == 1 or i == 2 or i == 3 or i == 4:
                    # Check if the request will fail if given a non interger, more that 6 trillion and non integer #
                    response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':wrong_reg_no, 'amount': price}, follow=True)
        
                    self.assertEqual(response.status_code, 200)
                    self.assertNotContains(response, 'An Error Found - wrong_reg_no.')
                    self.assertEqual(response.templates[0].name, 'billing/make_payment_form.html')
                    
  
                    
                else:
                
                    response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':wrong_reg_no, 'amount': price}, follow=True)
        
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, 'That registration')
                    self.assertNotContains(response, 'An Error Found - wrong_reg_no.')
                    self.assertEqual(response.templates[0].name, 'billing/make_payment_form.html')
                

            # ############## After making Payment ################
            self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
            self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
            self.assertEqual(MpesaLog.objects.all().exists(), False)



class MakePaymentViewForMultipleEmployeeProfilesForTopUserTestCase(TestCase, InitialUserDataMixin):
    def setUp(self):
        
        """
        This function is defined in the 'InitialUserDataMixin' mixin
        
        It creates 2 top users, 3 stores and 5 employee users as follows

        * Top User 1 assets:
            self.user1 - top user 
            self.top_profile1 - Profile for top user -- (john@gmail.com)

            - self.store1 - Store -- (Computer Store) 
                self.manager_profile1 - Manger Employee profile for top user 1 -- (gucci@gmail.com)

                self.cashier_profile1 - Cashier Employee profile under manager profile 1 -- (kate@gmail.com)
                self.cashier_profile2 - Cashier Employee profile under manager profile 1 -- (james@gmail.com)
                self.cashier_profile3 - Cashier Employee profile under manager profile 1 -- (ben@gmail.com)

            - self.store2 - Store -- (Cloth Store)
                self.manager_profile2 - Manger Employee profile for top user 1 -- (lewis@gmail.com)

                self.cashier_profile4 - Cashier Employee profile under manager profile 2 -- (hugo@gmail.com)


        * Top User 2 assets:
            self.user2 - top user
            self.top_profile2 - Profile for top user-- (jack@gmail.com)

            - self.store3 - Store -- (Toy Store)
                self.manager_profile3 - Manger Employee profile for top user 2 -- (cristiano@gmail.com):

                self.cashier_profile5 - Cashier Employee profile under manager profile 3 -- (juliet@gmail.com)
        """
        
        self.create_initial_user_data_with_superuser_with_no_payment_history()

        # We reduce the number of employee profiles to make the test managable
        self.manager_profile1.delete()
        self.cashier_profile2.delete()
        self.cashier_profile3.delete()

        self.manager_profile2.delete()

        self.assertEqual(EmployeeProfile.objects.filter(
            profile=self.top_profile1).count(), 2)


        # Turn off maintenance mode 
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
        

        # My client
        self.client = Client()
        self.client.login(username='john@gmail.com', password='secretpass')
      
    def test_if_MakePaymentView_can_accept_1_month_payment_for_employee_profiles(self):
        
        num_of_accounts = 2
        duration = 1

        # ############## Before making Payment ############### #
        
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False) # Make sure there are no MpesaLog
        
        
        # Ensure subscriptions have the right values #
        # Subscription 1
        s1 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        
        self.assertEqual((s1.due_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s1.last_payment_date, s1.employee_profile.join_date)
        self.assertEqual(s1.days_to_go, 0)
        self.assertEqual(s1.expired, True)
        self.assertEqual(s1.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s1.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s1.get_profile(), self.top_profile1)
        self.assertEqual(s1.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
        self.assertEqual(str(s1),'Subs - kate@gmail.com')
        
        # Subscription 2
        s2 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile4.reg_no)
        
        self.assertEqual((s2.due_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s2.last_payment_date, s2.employee_profile.join_date)
        self.assertEqual(s2.days_to_go, 0)
        self.assertEqual(s2.expired, True)
        self.assertEqual(s2.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s2.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s2.get_profile(), self.top_profile1)
        self.assertEqual(s2.get_employee_profile_reg_no(), self.cashier_profile4.reg_no)
        self.assertEqual(str(s2),'Subs - hugo@gmail.com')
        
        one_month_price = PriceGeneratorClass.all_accounts_price_calc(duration, num_of_accounts)
    
        response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':self.top_profile1.reg_no, 'amount': one_month_price}, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'billing/superuser_payment_completed.html')

        # ############## After making Payment ################
        
        # Ensure a PaymentLog has the right fields after it has been created #
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there is only 1 PaymentLog
        
        pl = PaymentLog.objects.get(reg_no=self.top_profile1.reg_no)
        
        self.assertEqual(pl.amount, one_month_price)
        self.assertEqual(pl.payment_method, "manual_payment")
        self.assertEqual(pl.mpesa_id, 0)
        self.assertEqual(pl.payment_type, 'multiple accounts (2)')
        self.assertEqual(pl.email, self.top_profile1.user.email)
        self.assertEqual(pl.reg_no, self.top_profile1.reg_no)
        self.assertEqual(pl.duration, 1)
        
        

        # Ensure payments have been made for each employee profile #
        self.assertEqual(Payment.objects.all().count(), 2) # Make sure payments are only 2
        
        p1 = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        p2 = Payment.objects.get(account_reg_no=self.cashier_profile4.reg_no)
        
        # Payment 1
        self.assertEqual(p1.paymentlog, pl)
        self.assertEqual(p1.amount, (one_month_price/2))
        self.assertEqual((p1.payed_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(p1.parent_reg_no, self.top_profile1.reg_no)
        self.assertEqual(p1.account_reg_no, self.cashier_profile1.reg_no)
        self.assertEqual(p1.account_type, 'account')
        self.assertEqual(p1.duration, 1)
        
        # Payment 2
        self.assertEqual(p2.paymentlog, pl)
        self.assertEqual(p2.amount, (one_month_price/2))
        self.assertEqual((p2.payed_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(p2.parent_reg_no, self.top_profile1.reg_no)
        self.assertEqual(p2.account_reg_no, self.cashier_profile4.reg_no)
        self.assertEqual(p2.account_type, 'account')
        self.assertEqual(p2.duration, 1)
        
        # Ensure there is no MpesaLog #
        self.assertEqual(MpesaLog.objects.all().count(), 0)
        
        # Ensure subscriptions have been updated #
        # Subscription 1
        s1 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        correct_due_date = (p1.payed_date + relativedelta(months=1)).strftime("%B, %d, %Y")
        
        self.assertEqual((s1.due_date).strftime("%B, %d, %Y"), correct_due_date)
        self.assertEqual(s1.last_payment_date, p1.payed_date) # Always confirm date
        
        # Due to months with 28, 29, 30 and 31 days, we cant be sure 
        # of days_to_go value but we know the range is btwn 28 and 31#
        self.assertTrue(s1.days_to_go > 28)
        self.assertTrue(s1.days_to_go < 31)
        
        self.assertEqual(s1.expired, False)
        self.assertEqual(s1.get_due_date(), correct_due_date)
        self.assertEqual(s1.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s1.get_profile(), self.top_profile1)
        self.assertEqual(s1.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
        self.assertEqual(str(s1),'Subs - kate@gmail.com')
        
        # Subscription 2
        s2 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile4.reg_no)
        correct_due_date = (p2.payed_date + relativedelta(months=1)).strftime("%B, %d, %Y")
        
        self.assertEqual((s2.due_date).strftime("%B, %d, %Y"), correct_due_date)
        self.assertEqual(s2.last_payment_date, p2.payed_date) # Always confirm date
        
        # Due to months with 28, 29, 30 and 31 days, we cant be sure 
        # of days_to_go value but we know the range is btwn 28 an 31#
        self.assertTrue(s1.days_to_go > 28)
        self.assertTrue(s1.days_to_go < 31)
        
        self.assertEqual(s2.expired, False)
        self.assertEqual(s2.get_due_date(), correct_due_date)
        self.assertEqual(s2.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s2.get_profile(), self.top_profile1)
        self.assertEqual(s2.get_employee_profile_reg_no(), self.cashier_profile4.reg_no)
        self.assertEqual(str(s2),'Subs - hugo@gmail.com')
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's accept_payments is False#                  
        # ******************************************************************* #

        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=False
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':self.top_profile1.reg_no, 'amount': one_month_price}, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'billing/superuser_payments_not_allowed.html')


    def test_if_MakePaymentView_can_accept_6_month_payment_for_employee_profiles(self):
        
        num_of_accounts = 2
        duration = 6

        
        # ############## Before making Payment ############### #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        
        
        # Ensure subscriptions have the right values #
        # Subscription 1
        s1 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        
        self.assertEqual((s1.due_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s1.last_payment_date, s1.employee_profile.join_date)
        self.assertEqual(s1.days_to_go, 0)
        self.assertEqual(s1.expired, True)
        self.assertEqual(s1.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s1.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s1.get_profile(), self.top_profile1)
        self.assertEqual(s1.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
        self.assertEqual(str(s1),'Subs - kate@gmail.com')
        
        # Subscription 1
        s2 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile4.reg_no)
        
        self.assertEqual((s2.due_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s2.last_payment_date, s2.employee_profile.join_date)
        self.assertEqual(s2.days_to_go, 0)
        self.assertEqual(s2.expired, True)
        self.assertEqual(s2.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s2.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s2.get_profile(), self.top_profile1)
        self.assertEqual(s2.get_employee_profile_reg_no(), self.cashier_profile4.reg_no)
        self.assertEqual(str(s2),'Subs - hugo@gmail.com')
        
        
        six_months_price = PriceGeneratorClass.all_accounts_price_calc(duration, num_of_accounts)
                                                                                   
        response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':self.top_profile1.reg_no, 'amount': six_months_price}, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'billing/superuser_payment_completed.html')
        
        # ############## After making Payment ################
        
        # Ensure a PaymentLog has the right fields after it has been created #
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there is only 1 PaymentLog
        
        pl = PaymentLog.objects.get(reg_no=self.top_profile1.reg_no)
        
        self.assertEqual(pl.amount, six_months_price)
        self.assertEqual(pl.payment_method, "manual_payment")
        self.assertEqual(pl.mpesa_id, 0)
        self.assertEqual(pl.payment_type, 'multiple accounts (2)')
        self.assertEqual(pl.email, self.top_profile1.user.email)
        self.assertEqual(pl.reg_no, self.top_profile1.reg_no)
        self.assertEqual(pl.duration, 6)
        
        # Ensure payments have been made for each employee profile #
        self.assertEqual(Payment.objects.all().count(), 2) # Make sure payments are only 2
        
        p1 = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        p2 = Payment.objects.get(account_reg_no=self.cashier_profile4.reg_no)
        
        # Payment 1
        self.assertEqual(p1.paymentlog, pl)
        self.assertEqual(p1.amount, (six_months_price/2))
        self.assertEqual((p1.payed_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(p1.parent_reg_no, self.top_profile1.reg_no)
        self.assertEqual(p1.account_reg_no, self.cashier_profile1.reg_no)
        self.assertEqual(p1.account_type, 'account')
        self.assertEqual(p1.duration, 6)
        
        # Payment 2
        self.assertEqual(p2.paymentlog, pl)
        self.assertEqual(p2.amount, (six_months_price/2))
        self.assertEqual((p2.payed_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(p2.parent_reg_no, self.top_profile1.reg_no)
        self.assertEqual(p2.account_reg_no, self.cashier_profile4.reg_no)
        self.assertEqual(p2.account_type, 'account')
        self.assertEqual(p2.duration, 6)
        
        
        # Ensure there is no MpesaLog #
        self.assertEqual(MpesaLog.objects.all().count(), 0)
        
        # Ensure subscriptions have been updated #
        # Subscription 1
        s1 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        correct_due_date = (p1.payed_date + relativedelta(months=6)).strftime("%B, %d, %Y")
        
        self.assertEqual((s1.due_date).strftime("%B, %d, %Y"), correct_due_date)
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s1.last_payment_date, p1.payed_date)
        
        # Due to months with 28, 29, 30 and 31 days, we cant be sure 
        # of days_to_go value but we know the range is btwn 180 an 185        
        self.assertTrue(s1.days_to_go >= 180)
        self.assertTrue(s1.days_to_go < 185)
        
        self.assertEqual(s1.expired, False)
        self.assertEqual(s1.get_due_date(), correct_due_date)
        self.assertEqual(s1.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s1.get_profile(), self.top_profile1)
        self.assertEqual(s1.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
        self.assertEqual(str(s1),'Subs - kate@gmail.com')
        
        # Subscription 2
        s2 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile4.reg_no)
        correct_due_date = (p2.payed_date + relativedelta(months=6)).strftime("%B, %d, %Y")
        
        self.assertEqual((s2.due_date).strftime("%B, %d, %Y"), correct_due_date)
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s2.last_payment_date, p2.payed_date)
        
        # Due to months with 28, 29, 30 and 31 days, we cant be sure 
        # of days_to_go value but we know the range is btwn 180 an 185        
        self.assertTrue(s2.days_to_go >= 180)
        self.assertTrue(s2.days_to_go < 185)
        
        self.assertEqual(s2.expired, False)
        self.assertEqual(s2.get_due_date(), correct_due_date)
        self.assertEqual(s2.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s2.get_profile(), self.top_profile1)
        self.assertEqual(s2.get_employee_profile_reg_no(), self.cashier_profile4.reg_no)
        self.assertEqual(str(s2),'Subs - hugo@gmail.com')
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's accept_payments is False#                  
        # ******************************************************************* #

        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=False
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':self.top_profile1.reg_no, 'amount': six_months_price}, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'billing/superuser_payments_not_allowed.html')
        
    def test_if_MakePaymentView_can_accept_12_month_payment_for_employee_profiles(self):
        
        num_of_accounts = 2
        duration = 12

        
        # ############## Before making Payment ############### #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        
        
        # Ensure subscriptions have the right values #
        # Subscription 1
        s1 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        
        self.assertEqual((s1.due_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s1.last_payment_date, s1.employee_profile.join_date)
        self.assertEqual(s1.days_to_go, 0)
        self.assertEqual(s1.expired, True)
        self.assertEqual(s1.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s1.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s1.get_profile(), self.top_profile1)
        self.assertEqual(s1.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
        self.assertEqual(str(s1),'Subs - kate@gmail.com')
        
        # Subscription 1
        s2 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile4.reg_no)
        
        self.assertEqual((s2.due_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s2.last_payment_date, s2.employee_profile.join_date)
        self.assertEqual(s2.days_to_go, 0)
        self.assertEqual(s2.expired, True)
        self.assertEqual(s2.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s2.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s2.get_profile(), self.top_profile1)
        self.assertEqual(s2.get_employee_profile_reg_no(), self.cashier_profile4.reg_no)
        self.assertEqual(str(s2),'Subs - hugo@gmail.com')
        
        
        one_year_price = PriceGeneratorClass.all_accounts_price_calc(duration, num_of_accounts)
                                                                                     
        response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':self.top_profile1.reg_no, 'amount': one_year_price}, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'billing/superuser_payment_completed.html')
        
        # ############## After making Payment ################
        
        # Ensure a PaymentLog has the right fields after it has been created #
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there is only 1 PaymentLog
        
        pl = PaymentLog.objects.get(reg_no=self.top_profile1.reg_no)
        
        self.assertEqual(pl.amount, one_year_price)
        self.assertEqual(pl.payment_method, "manual_payment")
        self.assertEqual(pl.mpesa_id, 0)
        self.assertEqual(pl.payment_type, 'multiple accounts (2)')
        self.assertEqual(pl.email, self.top_profile1.user.email)
        self.assertEqual(pl.reg_no, self.top_profile1.reg_no)
        self.assertEqual(pl.duration, 12)
        
        
        
        # Ensure payments have been made for each employee profile #
        self.assertEqual(Payment.objects.all().count(), 2) # Make sure payments are only 2
        
        p1 = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        p2 = Payment.objects.get(account_reg_no=self.cashier_profile4.reg_no)
        
        # Payment 1
        self.assertEqual(p1.paymentlog, pl)
        self.assertEqual(p1.amount, ( one_year_price/2))
        self.assertEqual((p1.payed_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(p1.parent_reg_no, self.top_profile1.reg_no)
        self.assertEqual(p1.account_reg_no, self.cashier_profile1.reg_no)
        self.assertEqual(p1.account_type, 'account')
        self.assertEqual(p1.duration, 12)
        
        # Payment 2
        self.assertEqual(p2.paymentlog, pl)
        self.assertEqual(p2.amount, ( one_year_price/2))
        self.assertEqual((p2.payed_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(p2.parent_reg_no, self.top_profile1.reg_no)
        self.assertEqual(p2.account_reg_no, self.cashier_profile4.reg_no)
        self.assertEqual(p2.account_type, 'account')
        self.assertEqual(p2.duration, 12)
        
        
        # Ensure there is no MpesaLog #
        self.assertEqual(MpesaLog.objects.all().count(), 0)
        
        # Ensure subscriptions have been updated #
        # Subscription 1
        s1 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        correct_due_date = (p1.payed_date + relativedelta(months=12)).strftime("%B, %d, %Y")
        
        self.assertEqual((s1.due_date).strftime("%B, %d, %Y"), correct_due_date)
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s1.last_payment_date, p1.payed_date)
        
        # Due to months with 28, 29, 30 and 31 days, we cant be sure 
        # of days_to_go value but we know the range is btwn 363 an 368
        self.assertTrue(s1.days_to_go > 363)
        self.assertTrue(s1.days_to_go < 368)
        
        self.assertEqual(s1.expired, False)
        self.assertEqual(s1.get_due_date(), correct_due_date)
        self.assertEqual(s1.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s1.get_profile(), self.top_profile1)
        self.assertEqual(s1.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
        self.assertEqual(str(s1),'Subs - kate@gmail.com')
        
        # Subscription 1
        s2 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile4.reg_no)
        correct_due_date = (p2.payed_date + relativedelta(months=12)).strftime("%B, %d, %Y")
        
        self.assertEqual((s2.due_date).strftime("%B, %d, %Y"), correct_due_date)
        #Make sure when created last_payment_date take employee_profile.join_date#
        self.assertEqual(s2.last_payment_date, p2.payed_date)
        
        # Due to months with 28, 29, 30 and 31 days, we cant be sure 
        # of days_to_go value but we know the range is btwn 363 an 368
        self.assertTrue(s2.days_to_go > 363)
        self.assertTrue(s2.days_to_go < 368)
        
        self.assertEqual(s2.expired, False)
        self.assertEqual(s2.get_due_date(), correct_due_date)
        self.assertEqual(s2.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(s2.get_profile(), self.top_profile1)
        self.assertEqual(s2.get_employee_profile_reg_no(), self.cashier_profile4.reg_no)
        self.assertEqual(str(s2),'Subs - hugo@gmail.com')
        
        
    def test_if_MakePaymentView_can_handle_a_wrong_amount(self):      
        
        # ############## Before making Payment ############### #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment

        # Amounts below 1 wont pass form validation so those type of values 
        # should be tested in the form
        
        wrong_prices = ['wrong format',
                        -1,
                        555555555555555555555555555555555555555555555555555555555555, #Extremley long interger
                        0,
                        3100, 
                        14500, 
                        2300, 
                        200000,
                        ]
      
        
        i = 0
        for wrong_price in wrong_prices:
            i+=1

            response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':self.top_profile1.reg_no, 'amount': wrong_price}, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.templates[0].name, 'billing/make_payment_form.html')
   
            if i == 1 or i == 2:
                self.assertNotContains(response, 'An Error Found - Wrong amount.')

            else:
                self.assertContains(response, 'An Error Found - Wrong amount.')
            
            
            # ############## After making Payment ################
            self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
            self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
            self.assertEqual(MpesaLog.objects.all().exists(), False)
            
            # Ensure subscriptions dont get updated #
            # Subscription 1
            s1 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
            
            self.assertEqual((s1.due_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
            #Make sure when created last_payment_date take employee_profile.join_date#
            self.assertEqual(s1.last_payment_date, s1.employee_profile.join_date)
            self.assertEqual(s1.days_to_go, 0)
            self.assertEqual(s1.expired, True)
            self.assertEqual(s1.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))
            self.assertEqual(s1.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
            self.assertEqual(s1.get_profile(), self.top_profile1)
            self.assertEqual(s1.get_employee_profile_reg_no(), self.cashier_profile1.reg_no)
            self.assertEqual(str(s1),'Subs - kate@gmail.com')
            
            # Subscription 1
            s2 = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile4.reg_no)
            self.assertEqual((s2.due_date).strftime("%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
            #Make sure when created last_payment_date take employee_profile.join_date#
            self.assertEqual(s2.last_payment_date, s2.employee_profile.join_date)
            self.assertEqual(s2.days_to_go, 0)
            self.assertEqual(s2.expired, True)
            self.assertEqual(s2.get_due_date(), (timezone.now()).strftime("%B, %d, %Y"))
            self.assertEqual(s2.get_last_payment_date(), (timezone.now()).strftime("%B, %d, %Y"))
            self.assertEqual(s2.get_profile(), self.top_profile1)
            self.assertEqual(s2.get_employee_profile_reg_no(), self.cashier_profile4.reg_no)
            self.assertEqual(str(s2),'Subs - hugo@gmail.com')
            

    def test_if_MakePaymentView_can_handle_wrong_reg_no(self):
        # Create DeviceKey and Device1 #
    
        num_of_accounts = 2
        durations = [1, 6, 12]
        
        
        wrong_reg_nos = [555555555555555555555555555555555555555555555555555555555555, #Extremley long interger
                         6000000000001, # Should not accept more than 6 trillion (6 000 000 000 000)
                         -1, # A zero,
                         'non interger',
                        1734908754, # The DeviceKey does not exist
                        10, # Just a guessed number
                        0,
                        ]
                
        for duration in durations:
            
            i=0
            for wrong_reg_no in wrong_reg_nos:
                i+=1
                
                # ############## Before making Payment ############### #
                self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
                self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
      
                
                price = PriceGeneratorClass.all_accounts_price_calc(duration, num_of_accounts)

                response = self.client.post(reverse('billing:super_make_payment' ),{'account_no':wrong_reg_no, 'amount': price}, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.templates[0].name, 'billing/make_payment_form.html')

                if i == 3 or i == 4:
                    self.assertNotContains(response, 'That registration number is not recognized.')

                else:
                    self.assertContains(response, 'That registration number is not recognized.')


                # ############## After making Payment ################
                self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
                self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
                self.assertEqual(MpesaLog.objects.all().exists(), False)
