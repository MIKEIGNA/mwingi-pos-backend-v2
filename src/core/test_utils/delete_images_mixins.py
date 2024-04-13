import os

from django.conf import settings

class DeleteProfileTestImagesMixin:
    def _delete_images_in_the_test_folder(self, folder_path):
        """
        Deletes profile assets in the images test folder
        """
        
#        folder_path = settings.MEDIA_ROOT + 'images/profiles'
        
        """
        Just a precaution to make sure we only delete assets in the test images folder
        """
        if not "media/images/tests/images" in folder_path:
            message = """Fool what are you trying to do. If you continue with this stupidity,you might end up deleting essential data.
            """
            print("\n\n\n XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")           
            print(message)
            print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX \n\n\n ") 
            return False
        
        for the_file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, the_file)
                        
            try:
                os.remove(file_path)
            except:
                pass

    def delete_test_profile_image_path(self):

        folder_path = settings.MEDIA_ROOT + 'images/profiles'
        self._delete_images_in_the_test_folder(folder_path)

    def delete_test_product_image_path(self):

        folder_path = settings.MEDIA_ROOT + 'images/products'
        self._delete_images_in_the_test_folder(folder_path)

    def delete_test_receipts_image_path(self):

        folder_path = settings.MEDIA_ROOT + 'images/receipts'
        self._delete_images_in_the_test_folder(folder_path)