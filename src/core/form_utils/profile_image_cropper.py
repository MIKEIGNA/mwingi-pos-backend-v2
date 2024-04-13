from PIL import Image, ExifTags


class ProfileImageCropperClass:
    @staticmethod
    def crop_profile_image(width, height, x_point, y_point, profile_image):
        
        pil_image = Image.open(profile_image.image)
        
        # Try to get the image orientation
        pic_orientation = 0
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation]=='Orientation':
                    break
                
            exif=dict(pil_image._getexif().items())
            
            pic_orientation = exif[orientation]
            
        except:
            
            pic_orientation = 0
            
        # Interchange x and y values if the image is oriented by 6
        if pic_orientation == 6:
            x_value = y_point
            y_value = x_point
        else:
            x_value = x_point
            y_value = y_point
            
        
        # Crop the image
        cropped_image = pil_image.crop((x_value, y_value, width+x_value, height+y_value))
        resized_image = cropped_image.resize((200, 200), Image.ANTIALIAS)
        
    
        # Change orientation if the image is not oriented correctly
        if pic_orientation == 3:
            resized_image=resized_image.rotate(180, expand=True)
        elif pic_orientation == 6:
            resized_image=resized_image.rotate(270, expand=True)
        elif pic_orientation == 8:
                resized_image=resized_image.rotate(90, expand=True)
 
        resized_image.save(profile_image.image.path)
    
    
    
