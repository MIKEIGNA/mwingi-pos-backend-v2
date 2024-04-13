from core.test_utils.create_store_models import create_new_store

from core.test_utils.create_user import create_new_user

from core.test_utils.custom_testcase import TestCase
from core.test_utils.log_reader import get_test_firebase_sender_log_content

from profiles.models import Profile
from profiles.models import LoyaltySetting, ReceiptSetting, UserGeneralSetting


"""
=========================== LoyaltySetting ===================================
"""  
class LoyaltySettingTestCase(TestCase):
    
    def setUp(self):
        
        #Create a top user1
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')
        
        self.store = create_new_store(self.top_profile, 'Computer Store')

        self.l_setting = LoyaltySetting.objects.get(profile=self.top_profile)

    def test_mode_fields_verbose_names(self):

        self.assertEqual(self.l_setting._meta.get_field('value').verbose_name,'value')
        
        fields = ([field.name for field in LoyaltySetting._meta.fields])
        
        self.assertEqual(len(fields), 3)

    def test_model_after_user_has_been_created(self):

        self.assertEqual(self.l_setting.value, 0)

    def test_firebase_messages_are_sent_correctly(self):

        content = get_test_firebase_sender_log_content(only_include=['loyalty'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.top_profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'loyalty', 
                'action_type': 'edit', 
                'value': '0.0'
            }
        }

        self.assertEqual(content[0], result)

        # Edit model
        l_setting = LoyaltySetting.objects.get(profile=self.top_profile)
        l_setting.value = 20.04
        l_setting.save()

        content = get_test_firebase_sender_log_content(only_include=['loyalty'])
        self.assertEqual(len(content), 2)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.top_profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'loyalty', 
                'action_type': 'edit', 
                'value': '20.04'
            }
        }

        self.assertEqual(content[1], result)


"""
=========================== ReceiptSetting ===================================
"""  
class ReceiptSettingTestCase(TestCase):
    
    def setUp(self):
        
        #Create a top user1
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')
        
        self.store = create_new_store(self.top_profile, 'Computer Store')

        r_setting = ReceiptSetting.objects.get(profile=self.top_profile)
        r_setting.header1 = 'Header1'
        r_setting.header2 = 'Header2'
        r_setting.header3 = 'Header3'
        r_setting.header4 = 'Header4'
        r_setting.header5 = 'Header5'
        r_setting.header6 = 'Header6'
        r_setting.footer1 = 'Footer1'
        r_setting.footer2 = 'Footer2'
        r_setting.footer3 = 'Footer3'
        r_setting.footer4 = 'Footer4'
        r_setting.footer5 = 'Footer5'
        r_setting.footer6 = 'Footer6'
        r_setting.save()

    def test_mode_fields_verbose_names(self):
              
        r_setting = ReceiptSetting.objects.get(profile=self.top_profile)

        self.assertEqual(r_setting._meta.get_field('header1').verbose_name,'header1')
        self.assertEqual(r_setting._meta.get_field('header2').verbose_name,'header2')
        self.assertEqual(r_setting._meta.get_field('header3').verbose_name,'header3')
        self.assertEqual(r_setting._meta.get_field('header4').verbose_name,'header4')
        self.assertEqual(r_setting._meta.get_field('header5').verbose_name,'header5')
        self.assertEqual(r_setting._meta.get_field('header6').verbose_name,'header6')

        self.assertEqual(r_setting._meta.get_field('footer1').verbose_name,'footer1')
        self.assertEqual(r_setting._meta.get_field('footer2').verbose_name,'footer2')
        self.assertEqual(r_setting._meta.get_field('footer3').verbose_name,'footer3')
        self.assertEqual(r_setting._meta.get_field('footer4').verbose_name,'footer4')
        self.assertEqual(r_setting._meta.get_field('footer5').verbose_name,'footer5')
        self.assertEqual(r_setting._meta.get_field('footer6').verbose_name,'footer6')

        self.assertEqual(r_setting._meta.get_field('reg_no').verbose_name,'reg no')
        
        fields = ([field.name for field in ReceiptSetting._meta.fields])
        
        self.assertEqual(len(fields), 16)

    def test_model_after_user_has_been_created(self):

        r_setting = ReceiptSetting.objects.get(profile=self.top_profile)
        
        self.assertEqual(r_setting.header1, 'Header1')
        self.assertEqual(r_setting.header2, 'Header2')
        self.assertEqual(r_setting.header3, 'Header3')
        self.assertEqual(r_setting.header4, 'Header4')
        self.assertEqual(r_setting.header5, 'Header5')
        self.assertEqual(r_setting.header6, 'Header6')

        self.assertEqual(r_setting.footer1, 'Footer1')
        self.assertEqual(r_setting.footer2, 'Footer2')
        self.assertEqual(r_setting.footer3, 'Footer3')
        self.assertEqual(r_setting.footer4, 'Footer4')
        self.assertEqual(r_setting.footer5, 'Footer5')
        self.assertEqual(r_setting.footer6, 'Footer6')

        self.assertTrue(r_setting.reg_no > 100000) # Check if we have a valid reg_no


"""
=========================== UserGeneralSetting ===================================
"""  
class UserGeneralSettingTestCase(TestCase):
    
    def setUp(self):
        
        #Create a top user1
        self.user = create_new_user('john')
        
        self.top_profile = Profile.objects.get(user__email='john@gmail.com')
        
        self.store = create_new_store(self.top_profile, 'Computer Store')

        self.g_setting = UserGeneralSetting.objects.get(profile=self.top_profile)

    def test_mode_fields_verbose_names(self):

        self.assertEqual(self.g_setting._meta.get_field('enable_shifts')\
            .verbose_name,'enable shifts')
        self.assertEqual(self.g_setting._meta.get_field('enable_open_tickets')\
            .verbose_name,'enable open tickets')
        self.assertEqual(self.g_setting._meta.get_field('enable_low_stock_notifications')\
            .verbose_name,'enable low stock notifications')
        self.assertEqual(self.g_setting._meta.get_field('enable_negative_stock_alerts')\
            .verbose_name,'enable negative stock alerts')
        self.assertEqual(self.g_setting._meta.get_field('reg_no').verbose_name,'reg no')
        
        fields = ([field.name for field in UserGeneralSetting._meta.fields])
        
        self.assertEqual(len(fields), 7)

    def test_model_after_user_has_been_created(self):

        self.assertEqual(self.g_setting.enable_shifts, False)
        self.assertEqual(self.g_setting.enable_open_tickets, False)
        self.assertEqual(self.g_setting.enable_low_stock_notifications, True)
        self.assertEqual(self.g_setting.enable_negative_stock_alerts, True)
        self.assertTrue(self.g_setting.reg_no > 100000) # Check if we have a valid reg_no

    def test_get_settings_dict_method(self):

        self.assertEqual(
            self.g_setting.get_settings_dict(), 
            {
                'enable_shifts': False, 
                'enable_open_tickets': False, 
                'enable_low_stock_notifications': True, 
                'enable_negative_stock_alerts': True
            }
        )

    def test_firebase_messages_are_sent_correctly(self):

        content = get_test_firebase_sender_log_content(only_include=['user_general_setting'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.top_profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'user_general_setting', 
                'action_type': 'edit', 
                'enable_shifts': 'False', 
                'enable_open_tickets': 'False', 
                'enable_low_stock_notifications': 'True', 
                'enable_negative_stock_alerts': 'True'
            }
        }

        self.assertEqual(content[0], result)

        # Edit model
        g_setting = UserGeneralSetting.objects.get(profile=self.top_profile)
        g_setting.enable_shifts = True
        g_setting.enable_open_tickets = True
        g_setting.enable_low_stock_notifications = False
        g_setting.enable_negative_stock_alerts = False
        g_setting.save()

        content = get_test_firebase_sender_log_content(only_include=['user_general_setting'])
        self.assertEqual(len(content), 2)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.top_profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'user_general_setting', 
                'action_type': 'edit', 
                'enable_shifts': 'True', 
                'enable_open_tickets': 'True', 
                'enable_low_stock_notifications': 'False', 
                'enable_negative_stock_alerts': 'False'
            }
        }

        self.assertEqual(content[1], result)
