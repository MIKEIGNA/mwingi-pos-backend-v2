from core.test_utils.custom_testcase import TestCase
from core.test_utils.log_reader import get_log_content

from mysettings.models import MySetting
from django.test import Client
from django.urls import reverse

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from core.test_utils.create_user import create_new_user

def is_log_line_correct(log_line):
    return len(log_line) == 14

def is_date(log_line):
    date = log_line['date'].split('-')
    return len(date) == 3

def is_time(log_line):
    date = log_line['time'].split(':')
    return len(date) == 3

def is_ip(log_line):
    ip = log_line['ip'].split('.')
    return len(ip) == 4

def is_meta_user(log_line):
    meta_user = log_line['meta_user']
    return meta_user == 'None'

def is_user(log_line):
    user = log_line['user']
    return len(user) > 7

def is_method(log_line):
    method = log_line['method']
    return method == 'GET' or method == 'POST' or method == 'PUT' or method == 'DELETE' 

def is_full_path(log_line):
    full_path = log_line['full_path']
    return len(full_path) > 5 or full_path == '/' 

def is_status_code(log_line):
    status_code = log_line['status_code']
    return type(int(status_code)) == int

def is_content_length(log_line):
    content = log_line['content_length']
    return type(int(content)) == int

def is_process(log_line):
    process = log_line['process']
    return process == 'OK'

def is_referer(log_line):
    referer = log_line['referer']
    return referer == 'None'

def is_user_agent(log_line):
    user_agent = log_line['user_agent']
    return len(user_agent) > 20
    
def is_port(log_line):
    port = log_line['port']
    return type(int(port)) == int

def is_response_time(log_line):
    response_time = log_line['response_time'].split(':')
    return len(response_time) == 3

class TestFileLoggingTestCase(TestCase):
    
    def setUp(self):
        
        #Create a user with email john@gmail.com
        self.user = create_new_user('john') 
        
        #Create a user with email jack@gmail.com
        create_new_user('jack')
        
        """ Turn off maintenance mode"""
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
        
        """ My client """
        self.client = Client()
    
    def test_if_request_are_being_logged_(self):

        data = {'username': 'john@gmail.com','password': 'secretpass'}
        
        response = self.client.post(reverse('api:token'), data, format='json')                                                    
        self.assertEqual(response.status_code, 200)

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        """ Confire that the user is logged in """
        response = self.client.get(reverse('api:tp_edit_profile'))
        self.assertEqual(response.status_code, 200)
        
        """ Check if the 2 requests were logged """
        data = get_log_content()
        
        self.assertEqual(len(data), 2)
        
        """ Check the first logline """
        self.assertEqual(data[0]['method'], 'POST')
        
        log_line = data[0]
        
        self.assertTrue(is_log_line_correct(log_line))
        self.assertTrue(is_date(log_line))
        self.assertTrue(is_time(log_line))
        self.assertTrue(is_ip(log_line))
        self.assertTrue(is_meta_user(log_line))
        self.assertTrue(is_user(log_line))
        self.assertTrue(is_method(log_line))
        self.assertTrue(is_full_path(log_line))
        self.assertTrue(is_status_code(log_line))
        self.assertTrue(is_content_length(log_line))
        self.assertTrue(is_process(log_line))
        self.assertTrue(is_referer(log_line))
        self.assertTrue(is_user_agent(log_line))
        self.assertTrue(is_port(log_line))
        self.assertTrue(is_response_time(log_line))
        
        """ Check the second logline """
        self.assertEqual(data[1]['method'], 'GET')
        
        log_line = data[1]
        
        self.assertTrue(is_log_line_correct(log_line))
        self.assertTrue(is_date(log_line))
        self.assertTrue(is_time(log_line))
        self.assertTrue(is_ip(log_line))
        self.assertTrue(is_meta_user(log_line))
        self.assertTrue(is_user(log_line))
        self.assertTrue(is_method(log_line))
        self.assertTrue(is_full_path(log_line))
        self.assertTrue(is_status_code(log_line))
        self.assertTrue(is_content_length(log_line))
        self.assertTrue(is_process(log_line))
        self.assertTrue(is_referer(log_line))
        self.assertTrue(is_user_agent(log_line))
        self.assertTrue(is_port(log_line))
        self.assertTrue(is_response_time(log_line))
