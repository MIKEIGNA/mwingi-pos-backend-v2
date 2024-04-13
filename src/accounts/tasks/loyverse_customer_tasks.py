
from traqsale_cloud.celery import app as celery_app

# pylint: disable=bare-except
# pylint: disable=broad-except 


### Syncs Loyverse customers incase there are receipts that we missed
@celery_app.task(name="update_customers_task")
def update_customers_task(profile, customers):
    _CreateLoyverseCustomerTasks(profile, customers)

class _CreateLoyverseCustomerTasks:
    """
    Create/update loyverse customers
    """
    
    def __init__(self, profile, customers):
        
        self.profile = profile
        self.customers = customers

        self.create_or_update_receipts()

    def create_or_update_receipts(self):
        """
        Create or update receipts
        """
        from loyverse.utils.loyverse_api import LoyverseSyncData


        LoyverseSyncData(
            profile=self.profile,
            customers=self.customers,
        ).sync_data()
