from collections import OrderedDict
from django.conf import settings

from rest_framework import serializers

from inventories.models import ProductTransform, ProductTransformLine

class ProductTransformLineFormsetSerializer(serializers.ModelSerializer):
    source_product_reg_no = serializers.IntegerField(write_only=True)
    target_product_reg_no = serializers.IntegerField(write_only=True)

    class Meta:
        model = ProductTransformLine
        fields = (
            'source_product_reg_no',
            'target_product_reg_no',
            'quantity',
            'cost',
            'added_quantity',
        )

class ProductTransformListSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='__str__')
    store_name = serializers.ReadOnlyField(source='get_store_name')
    reg_no = serializers.ReadOnlyField()
    creation_date = serializers.SerializerMethodField()

    store_reg_no = serializers.IntegerField(write_only=True)

    # List field
    product_transform_lines = serializers.ListField(
        child=ProductTransformLineFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_STOCK_ADJUSTMENT_LINE_COUNT,
        write_only=True
    ) 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)


    class Meta:
        model = ProductTransform
        fields = (
            'name',
            'store_name',
            'status',
            'total_quantity',
            'reg_no',
            'creation_date',
            'is_auto_repackaged',
            'auto_repackaged_source_desc',
            
            'store_reg_no',
            'product_transform_lines'
        )

    def get_creation_date(self, obj):

        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return '-'
            
        return obj.get_created_date(self.user.get_user_timezone())
    
class ProductTransformLineEditFormsetSerializer(serializers.ModelSerializer):

    # We redefine reg_no to by pass the unique validator
    target_product_reg_no = serializers.IntegerField(required=True, write_only=True)
    reg_no = serializers.IntegerField(required=True, write_only=True)
    is_dirty = serializers.BooleanField(required=True, write_only=True)
    class Meta:
        model = ProductTransformLine
        fields = (
            'quantity',
            'cost',
            'added_quantity',

            'target_product_reg_no',
            'reg_no',
            'is_dirty'
        )

class ProductTransformLineAddFormsetSerializer(serializers.ModelSerializer):

    # We redefine product_reg_nos to by pass the unique validator
    source_product_reg_no = serializers.IntegerField(required=True, write_only=True)
    target_product_reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = ProductTransformLine
        fields = (
            'source_product_reg_no',
            'target_product_reg_no',
            'quantity',
            'cost',
            'added_quantity',
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
    
class ProductTransformLineRemoveFormsetSerializer(serializers.ModelSerializer):

    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = ProductTransformLine
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

class ProductTransformViewSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='__str__')
    store_data = serializers.ReadOnlyField(source='get_store_data')
    reg_no = serializers.ReadOnlyField()
    created_by = serializers.ReadOnlyField(source='get_created_by')
    creation_date = serializers.SerializerMethodField()
    line_data = serializers.ReadOnlyField(source='get_line_data')

    store_reg_no = serializers.IntegerField(write_only=True) 

    # List field
    lines_info = serializers.ListField(
        child=ProductTransformLineEditFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )
    lines_to_add = serializers.ListField(
        child=ProductTransformLineAddFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )
    lines_to_remove = serializers.ListField(
        child=ProductTransformLineRemoveFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    class Meta:
        model = ProductTransform
        fields = (
            'name',
            'store_data',
            'status',
            'total_quantity',
            'reg_no',
            'created_by',
            'creation_date',
            'is_auto_repackaged',
            'auto_repackaged_source_desc',
            'auto_repackaged_source_reg_no',

            'line_data',

            'store_reg_no',
            'lines_info',
            'lines_to_add',
            'lines_to_remove'
        )

    def get_creation_date(self, obj):
        return obj.get_created_date(self.user.get_user_timezone())

    

    

