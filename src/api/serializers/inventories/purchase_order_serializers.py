from collections import OrderedDict
from django.conf import settings
from rest_framework import serializers

from inventories.models import PurchaseOrder, PurchaseOrderAdditionalCost, PurchaseOrderLine

class PurchaseOrderLineFormsetSerializer(serializers.ModelSerializer):
    product_reg_no = serializers.IntegerField(write_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = (
            'product_reg_no',

            'quantity',
            'purchase_cost',
        )

class PurchaseOrderAdditionalCostFormsetSerializer(serializers.ModelSerializer):
  
    class Meta:
        model = PurchaseOrderAdditionalCost
        fields = (
            'name',
            'amount',
        )

class PurchaseOrderListSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='__str__')
    supplier_name = serializers.ReadOnlyField(source='get_supplier_name')
    store_name = serializers.ReadOnlyField(source='get_store_name')
    reg_no = serializers.ReadOnlyField()
    creation_date = serializers.SerializerMethodField()
    completion_date = serializers.SerializerMethodField()
    expectation_date = serializers.SerializerMethodField()

    supplier_reg_no = serializers.IntegerField(write_only=True)
    store_reg_no = serializers.IntegerField(write_only=True)
    created_date_timestamp = serializers.IntegerField(write_only=True)

    # List field
    purchase_order_lines = serializers.ListField(
        child=PurchaseOrderLineFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_STOCK_ADJUSTMENT_LINE_COUNT,
        write_only=True
    ) 
    purchase_order_additional_cost = serializers.ListField(
        child=PurchaseOrderAdditionalCostFormsetSerializer(),
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
        model = PurchaseOrder
        fields = (
            'name',
            'notes',
            'status',
            'supplier_name',
            'store_name',
            'total_amount',
            'reg_no',
            'creation_date',
            'completion_date',
            'expectation_date',

            'created_date_timestamp',
            'supplier_reg_no',
            'store_reg_no',
            'purchase_order_lines',
            'purchase_order_additional_cost'
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

    def get_expectation_date(self, obj):

        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return '-'

        return obj.get_expected_date(self.user.get_user_timezone())
    
    


class PurchaseOrderLineEditFormsetSerializer(serializers.ModelSerializer):

    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    is_dirty = serializers.BooleanField(required=True, write_only=True)
    class Meta:
        model = PurchaseOrderLine
        fields = (
            'quantity',
            'purchase_cost',

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
    
class PurchaseOrderLineAddFormsetSerializer(serializers.ModelSerializer):

    # We redefine product_reg_no to by pass the unique validator
    product_reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = PurchaseOrderLine
        fields = (
            'quantity',
            'purchase_cost',
            
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

class PurchaseOrderLineRemoveFormsetSerializer(serializers.ModelSerializer):

    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = PurchaseOrderLine
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
 

class PurchaseOrderViewSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='__str__')
    supplier_data = serializers.ReadOnlyField(source='get_supplier_data')
    store_data = serializers.ReadOnlyField(source='get_store_data')
    reg_no = serializers.ReadOnlyField()
    ordered_by = serializers.ReadOnlyField(source='get_ordered_by')
    creation_date = serializers.SerializerMethodField()
    completion_date = serializers.SerializerMethodField()
    expectation_date = serializers.SerializerMethodField()
    line_data = serializers.ReadOnlyField(source='get_line_data')
    additional_cost_data = serializers.ReadOnlyField(source='get_additional_cost_line_data')

    supplier_reg_no = serializers.IntegerField(write_only=True)
    store_reg_no = serializers.IntegerField(write_only=True) 

    # List field
    lines_info = serializers.ListField(
        child=PurchaseOrderLineEditFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )
    lines_to_add = serializers.ListField(
        child=PurchaseOrderLineAddFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )
    lines_to_remove = serializers.ListField(
        child=PurchaseOrderLineRemoveFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    class Meta:
        model = PurchaseOrder
        fields = (
            'name',
            'notes',
            'supplier_data',
            'store_data',
            'status',
            'total_amount',
            'reg_no',
            'ordered_by',
            'creation_date',
            'completion_date',
            'expectation_date',
            'line_data',
            'additional_cost_data',

            'supplier_reg_no',
            'store_reg_no',
            'created_date_timestamp',

            'lines_info',
            'lines_to_add',
            'lines_to_remove'
        )

    def get_creation_date(self, obj):
        return obj.get_created_date(self.user.get_user_timezone())

    def get_completion_date(self, obj):
        return obj.get_completed_date(self.user.get_user_timezone())
    
    def get_expectation_date(self, obj):
        return obj.get_expected_date(self.user.get_user_timezone())

    
class PurchaseOrderViewStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = PurchaseOrder
        fields = (
            'status',
        )