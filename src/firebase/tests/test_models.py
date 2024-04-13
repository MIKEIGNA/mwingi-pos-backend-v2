import datetime

from django.utils import timezone
from core.test_utils.create_store_models import create_new_store

from firebase.models import FirebaseDevice

from core.test_utils.custom_testcase import TestCase
from core.test_utils.create_user import create_new_user
from profiles.models import Profile


"""
=========================== FirebaseDevice ===================================
"""  
# FirebaseDevice Verbose Names
class FirebaseDeviceTestCase(TestCase):
            
    def setUp(self):
        
        #Create a top user1
        self.user = create_new_user('john')

        self.profile = Profile.objects.get(user__email='john@gmail.com')
        
        #Create a store
        self.store = create_new_store(self.profile, 'Computer Store')

        self.token = 'cjSXLZvFSi6uzFLVPxFkfM:APA91bG3c4LagkGXl31iKi9uJB8Bfguf6uoX3VQ6n_69OgJIjTT_WvPMjqzd2bnU_uKAcBXkbxb_DJVETuVXTH2KYvy8uAPHZ7jLh3XBH0JhimtaRj-AvejuJw7HcunkUCIX0Rdy6_ZC'

        FirebaseDevice.objects.create(
            user = self.user,
            store=self.store,
            token=self.token,
            last_login_date = timezone.now()
        )
       
    def test_model_fields_verbose_names(self):
      
        firebase = FirebaseDevice.objects.get(token=self.token)
        
        self.assertEqual(firebase._meta.get_field('token').verbose_name,'token')
        self.assertEqual(firebase._meta.get_field('last_login_date').verbose_name,'last login date')
        self.assertEqual(firebase._meta.get_field('is_current_active').verbose_name,'is current active')
        self.assertEqual(firebase._meta.get_field('created_date').verbose_name,'created date')
        
        fields = ([field.name for field in FirebaseDevice._meta.fields])
        
        self.assertEqual(len(fields), 7)

    def test_model_existence(self):
        
        firebase = FirebaseDevice.objects.get(token=self.token)

        self.assertEqual(firebase.user, self.user)

    def test__str__method_when_token_length_is_correct(self):

        firebase = FirebaseDevice.objects.get(token=self.token)

        self.assertEqual(firebase.__str__(), 'cjSXLZvFSi....IX0Rdy6_ZC')

    def test__str__method_when_token_length_is_less_than_150(self):

        new_token = 't'*149

        firebase = FirebaseDevice.objects.get(token=self.token)
        firebase.token=new_token
        firebase.save()

        firebase = FirebaseDevice.objects.get(token=new_token)

        self.assertEqual(firebase.__str__(),'Short token')

    def test__str__method_when_token_length_is_empty(self):

        firebase = FirebaseDevice.objects.get(token=self.token)
        firebase.token=''
        firebase.save()

        firebase = FirebaseDevice.objects.get(user=self.user)

        self.assertEqual(firebase.__str__(),'Empty token')

    def test_get_last_login_date_method(self):
        # Confirm that get_last_login_date_method returns created_date
        # in local time 
        
        firebase = FirebaseDevice.objects.get(token=self.token)
             
        now =  timezone.now() + datetime.timedelta(hours=3)
        local_date = (now).strftime("%B, %d, %Y, %I:%M:%p")
        
        self.assertEqual(
            firebase.get_last_login_date(self.user.get_user_timezone()), local_date)

    def test_get_created_date_method(self):
        # Confirm that get_created_date_method returns created_date
        # in local time 
        
        firebase = FirebaseDevice.objects.get(token=self.token)
             
        now =  timezone.now() + datetime.timedelta(hours=3)
        local_date = (now).strftime("%B, %d, %Y, %I:%M:%p")
        
        self.assertEqual(
            firebase.get_created_date(self.user.get_user_timezone()), local_date)

