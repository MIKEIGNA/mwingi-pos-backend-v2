from rest_framework import serializers
from clusters.models import StoreCluster

from profiles.models import Customer

class CustomerPosListSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        super().__init__(*args, **kwargs)

    # Read only fields
    cluster_data = serializers.ReadOnlyField(source='get_cluster_data')
    non_null_phone = serializers.ReadOnlyField(source='get_non_null_phone')
    current_debt = serializers.ReadOnlyField()
    points = serializers.ReadOnlyField()
    reg_no = serializers.ReadOnlyField()

    cluster_reg_no = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Customer
        fields = (
            'name',
            'email',
            'village_name',
            'cluster_data',
            'non_null_phone',
            'phone',
            'address',
            'city',
            'region',
            'postal_code',
            'country',
            'customer_code',
            'credit_limit',
            'current_debt',
            'points',
            'reg_no',
            'cluster_reg_no'
        )

    def validate_name(self, name):
        
        # Check if the user already has a customer with the same name
        customer_exists = Customer.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exists()
            
        if customer_exists:
            
            msg = 'You already have a customer with this name.'
            raise serializers.ValidationError(msg)

        return name
    
    def validate_cluster_reg_no(self, cluster_reg_no):

        # Check if store cluster is valid
        cluster_exists = StoreCluster.objects.filter(reg_no=cluster_reg_no).exists()
            
        if not cluster_exists:
            
            msg = 'Cluster does not exist.'
            raise serializers.ValidationError(msg)

        return cluster_reg_no

    def validate_email(self, email):

        # Only validate if email is not empty
        if not email:
            return email
        
        # Check if the user already has a customer with the same name
        customer_exists = Customer.objects.filter(
            profile=self.current_user_profile,
            email=email
        ).exists()
            
        if customer_exists:
            
            msg = 'You already have a customer with this email.'
            raise serializers.ValidationError(msg)

        return email

    def validate_phone(self, phone):

        # Only validate if phone is not empty
        if not phone:
            return phone
        
        # Check if the user already has a customer with the same name
        customer_exists = Customer.objects.filter(
            profile=self.current_user_profile,
            phone=phone
        ).exists()
            
        if customer_exists:
            
            msg = 'You already have a customer with this phone.'
            raise serializers.ValidationError(msg)

        return phone

    def validate_customer_code(self, customer_code):

        # Only validate if customer code is not empty
        if not customer_code:
            return customer_code
        
        # Check if the user already has a customer with the same name
        customer_exists = Customer.objects.filter(
            profile=self.current_user_profile,
            customer_code=customer_code
        ).exists()
            
        if customer_exists:
            
            msg = 'You already have a customer with this phone.'
            raise serializers.ValidationError(msg)

        return customer_code

class CustomerPosViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        self.customer_reg_no = kwargs.pop('customer_reg_no')
        super().__init__(*args, **kwargs)

    cluster_reg_no = serializers.IntegerField(write_only=True)

    # Read only fields
    reg_no = serializers.ReadOnlyField()
    
    class Meta:
        model = Customer
        fields = (
            'name',
            'email',
            'village_name',
            'phone',
            'address',
            'city',
            'region',
            'postal_code',
            'country',
            'customer_code',
            'credit_limit',
            'reg_no',

            'cluster_reg_no'
        )

    def validate_name(self, name):
        
        # Check if the user already has a customer with the same name
        customer_exists = Customer.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exclude(reg_no=self.customer_reg_no).exists()
            
        if customer_exists:
            
            msg = 'You already have a customer with this name.'
            raise serializers.ValidationError(msg)

        return name
    
    def validate_cluster_reg_no(self, cluster_reg_no):

        # Check if store cluster is valid
        cluster_exists = StoreCluster.objects.filter(reg_no=cluster_reg_no).exists()
            
        if not cluster_exists:
            
            msg = 'Cluster does not exist.'
            raise serializers.ValidationError(msg)

        return cluster_reg_no

    def validate_email(self, email):

        # Only validate if email is not empty
        if not email:
            return email
        
        # Check if the user already has a customer with the same name
        customer_exists = Customer.objects.filter(
            profile=self.current_user_profile,
            email=email
        ).exclude(reg_no=self.customer_reg_no).exists()
            
        if customer_exists:
            
            msg = 'You already have a customer with this email.'
            raise serializers.ValidationError(msg)

        return email

    def validate_phone(self, phone):

        # Only validate if phone is not empty
        if not phone:
            return phone
        
        # Check if the user already has a customer with the same name
        customer_exists = Customer.objects.filter(
            profile=self.current_user_profile,
            phone=phone
        ).exclude(reg_no=self.customer_reg_no).exists()
            
        if customer_exists:
            
            msg = 'You already have a customer with this phone.'
            raise serializers.ValidationError(msg)

        return phone

    def validate_customer_code(self, customer_code):

        # Only validate if customer code is not empty
        if not customer_code:
            return customer_code
        
        # Check if the user already has a customer with the same name
        customer_exists = Customer.objects.filter(
            profile=self.current_user_profile,
            customer_code=customer_code
        ).exclude(reg_no=self.customer_reg_no).exists()
            
        if customer_exists:
            
            msg = 'You already have a customer with this phone.'
            raise serializers.ValidationError(msg)

        return customer_code

