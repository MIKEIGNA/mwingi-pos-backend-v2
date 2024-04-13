from rest_framework import serializers

from django.conf import settings

from api.serializers.formset_serializers import StoreFormsetSerializer

from stores.models import Tax


# ===================================== Web serializer
class TaxListSerializer(serializers.ModelSerializer):
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
        model = Tax
        fields = ('name', 'rate', 'reg_no', 'stores_info')
        
    
    def validate_name(self, name):
        
        # Check if the user already has a tax with the same name
        tax_exists = Tax.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exists()
            
        if tax_exists:
            
            msg = 'You already have a tax with this name.'
            raise serializers.ValidationError(msg)

        return name


class TaxEditViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        self.current_user_profile = None
        self.tax_reg_no = None

        if kwargs.get('tax_reg_no', None):
            self.tax_reg_no = kwargs.pop('tax_reg_no')

        if kwargs.get('current_user_profile', None):
            self.current_user_profile = kwargs.pop('current_user_profile')

        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    reg_no = serializers.ReadOnlyField()

    # List field
    stores_info = serializers.ListField(
        child=StoreFormsetSerializer(),
        allow_empty=False,
        max_length=settings.MAX_STORE_PER_ACCOUNT,
        write_only=True
    ) 

    class Meta:
        model = Tax
        fields = ('name', 'rate', 'reg_no', 'stores_info') 

    def validate_name(self, name):
        
        # Check if the user already has a tax (other than this one) with the same name
        tax_exists = Tax.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exclude(reg_no=self.tax_reg_no).exists()
            
        if tax_exists:
            msg = 'You already have a tax with this name.'
            raise serializers.ValidationError(msg)

        return name

    def to_representation(self, instance):
        context = super().to_representation(instance)
        
        context['registered_stores'] = self.context['registered_stores']
        context['available_stores'] = self.context['available_stores']
       
        return context 

# ===================================== Pos serializer
class TaxPosListSerializer(serializers.ModelSerializer):
    reg_no = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        super().__init__(*args, **kwargs)

    class Meta:
        model = Tax
        fields = ('name', 'rate', 'reg_no',)
        
    
    def validate_name(self, name):
        
        # Check if the user already has a tax with the same name
        tax_exists = Tax.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exists()
            
        if tax_exists:
            
            msg = 'You already have a tax with this name.'
            raise serializers.ValidationError(msg)

        return name


class TaxPosEditViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        self.tax_reg_no = kwargs.pop('tax_reg_no')

        super().__init__(*args, **kwargs)

    reg_no = serializers.ReadOnlyField()

    class Meta:
        model = Tax
        fields = ('name', 'rate', 'reg_no') 

    def validate_name(self, name):
        
        # Check if the user already has a tax (other than this one) with the same name
        tax_exists = Tax.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exclude(reg_no=self.tax_reg_no).exists()
            
        if tax_exists:
            msg = 'You already have a tax with this name.'
            raise serializers.ValidationError(msg)

        return name