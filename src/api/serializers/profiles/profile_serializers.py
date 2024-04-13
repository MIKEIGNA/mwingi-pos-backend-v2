from django.contrib.auth import get_user_model

from rest_framework import serializers
from core.image_utils import Base64ImageField

from profiles.models import Profile
from accounts.utils.validators import validate_phone_for_forms_n_serializers

class TpLeanUserProfileIndexViewSerializer(serializers.ModelSerializer):

    # Read only fields
    name = serializers.ReadOnlyField(source='get_full_name')
    reg_no = serializers.ReadOnlyField()

    class Meta:
        model = get_user_model()
        fields = (
            'name', 
            'reg_no',
        )
                
class ProfileEditViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(ProfileEditViewSerializer, self).__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    full_name = serializers.ReadOnlyField(source='user.get_full_name')
    currency_initials = serializers.ReadOnlyField(source='get_currency_initials')

    email = serializers.ReadOnlyField(source='user.email')
    image_url = serializers.ReadOnlyField(source='get_profile_image_url')
    join_date = serializers.SerializerMethodField()
    last_login_date = serializers.SerializerMethodField()
    phone =   serializers.IntegerField(required=True)

    class Meta:
        model = Profile
        fields = (
            'full_name', 
            'email', 
            'phone',
            'image_url', 
            'join_date', 
            'last_login_date',
            'business_name',
            'location', 
            'currency',
            'currency_initials',
        )
        
    def get_join_date(self, obj):
        return obj.get_join_date(self.user.get_user_timezone())
    
    def get_last_login_date(self, obj):
        return obj.get_last_login_date(self.user.get_user_timezone())

    """
    This validators will only work if the fields being validated are hardcoded 
    or overridden and manually typed above the class Meta:
    """
    def validate_phone(self, phone):
        """
        Raise a serializers.ValidationError if the phone is not correct safaricom
        number. 
        """
                
        """
        To implement DRY, we use this validator in forms and serializers
        """
        validate_phone_for_forms_n_serializers(phone, serializers.ValidationError)

        # Make sure phone is unique
        phone_exists = get_user_model().objects.filter(
            phone=phone).exclude(email=self.user).exists()

        if phone_exists:
            raise serializers.ValidationError("User with this phone already exists.")

        return phone

class ProfilePictureEditViewSerializer(serializers.ModelSerializer):

    uploaded_image = Base64ImageField(
        max_length=None, 
        use_url=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = Profile
        fields = ('uploaded_image',) 


