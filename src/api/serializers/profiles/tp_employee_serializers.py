from django.contrib.auth import get_user_model
from django.conf import settings

from rest_framework import serializers

from api.serializers.formset_serializers import StoreFormsetSerializer
from clusters.models import StoreCluster

from profiles.models import EmployeeProfile

from accounts.utils.validators import validate_phone_for_forms_n_serializers
from accounts.utils.user_type import USER_GENDER_CHOICES



class TpLeanEmployeeProfileIndexViewSerializer(serializers.ModelSerializer):

    # Read only fields
    name = serializers.ReadOnlyField(source='get_full_name')
    reg_no = serializers.ReadOnlyField()

    class Meta:
        model = EmployeeProfile
        fields = (
            'name', 
            'reg_no',
        )


class TpEmployeeProfileIndexViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(TpEmployeeProfileIndexViewSerializer, self).__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

        self.fields['role_reg_no'].write_only = True


    first_name = serializers.CharField(max_length=15, write_only=True)
    last_name = serializers.CharField(max_length=15, write_only=True)
    email = serializers.EmailField(max_length=30,
                                   required=True,
                                   write_only=True)
    phone =   serializers.IntegerField(required=True, write_only=True,)
    
    # Make sure max length matches that one of team profile
    gender = serializers.ChoiceField(USER_GENDER_CHOICES, write_only=True) 
    

    # Read only fields
    name = serializers.ReadOnlyField(source='get_full_name')
    user_email = serializers.ReadOnlyField(source='user.email')
    user_phone = serializers.ReadOnlyField(source='user.phone')
    role_name = serializers.ReadOnlyField()
    reg_no = serializers.ReadOnlyField()

    # List field
    stores_info = serializers.ListField(
        child=StoreFormsetSerializer(),
        allow_empty=False,
        max_length=settings.MAX_STORES_REG_MAX_LENGTH,
        write_only=True
    )

    class Meta:
        model = EmployeeProfile
        fields = (
            'first_name',
            'last_name',
            'email',
            'phone',
            'role_reg_no',
            'gender',
                
            'name', 
            'user_email',
            'user_phone',
            'role_name',
            'reg_no',

            'stores_info', # List field
        )
        
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
        """
        Raise a serializers.ValidationError if the phone is not correct
        number or unique. 
        """        
        """
        To implement DRY, we use this validator in forms and serializers
        """
        validate_phone_for_forms_n_serializers(phone, serializers.ValidationError)

        # Make sure phone is unique
        if get_user_model().objects.filter(phone=phone).exists():
            raise serializers.ValidationError("User with this phone already exists.")
        
        return phone

    def validate_role_reg_no(self, role_reg_no):

        error_msg = "Wrong role was selected"

        """ Check if reg_no is too big"""
         # If you change this in the future, change also in your apps verification processes
        if role_reg_no > 6000000000000:
            raise serializers.ValidationError(error_msg)

        return role_reg_no


class TpEmployeeProfileEditViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(TpEmployeeProfileEditViewSerializer, self).__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

        self.fields['role_reg_no'].write_only = True


    # Read only fields
    name = serializers.ReadOnlyField(source='get_full_name')
    user_email = serializers.ReadOnlyField(source='user.email')
    user_phone = serializers.ReadOnlyField(source='user.phone')
    reg_no = serializers.ReadOnlyField()
    

    # List field
    stores_info = serializers.ListField(
        child=StoreFormsetSerializer(),
        allow_empty=False,
        max_length=settings.MAX_STORES_REG_MAX_LENGTH,
        write_only=True
    )

    class Meta:
        model = EmployeeProfile
        fields = (
            'name', 
            'user_email',
            'user_phone',
            'role_reg_no',
            'reg_no',
            'stores_info', # List field
        )

    def to_representation(self, instance):
        context = super().to_representation(instance)
        
        context['roles'] = self.context['roles']
        context['registered_stores'] = self.context['registered_stores']
        context['available_stores'] = self.context['available_stores']
       
        return context 

    def validate_role_reg_no(self, role_reg_no):

        error_msg = "Wrong role was selected"

        """ Check if reg_no is too big"""
         # If you change this in the future, change also in your apps verification processes
        if role_reg_no > 6000000000000:
            raise serializers.ValidationError(error_msg)

        return role_reg_no



class EmployeeClusterFormsetSerializer(serializers.ModelSerializer):
    
    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = EmployeeProfile
        fields = ('reg_no',)



class TpEmployeeProfileClusterListSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='get_full_name')
    cluster_count = serializers.ReadOnlyField(source='get_registered_clusters_count')

    class Meta:
        model = EmployeeProfile
        fields = (
            'name',
            'cluster_count',
            'reg_no', 
        ) 



class TpEmployeeClusterViewSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='get_full_name')
    available_clusters = serializers.ReadOnlyField(source='get_available_clusters_data')
    registered_clusters = serializers.ReadOnlyField(source='get_registered_clusters_data')
    
    # List field
    clusters_info = serializers.ListField(
        child=EmployeeClusterFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['reg_no'].read_only=True

    class Meta:
        model = EmployeeProfile
        fields = (
            'name',
            'available_clusters',
            'registered_clusters',
            'reg_no', 
            'clusters_info'
        )