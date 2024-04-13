import re
from functools import wraps
import zlib
import time

from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy


class ApiThrottleException(HttpResponse):
    status_code = 429 

class ThrottledException(ValidationError):
    #status_code = 429
    pass

# Extend the expiration time by a few seconds to avoid misses.
EXPIRATION_FUDGE = 5

_PERIODS = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 24 * 60 * 60,
}

_SIMPLE_KEYS = ['user', 'ip', 'anon', 'login', 'location', 'api_user', 'api_ip', 
                'api_login', 'tracker_create', 'api_location', 'api_reg_no', 
                'normal_class_method']

rate_re = re.compile('([\d]+)/([\d]*)([smhd])?')
   
    
class Throttle():
    def __init__(self, request=None, view=None, scope=None, rate=None, kwargs=None, alt_name=None):
        """
        request => This is the request from the view
        view => This is the view's function that is being used to make a request
        scope => Respresents the type of user making the request
        rate => Represents the rate that should be used in throttling
        alt_name => This is used to differenciate views that are in the same module
        """
                    
        if not scope:
            raise ImproperlyConfigured("scope must be provided for {}".format(self.__class__.__name__))
            
        if not scope in _SIMPLE_KEYS:
            raise ImproperlyConfigured('Unknown scope value : {}'.format(scope))
        
        if not rate:
            raise ImproperlyConfigured("rate must be provided for {}".format(self.__class__.__name__))
            
        
        self.original_request = request
        
        """
        If a request is coming from the web or api, it's stored in a variable
        called 'request.request' . but when we are testing, it is stored in 'request'
        """
        self.request = request if isinstance(request, HttpRequest) else request.request
        
        self.view = view
        self.scope = scope
        self.rate = rate
        
        self.request_limit, self.duration = self.parse_rate()
        
        if alt_name:
            self.view_name = '.'.join((self.view.__module__,alt_name, self.view.__name__))
        else:
            self.view_name = '.'.join((self.view.__module__, self.view.__name__))
            

        self.kwargs = kwargs
        self.request_type = None
        
                
    def is_ratelimited(self):
        """
        Returns True if the request should be blocked due to execeding the number of 
        requests allowed within the specified throttle rate and Fasle other wise
        """
        
        try:
            if self.scope == 'anon':
                """
                Dont throttle authenticated users when scope is 'anon'
                """
                if self.request.user.is_authenticated:
                    return False
        except:
            pass
                    
        usage = self.get_usage_count()
        
        block = usage.get('num_requests') > usage.get('request_limit')
        
        #print('\n\n Desi')
        #print(usage)
        if block:
            
            """ 
            Insert the Throttled View message into the request so that it
            can be logged.
            """
            is_api = True if getattr(self.request, '_request', None) else False
            
            if is_api:
                self.request._request.throttled = "Throttled View"
            else:
                self.request.throttled = "Throttled View"
            
            #print('We should block\n')
            return True, self.request_type
        
        else:
            #print('No blocking\n')
            return False
        
    def get_usage_count(self):
        
        """
        Returns a dict with information about how many request have been made, 
        the number of requst limit and time left before throttling reset
        
        {'num_requests': 6, 'request_limit': 5, 'time_left': 33}
        """
                        
        cache = caches['default']
        
        cache_key = self.make_cache_key()
        time_left = self._get_timer() - int(time.time())
        initial_value = 1 
        
        added = cache.add(cache_key, initial_value, self.duration + EXPIRATION_FUDGE)
        
        if added:
            num_requests = initial_value
        else:
            try:
                num_requests = cache.incr(cache_key)
            except ValueError:
                num_requests = initial_value

        
        return {'num_requests': num_requests, 'request_limit': self.request_limit, 'time_left': time_left}
    
    def clean_reg(self, reg_no):
        """
        Limits reg_no chars to 15 if there more than 15
        """
        
        if reg_no:
            str_reg = str(reg_no)
            
            if len(str_reg) > 15:
                return str_reg[:15]
            
            else:
                return str_reg
        else:
            return reg_no
    
    def get_ident(self):
        if self.scope == 'user':
            scope_value = self.user_or_ip()
            
        elif self.scope == 'ip' or self.scope == 'anon':
            scope_value = self.request.META.get('REMOTE_ADDR', None)
            
        elif self.scope == 'login':
            scope_value = self.login_username()
            
        elif self.scope == 'api_user':
            scope_value = self.user_or_ip()
            self.request_type = 'api'
            
        elif self.scope == 'api_ip' or self.scope == 'anon':
            scope_value = self.request.META.get('REMOTE_ADDR', None)
            self.request_type = 'api'
            
        elif self.scope == 'api_login':
            scope_value = self.api_login_username()
            self.request_type = 'api'
            
        elif self.scope == 'api_location':
            reg_no = self.kwargs.get('reg_no', None)
            scope_value = self.clean_reg(reg_no)
            
            self.request_type = 'api'
            
        elif self.scope == 'api_reg_no':
            reg_no = self.kwargs.get('reg_no', None)
            scope_value = self.clean_reg(reg_no)

            self.request_type = 'api'
            
        elif self.scope == 'location':
            reg_no = self.kwargs.get('reg_no', None)
            scope_value = self.clean_reg(reg_no)
             
        elif self.scope == 'tracker_create':
            reg_no = self.kwargs.get('reg_no', None)
            scope_value = self.clean_reg(reg_no)

        elif self.scope == 'normal_class_method':
            reg_no = self.kwargs.get('reg_no', None)
            scope_value = self.clean_reg(reg_no)

            self.request_type = 'normal_method'

        return scope_value
    
    def make_cache_key(self):   
        """
        Generates and returns a cache key for the view funcion:
        Example --> accounts.views.signup.post_127.0.0.1_5/60s1531207565
        
        """
        
        short_cache_key = '{}_{}_'.format(self.view_name, self.get_ident())
        
        safe_rate = '%d/%ds' % (self.request_limit, self.duration)
        window = self._get_timer()
        cache_key = short_cache_key + safe_rate + str(window)

        return cache_key
    
    def _get_timer(self):

        ts = int(time.time())
        if self.duration == 1:
            
            return ts
        if not isinstance(self.rate, bytes):
            self.rate = self.rate.encode('utf-8')
        w = ts - (ts % self.duration) + (zlib.crc32(self.rate) % self.duration)
        if w < ts:
            
            return w + self.duration
        
        return w
    
    def parse_rate(self):
        """
        Given the request rate string, return a two tuple of:
        <allowed number of requests>, <period of time in seconds>
        
        It can read rates provided in seconds, minutes, hours and days. 
        Example : 5/s, 5/m, 5/h and 5/d
        """
    
        count, multi, period = rate_re.match(self.rate).groups()
        request_limit = int(count)
        if not period:
            period = 's'
        duration = _PERIODS[period.lower()]
        if multi:
            duration = duration * int(multi)
        return request_limit, duration
        
    def user_or_ip(self):
        try:

            if self.request.user.is_authenticated:
                user_or_ip = self.request.user.pk
            else:
                user_or_ip = self.request.META.get('REMOTE_ADDR', None)

        except:
            user_or_ip = self.request.META.get('REMOTE_ADDR', None)
        
        return user_or_ip
        
    def login_username(self):
        form = self.original_request.get_form() 
        fields = form.data.dict()
        username = fields.get('username', None)
                
        return username
    
    def api_login_username(self):
        return self.request.data.get('username', None)
             
        
        
def ratelimit(scope=None, rate=None, alt_name=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view_func(request, *args, **kwargs):
            """
            # _wrapped_view_func must have the same parameters as the function
            # that is being decorated by the 'ratelimit' decorator
            """
            limit = Throttle(request, view_func, scope, rate, kwargs, alt_name).is_ratelimited()
       
            if limit:
                if limit[1] == 'api' or limit[1] == 'normal_method': 
                    """
                    This is used in the api or a normal method during throttlng
                    
                    This is used to notify the api view that it has been throttled
                    so that it can raise it's own custom error
                    """
                    kwargs['request_throttled'] = True
                        
                    return view_func(request, *args, **kwargs)
                    
                else:
                    block_url = getattr(request, 'block_url', None)
                    
                    if block_url:
                    
                        return HttpResponseRedirect(reverse_lazy(block_url))
                    else:
                        raise ImproperlyConfigured("block_url must be set for {}".format(view_func.__name__))
                
            return view_func(request, *args, **kwargs)
            
        return _wrapped_view_func
    return decorator
