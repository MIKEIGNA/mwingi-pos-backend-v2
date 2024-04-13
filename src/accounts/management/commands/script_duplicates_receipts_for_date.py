from django.core.management.base import BaseCommand
from django.conf import settings


from loyverse.utils.loyverse_receipts_creator import LoyverseReceiptSync2
from profiles.models import Profile
from sales.models import Receipt


def find_duplicates(lst):
    seen = set()
    duplicates = set()
    for item in lst:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    return list(duplicates)

class Command(BaseCommand):
    """ 
    To call this command,

    
    python manage.py script_duplicates_receipts_for_date 2023 11 7
    
    Retrieve receipts for the specified hours 
    """
    help = 'Used to retrieve receipts for the specified hours'

    def add_arguments(self, parser):
        parser.add_argument('year', type=str)
        parser.add_argument('month', type=str)
        parser.add_argument('day', type=str)

    def handle(self, *args, **options):

        print(settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)

        receipt_numbers = Receipt.objects.filter(
            store__profile__user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT,
            created_date__year=options['year'], 
            created_date__month=options['month'], 
            created_date__day=options['day']
        ).values_list('receipt_number', flat=True)

        duplicate_items = find_duplicates(receipt_numbers)
        print("Duplicate receipts:", duplicate_items)



receipt_numbers = Receipt.objects.filter(
    store__profile__user__email="email@gmail.com",
    created_date__year=2023,
    created_date__month=10, 
    created_date__day__gte=8,
).values_list('receipt_number', flat=True)    

       
