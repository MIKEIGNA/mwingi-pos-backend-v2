from django.db import transaction
from django.urls import reverse

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.mpesa_testing_data import c2b_return_data
from core.test_utils.initial_user_data import InitialUserDataMixin

from mylogentries.models import PaymentLog, MpesaLog
from mysettings.models import MySetting

from billing.models import Payment
from billing.utils.payment_utils.price_gen import PriceGeneratorClass


class MpesaPaymentViewSerializerTestCase(APITestCase, InitialUserDataMixin):
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
        
    def test_if_MpesaPaymentViewSerializer_requires_TransactionType(self):

        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
    
        # Test for failure when TransactionType is not present #
        del c2b_data['TransactionType']
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)

    def test_if_MpesaPaymentViewSerializer_requires_TransID(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        # Test for failure when TransID is not present #
        del c2b_data['TransID']
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)

      
    def test_if_MpesaPaymentViewSerializer_requires_TransTime(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        
        # Test for failure if given the wrong transtime format#
        # ******************************************************************#
        wrong_trans_times = [2222222222222222222222222222222222222222222222222222222222222,  # Extremley long interger
                             "wong format"
                             ]
        
        i=0
        for wrong_trans_time in wrong_trans_times:
            # Test if we can handle and Extremly long TransTime#
            c2b_data['TransTime'] = wrong_trans_time
            
            response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
            self.assertEqual(response.status_code, 400)
            
            i+=1
        
        
        # Test for failure when TransTime is not present #
        # ******************************************************************#
        del c2b_data['TransTime']
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
    def test_if_MpesaPaymentViewSerializer_requires_TransAmount(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        # Test for failure if given the wrong TransAmount format#     
        # Here we dont test for TransAmount format because it has been extensivlye tested
        # below
        
        # ******************************************************************#
        # Test for failure when TransAmount is not present #
        # ******************************************************************#
        del c2b_data['TransAmount']
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
    def test_if_MpesaPaymentViewSerializer_requires_BusinessShortCode(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        
        # Test for failure if given the wrong BusinessShortCode format#     
        # Here we dont test for BusinessShortCode format because it has been extensivlye tested
        # below

        # ******************************************************************#
        # Test for failure when BusinessShortCode is not present #
        # ******************************************************************#
        del c2b_data['BusinessShortCode']
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
    def test_if_MpesaPaymentViewSerializer_requires_BillRefNumber(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        
        # Test for failure if given the wrong BillRefNumber format#     
        # Here we dont test for BillRefNumber format because it has been extensivlye tested
        # below
        
        # ******************************************************************#
        # Test for failure when BillRefNumber is not present #
        
        del c2b_data['BillRefNumber']
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
       
    def test_if_MpesaPaymentViewSerializer_requires_InvoiceNumber(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        # Test for failure when InvoiceNumber is not present #
        del c2b_data['InvoiceNumber']
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
    def test_if_MpesaPaymentViewSerializer_requires_OrgAccountBalance(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        # Test for failure when OrgAccountBalance is not present #
        del c2b_data['OrgAccountBalance']
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
    def test_if_MpesaPaymentViewSerializer_requires_ThirdPartyTransID(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        # Test for failure when ThirdPartyTransID is not present #
        del c2b_data['ThirdPartyTransID']
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
    def test_if_MpesaPaymentViewSerializer_requires_MSISDN(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        
        # Test for failure if given the wrong MSISDN format#     
        # Here we dont test for MSISDN format because it has been extensivlye tested
        # below
        
        # ******************************************************************#
        
        # Test for failure when MSISDN is not present #
        del c2b_data['MSISDN']
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
 
        
    def test_if_MpesaPaymentViewSerializer_requires_FirstName(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        # Test for failure when FirstName is not present #
        del c2b_data['FirstName']
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
    def test_if_MpesaPaymentViewSerializer_requires_MiddleName(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        # Test for failure when MiddleName is not present #
        del c2b_data['MiddleName']
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
    def test_if_MpesaPaymentViewSerializer_requires_LastName(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        # Test for failure when LastName is not present #
        del c2b_data['LastName']
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)

        
    def test_if_MpesaPaymentViewSerializer_requires_cannot_accept_a_wrong_BusinessShortCode(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        c2b_data['BusinessShortCode'] = 65845555555555555555555555555555555555555555555555555555555555 # Wrong BusinessShortCode
        
        # Test for failure when TransactionType is not present #
        
        response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 200)
        
        
        # ############## Make sure no payment was made during confirmation ################
        self.assertEqual(PaymentLog.objects.all().count(), 0) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().count(), 0) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().count(), 0) # Make sure there are no Mpesa
      
    def test_if_MpesaPaymentViewSerializer_wont_allow_a_wrong_non_safaricom_MSISDN(self):
        
        duration = 1
        c2b_data = c2b_return_data()

        wrong_phones = ['25470022332 non integer', # Number with letters
                               432922332222, # Number not starting with 07
                               1729223322, # Number not starting with 07
                               254739223322, # Non safcom number
                               254740223322, # Non safcom number
                               254759223322, # Non safcom number
                         254760223322, # Non safcom number
                         254779223322, # Non safcom number
                         254780223322, # Non safcom number
                         2547102233222, # Long Number
                         25471022332 ,  # Short Number
                         254710223325555555555555555555555555555555555555555555555555555555555555 ,  # Extremly long integer
                         ]
        
        
        # These expressins are enclosed within transaction atomic to prevent them
        # from raising an atomic block error
        with transaction.atomic():
            
            i = 0
            for wrong_number in wrong_phones:
                i+=1
                
                one_month_price = PriceGeneratorClass.account_price_calc(duration)
                
                c2b_data['TransID'] = c2b_data['TransID'] + str(i) # This is to give the TransID unique
                c2b_data['TransAmount'] = one_month_price
                c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
                c2b_data['MSISDN'] = wrong_number
                
                
                if i == 1:
                    # Check if the request will fail for non interger#
                    response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
                    self.assertEqual(response.status_code, 400)
                else:
                    # Check if the request will fail with wrong phone#
                    response = self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
                    self.assertEqual(response.status_code, 200)
                
        # ############## Make sure no payment was made during confirmation ################
        self.assertEqual(PaymentLog.objects.all().count(), 0) # Make sure there are no PaymentLog
        self.assertEqual(Payment.objects.all().count(), 0) # Make sure there are no Payment
        self.assertEqual(MpesaLog.objects.all().count(), 0) # Make sure there are no Mpesa

