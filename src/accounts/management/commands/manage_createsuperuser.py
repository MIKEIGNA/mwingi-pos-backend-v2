
from django.core.management.base import BaseCommand

from mysettings.models import MySetting

from .utils.create_superuser import create_loyverse_owner, create_superuser

class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py manage_createsuperuser
    
    Used to create a superuser
    """
    help = 'Used to create a superusers'

        
    def handle(self, *args, **options):
        
        create_superuser()
        create_loyverse_owner()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()

        self.stdout.write(self.style.SUCCESS('Successfully created a supersuer')) 
        
           
    