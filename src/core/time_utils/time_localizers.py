import datetime
import os
from django.conf import settings
import pytz
from django.utils import timezone



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traqsale_cloud.settings')



def utc_to_local_datetime(utc_time, local_timezone=settings.LOCATION_TIMEZONE):
    return utc_time.astimezone(pytz.timezone(local_timezone)) 

def utc_to_local_datetime_with_format(utc_time, local_timezone, short=False):

    # Change time from utc to local
    date = utc_to_local_datetime(utc_time, local_timezone)

    # Change date format
    local_date_and_time = (date).strftime(
        settings.PREFERED_DATE_FORMAT2 if short else settings.PREFERED_DATE_FORMAT
    )

    return local_date_and_time

def date_str_to_local_datetime(str_date, local_timezone, time_rep=datetime.time.min):
    """
    Accepts a date in iso format and then returns it as a datetime.datetime in
    the local timezone
    """
    try:

        new_date = timezone.datetime.fromisoformat(str_date)

        new_date = datetime.datetime.combine(new_date, time_rep)

        return pytz.timezone(local_timezone).localize(new_date)
    
    except: # pylint: disable=bare-except
        return None

def datetime_str_to_local_datetime(str_date, local_timezone, time_rep=datetime.time.min):
    """
    Accepts a date in iso format and then returns it as a datetime.datetime in
    the local timezone
    """
    try:

        date_time_obj = datetime.datetime.strptime(str_date, '%Y-%m-%d %H:%M')

        return pytz.timezone(local_timezone).localize(date_time_obj)
    
    except: # pylint: disable=bare-except
        return None

def is_valid_iso_format(str_date):
    """
    Returns true if str date is in correct iso format and false otherwise
    """
    try:

        datetime.date.fromisoformat(str_date)

        return True

    except: # pylint: disable=bare-except
        return False
