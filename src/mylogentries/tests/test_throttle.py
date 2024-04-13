from django.test import Client
from django.core.cache import cache
from django.test import RequestFactory
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from core.my_throttle import Throttle
from core.test_utils.custom_testcase import TestCase
from core.my_throttle import ratelimit
from core.test_utils.create_user import create_new_user

from mysettings.models import MySetting





rf = RequestFactory()


""" First test my throttle values in the settings file """
class MyThrottleSettingsValuesTests(TestCase):
    def setUp(self):
        pass
 
    def test_if_my_throttle_values_in_the_settings_file_are_correct(self):
        """ Test if my throttle values in the settings file are correct """
        
        self.assertEqual(len(settings.THROTTLE_RATES ), 48)   


# TODO We skip this intentionally
class RatelimitTests(TestCase):
    def setUp(self):
        cache.clear()
        
        self.factory = RequestFactory()
            
    def test_for_error_when_scope_is_not_provided(self):
        """
        Test for error when scope is not provided
        """
        @ratelimit(rate='5/m')
        def view(request):
            return True
        
        request = self.factory.get('/')
        with self.assertRaises(ImproperlyConfigured):
            view(request)
            
    def test_for_error_when_rate_is_not_provided(self):
        @ratelimit(scope='ip')
        def view(request):
            return True

        request = self.factory.get('/')
        with self.assertRaises(ImproperlyConfigured):
            view(request)
    

class SetUpMixin:
    def setUp(self):
        cache.clear()
        
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
       
      
# TODO We skip this intentionally
class RatelimitTestCase(SetUpMixin, TestCase):
    
    def test_if_user_scope_is_working(self):
        """
        Ensure user scope is working
        """
        
        # Create an instance of a GET request.
        request = self.factory.get('/', {'foo': 'a'})
        request.user = self.user
        
        @ratelimit(scope='user', rate='5/m')
        def view(request):
            return True
        
        request.block_url = 'accounts_too_many_requests'
        
        for i in range(5):
            self.assertEqual(view(request), True)
                  
        """ Ensure the next request billing/too_many_requests.html is loaded """ 
        response = view(request)
            
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/too_many_requests/')
    
    def test_if_user_scope_is_working_for_authenticated_users(self):
        """
        Ensure scope anon does not work on authenticated users
        """
        # Create an instance of a GET request.
        request = self.factory.get('/', {'foo': 'a'})
        request.user = self.user
        
        @ratelimit(scope='user', rate='5/m')
        def view(request):
            return True
        
        request.block_url = 'accounts_too_many_requests'
        
        for i in range(5):
            self.assertEqual(view(request), True)
            
        """ Ensure the next request billing/too_many_requests.html is loaded """ 
        response = view(request)
            
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/too_many_requests/')
            
    def test_if_user_scope_is_working_for_non_authenticated(self):
        """
        Ensure scope anon does not work on authenticated users
        """
        # Create an instance of a GET request.
        request = self.factory.get('/', {'foo': 'a'})
        
        @ratelimit(scope='user', rate='5/m')
        def view(request):
            return True
        
        request.block_url = 'accounts_too_many_requests'
        
        for i in range(5):
            self.assertEqual(view(request), True)
            
        """ Ensure the next request billing/too_many_requests.html is loaded """ 
        response = view(request)
            
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/too_many_requests/')
            
    
    def test_if_ip_scope_is_working_for_authenticated_users(self):
        """
        Ensure scope anon does not work on authenticated users
        """
        # Create an instance of a GET request.
        request = self.factory.get('/', {'foo': 'a'})
        request.user = self.user
        
        @ratelimit(scope='ip', rate='5/m')
        def view(request):
            return True
        
        request.block_url = 'accounts_too_many_requests'
        
        for i in range(5):
            self.assertEqual(view(request), True)
            
        """ Ensure the next request billing/too_many_requests.html is loaded """ 
        response = view(request)
            
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/too_many_requests/')
            
    def test_if_ip_scope_is_working_for_non_authenticated(self):
        """
        Ensure scope anon does not work on authenticated users
        """
        # Create an instance of a GET request.
        request = self.factory.get('/', {'foo': 'a'})
        
        @ratelimit(scope='ip', rate='5/m')
        def view(request):
            return True
        
        request.block_url = 'accounts_too_many_requests'
        
        for i in range(5):
            self.assertEqual(view(request), True)
            
        """ Ensure the next request billing/too_many_requests.html is loaded """ 
        response = view(request)
            
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/too_many_requests/')
    
  
    def test_if_anon_scope_is_working_for_non_authenticated(self):
        """
        Ensure scope anon is working
        """
        # Create an instance of a GET request.
        request = self.factory.get('/', {'foo': 'a'})
        
        @ratelimit(scope='anon', rate='5/m')
        def view(request):
            return True
        
        request.block_url = 'accounts_too_many_requests'
        
        for i in range(5):
            self.assertEqual(view(request), True)
            
        """ Ensure the next request billing/too_many_requests.html is loaded """ 
        response = view(request)
                
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/too_many_requests/')

               
    def test_if_anon_scope_is_not_working_for_authenticated_users(self):
        """
        Ensure scope anon does not work on authenticated users
        """
        # Create an instance of a GET request.
        request = self.factory.get('/', {'foo': 'a'})
        request.user = self.user
        
        @ratelimit(scope='anon', rate='5/m')
        def view(request):
            return True
        
        for i in range(15):
            self.assertEqual(view(request), True)
            
    def test_for_error_when_wrong_scope_is_provided(self):
        """
        Ensure an errror is raised when wrong scope is provided
        """
        
        # Create an instance of a GET request.
        request = self.factory.get('/', {'foo': 'a'})
        request.user = self.user
        
        @ratelimit(scope='wrong_scope_value', rate='5/m')
        def view(request):
            return True
                        
        with self.assertRaises(ImproperlyConfigured):
            view(request)
            
            
    def test_for_error_when_block_url_is_not_set_on_the_view(self):
        """
        Ensure an errror is raised the view being throttled does not have
        block url
        """
        
        # Create an instance of a GET request.
        request = self.factory.get('/', {'foo': 'a'})
        request.user = self.user
        
        @ratelimit(scope='user', rate='5/m')
        def view(request):
            return True
        
        for i in range(5):
            self.assertEqual(view(request), True)
                        
        with self.assertRaises(ImproperlyConfigured):
            view(request)
      
class ThrottleSetUpMixinTestCase(TestCase):
    def setUp(self):
        cache.clear()
        
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
        self.request = self.factory.get('/', {'foo': 'a'})
        self.request.user = self.user
        
        self.scope = 'user'
        self.rate = '5/m'
        
        def view(request):
            return True
        
        """
        This line is does not do anything, it's there just to make make sure 
        def view funcion get's called and so that coverage tests for this test 
        passes to 100% 
        """
        view(self.request)
        
        self.view = view
        
    def test_authenticated_user(self):
        """
        Ensure user_or_ip returns a user's pk when a user is authenticated
        """
        scope = 'user'
        rate = '5/m'
            
        throttle = Throttle(self.request, self.view, scope, rate, {})
        
        self.assertEqual(throttle.parse_rate(), (5, 60)) # parse_rate() should be tested before is_ratelimited
        
        self.assertEqual(throttle.is_ratelimited(), False)
        """
        get_usage_count()
        
        num_requests == 2 because is_ratelimited() is called first which fills the 
        cache with 1 request
        """
        self.assertEqual(throttle.get_usage_count()['num_requests'], 2)
        self.assertEqual(throttle.get_usage_count()['request_limit'], 5)
        self.assertTrue( 'time_left' in throttle.get_usage_count())
        
        self.assertEqual(throttle.get_ident(), self.user.pk) 

        cache_key = f'mylogentries.tests.test_throttle.view_{self.user.pk}_5/60s'

        self.assertTrue(cache_key in throttle.make_cache_key())
        self.assertEqual(throttle.make_cache_key(), cache_key + str(throttle._get_timer()))

        self.assertTrue(throttle._get_timer() >  10000)
        
        self.assertEqual(throttle.user_or_ip(), self.user.pk)
     
    def test_authenticated_user_with_alt_name(self):
        """
        Ensure user_or_ip returns a user's pk when a user is authenticated
        """
        scope = 'user'
        rate = '5/m'
        alt_name = 'my_alto_name'
            
        throttle = Throttle(self.request, self.view, scope, rate, {}, alt_name)
        
        self.assertEqual(throttle.parse_rate(), (5, 60)) # parse_rate() should be tested before is_ratelimited
        
        self.assertEqual(throttle.is_ratelimited(), False)
        """
        get_usage_count()
        
        num_requests == 2 because is_ratelimited() is called first which fills the 
        cache with 1 request
        """
        self.assertEqual(throttle.get_usage_count()['num_requests'], 2)
        self.assertEqual(throttle.get_usage_count()['request_limit'], 5)
        self.assertTrue( 'time_left' in throttle.get_usage_count())
        
        self.assertEqual(throttle.get_ident(), self.user.pk) 

        cache_key = f'mylogentries.tests.test_throttle.my_alto_name.view_{self.user.pk}_5/60s'

        self.assertTrue(cache_key in throttle.make_cache_key())
        self.assertEqual(throttle.make_cache_key(), cache_key + str(throttle._get_timer()))
        
        self.assertTrue(throttle._get_timer() >  10000)
        
        self.assertEqual(throttle.user_or_ip(), self.user.pk) 
      
    
    def test_non_authenticated_user(self):
        """
        Ensure user_or_ip returns an ip address when a user is not authenticated
        """
        # Create an instance of a GET request.
        request = self.factory.get('/', {'foo': 'a'})
        
        scope = 'user'
        rate = '5/m'
            
        throttle = Throttle(request, self.view, scope, rate, {})
    
        self.assertEqual(throttle.parse_rate(), (5, 60)) # parse_rate() should be tested before is_ratelimited
        
        self.assertEqual(throttle.is_ratelimited(), False)
        """
        get_usage_count()
        
        num_requests == 2 because is_ratelimited() is called first which fills the 
        cache with 1 request
        """
        self.assertEqual(throttle.get_usage_count()['num_requests'], 2)
        self.assertEqual(throttle.get_usage_count()['request_limit'], 5)
        self.assertTrue( 'time_left' in throttle.get_usage_count())
        
        self.assertEqual(throttle.get_ident(), '127.0.0.1') 
        
        self.assertTrue('mylogentries.tests.test_throttle.view_127.0.0.1_5/60s' in throttle.make_cache_key())
        self.assertEqual(throttle.make_cache_key(), 'mylogentries.tests.test_throttle.view_127.0.0.1_5/60s' + str(throttle._get_timer()))
        
        self.assertTrue(throttle._get_timer() >  10000)
        
        self.assertEqual(throttle.user_or_ip(), '127.0.0.1')
        
    def test_authenticated_ip(self):
        """
        Ensure user_or_ip returns a user's pk when a user is authenticated
        """
        scope = 'ip'
        rate = '5/m'
            
        throttle = Throttle(self.request, self.view, scope, rate, {})

        self.assertEqual(throttle.parse_rate(), (5, 60)) # parse_rate() should be tested before is_ratelimited
        
        self.assertEqual(throttle.is_ratelimited(), False)
        """
        get_usage_count()
        
        num_requests == 2 because is_ratelimited() is called first which fills the 
        cache with 1 request
        """
        self.assertEqual(throttle.get_usage_count()['num_requests'], 2)
        self.assertEqual(throttle.get_usage_count()['request_limit'], 5)
        self.assertTrue( 'time_left' in throttle.get_usage_count())
        
        self.assertEqual(throttle.get_ident(), '127.0.0.1') 
        
        self.assertTrue('mylogentries.tests.test_throttle.view_127.0.0.1_5/60s' in throttle.make_cache_key())
        self.assertEqual(throttle.make_cache_key(), 'mylogentries.tests.test_throttle.view_127.0.0.1_5/60s' + str(throttle._get_timer()))
        
        self.assertTrue(throttle._get_timer() >  10000)
        
        self.assertEqual(throttle.user_or_ip(), self.user.pk)
          
    def test_non_authenticated_ip(self):
        """
        Ensure user_or_ip returns an ip address when a user is not authenticated
        """
        # Create an instance of a GET request.
        request = self.factory.get('/', {'foo': 'a'})
        
        scope = 'ip'
        rate = '5/m'
            
        throttle = Throttle(request, self.view, scope, rate, {})
    
    
        self.assertEqual(throttle.parse_rate(), (5, 60)) # parse_rate() should be tested before is_ratelimited
        
        self.assertEqual(throttle.is_ratelimited(), False)
        """
        get_usage_count()
        
        num_requests == 2 because is_ratelimited() is called first which fills the 
        cache with 1 request
        """
        self.assertEqual(throttle.get_usage_count()['num_requests'], 2)
        self.assertEqual(throttle.get_usage_count()['request_limit'], 5)
        self.assertTrue( 'time_left' in throttle.get_usage_count())
        
        self.assertEqual(throttle.get_ident(), '127.0.0.1') 
        
        self.assertTrue('mylogentries.tests.test_throttle.view_127.0.0.1_5/60s' in throttle.make_cache_key())
        self.assertEqual(throttle.make_cache_key(), 'mylogentries.tests.test_throttle.view_127.0.0.1_5/60s' + str(throttle._get_timer()))
        
        self.assertTrue(throttle._get_timer() >  10000)
        
        self.assertEqual(throttle.user_or_ip(), '127.0.0.1')
        
    def test_authenticated_anon(self):
        """
        Ensure user_or_ip returns a user's pk when a user is authenticated
        """
        scope = 'anon'
        rate = '5/m'
            
        throttle = Throttle(self.request, self.view, scope, rate, {})

        
        self.assertEqual(throttle.parse_rate(), (5, 60)) # parse_rate() should be tested before is_ratelimited
        
        self.assertEqual(throttle.is_ratelimited(), False)
        """
        get_usage_count()
        
        num_requests == 2 because is_ratelimited() is called first which fills the 
        cache with 1 request
        """
        self.assertEqual(throttle.get_usage_count()['num_requests'], 1)
        self.assertEqual(throttle.get_usage_count()['request_limit'], 5)
        self.assertTrue( 'time_left' in throttle.get_usage_count())
        
        self.assertEqual(throttle.get_ident(), '127.0.0.1') 
        
        self.assertTrue('mylogentries.tests.test_throttle.view_127.0.0.1_5/60s' in throttle.make_cache_key())
        self.assertEqual(throttle.make_cache_key(), 'mylogentries.tests.test_throttle.view_127.0.0.1_5/60s' + str(throttle._get_timer()))
        
        self.assertTrue(throttle._get_timer() >  10000)
        
        self.assertEqual(throttle.user_or_ip(), self.user.pk)
        
    
    def test_non_authenticated_anon(self):
        """
        Ensure user_or_ip returns an ip address when a user is not authenticated
        """
        # Create an instance of a GET request.
        request = self.factory.get('/', {'foo': 'a'})
        
        scope = 'anon'
        rate = '5/m'
            
        throttle = Throttle(request, self.view, scope, rate, {})


        self.assertEqual(throttle.parse_rate(), (5, 60)) # parse_rate() should be tested before is_ratelimited
        
        self.assertEqual(throttle.is_ratelimited(), False)
        """
        get_usage_count()
        
        num_requests == 2 because is_ratelimited() is called first which fills the 
        cache with 1 request
        """
        self.assertEqual(throttle.get_usage_count()['num_requests'], 2)
        self.assertEqual(throttle.get_usage_count()['request_limit'], 5)
        self.assertTrue( 'time_left' in throttle.get_usage_count())
        
        self.assertEqual(throttle.get_ident(), '127.0.0.1') 
        
        self.assertTrue('mylogentries.tests.test_throttle.view_127.0.0.1_5/60s' in throttle.make_cache_key())
        self.assertEqual(throttle.make_cache_key(), 'mylogentries.tests.test_throttle.view_127.0.0.1_5/60s' + str(throttle._get_timer()))
        
        self.assertTrue(throttle._get_timer() >  10000)
        
        self.assertEqual(throttle.user_or_ip(), '127.0.0.1')
        
    def test_parse_rate_method2(self):
        tests = (
                ('100/s', (100, 1)),
                ('100/10s', (100, 10)),
                ('100/10', (100, 10)),
                ('100/m', (100, 60)),
                ('400/10m', (400, 600)),
                ('1000/h', (1000, 3600)),
                ('800/d', (800, 24 * 60 * 60)),
                )
        
        for i, o in tests:
            scope = 'user'
            rate = i
                        
            throttle = Throttle(self.request, self.view, scope, rate, {}).parse_rate()
            
            self.assertEqual(throttle, o)
         