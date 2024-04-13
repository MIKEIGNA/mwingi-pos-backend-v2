
from core.logger_manager import LoggerManager


from traqsale_cloud.celery import app as celery_app

# pylint: disable=bare-except
# pylint: disable=broad-except

@celery_app.task(name="two_minutes_tasks")
def two_minutes_tasks():
    """
    Runs tasks that need to be run every 2 minutes
    """
    _RunTwoMinutesTasks()
    
class _RunTwoMinutesTasks:

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
        from accounts.tasks.loyverse_receipts_tasks import sync_loyverse_receipts_task

        try:
            print('** Running hourly sync_loyverse_receipts_task')
            sync_loyverse_receipts_task(hours_to_go_back=0.25)
        except:
            LoggerManager.log_critical_error() 
