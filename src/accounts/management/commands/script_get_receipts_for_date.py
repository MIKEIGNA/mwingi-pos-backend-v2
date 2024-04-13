from django.core.management.base import BaseCommand
from django.conf import settings

from loyverse.utils.loyverse_receipts_creator import LoyverseReceiptSync2
from profiles.models import Profile



from inventories.models import InventoryValuationLine


# Define the batch size
# batch_size = 100

# # Get a queryset that will be iterated in batches
# lines_queryset = InventoryValuationLine.objects.filter(created_date__year=2024, created_date__day__gte=9).order_by('created_date')

# # Iterate over the queryset in batches
# for batch in lines_queryset.iterator(chunk_size=batch_size):
#     for line in batch:
#         line.recalculate_inventory_valuation_line()


class Command(BaseCommand):
    """ 
    Receipt.objects.filter(created_date__year=2024, created_date__day__gte=9).delete()


    receipts = Receipt.objects.filter(changed_stock=False)


    Receipt.objects.filter(created_date__year=2024, created_date__day__gte=9).delete()

    InventoryHistory.objects.filter(created_date__year=2024, created_date__day__gte=9).delete()

    receipts = InventoryHistory.objects.filter(created_date__year=2024, created_date__day=11)
    receipts.delete()

    To call this command,
    
    python manage.py script_get_receipts_for_date 2024-03-030T00:00:00.000Z 2020-12-31T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2023-10-02T00:00:00.000Z 2023-10-02T23:59:00.000Z

    python manage.py script_get_receipts_for_date 2024-01-10T00:00:00.000Z 2024-01-10T23:59:00.000Z
    
    python manage.py script_get_receipts_for_date 2023-09-22T00:00:00.000Z 2023-09-24T23:59:00.000Z

    python manage.py script_get_receipts_for_date 2023-09-30T00:00:00.000Z 2023-09-30T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2023-09-29T00:00:00.000Z 2023-09-29T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2023-09-28T00:00:00.000Z 2023-09-28T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2023-09-27T00:00:00.000Z 2023-09-27T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2023-09-26T00:00:00.000Z 2023-09-26T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2023-09-25T00:00:00.000Z 2023-09-25T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2023-09-24T00:00:00.000Z 2023-09-24T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2023-09-23T00:00:00.000Z 2023-09-23T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2023-09-22T00:00:00.000Z 2023-09-22T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2023-09-21T00:00:00.000Z 2023-09-21T23:59:00.000Z



    from sales.models import Receipt

    receipts = Receipt.objects.filter(created_date__month=10, created_date__day=1).order_by('-created_date')

    print(Receipt.objects.filter(receipt_number="302-4465"))

    print(len(receipts))

    for r in receipts:
        print(r.receipt_number)

    
    Retrieve receipts for the specified hours 
    """
    help = 'Used to retrieve receipts for the specified hours'

    def add_arguments(self, parser):
        parser.add_argument('min_date', type=str)
        parser.add_argument('max_date', type=str)

    def handle(self, *args, **options):
        min_date = options['min_date']
        max_date = options['max_date']

        print(f'Min date {min_date}')
        print(f'Max date {max_date}')

        profile = Profile.objects.get(
            user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT
        )

        LoyverseReceiptSync2(
            profile=profile,
            min_date=min_date, 
            max_date=max_date
        ).sync_receipts()
        

       
