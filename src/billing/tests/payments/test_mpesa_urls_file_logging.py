import yaml

from django.urls import reverse

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.mpesa_testing_data import c2b_return_data
from core.test_utils.initial_user_data import InitialUserDataMixin
from core.test_utils.log_reader import get_log_content

from mysettings.models import MySetting

from billing.utils.payment_utils.price_gen import PriceGeneratorClass


class MpesaPaymentViewConfirmationForSingleTeamsFileLoggingTestCase(APITestCase, InitialUserDataMixin):
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
        
        
    def test_if_MpesaPaymentView_can_log_a_confirmation_single_teams(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
                       
        content = get_log_content()
        
        self.assertEqual(len(content), 1)
        
        data = content[0]
        
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/confirmation')
        self.assertEqual(data['status_code'], '200')
        self.assertEqual(data['process'], 'OK')
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's accept_payments is False#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=False
        ms.save()
        
        self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        content = get_log_content()
        
        self.assertEqual(len(content), 2)
        
        data = content[1]
        
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/confirmation')
        self.assertEqual(data['status_code'], '503')
        
        self.assertEqual(data['process'].split('<=>')[0], 'payment_not_allowed')
        self.assertEqual(data['process'].split('<=>')[1], 'payment_denied')
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(str(process_dict['TransAmount']), '1425')
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's maintenance is true#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=True
        ms.maintenance=True
        ms.save()
        
        self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        content = get_log_content()
        
        self.assertEqual(len(content), 3)
        
        data = content[2]
                
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/confirmation')
        self.assertEqual(data['status_code'], '503')
        
        self.assertEqual(data['process'].split('<=>')[0], 'maintenance')
        self.assertEqual(data['process'].split('<=>')[1], 'payment_denied')
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(str(process_dict['TransAmount']), '1425')
              
    def test_if_MpesaPaymentView_can_log_a_confirmation_single_teams_with_wrong_amount(self):
        
        c2b_data = c2b_return_data()
        
        c2b_data['TransAmount'] = 2000 # Wrong amount
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        content = get_log_content()
        
        self.assertEqual(len(content), 1)
        
        data = content[0]
         
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/confirmation')
        self.assertEqual(data['status_code'], '200')
        
        self.assertEqual(data['process'].split('<=>')[0], 'payment_invalid')
        self.assertEqual(data['process'].split('<=>')[1], 'Wrong amount.')
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(str(process_dict['TransAmount']), "Decimal('2000.00')")
        
         
    def test_if_MpesaPaymentView_can_log_a_confirmation_single_teams_with_reg_no(self):
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = 2000000000
        
        self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        content = get_log_content()
        
        self.assertEqual(len(content), 1)
        
        data = content[0]
                                       
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/confirmation')
        self.assertEqual(data['status_code'], '200')
        
        self.assertEqual(data['process'].split('<=>')[0], 'payment_invalid')
        self.assertEqual(data['process'].split('<=>')[1], 'Account No is not recognized.')
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(str(process_dict['TransAmount']), "Decimal('1425.00')")
    
       
    def test_if_MpesaPaymentView_can_log_a_confirmation_serializer_is_invalid(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        del c2b_data['TransAmount']
        
        self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
                       
        content = get_log_content()
        
        self.assertEqual(len(content), 1)
        
        data = content[0]
        
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/confirmation')
        self.assertEqual(data['status_code'], '400')
        
        self.assertEqual(data['process'].split('<=>')[0], 'payment_invalid')
        self.assertTrue("'TransAmount': [ErrorDetail" in data['process'].split('<=>')[1])
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(process_dict['BillRefNumber'], c2b_data['BillRefNumber'])
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's accept_payments is False#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=False
        ms.save()
        
        self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        content = get_log_content()
        
        self.assertEqual(len(content), 2)
        
        data = content[1]
        
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/confirmation')
        self.assertEqual(data['status_code'], '503')
        
        self.assertEqual(data['process'].split('<=>')[0], 'payment_not_allowed')
        self.assertEqual(data['process'].split('<=>')[1], 'payment_denied')
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(process_dict['BillRefNumber'], c2b_data['BillRefNumber'])
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's maintenance is true#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=True
        ms.maintenance=True
        ms.save()
        
        self.client.post(reverse('billing:mpesa_confirmation'), c2b_data)
        
        content = get_log_content()
        
        self.assertEqual(len(content), 3)
        
        data = content[2]
                
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/confirmation')
        self.assertEqual(data['status_code'], '503')
        
        self.assertEqual(data['process'].split('<=>')[0], 'maintenance')
        self.assertEqual(data['process'].split('<=>')[1], 'payment_denied')
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(process_dict['BillRefNumber'], c2b_data['BillRefNumber'])
        
        
        
        ##########################################################################
        #                             Validation
        ##########################################################################
        
    def test_if_MpesaPaymentView_can_log_a_validation_single_teams(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        self.client.post(reverse('billing:mpesa_validation'), c2b_data)
                       
        content = get_log_content()
        
        self.assertEqual(len(content), 1)
        
        data = content[0]
        
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/validation')
        self.assertEqual(data['status_code'], '200')
        self.assertEqual(data['process'], 'OK')
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's accept_payments is False#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=False
        ms.save()
        
        self.client.post(reverse('billing:mpesa_validation'), c2b_data)
        
        content = get_log_content()
        
        self.assertEqual(len(content), 2)
        
        data = content[1]
        
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/validation')
        self.assertEqual(data['status_code'], '503')
        
        self.assertEqual(data['process'].split('<=>')[0], 'payment_not_allowed')
        self.assertEqual(data['process'].split('<=>')[1], 'payment_denied')
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(str(process_dict['TransAmount']), '1425')
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's maintenance is true#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=True
        ms.maintenance=True
        ms.save()
        
        self.client.post(reverse('billing:mpesa_validation'), c2b_data)
        
        content = get_log_content()
        
        self.assertEqual(len(content), 3)
        
        data = content[2]
                
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/validation')
        self.assertEqual(data['status_code'], '503')
        
        self.assertEqual(data['process'].split('<=>')[0], 'maintenance')
        self.assertEqual(data['process'].split('<=>')[1], 'payment_denied')
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(str(process_dict['TransAmount']), '1425')
       
    def test_if_MpesaPaymentView_can_log_a_validation_single_teams_with_wrong_amount(self):
        
        c2b_data = c2b_return_data()
        
        c2b_data['TransAmount'] = 2000 # Wrong amount
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        self.client.post(reverse('billing:mpesa_validation'), c2b_data)
        
        content = get_log_content()
        
        self.assertEqual(len(content), 1)
        
        data = content[0]
         
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/validation')
        self.assertEqual(data['status_code'], '200')
        
        self.assertEqual(data['process'].split('<=>')[0], 'payment_invalid')
        self.assertEqual(data['process'].split('<=>')[1], 'Wrong amount.')
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(str(process_dict['TransAmount']), "Decimal('2000.00')")
        
    def test_if_MpesaPaymentView_can_log_a_validation_single_teams_with_reg_no(self):
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = 2000000000
        
        self.client.post(reverse('billing:mpesa_validation'), c2b_data)
        
        content = get_log_content()
        
        self.assertEqual(len(content), 1)
        
        data = content[0]
                                       
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/validation')
        self.assertEqual(data['status_code'], '200')
        
        self.assertEqual(data['process'].split('<=>')[0], 'payment_invalid')
        self.assertEqual(data['process'].split('<=>')[1], 'Account No is not recognized.')
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(str(process_dict['TransAmount']), "Decimal('1425.00')")
        
    def test_if_MpesaPaymentView_can_log_a_validation_serializer_is_invalid(self):
        
        duration = 1
        c2b_data = c2b_return_data()
        
        one_month_price = PriceGeneratorClass.account_price_calc(duration)
        
        c2b_data['TransAmount'] = one_month_price
        c2b_data['BillRefNumber'] = self.cashier_profile1.reg_no
        
        del c2b_data['TransAmount']
        
        self.client.post(reverse('billing:mpesa_validation'), c2b_data)
                       
        content = get_log_content()
        
        self.assertEqual(len(content), 1)
        
        data = content[0]
        
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/validation')
        self.assertEqual(data['status_code'], '400')
        
        self.assertEqual(data['process'].split('<=>')[0], 'payment_invalid')
        self.assertTrue("'TransAmount': [ErrorDetail" in data['process'].split('<=>')[1])
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(process_dict['BillRefNumber'], c2b_data['BillRefNumber'])
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's accept_payments is False#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=False
        ms.save()
        
        self.client.post(reverse('billing:mpesa_validation'), c2b_data)
        
        content = get_log_content()
        
        self.assertEqual(len(content), 2)
        
        data = content[1]
        
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/validation')
        self.assertEqual(data['status_code'], '503')
        
        self.assertEqual(data['process'].split('<=>')[0], 'payment_not_allowed')
        self.assertEqual(data['process'].split('<=>')[1], 'payment_denied')
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(process_dict['BillRefNumber'], c2b_data['BillRefNumber'])
        
        
        # ******************************************************************* # 
        # Make sure new payments wont be allowed if MySetting's maintenance is true#                  
        # ******************************************************************* #
        
        # Turn accept payments mode 
        ms = MySetting.objects.get(name='main')
        ms.accept_payments=True
        ms.maintenance=True
        ms.save()
        
        self.client.post(reverse('billing:mpesa_validation'), c2b_data)
        
        content = get_log_content()
        
        self.assertEqual(len(content), 3)
        
        data = content[2]
                
        self.assertEqual(data['method'], 'POST')
        self.assertEqual(data['full_path'], '/mpesa/validation')
        self.assertEqual(data['status_code'], '503')
        
        self.assertEqual(data['process'].split('<=>')[0], 'maintenance')
        self.assertEqual(data['process'].split('<=>')[1], 'payment_denied')
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['TransID'], c2b_data['TransID'])
        self.assertEqual(process_dict['BillRefNumber'], c2b_data['BillRefNumber'])

