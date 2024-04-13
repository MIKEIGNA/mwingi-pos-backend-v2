
from traqsale_cloud.celery import app as celery_app

# pylint: disable=bare-except
# pylint: disable=broad-except 


### Syncs Loyverse taxes incase there are receipts that we missed
@celery_app.task(name="update_taxes_task")
def update_taxes_task(profile, taxes):
    _CreateLoyverseCustomerTasks(profile, taxes)

class _CreateLoyverseCustomerTasks:
    """
    Create/update loyverse taxes
    """
    
    def __init__(self, profile, taxes):
        
        self.profile = profile
        self.taxes = taxes

        self.create_or_update_receipts()

    def create_or_update_receipts(self):
        """
        Create or update receipts
        """
        from loyverse.utils.loyverse_api import LoyverseSyncData

        LoyverseSyncData(
            profile=self.profile,
            taxes=self.taxes,
        ).sync_data()
