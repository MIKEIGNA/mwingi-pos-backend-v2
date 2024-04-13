import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone


from loyverse.utils.loyverse_receipts_creator import LoyverseReceiptSync2, LoyverseReceiptSync4
from profiles.models import Profile


class Command(BaseCommand):
    """ 
    To call this command,

    
    python manage.py script_get_receipts_for_date2

    Retrieve receipts for the specified hours 
    """
    help = 'Used to retrieve receipts for the specified hours'

    def handle(self, *args, **options):
     
        minutes_to_go_back = 5

        start_date = timezone.now() - datetime.timedelta(minutes=minutes_to_go_back+10)
        end_date = timezone.now() - datetime.timedelta(minutes=minutes_to_go_back)
        
        min_date = start_date.strftime('%Y-%m-%dT%H:%M:00.000Z')
        max_date = end_date.strftime('%Y-%m-%dT%H:%M:00.000Z')

        LoyverseReceiptSync4(
            min_date=min_date, 
            max_date=max_date
        ).sync_receipts()





       
