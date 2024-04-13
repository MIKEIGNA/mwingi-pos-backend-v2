from rest_framework import serializers

from stores.models import Store
class LeanStoreListSerializer(serializers.ModelSerializer):
    
    deletion_date = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    class Meta:
        model = Store
        fields = (
            'name', 
            'is_shop', 
            'is_truck', 
            'is_warehouse', 
            'increamental_id', 
            'reg_no',
            'is_deleted',
            'deletion_date'
        )  

    def get_deletion_date(self, obj):
        return obj.get_deleted_date(self.user.get_user_timezone())

class LeanStoreWithReceiptSettingListSerializer(serializers.ModelSerializer):

    receipt_setting = serializers.ReadOnlyField(source='get_receipt_setting')
    deletion_date = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    class Meta:
        model = Store
        fields = (
            'name', 
            'reg_no', 
            'receipt_setting',
            'is_deleted',
            'deletion_date'
        )

    def get_deletion_date(self, obj):
        return obj.get_deleted_date(self.user.get_user_timezone())

class StoreListCreateSerializer(serializers.ModelSerializer):
    reg_no = serializers.ReadOnlyField()
    employee_count = serializers.ReadOnlyField(source='get_employee_count')

    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        super().__init__(*args, **kwargs)

    class Meta:
        model = Store
        fields = ('name', 'address', 'reg_no', 'employee_count')
        
    def validate_name(self, name):
        
        # Check if the user already has a store with the same name
        store_exists = Store.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exists()
            
        if store_exists:
            
            msg = 'You already have a store with this name.'
            raise serializers.ValidationError(msg)

        return name


class StoreListSerializer(serializers.ModelSerializer):
    reg_no = serializers.ReadOnlyField()
    employee_count = serializers.ReadOnlyField(source='get_employee_count')
    class Meta:
        model = Store
        fields = ('name', 'address', 'reg_no', 'employee_count')
        
class StoreEditViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        self.store_reg_no = kwargs.pop('store_reg_no')

        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    reg_no = serializers.ReadOnlyField()

    class Meta:
        model = Store
        fields = ('name', 'address', 'reg_no') 
    
    def validate_name(self, name):
        
        # Check if the user already has a store (other than this one) with the same name
        store_exists = Store.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exclude(reg_no=self.store_reg_no).exists()
            
        if store_exists:
            msg = 'You already have a store with this name.'
            raise serializers.ValidationError(msg)

        return name