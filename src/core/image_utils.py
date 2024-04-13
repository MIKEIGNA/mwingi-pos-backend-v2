from io import BytesIO
import os

from PIL import Image, ExifTags

from django.core.files import File
from django.conf import settings

from rest_framework import serializers, status
from rest_framework.response import Response
from core.logger_manager import LoggerManager

from traqsale_cloud.storage_backends import PublicMediaStorage

class Base64ImageField(serializers.ImageField):
    """
    A Django REST framework field for handling image-uploads through raw post data.
    It uses base64 for encoding and decoding the contents of the file.

    Heavily based on
    https://github.com/tomchristie/django-rest-framework/pull/1268

    Updated for Django REST framework 3.
    """

    def to_internal_value(self, data):
        from django.core.files.base import ContentFile
        import base64
        import six
        import uuid

        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # Check if the base64 string is in the "data:" format
            if 'data:' in data and ';base64,' in data:
                # Break out the header from the base64 content
                _, data = data.split(';base64,')

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            # Generate file name:
            file_name = str(uuid.uuid4())[:12] # 12 characters are more than enough.
            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)
            complete_file_name = "%s.%s" % (file_name, file_extension, )

            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension

class ApiImageVerifier():

    @staticmethod
    def verify_image(image):
        """
        If image is not valid, a response error is returned, otherwise None
        is returned

        Args:
            image: A serializer image
        """

        try:
       
            if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                
                error_data = {
                    'error': "Allowed image extensions are .jpg, .jpeg and .png"
                }
                return Response(
                    error_data, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except: # pylint: disable=bare-except
            error_data = {'error': "You did not provide a valid image"}
            
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

        return None


class ApiImageCropper():

    @staticmethod
    def crop_image11(model, serializer_image, image_sub_directory):
        """
        Crops the provided image and saves it in the correct path

        Args:
            model: Django model whose image is being cropped
            serializer_image: The image passed in the serializer
            image_sub_directory: A medial root sub director where the image will
                be saved to
        """

        image = serializer_image
        
        image_name = image.name
        
        temp_path = '{}/{}{}_{}_{}'.format(
            settings.MEDIA_ROOT, 
            image_sub_directory, 
            'temp_pic', 
            model.reg_no, image_name
        )
        
        """
        Open the image, resize it, change it's orientation if it necessary
        then save it to the temporary file path
        """
        pil_image = Image.open(image)

        

        # Try to get the image orientation
        pic_orientation = 0
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation]=='Orientation':
                    break
                
                exif=dict(pil_image._getexif().items())
            
                pic_orientation = exif[orientation]
            
        except: # pylint: disable=bare-except
            pic_orientation = 0

        # Only crop image when it's neccessary
        if (pil_image.size != (200, 200)):
            resized_image = pil_image.resize((200, 200), Image.ANTIALIAS)
        else:
            resized_image = pil_image
         
        # Change orientation if the image is not oriented correctly
        if pic_orientation == 3:
            resized_image=resized_image.rotate(180, expand=True)
        elif pic_orientation == 6:
            resized_image=resized_image.rotate(270, expand=True)
        elif pic_orientation == 8:
            resized_image=resized_image.rotate(90, expand=True)
                  
        resized_image.save(temp_path)
        
        """
        Open the resized image and then save it directy to the model's image field
        """
        image_file =  File(open(temp_path, 'rb')) #File(path, "rb")

        image_name = image.name
        model.image.save(image_name, image_file)

        """
        Delete the first image that you saved after you resized the image
        """
        try:
            os.remove(temp_path)
        except: # pylint: disable=bare-except
            pass


    @staticmethod
    def crop_image(model, serializer_image, image_sub_directory):
        """
        Crops the provided image and saves it in the correct path

        Args:
            model: Django model whose image is being cropped
            serializer_image: The image passed in the serializer
            image_sub_directory: A medial root sub director where the image will
                be saved to
        """

        image = serializer_image
        

        """
        Open the image, resize it, change it's orientation if it necessary
        then save it to the temporary file path
        """
        pil_image = Image.open(image)

        # Try to get the image orientation
        pic_orientation = 0
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation]=='Orientation':
                    break
                
                exif=dict(pil_image._getexif().items())
            
                pic_orientation = exif[orientation]
            
        except: # pylint: disable=bare-except
            pic_orientation = 0

        # Only crop image when it's neccessary
        if (pil_image.size != (200, 200)):
            resized_image = pil_image.resize((200, 200), Image.ANTIALIAS)
        else:
            resized_image = pil_image
         
        # Change orientation if the image is not oriented correctly
        if pic_orientation == 3:
            resized_image=resized_image.rotate(180, expand=True)
        elif pic_orientation == 6:
            resized_image=resized_image.rotate(270, expand=True)
        elif pic_orientation == 8:
            resized_image=resized_image.rotate(90, expand=True)
                  
        # resized_image.save(temp_path)
        
        from django.core.files.storage import default_storage as storage

        fh = storage.open(model.image.name, "wb")
        picture_format = 'png'
        resized_image.save(fh, picture_format)
        fh.close() 

        # We call this to trigger websocket update
        model.save()


class ApiImageUploader():
    """
    Crops the submitted image and then save the image

    Args:
        model: Django model whose image is being cropped
        serializer_image: The image passed in the serializer
        image_sub_directory: A media root sub director where the image will
            be saved to
    """

    def __init__(self, model, serializer_image) -> None:
        """
        Crops the submitted image and then save the image

        Args:
            model: Django model whose image is being cropped
            serializer_image: The image passed in the serializer
            image_sub_directory: A media root sub director where the image will
                be saved to
        """    
        self.model = model
        self.serializer_image = serializer_image
        self.image_sub_directory = self.model.IMAGE_SUB_DIRECTORY
        self.current_model_image_name = self.model.image.name

    def save_and_upload(self):
        """
        Normally, saves and uploads the a Pillow image into s3 but during testng,
        the image is upload normally
        """
        # Save the image directly to the bucket
        if not settings.TESTING_MODE and settings.WE_IN_CLOUD:
            self.save_and_upload_image_into_s3()
            
        else:
            self.save_and_upload_image()

    def save_and_upload_image_into_s3(self):
        """
        Saves and uploads the a Pillow image into s3
        """

        resized_image = self.crop_image()

        # Create a unique file path      
        file_path_within_bucket = os.path.join(
            self.image_sub_directory,
            f'{self.model.reg_no}-{self.serializer_image.name}' 
        )

        # Turn PIL image into bytes so that it can be saved in s3
        buffer = BytesIO()
        resized_image.save(buffer, format='PNG')

        # Save the image directly to the bucket
        if not settings.TESTING_MODE and settings.WE_IN_CLOUD:
            # We don't need to upload in cloud during testing
            media_storage = PublicMediaStorage()
            media_storage.save(file_path_within_bucket, buffer)

            # Delete old image that is being replaced
            media_storage.delete(self.current_model_image_name)

        # Change the model's image name
        self.model.image.name = file_path_within_bucket
        self.model.save()

    def save_and_upload_image(self):
        """
        Saves and uploads the a Pillow image
        """
        resized_image = self.crop_image()

        from django.core.files.storage import default_storage as storage

        fh = storage.open(self.model.image.name, "wb")
        picture_format = 'png'
        resized_image.save(fh, picture_format)
        fh.close() 

        # We call this to trigger websocket update
        self.model.save()

    def crop_image(self):
        """
        Crops the image to 200 by 200 if the image does not have these
        dimenstions already. Also, change orientation if the image is not 
        oriented correctly

        Returns:
            A pillow image object
        """
        # Open the image, resize it, change it's orientation if it necessary
        # then save it to the temporary file path
        pil_image = Image.open(self.serializer_image)

        # Try to get the image orientation
        pic_orientation = 0
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation]=='Orientation':
                    break
                
                exif=dict(pil_image._getexif().items())
            
                pic_orientation = exif[orientation]
            
        except: # pylint: disable=bare-except
            pic_orientation = 0

        

        # Only crop image when it's neccessary
        if (pil_image.size != (200, 200)):
            resized_image = pil_image.resize((200, 200), Image.ANTIALIAS)
        else:
            resized_image = pil_image
         
        # Change orientation if the image is not oriented correctly
        if pic_orientation == 3:
            resized_image=resized_image.rotate(180, expand=True)
        elif pic_orientation == 6:
            resized_image=resized_image.rotate(270, expand=True)
        elif pic_orientation == 8:
            resized_image=resized_image.rotate(90, expand=True)

        return resized_image

class ModelImageHelpers():

    @staticmethod
    def save_model_mage(model):

        try:
            original_img = './accounts/management/commands/utils/createmedia_assets/images/no_image.jpg'

            image_file =  File(open(original_img, 'rb')) #File(path, "rb")

            model.image.save('.jpg', image_file)

        except:
            LoggerManager.log_critical_error() 

        
