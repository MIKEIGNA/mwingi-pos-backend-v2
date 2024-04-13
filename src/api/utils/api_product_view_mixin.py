import os

from PIL import Image, ExifTags

from django.core.files import File
from django.conf import settings

class ApiProductViewMixin:
    
    def get_tax(self, profile, reg_no):

        # To avoid AppRegistryNotReady error in celery task, we call all the
        # imports locally
        from stores.models import Tax

        if reg_no:
            try:
                return Tax.objects.get(profile=profile, reg_no=reg_no)
            except: # pylint: disable=bare-except
                return None
        else:
            return None

    def get_category(self, profile, reg_no):

        # To avoid AppRegistryNotReady error in celery task, we call all the
        # imports locally
        from stores.models import Category

        if reg_no:
            try:
                return Category.objects.get(profile=profile, reg_no=reg_no)
            except: # pylint: disable=bare-except
                return None
        else:
            return None

    def crop_product_image(self, product, serializer):
        """
        Crops the provided image and saves it in the correct path
        """
        
        image = serializer.validated_data['image']
        
        image_name = image.name
        product_reg_no = product.reg_no
        
        temp_path = '{}/{}{}_{}_{}'.format(
            settings.MEDIA_ROOT, 
            settings.IMAGE_SETTINGS['product_images_dir'], 
            'temp_pic', 
            product_reg_no, image_name
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
            
            pic_orientation = exif[orientation] # pylint: disable=undefined-loop-variable
            
        except: # pylint: disable=bare-except
            pic_orientation = 0

     
        resized_image = pil_image.resize((200, 200), Image.ANTIALIAS)
        
        # Change orientation if the image is not oriented correctly
        if pic_orientation == 3:
            resized_image=resized_image.rotate(180, expand=True)
        elif pic_orientation == 6:
            resized_image=resized_image.rotate(270, expand=True)
        elif pic_orientation == 8:
            resized_image=resized_image.rotate(90, expand=True)
                  
        resized_image.save(temp_path)
                
        """
        Open the resized image and then save it directy to the product's image field
        """
        image_file =  File(open(temp_path, 'rb')) #File(path, "rb")
        
        image_name = image.name
        product.image.save(image_name, image_file)
        
        """
        Delete the first image that you saved after you resized the image
        """
        try:
            os.remove(temp_path)
        except: # pylint: disable=bare-except
            pass