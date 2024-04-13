from django.conf import settings

from traqsale_cloud.celery import app as celery_app

# pylint: disable=bare-except
# pylint: disable=broad-except 


### Syncs Loyverse receipts incase there are receipts that we missed
@celery_app.task(name="sync_loyverse_receipts_task")
def sync_loyverse_receipts_task(hours_to_go_back=2, receipts=None):
    """
    Syncs local receipts with the ones in loyverse

    Args:
        hours_to_go_back: Determines how many hours the system should go back for
        receipts. The default is 2
    """
    print("sync_loyverse_receipts_task called")
    _SyncLoyverseReceiptsTasks(hours_to_go_back, receipts)
    
class _SyncLoyverseReceiptsTasks:
    """
    Sync loyverse receipts 
    """
    
    def __init__(self, hours_to_go_back, receipts):

        self.hours_to_go_back = hours_to_go_back
        self.receipts = receipts

        self.sync_receipts()

    def sync_receipts(self):
        """
        Sync allloyverse receipts
        """
        from profiles.models import Profile
        from loyverse.utils.loyverse_receipts_creator import LoyverseReceiptSync

        profile = Profile.objects.get(user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)
        
        LoyverseReceiptSync(
            profile=profile,
            hours_to_go_back=self.hours_to_go_back, 
            receipts=self.receipts
        ).sync_receipts()

### Syncs Loyverse receipts incase there are receipts that we missed
@celery_app.task(name="update_receipts_task")
def update_receipts_task(user_email, receipts):
    _CreateLoyverseReceiptsTasks(user_email, receipts)

class _CreateLoyverseReceiptsTasks:
    """
    Create/update loyverse receipts 
    """
    
    def __init__(self, user_email, receipts):
        
        self.user_email = user_email
        self.receipts = receipts

        self.create_or_update_receipts()

    def create_or_update_receipts(self):
        """
        Create or update receipts
        """
        from loyverse.utils.loyverse_receipts_creator import CreateLoyverseReceipts
        from profiles.models import Profile

        profile = Profile.objects.get(user__email=self.user_email)

        CreateLoyverseReceipts(
            profile=profile,
            receipts=self.receipts
        ).create_receipts()
