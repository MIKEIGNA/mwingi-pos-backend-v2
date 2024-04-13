from decimal import Decimal
from dateutil.relativedelta import relativedelta

from django.utils import timezone

from core.test_utils.custom_testcase import TestCase
from core.test_utils.mpesa_testing_data import c2b_return_data
from core.test_utils.initial_user_data import InitialUserDataMixin

from mylogentries.models import PaymentLog, MpesaLog
from profiles.models import EmployeeProfile

from billing.models import Subscription, Payment
from billing.utils.payment_utils.price_gen import PriceGeneratorClass
from billing.utils.payment_utils.accept_payment import AcceptPayment


class AcceptPaymentConfirmationForSingleEmployeeProfileTestCase(TestCase, InitialUserDataMixin):

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
        
        self.create_initial_user_data_with_no_payment_history() 
        
        # We reduce the number of employee profiles to make the test managable
        self.manager_profile1.delete()
        self.cashier_profile2.delete()
        self.cashier_profile3.delete()

        self.manager_profile2.delete()

        self.assertEqual(EmployeeProfile.objects.filter(
            profile=self.top_profile1).count(), 2)

    def test_if_AcceptPayment_can_accept_1_month_payment_for_single_employee_profiles(self):
        
        duration = 1
        request_type = "confirmation"
        c2b_data = c2b_return_data()
        
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
                    
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = str(self.cashier_profile1.reg_no) # In AcceptPayment this is first treated as a string
        
        complete_payment_info = {"payment_method": "mpesa",
                        "request_type": request_type,
                        "payment_info": c2b_data}
        
        
        payment_result, error_result = AcceptPayment(**complete_payment_info).accept_payments()
        self.assertEqual(payment_result, True)
        self.assertEqual(error_result, False)
        
        
        # ############## After making Payment ################
        
        # Ensure a PaymentLog has the right fields after it has been created #
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there is only 1 PaymentLog
        
        pl = PaymentLog.objects.get(reg_no=self.cashier_profile1.reg_no)
        
        self.assertEqual(pl.amount, one_month_price)
        self.assertEqual(pl.payment_method, "mpesa")
        self.assertEqual(pl.mpesa_id, MpesaLog.objects.all()[0].id)
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
        
        
        # Ensure a MpesaLog has the right fields after it has been created #
        self.assertEqual(MpesaLog.objects.all().count(), 1) # Make sure there is only 1 MpesaLog
        
        ml=MpesaLog.objects.get(trans_id=c2b_data['TransID'])
        
        self.assertEqual(ml.paymentlog, pl)
        self.assertEqual(ml.transaction_type, c2b_data["TransactionType"])
        self.assertEqual(ml.trans_id,  c2b_data['TransID'])
        self.assertEqual(ml.trans_time,  int(c2b_data["TransTime"]))
        self.assertEqual(ml.trans_amount, one_month_price)
        self.assertEqual(ml.business_shortcode, c2b_data["BusinessShortCode"])
        self.assertEqual(ml.bill_ref_number, self.cashier_profile1.reg_no)
        self.assertEqual(ml.invoice_number, 0)
        self.assertEqual(ml.org_account_balance, Decimal('0.00') )
        self.assertEqual(ml.third_party_trans_id, c2b_data["ThirdPartyTransID"])
        self.assertEqual(ml.msisdn, c2b_data["MSISDN"])
        self.assertEqual(ml.first_name, c2b_data["FirstName"])
        self.assertEqual(ml.middle_name, c2b_data["MiddleName"])
        self.assertEqual(ml.last_name, c2b_data["LastName"])

        
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
             
    def test_if_AcceptPayment_can_accept_6_months_payment_for_single_employee_profiles(self):
        
        duration = 6
        request_type = "confirmation"
        c2b_data = c2b_return_data()
        
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
        
        c2b_data['TransAmount'] = six_months_price
        c2b_data['BillRefNumber'] = str(self.cashier_profile1.reg_no) # In AcceptPayment this is first treated as a string
        
        complete_payment_info = {"payment_method": "mpesa",
                        "request_type": request_type,
                        "payment_info": c2b_data}
        
        
        payment_result, error_result = AcceptPayment(**complete_payment_info).accept_payments()
        self.assertEqual(payment_result, True)
        self.assertEqual(error_result, False)
        
        
        # ############## After making Payment ################
        
        # Ensure a PaymentLog has the right fields after it has been created #
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there is only 1 PaymentLog
        
        pl = PaymentLog.objects.get(reg_no=self.cashier_profile1.reg_no)
        
        self.assertEqual(pl.amount, six_months_price)
        self.assertEqual(pl.payment_method, "mpesa")
        self.assertEqual(pl.mpesa_id, MpesaLog.objects.all()[0].id)
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
        
        
        # Ensure a MpesaLog has the right fields after it has been created #
        self.assertEqual(MpesaLog.objects.all().count(), 1) # Make sure there is only 1 MpesaLog
        
        ml=MpesaLog.objects.get(trans_id=c2b_data['TransID'])
        
        self.assertEqual(ml.paymentlog, pl)
        self.assertEqual(ml.transaction_type, c2b_data["TransactionType"])
        self.assertEqual(ml.trans_id,  c2b_data['TransID'])
        self.assertEqual(ml.trans_time,  int(c2b_data["TransTime"]))
        self.assertEqual(ml.trans_amount, six_months_price)
        self.assertEqual(ml.business_shortcode, c2b_data["BusinessShortCode"])
        self.assertEqual(ml.bill_ref_number, self.cashier_profile1.reg_no)
        self.assertEqual(ml.invoice_number, 0)
        self.assertEqual(ml.org_account_balance, Decimal('0.00') )
        self.assertEqual(ml.third_party_trans_id, c2b_data["ThirdPartyTransID"])
        self.assertEqual(ml.msisdn, c2b_data["MSISDN"])
        self.assertEqual(ml.first_name, c2b_data["FirstName"])
        self.assertEqual(ml.middle_name, c2b_data["MiddleName"])
        self.assertEqual(ml.last_name, c2b_data["LastName"])

                
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
              
    def test_if_AcceptPayment_can_accept_12_months_payment_for_single_employee_profiles(self):
        
        duration = 12
        request_type = "confirmation"
        c2b_data = c2b_return_data()
        
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
        
       
        c2b_data['TransAmount'] =  one_year_price
        c2b_data['BillRefNumber'] = str(self.cashier_profile1.reg_no) # In AcceptPayment this is first treated as a string
        
        complete_payment_info = {"payment_method": "mpesa",
                        "request_type": request_type,
                        "payment_info": c2b_data}
        
        
        payment_result, error_result = AcceptPayment(**complete_payment_info).accept_payments()
        self.assertEqual(payment_result, True)
        self.assertEqual(error_result, False)
        
        
        
        
        # ############## After making Payment ################
        
        # Ensure a PaymentLog has the right fields after it has been created #
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there is only 1 PaymentLog
        
        pl = PaymentLog.objects.get(reg_no=self.cashier_profile1.reg_no)
                
        self.assertEqual(pl.amount, one_year_price)
        self.assertEqual(pl.payment_method, "mpesa")
        self.assertEqual(pl.mpesa_id, MpesaLog.objects.all()[0].id)
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
        
        
        # Ensure a MpesaLog has the right fields after it has been created #
        self.assertEqual(MpesaLog.objects.all().count(), 1) # Make sure there is only 1 MpesaLog
        
        ml=MpesaLog.objects.get(trans_id=c2b_data['TransID'])
        
        self.assertEqual(ml.paymentlog, pl)
        self.assertEqual(ml.transaction_type, c2b_data["TransactionType"])
        self.assertEqual(ml.trans_id,  c2b_data['TransID'])
        self.assertEqual(ml.trans_time,  int(c2b_data["TransTime"]))
        self.assertEqual(ml.trans_amount,  one_year_price)
        self.assertEqual(ml.business_shortcode, c2b_data["BusinessShortCode"])
        self.assertEqual(ml.bill_ref_number, self.cashier_profile1.reg_no)
        self.assertEqual(ml.invoice_number, 0)
        self.assertEqual(ml.org_account_balance, Decimal('0.00') )
        self.assertEqual(ml.third_party_trans_id, c2b_data["ThirdPartyTransID"])
        self.assertEqual(ml.msisdn, c2b_data["MSISDN"])
        self.assertEqual(ml.first_name, c2b_data["FirstName"])
        self.assertEqual(ml.middle_name, c2b_data["MiddleName"])
        self.assertEqual(ml.last_name, c2b_data["LastName"])
        
        
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
                
    def test_if_AcceptPayment_can_handle_a_wrong_amount(self):
        self.cashier_profile1.reg_no = self.cashier_profile1.reg_no
        request_type = "confirmation"
        c2b_data = c2b_return_data()

        # ############## Before making Payment ############### #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False)
        
        wrong_prices = [-1, 0, 3100, 14500, 2300, 200000, 'wrong price format']
        
        i = 0
        for wrong_price in wrong_prices:
            i+=1
            
            c2b_data['TransID'] = c2b_data['TransID'] + str(i) # This is to give the TransID unique
            c2b_data['TransAmount'] = wrong_price
            c2b_data['BillRefNumber'] = str(self.cashier_profile1.reg_no) # In AcceptPayment this is first treated as a string
        
            complete_payment_info = {"payment_method": "mpesa",
                        "request_type": request_type,
                        "payment_info": c2b_data}
            
            payment_result, error_result = AcceptPayment(**complete_payment_info).accept_payments()
            self.assertEqual(payment_result, False)

            if i == 7:
                 
                # error_result will only be wrong_amount when the amount 
                # is in the right format but wrong amount
                self.assertEqual(error_result, False)
            else:
                self.assertEqual(error_result, 'Wrong amount.')

            
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

    def test_if_AcceptPayment_can_handle_wrong_reg_no(self):
        # Create DeviceKey and Device1 #

        request_type = "confirmation"
        durations = [1, 6, 12]
        c2b_data = c2b_return_data()
        
        
        wrong_reg_nos = [
            1734908754, # The DeviceKey does not exist
            10, # Just a guessed number
            0,
            -1, # A zero,
            "wrong reg no format"
            ]
        
        for duration in durations:
            
            i=0
            for wrong_reg_no in wrong_reg_nos:
                i+=1
                
                # ############## Before making Payment ############### #
                self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
                self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
                
                
                price = PriceGeneratorClass.account_price_calc(duration)
        
      
                c2b_data['TransID'] = c2b_data['TransID'] + str(i) # This is to give the TransID unique
                c2b_data['TransAmount'] = price
                c2b_data['BillRefNumber'] = str(wrong_reg_no) # In AcceptPayment this is first treated as a string
        
                complete_payment_info = {"payment_method": "mpesa",
                        "request_type": request_type,
                        "payment_info": c2b_data}
            
                payment_result, error_result = AcceptPayment(**complete_payment_info).accept_payments()
                self.assertEqual(payment_result, False)

                if i == 5:
                    # error_result will only be wrong_reg_no when the reg no is 
                    # in the right format but wrong reg no
                    self.assertEqual(error_result, False)

                else:
                    self.assertEqual(error_result, 'Account No is not recognized.')
                
                
                # ############## After making Payment ################
                self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
                self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
                self.assertEqual(MpesaLog.objects.all().exists(), False)
                                           
    def test_if_AcceptPayment_can_handle_a_wrong_payment_method_for_single_employee_profiles(self):
        self.cashier_profile1.reg_no = self.cashier_profile1.reg_no
        duration = 1
        request_type = "confirmation"
        c2b_data = c2b_return_data()
        
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
                    
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = str(self.cashier_profile1.reg_no) # In AcceptPayment this is first treated as a string
        
        complete_payment_info = {"payment_method": "wrong payment",
                        "request_type": request_type,
                        "payment_info": c2b_data}
        
        
        payment_result, error_result = AcceptPayment(**complete_payment_info).accept_payments()
        self.assertEqual(payment_result, False)
        self.assertEqual(error_result, False)
        
        
        # ############## After making Payment ################
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False)
                
                       
class AcceptPaymentValidationForSingleEmployeeProfilesTestCase(TestCase, InitialUserDataMixin):                

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
        
        self.create_initial_user_data_with_no_payment_history() 
        
        # We reduce the number of employee profiles to make the test managable
        self.manager_profile1.delete()
        self.cashier_profile2.delete()
        self.cashier_profile3.delete()

        self.manager_profile2.delete()

        self.assertEqual(EmployeeProfile.objects.filter(
            profile=self.top_profile1).count(), 2)

    def test_if_AcceptPayment_can_accept_1_month_payment_for_single_employee_profiles(self):
        self.cashier_profile1.reg_no = self.cashier_profile1.reg_no
        duration = 1
        request_type = "validation"
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        

        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = str(self.cashier_profile1.reg_no) # In AcceptPayment this is first treated as a string
        
        complete_payment_info = {"payment_method": "mpesa",
                        "request_type": request_type,
                        "payment_info": c2b_data}
        
        
        payment_result, error_result = AcceptPayment(**complete_payment_info).accept_payments()
        self.assertEqual(payment_result, True)
        self.assertEqual(error_result, False)
        
    
        # Make sure Payment was not accepted #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False) # Make sure there are no MpesaLog
              
    def test_if_AcceptPayment_can_accept_6_months_payment_for_single_employee_profiles(self):
        self.cashier_profile1.reg_no = self.cashier_profile1.reg_no
        duration = 6
        request_type = "validation"
        c2b_data = c2b_return_data()
        
        
        six_months_price = PriceGeneratorClass.account_price_calc(duration)
        
        
        c2b_data['TransAmount'] = six_months_price
        c2b_data['BillRefNumber'] = str(self.cashier_profile1.reg_no) # In AcceptPayment this is first treated as a string
        
        complete_payment_info = {"payment_method": "mpesa",
                        "request_type": request_type,
                        "payment_info": c2b_data}
        
        payment_result, error_result = AcceptPayment(**complete_payment_info).accept_payments()
        self.assertEqual(payment_result, True)
        self.assertEqual(error_result, False)
        
        
        # Make sure Payment was not accepted #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Paymen
        self.assertEqual(MpesaLog.objects.all().exists(), False) # Make sure there are no MpesaLog
              
    def test_if_AcceptPayment_can_accept_12_months_payment_for_single_employee_profiles(self):
        self.cashier_profile1.reg_no = self.cashier_profile1.reg_no
        duration = 12
        request_type = "validation"
        c2b_data = c2b_return_data()
        
    
        one_year_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_year_price
        c2b_data['BillRefNumber'] = str(self.cashier_profile1.reg_no) # In AcceptPayment this is first treated as a string
        
        complete_payment_info = {"payment_method": "mpesa",
                        "request_type": request_type,
                        "payment_info": c2b_data}
        
        payment_result, error_result = AcceptPayment(**complete_payment_info).accept_payments()
        self.assertEqual(payment_result, True)
        self.assertEqual(error_result, False)
        
        # Make sure Payment was not accepted #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False) # Make sure there are no MpesaLog
          
    def test_if_AcceptPayment_can_handle_a_wrong_amount(self):
        self.cashier_profile1.reg_no = self.cashier_profile1.reg_no
        request_type = "validation"
        c2b_data = c2b_return_data()

        # ############## Before making Payment ############### #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        
        
        wrong_prices = [-1, 0, 3100, 14500, 2300, 200000, "wrong reg price"]
        
        index=0
        for wrong_price in wrong_prices:
         
            c2b_data['TransAmount'] = wrong_price
            c2b_data['BillRefNumber'] = str(self.cashier_profile1.reg_no) # In AcceptPayment this is first treated as a string
        
            complete_payment_info = {"payment_method": "mpesa",
                        "request_type": request_type,
                        "payment_info": c2b_data}
        
            payment_result, error_result = AcceptPayment(**complete_payment_info).accept_payments()
            self.assertEqual(payment_result, False)
            
            if index == 6:
                # error_result will only be wrong_amount when the amount 
                # is in the right format but wrong amount
                
                self.assertEqual(error_result, False)
            else:
                self.assertEqual(error_result, 'Wrong amount.')
                
            index+=1
            
        # Make sure Payment was not accepted #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False) # Make sure there are no MpesaLog
                      
    def test_if_AcceptPayment_can_handle_wrong_reg_no(self):
        # Create DeviceKey and Device1 #

        request_type = "validation"
        durations = [1, 6, 12]
        c2b_data = c2b_return_data()
        
        
        wrong_reg_nos = [
            1734908754, # The DeviceKey does not exist
            10, # Just a guessed number
            0,
            -1, # A zero,
            "wrong reg format"
            ]
        
        
        for duration in durations:
            
            index=0
            for wrong_reg_no in wrong_reg_nos:
                # ############## Before making Payment ############### #
                self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
                self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
                
                
                price = PriceGeneratorClass.account_price_calc(duration)
      
                       
                c2b_data['TransAmount'] = price
                c2b_data['BillRefNumber'] = str(wrong_reg_no) # In AcceptPayment this is first treated as a string
        
                complete_payment_info = {"payment_method": "mpesa",
                        "request_type": request_type,
                        "payment_info": c2b_data}
        
                payment_result, error_result = AcceptPayment(**complete_payment_info).accept_payments()
                self.assertEqual(payment_result, False)
                
                if index == 4:
                    # error_result will only be wrong_reg_no when the reg no 
                    # is in the right format but wrong reg no
            
                    self.assertEqual(error_result, False)
                else:
                    self.assertEqual(error_result, 'Account No is not recognized.')
                        
        
                index+=1
                      
        # Make sure Payment was not accepted #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False) # Make sure there are no MpesaLog
