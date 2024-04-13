from datetime import datetime, timedelta

from django.utils import timezone

class DateHelperMethods:

    @staticmethod
    def _get_timestamp_from_date_str(date_str):
        """
        date_str should be in either one of these formats:
            2021-03-25 02:00:00+03:00
            2021-03-25T02:00:02Z
        """
        
        # Make sure we are dealing with a string
        date_str = str(date_str)
        
        try:
            
            if len(date_str) > 22:
                date_str = date_str[:19]
            else:
                date_str = date_str.replace('T',' ')
                date_str = date_str.replace('Z','')
        
            date_time_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

            timestamp = date_time_obj.timestamp()

        except: # pylint: disable=bare-except
            timestamp = 0

        return timestamp

    @staticmethod
    def date_and_timestamp_equilizer(date_str, date_timestamp):
        """
        If we have a valid date_timestamp, we get date from it. 
        If the date_timestamp is wrong, we replace it with the provided 
        date's timestamp 
        Args:
            date: datetime
            date_timestamp: timestamp value
        """

        # Start date
        if len(str(date_timestamp)) == 10:
            date_str = timezone.make_aware(
                datetime.fromtimestamp(date_timestamp)
            )

        elif len(str(date_timestamp)) == 13:
            date_str = timezone.make_aware(
                datetime.fromtimestamp(date_timestamp//1000)
            )

        else:

            # Create timestamp
            date_timestamp = DateHelperMethods._get_timestamp_from_date_str(
                date_str
            )

        return date_str, date_timestamp

    @staticmethod
    def get_date_from_date_str(date_str):
        """
        date_str should be in either one of these formats:
            2021-03-25 02:00:00+03:00
            2021-03-25T02:00:02Z
        """
        
        # Make sure we are dealing with a string
        date_str = str(date_str)
        date_time_obj = None
        
        try:
            
            date_str = date_str.replace('T',' ')
            date_str = date_str.replace('.000Z','')
        
            date_time_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')


        except Exception as e: # pylint: disable=bare-except
            print("Date error ", e)

        return date_time_obj
    
    @staticmethod
    def get_dates_in_between(start_date, end_date):
        """
        date_str should be in either one of these formats:
            2021-03-25 02:00:00+03:00
            2021-03-25T02:00:02Z
        """
        
        date_list = []
    
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)

        date_list.append(end_date)

        return date_list