
from django.core.management.base import BaseCommand
import os



class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py cmd_clear_logs page_critical.log
    python manage.py cmd_clear_logs page_views.log
    python manage.py cmd_clear_logs software_task_critical.log


    filepath = BASE_DIR + '/xlogs/' + 'page_critical.log'
    
    """
    help = 'Creates test data'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)
  
    def handle(self, *args, **options):

        # Define Django project base directory
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        BASE_DIR = BASE_DIR.replace('accounts/management', '')

        # Define the full file path
        filepath = BASE_DIR + '/xlogs/' + options['filename']
        # Open the file for reading content
        file = open(filepath, 'r+' ,encoding="utf8")
        file.truncate(0)
        file.close()


        

        