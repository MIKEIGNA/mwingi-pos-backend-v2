from profiles.models import Profile
from loyverse.utils.loyverse_api import LoyverseApi
from traqsale_cloud.celery import app as celery_app
from core.logger_manager import LoggerManager

from django.conf import settings

# pylint: disable=bare-except
# pylint: disable=broad-except

@celery_app.task(name="midnight_tasks")
def midnight_tasks():
    """
    Runs midnight tasks
    1. Save all subscriptions so that the ones that have expired, can be marked as 
       expired
    """
    MidnightTasks() 
    
class MidnightTasks:
    """
    1. Save all subscriptions so that the ones that have expired, can be marked as 
       expired
    """
    
    def __init__(self):
        self.sync_stores_and_employees()

    def sync_stores_and_employees(self):
        """
        Update stores and employees
        """

        try:

            profile = Profile.objects.get(
                user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT
            )

            LoyverseApi.sync_stores(profile=profile)
            LoyverseApi.sync_employees(profile=profile)

        except:
            LoggerManager.log_critical_error()


    



            
        
        

    

    