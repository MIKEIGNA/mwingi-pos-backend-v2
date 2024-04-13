from datetime import time
import datetime

from core.time_utils.time_localizers import date_str_to_local_datetime, datetime_str_to_local_datetime
class QuerysetFilterHelpers:

    @staticmethod
    def range_queryset_date_filter(
        queryset,
        filter_args, 
        field_name, 
        date_after, 
        date_before, local_timezone):
        """
        Filters queryset with date range of the passed date field name
        """
        date_after = date_str_to_local_datetime(
            date_after, local_timezone, time.min
        )
        date_before = date_str_to_local_datetime(
            date_before, local_timezone, time.max
        )

        if date_after and date_before:
            range_lookup = '__'.join([field_name, 'range'])
            queryset = queryset.filter(**{range_lookup: (date_after, date_before)})
   
        return queryset
    
    @staticmethod
    def range_date_filter(queryset, field_name, date_after, date_before, local_timezone):
        """
        Filters queryset with date range of the passed date field name
        """
        date_after = date_str_to_local_datetime(
            date_after, local_timezone, time.min
        )
        date_before = date_str_to_local_datetime(
            date_before, local_timezone, time.max
        )

        if date_after and date_before:
            range_lookup = '__'.join([field_name, 'range'])
            queryset = queryset.filter(**{range_lookup: (date_after, date_before)})
   
        return queryset

    @staticmethod
    def range_datetime_filter(queryset, field_name, datetime_after, datetime_before, local_timezone):
        """
        Filters queryset with date range of the passed date field name
        """
        datetime_after = datetime_str_to_local_datetime(
            datetime_after, local_timezone
        )
        datetime_before = datetime_str_to_local_datetime(
            datetime_before, local_timezone
        )

        if datetime_after and datetime_before:
            range_lookup = '__'.join([field_name, 'range'])
            queryset = queryset.filter(**{range_lookup: (datetime_after, datetime_before)})

        return queryset