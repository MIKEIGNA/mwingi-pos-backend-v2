
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from accounts.create_permissions import CreatePermission, GetPermission
from accounts.models import UserGroup

class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py update_perms
    
    Used to create a superuser
    """
    help = "Updates top user\'s perms"

        
    def handle(self, *args, **options):

        CreatePermission.create_permissions()

        self.stdout.write(self.style.SUCCESS('Successfully updated top user perms')) 
        
           
    