from django.core.management.base import BaseCommand
from loyverse.utils.loyverse_api import LoyverseApi
from profiles.models import Profile

class Command(BaseCommand):
    """
    To call this command,

    python manage.py create_loyverse_sync_customers email@gmail.com
    
    Used to run custom scripts to perform various operations
    """
    help = 'Used to run custom scripts to perform various operations'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str)

    def handle(self, *args, **options):

        profile = Profile.objects.get(user__email=options['email'])

        success = LoyverseApi.sync_customers(profile=profile)

        print(success) 


        
           
    
