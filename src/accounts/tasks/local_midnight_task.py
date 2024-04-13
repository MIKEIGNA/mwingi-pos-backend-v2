import datetime
import pytz
from stores.models import Store

from traqsale_cloud.celery import app as celery_app

from django.utils import timezone

from core.logger_manager import LoggerManager

from inventories.models.inventory_valuation_models import InventoryValuation
from profiles.models import Profile

# pylint: disable=bare-except
# pylint: disable=broad-except

@celery_app.task(name="local_midnight_tasks")
def local_midnight_tasks():
    """
    Runs local midnight tasks
    """
    _RealMidnightTasks()
    
class _RealMidnightTasks:
    """

    Create inventory valuations
    """
    
    def __init__(self):
        self.create_inventory_valuations_models()
        self.sync_loyverse_receipts()

    def get_yesterday_max_date(self, profile):
        """
        Get yesterday max date
        """

        # Set the timezone to Nairobi
        user_tz = pytz.timezone(profile.user.get_user_timezone())

        # Get the current date in Nairobi timezone
        today_local = datetime.datetime.now(user_tz).date()

        # Combine the date and time to create the target datetime
        yesterday_datetime = user_tz.localize(datetime.datetime.combine(
            today_local, 
            datetime.time(23, 59, 0))
        )

        # Minus 1 day
        yesterday_datetime = yesterday_datetime - timezone.timedelta(days=1)

        # Convert to UTC
        yesterday_datetime_utc = yesterday_datetime.astimezone(pytz.utc)

        return yesterday_datetime_utc
    
    def create_inventory_valuations_models(self):
        """
        Create inventory valuations models
        """

        try:

            profiles = Profile.objects.all()

            for profile in profiles:
                
                yesterday_max_date = self.get_yesterday_max_date(profile)

                stores_count = Store.objects.filter(
                    profile=profile,
                ).count()

                inventory_count = InventoryValuation.objects.filter(
                    user__profile=profile,
                    created_date=yesterday_max_date
                ).count()

                # Incase the task is called again after 
                # inventory valuations have already been created
                if stores_count == inventory_count: continue

                InventoryValuation.create_inventory_valutions(
                    profile=profile,
                    created_date=self.get_yesterday_max_date(profile)
                )
        except:
            LoggerManager.log_critical_error()

    def sync_loyverse_receipts(self):
        """
        Synces local receipts with the ones in loyverse
        """
        from accounts.tasks.loyverse_receipts_tasks import sync_loyverse_receipts_task

        try:
            print('** Running hourly sync_loyverse_receipts_task')
            sync_loyverse_receipts_task(hours_to_go_back=24)
        except:
            LoggerManager.log_critical_error()


    



            
        
        

    

    