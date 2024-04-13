from django.conf import settings
from rest_framework import serializers
from api.serializers.formset_serializers import StoreFormsetSerializer

from stores.models import Discount

# ===================================== Web serializer

class DiscountListSerializer(serializers.ModelSerializer):
    reg_no = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):

        self.current_user_profile = None

        if kwargs.get('current_user_profile', None):
            self.current_user_profile = kwargs.pop('current_user_profile')

        super().__init__(*args, **kwargs)

    # List field
    stores_info = serializers.ListField(
        child=StoreFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_STORE_PER_ACCOUNT,
        write_only=True
    ) 

    class Meta:
        model = Discount
        fields = ('name', 'amount', 'reg_no', 'stores_info')
        
    
    def validate_name(self, name):
        
        # Check if the user already has a discount with the same name
        discount_exists = Discount.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exists()
            
        if discount_exists:
            
            msg = 'You already have a discount with this name.'
            raise serializers.ValidationError(msg)

        return name


class DiscountEditViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        self.current_user_profile = None
        self.discount_reg_no = None

        if kwargs.get('discount_reg_no', None):
            self.discount_reg_no = kwargs.pop('discount_reg_no')

        if kwargs.get('current_user_profile', None):
            self.current_user_profile = kwargs.pop('current_user_profile')

        super().__init__(*args, **kwargs)

    reg_no = serializers.ReadOnlyField()

    # List field
    stores_info = serializers.ListField(
        child=StoreFormsetSerializer(),
        allow_empty=False,
        max_length=settings.MAX_STORE_PER_ACCOUNT,
        write_only=True
    ) 

    class Meta:
        model = Discount
        fields = ('name', 'amount', 'reg_no', 'stores_info') 

    def validate_name(self, name):
        
        # Check if the user already has a discount (other than this one) with the same name
        discount_exists = Discount.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exclude(reg_no=self.discount_reg_no).exists()
            
        if discount_exists:
            msg = 'You already have a discount with this name.'
            raise serializers.ValidationError(msg)

        return name

    def to_representation(self, instance):
        context = super().to_representation(instance)
        
        context['registered_stores'] = self.context['registered_stores']
        context['available_stores'] = self.context['available_stores']
       
        return context 


# ===================================== Pos serializer
class DiscountPosListSerializer(serializers.ModelSerializer):
    reg_no = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        super().__init__(*args, **kwargs)

    class Meta:
        model = Discount
        fields = ('name', 'amount', 'reg_no',)
        
    
    def validate_name(self, name):
        
        # Check if the user already has a discount with the same name
        discount_exists = Discount.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exists()
            
        if discount_exists:
            
            msg = 'You already have a discount with this name.'
            raise serializers.ValidationError(msg)

        return name


class DiscountPosEditViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        self.discount_reg_no = kwargs.pop('discount_reg_no')
        super().__init__(*args, **kwargs)

    reg_no = serializers.ReadOnlyField()

    class Meta:
        model = Discount
        fields = ('name', 'amount', 'reg_no') 

    def validate_name(self, name):
        
        # Check if the user already has a discount (other than this one) with the same name
        discount_exists = Discount.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exclude(reg_no=self.discount_reg_no).exists()
            
        if discount_exists:
            msg = 'You already have a discount with this name.'
            raise serializers.ValidationError(msg)

        return name