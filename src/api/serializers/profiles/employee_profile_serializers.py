from django.contrib.auth import get_user_model

from rest_framework import serializers

from core.image_utils import Base64ImageField

from profiles.models import EmployeeProfile
from accounts.utils.validators import validate_phone_for_forms_n_serializers

User = get_user_model()


class EpLeanUserProfileIndexViewSerializer(serializers.ModelSerializer):

    # Read only fields
    name = serializers.ReadOnlyField(source='get_full_name')
    reg_no = serializers.ReadOnlyField()

    class Meta:
        model = get_user_model()
        fields = (
            'name', 
            'reg_no',
        )
                
class EmployeeProfileEditViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(EmployeeProfileEditViewSerializer, self).__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)
    
    # TODO consider removing every field apart from phone in Car and Pta Trackers
    full_name = serializers.ReadOnlyField(source='user.get_full_name')
    email = serializers.ReadOnlyField(source='user.email')
    image_url = serializers.ReadOnlyField(source='get_profile_image_url')
    join_date = serializers.SerializerMethodField()
    last_login_date = serializers.SerializerMethodField()
    phone =   serializers.IntegerField(required=True)
    
    class Meta:
        model = EmployeeProfile
        fields = (
            'full_name', 
            'email', 
            'image_url', 
            'join_date', 
            'last_login_date',
            'location', 
            'phone' 
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
        phone_exists = User.objects.filter(
            phone=phone).exclude(email=self.user).exists()

        if phone_exists:
            raise serializers.ValidationError("User with this phone already exists.")

        return phone
        
class EmployeeProfilePictureEditViewSerializer(serializers.ModelSerializer):

    uploaded_image = Base64ImageField(
        max_length=None, 
        use_url=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = EmployeeProfile
        fields = ('uploaded_image',) 

