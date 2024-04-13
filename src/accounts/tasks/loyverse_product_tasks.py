
from traqsale_cloud.celery import app as celery_app

# pylint: disable=bare-except
# pylint: disable=broad-except 


### Syncs Loyverse products incase there are receipts that we missed
@celery_app.task(name="update_products_task")
def update_products_task(profile, products):
    _CreateLoyverseProductsTasks(profile, products)

class _CreateLoyverseProductsTasks:
    """
    Create/update loyverse products
    """
    
    def __init__(self, profile, products):
        
        self.profile = profile
        self.products = products

        self.create_or_update_receipts()

    def create_or_update_receipts(self):
        """
        Create or update receipts
        """
        from loyverse.utils.loyverse_api import LoyverseSyncData


        LoyverseSyncData(
            profile=self.profile,
            items=self.products,
        ).sync_data()
