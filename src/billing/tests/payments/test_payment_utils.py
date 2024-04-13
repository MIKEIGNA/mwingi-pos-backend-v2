from django.conf import settings

from core.test_utils.custom_testcase import TestCase

from billing.utils.payment_utils.price_gen import PriceGeneratorClass


class PaymentPriceTestCase(TestCase):
 
    def test_tracker_price_list(self):
        
        prices = {'account': 1500}
        
        self.assertEqual(settings.SUBSCRIPTION_PRICES, prices)
        self.assertEqual(len(settings.SUBSCRIPTION_PRICES), 1)
       
    def test_tracker_discountst(self):

        discount = {
            '1_months': 5,
            '3_months': 10,
            '6_months': 25,
            '12_months':40
        }
        
        self.assertEqual(settings.SUBSCRIPTION_PRICE_DISCOUNTS, discount)
        self.assertEqual(len(settings.SUBSCRIPTION_PRICE_DISCOUNTS), 4)

class PaymentUtilsPriceGeneratorClassMethodsTestCase(TestCase):
    def setUp(self):
        pass

    def test_account_price_discount_calc_method(self):
        # Ensure price_discount_calc returns the correct prices and discounts for accounts
                
        self.assertEqual(PriceGeneratorClass.account_price_discount_calc(1), (1425, 5))
        self.assertEqual(PriceGeneratorClass.account_price_discount_calc(6), (6750, 25))
        self.assertEqual(PriceGeneratorClass.account_price_discount_calc(12), (10800, 40))

        # Test wrong duration
        self.assertEqual(PriceGeneratorClass.account_price_discount_calc(5), (0, 0))

        # Test non integer
        self.assertEqual(PriceGeneratorClass.account_price_discount_calc("p"), (0, 0))
    
    def test_account_price_calc_method(self):
        # Ensure price_discount_calc returns the correct prices for accounts
                
        self.assertEqual(PriceGeneratorClass.account_price_calc(1), 1425)
        self.assertEqual(PriceGeneratorClass.account_price_calc(6), 6750)
        self.assertEqual(PriceGeneratorClass.account_price_calc(12), 10800)

        # Test wrong duration
        self.assertEqual(PriceGeneratorClass.account_price_calc(5), 0)

        # Test non integer
        self.assertEqual(PriceGeneratorClass.account_price_calc("p"), 0)

    def test_all_accounts_price_discount_calc_method(self):
        # Ensure all_trackers_price_discount_calc returns the correct prices and discounts for accounts
                
        self.assertEqual(PriceGeneratorClass.all_accounts_price_discount_calc(1, 4), (5700, 5))
        self.assertEqual(PriceGeneratorClass.all_accounts_price_discount_calc(6, 4), (27000, 25))
        self.assertEqual(PriceGeneratorClass.all_accounts_price_discount_calc(12, 4), (43200, 40))

        # Test wrong duration and count
        self.assertEqual(PriceGeneratorClass.all_accounts_price_discount_calc(5, 5), (0, 0))

        # Test non integer
        self.assertEqual(PriceGeneratorClass.all_accounts_price_discount_calc("p", "p"), (0, 0))

    def test_all_accounts_price_calc_method(self):
        # Ensure all_trackers_price_discount_calc returns the correct prices for accounts
                
        self.assertEqual(PriceGeneratorClass.all_accounts_price_calc(1, 4), 5700)
        self.assertEqual(PriceGeneratorClass.all_accounts_price_calc(6, 4), 27000)
        self.assertEqual(PriceGeneratorClass.all_accounts_price_calc(12, 4), 43200)

        # Test wrong duration and count
        self.assertEqual(PriceGeneratorClass.all_accounts_price_calc(5, 5), 0)

        # Test non integer
        self.assertEqual(PriceGeneratorClass.all_accounts_price_calc("p", "p"), 0)

class ConfirmMpesaResponsesTestCase(TestCase):
    def setUp(self):
        pass
    
    def test_if_mpesa_validation_accepted_response_is_correct(self):
        
        self.assertEqual(len(settings.SAFCOM_VALIDATION_ACCEPTED), 2)
        self.assertEqual(settings.SAFCOM_VALIDATION_ACCEPTED["ResultCode"], 0)
        self.assertEqual(settings.SAFCOM_VALIDATION_ACCEPTED["ResultDesc"], "Accepted")
        
    def test_if_mpesa_validation_rejected_response_is_correct(self):
        
        self.assertEqual(len(settings.SAFCOM_VALIDATION_REJECTED), 2)
        self.assertEqual(settings.SAFCOM_VALIDATION_REJECTED["ResultCode"], 1)
        self.assertEqual(settings.SAFCOM_VALIDATION_REJECTED["ResultDesc"], "Rejected")
        
    def test_if_mpesa_confirmation_success_response_is_correct(self):
        
        self.assertEqual(len(settings.SAFCOM_CONFIRMATION_SUCCESS), 1)
        self.assertEqual(settings.SAFCOM_CONFIRMATION_SUCCESS["C2BPaymentConfirmationResult"], "Success")
        
    def test_if_mpesa_confirmation_failure_response_is_correct(self):
        
        self.assertEqual(len(settings.SAFCOM_CONFIRMATION_FAILURE), 1)
        self.assertEqual(settings.SAFCOM_CONFIRMATION_FAILURE["C2BPaymentConfirmationResult"], "Failure")

