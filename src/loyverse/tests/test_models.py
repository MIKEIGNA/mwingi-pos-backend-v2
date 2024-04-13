import datetime

from django.utils import timezone


from core.test_utils.create_user import create_new_user
from core.test_utils.custom_testcase import TestCase
from core.test_utils.date_utils import DateUtils

from loyverse.models import LoyverseAppData

class LoyverseAppDataTestCase(TestCase):

    def setUp(self):
        
        #Create a user with email john@gmail.com
        self.user = create_new_user('john') 

        self.store1_email = 'dorobo@gmail.com'
        self.store2_email = 'shompole@gmail.com'

    def test_verbose_names(self):
        
        data = LoyverseAppData.objects.get()

        self.assertEqual(data._meta.get_field('name').verbose_name,'name')
        self.assertEqual(
            data._meta.get_field('access_token').verbose_name,'access token')
        self.assertEqual(
            data._meta.get_field('refresh_token').verbose_name,'refresh token')
        self.assertEqual(
            data._meta.get_field('access_token_expires_in').verbose_name,
            'access token expires in'
        )
        self.assertEqual(
            data._meta.get_field('updated_date').verbose_name,'updated date')
        self.assertEqual(
            data._meta.get_field('receipt_day_minus_today').verbose_name,'receipt day minus today')
                
        fields = ([field.name for field in LoyverseAppData._meta.fields])
        
        self.assertEqual(len(fields), 7)

    def test_model_fields_after_it_has_been_created(self):
        
        data = LoyverseAppData.objects.get()
        
        today = (timezone.now()).strftime("%B, %d, %Y")

        self.assertEqual(str(data), 'main')

        self.assertEqual(data.name, 'main')
        self.assertEqual(str(data.access_token), 'a827c4447e9d47a3c98')
        self.assertEqual(str(data.refresh_token), 'b827c4447e9d47a3c98')
        self.assertEqual(data.access_token_expires_in, 0)
        self.assertEqual((data.updated_date).strftime("%B, %d, %Y"), today)
        self.assertEqual(data.receipt_day_minus_today, 11)

    def test_get_updated_date_method(self):

        data = LoyverseAppData.objects.get()

        # Check if get_created_date is correct
        self.assertTrue(DateUtils.do_created_dates_compare(
            data.get_updated_date())
        )

    def test_updated_date_is_always_updated_when_save_is_called(self):
        
        # Change date to yesterday
        yesterday = timezone.now() + datetime.timedelta(days=-1)

        LoyverseAppData.objects.update(updated_date = yesterday)

        data = LoyverseAppData.objects.get()
        self.assertEqual(
            (data.updated_date).strftime("%B, %d, %Y"), 
            yesterday.strftime("%B, %d, %Y")
        )

    def test_receipt_anlayze_iso_date_method(self):

        receipt_day_minus_today = 11

        back_date = timezone.now() + datetime.timedelta(days=-(receipt_day_minus_today))
        
        data = LoyverseAppData.objects.get()

        self.assertEqual(
            data.receipt_anlayze_iso_date(), 
            (back_date).strftime("%Y-%m-%dT00:00:00.000Z")
        )

    def test_receipt_anlayze_date_method(self):

        receipt_day_minus_today = 11

        back_date = timezone.now() + datetime.timedelta(days=-(receipt_day_minus_today))
        
        data = LoyverseAppData.objects.get()

        self.assertEqual(
            data.receipt_anlayze_date(), 
            back_date.strftime("%B, %d, %Y")
        )
