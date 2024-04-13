
from django.core.management.base import BaseCommand
from profiles.models import Profile

from sales.models import Receipt



class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py cmd_delete_receipts email@gmail.com
    
    """
    help = 'Creates test data'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str)
  
    def handle(self, *args, **options):

        profile = Profile.objects.get(user__email=options['email'])

        Receipt.objects.filter(store__profile=profile).delete()

        