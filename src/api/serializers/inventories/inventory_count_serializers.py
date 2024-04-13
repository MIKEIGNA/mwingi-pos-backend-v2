from collections import OrderedDict
from django.conf import settings
from rest_framework import serializers

from inventories.models import InventoryCount, InventoryCountLine


class InventoryCountLineFormsetSerializer(serializers.ModelSerializer):
    product_reg_no = serializers.IntegerField(write_only=True)

    class Meta:
        model = InventoryCountLine
        fields = (
            'product_reg_no',

            'expected_stock',
            'counted_stock',
        )

class InventoryCountListSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='__str__')
    store_name = serializers.ReadOnlyField(source='get_store_name')
    reg_no = serializers.ReadOnlyField()
    creation_date = serializers.SerializerMethodField()
    completion_date = serializers.SerializerMethodField()

    store_reg_no = serializers.IntegerField(write_only=True)

    # List field
    inventory_count_lines = serializers.ListField(
        child=InventoryCountLineFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_STOCK_ADJUSTMENT_LINE_COUNT,
        write_only=True
    ) 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

        self.fields['notes'].write_only = True

    class Meta:
        model = InventoryCount
        fields = (
            'name',
            'notes',
            'store_name',
            'status',
            'reg_no',
            'creation_date',
            'completion_date',
            
            'store_reg_no',
            'inventory_count_lines'
        )

    def get_creation_date(self, obj):

        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return '-'

        return obj.get_created_date(self.user.get_user_timezone())
    
    def get_completion_date(self, obj):

        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return '-'

        return obj.get_completed_date(self.user.get_user_timezone())
    


class InventoryCountLineEditFormsetSerializer(serializers.ModelSerializer):

    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)

    class Meta:
        model = InventoryCountLine
        fields = (
            'expected_stock',
            'counted_stock',

            'reg_no'
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
    
class InventoryCountLineAddFormsetSerializer(serializers.ModelSerializer):

    # We redefine product_reg_no to by pass the unique validator
    product_reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = InventoryCountLine
        fields = (
            'expected_stock',
            'counted_stock',
            
            'product_reg_no'
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

class InventoryCountLineRemoveFormsetSerializer(serializers.ModelSerializer):

    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = InventoryCountLine
        fields = ('reg_no',)

    def validate_reg_no(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided wrong stores'

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000: # If you change this in the future, change also in your apps verification processes
            raise serializers.ValidationError(error_msg)
        
        return reg_no
    
class InventoryCountViewSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='__str__')
    store_data = serializers.ReadOnlyField(source='get_store_data')
    reg_no = serializers.ReadOnlyField()
    counted_by = serializers.ReadOnlyField(source='get_counted_by')
    creation_date = serializers.SerializerMethodField()
    completion_date = serializers.SerializerMethodField()
    line_data = serializers.ReadOnlyField(source='get_line_data')

    # List field
    lines_info = serializers.ListField(
        child=InventoryCountLineEditFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )
    lines_to_add = serializers.ListField(
        child=InventoryCountLineAddFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )
    lines_to_remove = serializers.ListField(
        child=InventoryCountLineRemoveFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    class Meta:
        model = InventoryCount
        fields = (
            'name',
            'notes',
            'store_data',
            'status',
            'reg_no',
            'counted_by',
            'creation_date',
            'completion_date',
            'line_data',

            'lines_info',
            'lines_to_add',
            'lines_to_remove'
        )
 
    def get_creation_date(self, obj):
        return obj.get_created_date(self.user.get_user_timezone())
    
    def get_completion_date(self, obj):

        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return '-'

        return obj.get_completed_date(self.user.get_user_timezone())

class InventoryCountViewStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = InventoryCount
        fields = (
            'status',
        )