
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from accounts.create_permissions import CreatePermission, GetPermission
from accounts.models import UserGroup

class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py update_top_user_perms
    
    Used to create a superuser
    """
    help = "Updates top user\'s perms"

    def add_arguments(self, parser):
        parser.add_argument('email', type=str)

    def handle(self, *args, **options):


        

        # ps = Permission.objects.all()

        # for p in ps:
        #     print(f'{p.codename} {p.name}')

        # Creates additional user permissions
        CreatePermission.create_permissions()

        # owner_groups = UserGroup.objects.filter(
        #         ident_name='Owner',
        #         is_owner_group=True
        # )

        # for group in owner_groups:
        #     group.permissions.set(GetPermission().get_owner_permissions())
        
        self.stdout.write(self.style.SUCCESS('Successfully updated top user perms')) 
        
           
    