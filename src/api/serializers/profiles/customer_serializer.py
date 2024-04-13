from rest_framework import serializers
from clusters.models import StoreCluster

from profiles.models import Customer


class LeanCustomerIndexViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = (
            'name', 
            'reg_no',
        )

class CustomerListSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        super().__init__(*args, **kwargs)

        # self.fields['village_name'].write_only = True
        self.fields['phone'].write_only = True
        self.fields['address'].write_only = True
        self.fields['city'].write_only = True
        self.fields['region'].write_only = True
        self.fields['postal_code'].write_only = True
        self.fields['country'].write_only = True
        self.fields['customer_code'].write_only = True
        self.fields['credit_limit'].write_only = True

    # Read only fields
    non_null_phone = serializers.ReadOnlyField(source='get_non_null_phone')
    points = serializers.ReadOnlyField()

    last_visit = serializers.ReadOnlyField(source='get_last_visit')
    total_visits = serializers.ReadOnlyField(source='get_total_visits')
    total_spent = serializers.ReadOnlyField(source='get_total_spent')
    cluster_data = serializers.ReadOnlyField(source='get_cluster_data')

    reg_no = serializers.ReadOnlyField()

    cluster_reg_no = serializers.IntegerField(write_only=True)

    class Meta:
        model = Customer
        fields = (
            'name',
            'email',
            'village_name',
            'non_null_phone',
            'phone',
            'cluster_data',
            'address',
            'city',
            'region',
            'postal_code',
            'country',
            'customer_code',
            'credit_limit',
            'last_visit',
            'total_visits',
            'total_spent',
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

class CustomerViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        self.customer_reg_no = kwargs.pop('customer_reg_no')
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    # Read only fields
    points = serializers.ReadOnlyField()
    
    location_desc = serializers.ReadOnlyField(source='get_location_desc')
    cluster_data = serializers.ReadOnlyField(source='get_cluster_data')
    first_visit = serializers.ReadOnlyField(source='get_first_visit')
    last_visit = serializers.ReadOnlyField(source='get_last_visit')
    sales_count = serializers.ReadOnlyField(source='get_sales_count')
    total_spent = serializers.ReadOnlyField(source='get_total_spent')
    reg_no = serializers.ReadOnlyField()
    creation_date = serializers.SerializerMethodField()

    cluster_reg_no = serializers.IntegerField(write_only=True)
    
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
            'cluster_reg_no',

            'current_debt',
            'points',
            'location_desc',
            'cluster_data',
            'first_visit',
            'last_visit',
            'sales_count',
            'total_spent',
            'reg_no',
            'creation_date',

        )

    def get_creation_date(self, obj):
        return obj.get_created_date(self.user.get_user_timezone())

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
