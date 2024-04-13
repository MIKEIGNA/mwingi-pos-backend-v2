
from core.logger_manager import LoggerManager


from traqsale_cloud.celery import app as celery_app

# pylint: disable=bare-except
# pylint: disable=broad-except

@celery_app.task(name="run_hourly_tasks")
def run_hourly_tasks():
    """
    Runs tasks that need to be run every hour
    """
    _RunHourlyTasks()
    
class _RunHourlyTasks:

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
            sync_loyverse_receipts_task()
        except:
            LoggerManager.log_critical_error() 
