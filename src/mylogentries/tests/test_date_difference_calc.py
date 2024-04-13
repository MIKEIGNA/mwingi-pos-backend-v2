import datetime

from django.utils import timezone

from core.date_difference_calc import date_difference_calc
from core.test_utils.custom_testcase import TestCase


class DateDifferenceCalcTests(TestCase):
    
    def test_if_date_differnce_calc_will_translate_60_secs_difference_into_1_minute(self):
        
        now = timezone.now()
        future_date = timezone.now() + datetime.timedelta(seconds=60)
        
        duration = date_difference_calc(future_date, now)
        
        self.assertEqual(duration, '1 Minute')
        
    def test_if_date_differnce_calc_will_translate_65_secs_difference_into_1_minute(self):
        
        now = timezone.now()
        future_date = timezone.now() + datetime.timedelta(seconds=65)
        
        duration = date_difference_calc(future_date, now)
        
        self.assertEqual(duration, '1 Minute')
        
    def test_if_date_differnce_calc_will_translate_120_secs_difference_into_2_minutes(self):
        
        now = timezone.now()
        future_date = timezone.now() + datetime.timedelta(seconds=120)
        
        duration = date_difference_calc(future_date, now)
        
        self.assertEqual(duration, '2 Minutes')
        
    def test_if_date_differnce_calc_will_translate_360_secs_difference_into_6_minutes(self):
        
        now = timezone.now()
        future_date = timezone.now() + datetime.timedelta(seconds=360)
        
        duration = date_difference_calc(future_date, now)
        
        self.assertEqual(duration, '6 Minutes')
        
    def test_if_date_differnce_calc_will_translate_59_secs_difference_into_59_seconds(self):
        
        now = timezone.now()
        future_date = timezone.now() + datetime.timedelta(seconds=59)
        
        duration = date_difference_calc(future_date, now)
        
        self.assertEqual(duration, '59 Seconds')
        
    def test_if_date_differnce_calc_will_translate_0_secs_difference_into_0_seconds(self):
        
        now = timezone.now()
        future_date = timezone.now() + datetime.timedelta(seconds=0)
        
        duration = date_difference_calc(future_date, now)
        
        self.assertEqual(duration, '0 Seconds')
        
    def test_if_date_differnce_calc_will_return_unknown_if_passed_wrong_values(self):
                
        duration = date_difference_calc("string instead of date", "string instead of date")
        
        self.assertEqual(duration, 'Unknown')
        
 