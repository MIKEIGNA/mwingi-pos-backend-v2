from __future__ import unicode_literals

import datetime

from django.contrib.admin.filters import DateFieldListFilter
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import models

from core.time_utils.time_localizers import utc_to_local_datetime

class ExtendedDateTimeFilter(DateFieldListFilter):
    """
    This is a customizaion of the DateFieldListFilter
    
    I added the following:
        1. I made sure to change the timezone to local using my utc_to_local function
        2 Added Last month
                Last month but 1
                Last month but 2
                Last 3 months
    """
    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        
        
        self.field_generic = '%s__' % field_path
        self.date_params = {k: v for k, v in params.items() if k.startswith(self.field_generic)}
        
        # Change time from utc to local
        now = utc_to_local_datetime(timezone.now(), request.user.get_user_timezone())
        
        if isinstance(field, models.DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:       # field is a models.DateField
            today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        next_year = today.replace(year=today.year + 1, month=1, day=1)
        
        
        """ Added Custom  Dates for:
              Last month
              Last month but 1
              Last month but 2
              Last 3 months
        """
        first_day_this_month = today.replace(day=1)
        
        last_month_end = first_day_this_month - datetime.timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        
        last_month_but_1_end = last_month_start - datetime.timedelta(days=1)
        last_month_but_1_start = last_month_but_1_end.replace(day=1)
        
        last_month_but_2_end = last_month_but_1_start - datetime.timedelta(days=1)
        last_month_but_2_start = last_month_but_2_end.replace(day=1)
        
        last_3_months_start = last_month_but_2_start
        
        """ End of date customization code """
        

        self.lookup_kwarg_since = '%s__gte' % field_path
        self.lookup_kwarg_until = '%s__lt' % field_path
        self.links = (
            (_('Any date'), {}),
            (_('Today'), {
                self.lookup_kwarg_since: str(today),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('Past 7 days'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=7)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('Past 14 days'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=14)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('Past 21 days'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=21)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('This month'), {
                self.lookup_kwarg_since: str(today.replace(day=1)),
                self.lookup_kwarg_until: str(next_month),
            }),
    
    
            (_('Last month'), {
                self.lookup_kwarg_since: str(last_month_start),
                self.lookup_kwarg_until: str(first_day_this_month),
            }),
            (_('Last month but 1'), {
                self.lookup_kwarg_since: str(last_month_but_1_start),
                self.lookup_kwarg_until: str(last_month_start),
            }),
            (_('Last month but 2'), {
                self.lookup_kwarg_since: str(last_month_but_2_start),
                self.lookup_kwarg_until: str(last_month_but_1_start),
            }),
            (_('Last 3 months'), {
                self.lookup_kwarg_since: str(last_3_months_start),
                self.lookup_kwarg_until: str(next_month),
            }),
    

            (_('This year'), {
                self.lookup_kwarg_since: str(today.replace(month=1, day=1)),
                self.lookup_kwarg_until: str(next_year),
            }),
        )
        if field.null:
            self.lookup_kwarg_isnull = '%s__isnull' % field_path
            self.links += (
                (_('No date'), {self.field_generic + 'isnull': 'True'}),
                (_('Has date'), {self.field_generic + 'isnull': 'False'}),
            )