import os
from distutils.dir_util import copy_tree
import shutil

from django.core.management.base import BaseCommand

from django.conf import settings

class CollectMediaFiles:

    def __init__(self):
        self.original_assets_dir = './accounts/management/commands/utils/createmedia_assets/'
        self.target_dir = f'.{settings.MEDIA_URL}'

        # Copy test images
        self.copy_test_imaage_files()
        
        # Copy default no image
        self.copy_default_no_image()
 
        # Copy sound files
        self.copy_sound_files()

 
    def copy_test_imaage_files(self):
        
        assets_dir = f'{self.original_assets_dir}images/tests'
        target_dir = f'{self.target_dir}images/tests'

        if not os.path.exists(assets_dir):
            raise Exception(f"Cannot seem to find {assets_dir}")

        # Create images directory if it does not exits
        self.create_directory(target_dir)

        # Create images directory if it does not exits
        self.create_directory(f'{target_dir}/images/profiles/')
        self.create_directory(f'{target_dir}/images/products/')
        self.create_directory(f'{target_dir}/images/receipts/')

        # Fill the test directory 
        self.copy_directory_assets(assets_dir, target_dir)

    def copy_default_no_image(self):

        image_name_and_extension = 'no_image.jpg'

        assets_dir = f'{self.original_assets_dir}images/{image_name_and_extension}'

        if not os.path.exists(assets_dir):
            raise Exception(f"Cannot seem to find {assets_dir}")

        target_dir = f'{self.target_dir}images/{image_name_and_extension}'

        if not os.path.exists(target_dir):
            shutil.copyfile(assets_dir, target_dir)

    def copy_sound_files(self):

        assets_dir = f'{self.original_assets_dir}sounds'
        target_dir = f'{self.target_dir}sounds'

        if not os.path.exists(assets_dir):
            raise Exception(f"Cannot seem to find {assets_dir}")

        # Create sounds directory if it does not exits
        self.create_directory(target_dir)

        # Fill the test directory 
        self.copy_directory_assets(assets_dir, target_dir)
        
    def copy_directory_assets(self, origin_dir, path):
        # Copy items in origin_dir into path
        copy_tree(origin_dir, path)
    
    def create_directory(self, path):
        # Create directory if it does not exist
        if not os.path.exists(path):
            os.mkdir(path)

 
class Command(BaseCommand):
    """
    To call this command,
    
    python manage.py collectmedia
    
    Used to create neccessarry folders and image files in the media folder
    """
    help = 'Used to prepare media folder'

    def handle(self, *args, **options):

        CollectMediaFiles()

        self.stdout.write(self.style.SUCCESS('Media files collected successfully')) 
        