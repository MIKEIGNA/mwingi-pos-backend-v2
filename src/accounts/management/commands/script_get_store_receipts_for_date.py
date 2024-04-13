from django.core.management.base import BaseCommand
from loyverse.utils.loyverse_receipts_creator import LoyverseReceiptSync3
from profiles.models import Profile
from django.conf import settings

class Command(BaseCommand):
    """
    To call this command,

    python manage.py script_get_store_receipts_for_date 2024-03-30T00:00:00.000Z 2024-03-30T23:59:00.000Z 0d1baa7a-83b4-4e76-8067-4be1cabd7d2d
    python manage.py script_get_store_receipts_for_date 2023-0-23T00:00:00.000Z 2023-04-28T23:59:00.000Z 
    

    python manage.py script_get_store_receipts_for_date 2023-02-18T00:00:00.000Z 2023-02-28T23:59:00.000Z 03073549-1221-45ca-8b5c-7edd7986f6e5

    python manage.py script_get_store_receipts_for_date 2023-01-01T00:00:00.000Z 2023-02-28T23:59:00.000Z f4b6f3cf-4be0-4f1a-a9f1-61e36fd7eb11

    python manage.py script_get_receipts_for_date 2022-11-24T00:00:00.000Z 2022-11-24T23:59:00.000Z

    python manage.py script_get_receipts_for_date 2022-08-01T00:00:00.000Z 2022-08-31T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2022-09-01T00:00:00.000Z 2022-09-30T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2022-10-01T00:00:00.000Z 2022-10-31T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2022-11-01T00:00:00.000Z 2022-11-30T23:59:00.000Z

    python manage.py script_get_receipts_for_date 2022-11-25T00:00:00.000Z 2022-11-25T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2022-11-26T00:00:00.000Z 2022-11-26T23:59:00.000Z
    python manage.py script_get_receipts_for_date 2022-11-27T00:00:00.000Z 2022-11-27T23:59:00.000Z

    Retrieve receipts for the specified hours 
    """
    help = 'Used to retrieve receipts for the specified hours'

    def add_arguments(self, parser):
        parser.add_argument('min_date', type=str)
        parser.add_argument('max_date', type=str)
        parser.add_argument('store_id', type=str)

    def handle(self, *args, **options):
        # sync_loyverse_receipts_task.delay(options['hours_to_go_back'])

        min_date = options['min_date']
        max_date = options['max_date']
        store_id = options['store_id']

        print(f'Min date {min_date}')
        print(f'Max date {max_date}')
        print(f'Store id {store_id}')
        
        profile = Profile.objects.get(
            user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT
        )

        print("CAlling")

        LoyverseReceiptSync3(
            profile=profile,
            min_date=min_date, 
            max_date=max_date, 
            store_id=store_id
        ).sync_receipts()



        
        