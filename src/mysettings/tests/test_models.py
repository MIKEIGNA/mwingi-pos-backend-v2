from django.test import Client
from django.urls import reverse
from django.contrib.sessions.models import Session

from core.test_utils.custom_testcase import TestCase
from mysettings.models import MySetting
from rest_framework.authtoken.models import Token

from core.test_utils.create_user import create_new_user


# MySetting
class MySettingVerboseNamesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):

        # Create a user with email john@gmail.com
        create_new_user('john')

    def test_MySetting_fields_verbose_names(self):
        """
        Ensure all fields in MySetting have the correct verbose names and can be
        found
        """
        ms = MySetting.objects.get(name='main')

        self.assertEqual(ms._meta.get_field('name').verbose_name, 'name')
        self.assertEqual(ms._meta.get_field(
            'reset_tokens').verbose_name, 'reset tokens')
        self.assertEqual(ms._meta.get_field('signups').verbose_name, 'signups')
        self.assertEqual(ms._meta.get_field(
            'maintenance').verbose_name, 'maintenance')
        self.assertEqual(ms._meta.get_field(
            'allow_contact').verbose_name, 'allow contact')
        self.assertEqual(ms._meta.get_field(
            'delete_sessions').verbose_name, 'delete sessions')
        self.assertEqual(ms._meta.get_field(
            'accept_payments').verbose_name, 'accept payments')
        self.assertEqual(ms._meta.get_field(
            'new_employee').verbose_name, 'new employee')
        self.assertEqual(ms._meta.get_field(
            'new_product').verbose_name, 'new product')
        self.assertEqual(ms._meta.get_field(
            'new_customer').verbose_name, 'new customer')
        self.assertEqual(ms._meta.get_field(
            'new_sale').verbose_name, 'new sale')
        self.assertEqual(ms._meta.get_field(
            'receipt_change_stock_task_running').verbose_name, 
            'receipt change stock task running'
        )

        fields = ([field.name for field in MySetting._meta.fields])

        self.assertEqual(len(fields), 14)


"""
=========================== Models ===================================
"""

# MySetting


class MySettingExistenceTestCase(TestCase):

    @classmethod
    def setUpTestData(self):

        # Create a user with email john@gmail.com
        self.user = create_new_user('john')

        # Create a user with email jack@gmail.com
        create_new_user('jack')

    def test_MySetting_after_user_has_been_created(self):
        """
        MySetting is created when a user is created

        MySetting fields

        Ensure everytime a user is created, a MySetting is created with
        the right fields and values
        """
        ms = MySetting.objects.get(name='main')

        self.assertEqual(ms.name, 'main')
        self.assertEqual(ms.reset_tokens, False)
        self.assertEqual(ms.signups, True)
        self.assertEqual(ms.maintenance, True)
        self.assertEqual(ms.delete_sessions, False)
        self.assertEqual(ms.new_employee, True)
        self.assertEqual(ms.new_product, True)
        self.assertEqual(ms.new_customer, True)
        self.assertEqual(ms.new_sale, True)
        self.assertEqual(ms.receipt_change_stock_task_running, False)
        self.assertEqual(str(ms), 'main')  # Test the str method

    def test_if_MySetting_delete_method_wont_work(self):
        """
        Profile delete()

        """
        ms = MySetting.objects.get(name='main')
        ms.delete()

        """ Confirm that MySetting's delete() did not work """

        ms = MySetting.objects.get(name='main')

        self.assertEqual(ms.name, 'main')
        self.assertEqual(ms.reset_tokens, False)
        self.assertEqual(ms.signups, True)
        self.assertEqual(ms.maintenance, True)
        self.assertEqual(ms.delete_sessions, False)
        self.assertEqual(ms.new_employee, True)
        self.assertEqual(ms.new_product, True)
        self.assertEqual(ms.new_customer, True)
        self.assertEqual(ms.new_sale, True)
        self.assertEqual(str(ms), 'main')  # Test the str method

    def test_if_MySettings_cant_be_created_with_a_non_unique_name(self):
        """
        Ensure two MySettings cant be created with a non unique name

        """
        result = None

        try:
            MySetting.objects.create(name='main')


        except:
            result = 'not created'

        self.assertEqual(result, 'not created')

    def test_MySetting_wont_be_created_when_a_second_user_is_created(self):
        """        
        MySetting fields

        Ensure MySetting wont be created when a second user is created
        """
        ms = MySetting.objects.all().count()

        self.assertEqual(ms, 1)

    def test_MySetting_when_reset_tokens_is_set_to_true(self):
        """
        reset_tokens

        MySetting fields

        Ensure tokens are regenerated when reset_tokens is set to true
        """
        tokens = Token.objects.all()
        token1a = tokens[0]
        token2a = tokens[1]

        ms = MySetting.objects.get(name='main')
        ms.reset_tokens = True
        ms.save()

        tokens = Token.objects.all()
        token1b = tokens[0]
        token2b = tokens[1]

        """ Confirm that tokens were regenerated """
        self.assertTrue(token1a != token1b)
        self.assertTrue(token2a != token2b)

        """ Confirm that reset_tokens is set back to false """
        self.assertEqual(ms.reset_tokens, False)

    def test_MySetting_when_delete_sessions_is_set_to_true(self):

        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        self.client = Client()
        self.client.login(username='john@gmail.com', password='secretpass')

        """ Confirm that the user is logged in """
        response = self.client.get(reverse('profiles:profile'))
        self.assertEqual(response.status_code, 200)

        """
        delete_sessions
        
        MySetting fields
                
        Ensure tokens are regenerated and sessions are deleted when 
        delete_sessions is set to true
        """
        tokens = Token.objects.all()
        token1a = tokens[0]
        token2a = tokens[1]

        ms = MySetting.objects.get(name='main')
        ms.delete_sessions = True
        ms.save()

        tokens = Token.objects.all()
        token1b = tokens[0]
        token2b = tokens[1]

        """ Confirm that tokens were regenerated """
        self.assertTrue(token1a != token1b)
        self.assertTrue(token2a != token2b)

        """ Confirm that reset_tokens is set back to false """
        self.assertEqual(ms.reset_tokens, False)

        """ Confirm that sessions were deleted """
        response = self.client.get(reverse('profiles:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=/profile/')

    def test_MySetting_when_maintenance_is_set_to_true(self):
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        self.client = Client()
        self.client.login(username='john@gmail.com', password='secretpass')

        """ Confirm that the user is logged in and there session in the db"""
        response = self.client.get(reverse('profiles:profile'))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Session.objects.all().count(), 1)

        """
        maintenance
        
        MySetting fields
        
        Ensure tokens are regenerated and sessions are deleted when maintenance is
        set to true while the previous one was false
        """
        tokens = Token.objects.all()
        token1a = tokens[0]
        token2a = tokens[1]

        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        tokens = Token.objects.all()
        token1b = tokens[0]
        token2b = tokens[1]

        """ Confirm that tokens were regenerated """
        self.assertTrue(token1a != token1b)
        self.assertTrue(token2a != token2b)

        """ Confirm that reset_tokens is set back to false """
        self.assertEqual(ms.reset_tokens, False)

        """ Confirm that sessions were deleted """
        response = self.client.get(reverse('profiles:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=/profile/')

        self.assertEqual(Session.objects.all().count(), 0)
