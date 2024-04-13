import datetime
from mysettings.models import MySetting

from traqsale_cloud.celery import app as celery_app

from django.utils import timezone
from django.conf import settings

from core.logger_manager import LoggerManager
from sales.models import Receipt

# pylint: disable=bare-except
# pylint: disable=broad-except

@celery_app.task(name="receipt_change_stock_tasks")
def receipt_change_stock_tasks(hours_to_go_back=1, ignore_dates=False):
    """
    Runs tasks that need to be run every 30 seconds
    """
    _ChangeReceiptStockTasks(hours_to_go_back, ignore_dates)

class _ChangeReceiptStockTasks:

    def __init__(self, hours_to_go_back=1, ignore_dates=False, ):

        LoggerManager.log_critical_error()

        self.ignore_dates = ignore_dates

        self.start_time = timezone.now() - datetime.timedelta(seconds=hours_to_go_back*3600)
        self.end_time = timezone.now() - datetime.timedelta(seconds=30)

        # Check if update is allowed
        if not self.is_update_allowed():
            
            return

        # Set receipt_change_stock_task_running to True
        MySetting.objects.all().update(
            receipt_change_stock_task_running=True,
            stock_task_update_date=timezone.now()
        )
        
        start_time = timezone.now()
        self.start_process()
        end_time = timezone.now()

        LoggerManager.log_tasks(f'ChangeReceiptStockTasks took {end_time - start_time} seconds')

        # Set receipt_change_stock_task_running to False
        MySetting.objects.all().update(
            receipt_change_stock_task_running=False,
            stock_task_update_date=timezone.now()
        )


    def is_update_allowed(self):
        """
        Check if the task is allowed to update
        """

        minutes_ago = timezone.now() - datetime.timedelta(
            seconds=10*60 + 1
        )

        my_setting = MySetting.objects.get()

        if my_setting.receipt_change_stock_task_running:
            # If the last update was less than ".." minutes ago, don't update
            if my_setting.stock_task_update_date > minutes_ago:
                return False
    
        return True

    def start_process(self): 

        try:
            self.change_receipt_stocks()
        except:
            LoggerManager.log_critical_error()

    def change_receipt_stocks(self):
        """
        # Check if receipts created 30 seconds ago have duplicate receipt numbers
        # If they do, delete one of them
        """
    
        receipt_number_field = Receipt.get_receipt_number_field_to_use_during_testing()

        original_receipts_params = {
            'changed_stock': False,
        }

        if not self.ignore_dates:
            original_receipts_params['sync_date__gte'] = self.start_time
            original_receipts_params['sync_date__lte'] = self.end_time

        # Get receipts created 30 seconds ago that have not been changed
        original_receipts = Receipt.objects.filter(
            **original_receipts_params
        ).order_by('created_date')

        # Get receipt numbers for the receipts and delete duplicates but retain one
        receipt_numbers = original_receipts.values_list(receipt_number_field, flat=True)
      
        # Log every line if we have receipts
        if receipt_numbers.count():
            LoggerManager.log_tasks(list(receipt_numbers))

        duplicate_items = self.find_duplicates(receipt_numbers)

        deleted_receipts_ids = []
        for receipt_number in duplicate_items:

            args = {
                'store__profile__user__email': settings.LOYVERSE_OWNER_EMAIL_ACCOUNT,
                receipt_number_field: receipt_number
            }
            
            receipts = Receipt.objects.filter(**args)

            if len(receipts) > 1:
                for receipt in receipts[1:]:
                    deleted_receipts_ids.append(receipt.id) 
                    receipt.delete()

        # Update stock units for each receipt line and then set changed_stock to True
        for receipt in original_receipts:
            
            if receipt.id in deleted_receipts_ids: 
                continue

            receipt_lines = receipt.receiptline_set.all()

            for receipt_line in receipt_lines:
                if not receipt_line.receipt.changed_stock:
                    receipt_line.update_product_stock_units()

            Receipt.objects.filter(id=receipt.id).update(changed_stock=True)

    def find_duplicates(self, lst):
        seen = set()
        duplicates = set()
        for item in lst:
            if item in seen:
                duplicates.add(item)
            else:
                seen.add(item)
        return list(duplicates)