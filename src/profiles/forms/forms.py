from PIL import Image, ExifTags

from django import forms
from django.contrib.auth import get_user_model

from core.core_forms import MyTextInput, MyTextarea, MqModelForm
from core.form_utils.form_helper_mixins import UserFormCleanPhoneNumbersMixin
from core.form_utils.profile_image_cropper import ProfileImageCropperClass

from billing.forms_mixin import IgnoreRegNoErrorMixin

from profiles.models import Profile



User = get_user_model()



class ProfileAdminForm(forms.ModelForm):
    """ Add widget to fields """
    
    def __init__(self, *args, **kwargs):
        super(ProfileAdminForm, self).__init__(*args, **kwargs)

        # When user viewing admin has no profile change permission, phone is
        # in the fields
        if (self.fields.get('phone', None)):
            self.fields['phone'].widget=MyTextInput()

class TeamAdminChangeForm(IgnoreRegNoErrorMixin, forms.ModelForm):
    """
    The 'IgnoreRegNoErrorMixin' overrides the 'add_error' methods so that it 
    can ignore all the reg_no errors that might be raised by the tracker's model
    clean method since we dont use reg_no in this form's fields
    
    This is how the method looks now in the IgnoreRegNoErrorMixin -- NB Dont uncomment this
    
    def add_error(self, field, error):
    
        if not "'reg_no'" in str(error):
            super(IgnoreRegNoErrorMixin, self).add_error(field, error)
    """



class ProfileEditForm(UserFormCleanPhoneNumbersMixin, MqModelForm):
    
    def __init__(self, *args, **kwargs):
        
        # Used by UserFormCleanPhoneNumbersMixin's clean_phone method
        self.user = kwargs.pop('user', None)
        
        super(ProfileEditForm, self).__init__(*args, **kwargs)

        self.fields['phone'].widget=MyTextInput()
        self.fields['phone'].required = True
        self.fields['location'].widget=MyTextInput()
        self.fields['location'].required = True
        self.fields['currency'].widget.attrs = {
            'class': 'form-control',
            'required': '',}
        
    class Meta:
        model = Profile
        fields = [
            'phone', 
            'location', 
            'currency',
        ]



   

class ProfilePictureForm(MqModelForm):
    
    x = forms.FloatField(widget=forms.HiddenInput())
    y = forms.FloatField(widget=forms.HiddenInput())
    width = forms.FloatField(widget=forms.HiddenInput())
    height = forms.FloatField(widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        super(ProfilePictureForm, self).__init__(*args, **kwargs)
        self.fields['image'].required = True
        self.fields['image'].blank = False
        self.fields['image'].label = "Upload Profile Picture"
        
        # Fields with hide as their label, their labels are hidden from view
        self.fields['x'].label = 'hide'
        self.fields['y'].label = 'hide'
        self.fields['width'].label = 'hide'
        self.fields['height'].label = 'hide'
        
        
    class Meta:
        model = Profile
        fields = ['image', 'x', 'y', 'width', 'height', ]
        widgets = {
            'image': forms.FileInput(),
            }
        

    def clean(self):
        cleaned_data = super().clean()
        
        try:
            image = cleaned_data.get("image")
            
            if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.add_error('image', "Allowed image extensions are .jpg, .jpeg and .png")
            
        except:
            self.add_error('image', "Provide a valid image")
                
        x = cleaned_data.get("x")
        y = cleaned_data.get("y")
        height = cleaned_data.get("height")
        width = cleaned_data.get("width")
        
        fields = [x, y, height, width]
        
        for field in fields:
            
            if int(field) > 6000:
                self.add_error('image', "Provide a valid image.")
                
        
    def save(self):
        profile_image = super(ProfilePictureForm, self).save()
        
        width = self.cleaned_data.get('width')
        height = self.cleaned_data.get('height')
        
        x_point = self.cleaned_data.get('x')
        y_point = self.cleaned_data.get('y')
        
        
        # Crops the profile image into the required dimensions and then saves it
        ProfileImageCropperClass.crop_profile_image(
                width, 
                height, 
                x_point, 
                y_point, 
                profile_image)
        
        return profile_image   
    

    
class TeamProfileEditForm(UserFormCleanPhoneNumbersMixin, MqModelForm):
    
    def __init__(self, *args, **kwargs):
        
        # Used by UserFormCleanPhoneNumbersMixin's clean_phone method
        self.user = kwargs.pop('user', None)
        
        super(TeamProfileEditForm, self).__init__(*args, **kwargs)
        self.fields['location'].widget=MyTextInput()
        self.fields['location'].required = True
        self.fields['phone'].widget=MyTextInput()
        self.fields['phone'].required = True
        
    class Meta:
        model = Profile
        fields = ['location', 'phone'] 
        
        
class TeamProfilePictureForm(MqModelForm):
    
    x = forms.FloatField(widget=forms.HiddenInput())
    y = forms.FloatField(widget=forms.HiddenInput())
    width = forms.FloatField(widget=forms.HiddenInput())
    height = forms.FloatField(widget=forms.HiddenInput())
        
    def __init__(self, *args, **kwargs):
        super(TeamProfilePictureForm, self).__init__(*args, **kwargs)
        self.fields['image'].required = True
        self.fields['image'].blank = False
        self.fields['image'].label = "Upload Profile Picture"
        
        # Fields with hide as their label, their labels are hidden from view
        self.fields['x'].label = 'hide'
        self.fields['y'].label = 'hide'
        self.fields['width'].label = 'hide'
        self.fields['height'].label = 'hide'
        
        
    class Meta:
        model = Profile
        fields = ['image', 'x', 'y', 'width', 'height', ]
        widgets = {
            'image': forms.FileInput(),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        
        try:
            image = cleaned_data.get("image")
            
            if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.add_error('image', "Allowed image extensions are .jpg, .jpeg and .png")
            
        except:
            self.add_error('image', "Provide a valid image")
                
        x = cleaned_data.get("x")
        y = cleaned_data.get("y")
        height = cleaned_data.get("height")
        width = cleaned_data.get("width")
        
        fields = [x, y, height, width]
        
        for field in fields:
            
            if int(field) > 6000:
                self.add_error('image', "Provide a valid image.")
        
        
        
        
    def save(self):
        profile_image = super(TeamProfilePictureForm, self).save()
        
        w = self.cleaned_data.get('width')
        h = self.cleaned_data.get('height')

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
            x_value = self.cleaned_data.get('y')
            y_value = self.cleaned_data.get('x')
        else:
            x_value = self.cleaned_data.get('x')
            y_value = self.cleaned_data.get('y')
            
        
        # Crop the image
        cropped_image = pil_image.crop((x_value, y_value, w+x_value, h+y_value))
        resized_image = cropped_image.resize((200, 200), Image.ANTIALIAS)
        
    
        # Change orientation if the image is not oriented correctly
        if pic_orientation == 3:
            resized_image=resized_image.rotate(180, expand=True)
        elif pic_orientation == 6:
            resized_image=resized_image.rotate(270, expand=True)
        elif pic_orientation == 8:
                resized_image=resized_image.rotate(90, expand=True)
 
        resized_image.save(profile_image.image.path)
            
        return profile_image 