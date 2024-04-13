from django.test import RequestFactory
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model
from accounts.utils.currency_choices import KSH

from core.test_utils.create_user import create_new_user
from core.test_utils.custom_testcase import TestCase
from core.test_utils.initial_user_data import InitialUserDataMixin

from mysettings.models import MySetting

from mylogentries.models import UserActivityLog, CREATED, DELETED, CHANGED


from profiles.models import Profile

User = get_user_model()


class UserActivityLogTestCase(TestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        
        #Create a user with email john@gmail.com
        self.user = create_new_user('john') 
        
        #Create a user with email jack@gmail.com
        create_new_user('jack')
        
        """ Turn off maintenance mode"""
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
        
        """
           My client
        """
        self.client = Client()
        
        # Create an instance of a GET request.
        self.request = self.factory.get('/')
        self.request.user = self.user

        payload = {
            "first_name": "Ben",
            "last_name": "Linus",
            "email": "linus@gmail.com",
            "phone": "254723223322",
            'business_name': "Skypac",
            "location": "Nairobi",
            "currency": KSH,
            "gender": 0,
            "password": "secretpass"
        }

        response = self.client.post(reverse('api:signup') , payload, format='json')
    
        self.user3 = User.objects.get(email='linus@gmail.com') 
        
        self.assertEqual(self.user3.first_name, 'Ben')
        self.assertEqual(self.user3.last_name, 'Linus')
        self.assertEqual(self.user3.email, 'linus@gmail.com')
        self.assertEqual(response.status_code, 201)

    def test_UserActivityLog_fields_and_verbose_names(self):
        """
        Ensure all fields in UserActivityLog have the correct verbose names and can be
        found
        """
        
        """ Verbose Names """
        log=UserActivityLog.objects.get(user__email='linus@gmail.com')
        
        self.assertEqual(log._meta.get_field('action_time').verbose_name,'action time')
        self.assertEqual(log._meta.get_field('change_message').verbose_name,'change message')
        self.assertEqual(log._meta.get_field('object_id').verbose_name,'object id')
        self.assertEqual(log._meta.get_field('object_repr').verbose_name,'object repr')
        self.assertEqual(log._meta.get_field('content_type').verbose_name,'content type')
        self.assertEqual(log._meta.get_field('user').verbose_name,'user')
        self.assertEqual(log._meta.get_field('ip').verbose_name,'ip')
        self.assertEqual(log._meta.get_field('action_type').verbose_name,'action type')
        self.assertEqual(log._meta.get_field('owner_email').verbose_name,'owner email')
        self.assertEqual(log._meta.get_field('panel').verbose_name,'panel')
        self.assertEqual(log._meta.get_field('is_hijacked').verbose_name,'is hijacked')
        
        self.assertEqual(str(log),'Accounts | User Created.')
        
        fields = ([field.name for field in UserActivityLog._meta.fields])
        
        self.assertEqual(len(fields), 12)
        
        """ Field Names """
        self.assertEqual(log.change_message, 'New User "linus@gmail.com" has been created by "linus@gmail.com"')
        self.assertEqual(log.object_id, str(self.user3.pk))
        self.assertEqual(log.object_repr, 'linus@gmail.com')
        self.assertEqual(log.content_type.model, 'user')
        self.assertEqual(log.user.email, 'linus@gmail.com')
        self.assertTrue(len(log.ip) > 7)
        self.assertEqual(log.action_type, CREATED)
        self.assertEqual(log.owner_email, '')
        self.assertEqual(log.panel, 'Api')
        self.assertEqual(log.is_hijacked, False)
        
        self.assertEqual(UserActivityLog.objects.all().count(), 1)
      
    def test_UserActivityLog_str_method(self):
        """
        Ensure str method is working correctly
        """
        
        log=UserActivityLog.objects.get(user__email='linus@gmail.com')
        
        """ Test is_creation()"""
        self.assertEqual(str(log),'Accounts | User Created.')
        
        """ Test is_change()"""
        log.action_type = CHANGED
        log.save()

        log=UserActivityLog.objects.get(user__email='linus@gmail.com')
        
        self.assertEqual(str(log),'Accounts | User Changed.')
        
        """ Test is_deletion()"""
        log.action_type = DELETED
        log.save()

        log=UserActivityLog.objects.get(user__email='linus@gmail.com')
        
        self.assertEqual(str(log),'Accounts | User Deleted.')
        
    def test_get_change_message_method(self):
        """
        Ensure get_change_message method is working correctly
        """
        log=UserActivityLog.objects.get(user__email='linus@gmail.com')
                
        self.assertEqual(log.get_change_message(), 'New User "linus@gmail.com" has been created by "linus@gmail.com"')
        
    def test_get_edited_object_method(self):
        """
        Ensure get_edited_object method is working correctly
        """
        log=UserActivityLog.objects.get(user__email='linus@gmail.com')
        
        self.assertEqual(str(log.get_edited_object()), 'linus@gmail.com')
        
    def test_get_admin_url_method(self):
        """
        Ensure get_admin_url method is working correctly
        """
        log=UserActivityLog.objects.get(user__email='linus@gmail.com')
        
        self.assertEqual(str(log.get_admin_url()), f'/magnupe/accounts/user/{self.user3.pk}/change/')
        
    def test_the_object_method(self):
        """
        Ensure the_object method is working correctly
        """
        log=UserActivityLog.objects.get(user__email='linus@gmail.com')
        
        self.assertEqual(
            log.the_object(), 
            f'<a href="http://127.0.0.1:8000/magnupe/accounts/user/{self.user3.pk}/change/">Accounts | User</a>')
        
        """ Test if action_type is DDELETED"""
        log.action_type = DELETED
        log.save()

        log=UserActivityLog.objects.get(user__email='linus@gmail.com')

        self.assertEqual(log.the_object(), 'Accounts | User')
        
    def test_editor_profile_method(self):
        """
        Ensure editor_profile method is working correctly
        """
        log=UserActivityLog.objects.get(user__email='linus@gmail.com')
        
        self.assertEqual(
            log.editor_profile(), 
            f'<a href="http://127.0.0.1:8000/magnupe/profiles/profile/{self.user3.profile.pk}/change/">linus@gmail.com</a>')
        
    def test_find_owner_method(self):
        """
        Ensure find_owner method is working correctly
        """
        log=UserActivityLog.objects.get(user__email='linus@gmail.com')
        
        self.assertEqual(log.find_owner(), 'Not Assigned')
        
