from django.test import (
    TestCase as OriginalTestsCase, 
    TransactionTestCase as OriginalTransactionTestCase, 
    override_settings,
    tag
)
from django.conf import settings

from rest_framework.test import (
    APITestCase as OrginalAPITestCase, 
    APILiveServerTestCase as OriginalAPILiveServerTestCase
)
from core.test_utils.log_reader import FileReader
from .delete_images_mixins import DeleteProfileTestImagesMixin



def empty_logfiles():
    FileReader('xlogs', '/test_page_views.log').emptyfile()
    FileReader('xlogs', '/test_firebase_sender.log').emptyfile()

@override_settings(
    TESTING_MODE=True, 
    DO_TASK_IN_CELERY_BACKGROUND=False,
    MEDIA_ROOT = settings.TESTING_MEDIA_ROOT)
class TestCase(OriginalTestsCase, DeleteProfileTestImagesMixin):

    maxDiff = None
    
    def tearDown(self):
        """ Empty this file after each test """
        empty_logfiles()

        # Helps in cleaning media folder by removing junk
        # Delete test profile and visits images if any have been created
        self.delete_test_profile_image_path()
        self.delete_test_product_image_path()
        self.delete_test_receipts_image_path()

        super(TestCase, self).tearDown()
        
# Use this when transaction errors keep occurring mainly in postgres 
@override_settings(TESTING_MODE = True)
class TransactionTestCase(OriginalTransactionTestCase):

    maxDiff = None
    
    def tearDown(self):
        """ Empty this file after each test """
        empty_logfiles()
        
        super(TransactionTestCase, self).tearDown() 

@override_settings(
    TESTING_MODE=True, 
    MEDIA_ROOT = settings.TESTING_MEDIA_ROOT,
    DO_TASK_IN_CELERY_BACKGROUND = False)
class APITestCase(OrginalAPITestCase, DeleteProfileTestImagesMixin):

    maxDiff = None
    
    def tearDown(self):
        """ Empty this file after each test """
        empty_logfiles()

        # Helps in cleaning media folder by removing junk
        # Delete test profile and visits images if any have been created
        self.delete_test_profile_image_path()
        self.delete_test_product_image_path()
        self.delete_test_receipts_image_path()
        
        super(APITestCase, self).tearDown()
        
@override_settings(TESTING_MODE=True)
class APILiveServerTestCase(OriginalAPILiveServerTestCase):

    maxDiff = None
    
    def tearDown(self):
        """ Empty this file after each test """
        empty_logfiles()
        
        super(APILiveServerTestCase, self).tearDown()