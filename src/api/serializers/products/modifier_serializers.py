from django.conf import settings
from rest_framework import serializers
from api.serializers.formset_serializers import StoreFormsetSerializer

from products.models import Modifier, ModifierOption

class ModifierOptionLineFormsetSerializer(serializers.ModelSerializer):

    class Meta:
        model = ModifierOption
        fields = ('name', 'price')

class ModifierOptionsFormsetSerializer(serializers.ModelSerializer):
    
    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    is_dirty = serializers.BooleanField(required=True, write_only=True)
    class Meta:
        model = ModifierOption
        fields = (
            'name',
            'price',
            'reg_no',
            'is_dirty'
        )

    def validate_reg_no(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided wrong stores'

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000: # If you change this in the future, change also in your apps verification processes
            raise serializers.ValidationError(error_msg)
        
        return reg_no


class LeanModifierListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modifier
        fields = ('name', 'reg_no',)

class ModifierListSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        self.current_user_profile = None

        if kwargs.get('current_user_profile', None):
            self.current_user_profile = kwargs.pop('current_user_profile')

        super().__init__(*args, **kwargs)

    # Read only fields
    description = serializers.ReadOnlyField()
    reg_no = serializers.ReadOnlyField()

    # List field
    modifier_options = serializers.ListField(
        child=ModifierOptionLineFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_MODIFIER_OPTION_COUNT,
        write_only=True
    )
    # List field
    stores_info = serializers.ListField(
        child=StoreFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_STORE_PER_ACCOUNT,
        write_only=True
    ) 
    class Meta:
        model = Modifier
        fields = ('name', 'description', 'reg_no', 'modifier_options', 'stores_info')

    def validate_name(self, name):
        
        # Check if the user already has a model with the same name
        model_exists = Modifier.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exists()
            
        if model_exists:
            
            msg = 'You already have a modifier with this name.'
            raise serializers.ValidationError(msg)

        return name


class ModifierViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        self.current_user_profile = None
        self.modifier_reg_no = None

        if kwargs.get('modifier_reg_no', None):
            self.modifier_reg_no = kwargs.pop('modifier_reg_no')

        if kwargs.get('current_user_profile', None):
            self.current_user_profile = kwargs.pop('current_user_profile')

        super().__init__(*args, **kwargs)

    reg_no = serializers.ReadOnlyField()
    options = serializers.ReadOnlyField(source='get_modifier_options')

    # List field
    options_info = serializers.ListField(
        child=ModifierOptionsFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_MODIFIER_OPTION_COUNT,
        write_only=True
    )
    # List field
    stores_info = serializers.ListField(
        child=StoreFormsetSerializer(),
        allow_empty=False,
        max_length=settings.MAX_STORE_PER_ACCOUNT,
        write_only=True
    ) 

    class Meta:
        model = Modifier
        fields = (
            'name',
            'reg_no',
            'options',
            'options_info',
            'stores_info'
        )

    def validate_name(self, name):
        
        # Check if the user already has a modifier (other than this one) with the same name
        modifier_exists = Modifier.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exclude(reg_no=self.modifier_reg_no).exists()
            
        if modifier_exists:
            msg = 'You already have a modifier with this name.'
            raise serializers.ValidationError(msg)

        return name

    def to_representation(self, instance):
        context = super().to_representation(instance)
        
        context['registered_stores'] = self.context['registered_stores']
        context['available_stores'] = self.context['available_stores']
       
        return context 