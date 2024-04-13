from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model

from billing.models import Payment
from profiles.models import Profile, EmployeeProfile

from mylogentries.models import PaymentLog, MpesaLog

from accounts.utils.user_type import (
    ADMIN_USER,
    EMPLOYEE_USER, 
    TOP_USER, 
)

User = get_user_model()

def get_price(account_type, account_num):
    """
    Returns a dict with 1 month, 6 months and 12 months prices
    
    Parameters:
        account_type --> A string that holds the name of the type of account
        account_num --> An int variable that holds the number of accounts
    
    Return:
        {'2850': 1, '13500': 6, '21600': 12}
    """
    
    
    num_of_months = [1, 6, 12]
    
    num_of_months_prices = {}
    
    for num_of_month in num_of_months:
        price = (settings.SUBSCRIPTION_PRICES[account_type] * num_of_month) * account_num
        discount_name = '{}_months'.format(num_of_month)
        discount = settings.SUBSCRIPTION_PRICE_DISCOUNTS[discount_name]
        
        # Formula used to calculate discount : 25/100 * 1500
        discount_amount = (discount / 100) * price
        final_price = price - discount_amount
        
        num_of_months_prices[str(int(final_price))] = num_of_month
        
    return num_of_months_prices


class AcceptPayment():
    def __init__(self, **complete_payment_info):
        """
        Receives, processes and accepts both Mpesa and manual payments for a single or 
        multiple accounts. 
        
        If the recieved payment information has any wrong value, the payment is
        rejected
        
        Parameters:
            complete_payment_info --> A dict with the required payment information 
            
            Example of an Mpesa Payment 
            ___________________________
            
            {'payment_method': 'mpesa', '
            request_type': 'confirmation', 
            'payment_info': OrderedDict([('TransactionType', ''), 
                                         ('TransID', 'LGR219G3EY'), 
                                         ('TransTime', 20190425125829), 
                                         ('TransAmount', Decimal('1425.00')), 
                                         ('BusinessShortCode', 600134), 
                                         ('BillRefNumber', 41188490695),
                                         ('InvoiceNumber', ''), 
                                         ('OrgAccountBalance', ''), 
                                         ('ThirdPartyTransID', ''), 
                                         ('MSISDN', 254708374149), 
                                         ('FirstName', 'John'), 
                                         ('MiddleName', 'J'), 
                                         ('LastName', 'Doe')])}
    
        Example of an manual payment 
        ____________________________
        
        {'payment_method': 'manual_payment', 
        'request_type': 'confirmation', 
        'payment_info': {'reg_no': 41188490695, 
                         'amount': 1425}}


            
        """

        self.REG_NO_ERROR_MSG = "Account No is not recognized."
        self.AMOUNT_ERROR_MSG = "Wrong amount."

        self.complete_payment_info =  complete_payment_info
        
        self.payment_method = self.complete_payment_info["payment_method"]
        self.request_type = self.complete_payment_info["request_type"]
        self.payment_info = self.complete_payment_info["payment_info"]
        
        
        """
        clean_payment_info() is called to clean payment info. If it succeds, 
        payment_info_cleaned is changed to True but remains false otherwise
        """
        self.payment_info_cleaned = False
        self.cleaned_payment_info = self.clean_payment_info(self.payment_info)
    
        self.payment_confirmed = False
        
        if self.request_type == "confirmation":
            self.payment_confirmed = True
            
        else:
            self.payment_confirmed = False
            
            
        self.mpesa_trans_id = ""
        self.payment_log= False
        
        if self.payment_method == "mpesa" and self.payment_info_cleaned:
            
            self.mpesa_trans_id = self.cleaned_payment_info["TransID"]
            self.amount = self.cleaned_payment_info["TransAmount"]
            self.reg_no = self.cleaned_payment_info["BillRefNumber"]
            
        elif self.payment_method == "manual_payment" and self.payment_info_cleaned:
            
            self.amount = self.cleaned_payment_info["amount"]
            self.reg_no = self.cleaned_payment_info["reg_no"]
        else:
            self.payment_info_cleaned = False
            
        self.error_msg = False
            
    def accept_payments(self):
        """
        Processes the payment and accepts the payment of rejects it if it is
        wrong or it has wrong values
        
        Parameters:
            none 
            
        Returns a boolean:
            If successful, returns a Tuple whth True, an error message if there were any
            eg (True, error_msg) True means the payment was successful
            
            
            If it fails, returns a Tuple whth False, and an error message
            eg (False, error_msg) False means the payment was not successful
        """

        if not self.payment_info_cleaned:
            return False, self.error_msg
    
        payment_accepted = self.process_payments()

        
        
        if payment_accepted:
            
            if self.payment_confirmed and self.payment_method == "mpesa":
                if self.payment_log:
                    self.create_MpesaLog()
        
        
        return payment_accepted, self.error_msg
    
    
    def process_payments(self):
        """
        Processes the payment and accepts the payment of rejects it if it is
        wrong or it has wrong values
        
        Parameters:
            none 
            
        Returns a boolean:
            If successful, returns True 
            If it fails, returns False
        """
      

        try:
            user = User.objects.get(reg_no=self.reg_no)
            user_type = user.user_type


            
            """ To prevent problems caused by unpredictable, number of decimal places, 
                we turn self.amount to an int
            """
            self.amount = int(self.amount)

            if user_type == ADMIN_USER or user_type == TOP_USER:
                payment_type = 'multiple'

            elif user_type == EMPLOYEE_USER:
                payment_type = 'single'
            else:
                payment_type = False


            model = EmployeeProfile
            account_type = 'account'


            if payment_type == 'multiple':
                accepted_multiple_payments = self.accept_multiple_payments(model, user, account_type)
                
                return accepted_multiple_payments
            
            elif payment_type == 'single':
                accepted_single_payment = self.accept_single_payment(model, account_type)
                
                return accepted_single_payment
                
            else:
                self.error_msg = self.REG_NO_ERROR_MSG
                    
        except:
            self.error_msg = self.REG_NO_ERROR_MSG
            
        return False
        
        
        
    def create_MpesaLog(self):
        """ Create a MpesaLog """
        if True:
            
            mpesa_log = MpesaLog.objects.create(paymentlog= self.payment_log,
                                transaction_type= self.cleaned_payment_info["TransactionType"],
                                trans_id = self.cleaned_payment_info["TransID"],
                                trans_time = self.cleaned_payment_info["TransTime"],
                                trans_amount = self.cleaned_payment_info["TransAmount"],
                                business_shortcode = self.cleaned_payment_info["BusinessShortCode"],
                                bill_ref_number = self.cleaned_payment_info["BillRefNumber"],
                                invoice_number = self.cleaned_payment_info["InvoiceNumber"],
                                org_account_balance = self.cleaned_payment_info["OrgAccountBalance"],
                                third_party_trans_id = self.cleaned_payment_info["ThirdPartyTransID"],
                                msisdn = self.cleaned_payment_info["MSISDN"],
                                first_name = self.cleaned_payment_info["FirstName"],
                                middle_name = self.cleaned_payment_info["MiddleName"],
                                last_name = self.cleaned_payment_info["LastName"],
                                )
            
            
            self.payment_log.mpesa_id = mpesa_log.id
            self.payment_log.save()
            
            
        else:
            pass
    
    
    def clean_payment_info(self, payment_info):
        
        """
        Verifies and Cleans the payment information by checking if it's correct
        
        If the provided payment info is correct, it changes "self.payment_info_cleaned"
        to True and returns a clean payment_info
        
        If the payment info provided is wrong, "self.payment_info_cleaned" is changed to 
        False and returns an uncleaned payment_info
        
        
        Parameters:
            payment_info --> A dictionary with the recieved payment informaton 
            
        Returns a boolean:
            If successful, returns a dict with clean and verified payment info 
            If it fails, returns a dict with the uncleand and unverified payment info
        """
           
        
        try:
            
            """ Identify the payment method"""
            if self.payment_method == "mpesa":
                
                
                payment_info['TransTime'] = int(payment_info['TransTime'])
                payment_info['TransAmount'] = Decimal(payment_info['TransAmount'])
                payment_info['BusinessShortCode'] = int(payment_info['BusinessShortCode'])
                payment_info['BillRefNumber'] = int(payment_info['BillRefNumber'])
                payment_info['MSISDN'] = int(payment_info['MSISDN'])
                
                """ If it's an Mpesa make sure it's unique """
                mpesalog_exists = MpesaLog.objects.filter(trans_id = payment_info['TransID']).exists()
                
                if not mpesalog_exists:
                    self.payment_info_cleaned = True
                else:
                    self.payment_info_cleaned = False
                
            elif self.payment_method == "manual_payment":
                """ Nothing to be cleaned """
                
                self.payment_info_cleaned = True
            
            else:
                self.payment_info_cleaned = False
                
                
            return payment_info
                
        except:
            
            self.payment_info_cleaned = False
            return payment_info
        
    
    def accept_single_payment(self, model, account_type):
        """
        Accepts the payment of a single account if the amount is correct or rejects it if it's 
        wrong.
        
        If payment is accepted, Payment, PaymentLog and MpesaLog models are created.
        However, if the request_type is not confirmation, it returns True
        but does not make any Payment, PaymentLog and MpesaLogs models
        
        Parameters:
            model --> The model of the account that it's being payed for
            profile --> The user's profile that's making the payment
            account_type --> A string that holds the name of the type of account
            
            
        Returns a boolean:
            If successful, returns true
            If it fails, returns false
            
        """
        
        
        account = model.objects.get(reg_no = self.reg_no)

        
        amount_for_account, amount_duration = self.confirm_single_price(account_type, self.amount)
        
        if amount_for_account and amount_duration:
            
            if not self.payment_confirmed:
                """ 
                If it's not a confirmed request, return True without accepting any payment
                
                Even though this does not accept the payment, it validates and shows that
                the amount and reg_no used were correct
                """
            
                return True
            
        
            top_profile_email=account.profile.user.email
            
            
            self.payment_log = PaymentLog.objects.create(amount=self.amount,
                                                    payment_method = self.payment_method,
                                                    payment_type='single {}'.format(account_type),
                                                    email=top_profile_email,
                                                    reg_no=self.reg_no,
                                                    duration=amount_duration,
                                                    )
            
            Payment.objects.create(paymentlog= self.payment_log,
                                   amount=amount_for_account,
                                   account_reg_no = account.reg_no,
                                   duration = amount_duration,
                                   parent_reg_no = 0,
                                   account_type = account_type,
                                   )
            
            
            return True
        else:
            return False
        
    def confirm_single_price(self, account_type, amount):
        """
        Confirms if the amount is correct and should be accepted or if it's 
        wrong and should be rejected
        
        Parameters:
            account_type --> A string that holds the name of the type of account
            amount --> An int that holds the amount to be paid
            
        Returns a tuple:
            If successful, returns a tuple with (amount_for_each_account, amount_duration)
            If it fails, returns a tuple with False and False. Eg (False, False)
            
        """
        
        prices = get_price(account_type, 1)
        amount_str = str(amount)
        
        
        if amount_str in prices:        
            amount_duration = prices[amount_str]
            amount_for_account = amount
            
            
            return amount_for_account, amount_duration
        
        else:
            
            self.error_msg = self.AMOUNT_ERROR_MSG
            
            return False, False
        

    def accept_multiple_payments(self, model, user, account_type):
        """
        Accepts the payment of multiple accounts if the amount is correct or rejects it if it's 
        wrong.
        
        If payment is accepted, Payment, PaymentLog and MpesaLog models are created.
        However, if the request_type is not confirmation, it returns True
        but does not make any Payment, PaymentLog and MpesaLogs models
        
        Parameters:
            model --> The model of the account that it's being payed for
            user --> The user making the payment
            account_type --> A string that holds the name of the type of account
            
            
        Returns a boolean:
            If successful, returns true
            If it fails, returns false
            
        """

        

        user_email = user.email

        # Check if we have the correct user type
        if user.user_type == TOP_USER:
            accounts = model.objects.filter(profile__user__email=user_email)
        else:
            return False

        
        num_of_accounts = accounts.count()
        
        #if not num_of_accounts:
        #    return False;
            
        amount_for_each_account, amount_duration = self.confirm_multiple_price(account_type, num_of_accounts, self.amount)

        if amount_for_each_account and amount_duration:
            
            if not self.payment_confirmed:
                """ 
                If it's not a confirmed request, return True without accepting any payment
                
                Even though this does not accept the payment, it validates and shows that
                the amount and reg_no used were correct
                """
                return True
            
            
            self.payment_log = PaymentLog.objects.create(amount=self.amount,
                                                    payment_method = self.payment_method,
                                                    payment_type='multiple {}s ({})'.format(account_type, num_of_accounts),
                                                    email=user_email,
                                                    reg_no=self.reg_no,
                                                    duration=amount_duration
                                                    )
            
            for account in accounts:
                Payment.objects.create(paymentlog= self.payment_log,
                                       amount=amount_for_each_account,
                                       account_reg_no = account.reg_no,
                                       duration = amount_duration,
                                       parent_reg_no = self.reg_no,
                                       account_type = account_type,
                                       )
            

            return True
        else:
            return False
        
    def confirm_multiple_price(self, account_type, num_of_accounts, amount):
        """
        Confirms if the amount is correct and should be accepted or if it's 
        wrong and should be rejected
        
        Parameters:
            account_type --> A string that holds the name of the type of account
            num_of_accounts --> An int that holds the number of accounts
            amount --> An int that holds the amount to be paid
            
        Returns a tuple:
            If successful, returns a tuple with (amount_for_each_account, amount_duration)
            If it fails, returns a tuple with False and False. Eg (False, False)
            
        """
                
        prices = get_price(account_type, num_of_accounts)
        amount_str = str(amount)


        if amount_str in prices:        
            amount_duration = prices[amount_str]
            amount_for_each_account = int(amount/num_of_accounts)
                        
            return amount_for_each_account, amount_duration
        
        else:
            
            self.error_msg = self.AMOUNT_ERROR_MSG
            
            return False, False
        
    
