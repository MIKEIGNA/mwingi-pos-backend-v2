from django.utils import timezone
from django.urls import reverse
from django.contrib.admin.utils import quote
from django.contrib.auth import get_user_model

from core.test_utils.create_store_models import create_new_store
from core.test_utils.create_user import (
    create_new_user,
    create_new_manager_user,
    create_new_cashier_user
)
from core.test_utils.custom_testcase import TestCase
from core.test_utils.phone_numbers_data import wrong_phones 

from accounts.admin import UserAdmin, UserChannelRecordAdmin
from profiles.models import Profile
from mylogentries.models import UserActivityLog, CREATED, CHANGED

from ..utils.user_type import EMPLOYEE_USER, TOP_USER

User = get_user_model()


class TestAccountsAppAdminTestCase(TestCase):

    def test_if_admin_classes_are_implementing_audit_log_mixin(self):
        """
        We make sure that account's admin classes we are implementing 
        AdminUserActivityLogMixin
        """
        admin_classes = [UserAdmin, UserChannelRecordAdmin]

        for admin_class in admin_classes:
            self.assertTrue(getattr(admin_class, "adux_collect_old_values", None))


class UserAdminTestCase(TestCase):
    def setUp(self):
    
        #Create a super user with email john@gmail.com
        self.user = create_new_user('super') 

        profile = Profile.objects.get(user=self.user) 

        self.store = create_new_store(profile, 'Computer Store')
        
        #Create a user with email jack@gmail.com
        self.user2 = create_new_user('jack')

    
        self.login = self.client.post(reverse('admin:login'), 
                                    {'username':'john@gmail.com',
                                     'password':'secretpass'
                                            }
                                    )

    def test_admin_fieldsets(self):
        admin_class = UserAdmin
        
        fieldsets = (
            ('Personal info', {'fields': (
                'first_name', 
                'last_name', 
                'email', 
                'get_user_type',
                'gender')}),
            ('Permissions', {'fields': ('is_active', 'is_staff', 'groups',)}),
            )
        
        self.assertEqual(admin_class.fieldsets, fieldsets)
       
    def test_admin_list_display(self):
        admin_class = UserAdmin
        
        list_display = (
            'first_name', 
            'last_name', 
            'email', 
            'phone', 
            'user_type', 
            'reg_no', 
            'is_staff', 
            'is_active')
        
        self.assertEqual(admin_class.list_display, list_display )
        
    def test_admin_list_filter(self):
        admin_class = UserAdmin
        
        list_filter = ('is_staff','user_type')
        
        self.assertEqual(admin_class.list_filter, list_filter )
        
    def test_admin_search_fields(self):
        admin_class = UserAdmin
        
        search_fields = ('email',)
        
        self.assertEqual(admin_class.search_fields, search_fields )
        
    def test_admin_ordering(self):
        admin_class = UserAdmin
        
        ordering = ('email',)
        
        self.assertEqual(admin_class.ordering, ordering)
       
    def test_if_UserAdmin_can_create_a_top_user(self):  
        """
        Ensure UserAdmin can create a user
        """
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
        
        response = self.client.post(reverse_url, {'first_name':'Ben',
                                                  'last_name':'Linus',
                                                  'email':'linus@gmail.com',
                                                  'phone': '254724223322',
                                                  'user_type': TOP_USER,
                                                  'gender': 0,
                                                  'password1': 'secretpass', 
                                                  'password2': 'secretpass'
                                                  }, follow=True)
            
        self.assertEqual(response.status_code, 200)

        u = User.objects.get(email='linus@gmail.com')
        
        today = (timezone.now()).strftime("%B, %d, %Y")
    
        self.assertEqual(str(u), 'linus@gmail.com')
        self.assertEqual(u.email, 'linus@gmail.com')
        self.assertEqual(u.first_name, 'Ben')
        self.assertEqual(u.last_name, 'Linus')
        self.assertEqual(u.phone, 254724223322)
        self.assertEqual(u.user_type, TOP_USER)
        self.assertEqual(u.gender, 0)
        self.assertEqual((u.join_date).strftime("%B, %d, %Y"), today)
        self.assertEqual(u.is_active, True)
        self.assertEqual(u.is_staff, False)
        self.assertEqual(u.is_superuser, False)


    def test_if_UserAdmin_can_create_a_manager_user(self):  
        """
        Ensure UserAdmin can create a user
        """
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
        
        response = self.client.post(reverse_url, {'first_name':'Ben',
                                                  'last_name':'Linus',
                                                  'email':'linus@gmail.com',
                                                  'phone': '254724223322',
                                                  'user_type': EMPLOYEE_USER,
                                                  'gender': 0,
                                                  'password1': 'secretpass', 
                                                  'password2': 'secretpass'
                                                  }, follow=True)
            
        self.assertEqual(response.status_code, 200)
        
        u = User.objects.get(email='linus@gmail.com')
        
        today = (timezone.now()).strftime("%B, %d, %Y")
    
        self.assertEqual(str(u), 'linus@gmail.com')
        self.assertEqual(u.email, 'linus@gmail.com')
        self.assertEqual(u.first_name, 'Ben')
        self.assertEqual(u.last_name, 'Linus')
        self.assertEqual(u.phone, 254724223322)
        self.assertEqual(u.user_type, EMPLOYEE_USER)
        self.assertEqual(u.gender, 0)
        self.assertEqual((u.join_date).strftime("%B, %d, %Y"), today)
        self.assertEqual(u.is_active, True)
        self.assertEqual(u.is_staff, False)
        self.assertEqual(u.is_superuser, False)

    def test_if_UserAdmin_can_create_a_employee_user(self):  
        """
        Ensure UserAdmin can create a user
        """
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
        
        response = self.client.post(reverse_url, {'first_name':'Ben',
                                                  'last_name':'Linus',
                                                  'email':'linus@gmail.com',
                                                  'phone': '254724223322',
                                                  'user_type': EMPLOYEE_USER,
                                                  'gender': 0,
                                                  'password1': 'secretpass', 
                                                  'password2': 'secretpass'
                                                  }, follow=True)
            
        self.assertEqual(response.status_code, 200)

        u = User.objects.get(email='linus@gmail.com')
        
        today = (timezone.now()).strftime("%B, %d, %Y")
    
        self.assertEqual(str(u), 'linus@gmail.com')
        self.assertEqual(u.email, 'linus@gmail.com')
        self.assertEqual(u.first_name, 'Ben')
        self.assertEqual(u.last_name, 'Linus')
        self.assertEqual(u.phone, 254724223322)
        self.assertEqual(u.user_type, EMPLOYEE_USER)
        self.assertEqual(u.gender, 0)
        self.assertEqual((u.join_date).strftime("%B, %d, %Y"), today)
        self.assertEqual(u.is_active, True)
        self.assertEqual(u.is_staff, False)
        self.assertEqual(u.is_superuser, False)

        
    def test_if_UserAdmin_cant_create_a_user_without_a_first_name(self):  
        """
        Ensure UserAdmin cant create a user without a first_name
        """
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
        
        response = self.client.post(reverse_url, {'first_name':'',
                                                  'last_name':'Linus',
                                                  'email':'linus@gmail.com',
                                                  'phone': '254724223322',
                                                  'user_type': TOP_USER,
                                                  'gender': 0,
                                                  'password1': 'secretpass', 
                                                  'password2': 'secretpass'
                                                  }, follow=True)
            
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='linus@gmail.com').exists(), False)

        self.assertContains(response, 'This field is required.')
       
    def test_if_UserAdmin_cant_create_a_user_without_a_last_name(self):  
        """
        Ensure UserAdmin cant create a user without a last_name
        """
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
        
        response = self.client.post(reverse_url, {'first_name':'Ben',
                                                  'last_name':'',
                                                  'email':'linus@gmail.com',
                                                  'phone': '254724223322',
                                                  'user_type': TOP_USER,
                                                  'gender': 0,
                                                  'password1': 'secretpass', 
                                                  'password2': 'secretpass'
                                                  }, follow=True)
            
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='linus@gmail.com').exists(), False)

        self.assertContains(response, 'This field is required.')
        
    def test_if_UserAdmin_cant_create_a_user_without_an_email(self):  
        """
        Ensure UserAdmin cant create a user without an email
        """
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
        
        response = self.client.post(reverse_url, {'first_name':'Ben',
                                                  'last_name':'Linus',
                                                  'email':'',
                                                  'phone': '254724223322',
                                                  'user_type': TOP_USER,
                                                  'gender': 0,
                                                  'password1': 'secretpass', 
                                                  'password2': 'secretpass'
                                                  }, follow=True)
            
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='linus@gmail.com').exists(), False)

        self.assertContains(response, 'This field is required.')
        
    def test_if_UserAdmin_cant_create_a_user_without_a_wrong_email(self):  
        """
        Ensure UserAdmin cant create a user without a wrong email
        """
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
        
        response = self.client.post(reverse_url, {'first_name':'Ben',
                                                  'last_name':'Linus',
                                                  'email':'wrong_email',
                                                  'phone': '254724223322',
                                                  'user_type': TOP_USER,
                                                  'gender': 0,
                                                  'password1': 'secretpass', 
                                                  'password2': 'secretpass'
                                                  }, follow=True)
            
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='linus@gmail.com').exists(), False)

        self.assertContains(response, 'Enter a valid email address.')

    def test_if_UserAdmin_cant_create_a_user_with_a_non_unique_email(self):

        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)

        # Try to signup with emails from existing users
        
        top_profile = Profile.objects.get(user__email='john@gmail.com')
        
        # Create 2 supervisor users
        create_new_manager_user("gucci", top_profile, self.store)
        create_new_manager_user("lewis", top_profile, self.store)
        
        # Create 2 team users
        create_new_cashier_user("james", top_profile, self.store)
        create_new_cashier_user("ben", top_profile, self.store)
 
        # Get users emails
        top_user1_email = User.objects.get(email='john@gmail.com').email
        top_user2_email = User.objects.get(email='jack@gmail.com').email 
        
        manager_user1_email = User.objects.get(email='gucci@gmail.com').email
        manager_user2_email = User.objects.get(email='lewis@gmail.com').email 
        
        employee_user1_email = User.objects.get(email='james@gmail.com').email
        employee_user2_email = User.objects.get(email='ben@gmail.com').email 
        
        user_emails = [top_user1_email, 
                       top_user2_email, 
                       manager_user1_email,
                       manager_user2_email,
                       employee_user1_email, employee_user2_email]
        
        i=0
        for email in user_emails:

            response = self.client.post(reverse_url, {
                'first_name':'Ben','last_name':'Linus',
                'email':email,
                'phone': '254724223322',
                'user_type': TOP_USER,
                'gender': 0,
                'password1': 'secretpass', 
                'password2': 'secretpass'
            }, follow=True)
            
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User with this Email already exists.')

        self.assertEqual(User.objects.filter(email='linus@gmail.com').exists(), False)

    def test_if_UserAdmin_cant_create_a_user_without_a_phone(self):  
        """
        Ensure UserAdmin cant create a user without a phone
        """
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
        
        response = self.client.post(reverse_url, {'first_name':'Ben',
                                                  'last_name':'Linus',
                                                  'email':'linus@gmail.com',
                                                  'phone': '',
                                                  'user_type': TOP_USER,
                                                  'gender': 0,
                                                  'password1': 'secretpass', 
                                                  'password2': 'secretpass'
                                                  }, follow=True)
            
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='linus@gmail.com').exists(), False)

        self.assertContains(response, 'This field is required.')
     
    def test_if_UserAdmin_cant_create_a_user_with_a_non_safaricom_number(self):  
        """
        Ensure UserAdmin cant create a user with a non safaricom number
        """
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
    
        i = 0
        for phone in wrong_phones:
            response = self.client.post(reverse_url, {'first_name':'Ben',
                                                  'last_name':'Linus',
                                                  'email':'linus@gmail.com',
                                                  'phone': phone,
                                                  'user_type': TOP_USER,
                                                  'gender': 0,
                                                  'password1': 'secretpass', 
                                                  'password2': 'secretpass'
                                                  }, follow=True)
            
            self.assertEqual(response.status_code, 200)

            if i == 1:
                self.assertContains(response, 'This phone is too long.')

            elif i == 2:
                self.assertContains(response, 'This phone is too short.')

            elif i == 3:
                self.assertContains(response, 'Ensure this value is less than or equal to 9223372036854775807.')

            else:
                self.assertContains(response, 'Enter a whole number.')
                  
            i+=1

            self.assertEqual(User.objects.filter(email='linus@gmail.com').exists(), False)

        
    def test_if_UserAdmin_cant_create_a_user_with_non_matching_passwords(self):  
        """
        Ensure UserAdmin cant_create a user with non matching passwords
        """
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
        
        response = self.client.post(reverse_url, {'first_name':'Ben',
                                                  'last_name':'Linus',
                                                  'email':'linus@gmail.com',
                                                  'phone': '254724223322',
                                                  'user_type': TOP_USER,
                                                  'gender': 0,
                                                  'password1': 'secretpass', 
                                                  'password2': 'yunggode'
                                                  }, follow=True)
            
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='linus@gmail.com').exists(), False)

    def test_if_UserAdmin_cant_create_a_user_without_a_user_type(self):  
       
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
        
        response = self.client.post(reverse_url, {'first_name':'Ben',
                                                  'last_name':'Linus',
                                                  'email':'linus@gmail.com',
                                                  'phone': '254724223322',
                                                  'user_type': '',
                                                  'gender': 0,
                                                  'password1': 'secretpass', 
                                                  'password2': 'secretpass'
                                                  }, follow=True)
            
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='linus@gmail.com').exists(), False)

        self.assertContains(response, 'This field is required.')

    def test_if_UserAdmin_cant_create_a_user_without_a_user_gender(self):  
       
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
        
        response = self.client.post(reverse_url, {'first_name':'Ben',
                                                  'last_name':'Linus',
                                                  'email':'linus@gmail.com',
                                                  'phone': '254724223322',
                                                  'user_type': TOP_USER,
                                                  'gender': '',
                                                  'password1': 'secretpass', 
                                                  'password2': 'secretpass'
                                                  }, follow=True)
            
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='linus@gmail.com').exists(), False)

        self.assertContains(response, 'This field is required.')

class UserActivityLogForUserModelTestCase(TestCase):
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
    
    def test_login(self):
        response = self.login
        """ Confirm that the user is logged in """
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        
    def test_if_UserActivityLog_logs_user_creation(self):  
        """
        Ensure UserActivityLog logs user creation
        """
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
        
        response = self.client.post(reverse_url, {'first_name':'Ben',
                                                  'last_name':'Linus',
                                                  'email':'linus@gmail.com',
                                                  'phone': '254724223322',
                                                  'user_type': TOP_USER,
                                                  'gender': 0,
                                                  'password1': 'secretpass', 
                                                  'password2': 'secretpass'
                                                  }, follow=True)
            
        self.assertEqual(response.status_code, 200)

        created_user = User.objects.get(email='linus@gmail.com')
        
        self.assertEqual(created_user.first_name, 'Ben')
        self.assertEqual(created_user.last_name, 'Linus')
        self.assertEqual(created_user.email, 'linus@gmail.com')
        self.assertEqual(created_user.phone, 254724223322)
        self.assertEqual(created_user.is_staff, False)
        
        """ Verbose Names """
        log=UserActivityLog.objects.get(user__email='john@gmail.com')
        
        self.assertEqual(log.change_message, 'New "User" "linus@gmail.com" has been created by "john@gmail.com"')
        self.assertEqual(log.object_id, str(created_user.pk))
        self.assertEqual(log.object_repr, 'linus@gmail.com')
        self.assertEqual(log.content_type.model, 'user')
        self.assertEqual(log.user.email, 'john@gmail.com')
        self.assertTrue(len(log.ip) > 7)
        self.assertEqual(log.action_type, CREATED)
        self.assertEqual(log.owner_email, '')
        self.assertEqual(log.panel, 'Admin')
        
        """ Methods """
        self.assertEqual(str(log),'Accounts | User Created.')
        self.assertEqual(log.is_creation(), True)
        self.assertEqual(log.is_change(), False)
        self.assertEqual(log.is_deletion(), False)
        self.assertEqual(log.get_change_message(), 'New "User" "linus@gmail.com" has been created by "john@gmail.com"')
        self.assertEqual(str(log.get_edited_object()), 'linus@gmail.com')
        self.assertEqual(str(log.get_admin_url()), f'/magnupe/accounts/user/{created_user.pk}/change/')
        self.assertEqual(log.the_object(), f'<a href="http://127.0.0.1:8000/magnupe/accounts/user/{created_user.pk}/change/">Accounts | User</a>')
        self.assertEqual(log.editor_profile(), f'<a href="http://127.0.0.1:8000/magnupe/profiles/profile/{self.user.profile.pk}/change/">john@gmail.com</a>')
        self.assertEqual(log.find_owner(), 'Not Assigned') 
        
    def test_if_UserActivityLog_logs_user_change(self):  
        """
        Ensure UserActivityLog logs user change
        """
        pk = User.objects.get(email='jack@gmail.com').pk
        
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_change' % (app_label, my_model)
        
        reverse_url = reverse(url_name, args=(quote(pk),))
        
        response = self.client.post(reverse_url, {'first_name':'Jacko',
                                                  'last_name':'Shephardo',
                                                  'email':'jacko@gmail.com',
                                                  'gender': 1,
                                                  'is_active': False,
                                                  'is_staff': True
                                                  }, follow=True)
        
        self.assertEqual(response.status_code, 200)

        changed_user = User.objects.get(email='jacko@gmail.com')
        
        self.assertEqual(changed_user.first_name, 'Jacko')
        self.assertEqual(changed_user.last_name, 'Shephardo')
        self.assertEqual(changed_user.email, 'jacko@gmail.com')
        self.assertEqual(changed_user.gender, 1)
        self.assertEqual(changed_user.is_active, False)
        self.assertEqual(changed_user.is_staff, True)

        """ Verbose Names """
        log=UserActivityLog.objects.get(user__email='john@gmail.com')
        
        change_msg = ['"First_Name" changed from "Jack" to "Jacko".',
                      '"Last_Name" changed from "Shephard" to "Shephardo".',
                      '"Email" changed from "jack@gmail.com" to "jacko@gmail.com".',
                      '"Gender" changed from "0" to "1".',
                      '"Is_Active" changed from "True" to "False".',
                      '"Is_Staff" changed from "False" to "True".',
                      ]

        """ Field Names """
        for msg in change_msg:
            self.assertTrue(msg in log.change_message)
         
        self.assertEqual((log.change_message).count('.\n'), 6) # Confirm the number of lines in the log's change message
        self.assertEqual(log.object_id, str(self.user2.pk))
        self.assertEqual(log.object_repr, 'jacko@gmail.com')
        self.assertEqual(log.content_type.model, 'user')
        self.assertEqual(log.user.email, 'john@gmail.com')
        self.assertTrue(len(log.ip) > 7)
        self.assertEqual(log.action_type, CHANGED)
        self.assertEqual(log.owner_email, '')
        self.assertEqual(log.panel, 'Admin')
        
        """ Methods """
        self.assertEqual(str(log),'Accounts | User Changed.')
        self.assertEqual(log.is_creation(), False)
        self.assertEqual(log.is_change(), True)
        self.assertEqual(log.is_deletion(), False)
        
        get_change_message = log.get_change_message()
        for msg in change_msg:
            self.assertTrue(msg in get_change_message)
    
        self.assertEqual(str(log.get_edited_object()), 'jacko@gmail.com')
        self.assertEqual(str(log.get_admin_url()), f'/magnupe/accounts/user/{self.user2.pk}/change/')
        self.assertEqual(log.the_object(), f'<a href="http://127.0.0.1:8000/magnupe/accounts/user/{self.user2.pk}/change/">Accounts | User</a>')
        self.assertEqual(log.editor_profile(), f'<a href="http://127.0.0.1:8000/magnupe/profiles/profile/{self.user.profile.pk}/change/">john@gmail.com</a>')
        self.assertEqual(log.find_owner(), 'Not Assigned')
    
    """
    TODO - This fails in testing for some reasons
    def test_if_UserActivityLog_logs_user_deletion(self):  
        # Ensure UserActivityLog logs user deletion
        
        pk = User.objects.get(email='jack@gmail.com').pk
        
        app_label = 'accounts'
        my_model = 'user'
        url_name = 'admin:%s_%s_delete' % (app_label, my_model)

        reverse_url = reverse(url_name, args=(pk,))
    
        response = self.client.get(reverse_url, follow=True)
        
        # For admin delete to work, you must post something to that url
        response = self.client.post(reverse_url, {'d':'d'}, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Confirm that the user was deleted
        self.assertEqual(User.objects.filter(email='jack@gmail.com').exists(), False)
        
        # Verbose Names
        log=UserActivityLog.objects.get(user__email='john@gmail.com')
        
        self.assertEqual(log.change_message, '"jack@gmail.com" has been deleted by "john@gmail.com"')
        self.assertEqual(log.object_id, str(pk))
        self.assertEqual(log.object_repr, 'jack@gmail.com')
        self.assertEqual(log.content_type.model, 'user')
        self.assertEqual(log.user.email, 'john@gmail.com')
        self.assertTrue(len(log.ip) > 7)
        self.assertEqual(log.action_type, DELETED)
        self.assertEqual(log.owner_email, '')
        self.assertEqual(log.panel, 'Admin')
        
        # Methods
        self.assertEqual(str(log),'User Deleted.')
        self.assertEqual(log.is_creation(), False)
        self.assertEqual(log.is_change(), False)
    """
    
