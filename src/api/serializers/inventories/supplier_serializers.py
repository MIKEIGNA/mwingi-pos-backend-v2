from rest_framework import serializers

from inventories.models import Supplier

class LeanSupplierListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Supplier
        fields = ('name', 'reg_no')

class SupplierListSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        super().__init__(*args, **kwargs)

        self.fields['address'].write_only = True
        self.fields['city'].write_only = True
        self.fields['region'].write_only = True
        self.fields['postal_code'].write_only = True
        self.fields['country'].write_only = True
        


    # Read only fields
    reg_no = serializers.ReadOnlyField()
    
    class Meta:
        model = Supplier
        fields = (
            'name',
            'email',
            'phone',
            'address',
            'city',
            'region',
            'postal_code',
            'country',
            'reg_no'
        )
 
    def validate_name(self, name):
        
        # Check if the user already has a supplier with the same name
        supplier_exists = Supplier.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exists()
            
        if supplier_exists:
            
            msg = 'You already have a supplier with this name.'
            raise serializers.ValidationError(msg)

        return name

    def validate_email(self, email):

        # Only validate if email is not empty
        if not email:
            return email
        
        # Check if the user already has a supplier with the same name
        supplier_exists = Supplier.objects.filter(
            profile=self.current_user_profile,
            email=email
        ).exists()
            
        if supplier_exists:
            
            msg = 'You already have a supplier with this email.'
            raise serializers.ValidationError(msg)

        return email

    def validate_phone(self, phone):

        # Only validate if phone is not empty
        if not phone:
            return phone
        
        # Check if the user already has a supplier with the same name
        supplier_exists = Supplier.objects.filter(
            profile=self.current_user_profile,
            phone=phone
        ).exists()
            
        if supplier_exists:
            
            msg = 'You already have a supplier with this phone.'
            raise serializers.ValidationError(msg)

        return phone

    def validate_supplier_code(self, supplier_code):

        # Only validate if supplier code is not empty
        if not supplier_code:
            return supplier_code
        
        # Check if the user already has a supplier with the same name
        supplier_exists = Supplier.objects.filter(
            profile=self.current_user_profile,
            supplier_code=supplier_code
        ).exists()
            
        if supplier_exists:
            
            msg = 'You already have a supplier with this phone.'
            raise serializers.ValidationError(msg)

        return supplier_code

class SupplierViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        self.supplier_reg_no = kwargs.pop('supplier_reg_no')

        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    # Read only fields
    reg_no = serializers.ReadOnlyField()
    location_desc = serializers.ReadOnlyField(source='get_location_desc')
    creation_date = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = (
            'name',
            'email',
            'phone',
            'address',
            'city',
            'region',
            'postal_code',
            'country',
            'reg_no',

            'location_desc',
            'creation_date'
        )

    def get_creation_date(self, obj):
        return obj.get_created_date(self.user.get_user_timezone())

    def validate_name(self, name):
        
        # Check if the user already has a supplier with the same name
        supplier_exists = Supplier.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exclude(reg_no=self.supplier_reg_no).exists()
            
        if supplier_exists:
            
            msg = 'You already have a supplier with this name.'
            raise serializers.ValidationError(msg)

        return name

    def validate_email(self, email):

        # Only validate if email is not empty
        if not email:
            return email
        
        # Check if the user already has a supplier with the same name
        supplier_exists = Supplier.objects.filter(
            profile=self.current_user_profile,
            email=email
        ).exclude(reg_no=self.supplier_reg_no).exists()
            
        if supplier_exists:
            
            msg = 'You already have a supplier with this email.'
            raise serializers.ValidationError(msg)

        return email

    def validate_phone(self, phone):

        # Only validate if phone is not empty
        if not phone:
            return phone
        
        # Check if the user already has a supplier with the same name
        supplier_exists = Supplier.objects.filter(
            profile=self.current_user_profile,
            phone=phone
        ).exclude(reg_no=self.supplier_reg_no).exists()
            
        if supplier_exists:
            
            msg = 'You already have a supplier with this phone.'
            raise serializers.ValidationError(msg)

        return phone

    

