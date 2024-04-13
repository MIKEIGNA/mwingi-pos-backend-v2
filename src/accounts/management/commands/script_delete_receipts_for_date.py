from django.core.management.base import BaseCommand
from django.conf import settings


from loyverse.utils.loyverse_receipts_creator import LoyverseReceiptSync2
from profiles.models import Profile
from sales.models import Receipt


class Command(BaseCommand):
    """ 
    To call this command,

    
    python manage.py script_delete_receipts_for_date 2023 11 2
    
    Retrieve receipts for the specified hours 
    """
    help = 'Used to retrieve receipts for the specified hours'

    def add_arguments(self, parser):
        parser.add_argument('year', type=str)
        parser.add_argument('month', type=str)
        parser.add_argument('day', type=str)

    def handle(self, *args, **options):
       
        print(settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)

        receipts = Receipt.objects.filter(
            store__profile__user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT,
            # created_date__year=options['year'], 
            # created_date__month=options['month'], 
            # created_date__day=options['day']
        ).delete()

        print(receipts)

    
        

       
