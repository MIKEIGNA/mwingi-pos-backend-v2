from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import get_user_model
from django.conf import settings

from rest_framework import serializers

from accounts.utils.validators import validate_phone_for_forms_n_serializers
from accounts.utils.user_type import TOP_USER
from accounts.models import WebSocketTicket

from profiles.models import Profile
from accounts.utils.currency_choices import CURRENCY_CHOICES
from stores.models import Store

class UserSerializer(serializers.ModelSerializer): 

    phone = serializers.IntegerField(required=True,)
    email = serializers.EmailField(max_length=30,
                                   required=True)
    # Make sure these fields max length matches those one on profile model
    business_name = serializers.CharField(max_length=60, write_only=True)
    location = serializers.CharField(max_length=30, write_only=True)

    password = serializers.CharField(min_length=8, 
                                     max_length=50,
                                     write_only=True)
    
    
    
    
    class Meta:
        model = get_user_model()
        fields = ('first_name', 
                  'last_name', 
                  'email', 
                  'phone', 
                  'business_name',
                  'location', 
                  'gender',
                  'password')
        
    def create(self, validated_data):
    
        # Use pop to remove these values from validate_data and store them
        # so that we can use them in update the profile
        business_name = validated_data.pop("business_name")
        location = validated_data.pop("location")

        user = super(UserSerializer, self).create(validated_data)
        
        user.user_type = TOP_USER
        user.set_password(validated_data['password'])
        user.save()
        
        try:
            # Update profile
            profile = Profile.objects.get(user__email=user)
            profile.business_name = business_name
            profile.location = location
            profile.save()

            Store.objects.create(
                profile=profile,
                name=settings.DEFAULT_STORE_NAME,
                address=location
            )
            
        except:
            # TODO log
            pass
        
        return user
    
    """
    This validators will only work if the fields being validated are hardcoded 
    or overridden and manually typed above the class Meta:
    """
    def validate_email(self, email):
        """
        Raise a serializers.ValidationError if the email is not unique. 
        """ 
        
        # Make sure email is unique
        if get_user_model().objects.filter(email=email).exists():
            raise serializers.ValidationError(
        "User with this Email already exists.")

        # Always return a value even if this method didn't change it.
        return email
        
    def validate_phone(self, phone):
        
        """Raise a serializers.ValidationError if the phone is not a 
        correct number. 
        """        
        """
        To implement DRY, we use this validator in forms and serializers
        """
        validate_phone_for_forms_n_serializers(phone, serializers.ValidationError)

        # Make sure phone is unique
        if get_user_model().objects.filter(phone=phone).exists():
            raise serializers.ValidationError("User with this phone already exists.")
        
        return phone
    
# The password change solution was inspired by django-rest-auth package
class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=50)
    new_password1 = serializers.CharField(max_length=50)
    new_password2 = serializers.CharField(max_length=50)

    set_password_form_class = SetPasswordForm

    def __init__(self, *args, **kwargs):
        
        super(PasswordChangeSerializer, self).__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    def validate_old_password(self, value):
        
        # Check if old_password is correct
        if not self.user.check_password(value):
            err_msg ="Your old password was entered incorrectly. Please enter it again."
            raise serializers.ValidationError(err_msg)
            
        return value

    def validate(self, attrs):

        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs
        )

        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        return attrs

    def save(self):
        self.set_password_form.save()




        
class HijackSerializer(serializers.Serializer):
    reg_no = serializers.IntegerField(required=True)
