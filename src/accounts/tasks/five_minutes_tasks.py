import datetime

from django.utils import timezone



from core.logger_manager import LoggerManager
from loyverse.utils.loyverse_receipts_creator import LoyverseReceiptSync4


from traqsale_cloud.celery import app as celery_app

# pylint: disable=bare-except
# pylint: disable=broad-except

@celery_app.task(name="five_minutes_tasks")
def five_minutes_tasks():
    """
    Runs tasks that need to be run every 5 minutes
    """
    _RunFiveMinutesTasks()
    
class _RunFiveMinutesTasks:

    def __init__(self):
        """
        Instead of running multiple tasks independently, we use one task so that
        we don't overwhelm the server and DB. This way, each task here can run
        after the other has finished running.


        1. Synces local receipts with the ones in loyverse.
        """
        self.sync_loyverse_receipts()

    def sync_loyverse_receipts(self): 
        """
        Synces local receipts with the ones in loyverse
        """
        try:
            print('** Running five_minutes_tasks')
       
            minutes_to_go_back = 5

            start_date = timezone.now() - datetime.timedelta(minutes=minutes_to_go_back+10)
            end_date = timezone.now() - datetime.timedelta(minutes=minutes_to_go_back)
            
            min_date = start_date.strftime('%Y-%m-%dT%H:%M:00.000Z')
            max_date = end_date.strftime('%Y-%m-%dT%H:%M:00.000Z')

            LoyverseReceiptSync4(
                min_date=min_date, 
                max_date=max_date
            ).sync_receipts()

        except:
            LoggerManager.log_critical_error() 
