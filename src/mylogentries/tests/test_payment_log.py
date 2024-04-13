from django.contrib.auth import get_user_model
from django.db import transaction

from profiles.models import Profile, EmployeeProfile

from mylogentries.models import PaymentLog, MpesaLog


from core.test_utils.custom_testcase import TestCase
from core.test_utils.create_store_models import create_new_store
from core.test_utils.create_user import create_new_user
from core.test_utils.create_user import (
    create_new_user,
    create_new_cashier_user
)

User = get_user_model()


class PaymentLogVerboseNamesAndFieldsTestCase(TestCase):

    def setUp(self):

        # Create users
        self.user1 = create_new_user('john')
        self.top_profile1 = Profile.objects.get(user__email='john@gmail.com')

        self.store = create_new_store(self.top_profile1, 'Computer Store')
        
        #Create a employee user1
        create_new_cashier_user("kate", self.top_profile1, self.store)
        self.cashier_profile1 = EmployeeProfile.objects.get(user__email='kate@gmail.com')
        

    
    def test_PaymentLog_existence_and_fields_verbose_names(self):
        """
        Ensure PaymentLog exists and all fields have the correct verbose names and can be
        found
        """

        PaymentLog.objects.create(amount=12000,
                                  payment_method = 'mpesa',
                                  mpesa_id = 1,
                                  payment_type='multiple {}s ({})'.format('team', 2),
                                  email=self.top_profile1.user.email,
                                  reg_no=self.cashier_profile1.reg_no,
                                  duration=12,
                                  )
        
        p = PaymentLog.objects.get(reg_no=self.cashier_profile1.reg_no)

        self.assertEqual(p._meta.get_field('amount').verbose_name,'amount')
        self.assertEqual(p._meta.get_field('payment_method').verbose_name,'payment method')
        self.assertEqual(p._meta.get_field('mpesa_id').verbose_name,'mpesa id')
        self.assertEqual(p._meta.get_field('payment_type').verbose_name,'payment type')
        self.assertEqual(p._meta.get_field('email').verbose_name,'email')
        self.assertEqual(p._meta.get_field('reg_no').verbose_name,'reg no')
        self.assertEqual(p._meta.get_field('duration').verbose_name,'duration')
        self.assertEqual(p._meta.get_field('created_date').verbose_name,'created date')
        
        fields = ([field.name for field in PaymentLog._meta.fields])
        
        self.assertEqual(len(fields), 9)
        
        """
        PaymentLog fields
        
        Ensure a PaymentLog has the right fields after it has been created
        """
        self.assertEqual(p.amount, 12000)
        self.assertEqual(p.payment_method, 'mpesa')
        self.assertEqual(p.mpesa_id, 1)
        self.assertEqual(p.payment_type, 'multiple teams (2)')
        self.assertEqual(p.email, self.top_profile1.user.email)
        self.assertEqual(p.reg_no, self.cashier_profile1.reg_no)
        self.assertEqual(p.duration, 12)
        self.assertEqual(p.amount, 12000)
        

class MpesaLogVerboseNamesAndFieldsTestCase(TestCase):
    def setUp(self):

        # Create users
        self.user1 = create_new_user('john')
        self.top_profile1 = Profile.objects.get(user__email='john@gmail.com')
        
        self.store = create_new_store(self.top_profile1, 'Computer Store')
        
        #Create a employee user1
        create_new_cashier_user("kate", self.top_profile1, self.store)
        self.cashier_profile1 = EmployeeProfile.objects.get(user__email='kate@gmail.com')
        
        
        self.payment_log = PaymentLog.objects.create(amount=12000,
                                  payment_method = 'mpesa',
                                  mpesa_id = 1,
                                  payment_type='multiple {}s ({})'.format('team', 2),
                                  email=self.top_profile1.user.email,
                                  reg_no=self.cashier_profile1.reg_no,
                                  duration=12,
                                  )
    
    def test_MpesaLog_existence_and_fields_verbose_names(self):
        """
        Ensure MpesaLog exists and all fields have the correct verbose names and can be
        found
        """

        MpesaLog.objects.create(paymentlog=self.payment_log,
                                transaction_type="",
                                trans_id = "LGR219G3EY",
                                trans_time = 20170727104247,
                                trans_amount = 1425.00,
                                business_shortcode = 600134,
                                bill_ref_number = self.cashier_profile1.reg_no,
                                invoice_number = 49197.00,
                                org_account_balance = 49197.00,
                                third_party_trans_id='1234567890',
                                msisdn = 254708374149,
                                first_name = "Dolla",
                                middle_name = "Bucks",
                                last_name = "Gucci",
                                )
        
        ml = MpesaLog.objects.get(trans_id = "LGR219G3EY")
        
        self.assertEqual(ml._meta.get_field('transaction_type').verbose_name,'transaction type')
        self.assertEqual(ml._meta.get_field('trans_id').verbose_name,'trans id')
        self.assertEqual(ml._meta.get_field('trans_time').verbose_name,'trans time')
        self.assertEqual(ml._meta.get_field('trans_amount').verbose_name,'trans amount')
        self.assertEqual(ml._meta.get_field('business_shortcode').verbose_name,'business shortcode')
        self.assertEqual(ml._meta.get_field('bill_ref_number').verbose_name,'bill ref number')
        self.assertEqual(ml._meta.get_field('invoice_number').verbose_name,'invoice number')
        self.assertEqual(ml._meta.get_field('org_account_balance').verbose_name,'org account balance')
        self.assertEqual(ml._meta.get_field('third_party_trans_id').verbose_name,'third party trans id')
        self.assertEqual(ml._meta.get_field('msisdn').verbose_name,'msisdn')
        self.assertEqual(ml._meta.get_field('first_name').verbose_name,'first name')
        self.assertEqual(ml._meta.get_field('middle_name').verbose_name,'middle name')
        self.assertEqual(ml._meta.get_field('last_name').verbose_name,'last name')
        
        fields = ([field.name for field in MpesaLog._meta.fields])
        
        self.assertEqual(len(fields), 16)
        
        """
        MpesaLog fields
        
        Ensure a MpesaLog has the right fields after it has been created
        """
        self.assertEqual(ml.paymentlog, self.payment_log)
        self.assertEqual(ml.transaction_type, "")
        self.assertEqual(ml.trans_id,  "LGR219G3EY")
        self.assertEqual(ml.trans_time,  20170727104247)
        self.assertEqual(ml.trans_amount, 1425.00)
        self.assertEqual(ml.business_shortcode, 600134)
        self.assertEqual(ml.bill_ref_number, self.cashier_profile1.reg_no)
        self.assertEqual(ml.invoice_number, 49197.00)
        self.assertEqual(ml.org_account_balance, 49197.00)
        self.assertEqual(ml.third_party_trans_id, '1234567890')
        self.assertEqual(ml.msisdn, 254708374149)
        self.assertEqual(ml.first_name, "Dolla")
        self.assertEqual(ml.middle_name, "Bucks")
        self.assertEqual(ml.last_name, "Gucci")
        
        """
        MpesaLog methods
        """
        
        self.assertEqual(ml.get_admin_url(), f'/magnupe/mylogentries/paymentlog/{self.payment_log.pk}/change/')
        self.assertEqual(
            ml.show_paymentlog_id_link(), 
            f'<a href="http://127.0.0.1:8000/magnupe/mylogentries/paymentlog/{self.payment_log.pk}/change/">mpesa</a>')
           
    def test_MpesaLog_trans_id_can_only_be_unique(self):
        """
        Ensure MpessaLog is unique
        """
        MpesaLog.objects.create(paymentlog=self.payment_log,
                                transaction_type="",
                                trans_id = "LGR219G3EY",
                                trans_time = 20170727104247,
                                trans_amount = 1425.00,
                                business_shortcode = 600134,
                                bill_ref_number = self.cashier_profile1.reg_no,
                                invoice_number = 49197.00,
                                org_account_balance = 49197.00,
                                third_party_trans_id='1234567890',
                                msisdn = 254708374149,
                                first_name = "Dolla",
                                middle_name = "Bucks",
                                last_name = "Gucci",
                                )
        
        ml_count = MpesaLog.objects.all().count()
        
        self.assertEqual(ml_count,1)
        
        """
        Try to create a duplicate
        """
       
        try:
            
            # Duplicates should be prevented.
            with transaction.atomic():
                MpesaLog.objects.create(paymentlog=self.payment_log,
                                transaction_type="",
                                trans_id = "LGR219G3EY",
                                trans_time = 20170727104247,
                                trans_amount = 1425.00,
                                business_shortcode = 600134,
                                bill_ref_number = self.cashier_profile1.reg_no,
                                invoice_number = 49197.00,
                                org_account_balance = 49197.00,
                                third_party_trans_id='1234567890',
                                msisdn = 254708374149,
                                first_name = "Dolla",
                                middle_name = "Bucks",
                                last_name = "Gucci",
                                )
            
            failed = False
            
        except:
            
            failed = True
            
          
        self.assertEqual(failed, True) # Check if duplicate creation failded
        self.assertEqual(MpesaLog.objects.all().count(), 1)
         
    def test_MpesaLog_cant_be_created_without_a_trans_amount(self):
        
        try:
            # Duplicates should be prevented.
            with transaction.atomic():
                MpesaLog.objects.create(paymentlog=self.payment_log,
                                transaction_type="",
                                trans_id = "LGR219G3EY",
                                trans_time = 20170727104247,
                                business_shortcode = 600134,
                                bill_ref_number = self.cashier_profile1.reg_no,
                                invoice_number = 49197.00,
                                org_account_balance = 49197.00,
                                third_party_trans_id='1234567890',
                                msisdn = 254708374149,
                                first_name = "Dolla",
                                middle_name = "Bucks",
                                last_name = "Gucci",
                                )
            
            failed = False
            
        except:
            
            failed = True
            
        self.assertEqual(failed, True) # Check if duplicate creation failded
        self.assertEqual(MpesaLog.objects.all().count(), 0)
         
    def test_MpesaLog_cant_be_created_without_a_business_shortcode(self):
        
        try:
            # Duplicates should be prevented.
            with transaction.atomic():
                MpesaLog.objects.create(paymentlog=self.payment_log,
                                transaction_type="",
                                trans_id = "LGR219G3EY",
                                trans_time = 20170727104247,
                                trans_amount = 1425.00,
                                bill_ref_number = self.cashier_profile1.reg_no,
                                invoice_number = 49197.00,
                                org_account_balance = 49197.00,
                                third_party_trans_id='1234567890',
                                msisdn = 254708374149,
                                first_name = "Dolla",
                                middle_name = "Bucks",
                                last_name = "Gucci",
                                )
            
            failed = False
            
        except:
            
            failed = True
            
        self.assertEqual(failed, True) # Check if duplicate creation failded
        self.assertEqual(MpesaLog.objects.all().count(), 0)

      
    def test_MpesaLog_cant_be_created_without_a_msisdn(self):
        
        try:
            # Duplicates should be prevented.
            with transaction.atomic():
                MpesaLog.objects.create(paymentlog=self.payment_log,
                                transaction_type="",
                                trans_id = "LGR219G3EY",
                                trans_time = 20170727104247,
                                trans_amount = 1425.00,
                                business_shortcode = 600134,
                                bill_ref_number = self.cashier_profile1.reg_no,
                                invoice_number = 49197.00,
                                org_account_balance = 49197.00,
                                third_party_trans_id='1234567890',
                                first_name = "Dolla",
                                middle_name = "Bucks",
                                last_name = "Gucci",
                                )
            
            failed = False
            
        except:
            
            failed = True
            
        self.assertEqual(failed, True) # Check if duplicate creation failded
        self.assertEqual(MpesaLog.objects.all().count(), 0)
        
