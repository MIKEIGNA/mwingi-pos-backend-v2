import re
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin
from django.http.response import Http404
from django.conf import settings
import logging
from mylogentries.models import RequestTimeSeries

class UserAgentParser():
    """
    Parses a user agent string and extracts os, device type and browser name
    
    Most of the search criteria is outlined in the following link
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Browser_detection_using_the_user_agent 
    http://www.useragentstring.com/pages/useragentstring.php?typ=Browser
    """
    def __init__(self, user_agent):
        self.user_agent = user_agent
        self.OS = ["Windows", "Android", "Amazon Fire", "Linux", "Mac OS X", "Other"]
        self.DEVICE = ["PC", "MOBILE",]
        self.BROWSER = ["Firefox", "Chromium", "Edge", "Chrome", "Safari", "Opera", "IE", "Other"]
        
    def get_user_agent_props(self):
        # If usser_agent string is empty, return a list of emtpy strings
        if not self.user_agent:
            return ["", "", ""]
        
        os = self.OS[self.parse_os()]
        device = self.DEVICE[self.parse_device()]
        browser = self.BROWSER[self.parse_browser()]
        
        return [os, device, browser]
    
    def parse_browser(self):
        """ Returns the browser code """
        
        if re.search("Firefox/", self.user_agent, re.IGNORECASE):
            if not re.search("Seamonkey/", self.user_agent, re.IGNORECASE):
                return 0
           
        elif re.search("Chrome/", self.user_agent, re.IGNORECASE):
            if re.search("Chromium/", self.user_agent, re.IGNORECASE):
                return 1
            
            elif re.search("Edge/", self.user_agent, re.IGNORECASE):
                return 2
            
            else:
                return 3
        
        # To avoid confusion, Safari should be checked after chrome has been checked
        elif re.search("Safari/", self.user_agent, re.IGNORECASE):
            return 4
            
        elif re.search("OPR/", self.user_agent, re.IGNORECASE) or re.search("Opera/", self.user_agent, re.IGNORECASE):
            return 5
            
        elif re.search("MSIE", self.user_agent, re.IGNORECASE):
            return 6
        
        return 7
    
    def parse_device(self):
        """ Returns the device type code """
        if re.search("mobi", self.user_agent, re.IGNORECASE):
            return 1
        else:
            return 0
    
    def parse_os(self):
        """ Returns the os code """
        
        if re.search("Windows NT", self.user_agent, re.IGNORECASE):
            return 0
        
        elif re.search("Linux", self.user_agent, re.IGNORECASE):
            if re.search("Android", self.user_agent, re.IGNORECASE):
                return 1
            elif re.search("KFAPWI", self.user_agent, re.IGNORECASE):
                return 2
            else:
                return 3
        
        elif re.search("Mac OS X", self.user_agent, re.IGNORECASE):
            return 4
        
        else:
            return 5

class AuditLoggingMiddleware(MiddlewareMixin):
    
    def process_request(self, request):
        
        request._request_time = datetime.now()
        
    def log_to_file(self, request_data_dict):


        # Check if there is a user making requests on behalf of another
        if request_data_dict['request_logged_in_as_user']:
            logged_in_as_email = request_data_dict['request_logged_in_as_user']
        else:
            logged_in_as_email = None

        # Creating logging message
        logging_msg = '{} {} {} "{} {} {}" {} {} {} "{}" "{}" {} {} {}'.format(
                request_data_dict['request_meta_ip'],
                request_data_dict['request_meta_user'],
                request_data_dict['request_user'],
                request_data_dict['request_method'], 
                request_data_dict['request_get_full_path'], 
                request_data_dict['request_meta_protocal'],
                request_data_dict['response_status_code'],
                request_data_dict['response_content_length'],
                request_data_dict['invalid_msg'],
                request_data_dict['request_meta_referer'],
                request_data_dict['request_meta_user_agent'],
                request_data_dict['request_port'],
                request_data_dict['response_time'],
                logged_in_as_email
                )
        
        # Get an instance of a logger
        logger_name = 'page_views_logger' if not settings.TESTING_MODE else 'test_page_views_logger'
        
        logger = logging.getLogger(logger_name)
        
        logger.info(logging_msg)
        
    def log_to_db(self, request_data_dict):
        
        """ 
        If resolver_match in None, most likely it's an error page so we log it
        as an error
        """
        if request_data_dict['resolver_match']:
            app_name = request_data_dict['resolver_match'].app_names
            url_name = request_data_dict['resolver_match'].url_name
            object_reg_no = request_data_dict['resolver_match'].kwargs.get('reg_no', 0)
            
            """
            Before using reg_no with a query or insert, make sure it's not too big
            """
            if int(object_reg_no) > 6000000000000:
                object_reg_no = 100
            
            
        else:
            app_name = ["error",]
            url_name = request_data_dict['request_get_full_path']
            object_reg_no = 0
            
            """
            If the url_name has a "." most likely it's a link to static media
            so we dont log that.
            Also, when there url_name is empty, there is no need of logging.
            """ 
            if not url_name or "." in url_name:
                return False
            

        response_time = request_data_dict['response_time']
        
        # Convert response_time to milli seconds
        response_time = (response_time.seconds * 1000) + int(response_time.microseconds/1000)
        
        # Convert new response time to seconds
        response_time = response_time/1000
        
        is_api = False
        
        if app_name:
            
            app_name = app_name[0]
            
            # If app_name is "admin", we do not log
            if app_name == "admin":
                return True
            
            if app_name == "api":
                is_api = True
                
            full_url_name = "{}:{}".format(app_name, url_name)
            
        else:
            full_url_name = "{}".format(url_name)
            
            
#        print("full url name >> ", full_url_name)
        
        
        if settings.TESTING_MODE:
            """
            During testing, user_agent is always empty so we provide our own
            """
            
            testing_user_agent = "Mozilla/5.0 (Linux; Android 7.0; SM-G892A Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/67.0.3396.87 Mobile Safari/537.36"
            request_data_dict['request_meta_user_agent'] = testing_user_agent
        
        
        
        
        user_agent = request_data_dict['request_meta_user_agent']
        
        
        
        user_agent_props =UserAgentParser(user_agent).get_user_agent_props()
        
#        print(user_agent)
#        
#        print(user_agent_props)
#        print()
        
        if request_data_dict['request_user']:
            email = request_data_dict['request_user']
        else:
            email = "NoUser"
            
            
        RequestTimeSeries.objects.create(
                        email = email,
                        is_logged_in_as_email= request_data_dict['request_logged_in_as_user'],
                        os = user_agent_props[0],
                        device_type = user_agent_props[1],
                        browser = user_agent_props[2],
                        ip_address = request_data_dict['request_meta_ip'],
                        view_name = full_url_name,
                        request_method = request_data_dict['request_method'],
                        status_code = request_data_dict['response_status_code'],
                        is_api = is_api,
                        location_update = request_data_dict['location_update'],
                        map_loaded = request_data_dict['map_loaded'],
                        was_throttled = request_data_dict['was_throttled'],
                        response_time = response_time,
                        reg_no = object_reg_no
                        )
        
        
        
    
    def log_request(self, request, response_status_code, response_content_length):
        
        # Check if there is an invalid message that should be logged
        invalid_msg = request.invalid_msg if getattr(request, 'invalid_msg', None) else 'OK'
        
        # Check if this was a location update
        location_update = True if getattr(request, 'location_update', None) else False
        
        # Check if a map was loaded on this request
        map_loaded = True if getattr(request, 'map_loaded', None) else False
        
        
        payment_invalid_msg = request.payment_invalid_msg if getattr(request, 'payment_invalid_msg', None) else False
    
        if payment_invalid_msg:
            invalid_msg = payment_invalid_msg
            
        was_throttled = True if getattr(request, 'throttled', None) else False
        
        if was_throttled:
            invalid_msg = '"Request_throttled"'
        
        request_data_dict = {'request_meta_ip': request.META.get('REMOTE_ADDR', None),
                             'request_meta_user_agent': request.META.get('HTTP_USER_AGENT', None),
                             'request_meta_referer': request.META.get('HTTP_REFERER', None),
                             'request_meta_protocal': request.META.get('SERVER_PROTOCOL', None),
                             'request_meta_user': request.META.get('USER', None), 
                             'request_user': request.user if getattr(request, 'user', None) else '',
                             'request_logged_in_as_user': request.session.get('request_logged_in_as_user', ''),
                             'request_method': request.method,
                             'response_status_code': response_status_code,
                             'response_content_length': response_content_length,
                             'request_get_full_path': request.get_full_path(),
                             'request_port': request.get_port(),
                             'response_time':  datetime.now() - request._request_time,
                             'invalid_msg': invalid_msg,
                             'location_update': location_update,
                             'map_loaded': map_loaded,
                             'was_throttled': was_throttled,
                             'resolver_match': request.resolver_match,
                             }

        try:
            """ Logs request to db """
            
            self.log_to_db(request_data_dict)
            
        except:
            # Get an instance of a logger
            logger = logging.getLogger('page_critical_logger')
            logger.exception('Log to db Failed at "{}" for request "{}"'.format(datetime.now(), request.get_full_path()))
         
        
        try:
            """ Logs request to file """
            self.log_to_file(request_data_dict)
        except:
            # Get an instance of a logger
            logger = logging.getLogger('page_critical_logger')
            logger.exception('Log to file Failed at "{}" for request "{}"'.format(datetime.now(), request.get_full_path()))
        
        
            


                
 
    
        

    def process_response(self, request, response):
        """
        For you to insert a message(string) into the logfile, it must be a written as 
        1 word or must be inside a "".
           1 word examples:
               1. message
               2. this_is_my_message
           
           Inside a "" examples:
               1. '"This is my message"'
        """

        response_status_code = response.status_code
        
        try:
            response_content_length = [v for k, v in response.items() if k == 'Content-Length'][0]
        except:
            response_content_length = None
            
        
        """
        We ignore 304s because of the following reason.
        
        A 304 Not Modified response code indicates that the requested resource 
        has not been modified since the previous transmission. This typically 
        means there is no need to retransmit the requested resource to the client, 
        and a cached version can be used, instead.
        """
        if not response_status_code == 304:
            self.log_request(request, response_status_code, response_content_length)
        
        return response

    def process_exception(self, request, exception):

        accepted_exceptions = [Http404,]
        
        if not type(exception) in accepted_exceptions:
            # Get an instance of a logger
            logger = logging.getLogger('page_critical_logger')
            logger.exception(exception)
        
        return None

