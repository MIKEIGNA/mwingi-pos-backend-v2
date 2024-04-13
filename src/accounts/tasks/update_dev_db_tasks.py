from inventories.models.inventory_valuation_models import InventoryValuationLine
from sales.models import ReceiptLine
from traqsale_cloud.celery import app as celery_app

@celery_app.task(name="update_receipt_lines_tasks1")
def update_receipt_lines_tasks1():
    
    # Update receipt_number field in ReceiptLine
    receipt_lines = ReceiptLine.objects.filter(receipt_number="")

    for receipt_line in receipt_lines:
        
        ReceiptLine.objects.filter(
            id=receipt_line.id
        ).update(
            receipt_number=receipt_line.receipt.receipt_number,
            refund_for_receipt_number=receipt_line.receipt.refund_for_receipt_number,
            store_reg_no=receipt_line.receipt.store.reg_no,
            user_reg_no=receipt_line.receipt.user.reg_no,
        )

@celery_app.task(name="update_receipt_lines_tasks2")
def update_receipt_lines_tasks2():
    
    # Update receipt_number field in ReceiptLine
    receipt_lines = ReceiptLine.objects.filter(store_reg_no=0)

    for receipt_line in receipt_lines:
        
        ReceiptLine.objects.filter(
            id=receipt_line.id
        ).update(
            receipt_number=receipt_line.receipt.receipt_number,
            refund_for_receipt_number=receipt_line.receipt.refund_for_receipt_number,
            store_reg_no=receipt_line.receipt.store.reg_no,
            user_reg_no=receipt_line.receipt.user.reg_no,
        )



@celery_app.task(name="update_receipt_tasks1")
def update_receipt_tasks1():
    
    # Update receipt_number field in ReceiptLine
    receipts = InventoryValuationLine.objects.filter(user_reg_no=0)

    for receipt in receipts:
        
        InventoryValuationLine.objects.filter(
            id=receipt.id
        ).update(
            store_reg_no=receipt.store.reg_no,
            user_reg_no=receipt.user.reg_no,
        )


@celery_app.task(name="update_receipt_total_cost_tasks")
def update_receipt_total_cost_tasks():
    
    # Update receipt_number field in ReceiptLine
    receipts = InventoryValuationLine.objects.filter(total_cost=0)

    for receipt in receipts:
        receipt.calculate_and_update_total_cost()
        

@celery_app.task(name="update_receipt_total_cost_tasks2")
def update_receipt_total_cost_tasks2(receipt_ids):
    
    # Update receipt_number field in ReceiptLine
    receipts = InventoryValuationLine.objects.filter(id__in=receipt_ids, total_cost=0)
    for receipt in receipts:
        receipt.calculate_and_update_total_cost()


@celery_app.task(name="update_inventory_valuation_tasks")
def update_inventory_valuation_tasks(line_ids):
    
    # Update receipt_number field in ReceiptLine
    lines = InventoryValuationLine.objects.filter(id__in=line_ids, is_recaclulated=False)
    for line in lines:
        line.recalculate_inventory_valuation_line()