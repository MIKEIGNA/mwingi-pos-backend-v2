from django.db import transaction
from django.urls import reverse
from django.conf import settings

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.mpesa_testing_data import c2b_return_data
from core.test_utils.initial_user_data import InitialUserDataMixin

from profiles.models import Profile
from mylogentries.models import PaymentLog, MpesaLog
from mysettings.models import MySetting

from billing.utils.payment_utils.price_gen import PriceGeneratorClass
from billing.models import Payment


SAFCOM_VALIDATION_ACCEPTED = settings.SAFCOM_VALIDATION_ACCEPTED
SAFCOM_VALIDATION_REJECTED = settings.SAFCOM_VALIDATION_REJECTED
SAFCOM_CONFIRMATION_SUCCESS = settings.SAFCOM_CONFIRMATION_SUCCESS
SAFCOM_CONFIRMATION_FAILURE = settings.SAFCOM_CONFIRMATION_FAILURE


class MpesaPaymentViewConfirmationForSingleTeamsTestCase(APITestCase, InitialUserDataMixin):
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
        

        # Turn off maintenance mode 
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
        
    
    
    def test_if_MpesaPaymentView_can_confirm_1_month_payment_for_single_teams(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
               
        # Check if the request was successful #
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, SAFCOM_CONFIRMATION_SUCCESS)
        
        # ############## Make sure no payment was made during confirmation ################
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().count(), 1) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().count(), 1) # Make sure there are no Mpesa   
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's accept_payments is False#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=False
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        self.assertEqual(response.status_code, 503)
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's maintenance is true#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=True
        ms.maintenance=True
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        self.assertEqual(response.status_code, 503)

    def test_if_MpesaPaymentView_can_confirm_6_months_payment_for_single_teams(self):
        
        duration = 6
        c2b_data = c2b_return_data()
        
        six_months_price = PriceGeneratorClass.account_price_calc(duration)
                
        c2b_data['TransAmount'] = six_months_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
               
        # Check if the request was successful #
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, SAFCOM_CONFIRMATION_SUCCESS)
        
        # ############## Make sure no payment was made during confirmation ################
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().count(), 1) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().count(), 1) # Make sure there are no Mpesa
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's accept_payments is False#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=False
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        self.assertEqual(response.status_code, 503)
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's maintenance is true#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=True
        ms.maintenance=True
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        self.assertEqual(response.status_code, 503)

   
    def test_if_MpesaPaymentView_can_confirm_12_months_payment_for_single_teams(self):
        
        duration = 12
        c2b_data = c2b_return_data()
        
    
        one_year_price = PriceGeneratorClass.account_price_calc(duration)
                
        c2b_data['TransAmount'] = one_year_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
               
        # Check if the request was successful #
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, SAFCOM_CONFIRMATION_SUCCESS)
        
        # ############## Make sure no payment was made during confirmation ################
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().count(), 1) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().count(), 1) # Make sure there are no Mpesa
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's accept_payments is False#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=False
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        self.assertEqual(response.status_code, 503)
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's maintenance is true#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=True
        ms.maintenance=True
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        self.assertEqual(response.status_code, 503)
        
        
    def test_if_MpesaPaymentView_wont_confirm_a_wrong_amount(self):
        
        c2b_data = c2b_return_data()

        wrong_prices = [555555555555555555555555555555555555555555555555555555555555, #Extremley long interger
                        'wrong format',
                        -1, 
                        0,
                        3100, 
                        14500, 
                        2300, 
                        200000,
                        ]
        
        # These expressins are enclosed within transaction atomic to prevent them
        # from raising an atomic block error
        with transaction.atomic():
            
            i = 0
            for wrong_price in wrong_prices:
                i+=1
                
                c2b_data['TransID'] = c2b_data['TransID'] + str(i) # This is to give the TransID unique
                c2b_data['TransAmount'] = wrong_price
                c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
                
                
                if i == 1:
                    # Check if the request will fail for extremley long numbers#
                    response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
                    self.assertEqual(response.status_code, 400)
                    
                elif i == 2:
                    # Check if the request will fail non integer amount#
                    response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
                    self.assertEqual(response.status_code, 400)
                    
                else:
                    # Check if the request will fail for wrong amounts #
                    response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data, SAFCOM_CONFIRMATION_FAILURE)
                
                    
        # ############## Make sure no payment was made during confirmation ################
        self.assertEqual(PaymentLog.objects.all().count(), 0) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().count(), 0) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().count(), 0) # Make sure there are no Mpesa
    
       
    def test_if_MpesaPaymentView_wont_confirm_wrong_reg_no(self):
        # Create DeviceKey and Device1 #
        c2b_data = c2b_return_data()
        durations = [1, 6, 12]
        
        
        wrong_reg_nos = ['non interger',
                        555555555555555555555555555555555555555555555555555555555555, #Extremley long interger
                        1734908754, # The DeviceKey does not exist
                        10, # Just a guessed number
                        0,
                        -1, # A zero,
                        ]
        
        
        # These expressins are enclosed within transaction atomic to prevent them
        # from raising an atomic block error
        
        with transaction.atomic():
            
            
            for duration in durations:
                
                i=0
                for wrong_reg_no in wrong_reg_nos:
                    i+=1
                    
                    one_month_price = PriceGeneratorClass.account_price_calc(duration)
                    
                    c2b_data['TransID'] = c2b_data['TransID'] + str(i) # This is to give the TransID unique
                    c2b_data['TransAmount'] = one_month_price
                    c2b_data['BillRefNumber'] = wrong_reg_no
                
                    if i == 1:
                        # Check if the request will fail if given a non interger #
                        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
                        self.assertEqual(response.status_code, 400)
                        
                    else:
                        # Check if the request will fail if given a wrong reg no#
                        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(response.data, SAFCOM_CONFIRMATION_FAILURE)
                
                
        # Make sure Payment was not accepted #
        self.assertEqual(PaymentLog.objects.all().count(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().count(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().count(), 0) # Make sure there are no Mpesa
        
        
    def test_if_MpesaPaymentView_wont_confirm_duplicate_payment_for_single_teams(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
               
        # Check if the request was successful #
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, SAFCOM_CONFIRMATION_SUCCESS)
        
        # ############## Make sure no payment was made during confirmation ################
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().count(), 1) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().count(), 1) # Make sure there are no MpesaLog
    
    
        # Try making another Mpesa Duplicate #
        
        # Check if the request was unsuccessful #
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
               
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, SAFCOM_CONFIRMATION_FAILURE)
        
        # ############## Make sure no payment was made during confirmation ################
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().count(), 1) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().count(), 1) # Make sure there are no MpesaLog



class MpesaPaymentViewValidationForSingleTeamsTestCase(APITestCase, InitialUserDataMixin):
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
        

        # Turn off maintenance mode 
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
        
        
    def test_if_MpesaPaymentView_can_validate_1_month_payment_for_single_teams(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
               
        # Check if the request was successful #
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, SAFCOM_VALIDATION_ACCEPTED)
        
        # ############## Make sure no payment was made during validation ################
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False) # Make sure there are no Mpesa
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's accept_payments is False#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=False
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
        
        self.assertEqual(response.status_code, 503)
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's maintenance is true#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=True
        ms.maintenance=True
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
        
        self.assertEqual(response.status_code, 503)
        
      
    def test_if_MpesaPaymentView_can_validate_6_months_payment_for_single_teams(self):
        
        duration = 6
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
                
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
               
        # Check if the request was successful #
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, SAFCOM_VALIDATION_ACCEPTED)
        
        # ############## Make sure no payment was made during validation ################
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False) # Make sure there are no Mpesa
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's accept_payments is False#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=False
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
        
        self.assertEqual(response.status_code, 503)
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's maintenance is true#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=True
        ms.maintenance=True
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
        
        self.assertEqual(response.status_code, 503)
        
    def test_if_MpesaPaymentView_can_validate_12_months_payment_for_single_teams(self):
        
        duration = 12
        c2b_data = c2b_return_data()
        
    
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
                
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
               
        # Check if the request was successful #
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, SAFCOM_VALIDATION_ACCEPTED)
        
        # ############## Make sure no payment was made during validation ################
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False) # Make sure there are no Mpesa
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's accept_payments is False#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=False
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
        
        self.assertEqual(response.status_code, 503)
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's maintenance is true#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=True
        ms.maintenance=True
        ms.save()
        
        # Try to make a new payment#
        response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
        
        self.assertEqual(response.status_code, 503)
         
      
    def test_if_MpesaPaymentView_wont_validate_a_wrong_amount_for_single_teams(self):
        
        c2b_data = c2b_return_data()
        
        wrong_prices = [555555555555555555555555555555555555555555555555555555555555, #Extremley long interger
                        'wrong format',
                        -1, 
                        0,
                        3100, 
                        14500, 
                        2300, 
                        200000,
                        ]
        
        i=0
        for wrong_price in wrong_prices:
            i+=1
            
            c2b_data['TransAmount'] = wrong_price
            c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
            
            
            if i == 1:
                # Check if the request will fail for extremley long numbers#
                response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
                self.assertEqual(response.status_code, 400)
                    
            elif i == 2:
                # Check if the request will fail non integer amount#
                response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
                self.assertEqual(response.status_code, 400)
                    
            else:
                # Check if the request will fail for wrong amounts #
                response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data, SAFCOM_VALIDATION_REJECTED)
    
            
        # ############## Make sure no payment was made during validation ################
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False) # Make sure there are no Mpesa

             
    def test_if_MpesaPaymentView_wont_validate_wrong_reg_no_for_single_teams(self):
        # Create DeviceKey and Device1 #
        c2b_data = c2b_return_data()
        durations = [1, 6, 12]
        
                
        wrong_reg_nos = ['non interger',
                        555555555555555555555555555555555555555555555555555555555555, #Extremley long interger
                        1734908754, # The DeviceKey does not exist
                        10, # Just a guessed number
                        0,
                        -1, # A zero,
                        ]
        
    
        for duration in durations:
            
            i=0
            for wrong_reg_no in wrong_reg_nos:
                i+=1
                           
                month_price = PriceGeneratorClass.account_price_calc(duration)
                
                c2b_data['TransAmount'] = month_price
                c2b_data['BillRefNumber'] = wrong_reg_no
                
                if i == 1:
                    # Check if the request will fail if given a non interger #
                    response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
                    self.assertEqual(response.status_code, 400)
                        
                else:
                    # Check if the request will fail if given a wrong reg no#
                    response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data, SAFCOM_VALIDATION_REJECTED)
                
                
        # Make sure Payment was not accepted #
        self.assertEqual(PaymentLog.objects.all().exists(), False) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().exists(), False) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().exists(), False) # Make sure there are no Mpesa

       
   
    def test_if_MpesaPaymentView_wont_validate_duplicate_payment_for_single_teams(self):
        profile = Profile.objects.get(user__email='john@gmail.com')
        
        duration = 1
        c2b_data = c2b_return_data()
        
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        # Check if the request was successful #
        response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)
               
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, SAFCOM_VALIDATION_ACCEPTED)
        
        # ############## Make sure no payment was made during validation ################
        self.assertEqual(PaymentLog.objects.all().count(), 0) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().count(), 0) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().count(), 0) # Make sure there are no MpesaLog
        
        
        # Create a MpesaLog
        payment_log = PaymentLog.objects.create(amount=one_month_price,
                                                payment_method = 'mpesa',
                                                    payment_type='single {}'.format('team'),
                                                    email=profile.user.email,
                                                    reg_no=self.cashier_profile1.reg_no,
                                                    duration=duration,
                                                    )
        
        
        
        
        MpesaLog.objects.create(paymentlog = payment_log ,
                                transaction_type= c2b_data ["TransactionType"],
                                trans_id = c2b_data ["TransID"],
                                trans_time = c2b_data ["TransTime"],
                                trans_amount = c2b_data ["TransAmount"],
                                business_shortcode = c2b_data ["BusinessShortCode"],
                                bill_ref_number = c2b_data ["BillRefNumber"],
                                invoice_number = c2b_data ["InvoiceNumber"],
                                org_account_balance = c2b_data ["OrgAccountBalance"],
                                third_party_trans_id =c2b_data ["ThirdPartyTransID"],
                                msisdn = c2b_data ["MSISDN"],
                                first_name = c2b_data ["FirstName"],
                                middle_name = c2b_data ["MiddleName"],
                                last_name = c2b_data ["LastName"],
                                )
        
        # Check if the request was successful #
        response = self.client.post(reverse('billing:mpesa_validation'), c2b_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, SAFCOM_VALIDATION_REJECTED)
        
        # ############## Make sure no payment was made during confirmation ################
        self.assertEqual(PaymentLog.objects.all().count(), 1) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().count(), 0) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.filter(trans_id = c2b_data['TransID']).count(), 1) # Make sure there are no MpesaLog


