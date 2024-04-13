from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.admin.utils import quote

from core.test_utils.custom_testcase import TestCase
from core.test_utils.create_user import create_new_user

from mylogentries.models import UserActivityLog, CHANGED

from mysettings.models import MySetting
from mysettings.admin import MySettingAdmin

from profiles.models import Profile

User = get_user_model()

class TestMySettingsAppAdminTestCase(TestCase):
    def test_if_admin_classes_are_implementing_audit_log_mixin(self):
        """
        We make sure that my settings admin classes we are implementing 
        AdminUserActivityLogMixin
        """
        admin_classes = (
            MySettingAdmin, 
            )

        for admin_class in admin_classes:
            self.assertTrue(getattr(admin_class, "adux_collect_old_values", None))


class MySettingAdminTestCase(TestCase):
    def setUp(self):
    
        
        #Create a super user with email john@gmail.com
        self.user = create_new_user('super') 
        
        #Create a user with email jack@gmail.com
        self.user2 = create_new_user('jack')
        


        self.login = self.client.post(reverse('admin:login'), 
                                    {'username':'john@gmail.com',
                                     'password':'secretpass'
                                            }
                                    )
        
    def test_fieldsets(self):
        admin = MySettingAdmin
        
        fieldsets = [
            (None, {'fields': (
                'name', 
                'reset_tokens', 
                'signups', 
                'maintenance', 
                'allow_contact', 
                'delete_sessions', 
                'accept_payments', 
                'accept_mpesa', 
                'new_employee',
                'new_product',
                'new_customer',
                'new_sale',)})]
        
        self.assertEqual(admin.fieldsets, fieldsets)
        
    def test_list_display(self):
        admin = MySettingAdmin
        
        list_display = (
            '__str__', 
            'signups', 
            'maintenance', 
            'accept_payments', 
            'accept_mpesa', 
            'new_employee'
        )
        
        self.assertEqual(admin.list_display, list_display )
        
    def test_readonly_fields(self):
        admin = MySettingAdmin
        
        self.assertEqual(admin.readonly_fields[0], 'name')
        
    def test_if_mysetting_admin_area_does_not_have_delete_selected_action(self):  
        """
        Ensure mysetting admin area does not have delete selected action
        """
        app_label = 'mysettings'
        my_model = 'mysetting'
        url_name = 'admin:%s_%s_changelist' % (app_label, my_model)

        response = self.client.get(reverse(url_name, args=()))
        self.assertEqual(response.status_code, 200)

        # ######### Test Content ######### #
        self.assertNotContains(response ,'Delete selected')


class UserActivityLogForMySettingModelTestCase(TestCase):
    def setUp(self):
        
        #Create a super user with email john@gmail.com
        self.user = create_new_user('super') 
        self.profile1 = Profile.objects.get(user=self.user)
        
        #Create a user with email jack@gmail.com
        self.user2 = create_new_user('jack')
        

        
        self.login = self.client.post(reverse('admin:login'), 
                                    {'username':'john@gmail.com',
                                     'password':'secretpass'
                                            }
                                    )
    
    def test_login(self):
        response = self.login
        """ Confirm that the user is logged in """
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        
    def test_if_UserActivityLog_logs_mysetting_creation(self):  
        """
        We can't test mysetting creation coz mysetting are created progamatically
        when the first user model is created
        """
         
    def test_if_UserActivityLog_logs_mysetting_change(self):  
        """
        Ensure UserActivityLog logs mysetting change
        """
        
        # First confirm the values in the Mysetting obj
        ms1 = MySetting.objects.get(name='main')
        
        self.assertEqual(ms1.name, 'main')
        self.assertEqual(ms1.reset_tokens, False)
        self.assertEqual(ms1.signups, True)
        self.assertEqual(ms1.maintenance, True)
        self.assertEqual(ms1.delete_sessions, False)
        self.assertEqual(ms1.new_employee, True)
        self.assertEqual(ms1.new_product, True)
        self.assertEqual(ms1.new_customer, True)
        self.assertEqual(ms1.new_sale, True)

        payload = {
            'name': 'mainn',
            'reset_tokens': True,
            'signups': False,
            'maintenance': False,
            'allow_contact': False,
            'delete_sessions': True,
            'accept_payments': False,
            'accept_mpesa': False,
            'new_employee': False,
            'new_product': False,
            'new_customer': False,
            'new_sale': False,
            }

  
        app_label = 'mysettings'
        my_model = 'mysetting'
        url_name = 'admin:%s_%s_change' % (app_label, my_model)
        
        pk = MySetting.objects.get(name='main').pk
        
        reverse_url = reverse(url_name, args=(quote(pk),))


        payload = {
            'name': 'mainn',
            'reset_tokens': True,
            'signups': False,
            'maintenance': False,
            'allow_contact': False,
            'delete_sessions': True,
            'accept_payments': False,
            'accept_mpesa': False,
            'new_employee': False,
            'new_product': False,
            'new_customer': False,
            'new_sale': False,
            }
        
        response = self.client.post(reverse_url, payload, follow=True)
        
        self.assertEqual(response.status_code, 200)

      
        ms = MySetting.objects.get(name='main') # Make sure name cant and changed 

        self.assertEqual(ms.name, 'main') # This field is designed to never change
        self.assertEqual(ms.reset_tokens, False) # This field is designed to never change
        self.assertEqual(ms.signups, False)
        self.assertEqual(ms.maintenance, False)
        self.assertEqual(ms.allow_contact, False)
        self.assertEqual(ms.delete_sessions, False) # This field is designed to never change
        self.assertEqual(ms.accept_payments, False)
        self.assertEqual(ms.accept_mpesa, False)
        self.assertEqual(ms.new_employee, False)
        self.assertEqual(ms.new_product, False)
        self.assertEqual(ms.new_customer, False)
        self.assertEqual(ms.new_sale, False)

         
        """ Verbose Names """
        log=UserActivityLog.objects.get(user__email='john@gmail.com')

        change_msg = [
            '"Signups" changed from "True" to "False".',
            '"Maintenance" changed from "True" to "False".',
            '"Allow_Contact" changed from "True" to "False".',
            '"Accept_Payments" changed from "True" to "False".',
            '"Accept_Mpesa" changed from "True" to "False".',
            '"New_Employee" changed from "True" to "False".',
            '"New_Product" changed from "True" to "False".',
            '"New_Customer" changed from "True" to "False".',
            '"New_Sale" changed from "True" to "False".',
        ]

        """ Field Names """
        for msg in change_msg:
            self.assertTrue(msg in log.change_message)

        self.assertEqual((log.change_message).count('.\n'), 9) # Confirm the number of lines in the log's change message
        self.assertEqual(log.object_id, str(pk))
        self.assertEqual(log.object_repr, 'main')
        self.assertEqual(log.content_type.model, 'mysetting')
        self.assertEqual(log.user.email, 'john@gmail.com')
        self.assertTrue(len(log.ip) > 7)
        self.assertEqual(log.action_type, CHANGED)
        self.assertEqual(log.owner_email, '')
        self.assertEqual(log.panel, 'Admin')
         
        """ Methods """
        self.assertEqual(str(log),'Mysettings | My Setting Changed.')
        self.assertEqual(log.is_creation(), False)
        self.assertEqual(log.is_change(), True)
        self.assertEqual(log.is_deletion(), False)
        
        get_change_message = log.get_change_message()
        for msg in change_msg:
            self.assertTrue(msg in get_change_message)
    
        self.assertEqual(str(log.get_edited_object()), 'main')
        self.assertEqual(str(log.get_admin_url()), f'/magnupe/mysettings/mysetting/{ms.pk}/change/')
        self.assertEqual(log.the_object(), f'<a href="http://127.0.0.1:8000/magnupe/mysettings/mysetting/{ms.pk}/change/">Mysettings | My Setting</a>')
        self.assertEqual(log.editor_profile(), f'<a href="http://127.0.0.1:8000/magnupe/profiles/profile/{self.profile1.pk}/change/">john@gmail.com</a>')
        self.assertEqual(log.find_owner(), 'Not Assigned')

    def test_if_a_new_mysetting_obj_cant_be_added_through_the_admin_area(self):  

        app_label = 'mysettings'
        my_model = 'mysetting'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)

        payload = {
            'name': 'mainn',
            'reset_tokens': True,
            'signups': False,
            'maintenance': False,
            'allow_contact': False,
            'delete_sessions': True,
            'accept_payments': False,
            'accept_mpesa': False,
            'new_employee': False,
            'new_product': False,
            'new_customer': False,
            'new_sale': False,
            }
        
        response = self.client.post(reverse_url, payload, follow=True)
            
        self.assertEqual(response.status_code, 403)
       
        mysetting = MySetting.objects.all().count()
        self.assertEqual(mysetting, 1)
      
    def test_if_mysetting_cant_be_deleted_through_the_admin_area(self):  
        # Begin the admin testing
        
        app_label = 'mysettings'
        my_model = 'mysetting'
        url_name = 'admin:%s_%s_delete' % (app_label, my_model)
        
        pk = MySetting.objects.get(name='main').pk

        reverse_url = reverse(url_name, args=(quote(pk),))
    
        """ Confirm that mysetting cant deleted """
        response = self.client.get(reverse_url, follow=True)
        self.assertEqual(response.status_code, 403)
        
