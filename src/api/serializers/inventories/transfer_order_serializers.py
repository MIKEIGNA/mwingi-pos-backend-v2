from collections import OrderedDict
from django.conf import settings

from rest_framework import serializers

from inventories.models import TransferOrder, TransferOrderLine


###################### Transfer Order Index Serializers ######################
class TransferOrderLineFormsetSerializer(serializers.ModelSerializer):
    product_reg_no = serializers.IntegerField(write_only=True)

    class Meta:
        model = TransferOrderLine
        fields = (
            'product_reg_no',

            'quantity',
        )  

class TransferOrderListSerializer(serializers.ModelSerializer):

    name = serializers.ReadOnlyField(source='__str__')
    source_store_name = serializers.ReadOnlyField(source='get_source_store_name')
    destination_store_name = serializers.ReadOnlyField(source='get_destination_store_name')
    str_quantity = serializers.ReadOnlyField(source='get_str_quantity')
    reg_no = serializers.ReadOnlyField()
    creation_date = serializers.SerializerMethodField()
    completion_date = serializers.SerializerMethodField()

    source_store_reg_no = serializers.IntegerField(write_only=True)
    destination_store_reg_no = serializers.IntegerField(write_only=True)

    # List field
    transfer_order_lines = serializers.ListField(
        child=TransferOrderLineFormsetSerializer(),
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
        model = TransferOrder
        fields = (
            'name',
            'notes',
            'status',
            'source_store_name',
            'destination_store_name',
            'str_quantity',
            'reg_no',
            'creation_date',
            'completion_date',
            'is_auto_created',
            'source_description',
            
            'source_store_reg_no',
            'destination_store_reg_no',
            'transfer_order_lines'
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
    

###################### Transfer Order Completed Serializers ######################
    
class TransferOrderLineCompletedFormsetSerializer(serializers.ModelSerializer):
    loyverse_variant_id = serializers.CharField(max_length=60, write_only=True)

    class Meta:
        model = TransferOrderLine
        fields = (
            'loyverse_variant_id',
            'quantity',
        ) 
class TransferOrderCompletedListSerializer(serializers.ModelSerializer):
    source_store_id = serializers.CharField(max_length=60, write_only=True)
    destination_store_id = serializers.CharField(max_length=60, write_only=True)

    # List field
    transfer_order_lines = serializers.ListField(
        child=TransferOrderLineCompletedFormsetSerializer(),
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
        model = TransferOrder
        fields = (
            'notes',
            'source_description',
            
            'source_store_id',
            'destination_store_id',
            'transfer_order_lines'
        )

class TransferOrderLineEditFormsetSerializer(serializers.ModelSerializer):

    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    is_dirty = serializers.BooleanField(required=True, write_only=True)
    class Meta:
        model = TransferOrderLine
        fields = (
            'quantity',

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
    
class TransferOrderLineAddFormsetSerializer(serializers.ModelSerializer):

    # We redefine product_reg_no to by pass the unique validator
    product_reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = TransferOrderLine
        fields = (
            'quantity',
            
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

class TransferOrderLineRemoveFormsetSerializer(serializers.ModelSerializer):

    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = TransferOrderLine
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

class TransferOrderViewSerializer(serializers.ModelSerializer):

    name = serializers.ReadOnlyField(source='__str__')
    stores_data = serializers.ReadOnlyField(source='get_stores_data')
    source_store_name = serializers.ReadOnlyField(source='get_source_store_name')
    destination_store_name = serializers.ReadOnlyField(source='get_destination_store_name')
    reg_no = serializers.ReadOnlyField()
    ordered_by = serializers.ReadOnlyField(source='get_ordered_by')
    creation_date = serializers.SerializerMethodField()
    completion_date = serializers.SerializerMethodField()
    line_data = serializers.ReadOnlyField(source='get_line_data')

    source_store_reg_no = serializers.IntegerField(write_only=True)
    destination_store_reg_no = serializers.IntegerField(write_only=True)

    # List field
    lines_info = serializers.ListField(
        child=TransferOrderLineEditFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )
    lines_to_add = serializers.ListField(
        child=TransferOrderLineAddFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )
    lines_to_remove = serializers.ListField(
        child=TransferOrderLineRemoveFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    class Meta:
        model = TransferOrder
        fields = (
            'name',
            'notes',
            'status',
            'stores_data',
            'source_store_name',
            'destination_store_name',
            'quantity',
            'reg_no',
            'ordered_by',
            'creation_date',
            'completion_date',
            'source_description',
            'is_auto_created',
            'line_data',

            'source_store_reg_no',
            'destination_store_reg_no',

            'lines_info',
            'lines_to_add',
            'lines_to_remove'
        )

    def get_creation_date(self, obj):
        return obj.get_created_date(self.user.get_user_timezone())
    
    def get_completion_date(self, obj):
        return obj.get_completed_date(self.user.get_user_timezone())
    

class TransferOrderViewStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = TransferOrder
        fields = (
            'status',
        )
    
    

