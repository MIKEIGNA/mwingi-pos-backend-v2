from django.conf import settings

from core.logger_manager import LoggerManager
from loyverse.utils.loyverse_api import LoyverseApi
from profiles.models import Profile


from traqsale_cloud.celery import app as celery_app

# pylint: disable=bare-except
# pylint: disable=broad-except

@celery_app.task(name="thirty_minutes_tasks")
def thirty_minutes_tasks():
    """
    Runs tasks that need to be run every 30 minutes
    """
    _RunThirtyMinutesTasks()
    
class _RunThirtyMinutesTasks:

    def __init__(self):
        """
        Instead of running multiple tasks independently, we use one task so that
        we don't overwhelm the server and DB. This way, each task here can run
        after the other has finished running.


        1. Synces items.
        """
        self.sync_items()

    def sync_items(self):
        """
        Synces local receipts with the ones in loyverse
        """
        try:
            print('** Running five_minutes_tasks')

            profile = Profile.objects.get(
                user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT
            )

            LoyverseApi.sync_items(profile=profile)

        except:
            LoggerManager.log_critical_error() 
