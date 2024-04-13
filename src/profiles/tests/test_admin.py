from django.urls import reverse
from django.contrib.auth.models import Permission

from core.test_utils.custom_testcase import TestCase
from core.test_utils.create_user import create_new_user, create_new_manager_user
from core.test_utils.create_store_models import create_new_store

from profiles.admin import (
    ProfileAdmin, 
    ProfileCountAdmin,
    EmployeeProfileAdmin,
    EmployeeProfileCountAdmin
)
from profiles.models import Profile

class TestProfilesAppAdminTestCase(TestCase):
    def test_if_admin_classes_are_implementing_audit_log_mixin(self):
        """
        We make sure that account's admin classes we are implementing 
        AdminUserActivityLogMixin
        """
        admin_classes = (
            ProfileAdmin, 
            ProfileCountAdmin,
            EmployeeProfileAdmin,
            EmployeeProfileCountAdmin,
        )

        for admin_class in admin_classes:
            self.assertTrue(getattr(admin_class, "adux_collect_old_values", None))


class ProfileAdminHijackTestCase(TestCase):
    def setUp(self):
        #Create a super user with email john@gmail.com
        self.user = create_new_user('super') 
        
        #Create a user with email jack@gmail.com
        self.user2 = create_new_user('jack')

        # Make user to into a staff
        self.user2.is_staff = True
        self.user2.save()

        # Assign profile permissions to user2
        profile_permissions = [
            Permission.objects.get(codename='view_profile'),
            Permission.objects.get(codename='change_profile'),
            Permission.objects.get(codename='add_profile'),
            Permission.objects.get(codename='delete_profile')]

        for permission in profile_permissions:
            self.user2.user_permissions.add(permission)

        # Login superuser
        self.login = self.client.post(
            reverse('admin:login'), 
            {'username':'john@gmail.com',
             'password':'secretpass'})

    def test_if_delete_selected_action_has_been_disabled(self):

        app_label = 'profiles'
        my_model = 'profile'
        url_name = 'admin:%s_%s_changelist' % (app_label, my_model)
                
        response = self.client.get(reverse(url_name, args=()))
        self.assertEqual(response.status_code, 200)

        # ######### Test Content ######### #
        #self.assertNotContains(response ,'Delete selected')

    def test_if_the_add_button_has_been_disabled(self):

        app_label = 'profiles'
        my_model = 'profile'
        url_name = 'admin:%s_%s_changelist' % (app_label, my_model)
                
        response = self.client.get(reverse(url_name, args=()))
        self.assertEqual(response.status_code, 200)

        # ######### Test Content ######### #
        #self.assertNotContains(response ,'/add/') # Partial add link

    def test_if_payment_actions_are_displayed_to_superuser(self):

        app_label = 'profiles'
        my_model = 'profile'
        url_name = 'admin:%s_%s_changelist' % (app_label, my_model)
                
        response = self.client.get(reverse(url_name, args=()))
        self.assertEqual(response.status_code, 200)

        # ######### Test Content ######### #
        self.assertContains(response, '1 Month Plan For Top Profile')
        self.assertContains(response, '6 Months Plan For Top Profile')
        self.assertContains(response, '1 Year Plan For Top Profile')

    def test_if_payment_actions_are_not_displayed_to_non_superuser(self):

        # Login user2
        self.login = self.client.post(
            reverse('admin:login'), 
            {'username':'jack@gmail.com',
             'password':'secretpass'})

        app_label = 'profiles'
        my_model = 'profile'
        url_name = 'admin:%s_%s_changelist' % (app_label, my_model)
                
        response = self.client.get(reverse(url_name, args=()))
        self.assertEqual(response.status_code, 200)


        # ######### Test Content ######### #
        self.assertNotContains(response, '1 Month Plan For Top Profile')
        self.assertNotContains(response, '6 Months Plan For Top Profile')
        self.assertNotContains(response, '1 Year Plan For Top Profile')

    def test_if_log_in_as_links_are_displayed_to_superuser(self):

        app_label = 'profiles'
        my_model = 'profile'
        url_name = 'admin:%s_%s_changelist' % (app_label, my_model)
                
        response = self.client.get(reverse(url_name, args=()))
        self.assertEqual(response.status_code, 200)

        # ######### Test Content ######### #
        self.assertContains(response, '<a href="/magnupe/">Django administration</a>')
        self.assertContains(response, 'Select profile to change')

        # Profiles
        self.assertContains(
            response, 
            f'<a href="/magnupe/profiles/profile/{self.user.profile.pk}/change/">{self.user.get_full_name()}</a>')
        self.assertContains(
            response, 
            f'<a href="/magnupe/profiles/profile/{self.user2.profile.pk}/change/">{self.user2.get_full_name()}</a>')
        
        # Log is as links
        #self.assertContains(response, f'<a href="/hijack/login_as_user/{self.user.reg_no}/"')
        #self.assertContains(response, f'<a href="/hijack/login_as_user/{self.user2.reg_no}/"')
        #self.assertContains(response, 'Log In As')

    def test_if_log_in_as_links_are_not_displayed_to_non_superuser(self):

        # Login user2
        self.login = self.client.post(
            reverse('admin:login'), 
            {'username':'jack@gmail.com',
             'password':'secretpass'})

        app_label = 'profiles'
        my_model = 'profile'
        url_name = 'admin:%s_%s_changelist' % (app_label, my_model)

        response = self.client.get(reverse(url_name, args=()))
        self.assertEqual(response.status_code, 200)

        # ######### Test Content ######### #
        self.assertContains(response, '<a href="/magnupe/">Django administration</a>')
        self.assertContains(response, 'Select profile to change')

        # Profiles
        self.assertContains(
            response, 
            f'<a href="/magnupe/profiles/profile/{self.user.profile.pk}/change/">{self.user.get_full_name()}</a>')
        self.assertContains(
            response, 
            f'<a href="/magnupe/profiles/profile/{self.user2.profile.pk}/change/">{self.user2.get_full_name()}</a>')
        

        # Make sure Log is as links are not displayed
        self.assertNotContains(response, f'<a href="/hijack/login_as_user/{self.user.reg_no}/"')
        self.assertNotContains(response, f'<a href="/hijack/login_as_user/{self.user2.reg_no}/"')
        self.assertNotContains(response, 'Log In As')


class EmployeeProfileAdminHijackTestCase(TestCase):
    def setUp(self):
        #Create a super user with email john@gmail.com
        self.user = create_new_user('super') 

        profile = Profile.objects.get(user=self.user)

        self.store = create_new_store(profile, 'Computer Store')

        self.supervisor_user = create_new_manager_user("gucci", self.user.profile, self.store)
        
        #Create a user with email jack@gmail.com
        self.user2 = create_new_user('jack')

        # Make user to into a staff
        self.user2.is_staff = True
        self.user2.save()


        # Assign profile permissions to user2
        profile_permissions = [
            Permission.objects.get(codename='add_employeeprofile'),
            Permission.objects.get(codename='change_employeeprofile'),
            Permission.objects.get(codename='add_employeeprofile'),
            Permission.objects.get(codename='delete_employeeprofile')]

        for permission in profile_permissions:
            self.user2.user_permissions.add(permission)

        # Login superuser
        self.login = self.client.post(
            reverse('admin:login'), 
            {'username':'john@gmail.com',
             'password':'secretpass'})

    def test_if_delete_selected_action_has_been_disabled(self):

        app_label = 'profiles'
        my_model = 'employeeprofile'
        url_name = 'admin:%s_%s_changelist' % (app_label, my_model)
                
        response = self.client.get(reverse(url_name, args=()))
        self.assertEqual(response.status_code, 200)

        # ######### Test Content ######### #
        self.assertNotContains(response ,'Delete selected')

    def test_if_the_add_button_has_been_disabled(self):

        app_label = 'profiles'
        my_model = 'employeeprofile'
        url_name = 'admin:%s_%s_changelist' % (app_label, my_model)
                
        response = self.client.get(reverse(url_name, args=()))
        self.assertEqual(response.status_code, 200)

        # ######### Test Content ######### #
        #self.assertNotContains(response ,'/add/') # Partial add link

    def test_if_log_in_as_links_are_displayed_to_superuser(self):

        app_label = 'profiles'
        my_model = 'employeeprofile'
        url_name = 'admin:%s_%s_changelist' % (app_label, my_model)
                
        response = self.client.get(reverse(url_name, args=()))
        self.assertEqual(response.status_code, 200)


        # ######### Test Content ######### #
        self.assertContains(response, '<a href="/magnupe/">Django administration</a>')
        self.assertContains(response, 'Select employee profile to change')

        # Profiles
        self.assertContains(
            response, 
            f'<a href="/magnupe/profiles/employeeprofile/{self.supervisor_user.employeeprofile.pk}/change/">{self.supervisor_user.get_full_name()}</a>')
      
        # Log is as links
        #self.assertContains(response, f'<a href="/hijack/login_as_user/{self.supervisor_user.reg_no}/"')
        #self.assertContains(response, f'<a href="/hijack/login_as_user/{self.supervisor_user.reg_no}/"')
        #self.assertContains(response, 'Log In As')

    def test_if_log_in_as_links_are_not_displayed_to_non_superuser(self):

        # Login user2
        self.login = self.client.post(
            reverse('admin:login'), 
            {'username':'jack@gmail.com',
             'password':'secretpass'})

        app_label = 'profiles'
        my_model = 'employeeprofile'
        url_name = 'admin:%s_%s_changelist' % (app_label, my_model)

        response = self.client.get(reverse(url_name, args=()))
        self.assertEqual(response.status_code, 200)

        # ######### Test Content ######### #
        self.assertContains(response, '<a href="/magnupe/">Django administration</a>')
        self.assertContains(response, 'Select employee profile to change')

        # Supervisor profiles
        self.assertContains(
            response, 
            f'<a href="/magnupe/profiles/employeeprofile/{self.supervisor_user.employeeprofile.pk}/change/">{self.supervisor_user.get_full_name()}</a>')
      

        # Make sure Log is as links are not displayed
        self.assertNotContains(response, f'<a href="/hijack/login_as_user/{self.supervisor_user.reg_no}/"')
        self.assertNotContains(response, f'<a href="/hijack/login_as_user/{self.supervisor_user.reg_no}/"')
        self.assertNotContains(response, 'Log In As')