
from django.urls import reverse
from core.test_utils.custom_testcase import TestCase, APITestCase
from django.contrib.auth import get_user_model

from mysettings.models import MySetting
from mylogentries.models import UserActivityLog, PaymentLog, MpesaLog, RequestTimeSeries
from mylogentries.admin import UserActivityLogAdmin, PaymentLogAdmin, MpesaLogAdmin
from django.test import Client
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from core.test_utils.initial_user_data import InitialUserDataMixin
from core.test_utils.create_user import create_new_user

User = get_user_model()


# TODO We skip this intentionally
class RequestTimeSeriesFieldsTestCase(TestCase):
    def setUp(self):

        #Create a user with email john@gmail.com
        self.user = create_new_user('john') 
                
        RequestTimeSeries.objects.create(
                email = self.user.email, 
                is_logged_in_as_email = 'john@gmail.com',
                os = "Linux",
                device_type = "MOBILE",
                browser = "Firefox",
                ip_address = "127.0.0.1",
                view_name = "profiles:profile",
                request_method = "GET",
                status_code = 200,
                response_time = 200,
                reg_no = 1545
                )
        
    def test_RequestTimeSeries_verbose_names(self):
        """
        Ensure RequestTimeSeries exists and all fields have the correct verbose names and can be
        found
        """

        rts = RequestTimeSeries.objects.get(email=self.user.email)

        self.assertEqual(rts._meta.get_field('email').verbose_name,'email')
        self.assertEqual(rts._meta.get_field('is_logged_in_as_email').verbose_name,'is logged in as email')
        self.assertEqual(rts._meta.get_field('is_logged_in_as').verbose_name,'is logged in as')
        self.assertEqual(rts._meta.get_field('os').verbose_name,'os')
        self.assertEqual(rts._meta.get_field('device_type').verbose_name,'device type')
        self.assertEqual(rts._meta.get_field('browser').verbose_name,'browser')
        self.assertEqual(rts._meta.get_field('ip_address').verbose_name,'ip address')
        self.assertEqual(rts._meta.get_field('view_name').verbose_name,'view name')
        self.assertEqual(rts._meta.get_field('request_method').verbose_name,'request method')
        self.assertEqual(rts._meta.get_field('status_code').verbose_name,'status code')
        self.assertEqual(rts._meta.get_field('location_update').verbose_name,'location update')
        self.assertEqual(rts._meta.get_field('map_loaded').verbose_name,'map loaded')
        self.assertEqual(rts._meta.get_field('is_api').verbose_name,'is api')
        self.assertEqual(rts._meta.get_field('was_throttled').verbose_name,'was throttled')
        self.assertEqual(rts._meta.get_field('response_time').verbose_name,'response time')
        self.assertEqual(rts._meta.get_field('reg_no').verbose_name,'reg no')
        
        fields = ([field.name for field in RequestTimeSeries._meta.fields])
        
        self.assertEqual(len(fields), 18)
        
    def test_RequestTimeSeries_fields_existence(self):
            
        rts = RequestTimeSeries.objects.get(email=self.user.email)
        
        self.assertEqual(rts.email, self.user.email)
        self.assertEqual(rts.is_logged_in_as_email, 'john@gmail.com')
        self.assertEqual(rts.is_logged_in_as, True)
        self.assertEqual(rts.os, "Linux")
        self.assertEqual(rts.device_type, "MOBILE")
        self.assertEqual(rts.browser, "Firefox")
        self.assertEqual(rts.ip_address, "127.0.0.1")
        self.assertEqual(rts.view_name, "profiles:profile")
        self.assertEqual(rts.request_method, "GET")
        self.assertEqual(rts.status_code, 200)
        self.assertEqual(rts.location_update, False)
        self.assertEqual(rts.map_loaded, False)
        self.assertEqual(rts.is_api, False)
        self.assertEqual(rts.was_throttled, False)
        self.assertEqual(rts.response_time, 200.0)
        self.assertEqual(rts.reg_no, 1545)

    def test_set_is_logged_in_as_method(self):

        # Test with is_logged_in_as_email provided
        rts = RequestTimeSeries.objects.get(email=self.user.email)

        self.assertEqual(rts.is_logged_in_as_email, 'john@gmail.com')
        self.assertEqual(rts.is_logged_in_as, True)

        # Test with is_logged_in_as_email not provided
        rts = RequestTimeSeries.objects.get(email=self.user.email)
        rts.is_logged_in_as_email = ''
        rts.save()

        self.assertEqual(rts.is_logged_in_as_email, '')
        self.assertEqual(rts.is_logged_in_as, False)


class WebRequestTimeSeriesTestCase(TestCase, InitialUserDataMixin):
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
        
        self.create_initial_user_data_with_superuser()

        """ Turn off maintenance mode"""
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
        
        # My client
        self.client = Client()
        self.client.login(username='john@gmail.com', password='secretpass')

    def test_if_requests_are_being_logged_to_db(self):

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
        self.assertEqual(RequestTimeSeries.objects.all().count(), 1)
        
        # First RequestTimeSeries
        rts = RequestTimeSeries.objects.all().order_by('created_date')[0]
        
        self.assertEqual(rts.email, 'john@gmail.com')
        self.assertEqual(rts.is_logged_in_as_email, '')
        self.assertEqual(rts.is_logged_in_as, False)
        self.assertEqual(rts.os, 'Android')
        self.assertEqual(rts.device_type, 'MOBILE')
        self.assertEqual(rts.browser, 'Chrome')
        self.assertEqual(rts.ip_address, "127.0.0.1")
        self.assertEqual(rts.view_name, "home")
        self.assertEqual(rts.request_method, "GET")
        self.assertEqual(rts.status_code, 200)
        self.assertEqual(rts.location_update, False)
        self.assertEqual(rts.map_loaded, False)
        self.assertEqual(rts.is_api, False)
        self.assertEqual(rts.was_throttled, False)
        self.assertTrue(rts.response_time < 0.500)
        self.assertEqual(rts.reg_no, 0)
 
    def test_if_requests_with_reg_no_will_be_logged_to_db(self):
        
        response = self.client.get(
            reverse('profiles:tp_team_profile', 
            args=(self.team_profile1.reg_no,)), follow=True)
        self.assertEqual(response.status_code, 200)
    
        self.assertEqual(RequestTimeSeries.objects.all().count(), 1)
        
        
        # First RequestTimeSeries
        rts = RequestTimeSeries.objects.all().order_by('created_date')[0]
        
        self.assertEqual(rts.email, 'john@gmail.com')
        self.assertEqual(rts.is_logged_in_as_email, '')
        self.assertEqual(rts.is_logged_in_as, False)
        self.assertEqual(rts.os, 'Android')
        self.assertEqual(rts.device_type, 'MOBILE')
        self.assertEqual(rts.browser, 'Chrome')
        self.assertEqual(rts.ip_address, "127.0.0.1")
        self.assertEqual(rts.view_name, "profiles:tp_team_profile")
        self.assertEqual(rts.request_method, "GET")
        self.assertEqual(rts.status_code, 200)
        self.assertEqual(rts.location_update, False)
        self.assertEqual(rts.map_loaded, False)
        self.assertEqual(rts.is_api, False)
        self.assertEqual(rts.was_throttled, False)
        self.assertTrue(rts.response_time < 0.500)
        self.assertEqual(rts.reg_no, self.team_profile1.reg_no)

    def test_if_hijacks_processes_are_loggeg_correctley(self):

        #### Hijack top profile user 2
        response = self.client.get(
                reverse(
                    'hijack:login_with_reg_no', 
                    args=(self.top_profile2.reg_no,)), 
                follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/')
        self.assertEqual(response.template_name[0], 'home.html')

        #### Release hijack of top profile user 2
        response = self.client.get(reverse('hijack:release_login_as'), follow=True)

        self.assertEqual(RequestTimeSeries.objects.all().count(), 4)


        # First RequestTimeSeries
        rts = RequestTimeSeries.objects.all().order_by('created_date')[0]
        
        self.assertEqual(rts.email, 'jack@gmail.com')
        self.assertEqual(rts.is_logged_in_as_email, 'john@gmail.com')
        self.assertEqual(rts.is_logged_in_as, True)
        self.assertEqual(rts.os, 'Android')
        self.assertEqual(rts.device_type, 'MOBILE')
        self.assertEqual(rts.browser, 'Chrome')
        self.assertEqual(rts.ip_address, "127.0.0.1")
        self.assertEqual(rts.view_name, 'hijack:login_with_reg_no')
        self.assertEqual(rts.request_method, 'GET')
        self.assertEqual(rts.status_code, 302)
        self.assertEqual(rts.location_update, False)
        self.assertEqual(rts.map_loaded, False)
        self.assertEqual(rts.is_api, False)
        self.assertEqual(rts.was_throttled, False)
        self.assertTrue(rts.response_time < 0.500)
        self.assertEqual(rts.reg_no, self.top_profile2.reg_no)

        # Third RequestTimeSeries
        rts = RequestTimeSeries.objects.all().order_by('created_date')[1]
        
        self.assertEqual(rts.email, 'jack@gmail.com')
        self.assertEqual(rts.is_logged_in_as_email, 'john@gmail.com')
        self.assertEqual(rts.is_logged_in_as, True)
        self.assertEqual(rts.os, 'Android')
        self.assertEqual(rts.device_type, 'MOBILE')
        self.assertEqual(rts.browser, 'Chrome')
        self.assertEqual(rts.ip_address, "127.0.0.1")
        self.assertEqual(rts.view_name, 'home')
        self.assertEqual(rts.request_method, 'GET')
        self.assertEqual(rts.status_code, 200)
        self.assertEqual(rts.location_update, False)
        self.assertEqual(rts.map_loaded, False)
        self.assertEqual(rts.is_api, False)
        self.assertEqual(rts.was_throttled, False)
        self.assertTrue(rts.response_time < 0.500)
        self.assertEqual(rts.reg_no, 0)
        
        # Fouth RequestTimeSeries
        rts = RequestTimeSeries.objects.all().order_by('created_date')[2]
        
        self.assertEqual(rts.email, 'john@gmail.com')
        self.assertEqual(rts.is_logged_in_as_email, '')
        self.assertEqual(rts.is_logged_in_as, False)
        self.assertEqual(rts.os, 'Android')
        self.assertEqual(rts.device_type, 'MOBILE')
        self.assertEqual(rts.browser, 'Chrome')
        self.assertEqual(rts.ip_address, "127.0.0.1")
        self.assertEqual(rts.view_name, 'hijack:release_login_as')
        self.assertEqual(rts.request_method, 'GET')
        self.assertEqual(rts.status_code, 302)
        self.assertEqual(rts.location_update, False)
        self.assertEqual(rts.map_loaded, False)
        self.assertEqual(rts.is_api, False)
        self.assertEqual(rts.was_throttled, False)
        self.assertTrue(rts.response_time < 0.500)
        self.assertEqual(rts.reg_no, 0)

        # Fifth RequestTimeSeries
        rts = RequestTimeSeries.objects.all().order_by('created_date')[3]
        
        self.assertEqual(rts.email, 'john@gmail.com')
        self.assertEqual(rts.is_logged_in_as_email, '')
        self.assertEqual(rts.is_logged_in_as, False)
        self.assertEqual(rts.os, 'Android')
        self.assertEqual(rts.device_type, 'MOBILE')
        self.assertEqual(rts.browser, 'Chrome')
        self.assertEqual(rts.ip_address, "127.0.0.1")
        self.assertEqual(rts.view_name, 'home')
        self.assertEqual(rts.request_method, 'GET')
        self.assertEqual(rts.status_code, 200)
        self.assertEqual(rts.location_update, False)
        self.assertEqual(rts.map_loaded, False)
        self.assertEqual(rts.is_api, False)
        self.assertEqual(rts.was_throttled, False)
        self.assertTrue(rts.response_time < 0.500)
        self.assertEqual(rts.reg_no, 0)
 
    def test_if_requests_that_return_404_will_be_logged_to_db(self):
        
        """ Check if 404 will be logged """
        response = self.client.get(
            reverse('profiles:tp_team_profile', 
            args=(1,)), follow=True)
        self.assertEqual(response.status_code, 404)
    
        self.assertEqual(RequestTimeSeries.objects.all().count(), 1)
        
        # First RequestTimeSeries
        rts = RequestTimeSeries.objects.all().order_by('created_date')[0]
        
        self.assertEqual(rts.email, 'john@gmail.com')
        self.assertEqual(rts.is_logged_in_as_email, '')
        self.assertEqual(rts.is_logged_in_as, False)
        self.assertEqual(rts.os, 'Android')
        self.assertEqual(rts.device_type, 'MOBILE')
        self.assertEqual(rts.browser, 'Chrome')
        self.assertEqual(rts.ip_address, "127.0.0.1")
        self.assertEqual(rts.view_name, "profiles:tp_team_profile")
        self.assertEqual(rts.request_method, "GET")
        self.assertEqual(rts.status_code, 404)
        self.assertEqual(rts.location_update, False)
        self.assertEqual(rts.map_loaded, False)
        self.assertEqual(rts.is_api, False)
        self.assertEqual(rts.was_throttled, False)
        self.assertTrue(rts.response_time < 0.500)
        self.assertEqual(rts.reg_no, 1)

    def test_if_unlogged_in_user_requests_are_being_logged_to_db(self):

        # First delete all RequestTimeSeries
        RequestTimeSeries.objects.all().delete()

        # Unlogged in user
        self.client = Client()

        """ Unlogged in user """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
        self.assertEqual(RequestTimeSeries.objects.all().count(), 1)
        
        rts = RequestTimeSeries.objects.all().order_by('created_date')[0]
        
        self.assertEqual(rts.email, 'AnonymousUser')
        self.assertEqual(rts.is_logged_in_as_email, '')
        self.assertEqual(rts.is_logged_in_as, False)
        self.assertEqual(rts.os, 'Android')
        self.assertEqual(rts.device_type, 'MOBILE')
        self.assertEqual(rts.browser, 'Chrome')
        self.assertEqual(rts.ip_address, "127.0.0.1")
        self.assertEqual(rts.view_name, "home")
        self.assertEqual(rts.request_method, "GET")
        self.assertEqual(rts.status_code, 200)
        self.assertEqual(rts.location_update, False)
        self.assertEqual(rts.map_loaded, False)
        self.assertEqual(rts.is_api, False)
        self.assertEqual(rts.was_throttled, False)
        self.assertTrue(rts.response_time < 0.500)
        self.assertEqual(rts.reg_no, 0)
           
# TODO We skip this intentionally
class ApiRequestTimeSeriesTestCase(APITestCase, InitialUserDataMixin):
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
        
        self.create_initial_user_data_with_superuser()
        
        
        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save() 

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
    def test_if_requests_with_reg_no_will_be_logged_to_db(self):
    
        response = self.client.get(
            reverse('api:tp_team_profile_dashboard', 
            args=(self.team_profile1.reg_no,)))
        self.assertEqual(response.status_code, 200)
            
        self.assertEqual(RequestTimeSeries.objects.all().count(), 1)
        
        rts = RequestTimeSeries.objects.all().order_by('created_date')[0]
        
        self.assertEqual(rts.email, 'john@gmail.com')
        self.assertEqual(rts.is_logged_in_as_email, '')
        self.assertEqual(rts.is_logged_in_as, False)
        self.assertEqual(rts.os, 'Android')
        self.assertEqual(rts.device_type, 'MOBILE')
        self.assertEqual(rts.browser, 'Chrome')
        self.assertEqual(rts.ip_address, "127.0.0.1")
        self.assertEqual(rts.view_name, "api:tp_team_profile_dashboard")
        self.assertEqual(rts.request_method, "GET")
        self.assertEqual(rts.status_code, 200)
        self.assertEqual(rts.location_update, False)
        self.assertEqual(rts.map_loaded, False)
        self.assertEqual(rts.is_api, True)
        self.assertEqual(rts.was_throttled, False)
        self.assertTrue(rts.response_time < 0.500)
        self.assertEqual(rts.reg_no, self.team_profile1.reg_no)

    def test_if_requests_that_return_404_will_be_logged_to_db(self):
                
        response = self.client.get(
            reverse('api:tp_team_profile_dashboard', 
            args=(1,)))
        self.assertEqual(response.status_code, 404)
            
        self.assertEqual(RequestTimeSeries.objects.all().count(), 1)
        
        rts = RequestTimeSeries.objects.all().order_by('created_date')[0]
        
        self.assertEqual(rts.email, 'john@gmail.com')
        self.assertEqual(rts.is_logged_in_as_email, '')
        self.assertEqual(rts.is_logged_in_as, False)
        self.assertEqual(rts.os, 'Android')
        self.assertEqual(rts.device_type, 'MOBILE')
        self.assertEqual(rts.browser, 'Chrome')
        self.assertEqual(rts.ip_address, "127.0.0.1")
        self.assertEqual(rts.view_name, "api:tp_team_profile_dashboard")
        self.assertEqual(rts.request_method, "GET")
        self.assertEqual(rts.status_code, 404)
        self.assertEqual(rts.location_update, False)
        self.assertEqual(rts.map_loaded, False)
        self.assertEqual(rts.is_api, True)
        self.assertEqual(rts.was_throttled, False)
        self.assertTrue(rts.response_time < 0.500)
        self.assertEqual(rts.reg_no, 1)

    def test_if_unlogged_in_user_requests_are_being_logged_to_db(self):

        # First delete all RequestTimeSeries
        RequestTimeSeries.objects.all().delete()

        # Unlogged in user
        self.client = APIClient()

        """ Unlogged in user """
        response = self.client.get(
            reverse('api:tp_team_profile_dashboard', 
            args=(self.team_profile1.reg_no,)))
        self.assertEqual(response.status_code, 401)
            
        self.assertEqual(RequestTimeSeries.objects.all().count(), 1)
        
        rts = RequestTimeSeries.objects.all().order_by('created_date')[0]
        
        self.assertEqual(rts.email, 'AnonymousUser')
        self.assertEqual(rts.is_logged_in_as_email, '')
        self.assertEqual(rts.is_logged_in_as, False)
        self.assertEqual(rts.os, 'Android')
        self.assertEqual(rts.device_type, 'MOBILE')
        self.assertEqual(rts.browser, 'Chrome')
        self.assertEqual(rts.ip_address, "127.0.0.1")
        self.assertEqual(rts.view_name, "api:tp_team_profile_dashboard")
        self.assertEqual(rts.request_method, "GET")
        self.assertEqual(rts.status_code, 401)
        self.assertEqual(rts.location_update, False)
        self.assertEqual(rts.map_loaded, False)
        self.assertEqual(rts.is_api, True)
        self.assertEqual(rts.was_throttled, False)
        self.assertTrue(rts.response_time < 0.500)
        self.assertEqual(rts.reg_no, self.team_profile1.reg_no)


class AdminRequestTimeSeriesTestCase(TestCase):
    def setUp(self):
        
        #Create a super user with email john@gmail.com
        self.user = create_new_user('super') 
        
        #Create a user with email jack@gmail.com
        self.user2 = create_new_user('jack')

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
        
        # My client #
        self.client = Client()
        self.client.login(username='john@gmail.com', password='secretpass')
        
    def test_if_admin_requests_are_not_logged_in_the_db(self):        
        
        app_label = 'assignments'
        my_model = 'report'
        url_name = 'admin:%s_%s_add' % (app_label, my_model)
        
        reverse_url = reverse(url_name)
                
        response = self.client.get(reverse_url)
            
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(RequestTimeSeries.objects.all().count(), 0)
        
